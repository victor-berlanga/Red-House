import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from flask import current_app, g
from pydantic import ConfigDict, Field, StringConstraints
from werkzeug.security import check_password_hash, generate_password_hash

from redhouse.api import atomic, endpoint, listing
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import Confirm, ID, Model, Role, Text, validate_id
from redhouse.decisions import record, history
from redhouse.security import access_token, key, own, redis_call


class Login(Model):
    model_config = ConfigDict(
        extra="forbid", strict=True, str_strip_whitespace=False, allow_inf_nan=False
    )
    username: Annotated[
        str,
        StringConstraints(strip_whitespace=True),
        Field(min_length=3, max_length=80),
    ]
    password: Annotated[str, Field(min_length=12, max_length=128)]


class Refresh(Model):
    refresh_token: Annotated[str, Field(min_length=60, max_length=120)]


class NewInstitution(Model):
    name: Text


class NewUser(Login):
    tenant_id: ID
    role: Role


class InstitutionEdit(Confirm):
    name: Text
    version: Annotated[int, Field(ge=1)]


class InstitutionAdministrator(Login, Confirm):
    pass


class UserState(Model):
    active: bool
    version: Annotated[int, Field(ge=1)]


def public_user(row):
    return {
        k: str(row[k]) if k in ("id", "tenant_id", "region_id") else row[k]
        for k in (
            "id",
            "tenant_id",
            "region_id",
            "username",
            "role",
            "active",
            "version",
        )
    }


def permissions(user):
    # PostgreSQL es la autoridad. El bloqueo serializa publicación y cambios de
    # cuenta; permite reparar una invalidación Redis cuyo SQL fue revertido.
    with transaction() as conn:
        latest = get(conn, "users", user["id"], True)
        if latest["version"] != user["version"] or latest["active"] != user["active"]:
            raise APIError(
                "permissions_changed",
                "Permisos cambiaron durante la operación; vuelve a autenticarte.",
                503,
            )
        script = """
        redis.call('SET',KEYS[2],ARGV[2]);
        redis.call('SET',KEYS[1],ARGV[1],'EX',ARGV[3]); return 1
        """
        redis_call(
            lambda r: r.eval(
                script,
                2,
                key("permissions:" + user["id"]),
                key("permission_version:" + user["id"]),
                json.dumps(user),
                user["version"],
                current_app.config["REFRESH_TTL"],
            )
        )


def refresh_key(token):
    return key("refresh:" + hashlib.sha256(token.encode()).hexdigest())


