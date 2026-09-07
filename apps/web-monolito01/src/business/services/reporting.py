from ..access import require
from ...data_access.connection import transaction
from ...data_access.repositories import audit, inventory, network
from ...data_access.repositories.common import pattern, scope


def dashboard(principal):
    require(principal, "dashboard")
    with transaction() as conn:
        parameter = network.parameter(conn, principal.region_name)
        hours = parameter["scalar_value"] if parameter else 72
        result = {"hours": hours, "parameter": parameter, "chart": [], "urgent": [], "recent": []}
        if principal.role_code == "ADMIN":
            result["stats"] = []
            for entity, label in (("institutions", "Instituciones"), ("users", "Usuarios"),
                                  ("sites", "Sedes"), ("components", "Componentes")):
                query, params = network.query_for(entity, principal)
                count = conn.execute("SELECT count(*) AS total FROM (" + query + ") permitted", params).fetchone()["total"]
                result["stats"].append({"label": label, "value": count, "icon": "building-2" if entity != "users" else "users"})
                result["chart"].append({"label": label, "value": count})
            result["institutions"], _ = network.listing(conn, "institutions", principal)
            result["chart_title"] = "Configuración de tu red"
        else:
            totals, groups, urgent = inventory.summary(conn, principal, hours)
            result["stats"] = [
                {"label": "Unidades registradas", "value": totals["total"], "icon": "package"},
                {"label": "Disponibles", "value": totals["available"], "icon": "droplet"},
                {"label": "Próximas a vencer", "value": totals["soon"], "icon": "clock"},
                {"label": "Vencidas", "value": totals["expired"], "icon": "triangle-alert"},
            ]
            counts = {r["label"]: r["value"] for r in groups}
            result["chart"] = [{"label": k, "value": counts.get(k, 0)} for k in inventory.GROUPS]
            result["urgent"] = urgent
            result["chart_title"] = "Unidades disponibles por grupo registrado"
            clause, params = scope(principal, "v")
            result["recent"] = conn.execute("SELECT * FROM blood_inventory v WHERE " + clause +
                " AND v.current_status <> 'WITHDRAWN'" +
                " ORDER BY registered_at DESC, resource_id DESC LIMIT 5", params).fetchall()
        audit.record(conn, principal, "READ", "DASHBOARD", "SUMMARY", "Consulta del panel del ámbito autorizado")
        return result


def audit_list(principal, filters, page):
    require(principal, "audit.read")
    with transaction() as conn:
        if principal.institution_id:
            clause, params = "a.institution_id = %s", [principal.institution_id]
        else:
            clause, params = "a.region_name = %s", [principal.region_name]
        query = filters.get("q", "")
        clause += " AND (a.entity_reference ILIKE %s OR a.action ILIKE %s OR a.entity_type ILIKE %s)"
        params += [pattern(query)] * 3
        if filters.get("outcome"):
            clause += " AND a.outcome = %s"
            params += [filters["outcome"]]
        if filters.get("date"):
            clause += " AND a.occurred_at >= %s::date AND a.occurred_at < %s::date + interval '1 day'"
            params += [filters["date"]] * 2
        source = " FROM audit_event a LEFT JOIN user_account u ON u.account_id = a.actor_id LEFT JOIN party p USING (party_id) WHERE " + clause
        total = conn.execute("SELECT count(*) AS total" + source, params).fetchone()["total"]
        rows = conn.execute("SELECT a.*, coalesce(p.party_name, 'No identificado') AS actor_name" + source +
                            " ORDER BY a.occurred_at DESC, a.event_id DESC LIMIT 12 OFFSET %s", [*params, (page - 1) * 12]).fetchall()
        for row in rows:
            row["changes"] = conn.execute("SELECT * FROM audit_change WHERE event_id = %s ORDER BY field_name", (row["event_id"],)).fetchall()
        audit.record(conn, principal, "READ", "AUDIT_EVENT", "LIST", "Consulta paginada de bitácora")
        return rows, total
