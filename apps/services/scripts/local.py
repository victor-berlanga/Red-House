"""Entorno local aislado y reproducible. Nunca abre/reinicia bases existentes."""

import argparse
import importlib
import json
import os
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg
import redis
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from pymongo import MongoClient

from redhouse.config import SERVICES
from scripts.dependencies import resolve_binary


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def private_file(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(value)


def pem(private):
    return (
        private.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        ).decode(),
        private.public_key()
        .public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        .decode(),
    )


def pid_matches(pid, directory):
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True
    )
    return str(directory) in result.stdout


def check_port(port, name):
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            raise RuntimeError(
                f"Puerto {port} de {name} ocupado por otro proceso; no se interviene."
            ) from None


def infrastructure_pid(state, name):
    """Identificar la instancia privada; Redis reescribe su título de proceso."""
    directory = Path(state["directory"])
    try:
        if name == "redis":
            info = redis.Redis.from_url(
                state["redis_admin"], socket_connect_timeout=1, socket_timeout=1
            ).info("server")
            if Path(info.get("config_file", "")).resolve() != directory / "redis.conf":
                raise RuntimeError(
                    "El puerto Redis pertenece a otra configuración; no se interviene."
                )
            return info["process_id"]
        if name == "postgres":
            pid = int((directory / "pg/postmaster.pid").read_text().splitlines()[0])
        else:
            with MongoClient(
                state["mongo_admin"],
                serverSelectionTimeoutMS=1000,
                socketTimeoutMS=1000,
            ) as client:
                pid = int(client.admin.command("serverStatus")["pid"])
        return pid if pid_matches(pid, directory) else None
    except (OSError, ValueError, redis.RedisError):
        return None
    except Exception as exc:
        from pymongo.errors import PyMongoError

        if isinstance(exc, PyMongoError):
            return None
        raise


