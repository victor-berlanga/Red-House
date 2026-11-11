"""Integración HTTP/WSS real con PostgreSQL, Redis y MongoDB aislados; sin GPS físico."""
from uuid import uuid4
import pytest
from .test_final_tracking import tracking, connect, send, receive
from .helpers import iso, move


@pytest.mark.parametrize("source", ["ANDROID", "IOS"])
def test_mobile_registration_is_owner_scoped_and_revocable(p, source):
    body={"id":str(uuid4()),"source":source,"label":"Teléfono de integración"}
    device=p.ok("identidad_acceso","POST","/api/v1/mobile/devices",user="transport1",data=body)
    assert device["user_id"]==p.env.state["accounts"]["transport1"]["id"]
    assert "token_hash" not in device
    assert p.ok("identidad_acceso","POST","/api/v1/mobile/devices",user="transport1",data=body)["id"]==device["id"]
    assert p.request("identidad_acceso","POST","/api/v1/mobile/devices",user="donor1",data=body).status_code==403
    assert p.request("identidad_acceso","POST","/api/v1/mobile/devices",user="transport1",data=dict(body,user_id=p.env.state["accounts"]["donor1"]["id"])).status_code==422
    p.ok("identidad_acceso","POST",f"/api/v1/mobile/devices/{device['id']}/revoke",user="transport1",data={"version":1,"reason":"Fin de prueba autorizada","human_confirmation":True})
    assert p.request("identidad_acceso","POST","/api/v1/mobile/devices",user="transport1",data=body).status_code==403


def test_phone_ios_wss_and_scan_use_real_owners(p, tracking):
    t=tracking;s=t["shipment"]
    device=p.ok("identidad_acceso","POST","/api/v1/mobile/devices",user="transport1",data={"id":str(uuid4()),"source":"IOS","label":"iOS contrato; ubicación sintética"})
    command={"device_id":device["id"],"version":s["version"],"human_confirmation":True,"reason":"Consentimiento de rastreo en tarea propia"}
    assignment=p.ok("transporte","POST",f"/api/v1/shipments/{s['id']}/tracking/mobile-session",user="transport1",data=command)
    assert assignment["responsible_id"]==p.env.state["accounts"]["transport1"]["id"]
    assert p.request("transporte","POST",f"/api/v1/shipments/{s['id']}/scan",user="transport1",data={"scanned_resource_id":str(uuid4())}).status_code==409
    with p.owner("inventario") as conn:
        resource_id=str(conn.execute("SELECT resource_id FROM reservations WHERE id=%s",(s["reservation_id"],)).fetchone()[0])
    scan=p.ok("transporte","POST",f"/api/v1/shipments/{s['id']}/scan",user="transport1",data={"scanned_resource_id":resource_id})
    assert scan["verified"] and scan["version"]==s["version"]
    assert p.request("transporte","POST",f"/api/v1/shipments/{s['id']}/scan",user="donor1",data={"scanned_resource_id":resource_id}).status_code==403
    publisher=connect(t,p.tokens["transport1"]);receive(publisher,"authenticated")
    subscriber=connect(t,p.tokens["coordinator1"]);receive(subscriber,"authenticated")
    send(subscriber,{"type":"subscribe","shipment_id":s["id"]});receive(subscriber,"subscribed")
    point={"event_id":str(uuid4()),"shipment_id":s["id"],"device_id":device["id"],"source":"IOS","simulated":True,"sequence":1,"captured_at":iso(),"fix_valid":True,"latitude":25.6866,"longitude":-100.3161,"accuracy_m":12.0}
    send(publisher,{"type":"position.publish","position":point})
    ack=receive(publisher,"position.ack");assert ack["state"]=="PERSISTED_SQL"
    event=receive(subscriber,"position.updated");assert event["position"]["source"]=="IOS" and event["position"]["simulated"]
    send(publisher,{"type":"position.publish","position":point});assert receive(publisher,"position.ack")["cursor"]==ack["cursor"]
    p.ok("transporte","POST",f"/api/v1/shipments/{s['id']}/tracking/mobile-session/stop",user="transport1",data=command)
    send(publisher,{"type":"position.publish","position":dict(point,event_id=str(uuid4()),sequence=2)})
    assert receive(publisher,"error")["code"]=="unassigned_device"
    publisher.close();subscriber.close()
    with p.owner("transporte") as conn:
        assert conn.execute("SELECT count(*) FROM tracking_points WHERE device_id=%s",(device["id"],)).fetchone()[0]==1


def test_push_rotation_reuses_own_subscription(p):
    body={"channel":"PUSH","push_destination":"synthetic-destination-first"}
    first=p.ok("alertas","POST","/api/v1/alert-subscriptions",user="transport1",data=body)
    confirm={"human_confirmation":True,"reason":"Rotación de destino de prueba"}
    assert p.request("alertas","POST",f"/api/v1/alert-subscriptions/{first['id']}/revoke",user="donor1",data=confirm).status_code==403
    revoked=p.ok("alertas","POST",f"/api/v1/alert-subscriptions/{first['id']}/revoke",user="transport1",data=confirm)
    second=p.ok("alertas","POST","/api/v1/alert-subscriptions",user="transport1",data=dict(body,push_destination="synthetic-destination-second"))
    assert second["id"]==first["id"] and second["active"]
    assert second["version"]==revoked["version"]+1
    assert second["destination"]=="synthetic-destination-second"
    with p.owner("alertas") as conn:
        assert conn.execute("SELECT count(*) FROM alert_subscriptions WHERE user_id=%s AND channel='PUSH'",(second["user_id"],)).fetchone()[0]==1


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_operational_context_hides_private_contacts_and_checks_assignment(p, tracking, fmt):
    shipment=tracking["shipment"]
    private=p.ok("identidad_acceso","POST","/api/v1/catalogues/contacts",user="admin1",data={"name":"Contacto privado "+uuid4().hex,"value":"NO-EXPOSE"})
    public=p.ok("identidad_acceso","POST","/api/v1/catalogues/contacts",user="admin1",data={"name":"Mesa logística "+uuid4().hex,"value":"555-0100","operational":True})
    path=f"/api/v1/shipments/{shipment['id']}/operational-context"
    response=p.request("transporte","GET",path,user="transport1",headers={"Accept":"application/"+fmt})
    assert response.status_code==200,response.text
    import json
    from pathlib import Path
    from redhouse.xml_response import validate_response
    from jsonschema import validate
    contract=json.loads((Path(__file__).parents[1]/"ms_transporte/contracts/operational_context.response.json").read_text())
    envelope=response.json() if fmt=="json" else validate_response(response.content,contract)
    validate(envelope,contract)
    result=envelope["data"]
    assert public["id"] in [c["id"] for c in result["origin"]["contacts"]]
    assert private["id"] not in [c["id"] for c in result["origin"]["contacts"]]
    assert "NO-EXPOSE" not in str(result) and "password" not in str(result)
    assert result["route"]["reserved_version"]==result["route"]["current_version"]
    assert result["transport_user_id"]==p.env.state["accounts"]["transport1"]["id"]
    assert p.request("transporte","GET",path,user="donor1",headers={"Accept":"application/"+fmt}).status_code==403
    assert p.request("transporte","GET",path,user="transport2",headers={"Accept":"application/"+fmt}).status_code==403
    assert p.request("identidad_acceso","GET",f"/internal/v1/institutions/{shipment['origin_id']}/operational-contacts",user="transport1",headers={"Accept":"application/"+fmt}).status_code in (401,403)
