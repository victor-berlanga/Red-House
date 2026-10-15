"""Construcción de tablas comunes y vistas API sobre el modelo heredado de main.

Solo se ejecuta al generar SQL en un clúster vacío, nunca al atender peticiones.
"""

import re
from psycopg import sql
from .config import SERVICES
from .schema import COMMON, SCHEMAS
from .migrations import migrate
from .shared import TABLES, COMMON_TABLES, REFERENCES, service_schema


def ident(value):
    return '"' + value.replace('"', '""') + '"'


def target(table):
    return TABLES.get(table, (table, {}))


def columns(conn, schema, table):
    return conn.execute(
        """SELECT a.attname,format_type(a.atttypid,a.atttypmod),
      pg_get_expr(d.adbin,d.adrelid),a.attnotnull
      FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
      LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
      WHERE n.nspname=%s AND c.relname=%s AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum""",
        (schema, table),
    ).fetchall()


def rewrite(definition, owner_schema, table):
    physical, mapping = target(table)
    references = []

    def ref(m):
        remote = m.group(1)
        fields = m.group(2).split(", ")
        remote_table, remote_map = target(remote)
        value = (
            "REFERENCES red_house."
            + ident(remote_table)
            + " ("
            + ", ".join(
                ident(remote_map.get(f.strip('"'), f.strip('"'))) for f in fields
            )
            + ")"
        )
        references.append(value)
        return f"REFERENCEPLACEHOLDER{len(references) - 1}"

    definition = re.sub(
        r"REFERENCES (?:" + owner_schema + r"\.)?([a-z_]+)\(([^)]+)\)", ref, definition
    )
    for original, destination in sorted(mapping.items(), key=lambda i: -len(i[0])):
        definition = re.sub(r"\b" + original + r"\b", destination, definition)
    for i, value in enumerate(references):
        definition = definition.replace(f"REFERENCEPLACEHOLDER{i}", value)
    return definition


