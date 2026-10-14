"""Provisiona solo un entorno local nuevo. Los datos de negocio se crean por API con perfiles reales."""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import psycopg
import redis
import requests
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.local import private_file

CITIES = (
    "Monterrey",
    "San Nicolás de los Garza",
    "Guadalupe",
    "Apodaca",
    "General Escobedo",
    "Santa Catarina",
)
HOSPITALS = (
    "Hospital Regional Sierra Madre",
    "Centro Hospitalario Las Puentes",
    "Hospital Metropolitano La Silla",
    "Hospital Regional Huinalá",
    "Centro Hospitalario Anáhuac",
    "Hospital Regional La Huasteca",
)
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
)
LAST = (
    "Garza",
    "Treviño",
    "Salinas",
    "González",
    "Villarreal",
    "Hernández",
    "Martínez",
    "Rodríguez",
    "Cavazos",
    "García",
    "Elizondo",
    "Flores",
)
ROLES = ("ADMIN", "OPERATOR", "MEDICAL", "COORDINATOR", "TRANSPORT", "AUDITOR", "DONOR")
GROUPS = ("O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-")
REASON = "Registro ficticio para presentación académica; revisión humana representada por el perfil autorizado."


def write_private(path, value):
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    private_file(temporary, value)
    os.replace(temporary, path)


