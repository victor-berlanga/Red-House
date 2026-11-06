"""Puente GPS normalizado/NMEA y simulador. Nunca accede a bases del servidor."""

import argparse
import json
import math
import os
from pathlib import Path
import random
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from cryptography.fernet import Fernet
import websocket

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ms_transporte.tracking_contracts import Message, Event, Position, encode, decode

ROUTES = {
    "metro": [
        (25.6866, -100.3161),
        (25.6910, -100.3000),
        (25.7050, -100.2550),
        (25.7460, -100.1850),
    ],
    "regional": [
        (25.6866, -100.3161),
        (25.4160, -100.1510),
        (25.1880, -99.8240),
        (24.8600, -99.5670),
    ],
}


def nmea_rmc(line):
    """Adaptador RMC con checksum y fecha UTC. GGA/otros requieren política de fecha propia."""
    body, check = line.strip().split("*")
    if not body.startswith("$"):
        raise ValueError("NMEA sin inicio")
    checksum = 0
    for char in body[1:]:
        checksum ^= ord(char)
    if checksum != int(check, 16):
        raise ValueError("Checksum NMEA inválido")
    fields = body[1:].split(",")
    if not fields[0].endswith("RMC") or len(fields) < 10:
        raise ValueError("Se requiere sentencia RMC")
    captured = datetime.strptime(
        fields[9] + fields[1].split(".")[0], "%d%m%y%H%M%S"
    ).replace(tzinfo=timezone.utc)
    if fields[2] != "A":
        return {"captured_at": captured.isoformat(), "fix_valid": False}

    def coordinate(value, hemisphere, valid):
        if hemisphere not in valid:
            raise ValueError("Hemisferio inválido")
        amount = float(value)
        degrees = int(amount // 100)
        minutes = amount - degrees * 100
        if not math.isfinite(amount) or not 0 <= minutes < 60:
            raise ValueError("Coordenada NMEA inválida")
        return (degrees + minutes / 60) * (-1 if hemisphere in ("S", "W") else 1)

    result = {
        "captured_at": captured.isoformat(),
        "fix_valid": True,
        "latitude": coordinate(fields[3], fields[4], ("N", "S")),
        "longitude": coordinate(fields[5], fields[6], ("E", "W")),
    }
    if fields[7]:
        result["speed_m_s"] = float(fields[7]) * 1852 / 3600
    if fields[8]:
        result["heading_deg"] = float(fields[8])
    return result


class Spool:
    """Cola cifrada; ID/cuerpo estables ante respuesta perdida o reinicio."""

    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        key_path = path.with_suffix(".key")
        if not key_path.exists():
            fd = os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as output:
                output.write(Fernet.generate_key())
        self.cipher = Fernet(key_path.read_bytes())
        fd = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(fd)
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS pending(id INTEGER PRIMARY KEY AUTOINCREMENT, body BLOB NOT NULL)"
        )

    def add(self, value):
        if self.db.execute("SELECT count(*) FROM pending").fetchone()[0] >= 1000:
            raise RuntimeError("Cola llena; conserva y sincroniza los pendientes")
        with self.db:
            self.db.execute(
                "INSERT INTO pending(body) VALUES(?)",
                (self.cipher.encrypt(json.dumps(value).encode()),),
            )

    def first(self):
        row = self.db.execute(
            "SELECT id,body FROM pending ORDER BY id LIMIT 1"
        ).fetchone()
        return (row[0], json.loads(self.cipher.decrypt(row[1]))) if row else None

    def ack(self, identifier):
        with self.db:
            self.db.execute("DELETE FROM pending WHERE id=?", (identifier,))


