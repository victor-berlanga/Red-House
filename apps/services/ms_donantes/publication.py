"""Solo contenido de campaña expresamente autorizado para el sitio público."""

from typing import Annotated
from flask import g, request
from pydantic import Field
from redhouse.api import endpoint, atomic, pagination
from redhouse.db import transaction, get, insert, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.decisions import record
from redhouse.models import Confirm, Model, ID, Text, utc_date
from redhouse.extension_contracts import schema, page_schema
from redhouse.security import own


class PublicationChange(Confirm):
    version: Annotated[int, Field(ge=0)]
    published: bool
    venue: Text
    information: Annotated[str, Field(min_length=1, max_length=1000)]


class Publication(Model):
    id: ID
    tenant_id: ID
    published: bool
    venue: str
    information: str
    version: int


class PublicCampaign(Model):
    title: str
    starts_at: str
    ends_at: str
    venue: str
    information: str


def install(app):
    @endpoint(
        app,
        "/api/v1/public/campaigns",
        public=True,
        result={
            "type": "object",
            "required": ["items"],
            "properties": {"items": {"type": "array", "items": schema(PublicCampaign)}},
        },
    )
    def public_campaigns():
        with transaction() as conn:
            return {
                "items": conn.execute(
                    "SELECT c.title,c.starts_at,c.ends_at,p.venue,p.information FROM campaigns c JOIN campaign_publications p ON p.id=c.id WHERE p.published AND c.status='OPEN' AND c.ends_at>now() ORDER BY c.starts_at,c.id"
                ).fetchall()
            }

    @endpoint(
        app,
        "/api/v1/public/campaign-feed",
        public=True,
        paginated=True,
        query=("q", "from_at", "until_at"),
        result=page_schema(PublicCampaign),
        summary="Campañas públicas paginadas, con búsqueda y fechas de inicio",
    )
    def public_campaign_feed():
        page, size, offset = pagination(("q", "from_at", "until_at"))
        condition = "p.published AND c.status='OPEN' AND c.ends_at>now()"
        values = []
        raw_query = request.args.get("q", "")
        if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in raw_query):
            raise APIError("validation", "El filtro contiene caracteres no admitidos.")
        query = raw_query.strip()
        if len(query) > 100:
            raise APIError("validation", "Filtro demasiado largo.")
        if query:
            escaped = (
                query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            condition += " AND (c.title ILIKE %s OR p.venue ILIKE %s)"
            values.extend(["%" + escaped + "%"] * 2)
        bounds = {}
        for parameter, operator in (("from_at", ">="), ("until_at", "<")):
            if parameter in request.args:
                bounds[parameter] = utc_date(request.args[parameter], parameter)
                condition += " AND c.starts_at" + operator + "%s"
                values.append(bounds[parameter])
        if len(bounds) == 2 and bounds["from_at"] >= bounds["until_at"]:
            raise APIError("validation", "Ventana temporal inválida.", 422)
        with transaction() as conn:
            # One statement: the count and rows share a PostgreSQL snapshot.
            row = conn.execute(
                "WITH visible AS ("
                "SELECT c.id,c.title,c.starts_at,c.ends_at,p.venue,p.information "
                "FROM campaigns c JOIN campaign_publications p ON p.id=c.id "
                "WHERE " + condition + "), selected AS ("
                "SELECT id,title,starts_at,ends_at,venue,information FROM visible "
                "ORDER BY starts_at,id LIMIT %s OFFSET %s) "
                "SELECT (SELECT count(*) FROM visible) AS total, "
                "COALESCE((SELECT jsonb_agg(to_jsonb(selected)-'id' "
                "ORDER BY starts_at,id) FROM selected),'[]'::jsonb) AS items",
                (*values, size, offset),
            ).fetchone()
            return dict(row, page=page, page_size=size)

    @endpoint(
        app,
        "/api/v1/campaigns/<identifier>/publication",
        roles=("OPERATOR",),
        result=schema(Publication),
    )
    def campaign_publication(identifier):
        with transaction() as conn:
            own(get(conn, "campaigns", identifier)["tenant_id"])
            return conn.execute(
                "SELECT * FROM campaign_publications WHERE id=%s", (identifier,)
            ).fetchone() or dict(
                id=identifier,
                tenant_id=g.actor["tenant_id"],
                version=0,
                published=False,
                venue="",
                information="",
            )

    @endpoint(
        app,
        "/api/v1/campaigns/<identifier>/publication",
        "POST",
        roles=("OPERATOR",),
        model=PublicationChange,
        result=schema(Publication),
    )
    def campaign_publish(identifier, data):
        def work(conn):
            own(get(conn, "campaigns", identifier, True)["tenant_id"])
            old = conn.execute(
                "SELECT * FROM campaign_publications WHERE id=%s FOR UPDATE",
                (identifier,),
            ).fetchone()
            if data["version"] != (old["version"] if old else 0):
                raise APIError(
                    "stale_version", "Publicación modificada; consulta su versión.", 412
                )
            values = {k: data[k] for k in ("published", "venue", "information")}
            values["version"] = data["version"] + 1
            result = (
                update(conn, "campaign_publications", identifier, values)
                if old
                else insert(
                    conn,
                    "campaign_publications",
                    dict(values, id=identifier, tenant_id=g.actor["tenant_id"]),
                )
            )
            record(
                conn,
                identifier,
                g.actor["tenant_id"],
                "CAMPAIGN_PUBLICATION_CHANGED",
                data["reason"],
                values,
            )
            emit(conn, "CAMPAIGN_PUBLICATION_CHANGED", identifier, g.actor["tenant_id"])
            return result

        return atomic("campaign_publish:" + identifier, data, work)
