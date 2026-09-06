SELECT_ACCOUNT = """
    SELECT u.*, p.party_name, ar.role_code, r.role_name, r.is_enabled,
           ar.institution_id, coalesce(i.region_name, ar.region_name) AS region_name,
           coalesce(i.institution_name, 'Ámbito regional') AS institution_name,
           i.participation_status
    FROM user_account u JOIN party p USING (party_id)
    JOIN account_role ar USING (account_id) JOIN role r USING (role_code)
    LEFT JOIN institution i ON i.institution_id = ar.institution_id
"""


def by_email(conn, email):
    return conn.execute(SELECT_ACCOUNT + " WHERE u.login_email = %s", (email,)).fetchone()


def by_id(conn, identifier):
    return conn.execute(SELECT_ACCOUNT + " WHERE u.account_id = %s", (identifier,)).fetchone()


def revoke_all(conn, identifier):
    conn.execute("UPDATE web_session SET revoked_at = now() WHERE account_id = %s AND revoked_at IS NULL", (identifier,))
