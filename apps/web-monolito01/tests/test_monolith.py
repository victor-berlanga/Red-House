import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import psycopg
import pytest
from werkzeug.datastructures import MultiDict

from conftest import csrf
from src.business.access import BusinessError, Principal
from src.business.services import inventory as service
from src.cli import seed_demo
from src.data_access.connection import transaction
from src.data_access.repositories import accounts


def unit_payload(db, code="RH-TEST-999"):
    row = db.execute("SELECT * FROM blood_inventory WHERE institution_code = 'DEMO-NORTE' AND is_available LIMIT 1").fetchone()
    now = datetime.now(timezone.utc)
    return {"traceability_code": code, "component_id": str(row["component_id"]), "location_id": str(row["location_id"]),
            "collected_at": (now-timedelta(hours=10)).isoformat(), "expires_at": (now+timedelta(hours=20)).isoformat(),
            "current_status": "AVAILABLE", "recorded_group_code":"O+", "source_reference":"SOURCE-TEST",
            "reason":"Registro ficticio de prueba"}


def test_public_and_csrf(client, app):
    assert client.get("/").status_code == 200
    assert b"RH-DEMO-001" not in client.get("/").data
    assert client.get("/panel").status_code == 302
    assert client.get("/health/live").json["status"] == "alive"
    assert client.post("/login", data={"login_email":"admin@red-house.test","password":app.config["DEMO_TEST_PASSWORD"]}).status_code == 400
    assert client.get("/logout").status_code == 405


@pytest.mark.parametrize("role,paths", [
    ("admin", ["/panel", "/administracion/institutions", "/administracion/sites", "/administracion/locations",
               "/administracion/users", "/administracion/components", "/administracion/configuracion/parametros",
               "/administracion/users/nuevo", "/administracion/institutions/nuevo"]),
    ("operador", ["/panel", "/inventario", "/inventario?page=2", "/inventario/nueva"]),
    ("auditor", ["/panel", "/auditoria", "/inventario"]),
])
def test_role_pages_render(client, sign_in, role, paths):
    sign_in(client, role)
    for path in paths:
        assert client.get(path).status_code == 200, path


def test_bad_login_rate_limit_and_no_leak(client, app, db):
    token = csrf(client)
    for _ in range(5):
        assert client.post("/login", data={"csrf_token":token, "login_email":"admin@red-house.test", "password":"not-the-password"}).status_code == 401
    assert client.post("/login", data={"csrf_token":token, "login_email":"admin@red-house.test", "password":app.config["DEMO_TEST_PASSWORD"]}).status_code == 429
    rows = db.execute("SELECT * FROM login_attempt").fetchall()
    assert len(rows) == 5
    assert all(len(r["identity_hash"]) == 64 for r in rows)
    assert b"password_hash" not in client.get("/login").data


def test_logout_revokes_copied_jwt(client, sign_in, app):
    response = sign_in(client)
    assert "HttpOnly" in " ".join(response.headers.getlist("Set-Cookie"))
    copied = client.get_cookie(app.config["JWT_COOKIE_NAME"]).value
    assert client.post("/logout", data={"csrf_token":csrf(client,"/panel")}).status_code == 302
    client.set_cookie(app.config["JWT_COOKIE_NAME"], copied)
    assert client.get("/panel").status_code == 302


def test_tampered_expired_and_wrong_audience_jwt(client, sign_in, app):
    sign_in(client)
    key = app.config["JWT_COOKIE_NAME"]
    valid = client.get_cookie(key).value
    claims = jwt.decode(valid, options={"verify_signature":False})
    for changes in ({"exp":1}, {"aud":"wrong"}, {"iss":"wrong"}, {"jti":"not-a-uuid"}):
        client.set_cookie(key, jwt.encode({**claims, **changes}, app.config["JWT_SECRET_KEY"], algorithm="HS256"))
        assert client.get("/panel").status_code == 302
    client.set_cookie(key, valid[:-6] + "wrongx")
    assert client.get("/panel").status_code == 302


def test_role_and_tenant_isolation(client, sign_in, db):
    sign_in(client)
    assert client.get("/administracion/users").status_code == 403
    assert client.get("/auditoria").status_code == 403
    other = db.execute("SELECT * FROM blood_inventory WHERE institution_code = 'DEMO-VALLE' LIMIT 1").fetchone()
    assert client.get("/inventario/"+str(other["resource_id"])).status_code == 404
    html = client.get("/inventario?institution_id="+str(other["institution_id"])).data
    assert other["traceability_code"].encode() not in html
    assert "0 registros".encode() in html
    payload = unit_payload(db)
    payload["location_id"] = str(other["location_id"])
    assert client.post("/inventario/nueva", data={**payload,"csrf_token":csrf(client,"/inventario/nueva")}).status_code == 404


