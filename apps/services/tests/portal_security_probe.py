"""Inyección de fallos exclusiva del servidor TLS temporal de aceptación."""

def install(web, p, accounts):
    from flask import request
    from src.integration import sessions
    from redhouse.security import redis_call, key
    import jwt

    def end_session(mode):
        sid = request.cookies[web.config["JWT_COOKIE_NAME"]]
        session = sessions.load(sid)
        claims = jwt.decode(
            session["access_token"], options={"verify_signature": False}
        )
        assert claims["sub"] == accounts["map_viewer"]["id"]
        with p.apps["identidad_acceso"].app_context():
            session_key = key("session:" + claims["sid"])
            if mode == "expire":
                redis_call(lambda r: r.expire(session_key, 1))
            elif mode == "revoke":
                redis_call(lambda r: r.delete(session_key))
            else:
                return {"error": "unknown mode"}, 400
        return {"injected": mode}

    previous = {}

    def assignment(identifier, mode):
        with p.owner("transporte") as conn:
            row = conn.execute(
                "SELECT transport_user_id FROM shipments WHERE id=%s", (identifier,)
            ).fetchone()
            assert row
            if mode == "change":
                previous[identifier] = row[0]
                target = accounts["other_transport"]["id"]
            elif mode == "restore":
                target = previous.pop(identifier)
            else:
                return {"error": "unknown mode"}, 400
            conn.execute(
                "UPDATE shipments SET transport_user_id=%s,version=version+1 WHERE id=%s",
                (target, identifier),
            )
        return {
            "injected": mode,
            "scope": "solo fixture aislado; no acredita operación administrativa",
        }

    web.add_url_rule(
        "/test/tracking-session/<mode>",
        "test_tracking_session",
        web.extensions["csrf"].exempt(end_session),
        methods=["POST"],
    )
    web.add_url_rule(
        "/test/tracking-assignment/<identifier>/<mode>",
        "test_tracking_assignment",
        web.extensions["csrf"].exempt(assignment),
        methods=["POST"],
    )
