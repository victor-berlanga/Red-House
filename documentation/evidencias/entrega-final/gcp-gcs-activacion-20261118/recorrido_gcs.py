# Recorrido real Documentos+GCS con donor1 (datos sintéticos). No imprime credenciales ni URLs firmadas.
import hashlib, json, os, struct, sys, time, zlib
from urllib.parse import urlsplit
from uuid import uuid4
import requests
O = "https://34.18.186.116"
pw = os.environ.pop("RH_PW")
out = {}
def h(tok=None):
    d = {"Accept": "application/json", "Idempotency-Key": uuid4().hex}
    if tok: d["Authorization"] = "Bearer " + tok
    return d
def png():
    raw = b"\x00\xff\x00\x00"
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
r = requests.post(O + "/services/identidad-acceso/api/v1/auth/login", json={"username": "donor1", "password": pw}, headers=h(), timeout=20)
out["login"] = r.status_code; tok = r.json()["data"]["access_token"]
r = requests.get(O + "/services/donantes/api/v1/donors?page_size=5", headers=h(tok), timeout=20)
items = r.json()["data"]["items"]; out["donors_visible"] = len(items); donor = items[0]["id"]
r = requests.get(O + "/services/documentos/api/v1/documents?page_size=100", headers=h(tok), timeout=20)
before = r.json()["data"]["items"] if r.ok else []
out["documents_before"] = len(before)
body = png(); sha = hashlib.sha256(body).hexdigest()
r = requests.post(O + "/services/documentos/api/v1/documents", headers=h(tok), timeout=20, json={
    "subject_kind": "DONOR", "subject_id": donor, "category": "CONSENT", "mime_type": "image/png",
    "size": len(body), "sha256": sha, "policy_reference": "PRUEBA SINTETICA GCS 18/11/2026"})
out["prepare"] = r.status_code
d = r.json().get("data") or {}; out["prepare_error"] = (r.json().get("error") or {}).get("code")
fid = d.get("id"); out["file_id"] = fid
up = d.get("upload_url", ""); out["upload_host"] = urlsplit(up).hostname
r = requests.put(up, data=body, headers=d.get("upload_headers", {}), timeout=30); out["put"] = r.status_code
r = requests.put(up, data=body, headers=d.get("upload_headers", {}), timeout=30); out["put_repeat"] = r.status_code
state = None
for i in range(30):
    r = requests.post(O + f"/services/documentos/api/v1/files/{fid}/verify", headers=h(tok), timeout=30)
    state = (r.status_code, (r.json().get("data") or {}).get("status"), (r.json().get("error") or {}).get("code"))
    if r.status_code == 200 and state[1] == "VERIFIED": break
    time.sleep(4)
out["verify"] = state
r = requests.get(O + f"/services/documentos/api/v1/files/{fid}/download", headers=h(tok), timeout=20); out["download_api"] = r.status_code
dl = (r.json().get("data") or {}).get("download_url", "")
out["download_host"] = urlsplit(dl).hostname
g = requests.get(dl, timeout=30); out["download"] = g.status_code; out["same_sha256"] = hashlib.sha256(g.content).hexdigest() == sha
s = urlsplit(dl); out["anonymous_no_signature"] = requests.get(f"{s.scheme}://{s.netloc}{s.path}", timeout=20).status_code
# Documento LOCAL anterior del mismo donante: sigue descargando por el origen del portal.
local = None
for item in before:
    rr = requests.get(O + f"/services/documentos/api/v1/files/{item['id']}/download", headers=h(tok), timeout=20)
    if rr.status_code == 200:
        u = rr.json()["data"]["download_url"]; host = urlsplit(u).hostname
        if host != "storage.googleapis.com":
            gg = requests.get(u, timeout=30); local = {"host": host, "status": gg.status_code, "bytes": len(gg.content)}; break
out["previous_local_download"] = local
r = requests.post(O + "/services/identidad-acceso/api/v1/auth/logout", headers=h(tok), timeout=20); out["logout"] = r.status_code
print(json.dumps(out, ensure_ascii=False))