class RegionalDataset:
    def __init__(self, directory):
        self.directory = directory.resolve()
        self.state = json.loads((directory / "state.json").read_text())
        if Path(self.state["directory"]).resolve() != self.directory:
            raise RuntimeError("Directorio no coincide con entorno local propio.")
        self.tokens = {}
        migration = self.directory / "regional-load.json"
        self.summary = json.loads(migration.read_text()) if migration.exists() else {}

    def sql(self, service):
        return psycopg.connect(
            self.state["database_owners"][service],
            options="-c search_path=api,pg_catalog",
            row_factory=dict_row,
        )

    def provision(self):
        if (self.directory / "dataset-nl.json").exists():
            raise RuntimeError(
                "Esta carga ya terminó; no duplicar datos ni reinicializar."
            )
        with self.sql("inventario") as conn:
            if conn.execute("SELECT count(*) AS n FROM resources").fetchone()["n"]:
                raise RuntimeError(
                    "La carga requiere inventario vacío en un entorno exclusivo nuevo."
                )
        with self.sql("identidad_acceso") as conn:
            for i in range(6):
                if i < 2:
                    tenant = self.state["tenants"][i]
                    conn.execute(
                        "UPDATE institutions SET name=%s WHERE id=%s",
                        (HOSPITALS[i] + " · " + CITIES[i], tenant),
                    )
                else:
                    name = HOSPITALS[i] + " · " + CITIES[i]
                    existing = conn.execute(
                        "SELECT id FROM institutions WHERE name=%s AND region_id=%s",
                        (name, self.state["region_id"]),
                    ).fetchone()
                    tenant = str(existing["id"]) if existing else str(uuid4())
                    if i >= len(self.state["tenants"]):
                        self.state["tenants"].append(tenant)
                    conn.execute(
                        "INSERT INTO institutions(id,name,region_id) VALUES(%s,%s,%s) ON CONFLICT(id) DO NOTHING",
                        (tenant, name, self.state["region_id"]),
                    )
                    # Reutilizar el hash aleatorio de las cuentas, nunca copiar contraseña al repositorio.
                    password_hash = conn.execute(
                        "SELECT password_hash FROM users LIMIT 1"
                    ).fetchone()["password_hash"]
                    for role in ROLES:
                        username = role.lower() + str(i + 1)
                        user = str(uuid4())
                        conn.execute(
                            "INSERT INTO users(id,tenant_id,username,password_hash,role) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(username) DO NOTHING",
                            (user, tenant, username, password_hash, role),
                        )
                        user = str(
                            conn.execute(
                                "SELECT id FROM users WHERE username=%s", (username,)
                            ).fetchone()["id"]
                        )
                        self.state["accounts"][username] = {
                            "id": user,
                            "tenant_id": tenant,
                            "role": role,
                        }
        for service in self.state["urls"]:
            path = self.directory / (service + ".json")
            config = json.loads(path.read_text())
            config["RATE_LIMIT"] = (
                100000  # Solo provisionamiento; restore vuelve a 180 antes de publicar el corte.
            )
            write_private(path, json.dumps(config, indent=2))
        write_private(self.directory / "state.json", json.dumps(self.state, indent=2))
        write_private(
            self.directory / "regional-load.json",
            json.dumps(self.summary, indent=2),
        )
        write_private(
            self.directory / "web-client.json",
            json.dumps(
                {
                    "SERVICE_URLS": self.state["urls"],
                    "WEB_SESSION_STORE": str(self.directory / "web-sessions.sqlite3"),
                    "REGION_NAME": "Nuevo León",
                    "SERVICE_TIMEOUT": 8,
                },
                indent=2,
            ),
        )
        print(
            "Seis instituciones ficticias y cuentas provisionadas. La base anterior solo se consultó; no se modificó."
        )

    def call(self, service, method, path, user="medical1", data=None):
        if user not in self.tokens:
            login = requests.post(
                self.state["urls"]["identidad_acceso"] + "/api/v1/auth/login",
                json={"username": user, "password": self.state["password"]},
                timeout=20,
            )
            if login.status_code != 200:
                raise RuntimeError("No se pudo autenticar perfil durante la carga.")
            self.tokens[user] = login.json()["data"]["access_token"]
        response = requests.request(
            method,
            self.state["urls"][service] + path,
            json=data,
            headers={
                "Authorization": "Bearer " + self.tokens[user],
                "Accept": "application/json",
                "Idempotency-Key": uuid4().hex,
            },
            timeout=30,
        )
        if response.status_code >= 300:
            error = response.json().get("error", {})
            raise RuntimeError(
                f"Carga interrumpida: {service} {path} HTTP {response.status_code} ({error.get('code', 'unknown')})."
            )
        return response.json()["data"]

    def populate(self):
        recipients_by_tenant = []
        resource_count = donors_count = donations_count = appointments_count = 0
        for i, tenant in enumerate(self.state["tenants"]):
            op, medical = "operator" + str(i + 1), "medical" + str(i + 1)
            donors = []
            for n in range(18):
                name = (
                    NAMES[(n + i * 3) % len(NAMES)]
                    + " "
                    + LAST[(n + i) % len(LAST)]
                    + " "
                    + LAST[(n + 5 + i * 2) % len(LAST)]
                )
                donor = self.call(
                    "donantes",
                    "POST",
                    "/api/v1/donors",
                    op,
                    {
                        "folio": f"DON-NL-{i + 1:02d}-{n + 1:04d}",
                        "display_name": name,
                        "blood_group": GROUPS[n % 8],
                        "consent": True,
                    },
                )
                donors.append(donor)
                if n < 16:
                    self.call(
                        "donantes",
                        "POST",
                        "/api/v1/donors/" + donor["id"] + "/reviews",
                        medical,
                        {
                            "decision": "ELIGIBLE" if n < 12 else "DEFERRED",
                            "version": 1,
                            "human_confirmation": True,
                            "reason": REASON,
                        },
                    )
                donors_count += 1
            for n in range(6):
                donation = self.call(
                    "donantes",
                    "POST",
                    "/api/v1/donations",
                    medical,
                    {
                        "donor_id": donors[n]["id"],
                        "kind": "BLOOD",
                        "component": "RBC",
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                        "reason": REASON,
                        "human_confirmation": True,
                    },
                )
                if n < 5:
                    donation = self.call(
                        "donantes",
                        "POST",
                        "/api/v1/donations/" + donation["id"] + "/steps",
                        op,
                        {
                            "state": "PROCESSED" if n < 4 else "REJECTED",
                            "version": 1,
                            "reason": REASON,
                            "human_confirmation": True,
                        },
                    )
                donations_count += 1
            campaigns = []
            for n in range(2):
                campaigns.append(
                    self.call(
                        "donantes",
                        "POST",
                        "/api/v1/campaigns",
                        op,
                        {
                            "title": f"Jornada solidaria {CITIES[i]} · "
                            + ("Octubre" if n == 0 else "Comunidad universitaria"),
                            "starts_at": (
                                datetime.now(timezone.utc) + timedelta(days=n)
                            ).isoformat(),
                            "ends_at": (
                                datetime.now(timezone.utc) + timedelta(days=n + 7)
                            ).isoformat(),
                            "capacity": 30 + n * 10,
                        },
                    )
                )
            for n in range(6):
                self.call(
                    "donantes",
                    "POST",
                    "/api/v1/appointments",
                    op,
                    {
                        "donor_id": donors[n]["id"],
                        "campaign_id": campaigns[n % 2]["id"],
                    },
                )
                appointments_count += 1
            for n in range(42):
                kind = "BLOOD" if n < 36 else "ORGAN"
                component = (
                    "RBC"
                    if kind == "BLOOD"
                    else ("KIDNEY", "LIVER", "HEART")[(n - 36) % 3]
                )
                resource = self.call(
                    "inventario",
                    "POST",
                    "/api/v1/resources",
                    op,
                    {
                        "folio": f"{'SAN' if kind == 'BLOOD' else 'ORG'}-NL-{i + 1:02d}-{n + 1:04d}",
                        "kind": kind,
                        "component": component,
                        "blood_group": GROUPS[n % 8] if kind == "BLOOD" else "O+",
                        "expires_at": (
                            datetime.now(timezone.utc)
                            + timedelta(
                                hours=(6 + n * 6)
                                if kind == "BLOOD"
                                else 24 + (n - 36) * 3
                            )
                        ).isoformat(),
                    },
                )
                if n % 9 != 8:
                    self.call(
                        "inventario",
                        "POST",
                        "/api/v1/resources/" + resource["id"] + "/release",
                        medical,
                        {"version": 1, "reason": REASON, "human_confirmation": True},
                    )
                resource_count += 1
            persons = []
            for n in range(12):
                kind = "BLOOD" if n < 9 else "ORGAN"
                organ = None if kind == "BLOOD" else ("KIDNEY", "LIVER", "HEART")[n - 9]
                name = (
                    NAMES[(n + i + 7) % len(NAMES)]
                    + " "
                    + LAST[(n + i + 3) % len(LAST)]
                    + " "
                    + LAST[(n + i + 8) % len(LAST)]
                )
                recipient = self.call(
                    "receptores",
                    "POST",
                    "/api/v1/recipients",
                    medical,
                    {
                        "folio": f"REC-NL-{i + 1:02d}-{n + 1:04d}",
                        "display_name": name,
                        "kind": kind,
                        "blood_group": "AB+" if kind == "BLOOD" else "O+",
                        "organ_type": organ,
                        "studies": "Expediente ficticio de "
                        + CITIES[i]
                        + ". Estudios documentales de presentación; HLA y pruebas cruzadas requieren revisión especializada, sin interpretación automática.",
                    },
                )
                req = self.call(
                    "receptores",
                    "POST",
                    "/api/v1/requests",
                    medical,
                    {
                        "recipient_id": recipient["id"],
                        "component": "RBC" if kind == "BLOOD" else organ,
                        "quantity": 1 if n % 3 == 0 or kind == "ORGAN" else n % 3 + 1,
                        "urgency": n % 3 + 1,
                    },
                )
                persons.append(req)
            recipients_by_tenant.append(persons)
            print("Datos ficticios creados para", CITIES[i])
        for i, origin in enumerate(self.state["tenants"]):
            for j, destination in enumerate(self.state["tenants"]):
                distance = 0.0 if i == j else round(7.5 + abs(i - j) * 4.3, 1)
                self.call(
                    "priorizacion_geografia",
                    "POST",
                    "/api/v1/routes",
                    "coordinator1",
                    {
                        "origin_id": origin,
                        "destination_id": destination,
                        "distance_km": distance,
                        "travel_minutes": 5 if i == j else 18 + abs(i - j) * 7,
                        "source": "Estimación operativa ficticia entre municipios de Nuevo León; no navegación ni tiempo de tráfico verificado.",
                    },
                )
        shipments = []
        for i, requests_by_person in enumerate(recipients_by_tenant):
            medical, coord = "medical" + str(i + 1), "coordinator" + str(i + 1)
            for n in (0, 3, 9):
                req = requests_by_person[n]
                evaluation = self.call(
                    "compatibilidad",
                    "POST",
                    "/api/v1/evaluations",
                    medical,
                    {"request_id": req["id"]},
                )
                candidate = next(
                    c
                    for c in evaluation["candidates"]
                    if c["origin_id"] != self.state["tenants"][i]
                )
                self.call(
                    "compatibilidad",
                    "POST",
                    "/api/v1/evaluations/" + evaluation["id"] + "/reviews",
                    medical,
                    {
                        "resource_id": candidate["resource_id"],
                        "decision": "FAVORABLE",
                        "reason": REASON,
                        "human_confirmation": True,
                    },
                )
                self.call(
                    "priorizacion_geografia",
                    "POST",
                    "/api/v1/rankings",
                    medical,
                    {"evaluation_id": evaluation["id"]},
                )
                result = self.call(
                    "inventario",
                    "POST",
                    "/api/v1/reservations",
                    medical,
                    {
                        "evaluation_id": evaluation["id"],
                        "resource_id": candidate["resource_id"],
                        "reason": REASON,
                        "human_confirmation": True,
                    },
                )
                if result["status"] != "COMPLETED":
                    raise RuntimeError(
                        "Reserva pendiente; consultar y resolver antes de continuar."
                    )
                origin = self.state["tenants"].index(candidate["origin_id"])
                transport = "transport" + str(origin + 1)
                row = self.call(
                    "transporte",
                    "POST",
                    "/api/v1/shipments",
                    coord,
                    {
                        "reservation_id": result["reservation"]["id"],
                        "transport_user_id": self.state["accounts"][transport]["id"],
                        "departure_at": datetime.now(timezone.utc).isoformat(),
                        "eta": (
                            datetime.now(timezone.utc)
                            + timedelta(minutes=candidate["travel_minutes"] + 15)
                        ).isoformat(),
                        "reason": REASON,
                        "human_confirmation": True,
                    },
                )
                states = [
                    (),
                    ("PREPARED",),
                    ("PREPARED", "COLLECTED", "IN_TRANSIT"),
                    ("PREPARED", "COLLECTED", "IN_TRANSIT", "DELIVERED"),
                    ("PREPARED", "COLLECTED", "IN_TRANSIT", "DELIVERED", "ACCEPTED"),
                    ("CANCELLED",),
                ][(i + (0 if n == 0 else 1 if n == 3 else 2)) % 6]
                for step in states:
                    user = (
                        "operator" + str(origin + 1)
                        if step == "PREPARED"
                        else "operator" + str(i + 1)
                        if step == "ACCEPTED"
                        else coord
                        if step == "CANCELLED"
                        else transport
                    )
                    row = self.call(
                        "transporte",
                        "POST",
                        "/api/v1/shipments/" + row["id"] + "/transitions",
                        user,
                        {
                            "state": step,
                            "version": row["version"],
                            "reason": REASON,
                            "human_confirmation": True,
                        },
                    )
                if row["status"] == "IN_TRANSIT":
                    self.call(
                        "transporte",
                        "POST",
                        "/api/v1/shipments/" + row["id"] + "/telemetry",
                        transport,
                        {
                            "latitude": 25.6866 + origin * 0.006,
                            "longitude": -100.3161 + origin * 0.006,
                            "captured_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                shipments.append(
                    {
                        "id": row["id"],
                        "status": row["status"],
                        "origin": CITIES[origin],
                        "destination": CITIES[i],
                    }
                )
        self.summary.update(
            institutions=6,
            donors=donors_count,
            donations=donations_count,
            appointments=appointments_count,
            campaigns=12,
            recipients=72,
            requests=72,
            resources=resource_count,
            blood_units=216,
            organ_offers=36,
            routes=36,
            shipments=shipments,
            notice="Todos los nombres, instituciones, estudios, fechas y límites son ficticios. Los municipios son de Nuevo León. No representa pacientes ni reglas clínicas reales.",
        )
        write_private(
            self.directory / "dataset-nl.json",
            json.dumps(self.summary, indent=2, ensure_ascii=False),
        )
        print(
            "Carga de presentación finalizada; resumen sin credenciales guardado en dataset-nl.json."
        )

    def restore(self):
        for service in self.state["urls"]:
            path = self.directory / (service + ".json")
            config = json.loads(path.read_text())
            config["RATE_LIMIT"] = 180
            write_private(path, json.dumps(config, indent=2))
        r = redis.Redis.from_url(self.state["redis_admin"])
        keys = list(r.scan_iter(match="*:limit:*"))
        if keys:
            r.delete(*keys)
        print(
            "Límite normal de 180 peticiones/minuto restaurado en configuraciones; reiniciar para aplicarlo."
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("provision", "populate", "restore"))
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    sample = RegionalDataset(args.directory)
    if args.action == "provision":
        sample.provision()
    elif args.action == "populate":
        sample.populate()
    else:
        sample.restore()


if __name__ == "__main__":
    main()
