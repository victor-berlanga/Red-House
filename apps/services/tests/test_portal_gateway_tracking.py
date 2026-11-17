"""I06-07 local: Chrome, Nginx HTTPS/WSS y continuidad real del monolito.

Ejecución explícita: REDHOUSE_BROWSER_TESTS=1, REDHOUSE_TEST_NGINX=<binario>,
REDHOUSE_BROWSER_RESULTS=<directorio nuevo> y Playwright local instalado.
No acepta cartografía, capacidad, MFA, GCP ni confianza CA del sistema operativo.
"""

import base64
import hashlib
import importlib.util
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
import requests
import websocket
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from redhouse.events import mongodb
from redhouse.proxy import TrustedProxy
from scripts.local import free_port
from werkzeug.serving import make_server

from .conftest import QuietHandler
from .helpers import iso
from .test_continuity import autonomous as autonomous  # noqa: PLC0414 - expose fixture
from .test_final_tracking import connect, point, receive, send
from .test_final_tracking import tracking as tracking  # noqa: PLC0414 - expose fixture
from .test_nginx_runtime import NGINX, certificate, wait_live

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "scripts/verify_portal_gateway_tracking.cjs"


def source_manifest():
    names = subprocess.check_output(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "apps/services",
            "apps/web",
            "scripts",
            "deployment",
            "data/database",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in sorted(set(names))
        if (ROOT / name).is_file()
    }


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def stop_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def start_process(args, log):
    with log.open("wb") as output:
        return subprocess.Popen(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)


def run_security_flow(
    scenario,
    p,
    web,
    tracking,
    points,
    processes,
    replica_args,
    replica_ports,
    tmp_path,
    session,
    report,
    publish,
    expect,
    reply,
    identity_baseline,
    web_revocation_baseline,
    logout_event_baseline,
    restore_identity,
):
    """Only real domain calls, process cuts and browser-owned session transitions."""
    active = {0: processes[0], 1: processes[1]}

    def restart(index):
        process = start_process(
            replica_args[index], tmp_path / f"security-restored-{index}.log"
        )
        processes.append(process)
        active[index] = process
        wait_live(f"http://127.0.0.1:{replica_ports[index]}/health/live", process)

    def stop_all():
        for index in (0, 1):
            stop_process(active[index])
        assert all(active[index].poll() is not None for index in (0, 1))
        report["all_tracking_replicas_stopped"] = True

    def health():
        result = {}
        for index in (0, 1):
            assert active[index].poll() is None
            result[str(index)] = {}
            for endpoint in ("live", "ready"):
                status = session.get(
                    f"http://127.0.0.1:{replica_ports[index]}/health/{endpoint}",
                    timeout=10,
                ).status_code
                assert status == 200
                result[str(index)][endpoint] = status
        report["final_replicas_health"] = result

    def append_points(count):
        for _ in range(count):
            points.append(point(tracking, sequence=len(points) + 1))
        report.setdefault("acks", []).extend(publish(points[-count:]))

    def prove_session_transition(*, expired=False):
        from redhouse.security import key, redis_call
        from src.integration import sessions as portal_sessions

        expected_sessions = 2 if scenario == "logout_disconnected" else 1
        user_id = p.env.state["accounts"]["transport1"]["id"]
        with p.owner("identidad_acceso") as conn:
            rows = [
                row
                for row in conn.execute(
                    "SELECT id,expires_at,revoked_at,expires_at<=now() FROM sessions WHERE user_id=%s",
                    (user_id,),
                ).fetchall()
                if str(row[0]) not in identity_baseline
            ]
            assert len(rows) == expected_sessions
            issued = conn.execute(
                "SELECT event->>'occurred_at' FROM activity_events "
                "WHERE event->>'actor_id'=%s AND event->>'action'='LOGIN' "
                "ORDER BY event->>'occurred_at' DESC LIMIT %s",
                (user_id, expected_sessions),
            ).fetchall()
            logout_events = [
                row
                for row in conn.execute(
                    "SELECT id FROM activity_events WHERE event->>'actor_id'=%s AND event->>'action'='LOGOUT'",
                    (user_id,),
                ).fetchall()
                if str(row[0]) not in logout_event_baseline
            ]
        with web.app_context(), portal_sessions.database() as conn:
            web_revocations = (
                conn.execute(
                    "SELECT count(*) FROM web_runtime.session_revocations WHERE confirmed"
                ).fetchone()[0]
                - web_revocation_baseline
            )
        with p.apps["identidad_acceso"].app_context():
            active_sessions = [
                bool(
                    redis_call(
                        lambda r, identifier=str(row[0]): r.exists(
                            key("session:" + identifier)
                        )
                    )
                )
                for row in rows
            ]
            permission_present = bool(
                redis_call(lambda r: r.exists(key("permissions:" + user_id)))
            )
        if expired:
            assert rows[0][3] and rows[0][2] is None
            assert not active_sessions[0] and not logout_events and web_revocations == 0
        else:
            assert sum(row[2] is not None for row in rows) == 1
            assert sum(active_sessions) == expected_sessions - 1
            assert len(logout_events) == 1 and web_revocations == 1
            p.drain(rounds=8)
            with p.owner("auditoria") as conn:
                assert (
                    conn.execute(
                        "SELECT count(*) FROM audit_events WHERE id=%s",
                        (logout_events[0][0],),
                    ).fetchone()[0]
                    == 1
                )
        # Session identifiers, tokens and cookies are intentionally excluded.
        report["session_transition"] = {
            "new_sessions": len(rows),
            "login_occurred_at": [row[0] for row in issued],
            "family_expires_at": [row[1].isoformat() for row in rows],
            "expired_in_sql": [row[3] for row in rows],
            "revoked_count": sum(row[2] is not None for row in rows),
            "active_redis_count": sum(active_sessions),
            "logout_events": len(logout_events),
            "confirmed_web_revocations": web_revocations,
            "permission_cache_present": permission_present,
        }
        return [str(row[0]) for row in rows]

    expect("initial_publish")
    append_points(1)
    reply("initial_publish", eventId=points[0]["event_id"])
    if scenario == "cursor_resync":
        expect("cursor_stop")
        stop_all()
        reply("cursor_stop")
        expect("cursor_gap")
        restart(1)
        time.sleep(2.1)
        append_points(3)
        reply("cursor_gap", eventIds=[value["event_id"] for value in points])
        expect("cursor_continue")
        append_points(1)
        reply("cursor_continue", eventId=points[-1]["event_id"])
        expect("restore_second")
        restart(0)
        health()
        reply("restore_second")
    elif scenario == "logout_disconnected":
        expect("logout_stop")
        stop_all()
        reply("logout_stop")
        expect("verify_logout")
        prove_session_transition()
        reply("verify_logout")
        expect("restore_authorized")
        report["recovery_timeline"] = [
            {
                "phase": "replica_b_restore_requested",
                "at_utc": datetime.now(UTC).isoformat(),
            }
        ]
        restart(1)
        report["recovery_timeline"].append(
            {
                "phase": "replica_b_direct_live_200",
                "at_utc": datetime.now(UTC).isoformat(),
            }
        )
        reply("restore_authorized")
        expect("publish_for_authorized")
        report["recovery_timeline"].append(
            {
                "phase": "new_authorized_native_socket_ready",
                "at_utc": datetime.now(UTC).isoformat(),
            }
        )
        append_points(2)
        report["recovery_timeline"].append(
            {"phase": "later_positions_acked", "at_utc": datetime.now(UTC).isoformat()}
        )
        reply(
            "publish_for_authorized", eventIds=[value["event_id"] for value in points]
        )
        expect("restore_second")
        restart(0)
        health()
        reply("restore_second")
    elif scenario == "logout_live":
        expect("verify_logout")
        prove_session_transition()
        reply("verify_logout")
        expect("publish_after_logout")
        append_points(2)
        health()
        reply("publish_after_logout", eventIds=[value["event_id"] for value in points])
    else:
        assert scenario == "session_expiry"
        expect("await_expiry")
        reply("await_expiry")
        # Test orchestration only: the actual family lifetime is 90 s, without clock changes.
        expect("verify_expiry", timeout=150)
        expired_families = prove_session_transition(expired=True)
        report["expiry_guards"]["family_expiry_verified"] = True
        # Device-kind authorization reads its own credential key and SQL device,
        # user/tenant/assignment state, without the human JWT permission cache.
        # Still require actual correlated PERSISTED_SQL ACKs before any repair login.
        append_points(2)
        report["expiry_guards"]["post_expiry_device_acks_verified"] = True
        report["post_expiry_acks_before_fixture_restore"] = report["acks"][-2:]
        health()
        reply(
            "verify_expiry",
            eventIds=[value["event_id"] for value in points],
            familyExpiresAt=report["session_transition"]["family_expires_at"][0],
        )
        expect("restore_fixture_identity")
        restore_identity(phase="after_expiry_assertions")
        with p.owner("identidad_acceso") as conn:
            for identifier in expired_families:
                assert conn.execute(
                    "SELECT expires_at<=now() AND revoked_at IS NULL FROM sessions WHERE id=%s",
                    (identifier,),
                ).fetchone()[0]
        with p.apps["identidad_acceso"].app_context():
            from redhouse.security import key, redis_call

            assert all(
                not redis_call(
                    lambda r, identifier=identifier: r.exists(
                        key("session:" + identifier)
                    )
                )
                for identifier in expired_families
            )
        report["expired_family_still_dead_after_fixture_login"] = True
        report["expiry_guards"]["old_family_rechecked_after_fixture_login"] = True
        reply("restore_fixture_identity")


