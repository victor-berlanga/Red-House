from werkzeug.security import generate_password_hash

from .. import validators as v
from ..access import BusinessError, check_version, require
from ...data_access.connection import transaction
from ...data_access.repositories import accounts, audit, network
from ...data_access.repositories.common import insert, update

ACTIVE = ("ACTIVE", "INACTIVE")


def permitted_reference(conn, entity, principal, identifier, *, active=True):
    row = network.one(conn, entity, principal, identifier)
    if not row:
        raise BusinessError("La referencia no está disponible en tu ámbito.", 404)
    if active and (row.get("participation_status", "ACTIVE") != "ACTIVE"
                   or row.get("site_status", "ACTIVE") != "ACTIVE" or not row.get("is_active", True)):
        raise BusinessError("La referencia seleccionada está inactiva.")
    return row


def save(entity, principal, data, identifier=None):
    require(principal, "administration")
    if entity not in network.ENTITIES:
        raise BusinessError("La sección no existe.", 404)
    if entity == "components" and principal.institution_id:
        raise BusinessError("El catálogo regional requiere un administrador regional.", 403)
    table, key, _ = network.ENTITIES[entity]
    with transaction() as conn:
        before = network.one(conn, entity, principal, identifier) if identifier else None
        if identifier:
            # La escritura usa además una versión optimista; nunca sobrescribe otra edición.
            check_version(before, v.integer(data, "version_no"))
        if entity == "users":
            return save_user(conn, principal, data, identifier, before)

        values, target_institution = {}, None
        if entity == "institutions":
            if not identifier and principal.institution_id:
                raise BusinessError("Solo la administración regional puede incorporar instituciones.", 403)
            values = {
                "institution_code": v.code(data, "institution_code", "el código"),
                "institution_name": v.text(data, "institution_name", "el nombre", 160),
                "institution_type": v.choice(data, "institution_type", ("BLOOD_BANK", "HOSPITAL", "COORDINATION"), "el tipo"),
                "region_name": principal.region_name,
                "city": v.text(data, "city", "la ciudad", 100),
                "street": v.text(data, "street", "la dirección", 200),
                "participation_status": v.choice(data, "participation_status", ACTIVE, "el estado"),
            }
            if identifier == principal.institution_id and values["participation_status"] != "ACTIVE":
                raise BusinessError("No puedes desactivar la institución de tu propio acceso.", 409)
            # Valida todos los datos compuestos antes de persistir.
            contact_name = v.text(data, "contact_name", "el contacto", 120, False)
            contact_email = v.email(data, "contact_email", False)
            contact_phone = v.text(data, "contact_phone", "el teléfono", 40, False)
            capabilities = list(dict.fromkeys(data.getlist("capabilities")))
            allowed = {r["capability_code"] for r in conn.execute("SELECT capability_code FROM capability")}
            if not set(capabilities) <= allowed:
                raise BusinessError("Selecciona capacidades válidas.")
            if (contact_email or contact_phone) and not contact_name:
                raise BusinessError("Indica el nombre del contacto institucional.")
        elif entity == "components":
            values = {"component_code": v.code(data, "component_code", "el código"),
                      "component_name": v.text(data, "component_name", "el componente", 100),
                      "region_name": principal.region_name, "is_active": data.get("is_active") == "on"}
        elif entity == "sites":
            institution = permitted_reference(conn, "institutions", principal, v.identifier(data, "institution_id"))
            target_institution = institution["institution_id"]
            if before and before["institution_id"] != target_institution:
                raise BusinessError("Una sede con identidad propia no puede cambiar de institución.")
            values = {"institution_id": target_institution, "site_code": v.code(data, "site_code", "el código"),
                      "site_name": v.text(data, "site_name", "la sede"), "street": v.text(data, "street", "la dirección", 200),
                      "city": v.text(data, "city", "la ciudad", 100),
                      "site_status": v.choice(data, "site_status", ACTIVE, "el estado")}
        elif entity == "locations":
            site = permitted_reference(conn, "sites", principal, v.identifier(data, "site_id"))
            permitted_reference(conn, "institutions", principal, site["institution_id"])
            target_institution = site["institution_id"]
            if before and before["site_id"] != site["site_id"]:
                raise BusinessError("No se puede reasociar una ubicación a otra sede; crea una ubicación nueva.")
            values = {"site_id": site["site_id"], "location_code": v.code(data, "location_code", "el código"),
                      "location_description": v.text(data, "location_description", "la ubicación", 150),
                      "is_active": data.get("is_active") == "on"}

        if identifier:
            row = update(conn, table, key, identifier, values, before["version_no"])
            if not row:
                raise BusinessError("Otra persona modificó el registro. Recarga la página.", 409)
        else:
            row = insert(conn, table, values, key)
            identifier = row[key]
        if entity == "institutions":
            target_institution = identifier
            previous_details = network.institution_details(conn, identifier)
            old_contact = previous_details.get("contact_id")
            if contact_name:
                if old_contact:
                    conn.execute("UPDATE contact SET contact_name = %s WHERE contact_id = %s", (contact_name, old_contact))
                else:
                    old_contact = insert(conn, "contact", {"contact_name": contact_name, "contact_function": "Coordinación institucional"}, "contact_id")["contact_id"]
                    insert(conn, "institution_contact", {"institution_id": identifier, "contact_id": old_contact}, "contact_id")
                for kind, value in (("EMAIL", contact_email), ("PHONE", contact_phone)):
                    if value:
                        conn.execute("""INSERT INTO contact_method VALUES (%s,%s,%s)
                            ON CONFLICT (contact_id,method_kind) DO UPDATE SET method_value = excluded.method_value""", (old_contact, kind, value))
                    else:
                        conn.execute("DELETE FROM contact_method WHERE contact_id = %s AND method_kind = %s", (old_contact, kind))
            elif old_contact:
                raise BusinessError("Para conservar la referencia del contacto, mantén su nombre; puedes retirar sus medios.")
            conn.execute("DELETE FROM institution_capability WHERE institution_id = %s", (identifier,))
            for capability in capabilities:
                insert(conn, "institution_capability", {"institution_id": identifier, "capability_code": capability}, "institution_id")
            # Registra el cambio de contacto sin duplicar sus medios personales.
            values["contact_updated"] = any(previous_details.get(k, "") != val for k, val in (
                ("contact_name", contact_name), ("contact_email", contact_email), ("contact_phone", contact_phone)))
            for capability in allowed:
                values["capability_" + capability] = capability in capabilities
                if before:
                    before["capability_" + capability] = capability in previous_details["capabilities"]
            if before:
                before["contact_updated"] = False
            if values["participation_status"] == "INACTIVE":
                conn.execute("""UPDATE web_session SET revoked_at = now() WHERE revoked_at IS NULL AND
                    account_id IN (SELECT account_id FROM account_role WHERE institution_id = %s)""", (identifier,))
        audit.record(conn, principal, "UPDATE" if before else "CREATE", table.upper(), identifier,
                     "Actualización administrativa" if before else "Registro administrativo",
                     institution_id=target_institution, before={k: before.get(k) for k in values} if before else {}, after=values)
        return identifier


