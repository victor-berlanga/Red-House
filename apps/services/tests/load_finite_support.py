"""Finite synthetic prerequisites and read-only oracle for three specific roles."""

import hashlib
import json
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

PROFILES = {
    "medical2": "MEDICAL",
    "coordinator1": "COORDINATOR",
    "transport1": "TRANSPORT",
}
NOTICE = "Precondición SQL sintética de carga; no es decisión clínica ni recorrido API"
REASON = "Confirmación académica sintética autorizada para ensayo finito de carga"


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()
    ).hexdigest()


def save(path, value):
    temporary = path.with_suffix(".new")
    temporary.write_text(json.dumps(value, indent=2, default=str) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def _insert(conn, schema, table, **values):
    # Schema/table/columns are constants below, never values supplied by a client.
    names = list(values)
    conn.execute(
        sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
            sql.Identifier("access_" + schema),
            sql.Identifier(table),
            sql.SQL(",").join(map(sql.Identifier, names)),
            sql.SQL(",").join(sql.Placeholder() for _ in names),
        ),
        [Jsonb(v) if isinstance(v, (dict, list)) else v for v in values.values()],
    )


def seed_snapshot(conn, manifest):
    rows = {}
    for schema, table, ids in manifest["seed_rows"]:
        found = conn.execute(
            sql.SQL(
                "SELECT to_jsonb(t) AS row FROM {}.{} t WHERE id=ANY(%s::uuid[]) ORDER BY id"
            ).format(sql.Identifier("access_" + schema), sql.Identifier(table)),
            (ids,),
        ).fetchall()
        rows[schema + "." + table] = [r["row"] for r in found]
    return rows


