import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from ..access import BusinessError, Principal
from ...data_access.connection import transaction
from ...data_access.repositories import accounts, audit

# Se genera al cargar para aproximar el coste de una cuenta inexistente.
DUMMY_HASH = generate_password_hash(uuid4().hex, method="scrypt")
ISSUER = "red-house-web"
AUDIENCE = "red-house-portal"


def active(row):
    return row and row["account_status"] == "ACTIVE" and row["is_enabled"] and (
        row["institution_id"] is None or row["participation_status"] == "ACTIVE")


def digest(value):
    return hmac.new(current_app.config["SECRET_KEY"].encode(), value.encode(), hashlib.sha256).hexdigest()


def login(email, password, address):
    identity_hash, address_hash = digest("identity:" + email), digest("address:" + address)
    with transaction() as conn:
        # Serializa intentos concurrentes de la misma identidad o dirección.
        for key in (identity_hash, address_hash):
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (key,))
        counts = conn.execute("""SELECT count(*) FILTER (WHERE identity_hash = %s) AS identity_count,
            count(*) FILTER (WHERE address_hash = %s) AS address_count FROM login_attempt
            WHERE occurred_at > now() - interval '15 minutes' AND NOT was_successful
            AND (identity_hash = %s OR address_hash = %s)""",
            (identity_hash, address_hash, identity_hash, address_hash)).fetchone()
        if counts["identity_count"] >= 5 or counts["address_count"] >= 30:
            return None, "Demasiados intentos. Espera 15 minutos antes de intentarlo de nuevo.", 429
        row = accounts.by_email(conn, email)
        valid_password = check_password_hash(row["password_hash"] if row else DUMMY_HASH, password)
        principal = Principal.from_row(row) if row else None
        success = bool(active(row) and valid_password)
        conn.execute("""INSERT INTO login_attempt (identity_hash,address_hash,was_successful)
                        VALUES (%s,%s,%s)""", (identity_hash, address_hash, success))
        audit.record(conn, principal, "LOGIN", "USER_ACCOUNT", row["account_id"] if row else "UNKNOWN",
                     "Inicio de sesión" if success else "Credencial rechazada", outcome="SUCCESS" if success else "FAILED")
        if not success:
            return None, "No fue posible iniciar sesión. Revisa tus credenciales y el estado de tu acceso.", 401
        now, sid = datetime.now(timezone.utc), uuid4()
        expires = now + timedelta(seconds=current_app.config["JWT_LIFETIME_SECONDS"])
        conn.execute("INSERT INTO web_session (session_id,account_id,expires_at) VALUES (%s,%s,%s)",
                     (sid, row["account_id"], expires))
        token = jwt.encode({"sub": str(row["account_id"]), "jti": str(sid), "iat": now,
                            "nbf": now, "exp": expires, "iss": ISSUER, "aud": AUDIENCE},
                           current_app.config["JWT_SECRET_KEY"], algorithm="HS256")
        return token, None, 200


def authenticate(token):
    if not token:
        return None, None
    try:
        claims = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"],
                            audience=AUDIENCE, issuer=ISSUER,
                            options={"require": ["sub", "jti", "exp", "iat", "nbf", "aud", "iss"]})
        account_id, sid = UUID(claims["sub"]), UUID(claims["jti"])
    except (jwt.InvalidTokenError, ValueError, TypeError, AttributeError):
        return None, None
    with transaction() as conn:
        valid = conn.execute("""SELECT 1 FROM web_session WHERE session_id = %s AND account_id = %s
            AND revoked_at IS NULL AND expires_at > now()""", (sid, account_id)).fetchone()
        row = accounts.by_id(conn, account_id) if valid else None
        return (Principal.from_row(row), sid) if active(row) else (None, None)


def logout(principal, sid):
    with transaction() as conn:
        conn.execute("UPDATE web_session SET revoked_at = now() WHERE session_id = %s AND account_id = %s",
                     (sid, principal.account_id))
        audit.record(conn, principal, "LOGOUT", "USER_ACCOUNT", principal.account_id, "Sesión cerrada")