REMAINING_SCENARIOS = ("assignment_disconnected", "role_live_gateway")


def remaining_call(p, service, method, path, **kwargs):
    response = p.request(service, method, path, **kwargs)
    assert response.status_code < 300, (service, method, response.status_code)
    return response.json()["data"]


def remaining_relation(p, tracking, state, target):
    """Controlled fixture fault only; not an administrative reassignment API."""
    with p.owner("transporte") as conn:
        current = conn.execute(
            "SELECT transport_user_id,version FROM shipments WHERE id=%s FOR UPDATE",
            (tracking["shipment"]["id"],),
        ).fetchone()
        assert (str(current[0]), current[1]) == state["relation_current"]
        updated = conn.execute(
            "UPDATE shipments SET transport_user_id=%s,version=version+1 "
            "WHERE id=%s AND transport_user_id=%s AND version=%s RETURNING version",
            (target, tracking["shipment"]["id"], current[0], current[1]),
        ).fetchone()
        assert updated and updated[0] == current[1] + 1
    state["relation_current"] = (str(target), updated[0])
    return updated[0]


def prepare_remaining(p, tracking, scenario, state, report, secrets_to_hide):
    with p.owner("identidad_acceso") as conn:
        state["sessions_before"] = {
            str(r[0]) for r in conn.execute("SELECT id FROM sessions")
        }
        state["operator"] = p.env.state["accounts"]["operator1"]["id"]
        state["role_before"] = conn.execute(
            "SELECT role,version FROM users WHERE id=%s", (state["operator"],)
        ).fetchone()
        state["role_events_before"] = {
            str(r[0])
            for r in conn.execute(
                "SELECT id FROM activity_events WHERE event->>'resource_id'=%s "
                "AND event->>'action'='USER_ROLE_CHANGED'",
                (state["operator"],),
            )
        }
    state["reason"] = "Cambio de perfil sintético I06 " + uuid4().hex[:12]
    report["effective_test_policy"] = {
        name: {
            k: app.config.get(k)
            for k in (
                "TESTING",
                "RATE_LIMIT",
                "INTERNAL_RATE_LIMIT",
                "MFA_REQUIRED_ROLES",
            )
        }
        for name, app in p.apps.items()
    }
    if scenario == "role_live_gateway":
        assert state["role_before"][0] == "OPERATOR"
        return
    assert scenario == "assignment_disconnected"
    with p.owner("transporte") as conn:
        row = conn.execute(
            "SELECT transport_user_id,version FROM shipments WHERE id=%s",
            (tracking["shipment"]["id"],),
        ).fetchone()
    state["relation_before"] = state["relation_current"] = (str(row[0]), row[1])
    assert str(row[0]) == p.env.state["accounts"]["transport1"]["id"]
    state["original_emitter"] = (tracking["device"], tracking["credential"])
    user = remaining_call(
        p,
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": "i06_transport_" + uuid4().hex[:12],
            "password": p.env.state["password"],
            "tenant_id": tracking["shipment"]["origin_id"],
            "role": "TRANSPORT",
        },
    )
    state["replacement_user"] = user
    device = remaining_call(
        p,
        "identidad_acceso",
        "POST",
        "/api/v1/devices",
        user="admin1",
        data={
            "id": str(uuid4()),
            "user_id": user["id"],
            "source": "SIMULATOR",
            "label": "Relevo sintético I06",
            "expires_at": iso(days=1),
        },
    )
    state["replacement_device"] = device
    credential = remaining_call(
        p,
        "identidad_acceso",
        "POST",
        f"/api/v1/devices/{device['id']}/credentials",
        user="admin1",
        data={
            "version": device["version"],
            "human_confirmation": True,
            "reason": "Credencial sintética para fallo aislado I06",
        },
    )
    state["replacement_credential"] = credential
    secrets_to_hide.append(credential["credential"])
    # Prepare the valid alternate assignment before any observer or outage. Restore
    # the original responsible before Chrome sees the first point.
    version = remaining_relation(p, tracking, state, user["id"])
    try:
        state["replacement_assignment"] = remaining_call(
            p,
            "transporte",
            "POST",
            f"/api/v1/shipments/{tracking['shipment']['id']}/tracking/assignments",
            user="coordinator1",
            data={
                "device_id": device["id"],
                "version": version,
                "starts_at": iso(minutes=-5),
                "ends_at": iso(minutes=60),
                "human_confirmation": True,
                "reason": "Asignación previa al fallo controlado I06; no reasignación administrativa",
            },
        )
    finally:
        remaining_relation(p, tracking, state, state["relation_before"][0])
    report["replacement_preparation"] = {
        "one_new_account": True,
        "same_institution": True,
        "device_and_assignment_via_API": True,
        "original_responsible_restored_before_browser": True,
        "version_delta": 2,
        "administrative_reassignment": False,
    }


