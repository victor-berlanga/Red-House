"""I06-05 opt-in: GCS real, corte local de Documentos y recuperación del mismo objeto.

No cambia IAM, bucket ni objetos anteriores. El proxy transporta TLS sin terminarlo.
La preparación y PUT preceden al corte; Chrome verifica, recupera y descarga.
"""

import base64
import hashlib
import json
import os
import select
import selectors
import socket
import subprocess
import threading
import time
from collections import Counter
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

import pytest
import requests
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from google.api_core.exceptions import NotFound
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials
from PIL import Image
from werkzeug.serving import make_server, make_ssl_devcert

from .helpers import iso
from .test_continuity import autonomous as autonomous  # noqa: PLC0414 - fixture pytest
from .test_final_operations import CONFIRM
from .test_gcs_real_isolated import BUCKET
from .test_portal_private_document_browser import QuietHandler, owned_clamd


class GCSGate:
    """Solo CONNECT al destino GCS exacto; deny cierra todos los túneles propios."""

    def __init__(self):
        self.lock = threading.Lock()
        self.denied = False
        self.epoch = 0
        self.tunnels = set()
        self.accepted = 0
        self.rejected = 0
        self.closed = 0

    def admit(self, authority):
        with self.lock:
            if self.denied or authority != "storage.googleapis.com:443":
                self.rejected += 1
                return None
            return self.epoch

    def attach(self, epoch, pair):
        with self.lock:
            # Incluye deny seguido de allow mientras connect() seguía pendiente.
            if self.denied or epoch != self.epoch:
                self.rejected += 1
                return False
            self.tunnels.add(pair)
            self.accepted += 1
            return True

    def detach(self, pair):
        with self.lock:
            self.tunnels.discard(pair)

    def block(self):
        with self.lock:
            self.denied = True
            self.epoch += 1
            pairs = list(self.tunnels)
            self.tunnels.clear()
            self.closed += len(pairs)
        for pair in pairs:
            for connection in pair:
                try:
                    connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                connection.close()

    def allow(self):
        with self.lock:
            self.denied = False


@contextmanager
def gcs_connect_proxy():
    gate = GCSGate()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_args):
            pass

        def do_CONNECT(self):
            epoch = gate.admit(self.path)
            if epoch is None:
                self.send_error(503)
                return
            upstream = None
            pair = None
            try:
                upstream = socket.create_connection(
                    ("storage.googleapis.com", 443), timeout=5
                )
                pair = (self.connection, upstream)
                if not gate.attach(epoch, pair):
                    self.send_error(503)
                    return
                self.send_response(200, "Connection Established")
                self.end_headers()
                for connection in pair:
                    connection.settimeout(1)
                # Nunca se interpreta el contenido TLS, ni se escribe en logs.
                while not gate.denied:
                    readable, _, _ = select.select(pair, [], [], 1)
                    for connection in readable:
                        content = connection.recv(65536)
                        if not content:
                            return
                        other = (
                            upstream
                            if connection is self.connection
                            else self.connection
                        )
                        other.sendall(content)
            except (OSError, ValueError):
                # deny cierra descriptores incluso si select/sendall está activo.
                return
            finally:
                if pair is not None:
                    gate.detach(pair)
                if upstream is not None:
                    upstream.close()
                self.close_connection = True

    class Server(ThreadingHTTPServer):
        def get_request(self):
            connection, address = super().get_request()
            connection.settimeout(5)
            return connection, address

        def handle_error(self, _request, _client_address):
            # Las desconexiones controladas no imprimen contenido de solicitudes.
            pass

    server = Server(("127.0.0.1", 0), Handler)
    server.daemon_threads = False
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield gate, f"http://127.0.0.1:{server.server_port}"
    finally:
        gate.block()
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        assert not thread.is_alive()


def gcs_signed_target(url, object_path):
    try:
        parsed = urlsplit(url)
        valid = (
            parsed.scheme == "https"
            and parsed.hostname == "storage.googleapis.com"
            and parsed.port in (None, 443)
            and not parsed.username
            and not parsed.password
            and not parsed.fragment
            and parsed.path == f"/{BUCKET}/{object_path}"
            and parse_qs(parsed.query).get("X-Goog-Expires") == ["300"]
        )
    except ValueError:
        valid = False
    if not valid:
        raise RuntimeError("Destino o TTL GCS inválido; capacidad omitida.")


