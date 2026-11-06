"""Import an integrity-checked OSRM/OSM snapshot, never client-asserted real roads."""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import g
from redhouse.api import atomic, endpoint
from redhouse.db import get, insert
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema
from redhouse.models import ID, Model, Text, utc_date
from redhouse.security import own

ROOT = Path(__file__).resolve().parents[1] / "redhouse/reference_data/roads"


def manifest():
    try:
        return json.loads((ROOT / "manifest.json").read_text())
    except (OSError, ValueError):
        raise APIError(
            "road_source_unavailable", "Manifiesto vial ausente o inválido.", 503
        ) from None


def source_status():
    spec = manifest()
    in_window = (
        utc_date(spec["retrieved_at"])
        <= datetime.now(timezone.utc)
        < utc_date(spec["valid_until"])
    )
    try:
        build(spec["id"])
        integrity = True
    except APIError:
        integrity = False
    return dict(
        spec,
        in_validity_window=in_window,
        integrity_verified=integrity,
        available=in_window and integrity,
    )


def build(identifier):
    spec = manifest()
    if identifier != spec["id"]:
        raise APIError("unknown_road_source", "Fuente vial no registrada.", 422)
    edges, segments = [], []
    try:
        for segment in spec["segments"]:
            raw = (ROOT / segment["file"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != segment["sha256"]:
                raise ValueError("Road source digest mismatch")
            response = json.loads(raw)
            if response["code"] != "Ok" or len(response["routes"]) != 1:
                raise ValueError("No unique provider route")
            route = response["routes"][0]
            if any(
                not math.isfinite(route[k]) or route[k] <= 0
                for k in ("duration", "distance")
            ):
                raise ValueError("Invalid weight")
            coords = route["geometry"]["coordinates"]
            if (
                route["geometry"]["type"] != "LineString"
                or not 2 <= len(coords) <= 20000
            ):
                raise ValueError("Invalid geometry")
            if any(
                len(c) != 2
                or not all(math.isfinite(v) for v in c)
                or not -180 <= c[0] <= 180
                or not -90 <= c[1] <= 90
                for c in coords
            ):
                raise ValueError("Invalid coordinates")
            edges.append(
                {
                    "origin": segment["origin"],
                    "destination": segment["destination"],
                    "minutes": route["duration"] / 60,
                    "distance_km": route["distance"] / 1000,
                    "blocked": False,
                }
            )
            segments.append(
                dict(
                    segment,
                    geometry=route["geometry"],
                    snapped_waypoints=response["waypoints"],
                )
            )
    except (OSError, ValueError, KeyError, TypeError):
        raise APIError(
            "road_source_unavailable",
            "Fuente vial ausente, inválida o con integridad incorrecta.",
            503,
        ) from None
    return spec, edges, dict(spec, segments=segments)


class RoadImport(Model):
    reference_id: Text
    supersedes: ID | None = None


class RoadSources(Model):
    items: list[dict]


def install(app, Graph):
    @endpoint(
        app,
        "/api/v1/regional-graph-sources",
        roles=("MEDICAL",),
        result=schema(RoadSources),
    )
    def regional_graph_sources():
        return {"items": [source_status()]}

    @endpoint(
        app,
        "/api/v1/regional-graphs/from-reference",
        "POST",
        model=RoadImport,
        roles=("MEDICAL",),
        status=201,
        result=schema(Graph),
    )
    def regional_graph_import(data):
        spec, edges, provenance = build(data["reference_id"])
        if (
            not utc_date(spec["retrieved_at"])
            <= datetime.now(timezone.utc)
            < utc_date(spec["valid_until"])
        ):
            raise APIError(
                "road_source_expired",
                "Instantánea vial fuera de vigencia; requiere nueva adquisición.",
                409,
            )

        def work(conn):
            version = 1
            if data["supersedes"]:
                conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                    ("regional-graph:" + data["supersedes"],),
                )
                previous = get(conn, "regional_graphs", data["supersedes"])
                own(previous["tenant_id"])
                if conn.execute(
                    "SELECT 1 FROM regional_graphs WHERE supersedes=%s",
                    (data["supersedes"],),
                ).fetchone():
                    raise APIError("stale_version", "Grafo ya sustituido.", 412)
                version = previous["version"] + 1
            payload = {
                "id": str(uuid4()),
                "tenant_id": g.actor["tenant_id"],
                "author_id": g.actor["id"],
                "name": spec["name"],
                "version": version,
                "supersedes": data["supersedes"],
                "source": spec["attribution"] + " / " + spec["provider"],
                "observed_at": spec["retrieved_at"],
                "valid_until": spec["valid_until"],
                "synthetic": False,
                "region": spec["region"],
                "quality": spec["data_age"] + "; " + spec["coverage"],
                "nodes": spec["nodes"],
                "edges": edges,
                "provenance": provenance,
            }
            # Validate the same result contract before persisting trusted reference data.
            Graph.model_validate(
                dict(payload, created_at=datetime.now(timezone.utc).isoformat())
            )
            row = insert(conn, "regional_graphs", payload)
            emit(conn, "REGIONAL_GRAPH_RECORDED", row["id"], g.actor["tenant_id"])
            return row

        return atomic("regional_graph_import", data, work)
