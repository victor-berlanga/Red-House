"""Inicialización explícita; nunca borra o reinicializa una base existente."""
from datetime import datetime, timedelta, timezone

import click
import psycopg
from werkzeug.security import generate_password_hash

from .business.access import BusinessError, Principal
from .business.validators import password as validate_password
from .data_access.connection import transaction
from .data_access.repositories import accounts, audit
from .data_access.repositories.common import insert

DEMO_REGION = "DEMO-NORTE"


def seed_demo(conn, password):
    validate_password(password)
    if conn.execute("SELECT EXISTS (SELECT 1 FROM institution) OR EXISTS (SELECT 1 FROM user_account) AS occupied").fetchone()["occupied"]:
        raise BusinessError("La carga DEMO solo se permite sobre el esquema inicial vacío; no modifica datos existentes.", 409)
    institutions, locations = [], []
    for code, name, city in (("DEMO-NORTE", "Banco Regional Norte · DEMO", "Ciudad Norte (ficticia)"),
                             ("DEMO-VALLE", "Hospital del Valle · DEMO", "Ciudad Valle (ficticia)")):
        institution = insert(conn, "institution", {"institution_code": code, "institution_name": name,
            "institution_type": "BLOOD_BANK" if not institutions else "HOSPITAL", "region_name": DEMO_REGION,
            "city": city, "street": "Avenida Demostración 100 (ficticia)"}, "institution_id")
        institutions.append(institution)
        site = insert(conn, "site", {"institution_id": institution["institution_id"], "site_code": "SEDE-01",
            "site_name": "Sede principal DEMO", "street": institution["street"], "city": city}, "site_id")
        for code, description in (("LOC-01", "Almacén de demostración A"), ("LOC-02", "Almacén de demostración B")):
            locations.append(insert(conn, "storage_location", {"site_id": site["site_id"], "location_code": code,
                                    "location_description": description}, "location_id"))
        insert(conn, "institution_capability", {"institution_id": institution["institution_id"],
               "capability_code": "BLOOD_INVENTORY"}, "institution_id")
        contact = insert(conn, "contact", {"contact_name": "Coordinación DEMO", "contact_function": "Contacto institucional ficticio"}, "contact_id")
        insert(conn, "institution_contact", {"institution_id": institution["institution_id"], "contact_id": contact["contact_id"]}, "institution_id")
        insert(conn, "contact_method", {"contact_id": contact["contact_id"], "method_kind": "EMAIL",
                                       "method_value": "contacto@" + institution["institution_code"].lower() + ".test"}, "contact_id")
    components = [insert(conn, "blood_component", {"component_code": code, "component_name": name, "region_name": DEMO_REGION}, "component_id")
                  for code, name in (("RBC-DEMO", "Concentrado eritrocitario DEMO"), ("PLASMA-DEMO", "Plasma DEMO"),
                                     ("PLATELETS-DEMO", "Plaquetas DEMO"))]
    for email, name, role, institution in (
        ("admin@red-house.test", "Administración DEMO", "ADMIN", None),
        ("operador@red-house.test", "Operador Norte DEMO", "OPERATOR", institutions[0]["institution_id"]),
        ("auditor@red-house.test", "Auditoría DEMO", "AUDITOR", None),
        ("operador.valle@red-house.test", "Operador Valle DEMO", "OPERATOR", institutions[1]["institution_id"]),
    ):
        party = insert(conn, "party", {"party_name": name}, "party_id")
        user = insert(conn, "user_account", {"party_id": party["party_id"], "login_email": email,
                      "password_hash": generate_password_hash(password, method="scrypt")}, "account_id")
        insert(conn, "account_role", {"account_id": user["account_id"], "role_code": role,
               "institution_id": institution, "region_name": DEMO_REGION if institution is None else None}, "account_id")
    admin = Principal.from_row(accounts.by_email(conn, "admin@red-house.test"))
    north = Principal.from_row(accounts.by_email(conn, "operador@red-house.test"))
    valley = Principal.from_row(accounts.by_email(conn, "operador.valle@red-house.test"))
    insert(conn, "parameter_version", {"parameter_code": "EXPIRY_WARNING_HOURS", "region_name": DEMO_REGION,
           "version_no": 1, "scalar_value": 72, "approved_by": admin.account_id}, "parameter_version_id")
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    groups = ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+")
    for n in range(36):
        actor = north if n < 26 else valley
        location = locations[(0 if n < 26 else 2) + n % 2]
        component = components[n % len(components)]
        resource = insert(conn, "resource", {"traceability_code": f"RH-DEMO-{n+1:03}"}, "resource_id")
        state = "WITHDRAWN" if n % 13 == 0 else "QUARANTINED" if n % 7 == 0 else "AVAILABLE"
        # Fechas sintéticas para mostrar estados, nunca vidas útiles por componente.
        expires = now + timedelta(hours=(-12 if n % 9 == 0 else 8 + n * 9))
        insert(conn, "blood_unit", {"resource_id": resource["resource_id"], "component_id": component["component_id"],
               "location_id": location["location_id"], "collected_at": now - timedelta(days=20),
               "expires_at": expires, "current_status": state}, "resource_id")
        insert(conn, "blood_classification", {"resource_id": resource["resource_id"], "recorded_group_code": groups[n % 8],
               "source_reference": f"FUENTE-DEMO-{n+1:03}"}, "resource_id")
        insert(conn, "blood_movement", {"resource_id": resource["resource_id"], "sequence": 1, "new_status": state,
               "destination_location_id": location["location_id"], "actor_id": actor.account_id,
               "reason": "Carga de historial ficticio para demostración"}, "movement_id")
        audit.record(conn, actor, "CREATE", "BLOOD_UNIT", resource["resource_id"], "Carga DEMO de unidad e historial",
                     after={"traceability_code": resource["traceability_code"], "current_status": state})
    audit.record(conn, admin, "BOOTSTRAP", "DEMO_DATASET", "SEED-01", "Carga inicial académica: instituciones, sedes, catálogos y cuentas ficticias")


