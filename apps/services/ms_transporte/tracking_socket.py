"""WSS JSON/XML: reautoriza antes de cada lote, con historial durable entre réplicas."""

import hashlib
import time
from uuid import uuid4

from flask import Response, request
from simple_websocket import ConnectionClosed, Server

from redhouse.codec import request_xsd
from redhouse.errors import APIError
from redhouse.events import audit_read
from redhouse.security import redis_call, key
from .tracking import authorize, publish, snapshot, access
from redhouse.db import transaction
from .tracking_contracts import Message, Event, decode, encode


class BoundedServer(Server):
    def _handle_events(self):
        result = super()._handle_events()
        if len(self.input_buffer) > 32:
            self.close(reason=1008, message="buffer_limit")
            return False
        return result


def lease(scope, identifier, limit):
    script = """redis.call('ZREMRANGEBYSCORE',KEYS[1],'-inf',ARGV[1]);
    if not redis.call('ZSCORE',KEYS[1],ARGV[2]) and redis.call('ZCARD',KEYS[1])>=tonumber(ARGV[4]) then return 0 end
    redis.call('ZADD',KEYS[1],ARGV[3],ARGV[2]); redis.call('EXPIRE',KEYS[1],45); return 1"""
    now = time.time()
    if not redis_call(
        lambda r: r.eval(
            script,
            1,
            key("tracking:connections:" + scope),
            now - 40,
            identifier,
            now,
            limit,
        )
    ):
        raise APIError("connection_limit", "Límite de conexiones alcanzado.", 429)


