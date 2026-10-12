import csv
import io
import math
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import uuid4
from zoneinfo import ZoneInfo

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import generate_csrf
from markupsafe import Markup, escape

from ...business.access import BusinessError, require
from ...presentation.timezones import datefmt, selected_zone, ZONES
from .. import ROLES, sessions
from ..client import call
from ..presentation import (
    LISTS,
    FIELD_LABELS,
    TECHNICAL,
    return_to,
    contextual,
    grouped_facts,
    institution_label,
    edit_action,
    event_label,
    SERVICE_LABELS,
)

public = Blueprint("public", __name__)
portal = Blueprint("portal", __name__)
regional = Blueprint("regional", __name__)
inventory = Blueprint("inventory", __name__)
organs = Blueprint("organs", __name__)
admin = Blueprint("admin", __name__)

GROUPS = ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+")
COMPONENTS = (
    ("RBC-DEMO", "Eritrocitos"),
    ("KIDNEY", "Riñón"),
    ("LIVER", "Hígado"),
    ("HEART", "Corazón"),
)
LABELS = {
    "BLOOD": "Sangre",
    "ORGAN": "Órgano",
    "RBC-DEMO": "Eritrocitos",
    "KIDNEY": "Riñón",
    "LIVER": "Hígado",
    "HEART": "Corazón",
    "QUARANTINE": "Cuarentena",
    "PRELIMINARY": "Registro preliminar",
    "ELIGIBLE": "Elegible",
    "DEFERRED": "Diferido",
    "AVAILABLE": "Disponible",
    "RESERVED": "Reservado",
    "COLLECTED": "Recolectado",
    "RECEIVED": "Recibido",
    "OPEN": "Abierta",
    "IN_PROGRESS": "En atención",
    "CLOSED": "Cerrada",
    "CANCELLED": "Cancelado",
    "ACTIVE": "Activo",
    "BOOKED": "Inscrita",
    "PROCESSED": "Procesado",
    "REJECTED": "Rechazado",
    "PLANNED": "Programado",
    "PREPARED": "Preparado",
    "IN_TRANSIT": "En tránsito",
    "DELIVERED": "Entregado",
    "ACCEPTED": "Aceptado",
    "PENDING": "Pendiente",
    "COMPLETED": "Completado",
    "FAILED": "Fallido",
    "WITHDRAWN": "Retirado",
    "ACKNOWLEDGED": "Leída",
    "CREATED": "Registro inicial",
    "RELEASED": "Liberación",
    "INACTIVE": "Inactivo",
    "VOLUNTARY": "Voluntaria",
    "REPLACEMENT": "Reposición",
    "ROLLBACK_PENDING": "Compensación pendiente",
    "FAVORABLE": "Favorable",
    "UNFAVORABLE": "No favorable",
    "INCIDENT": "Incidencia",
    "up": "Disponible",
    "down": "Caído",
    "degraded": "Degradado",
    **ROLES,
}


def display(value):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Sí" if value else "No"
    if isinstance(value, (dict, list)):
        return "Información registrada"
    if isinstance(value, str):
        if value in getattr(g, "institutions", {}):
            return institution_label(g.institutions[value])
        if value in LABELS:
            return LABELS[value]
        if len(value) > 19 and value[10:11] == "T":
            try:
                return datefmt(datetime.fromisoformat(value.replace("Z", "+00:00")))
            except ValueError:
                pass
    return institution_label(value)


def display_html(value):
    """Conserva el instante UTC en HTML; CSV sigue usando display sin etiquetas."""
    if isinstance(value, str) and len(value) > 19 and value[10:11] == "T":
        try:
            captured = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if captured.tzinfo is not None:
                return Markup('<time datetime="{}" data-local-time>{}</time>').format(
                    escape(captured.isoformat()), escape(datefmt(captured))
                )
        except ValueError:
            pass
    return display(value)


def rows(service, path, **params):
    result, page = [], 1
    while True:
        batch = call(service, path, params={**params, "page_size": 100, "page": page})
        result.extend(batch["items"])
        if len(result) >= batch["total"] or not batch["items"]:
            return result
        page += 1


