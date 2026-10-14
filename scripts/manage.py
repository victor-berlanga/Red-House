"""Preparación y operación local; dependencias Python aisladas y datos persistentes."""

import argparse
import fcntl
import hashlib
import json
import os
import platform
import secrets
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SERVICES_ROOT = REPO / "apps/services"
WEB = REPO / "apps/web"
sys.path.insert(0, str(SERVICES_ROOT))
# Leer el catálogo sin importar Flask ni dependencias antes de preparar el venv.
import ast

from scripts.dependencies import MONGO_SHA256, MONGO_VERSION, pg_major, resolve_binary

config_tree = ast.parse((SERVICES_ROOT / "redhouse/config.py").read_text())
SERVICES = next(
    ast.literal_eval(node.value)
    for node in config_tree.body
    if isinstance(node, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "SERVICES" for t in node.targets)
)
COMPONENTS = ["todo", "ms", "web", "bases", *SERVICES]


def run(command):
    subprocess.run([str(x) for x in command], check=True)


def venv_help():
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    message = f"\nCausa: Python {version} necesita los módulos venv y ensurepip para preparar pip.\n"
    if platform.system() == "Linux":
        message += (
            "Solución en Debian/Ubuntu (también dentro de WSL):\n"
            f"  sudo apt update\n  sudo apt install python{version}-venv\n"
            "Si el paquete no está disponible, instala el soporte venv desde el mismo "
            "proveedor de ese Python.\n"
            "En otras distribuciones usa su gestor de paquetes.\n"
            "Los paquetes del sistema no se instalan automáticamente.\n"
        )
    else:
        message += "Solución: repara la instalación de Python 3.12+ para incluir venv y ensurepip.\n"
    return message + (
        "Si no tienes permisos de administrador, solicita su instalación.\n"
        "Después repite el instalador. No es necesario borrar las bases de datos."
    )


def ensure_pip(python, install):
    if (
        subprocess.run(
            check=False,
            args=[str(python), "-m", "pip", "--version"],
            capture_output=True,
        ).returncode
        == 0
    ):
        return
    if not install:
        raise RuntimeError(
            f"Falta pip o no funciona en {python.parent.parent}. "
            "Ejecuta el instalador sin --no-install para intentar repararlo."
        )
    print(f"Reparando pip en {python.parent.parent}…", flush=True)
    try:
        run([python, "-m", "ensurepip", "--upgrade"])
    except (subprocess.CalledProcessError, OSError) as exc:
        raise RuntimeError(
            f"No se pudo preparar pip.\nEntorno: {python.parent.parent}\n"
            "Revisa el error anterior y los permisos de escritura de esa carpeta.\n"
            + venv_help()
        ) from exc
    if subprocess.run(
        check=False, args=[str(python), "-m", "pip", "--version"], capture_output=True
    ).returncode:
        raise RuntimeError(
            f"pip sigue sin funcionar en {python.parent.parent}. " + venv_help()
        )