def save_user(conn, principal, data, identifier, before):
    name = v.text(data, "party_name", "el nombre")
    email = v.email(data)
    role = v.choice(data, "role_code", ("ADMIN", "OPERATOR", "AUDITOR"), "el perfil inicial")
    status = v.choice(data, "account_status", ACTIVE, "el estado")
    if data.get("scope") == "REGIONAL":
        if principal.institution_id or role == "OPERATOR":
            raise BusinessError("Ese perfil o ámbito no está autorizado.", 403)
        institution_id, region_name = None, principal.region_name
    else:
        target = permitted_reference(conn, "institutions", principal, v.identifier(data, "scope"))
        institution_id, region_name = target["institution_id"], None
    if identifier == principal.account_id and (status != "ACTIVE" or role != principal.role_code or
                                              institution_id != principal.institution_id):
        raise BusinessError("No puedes retirar tu propio perfil, ámbito o acceso.", 409)
    new_password = data.get("password", "")
    if not identifier or new_password:
        v.password(new_password)
    values = {"login_email": email, "account_status": status}
    if new_password:
        values["password_hash"] = generate_password_hash(new_password, method="scrypt")
    if before:
        row = update(conn, "user_account", "account_id", identifier, values, before["version_no"])
        if not row:
            raise BusinessError("La cuenta cambió. Recarga antes de guardar.", 409)
        conn.execute("UPDATE party SET party_name = %s WHERE party_id = %s", (name, before["party_id"]))
        conn.execute("UPDATE account_role SET role_code = %s, institution_id = %s, region_name = %s WHERE account_id = %s",
                     (role, institution_id, region_name, identifier))
        accounts.revoke_all(conn, identifier)
    else:
        party = insert(conn, "party", {"party_name": name}, "party_id")
        row = insert(conn, "user_account", {**values, "party_id": party["party_id"]}, "account_id")
        identifier = row["account_id"]
        insert(conn, "account_role", {"account_id": identifier, "role_code": role,
               "institution_id": institution_id, "region_name": region_name}, "account_id")
    tracked = {"account_status": status, "role_code": role, "institution_id": institution_id,
               "region_name": region_name, "password_changed": bool(new_password)}
    previous = {k: before.get(k) for k in tracked} if before else {}
    if before:
        previous["region_name"] = None if before["institution_id"] else before["region_name"]
        previous["password_changed"] = False
    audit.record(conn, principal, "UPDATE" if before else "CREATE", "USER_ACCOUNT", identifier,
                 "Cuenta y ámbito actualizados; sesiones anteriores revocadas" if before else "Cuenta creada",
                 institution_id=institution_id, before=previous, after=tracked)
    return identifier


def save_parameter(principal, data):
    require(principal, "administration")
    if principal.institution_id:
        raise BusinessError("El parámetro regional requiere un administrador regional.", 403)
    hours = v.integer(data, "hours", 1, 720)
    with transaction() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", ("expiry:" + principal.region_name,))
        previous = network.parameter(conn, principal.region_name)
        current_version = previous["version_no"] if previous else 0
        if v.integer(data, "version_no", 0) != current_version:
            raise BusinessError("El parámetro cambió. Recarga la configuración.", 409)
        row = insert(conn, "parameter_version", {"parameter_code": "EXPIRY_WARNING_HOURS",
                     "region_name": principal.region_name, "version_no": current_version + 1,
                     "scalar_value": hours, "approved_by": principal.account_id}, "parameter_version_id")
        audit.record(conn, principal, "CONFIGURE", "PARAMETER_VERSION", row["parameter_version_id"],
                     "Umbral DEMO de aviso; no modifica fechas de caducidad",
                     before={"hours": previous["scalar_value"] if previous else None}, after={"hours": hours})