def test_admin_cannot_operate_and_auditor_cannot_write(client, sign_in, app, db):
    sign_in(client, "admin")
    assert client.get("/inventario").status_code == 403
    auditor = app.test_client()
    sign_in(auditor, "auditor")
    assert auditor.get("/inventario/nueva").status_code == 403
    row = db.execute("SELECT * FROM blood_inventory LIMIT 1").fetchone()
    assert auditor.post("/inventario/"+str(row["resource_id"]), data={"csrf_token":csrf(auditor,"/panel")}).status_code == 403


def test_create_inventory_and_history_are_atomic(client, sign_in, db):
    sign_in(client)
    payload = unit_payload(db)
    response = client.post("/inventario/nueva", data={**payload,"csrf_token":csrf(client,"/inventario/nueva")})
    assert response.status_code == 302
    assert client.get(response.location).status_code == 200
    row = db.execute("SELECT * FROM blood_inventory WHERE traceability_code = %s", (payload["traceability_code"],)).fetchone()
    assert row["is_available"]
    assert db.execute("SELECT count(*) AS n FROM blood_movement WHERE resource_id = %s",(row["resource_id"],)).fetchone()["n"] == 1
    assert db.execute("SELECT count(*) AS n FROM audit_event WHERE entity_reference = %s AND action = 'CREATE'",(str(row["resource_id"]),)).fetchone()["n"] == 1
    duplicate = client.post("/inventario/nueva", data={**payload,"csrf_token":csrf(client,"/inventario/nueva")})
    assert duplicate.status_code == 409


def test_operator_soft_delete_hides_inventory_but_preserves_history(client, sign_in, db):
    sign_in(client)
    payload = unit_payload(db, "RH-SOFT-DELETE")
    response = client.post("/inventario/nueva", data={**payload, "csrf_token":csrf(client, "/inventario/nueva")})
    assert response.status_code == 302
    row = db.execute("SELECT * FROM blood_inventory WHERE traceability_code = %s", (payload["traceability_code"],)).fetchone()
    detail_path = f"/inventario/{row['resource_id']}"
    assert b"Dar de baja unidad" in client.get(detail_path).data

    delete_path = f"/inventario/{row['resource_id']}/eliminar"
    response = client.post(delete_path, data={"csrf_token":csrf(client, detail_path),
        "version_no":row["version_no"], "reason":"Retiro ficticio del inventario"})
    assert response.status_code == 302
    assert response.location.endswith("/inventario")
    assert payload["traceability_code"].encode() not in client.get("/inventario").data
    assert payload["traceability_code"].encode() not in client.get("/panel").data

    stored = db.execute("SELECT * FROM blood_unit WHERE resource_id = %s", (row["resource_id"],)).fetchone()
    assert stored["current_status"] == "WITHDRAWN"
    assert stored["version_no"] == row["version_no"] + 1
    assert db.execute("SELECT count(*) AS n FROM blood_movement WHERE resource_id = %s", (row["resource_id"],)).fetchone()["n"] == 2
    audit_row = db.execute("SELECT * FROM audit_event WHERE entity_reference = %s AND action = 'DELETE'",
                           (str(row["resource_id"]),)).fetchone()
    assert audit_row["outcome"] == "SUCCESS"
    assert client.get(detail_path).status_code == 200
    assert b"Baja" in client.get(detail_path).data

    api_payload = unit_payload(db, "RH-HTTP-DELETE")
    assert client.post("/inventario/nueva", data={**api_payload, "csrf_token":csrf(client, "/inventario/nueva")}).status_code == 302
    api_row = db.execute("SELECT * FROM blood_inventory WHERE traceability_code = %s", (api_payload["traceability_code"],)).fetchone()
    api_path = f"/inventario/{api_row['resource_id']}"
    response = client.delete(api_path, data={"csrf_token":csrf(client, api_path),
        "version_no":api_row["version_no"], "reason":"Baja HTTP ficticia"})
    assert response.status_code == 204
    assert db.execute("SELECT current_status FROM blood_unit WHERE resource_id = %s", (api_row["resource_id"],)).fetchone()["current_status"] == "WITHDRAWN"


