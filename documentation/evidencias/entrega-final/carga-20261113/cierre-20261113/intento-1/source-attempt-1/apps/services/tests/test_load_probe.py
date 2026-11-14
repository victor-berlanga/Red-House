"""Pruebas funcionales Locust; no equivalen a medición de capacidad o estrés."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from tests.load_support import run_locust


def test_six_profiles_locust_contracts_renewal_and_logout(platform, tmp_path):
    summary = run_locust(platform, tmp_path)
    assert summary["counts"]["donantes / Feed público"] > 0
    assert summary["counts"]["transporte / Tareas propias"] > 0


def test_appointments_and_inventory_are_persisted_under_locust(platform, tmp_path):
    p = platform
    marker = "Carga-" + uuid4().hex[:10]
    now = datetime.now(timezone.utc)
    site = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/catalogues/sites",
        user="admin1",
        data={
            "name": marker,
            "municipality": "Monterrey",
            "address": "Ubicación sintética",
        },
    )
    campaign = p.ok(
        "donantes",
        "POST",
        "/api/v1/campaigns",
        user="operator1",
        data={
            "title": marker,
            "starts_at": (now + timedelta(minutes=10)).isoformat(),
            "ends_at": (now + timedelta(days=1)).isoformat(),
            "capacity": 4,
        },
    )
    for index in range(2):
        p.ok(
            "donantes",
            "POST",
            "/api/v1/campaign-slots",
            user="operator1",
            data={
                "campaign_id": campaign["id"],
                "site_id": site["id"],
                "capacity": 4,
                "starts_at": (now + timedelta(minutes=30 + index * 30)).isoformat(),
                "ends_at": (now + timedelta(minutes=45 + index * 30)).isoformat(),
            },
        )
    accounts = []
    donor_ids = []
    for index, role in enumerate(("DONOR", "OPERATOR", "DONOR", "OPERATOR")):
        username = marker.lower() + "-" + str(index)
        p.ok(
            "identidad_acceso",
            "POST",
            "/api/v1/users",
            user="admin1",
            data={
                "username": username,
                "password": p.env.state["password"],
                "tenant_id": p.env.state["tenants"][0],
                "role": role,
            },
        )
        accounts.append(
            {
                "username": username,
                "role": role,
                "mime": "application/json" if role == "DONOR" else "application/xml",
            }
        )
        if role == "DONOR":
            session = p.ok(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/login",
                user=None,
                data={
                    "username": username,
                    "password": p.env.state["password"],
                },
            )
            p.tokens[username] = session["access_token"]
            donor = p.ok(
                "donantes",
                "POST",
                "/api/v1/donors",
                user=username,
                data={
                    "folio": marker + "-" + str(index),
                    "display_name": "Persona sintética",
                    "blood_group": "O-",
                    "consent": True,
                },
            )
            donor_ids.append(donor["id"])
            p.ok(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/revoke",
                user=None,
                data={"refresh_token": session["refresh_token"]},
            )
            p.tokens.pop(username)
    with p.owner("inventario") as conn:
        before = conn.execute(
            "SELECT count(*) FROM resources WHERE folio LIKE 'LOAD-%'"
        ).fetchone()[0]
    summary = run_locust(
        p,
        tmp_path,
        workload="locust_transactions",
        users=4,
        extra_state={"load_accounts": accounts, "load_campaign": marker},
        label="transactions",
    )
    counts = summary["counts"]
    assert (
        counts["Recorrido / DONOR"]
        == counts["Citas / Reservar"]
        == counts["Citas / Cancelar"]
        > 0
    )
    assert (
        counts["Recorrido / OPERATOR"]
        == counts["Inventario / Registrar cuarentena"]
        > 0
    )
    with p.owner("donantes") as conn:
        rows = conn.execute(
            "SELECT a.id,a.status,s.status,s.version FROM appointments a JOIN appointment_slots s ON s.id=a.id WHERE a.donor_id=ANY(%s::uuid[])",
            (donor_ids,),
        ).fetchall()
        assert len(rows) == counts["Recorrido / DONOR"]
        assert all(row[1:] == ("CANCELLED", "CANCELLED", 3) for row in rows)
        ids = [str(row[0]) for row in rows]
    with p.owner("inventario") as conn:
        after, quarantined = conn.execute(
            "SELECT count(*), count(*) FILTER (WHERE status='QUARANTINE') FROM resources WHERE folio LIKE 'LOAD-%'"
        ).fetchone()
        assert after - before == counts["Recorrido / OPERATOR"]
        assert quarantined == after
    # Explicit after-load dispatch does not represent concurrent worker
    # throughput or end-to-end notification latency.
    p.drain()
    with p.owner("auditoria") as conn:
        audited = conn.execute(
            "SELECT count(DISTINCT event->>'resource_id') FROM audit_events WHERE action='APPOINTMENT_CANCEL' AND event->>'resource_id'=ANY(%s)",
            (ids,),
        ).fetchone()[0]
        assert audited == len(ids)
