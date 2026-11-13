"""Operaciones móviles sobre el traslado asignado; sin reglas clínicas en el cliente."""
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from flask import g
from redhouse.api import endpoint, atomic
from redhouse.db import transaction, get, insert, update
from redhouse.client import call
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema, version
from redhouse.models import Model, ID, Confirm, Text
from .routes import shipment_access
from .tracking import Assignment, AssignmentChange, ACTIVE


class Scan(Model):
    scanned_resource_id: ID


class ScanResult(Model):
    shipment_id: ID
    resource_id: ID
    origin_id: ID
    destination_id: ID
    version: int
    status: str
    verified: bool


class PhoneTracking(AssignmentChange):
    device_id: ID


class OperationalContact(Model):
    id: ID
    name: Text
    value: Text
    version: int


class HandoverPerson(Model):
    id: ID
    name: Text


class OperationalInstitution(Model):
    id: ID
    name: Text
    contacts: list[OperationalContact]
    operators: list[HandoverPerson]


class PlannedRoute(Model):
    id: ID
    reserved_version: int
    current_version: int
    changed: bool
    distance_km: float
    travel_minutes: int
    source: Text
    updated_at: Text


class OperationalContext(Model):
    shipment_id: ID
    shipment_version: int
    origin: OperationalInstitution
    destination: OperationalInstitution
    route: PlannedRoute
    transport_user_id: ID
    consulted_at: Text


class OperationalHandover(Model):
    shipment_id: ID
    shipment_version: int
    transport_user: HandoverPerson


