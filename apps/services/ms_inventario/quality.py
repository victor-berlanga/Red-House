"""Laboratorio, frío, linaje y destino: una autoridad para bloquear o liberar recursos."""

from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import uuid4

from flask import current_app, g
from pydantic import Field
from redhouse.api import atomic, endpoint, listing
from redhouse.client import call
from redhouse.db import get, insert, transaction, update
from redhouse.decisions import record
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import install_reads, page_schema, schema, version
from redhouse.models import ID, Confirm, Kind, Model, Text, utc_date
from redhouse.security import own


class EquipmentCreate(Model):
    label: Text
    location: Text
    calibration_reference: Text | None = None


class Equipment(EquipmentCreate):
    id: ID
    tenant_id: ID
    active: bool
    version: int
    created_at: Text


class ColdProfileCreate(Model):
    kind: Kind
    component: Text
    minimum_c: Annotated[float, Field(ge=-273.15, le=100)]
    maximum_c: Annotated[float, Field(ge=-273.15, le=100)]
    max_gap_seconds: Annotated[int, Field(ge=1, le=86400)]
    source: Text
    synthetic: Literal[True]
    version: Annotated[int, Field(ge=1)] = 1
    effective_at: Text
    supersedes: ID | None = None


class ColdProfile(ColdProfileCreate):
    id: ID
    tenant_id: ID
    author_id: ID
    created_at: Text


class ControlsCreate(Confirm):
    version: Annotated[int, Field(ge=1)]
    lab_profile_id: ID
    cold_equipment_id: ID | None = None
    cold_profile_id: ID | None = None


class Controls(Model):
    id: ID
    lab_profile_id: ID | None
    cold_equipment_id: ID | None
    cold_profile_id: ID | None
    blocked: bool
    version: int
    created_at: Text


class ReadingCreate(Model):
    temperature_c: Annotated[float, Field(ge=-273.15, le=100)]
    captured_at: Text
    source: Text
    calibration_reference: Text | None = None


class Reading(ReadingCreate):
    id: ID
    resource_id: ID
    equipment_id: ID
    profile_id: ID
    tenant_id: ID
    received_at: Text
    excursion: bool
    gap: bool
    author_id: ID


class QualityReview(Confirm):
    version: Annotated[int, Field(ge=1)]


class CustodyValidation(Model):
    shipment_id: ID
    check_quality: bool


class CustodyResource(Model):
    resource_id: ID
    authorized: bool


class DestinationCreate(Confirm):
    version: Annotated[int, Field(ge=1)]
    destination: Literal[
        "TRANSFUSED", "TRANSPLANTED", "DISCARDED", "RETURNED", "RESEARCH"
    ]
    reference: Text
    occurred_at: Text
    supersedes: ID | None = None


class Destination(Model):
    id: ID
    resource_id: ID
    tenant_id: ID
    destination: str
    reference: Text
    occurred_at: Text
    reason: str
    author_id: ID
    version: int
    supersedes: ID | None
    created_at: Text