def remaining_sessions(p, state):
    from redhouse.security import key, redis_call

    with p.owner("identidad_acceso") as conn:
        rows = [
            r
            for r in conn.execute("SELECT id,revoked_at FROM sessions")
            if str(r[0]) not in state["sessions_before"]
        ]
        assert all(r[1] is not None for r in rows), "New browser family not revoked"
    with p.apps["identidad_acceso"].app_context():
        assert all(
            not redis_call(lambda r, sid=str(row[0]): r.exists(key("session:" + sid)))
            for row in rows
        )
    return {"new_families": len(rows), "all_revoked_sql_redis": True}


def cleanup_remaining(p, tracking, scenario, state, report):
    """Attempt each owned restoration independently; never hide a failed restore."""
    failures = []

    def attempt(name, action):
        try:
            action()
        except Exception as error:  # noqa: BLE001 - attempt every independent owned cleanup
            failures.append({"step": name, "type": type(error).__name__})

    def restore_relation():
        original = state["relation_before"][0]
        if state["relation_current"][0] != original:
            remaining_relation(p, tracking, state, original)
        with p.owner("transporte") as conn:
            row = conn.execute(
                "SELECT transport_user_id,version FROM shipments WHERE id=%s",
                (tracking["shipment"]["id"],),
            ).fetchone()
            assert (str(row[0]), row[1]) == state["relation_current"] and str(
                row[0]
            ) == original
        report["relationship_restored"] = {
            "exact_original": True,
            "monotonic_version_delta": row[1] - state["relation_before"][1],
        }

    if "relation_before" in state:
        attempt("responsible", restore_relation)
    if "original_emitter" in state:
        tracking["device"], tracking["credential"] = state["original_emitter"]
    if "replacement_assignment" in state:
        a = state["replacement_assignment"]
        attempt(
            "assignment",
            lambda: remaining_call(
                p,
                "transporte",
                "POST",
                f"/api/v1/tracking/assignments/{a['id']}/revoke",
                user="coordinator1",
                data={
                    "version": a["version"],
                    "human_confirmation": True,
                    "reason": "Cierre de ensayo sintético I06",
                },
            ),
        )
    if "replacement_device" in state:

        def revoke_device():
            d = remaining_call(
                p,
                "identidad_acceso",
                "GET",
                f"/api/v1/devices/{state['replacement_device']['id']}",
                user="admin1",
            )
            v = remaining_call(
                p,
                "identidad_acceso",
                "POST",
                f"/api/v1/devices/{d['id']}/revoke",
                user="admin1",
                data={
                    "version": d["version"],
                    "human_confirmation": True,
                    "reason": "Cierre de ensayo sintético I06",
                },
            )
            assert not v["active"]

        attempt("device", revoke_device)
    if "replacement_user" in state:

        def disable_user():
            uid = state["replacement_user"]["id"]
            with p.owner("identidad_acceso") as conn:
                version = conn.execute(
                    "SELECT version FROM users WHERE id=%s", (uid,)
                ).fetchone()[0]
            v = remaining_call(
                p,
                "identidad_acceso",
                "PATCH",
                f"/api/v1/users/{uid}",
                user="admin1",
                data={"version": version, "active": False},
            )
            assert not v["active"]

        attempt("synthetic_account", disable_user)
    if scenario == "role_live_gateway" and "role_before" in state:

        def restore_role():
            with p.owner("identidad_acceso") as conn:
                current = conn.execute(
                    "SELECT role,version FROM users WHERE id=%s", (state["operator"],)
                ).fetchone()
            if current != state["role_before"]:
                assert current == ("DONOR", state["role_before"][1] + 1)
                v = remaining_call(
                    p,
                    "identidad_acceso",
                    "POST",
                    f"/api/v1/users/{state['operator']}/role",
                    user="admin1",
                    data={
                        "role": state["role_before"][0],
                        "version": current[1],
                        "human_confirmation": True,
                        "reason": "Restauración de perfil tras ensayo sintético I06",
                    },
                )
                assert (
                    v["role"] == state["role_before"][0]
                    and v["version"] == current[1] + 1
                )
            report["role_restored"] = True

        attempt("role", restore_role)
    if "sessions_before" in state:

        def check_sessions():
            report["browser_session_cleanup"] = remaining_sessions(p, state)

        attempt("browser_sessions", check_sessions)
    report["remaining_cleanup"] = {"passed": not failures, "failures": failures}
    return not failures