def prepare_finite_fixture(env):
    """One transaction, new IDs only. Lost commit acknowledgement requires reconciliation."""
    from ms_compatibilidad.laboratory import completeness
    from redhouse.config import settings
    from scripts.local import private_file
    from scripts.prepare_load import validate_environment

    validate_environment(env)
    for owner in ("inventario", "compatibilidad", "transporte"):
        cfg = settings(owner, env.configs[owner])
        if cfg["OPERATION_SCOPE"] != "ACADEMIC" or cfg.get("TESTING", False):
            raise ValueError("academic_real_configuration_required")
    path = env.directory / "finite-roles-fixture.json"
    profile_id = json.loads((env.directory / "transaction-fixture.json").read_text())[
        "profile_id"
    ]
    origin, destination = env.state["tenants"]
    accounts = [
        dict(
            env.state["accounts"][name],
            username=name,
            mime="application/json" if role == "TRANSPORT" else "application/xml",
        )
        for name, role in PROFILES.items()
    ]
    with psycopg.connect(
        env.state["database_owners"]["compatibilidad"], row_factory=dict_row
    ) as conn:
        if (
            conn.execute(
                "SELECT max(version) AS v FROM red_house.schema_migration"
            ).fetchone()["v"]
            != 21
        ):
            raise ValueError("schema_21_required")
        for a in accounts:
            actual = conn.execute(
                "SELECT id::text,tenant_id::text,role,active FROM access_identidad_acceso.users WHERE username=%s",
                (a["username"],),
            ).fetchone()
            if actual != {
                "id": a["id"],
                "tenant_id": a["tenant_id"],
                "role": a["role"],
                "active": True,
            }:
                raise ValueError("finite_identity_changed")
        profile = conn.execute(
            "SELECT * FROM lab_profiles WHERE id=%s", (profile_id,)
        ).fetchone()
        if (
            not profile
            or str(profile["tenant_id"]) != origin
            or profile["kind"] != "BLOOD"
            or profile["component"] != "RBC"
            or not profile["synthetic"]
            or profile["clinical_enabled"]
            or profile["required_tests"] != ["ABO"]
        ):
            raise ValueError("existing_synthetic_profile_required")
        routes = conn.execute(
            "SELECT * FROM access_priorizacion_geografia.routes WHERE origin_id=%s AND destination_id=%s ORDER BY id",
            (origin, destination),
        ).fetchall()
        if len(routes) > 1:
            raise ValueError("ambiguous_existing_route")
        if path.exists():
            manifest = json.loads(path.read_text())
            if (
                manifest["directory"] != str(env.directory)
                or manifest["profile_sha256"] != digest(profile)
                or manifest["accounts"] != accounts
            ):
                raise ValueError("finite_manifest_changed")
            if datetime.fromisoformat(manifest["expires_at"]) <= datetime.now(
                timezone.utc
            ) + timedelta(hours=1):
                raise ValueError("finite_fixture_expiring")
            current = seed_snapshot(conn, manifest)
            if (
                manifest.get("preparation_complete")
                and digest(current) == manifest["seed_snapshot_sha256"]
            ):
                return manifest
            if any(current.values()):
                raise ValueError("finite_seed_present_reconcile_before_resume")
            # Rollback left no rows: reuse the same durable IDs, never create another batch.
        else:
            now = datetime.now(timezone.utc)
            route_id = str(routes[0]["id"]) if routes else str(uuid4())
            manifest = {
                "kind": "finite-three-roles-v1",
                "schema_version": 21,
                "directory": str(env.directory),
                "gps": False,
                "preparation_complete": False,
                "notice": NOTICE,
                "accounts": accounts,
                "profile_id": profile_id,
                "profile_sha256": digest(profile),
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(days=2)).isoformat(),
                "route_id": route_id,
                "route_version": routes[0]["version"] if routes else 1,
                "existing_route_sha256": digest(routes[0]) if routes else None,
                "seed_rows": [],
                "cases": {role: [] for role in PROFILES.values()},
            }
            for role in PROFILES.values():
                for index in range(3):
                    case = {
                        key: str(uuid4())
                        for key in (
                            "case_id",
                            "resource_id",
                            "recipient_id",
                            "request_id",
                            "sample_id",
                            "result_id",
                        )
                    }
                    case.update(
                        approved_reason=REASON,
                        seal="Carga sintética " + case["case_id"][:8],
                        origin_operator_id=env.state["accounts"]["operator1"]["id"],
                        destination_operator_id=env.state["accounts"]["operator2"][
                            "id"
                        ],
                        transport_username="transport1",
                        transport_user_id=env.state["accounts"]["transport1"]["id"],
                    )
                    if role != "MEDICAL":
                        case.update(
                            {
                                key: str(uuid4())
                                for key in (
                                    "evaluation_id",
                                    "operation_id",
                                    "hold_id",
                                    "reservation_id",
                                )
                            }
                        )
                    if role == "TRANSPORT":
                        case["shipment_id"] = str(uuid4())
                    manifest["cases"][role].append(case)
            private_file(path, json.dumps(manifest, indent=2) + "\n")
        if datetime.fromisoformat(manifest["expires_at"]) <= datetime.now(
            timezone.utc
        ) + timedelta(hours=1):
            raise ValueError("finite_fixture_expiring")
        if manifest["existing_route_sha256"]:
            if (
                len(routes) != 1
                or digest(routes[0]) != manifest["existing_route_sha256"]
            ):
                raise ValueError("existing_route_changed")
        elif routes:
            raise ValueError("route_appeared_before_seed")
        added = {}

        def insert(owner, table, **data):
            _insert(conn, owner, table, **data)
            added.setdefault((owner, table), []).append(data["id"])

        now = datetime.fromisoformat(manifest["created_at"])
        expires = datetime.fromisoformat(manifest["expires_at"])
        if not routes:
            insert(
                "priorizacion_geografia",
                "routes",
                id=manifest["route_id"],
                region_id=env.state["region_id"],
                origin_id=origin,
                destination_id=destination,
                distance_km=10.0,
                travel_minutes=15,
                source=NOTICE,
                version=1,
                updated_at=now,
            )
        for role, cases in manifest["cases"].items():
            for case in cases:
                reserved = role != "MEDICAL"
                transported = role == "TRANSPORT"
                insert(
                    "inventario",
                    "resources",
                    id=case["resource_id"],
                    tenant_id=origin,
                    current_institution_id=origin,
                    region_id=env.state["region_id"],
                    folio="FIN-" + case["case_id"][:24],
                    kind="BLOOD",
                    component="RBC",
                    blood_group="O-",
                    expires_at=expires,
                    status="RESERVED" if reserved else "AVAILABLE",
                    version=1,
                    created_at=now,
                )
                insert(
                    "inventario",
                    "resource_controls",
                    id=case["resource_id"],
                    lab_profile_id=profile_id,
                    blocked=False,
                    version=1,
                    created_at=now,
                )
                insert(
                    "receptores",
                    "recipients",
                    id=case["recipient_id"],
                    tenant_id=destination,
                    folio="FIN-" + case["case_id"][:24],
                    display_name="Persona sintética de carga",
                    kind="BLOOD",
                    blood_group="O-",
                    studies=NOTICE,
                    status="ACTIVE",
                    version=1,
                )
                insert(
                    "receptores",
                    "requests",
                    id=case["request_id"],
                    tenant_id=destination,
                    recipient_id=case["recipient_id"],
                    kind="BLOOD",
                    component="RBC",
                    quantity=1,
                    urgency=3,
                    status="IN_PROGRESS" if reserved else "OPEN",
                    version=1,
                    created_at=now,
                )
                insert(
                    "compatibilidad",
                    "lab_samples",
                    id=case["sample_id"],
                    tenant_id=origin,
                    resource_id=case["resource_id"],
                    profile_id=profile_id,
                    identifier="FIN-" + case["case_id"],
                    collected_at=now - timedelta(minutes=2),
                    received_at=now - timedelta(minutes=1),
                    status="RECEIVED",
                    version=2,
                    author_id=case["origin_operator_id"],
                    created_at=now,
                )
                insert(
                    "compatibilidad",
                    "lab_results",
                    id=case["result_id"],
                    sample_id=case["sample_id"],
                    tenant_id=origin,
                    test_code="ABO",
                    value="O",
                    method="Método sintético de carga",
                    laboratory="Laboratorio sintético",
                    reference=NOTICE,
                    measured_at=now - timedelta(seconds=30),
                    issued_at=now,
                    author_id=case["origin_operator_id"],
                    version=1,
                    status="AUTHORIZED",
                    result_state="REPORTED",
                    created_at=now,
                )
                complete = completeness(conn, case["resource_id"], profile_id, origin)
                if (
                    not complete["complete"]
                    or not complete["synthetic"]
                    or complete["clinical_approval"]
                ):
                    raise ValueError("seed_laboratory_incomplete")
                if reserved:
                    # Explicit fixture data; no fabricated audit, review, proof or clinical grant.
                    insert(
                        "compatibilidad",
                        "evaluations",
                        id=case["evaluation_id"],
                        tenant_id=destination,
                        request_id=case["request_id"],
                        request_version=1,
                        recipient_version=1,
                        kind="BLOOD",
                        algorithm_version="LOAD-PRECONDITION-NOT-EXECUTED",
                        snapshot={
                            "operation_scope": "ACADEMIC",
                            "synthetic_precondition": True,
                            "notice": NOTICE,
                        },
                        candidates=[],
                        elapsed_ms=0,
                        created_at=now,
                    )
                    body = {
                        "evaluation_id": case["evaluation_id"],
                        "resource_id": case["resource_id"],
                        "synthetic_precondition": True,
                        "notice": NOTICE,
                    }
                    insert(
                        "inventario",
                        "operations",
                        id=case["operation_id"],
                        user_id=env.state["accounts"]["medical2"]["id"],
                        tenant_id=destination,
                        key="finite-seed-" + case["case_id"],
                        fingerprint=digest(body),
                        input=body,
                        status="COMPLETED",
                        hold_id=case["hold_id"],
                        created_at=now,
                    )
                    insert(
                        "receptores",
                        "holds",
                        id=case["hold_id"],
                        request_id=case["request_id"],
                        recipient_id=case["recipient_id"],
                        operation_id=case["operation_id"],
                        resource_id=case["resource_id"],
                        kind="BLOOD",
                        request_version=1,
                        region_id=env.state["region_id"],
                        status="CONFIRMED",
                        created_at=now,
                    )
                    insert(
                        "inventario",
                        "reservations",
                        id=case["reservation_id"],
                        operation_id=case["operation_id"],
                        resource_id=case["resource_id"],
                        request_id=case["request_id"],
                        recipient_id=case["recipient_id"],
                        origin_id=origin,
                        destination_id=destination,
                        region_id=env.state["region_id"],
                        hold_id=case["hold_id"],
                        evaluation_id=case["evaluation_id"],
                        route_id=manifest["route_id"],
                        route_version=manifest["route_version"],
                        status="RESERVED",
                        shipment_id=case.get("shipment_id"),
                        shipment_sequence=0,
                        created_at=now,
                    )
                    if transported:
                        insert(
                            "transporte",
                            "shipments",
                            id=case["shipment_id"],
                            reservation_id=case["reservation_id"],
                            origin_id=origin,
                            destination_id=destination,
                            region_id=env.state["region_id"],
                            transport_user_id=case["transport_user_id"],
                            departure_at=now,
                            eta=now + timedelta(minutes=30),
                            expires_at=expires,
                            status="PREPARED",
                            version=1,
                            sequence=0,
                            inventory_pending=False,
                        )
        manifest["seed_rows"] = [
            [owner, table, ids] for (owner, table), ids in sorted(added.items())
        ]
        snapshot = seed_snapshot(conn, manifest)
        manifest["seed_snapshot_sha256"] = digest(snapshot)
        manifest["seed_counts"] = {table: len(rows) for table, rows in snapshot.items()}
        # Persist receipt before commit as PREPARED. Uncertain commit is never repeated blindly.
        save(path, manifest)
    manifest["preparation_complete"] = True
    save(path, manifest)
    return manifest


