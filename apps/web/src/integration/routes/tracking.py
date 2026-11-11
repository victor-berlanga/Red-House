"""Mapa autorizado; la autoridad y el historial permanecen en Transporte."""

import os
import re
from urllib.parse import urlsplit
from flask import current_app, g, jsonify, render_template

from .common import (
    BusinessError,
    call,
    regional,
    field,
    confirmations,
    submit,
    table,
    rows,
    url_for,
    soon,
)
from .conservation import permit


def map_provider():
    def configured(name, default):
        return current_app.config.get(name, os.environ.get(name, default))

    tile_url = configured(
        "MAP_TILE_URL", "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    )
    attribution_url = configured(
        "MAP_ATTRIBUTION_URL", "https://www.openstreetmap.org/copyright"
    )
    for value in (tile_url, attribution_url):
        part = urlsplit(value)
        if (
            part.scheme != "https"
            or part.username
            or part.password
            or part.fragment
            or not re.fullmatch(r"[A-Za-z0-9.-]+", part.hostname or "")
        ):
            raise BusinessError(
                "Proveedor cartográfico no configurado correctamente.", 503
            )
    if not all("{" + key + "}" in tile_url for key in ("x", "y", "z")):
        raise BusinessError(
            "La plantilla cartográfica requiere coordenadas de mosaico.", 503
        )
    g.map_tile_origin = "https://" + urlsplit(tile_url).netloc
    return dict(
        url=tile_url,
        name=configured("MAP_PROVIDER_NAME", "OpenStreetMap"),
        attribution=configured("MAP_ATTRIBUTION", "© OpenStreetMap contributors"),
        attribution_url=attribution_url,
        updated_at=configured(
            "MAP_UPDATED_AT", "El proveedor no publica fecha exacta por zona"
        ),
    )


@regional.get("/traslados/<uuid:identifier>/mapa")
def shipment_tracking(identifier):
    path = f"/api/v1/shipments/{identifier}"
    shipment = call("transporte", path)
    snapshot = call("transporte", path + "/tracking/snapshot")
    # Ventana inicial acotada; el socket recupera lo posterior al cursor obtenido.
    if snapshot["head"]:
        try:
            snapshot = call(
                "transporte",
                path + "/tracking/snapshot",
                params={"cursor": max(0, snapshot["head"] - 100)},
            )
        except BusinessError as exc:
            if exc.status != 409:
                raise
    anchors = []
    for key, label in (("origin_id", "Origen"), ("destination_id", "Destino")):
        location = call(
            "identidad_acceso", f"/api/v1/institutions/{shipment[key]}/presentation"
        )
        anchors.append(
            dict(
                location,
                label=label,
                name=getattr(g, "institutions", {}).get(shipment[key], label),
            )
        )
    policy = call("identidad_acceso", "/api/v1/portal-policy")
    return render_template(
        "integration/tracking.html",
        title="Seguimiento en Nuevo León",
        active="traslados",
        identifier=str(identifier),
        snapshot=snapshot,
        anchors=anchors,
        policy=policy,
        provider=map_provider(),
    )


@regional.post("/traslados/<uuid:identifier>/mapa/acceso")
def tracking_access(identifier):
    return jsonify(
        call(
            "transporte",
            f"/api/v1/shipments/{identifier}/tracking/ticket",
            method="POST",
        )
    )


@regional.get("/traslados/<uuid:identifier>/rastreo")
def tracking_assignments(identifier):
    return table(
        "Asignaciones de rastreo",
        "traslados",
        "transporte",
        f"/api/v1/shipments/{identifier}/tracking/assignments",
        [
            ("responsible_id", "Responsable"),
            ("starts_at", "Inicio"),
            ("ends_at", "Fin"),
            ("active", "Vigente"),
        ],
        new=url_for("regional.tracking_assign", identifier=identifier)
        if g.principal.role_code == "COORDINATOR"
        else None,
        actions=lambda r: (
            [
                (
                    "Revocar",
                    url_for(
                        "regional.tracking_revoke",
                        identifier=identifier,
                        assignment_id=r["id"],
                    ),
                    "",
                )
            ]
            if r["active"] and g.principal.role_code == "COORDINATOR"
            else []
        ),
    )


@regional.route("/traslados/<uuid:identifier>/rastreo/asignar", methods=["GET", "POST"])
def tracking_assign(identifier):
    permit("COORDINATOR")
    shipment = call("transporte", f"/api/v1/shipments/{identifier}")
    devices = call("transporte", f"/api/v1/shipments/{identifier}/tracking/devices")[
        "items"
    ]
    return submit(
        "transporte",
        f"/api/v1/shipments/{identifier}/tracking/assignments",
        [
            field("version", "Versión", "hidden", default=shipment["version"]),
            field(
                "device_id",
                "Emisor del transportista asignado",
                "select",
                [(r["id"], r["label"] + " · " + r["source"]) for r in devices],
            ),
            field("starts_at", "Inicio autorizado", "datetime-local", default=soon(-1)),
            field("ends_at", "Fin autorizado", "datetime-local", default=soon(1)),
        ]
        + confirmations(),
        title="Asignar rastreo a la orden",
        active="traslados",
        back=url_for("regional.tracking_assignments", identifier=identifier),
    )


@regional.route(
    "/traslados/<uuid:identifier>/rastreo/<uuid:assignment_id>/revocar",
    methods=["GET", "POST"],
)
def tracking_revoke(identifier, assignment_id):
    permit("COORDINATOR")
    assignments = rows(
        "transporte", f"/api/v1/shipments/{identifier}/tracking/assignments"
    )
    row = next((r for r in assignments if r["id"] == str(assignment_id)), None)
    if row is None:
        raise BusinessError("Asignación no disponible en esta orden.", 404)
    return submit(
        "transporte",
        f"/api/v1/tracking/assignments/{assignment_id}/revoke",
        [field("version", "Versión", "hidden", default=row["version"])]
        + confirmations(),
        title="Revocar asignación de rastreo",
        active="traslados",
        back=url_for("regional.tracking_assignments", identifier=identifier),
    )
