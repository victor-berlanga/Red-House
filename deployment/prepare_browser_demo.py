"""Prepara un traslado ficticio abierto usando exclusivamente las API de negocio."""

from verify import Deployment, helpers


def main():
    p = Deployment(
        ".local/compose", "documentation/evidencias/segundo-parcial/browser-setup"
    )
    try:
        rows = p.query(
            "transporte",
            "SELECT id FROM shipments WHERE origin_id=%s "
            "AND status NOT IN ('ACCEPTED','CANCELLED','REJECTED') "
            "AND NOT inventory_pending ORDER BY id LIMIT 1",
            (p.env.state["tenants"][0],),
        )
        if rows:
            identifier = rows[0]["id"]
        else:
            p.login()
            helpers.route = lambda _: p.route()
            unit = helpers.resource(p)
            _, request = helpers.recipient_request(p)
            evaluation = helpers.evaluation(p, request, [unit])
            allocation = helpers.reservation(p, evaluation, unit)
            identifier = helpers.plan(p, allocation["reservation"])["id"]
        p.checks.append(
            {"check": "traslado_ficticio_abierto", "status": "passed", "id": identifier}
        )
        p.result, p.stage = "passed", "complete"
        print(identifier)
    except Exception:
        p.result = "failed"
        raise
    finally:
        p.save()


if __name__ == "__main__":
    main()