def test_delete_is_blocked_after_operational_movement_and_not_allowed_to_auditor(client, sign_in, app, db):
    sign_in(client)
    payload = unit_payload(db, "RH-SOFT-BLOCKED")
    assert client.post("/inventario/nueva", data={**payload, "csrf_token":csrf(client, "/inventario/nueva")}).status_code == 302
    row = db.execute("SELECT * FROM blood_inventory WHERE traceability_code = %s", (payload["traceability_code"],)).fetchone()
    path = f"/inventario/{row['resource_id']}"
    assert client.post(path, data={"csrf_token":csrf(client, path), "current_status":"QUARANTINED",
        "location_id":str(row["location_id"]), "version_no":row["version_no"],
        "reason":"Movimiento operativo ficticio"}).status_code == 302
    changed = db.execute("SELECT * FROM blood_unit WHERE resource_id = %s", (row["resource_id"],)).fetchone()
    blocked = client.post(f"{path}/eliminar", data={"csrf_token":csrf(client, path),
        "version_no":changed["version_no"], "reason":"Intento de retiro bloqueado"})
    assert blocked.status_code == 409
    assert b"movimiento operativo registrado" in blocked.data
    assert db.execute("SELECT current_status FROM blood_unit WHERE resource_id = %s", (row["resource_id"],)).fetchone()["current_status"] == "QUARANTINED"
    assert db.execute("SELECT count(*) AS n FROM audit_event WHERE entity_reference = %s AND action = 'DELETE'",
                      (str(row["resource_id"]),)).fetchone()["n"] == 0

    auditor = app.test_client()
    sign_in(auditor, "auditor")
    denied = auditor.post(f"{path}/eliminar", data={"csrf_token":csrf(auditor, path),
        "version_no":changed["version_no"], "reason":"Sin permiso"})
    assert denied.status_code == 403


def test_expiry_and_illegal_transitions(client, sign_in, db):
    sign_in(client)
    expired = db.execute("SELECT * FROM blood_inventory WHERE institution_code = 'DEMO-NORTE' AND effective_status = 'EXPIRED' LIMIT 1").fetchone()
    assert not expired["is_available"]
    path = "/inventario/"+str(expired["resource_id"])
    response = client.post(path, data={"csrf_token":csrf(client,path), "current_status":"AVAILABLE",
        "location_id":str(expired["location_id"]), "version_no":expired["version_no"], "reason":"Prueba ficticia"})
    assert response.status_code == 409
    invalid = unit_payload(db)
    invalid["expires_at"] = invalid["collected_at"]
    assert client.post("/inventario/nueva", data={**invalid,"csrf_token":csrf(client,"/inventario/nueva")}).status_code == 400


def test_concurrent_inventory_updates_one_wins(app, db):
    row = db.execute("SELECT * FROM blood_inventory WHERE institution_code = 'DEMO-NORTE' AND is_available LIMIT 1").fetchone()
    principal = Principal.from_row(accounts.by_email(db, "operador@red-house.test"))
    data = MultiDict({"current_status":"QUARANTINED", "location_id":str(row["location_id"]),
                      "version_no":str(row["version_no"]), "reason":"Movimiento concurrente ficticio"})
    def move():
        with app.app_context():
            try:
                service.change(principal, row["resource_id"], data)
                return 200
            except BusinessError as error:
                return error.status
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: move(), range(2)))
    assert sorted(results) == [200,409]
    assert db.execute("SELECT count(*) AS n FROM blood_movement WHERE resource_id = %s",(row["resource_id"],)).fetchone()["n"] == 2


def test_parameters_versions_and_global_permission(client, sign_in, db):
    sign_in(client,"admin")
    response = client.post("/administracion/configuracion/parametros", data={"csrf_token":csrf(client,"/administracion/configuracion/parametros"),"version_no":1,"hours":24})
    assert response.status_code == 302
    assert db.execute("SELECT count(*) AS n FROM parameter_version").fetchone()["n"] == 2
    assert client.post("/administracion/configuracion/parametros",data={"csrf_token":csrf(client,"/panel"),"version_no":1,"hours":10}).status_code == 409


def test_future_views_are_explicitly_nonfunctional(client, sign_in):
    sign_in(client)
    for slug in ("donantes","receptores","organos","compatibilidad","solicitudes","traslados","custodia"):
        response = client.get("/proximamente/"+slug)
        assert response.status_code == 200
        assert "Vista futura · Sin funcionalidad".encode() in response.data
        assert b"fieldset disabled" in response.data
        assert client.post("/proximamente/"+slug, data={"csrf_token":csrf(client,"/panel")}).status_code == 405