def extend(conn):
    specs = {}
    owners = {}
    for service in SERVICES:
        schema = "template_" + service
        conn.execute("CREATE SCHEMA " + ident(schema))
        conn.execute("SET LOCAL search_path=" + ident(schema) + ",pg_catalog")
        conn.execute(COMMON + SCHEMAS[service])
        conn.execute("INSERT INTO schema_version(version) VALUES(1)")
        migrate(conn, service)
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname=%s ORDER BY tablename",
                (schema,),
            )
        ]
        for table in tables:
            if table in COMMON_TABLES and table in specs:
                continue
            specs[table] = (schema, columns(conn, schema, table))
            owners.setdefault(table, []).append(service)
    conn.execute("SET LOCAL search_path=red_house,pg_catalog")
    conn.execute("DROP VIEW blood_inventory")
    # Remove provisional target tables superseded by actual endpoint contracts.
    # Retain all main tables; these four were additions in the preceding proposal.
    conn.execute(
        "DROP TABLE event_inbox,event_outbox,request_idempotency,service_worker_health"
    )
    for table, (schema, fields) in specs.items():
        physical, mapping = target(table)
        if table in COMMON_TABLES:
            physical = "service_" + table
            defs = ["service text NOT NULL"] + [
                ident(n)
                + " "
                + typ
                + (" DEFAULT " + default if default else "")
                + (" NOT NULL" if required else "")
                for n, typ, default, required in fields
            ]
            conn.execute(
                "CREATE TABLE " + ident(physical) + " (" + ", ".join(defs) + ")"
            )
            # Scope keys and references to the service; one physical table, not eleven copies.
            constraints = conn.execute(
                "SELECT contype,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid=%s::regclass",
                (schema + "." + table,),
            ).fetchall()
            for kind, definition in constraints:
                if kind in ("p", "u"):
                    definition = definition.replace("(", "(service,", 1)
                conn.execute("ALTER TABLE " + ident(physical) + " ADD " + definition)
            if table in ("activity_events", "decisions"):
                conn.execute(
                    f"CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON {ident(physical)} FOR EACH ROW EXECUTE FUNCTION reject_history_mutation()"
                )
            continue
        existing = columns(conn, "red_house", physical)
        if not existing:
            conn.execute("CREATE TABLE " + ident(physical) + " ()")
        mapped = {mapping.get(n, n) for n, *_ in fields}
        # Retain historical-only columns without inventing values for current APIs.
        for name, typ, default, required in existing:
            if name not in mapped and required:
                conn.execute(
                    f"ALTER TABLE {ident(physical)} ALTER COLUMN {ident(name)} DROP NOT NULL"
                )
        # Existing CHECK/FK/UNIQUE semantics on mapped attributes are replaced by
        # those actually used by the current APIs, then strengthened across modules.
        constraints = conn.execute(
            """SELECT conname,contype,ARRAY(SELECT attname FROM pg_attribute WHERE attrelid=conrelid AND attnum=ANY(conkey))
          FROM pg_constraint WHERE conrelid=%s::regclass""",
            ("red_house." + physical,),
        ).fetchall()
        for name, kind, attrs in constraints:
            if kind != "p" and set(attrs) & mapped:
                conn.execute(
                    f"ALTER TABLE {ident(physical)} DROP CONSTRAINT {ident(name)} CASCADE"
                )
        by_name = {r[0]: r for r in existing}
        for name, typ, default, required in fields:
            destination = mapping.get(name, name)
            if destination not in by_name:
                conn.execute(
                    f"ALTER TABLE {ident(physical)} ADD COLUMN {ident(destination)} {typ}"
                )
            elif by_name[destination][1] != typ:
                conn.execute(
                    f"ALTER TABLE {ident(physical)} ALTER COLUMN {ident(destination)} DROP DEFAULT"
                )
                conn.execute(
                    f"ALTER TABLE {ident(physical)} ALTER COLUMN {ident(destination)} TYPE {typ} USING {ident(destination)}::{typ}"
                )
            conn.execute(
                f"ALTER TABLE {ident(physical)} ALTER COLUMN {ident(destination)} "
                + ("SET DEFAULT " + default if default else "DROP DEFAULT")
            )
            conn.execute(
                f"ALTER TABLE {ident(physical)} ALTER COLUMN {ident(destination)} "
                + ("SET NOT NULL" if required else "DROP NOT NULL")
            )
        # Preserve immutable main triggers; add current ones later where absent.
    # Build constraints after all targets exist.
    for table, (schema, fields) in specs.items():
        if table in COMMON_TABLES:
            continue
        physical, mapping = target(table)
        constraints = conn.execute(
            "SELECT conname,contype,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid=%s::regclass ORDER BY CASE contype WHEN 'p' THEN 0 WHEN 'u' THEN 1 ELSE 2 END, conname",
            (schema + "." + table,),
        ).fetchall()
        for name, kind, definition in constraints:
            if (
                kind == "p"
                and conn.execute(
                    "SELECT 1 FROM pg_constraint WHERE conrelid=%s::regclass AND contype='p'",
                    ("red_house." + physical,),
                ).fetchone()
            ):
                continue
            conn.execute(
                f"ALTER TABLE red_house.{ident(physical)} ADD CONSTRAINT {ident('api_' + name)} "
                + rewrite(definition, schema, table)
            )
        indexes = conn.execute(
            """SELECT c.relname,pg_get_indexdef(i.indexrelid) FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid
         WHERE i.indrelid=%s::regclass AND NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conindid=i.indexrelid)""",
            (schema + "." + table,),
        ).fetchall()
        for name, definition in indexes:
            definition = definition.replace(
                "INDEX " + name + " ON " + schema + "." + table,
                "INDEX " + ident("api_" + name) + " ON red_house." + ident(physical),
            )
            # Attribute mapping only applies after the USING clause.
            head, body = definition.split(" USING ", 1)
            conn.execute(head + " USING " + rewrite(body, schema, table))
        immutable = conn.execute(
            "SELECT 1 FROM pg_trigger WHERE tgrelid=%s::regclass AND NOT tgisinternal AND pg_get_triggerdef(oid) LIKE '%%reject_history_mutation%%'",
            (schema + "." + table,),
        ).fetchone()
        if (
            immutable
            and not conn.execute(
                "SELECT 1 FROM pg_trigger WHERE tgrelid=%s::regclass AND NOT tgisinternal AND pg_get_triggerdef(oid) LIKE '%%reject_history_mutation%%'",
                ("red_house." + physical,),
            ).fetchone()
        ):
            conn.execute(
                f"CREATE TRIGGER api_immutable BEFORE UPDATE OR DELETE ON red_house.{ident(physical)} FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()"
            )
    for table, refs in REFERENCES.items():
        physical, mapping = target(table)
        for column, (remote, key) in refs.items():
            remote_table, remote_mapping = target(remote)
            conn.execute(
                f"ALTER TABLE red_house.{ident(physical)} ADD CONSTRAINT {ident('shared_' + table + '_' + column)} FOREIGN KEY ({ident(mapping.get(column, column))}) REFERENCES red_house.{ident(remote_table)} ({ident(remote_mapping.get(key, key))})"
            )
    # No duplicate clinical storage: views expose each current contract over main tables.
    for service in SERVICES:
        access = service_schema(service)
        conn.execute("CREATE SCHEMA " + ident(access))
        template = "template_" + service
        for table in [
            r[0]
            for r in conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname=%s", (template,)
            )
        ]:
            fields = specs[table][1]
            physical, mapping = target(table)
            where = ""
            if table in COMMON_TABLES:
                physical = "service_" + table
                where = " WHERE service='" + service + "' WITH LOCAL CHECK OPTION"
            if table == "cache_revision":
                namespace = "inventory" if service == "inventario" else "catalogues"
                where = " WHERE name='" + namespace + "' WITH LOCAL CHECK OPTION"
            select = ", ".join(
                ident(mapping.get(n, n)) + " AS " + ident(n) for n, *_ in fields
            )
            conn.execute(
                f"CREATE VIEW {ident(access)}.{ident(table)} AS SELECT {select} FROM red_house.{ident(physical)}"
                + where
            )
            if table in COMMON_TABLES:
                # A dedicated insertion rule supplies the invisible scope column.
                values = ", ".join("NEW." + ident(n) for n, *_ in fields)
                names = ", ".join(ident(n) for n, *_ in fields)
                # Use a trigger for INSERT only; UPDATE/DELETE remain auto-updatable.
                function = ident(access) + "." + ident("insert_" + table)
                conn.execute(f"""CREATE FUNCTION {function}() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house.{ident(physical)}(service,{names}) VALUES ('{service}',{values}) RETURNING {names} INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$""")
                conn.execute(
                    f"CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON {ident(access)}.{ident(table)} FOR EACH ROW EXECUTE FUNCTION {function}()"
                )
            for n, typ, default, required in fields:
                if default:
                    conn.execute(
                        f"ALTER VIEW {ident(access)}.{ident(table)} ALTER COLUMN {ident(n)} SET DEFAULT {default}"
                    )
        # The view filters, not separate schemas of tables, isolate technical queues.
    conn.execute("ALTER FUNCTION red_house.bump_read_cache() SECURITY DEFINER")
    conn.execute(
        "ALTER FUNCTION red_house.bump_read_cache() SET search_path=pg_catalog"
    )
    # seed migration versions; shared global schema records its own version separately.
    for service in SERVICES:
        versions = conn.execute(
            "SELECT version FROM " + ident("template_" + service) + ".schema_version"
        ).fetchall()
        for (version,) in versions:
            conn.execute(
                "INSERT INTO red_house.service_schema_version(service,version) VALUES(%s,%s)",
                (service, version),
            )
    for service in SERVICES:
        conn.execute("DROP SCHEMA " + ident("template_" + service) + " CASCADE")
    conn.execute(
        "INSERT INTO red_house.schema_migration(version,description) VALUES(6,'Adaptación ejecutable de servicios y relaciones compartidas')"
    )
    conn.execute(
        "CREATE INDEX shared_outbox_pending ON red_house.service_outbox(service,next_attempt,created_at) WHERE delivered_at IS NULL"
    )
    conn.execute(
        "CREATE TRIGGER api_catalogue_cache AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON red_house.catalogue_entry FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()"
    )

    conn.execute("INSERT INTO red_house.cache_revision(name) VALUES('inventory')")
    conn.execute("""CREATE FUNCTION red_house.bump_inventory_cache() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
        BEGIN UPDATE red_house.cache_revision SET revision=revision+1 WHERE name='inventory'; RETURN NULL; END $$""")
    conn.execute(
        "CREATE TRIGGER api_inventory_cache AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON red_house.resource FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_inventory_cache()"
    )

    # Importación con ciclos validada al commit; ejecución ordinaria sigue siendo inmediata.
    for relation, constraint in conn.execute(
        "SELECT conrelid::regclass::text,conname FROM pg_constraint WHERE contype='f' AND connamespace='red_house'::regnamespace"
    ).fetchall():
        conn.execute(
            sql.SQL(
                "ALTER TABLE {} ALTER CONSTRAINT {} DEFERRABLE INITIALLY IMMEDIATE"
            ).format(sql.Identifier(*relation.split(".")), sql.Identifier(constraint))
        )