def register(app):
    @endpoint(
        app,
        "/api/v1/audit-assignees",
        roles=("AUDITOR",),
        paginated=True,
        query=("q",),
        summary="Coordinadores habilitados de la región para atención de hallazgos",
    )
    def audit_assignees():
        with transaction() as conn:
            return listing(
                conn,
                "users u JOIN institutions i ON i.id=u.tenant_id",
                "i.region_id=%s AND u.active AND i.active AND u.role='COORDINATOR'",
                (g.actor["region_id"],),
                columns="u.id,u.username,u.tenant_id,u.role",
                order="u.username,u.id",
                filters={"q": ("u.username",)},
            )

    @endpoint(
        app,
        "/internal/v1/audit-assignees/<identifier>",
        internal=("auditoria",),
        roles=("AUDITOR",),
        summary="Validar coordinador regional para un hallazgo",
    )
    def audit_assignee(identifier):
        with transaction() as conn:
            row = get(conn, "users", identifier)
            institution = get(conn, "institutions", str(row["tenant_id"]))
            if (
                str(institution["region_id"]) != g.actor["region_id"]
                or not institution["active"]
                or not row["active"]
                or row["role"] != "COORDINATOR"
            ):
                raise APIError(
                    "forbidden",
                    "El responsable debe ser un coordinador activo de tu región.",
                    403,
                )
            return {key: row[key] for key in ("id", "username", "tenant_id", "role")}

    @endpoint(
        app,
        "/api/v1/auth/login",
        "POST",
        model=Login,
        public=True,
        summary="Iniciar sesión independiente",
    )
    def login(data):
        lock = key(
            "login_fail:" + hashlib.sha256(data["username"].encode()).hexdigest()
        )
        attempts = redis_call(lambda r: r.get(lock))
        if attempts and int(attempts) >= 5:
            raise APIError("login_locked", "Acceso temporalmente bloqueado.", 429)
        with transaction() as conn:
            row = conn.execute(
                "SELECT u.*,i.region_id FROM users u JOIN institutions i ON i.id=u.tenant_id WHERE username=%s AND i.active",
                (data["username"],),
            ).fetchone()
            valid = check_password_hash(
                row["password_hash"]
                if row
                else app.config.get("DUMMY_HASH")
                or generate_password_hash(secrets.token_urlsafe(24)),
                data["password"],
            )
            if not row or not row["active"] or not valid:
                redis_call(
                    lambda r: r.eval(
                        "local n=redis.call('INCR',KEYS[1]); redis.call('EXPIRE',KEYS[1],300); return n",
                        1,
                        lock,
                    )
                )
                if row:
                    g.actor = public_user(row)
                    emit(conn, "LOGIN_FAILED", row["id"], row["tenant_id"])
                # Registrar fallo antes de emitir 401 (no lanzar dentro de la transacción).
                failed = True
            else:
                failed = False
                user = public_user(row)
                g.actor = user
                sid = str(uuid4())
                expires = datetime.now(timezone.utc) + timedelta(
                    seconds=app.config["REFRESH_TTL"]
                )
                insert(
                    conn,
                    "sessions",
                    {"id": sid, "user_id": user["id"], "expires_at": expires},
                )
                emit(conn, "LOGIN", user["id"], user["tenant_id"])
        if failed:
            raise APIError("unauthorized", "Credenciales inválidas.", 401)
        token = sid + "." + secrets.token_urlsafe(32)
        permissions(user)

        def save(r):
            with r.pipeline(transaction=True) as pipe:
                pipe.set(
                    key("session:" + sid),
                    json.dumps(
                        {"user_id": user["id"], "expires": int(expires.timestamp())}
                    ),
                    ex=app.config["REFRESH_TTL"],
                )
                pipe.set(refresh_key(token), sid, ex=app.config["REFRESH_TTL"])
                pipe.delete(lock)
                pipe.execute()

        redis_call(save)
        return {
            "access_token": access_token(user, sid),
            "refresh_token": token,
            "token_type": "Bearer",
            "expires_in": app.config["ACCESS_TTL"],
            "user": user,
        }

    @endpoint(
        app,
        "/api/v1/auth/refresh",
        "POST",
        model=Refresh,
        public=True,
        summary="Rotar renovación; repetición revoca familia",
    )
    def refresh(data):
        token = data["refresh_token"]
        sid = token.split(".")[0]
        validate_id(sid)
        current = redis_call(lambda r: r.get(key("session:" + sid)))
        if not current:
            raise APIError("unauthorized", "Renovación inválida.", 401)
        state = json.loads(current)
        with transaction() as conn:
            row = conn.execute(
                "SELECT u.*,i.region_id FROM users u JOIN institutions i ON i.id=u.tenant_id WHERE u.id=%s AND i.active",
                (state["user_id"],),
            ).fetchone()
            if not row or not row["active"]:
                raise APIError("unauthorized", "Cuenta inactiva.", 401)
            user = public_user(row)
            g.actor = user
            emit(conn, "REFRESH_ATTEMPT", user["id"], user["tenant_id"])
        replacement = sid + "." + secrets.token_urlsafe(32)
        ttl = max(0, state["expires"] - int(time.time()))
        if not ttl:
            raise APIError("unauthorized", "Sesión vencida.", 401)
        script = """
        if redis.call('EXISTS',KEYS[4])==1 then redis.call('DEL',KEYS[3]); return -1 end
        if redis.call('GET',KEYS[1])~=ARGV[1] or redis.call('EXISTS',KEYS[3])==0 then return 0 end
        redis.call('DEL',KEYS[1]); redis.call('SET',KEYS[4],'1','EX',ARGV[2]);
        redis.call('SET',KEYS[2],ARGV[1],'EX',ARGV[2]); return 1
        """
        result = redis_call(
            lambda r: r.eval(
                script,
                4,
                refresh_key(token),
                refresh_key(replacement),
                key("session:" + sid),
                key("used_refresh:" + hashlib.sha256(token.encode()).hexdigest()),
                sid,
                ttl,
            )
        )
        if result != 1:
            raise APIError(
                "unauthorized", "Renovación inválida o reutilizada; inicia sesión.", 401
            )
        permissions(user)
        return {
            "access_token": access_token(user, sid),
            "refresh_token": replacement,
            "token_type": "Bearer",
            "expires_in": app.config["ACCESS_TTL"],
        }

    @endpoint(
        app, "/api/v1/auth/logout", "POST", summary="Cerrar sesión y revocar familia"
    )
    def logout():
        def work(conn):
            conn.execute(
                "UPDATE sessions SET revoked_at=now() WHERE id=%s", (g.claims["sid"],)
            )
            emit(conn, "LOGOUT", g.actor["id"], g.actor["tenant_id"])
            redis_call(lambda r: r.delete(key("session:" + g.claims["sid"])))
            redis_call(
                lambda r: r.set(
                    key("revoked:" + g.claims["jti"]),
                    "1",
                    ex=max(1, g.claims["exp"] - int(time.time())),
                )
            )
            return {"revoked": True}

        return atomic("logout", {}, work)

    @endpoint(
        app,
        "/api/v1/auth/revoke",
        "POST",
        model=Refresh,
        public=True,
        summary="Revocar familia con renovación opaca, incluso si venció el JWT de acceso",
    )
    def revoke(data):
        token = data["refresh_token"]
        sid = token.split(".")[0]
        validate_id(sid)
        # Un token utilizado también prueba pertenencia; su reutilización ya
        # revoca la familia en refresh. No se confía solamente en el UUID.
        used = key("used_refresh:" + hashlib.sha256(token.encode()).hexdigest())
        script = """
        if redis.call('GET',KEYS[1])==ARGV[1] or redis.call('EXISTS',KEYS[2])==1 then
          redis.call('DEL',KEYS[3]); redis.call('DEL',KEYS[1]);
          redis.call('SET',KEYS[2],'1','EX',ARGV[2]); return 1
        end
        return 0
        """
        valid = redis_call(
            lambda r: r.eval(
                script,
                3,
                refresh_key(token),
                used,
                key("session:" + sid),
                sid,
                app.config["REFRESH_TTL"],
            )
        )
        if valid:
            with transaction() as conn:
                row = conn.execute(
                    "SELECT u.*,i.region_id FROM sessions s JOIN users u ON u.id=s.user_id JOIN institutions i ON i.id=u.tenant_id WHERE s.id=%s",
                    (sid,),
                ).fetchone()
                if row:
                    g.actor = public_user(row)
                    conn.execute(
                        "UPDATE sessions SET revoked_at=coalesce(revoked_at,now()) WHERE id=%s",
                        (sid,),
                    )
                    emit(conn, "LOGOUT", g.actor["id"], g.actor["tenant_id"])
        # Resultado uniforme e idempotente sin oráculo de tokens.
        return {"revoked": True}

    @endpoint(app, "/api/v1/auth/me", summary="Consultar perfil y permisos vigentes")
    def me():
        return g.actor

    @endpoint(
        app,
        "/api/v1/institutions",
        summary="Instituciones de la región; sin datos clínicos",
        paginated=True,
    )
    def institutions():
        with transaction() as conn:
            return listing(
                conn,
                "institutions",
                "region_id=%s AND active",
                (g.actor["region_id"],),
                order="name,id",
            )

    @endpoint(
        app,
        "/api/v1/institutions",
        "POST",
        model=NewInstitution,
        roles=("ADMIN",),
        status=201,
        summary="Registrar institución de la región",
    )
    def institution_create(data):
        def work(conn):
            row = insert(
                conn,
                "institutions",
                dict(
                    id=str(uuid4()),
                    region_id=g.actor["region_id"],
                    created_by=g.actor["id"],
                    **data,
                ),
            )
            emit(conn, "INSTITUTION_CREATED", row["id"], row["id"])
            return row

        return atomic("institution_create", data, work)

    @endpoint(
        app,
        "/api/v1/institutions/<identifier>",
        roles=("ADMIN",),
        summary="Detalle administrativo de institución regional",
    )
    def institution_detail(identifier):
        with transaction() as conn:
            row = get(conn, "institutions", identifier)
            if str(row["region_id"]) != g.actor["region_id"]:
                raise APIError("forbidden", "Institución de otra región.", 403)
            row["decisions"] = history(conn, identifier)
            return row

    @endpoint(
        app,
        "/api/v1/institutions/<identifier>",
        "PATCH",
        model=InstitutionEdit,
        roles=("ADMIN",),
        summary="Editar nombre institucional propio con versión y motivo",
    )
    def institution_edit(identifier, data):
        own(identifier)

        def work(conn):
            row = get(conn, "institutions", identifier, True)
            if row["version"] != data["version"]:
                raise APIError("stale_version", "Institución modificada.", 409)
            record(
                conn,
                identifier,
                identifier,
                "INSTITUTION_UPDATED",
                data["reason"],
                {"name": data["name"]},
            )
            result = update(
                conn,
                "institutions",
                identifier,
                {"name": data["name"], "version": row["version"] + 1},
            )
            emit(conn, "INSTITUTION_UPDATED", identifier, identifier)
            return result

        return atomic("institution_edit:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/institutions/<identifier>/administrator",
        "POST",
        model=InstitutionAdministrator,
        roles=("ADMIN",),
        status=201,
        summary="Provisionar primer administrador de una institución creada por esta cuenta",
    )
    def institution_administrator(identifier, data):
        def work(conn):
            institution = get(conn, "institutions", identifier, True)
            if (
                str(institution["created_by"]) != g.actor["id"]
                or str(institution["region_id"]) != g.actor["region_id"]
            ):
                raise APIError(
                    "forbidden",
                    "Solo el creador puede completar el alta institucional.",
                    403,
                )
            if conn.execute(
                "SELECT 1 FROM users WHERE tenant_id=%s LIMIT 1", (identifier,)
            ).fetchone():
                raise APIError(
                    "conflict",
                    "La institución ya tiene cuentas; su administrador gestiona los accesos.",
                    409,
                )
            row = insert(
                conn,
                "users",
                dict(
                    id=str(uuid4()),
                    tenant_id=identifier,
                    username=data["username"],
                    password_hash=generate_password_hash(
                        data["password"], method="scrypt:32768:8:1"
                    ),
                    role="ADMIN",
                ),
            )
            row["region_id"] = institution["region_id"]
            record(
                conn, identifier, identifier, "INSTITUTION_PROVISIONED", data["reason"]
            )
            emit(conn, "INSTITUTION_PROVISIONED", identifier, identifier)
            return public_user(row)

        sanitized = {k: v for k, v in data.items() if k != "password"}
        sanitized["password_digest"] = hmac.new(
            app.config["SERVICE_PRIVATE_KEY"].encode(),
            data["password"].encode(),
            hashlib.sha256,
        ).hexdigest()
        return atomic("institution_administrator:" + identifier, sanitized, work)

    @endpoint(
        app,
        "/api/v1/users",
        "POST",
        model=NewUser,
        roles=("ADMIN",),
        status=201,
        summary="Crear cuenta institucional",
    )
    def user_create(data):
        own(data["tenant_id"])

        def work(conn):
            institution = get(conn, "institutions", data["tenant_id"])
            row = insert(
                conn,
                "users",
                dict(
                    id=str(uuid4()),
                    tenant_id=data["tenant_id"],
                    username=data["username"],
                    password_hash=generate_password_hash(
                        data["password"], method="scrypt:32768:8:1"
                    ),
                    role=data["role"],
                ),
            )
            row["region_id"] = institution["region_id"]
            emit(conn, "USER_CREATED", row["id"], row["tenant_id"])
            return public_user(row)

        # No guardar contraseñas en resultado ni huellas de idempotencia recuperables.
        sanitized = {k: v for k, v in data.items() if k != "password"}
        sanitized["password_digest"] = hmac.new(
            app.config["SERVICE_PRIVATE_KEY"].encode(),
            data["password"].encode(),
            hashlib.sha256,
        ).hexdigest()
        return atomic("user_create", sanitized, work)

    @endpoint(
        app,
        "/api/v1/users/<identifier>",
        "PATCH",
        model=UserState,
        roles=("ADMIN",),
        summary="Activar/desactivar cuenta; invalidar permisos antes del cambio",
    )
    def user_state(identifier, data):
        validate_id(identifier)
        with transaction() as conn:
            own(get(conn, "users", identifier)["tenant_id"])
        if identifier == g.actor["id"] and not data["active"]:
            raise APIError("conflict", "No puedes desactivar tu propia cuenta.", 409)

        def work(conn):
            row = get(conn, "users", identifier, True)
            own(row["tenant_id"])
            if row["version"] != data["version"]:
                raise APIError("stale_version", "Versión obsoleta.", 409)
            redis_call(
                lambda r: r.eval(
                    "redis.call('SET',KEYS[1],ARGV[1]); redis.call('DEL',KEYS[2]); return 1",
                    2,
                    key("permission_version:" + identifier),
                    key("permissions:" + identifier),
                    row["version"] + 1,
                )
            )
            if not data["active"]:
                sessions = conn.execute(
                    "SELECT id FROM sessions WHERE user_id=%s AND revoked_at IS NULL",
                    (identifier,),
                ).fetchall()
                if sessions:
                    redis_call(
                        lambda r: r.delete(
                            *(key("session:" + str(s["id"])) for s in sessions)
                        )
                    )
                    conn.execute(
                        "UPDATE sessions SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL",
                        (identifier,),
                    )
            updated = update(
                conn,
                "users",
                identifier,
                {"active": data["active"], "version": row["version"] + 1},
            )
            updated["region_id"] = get(conn, "institutions", str(row["tenant_id"]))[
                "region_id"
            ]
            emit(conn, "USER_STATE_CHANGED", identifier, row["tenant_id"])
            return public_user(updated)

        result = atomic("user_state:" + identifier, data, work)
        with transaction() as conn:
            latest = get(conn, "users", identifier)
            latest["region_id"] = get(conn, "institutions", str(latest["tenant_id"]))[
                "region_id"
            ]
        permissions(public_user(latest))
        return result

    @endpoint(
        app,
        "/internal/v1/institutions/<identifier>",
        internal=("inventario", "priorizacion_geografia", "transporte", "donantes"),
        summary="Referencia institucional autorizada",
    )
    def institution_internal(identifier):
        with transaction() as conn:
            row = get(conn, "institutions", identifier)
            if str(row["region_id"]) != g.actor["region_id"] or not row["active"]:
                raise APIError(
                    "forbidden", "Institución fuera de la región o inactiva.", 403
                )
            return row

    @endpoint(
        app,
        "/internal/v1/users/<identifier>",
        internal=("transporte",),
        roles=("COORDINATOR",),
        summary="Validar personal de traslado",
    )
    def user_internal(identifier):
        with transaction() as conn:
            row = get(conn, "users", identifier)
            institution = get(conn, "institutions", str(row["tenant_id"]))
            if (
                str(institution["region_id"]) != g.actor["region_id"]
                or row["role"] != "TRANSPORT"
                or not row["active"]
                or not institution["active"]
            ):
                raise APIError("forbidden", "Personal no habilitado.", 403)
            row["region_id"] = institution["region_id"]
            return public_user(row)