def install(app):
    def authorize_delivery(kind, credential, shipment_id):
        authorize(kind, credential)
        with transaction() as conn:
            access(conn, shipment_id, live=True)

    def send_position(ws, representation, kind, credential, shipment_id, position):
        authorize_delivery(kind, credential, shipment_id)
        ws.send(
            encode(
                {
                    "type": "position.updated",
                    "shipment_id": shipment_id,
                    "cursor": position["cursor"],
                    "position": position,
                },
                representation,
            )
        )

    @app.get("/schemas/tracking/<name>.xsd")
    def tracking_xsd(name):
        if name not in ("message", "event"):
            raise APIError("not_found", "Contrato inexistente.", 404)
        return Response(
            request_xsd(Message if name == "message" else Event),
            mimetype="application/xml",
        )

    @app.route("/ws/v1/tracking/<representation>", websocket=True)
    def tracking_socket(representation):
        if representation not in ("json", "xml") or request.query_string:
            raise APIError("invalid_handshake", "Ruta o parámetros no permitidos.", 400)
        origin = request.headers.get("Origin")
        if origin and origin not in app.config.get("TRACKING_ALLOWED_ORIGINS", []):
            raise APIError("origin_forbidden", "Origen no autorizado.", 403)
        if not request.is_secure and not app.config.get(
            "TRACKING_ALLOW_INSECURE_LOCAL", False
        ):
            # Solo proxies de confianza pueden terminar TLS. No se confía en cabeceras arbitrarias.
            raise APIError("tls_required", "El canal requiere WSS.", 400)
        protocol = "redhouse.tracking.v1." + representation
        if protocol not in request.headers.get("Sec-WebSocket-Protocol", "").split(
            ", "
        ):
            raise APIError("subprotocol_required", "Subprotocolo v1 requerido.", 400)
        identifier, scopes, ws = str(uuid4()), ["global"], None
        lease("global", identifier, app.config.get("TRACKING_MAX_CONNECTIONS", 64))
        try:
            ws = BoundedServer.accept(
                request.environ,
                subprotocols=[protocol],
                ping_interval=15,
                max_message_size=16384,
                receive_bytes=4096,
            )
            # Evita que un lector lento retenga una conexión/hilo indefinidamente.
            ws.sock.settimeout(5)
            raw = ws.receive(timeout=5)
            if raw is None:
                raise APIError("auth_timeout", "Autenticación no recibida.", 401)
            auth = decode(raw, representation=representation)
            if auth["type"] != "authenticate":
                raise APIError("unauthorized", "Autentica antes de suscribirte.", 401)
            kind, credential = auth["credential_kind"], auth["credential"]
            actor = authorize(kind, credential)
            scope = hashlib.sha256((kind + ":" + actor["id"]).encode()).hexdigest()
            lease(
                scope, identifier, app.config.get("TRACKING_CONNECTIONS_PER_ACTOR", 4)
            )
            scopes.append(scope)
            app.logger.info(
                "tracking_open connection=%s principal_kind=%s", identifier, kind
            )
            ws.send(encode({"type": "authenticated"}, representation))
            subscriptions = {}
            last_input, last_status = time.monotonic(), 0.0
            while ws.connected:
                authorize(kind, credential)
                for scope_name in scopes:
                    lease(
                        scope_name,
                        identifier,
                        app.config.get("TRACKING_MAX_CONNECTIONS", 64)
                        if scope_name == "global"
                        else app.config.get("TRACKING_CONNECTIONS_PER_ACTOR", 4),
                    )
                raw = ws.receive(timeout=0.5)
                if raw is not None:
                    last_input = time.monotonic()
                    limit_key = key(f"tracking:rate:{scope}:{int(time.time()) // 60}")
                    count = redis_call(
                        lambda r: r.eval(
                            "local n=redis.call('INCR',KEYS[1]); redis.call('EXPIRE',KEYS[1],61); return n",
                            1,
                            limit_key,
                        )
                    )
                    if count > app.config.get("TRACKING_MESSAGES_PER_MINUTE", 1200):
                        raise APIError("rate_limit", "Frecuencia excesiva.", 429)
                    message = decode(raw, representation=representation)
                    typ, shipment_id = message["type"], message["shipment_id"]
                    if typ == "position.publish":
                        point = publish(message["position"], kind, credential)
                        ws.send(
                            encode(
                                {
                                    "type": "position.ack",
                                    "shipment_id": point["shipment_id"],
                                    "event_id": point["event_id"],
                                    "cursor": point["cursor"],
                                    "state": "PERSISTED_SQL",
                                },
                                representation,
                            )
                        )
                    elif typ == "subscribe":
                        if kind not in ("user", "browser"):
                            raise APIError(
                                "forbidden", "Dispositivos solo publican.", 403
                            )
                        if shipment_id not in subscriptions and len(subscriptions) >= 8:
                            raise APIError(
                                "subscription_limit", "Máximo ocho traslados.", 429
                            )
                        try:
                            result = snapshot(shipment_id, message["cursor"], live=True)
                        except APIError as exc:
                            if exc.code == "resync_required":
                                ws.send(
                                    encode(
                                        {
                                            "type": "resync.required",
                                            "shipment_id": shipment_id,
                                            "code": exc.code,
                                        },
                                        representation,
                                    )
                                )
                                continue
                            raise
                        audit_read(shipment_id)
                        subscriptions[shipment_id] = result["cursor"]
                        authorize_delivery(kind, credential, shipment_id)
                        ws.send(
                            encode(
                                {
                                    "type": "subscribed",
                                    "shipment_id": shipment_id,
                                    "cursor": result["cursor"],
                                    "position": result["position"],
                                    "state": result["state"],
                                },
                                representation,
                            )
                        )
                        for position in result["events"]:
                            send_position(
                                ws,
                                representation,
                                kind,
                                credential,
                                shipment_id,
                                position,
                            )
                    elif typ == "unsubscribe":
                        subscriptions.pop(shipment_id, None)
                        ws.send(
                            encode(
                                {"type": "unsubscribed", "shipment_id": shipment_id},
                                representation,
                            )
                        )
                    elif typ == "heartbeat":
                        ws.send(encode({"type": "heartbeat"}, representation))
                    else:
                        raise APIError(
                            "invalid_message",
                            "La autenticación no puede sustituirse en un socket.",
                            400,
                        )
                if time.monotonic() - last_input > 60:
                    raise APIError(
                        "idle_timeout", "Envía heartbeat para conservar el canal.", 408
                    )
                report_status = time.monotonic() - last_status >= 10
                for shipment_id, cursor in list(subscriptions.items()):
                    authorize(kind, credential)
                    result = snapshot(shipment_id, cursor, live=True)
                    for position in result["events"]:
                        send_position(
                            ws, representation, kind, credential, shipment_id, position
                        )
                        subscriptions[shipment_id] = position["cursor"]
                    if report_status:
                        authorize_delivery(kind, credential, shipment_id)
                        ws.send(
                            encode(
                                {
                                    "type": "tracking.status",
                                    "shipment_id": shipment_id,
                                    "state": result["state"],
                                    "cursor": subscriptions[shipment_id],
                                },
                                representation,
                            )
                        )
                if report_status:
                    last_status = time.monotonic()
        except APIError as exc:
            app.logger.info("tracking_rejected code=%s", exc.code)
            if ws and ws.connected:
                try:
                    ws.send(
                        encode(
                            {
                                "type": "resync.required"
                                if exc.code == "resync_required"
                                else "error",
                                "code": exc.code,
                                "message": exc.message,
                            },
                            representation,
                        )
                    )
                    ws.close(reason=1013 if exc.status == 503 else 1008)
                except (ConnectionClosed, OSError):
                    pass
        except (ConnectionClosed, OSError):
            pass
        except Exception as exc:  # noqa: BLE001 - socket boundary never exposes input or dependency details
            app.logger.error(
                "tracking_failure connection=%s exception_type=%s",
                identifier,
                type(exc).__name__,
            )
            if ws and ws.connected:
                try:
                    ws.send(
                        encode(
                            {
                                "type": "error",
                                "code": "tracking_unavailable",
                                "message": "Canal temporalmente indisponible; conserva el cursor.",
                            },
                            representation,
                        )
                    )
                    ws.close(reason=1013)
                except (ConnectionClosed, OSError):
                    pass
        finally:
            app.logger.info("tracking_close connection=%s", identifier)
            for scope in scopes:
                try:
                    redis_call(
                        lambda r: r.zrem(
                            key("tracking:connections:" + scope), identifier
                        )
                    )
                except APIError:
                    pass  # Las concesiones huérfanas expiran; no mantienen acceso.
            if ws and ws.connected:
                ws.close()
        return ""