def run_remaining_security_flow(
    scenario,
    p,
    tracking,
    points,
    processes,
    replica_args,
    replica_ports,
    tmp_path,
    session,
    report,
    publish,
    expect,
    reply,
    state,
):
    from redhouse.security import key, redis_call

    active = {0: processes[0], 1: processes[1]}

    def restart(index):
        process = start_process(
            replica_args[index], tmp_path / f"remaining-restored-{index}.log"
        )
        processes.append(process)
        active[index] = process
        wait_live(f"http://127.0.0.1:{replica_ports[index]}/health/live", process)

    def append(count):
        values = [point(tracking, sequence=len(points) + i + 1) for i in range(count)]
        points.extend(values)
        report.setdefault("acks", []).extend(publish(values))

    expect("initial_publish")
    append(1)
    reply("initial_publish", eventId=points[0]["event_id"])
    if scenario == "role_live_gateway":
        expect("verify_role")
        with p.owner("identidad_acceso") as conn:
            current = conn.execute(
                "SELECT role,version FROM users WHERE id=%s", (state["operator"],)
            ).fetchone()
            assert current == ("DONOR", state["role_before"][1] + 1)
            rows = conn.execute(
                "SELECT id,revoked_at FROM sessions WHERE user_id=%s",
                (state["operator"],),
            ).fetchall()
            assert rows and all(r[1] is not None for r in rows)
            events = [
                r
                for r in conn.execute(
                    "SELECT id,event->>'actor_id',event->'metadata'->>'role' FROM activity_events "
                    "WHERE event->>'resource_id'=%s AND event->>'action'='USER_ROLE_CHANGED'",
                    (state["operator"],),
                )
                if str(r[0]) not in state["role_events_before"]
            ]
            assert (
                len(events) == 1
                and events[0][1] == p.env.state["accounts"]["admin1"]["id"]
                and events[0][2] == "DONOR"
            )
        with p.apps["identidad_acceso"].app_context():
            assert all(
                not redis_call(
                    lambda r, sid=str(row[0]): r.exists(key("session:" + sid))
                )
                for row in rows
            )
        p.drain(rounds=8)
        with p.owner("auditoria") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM audit_events WHERE id=%s", (events[0][0],)
                ).fetchone()[0]
                == 1
            )
        report["role_change"] = {
            "version_delta": 1,
            "revoked_families": len(rows),
            "audit_events": 1,
            "method": "actual_portal_form_same_nginx",
        }
        reply("verify_role")
    else:
        assert scenario == "assignment_disconnected"
        expect("assignment_stop")
        for index in (0, 1):
            stop_process(active[index])
        assert all(active[i].poll() is not None for i in (0, 1))
        report["all_tracking_replicas_stopped"] = True
        reply("assignment_stop")
        expect("assignment_change")
        remaining_relation(p, tracking, state, state["replacement_user"]["id"])
        tracking["device"], tracking["credential"] = (
            state["replacement_device"],
            state["replacement_credential"],
        )
        for suffix in ("tracking/snapshot", "tracking/history"):
            assert (
                p.request(
                    "transporte",
                    "GET",
                    f"/api/v1/shipments/{tracking['shipment']['id']}/{suffix}",
                    user="transport1",
                ).status_code
                == 403
            )
        report["assignment_fault"] = {
            "method": "owner_SQL_fixture_relationship_only",
            "administrative_operation_accepted": False,
            "old_responsible_snapshot_history": [403, 403],
        }
        reply("assignment_change")
        expect("restore_authorized")
        restart(1)
        reply("restore_authorized")
    expect("publish_for_authorized")
    append(2)
    reply("publish_for_authorized", eventIds=[v["event_id"] for v in points])
    expect("remaining_restore")
    if scenario == "assignment_disconnected":
        restart(0)
    for i in (0, 1):
        assert active[i].poll() is None
        for endpoint in ("live", "ready"):
            assert (
                session.get(
                    f"http://127.0.0.1:{replica_ports[i]}/health/{endpoint}", timeout=10
                ).status_code
                == 200
            )
    report["both_replicas_healthy"] = True
    reply("remaining_restore")
    expect("remaining_finish")
    report["browser_session_cleanup"] = remaining_sessions(p, state)
    assert report["browser_session_cleanup"]["new_families"] >= 2
    reply("remaining_finish")


