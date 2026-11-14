"""Ejecución Locust aislada compartida por los ensayos funcionales."""

import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import redis


def verify_created_sessions_closed(before_ids, rows, user_ids, prefix, client):
    created = [row for row in rows if str(row[0]) not in before_ids]
    if len({str(row[0]) for row in created}) != len(created) or any(
        str(row[1]) not in user_ids or row[2] is None for row in created
    ):
        raise ValueError("Familias nuevas ajenas, duplicadas o no revocadas.")
    keys = [prefix + "session:" + str(row[0]) for row in created]
    if keys and any(value is not None for value in client.mget(keys)):
        raise ValueError("Sesiones nuevas todavía presentes en Redis.")
    return created


def verify_new_sessions(before_ids, rows, user_ids, prefix, client, multiplicity=1):
    if (
        not isinstance(multiplicity, int)
        or isinstance(multiplicity, bool)
        or multiplicity < 1
        or len(set(user_ids)) != len(user_ids)
    ):
        raise ValueError("Multiplicidad o identidades inválidas.")
    created = verify_created_sessions_closed(before_ids, rows, user_ids, prefix, client)
    if (
        len(created) != len(user_ids) * multiplicity
        or len({str(row[0]) for row in created}) != len(created)
        or Counter(str(row[1]) for row in created)
        != Counter({user_id: multiplicity for user_id in user_ids})
        or any(row[2] is None for row in created)
    ):
        raise ValueError("Familias nuevas incompletas o no revocadas.")


def transaction_site_matches(row, fixture):
    """La sede de agenda pertenece al catálogo vigente, no a red_house.site."""
    return row is not None and (str(row[0]), *row[1:]) == (
        fixture["tenant_id"],
        "sites",
        fixture["prefix"],
        None,
        {"municipality": "Monterrey", "address": "Dirección sintética"},
        True,
        1,
    )


def transaction_campaign_matches(row, fixture):
    """Compara instantes completos; PostgreSQL puede devolver otra zona horaria."""
    return row is not None and (row[0], str(row[1]), *row[2:]) == (
        fixture["prefix"],
        fixture["tenant_id"],
        datetime.fromisoformat(fixture["starts_at"]),
        datetime.fromisoformat(fixture["ends_at"]),
        6,
        "OPEN",
    )


