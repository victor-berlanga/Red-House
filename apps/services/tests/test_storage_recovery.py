"""Restauración coordinada sintética; nunca conecta a producción ni a GCS."""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import time
from contextlib import nullcontext
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import jwt
import psycopg
import pytest
import redis
from PIL import Image
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from pymongo import MongoClient
from redhouse.embedded import ApplicationKernel
from scripts.local import free_port

from .final_receivers import clamd_receiver
from .helpers import iso
from .test_continuity import stopped_apis
from .test_final_operations import CONFIRM


def port_url(url, port):
    parts = urlsplit(url)
    assert parts.hostname == "127.0.0.1"
    credentials = parts.netloc.rsplit("@", 1)[0] + "@" if "@" in parts.netloc else ""
    return urlunsplit((parts.scheme, credentials + "127.0.0.1:" + str(port), parts.path, parts.query, parts.fragment))


def wait_for(probe, processes, seconds=60):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise RuntimeError("El proceso restaurado terminó antes de estar listo")
        try:
            return probe()
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("La dependencia restaurada no inició a tiempo")


def binary_manifest(root):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}


def test_coordinated_recovery_in_isolated_lab(p, tmp_path, monkeypatch, record_property):
    """Corte sin escritores; destino nuevo. No mide restauración de host ni HA."""
    admin_url = p.env.state["database_admin"]
    params = conninfo_to_dict(admin_url)
    lab_root = Path(p.env.state["directory"]).resolve()
    assert params["host"] == "127.0.0.1" and lab_root.name.startswith("red-house-ms-tests-")
    assert lab_root.is_dir() and not lab_root.is_symlink()
    for name in ("redis_admin", "mongo_admin"):
        assert urlsplit(p.env.state[name]).hostname == "127.0.0.1"
    source_root = tmp_path / "active"
    source_root.mkdir(mode=0o700)
    app = p.apps["documentos"]
    monkeypatch.setitem(app.config, "STORAGE_PROVIDER", "local")
    monkeypatch.setitem(app.config, "STORAGE_LOCAL_ROOT", str(source_root))
    monkeypatch.setitem(app.config, "STORAGE_PUBLIC_BASE_URL", "https://example.test")
    subject = p.ok("identidad_acceso", "POST", "/api/v1/accreditations", user="admin1", data=dict(
        CONFIRM, issuer="Recuperación ficticia", category="LICENSE", reference=uuid4().hex,
        valid_from=iso(days=-1), valid_until=iso(days=2)))
    old_session = p.ok("identidad_acceso", "POST", "/api/v1/auth/login", user=None,
                       data={"username": "admin1", "password": p.env.state["password"]})
    old_token, old_refresh = old_session["access_token"], old_session["refresh_token"]
    old_sid = jwt.decode(old_token, options={"verify_signature": False})["sid"]
    image = BytesIO()
    Image.new("RGB", (4, 4), "red").save(image, format="PNG")
    content = image.getvalue()

    def create_verified():
        item = p.ok("documentos", "POST", "/api/v1/documents", user="admin1", data={
            "subject_kind": "ACCREDITATION", "subject_id": subject["id"], "category": "ACCREDITATION",
            "mime_type": "image/png", "size": len(content), "sha256": hashlib.sha256(content).hexdigest(),
            "policy_reference": "Retención sintética"})
        assert app.test_client().put(urlsplit(item["upload_url"]).path, data=content, content_type="image/png").status_code == 201
        assert p.ok("documentos", "POST", "/api/v1/files/" + item["id"] + "/verify", user="admin1")["status"] == "VERIFIED"
        return item["id"]

    real_port = os.environ.get("REDHOUSE_TEST_CLAMD_PORT")
    receiver = nullcontext((int(real_port), None)) if real_port else clamd_receiver()
    children = []
    log = None
    with receiver as (port, _):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        first = create_verified()
        last_preserved = time.monotonic()
        last_preserved_utc = datetime.now(timezone.utc).isoformat()
        old_download_response = p.request(
            "documentos", "GET", "/api/v1/files/" + first + "/download",
            headers={"Authorization": "Bearer " + old_token},
        )
        assert old_download_response.status_code == 200
        old_download = old_download_response.json()["data"]["download_url"]
        issued_at = time.monotonic()
        with p.owner("documentos") as conn:
            before = conn.execute("SELECT object_path,generation,sha256,status,storage_provider FROM files WHERE id=%s", (first,)).fetchone()
            privileges_before = conn.execute(
                "SELECT has_table_privilege('rh_documentos','access_documentos.files','SELECT'), "
                "has_table_privilege('rh_documentos','access_documentos.files','INSERT'), "
                "has_schema_privilege('rh_documentos','access_receptores','USAGE'), "
                "has_table_privilege('rh_inventario','access_inventario.operations','DELETE')"
            ).fetchone()
        backup = tmp_path / "snapshot"
        backup.mkdir(mode=0o700)
        mongo_original = MongoClient(p.env.state["mongo_admin"], serverSelectionTimeoutMS=2000)
        cache_original = redis.Redis.from_url(p.env.state["redis_admin"])
        marker = uuid4().hex
        marker_after = uuid4().hex
        prefix = app.config["REDIS_PREFIX"]
        try:
            p.drain()
            audit_event = mongo_original.rh_auditoria.events.find_one(
                {"action": "FILE_VERIFIED", "resource_id": first}
            )
            assert audit_event is not None
            mongo_original.rh_auditoria.recovery_probe.insert_one({"_id": marker, "value": "antes del corte"})
            cache_original.set(prefix + "recovery:probe", marker)
            # El fixture no inicia workers; cerrar todos los listeners durante el corte.
            assert not p.env.state["worker_pids"]
            with stopped_apis(p):
                for server in p.servers.values():
                    with socket.socket() as probe:
                        probe.settimeout(0.5)
                        assert probe.connect_ex(("127.0.0.1", server.server_port)) != 0
                cache_original.execute_command("ACL", "SAVE")
                assert cache_original.save()
                shutil.copy2(lab_root / "redis.acl", backup / "redis.acl")
                shutil.copy2(lab_root / "dump.rdb", backup / "dump.rdb")
                mongo_original.admin.command({"fsync": 1, "lock": True})
                try:
                    shutil.copytree(lab_root / "mongo", backup / "mongo", ignore=shutil.ignore_patterns("mongod.lock", "WiredTiger.lock"))
                finally:
                    mongo_original.admin.command("fsyncUnlock")
                shutil.copytree(source_root, backup / "files")
                pg_bin = Path(p.env.state["infrastructure_commands"]["postgres"][0]).parent
                env = dict(os.environ, PGPASSWORD=params["password"])
                base = ["-h", params["host"], "-p", params["port"], "-U", params["user"]]
                dump = backup / "postgres.dump"
                subprocess.run([str(pg_bin / "pg_dump"), *base, "-d", "red_house", "-Fc", "-f", str(dump)],
                               env=env, check=True, capture_output=True, timeout=120)
                subprocess.run([str(pg_bin / "pg_dumpall"), *base, "--roles-only", "-f", str(backup / "roles.sql")],
                               env=env, check=True, capture_output=True, timeout=120)
            manifest = binary_manifest(backup / "files")
            second = create_verified()
            p.drain()
            assert mongo_original.rh_auditoria.events.find_one(
                {"action": "FILE_VERIFIED", "resource_id": second}
            ) is not None
            mongo_original.rh_auditoria.recovery_probe.insert_one({"_id": marker_after, "value": "después del corte"})
            cache_original.set(prefix + "recovery:probe", marker_after)
            assert p.request("identidad_acceso", "POST", "/api/v1/auth/logout", user="admin1",
                             headers={"Authorization": "Bearer " + old_token}).status_code == 200
            incident = time.monotonic()
            incident_utc = datetime.now(timezone.utc).isoformat()
            observed_rpo_seconds = incident - last_preserved
            # Clúster PostgreSQL nuevo, con otro superusuario inicial; se restauran
            # todos los roles y sus hashes SCRAM desde el dump privado del fixture.
            pg_dir = tmp_path / "restored-pg"
            pg_port = free_port()
            subprocess.run([str(pg_bin / "initdb"), "-D", str(pg_dir), "-U", "rh_recovery_admin",
                            "--pwfile", str(lab_root / "pg-password"), "--auth-local=trust",
                            "--auth-host=scram-sha-256", "--encoding=UTF8", "--no-locale"],
                           check=True, capture_output=True, timeout=120)
            log = (tmp_path / "restore.log").open("wb")
            children.append(subprocess.Popen([str(pg_bin / "postgres"), "-D", str(pg_dir),
                                             "-p", str(pg_port), "-h", "127.0.0.1", "-k", str(tmp_path)],
                                            stdout=log, stderr=subprocess.STDOUT))
            target_params = dict(params, port=str(pg_port), user="rh_recovery_admin", dbname="postgres")
            target_admin = make_conninfo(**target_params)
            wait_for(lambda: psycopg.connect(target_admin).close(), children)
            target_base = ["-h", "127.0.0.1", "-p", str(pg_port), "-U", "rh_recovery_admin"]
            subprocess.run([str(pg_bin / "psql"), *target_base, "-d", "postgres", "-X", "-v", "ON_ERROR_STOP=1",
                            "-f", str(backup / "roles.sql")], env=env, check=True, capture_output=True, timeout=120)
            with psycopg.connect(target_admin, autocommit=True) as admin:
                admin.execute("CREATE DATABASE red_house OWNER rh_shared_owner")
            subprocess.run([str(pg_bin / "pg_restore"), *target_base, "-d", "red_house", "--exit-on-error", str(dump)],
                           env=env, check=True, capture_output=True, timeout=120)
            restored_root = tmp_path / "restored-files"
            shutil.copytree(backup / "files", restored_root)
            assert binary_manifest(restored_root) == manifest
            with psycopg.connect(make_conninfo(**dict(target_params, dbname="red_house"))) as conn:
                privileges_after = conn.execute(
                    "SELECT has_table_privilege('rh_documentos','access_documentos.files','SELECT'), "
                    "has_table_privilege('rh_documentos','access_documentos.files','INSERT'), "
                    "has_schema_privilege('rh_documentos','access_receptores','USAGE'), "
                    "has_table_privilege('rh_inventario','access_inventario.operations','DELETE')"
                ).fetchone()
                assert privileges_after == privileges_before
                assert privileges_after[:2] == (True, True) and privileges_after[-1] is False
                row = conn.execute("SELECT object_path,generation,sha256,current_status,storage_provider FROM red_house.stored_file WHERE file_id=%s", (first,)).fetchone()
                assert row == before
                assert conn.execute("SELECT count(*) FROM red_house.stored_file WHERE file_id=%s", (second,)).fetchone()[0] == 0
                assert conn.execute("SELECT count(*) FROM red_house.file_scans WHERE file_id=%s AND generation=%s AND sha256=%s AND status='CLEAN'", (first, before[1], before[2])).fetchone()[0] == 1
            redis_dir = tmp_path / "restored-redis"
            redis_dir.mkdir(mode=0o700)
            shutil.copy2(backup / "dump.rdb", redis_dir / "dump.rdb")
            shutil.copy2(backup / "redis.acl", redis_dir / "redis.acl")
            redis_port, mongo_port = free_port(), free_port()
            redis_conf = redis_dir / "redis.conf"
            redis_conf.write_text(f"bind 127.0.0.1\nport {redis_port}\nprotected-mode yes\naclfile {redis_dir / 'redis.acl'}\ndir {redis_dir}\nappendonly no\n")
            redis_conf.chmod(0o600)
            mongo_dir = tmp_path / "restored-mongo"
            shutil.copytree(backup / "mongo", mongo_dir)
            try:
                children.append(subprocess.Popen([p.env.state["infrastructure_commands"]["redis"][0], str(redis_conf)], stdout=log, stderr=subprocess.STDOUT))
                children.append(subprocess.Popen([p.env.state["infrastructure_commands"]["mongodb"][0], "--dbpath", str(mongo_dir), "--port", str(mongo_port), "--bind_ip", "127.0.0.1", "--auth", "--quiet", "--wiredTigerCacheSizeGB", "0.25"], stdout=log, stderr=subprocess.STDOUT))
                cache = redis.Redis.from_url(port_url(p.env.state["redis_admin"], redis_port))
                mongo = MongoClient(port_url(p.env.state["mongo_admin"], mongo_port), serverSelectionTimeoutMS=1000)
                wait_for(cache.ping, children)
                wait_for(lambda: mongo.admin.command("ping"), children)
                assert cache.get(prefix + "recovery:probe").decode() == marker
                assert mongo.rh_auditoria.recovery_probe.find_one({"_id": marker})["value"] == "antes del corte"
                assert mongo.rh_auditoria.recovery_probe.find_one({"_id": marker_after}) is None
                assert mongo.rh_auditoria.events.find_one({"_id": audit_event["_id"]}) == audit_event
                assert mongo.rh_auditoria.events.find_one({"action": "FILE_VERIFIED", "resource_id": second}) is None
                assert cache.exists(prefix + "session:" + old_sid) == 1
                # Una copia anterior puede resucitar sesiones revocadas: invalidar todas antes de servir.
                for area in ("session", "refresh", "used_refresh", "reauth", "permissions", "permission_version"):
                    keys = list(cache.scan_iter(match=prefix + area + ":*"))
                    if keys:
                        cache.delete(*keys)
                assert cache.exists(prefix + "session:" + old_sid) == 0
                configs = {}
                for name, old in p.apps.items():
                    cfg = dict(old.config)
                    db = conninfo_to_dict(cfg["DATABASE_URL"])
                    cfg.update(DATABASE_URL=make_conninfo(**dict(db, dbname="red_house", port=str(pg_port))), DATABASE_POOL_SIZE=0,
                               REDIS_URL=port_url(cfg["REDIS_URL"], redis_port))
                    if cfg.get("MONGODB_URL"):
                        cfg["MONGODB_URL"] = port_url(cfg["MONGODB_URL"], mongo_port)
                    if name == "documentos":
                        cfg.update(STORAGE_PROVIDER="local", STORAGE_LOCAL_ROOT=str(restored_root), STORAGE_PUBLIC_BASE_URL="https://example.test")
                    configs[name] = cfg
                kernel = ApplicationKernel(configs)
                from redhouse.events import mongodb
                with kernel.apps["auditoria"].app_context(), mongodb() as service_mongo:
                    assert service_mongo["rh_auditoria"].events.find_one({"_id": audit_event["_id"]}) == audit_event
                assert time.monotonic() - issued_at < 295, "La capacidad venció antes de comprobar revocación"
                assert jwt.decode(old_token, options={"verify_signature": False})["exp"] > time.time()
                old_headers = {"Authorization": "Bearer " + old_token, "Accept": "application/json"}
                assert kernel.request("documentos", "GET", "/api/v1/files/" + first + "/download", headers=old_headers).status_code == 401
                assert kernel.request("documentos", "GET", urlsplit(old_download).path).status_code == 401
                assert kernel.request("identidad_acceso", "POST", "/api/v1/auth/refresh", data=json.dumps({"refresh_token": old_refresh}), headers={"Content-Type": "application/json"}).status_code == 401
                login = kernel.request("identidad_acceso", "POST", "/api/v1/auth/login", data=json.dumps({"username": "admin1", "password": p.env.state["password"]}), headers={"Content-Type": "application/json", "Accept": "application/json"})
                assert login.status_code == 200, login.text
                token = login.json()["data"]["access_token"]
                headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
                outsider = kernel.request("identidad_acceso", "POST", "/api/v1/auth/login",
                                          data=json.dumps({"username": "medical2", "password": p.env.state["password"]}),
                                          headers={"Content-Type": "application/json", "Accept": "application/json"})
                assert outsider.status_code == 200
                denied = kernel.request("documentos", "GET", "/api/v1/files/" + first + "/download",
                                        headers={"Authorization": "Bearer " + outsider.json()["data"]["access_token"], "Accept": "application/json"})
                assert denied.status_code == 403
                issued = kernel.request("documentos", "GET", "/api/v1/files/" + first + "/download", headers=headers)
                assert issued.status_code == 200, issued.text
                path = urlsplit(issued.json()["data"]["download_url"]).path.replace("/portal-storage/", "/storage/", 1)
                downloaded = kernel.request("documentos", "GET", path)
                assert downloaded.status_code == 200 and downloaded.content == content
                measured_restore_seconds = time.monotonic() - incident
                # La prueba niega explícitamente cualquier intento de fallback al proveedor GCS.
                import redhouse.storage as storage
                calls = []
                def forbidden_gcs():
                    calls.append(True)
                    raise AssertionError("No debe invocarse GCS")
                monkeypatch.setattr(storage, "bucket", forbidden_gcs)
                object_file = restored_root / str(before[0]).rsplit("/", 1)[-1]
                hidden = restored_root / ".temporarily-missing"
                object_file.rename(hidden)
                assert kernel.request("documentos", "GET", path).status_code == 503
                hidden.rename(object_file)
                restored_root.chmod(0o755)
                try:
                    assert kernel.request("documentos", "GET", path).status_code == 503
                finally:
                    restored_root.chmod(0o700)
                assert not calls
                assert kernel.request("documentos", "GET", path).content == content
                record_property("restore_seconds", measured_restore_seconds)
                record_property("observed_rpo_seconds", observed_rpo_seconds)
                record_property("last_preserved_confirmation_utc", last_preserved_utc)
                record_property("incident_utc", incident_utc)
                record_property("post_snapshot_objects_missing", 1)
                record_property("post_snapshot_mongo_events_missing", 1)
                record_property("backup_dump_bytes", dump.stat().st_size)
                record_property("backup_roles_bytes", (backup / "roles.sql").stat().st_size)
                record_property("backup_objects", len(manifest))
                record_property("scanner", "clamd_real" if real_port else "test_receiver")
                record_property("pre_restore_sessions_invalidated", True)
                record_property("scope", "isolated restored PostgreSQL cluster and roles, MongoDB, Redis ACL/RDB and private local files; signing keys reused")
                mongo.close()
                cache.close()
            finally:
                for child in reversed(children):
                    if child.poll() is None:
                        child.terminate()
                for child in reversed(children):
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait(timeout=5)
                log.close()
        finally:
            mongo_original.close()
            cache_original.close()
            for child in reversed(children):
                if child.poll() is None:
                    child.terminate()
            for child in reversed(children):
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
            if log and not log.closed:
                log.close()
            # Material de copia y credenciales de prueba no deben quedar en
            # el directorio retenido por pytest tras el caso.
            for name in ("snapshot", "restored-pg", "restored-mongo", "restored-redis", "restored-files", "active"):
                target = tmp_path / name
                if target.exists():
                    shutil.rmtree(target)
            (tmp_path / "restore.log").unlink(missing_ok=True)