def run_gateway_scenario(p, tracking, request, tmp_path, scenario):
    # tracking is prepared before autonomous stops every fixture API listener.
    output = Path(os.environ["REDHOUSE_BROWSER_RESULTS"]) / (
        "portal-gateway"
        if scenario == "replica_recovery"
        else "portal-gateway-" + scenario
    )
    output.mkdir(parents=True, exist_ok=False)
    sources = source_manifest()
    write_json(output / "sources-before.json", sources)
    report = {
        "case": "I06-07" if scenario == "replica_recovery" else "I06-08",
        "scenario": scenario,
        "shipment_id": tracking["shipment"]["id"],
        "environment": {
            "directory": str(p.env.directory),
            "uid": p.env.directory.stat().st_uid,
            "mode": oct(p.env.directory.stat().st_mode & 0o777),
        },
        "passed": False,
        "checks": [],
        "scope": "Laboratorio local aislado; datos y ubicaciones sintéticos",
        "limits": [
            "No cierra I06 completo ni acredita producción, GCP o capacidad",
            "Fixture TESTING=True; cuotas de prueba 100000; no prueba MFA",
            "DONOR/TRANSPORT sin omitir MFA de roles críticos",
            "TLS Python con CA explícita; Chrome con excepción SPKI del certificado efímero",
            "No prueba confianza CA del sistema; perfiles Chrome privados efímeros",
            "Mosaicos OSM bloqueados para evitar consumo masivo; cartografía no aceptada",
            "Listeners loopback y puertos efímeros; WSGI de prueba con TrustedProxy real",
        ],
    }
    if scenario == "session_expiry":
        report["expiry_guards"] = {
            "family_expiry_verified": False,
            "post_expiry_device_acks_verified": False,
            "old_family_rechecked_after_fixture_login": False,
        }
    remaining_state = {}
    processes = []
    browser = None
    server = None
    short_identity = None
    identity_ttl_original = {}
    identity_restored = False
    session = requests.Session()
    session.trust_env = False
    secrets_to_hide = [p.env.state["password"], tracking["credential"]["credential"]]
    secrets_to_hide.extend(p.tokens.values())

    def sanitized(error):
        value = str(error)
        for secret in secrets_to_hide:
            value = value.replace(secret, "[REDACTED]")
        value = re.sub(
            r"(?:postgres(?:ql)?|redis|mongodb)://\S+", "[PRIVATE_DSN]", value
        )
        value = re.sub(
            r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[JWT]", value
        )
        value = re.sub(r"(https?://[^\s?]+)\?[^\s]+", r"\1?[REDACTED]", value)
        return value[:1500]

    def restore_identity(*, phase):
        nonlocal identity_restored
        if short_identity is None or identity_restored:
            return
        short_identity.config.update(identity_ttl_original)
        restored_auth = p.ok(
            "identidad_acceso",
            "POST",
            "/api/v1/auth/login",
            user=None,
            data={"username": "transport1", "password": p.env.state["password"]},
        )
        p.tokens["transport1"] = restored_auth["access_token"]
        secrets_to_hide.extend(
            (restored_auth["access_token"], restored_auth["refresh_token"])
        )
        identity_restored = True
        report["fixture_identity_configuration_restored"] = True
        report["fixture_identity_restore"] = {
            "method": "actual_identity_login_fixture_restore",
            "phase": phase,
            "guards_at_login": dict(report.get("expiry_guards", {})),
            "access_ttl": identity_ttl_original["ACCESS_TTL"],
            "refresh_ttl": identity_ttl_original["REFRESH_TTL"],
        }

    try:
        appointment = None
        if scenario not in REMAINING_SCENARIOS:
            donor = p.ok(
                "donantes",
                "POST",
                "/api/v1/donors",
                user="donor1",
                data={
                    "folio": "GW-" + uuid4().hex[:12],
                    "display_name": "Donante sintético gateway",
                    "blood_group": "O+",
                    "consent": True,
                },
            )
            campaign = p.ok(
                "donantes",
                "POST",
                "/api/v1/campaigns",
                user="operator1",
                data={
                    "title": "Continuidad sintética " + uuid4().hex[:8],
                    "starts_at": iso(minutes=5),
                    "ends_at": iso(days=1),
                    "capacity": 5,
                },
            )
            appointment = p.ok(
                "donantes",
                "POST",
                "/api/v1/appointments",
                user="donor1",
                data={"donor_id": donor["id"], "campaign_id": campaign["id"]},
            )
        # The reused tracking fixture starts a direct TLS helper. Close it so the
        # only external Transporte listeners in this case are the two Nginx upstreams.
        tracking["server"].shutdown()
        tracking["server"].server_close()
        assert tracking["server"].socket.fileno() == -1
        web = request.getfixturevalue("autonomous")
        web.config.update(
            PRODUCTION=True, SESSION_COOKIE_SECURE=True, HIGHCHARTS_ENABLED=False
        )
        if scenario in REMAINING_SCENARIOS:
            prepare_remaining(
                p, tracking, scenario, remaining_state, report, secrets_to_hide
            )
            report["limits"] = [
                v
                for v in report["limits"]
                if v != "DONOR/TRANSPORT sin omitir MFA de roles críticos"
            ]
        if scenario == "session_expiry":
            # Actual Identity issuance and expiry; never mutate tokens, Redis TTLs or clocks.
            short_identity = web.extensions["application_kernel"].apps[
                "identidad_acceso"
            ]
            identity_ttl_original = {
                name: short_identity.config[name]
                for name in ("ACCESS_TTL", "REFRESH_TTL")
            }
            short_identity.config.update(ACCESS_TTL=330, REFRESH_TTL=90)
            report["laboratory_ttl_seconds"] = {"access": 330, "refresh_session": 90}
        if scenario == "cursor_resync":
            report["replay_window"] = 2
            report["limits"].append(
                "Replay window 2 only in laboratory replicas; observer network offline is emulated"
            )
        server = make_server(
            "127.0.0.1",
            0,
            TrustedProxy(web, "127.0.0.1"),
            threaded=True,
            request_handler=QuietHandler,
        )
        threading.Thread(target=server.serve_forever, daemon=True).start()
        spec = importlib.util.spec_from_file_location(
            "portal_gateway_configuration", ROOT / "deployment/gcp/configure_public.py"
        )
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        (tmp_path / "apps").mkdir()
        (tmp_path / "web.json").write_text("{}")
        for service in p.urls:
            (tmp_path / "apps" / (service + ".json")).write_text("{}")
        generator.configure(tmp_path, "127.0.0.1")
        certificate(tmp_path / "tls")
        cert_path = tmp_path / "tls/fullchain.pem"
        cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
        spki = base64.b64encode(
            hashlib.sha256(
                cert.public_key().public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            ).digest()
        ).decode()
        # Only ephemeral listeners, upstream addresses, TLS paths and public port change.
        config = (tmp_path / "public.nginx.conf").read_text()
        ports = {}

        def listener(match):
            old = int(match.group(1))
            ports.setdefault(old, free_port())
            return f"listen 127.0.0.1:{ports[old]}"

        config = re.sub(r"listen (\d+)", listener, config)
        origin = f"https://127.0.0.1:{ports[8443]}"
        replica_args = []
        replica_ports = []
        for index in range(2):
            port = free_port()
            replica_ports.append(port)
            replica_config = dict(
                p.env.configs["transporte"],
                TESTING=True,
                RATE_LIMIT=100000,
                INTERNAL_RATE_LIMIT=100000,
                SERVICE_URLS=p.urls,
                WORKER_REQUIRED=False,
                TRUSTED_PROXY_ADDRESS="127.0.0.1",
                TRUSTED_PROXY_HOST="",
                TRACKING_ALLOWED_ORIGINS=[origin],
            )
            if scenario == "cursor_resync":
                replica_config["TRACKING_REPLAY_WINDOW"] = 2
            config_path = tmp_path / f"transporte-{index}.json"
            write_json(config_path, replica_config)
            config_path.chmod(0o600)
            args = [
                sys.executable,
                str(ROOT / "apps/services/run.py"),
                "transporte",
                "--config",
                str(config_path),
                "--port",
                str(port),
            ]
            replica_args.append(args)
            process = start_process(args, tmp_path / f"transporte-{index}.log")
            processes.append(process)
            wait_live(f"http://127.0.0.1:{port}/health/live", process)

        def backend(match):
            name = match.group(1).removesuffix("-private")
            if name == "web":
                port = server.server_port
            elif name.startswith("transporte-"):
                port = replica_ports[0 if name.endswith("-a") else 1]
            else:
                port = int(p.urls[name[:-2].replace("-", "_")].rsplit(":", 1)[1])
            return f"server 127.0.0.1:{port} resolve"

        config = re.sub(r"server ([a-z-]+):8080 resolve", backend, config)
        config = config.replace("/tmp/", str(tmp_path) + "/")
        config = config.replace("/etc/nginx/tls", str(tmp_path / "tls"))
        config = config.replace(
            "proxy_set_header Host 127.0.0.1;",
            f"proxy_set_header Host 127.0.0.1:{ports[8443]};",
        )
        nginx_path = tmp_path / "runtime.nginx.conf"
        nginx_path.write_text(config)
        result = subprocess.run(
            [NGINX, "-t", "-p", str(tmp_path), "-c", str(nginx_path)],
            capture_output=True,
            timeout=15,
            check=False,
        )
        assert result.returncode == 0, "Nginx rechazó la configuración aislada"
        nginx = start_process(
            [NGINX, "-p", str(tmp_path), "-c", str(nginx_path), "-g", "daemon off;"],
            tmp_path / "nginx.log",
        )
        processes.append(nginx)
        wait_live(f"http://127.0.0.1:{ports[8080]}/health/live", nginx)
        assert (
            session.get(
                origin + "/login", verify=str(cert_path), timeout=10
            ).status_code
            == 200
        )
        report["checks"].append(
            "HTTPS Nginx verificado por Python con certificado explícito"
        )
        report["generated_configuration_sha256"] = hashlib.sha256(
            config.encode()
        ).hexdigest()
        report["certificate_spki_sha256"] = spki
        target = dict(
            tracking,
            url=origin.replace("https:", "wss:")
            + "/services/transporte/ws/v1/tracking/",
            cert=str(cert_path),
        )
        points = []

        def publish(values):
            publisher = connect(target, tracking["credential"]["credential"], "device")
            try:
                receive(publisher, "authenticated")
                acks = []
                for value in values:
                    send(publisher, {"type": "position.publish", "position": value})
                    ack = receive(publisher, "position.ack")
                    assert ack["state"] == "PERSISTED_SQL"
                    assert ack["event_id"] == value["event_id"]
                    assert ack["shipment_id"] == value["shipment_id"]
                    acks.append(
                        {
                            "event_id": ack["event_id"],
                            "cursor": ack["cursor"],
                            "state": ack["state"],
                        }
                    )
                return acks
            finally:
                publisher.close()

        messages = queue.Queue()
        with (tmp_path / "node.stderr").open("wb") as error_log:
            browser = subprocess.Popen(
                ["node", str(RUNNER)],
                cwd=ROOT,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=error_log,
                text=True,
                bufsize=1,
            )

        def read_messages():
            for line in browser.stdout:
                try:
                    messages.put(json.loads(line))
                except (ValueError, TypeError):
                    messages.put({"action": "invalid_protocol"})
            messages.put({"action": "eof"})

        threading.Thread(target=read_messages, daemon=True).start()

        def reply(action, **values):
            browser.stdin.write(json.dumps({"action": action, **values}) + "\n")
            browser.stdin.flush()

        def expect(action, timeout=90):
            try:
                message = messages.get(timeout=timeout)
            except queue.Empty:
                pytest.fail("Timeout de coordinación del navegador")
            assert message.get("action") == action, "Fase inesperada: " + sanitized(
                message.get("action")
            )

        identity_baseline, logout_event_baseline, web_revocation_baseline = (
            set(),
            set(),
            0,
        )
        if scenario != "replica_recovery":
            with p.owner("identidad_acceso") as conn:
                identity_baseline = {
                    str(row[0])
                    for row in conn.execute(
                        "SELECT id FROM sessions WHERE user_id=%s",
                        (p.env.state["accounts"]["transport1"]["id"],),
                    ).fetchall()
                }
                logout_event_baseline = {
                    str(row[0])
                    for row in conn.execute(
                        "SELECT id FROM activity_events WHERE event->>'actor_id'=%s AND event->>'action'='LOGOUT'",
                        (p.env.state["accounts"]["transport1"]["id"],),
                    ).fetchall()
                }
            from src.integration import sessions as portal_sessions

            with web.app_context(), portal_sessions.database() as conn:
                web_revocation_baseline = conn.execute(
                    "SELECT count(*) FROM web_runtime.session_revocations WHERE confirmed"
                ).fetchone()[0]
        reply(
            "configure",
            scenario=scenario,
            base=origin,
            password=p.env.state["password"],
            shipment=tracking["shipment"]["id"],
            appointment=appointment["id"] if appointment else None,
            operatorId=remaining_state.get("operator"),
            roleReason=remaining_state.get("reason"),
            spki=spki,
            output=str(output),
            profiles=str(tmp_path / "chrome-profiles"),
        )
        if scenario == "replica_recovery":
            expect("initial_publish")
            points.append(point(tracking, sequence=1))
            report["initial_ack"] = publish([points[0]])
            reply("initial_publish", eventId=points[0]["event_id"])
            expect("stop_one")
            stop_process(processes[0])
            report["checks"].append("Réplica A detenida; B conserva proceso vivo")
            reply("stop_one")
            expect("single_publish")
            points.append(point(tracking, sequence=2))
            report["single_replica_ack"] = publish([points[1]])
            reply("single_publish", eventId=points[1]["event_id"])
            expect("stop_all")
            stop_process(processes[1])
            assert processes[0].poll() is not None and processes[1].poll() is not None
            failed_upgrade = session.get(
                origin + "/services/transporte/ws/v1/tracking/json",
                headers={
                    "Connection": "Upgrade",
                    "Upgrade": "websocket",
                    "Sec-WebSocket-Version": "13",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                },
                verify=str(cert_path),
                timeout=10,
            )
            assert failed_upgrade.status_code == 502
            report["all_down_gateway_status"] = failed_upgrade.status_code
            with pytest.raises((OSError, websocket.WebSocketException)):
                connect(target, p.tokens["transport1"])
            reply("stop_all")
            expect("verify_mutation")
            # The browser submits the real CSRF-protected cancellation while all APIs are off.
            assert all(process.poll() is not None for process in processes[:2])
            assert all(server.socket.fileno() == -1 for server in p.servers.values())
            with p.owner("donantes") as conn:
                status = conn.execute(
                    "SELECT status FROM appointments WHERE id=%s", (appointment["id"],)
                ).fetchone()[0]
                assert status == "CANCELLED"
                events = conn.execute(
                    "SELECT id,event->>'actor_id' FROM activity_events WHERE event->>'resource_id'=%s "
                    "AND event->>'action'='APPOINTMENT_CANCELLED'",
                    (appointment["id"],),
                ).fetchall()
                assert len(events) == 1
                assert events[0][1] == p.env.state["accounts"]["donor1"]["id"]
            p.drain(rounds=8)
            with p.owner("auditoria") as conn:
                assert (
                    conn.execute(
                        "SELECT count(*) FROM audit_events WHERE id=%s", (events[0][0],)
                    ).fetchone()[0]
                    == 1
                )
            report["autonomy"] = {
                "appointment_id": appointment["id"],
                "status": status,
                "activity_event_id": str(events[0][0]),
                "audit_count": 1,
                "all_fixture_api_listeners_closed": True,
                "direct_tracking_fixture_listener_closed": True,
            }
            reply("verify_mutation")
            expect("restore")
            restored = start_process(
                replica_args[1], tmp_path / "transporte-restored.log"
            )
            processes.append(restored)
            wait_live(f"http://127.0.0.1:{replica_ports[1]}/health/live", restored)
            time.sleep(
                2.1
            )  # Existing generated fail_timeout=2s, not an altered policy.
            points.append(point(tracking, sequence=3))
            report["recovery_acks"] = publish(
                [points[0], points[1], points[2], points[2]]
            )
            assert [ack["cursor"] for ack in report["recovery_acks"]] == [1, 2, 3, 3]
            reply("restore", eventIds=[value["event_id"] for value in points])
            expect("restore_second")
            restored_a = start_process(
                replica_args[0], tmp_path / "transporte-a-restored.log"
            )
            processes.append(restored_a)
            wait_live(f"http://127.0.0.1:{replica_ports[0]}/health/live", restored_a)
            health = {}
            for name, port, process in zip(
                ("A", "B"), replica_ports, (restored_a, restored), strict=True
            ):
                assert process.poll() is None
                health[name] = {}
                for endpoint in ("live", "ready"):
                    response = session.get(
                        f"http://127.0.0.1:{port}/health/{endpoint}", timeout=10
                    )
                    assert response.status_code == 200
                    health[name][endpoint] = response.status_code
            report["restored_replicas_health"] = health
            reply("restore_second")
            expect("complete")
            assert browser.wait(timeout=20) == 0, (
                "Navegador terminó con error; revisar browser.json sanitizado"
            )
        elif scenario in REMAINING_SCENARIOS:
            run_remaining_security_flow(
                scenario,
                p,
                tracking,
                points,
                processes,
                replica_args,
                replica_ports,
                tmp_path,
                session,
                report,
                publish,
                expect,
                reply,
                remaining_state,
            )
            expect("complete")
            assert browser.wait(timeout=20) == 0, (
                "Browser failed; inspect sanitized receipt"
            )
        else:
            run_security_flow(
                scenario,
                p,
                web,
                tracking,
                points,
                processes,
                replica_args,
                replica_ports,
                tmp_path,
                session,
                report,
                publish,
                expect,
                reply,
                identity_baseline,
                web_revocation_baseline,
                logout_event_baseline,
                restore_identity,
            )
            expect("complete")
            assert browser.wait(timeout=20) == 0, (
                "Navegador terminó con error; revisar browser.json sanitizado"
            )
        with p.owner("transporte") as conn:
            rows = conn.execute(
                "SELECT id,cursor FROM tracking_points WHERE shipment_id=%s ORDER BY cursor",
                (tracking["shipment"]["id"],),
            ).fetchall()
        assert [(str(row[0]), row[1]) for row in rows] == [
            (value["event_id"], i) for i, value in enumerate(points, 1)
        ]
        report["sql_points"] = [
            {"event_id": str(row[0]), "cursor": row[1]} for row in rows
        ]
        report["checks"].append(
            f"{len(points)} puntos SQL únicos con sus IDs y cursores esperados"
        )
        p.drain(rounds=8)
        with p.owner("transporte") as conn:
            pending_positions = conn.execute(
                "SELECT count(*) FROM outbox WHERE target='mongodb' AND delivered_at IS NULL "
                "AND event->'metadata'->'position'->>'shipment_id'=%s",
                (tracking["shipment"]["id"],),
            ).fetchone()[0]
        assert pending_positions == 0
        # Position projections are real documents in Transporte's events collection:
        # tracking.publish queues metadata.position; events.deliver_mongo stores it.
        # shipment_tracking instead projects custody-state sequences, not GPS points.
        with p.apps["transporte"].app_context(), mongodb() as client:
            database = client[p.apps["transporte"].config["MONGODB_DATABASE"]]
            projected = list(
                database.events.find(
                    {
                        "source": "transporte",
                        "metadata.position.shipment_id": tracking["shipment"]["id"],
                    },
                    {
                        "_id": 0,
                        "metadata.position.event_id": 1,
                        "metadata.position.cursor": 1,
                    },
                ).sort("metadata.position.cursor", 1)
            )
        mongo_points = [document["metadata"]["position"] for document in projected]
        assert mongo_points == report["sql_points"]
        report["mongo_projection"] = {
            "collection": "events",
            "position_field": "metadata.position",
            "points": mongo_points,
            "pending_outbox_positions": pending_positions,
        }
        report["checks"].append(
            "SQL y Mongo conservan los mismos IDs/cursores; salud de réplicas comprobada por escenario"
        )
        assert source_manifest() == sources, "Cambió una fuente durante el ensayo"
        report["passed"] = True
    except BaseException as error:
        report["failure"] = {"type": type(error).__name__, "message": sanitized(error)}
        raise
    finally:
        failed_before_cleanup = sys.exc_info()[0] is not None
        restore_failure = None
        if browser is not None:
            stop_process(browser)
            if browser.stdin is not None:
                browser.stdin.close()
            if browser.stdout is not None:
                browser.stdout.close()
        if scenario in REMAINING_SCENARIOS and not cleanup_remaining(
            p, tracking, scenario, remaining_state, report
        ):
            restore_failure = "RemainingScenarioCleanupFailure"
            report["passed"] = False
        for process in reversed(processes):
            stop_process(process)
        session.close()
        if server is not None:
            server.shutdown()
            server.server_close()
        if short_identity is not None and not identity_restored:
            # A session-scoped fixture must not retain the shortened permission-cache
            # lifetime. Restore by an actual login under its original configuration,
            # never by editing JWTs or Redis TTLs. Preserve the actual proof flags,
            # including early failures before family expiry or later publication.
            try:
                restore_identity(
                    phase="failure_cleanup"
                    if failed_before_cleanup
                    else "normal_cleanup"
                )
            except Exception as error:  # noqa: BLE001 - record cleanup failure without masking the original failure
                restore_failure = type(error).__name__
                report["passed"] = False
                report["fixture_restore_failure"] = restore_failure
        write_json(output / "sources-after.json", source_manifest())
        write_json(output / "runtime.json", report)
        if restore_failure is not None and not failed_before_cleanup:
            pytest.fail("No se pudo restaurar la sesión técnica de la fixture")