def prepare_transaction_fixture(env):
    """Fixture mínima una vez por dataset; SQL de preparación, jamás carga medida."""
    from scripts.local import private_file
    from scripts.prepare_load import validate_environment

    validate_environment(env)
    path = env.directory / "transaction-fixture.json"
    if not path.exists():
        now = datetime.now(timezone.utc)
        prefix = "tx-" + uuid4().hex[:10]
        tenant = env.state["tenants"][0]
        fixture = {
            "directory": str(env.directory),
            "prefix": prefix,
            "tenant_id": tenant,
            "campaign_id": str(uuid4()),
            "site_id": str(uuid4()),
            "profile_id": str(uuid4()),
            "slot_ids": [str(uuid4()), str(uuid4())],
            "starts_at": (now + timedelta(days=1)).isoformat(),
            "ends_at": (now + timedelta(days=2)).isoformat(),
            "effective_at": (now - timedelta(minutes=1)).isoformat(),
            "notice": "Fixture SQL sintética; fuera de métricas API; sin autorización clínica",
            "accounts": [],
        }
        for index in range(12):
            role = "DONOR" if index % 2 == 0 else "OPERATOR"
            fixture["accounts"].append(
                {
                    "id": str(uuid4()),
                    "username": prefix + "-" + str(index),
                    "tenant_id": tenant,
                    "role": role,
                    "donor_id": str(uuid4()) if role == "DONOR" else None,
                    "mime": "application/json"
                    if role == "DONOR"
                    else "application/xml",
                }
            )
        private_file(path, json.dumps(fixture, indent=2) + "\n")
    fixture = json.loads(path.read_text())
    accounts = fixture["accounts"]
    if (
        fixture["directory"] != str(env.directory)
        or fixture["tenant_id"] != env.state["tenants"][0]
        or len(accounts) != 12
        or len({a["id"] for a in accounts}) != 12
        or Counter(a["role"] for a in accounts) != {"DONOR": 6, "OPERATOR": 6}
        or datetime.fromisoformat(fixture["starts_at"])
        <= datetime.now(timezone.utc) + timedelta(minutes=15)
    ):
        raise ValueError("Fixture transaccional ajena, vencida o incompleta")
    # provision.py builds laboratory owner DSNs from rh_bootstrap/admin_url,
    # not the restricted runtime rh_<service> credentials. One transaction
    # preserves the complete seed; validate_environment above checks ownership.
    with psycopg.connect(env.state["database_owners"]["identidad_acceso"]) as conn:
        password_hash = conn.execute(
            "SELECT password_hash FROM users WHERE id=%s AND role='OPERATOR' AND active",
            (env.state["accounts"]["operator1"]["id"],),
        ).fetchone()[0]
        existing = conn.execute(
            "SELECT id,username,tenant_id,role,active,password_hash FROM users WHERE id=ANY(%s::uuid[])",
            ([a["id"] for a in accounts],),
        ).fetchall()
        if not existing:
            for account in accounts:
                conn.execute(
                    "INSERT INTO users(id,tenant_id,username,password_hash,role) VALUES(%s,%s,%s,%s,%s)",
                    (
                        account["id"],
                        account["tenant_id"],
                        account["username"],
                        password_hash,
                        account["role"],
                    ),
                )
                if account["donor_id"]:
                    conn.execute(
                        "INSERT INTO access_donantes.donors(id,tenant_id,user_id,folio,display_name,blood_group,consent,status) "
                        "VALUES(%s,%s,%s,%s,'Persona sintética','O-',true,'PRELIMINARY')",
                        (
                            account["donor_id"],
                            account["tenant_id"],
                            account["id"],
                            account["username"],
                        ),
                    )
            conn.execute(
                "INSERT INTO access_identidad_acceso.catalogue(id,tenant_id,kind,name,details) "
                "VALUES(%s,%s,'sites',%s,%s::jsonb)",
                (
                    fixture["site_id"],
                    fixture["tenant_id"],
                    fixture["prefix"],
                    json.dumps(
                        {"municipality": "Monterrey", "address": "Dirección sintética"}
                    ),
                ),
            )
            conn.execute(
                "INSERT INTO access_donantes.campaigns(id,tenant_id,title,starts_at,ends_at,capacity) VALUES(%s,%s,%s,%s,%s,6)",
                (
                    fixture["campaign_id"],
                    fixture["tenant_id"],
                    fixture["prefix"],
                    fixture["starts_at"],
                    fixture["ends_at"],
                ),
            )
            for index, identifier in enumerate(fixture["slot_ids"]):
                start = datetime.fromisoformat(fixture["starts_at"]) + timedelta(
                    minutes=index * 30
                )
                conn.execute(
                    "INSERT INTO access_donantes.campaign_slots(id,campaign_id,tenant_id,site_id,starts_at,ends_at,capacity) "
                    "VALUES(%s,%s,%s,%s,%s,%s,6)",
                    (
                        identifier,
                        fixture["campaign_id"],
                        fixture["tenant_id"],
                        fixture["site_id"],
                        start,
                        start + timedelta(minutes=15),
                    ),
                )
            conn.execute(
                "INSERT INTO access_compatibilidad.lab_profiles(id,tenant_id,name,kind,component,version,required_tests,source,synthetic,author_id,effective_at) "
                "VALUES(%s,%s,%s,'BLOOD','RBC',1,'[\"ABO\"]'::jsonb,'Fixture académica de carga',true,%s,%s)",
                (
                    fixture["profile_id"],
                    fixture["tenant_id"],
                    fixture["prefix"],
                    env.state["accounts"]["medical1"]["id"],
                    fixture["effective_at"],
                ),
            )
        rows = conn.execute(
            "SELECT id,username,tenant_id,role,active,password_hash FROM users WHERE id=ANY(%s::uuid[])",
            ([a["id"] for a in accounts],),
        ).fetchall()
        expected = {
            (a["id"], a["username"], a["tenant_id"], a["role"], True, password_hash)
            for a in accounts
        }
        if {(str(r[0]), r[1], str(r[2]), *r[3:]) for r in rows} != expected:
            raise ValueError("Las cuentas existentes no corresponden a la fixture")
        for a in accounts:
            if a["donor_id"] and conn.execute(
                "SELECT user_id,tenant_id,status FROM access_donantes.donors WHERE id=%s",
                (a["donor_id"],),
            ).fetchone() != (UUID(a["id"]), UUID(a["tenant_id"]), "PRELIMINARY"):
                raise ValueError("Expediente sintético cambiado")
        site = conn.execute(
            "SELECT tenant_id,kind,name,parent_id,details,active,version "
            "FROM access_identidad_acceso.catalogue WHERE id=%s",
            (fixture["site_id"],),
        ).fetchone()
        if not transaction_site_matches(site, fixture):
            raise ValueError("Sede sintética del catálogo ausente o cambiada")
        campaign = conn.execute(
            "SELECT title,tenant_id,starts_at,ends_at,capacity,status FROM access_donantes.campaigns WHERE id=%s",
            (fixture["campaign_id"],),
        ).fetchone()
        if not transaction_campaign_matches(campaign, fixture):
            raise ValueError("Campaña sintética cambiada")
        slots = conn.execute(
            "SELECT id,campaign_id,tenant_id,site_id,capacity,active,starts_at,ends_at FROM access_donantes.campaign_slots WHERE campaign_id=%s",
            (fixture["campaign_id"],),
        ).fetchall()
        if {tuple(str(v) for v in r[:4]) + tuple(r[4:]) for r in slots} != {
            (
                i,
                fixture["campaign_id"],
                fixture["tenant_id"],
                fixture["site_id"],
                6,
                True,
                datetime.fromisoformat(fixture["starts_at"])
                + timedelta(minutes=index * 30),
                datetime.fromisoformat(fixture["starts_at"])
                + timedelta(minutes=index * 30 + 15),
            )
            for index, i in enumerate(fixture["slot_ids"])
        }:
            raise ValueError("Horarios sintéticos cambiados")
        profile = conn.execute(
            "SELECT tenant_id,kind,component,version,synthetic,clinical_enabled,rule_status FROM access_compatibilidad.lab_profiles WHERE id=%s",
            (fixture["profile_id"],),
        ).fetchone()
        if not profile or (str(profile[0]), *profile[1:]) != (
            fixture["tenant_id"],
            "BLOOD",
            "RBC",
            1,
            True,
            False,
            "DRAFT",
        ):
            raise ValueError("Perfil académico cambiado")
        if conn.execute(
            "SELECT 1 FROM access_compatibilidad.rule_actions WHERE profile_id=%s UNION ALL "
            "SELECT 1 FROM access_compatibilidad.lab_profiles WHERE supersedes=%s",
            (fixture["profile_id"], fixture["profile_id"]),
        ).fetchone():
            raise ValueError("El perfil académico tiene decisiones o sucesor")
    return fixture