def ensure_python(app, install):
    python = app / ".venv/bin/python"
    if not python.exists():
        if not install:
            raise RuntimeError(
                f"Falta el entorno Python de {app.name}. Ejecuta el instalador sin --no-install."
            )
        if subprocess.run(
            check=False,
            args=[sys.executable, "-c", "import venv, ensurepip"],
            capture_output=True,
        ).returncode:
            raise RuntimeError("No se puede crear el entorno virtual. " + venv_help())
        print(f"Creando entorno Python de {app.name}…", flush=True)
        try:
            run([sys.executable, "-m", "venv", app / ".venv"])
        except (subprocess.CalledProcessError, OSError) as exc:
            raise RuntimeError(
                f"No se pudo crear el entorno virtual {app / '.venv'}. "
                "Revisa el error anterior, el espacio libre y los permisos de escritura. "
                + venv_help()
            ) from exc
    if subprocess.run(
        check=False,
        args=[str(python), "-c", "import sys; sys.exit(sys.version_info < (3, 12))"],
        capture_output=True,
    ).returncode:
        raise RuntimeError(
            f"El .venv de {app.name} necesita Python 3.12+. "
            "Detén sus procesos y recrea ese entorno virtual con Python 3.12; las bases se conservan."
        )
    ensure_pip(python, install)
    # pip incluye packaging: comprobar versiones y extras sin consultar la red.
    check = """
import sys
from importlib.metadata import version, PackageNotFoundError
from pip._vendor.packaging.requirements import Requirement
from pathlib import Path
missing = []
for line in Path(sys.argv[1]).read_text().splitlines():
    if not line.strip() or line.startswith('#'): continue
    r=Requirement(line)
    if r.marker and not r.marker.evaluate(): continue
    try: installed=version(r.name)
    except PackageNotFoundError:
        missing.append(str(r))
        continue
    if installed not in r.specifier: missing.append(str(r))
print(', '.join(missing))
sys.exit(bool(missing))
"""
    requirements = subprocess.run(
        check=False,
        args=[str(python), "-c", check, str(app / "requirements.txt")],
        capture_output=True,
        text=True,
    )
    ready = requirements.returncode == 0
    if ready:
        ready = (
            subprocess.run(
                check=False,
                args=[str(python), "-m", "pip", "check"],
                capture_output=True,
            ).returncode
            == 0
        )
    # Extras críticos de psycopg/PyJWT no necesariamente son dependencias base.
    if ready:
        ready = (
            subprocess.run(
                check=False,
                args=[
                    str(python),
                    "-c",
                    "import psycopg, cryptography; from psycopg import pq; assert pq.__impl__ == 'binary'",
                ],
                capture_output=True,
            ).returncode
            == 0
        )
    if not ready:
        if not install:
            raise RuntimeError(
                f"Dependencias incompletas en {app.name}: "
                + (
                    requirements.stdout.strip()
                    or "conflictos de pip o extras psycopg/cryptography"
                )
                + "; ejecuta el instalador sin --no-install."
            )
        print(f"Instalando dependencias de {app.name}…", flush=True)
        try:
            run([python, "-m", "pip", "install", "-r", app / "requirements.txt"])
            run([python, "-m", "pip", "check"])
        except (subprocess.CalledProcessError, OSError) as exc:
            raise RuntimeError(
                f"No se completaron las dependencias de {app.name}. "
                f"Archivo: {app / 'requirements.txt'}. "
                "El error anterior de pip identifica el paquete o conflicto. "
                "Revisa conexión/proxy, compatibilidad con tu Python y permisos de escritura "
                f"en {app / '.venv'}. No ejecutes pip con sudo. "
                "Corrige la causa y repite el instalador. Para comprobar conflictos entre paquetes instalados:\n  "
                + shlex.join([str(python), "-m", "pip", "check"])
            ) from exc
    return python


