from .common import pattern, scope

STATUSES = {"AVAILABLE": "Disponible", "QUARANTINED": "Cuarentena DEMO", "WITHDRAWN": "Baja",
            "EXPIRED": "Vencida", "UNAVAILABLE": "Referencia inactiva"}
VISIBLE_STATUSES = {key: label for key, label in STATUSES.items() if key != "WITHDRAWN"}
GROUPS = ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+")


def listing(conn, principal, filters, hours, page=1):
    clause, params = scope(principal, "v")
    clause += " AND v.current_status <> 'WITHDRAWN'"
    clause += " AND (v.traceability_code ILIKE %s OR v.component_name ILIKE %s)"
    params += [pattern(filters.get("q", ""))] * 2
    for name in ("institution_id", "component_id", "effective_status", "recorded_group_code"):
        value = filters.get(name)
        if value:
            clause += f" AND v.{name} = %s"
            params += [value]
    if filters.get("expiry") == "soon":
        clause += " AND v.is_available AND v.expires_at <= now() + %s * interval '1 hour'"
        params += [hours]
    elif filters.get("expiry") == "expired":
        clause += " AND v.effective_status = 'EXPIRED'"
    source = " FROM blood_inventory v WHERE " + clause
    count = conn.execute("SELECT count(*) AS total" + source, params).fetchone()["total"]
    rows = conn.execute("SELECT v.*" + source + " ORDER BY expires_at, resource_id LIMIT 12 OFFSET %s",
                        [*params, (page - 1) * 12]).fetchall()
    return rows, count


def one(conn, principal, identifier):
    clause, params = scope(principal, "v")
    return conn.execute("SELECT * FROM blood_inventory v WHERE " + clause + " AND resource_id = %s",
                        [*params, identifier]).fetchone()


def summary(conn, principal, hours):
    clause, params = scope(principal, "v")
    clause += " AND v.current_status <> 'WITHDRAWN'"
    totals = conn.execute("""SELECT count(*) AS total, count(*) FILTER (WHERE is_available) AS available,
        count(*) FILTER (WHERE effective_status = 'EXPIRED') AS expired,
        count(*) FILTER (WHERE effective_status = 'QUARANTINED') AS quarantined,
        count(*) FILTER (WHERE is_available AND expires_at <= now() + %s * interval '1 hour') AS soon
        FROM blood_inventory v WHERE """ + clause, [hours, *params]).fetchone()
    groups = conn.execute("""SELECT recorded_group_code AS label, count(*) AS value
        FROM blood_inventory v WHERE """ + clause + " AND is_available GROUP BY recorded_group_code", params).fetchall()
    urgent = conn.execute("""SELECT * FROM blood_inventory v WHERE """ + clause + """
        AND is_available AND expires_at <= now() + %s * interval '1 hour'
        ORDER BY expires_at, resource_id LIMIT 5""", [*params, hours]).fetchall()
    return totals, groups, urgent
