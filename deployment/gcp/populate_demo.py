"""Carga ficticia aditiva en la VM existente; escrituras de negocio por HTTP.

Requiere respaldo previo y autorización explícita mediante --apply. Conserva
un checkpoint privado con claves de idempotencia para reanudar sin duplicar.
No instala dependencias, cambia permisos, reinicia servicios ni carga tablas
históricas ajenas a las operaciones actuales.
"""

import argparse
import fcntl
import hashlib
import http.client
import json
import os
import struct
import subprocess
import time
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path("/opt/redhouse")
SERVICES = (
    "identidad_acceso",
    "donantes",
    "receptores",
    "inventario",
    "compatibilidad",
    "priorizacion_geografia",
    "transporte",
    "custodia",
    "alertas",
    "auditoria",
    "monitoreo",
)
REASON = "Revisión de la información registrada para coordinación regional."
CONFIRM = {"human_confirmation": True, "reason": REASON}
NAMES = (
    "Ana Sofía",
    "José Luis",
    "María Fernanda",
    "Luis Fernando",
    "Valeria",
    "Carlos Eduardo",
    "Daniela",
    "Miguel Ángel",
    "Andrea",
    "Jorge Alejandro",
    "Natalia",
    "Roberto",
    "Lucía",
    "Diego",
    "Paola",
    "Santiago",
    "Gabriela",
    "Emilio",
    "Mariana",
    "Eduardo",
    "Camila",
    "Andrés",
    "Renata",
    "Javier",
    "Elena",
    "Mateo",
    "Isabel",
    "Tomás",
    "Sofía",
    "Daniel",
)
SURNAMES = ("Garza", "Treviño", "Salinas", "González", "Villarreal", "Martínez")
GROUPS = ("O-", "O+", "A+", "B+", "AB+", "A-", "B-", "AB-")
ORGANS = ("KIDNEY", "LIVER", "HEART")


def write_private(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    temporary.chmod(0o600)
    temporary.replace(path)


def progress(stage, **fields):
    print(json.dumps({"stage": stage, **fields}, ensure_ascii=False), flush=True)


def sql(query):
    if not query.lstrip().startswith("SELECT"):
        raise ValueError("Solo se permiten consultas de comprobación.")
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(ROOT / "compose.yaml"),
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "rh_bootstrap",
            "-d",
            "red_house",
            "-qAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            query,
        ],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            "Falló consulta de comprobación; no se exponen credenciales."
        )
    return json.loads(result.stdout)