def transaction_commits(env, accounts):
    ids = [a["id"] for a in accounts]
    with psycopg.connect(env.state["database_owners"]["identidad_acceso"]) as conn:
        rows = conn.execute(
            "SELECT service,user_id,key,operation,result FROM red_house.service_idempotency "
            "WHERE user_id=ANY(%s::uuid[])",
            (ids,),
        ).fetchall()
    return {
        (service, str(user), key): {"operation": operation, "result": result}
        for service, user, key, operation, result in rows
    }


def reconcile_transaction_log(events, commits, accounts):
    """Oráculo puro: cada intento queda confirmado, no confirmado o incoherente."""
    owners = {a["id"]: a for a in accounts}
    intents, responses, cycles, endings = {}, {}, {}, {}
    replays, replay_responses = set(), set()
    errors = []
    for event in events:
        user, cycle = event["user_id"], event["cycle"]
        if (
            user not in owners
            or event["tenant_id"] != owners[user]["tenant_id"]
            or event["role"] != owners[user]["role"]
        ):
            errors.append("trace_identity")
            continue
        slot = (user, cycle)
        kind = event["kind"]
        if kind == "cycle_start":
            if slot in cycles:
                errors.append("duplicate_cycle")
            cycles[slot] = event
        elif kind == "cycle_end":
            if slot not in cycles or slot in endings:
                errors.append("invalid_cycle_end")
            endings[slot] = event
        elif kind == "intent":
            key = (event["service"], user, event["key"])
            if key in intents or slot not in cycles:
                errors.append("duplicate_or_orphan_intent")
            intents[key] = event
        elif kind in ("response", "replay_intent", "replay_response"):
            matches = [k for k in intents if k[1:] == (user, event["key"])]
            if len(matches) != 1:
                errors.append("orphan_response")
                continue
            key = matches[0]
            if kind == "response":
                if key in responses:
                    errors.append("duplicate_response")
                responses[key] = event["result"]
            elif kind == "replay_intent":
                replays.add(key)
            else:
                replay_responses.add(key)
                if event["result"] != responses.get(key):
                    errors.append("replay_mismatch")
        else:
            errors.append("unknown_trace_event")
    if set(commits) - set(intents):
        errors.append("untracked_commit")
    expected = {"appointments": {}, "resources": {}, "samples": {}}
    audit, alerts = set(), set()
    for key, intent in intents.items():
        commit = commits.get(key)
        if not commit:
            if key in responses:
                errors.append("response_without_commit")
            continue
        result, operation = commit["result"], commit["operation"]
        body, tenant, user = intent["body"], intent["tenant_id"], intent["user_id"]
        if key in responses and responses[key] != result:
            errors.append("response_commit_mismatch")
        identifier = result.get("id")
        if not identifier or result.get("tenant_id") != tenant:
            errors.append("commit_scope")
            continue
        base = {"id": identifier, "tenant_id": tenant}
        if (
            intent["path"] == "/api/v1/appointments"
            and operation == "appointment_create"
        ):
            if (
                result.get("donor_id") != owners[user]["donor_id"]
                or result.get("donor_id") != body["donor_id"]
                or result.get("campaign_id") != body["campaign_id"]
            ):
                errors.append("appointment_correlation")
            expected["appointments"][identifier] = {
                **base,
                "user_id": user,
                "status": "BOOKED",
                "version": 1,
                "slot_id": body["slot_id"],
            }
            action = "APPOINTMENT_BOOKED"
            alerts.add((identifier, user))
        elif (
            operation == "appointment_command:" + identifier
            and intent["path"] == "/api/v1/appointments/" + identifier + "/commands"
        ):
            current = expected["appointments"].get(identifier)
            if (
                not current
                or current["user_id"] != user
                or body["version"] != current["version"]
            ):
                errors.append("appointment_version")
                continue
            if result.get("version") != body["version"] + 1:
                errors.append("appointment_response_version")
            if body["action"] == "RESCHEDULE":
                current.update(version=body["version"] + 1, slot_id=body["slot_id"])
            elif body["action"] == "CANCEL":
                current.update(version=body["version"] + 1, status="CANCELLED")
            else:
                errors.append("unexpected_appointment_action")
            if any(
                result.get(f) != current[f] for f in ("slot_id", "status", "version")
            ):
                errors.append("appointment_response_state")
            action = "APPOINTMENT_" + body["action"]
        elif operation == "resource_create" and intent["path"] == "/api/v1/resources":
            if (
                result.get("folio") != body["folio"]
                or result.get("status") != "QUARANTINE"
            ):
                errors.append("resource_correlation")
            expected["resources"][identifier] = {
                **base,
                "folio": body["folio"],
                "status": "QUARANTINE",
                "actor_id": user,
            }
            action = "RESOURCE_CREATED"
        elif (
            operation == "lab_sample_create"
            and intent["path"] == "/api/v1/laboratory/samples"
        ):
            if any(
                result.get(f) != body[f]
                for f in ("resource_id", "profile_id", "identifier")
            ):
                errors.append("sample_correlation")
            expected["samples"][identifier] = {
                **base,
                "resource_id": body["resource_id"],
                "profile_id": body["profile_id"],
                "identifier": body["identifier"],
                "status": "REQUESTED",
                "version": 1,
                "author_id": user,
            }
            action = "LAB_SAMPLE_REQUESTED"
        elif (
            operation == "lab_sample_receive:" + identifier
            and intent["path"]
            == "/api/v1/laboratory/samples/" + identifier + "/receive"
        ):
            current = expected["samples"].get(identifier)
            if (
                not current
                or current["author_id"] != user
                or body["version"] != current["version"]
                or body["decision"] != "RECEIVED"
            ):
                errors.append("sample_version")
                continue
            current.update(status="RECEIVED", version=body["version"] + 1)
            if (
                result.get("status") != "RECEIVED"
                or result.get("version") != current["version"]
            ):
                errors.append("sample_response_state")
            action = "LAB_SAMPLE_RECEIVED"
        else:
            errors.append("unexpected_operation")
            continue
        audit.add((key[0], action, identifier, user))
    completed = Counter()
    for slot, start in cycles.items():
        end = endings.get(slot)
        writes = [
            k
            for k, value in intents.items()
            if (value["user_id"], value["cycle"]) == slot
        ]
        if end and end["success"]:
            if len(writes) != 3 or any(
                k not in commits or k not in responses for k in writes
            ):
                errors.append("incomplete_successful_cycle")
            else:
                completed[start["role"]] += 1
    return {
        "errors": errors,
        "intents": intents,
        "expected": expected,
        "audit": audit,
        "alerts": alerts,
        "committed": len(set(intents) & set(commits)),
        "not_committed": len(set(intents) - set(commits)),
        "response_lost_committed": len(set(commits) & set(intents) - set(responses)),
        "incomplete_cycles": sum(
            slot not in endings or not endings[slot]["success"] for slot in cycles
        ),
        "completed": dict(completed),
        "cycles": cycles,
        "endings": endings,
        "replays": len(replays & replay_responses),
        "unconfirmed_replays": len(replays - replay_responses),
    }