def find_record(service, path, identifier):
    """Busca únicamente en el listado autorizado cuando la API no tiene detalle."""
    page = 1
    while True:
        batch = call(service, path, params={"page_size": 100, "page": page})
        for row in batch["items"]:
            if str(row["id"]) == str(identifier):
                return row
        if not batch["items"] or page * 100 >= batch["total"]:
            raise BusinessError("El registro no está disponible en tu ámbito.", 404)
        page += 1


def field(name, label, type="text", options=None, default="", required=True):
    return dict(
        name=name,
        label=label,
        type=type,
        options=options or [],
        default=default,
        required=required,
    )


def choices(items, label="folio"):
    return [
        (row["id"], row.get(label) or row.get("username") or row["id"][:8])
        for row in items
    ]


def confirmations():
    return [
        field("reason", "Motivo y fundamento", "textarea"),
        field(
            "human_confirmation",
            "Confirmo que revisé y autorizo esta operación",
            "checkbox",
        ),
    ]


def local_date(value):
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            result = result.replace(tzinfo=ZoneInfo(selected_zone()))
        return result.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError):
        raise BusinessError("Revisa la fecha y hora capturadas.", 422) from None


def soon(hours=0):
    return (datetime.now(ZoneInfo(selected_zone())) + timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M"
    )


def submit(
    service,
    path,
    fields,
    *,
    method="POST",
    title="Nuevo registro",
    active="",
    back=None,
    success=None,
    note=None,
    prompt=None,
    location_capture=False,
):
    error, status = None, 200
    destination = return_to(active, back)
    if request.method == "POST":
        try:
            data = {}
            for item in fields:
                value = request.form.get(item["name"], "")
                if item["type"] == "multiselect":
                    value = request.form.getlist(item["name"])
                if not value and not item["required"]:
                    if item["name"] == "organ_type":
                        data[item["name"]] = None
                    continue
                if item["type"] == "checkbox":
                    value = value == "on"
                elif item["type"] in ("number", "integer-select") or (
                    item["type"] == "hidden" and isinstance(item["default"], int)
                ):
                    value = int(value)
                elif item["type"] == "decimal":
                    value = float(value)
                    if not math.isfinite(value):
                        raise ValueError()
                elif item["type"] == "datetime-local":
                    value = local_date(value)
                data[item["name"]] = value
            result = call(
                service,
                path,
                method,
                data,
                idem=request.form.get("idempotency_key") or uuid4().hex,
            )
            flash(title + ": operación completada.", "success")
            if request.values.get("return_to"):
                return redirect(destination)
            if success:
                return redirect(success(result))
            return redirect(back or url_for("portal.dashboard"))
        except (ValueError, TypeError):
            error, status = "Revisa los valores numéricos capturados.", 422
        except BusinessError as exc:
            error, status = exc.message, exc.status
    return render_template(
        "integration/form.html",
        title=title,
        active=active,
        fields=fields,
        error=error,
        idempotency_key=request.form.get("idempotency_key") or uuid4().hex,
        back=destination,
        return_target=request.values.get("return_to", ""),
        submit_label="Guardar cambios" if method == "PATCH" else title.split(" · ")[0],
        note=note,
        prompt=prompt,
        location_capture=location_capture,
        action_modal=request.headers.get("X-Action-Modal") == "1",
    ), status