@pytest.mark.skipif(
    not NGINX or not os.environ.get("REDHOUSE_BROWSER_TESTS"),
    reason="Requiere autorización explícita de Chrome y Nginx real",
)
def test_portal_gateway_replica_loss_autonomy_and_recovery(
    p, tracking, request, tmp_path
):
    run_gateway_scenario(p, tracking, request, tmp_path, "replica_recovery")


@pytest.mark.skipif(
    not NGINX or not os.environ.get("REDHOUSE_BROWSER_TESTS"),
    reason="Requiere autorización explícita de Chrome y Nginx real",
)
@pytest.mark.parametrize(
    "scenario",
    [
        "cursor_resync",
        "logout_disconnected",
        "logout_live",
        "session_expiry",
    ],
)
def test_portal_gateway_security_states(p, tracking, request, tmp_path, scenario):
    run_gateway_scenario(p, tracking, request, tmp_path, scenario)


@pytest.mark.skipif(
    not NGINX or not os.environ.get("REDHOUSE_BROWSER_TESTS"),
    reason="Requires explicit Chrome/Nginx laboratory window",
)
@pytest.mark.parametrize("scenario", REMAINING_SCENARIOS)
def test_portal_gateway_remaining_security(p, tracking, request, tmp_path, scenario):
    run_gateway_scenario(p, tracking, request, tmp_path, scenario)
