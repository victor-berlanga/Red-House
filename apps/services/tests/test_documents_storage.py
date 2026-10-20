"""Proyecciones reales y archivos privados GCS; sin reemplazar dependencias por mocks."""

import hashlib
import json
import os
import time
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
import requests
from PIL import Image
from pymongo import MongoClient

from .helpers import evaluation, move, plan, recipient_request, reservation, resource
from .test_web_integration import form, login, web  # noqa: F401


def artifact(name, value):
    if root := os.environ.get("REDHOUSE_RESULT_DIR"):
        directory = Path(root)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / (name + ".json")).write_text(
            json.dumps(value, indent=2, default=str) + "\n"
        )


def planned(p):
    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    return plan(p, reservation(p, ev, unit)["reservation"])


def test_projection_updates_order_dedup_rebuild_indexes_and_permissions(p):
    from ms_transporte.projection import project, rebuild
    from redhouse.events import mongodb

    shipment = planned(p)
    shipment = move(p, shipment, "PREPARED", "operator1")
    shipment = move(p, shipment, "COLLECTED", "transport1")
    p.drain()
    app = p.apps["transporte"]
    with MongoClient(p.env.state["mongo_admin"]) as admin:
        database = admin.rh_transporte
        events = list(
            database.events.find(
                {"resource_id": shipment["id"], "metadata.sequence": {"$exists": True}}
            ).sort("metadata.sequence", -1)
        )
        assert len(events) == 3
        before = database.shipment_tracking.find_one({"_id": shipment["id"]})
        with app.app_context(), mongodb() as runtime:
            for event in events + events:
                project(runtime.rh_transporte, event)
            from pymongo.errors import OperationFailure

            with pytest.raises(OperationFailure):
                runtime.rh_transporte.events.update_one(
                    {"_id": events[0]["_id"]}, {"$set": {"action": "ALTERED"}}
                )
        assert database.shipment_tracking.find_one({"_id": shipment["id"]}) == before
        database.shipment_tracking.delete_many({})
        assert rebuild(database) >= 3
        assert database.shipment_tracking.find_one({"_id": shipment["id"]}) == before
        explanation = database.command(
            "explain",
            {
                "find": "shipment_tracking",
                "filter": {"region_id": p.env.state["region_id"]},
            },
            verbosity="executionStats",
        )
        assert "regional_state" in str(explanation["queryPlanner"]["winningPlan"])
        artifact(
            "mongo-projection",
            {
                "projection": before,
                "events_replayed": len(events) * 2,
                "unchanged_after_duplicates_and_rebuild": True,
                "explain": explanation,
                "indexes": list(database.shipment_tracking.list_indexes()),
                "immutable_event_update": "denied",
            },
        )
    row = p.ok(
        "transporte",
        "GET",
        "/api/v1/shipments/" + shipment["id"] + "/tracking",
        user="transport1",
    )
    assert (
        row["version"] == 3 and row["last_state"] == "COLLECTED" and not row["pending"]
    )
    assert (
        p.request(
            "transporte",
            "GET",
            "/api/v1/shipments/" + shipment["id"] + "/tracking",
            user="transport2",
        ).status_code
        == 403
    )
    summary = p.ok(
        "transporte", "GET", "/api/v1/shipment-statistics", user="coordinator1"
    )
    assert any(row["last_state"] == "COLLECTED" for row in summary["items"])


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_GCS_TEST_BUCKET"),
    reason="Requiere bucket GCS real autorizado y ADC; no se simula nube.",
)
def test_gcs_web_upload_private_download_validation_expiry_and_recovery(
    p,
    web,
    monkeypatch,  # noqa: F811 - imported pytest fixture
):
    from google.cloud import storage

    app = p.apps["transporte"]
    monkeypatch.setitem(
        app.config, "GCS_BUCKET", os.environ["REDHOUSE_GCS_TEST_BUCKET"]
    )
    monkeypatch.setitem(
        app.config, "GCS_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT")
    )
    bucket = storage.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT")).bucket(
        os.environ["REDHOUSE_GCS_TEST_BUCKET"]
    )
    assert (
        p.request("transporte", "GET", "/health/storage", user=None).status_code == 200
    )
    shipment = planned(p)
    client = login(web, p, "operator1")
    page = "/traslados/" + shipment["id"] + "/archivos"
    content = BytesIO()
    Image.new("RGB", (4, 4), color="red").save(content, format="PNG")
    payload = content.getvalue()
    objects = []
    try:
        values = form(client, page)
        values["evidence"] = (BytesIO(payload), "evidencia-ficticia.png", "image/png")
        result = client.post(page, data=values, content_type="multipart/form-data")
        assert result.status_code == 303, result.data[:1000]
        files = p.ok(
            "transporte",
            "GET",
            f"/api/v1/shipments/{shipment['id']}/files",
            user="operator1",
        )["items"]
        row = files[0]
        objects.append(row["object_path"])
        assert (
            row["status"] == "VERIFIED"
            and row["sha256"] == hashlib.sha256(payload).hexdigest()
        )
        with p.owner("transporte") as conn:
            assert conn.execute(
                "SELECT status,generation FROM files WHERE id=%s", (row["id"],)
            ).fetchone() == ("VERIFIED", row["generation"])
        downloaded = client.get("/archivos/" + row["id"] + "/descargar")
        assert downloaded.status_code == 303
        received = requests.get(downloaded.headers["Location"], timeout=10)
        assert received.content == payload
        anonymous = requests.get(bucket.blob(row["object_path"]).public_url, timeout=10)
        assert anonymous.status_code in (401, 403)
        assert (
            p.request(
                "transporte",
                "GET",
                "/api/v1/files/" + row["id"] + "/download",
                user="transport2",
            ).status_code
            == 403
        )
        assert (
            p.request(
                "transporte",
                "GET",
                "/api/v1/files/" + str(uuid4()) + "/download",
                user="operator1",
            ).status_code
            == 404
        )
        for raw, mime, expected in [
            (b"not a PNG", "image/png", 422),
            (payload, "image/png", 404),
        ]:
            prepared = p.ok(
                "transporte",
                "POST",
                f"/api/v1/shipments/{shipment['id']}/files",
                user="operator1",
                data={
                    "mime_type": mime,
                    "size": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                },
            )
            object_path = prepared["file"]["object_path"]
            objects.append(object_path)
            if expected == 422:
                assert (
                    requests.put(
                        prepared["upload_url"],
                        data=raw,
                        headers=prepared["upload_headers"],
                        timeout=10,
                    ).status_code
                    == 200
                )
                assert (
                    requests.put(
                        prepared["upload_url"],
                        data=raw,
                        headers=prepared["upload_headers"],
                        timeout=10,
                    ).status_code
                    == 412
                )
            response = p.request(
                "transporte",
                "POST",
                "/api/v1/files/" + prepared["file"]["id"] + "/verify",
                user="operator1",
            )
            assert response.status_code == expected
        short_url = bucket.blob(row["object_path"]).generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=1),
            method="GET",
            credentials=app.extensions["gcs_signing"],
        )
        time.sleep(2)
        expired = requests.get(short_url, timeout=10)
        # GCS XML API documents ExpiredToken as HTTP 400, not permission 403.
        from lxml import etree

        assert expired.status_code == 400
        assert etree.fromstring(expired.content).findtext("Code") == "ExpiredToken"
        with monkeypatch.context() as outage:
            outage.setitem(app.config, "GCS_BUCKET", "redhouse-missing-" + uuid4().hex)
            assert (
                p.request("transporte", "GET", "/health/storage", user=None).status_code
                == 503
            )
        assert (
            p.request("transporte", "GET", "/health/storage", user=None).status_code
            == 200
        )
        artifact(
            "gcs-real",
            {
                "bucket": bucket.name,
                "file": row,
                "web_upload_http": result.status_code,
                "signed_download_http": received.status_code,
                "download_sha256": hashlib.sha256(received.content).hexdigest(),
                "anonymous_http": anonymous.status_code,
                "expired_http": expired.status_code,
                "expired_code": etree.fromstring(expired.content).findtext("Code"),
                "invalid_content_http": 422,
                "missing_object_http": 404,
                "dependency_failure_and_recovery": [503, 200],
                "cleanup": "test objects deleted in finally",
            },
        )
    finally:
        from google.api_core.exceptions import NotFound

        for path in objects:
            try:
                bucket.blob(path).delete(timeout=10)
            except NotFound:
                pass
