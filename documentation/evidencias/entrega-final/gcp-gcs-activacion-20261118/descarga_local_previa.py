import json, os, hashlib
from urllib.parse import urlsplit
from uuid import uuid4
import requests
O = "https://34.18.186.116"; pw = os.environ.pop("RH_PW"); out = {}
H = lambda t=None: {"Accept": "application/json", "Idempotency-Key": uuid4().hex, **({"Authorization": "Bearer " + t} if t else {})}
r = requests.post(O + "/services/identidad-acceso/api/v1/auth/login", json={"username": "transport1", "password": pw}, headers=H(), timeout=20)
out["login"] = r.status_code; t = r.json()["data"]["access_token"]
for fid in ("22cf879e-10fb-48a1-a2bc-543198e6517b", "8fd76e97-9fc4-43d6-862f-5c5a972274cb"):
    r = requests.get(O + f"/services/documentos/api/v1/files/{fid}/download", headers=H(t), timeout=20)
    u = (r.json().get("data") or {}).get("download_url", "")
    g = requests.get(u, timeout=30) if u else None
    out[fid[:8]] = {"api": r.status_code, "host": urlsplit(u).hostname, "get": g.status_code if g is not None else None, "bytes": len(g.content) if g is not None else 0}
out["logout"] = requests.post(O + "/services/identidad-acceso/api/v1/auth/logout", headers=H(t), timeout=20).status_code
print(json.dumps(out))
