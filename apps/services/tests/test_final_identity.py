import re
import time
from email import policy
from email.parser import BytesParser
from uuid import uuid4

import pytest

from .final_receivers import smtp_receiver
from .helpers import iso
from .test_final_quality import api


def email_token(message):
    body = BytesParser(policy=policy.default).parsebytes(message).get_content()
    return re.search(r": ([A-Za-z0-9_-]{64})", body)[1]


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_mfa_reauth_contact_recovery_and_revocation(p, monkeypatch, fmt):
    from ms_identidad_acceso.strong_auth import totp, deliver_pending

    name = "mfa-" + uuid4().hex[:12]
    password = "Synthetic-private-password-2026"
    api(
        p,
        "identidad_acceso",
        "/api/v1/users",
        {
            "username": name,
            "password": password,
            "tenant_id": p.env.state["tenants"][0],
            "role": "MEDICAL",
        },
        "admin1",
        fmt,
    )
    session = api(
        p,
        "identidad_acceso",
        "/api/v1/auth/login",
        {"username": name, "password": password},
        None,
        fmt,
    )
    p.tokens[name] = session["access_token"]
    identity = p.apps["identidad_acceso"]
    with smtp_receiver() as (port, messages):
        for key, value in {
            "SMTP_HOST": "127.0.0.1",
            "SMTP_PORT": port,
            "SMTP_TEST_RECEIVER": True,
            "SMTP_FROM": "tests@redhouse.invalid",
        }.items():
            monkeypatch.setitem(identity.config, key, value)
        api(
            p,
            "identidad_acceso",
            "/api/v1/auth/contact",
            {"email": name + "@example.invalid", "password": password},
            name,
            fmt,
        )
        with identity.app_context():
            deliver_pending()
        assert len(messages) == 1
        contact_token = email_token(messages[-1])
        api(
            p,
            "identidad_acceso",
            "/api/v1/auth/contact/verify",
            {"token": contact_token},
            name,
            fmt,
        )
        assert (
            p.request(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/contact/verify",
                user=name,
                data={"token": contact_token},
            ).status_code
            == 401
        )
        enrollment = api(
            p,
            "identidad_acceso",
            "/api/v1/auth/mfa/enrollment",
            {"username": name, "password": password},
            None,
            fmt,
        )
        counter = int(time.time()) // 30
        api(
            p,
            "identidad_acceso",
            "/api/v1/auth/mfa/confirm",
            {
                "challenge": enrollment["challenge"],
                "code": totp(enrollment["secret"], counter - 1),
            },
            None,
            fmt,
        )
        assert (
            p.request(
                "identidad_acceso", "GET", "/api/v1/auth/me", user=name
            ).status_code
            == 401
        )
        assert (
            p.request(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/login",
                user=None,
                data={"username": name, "password": password},
            ).status_code
            == 401
        )
        session = api(
            p,
            "identidad_acceso",
            "/api/v1/auth/login",
            {
                "username": name,
                "password": password,
                "otp": totp(enrollment["secret"], counter),
            },
            None,
            fmt,
        )
        p.tokens[name] = session["access_token"]
        unit = api(
            p,
            "inventario",
            "/api/v1/resources",
            {
                "folio": "AUTH-" + uuid4().hex[:10],
                "kind": "BLOOD",
                "component": "RBC",
                "blood_group": "O-",
                "expires_at": iso(days=2),
            },
            "operator1",
            fmt,
        )
        monkeypatch.setitem(
            p.apps["inventario"].config,
            "REAUTH_REQUIRED_OPERATIONS",
            ["resource_release"],
        )
        body = {
            "version": 1,
            "human_confirmation": True,
            "reason": "Dictamen de prueba con segundo factor",
        }
        path = f"/api/v1/resources/{unit['id']}/release"
        command_key = uuid4().hex
        initial = p.request(
            "inventario", "POST", path, data=body, user=name, key=command_key
        )
        assert initial.status_code == 403
        challenge = initial.json()["error"]["details"][0]["challenge"]
        proof = api(
            p,
            "identidad_acceso",
            "/api/v1/auth/reauthentication-proofs",
            {
                "password": password,
                "otp": totp(enrollment["secret"], counter + 1),
                "challenge": challenge,
            },
            name,
            fmt,
        )
        assert (
            p.request(
                "inventario",
                "POST",
                path,
                data=body,
                user="medical1",
                key=command_key,
                headers={"X-Reauthentication-Proof": proof["proof"]},
            ).status_code
            == 403
        )
        assert (
            p.request(
                "inventario",
                "POST",
                path,
                data=body,
                user=name,
                key=command_key,
                headers={"X-Reauthentication-Proof": proof["proof"]},
            ).status_code
            == 200
        )
        accepted = api(
            p,
            "identidad_acceso",
            "/api/v1/auth/recovery",
            {"username": name},
            None,
            fmt,
        )
        assert (
            api(
                p,
                "identidad_acceso",
                "/api/v1/auth/recovery",
                {"username": "unknown-" + uuid4().hex},
                None,
                fmt,
            )
            == accepted
        )
        with identity.app_context():
            deliver_pending()
        token = email_token(messages[-1])
        new_password = password + "-renewed"
        api(
            p,
            "identidad_acceso",
            "/api/v1/auth/recovery/complete",
            {"token": token, "password": new_password},
            None,
            fmt,
        )
        assert (
            p.request(
                "identidad_acceso", "GET", "/api/v1/auth/me", user=name
            ).status_code
            == 401
        )
        assert (
            p.request(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/recovery/complete",
                user=None,
                data={"token": token, "password": new_password},
            ).status_code
            == 401
        )
        with p.owner("identidad_acceso") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM recovery_tokens WHERE used_at IS NULL AND token_hash=%s",
                    (token,),
                ).fetchone()[0]
                == 0
            )
            assert (
                conn.execute(
                    "SELECT count(*) FROM identity_deliveries WHERE recipient=%s AND status='ACCEPTED_BY_SMTP'",
                    (name + "@example.invalid",),
                ).fetchone()[0]
                == 2
            )
    p.tokens.pop(name)


def test_totp_rfc_vector_and_policy_requirement(p, monkeypatch):
    import base64
    from ms_identidad_acceso.strong_auth import totp

    assert totp(base64.b32encode(b"12345678901234567890").decode(), 1) == "287082"
    monkeypatch.setitem(
        p.apps["identidad_acceso"].config, "MFA_REQUIRED_ROLES", ["ADMIN"]
    )
    response = p.request(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": "admin1", "password": p.env.state["password"]},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "mfa_enrollment_required"