def finite_commits(env, accounts):
    """Snapshot idempotency ledgers, including the separately owned reservation saga."""
    users = [a["id"] for a in accounts]
    with psycopg.connect(
        env.state["database_owners"]["inventario"], row_factory=dict_row
    ) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        rows = conn.execute(
            "SELECT service,user_id::text,key,operation,fingerprint,result FROM red_house.service_idempotency WHERE user_id=ANY(%s::uuid[])",
            (users,),
        ).fetchall()
        operations = conn.execute(
            "SELECT id::text,user_id::text,tenant_id::text,key,fingerprint,input,status,error FROM operations WHERE user_id=ANY(%s::uuid[])",
            (users,),
        ).fetchall()
    return {
        "atomic": {"|".join((r["service"], r["user_id"], r["key"])): r for r in rows},
        "sagas": {
            "|".join(("inventario", r["user_id"], r["key"])): r for r in operations
        },
    }


def normalized_intent(row):
    from ms_compatibilidad.routes import EvaluationCreate, ReviewCreate
    from ms_inventario.routes import ReservationCreate
    from ms_transporte.mobile import Scan
    from ms_transporte.routes import ShipmentCreate, Transition

    path = row["path"]
    identifier = path.split("/")[4] if len(path.split("/")) > 4 else None
    choices = {
        ("compatibilidad", "/api/v1/evaluations"): (
            "evaluation_create",
            EvaluationCreate,
        ),
        ("compatibilidad", "/api/v1/evaluations/{identifier}/reviews"): (
            "evaluation_review:" + str(identifier),
            ReviewCreate,
        ),
        ("inventario", "/api/v1/reservations"): (
            "reservation_create",
            ReservationCreate,
        ),
        ("transporte", "/api/v1/shipments"): ("shipment_create", ShipmentCreate),
        ("transporte", "/api/v1/shipments/{identifier}/scan"): (
            "shipment_scan:" + str(identifier),
            Scan,
        ),
        ("transporte", "/api/v1/shipments/{identifier}/transitions"): (
            "shipment_transition:" + str(identifier),
            Transition,
        ),
    }
    operation, model = choices[row["service"], row["canonical"]]
    body = model.model_validate(row["body"]).model_dump(mode="json")
    return (
        operation,
        body,
        digest(
            body
            if operation == "reservation_create"
            else {"operation": operation, "input": body}
        ),
    )


