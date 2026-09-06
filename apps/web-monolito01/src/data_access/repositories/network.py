from . import accounts
from .common import pattern, scope

ENTITIES = {
    "institutions": ("institution", "institution_id", "institution_name"),
    "sites": ("site", "site_id", "site_name"),
    "locations": ("storage_location", "location_id", "location_description"),
    "components": ("blood_component", "component_id", "component_name"),
    "users": ("user_account", "account_id", "party_name"),
}


def query_for(entity, principal):
    clause, params = scope(principal)
    if entity == "institutions":
        return "SELECT i.* FROM institution i WHERE " + clause, params
    if entity == "sites":
        return """SELECT s.*, i.institution_name, i.region_name FROM site s JOIN institution i
                  USING (institution_id) WHERE """ + clause, params
    if entity == "locations":
        return """SELECT l.*, s.site_name, s.institution_id, i.institution_name, i.region_name
                  FROM storage_location l JOIN site s USING (site_id)
                  JOIN institution i USING (institution_id) WHERE """ + clause, params
    if entity == "components":
        return "SELECT * FROM blood_component WHERE region_name = %s", [principal.region_name]
    if entity == "users":
        if principal.institution_id:
            return accounts.SELECT_ACCOUNT + " WHERE ar.institution_id = %s", [principal.institution_id]
        return accounts.SELECT_ACCOUNT + " WHERE (i.region_name = %s OR ar.region_name = %s)", [principal.region_name] * 2
    raise ValueError("Unknown entity")


def one(conn, entity, principal, identifier):
    query, params = query_for(entity, principal)
    key = ENTITIES[entity][1]
    return conn.execute(f"SELECT * FROM ({query}) permitted WHERE {key} = %s", [*params, identifier]).fetchone()


def listing(conn, entity, principal, query="", state="", page=1):
    base, params = query_for(entity, principal)
    label = ENTITIES[entity][2]
    filters = f"{label} ILIKE %s"
    params += [pattern(query)]
    if state:
        status_columns = {"institutions": "participation_status", "sites": "site_status", "users": "account_status"}
        if entity in status_columns:
            filters += f" AND {status_columns[entity]} = %s"
            params += [state]
        else:
            filters += " AND is_active = %s"
            params += [state == "ACTIVE"]
    source = f"FROM ({base}) permitted WHERE {filters}"
    count = conn.execute("SELECT count(*) AS total " + source, params).fetchone()["total"]
    rows = conn.execute(f"SELECT * {source} ORDER BY {label}, {ENTITIES[entity][1]} LIMIT 12 OFFSET %s",
                        [*params, (page - 1) * 12]).fetchall()
    # No hashes ni contraseñas se entregan a presentación.
    for row in rows:
        row.pop("password_hash", None)
    return rows, count


def options(conn, principal):
    result = {}
    for entity in ("institutions", "sites", "locations", "components"):
        query, params = query_for(entity, principal)
        rows = conn.execute(query + f" ORDER BY {ENTITIES[entity][2]}", params).fetchall()
        result[entity] = rows
    result["capabilities"] = conn.execute("SELECT * FROM capability ORDER BY capability_name").fetchall()
    return result


def institution_details(conn, identifier):
    contact = conn.execute("""SELECT c.* FROM contact c JOIN institution_contact ic USING (contact_id)
                              WHERE ic.institution_id = %s ORDER BY c.contact_id LIMIT 1""", (identifier,)).fetchone()
    data = dict(contact or {})
    if contact:
        for method in conn.execute("SELECT * FROM contact_method WHERE contact_id = %s", (contact["contact_id"],)):
            data["contact_" + method["method_kind"].lower()] = method["method_value"]
    data["capabilities"] = [r["capability_code"] for r in conn.execute(
        "SELECT capability_code FROM institution_capability WHERE institution_id = %s", (identifier,))]
    return data


def parameter(conn, region_name):
    return conn.execute("""SELECT * FROM parameter_version WHERE region_name = %s
        AND parameter_code = 'EXPIRY_WARNING_HOURS' ORDER BY version_no DESC LIMIT 1""", (region_name,)).fetchone()
