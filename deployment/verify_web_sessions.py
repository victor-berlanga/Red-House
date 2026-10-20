"""Verificar por HTTP real las sesiones del portal Docker; emitir solo evidencia sin credenciales."""

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / ".local/compose")
    parser.add_argument("--url", default="http://127.0.0.1:6050")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "documentation/evidencias/sesiones-redis/docker.json",
    )
    args = parser.parse_args()
    state = json.loads((args.directory / "state.json").read_text())
    compose = ["docker", "compose", "-f", str(ROOT / "compose.yaml")]
    environment = dict(os.environ, REDHOUSE_COMPOSE_DIR=str(args.directory.resolve()))
    session = requests.Session()

    def csrf(path):
        response = session.get(args.url + path, timeout=8)
        assert response.status_code == 200, (path, response.status_code)
        return etree.HTML(response.content).xpath('//input[@name="csrf_token"]/@value')[
            0
        ]

    response = session.post(
        args.url + "/login",
        data={
            "csrf_token": csrf("/login"),
            "login_email": "medical1",
            "password": state["password"],
        },
        allow_redirects=False,
        timeout=8,
    )
    assert response.status_code == 302
    config = json.loads((args.directory / "web.json").read_text())
    # El nombre de la cookie se obtiene del módulo real, no se expone su valor.
    program = """
import json
from src import create_app
from src.integration import sessions
app=create_app({'MICROSERVICES_CONFIG':'/run/secrets/config'})
cookies=COOKIES
with app.app_context():
 sid=cookies[app.config['JWT_COOKIE_NAME']]
 value=sessions.load(sid)
 assert value
 name=sessions.redis_key('session',sessions.key(sid))
 payload=sessions.redis_client().get(name)
 ttl=sessions.redis_client().ttl(name)
 assert 0<ttl<=86400
 assert value['access_token'].encode() not in payload and value['refresh_token'].encode() not in payload
 with sessions.database() as conn:
  role=conn.execute('SELECT current_user').fetchone()[0]
  assert role=='rh_web_sessions'
 print(json.dumps({'ttl':ttl,'tokens_encrypted':True,'postgres_role':role,'cookie_name':app.config['JWT_COOKIE_NAME']}))
""".replace("COOKIES", repr(dict(session.cookies)))
    result = subprocess.run(
        compose + ["exec", "-T", "web", "python", "-"],
        input=program,
        text=True,
        capture_output=True,
        env=environment,
    )
    assert result.returncode == 0, (
        "Falló inspección privada de almacenamiento en contenedor."
    )
    proof = json.loads(result.stdout)
    token = csrf("/solicitudes/nueva")
    renewal = session.post(
        args.url + "/sesion/continuar", headers={"X-CSRFToken": token}, timeout=8
    )
    assert renewal.status_code == 200
    assert (
        "access_token" not in renewal.json() and "refresh_token" not in renewal.json()
    )
    old_cookie = session.cookies.get(proof.pop("cookie_name"))
    cookies = dict(session.cookies)
    logout = session.post(
        args.url + "/logout",
        data={"csrf_token": renewal.json()["csrf_token"]},
        allow_redirects=False,
        timeout=8,
    )
    assert logout.status_code == 302
    assert old_cookie not in session.cookies.values()
    replay = requests.get(
        args.url + "/panel", cookies=cookies, allow_redirects=False, timeout=8
    )
    assert replay.status_code == 302 and "/login" in replay.headers["Location"]
    cid = subprocess.check_output(
        compose + ["ps", "-q", "web"], env=environment, text=True
    ).strip()
    container = json.loads(
        subprocess.check_output(["docker", "inspect", cid], text=True)
    )[0]
    mounts = [m["Destination"] for m in container["Mounts"]]
    assert "/data/web" not in mounts and "WEB_SESSION_STORE" not in config
    running = subprocess.check_output(
        compose + ["ps", "--services", "--status", "running"],
        env=environment,
        text=True,
    ).splitlines()
    apis = [name for name in running if name.endswith(("-a", "-b"))]
    evidence = {
        "date": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "http": {
            "login": response.status_code,
            "renew": renewal.status_code,
            "logout": logout.status_code,
            "closed_cookie_replay": replay.status_code,
        },
        "storage": proof,
        "local_session_mount": False,
        "web_image": container["Image"],
        "backend": config["BACKEND_MODE"],
        "api_containers_running": apis,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(evidence, ensure_ascii=False))


if __name__ == "__main__":
    main()
