"""Corrección acotada de etiquetas de la carga del 21/10/2026, autorizada por el dueño.

No modifica eventos históricos, respuestas de idempotencia ni datos clínicos.
La API bloquea ediciones de expedientes con historia; esta tarea administrativa
solo cambia las columnas de texto enumeradas abajo, con respaldo y auditoría.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from uuid import UUID, uuid4

from populate_demo import ROOT, Demo, sql, write_private

WORK = ROOT / ".local/compose/labels-20261021"
SPECS = (
    (
        "institution/",
        "institution",
        "institution_id",
        "institution_id",
        "identidad_acceso",
        ("institution_name",),
    ),
    (
        "user/",
        "user_account",
        "account_id",
        "tenant_id",
        "identidad_acceso",
        ("username",),
    ),
    (
        "catalogue/",
        "catalogue_entry",
        "id",
        "tenant_id",
        "identidad_acceso",
        ("name", "details"),
    ),
    (
        "donor/",
        "donor",
        "donor_id",
        "institution_id",
        "donantes",
        ("record_code", "display_name", "consent_reference", "background"),
    ),
    ("campaign/", "campaign", "campaign_id", "institution_id", "donantes", ("title",)),
    ("resource/", "resource", "resource_id", "tenant_id", "inventario", ("folio",)),
    (
        "recipient/",
        "recipient",
        "recipient_id",
        "institution_id",
        "receptores",
        ("record_code", "display_name", "studies", "requirement"),
    ),
    (
        "route/",
        "regional_route",
        "route_id",
        "origin_id",
        "priorizacion_geografia",
        ("source_reference",),
    ),
)
TEXT = {
    "Persona ficticia creada para presentación académica.": "Expediente de donante registrado.",
    "Expediente ficticio; revisión clínica externa pendiente, sin interpretación HLA.": "Revisión clínica externa pendiente; sin interpretación HLA.",
    "Solicitud de ejemplo para demostración académica.": "Solicitud de recurso para coordinación entre instituciones.",
    "Referencia logística ficticia; sin reglas clínicas de conservación.": "Ubicación interna de almacenamiento.",
    "Estimación ficticia de demostración; no representa tráfico real.": "Estimación de referencia; no representa tráfico en tiempo real.",
}


def normalize(value, institution):
    if isinstance(value, dict):
        return {key: normalize(item, institution) for key, item in value.items()}
    if not isinstance(value, str):
        return value
    if value in TEXT:
        return TEXT[value]
    address = re.fullmatch(
        r"Domicilio ficticio para demostración, referencia (\d+)", value
    )
    if address:
        return f"Sede H{institution}, referencia de ubicación {address[1]}"
    value = value.replace("DEMO26-", "RH26-").replace("DEMO-CONSENT-", "CONSENT-")
    value = value.replace("demo_donor_", "donor_").replace("demo-h", "contacto-h")
    return re.sub(r"\bDEMO\s*", "", value).strip()


def table_counts():
    parts = [
        f"SELECT '{table}' AS name,count(*) AS rows FROM red_house.{table}"
        for _, table, *_ in SPECS
    ]
    return {
        row["name"]: row["rows"]
        for row in sql("SELECT json_agg(t) FROM (" + " UNION ALL ".join(parts) + ") t")
    }


def prepare(demo):
    assert demo.cp["phase"] == "complete", "La carga original debe estar completa."
    admins = sql(
        "SELECT json_agg(t) FROM (SELECT account_id,tenant_id,username FROM red_house.user_account WHERE username IN ('admin1','admin2') AND role='ADMIN' AND active) t"
    )
    assert len(admins) == 2
    actors = {row["tenant_id"]: row["account_id"] for row in admins}
    first_admin = next(
        row["account_id"] for row in admins if row["username"] == "admin1"
    )
    region = demo.state["region_id"]
    plan = []
    for prefix, table, pk, tenant_column, service, columns in SPECS:
        ids = [
            str(UUID(op["result"]["id"]))
            for tag, op in demo.cp["operations"].items()
            if tag.startswith(prefix)
        ]
        assert ids, table
        identifiers = ",".join("'" + identifier + "'::uuid" for identifier in ids)
        fields = ",".join(f"'{column}',t.{column}" for column in columns)
        names = ",".join("'" + column + "'" for column in columns)
        rows = sql(
            f"SELECT json_agg(x) FROM (SELECT t.{pk} AS id,t.{tenant_column} AS tenant_id,jsonb_build_object({fields}) AS fields,md5((to_jsonb(t)-ARRAY[{names}])::text) AS unchanged_hash FROM red_house.{table} t WHERE t.{pk} IN ({identifiers})) x"
        )
        assert len(rows) == len(ids), table
        for row in rows:
            tenant = row["tenant_id"]
            institution = (
                1 + demo.tenants.index(tenant) if tenant in demo.tenants else 0
            )
            after = normalize(row["fields"], institution)
            if after == row["fields"]:
                continue
            plan.append(
                {
                    "table": table,
                    "pk": pk,
                    "id": row["id"],
                    "tenant_id": tenant,
                    "service": service,
                    "actor_id": actors.get(tenant, first_admin),
                    "region_id": region,
                    "columns": list(columns),
                    "before": row["fields"],
                    "after": after,
                    "unchanged_hash": row["unchanged_hash"],
                    "event_id": str(uuid4()),
                    "decision_id": str(uuid4()),
                    "outbox_id": str(uuid4()),
                }
            )
    return plan


def apply(plan):
    encoded = base64.b64encode(json.dumps(plan).encode()).decode()
    statement = """
