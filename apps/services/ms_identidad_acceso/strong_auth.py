"""TOTP RFC 6238, recuperación de un uso y reautenticación acotada."""

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from datetime import datetime, timezone, timedelta
from typing import Annotated
from uuid import uuid4

from cryptography.fernet import Fernet
from flask import current_app, g
from pydantic import Field
from werkzeug.security import check_password_hash, generate_password_hash

from redhouse.api import endpoint
from redhouse.db import transaction, get, insert, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema
from redhouse.models import ID, Model, Text
from redhouse.security import redis_call, key
from .routes import Login, public_user

OTP = Annotated[str, Field(pattern=r"^[0-9]{6}$")]
Secret = Annotated[str, Field(min_length=40, max_length=200)]


def cipher():
    return Fernet(
        base64.urlsafe_b64encode(
            hashlib.sha256(
                (
                    "identity-factors:v1:" + current_app.config["SERVICE_PRIVATE_KEY"]
                ).encode()
            ).digest()
        )
    )


def totp(secret, counter):
    digest = hmac.new(
        base64.b32decode(secret), struct.pack(">Q", counter), hashlib.sha1
    ).digest()
    offset = digest[-1] & 15
    return str(
        (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000
    ).zfill(6)


def verify_code(secret, code, last=-1):
    now = int(time.time()) // 30
    for counter in (now - 1, now, now + 1):
        if counter > last and hmac.compare_digest(totp(secret, counter), code or ""):
            return counter
    raise APIError("mfa_required", "Segundo factor inválido o ya utilizado.", 401)


def enforce_login(conn, user, code):
    factor = conn.execute(
        "SELECT * FROM security_factors WHERE id=%s FOR UPDATE", (user["id"],)
    ).fetchone()
    if factor and factor["active"]:
        failures = key("mfa:verification:" + str(user["id"]))
        count = redis_call(lambda r: r.get(failures))
        if count and int(count) >= 5:
            raise APIError("rate_limit", "Segundo factor temporalmente bloqueado.", 429)
        try:
            counter = verify_code(
                cipher().decrypt(factor["secret_ciphertext"].encode()).decode(),
                code,
                factor["last_counter"],
            )
        except APIError:
            redis_call(
                lambda r: r.eval(
                    "local n=redis.call('INCR',KEYS[1]); redis.call('EXPIRE',KEYS[1],300); return n",
                    1,
                    failures,
                )
            )
            current_app.logger.warning("mfa_verification_rejected")
            raise
        update(conn, "security_factors", user["id"], {"last_counter": counter})
        redis_call(lambda r: r.delete(failures))
    elif user["role"] in current_app.config.get("MFA_REQUIRED_ROLES", []):
        raise APIError(
            "mfa_enrollment_required",
            "Configura el segundo factor antes de acceder.",
            403,
        )


def revoke_sessions(conn, user):
    sessions = conn.execute(
        "SELECT id FROM sessions WHERE user_id=%s AND revoked_at IS NULL", (user["id"],)
    ).fetchall()
    redis_call(
        lambda r: r.set(
            key("permission_version:" + str(user["id"])), str(user["version"] + 1)
        )
    )
    if sessions:
        redis_call(
            lambda r: r.delete(*(key("session:" + str(s["id"])) for s in sessions))
        )
    conn.execute(
        "UPDATE sessions SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL",
        (user["id"],),
    )
    update(conn, "users", user["id"], {"version": user["version"] + 1})


def password_user(conn, username, password):
    attempts_key = key("mfa:attempt:" + hashlib.sha256(username.encode()).hexdigest())
    attempts = redis_call(
        lambda r: r.eval(
            "local n=redis.call('INCR',KEYS[1]); redis.call('EXPIRE',KEYS[1],300); return n",
            1,
            attempts_key,
        )
    )
    if attempts > 10:
        raise APIError("rate_limit", "Límite de verificación alcanzado.", 429)
    user = conn.execute(
        "SELECT u.*,i.region_id FROM users u JOIN institutions i ON i.id=u.tenant_id WHERE u.username=%s AND i.active FOR UPDATE OF u",
        (username,),
    ).fetchone()
    password_hash = (
        user["password_hash"]
        if user
        else generate_password_hash(secrets.token_urlsafe(20))
    )
    valid = check_password_hash(password_hash, password)
    if not user or not user["active"] or not valid:
        raise APIError("unauthorized", "Credenciales inválidas.", 401)
    return user


def queue_email(conn, user, subject, body, recipient):
    return insert(
        conn,
        "identity_deliveries",
        {
            "id": str(uuid4()),
            "recipient": recipient,
            "payload_ciphertext": cipher()
            .encrypt(json.dumps({"subject": subject, "body": body}).encode())
            .decode(),
        },
    )


def deliver_pending(limit=20):
    from redhouse.delivery import email

    for _ in range(limit):
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM identity_deliveries WHERE status='PENDING' AND next_attempt<=now() ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
            ).fetchone()
            if not row:
                break
            try:
                payload = json.loads(
                    cipher().decrypt(row["payload_ciphertext"].encode())
                )
                email(
                    row["recipient"],
                    payload["subject"],
                    payload["body"],
                    str(row["id"]),
                )
                update(
                    conn,
                    "identity_deliveries",
                    row["id"],
                    {
                        "status": "ACCEPTED_BY_SMTP",
                        "delivered_at": datetime.now(timezone.utc),
                        "payload_ciphertext": "",
                        "attempts": row["attempts"] + 1,
                        "last_error": None,
                    },
                )
            except APIError as exc:
                update(
                    conn,
                    "identity_deliveries",
                    row["id"],
                    {
                        "attempts": row["attempts"] + 1,
                        "last_error": exc.code,
                        "next_attempt": datetime.now(timezone.utc)
                        + timedelta(
                            seconds=min(3600, 2 ** min(row["attempts"] + 1, 11))
                        ),
                    },
                )