def test_sql_injection_and_html_escape(client, sign_in, db):
    sign_in(client,"admin")
    data={"institution_code":"TEST-XSS", "institution_name":"<script>alert(1)</script>", "institution_type":"HOSPITAL",
          "participation_status":"ACTIVE", "city":"Ficticia", "street":"Prueba"}
    response=client.post("/administracion/institutions/nuevo",data={**data,"csrf_token":csrf(client,"/panel")})
    assert response.status_code == 302
    page=client.get("/administracion/institutions?q=%3Cscript%3E").data
    assert b"<script>alert(1)</script>" not in page
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert client.get("/administracion/institutions?q=';DROP%20TABLE%20institution;--").status_code == 200
    assert db.execute("SELECT count(*) AS n FROM institution").fetchone()["n"] == 3


def test_sensitive_data_and_audit_scope(client, sign_in, db):
    sign_in(client,"auditor")
    response=client.get("/auditoria")
    assert response.status_code == 200
    assert b"password_hash" not in response.data
    assert b"scrypt:" not in response.data
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "form-action 'self'" in response.headers["Content-Security-Policy"]
    client.get("/inventario")
    assert db.execute("SELECT count(*) AS n FROM audit_event WHERE entity_type='BLOOD_UNIT' AND action='READ' AND entity_reference='LIST'").fetchone()["n"] == 1


def test_append_only_audit_and_idempotent_seed(app):
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code != 0
    assert "ya existe" in result.output
    with app.app_context():
        with pytest.raises(psycopg.errors.CheckViolation), transaction() as conn:
            conn.execute("UPDATE audit_event SET reason = 'tamper'")
        with pytest.raises(BusinessError), transaction() as conn:
            seed_demo(conn, app.config["DEMO_TEST_PASSWORD"])


def test_database_outage_fails_closed_and_recovers(client, sign_in, app):
    sign_in(client)
    actual=app.config["DATABASE_URL"]
    app.config["DATABASE_URL"]="postgresql://localhost:1/red_house_unavailable?connect_timeout=1"
    assert client.get("/panel").status_code == 503
    assert client.get("/").status_code == 200
    assert client.get("/health/live").status_code == 200
    app.config["DATABASE_URL"]=actual
    assert client.get("/panel").status_code == 200


def test_user_creation_role_change_deactivation_and_self_protection(client, sign_in, app, db):
    sign_in(client,"admin")
    institution=db.execute("SELECT * FROM institution WHERE institution_code='DEMO-NORTE'").fetchone()
    payload={"party_name":"Usuario ficticio", "login_email":"new@red-house.test", "role_code":"OPERATOR",
             "scope":str(institution["institution_id"]), "account_status":"ACTIVE", "password":app.config["DEMO_TEST_PASSWORD"]}
    assert client.post("/administracion/users/nuevo",data={**payload,"csrf_token":csrf(client,"/panel")}).status_code == 302
    row=accounts.by_email(db,payload["login_email"])
    new_client=app.test_client()
    response=new_client.post("/login",data={"csrf_token":csrf(new_client),"login_email":payload["login_email"],"password":payload["password"]})
    assert response.status_code == 302
    assert new_client.get("/inventario").status_code == 200
    path=f"/administracion/users/{row['account_id']}/editar"
    assert client.get(path).status_code == 200
    assert client.post(path,data={**payload,"password":"","version_no":row["version_no"],"account_status":"INACTIVE",
                                  "csrf_token":csrf(client,path)}).status_code == 302
    assert new_client.get("/inventario").status_code == 302
    admin=accounts.by_email(db,"admin@red-house.test")
    assert client.post(f"/administracion/users/{admin['account_id']}/editar",data={
        **payload,"login_email":admin["login_email"],"version_no":admin["version_no"],"password":"",
        "role_code":"ADMIN","scope":"REGIONAL","account_status":"INACTIVE","csrf_token":csrf(client,"/panel")}).status_code == 409


def test_institutional_admin_cannot_expand_scope(client, sign_in, app, db):
    sign_in(client,"admin")
    institution=db.execute("SELECT * FROM institution WHERE institution_code='DEMO-NORTE'").fetchone()
    other=db.execute("SELECT * FROM institution WHERE institution_code='DEMO-VALLE'").fetchone()
    data={"party_name":"Administrador institucional DEMO","login_email":"local@red-house.test","role_code":"ADMIN",
          "scope":str(institution["institution_id"]),"account_status":"ACTIVE","password":app.config["DEMO_TEST_PASSWORD"]}
    assert client.post("/administracion/users/nuevo",data={**data,"csrf_token":csrf(client,"/panel")}).status_code == 302
    local=app.test_client()
    assert local.post("/login",data={"login_email":data["login_email"],"password":data["password"],"csrf_token":csrf(local)}).status_code == 302
    assert local.get(f"/administracion/institutions/{other['institution_id']}/editar").status_code == 404
    assert local.post("/administracion/users/nuevo",data={**data,"login_email":"escalation@red-house.test",
        "scope":"REGIONAL","csrf_token":csrf(local,"/panel")}).status_code == 403
    assert local.post("/administracion/configuracion/parametros",data={"hours":1,"version_no":1,"csrf_token":csrf(local,"/panel")}).status_code == 403


