"""Provisionamiento común para instalación local y contenedores vacíos.

No se ejecuta al arrancar las aplicaciones. Requiere autoridad de instalación.
"""

import json
import secrets
from urllib.parse import quote
from uuid import uuid4

import psycopg
from psycopg import sql
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from werkzeug.security import generate_password_hash

from redhouse.config import SERVICES, MONGO_SERVICES
from redhouse.shared import service_schema


def provision(
    directory,
    *,
    admin_url,
    pg_host,
    pgport,
    redisadmin,
    redis_host,
    redisport,
    mongo,
    mongo_host,
    mongoport,
    urls,
    schema_path,
    seed=True,
):
    from scripts.local import pem, private_file

    configs = {}
    prefix = "rh-" + uuid4().hex[:12] + ":"
    jwt_private, jwt_public = pem(
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
    )
    service_keys = {s: pem(ed25519.Ed25519PrivateKey.generate()) for s in SERVICES}
    dbowners, runtime_dbs = {}, {}
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute("CREATE ROLE rh_shared_owner NOLOGIN")
        conn.execute("CREATE DATABASE red_house OWNER rh_shared_owner")
        conn.execute("REVOKE ALL ON DATABASE red_house FROM PUBLIC")
    owner_url = admin_url.rsplit("/", 1)[0] + "/red_house"
    with psycopg.connect(owner_url) as conn:
        conn.execute("SET ROLE rh_shared_owner")
        conn.execute((schema_path).read_text())
        conn.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
        conn.execute("REVOKE ALL ON SCHEMA red_house FROM PUBLIC")
    for service in SERVICES:
        username = "rh_" + service
        password = secrets.token_urlsafe(32)
        access = service_schema(service)
        owner_options = quote("-csearch_path=" + access + ",pg_catalog", safe="")
        dbowners[service] = owner_url + "?options=" + owner_options
        with psycopg.connect(owner_url) as conn:
            conn.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE"
                ).format(sql.Identifier(username), sql.Literal(password))
            )
            conn.execute(
                sql.SQL(
                    "ALTER ROLE {} IN DATABASE red_house SET search_path={},pg_catalog"
                ).format(sql.Identifier(username), sql.Identifier(access))
            )
            conn.execute(
                sql.SQL("GRANT CONNECT ON DATABASE red_house TO {}").format(
                    sql.Identifier(username)
                )
            )
            conn.execute(
                sql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC").format(
                    sql.Identifier(access)
                )
            )
            conn.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(access), sql.Identifier(username)
                )
            )
            conn.execute(
                sql.SQL(
                    "GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA {} TO {}"
                ).format(sql.Identifier(access), sql.Identifier(username))
            )
            for table in (
                "activity_events",
                "schema_version",
                "inbox",
                "idempotency",
                "decisions",
                "donor_reviews",
                "donation_steps",
                "resource_reviews",
                "movements",
                "reviews",
                "evaluations",
                "rankings",
                "proposals",
                "transitions",
                "telemetry",
                "custody_events",
                "audit_events",
                "audit_finding_links",
                "audit_finding_actions",
                "checks",
            ):
                if conn.execute(
                    "SELECT to_regclass(%s)", (access + "." + table,)
                ).fetchone()[0]:
                    conn.execute(
                        sql.SQL("REVOKE UPDATE,DELETE ON {}.{} FROM {}").format(
                            sql.Identifier(access),
                            sql.Identifier(table),
                            sql.Identifier(username),
                        )
                    )
            conn.execute(
                sql.SQL(
                    "REVOKE INSERT,UPDATE,DELETE ON {}.schema_version FROM {}"
                ).format(sql.Identifier(access), sql.Identifier(username))
            )
            if service == "auditoria":
                from redhouse.shared_migrations import upgrade

                upgrade(conn)
        database_url = f"postgresql://{username}:{password}@{pg_host}:{pgport}/red_house?options={owner_options}"
        runtime_dbs[service] = database_url
        redis_user, redis_pwd = service, secrets.token_urlsafe(32)
        # ACL de lectura para sesiones/permisos; solo Identidad puede escribirlos.
        key_rules = [
            f"%R~{prefix}session:*",
            f"%R~{prefix}permissions:*",
            f"%R~{prefix}permission_version:*",
            f"%R~{prefix}revoked:*",
            f"~{prefix}limit:{service}:*",
            f"~{prefix}nonce:{service}:*",
            f"~{prefix}cache:{service}:*",
        ]
        if service == "identidad_acceso":
            key_rules += [
                f"~{prefix}{area}:*"
                for area in (
                    "session",
                    "permissions",
                    "permission_version",
                    "revoked",
                    "refresh",
                    "used_refresh",
                    "login_fail",
                )
            ]
        if service == "transporte":
            key_rules.append(f"~{prefix}transporte:location:*")
        redisadmin.execute_command(
            "ACL",
            "SETUSER",
            redis_user,
            "on",
            ">" + redis_pwd,
            "resetkeys",
            "-@all",
            *key_rules,
            "+ping",
            "+get",
            "+mget",
            "+exists",
            "+set",
            "+del",
            "+incr",
            "+expire",
            "+ttl",
            "+eval",
            "+multi",
            "+exec",
        )
        config = {
            "SERVICE": service,
            "PORT": int(urls[service].rsplit(":", 1)[1]),
            "DATABASE_URL": database_url,
            "WORKER_REQUIRED": True,
            "REDIS_URL": f"redis://{redis_user}:{redis_pwd}@{redis_host}:{redisport}/0",
            "REDIS_PREFIX": prefix,
            "JWT_PUBLIC_KEY": jwt_public,
            "SERVICE_PRIVATE_KEY": service_keys[service][0],
            "SERVICE_PUBLIC_KEYS": {s: service_keys[s][1] for s in SERVICES},
            "SERVICE_URLS": urls,
            "MONGODB_DATABASE": "rh_" + service,
        }
        if service == "identidad_acceso":
            config["JWT_PRIVATE_KEY"] = jwt_private
        if service in MONGO_SERVICES:
            mongo_name = "rh_" + service
            mongo_db = mongo[mongo_name]
            mongo_db.create_collection("events")
            mongo_db.events.create_index([("region_id", 1), ("source", 1)])
            mongo_db.command(
                "createRole",
                "journal_writer",
                privileges=[
                    {
                        "resource": {"db": mongo_name, "collection": "events"},
                        "actions": ["find", "insert"],
                    }
                ],
                roles=[],
            )
            mongo_pwd = secrets.token_urlsafe(32)
            mongo_db.command(
                "createUser",
                service,
                pwd=mongo_pwd,
                roles=[{"role": "journal_writer", "db": mongo_name}],
            )
            config["MONGODB_URL"] = (
                f"mongodb://{service}:{mongo_pwd}@{mongo_host}:{mongoport}/{mongo_name}?authSource={mongo_name}"
            )
        configs[service] = config
        private_file(directory / (service + ".json"), json.dumps(config, indent=2))
    region = str(uuid4())
    tenants = [str(uuid4()), str(uuid4())]
    password = secrets.token_urlsafe(18)
    accounts = {}
    if seed:
        with psycopg.connect(dbowners["identidad_acceso"]) as conn:
            conn.execute("SET search_path=access_identidad_acceso,pg_catalog")
            for index, tenant in enumerate(tenants):
                conn.execute(
                    "INSERT INTO institutions(id,name,region_id) VALUES(%s,%s,%s)",
                    (tenant, f"Hospital {index + 1}", region),
                )
                for role in (
                    "ADMIN",
                    "OPERATOR",
                    "MEDICAL",
                    "COORDINATOR",
                    "TRANSPORT",
                    "AUDITOR",
                    "DONOR",
                ):
                    username = role.lower() + str(index + 1)
                    user_id = str(uuid4())
                    conn.execute(
                        "INSERT INTO users(id,tenant_id,username,password_hash,role) VALUES(%s,%s,%s,%s,%s)",
                        (
                            user_id,
                            tenant,
                            username,
                            generate_password_hash(password),
                            role,
                        ),
                    )
                    accounts[username] = {
                        "id": user_id,
                        "tenant_id": tenant,
                        "role": role,
                    }
    from scripts.migrate_documents import migrate

    migrate(mongo)
    from scripts.web_sessions import provision_web_storage

    web_sessions = provision_web_storage(
        directory,
        admin_url,
        redisadmin,
        f"redis://{redis_host}:{redisport}/0",
        prefix,
    )
    return {
        "configs": configs,
        "web_sessions": web_sessions,
        "database_owners": dbowners,
        "accounts": accounts,
        "password": password,
        "region_id": region,
        "tenants": tenants,
    }