class Child(Model):
    folio: Annotated[
        str, Field(min_length=6, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    ]
    component: Text
    expires_at: Text


class Fractionate(Confirm):
    version: Annotated[int, Field(ge=1)]
    children: Annotated[list[Child], Field(min_length=1, max_length=8)]


class Lineage(Model):
    id: ID
    parent_id: ID
    child_id: ID
    donation_id: ID
    tenant_id: ID
    author_id: ID
    reason: str
    created_at: Text


def guard(conn, resource, *, release=False):
    """Siempre se evalúa en el propietario y dentro del bloqueo del recurso."""
    control = conn.execute(
        "SELECT * FROM resource_controls WHERE id=%s", (resource["id"],)
    ).fetchone()
    if not control:
        if current_app.config.get("REQUIRE_LAB_PROFILE", not current_app.testing):
            raise APIError(
                "laboratory_incomplete",
                "Vincula el perfil de laboratorio antes de usar la unidad.",
                409,
            )
        from redhouse.operational import require_clinical_policy

        require_clinical_policy(None)
        return  # Compatibilidad explícita del inventario académico anterior.
    if control["blocked"]:
        raise APIError("quality_block", "Cuarentena pendiente de revisión humana.", 409)
    if control["cold_profile_id"]:
        profile = get(conn, "cold_profiles", str(control["cold_profile_id"]))
        latest = conn.execute(
            "SELECT captured_at FROM cold_readings WHERE resource_id=%s ORDER BY captured_at DESC LIMIT 1",
            (resource["id"],),
        ).fetchone()
        if (
            not latest
            or (datetime.now(timezone.utc) - latest["captured_at"]).total_seconds()
            > profile["max_gap_seconds"]
        ):
            raise APIError("cold_gap", "Falta lectura térmica vigente.", 409)
    if control["lab_profile_id"]:
        conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            ("laboratory:" + str(resource["id"]),),
        )
        result = call(
            "compatibilidad",
            "POST",
            f"/internal/v1/laboratory/resources/{resource['id']}/check",
            {
                "profile_id": str(control["lab_profile_id"]),
                "tenant_id": str(resource["tenant_id"]),
            },
            delegate=False,
        )
        if not result["complete"]:
            raise APIError(
                "laboratory_incomplete",
                "Faltan muestras/resultados autorizados del perfil registrado.",
                409,
            )
        from redhouse.operational import require_clinical_policy

        require_clinical_policy(result)
        return result
    elif release:
        raise APIError("laboratory_incomplete", "Perfil de laboratorio requerido.", 409)
    else:
        from redhouse.operational import require_clinical_policy

        require_clinical_policy(None)


def block(conn, row, action):
    control = conn.execute(
        "SELECT * FROM resource_controls WHERE id=%s", (row["id"],)
    ).fetchone()
    if control and control["blocked"]:
        return
    if control:
        update(
            conn,
            "resource_controls",
            row["id"],
            {"blocked": True, "version": control["version"] + 1},
        )
    else:
        insert(conn, "resource_controls", {"id": row["id"], "blocked": True})
    fields = {"version": row["version"] + 1}
    if row["status"] == "AVAILABLE":
        fields["status"] = "QUARANTINE"
    update(conn, "resources", row["id"], fields)
    if g.actor.get("id"):
        insert(
            conn,
            "movements",
            {
                "id": str(uuid4()),
                "resource_id": row["id"],
                "action": action,
                "actor_id": g.actor["id"],
            },
        )
    emit(
        conn,
        action,
        row["id"],
        row["current_institution_id"],
        targets=("auditoria", "alertas"),
    )


def scan_quality():
    """Caducidad y brechas; las restricciones de uso no dependen del worker."""
    with transaction() as conn:
        rows = conn.execute(
            "SELECT r.* FROM resources r LEFT JOIN resource_controls c ON c.id=r.id "
            "LEFT JOIN cold_profiles p ON p.id=c.cold_profile_id WHERE r.status<>'WITHDRAWN' AND NOT coalesce(c.blocked,false) "
            "AND (r.expires_at<=now() OR (p.id IS NOT NULL AND coalesce((SELECT max(captured_at) FROM cold_readings l WHERE l.resource_id=r.id),c.created_at) "
            "<now()-p.max_gap_seconds*interval '1 second')) ORDER BY r.id FOR UPDATE OF r SKIP LOCKED LIMIT 100"
        ).fetchall()
        for row in rows:
            g.actor = {
                "id": None,
                "tenant_id": str(row["current_institution_id"]),
                "region_id": str(row["region_id"]),
            }
            block(
                conn,
                row,
                "RESOURCE_EXPIRED"
                if row["expires_at"] <= datetime.now(timezone.utc)
                else "RESOURCE_COLD_GAP",
            )
    return len(rows)