def reconcile_finite_trace(events, before, after, accounts):
    allowed = {a["id"]: a for a in accounts}
    errors = []
    intents = {}
    responses = {}
    replays = {}
    replay_intents = set()
    starts = {}
    ends = {}
    results = {}
    for row in events:
        user = row["user_id"]
        a = allowed.get(user)
        if not a or any(row[k] != a[k] for k in ("tenant_id", "role")):
            errors.append("trace_identity")
            continue
        slot = (user, row["cycle"])
        kind = row["kind"]
        target = {"cycle_start": starts, "cycle_end": ends, "case_result": results}.get(
            kind
        )
        if target is not None:
            if slot in target:
                errors.append("duplicate_" + kind)
            target[slot] = row
        if kind == "intent":
            key = "|".join((row["service"], user, row["key"]))
            if key in intents:
                errors.append("duplicate_intent")
            intents[key] = row
        elif kind == "replay_intent":
            token = (user, row["key"])
            if token in replay_intents:
                errors.append("duplicate_replay_intent")
            replay_intents.add(token)
        elif kind in ("response", "replay_response"):
            dest = responses if kind == "response" else replays
            k = (user, row["key"])
            if k in dest:
                errors.append("duplicate_" + kind)
            dest[k] = row
    delta = {}
    for ledger in ("atomic", "sagas"):
        if any(after[ledger].get(k) != v for k, v in before[ledger].items()):
            errors.append("prior_ledger_changed")
        delta.update(
            {k: v for k, v in after[ledger].items() if k not in before[ledger]}
        )
    if set(delta) - set(intents):
        errors.append("untracked_commit")
    known = {(row["user_id"], row["key"]) for row in intents.values()}
    if set(responses) - known or replay_intents - known:
        errors.append("response_without_intent")
    lost = uncommitted = 0
    for key, row in intents.items():
        commit = delta.get(key)
        reply = responses.get((row["user_id"], row["key"]))
        if not commit:
            uncommitted += 1
            continue
        operation, body, fingerprint = normalized_intent(row)
        if commit["fingerprint"] != fingerprint:
            errors.append("command_fingerprint")
        if operation == "reservation_create":
            if commit["status"] != "COMPLETED" or commit["input"] != body:
                errors.append("reservation_saga_pending")
            if reply and reply["result"]["operation_id"] != commit["id"]:
                errors.append("operation_response")
        else:
            if commit["operation"] != operation:
                errors.append("operation_name")
            if reply:
                # Shipment creation returns claim_shipment's current row, not its pending atomic row.
                if operation == "shipment_create":
                    if reply["result"]["id"] != commit["result"]["id"]:
                        errors.append("shipment_response")
                elif reply["result"] != commit["result"]:
                    errors.append("atomic_response")
        if not reply:
            lost += 1
    if uncommitted:
        errors.append("uncommitted_intent")
    if lost:
        errors.append("response_lost_committed")
    for k, replay in replays.items():
        if k not in responses or replay["result"] != responses[k]["result"]:
            errors.append("replay_not_original")
    if Counter(user for user, _key in replays) != {a["id"]: 1 for a in accounts}:
        errors.append("replay_count")
    unconfirmed_replays = len(replay_intents - set(replays))
    if unconfirmed_replays or set(replays) - replay_intents:
        errors.append("unconfirmed_replay")
    completed = Counter()
    measured = Counter()
    incomplete = 0
    for slot, start in starts.items():
        end = ends.get(slot)
        if not end or not end["success"] or slot not in results:
            incomplete += 1
            continue
        completed[start["role"]] += 1
        if start["stage"] == "measuring" and end["stage"] == "measuring":
            measured[start["role"]] += 1
    if incomplete:
        errors.append("incomplete_cycle")
    if completed != {r: 3 for r in PROFILES.values()}:
        errors.append("finite_cycle_count")
    if measured != {r: 2 for r in PROFILES.values()}:
        errors.append("finite_measurement_count")
    if len(results) != 9 or len({r["case_id"] for r in results.values()}) != 9:
        errors.append("case_count")
    intervals = [
        (start["at"], ends[slot]["at"])
        for slot, start in starts.items()
        if start["stage"] == "measuring" and slot in ends
    ]
    boundaries = sorted(
        [(a, 1) for a, b in intervals] + [(b, -1) for a, b in intervals]
    )
    active = peak = 0
    active_seconds = 0.0
    previous = None
    for at, delta_active in boundaries:
        if previous is not None and active:
            active_seconds += at - previous
        active += delta_active
        peak = max(peak, active)
        previous = at
    return {
        "unconfirmed_replays": unconfirmed_replays,
        "active_cycle_peak": peak,
        "active_cycle_seconds": active_seconds,
        "errors": errors,
        "attempted": len(intents),
        "committed": len(delta),
        "not_committed": uncommitted,
        "response_lost_committed": lost,
        "incomplete_cycles": incomplete,
        "completed": dict(completed),
        "measured_completed": dict(measured),
        "replays": len(replays),
        "results": list(results.values()),
        "pending": [k for k in intents if k not in delta],
    }