def table(
    title,
    active,
    service,
    path,
    columns,
    *,
    params=None,
    links=None,
    actions=None,
    new=None,
    filters=(),
    note=None,
    prepare=None,
):
    params = dict(params or {})
    for name in filters:
        params[name] = request.args.get(name, "")
    try:
        page = int(request.args.get("page", 1))
        if not 1 <= page <= 100000:
            raise ValueError()
    except ValueError:
        raise BusinessError("Página inválida.", 422) from None
    data = call(service, path, params={**params, "page": page, "page_size": 20})
    pages = max(1, math.ceil(data["total"] / 20))
    if page > pages:
        page = pages
        data = call(service, path, params={**params, "page": page, "page_size": 20})
    items = data["items"]
    if prepare:
        prepare(items)
    target = request.path + (
        "?" + request.query_string.decode() if request.query_string else ""
    )
    for row in items:
        row["_href"] = contextual(links(row), target) if links else None
        row["_actions"] = [
            (label, contextual(link, target), glyph)
            for label, link, glyph in (
                actions(row) if actions else edit_action(path.rsplit("/", 1)[-1], row)
            )
        ]
        if "id" in row:
            row["reference"] = row.get("folio") or "REG-" + row["id"][:8].upper()
        row["_action_key"] = uuid4().hex
    pages = max(1, math.ceil(data["total"] / 20))
    pagination = []
    for num in sorted({1, pages, page - 1, page, page + 1}):
        if 1 <= num <= pages:
            pagination.append(
                (
                    num,
                    url_for(
                        request.endpoint, **{**request.view_args, **params, "page": num}
                    ),
                )
            )
    if request.args.get("format") == "csv":
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow([label for name, label in columns])
        for row in items:
            cells = []
            for name, label in columns:
                value = row.get(name)
                if name in ("message_code", "action"):
                    value = event_label(value)
                elif name == "source" and active == "audit":
                    value = SERVICE_LABELS.get(value, "Servicio de la plataforma")
                value = str(display(value))
                cells.append(
                    "'" + value if value.startswith(("=", "+", "-", "@")) else value
                )
            writer.writerow(cells)
        return Response(
            "\ufeff" + stream.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=red-house-listado.csv"
            },
        )
    return render_template(
        "integration/list.html",
        title=title,
        active=active,
        rows=items,
        columns=columns,
        total=data["total"],
        page=page,
        pages=pages,
        pagination=pagination,
        previous_page=dict(pagination).get(page - 1),
        next_page=dict(pagination).get(page + 1),
        new=contextual(new, target),
        new_label=LISTS.get(active, ("", "", "Registrar"))[2],
        filters=filters,
        filter_options=filter_choices(active),
        groups=GROUPS,
        refresh_enabled=active
        in (
            "inventory",
            "organos",
            "disponibilidad",
            "solicitudes",
            "traslados",
            "alertas",
        ),
        note=note,
        has_actions=any(row["_href"] or row["_actions"] for row in items),
        export=url_for(
            request.endpoint,
            **{**request.view_args, **params, "page": page, "format": "csv"},
        ),
    )


def facts(row):
    labels = {
        **FIELD_LABELS,
        "folio": "Folio",
        "display_name": "Nombre",
        "username": "Cuenta",
        "blood_group": "ABO / Rh",
        "kind": "Recurso",
        "component": "Componente",
        "organ_type": "Órgano",
        "status": "Estado",
        "version": "Versión",
        "studies": "Estudios documentales",
        "expires_at": "Caducidad capturada",
        "created_at": "Registro",
        "collected_at": "Recolección",
        "quantity": "Cantidad solicitada",
        "urgency": "Urgencia capturada (1–3)",
        "departure_at": "Salida prevista",
        "eta": "Llegada prevista",
        "inventory_pending": "Confirmación de inventario pendiente",
        "origin_id": "Origen",
        "destination_id": "Destino",
        "current_institution_id": "Ubicación institucional actual",
        "algorithm_version": "Versión de la regla",
        "elapsed_ms": "Procesamiento (ms)",
        "reason": "Fundamento",
        "decision": "Dictamen",
        "restrictions": "Restricciones",
        "background": "Antecedentes",
        "requirement": "Requerimiento",
        "donation_kind": "Tipo de donación",
        "consent_reference": "Referencia del consentimiento",
        "consent_at": "Fecha del consentimiento",
        "location_id": "Ubicación",
        "source": "Procedencia",
        "distance_km": "Distancia estimada (km)",
        "travel_minutes": "Tiempo estimado (min)",
        "active": "Activo",
        "role": "Perfil",
        "action": "Acción",
        "occurred_at": "Fecha",
        "last_error": "Último error",
    }
    result = []
    for name, label in labels.items():
        if name not in row:
            continue
        value = row[name]
        if name in ("action", "message_code"):
            value = event_label(value)
        elif name == "source" and value in SERVICE_LABELS:
            value = SERVICE_LABELS[value]
        result.append((label, reference_value(name, value)))
    return result


