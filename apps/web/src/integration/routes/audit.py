"""Investigación y hallazgos por los mismos contratos en ambos modos del portal."""

import csv
import io
import math

from .common import (
    FIELD_LABELS,
    ROLES,
    BusinessError,
    Response,
    call,
    confirmations,
    contextual,
    field,
    g,
    local_date,
    portal,
    render_template,
    request,
    return_to,
    submit,
    table,
    url_for,
)

DEFAULT_CATEGORIES = ("BUSINESS", "DECISION", "SECURITY")
STATE_LABELS = {
    "OPEN": "Abierto",
    "IN_PROGRESS": "En atención",
    "PENDING_VERIFICATION": "Pendiente de verificación",
    "CLOSED": "Cerrado",
}
PRIORITY_LABELS = {
    "LOW": "Baja",
    "MEDIUM": "Media",
    "HIGH": "Alta",
    "CRITICAL": "Crítica",
}


def audit_filters():
    params = {
        name: request.args.get(name, "").strip()
        for name in (
            "from",
            "to",
            "action",
            "actor",
            "institution_id",
            "resource",
            "result",
            "correlation_id",
        )
    }
    selected = (
        request.args.getlist("categories")
        if request.args.get("applied")
        else list(DEFAULT_CATEGORIES)
    )
    selected = [
        part
        for value in selected
        for part in value.split(",")
        if part and part != "NONE"
    ]
    if "ALL" in selected:
        selected = ["BUSINESS", "DECISION", "SECURITY", "SESSION", "READ", "TECHNICAL"]
    params["categories"] = ",".join(selected) or "NONE"
    api = dict(params)
    for name in ("from", "to"):
        if api[name]:
            api[name] = local_date(api[name])
    return params, api, selected


def csv_response(items):
    columns = [
        ("action_label", "Acción"),
        ("actor_display", "Responsable"),
        ("tenant_id", "Institución"),
        ("resource_display", "Recurso o folio"),
        ("executed_at", "Fecha de ejecución"),
        ("result_label", "Resultado"),
    ]
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow([label for _, label in columns])
    for row in items:
        cells = []
        for key, _ in columns:
            value = row.get(key)
            if key == "tenant_id":
                value = g.institutions.get(str(value), value)
            value = str(value) if value is not None else "No registrado"
            # También bloquea fórmulas precedidas por espacio, tabulador o salto.
            cells.append(
                "'" + value
                if value.lstrip().startswith(("=", "+", "-", "@"))
                or value.startswith(("\t", "\r", "\n"))
                else value
            )
        writer.writerow(cells)
    return Response(
        "\ufeff" + stream.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=red-house-auditoria.csv"},
    )


@portal.get("/auditoria")
def audit():
    params, api, selected = audit_filters()
    options = call("auditoria", "/api/v1/event-options")
    try:
        page = int(request.args.get("page", "1"))
        if not 1 <= page <= 100000:
            raise ValueError()
    except ValueError:
        raise BusinessError("Selecciona una página válida.", 422) from None
    exporting = request.args.get("format") == "csv"
    all_results = exporting and request.args.get("scope") == "all"
    path = "/api/v1/events/export" if all_results else "/api/v1/events"
    data = call(
        "auditoria",
        path,
        params={**api, **({} if all_results else {"page": page, "page_size": 20})},
    )
    pages = max(1, math.ceil(data["total"] / 20))
    if page > pages and not all_results:
        page = pages
        data = call("auditoria", path, params={**api, "page": page, "page_size": 20})
    if exporting:
        return csv_response(data["items"])
    target = url_for("portal.audit", **params, applied="1", page=page)
    for row in data["items"]:
        row["href"] = contextual(
            url_for("portal.audit_detail", identifier=row["id"]), target
        )
    return render_template(
        "integration/audit.html",
        title="Bitácora de auditoría",
        active="audit",
        data=data,
        options=options,
        selected=selected,
        filters=params,
        page=page,
        pages=pages,
        institutions=g.institutions,
        previous=url_for("portal.audit", **params, applied="1", page=page - 1)
        if page > 1
        else None,
        next=url_for("portal.audit", **params, applied="1", page=page + 1)
        if page < pages
        else None,
        export_page=url_for(
            "portal.audit", **params, applied="1", page=page, format="csv"
        ),
        export_all=url_for(
            "portal.audit", **params, applied="1", format="csv", scope="all"
        ),
    )


@portal.get("/auditoria/<uuid:identifier>")
def audit_detail(identifier):
    row = call("auditoria", "/api/v1/events/" + str(identifier))
    related = call("auditoria", "/api/v1/events/" + str(identifier) + "/related")
    back = return_to("audit", url_for("portal.audit"))
    return render_template(
        "integration/audit_detail.html",
        title=row["action_label"],
        active="audit",
        row=row,
        related=related,
        back=back,
        roles=ROLES,
        field_labels=FIELD_LABELS,
    )


