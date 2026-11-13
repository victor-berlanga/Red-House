"""Portal modular y Documentos sin listeners de API; receptor ClamD explícito."""

import os
from contextlib import nullcontext
from io import BytesIO
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

from PIL import Image

from .final_receivers import clamd_receiver
from .helpers import iso
from .test_continuity import autonomous  # noqa: F401
from .test_final_operations import CONFIRM
from .test_web_integration import form, login


def test_document_web_upload_without_api_listeners(
    autonomous, p, tmp_path, monkeypatch
):
    app = autonomous.extensions["application_kernel"].apps["documentos"]
    monkeypatch.setitem(app.config, "STORAGE_PROVIDER", "local")
    monkeypatch.setitem(app.config, "STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setitem(app.config, "STORAGE_PUBLIC_BASE_URL", "https://example.test")
    subject = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/accreditations",
        user="admin1",
        data=dict(
            CONFIRM,
            issuer="Prueba",
            category="LICENSE",
            reference=uuid4().hex,
            valid_from=iso(days=-1),
            valid_until=iso(days=2),
        ),
    )
    client = login(autonomous, p, "admin1")
    path = "/documentos/nuevo?" + urlencode(
        {"subject_kind": "ACCREDITATION", "subject_id": subject["id"]}
    )
    data = form(client, path)
    image = BytesIO()
    Image.new("RGB", (4, 4), "red").save(image, format="PNG")
    content = image.getvalue()
    data.update(
        subject_kind="ACCREDITATION",
        subject_id=subject["id"],
        policy_reference="Política de prueba",
        evidence=(BytesIO(content), "document.png", "image/png"),
    )
    real_port = os.environ.get("REDHOUSE_TEST_CLAMD_PORT")
    receiver = nullcontext((int(real_port), None)) if real_port else clamd_receiver()
    with receiver as (port, scanned):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        response = client.post(path, data=data, content_type="multipart/form-data")
        assert response.status_code == 303, response.data[:3000]
        if scanned is not None:
            assert scanned == [content]
        else:
            from redhouse.malware import scan

            with app.app_context():
                sample = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
                assert scan(sample) == "INFECTED"
    identifier = response.headers["Location"].rstrip("/").split("/")[-1]
    status = p.ok(
        "documentos",
        "GET",
        "/api/v1/documents/" + identifier + "/verified",
        user="admin1",
    )
    assert status["analysis"] == "CLEAN"
    kernel = autonomous.extensions["application_kernel"]
    downloaded = kernel.request(
        "documentos", "GET", "/api/v1/files/" + identifier + "/download",
        headers={"Authorization": "Bearer " + p.tokens["admin1"], "Accept": "application/json"},
    ).json()["data"]
    download_path = urlsplit(downloaded["download_url"]).path
    assert download_path.startswith("/portal-storage/v1/objects/")
    assert client.get(download_path).data == content
    assert client.put(download_path, data=content, content_type="application/pdf").status_code == 401
    assert p.request("identidad_acceso", "POST", "/api/v1/auth/logout", user="admin1").status_code == 200
    assert client.get(download_path).status_code == 401
    renewed = p.ok("identidad_acceso", "POST", "/api/v1/auth/login", user=None,
                   data={"username": "admin1", "password": p.env.state["password"]})
    p.tokens["admin1"] = renewed["access_token"]
