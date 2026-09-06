from datetime import datetime, timezone

from .. import validators as v
from ..access import BusinessError, check_version, require
from .administration import permitted_reference
from ...data_access.connection import transaction
from ...data_access.repositories import audit, inventory as repo
from ...data_access.repositories.common import insert


def valid_location(conn, principal, identifier):
    location = permitted_reference(conn, "locations", principal, identifier)
    permitted_reference(conn, "sites", principal, location["site_id"])
    permitted_reference(conn, "institutions", principal, location["institution_id"])
    return location


def create(principal, data):
    require(principal, "inventory.write")
    code = v.code(data, "traceability_code", "el folio DEMO")
    collected, expires = v.timestamp(data, "collected_at"), v.timestamp(data, "expires_at")
    now = datetime.now(timezone.utc)
    if collected > now or expires <= collected:
        raise BusinessError("La recolección no puede ser futura y la caducidad debe ser posterior a ella.")
    state = v.choice(data, "current_status", ("AVAILABLE", "QUARANTINED"), "el estado DEMO")
    if state == "AVAILABLE" and expires <= now:
        raise BusinessError("Una unidad vencida no puede registrarse como disponible.")
    group = v.choice(data, "recorded_group_code", repo.GROUPS, "el grupo registrado")
    source = v.text(data, "source_reference", "la referencia ficticia del dato")
    reason = v.text(data, "reason", "el motivo", 240)
    with transaction() as conn:
        location = valid_location(conn, principal, v.identifier(data, "location_id"))
        component = permitted_reference(conn, "components", principal, v.identifier(data, "component_id"))
        row = insert(conn, "resource", {"traceability_code": code}, "resource_id")
        identifier = row["resource_id"]
        unit = insert(conn, "blood_unit", {"resource_id": identifier, "component_id": component["component_id"],
                      "location_id": location["location_id"], "collected_at": collected, "expires_at": expires,
                      "current_status": state}, "resource_id")
        insert(conn, "blood_classification", {"resource_id": identifier, "recorded_group_code": group,
               "source_reference": source}, "resource_id")
        insert(conn, "blood_movement", {"resource_id": identifier, "sequence": 1, "new_status": state,
               "destination_location_id": location["location_id"], "actor_id": principal.account_id,
               "reason": reason}, "movement_id")
        audit.record(conn, principal, "CREATE", "BLOOD_UNIT", identifier, reason,
                     institution_id=location["institution_id"], after={"traceability_code": code,
                     "component_id": component["component_id"], "location_id": location["location_id"],
                     "current_status": state, "collected_at": collected, "expires_at": expires})
        return identifier


def change(principal, identifier, data):
    require(principal, "inventory.write")
    reason = v.text(data, "reason", "el motivo del movimiento", 240)
    state = v.choice(data, "current_status", ("AVAILABLE", "QUARANTINED", "WITHDRAWN"), "el estado DEMO")
    with transaction() as conn:
        existing = repo.one(conn, principal, identifier)
        if not existing:
            raise BusinessError("La unidad no está disponible en tu ámbito.", 404)
        # Lock del agregado: historial secuencial y cambio de estado indivisibles.
        locked = conn.execute("SELECT * FROM blood_unit WHERE resource_id = %s FOR UPDATE", (identifier,)).fetchone()
        check_version(locked, v.integer(data, "version_no"))
        if locked["current_status"] == "WITHDRAWN":
            raise BusinessError("Una unidad dada de baja no admite nuevos movimientos.", 409)
        location = valid_location(conn, principal, v.identifier(data, "location_id"))
        if location["institution_id"] != existing["institution_id"]:
            raise BusinessError("Los traslados interinstitucionales pertenecen al módulo futuro.", 403)
        if state == "AVAILABLE":
            permitted_reference(conn, "components", principal, locked["component_id"])
            if locked["expires_at"] <= datetime.now(timezone.utc):
                raise BusinessError("Una unidad vencida no puede pasar a disponible.", 409)
        previous = locked["current_status"]
        if state != previous:
            allowed = conn.execute("SELECT 1 FROM blood_status_transition WHERE previous_status = %s AND new_status = %s",
                                   (previous, state)).fetchone()
            if not allowed:
                raise BusinessError("La transición no está configurada para el flujo DEMO.", 409)
        elif location["location_id"] == locked["location_id"]:
            raise BusinessError("No hay un cambio de estado o ubicación que guardar.")
        conn.execute("UPDATE blood_unit SET current_status = %s, location_id = %s, version_no = version_no + 1 WHERE resource_id = %s",
                     (state, location["location_id"], identifier))
        sequence = conn.execute("SELECT coalesce(max(sequence),0) + 1 AS next FROM blood_movement WHERE resource_id = %s", (identifier,)).fetchone()["next"]
        insert(conn, "blood_movement", {"resource_id": identifier, "sequence": sequence,
               "previous_status": previous, "new_status": state, "origin_location_id": locked["location_id"],
               "destination_location_id": location["location_id"], "actor_id": principal.account_id,
               "reason": reason}, "movement_id")
        audit.record(conn, principal, "MOVE", "BLOOD_UNIT", identifier, reason,
                     institution_id=existing["institution_id"],
                     before={"current_status": previous, "location_id": locked["location_id"]},
                     after={"current_status": state, "location_id": location["location_id"]})


def details(principal, identifier):
    require(principal, "inventory.read")
    with transaction() as conn:
        row = repo.one(conn, principal, identifier)
        if not row:
            raise BusinessError("La unidad no está disponible en tu ámbito.", 404)
        history = conn.execute("""SELECT m.*, p.party_name, l.location_description FROM blood_movement m
            JOIN user_account u ON u.account_id = m.actor_id JOIN party p USING (party_id)
            JOIN storage_location l ON l.location_id = m.destination_location_id
            WHERE m.resource_id = %s ORDER BY m.sequence DESC""", (identifier,)).fetchall()
        audit.record(conn, principal, "READ", "BLOOD_UNIT", identifier, "Consulta de trazabilidad DEMO",
                     institution_id=row["institution_id"])
        return row, history