def reference_value(name, value):
    """Resuelve referencias por las API autorizadas, sin acceso directo a datos."""
    if not value:
        return value
    sources = {
        "donor_id": (
            "donantes",
            "donors",
            "regional.person_detail",
            {"kind": "donor"},
            ("OPERATOR", "MEDICAL", "DONOR"),
        ),
        "recipient_id": (
            "receptores",
            "recipients",
            "regional.person_detail",
            {"kind": "recipient"},
            ("MEDICAL",),
        ),
        "resource_id": (
            "inventario",
            "resources",
            "inventory.detail",
            {},
            ("OPERATOR", "MEDICAL", "COORDINATOR"),
        ),
        "request_id": (
            "receptores",
            "requests",
            "regional.request_detail",
            {},
            ("OPERATOR", "MEDICAL"),
        ),
    }
    if name not in sources:
        return value
    service, path, endpoint, args, allowed = sources[name]
    if g.principal.role_code not in allowed:
        return {"_label": FIELD_LABELS[name] + " · " + str(value)[:8].upper()}
    cache = g.setdefault("reference_labels", {})
    key = (name, str(value))
    if key not in cache:
        try:
            related = call(service, "/api/v1/" + path + "/" + str(value))
            cache[key] = {
                "_label": related.get("display_name")
                or related.get("folio")
                or FIELD_LABELS[name] + " · " + str(value)[:8].upper(),
                "_href": url_for(endpoint, identifier=value, **args),
            }
        except BusinessError as exc:
            if exc.status not in (403, 404, 503):
                raise
            cache[key] = {"_label": FIELD_LABELS[name] + " · " + str(value)[:8].upper()}
    return cache[key]


def detail(title, active, row, actions=(), sections=(), note=None):
    sections = list(sections)
    if row.get("decisions") and not any(
        label == "Decisiones registradas" for label, items in sections
    ):
        sections.append(("Decisiones registradas", row["decisions"]))
    prepared = facts(row)
    return render_template(
        "integration/detail.html",
        title=institution_label(title),
        active=active,
        facts=prepared,
        fact_groups=grouped_facts(row, prepared),
        record=row,
        back=return_to(active),
        full_url=contextual(request.path, return_to(active)),
        actions=[
            (label, contextual(link, return_to(active))) for label, link in actions
        ],
        sections=sections,
        note=note,
    )


def person_extra(kind):
    fields = [
        field("restrictions", "Restricciones documentadas", "textarea", required=False)
    ]
    if kind == "donor":
        fields += [
            field(
                "background", "Antecedentes documentales", "textarea", required=False
            ),
            field(
                "donation_kind",
                "Tipo de donación",
                "select",
                [("VOLUNTARY", "Voluntaria"), ("REPLACEMENT", "Reposición")],
                required=False,
            ),
            field("consent_reference", "Referencia del consentimiento", required=False),
            field(
                "consent_at",
                "Fecha del consentimiento",
                "datetime-local",
                required=False,
            ),
        ]
    else:
        fields += [
            field(
                "requirement", "Requerimiento documentado", "textarea", required=False
            ),
            field(
                "status",
                "Estado del expediente",
                "select",
                [("ACTIVE", "Activo"), ("INACTIVE", "Inactivo")],
                default="ACTIVE",
                required=False,
            ),
        ]
    return fields


def location_field(name="location_id"):
    from ..selectors import selection

    return selection(name, "Ubicación de almacenamiento", "locations", required=False)


def filter_choices(active):
    states = {
        "inventory": [
            "QUARANTINE",
            "AVAILABLE",
            "RESERVED",
            "IN_TRANSIT",
            "RECEIVED",
            "WITHDRAWN",
        ],
        "organos": [
            "QUARANTINE",
            "AVAILABLE",
            "RESERVED",
            "IN_TRANSIT",
            "RECEIVED",
            "WITHDRAWN",
        ],
        "solicitudes": ["OPEN", "IN_PROGRESS", "CLOSED", "CANCELLED"],
        "donaciones": ["COLLECTED", "PROCESSED", "REJECTED"],
        "donantes": ["PRELIMINARY", "ELIGIBLE", "DEFERRED"],
    }
    return {
        "status": [(v, display(v)) for v in states.get(active, [])],
        "kind": [(v, display(v)) for v in ("BLOOD", "ORGAN")],
        "role": list(ROLES.items()),
        "blood_group": [(v, v) for v in GROUPS],
        "component": list(COMPONENTS if active == "organos" else COMPONENTS[:1]),
        "expiry": [
            ("soon", "Próximas 48 horas"),
            ("expired", "Fecha vencida"),
            ("later", "Después de 48 horas"),
        ],
        "active": [("true", "Activo"), ("false", "Inactivo")],
        "current_institution_id": list(getattr(g, "institutions", {}).items()),
    }