def gcs_document_state(p, subject, identifier, source, generation, recovered):
    """Oráculo SQL de solo lectura, correlacionado con objeto y actor propios."""
    assert str(UUID(identifier)) == identifier
    actor = p.env.state["accounts"]["admin1"]["id"]
    expected_path = f"documents/{p.env.state['tenants'][0]}/{identifier}"
    with p.owner("documentos") as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        row = conn.execute(
            "SELECT f.status,f.size,f.sha256,f.mime_type,f.generation,f.owner_id::text,"
            "f.object_path,f.storage_provider,d.version,d.supersedes "
            "FROM files f JOIN document_metadata d ON d.id=f.id "
            "WHERE f.id=%s AND d.subject_kind='ACCREDITATION' AND d.subject_id=%s",
            (identifier, subject),
        ).fetchone()
        assert row == (
            "VERIFIED" if recovered else "ERROR",
            Path(source["path"]).stat().st_size,
            source["sha256"],
            "image/png",
            str(generation) if recovered else None,
            actor,
            expected_path,
            "gcs",
            1,
            None,
        )
        assert (
            conn.execute(
                "SELECT count(*) FROM document_metadata WHERE subject_id=%s",
                (subject,),
            ).fetchone()[0]
            == 1
        )
        scans = conn.execute(
            "SELECT status,generation,sha256,engine,engine_version,signature_version,"
            "signature_at,signature_max_age_seconds FROM file_scans WHERE file_id=%s",
            (identifier,),
        ).fetchall()
        if recovered:
            assert len(scans) == 1
            assert scans[0][:4] == (
                "CLEAN",
                str(generation),
                source["sha256"],
                "CLAMD_INSTREAM",
            )
            assert scans[0][4] and scans[0][5].isdigit() and scans[0][6]
            assert scans[0][7] == 172800
        else:
            assert scans == []  # El corte GCS sucede antes del escaneo real.
        events = conn.execute(
            "SELECT event->>'action',event->>'actor_id',event->>'source',"
            "event->'metadata'->>'code' FROM activity_events "
            "WHERE event->>'resource_id'=%s AND event->>'action' IN "
            "('DOCUMENT_PREPARED','FILE_ERROR','FILE_VERIFIED','FILE_REJECTED')",
            (identifier,),
        ).fetchall()
        expected = Counter(DOCUMENT_PREPARED=1, FILE_ERROR=1)
        if recovered:
            expected.update(FILE_VERIFIED=1)
        assert Counter(event[0] for event in events) == expected
        assert all(event[1:3] == (actor, "documentos") for event in events)
        assert [event[3] for event in events if event[0] == "FILE_ERROR"] == [
            "storage_unavailable"
        ]