def install(app):
    @endpoint(
        app,
        "/internal/v1/reservations/<identifier>/custody-check",
        "POST",
        model=CustodyValidation,
        internal=("transporte",),
        delegate=False,
        result=schema(CustodyResource),
    )
    def custody_check(identifier, data):
        with transaction() as conn:
            allocation = get(conn, "reservations", identifier)
            if str(allocation["shipment_id"]) != data["shipment_id"]:
                raise APIError("forbidden", "Traslado ajeno a la reserva.", 403)
            resource = get(conn, "resources", str(allocation["resource_id"]), True)
            if data["check_quality"]:
                if resource["expires_at"] <= datetime.now(timezone.utc):
                    raise APIError(
                        "expired_resource", "El vencimiento impide la aceptación.", 409
                    )
                guard(conn, resource)
            return {"resource_id": str(resource["id"]), "authorized": True}

    install_reads(
        app,
        "/api/v1/cold/equipment",
        "cold_equipment",
        Equipment,
        ("MEDICAL", "OPERATOR"),
    )
    install_reads(
        app,
        "/api/v1/cold/profiles",
        "cold_profiles",
        ColdProfile,
        ("MEDICAL", "OPERATOR"),
    )
    install_reads(
        app,
        "/api/v1/resource-destinations",
        "resource_destinations",
        Destination,
        ("MEDICAL", "OPERATOR"),
        {"resource_id": ("resource_id", ())},
    )

    @endpoint(
        app,
        "/api/v1/cold/equipment",
        "POST",
        model=EquipmentCreate,
        roles=("OPERATOR",),
        result=schema(Equipment),
        status=201,
    )
    def cold_equipment_create(data):
        def work(conn):
            row = insert(
                conn,
                "cold_equipment",
                dict(data, id=str(uuid4()), tenant_id=g.actor["tenant_id"]),
            )
            emit(conn, "COLD_EQUIPMENT_CREATED", row["id"], row["tenant_id"])
            return row

        return atomic("cold_equipment_create", data, work)

    @endpoint(
        app,
        "/api/v1/cold/profiles",
        "POST",
        model=ColdProfileCreate,
        roles=("MEDICAL",),
        result=schema(ColdProfile),
        status=201,
    )
    def cold_profile_create(data):
        if data["minimum_c"] >= data["maximum_c"]:
            raise APIError("validation", "Intervalo térmico inválido.", 422)
        effective = utc_date(data["effective_at"], "effective_at")
        if effective > datetime.now(timezone.utc):
            raise APIError("validation", "Perfil requiere fecha efectiva vigente.", 422)

        def work(conn):
            previous = (
                get(conn, "cold_profiles", data["supersedes"])
                if data["supersedes"]
                else None
            )
            if previous:
                own(previous["tenant_id"])
                if (
                    previous["kind"] != data["kind"]
                    or previous["component"] != data["component"]
                    or effective < previous["effective_at"]
                ):
                    raise APIError(
                        "conflict",
                        "La corrección debe conservar producto y orden temporal.",
                        409,
                    )
            if data["version"] != (previous["version"] + 1 if previous else 1):
                raise APIError("stale_version", "Versión siguiente requerida.", 412)
            row = insert(
                conn,
                "cold_profiles",
                dict(
                    data,
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    author_id=g.actor["id"],
                    effective_at=effective,
                ),
            )
            emit(conn, "COLD_PROFILE_CREATED", row["id"], row["tenant_id"])
            return row

        return atomic("cold_profile_create", data, work)

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/controls",
        "POST",
        model=ControlsCreate,
        roles=("MEDICAL",),
        result=schema(Controls),
        status=201,
    )
    def resource_controls_create(identifier, data):
        profile = call(
            "compatibilidad",
            "GET",
            "/api/v1/laboratory/profiles/" + data["lab_profile_id"],
        )

        def work(conn):
            row = get(conn, "resources", identifier, True)
            own(row["current_institution_id"])
            version(row, data["version"])
            if row["status"] not in ("QUARANTINE", "AVAILABLE") or any(
                row[k] != profile[k] for k in ("kind", "component")
            ):
                raise APIError("conflict", "Recurso o perfil incompatibles.", 409)
            if bool(data["cold_equipment_id"]) != bool(data["cold_profile_id"]):
                raise APIError(
                    "validation", "Equipo y perfil térmico deben indicarse juntos.", 422
                )
            if data["cold_equipment_id"]:
                equipment = get(conn, "cold_equipment", data["cold_equipment_id"])
                cold = get(conn, "cold_profiles", data["cold_profile_id"])
                own(equipment["tenant_id"])
                own(cold["tenant_id"])
                if not equipment["active"] or any(
                    row[k] != cold[k] for k in ("kind", "component")
                ):
                    raise APIError(
                        "conflict", "Perfil térmico o equipo incompatibles.", 409
                    )
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                ("laboratory:" + identifier,),
            )
            old = conn.execute(
                "SELECT * FROM resource_controls WHERE id=%s", (identifier,)
            ).fetchone()
            fields = {
                k: data[k]
                for k in ("lab_profile_id", "cold_equipment_id", "cold_profile_id")
            }
            result = (
                update(
                    conn,
                    "resource_controls",
                    identifier,
                    {**fields, "version": old["version"] + 1},
                )
                if old
                else insert(conn, "resource_controls", {"id": identifier, **fields})
            )
            update(
                conn,
                "resources",
                identifier,
                {"version": row["version"] + 1, "status": "QUARANTINE"},
            )
            record(
                conn,
                identifier,
                row["tenant_id"],
                "RESOURCE_CONTROLS_BOUND",
                data["reason"],
                {
                    "previous_profiles": {
                        k: str(old[k]) if old[k] else None for k in fields
                    }
                    if old
                    else None,
                    "profiles": fields,
                    "version": result["version"],
                    "previous_status": row["status"],
                    "status": "QUARANTINE",
                },
            )
            emit(conn, "RESOURCE_CONTROLS_BOUND", identifier, row["tenant_id"])
            return result

        return atomic("resource_controls:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/controls",
        roles=("MEDICAL", "OPERATOR"),
        result=schema(Controls),
    )
    def resource_controls_detail(identifier):
        with transaction() as conn:
            own(get(conn, "resources", identifier)["current_institution_id"])
            return get(conn, "resource_controls", identifier)

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/cold-readings",
        "POST",
        model=ReadingCreate,
        roles=("OPERATOR",),
        result=schema(Reading),
        status=201,
    )
    def cold_reading_create(identifier, data):
        captured = utc_date(data["captured_at"], "captured_at")
        if captured > datetime.now(timezone.utc):
            raise APIError("validation", "Lectura futura.", 422)

        def work(conn):
            resource = get(conn, "resources", identifier, True)
            own(resource["current_institution_id"])
            control = get(conn, "resource_controls", identifier)
            if not control["cold_profile_id"] or resource["status"] == "WITHDRAWN":
                raise APIError(
                    "conflict", "Perfil térmico requerido y recurso activo.", 409
                )
            profile = get(conn, "cold_profiles", str(control["cold_profile_id"]))
            last = conn.execute(
                "SELECT captured_at FROM cold_readings WHERE resource_id=%s ORDER BY captured_at DESC LIMIT 1",
                (identifier,),
            ).fetchone()
            excursion = (
                not profile["minimum_c"]
                <= data["temperature_c"]
                <= profile["maximum_c"]
            )
            gap = bool(
                last
                and abs((captured - last["captured_at"]).total_seconds())
                > profile["max_gap_seconds"]
            )
            row = insert(
                conn,
                "cold_readings",
                dict(
                    data,
                    id=str(uuid4()),
                    resource_id=identifier,
                    equipment_id=control["cold_equipment_id"],
                    profile_id=profile["id"],
                    tenant_id=g.actor["tenant_id"],
                    captured_at=captured,
                    excursion=excursion,
                    gap=gap,
                    author_id=g.actor["id"],
                ),
            )
            if excursion or gap:
                block(conn, resource, "RESOURCE_COLD_QUARANTINE")
            emit(conn, "COLD_READING_RECORDED", identifier, g.actor["tenant_id"])
            return row

        return atomic("cold_reading:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/cold-readings",
        roles=("MEDICAL", "OPERATOR"),
        paginated=True,
        result=page_schema(Reading),
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def cold_readings_list(identifier):
        with transaction() as conn:
            own(get(conn, "resources", identifier)["current_institution_id"])
            return listing(
                conn,
                "cold_readings",
                "resource_id=%s",
                (identifier,),
                order="captured_at DESC,id",
                date_columns=("captured_at", "received_at"),
            )

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/quality-review",
        "POST",
        model=QualityReview,
        roles=("MEDICAL",),
        result=schema(Controls),
    )
    def quality_review(identifier, data):
        def work(conn):
            resource = get(conn, "resources", identifier, True)
            own(resource["current_institution_id"])
            control = get(conn, "resource_controls", identifier, True)
            version(control, data["version"])
            if resource["expires_at"] <= datetime.now(timezone.utc):
                raise APIError(
                    "expired_resource", "El vencimiento impide desbloquear.", 409
                )
            insert(
                conn,
                "cold_reviews",
                {
                    "id": str(uuid4()),
                    "resource_id": identifier,
                    "tenant_id": g.actor["tenant_id"],
                    "author_id": g.actor["id"],
                    "reason": data["reason"],
                    "decision": "REVIEWED",
                },
            )
            result = update(
                conn,
                "resource_controls",
                identifier,
                {"blocked": False, "version": control["version"] + 1},
            )
            update(conn, "resources", identifier, {"version": resource["version"] + 1})
            # Revisar el incidente no libera: la ruta de liberación conserva su dictamen y controles.
            emit(conn, "QUALITY_INCIDENT_REVIEWED", identifier, g.actor["tenant_id"])
            return result

        return atomic("quality_review:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/destination",
        "POST",
        model=DestinationCreate,
        roles=("MEDICAL",),
        result=schema(Destination),
        status=201,
    )
    def resource_destination(identifier, data):
        occurred = utc_date(data["occurred_at"], "occurred_at")
        if occurred > datetime.now(timezone.utc):
            raise APIError(
                "validation", "Destino no puede registrarse en el futuro.", 422
            )

        def work(conn):
            resource = get(conn, "resources", identifier, True)
            own(resource["current_institution_id"])
            version(resource, data["version"])
            old = conn.execute(
                "SELECT * FROM resource_destinations WHERE resource_id=%s ORDER BY version DESC LIMIT 1",
                (identifier,),
            ).fetchone()
            if (str(old["id"]) if old else None) != data["supersedes"]:
                raise APIError(
                    "stale_version",
                    "Corrección debe identificar el último destino.",
                    412,
                )
            clinical_use = data["destination"] in ("TRANSFUSED", "TRANSPLANTED")
            if resource["status"] not in (
                "QUARANTINE",
                "AVAILABLE",
                "RECEIVED",
                "WITHDRAWN",
            ):
                raise APIError("conflict", "Reserva o traslado sin concluir.", 409)
            if clinical_use:
                received = (
                    resource["status"] == "RECEIVED"
                    or conn.execute(
                        "SELECT 1 FROM reservations WHERE resource_id=%s AND status='RECEIVED'",
                        (identifier,),
                    ).fetchone()
                )
                if not received or (
                    (data["destination"] == "TRANSFUSED")
                    != (resource["kind"] == "BLOOD")
                ):
                    raise APIError(
                        "conflict", "Uso incompatible con recepción o tipo.", 409
                    )
                # Una corrección exclusivamente documental conserva el hecho de uso
                # ya validado; cambiar destino o fecha constituye un nuevo hecho.
                documentary = (
                    old
                    and old["destination"] == data["destination"]
                    and old["occurred_at"] == occurred
                )
                if not documentary:
                    if resource["status"] != "RECEIVED" or resource[
                        "expires_at"
                    ] <= datetime.now(timezone.utc):
                        raise APIError(
                            "quality_block",
                            "Uso nuevo requiere una unidad recibida, vigente y fuera de cuarentena.",
                            409,
                        )
                    guard(conn, resource)
            row = insert(
                conn,
                "resource_destinations",
                {
                    "id": str(uuid4()),
                    "resource_id": identifier,
                    "tenant_id": g.actor["tenant_id"],
                    "author_id": g.actor["id"],
                    "version": old["version"] + 1 if old else 1,
                    **{
                        k: data[k]
                        for k in ("destination", "reference", "reason", "supersedes")
                    },
                    "occurred_at": occurred,
                },
            )
            update(
                conn,
                "resources",
                identifier,
                {"status": "WITHDRAWN", "version": resource["version"] + 1},
            )
            emit(
                conn,
                "RESOURCE_DESTINATION_RECORDED",
                identifier,
                g.actor["tenant_id"],
                targets=("auditoria", "alertas"),
            )
            return row

        return atomic("resource_destination:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/components",
        "POST",
        model=Fractionate,
        roles=("OPERATOR",),
        status=201,
        result={"type": "array", "items": schema(Lineage)},
    )
    def resource_fractionate(identifier, data):
        def work(conn):
            parent = get(conn, "resources", identifier, True)
            own(parent["current_institution_id"])
            version(parent, data["version"])
            if (
                parent["status"] != "QUARANTINE"
                or not parent["donation_id"]
                or parent["kind"] != "BLOOD"
            ):
                raise APIError(
                    "conflict",
                    "Fraccionamiento requiere origen sanguíneo trazable en cuarentena.",
                    409,
                )
            links = []
            for child in data["children"]:
                expires = utc_date(child["expires_at"], "expires_at")
                if expires <= datetime.now(timezone.utc):
                    raise APIError(
                        "validation", "Caducidad futura capturada requerida.", 422
                    )
                row = insert(
                    conn,
                    "resources",
                    {
                        "id": str(uuid4()),
                        "tenant_id": parent["tenant_id"],
                        "current_institution_id": parent["current_institution_id"],
                        "region_id": parent["region_id"],
                        "donation_id": parent["donation_id"],
                        "kind": "BLOOD",
                        "component": child["component"],
                        "blood_group": parent["blood_group"],
                        "folio": child["folio"],
                        "expires_at": expires,
                        "status": "QUARANTINE",
                    },
                )
                links.append(
                    insert(
                        conn,
                        "resource_lineage",
                        {
                            "id": str(uuid4()),
                            "parent_id": identifier,
                            "child_id": row["id"],
                            "donation_id": parent["donation_id"],
                            "tenant_id": g.actor["tenant_id"],
                            "author_id": g.actor["id"],
                            "reason": data["reason"],
                        },
                    )
                )
            update(
                conn,
                "resources",
                identifier,
                {"status": "WITHDRAWN", "version": parent["version"] + 1},
            )
            emit(conn, "RESOURCE_FRACTIONATED", identifier, parent["tenant_id"])
            return links

        return atomic("resource_fractionate:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/lineage",
        roles=("MEDICAL", "OPERATOR"),
        result={"type": "array", "items": schema(Lineage)},
    )
    def resource_lineage(identifier):
        with transaction() as conn:
            resource = get(conn, "resources", identifier)
            own(resource["current_institution_id"])
            return conn.execute(
                "SELECT * FROM resource_lineage WHERE donation_id=%s ORDER BY created_at,id LIMIT 500",
                (resource["donation_id"],),
            ).fetchall()