def install_binary(name, directory):
    if platform.system() != "Darwin":
        raise RuntimeError(
            f"Falta {name}. La instalación automática está disponible en macOS. "
            "En Linux instala PostgreSQL del major indicado, Redis 7+ y MongoDB 8.0, y añádelos al PATH."
        )
    if name != "mongod":
        package = (
            "redis" if name == "redis-server" else "postgresql@" + pg_major(directory)
        )
        run(["bash", REPO / "scripts/homebrew.sh", package])
        return
    arch = platform.machine()
    if arch not in MONGO_SHA256:
        raise RuntimeError("Arquitectura no soportada por el instalador de MongoDB.")
    target = REPO / f".local/tools/mongodb-{MONGO_VERSION}"
    if target.exists():
        raise RuntimeError(
            f"Instalación MongoDB existente pero inválida: {target}. Revísala antes de sustituirla."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://fastdl.mongodb.org/osx/mongodb-macos-{arch}-{MONGO_VERSION}.tgz"
    print(f"Instalando MongoDB {MONGO_VERSION} en {target}…", flush=True)
    with tempfile.TemporaryDirectory(prefix="download-", dir=target.parent) as temp:
        archive = Path(temp) / "mongodb.tgz"
        run(
            [
                "curl",
                "-fL",
                "--retry",
                "2",
                "--connect-timeout",
                "20",
                "--max-time",
                "600",
                url,
                "-o",
                archive,
            ]
        )
        with archive.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != MONGO_SHA256[arch]:
            raise RuntimeError(
                "SHA-256 de MongoDB no coincide con el publicado; descarga rechazada."
            )
        with tarfile.open(archive) as bundle:
            bundle.extractall(Path(temp) / "unpacked", filter="data")
        unpacked = next((Path(temp) / "unpacked").iterdir())
        unpacked.rename(target)


def ensure_binaries(directory, install):
    state_file = directory / "state.json"
    commands = (
        json.loads(state_file.read_text()).get("infrastructure_commands", {})
        if state_file.exists()
        else {}
    )
    resolved = {}
    for name, key in [
        ("postgres", "postgres"),
        ("initdb", "initdb"),
        ("redis-server", "redis"),
        ("mongod", "mongodb"),
    ]:
        saved = commands.get(key, [None])[0]
        try:
            binary = resolve_binary(name, directory, saved=saved)
        except RuntimeError:
            # Un override explícito incorrecto debe corregirse, nunca ignorarse.
            variable = {
                "postgres": "REDHOUSE_POSTGRES",
                "initdb": "REDHOUSE_INITDB",
                "redis-server": "REDHOUSE_REDIS",
                "mongod": "REDHOUSE_MONGOD",
            }[name]
            if not install or os.environ.get(variable):
                raise
            install_binary(name, directory)
            binary = resolve_binary(name, directory, saved=saved)
        resolved[key] = binary
        print(f"  {name}: {binary}", flush=True)
    return resolved


def prepare_web(directory, state):
    from dotenv import dotenv_values
    from scripts.local import private_file

    config = directory / "web-client.json"
    if not config.exists():
        private_file(
            config,
            json.dumps(
                {
                    "SERVICE_URLS": state["urls"],
                    "WEB_SESSION_STORE": str(directory / "web-sessions.sqlite3"),
                    "REGION_NAME": "Red regional",
                    "SERVICE_TIMEOUT": 8,
                },
                indent=2,
            ),
        )
    secret_file = directory / "web-secrets.env"
    if not secret_file.exists():
        previous = {**dotenv_values(WEB / ".env"), **os.environ}
        values = {}
        for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
            value = previous.get(key)
            if not value:
                value = secrets.token_hex(32)
            if len(value) < 32 or "\n" in value or "\r" in value:
                raise RuntimeError(
                    f"Corrige {key} en tu configuración privada antes de iniciar la web."
                )
            values[key] = value
        if values["SECRET_KEY"] == values["JWT_SECRET_KEY"]:
            raise RuntimeError("Las dos claves web existentes deben ser distintas.")
        # JSON quoting es compatible con valores dotenv entre comillas dobles.
        private_file(
            secret_file, "".join(f"{k}={json.dumps(v)}\n" for k, v in values.items())
        )


def wait_ready(state, services):
    import requests

    pending = set(services)
    until = time.monotonic() + 45
    while pending and time.monotonic() < until:
        for service in list(pending):
            try:
                response = requests.get(
                    state["urls"][service] + "/health/ready", timeout=2
                )
                if response.status_code == 200:
                    pending.remove(service)
            except requests.RequestException:
                pass
        if pending:
            time.sleep(0.5)
    if pending:
        raise RuntimeError(
            "Procesos iniciados pero sin readiness: "
            + ", ".join(sorted(pending))
            + ". Consulta sus logs privados y ejecuta estado."
        )


def prepare_environment(args):
    from scripts.local import Environment

    directory = args.directory
    state_path = directory / "state.json"
    if not state_path.exists() and directory.exists() and any(directory.iterdir()):
        raise RuntimeError(
            "El directorio contiene archivos pero no state.json; no se reinicializa. Usa un directorio nuevo o recupera su estado."
        )
    ensure_python(WEB, not args.no_install)
    resolved = ensure_binaries(directory, not args.no_install)
    env = Environment(directory, resolved["mongodb"])
    try:
        if state_path.exists():
            env.state = json.loads(state_path.read_text())
            for name in ("postgres", "redis", "mongodb"):
                env.state["infrastructure_commands"][name][0] = resolved[name]
            env.save()
        else:
            env.init()
            print(
                "Entorno nuevo creado con dos instituciones y cuentas básicas; credenciales privadas en state.json."
            )
        prepare_web(directory, env.state)
    finally:
        # Solo procesos creados por esta preparación; nunca detener una instalación activa.
        env.stop()
    print(
        "Dependencias y configuración listas. Para iniciar: bash start.sh"
        + (
            " --directory " + str(directory)
            if directory != REPO / ".local/runtime"
            else ""
        )
    )


def operate(args):
    directory = args.directory
    state_path = directory / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if Path(state["directory"]).resolve() != directory:
            raise RuntimeError(
                "El directorio no corresponde a state.json; utiliza relocate.py."
            )
    if args.action == "preparar":
        prepare_environment(args)
        return
    if not state_path.exists():
        raise RuntimeError(
            "Entorno todavía no preparado. Ejecuta bash install.sh con el mismo --directory."
        )
    state = json.loads(state_path.read_text())
    component = args.component if args.action == "reiniciar" else args.action
    web_needed = component in ("todo", "web")
    local = [sys.executable, SERVICES_ROOT / "scripts/local.py"]
    integrated = [sys.executable, SERVICES_ROOT / "scripts/integrated.py"]
    location = ["--directory", directory]
    web_port = ["--web-port", str(args.web_port)]

    def stop(target):
        if target == "todo":
            run(integrated + ["stop"] + location)
        elif target == "web":
            run(integrated + ["stop-web"] + location)
        elif target == "ms":
            for service in SERVICES:
                run(local + ["stop-service", "--service", service] + location)
        else:
            run(local + ["stop-service", "--service", target] + location)

    if args.action == "detener":
        stop(args.component)
        return
    if args.action == "estado":
        run(integrated + ["status"] + location + web_port)
        return
    if args.action == "reiniciar":
        stop(component)
    if component == "todo":
        run(integrated + ["start"] + location + web_port)
        selected = list(SERVICES)
    elif component == "web":
        run(integrated + ["start-web"] + location + web_port)
        selected = []
        print(
            "Solo la web está solicitada; sus operaciones necesitan los microservicios correspondientes."
        )
    else:
        command = "start-infrastructure" if component == "bases" else "start"
        selected = (
            []
            if component == "bases"
            else list(SERVICES)
            if component == "ms"
            else [component]
        )
        extra = ["--service", component] if component in SERVICES else []
        run(local + [command] + location + extra)
    state = json.loads(state_path.read_text())
    wait_ready(state, selected)
    for service in selected:
        print(f"  {service}: {state['urls'][service]}/docs")
    if web_needed:
        print("Portal:", state["web_url"])
    print("Logs y datos privados:", directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=COMPONENTS + ["preparar", "listar", "estado", "detener", "reiniciar"],
    )
    parser.add_argument(
        "component",
        nargs="?",
        choices=[c for c in COMPONENTS if c != "bases"],
        default="todo",
    )
    parser.add_argument("--directory", type=Path, default=REPO / ".local/runtime")
    parser.add_argument("--web-port", type=int, default=5050)
    parser.add_argument("--no-install", action="store_true")
    args = parser.parse_args()
    if args.component != "todo" and args.action not in ("detener", "reiniciar"):
        parser.error("El segundo componente solo se admite con detener o reiniciar.")
    if not 1 <= args.web_port <= 65535:
        parser.error("Puerto fuera de rango.")
    if args.action == "listar":
        print("\n".join(SERVICES))
        return
    args.directory = args.directory.resolve()
    if (
        args.directory == REPO / ".local/runtime"
        and not (args.directory / "state.json").exists()
    ):
        existing = sorted((REPO / ".local").glob("*/state.json"))
        if existing:
            raise RuntimeError(
                "Hay un entorno preparado en otra carpeta: "
                + ", ".join(str(path.parent) for path in existing)
                + ". Usa --directory con esa ruta o trasládalo detenido con "
                "apps/services/scripts/relocate.py. No se creará otra base automáticamente."
            )
    os.umask(0o077)
    lock_root = REPO / ".local"
    lock_root.mkdir(exist_ok=True, mode=0o700)
    inherited = os.environ.pop("REDHOUSE_LAUNCHER_LOCK", None)
    lock_file = (
        os.fdopen(int(inherited), "a")
        if inherited
        else (lock_root / "launcher.lock").open("a")
    )
    with lock_file as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(
                "Otro lanzador está preparando/iniciando el entorno. Espera a que termine."
            ) from None
        python = SERVICES_ROOT / ".venv/bin/python"
        if args.action == "preparar":
            python = ensure_python(SERVICES_ROOT, not args.no_install)
        elif not python.is_file():
            raise RuntimeError("Falta el entorno Python. Ejecuta bash install.sh.")
        # Reejecutar con el venv sin liberar el bloqueo entre preparación y operación.
        if Path(sys.prefix).resolve() != (SERVICES_ROOT / ".venv").resolve():
            os.set_inheritable(lock.fileno(), True)
            os.environ["REDHOUSE_LAUNCHER_LOCK"] = str(lock.fileno())
            os.execv(
                str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]]
            )
        operate(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(
            "\nInterrumpido. Consulta estado antes de repetir; los datos se conservan.",
            file=sys.stderr,
        )
        sys.exit(130)
    except subprocess.CalledProcessError as exc:
        print(
            f"No se completó el comando (salida {exc.returncode}). Revisa el mensaje anterior y los logs privados del entorno.",
            file=sys.stderr,
        )
        sys.exit(exc.returncode or 1)
    except ModuleNotFoundError:
        print("Faltan dependencias Python. Ejecuta bash install.sh.", file=sys.stderr)
        sys.exit(1)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