class Enrollment(Model):
    challenge: Secret
    code: OTP


class PasswordCheck(Model):
    password: Annotated[str, Field(min_length=12, max_length=128)]
    otp: OTP | None = None


class Reauthentication(PasswordCheck):
    challenge: Annotated[str, Field(min_length=40, max_length=4096)]


class Contact(PasswordCheck):
    email: Annotated[
        str, Field(min_length=5, max_length=200, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    ]


class TokenInput(Model):
    token: Secret


class RecoveryRequest(Model):
    username: Annotated[str, Field(min_length=3, max_length=80)]


class RecoveryFinish(TokenInput):
    password: Annotated[str, Field(min_length=12, max_length=128)]


class Accepted(Model):
    accepted: bool


class EnrollmentOutput(Model):
    challenge: str
    secret: str
    expires_in: int


class Proof(Model):
    proof: str
    expires_in: int
    operation: str
    resource_id: ID


def install(app):
    @endpoint(
        app,
        "/internal/v1/transport-users/<identifier>/operational-name",
        internal=("transporte",),
        roles=("TRANSPORT", "OPERATOR", "COORDINATOR"),
        result={
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "name": {"type": "string"},
            },
        },
        summary="Nombre operativo mínimo para una tarea autorizada por Transporte",
    )
    def transport_operational_name(identifier):
        with transaction() as conn:
            user = get(conn, "users", identifier)
            institution = get(conn, "institutions", str(user["tenant_id"]))
            if (
                not user["active"]
                or user["role"] != "TRANSPORT"
                or not institution["active"]
                or str(institution["region_id"]) != g.actor["region_id"]
            ):
                raise APIError("forbidden", "Transportista no disponible para esta tarea.", 403)
            return {"id": identifier, "name": user["username"]}

    @endpoint(
        app,
        "/internal/v1/custody-users/<identifier>",
        internal=("transporte",),
        delegate=False,
        result={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "active": {"type": "boolean"},
                "role": {"type": "string"},
            },
        },
    )
    def custody_user(identifier):
        with transaction() as conn:
            user = get(conn, "users", identifier)
            institution = get(conn, "institutions", str(user["tenant_id"]))
            return {
                "id": identifier,
                "tenant_id": str(user["tenant_id"]),
                "active": user["active"] and institution["active"],
                "role": user["role"],
            }

    @endpoint(
        app,
        "/internal/v1/notification-users/<identifier>",
        internal=("alertas",),
        delegate=False,
        result={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "active": {"type": "boolean"},
                "role": {"type": "string"},
                "email": {"type": ["string", "null"]},
            },
        },
    )
    def notification_user(identifier):
        with transaction() as conn:
            user = get(conn, "users", identifier)
            institution = get(conn, "institutions", str(user["tenant_id"]))
            contact = conn.execute(
                "SELECT email FROM security_contacts WHERE id=%s AND verified",
                (identifier,),
            ).fetchone()
            return {
                "id": identifier,
                "tenant_id": str(user["tenant_id"]),
                "active": user["active"] and institution["active"],
                "role": user["role"],
                "email": contact["email"] if contact else None,
            }

    @endpoint(
        app,
        "/api/v1/auth/mfa/enrollment",
        "POST",
        model=Login,
        public=True,
        result=schema(EnrollmentOutput),
    )
    def mfa_enrollment(data):
        with transaction() as conn:
            user = password_user(conn, data["username"], data["password"])
            if conn.execute(
                "SELECT 1 FROM security_factors WHERE id=%s", (user["id"],)
            ).fetchone():
                raise APIError(
                    "mfa_exists",
                    "Segundo factor ya registrado; recuperación requiere proceso institucional.",
                    409,
                )
        secret = base64.b32encode(secrets.token_bytes(20)).decode()
        challenge = secrets.token_urlsafe(48)
        payload = {
            "user_id": str(user["id"]),
            "secret": secret,
            "version": user["version"],
        }
        redis_call(
            lambda r: r.set(
                key("mfa:challenge:" + hashlib.sha256(challenge.encode()).hexdigest()),
                cipher().encrypt(json.dumps(payload).encode()).decode(),
                ex=300,
            )
        )
        return {"challenge": challenge, "secret": secret, "expires_in": 300}

    @endpoint(
        app,
        "/api/v1/auth/mfa/confirm",
        "POST",
        model=Enrollment,
        public=True,
        result=schema(Accepted),
    )
    def mfa_confirm(data):
        cache_key = key(
            "mfa:challenge:" + hashlib.sha256(data["challenge"].encode()).hexdigest()
        )
        attempts = redis_call(
            lambda r: r.eval(
                "local n=redis.call('INCR',KEYS[1]); redis.call('EXPIRE',KEYS[1],300); return n",
                1,
                cache_key + ":attempts",
            )
        )
        if attempts > 5:
            redis_call(lambda r: r.delete(cache_key))
            raise APIError(
                "rate_limit", "Desafío agotado; inicia otro enrolamiento.", 429
            )
        payload = redis_call(lambda r: r.get(cache_key))
        if not payload:
            raise APIError("unauthorized", "Desafío inválido o vencido.", 401)
        value = json.loads(cipher().decrypt(payload.encode()))
        counter = verify_code(value["secret"], data["code"])
        with transaction() as conn:
            user = get(conn, "users", value["user_id"], True)
            if not user["active"] or user["version"] != value["version"]:
                raise APIError("unauthorized", "Cuenta modificada.", 401)
            insert(
                conn,
                "security_factors",
                {
                    "id": user["id"],
                    "tenant_id": user["tenant_id"],
                    "secret_ciphertext": cipher()
                    .encrypt(value["secret"].encode())
                    .decode(),
                    "last_counter": counter,
                },
            )
            revoke_sessions(conn, user)
            institution = get(conn, "institutions", str(user["tenant_id"]))
            g.actor = {
                "id": str(user["id"]),
                "tenant_id": str(user["tenant_id"]),
                "region_id": str(institution["region_id"]),
            }
            emit(conn, "MFA_ENROLLED", user["id"], user["tenant_id"])
        redis_call(lambda r: r.delete(cache_key))
        return {"accepted": True}

    @endpoint(app, "/api/v1/auth/reauthenticate", "POST")
    def obsolete_reauthentication():
        raise APIError(
            "reauthentication_protocol_obsolete",
            "Actualiza el cliente para confirmar operaciones protegidas.",
            410,
        )

    @endpoint(
        app,
        "/api/v1/auth/reauthentication-proofs",
        "POST",
        model=Reauthentication,
        result=schema(Proof),
    )
    def reauthenticate(data):
        from redhouse.reauth import verify_challenge

        bound = verify_challenge(data["challenge"])
        with transaction() as conn:
            user = password_user(conn, g.actor["username"], data["password"])
            if (
                str(user["id"]) != g.actor["id"]
                or str(user["tenant_id"]) != g.actor["tenant_id"]
                or user["version"] != g.actor["version"]
            ):
                raise APIError(
                    "unauthorized", "La identidad o sus permisos cambiaron.", 401
                )
            enforce_login(conn, user, data["otp"])
            emit(conn, "REAUTHENTICATED", bound["resource_id"], user["tenant_id"])
        from redhouse.security import authenticate

        authenticate()
        bound = verify_challenge(data["challenge"])
        remaining = bound["issued_at"] + 120 - int(time.time())
        if remaining <= 0:
            raise APIError(
                "reauthentication_required",
                "El desafío venció; solicítalo nuevamente.",
                403,
            )
        token = secrets.token_urlsafe(48)
        redis_call(
            lambda r: r.set(
                key("reauth:v1:" + hashlib.sha256(token.encode()).hexdigest()),
                json.dumps(bound),
                ex=remaining,
            )
        )
        return {
            "proof": token,
            "expires_in": remaining,
            "operation": bound["operation"],
            "resource_id": bound["resource_id"],
        }

    @endpoint(
        app,
        "/api/v1/auth/contact",
        "POST",
        model=Contact,
        result=schema(Accepted),
        status=202,
    )
    def security_contact(data):
        token = secrets.token_urlsafe(48)
        with transaction() as conn:
            user = password_user(conn, g.actor["username"], data["password"])
            enforce_login(conn, user, data["otp"])
            old = conn.execute(
                "SELECT * FROM security_contacts WHERE id=%s", (user["id"],)
            ).fetchone()
            fields = {
                "email": data["email"],
                "verified": False,
                "verification_hash": hashlib.sha256(token.encode()).hexdigest(),
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
                "version": old["version"] + 1 if old else 1,
            }
            if old:
                update(conn, "security_contacts", user["id"], fields)
            else:
                insert(
                    conn,
                    "security_contacts",
                    dict(fields, id=user["id"], tenant_id=user["tenant_id"]),
                )
            queue_email(
                conn,
                user,
                "Verificar contacto Red House",
                "Código de verificación de un uso: " + token,
                data["email"],
            )
            emit(conn, "CONTACT_VERIFICATION_REQUESTED", user["id"], user["tenant_id"])
        return {"accepted": True}

    @endpoint(
        app,
        "/api/v1/auth/contact/verify",
        "POST",
        model=TokenInput,
        result=schema(Accepted),
    )
    def security_contact_verify(data):
        with transaction() as conn:
            contact = get(conn, "security_contacts", g.actor["id"], True)
            if (
                contact["verified"]
                or contact["expires_at"] <= datetime.now(timezone.utc)
                or not hmac.compare_digest(
                    contact["verification_hash"],
                    hashlib.sha256(data["token"].encode()).hexdigest(),
                )
            ):
                raise APIError("unauthorized", "Token inválido o vencido.", 401)
            update(
                conn,
                "security_contacts",
                g.actor["id"],
                {"verified": True, "verification_hash": "USED"},
            )
            emit(conn, "CONTACT_VERIFIED", g.actor["id"], g.actor["tenant_id"])
        return {"accepted": True}

    @endpoint(
        app,
        "/api/v1/auth/recovery",
        "POST",
        model=RecoveryRequest,
        public=True,
        result=schema(Accepted),
        status=202,
    )
    def recovery_request(data):
        count = redis_call(
            lambda r: r.eval(
                "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],3600) end; return n",
                1,
                key(
                    "recovery:" + hashlib.sha256(data["username"].encode()).hexdigest()
                ),
            )
        )
        if count > 3:
            return {"accepted": True}
        token = secrets.token_urlsafe(48)
        with transaction() as conn:
            user = conn.execute(
                "SELECT u.*,c.email FROM users u JOIN security_contacts c ON c.id=u.id JOIN institutions i ON i.id=u.tenant_id "
                "WHERE u.username=%s AND u.active AND i.active AND c.verified",
                (data["username"],),
            ).fetchone()
            if user:
                insert(
                    conn,
                    "recovery_tokens",
                    {
                        "id": str(uuid4()),
                        "user_id": user["id"],
                        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                        "expires_at": datetime.now(timezone.utc)
                        + timedelta(minutes=15),
                    },
                )
                queue_email(
                    conn,
                    user,
                    "Recuperación Red House",
                    "Token de recuperación de un uso: " + token,
                    user["email"],
                )
        return {"accepted": True}

    @endpoint(
        app,
        "/api/v1/auth/recovery/complete",
        "POST",
        model=RecoveryFinish,
        public=True,
        result=schema(Accepted),
    )
    def recovery_complete(data):
        with transaction() as conn:
            token = conn.execute(
                "SELECT * FROM recovery_tokens WHERE token_hash=%s FOR UPDATE",
                (hashlib.sha256(data["token"].encode()).hexdigest(),),
            ).fetchone()
            if (
                not token
                or token["used_at"]
                or token["expires_at"] <= datetime.now(timezone.utc)
            ):
                raise APIError("unauthorized", "Token inválido o vencido.", 401)
            user = get(conn, "users", str(token["user_id"]), True)
            institution = get(conn, "institutions", str(user["tenant_id"]))
            if not user["active"] or not institution["active"]:
                raise APIError("unauthorized", "Cuenta no disponible.", 401)
            revoke_sessions(conn, user)
            update(
                conn,
                "users",
                user["id"],
                {
                    "password_hash": generate_password_hash(
                        data["password"], method="scrypt:32768:8:1"
                    )
                },
            )
            conn.execute(
                "UPDATE recovery_tokens SET used_at=now() WHERE user_id=%s AND used_at IS NULL",
                (user["id"],),
            )
            g.actor = {
                "id": str(user["id"]),
                "tenant_id": str(user["tenant_id"]),
                "region_id": str(institution["region_id"]),
            }
            emit(conn, "PASSWORD_RECOVERED", user["id"], user["tenant_id"])
        return {"accepted": True}