def test_catalog_inactivation_hides_availability_and_stale_write_is_rejected(client, sign_in, db):
    sign_in(client,"admin")
    component=db.execute("SELECT * FROM blood_component LIMIT 1").fetchone()
    data={"component_code":component["component_code"],"component_name":component["component_name"],"version_no":component["version_no"]}
    path=f"/administracion/components/{component['component_id']}/editar"
    assert client.post(path,data={**data,"csrf_token":csrf(client,path)}).status_code == 302
    assert db.execute("SELECT count(*) AS n FROM blood_inventory WHERE component_id=%s AND is_available",(component["component_id"],)).fetchone()["n"] == 0
    assert db.execute("SELECT count(*) AS n FROM blood_unit WHERE component_id=%s",(component["component_id"],)).fetchone()["n"] > 0
    assert client.post(path,data={**data,"is_active":"on","csrf_token":csrf(client,path)}).status_code == 409


def test_network_references_contacts_and_activation(client, sign_in, app, db):
    sign_in(client,"admin")
    data=MultiDict({"institution_code":"DEMO-NEW","institution_name":"Nueva institución DEMO","institution_type":"HOSPITAL",
        "participation_status":"ACTIVE","city":"Ciudad ficticia","street":"Calle de prueba","contact_name":"Coordinación ficticia",
        "contact_email":"contact@test.test","contact_phone":"0000000000","csrf_token":csrf(client,"/panel")})
    data.setlist("capabilities",["LABORATORY","BLOOD_INVENTORY"])
    assert client.post("/administracion/institutions/nuevo",data=data).status_code == 302
    institution=db.execute("SELECT * FROM institution WHERE institution_code='DEMO-NEW'").fetchone()
    assert db.execute("SELECT count(*) AS n FROM institution_capability WHERE institution_id=%s",(institution["institution_id"],)).fetchone()["n"] == 2
    site_data={"institution_id":str(institution["institution_id"]),"site_code":"TEST-SITE","site_name":"Sede de prueba",
               "city":"Ciudad ficticia","street":"Otra calle ficticia","site_status":"ACTIVE","csrf_token":csrf(client,"/panel")}
    assert client.post("/administracion/sites/nuevo",data=site_data).status_code == 302
    site=db.execute("SELECT * FROM site WHERE site_code='TEST-SITE'").fetchone()
    assert client.post("/administracion/locations/nuevo",data={"site_id":str(site["site_id"]),"location_code":"TEST-LOCATION",
        "location_description":"Ubicación ficticia","is_active":"on","csrf_token":csrf(client,"/panel")}).status_code == 302
    north=db.execute("SELECT * FROM institution WHERE institution_code='DEMO-NORTE'").fetchone()
    operator=app.test_client(); sign_in(operator)
    for key, value in {"institution_code":north["institution_code"],"institution_name":north["institution_name"],"contact_name":"Contacto DEMO",
        "participation_status":"INACTIVE","version_no":north["version_no"],"csrf_token":csrf(client,"/panel")}.items():
        data[key] = value
    assert client.post(f"/administracion/institutions/{north['institution_id']}/editar",data=data).status_code == 302
    assert operator.get("/panel").status_code == 302


def test_audit_failure_rolls_back_inventory(client, sign_in, db, monkeypatch):
    sign_in(client)
    from src.data_access.repositories import audit
    def fail(*args, **kwargs):
        raise RuntimeError("Deliberate test failure")
    token=csrf(client,"/inventario/nueva")
    payload=unit_payload(db,"TEST-ROLLBACK")
    monkeypatch.setattr(audit,"record",fail)
    with pytest.raises(RuntimeError):
        client.post("/inventario/nueva",data={**payload,"csrf_token":token})
    assert db.execute("SELECT count(*) AS n FROM resource WHERE traceability_code='TEST-ROLLBACK'").fetchone()["n"] == 0


def test_unenabled_roles_and_inactive_accounts_cannot_login(client, app, db):
    db.execute("UPDATE account_role SET role_code='MEDICAL' WHERE account_id=(SELECT account_id FROM user_account WHERE login_email='operador@red-house.test')")
    db.commit()
    assert client.post("/login",data={"csrf_token":csrf(client),"login_email":"operador@red-house.test",
        "password":app.config["DEMO_TEST_PASSWORD"]}).status_code == 401