class Environment:
    def __init__(self, directory, mongo_bin=None):
        self.directory = Path(directory).resolve()
        self.mongo_bin = mongo_bin
        self.processes = []
        self.configs = {}
        self.state = {}

    def launch(self, args, name):
        with open(self.directory / (name + ".log"), "ab") as log:
            process = subprocess.Popen(
                args,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=ROOT,
                start_new_session=True,
            )
        self.processes.append(process)
        return process

    def wait(self, fn, seconds=20):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            try:
                return fn()
            except Exception:
                if any(p.poll() is not None for p in self.processes):
                    raise RuntimeError(
                        "Un proceso de infraestructura terminó; revisa los logs privados."
                    ) from None
                time.sleep(0.15)
        raise RuntimeError("Dependencia no inició dentro del tiempo límite.")

    def init(self, seed=True):
        self.mongo_bin = resolve_binary(
            "mongod", self.directory, explicit=self.mongo_bin
        )
        initdb = resolve_binary("initdb", self.directory)
        postgres = resolve_binary("postgres", self.directory)
        redis_bin = resolve_binary("redis-server", self.directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.directory, 0o700)
        if (self.directory / "state.json").exists() or (self.directory / "pg").exists():
            raise RuntimeError(
                "Directorio ya inicializado: no se reinicializa ni se sobrescriben datos."
            )
        pgport, redisport, mongoport = free_port(), free_port(), free_port()
        pgpassword, redispassword, mongopassword = (
            secrets.token_urlsafe(32) for _ in range(3)
        )
        pwfile = self.directory / "pg-password"
        private_file(pwfile, pgpassword + "\n")
        command = [
            initdb,
            "-D",
            str(self.directory / "pg"),
            "-U",
            "rh_bootstrap",
            "--pwfile",
            str(pwfile),
            "--auth-local=trust",
            "--auth-host=scram-sha-256",
            "--encoding=UTF8",
            "--no-locale",
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError("initdb no pudo crear el clúster aislado.")
        pg = self.launch(
            [
                postgres,
                "-D",
                str(self.directory / "pg"),
                "-p",
                str(pgport),
                "-h",
                "127.0.0.1",
                "-k",
                str(self.directory),
                "-c",
                "max_connections=100",
            ],
            "postgres",
        )
        admin_url = (
            f"postgresql://rh_bootstrap:{pgpassword}@127.0.0.1:{pgport}/postgres"
        )
        self.wait(lambda: psycopg.connect(admin_url).close())
        redisconf = self.directory / "redis.conf"
        aclfile = self.directory / "redis.acl"
        private_file(aclfile, f"user default on >{redispassword} ~* &* +@all\n")
        private_file(
            redisconf,
            f"bind 127.0.0.1\nport {redisport}\nprotected-mode yes\naclfile {aclfile}\n"
            f"dir {self.directory}\nappendonly yes\nappendfsync always\nmaxmemory-policy noeviction\n",
        )
        redisprocess = self.launch([redis_bin, str(redisconf)], "redis")
        redisadmin = redis.Redis(
            host="127.0.0.1",
            port=redisport,
            password=redispassword,
            decode_responses=True,
        )
        self.wait(redisadmin.ping)
        mongo_dir = self.directory / "mongo"
        mongo_dir.mkdir(mode=0o700)
        mongoprocess = self.launch(
            [
                self.mongo_bin,
                "--dbpath",
                str(mongo_dir),
                "--port",
                str(mongoport),
                "--bind_ip",
                "127.0.0.1",
                "--auth",
                "--quiet",
                "--wiredTigerCacheSizeGB",
                "0.25",
            ],
            "mongodb",
        )
        bootstrap = MongoClient(
            f"mongodb://127.0.0.1:{mongoport}", serverSelectionTimeoutMS=1000
        )
        self.wait(lambda: bootstrap.admin.command("ping"))
        bootstrap.admin.command(
            "createUser",
            "rh_bootstrap",
            pwd=mongopassword,
            roles=[{"role": "root", "db": "admin"}],
        )
        bootstrap.close()
        mongo_admin_url = f"mongodb://rh_bootstrap:{mongopassword}@127.0.0.1:{mongoport}/?authSource=admin"
        mongo = MongoClient(mongo_admin_url, serverSelectionTimeoutMS=2000)
        from scripts.provision import provision

        urls = {s: f"http://127.0.0.1:{free_port()}" for s in SERVICES}
        prepared = provision(
            self.directory,
            admin_url=admin_url,
            pg_host="127.0.0.1",
            pgport=pgport,
            redisadmin=redisadmin,
            redis_host="127.0.0.1",
            redisport=redisport,
            mongo=mongo,
            mongo_host="127.0.0.1",
            mongoport=mongoport,
            urls=urls,
            schema_path=ROOT.parents[1] / "data/database/schema.sql",
            seed=seed,
        )
        self.configs = prepared["configs"]
        dbowners, accounts = prepared["database_owners"], prepared["accounts"]
        password, region, tenants = (
            prepared[k] for k in ("password", "region_id", "tenants")
        )
        mongo.close()
        redisadmin.execute_command("ACL", "SAVE")
        self.state = {
            "database_layout": "shared-v6",
            "web_sessions": prepared["web_sessions"],
            "directory": str(self.directory),
            "database_admin": admin_url,
            "database_owners": dbowners,
            "redis_admin": f"redis://:{redispassword}@127.0.0.1:{redisport}/0",
            "mongo_admin": mongo_admin_url,
            "accounts": accounts,
            "password": password,
            "region_id": region,
            "tenants": tenants,
            "infrastructure_pids": {
                "postgres": pg.pid,
                "redis": redisprocess.pid,
                "mongodb": mongoprocess.pid,
            },
            "infrastructure_commands": {
                "postgres": pg.args,
                "redis": redisprocess.args,
                "mongodb": mongoprocess.args,
            },
            "service_pids": {},
            "worker_pids": {},
            "urls": urls,
        }
        private_file(self.directory / "state.json", json.dumps(self.state, indent=2))
        return self

    def start(self, workers=True, services=None):
        if self.state.get("database_layout") != "shared-v6":
            raise RuntimeError(
                "El entorno conserva bases separadas. Ejecuta scripts/migrate_shared.py con APIs y workers detenidos antes de iniciar esta versión."
            )
        selected = list(SERVICES if services is None else services)
        # Comprobar todos los puertos antes de publicar procesos nuevos.
        for service in selected:
            pid = self.state.get("service_pids", {}).get(service)
            if not pid or not pid_matches(pid, self.directory):
                port = int(self.state["urls"][service].rsplit(":", 1)[1])
                check_port(port, service)
        for service in selected:
            pid = self.state.get("service_pids", {}).get(service)
            if not pid or not pid_matches(pid, self.directory):
                self.start_api(service)
            if workers:
                pid = self.state.get("worker_pids", {}).get(service)
                if not pid or not pid_matches(pid, self.directory):
                    self.start_worker(service)
        self.save()
        import requests

        def available(service):
            response = requests.get(
                self.state["urls"][service] + "/health/live", timeout=2
            )
            response.raise_for_status()
            if workers and not pid_matches(
                self.state["worker_pids"][service], self.directory
            ):
                raise RuntimeError("Worker no inició.")

        for service in selected:
            self.wait(lambda service=service: available(service), seconds=30)
        return self

    def start_api(self, service):
        process = self.launch(
            [
                sys.executable,
                str(ROOT / "run.py"),
                service,
                "--config",
                str(self.directory / (service + ".json")),
            ],
            service,
        )
        self.state["service_pids"][service] = process.pid
        self.save()

    def start_worker(self, service):
        worker = self.launch(
            [
                sys.executable,
                str(ROOT / "worker.py"),
                service,
                "--config",
                str(self.directory / (service + ".json")),
            ],
            service + "-worker",
        )
        self.state["worker_pids"][service] = worker.pid
        self.save()

    def ensure_infrastructure(self):
        commands = self.state.get("infrastructure_commands", {})
        if set(commands) != {"postgres", "redis", "mongodb"}:
            raise RuntimeError(
                "Entorno sin comandos de infraestructura; conserva sus datos."
            )
        if self.mongo_bin:
            commands["mongodb"][0] = self.mongo_bin
        # El instalador ya resolvió/versionó las rutas. No consultar versiones al arrancar.
        pending = []
        for name in commands:
            current = infrastructure_pid(self.state, name)
            if current:
                self.state["infrastructure_pids"][name] = current
            else:
                executable = commands[name][0]
                if not Path(executable).is_file() or not os.access(executable, os.X_OK):
                    raise RuntimeError(
                        f"Falta el ejecutable de {name}. Ejecuta bash install.sh con el mismo --directory."
                    )
                from urllib.parse import urlsplit

                url = self.state[
                    {
                        "postgres": "database_admin",
                        "redis": "redis_admin",
                        "mongodb": "mongo_admin",
                    }[name]
                ]
                check_port(urlsplit(url).port, name)
                pending.append(name)
        self.save()
        for name in pending:
            self.state["infrastructure_pids"][name] = self.launch(
                commands[name], name
            ).pid
            self.save()
        self.wait(
            lambda: psycopg.connect(
                self.state["database_admin"], connect_timeout=2
            ).close()
        )

        def redis_ready():
            with redis.Redis.from_url(
                self.state["redis_admin"], socket_connect_timeout=2, socket_timeout=2
            ) as client:
                client.ping()

        def mongo_ready():
            with MongoClient(
                self.state["mongo_admin"], serverSelectionTimeoutMS=1000
            ) as client:
                client.admin.command("ping")

        self.wait(redis_ready)
        self.wait(mongo_ready)

    def save(self):
        path = self.directory / "state.json"
        # Una interrupción no debe truncar el único registro de configuración/PID.
        with tempfile.NamedTemporaryFile(
            mode="w", dir=self.directory, delete=False
        ) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(json.dumps(self.state, indent=2))
                stream.flush()
                os.fsync(stream.fileno())
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)

    def stop(self):
        for process in reversed(self.processes):
            if process.poll() is None:
                process.terminate()
        for process in reversed(self.processes):
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "init",
            "start",
            "start-infrastructure",
            "stop",
            "stop-service",
            "status",
            "restart-service",
        ),
    )
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--mongo-bin")
    parser.add_argument("--no-workers", action="store_true")
    parser.add_argument("--service", choices=SERVICES)
    args = parser.parse_args()
    env = Environment(args.directory, args.mongo_bin)
    if args.action == "init":
        try:
            env.init()
        except BaseException:
            env.stop()
            raise
        print(
            "Entorno creado. Configuración y credenciales privadas en",
            env.directory / "state.json",
        )
        print(
            "Puertos publicados en state.json; no se ha usado ninguna base existente."
        )
        return
    env.state = json.loads((env.directory / "state.json").read_text())
    if Path(env.state["directory"]).resolve() != env.directory:
        raise RuntimeError(
            "El directorio no corresponde al entorno; usa relocate.py para moverlo."
        )
    if args.action in ("restart-service", "stop-service"):
        if not args.service:
            parser.error(args.action + " requiere --service")
        for group in ("service_pids", "worker_pids"):
            pid = env.state.get(group, {}).get(args.service)
            if pid and pid_matches(pid, env.directory):
                os.kill(pid, signal.SIGTERM)
                until = time.monotonic() + 10
                while pid_matches(pid, env.directory) and time.monotonic() < until:
                    time.sleep(0.1)
                if pid_matches(pid, env.directory):
                    raise RuntimeError(
                        "El proceso no terminó; no se duplica el servicio."
                    )
        if args.action == "stop-service":
            print("Servicio detenido:", args.service)
            return
        env.ensure_infrastructure()
        env.start(not args.no_workers, [args.service])
        print(
            "Servicio reiniciado:", args.service, "; los demás procesos se conservaron."
        )
        return
    if args.action in ("start", "start-infrastructure"):
        env.ensure_infrastructure()
        if args.action == "start":
            env.start(not args.no_workers, [args.service] if args.service else None)
            print(
                "Servicios solicitados disponibles; URLs en",
                env.directory / "state.json",
            )
        else:
            print("PostgreSQL, Redis y MongoDB disponibles.")
    elif args.action == "stop":
        # Verificar PID y comando antes de señalar; evitar reutilización de PID ajeno.
        signaled = []
        for group in ("web_pids", "worker_pids", "service_pids", "infrastructure_pids"):
            for name, pid in env.state.get(group, {}).items():
                if group == "infrastructure_pids":
                    pid = infrastructure_pid(env.state, name)
                    owned = pid is not None
                else:
                    owned = pid_matches(pid, env.directory)
                if owned:
                    try:
                        os.kill(pid, signal.SIGTERM)
                        signaled.append(pid)
                    except ProcessLookupError:
                        pass
        until = time.monotonic() + 10
        while time.monotonic() < until:
            alive = []
            for pid in signaled:
                try:
                    os.kill(pid, 0)
                    alive.append(pid)
                except ProcessLookupError:
                    pass
            if not alive:
                break
            time.sleep(0.1)
        print(
            "Detención solicitada únicamente a los procesos de este entorno. Datos conservados."
        )
    else:
        import requests

        for service, url in env.state["urls"].items():
            try:
                result = requests.get(url + "/health/ready", timeout=4)
                print(
                    service,
                    result.status_code,
                    result.json()["data"]["state"],
                    url + "/docs",
                )
            except Exception:
                print(service, "down")


if __name__ == "__main__":
    main()