def verify_finite_persistence(env, output, manifest, before, *, wait_seconds=30):
    """Reconcile all attempts even if Locust failed; do not fix data or extend time."""
    from pymongo import MongoClient

    events = []
    trace_errors = []
    files = sorted(output.glob("attempts-*.jsonl"))
    for path in files:
        for line in path.read_text().splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                trace_errors.append("truncated_trace")
    report = reconcile_finite_trace(
        events, before, finite_commits(env, manifest["accounts"]), manifest["accounts"]
    )
    errors = report["errors"] + trace_errors
    if len(files) != 3:
        errors.append("missing_trace")
    accounts = {a["role"]: a for a in manifest["accounts"]}
    cases = {c["case_id"]: c for rows in manifest["cases"].values() for c in rows}
    expected = Counter()
    identifiers = set()
    essential_targets = set()
    shipment_expectations = {}
    with psycopg.connect(
        env.state["database_owners"]["inventario"], row_factory=dict_row
    ) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        for result in report.pop("results"):
            case = cases.get(result["case_id"])
            role = result["role"]
            actor = accounts[role]["id"]
            if not case or case["resource_id"] != result["resource_id"]:
                errors.append("case_correlation")
                continue
            resource = conn.execute(
                "SELECT * FROM resources WHERE id=%s", (case["resource_id"],)
            ).fetchone()
            reserve = conn.execute(
                "SELECT * FROM reservations WHERE resource_id=%s",
                (case["resource_id"],),
            ).fetchall()
            if len(reserve) != 1:
                errors.append("reservation_multiplicity")
                continue
            reserve = reserve[0]
            rid = str(reserve["id"])
            identifiers.update((case["resource_id"], case["request_id"], rid))
            if (
                str(reserve["request_id"]) != case["request_id"]
                or str(reserve["resource_id"]) != case["resource_id"]
            ):
                errors.append("reservation_correlation")
            if role == "MEDICAL":
                eid = result["evaluation_id"]
                identifiers.add(eid)
                if (
                    str(reserve["operation_id"]) != result["operation_id"]
                    or rid != result["reservation_id"]
                    or reserve["status"] != "RESERVED"
                    or resource["status"] != "RESERVED"
                ):
                    errors.append("medical_final_state")
                reviews = conn.execute(
                    "SELECT * FROM access_compatibilidad.reviews WHERE evaluation_id=%s",
                    (eid,),
                ).fetchall()
                if (
                    len(reviews) != 1
                    or str(reviews[0]["resource_id"]) != case["resource_id"]
                    or str(reviews[0]["actor_id"]) != actor
                    or reviews[0]["decision"] != "FAVORABLE"
                    or reviews[0]["operation_scope"] != "ACADEMIC"
                ):
                    errors.append("medical_review")
                expected.update(
                    {
                        ("compatibilidad", "EVALUATION_CREATED", eid, actor): 1,
                        ("compatibilidad", "EVALUATION_REVIEWED", eid, actor): 1,
                        ("inventario", "RESOURCE_RESERVED", rid, actor): 1,
                    }
                )
                essential_targets.add(("inventario", "RESOURCE_RESERVED", rid))
            else:
                sid = result["shipment_id"]
                identifiers.add(sid)
                shipment = conn.execute(
                    "SELECT * FROM access_transporte.shipments WHERE id=%s", (sid,)
                ).fetchone()
                desired = "PLANNED" if role == "COORDINATOR" else "DELIVERED"
                shipment_expectations[sid] = (
                    case["resource_id"],
                    1 if role == "COORDINATOR" else 3,
                    desired,
                )
                if (
                    not shipment
                    or shipment["status"] != desired
                    or shipment["inventory_pending"]
                    or str(shipment["reservation_id"]) != rid
                    or str(shipment["transport_user_id"]) != accounts["TRANSPORT"]["id"]
                    or str(reserve["shipment_id"]) != sid
                ):
                    errors.append("shipment_final_state")
                if role == "COORDINATOR":
                    expected.update(
                        {
                            ("transporte", "SHIPMENT_PLAN_PENDING", sid, actor): 1,
                            ("transporte", "SHIPMENT_PLANNED", sid, None): 1,
                        }
                    )
                    essential_targets.add(("transporte", "SHIPMENT_PLANNED", sid))
                else:
                    transitions = conn.execute(
                        "SELECT sequence,state,actor_id::text FROM access_transporte.transitions WHERE shipment_id=%s ORDER BY sequence",
                        (sid,),
                    ).fetchall()
                    if transitions != [
                        {"sequence": i, "state": state, "actor_id": actor}
                        for i, state in enumerate(
                            ("COLLECTED", "IN_TRANSIT", "DELIVERED"), 1
                        )
                    ]:
                        errors.append("transition_sequence")
                    expected[
                        (
                            "transporte",
                            "SHIPMENT_RESOURCE_IDENTIFIER_VERIFIED",
                            sid,
                            actor,
                        )
                    ] = 2
                    for state in ("COLLECTED", "IN_TRANSIT", "DELIVERED"):
                        expected[("transporte", "SHIPMENT_" + state, sid, actor)] = 1
                        essential_targets.add(("transporte", "SHIPMENT_" + state, sid))
        sources = conn.execute(
            "SELECT event FROM red_house.service_activity_events WHERE event->>'resource_id'=ANY(%s::text[])",
            (sorted(identifiers),),
        ).fetchall()
        source_events = {r["event"]["event_id"]: r["event"] for r in sources}
        actual = Counter(
            (e["source"], e["action"], e["resource_id"], e["actor_id"])
            for e in source_events.values()
        )
        scope = {key[:3] for key in expected}
        if (
            Counter({key: count for key, count in actual.items() if key[:3] in scope})
            != expected
        ):
            errors.append("source_event_count")
        selected = [
            e
            for e in source_events.values()
            if (e["source"], e["action"], e["resource_id"]) in scope
        ]
        scans = [
            e
            for e in selected
            if e["action"] == "SHIPMENT_RESOURCE_IDENTIFIER_VERIFIED"
        ]
        if any(
            e["metadata"].get("request_representation") != "json"
            or e["metadata"].get("response_representation") != "json"
            for e in scans
        ):
            errors.append("scan_representation")
        target_rows = conn.execute(
            "SELECT service,target,event_id::text,event FROM red_house.service_outbox WHERE event_id=ANY(%s::uuid[])",
            ([e["event_id"] for e in selected],),
        ).fetchall()
        actual_targets = {
            (r["service"], r["event"]["action"], r["event"]["resource_id"])
            for r in target_rows
            if r["target"] == "alertas"
        }
        if not essential_targets <= actual_targets:
            errors.append("missing_alert_dispatch")
    # Keep a bounded single convergence deadline. All source events have exact Audit/Mongo projections.
    start = time.monotonic()
    deadline = start + wait_seconds
    projection = False
    expected_alerts = Counter()
    for r in target_rows:
        if r["target"] != "alertas":
            continue
        e = r["event"]
        meta = e["metadata"]
        targets = {
            (meta.get("origin_id", e["tenant_id"]), "OPERATOR"),
            (meta.get("destination_id", e["tenant_id"]), "OPERATOR"),
        }
        for tenant, role in targets:
            expected_alerts[
                (e["event_id"], tenant, role, None, e["action"], e["resource_id"])
            ] += 1
    with MongoClient(
        env.state["mongo_admin"], serverSelectionTimeoutMS=1000, socketTimeoutMS=1500
    ) as mongo:
        while True:
            with psycopg.connect(
                env.state["database_owners"]["auditoria"], row_factory=dict_row
            ) as conn:
                conn.execute("SET TRANSACTION READ ONLY")
                ids = list(source_events)
                audit = conn.execute(
                    "SELECT id::text,event FROM audit_events WHERE id=ANY(%s::uuid[])",
                    (ids,),
                ).fetchall()
                pending = conn.execute(
                    "SELECT count(*) AS n FROM red_house.service_outbox WHERE event_id=ANY(%s::uuid[]) AND delivered_at IS NULL",
                    (ids,),
                ).fetchone()["n"]
                alerts = conn.execute(
                    "SELECT event_id::text,tenant_id::text,target_role,target_user_id::text,message_code,resource_id FROM access_alertas.alerts WHERE event_id=ANY(%s::uuid[])",
                    ([e["event_id"] for e in selected],),
                ).fetchall()
                logistics = True
                for sid, (
                    resource_id,
                    sequence,
                    state,
                ) in shipment_expectations.items():
                    projected = conn.execute(
                        "SELECT r.status,r.shipment_sequence,x.status AS resource_status FROM access_inventario.reservations r JOIN access_inventario.resources x ON x.id=r.resource_id WHERE r.shipment_id=%s AND x.id=%s",
                        (sid, resource_id),
                    ).fetchone()
                    target_status = "RESERVED" if state == "PLANNED" else "IN_TRANSIT"
                    logistics &= bool(
                        projected
                        and projected["status"] == target_status
                        and projected["resource_status"] == target_status
                        and projected["shipment_sequence"] == sequence
                    )
                    chain = conn.execute(
                        "SELECT last_sequence FROM access_custodia.chains WHERE id=%s",
                        (sid,),
                    ).fetchone()
                    logistics &= bool(chain and chain["last_sequence"] == sequence)
            mongodb = list(mongo.rh_auditoria.events.find({"_id": {"$in": ids}}))
            matched_audit = {r["id"]: r["event"] for r in audit} == source_events
            matched_mongo = {
                d["_id"]: {k: v for k, v in d.items() if k != "_id"} for d in mongodb
            } == source_events
            matched_alerts = (
                Counter(tuple(r.values()) for r in alerts) == expected_alerts
            )
            projection = (
                matched_audit
                and matched_mongo
                and matched_alerts
                and pending == 0
                and logistics
            )
            if projection or time.monotonic() >= deadline:
                break
            time.sleep(0.5)
    if not projection:
        errors.append("event_propagation")
    report.update(
        errors=sorted(set(errors)),
        persistence_verified=not errors,
        event_wait_seconds=time.monotonic() - start,
        source_events=len(source_events),
        expected_alerts=sum(expected_alerts.values()),
        pending_outbox=pending,
        timings=[
            {
                k: r[k]
                for k in (
                    "role",
                    "stage",
                    "elapsed_ms",
                    "mfa_wait_ms",
                    "excluding_mfa_wait_ms",
                )
            }
            for r in events
            if r["kind"] == "case_timing"
        ],
        connected_users=3,
        capacity_estimate=False,
        gps_in_this_increment=False,
    )
    save(output / "reconciliation.private.json", report)
    return report