def register(app):
    @app.cli.command("init-db")
    def init_db_command():
        """Crea el esquema inicial, sin borrar ni sobrescribir otro esquema."""
        try:
            with transaction() as conn:
                conn.execute(app.config["SCHEMA_PATH"].read_text(encoding="utf-8"))
        except psycopg.errors.DuplicateSchema:
            raise click.ClickException("El esquema red_house ya existe. No se modificó; no vuelvas a inicializarlo.") from None
        except psycopg.Error:
            raise click.ClickException("No fue posible inicializar PostgreSQL. Revisa conexión y permisos; no se confirma una inicialización parcial.") from None
        click.echo("Esquema red_house creado. No se cargaron cuentas ni datos DEMO.")

    @app.cli.command("seed-demo")
    @click.password_option(prompt="Contraseña para las cuatro cuentas DEMO (12–128 caracteres)", confirmation_prompt=True)
    def seed_demo_command(password):
        """Carga una sola vez datos ficticios en un esquema inicial vacío."""
        try:
            with transaction() as conn:
                seed_demo(conn, password)
        except BusinessError as exc:
            raise click.ClickException(exc.message) from None
        except psycopg.Error:
            raise click.ClickException("No se pudo completar la carga DEMO; no se guardaron cambios parciales.") from None
        click.echo("DEMO cargada: 2 instituciones, 4 cuentas y 36 unidades ficticias. La contraseña no se imprime ni se guarda en texto plano.")

    @app.cli.command("prune-auth")
    def prune_auth_command():
        """Retira controles temporales antiguos; no elimina auditoría del negocio."""
        with transaction() as conn:
            attempts = conn.execute("DELETE FROM login_attempt WHERE occurred_at < now() - interval '1 day'").rowcount
            sessions = conn.execute("DELETE FROM web_session WHERE expires_at < now() - interval '1 day'").rowcount
        click.echo(f"Controles temporales retirados: {attempts} intentos y {sessions} sesiones expiradas. Auditoría conservada.")