class Demo:
    def __init__(self, directory):
        self.directory = directory.resolve()
        if self.directory != ROOT / ".local/compose":
            raise ValueError(
                "Este incremento está acotado al despliegue GCP existente."
            )
        self.work = self.directory / "demo-20261021"
        self.checkpoint_path = self.work / "checkpoint.json"
        if not (self.work / "backup-before/manifest.json").is_file():
            raise ValueError("Falta el respaldo previo; no se inicia la carga.")
        self.state = json.loads((self.directory / "state.json").read_text())
        self.cp = (
            json.loads(self.checkpoint_path.read_text())
            if self.checkpoint_path.exists()
            else {
                "started_at": datetime.now(timezone.utc).isoformat(),
                "operations": {},
                "phase": "prepared",
            }
        )
        self.base_time = datetime.fromisoformat(self.cp["started_at"])
        self.tokens, self.connections, self.last_calls = {}, {}, {}
        self.tenants = self.state["tenants"][:2]
        if len(self.tenants) != 2:
            raise ValueError("Se requieren las dos instituciones de demostración.")
        self.people, self.resources, self.requests, self.locations = {}, {}, {}, {}
        self.shipments = []

    def save(self):
        write_private(self.checkpoint_path, self.cp)

    def at(self, *, days=0, hours=0, minutes=0):
        return (
            self.base_time + timedelta(days=days, hours=hours, minutes=minutes)
        ).isoformat()

    def raw(self, service, method, path, payload=None, headers=None):
        if service not in self.connections:
            self.connections[service] = http.client.HTTPConnection(
                "127.0.0.1", 6101 + SERVICES.index(service), timeout=30
            )
        conn = self.connections[service]
        hdr = {"Accept": "application/json", **(headers or {})}
        body = None
        if payload is not None:
            body = json.dumps(payload).encode()
            hdr["Content-Type"] = "application/json"
        try:
            conn.request(method, path, body=body, headers=hdr)
            response = conn.getresponse()
            content = response.read()
            return response.status, json.loads(content), dict(response.getheaders())
        except (OSError, http.client.HTTPException, ValueError) as exc:
            conn.close()
            self.connections.pop(service, None)
            raise RuntimeError(
                f"Respuesta HTTP inaccesible: {service} ({type(exc).__name__})"
            ) from None

    def token(self, user, force=False):
        token = self.tokens.get(user)
        if token and not force and token["until"] > time.time() + 45:
            return token["access"]
        for attempt in range(5):
            token = self.tokens.get(user)
            payload = (
                {"refresh_token": token["refresh"]}
                if token
                else {"username": user, "password": self.state["password"]}
            )
            path = "/api/v1/auth/refresh" if token else "/api/v1/auth/login"
            try:
                status, response, headers = self.raw(
                    "identidad_acceso", "POST", path, payload
                )
            except RuntimeError:
                # A lost refresh response may already have rotated the token.
                # Authenticate anew rather than replaying an ambiguous refresh.
                self.tokens.pop(user, None)
                if attempt == 4:
                    raise
                time.sleep(2)
                continue
            if status == 200:
                value = response["data"]
                self.tokens[user] = {
                    "access": value["access_token"],
                    "refresh": value["refresh_token"],
                    "until": time.time() + value["expires_in"],
                }
                return self.tokens[user]["access"]
            if token and status in (400, 401):
                self.tokens.pop(user, None)
                continue
            if status in (429, 502, 503, 504) and attempt < 4:
                self.tokens.pop(user, None)
                time.sleep(min(60, int(headers.get("Retry-After", "5"))))
                continue
            raise RuntimeError("No se pudo autenticar " + user + ": " + str(status))
        raise RuntimeError("Se agotaron los reintentos de autenticación.")

    def request(self, service, method, path, user, payload=None, key=None):
        for attempt in range(5):
            bucket = (service, user)
            wait = 0.36 - (time.monotonic() - self.last_calls.get(bucket, 0))
            if wait > 0:
                time.sleep(wait)
            headers = {
                "Authorization": "Bearer " + self.token(user),
                "X-Correlation-ID": str(uuid4()),
            }
            if key:
                headers["Idempotency-Key"] = key
            self.last_calls[bucket] = time.monotonic()
            try:
                status, response, response_headers = self.raw(
                    service, method, path, payload, headers
                )
            except RuntimeError:
                if attempt == 4:
                    raise
                time.sleep(2)
                continue
            if status in (200, 201, 202):
                return response["data"]
            if status == 401 and attempt == 0:
                self.token(user, force=True)
                continue
            if status in (429, 502, 503, 504) and attempt < 4:
                delay = (
                    5
                    if status != 429
                    else min(60, int(response_headers.get("Retry-After", "60")))
                )
                progress("retry", service=service, status=status, seconds=delay)
                time.sleep(delay)
                continue
            code = response.get("error", {}).get("code", "unknown")
            raise RuntimeError(f"{service} {method} {path}: HTTP {status} ({code})")
        raise RuntimeError("Se agotaron los reintentos.")

    def once(self, tag, service, method, path, user, payload=None, fresh=False):
        previous = self.cp["operations"].get(tag)
        if previous and "result" in previous and not fresh:
            return previous["result"]
        if previous is None:
            stored = dict(payload) if payload is not None else None
            if stored is not None and "password" in stored:
                stored["password"] = "__PRIVATE_DEMO_PASSWORD__"
            previous = {
                "key": hashlib.sha256(("gcp-demo-30-v1:" + tag).encode()).hexdigest(),
                "payload": stored,
                "service": service,
                "path": path,
                "method": method,
                "user": user,
            }
            self.cp["operations"][tag] = previous
            self.save()
        data = previous["payload"]
        if data is not None:
            data = dict(data)
            if data.get("password") == "__PRIVATE_DEMO_PASSWORD__":
                data["password"] = self.state["password"]
        result = self.request(service, method, path, user, data, previous["key"])
        previous["result"] = {
            k: v for k, v in result.items() if k not in ("upload_url", "download_url")
        }
        self.save()
        return result

    def phase(self, name):
        self.cp["phase"] = name
        self.save()
        progress(
            name,
            completed_operations=sum(
                "result" in x for x in self.cp["operations"].values()
            ),
        )

    def foundations(self):
        self.phase("institutions_and_accounts")
        institutions = list(self.tenants)
        for n in range(3, 31):
            row = self.once(
                f"institution/{n}",
                "identidad_acceso",
                "POST",
                "/api/v1/institutions",
                "admin1",
                {"name": f"Institución Nuevo León {n:02d}"},
            )
            institutions.append(row["id"])
        for i, tenant in enumerate(self.tenants, 1):
            for n in range(1, 9):
                self.once(
                    f"user/{i}/{n}",
                    "identidad_acceso",
                    "POST",
                    "/api/v1/users",
                    f"admin{i}",
                    {
                        "username": f"donor_{i}_{n:02d}",
                        "password": self.state["password"],
                        "tenant_id": tenant,
                        "role": "DONOR",
                    },
                )
        routes = self.request(
            "priorizacion_geografia",
            "GET",
            "/api/v1/routes?page_size=100",
            "coordinator1",
        )["items"]
        pairs = {(r["origin_id"], r["destination_id"]) for r in routes}
        wanted = [(self.tenants[0], x) for x in institutions]
        wanted += [(self.tenants[1], x) for x in self.tenants]
        for n, (origin, destination) in enumerate(wanted):
            if (origin, destination) in pairs:
                continue
            self.once(
                f"route/{origin}/{destination}",
                "priorizacion_geografia",
                "POST",
                "/api/v1/routes",
                "coordinator1",
                {
                    "origin_id": origin,
                    "destination_id": destination,
                    "distance_km": 0.0 if origin == destination else float(5 + n % 35),
                    "travel_minutes": 5 if origin == destination else 15 + n % 30,
                    "source": "Estimación de referencia; no representa tráfico en tiempo real.",
                },
            )

    def catalogues(self):
        self.phase("catalogues")
        for i in (1, 2):
            self.locations[i] = []
            for n in range(30):
                prefix = f"catalogue/{i}/{n}"

                def create(kind, data, prefix=prefix, admin=f"admin{i}"):
                    return self.once(
                        prefix + "/" + kind,
                        "identidad_acceso",
                        "POST",
                        "/api/v1/catalogues/" + kind,
                        admin,
                        data,
                    )

                site = create(
                    "sites",
                    {
                        "name": f"Sede H{i} {n + 1:02d}",
                        "municipality": ("Monterrey", "Guadalupe", "Apodaca")[n % 3],
                        "address": f"Sede H{i}, referencia de ubicación {n + 1}",
                    },
                )
                create(
                    "contacts",
                    {
                        "name": f"Contacto H{i} {n + 1:02d}",
                        "value": f"contacto-h{i}-{n + 1:02d}@red-house.example",
                    },
                )
                create(
                    "schedules",
                    {
                        "name": f"Horario H{i} {n + 1:02d}",
                        "parent_id": site["id"],
                        "weekday": n % 7,
                        "opens_at": "08:00",
                        "closes_at": "16:00",
                    },
                )
                create(
                    "capacities",
                    {
                        "name": f"Capacidad H{i} {n + 1:02d}",
                        "parent_id": site["id"],
                        "component": "RBC",
                        "quantity": 20 + n,
                    },
                )
                location = create(
                    "locations",
                    {
                        "name": f"Ubicación H{i} {n + 1:02d}",
                        "parent_id": site["id"],
                        "description": "Ubicación interna de almacenamiento.",
                    },
                )
                self.locations[i].append(location["id"])
                if (n + 1) % 10 == 0:
                    progress("catalogues", institution=i, complete_sets=n + 1)

    def persons(self):
        self.phase("donors_campaigns_appointments")
        for i in (1, 2):
            donors, campaigns = [], []
            for n in range(34):
                user = (
                    f"donor{i}"
                    if n == 0
                    else f"donor_{i}_{n:02d}"
                    if n <= 8
                    else f"operator{i}"
                )
                row = self.once(
                    f"donor/{i}/{n}",
                    "donantes",
                    "POST",
                    "/api/v1/donors",
                    user,
                    {
                        "folio": f"RH26-D-H{i}-{n + 1:03d}",
                        "display_name": f"{NAMES[n % 30]} {SURNAMES[(n + i) % 6]}",
                        "blood_group": GROUPS[n % 8],
                        "consent": True,
                        "background": "Expediente de donante registrado.",
                        "donation_kind": "VOLUNTARY",
                        "consent_reference": f"CONSENT-H{i}-{n + 1:03d}",
                        "consent_at": self.at(minutes=-5),
                    },
                )
                if n < 32:
                    self.once(
                        f"donor-review/{i}/{n}",
                        "donantes",
                        "POST",
                        f"/api/v1/donors/{row['id']}/reviews",
                        f"medical{i}",
                        {
                            **CONFIRM,
                            "version": row["version"],
                            "decision": "ELIGIBLE" if n < 30 else "DEFERRED",
                        },
                    )
                donors.append(row)
            for n in range(30):
                campaign = self.once(
                    f"campaign/{i}/{n}",
                    "donantes",
                    "POST",
                    "/api/v1/campaigns",
                    f"operator{i}",
                    {
                        "title": f"Campaña H{i} {n + 1:02d} · Jornada solidaria",
                        "starts_at": self.at(days=n % 15 + 1),
                        "ends_at": self.at(days=n % 15 + 31),
                        "capacity": 50 + n,
                    },
                )
                campaigns.append(campaign)
                self.once(
                    f"appointment/{i}/{n}",
                    "donantes",
                    "POST",
                    "/api/v1/appointments",
                    f"operator{i}",
                    {"donor_id": donors[n]["id"], "campaign_id": campaign["id"]},
                )
                if n:
                    self.once(
                        f"own-appointment/{i}/{n}",
                        "donantes",
                        "POST",
                        "/api/v1/appointments",
                        f"donor{i}",
                        {"donor_id": donors[0]["id"], "campaign_id": campaign["id"]},
                    )
            self.people[i] = donors
            progress(
                "people",
                institution=i,
                donors=len(donors),
                campaigns=len(campaigns),
                appointments=59,
            )

    def inventory_and_requests(self):
        self.phase("donations_inventory_requests")
        for i in (1, 2):
            for kind in ("BLOOD", "ORGAN"):
                units, requests = [], []
                for n in range(30):
                    component = "RBC" if kind == "BLOOD" else ORGANS[n % 3]
                    group = (
                        self.people[i][n]["blood_group"] if kind == "BLOOD" else "O+"
                    )
                    donation_id = None
                    if kind == "BLOOD":
                        donation = self.once(
                            f"donation/{i}/{n}",
                            "donantes",
                            "POST",
                            "/api/v1/donations",
                            f"medical{i}",
                            {
                                **CONFIRM,
                                "donor_id": self.people[i][n]["id"],
                                "kind": kind,
                                "component": component,
                                "collected_at": self.at(minutes=-2),
                            },
                        )
                        self.once(
                            f"process-donation/{i}/{n}",
                            "donantes",
                            "POST",
                            f"/api/v1/donations/{donation['id']}/steps",
                            f"operator{i}",
                            {
                                **CONFIRM,
                                "state": "PROCESSED",
                                "version": donation["version"],
                            },
                        )
                        donation_id = donation["id"]
                    unit = self.once(
                        f"resource/{i}/{kind}/{n}",
                        "inventario",
                        "POST",
                        "/api/v1/resources",
                        f"operator{i}",
                        {
                            "folio": f"RH26-{'SAN' if kind == 'BLOOD' else 'ORG'}-H{i}-{n + 1:03d}",
                            "kind": kind,
                            "component": component,
                            "blood_group": group,
                            "expires_at": self.at(days=7 + n % 7)
                            if kind == "BLOOD"
                            else self.at(hours=72 + n % 12),
                            "collected_at": self.at(minutes=-2),
                            "donation_id": donation_id,
                            "location_id": self.locations[i][n],
                        },
                    )
                    unit = self.once(
                        f"release/{i}/{kind}/{n}",
                        "inventario",
                        "POST",
                        f"/api/v1/resources/{unit['id']}/release",
                        f"medical{i}",
                        {**CONFIRM, "version": unit["version"]},
                    )
                    units.append(unit)
                    person = self.once(
                        f"recipient/{i}/{kind}/{n}",
                        "receptores",
                        "POST",
                        "/api/v1/recipients",
                        f"medical{i}",
                        {
                            "folio": f"RH26-REC-{kind[0]}-H{i}-{n + 1:03d}",
                            "display_name": f"{NAMES[(n + 7) % 30]} {SURNAMES[(n + 2) % 6]}",
                            "kind": kind,
                            "blood_group": "AB+" if kind == "BLOOD" else "O+",
                            "organ_type": component if kind == "ORGAN" else None,
                            "studies": "Revisión clínica externa pendiente; sin interpretación HLA.",
                            "requirement": "Solicitud de recurso para coordinación entre instituciones.",
                        },
                    )
                    req = self.once(
                        f"request/{i}/{kind}/{n}",
                        "receptores",
                        "POST",
                        "/api/v1/requests",
                        f"medical{i}",
                        {
                            "recipient_id": person["id"],
                            "component": component,
                            "quantity": 1,
                            "urgency": n % 3 + 1,
                        },
                    )
                    requests.append(req)
                    if (n + 1) % 10 == 0:
                        progress(
                            "inventory_and_requests",
                            institution=i,
                            kind=kind,
                            records_each=n + 1,
                        )
                self.resources[i, kind], self.requests[i, kind] = units, requests

    def wait_shipment(self, identifier, user):
        for _ in range(45):
            row = self.request(
                "transporte", "GET", "/api/v1/shipments/" + identifier, user
            )
            if not row["inventory_pending"]:
                return row
            time.sleep(2)
        raise RuntimeError(
            "Traslado pendiente de sincronizar inventario: " + identifier
        )

    def evidence(self, case, shipment, user):
        tag = f"file-verify/{case}"
        cached = self.cp["operations"].get(tag, {}).get("result")
        if cached:
            return cached

        # Small synthetic binary fixture; no personal information or clinical image.
        def chunk(kind, data):
            return (
                struct.pack(">I", len(data))
                + kind
                + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            )

        content = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\x00" + b"\xc8\x20\x30" * 4) * 4))
            + chunk(b"IEND", b"")
        )
        prepared = self.once(
            f"file/{case}",
            "transporte",
            "POST",
            f"/api/v1/shipments/{shipment['id']}/files",
            user,
            {
                "mime_type": "image/png",
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            },
            fresh=True,
        )
        upload = Request(
            prepared["upload_url"],
            data=content,
            method="PUT",
            headers=prepared["upload_headers"],
        )
        try:
            with urlopen(upload, timeout=30) as response:
                response.read()
        except HTTPError as exc:
            if exc.code != 412:
                raise RuntimeError("Carga GCS rechazada: " + str(exc.code)) from None
        except OSError:
            raise RuntimeError(
                "Carga GCS inaccesible; se conserva el pendiente."
            ) from None
        return self.once(
            tag,
            "transporte",
            "POST",
            f"/api/v1/files/{prepared['file']['id']}/verify",
            user,
            {},
        )

    def logistics(self):
        self.phase("evaluations_reservations_shipments")
        used = {}
        for case in range(30):
            origin = 1 + case % 2
            destination = 3 - origin
            kind = "BLOOD" if case % 4 < 2 else "ORGAN"
            start = used.get((origin, kind), 0)
            used[origin, kind] = start + 2
            medical = f"medical{destination}"
            evaluations = []
            for offset in (0, 1):
                index = start + offset
                unit = self.resources[origin, kind][index]
                req = self.requests[destination, kind][index]
                evaluation = self.once(
                    f"evaluation/{case}/{offset}",
                    "compatibilidad",
                    "POST",
                    "/api/v1/evaluations",
                    medical,
                    {"request_id": req["id"]},
                )
                if not any(
                    c["resource_id"] == unit["id"] for c in evaluation["candidates"]
                ):
                    raise RuntimeError(
                        "El recurso ficticio no es candidato: " + unit["id"]
                    )
                self.once(
                    f"review/{case}/{offset}",
                    "compatibilidad",
                    "POST",
                    f"/api/v1/evaluations/{evaluation['id']}/reviews",
                    medical,
                    {**CONFIRM, "resource_id": unit["id"], "decision": "FAVORABLE"},
                )
                self.once(
                    f"ranking/{case}/{offset}",
                    "priorizacion_geografia",
                    "POST",
                    "/api/v1/rankings",
                    medical,
                    {"evaluation_id": evaluation["id"]},
                )
                evaluations.append(evaluation)
            self.once(
                f"proposal/{case}",
                "priorizacion_geografia",
                "POST",
                "/api/v1/allocation-proposals",
                medical,
                {"evaluation_ids": [e["id"] for e in evaluations]},
            )
            unit = self.resources[origin, kind][start]
            allocation = self.once(
                f"reservation/{case}",
                "inventario",
                "POST",
                "/api/v1/reservations",
                medical,
                {
                    **CONFIRM,
                    "evaluation_id": evaluations[0]["id"],
                    "resource_id": unit["id"],
                },
            )
            if allocation["status"] != "COMPLETED":
                allocation = self.request(
                    "inventario",
                    "POST",
                    f"/api/v1/operations/{allocation['operation_id']}/resume",
                    medical,
                    {},
                    hashlib.sha256(f"resume-demo-{case}".encode()).hexdigest(),
                )
            if allocation["status"] != "COMPLETED":
                raise RuntimeError("Reserva pendiente; no se duplica: " + str(case))
            now = datetime.now(timezone.utc)
            shipment = self.once(
                f"shipment/{case}",
                "transporte",
                "POST",
                "/api/v1/shipments",
                f"coordinator{origin}",
                {
                    **CONFIRM,
                    "reservation_id": allocation["reservation"]["id"],
                    "transport_user_id": self.state["accounts"][f"transport{origin}"][
                        "id"
                    ],
                    "departure_at": (now + timedelta(minutes=2)).isoformat(),
                    "eta": (now + timedelta(minutes=90)).isoformat(),
                },
            )
            user = f"transport{origin}"
            current = self.wait_shipment(shipment["id"], user)
            file = self.evidence(case, current, f"operator{origin}")
            targets = (
                ["PREPARED", "COLLECTED", "IN_TRANSIT", "DELIVERED", "ACCEPTED"]
                if case < 10
                else ["PREPARED", "COLLECTED", "IN_TRANSIT"]
                if case < 20
                else ["PREPARED", "COLLECTED"]
                if case < 25
                else []
            )
            for target in targets:
                actor = (
                    f"operator{origin}"
                    if target == "PREPARED"
                    else f"operator{destination}"
                    if target == "ACCEPTED"
                    else user
                )
                payload = {**CONFIRM, "version": current["version"], "state": target}
                if target == "DELIVERED":
                    payload["evidence"] = {"object_id": file["id"]}
                if target == "ACCEPTED":
                    payload["destination_location_id"] = self.locations[destination][
                        case
                    ]
                current = self.once(
                    f"transition/{case}/{target}",
                    "transporte",
                    "POST",
                    f"/api/v1/shipments/{shipment['id']}/transitions",
                    actor,
                    payload,
                )
                if target == "COLLECTED":
                    for point in range(2):
                        self.once(
                            f"telemetry/{case}/{point}",
                            "transporte",
                            "POST",
                            f"/api/v1/shipments/{shipment['id']}/telemetry",
                            user,
                            {
                                "latitude": 25.60 + case * 0.001 + point * 0.0001,
                                "longitude": -100.30 + case * 0.001,
                                "captured_at": datetime.now(timezone.utc).isoformat(),
                            },
                        )
            self.shipments.append(
                {
                    "case": case,
                    "id": shipment["id"],
                    "kind": kind,
                    "origin": origin,
                    "destination": destination,
                    "status": current["status"],
                    "file_id": file["id"],
                }
            )
            self.cp["shipments"] = self.shipments
            self.save()
            progress(
                "shipment",
                number=case + 1,
                status=current["status"],
                kind=kind,
                file_verified=file["status"] == "VERIFIED",
            )

    def verify(self):
        self.phase("verify")
        expected = {
            "donor": 60,
            "donor_review": 60,
            "campaign": 60,
            "appointment": 60,
            "donation": 60,
            "donation_event": 60,
            "catalogue_entry": 300,
            "resource": 120,
            "resource_review": 120,
            "recipient": 120,
            "blood_request": 120,
            "candidate_evaluation": 60,
            "blood_review": 60,
            "ranking_run": 60,
            "balance_proposal": 30,
            "blood_allocation": 30,
            "allocation_operation": 30,
            "request_hold": 30,
            "shipment": 30,
            "custody_chain": 30,
            "custody_event": 30,
            "shipment_transition": 30,
            "transport_telemetry": 30,
            "stored_file": 30,
            "institution": 30,
            "regional_route": 30,
            "user_account": 30,
        }
        tables = sql(
            "SELECT json_agg(x) FROM (SELECT schemaname,tablename FROM pg_tables "
            "WHERE schemaname IN ('red_house','web_runtime') ORDER BY 1,2) x"
        )
        parts = []
        for table in tables:
            schema, name = table["schemaname"], table["tablename"]
            if not (
                schema.replace("_", "").isalnum() and name.replace("_", "").isalnum()
            ):
                raise ValueError("Nombre de tabla no admitido.")
            parts.append(
                f"SELECT '{schema}.{name}' AS name,count(*) AS rows "
                f'FROM "{schema}"."{name}"'
            )
        counts = sql("SELECT json_agg(t) FROM (" + " UNION ALL ".join(parts) + ") t")
        by_name = {r["name"]: r["rows"] for r in counts}
        for name, minimum in expected.items():
            if by_name["red_house." + name] < minimum:
                raise RuntimeError("Falta cantidad mínima: " + name)
        visible = {}
        for i in (1, 2):
            views = {}
            for key, service, endpoint, user in (
                ("donors", "donantes", "donors", f"operator{i}"),
                ("campaigns", "donantes", "campaigns", f"operator{i}"),
                ("appointments", "donantes", "appointments", f"operator{i}"),
                ("own_appointments", "donantes", "appointments", f"donor{i}"),
                ("donations", "donantes", "donations", f"operator{i}"),
                ("recipients", "receptores", "recipients", f"medical{i}"),
                ("requests", "receptores", "requests", f"medical{i}"),
                ("resources", "inventario", "resources", f"operator{i}"),
            ):
                value = self.request(
                    service, "GET", f"/api/v1/{endpoint}?page_size=1", user
                )
                views[key] = value["total"]
                if value["total"] < 30:
                    raise RuntimeError(f"Vista incompleta: {i} {key}")
            own = self.request(
                "donantes", "GET", "/api/v1/donors?page_size=1", f"donor{i}"
            )
            views["own_donor_profiles"] = own["total"]
            if own["total"] < 1:
                raise RuntimeError("Falta expediente del perfil donante.")
            visible[str(i)] = views
        report = {
            "date": datetime.now(timezone.utc).isoformat(),
            "result": "passed",
            "target": 30,
            "writes": "authenticated_business_http",
            "baseline": json.loads((self.work / "baseline.json").read_text())["counts"],
            "after": counts,
            "visible_by_institution": visible,
            "shipments": self.cp["shipments"],
            "completed_operations": sum(
                "result" in x for x in self.cp["operations"].values()
            ),
        }
        output = ROOT / "documentation/evidencias/gcp/datos-demo"
        output.mkdir(parents=True, exist_ok=True)
        (output / "counts.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        )
        self.cp["phase"] = "complete"
        self.save()
        progress(
            "complete",
            visible=visible,
            physical_tables_at_least_30=sum(r["rows"] >= 30 for r in counts),
        )

    def close(self):
        for user in list(self.tokens):
            try:
                self.request(
                    "identidad_acceso",
                    "POST",
                    "/api/v1/auth/logout",
                    user,
                    {},
                    uuid4().hex,
                )
            except RuntimeError:
                progress("session_cleanup_pending", user=user)
        for conn in self.connections.values():
            conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("--directory", type=Path, default=ROOT / ".local/compose")
    args = parser.parse_args()
    os.umask(0o077)
    demo = Demo(args.directory)
    with (demo.work / "populate.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Ya hay una carga en ejecución.") from None
        populate(demo)


def populate(demo):
    try:
        demo.foundations()
        demo.catalogues()
        demo.persons()
        demo.inventory_and_requests()
        demo.logistics()
        demo.verify()
    except Exception as exc:  # noqa: BLE001 - stop safely and preserve resumable state.
        demo.save()
        progress(
            "failed",
            error_type=type(exc).__name__,
            message=str(exc)
            if isinstance(exc, RuntimeError)
            else "Checkpoint conservado; revisar la etapa.",
        )
        raise SystemExit(1) from None
    finally:
        demo.close()


if __name__ == "__main__":
    main()
