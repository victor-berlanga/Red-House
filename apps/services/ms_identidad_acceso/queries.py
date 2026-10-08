"""Consultas y proyecciones públicas del servicio propietario."""

from flask import g
from redhouse.api import endpoint, listing
from redhouse.db import transaction


def install(app):

    @endpoint(
        app,
        "/api/v1/users",
        roles=("ADMIN", "COORDINATOR"),
        paginated=True,
        query=("q", "role"),
        summary="Cuentas propias o personal regional de traslado; nunca hashes ni sesiones",
    )
    def user_list():
        with transaction() as conn:
            if g.actor["role"] == "ADMIN":
                where, values = "tenant_id=%s", (g.actor["tenant_id"],)
            else:
                where, values = (
                    "role='TRANSPORT' AND active AND tenant_id IN (SELECT id FROM institutions WHERE region_id=%s AND active)",
                    (g.actor["region_id"],),
                )
            return listing(
                conn,
                "users",
                where,
                values,
                order="username,id",
                columns="id,tenant_id,username,role,active,version",
                filters={
                    "q": ("username",),
                    "role": (
                        "role",
                        (
                            "ADMIN",
                            "OPERATOR",
                            "MEDICAL",
                            "COORDINATOR",
                            "TRANSPORT",
                            "AUDITOR",
                            "DONOR",
                        ),
                    ),
                },
            )