def install(app):
    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/operational-handover",
        roles=("TRANSPORT", "OPERATOR", "COORDINATOR"),
        result=schema(OperationalHandover),
        summary="Identidad operativa mínima del transportista de la tarea autorizada",
    )
    def operational_handover(identifier):
        with transaction() as conn:
            row = get(conn, "shipments", identifier)
            shipment_access(row)
        person = call(
            "identidad_acceso", "GET",
            f"/internal/v1/transport-users/{row['transport_user_id']}/operational-name",
        )
        if person["id"] != str(row["transport_user_id"]):
            raise APIError("conflict", "La identidad operativa no corresponde a la tarea.", 409)
        with transaction() as conn:
            current = get(conn, "shipments", identifier)
            shipment_access(current)
            fields = ("version", "transport_user_id", "origin_id", "destination_id", "region_id")
            if any(current[field] != row[field] for field in fields):
                raise APIError("stale_version", "La tarea cambió; vuelve a consultar.", 409)
            emit(conn, "SHIPMENT_OPERATIONAL_HANDOVER_READ", identifier, row["origin_id"])
        return {
            "shipment_id": identifier,
            "shipment_version": row["version"],
            "transport_user": person,
        }

    @endpoint(app,"/api/v1/shipments/<identifier>/operational-context",
              roles=("TRANSPORT","OPERATOR","COORDINATOR"),result=schema(OperationalContext),
              summary="Contactos operativos y ruta vinculada a la tarea autorizada; sin expediente clínico")
    def operational_context(identifier):
        with transaction() as conn:
            row=get(conn,"shipments",identifier);shipment_access(row)
        origin=call("identidad_acceso","GET",f"/internal/v1/institutions/{row['origin_id']}/operational-contacts")
        destination=call("identidad_acceso","GET",f"/internal/v1/institutions/{row['destination_id']}/operational-contacts")
        reference=call("inventario","POST",f"/internal/v1/reservations/{row['reservation_id']}/logistics",{"shipment_id":identifier,"check_quality":False},delegate=False)
        route=call("priorizacion_geografia","GET",f"/internal/v1/routes/{reference['route_id']}")
        with transaction() as conn:
            # Reauthorize after remote reads in case the assignment changed concurrently.
            current=get(conn,"shipments",identifier);shipment_access(current)
            if current["version"]!=row["version"]:
                raise APIError("stale_version","La tarea cambió; vuelve a consultar.",409)
            emit(conn,"SHIPMENT_OPERATIONAL_CONTEXT_READ",identifier,row["origin_id"])
        return dict(shipment_id=identifier,shipment_version=row["version"],origin=origin,destination=destination,
                    transport_user_id=str(row["transport_user_id"]),consulted_at=datetime.now(timezone.utc).isoformat(),
                    route=dict(id=route["id"],reserved_version=reference["route_version"],current_version=route["version"],
                               changed=route["version"]!=reference["route_version"],distance_km=route["distance_km"],
                               travel_minutes=route["travel_minutes"],source=route["source"],updated_at=route["updated_at"]))

    @endpoint(app, "/api/v1/shipments/<identifier>/scan", "POST", model=Scan,
              roles=("TRANSPORT", "OPERATOR"), result=schema(ScanResult))
    def shipment_scan(identifier, data):
        from flask import request
        from redhouse.codec import representation

        def authorized(conn, *, lock=False):
            row = get(conn, "shipments", identifier, lock)
            shipment_access(row)
            if row["status"] in ("ACCEPTED", "CANCELLED", "REJECTED"):
                raise APIError("conflict", "Traslado finalizado.", 409)
            return row

        with transaction() as conn:
            observed = authorized(conn)
        check = call("inventario", "POST", f"/internal/v1/reservations/{observed['reservation_id']}/custody-check",
                     {"shipment_id": identifier, "check_quality": False}, delegate=False)
        if check["resource_id"] != data["scanned_resource_id"]:
            raise APIError("custody_mismatch", "El código no pertenece a la tarea.", 409)

        def current(conn):
            row = authorized(conn, lock=True)
            fields = ("version", "status", "reservation_id", "origin_id", "destination_id", "region_id", "transport_user_id")
            if any(row[field] != observed[field] for field in fields):
                raise APIError("stale_version", "El traslado cambió; vuelve a consultar.", 409)
            return row

        def work(conn):
            row = current(conn)
            emit(conn, "SHIPMENT_RESOURCE_IDENTIFIER_VERIFIED", identifier, row["origin_id"],
                 metadata={"request_representation": "xml" if request.mimetype in ("application/xml", "text/xml") else "json",
                           "response_representation": representation()})
            return dict(shipment_id=identifier, resource_id=check["resource_id"], origin_id=row["origin_id"],
                        destination_id=row["destination_id"], version=row["version"], status=row["status"], verified=True)

        result = atomic("shipment_scan:" + identifier, data, work)
        # La respuesta guardada puede preceder cambios de autorización o estado.
        with transaction() as conn:
            row = current(conn)
            if row["version"] != result["version"] or row["status"] != result["status"] or result["resource_id"] != check["resource_id"]:
                raise APIError("stale_version", "La verificación previa quedó obsoleta.", 409)
        return result

    @endpoint(app,"/api/v1/shipments/<identifier>/tracking/mobile-session","POST",model=PhoneTracking,
              roles=("TRANSPORT",),result=schema(Assignment))
    def mobile_tracking_start(identifier,data):
        def work(conn):
            shipment=get(conn,"shipments",identifier,True);shipment_access(shipment)
            version(shipment,data["version"])
            device=get(conn,"tracking_devices",data["device_id"])
            now=datetime.now(timezone.utc)
            if shipment["status"] not in ACTIVE or str(device["user_id"])!=g.actor["id"] or str(device["tenant_id"])!=g.actor["tenant_id"] or device["source"] not in ("ANDROID","IOS") or not device["active"] or device["expires_at"]<=now:
                raise APIError("forbidden","Teléfono o tarea no autorizados.",403)
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,92))", (data["device_id"],))
            conn.execute("UPDATE tracking_assignments SET active=false,version=version+1 WHERE device_id=%s AND active AND ends_at<=now()", (data["device_id"],))
            active=conn.execute("SELECT shipment_id FROM tracking_assignments WHERE device_id=%s AND active",(data["device_id"],)).fetchone()
            if active and str(active["shipment_id"])!=identifier:
                raise APIError("device_busy","Finaliza el rastreo anterior antes de iniciar otra tarea.",409)
            old=conn.execute("SELECT * FROM tracking_assignments WHERE device_id=%s AND shipment_id=%s AND active AND starts_at<=now() AND ends_at>now() FOR UPDATE",(data["device_id"],identifier)).fetchone()
            if old:return old
            row=insert(conn,"tracking_assignments",dict(id=str(uuid4()),shipment_id=identifier,device_id=data["device_id"],
                responsible_id=g.actor["id"],actor_id=g.actor["id"],starts_at=now,
                ends_at=min(now+timedelta(hours=1),device["expires_at"])))
            emit(conn,"TRACKING_ASSIGNED",identifier,shipment["origin_id"])
            return row
        return atomic("mobile_tracking_start:"+identifier,data,work)

    @endpoint(app,"/api/v1/shipments/<identifier>/tracking/mobile-session/stop","POST",model=PhoneTracking,
              roles=("TRANSPORT",),result={"type":"object","required":["stopped"],"properties":{"stopped":{"type":"boolean"}}})
    def mobile_tracking_stop(identifier,data):
        with transaction() as conn:
            shipment=get(conn,"shipments",identifier,True);shipment_access(shipment)
            device=get(conn,"tracking_devices",data["device_id"])
            if str(device["user_id"])!=g.actor["id"] or device["source"] not in ("ANDROID","IOS"):
                raise APIError("forbidden","Teléfono ajeno.",403)
            conn.execute("UPDATE tracking_assignments SET active=false,version=version+1 WHERE shipment_id=%s AND device_id=%s AND active",(identifier,data["device_id"]))
            emit(conn,"TRACKING_UNASSIGNED",identifier,shipment["origin_id"])
            return {"stopped":True}