@pytest.mark.skipif(
    os.environ.get("REDHOUSE_TEST_GCS_FAILURES") != "1"
    or not os.environ.get("REDHOUSE_BROWSER_TESTS")
    or os.environ.get("REDHOUSE_TEST_GCS_BUCKET") != BUCKET,
    reason="Requiere autorización GCS sintético, Chrome y corte CONNECT local explícitos",
)
def test_gcs_outage_and_same_generation_recovery_in_browser(
    autonomous, p, tmp_path, monkeypatch
):
    from redhouse.malware import scan
    from redhouse.storage import bucket

    web = autonomous
    web.config.update(PRODUCTION=True, SESSION_COOKIE_SECURE=True)
    output = Path(os.environ["REDHOUSE_BROWSER_RESULTS"])
    output.mkdir(parents=True, exist_ok=True)
    docapp = p.apps["documentos"]
    source_path = tmp_path / "gcs-synthetic.png"
    Image.new("RGB", (16, 16), "blue").save(source_path, format="PNG")
    content = source_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    source = {"path": str(source_path), "sha256": digest, "mime": "image/png"}
    # El helper existente comprueba frescura real. Nunca modifica ni renueva firmas.
    with owned_clamd(tmp_path) as (port, _start, _stop, scanner_pids):
        for key, value in {
            "STORAGE_PROVIDER": "gcs",
            "GCS_BUCKET": BUCKET,
            "GCS_PROJECT": "sistemas-integracion-01",
            "CLAMD_HOST": "127.0.0.1",
            "CLAMD_PORT": port,
            "CLAMD_VERSION_TIMEZONE": "UTC",
            "CLAMD_SIGNATURE_MAX_AGE_SECONDS": 172800,
        }.items():
            monkeypatch.setitem(docapp.config, key, value)
        with docapp.app_context():
            assert scan(content) == "CLEAN"
            assert (
                scan(
                    rb"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
                )
                == "INFECTED"
            )
        subject = p.ok(
            "identidad_acceso",
            "POST",
            "/api/v1/accreditations",
            user="admin1",
            data=dict(
                CONFIRM,
                issuer="Ensayo sintético de recuperación GCS",
                category="LICENSE",
                reference="GCS-FAILURE-" + uuid4().hex,
                valid_from=iso(days=-1),
                valid_until=iso(days=2),
            ),
        )
        prepared = p.ok(
            "documentos",
            "POST",
            "/api/v1/documents",
            user="admin1",
            data={
                "subject_kind": "ACCREDITATION",
                "subject_id": subject["id"],
                "category": "ACCREDITATION",
                "mime_type": "image/png",
                "size": len(content),
                "sha256": digest,
                "policy_reference": "Ensayo sintético aislado; objeto desechable",
            },
        )
        identifier = prepared["id"]
        object_path = f"documents/{p.env.state['tenants'][0]}/{identifier}"
        with p.owner("documentos") as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            assert conn.execute(
                "SELECT object_path,storage_provider FROM files WHERE id=%s",
                (identifier,),
            ).fetchone() == (object_path, "gcs")
        gcs_signed_target(prepared["upload_url"], object_path)
        assert prepared["upload_headers"]["x-goog-if-generation-match"] == "0"
        with docapp.app_context():
            blob = bucket().blob(object_path)
        client = docapp.extensions["gcs_client"]
        assert isinstance(client._credentials, ImpersonatedCredentials), (
            "El ensayo exige ADC impersonada; no cambia credenciales locales"
        )
        session = client._http
        assert session.verify is True
        original_proxies, original_trust_env = session.proxies.copy(), session.trust_env
        journal = output / "gcs-cleanup.private.json"
        journal_created = False
        attempted = False
        outcome_known = False
        uploaded_by_test = False
        generation = None
        cleaned = False
        try:
            descriptor = os.open(journal, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            journal_created = True
            with os.fdopen(descriptor, "w") as saved:
                json.dump(
                    {"bucket": BUCKET, "object": object_path, "sha256": digest}, saved
                )
                saved.flush()
                os.fsync(saved.fileno())
            attempted = True
            try:
                with requests.Session() as uploader:
                    uploader.trust_env = False
                    uploaded = uploader.put(
                        prepared["upload_url"],
                        data=content,
                        headers=prepared["upload_headers"],
                        timeout=30,
                        allow_redirects=False,
                    )
            except requests.RequestException:
                raise RuntimeError(
                    "PUT GCS incierto; conservar diario privado."
                ) from None
            outcome_known = True
            uploaded_by_test = uploaded.status_code == 200
            assert uploaded.status_code == 200
            raw_generation = uploaded.headers.get("x-goog-generation", "")
            assert raw_generation.isdigit() and int(raw_generation) > 0
            generation = int(raw_generation)
            next_journal = journal.with_suffix(".next")
            descriptor = os.open(
                next_journal, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
            )
            with os.fdopen(descriptor, "w") as saved:
                json.dump(
                    {
                        "bucket": BUCKET,
                        "object": object_path,
                        "sha256": digest,
                        "generation": generation,
                    },
                    saved,
                )
                saved.flush()
                os.fsync(saved.fileno())
            os.replace(next_journal, journal)
            with gcs_connect_proxy() as (gate, proxy):
                # Solo esta AuthorizedSession. No HTTPS_PROXY global ni cambios al
                # cliente web, ADC, IAM signer, otros servicios o Chrome.
                session.proxies = {"https": proxy}
                session.trust_env = False
                try:
                    with docapp.app_context():
                        blob.reload(
                            if_generation_match=generation, timeout=8, retry=None
                        )
                    assert str(blob.generation) == str(generation)
                    assert (
                        blob.size == len(content) and blob.content_type == "image/png"
                    )
                    assert gate.accepted >= 1
                    gate.block()
                    assert not gate.tunnels
                    _gcs_browser(
                        web,
                        p,
                        tmp_path,
                        output,
                        subject["id"],
                        identifier,
                        source,
                        generation,
                        gate,
                    )
                    assert gate.rejected >= 1 and gate.accepted >= 2
                    (output / "persistencia.json").write_text(
                        json.dumps(
                            {
                                "same_uuid": True,
                                "same_generation": True,
                                "prepare_count": 1,
                                "verify_attempts": 2,
                                "error": "storage_unavailable",
                                "error_http": 503,
                                "download_blocked_http": 409,
                                "recovered_status": "VERIFIED",
                                "scan": "CLEAN",
                                "download_sha256": digest,
                                "real_gcs": True,
                                "gcs_tls_ca_validation": True,
                                "proxy": {
                                    "accepted": gate.accepted,
                                    "rejected": gate.rejected,
                                    "closed_on_cut": gate.closed,
                                },
                                "scanner_processes": len(scanner_pids),
                                "backend": "monolith_without_api_listeners",
                                "scope": "Documentos SDK egress; preparation/PUT precede fault",
                            },
                            indent=2,
                        )
                        + "\n"
                    )
                finally:
                    gate.allow()
                    session.proxies = original_proxies
                    session.trust_env = original_trust_env
        finally:
            # Jamás se elimina por prefijo ni sin generación confirmada propia.
            try:
                if uploaded_by_test and generation is not None:
                    with docapp.app_context():
                        blob.reload(
                            if_generation_match=generation, timeout=15, retry=None
                        )
                        actual = blob.download_as_bytes(
                            if_generation_match=generation, timeout=15, retry=None
                        )
                        assert hashlib.sha256(actual).hexdigest() == digest
                        blob.delete(
                            if_generation_match=generation, timeout=15, retry=None
                        )
                        try:
                            blob.reload(timeout=15, retry=None)
                        except NotFound:
                            cleaned = True
                elif not attempted or (outcome_known and not uploaded_by_test):
                    cleaned = True
            finally:
                client.close()
                (output / "limpieza.json").write_text(
                    json.dumps(
                        {
                            "cleaned": cleaned,
                            "generation_confirmed": generation is not None,
                            "generation_precondition": generation is not None,
                            "physical_soft_delete_expiry_not_asserted": True,
                        },
                        indent=2,
                    )
                    + "\n"
                )
                if cleaned and journal_created:
                    journal.unlink(missing_ok=True)
            assert cleaned, (
                "Limpieza GCS incompleta: conservar diario privado y fixture"
            )


def _gcs_browser(
    web, p, tmp_path, output, subject, identifier, source, generation, gate
):
    cert, key = make_ssl_devcert(str(tmp_path / "portal-tls"), host="localhost")
    certificate = x509.load_pem_x509_certificate(Path(cert).read_bytes())
    spki = certificate.public_key().public_bytes(
        Encoding.DER, PublicFormat.SubjectPublicKeyInfo
    )
    local_spki = base64.b64encode(hashlib.sha256(spki).digest()).decode("ascii")
    server = make_server(
        "127.0.0.1",
        0,
        web,
        threaded=True,
        ssl_context=(cert, key),
        request_handler=QuietHandler,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    process = None
    try:
        diagnostic = output / "browser.private.log"
        with diagnostic.open("xb") as log:
            diagnostic.chmod(0o600)
            process = subprocess.Popen(
                ["node", "scripts/verify_portal_private_documents.cjs"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                text=True,
            )
            process.stdin.write(
                json.dumps(
                    {
                        "scenario": "gcs-failure",
                        "base": f"https://localhost:{server.server_port}",
                        "password": p.env.state["password"],
                        "subject": subject,
                        "document": identifier,
                        "files": [source],
                        "output": str(output),
                        "root": str(Path.cwd()),
                        "local_tls_spki": local_spki,
                    }
                )
                + "\n"
            )
            process.stdin.flush()
            deadline = time.monotonic() + 180
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                for action in ("gcs-restore", "gcs-complete"):
                    assert selector.select(max(0, deadline - time.monotonic())), (
                        "Chrome no pidió control GCS"
                    )
                    message = json.loads(process.stdout.readline())
                    assert message == {"control": action, "document": identifier}
                    recovered = action == "gcs-complete"
                    gcs_document_state(
                        p, subject, identifier, source, generation, recovered
                    )
                    if not recovered:
                        assert gate.denied and gate.rejected >= 1
                        gate.allow()
                    process.stdin.write(
                        json.dumps({"control": action, "passed": True}) + "\n"
                    )
                    process.stdin.flush()
            process.wait(timeout=max(1, deadline - time.monotonic()))
            assert process.returncode == 0, (
                "Chrome falló; conservar recibo y log privado"
            )
        report = json.loads((output / "browser.json").read_text())
        assert report["passed"] and report["scenario"] == "gcs-failure"
        assert report["documents"] == [identifier]
        assert report["mutations"] == {"prepare": 0, "verify": 2}
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
