"""Permisos de ampliaciones aditivas, sin otorgar acceso a tablas vecinas."""

from psycopg import sql

TABLES = {
    "identidad_acceso": {
        "institution_presentations": True,
        "portal_policies": True,
        "devices": True,
        "security_factors": True,
        "recovery_tokens": True,
        "security_contacts": True,
        "identity_deliveries": True,
        "accreditations": False,
    },
    "transporte": {
        "tracking_assignments": True,
        "tracking_points": False,
        "sync_commands": False,
    },
    "documentos": {"document_metadata": True, "file_scans": False, "export_jobs": True},
    "donantes": {
        "campaign_publications": True,
        "consent_versions": False,
        "campaign_slots": True,
        "appointment_slots": True,
        "appointment_reminders": True,
    },
    "priorizacion_geografia": {
        "algorithm_runs": False,
        "decision_runs": False,
        "regional_graphs": False,
    },
    "receptores": {"external_authorizations": False},
    "compatibilidad": {
        "lab_profiles": False,
        "rule_actions": False,
        "lab_samples": True,
        "lab_results": False,
        "lab_actions": False,
    },
    "inventario": {
        "resource_lineage": False,
        "resource_controls": True,
        "cold_equipment": True,
        "cold_profiles": False,
        "cold_readings": False,
        "cold_reviews": False,
        "resource_destinations": False,
        "external_mappings": False,
    },
    "auditoria": {"anomaly_reviews": True, "anomaly_actions": False},
    "alertas": {
        "alert_policies": False,
        "alert_subscriptions": True,
        "alert_deliveries": True,
        "alert_actions": False,
    },
}


def views(conn):
    """Vistas de propietario; defaults copiados sin reconstruir tablas ni datos."""
    from .config import SERVICES

    for service in SERVICES:
        conn.execute(
            sql.SQL(
                "CREATE OR REPLACE VIEW {}.shared_schema_version AS SELECT max(version) AS version FROM red_house.schema_migration"
            ).format(sql.Identifier("access_" + service))
        )
    for service, tables in TABLES.items():
        for table in tables:
            conn.execute(
                sql.SQL(
                    "CREATE OR REPLACE VIEW {}.{} AS SELECT * FROM red_house.{}"
                ).format(
                    sql.Identifier("access_" + service),
                    sql.Identifier(table),
                    sql.Identifier(table),
                )
            )
            defaults = conn.execute(
                "SELECT column_name,column_default FROM information_schema.columns "
                "WHERE table_schema='red_house' AND table_name=%s AND column_default IS NOT NULL",
                (table,),
            ).fetchall()
            for column, default in defaults:
                conn.execute(
                    sql.SQL("ALTER VIEW {}.{} ALTER COLUMN {} SET DEFAULT {}").format(
                        sql.Identifier("access_" + service),
                        sql.Identifier(table),
                        sql.Identifier(column),
                        sql.SQL(default),
                    )
                )


def grants(conn):
    from .config import SERVICES

    for service in SERVICES:
        role = "rh_" + service
        if conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone():
            conn.execute(
                sql.SQL("GRANT SELECT ON {}.shared_schema_version TO {}").format(
                    sql.Identifier("access_" + service), sql.Identifier(role)
                )
            )
    for service, tables in TABLES.items():
        role = "rh_" + service
        if not conn.execute(
            "SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)
        ).fetchone():
            continue
        for table, mutable in tables.items():
            conn.execute(
                sql.SQL("REVOKE INSERT,UPDATE,DELETE ON {}.{} FROM {}").format(
                    sql.Identifier("access_" + service),
                    sql.Identifier(table),
                    sql.Identifier(role),
                )
            )
            conn.execute(
                sql.SQL("GRANT SELECT,INSERT{} ON {}.{} TO {}").format(
                    sql.SQL(",UPDATE" if mutable else ""),
                    sql.Identifier("access_" + service),
                    sql.Identifier(table),
                    sql.Identifier(role),
                )
            )
        if service == "auditoria" and "anomaly_reviews" in tables:
            conn.execute(
                "REVOKE UPDATE ON access_auditoria.anomaly_reviews FROM rh_auditoria"
            )
            conn.execute(
                "GRANT UPDATE(state,version) ON access_auditoria.anomaly_reviews TO rh_auditoria"
            )
        if service == "compatibilidad":
            conn.execute(
                "REVOKE UPDATE ON access_compatibilidad.lab_samples FROM rh_compatibilidad"
            )
            conn.execute(
                "GRANT UPDATE(status,received_at,version) ON access_compatibilidad.lab_samples TO rh_compatibilidad"
            )
            conn.execute(
                "GRANT UPDATE(status) ON access_compatibilidad.lab_results TO rh_compatibilidad"
            )
        if service == "transporte":
            conn.execute(
                "REVOKE INSERT,UPDATE,DELETE ON access_transporte.tracking_devices FROM rh_transporte"
            )
            conn.execute(
                "GRANT SELECT ON access_transporte.tracking_devices TO rh_transporte"
            )
        if service == "alertas":
            conn.execute(
                "GRANT SELECT,UPDATE ON access_alertas.alert_severity TO rh_alertas"
            )

    # Autoridad única: ninguna credencial de Transporte conserva acceso a archivos.
    if conn.execute("SELECT 1 FROM pg_roles WHERE rolname='rh_transporte'").fetchone():
        for table in ("files", "document_metadata", "file_scans", "export_jobs"):
            if conn.execute(
                "SELECT to_regclass(%s)", ("access_transporte." + table,)
            ).fetchone()[0]:
                conn.execute(
                    sql.SQL(
                        "REVOKE ALL ON access_transporte.{} FROM rh_transporte"
                    ).format(sql.Identifier(table))
                )
    if conn.execute("SELECT 1 FROM pg_roles WHERE rolname='rh_documentos'").fetchone():
        conn.execute("REVOKE DELETE ON access_documentos.files FROM rh_documentos")