@portal.get("/hallazgos")
def findings():
    return table(
        "Hallazgos",
        "findings",
        "auditoria",
        "/api/v1/findings",
        [
            ("description", "Descripción"),
            ("priority", "Prioridad"),
            ("assignee_name", "Responsable de atención"),
            ("status", "Estado"),
            ("updated_at", "Última acción"),
        ],
        filters=("q", "status", "priority"),
        new=url_for("portal.finding_new")
        if g.principal.role_code == "AUDITOR"
        else None,
        links=lambda row: url_for("portal.finding_detail", identifier=row["id"]),
        filter_options={
            "status": list(STATE_LABELS.items()),
            "priority": list(PRIORITY_LABELS.items()),
        },
    )


@portal.route("/hallazgos/nuevo", methods=["GET", "POST"])
def finding_new():
    if g.principal.role_code != "AUDITOR":
        raise BusinessError("Solo auditoría puede registrar hallazgos.", 403)
    from ..selectors import selection

    events = call(
        "auditoria", "/api/v1/events", params={"categories": "ALL", "page_size": 100}
    )["items"]
    selected = (
        request.form.getlist("event_ids")
        if request.method == "POST"
        else ([request.args["event_id"]] if request.args.get("event_id") else [])
    )
    choices = [
        (e["id"], e["action_label"] + " · " + e["resource_display"]) for e in events
    ]
    for identifier in selected:
        if identifier not in [key for key, _ in choices]:
            choices.append((identifier, "Evento seleccionado · " + identifier))
    return submit(
        "auditoria",
        "/api/v1/findings",
        [
            field("description", "Descripción del hallazgo", "textarea"),
            field("priority", "Prioridad", "select", list(PRIORITY_LABELS.items())),
            selection(
                "assignee_id",
                "Responsable de atención",
                "audit-assignees",
                default=request.form.get("assignee_id", ""),
            ),
            field(
                "event_ids",
                "Eventos vinculados",
                "multiselect",
                choices,
                default=selected,
                required=False,
            ),
            field(
                "resource_id",
                "Referencia del recurso",
                default=request.args.get("resource", ""),
                required=False,
            ),
            field(
                "evidence",
                "Evidencia inicial o referencia documental",
                "textarea",
                required=False,
            ),
        ],
        title="Registrar hallazgo",
        active="findings",
        back=url_for("portal.findings"),
        success=lambda row: url_for("portal.finding_detail", identifier=row["id"]),
        note="Vincula un evento o un recurso de la bitácora. Describe hechos verificables y evita copiar información clínica innecesaria.",
    )


def transitions(row):
    if g.principal.role_code == "AUDITOR":
        return (
            [("CLOSED", "Verificar y cerrar"), ("IN_PROGRESS", "Devolver a atención")]
            if row["status"] == "PENDING_VERIFICATION"
            else []
        )
    if row["status"] == "OPEN":
        return [("IN_PROGRESS", "Iniciar atención")]
    if row["status"] == "IN_PROGRESS":
        return [
            ("IN_PROGRESS", "Registrar avance"),
            ("PENDING_VERIFICATION", "Enviar a verificación"),
        ]
    return []


@portal.get("/hallazgos/<uuid:identifier>")
def finding_detail(identifier):
    row = call("auditoria", "/api/v1/findings/" + str(identifier))
    return render_template(
        "integration/finding.html",
        title="Seguimiento de hallazgo",
        active="findings",
        row=row,
        states=STATE_LABELS,
        priorities=PRIORITY_LABELS,
        transitions=transitions(row),
        back=return_to("findings", url_for("portal.findings")),
    )


@portal.route("/hallazgos/<uuid:identifier>/atender/<state>", methods=["GET", "POST"])
def finding_action(identifier, state):
    row = call("auditoria", "/api/v1/findings/" + str(identifier))
    titles = {
        "IN_PROGRESS": "Registrar atención",
        "PENDING_VERIFICATION": "Enviar a verificación",
        "CLOSED": "Verificar y cerrar",
    }
    # Un reenvío después de perder la respuesta debe llegar a la idempotencia API.
    if state not in titles or (
        request.method == "GET" and state not in dict(transitions(row))
    ):
        raise BusinessError(
            "Ese cambio no está permitido en el estado actual del hallazgo.", 403
        )
    return submit(
        "auditoria",
        "/api/v1/findings/" + str(identifier) + "/actions",
        [
            field("version", "Versión", "hidden", default=row["version"]),
            field("status", "Estado", "hidden", default=state),
            field(
                "corrective_action",
                "Acción correctiva o plan de atención",
                "textarea",
                required=g.principal.role_code != "AUDITOR",
            ),
            field(
                "evidence",
                "Evidencia de la corrección o de su verificación",
                "textarea",
                required=state in ("CLOSED", "PENDING_VERIFICATION"),
            ),
            *confirmations(),
        ],
        title=dict(transitions(row)).get(state, titles[state]),
        active="findings",
        back=url_for("portal.finding_detail", identifier=identifier),
        note=row["description"],
    )