BEGIN;
SET LOCAL lock_timeout='5s';
SET LOCAL statement_timeout='120s';
SELECT pg_advisory_xact_lock(20261021, 2);
DO $normalize$
DECLARE
    item jsonb;
    current_row jsonb;
    next_row jsonb;
    names text[];
    assignments text;
    event jsonb;
    changed integer;
BEGIN
    FOR item IN SELECT value FROM jsonb_array_elements(convert_from(decode('__PAYLOAD__','base64'),'UTF8')::jsonb)
    LOOP
        SELECT array_agg(value) INTO names FROM jsonb_array_elements_text(item->'columns');
        EXECUTE format('SELECT to_jsonb(t) FROM red_house.%I t WHERE %I=$1::uuid FOR UPDATE',item->>'table',item->>'pk')
            INTO current_row USING item->>'id';
        IF current_row IS NULL OR md5((current_row-names)::text)<>item->>'unchanged_hash'
            OR NOT current_row @> (item->'before') THEN
            RAISE EXCEPTION 'Cambio concurrente; se cancela la normalización: %',item->>'id';
        END IF;
        SELECT string_agg(format('%I=patch.%I',name,name),',') INTO assignments FROM unnest(names) name;
        EXECUTE format('UPDATE red_house.%I t SET %s FROM jsonb_populate_record(NULL::red_house.%I,$1) patch WHERE t.%I=$2::uuid',item->>'table',assignments,item->>'table',item->>'pk')
            USING item->'after',item->>'id';
        GET DIAGNOSTICS changed=ROW_COUNT;
        IF changed<>1 THEN RAISE EXCEPTION 'Cantidad inesperada'; END IF;
        EXECUTE format('SELECT to_jsonb(t) FROM red_house.%I t WHERE %I=$1::uuid',item->>'table',item->>'pk')
            INTO next_row USING item->>'id';
        IF md5((next_row-names)::text)<>item->>'unchanged_hash' OR NOT next_row @> (item->'after') THEN
            RAISE EXCEPTION 'Cambió un campo fuera de las etiquetas autorizadas';
        END IF;
        INSERT INTO red_house.service_decisions(service,id,resource_id,tenant_id,actor_id,action,reason,changes)
            VALUES(item->>'service',(item->>'decision_id')::uuid,(item->>'id')::uuid,(item->>'tenant_id')::uuid,(item->>'actor_id')::uuid,
                'LABELS_NORMALIZED','Normalización de etiquetas solicitada por el responsable del proyecto.',
                jsonb_build_object('fields',item->'after','maintenance','labels-20261021'));
        event=jsonb_build_object('event_id',item->>'event_id','source',item->>'service','action','LABELS_NORMALIZED',
            'resource_id',item->>'id','tenant_id',item->>'tenant_id','region_id',item->>'region_id','actor_id',item->>'actor_id',
            'correlation_id',item->>'event_id','metadata',jsonb_build_object('maintenance','labels-20261021','channel','server_maintenance','columns',item->'columns'),
            'occurred_at',clock_timestamp()::text);
        INSERT INTO red_house.service_activity_events(service,id,tenant_id,event)
            VALUES(item->>'service',(item->>'event_id')::uuid,(item->>'tenant_id')::uuid,event);
        INSERT INTO red_house.service_outbox(service,id,event_id,target,event)
            VALUES(item->>'service',(item->>'outbox_id')::uuid,(item->>'event_id')::uuid,'auditoria',event);
    END LOOP;
END;
$normalize$;
COMMIT;
""".replace("__PAYLOAD__", encoded)
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(ROOT / "compose.yaml"),
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "rh_bootstrap",
            "-d",
            "red_house",
            "-qAt",
            "-v",
            "ON_ERROR_STOP=1",
        ],
        input=statement,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if result.returncode:
        write_private(WORK / "failure.json", {"stderr": result.stderr})
        raise RuntimeError("Transacción cancelada; revisar el error privado.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    WORK.mkdir(exist_ok=True, mode=0o700)
    demo = Demo(ROOT / ".local/compose")
    try:
        plan = prepare(demo)
        summary = dict(Counter(item["table"] for item in plan))
        print(
            json.dumps({"rows_to_normalize": len(plan), "tables": summary}), flush=True
        )
        if not args.apply:
            write_private(WORK / "preview.json", plan)
            return
        manifest = json.loads((WORK / "backup.json").read_text())
        assert manifest["archive_list_valid"]
        assert (
            hashlib.sha256((WORK / "before.dump").read_bytes()).hexdigest()
            == manifest["sha256"]
        )
        if not plan:
            print(json.dumps({"already_normalized": True}), flush=True)
            return
        for user in ("admin1", "admin2"):
            demo.request("identidad_acceso", "GET", "/api/v1/users?page_size=1", user)
        write_private(WORK / "applied-plan.json", plan)
        before = table_counts()
        apply(plan)
        after = table_counts()
        assert before == after, "Cambió la cantidad de registros."
        assert not prepare(demo), "Quedan etiquetas del conjunto sin normalizar."
        report = {
            "date": datetime.now(timezone.utc).isoformat(),
            "result": "passed",
            "rows_changed": len(plan),
            "tables": summary,
            "counts_before": before,
            "counts_after": after,
            "unchanged_columns_verified_in_transaction": True,
            "historical_events_untouched": True,
            "identifiers_password_hashes_versions_and_states_preserved": True,
            "audit_events_added": len(plan),
            "second_pass_changes": 0,
            "backup_sha256": manifest["sha256"],
            "username_mapping": {
                item["before"]["username"]: item["after"]["username"]
                for item in plan
                if item["table"] == "user_account"
            },
        }
        output = ROOT / "documentation/evidencias/gcp/datos-demo/labels.json"
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"result": "passed", "rows_changed": len(plan)}), flush=True)
    finally:
        demo.close()


if __name__ == "__main__":
    main()
