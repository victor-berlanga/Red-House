from psycopg import sql


def insert(conn, table, values, key):
    """Solo recibe tablas/columnas de los servicios, nunca nombres del formulario."""
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
        sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, values)),
        sql.SQL(", ").join(sql.Placeholder() for _ in values))
    return conn.execute(query, list(values.values())).fetchone()


def update(conn, table, key, identifier, values, version):
    assignments = [sql.SQL("{} = %s").format(sql.Identifier(k)) for k in values]
    query = sql.SQL("UPDATE {} SET {}, version_no = version_no + 1 WHERE {} = %s AND version_no = %s RETURNING *").format(
        sql.Identifier(table), sql.SQL(", ").join(assignments), sql.Identifier(key))
    return conn.execute(query, [*values.values(), identifier, version]).fetchone()


def scope(principal, alias="i"):
    # alias is a code constant. An institutional role never inherits regional access.
    if principal.institution_id:
        return f"{alias}.institution_id = %s", [principal.institution_id]
    return f"{alias}.region_name = %s", [principal.region_name]


def pattern(value):
    return "%" + value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