def verify_transaction_persistence(env, output, accounts, before, *, wait_seconds=30):
    events, files = [], sorted(output.glob("attempts-*.jsonl"))
    trace_errors = []
    for path in files:
        for line in path.read_text().splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                trace_errors.append("truncated_trace")
    after = transaction_commits(env, accounts)
    if any(after.get(k) != v for k, v in before.items()):
        trace_errors.append("prior_commit_changed")
    delta = {k: v for k, v in after.items() if k not in before}
    result = reconcile_transaction_log(events, delta, accounts)
    errors = result["errors"] + trace_errors
    if len(files) != 12:
        errors.append("missing_user_trace")
    with psycopg.connect(env.state["database_owners"]["identidad_acceso"]) as conn:
        users = [a["id"] for a in accounts]
        # Detect extra effects even when a faulty replay returns the original ID.
        all_ids = {
            "appointments": {
                str(r[0])
                for r in conn.execute(
                    "SELECT a.id FROM access_donantes.appointments a JOIN access_donantes.donors d ON d.id=a.donor_id WHERE d.user_id=ANY(%s::uuid[])",
                    (users,),
                )
            },
            "resources": {
                str(r[0])
                for r in conn.execute(
                    "SELECT resource_id FROM access_inventario.movements WHERE action='CREATED' AND actor_id=ANY(%s::uuid[])",
                    (users,),
                )
            },
            "samples": {
                str(r[0])
                for r in conn.execute(
                    "SELECT id FROM access_compatibilidad.lab_samples WHERE author_id=ANY(%s::uuid[])",
                    (users,),
                )
            },
        }
        for kind, operation in (
            ("appointments", "appointment_create"),
            ("resources", "resource_create"),
            ("samples", "lab_sample_create"),
        ):
            known = {
                c["result"]["id"] for c in after.values() if c["operation"] == operation
            }
            if all_ids[kind] != known:
                errors.append("untracked_" + kind)
        for identifier, expected in result["expected"]["appointments"].items():
            row = conn.execute(
                "SELECT a.id,a.tenant_id,d.user_id,a.status,s.version,s.slot_id FROM access_donantes.appointments a "
                "JOIN access_donantes.donors d ON d.id=a.donor_id JOIN access_donantes.appointment_slots s ON s.id=a.id WHERE a.id=%s",
                (identifier,),
            ).fetchone()
            actual = (
                dict(
                    zip(
                        ("id", "tenant_id", "user_id", "status", "version", "slot_id"),
                        [str(x) if isinstance(x, UUID) else x for x in row],
                    )
                )
                if row
                else {}
            )
            if actual != expected:
                errors.append("appointment_persistence")
        for identifier, expected in result["expected"]["resources"].items():
            rows = conn.execute(
                "SELECT r.id,r.tenant_id,r.folio,r.status,m.actor_id FROM access_inventario.resources r "
                "JOIN access_inventario.movements m ON m.resource_id=r.id AND m.action='CREATED' WHERE r.id=%s",
                (identifier,),
            ).fetchall()
            actual = (
                dict(
                    zip(
                        ("id", "tenant_id", "folio", "status", "actor_id"),
                        [str(x) if isinstance(x, UUID) else x for x in rows[0]],
                    )
                )
                if len(rows) == 1
                else {}
            )
            if actual != expected:
                errors.append("resource_persistence")
        for identifier, expected in result["expected"]["samples"].items():
            row = conn.execute(
                "SELECT id,tenant_id,resource_id,profile_id,identifier,status,version,author_id FROM access_compatibilidad.lab_samples WHERE id=%s",
                (identifier,),
            ).fetchone()
            actual = (
                dict(
                    zip(
                        (
                            "id",
                            "tenant_id",
                            "resource_id",
                            "profile_id",
                            "identifier",
                            "status",
                            "version",
                            "author_id",
                        ),
                        [str(x) if isinstance(x, UUID) else x for x in row],
                    )
                )
                if row
                else {}
            )
            if actual != expected:
                errors.append("sample_persistence")
    # Workers continue normally; observe bounded convergence, never manually dispatch.
    deadline, propagation_started = time.monotonic() + wait_seconds, time.monotonic()
    identifiers = [i for kind in result["expected"].values() for i in kind]
    while True:
        with psycopg.connect(env.state["database_owners"]["auditoria"]) as conn:
            audit = Counter(
                (r[0], r[1], r[2], str(r[3]))
                for r in conn.execute(
                    "SELECT source,action,event->>'resource_id',actor_id FROM audit_events WHERE event->>'resource_id'=ANY(%s::text[])",
                    (identifiers,),
                ).fetchall()
            )
        with psycopg.connect(env.state["database_owners"]["alertas"]) as conn:
            alerts = Counter(
                (r[0], str(r[1]))
                for r in conn.execute(
                    "SELECT resource_id,target_user_id FROM alerts WHERE message_code='APPOINTMENT_BOOKED' AND target_role='DONOR' AND resource_id=ANY(%s::text[])",
                    (identifiers,),
                ).fetchall()
            )
        if all(audit[k] == 1 for k in result["audit"]) and alerts == Counter(
            {k: 1 for k in result["alerts"]}
        ):
            break
        if time.monotonic() >= deadline:
            errors.append("event_propagation")
            break
        time.sleep(0.5)
    report = {
        k: result[k]
        for k in (
            "committed",
            "not_committed",
            "response_lost_committed",
            "incomplete_cycles",
            "completed",
            "replays",
            "unconfirmed_replays",
        )
    }
    measured_completed = Counter(
        start["role"]
        for slot, start in result["cycles"].items()
        if start["stage"] == "measuring"
        and (end := result["endings"].get(slot))
        and end["stage"] == "measuring"
        and end["success"]
    )
    report.update(
        errors=errors,
        attempted=len(result["intents"]),
        trace_files=len(files),
        measured_completed=dict(measured_completed),
        persistence_verified=not errors,
        event_wait_seconds=time.monotonic() - propagation_started,
        pending=[
            {"service": k[0], "user_id": k[1], "key": k[2]}
            for k in result["intents"]
            if k not in delta
        ],
    )
    (output / "reconciliation.private.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    (output / "reconciliation.private.json").chmod(0o600)
    return report


def run_locust(
    platform,
    tmp_path,
    *,
    workload="locustfile",
    users=6,
    extra_state=None,
    label="smoke",
    user_ids,
):
    root = Path(__file__).resolve().parents[1]
    private = tmp_path / "load"
    private.mkdir(mode=0o700)
    state = private / "state.json"
    state.write_text(
        json.dumps(
            {
                "directory": str(private),
                "urls": platform.urls,
                "password": platform.env.state["password"],
                **(extra_state or {}),
            }
        )
    )
    state.chmod(0o600)
    # Early rotation is deliberate; this smoke does not claim JWT expiration.
    base_import = (
        "from locustfile import RegionalUser"
        if workload == "locustfile"
        else "from locust_transactions import TransactionUser as RegionalUser"
    )
    (private / "probe.py").write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(root / 'tests')!r})\n"
        f"{base_import}\n"
        "class RenewalProbe(RegionalUser):\n"
        "    def on_start(self):\n"
        "        super().on_start()\n"
        "        self.api.renew_at = self.api.clock() + 2\n"
    )
    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(private / "probe.py"),
        "--headless",
        "--users",
        str(users),
        "--spawn-rate",
        "2",
        "--run-time",
        "12s",
        "--stop-timeout",
        "30",
        "--host",
        "http://127.0.0.1",
        "--csv",
        str(private / "smoke"),
        "--csv-full-history",
        "--json-file",
        str(private / "smoke-final"),
        "--exit-code-on-error",
        "1",
        "--only-summary",
        "RenewalProbe",
    ]
    env = {
        **os.environ,
        "REDHOUSE_LOAD_ISOLATED": "1",
        "REDHOUSE_LOAD_STATE": str(state),
    }
    env.pop("REDHOUSE_LOAD_NO_CACHE", None)
    if len(user_ids) != users or len(set(user_ids)) != users:
        raise ValueError("La carga exige una cuenta distinta por usuario.")

    def session_rows():
        with platform.owner("identidad_acceso") as conn:
            return conn.execute(
                "SELECT id,user_id,revoked_at FROM sessions WHERE user_id=ANY(%s::uuid[])",
                (user_ids,),
            ).fetchall()

    before_ids = {str(row[0]) for row in session_rows()}
    result = subprocess.run(
        command,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=75,
        check=False,
    )
    (private / "runner.private.log").write_text(result.stdout + result.stderr)
    summary = {"runner_exit": result.returncode, "users": users, "seconds": 12}
    # El revoke responde uniformemente; verificar familias nuevas en las dos
    # autoridades del fixture, excluyendo las sesiones que ya existían.
    verification_error = None
    try:
        prefix = platform.apps["identidad_acceso"].config["REDIS_PREFIX"]
        with redis.Redis.from_url(
            platform.env.state["redis_admin"], socket_timeout=3
        ) as client:
            verify_new_sessions(before_ids, session_rows(), user_ids, prefix, client)
        summary["session_revocation_verified"] = True
    except Exception:  # noqa: BLE001 - resultados públicos no incluyen detalles de conexión
        verification_error = (
            "No se comprobó la revocación de todas las sesiones nuevas."
        )
        summary["session_revocation_verified"] = False
    # CSV is periodic and can precede test_stop. Locust writes this final JSON
    # after runner.quit(), including the coordinated revocations.
    if (private / "smoke-final.json").exists():
        rows = json.loads((private / "smoke-final.json").read_text())
        counts = {row["name"]: int(row["num_requests"]) for row in rows}
        failures = sum(int(row["num_failures"]) for row in rows)
        summary.update(counts=counts, failures=failures)
    output = os.environ.get("REDHOUSE_LOAD_OUTPUT")
    if output:
        directory = Path(output) / label
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "smoke-summary.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        for name in (
            "smoke-final.json",
            "smoke_stats.csv",
            "smoke_stats_history.csv",
            "smoke_failures.csv",
            "smoke_exceptions.csv",
        ):
            source = private / name
            if source.exists():
                raw = source.read_bytes()
                assert platform.env.state["password"].encode() not in raw
                shutil.copyfile(source, directory / name)
    assert result.returncode == 0, (
        "Locust falló; diagnóstico conservado en directorio privado."
    )
    assert verification_error is None, verification_error
    assert summary["failures"] == 0
    assert summary["counts"]["Identidad / login"] == users
    assert summary["counts"]["Identidad / renovación"] == users
    assert summary["counts"]["Identidad / revocación al salir"] == users
    return summary