def flush(spool, config, fmt, *, reconnect=False, retries=6):
    attempt, ws = 0, None
    try:
        while (row := spool.first()) is not None:
            try:
                if ws is None:
                    options = (
                        {"ca_certs": config["ca_file"]} if config.get("ca_file") else {}
                    )
                    ws = websocket.create_connection(
                        config["url"].rstrip("/") + "/" + fmt,
                        timeout=10,
                        suppress_origin=True,
                        subprotocols=["redhouse.tracking.v1." + fmt],
                        sslopt=options,
                    )
                    ws.send(
                        encode(
                            {
                                "type": "authenticate",
                                "credential_kind": "device",
                                "credential": config["credential"],
                            },
                            fmt,
                            Message,
                        )
                    )
                    event = decode(ws.recv(), Event, fmt)
                    if event["type"] != "authenticated":
                        raise RuntimeError("Autenticación rechazada; cola conservada")
                ws.send(
                    encode(
                        {"type": "position.publish", "position": row[1]}, fmt, Message
                    )
                )
                event = decode(ws.recv(), Event, fmt)
                if (
                    event["type"] != "position.ack"
                    or event["event_id"] != row[1]["event_id"]
                    or event["state"] != "PERSISTED_SQL"
                ):
                    raise RuntimeError(
                        "Publicación rechazada; revisar asignación/contrato. Cola conservada"
                    )
                spool.ack(row[0])
                print(
                    json.dumps(
                        {
                            "event_id": event["event_id"],
                            "cursor": event["cursor"],
                            "state": event["state"],
                        }
                    )
                )
                attempt = 0
                if reconnect:
                    ws.close()
                    ws = None
            except (OSError, websocket.WebSocketException):
                if ws:
                    ws.close()
                ws = None
                attempt += 1
                if attempt > retries:
                    raise RuntimeError(
                        "WSS inaccesible; pendientes cifrados conservados"
                    ) from None
                time.sleep(min(30, 2**attempt) * random.uniform(0.5, 1.0))
    finally:
        if ws:
            ws.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="JSON privado: url, credential, shipment_id, device_id, ca_file opcional",
    )
    parser.add_argument("--spool", type=Path, required=True)
    parser.add_argument(
        "--input", type=Path, help="Líneas normalizadas JSON o NMEA RMC"
    )
    parser.add_argument("--adapter", choices=("json", "nmea-rmc"), default="json")
    parser.add_argument("--simulate", choices=tuple(ROUTES))
    parser.add_argument("--format", choices=("json", "xml"), default="json")
    parser.add_argument(
        "--scenario",
        choices=(
            "normal",
            "no-fix",
            "delay",
            "duplicate",
            "disorder",
            "reconnect",
            "offline",
        ),
        default="normal",
    )
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--sequence-start",
        type=int,
        default=None,
        help="Secuencia persistente del origen; por defecto tiempo Unix en microsegundos",
    )
    args = parser.parse_args()
    if args.interval < 0.1 or not 1 <= args.count <= 1000:
        parser.error("Intervalo >=0.1 segundos; entre 1 y 1000 eventos")
    config = json.loads(args.config.read_text())
    if not config["url"].startswith("wss://"):
        parser.error("Se requiere WSS con certificado verificable")
    spool = Spool(args.spool)
    rng = random.Random(args.seed)
    lines = iter(args.input.read_text().splitlines()) if args.input else iter(sys.stdin)
    start = (
        args.sequence_start
        if args.sequence_start is not None
        else time.time_ns() // 1000
    )
    if args.scenario != "offline":
        flush(spool, config, args.format)
    try:
        for index in range(args.count):
            if args.simulate:
                route = ROUTES[args.simulate]
                progress = index / max(1, args.count - 1) * (len(route) - 1)
                segment = min(int(progress), len(route) - 2)
                ratio = progress - segment
                latitude, longitude = (
                    route[segment][axis] * (1 - ratio)
                    + route[segment + 1][axis] * ratio
                    for axis in (0, 1)
                )
                point = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "accuracy_m": rng.uniform(5, 10),
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "fix_valid": True,
                }
            else:
                try:
                    line = next(lines)
                except StopIteration:
                    break
                point = json.loads(line) if args.adapter == "json" else nmea_rmc(line)
            if args.scenario == "no-fix" and index % 3 == 1:
                point.update(fix_valid=False, latitude=None, longitude=None)
            if args.scenario == "delay" or (args.scenario == "disorder" and index % 2):
                point["captured_at"] = (
                    datetime.now(timezone.utc) - timedelta(minutes=2)
                ).isoformat()
            point.update(
                event_id=str(uuid4()),
                sequence=start + index,
                shipment_id=config["shipment_id"],
                device_id=config["device_id"],
                source="SIMULATOR" if args.simulate else "GPS_BRIDGE",
            )
            value = Position.model_validate(point).model_dump()
            spool.add(value)
            if args.scenario == "duplicate":
                spool.add(value)
            if args.scenario != "offline":
                flush(
                    spool, config, args.format, reconnect=args.scenario == "reconnect"
                )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Detenido; pendientes cifrados conservados.")
    finally:
        spool.db.close()


if __name__ == "__main__":
    main()
