"""Indicadores de cada propietario; nunca consultan tablas de otro dominio."""

from datetime import datetime, timedelta, timezone
from flask import g, request
from pydantic import Field
from redhouse.api import endpoint
from redhouse.db import transaction
from redhouse.errors import APIError
from redhouse.extension_contracts import schema
from redhouse.models import Model, Text, utc_date


class Point(Model):
    label: Text
    value: float | None


class Series(Model):
    title: Text
    population: Text
    denominator: int
    unit: Text = "registros"
    values: list[Point] = Field(default_factory=list)


class Metrics(Model):
    from_at: Text
    until_at: Text
    updated_at: Text
    scope: Text
    series: list[Series]


ROLES = {
    "donantes": ("OPERATOR", "MEDICAL"),
    "inventario": ("OPERATOR", "MEDICAL", "COORDINATOR"),
    "receptores": ("OPERATOR", "MEDICAL"),
    "compatibilidad": ("OPERATOR", "MEDICAL"),
    "transporte": ("OPERATOR", "MEDICAL", "COORDINATOR", "TRANSPORT"),
}


def install(app, owner):
    @endpoint(
        app,
        "/api/v1/portal-metrics",
        roles=ROLES[owner],
        query=("from_at", "until_at"),
        result=schema(Metrics),
    )
    def portal_metrics():
        end = (
            utc_date(request.args["until_at"])
            if request.args.get("until_at")
            else datetime.now(timezone.utc)
        )
        start = (
            utc_date(request.args["from_at"])
            if request.args.get("from_at")
            else end - timedelta(days=30)
        )
        if not start < end or end - start > timedelta(days=366):
            raise APIError(
                "validation", "Periodo requerido: mayor de cero y hasta 366 días.", 422
            )
        actor, series = g.actor, []
        with transaction() as conn:

            def grouped(
                title, table, field, where, args, date="created_at", population=None
            ):
                rows = conn.execute(
                    f"SELECT {field}::text AS label,count(*) AS value FROM {table} WHERE ({where}) AND {date}>=%s AND {date}<%s GROUP BY {field} ORDER BY {field}",
                    (*args, start, end),
                ).fetchall()
                count = sum(r["value"] for r in rows)
                series.append(
                    dict(
                        title=title,
                        population=population or title,
                        denominator=count,
                        values=rows,
                    )
                )

            own, params = "tenant_id=%s", (actor["tenant_id"],)
            if owner == "donantes":
                grouped(
                    "Donaciones por estado",
                    "donations",
                    "status",
                    own,
                    params,
                    population="Donaciones registradas en el periodo; estado actual",
                )
            elif owner == "inventario":
                scope = (
                    "region_id=%s"
                    if actor["role"] == "COORDINATOR"
                    else "current_institution_id=%s"
                )
                ids = (
                    actor["region_id"]
                    if actor["role"] == "COORDINATOR"
                    else actor["tenant_id"],
                )
                grouped(
                    "Inventario por estado",
                    "resources",
                    "status",
                    scope,
                    ids,
                    population="Recursos creados en el periodo, incluidos retirados; estado actual",
                )
                grouped(
                    "Inventario por componente",
                    "resources",
                    "component",
                    scope,
                    ids,
                    population="Recursos creados en el periodo por componente; estado actual",
                )
                grouped(
                    "Caducidades por estado",
                    "resources",
                    "status",
                    scope,
                    ids,
                    "expires_at",
                    "Recursos cuya fecha de vencimiento cae en el periodo; no equivale a descarte documentado",
                )
                if actor["role"] != "COORDINATOR":
                    grouped(
                        "Destino vigente: uso, devolución y desperdicio",
                        "resource_destinations d",
                        "destination",
                        "d.tenant_id=%s AND NOT EXISTS (SELECT 1 FROM resource_destinations later WHERE later.resource_id=d.resource_id AND later.version>d.version)",
                        params,
                        "occurred_at",
                        "Última versión por recurso con hecho en el periodo; DISCARDED es descarte documentado",
                    )
                    grouped(
                        "Destinos documentados",
                        "resource_destinations",
                        "destination",
                        own,
                        params,
                        "occurred_at",
                        "Eventos de destino en el periodo; incluyen correcciones, no equivalen a unidades únicas",
                    )
                    grouped(
                        "Lecturas con excursión",
                        "cold_readings",
                        "excursion",
                        own,
                        params,
                        "captured_at",
                        "Lecturas capturadas en el periodo según perfil sintético registrado",
                    )
                    temp = conn.execute(
                        "SELECT count(*) AS n,min(temperature_c) AS minimum,avg(temperature_c) AS average,max(temperature_c) AS maximum FROM cold_readings WHERE tenant_id=%s AND captured_at>=%s AND captured_at<%s",
                        (*params, start, end),
                    ).fetchone()
                    series.append(
                        dict(
                            title="Temperatura registrada",
                            population="Lecturas del periodo; sin extrapolación",
                            denominator=temp["n"],
                            unit="°C",
                            values=[
                                dict(label=label, value=temp[key])
                                for key, label in (
                                    ("minimum", "Mínima"),
                                    ("average", "Media"),
                                    ("maximum", "Máxima"),
                                )
                            ],
                        )
                    )
            elif owner == "receptores":
                grouped(
                    "Solicitudes por estado",
                    "requests",
                    "status",
                    own,
                    params,
                    population="Solicitudes creadas en el periodo; estado actual",
                )
                row = conn.execute(
                    "SELECT count(*) AS n,avg(extract(epoch FROM (%s-created_at))/3600) AS hours FROM requests WHERE tenant_id=%s AND created_at>=%s AND created_at<%s AND status IN ('OPEN','IN_PROGRESS')",
                    (end, *params, start, end),
                ).fetchone()
                series.append(
                    dict(
                        title="Antigüedad de solicitudes abiertas",
                        population="Abiertas/en proceso de la cohorte, hasta fin del periodo; no tiempo clínico de atención",
                        denominator=row["n"],
                        unit="horas",
                        values=[dict(label="Media", value=row["hours"])],
                    )
                )
            elif owner == "compatibilidad":
                grouped(
                    "Calidad: revisión de resultados",
                    "lab_results",
                    "status",
                    own,
                    params,
                    population="Versiones de resultados creadas en el periodo; incluye correcciones",
                )
            elif owner == "transporte":
                if actor["role"] == "COORDINATOR":
                    own, params = "region_id=%s", (actor["region_id"],)
                elif actor["role"] == "TRANSPORT":
                    own, params = "transport_user_id=%s", (actor["id"],)
                else:
                    own, params = (
                        "origin_id=%s OR destination_id=%s",
                        (actor["tenant_id"], actor["tenant_id"]),
                    )
                grouped(
                    "Traslados por etapa",
                    "shipments",
                    "status",
                    own,
                    params,
                    "departure_at",
                    "Traslados con salida programada en el periodo; estado actual",
                )
                grouped(
                    "Cobertura por destino",
                    "shipments",
                    "destination_id",
                    own,
                    params,
                    "departure_at",
                    "Traslados con salida programada en el periodo por destino; no población regional",
                )
                row = conn.execute(
                    f"WITH cohort AS (SELECT id FROM shipments WHERE ({own}) AND departure_at>=%s AND departure_at<%s), moments AS (SELECT shipment_id,min(created_at) FILTER(WHERE state='COLLECTED') AS collected_at,min(created_at) FILTER(WHERE state='ACCEPTED') AS accepted_at FROM transitions JOIN cohort ON cohort.id=shipment_id GROUP BY shipment_id) SELECT count(*) AS n,avg(extract(epoch FROM (accepted_at-collected_at))/60) AS minutes FROM moments WHERE accepted_at IS NOT NULL AND collected_at IS NOT NULL",
                    (*params, start, end),
                ).fetchone()
                series.append(
                    dict(
                        title="Recolección a aceptación",
                        population="Traslados de la cohorte con ambos tiempos registrados",
                        denominator=row["n"],
                        unit="minutos",
                        values=[dict(label="Media observada", value=row["minutes"])],
                    )
                )
        return dict(
            from_at=start.isoformat(),
            until_at=end.isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            scope="Región"
            if actor["role"] == "COORDINATOR"
            else "Tareas propias"
            if actor["role"] == "TRANSPORT"
            else "Institución",
            series=series,
        )
