"""Demostración de fallos en la VM de Red House, un comando por caso.

Uso, dentro de la VM (`gcloud compute ssh red-house --project=sistemas-integracion-01 --zone=me-central1-a`):

    sudo python3 /opt/redhouse/deployment/gcp/fallo.py                 # lista de casos
    sudo python3 /opt/redhouse/deployment/gcp/fallo.py estado          # salud de todo
    sudo python3 /opt/redhouse/deployment/gcp/fallo.py <caso>          # provoca y muestra
    sudo python3 /opt/redhouse/deployment/gcp/fallo.py <caso> restablecer
    sudo python3 /opt/redhouse/deployment/gcp/fallo.py todo restablecer

Los casos que detienen algo (microservicio, redis, mongodb, postgres, archivos) lo dejan
detenido para que se vea el efecto; al final imprimen el comando para restablecer. Los
demás terminan solos. Usa cuentas sintéticas sin MFA (operator1, operator2, donor1,
transport1); la contraseña se lee de `state.json` y nunca se imprime.
"""

import json
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

ROOT = Path("/opt/redhouse")
PRIVATE = ROOT / ".local/compose"


def _origin():
    # Nginx solo atiende el nombre público (con 127.0.0.1 cierra la conexión).
    try:
        return json.loads((PRIVATE / "public.json").read_text())["origin"].rstrip("/")
    except (OSError, ValueError, KeyError):
        return "https://34.18.186.116"


BASE = _origin()
SCRIPT = "sudo python3 /opt/redhouse/deployment/gcp/fallo.py"
SERVICES = (
    "identidad-acceso donantes receptores inventario compatibilidad "
    "priorizacion-geografia transporte custodia alertas auditoria monitoreo documentos"
).split()
TLS = ssl.create_default_context()
TLS.check_hostname = False
TLS.verify_mode = ssl.CERT_NONE  # La VM se consulta a sí misma; no se valida su propio certificado.


# ----------------------------------------------------------------------------- utilidades
def titulo(texto):
    print("\n\033[1m== " + texto + "\033[0m")


def ver(texto):
    print("   -> " + texto)


def mostrar(*lineas):
    print("\n\033[1mQué mostrar al profesor:\033[0m")
    for linea in lineas:
        print("   * " + linea)


def compose(*args, check=True, quiet=True):
    command = ["docker", "compose", "--project-directory", str(ROOT), "-f", str(ROOT / "compose.yaml")]
    for name in ("gcs.compose.yaml", "public.compose.yaml"):
        if (PRIVATE / name).exists():
            command += ["-f", str(PRIVATE / name)]
    env = {"REDHOUSE_COMPOSE_DIR": str(PRIVATE), "PATH": "/usr/bin:/usr/local/bin:/bin"}
    result = subprocess.run(command + list(args), env=env, capture_output=quiet, text=True)
    if check and result.returncode:
        raise SystemExit("docker compose " + " ".join(args) + " falló:\n" + (result.stderr or ""))
    return result


def health(container):
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}",
         "redhouse-parcial2-" + container + "-1"], capture_output=True, text=True)
    return result.stdout.strip() or "no existe"


def esperar_sanos(*containers, limite=180):
    inicio = time.monotonic()
    while time.monotonic() - inicio < limite:
        estados = [health(c) for c in containers]
        if all(e.endswith("healthy") and "unhealthy" not in e for e in estados):
            ver(f"{', '.join(containers)}: sanos en {time.monotonic() - inicio:.0f} s")
            return True
        time.sleep(3)
    ver("todavía no están sanos: " + ", ".join(f"{c}={health(c)}" for c in containers))
    return False


def http(method, path, token=None, data=None, raw=None, headers=None, timeout=20):
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    request = urllib.request.Request(BASE + path, data=body, method=method)
    request.add_header("Accept", "application/json")
    request.add_header("Idempotency-Key", uuid4().hex)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", "Bearer " + token)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    inicio = time.monotonic()
    try:
        with urllib.request.urlopen(request, context=TLS, timeout=timeout) as response:
            status, text, head = response.status, response.read().decode(errors="replace"), response.headers
    except urllib.error.HTTPError as exc:
        status, text, head = exc.code, exc.read().decode(errors="replace"), exc.headers
    except Exception as exc:  # noqa: BLE001 - se muestra el tipo de falla de red
        return {"status": None, "error": type(exc).__name__, "s": round(time.monotonic() - inicio, 2)}
    try:
        payload = json.loads(text)
    except ValueError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    return {
        "status": status,
        "code": (payload.get("error") or {}).get("code"),
        "message": (payload.get("error") or {}).get("message"),
        "data": payload.get("data"),
        "correlation_id": (payload.get("meta") or {}).get("correlation_id"),
        "retry_after": head.get("Retry-After") if head else None,
        "s": round(time.monotonic() - inicio, 2),
    }


def resumen(r):
    texto = f"HTTP {r['status']}"
    if r.get("code"):
        texto += f" {r['code']}"
    if r.get("error"):
        texto += f" ({r['error']})"
    return texto + f" en {r['s']} s"


def password():
    return json.loads((PRIVATE / "state.json").read_text())["password"]


def login(user):
    r = http("POST", "/services/identidad-acceso/api/v1/auth/login", data={"username": user, "password": password()},
             headers={"X-RedHouse-Client": "mobile" if user.startswith(("donor", "transport")) else "web"})
    if r["status"] != 200:
        raise SystemExit(f"No se pudo iniciar sesión con {user}: {resumen(r)}")
    return r["data"]


def ready(service):
    r = http("GET", f"/services/{service}/health/ready", timeout=10)
    deps = (r.get("data") or {}).get("dependencies") or {}
    caidas = [k for k, v in deps.items() if isinstance(v, dict) and v.get("state") == "down"]
    return r, caidas


def sql(query):
    return subprocess.run(
        ["docker", "exec", "redhouse-parcial2-postgres-1", "psql", "-U", "rh_bootstrap", "-d", "red_house",
         "-At", "-c", query], capture_output=True, text=True).stdout.strip()


def monitoreo(service):
    schema = sql("SELECT table_schema FROM information_schema.tables WHERE table_name='checks' LIMIT 1")
    if not schema:
        return "sin datos"
    return sql(f"SELECT to_char(created_at,'HH24:MI:SS')||' '||state FROM {schema}.checks "
               f"WHERE service='{service.replace('-', '_')}' ORDER BY created_at DESC LIMIT 1")


def pendientes_outbox():
    schemas = sql("SELECT table_schema FROM information_schema.tables WHERE table_name='outbox'").split()
    if not schemas:
        return 0
    query = " UNION ALL ".join(f"SELECT count(*) FROM {s}.outbox WHERE delivered_at IS NULL" for s in schemas)
    return sum(int(x) for x in sql(query).split() or [0])


def portal():
    return http("GET", "/login", headers={"Accept": "text/html"})


# ----------------------------------------------------------------------------- casos
def estado():
    titulo("Estado de la plataforma")
    salida = subprocess.run(["docker", "ps", "--format", "{{.Names}} {{.Status}}"], capture_output=True, text=True).stdout
    sanos = sum("(healthy)" in l for l in salida.splitlines())
    ver(f"contenedores sanos: {sanos} de {len(salida.splitlines())}")
    for service in SERVICES:
        r, caidas = ready(service)
        ver(f"{service:24} /health/ready {resumen(r)}" + (f"  dependencias caídas: {caidas}" if caidas else ""))
    ver("portal /login " + resumen(portal()))


def microservicio(restablecer=False):
    if restablecer:
        titulo("Restablecer Inventario")
        compose("start", "inventario-a", "inventario-b")
        esperar_sanos("inventario-a", "inventario-b")
        time.sleep(12)
        ver("Inventario /health/ready " + resumen(ready("inventario")[0]))
        ver("Monitoreo, última comprobación de inventario: " + monitoreo("inventario"))
        return
    titulo("Detener un microservicio: Inventario (sus dos réplicas)")
    compose("stop", "inventario-a", "inventario-b")
    ver("inventario-a e inventario-b detenidos")
    time.sleep(12)
    ver("Inventario /health/ready " + resumen(ready("inventario")[0]))
    ver("Donantes /health/ready " + resumen(ready("donantes")[0]))
    ver("Identidad /health/ready " + resumen(ready("identidad-acceso")[0]))
    ver("portal /login " + resumen(portal()))
    ver("Monitoreo, última comprobación de inventario: " + monitoreo("inventario"))
    mostrar("Inventario responde 502 desde Nginx; los demás servicios y el portal siguen en 200.",
            "Monitoreo lo detecta solo y lo marca 'down' (panel Estado de la plataforma, con auditor1).",
            f"Restablecer: {SCRIPT} microservicio restablecer")


def base(nombre, servicio_ejemplo, restablecer=False):
    if restablecer:
        titulo(f"Restablecer {nombre}")
        compose("start", nombre)
        esperar_sanos(nombre)
        # Los servicios reconectan sus pools por su cuenta; se espera a que vuelvan a estar listos.
        inicio = time.monotonic()
        while True:
            r, caidas = ready(servicio_ejemplo)
            if r["status"] == 200 or time.monotonic() - inicio > 90:
                break
            time.sleep(2)
        ver(f"{servicio_ejemplo} /health/ready {resumen(r)}, listo {time.monotonic() - inicio:.0f} s después"
            + (f" caídas: {caidas}" if caidas else ""))
        return True
    compose("stop", nombre)
    ver(f"{nombre} detenido")
    time.sleep(3)
    r, caidas = ready(servicio_ejemplo)
    ver(f"{servicio_ejemplo} /health/ready {resumen(r)}  dependencias caídas: {caidas}")
    live = http("GET", f"/services/{servicio_ejemplo}/health/live")
    ver(f"{servicio_ejemplo} /health/live {resumen(live)} (el proceso sigue vivo)")
    return False


def redis(restablecer=False):
    if restablecer:
        base("redis", "donantes", True)
        if Path("/tmp/redhouse-fallo-token").exists():
            token = Path("/tmp/redhouse-fallo-token").read_text()
            Path("/tmp/redhouse-fallo-token").unlink()
            ver("el mismo token de antes: " + resumen(http("GET", "/services/donantes/api/v1/campaigns", token)))
        return
    titulo("Desactivar temporalmente Redis")
    token = login("operator1")["access_token"]
    ver("antes: consulta autenticada " + resumen(http("GET", "/services/donantes/api/v1/campaigns", token)))
    Path("/tmp/redhouse-fallo-token").write_text(token)
    Path("/tmp/redhouse-fallo-token").chmod(0o600)
    base("redis", "donantes")
    ver("consulta autenticada con Redis caído " + resumen(http("GET", "/services/donantes/api/v1/campaigns", token)))
    ver("inicio de sesión con Redis caído " + resumen(http(
        "POST", "/services/identidad-acceso/api/v1/auth/login", data={"username": "operator2", "password": password()}, headers={"X-RedHouse-Client": "web"})))
    mostrar("Falla cerrada: las peticiones autenticadas responden 503 (sesiones y revocaciones viven en Redis); no hay 500 ni se cuelga.",
            "/health/ready marca redis: down; /health/live sigue en 200.",
            f"Restablecer: {SCRIPT} redis restablecer (verás 200 otra vez).")


def mongodb(restablecer=False):
    if restablecer:
        base("mongodb", "auditoria", True)
        for _ in range(20):
            if pendientes_outbox() == 0:
                break
            time.sleep(3)
        ver(f"eventos pendientes en la bandeja de salida: {pendientes_outbox()} (se entregaron a Auditoría)")
        return
    titulo("MongoDB no responde")
    ver(f"eventos pendientes en la bandeja de salida antes: {pendientes_outbox()}")
    base("mongodb", "auditoria")
    sesion = login("operator1")  # El inicio de sesión es una operación que se audita.
    ver("inicio de sesión (operación auditada) con MongoDB caído: HTTP 200")
    http("POST", "/services/identidad-acceso/api/v1/auth/logout", sesion["access_token"])
    time.sleep(8)
    ver(f"eventos pendientes en la bandeja de salida ahora: {pendientes_outbox()}")
    mostrar("El negocio sigue (PostgreSQL); la auditoría documental queda retenida en la bandeja de salida, sin perderse.",
            "Auditoría /health/ready marca mongodb: down.",
            f"Restablecer: {SCRIPT} mongodb restablecer (los pendientes bajan a 0).")


def postgres(restablecer=False):
    if restablecer:
        base("postgres", "donantes", True)
        ver("consulta pública " + resumen(http("GET", "/services/donantes/api/v1/public/campaigns")))
        return
    titulo("PostgreSQL no responde")
    base("postgres", "donantes")
    ver("inicio de sesión " + resumen(http(
        "POST", "/services/identidad-acceso/api/v1/auth/login", data={"username": "operator1", "password": password()}, headers={"X-RedHouse-Client": "web"})))
    mostrar("Las operaciones responden 503 controlado (database_unavailable), sin escrituras a medias.",
            "/health/live 200 (proceso vivo) y /health/ready 503 (no listo).",
            f"Restablecer: {SCRIPT} postgres restablecer")


def archivos(restablecer=False):
    if restablecer:
        titulo("Restablecer Documentos")
        compose("start", "documentos-a", "documentos-b")
        esperar_sanos("documentos-a", "documentos-b")
        r, caidas = ready("documentos")
        ver("Documentos /health/ready " + resumen(r) + f" almacenamiento: {(r.get('data') or {}).get('dependencies', {}).get('storage')}")
        return
    titulo("El servicio de archivos no está disponible (Documentos)")
    compose("stop", "documentos-a", "documentos-b")
    time.sleep(3)
    ver("Documentos /health/ready " + resumen(ready("documentos")[0]))
    ver("Inventario /health/ready " + resumen(ready("inventario")[0]))
    ver("portal /login " + resumen(portal()))
    mostrar("Solo fallan las cargas y descargas; el resto del sistema y el portal siguen.",
            "Los archivos ya guardados en GCS no se pierden: el bucket es independiente.",
            f"Restablecer: {SCRIPT} archivos restablecer")


def tiempo():
    titulo("Una petición excede el tiempo máximo (Identidad congelada)")
    token = login("operator1")["access_token"]
    datos = {"folio": "DEMO-TO-" + uuid4().hex[:8], "kind": "BLOOD", "component": "RBC",
             "blood_group": "O-", "expires_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 172800)),
             "location_id": str(uuid4())}  # Ubicación ficticia: Inventario debe consultar a Identidad.
    compose("pause", "identidad-acceso-a", "identidad-acceso-b")
    ver("Identidad congelada: acepta la conexión pero no responde")
    try:
        r = http("POST", "/services/inventario/api/v1/resources", token, data=datos)
        ver("Inventario, alta que consulta a Identidad: " + resumen(r))
    finally:
        compose("unpause", "identidad-acceso-a", "identidad-acceso-b")
        ver("Identidad reanudada")
    r = http("POST", "/services/inventario/api/v1/resources", token, data=datos)
    ver("misma petición con Identidad de vuelta: " + resumen(r) + " (la ubicación ficticia no existe; no se creó nada)")
    mostrar("Inventario corta la espera a ~3 s (lectura máx. 3 s en redhouse/client.py) y responde 503 dependency_unavailable.",
            "No queda colgado ni escribe: la unidad no se registró.",
            "Docker puede mostrar Identidad como no sana unos 30 s después de reanudarla; se recupera sola.")


def token():
    titulo("Revocar un token")
    a = login("transport1")
    b = login("transport1")
    ver("sesión A consulta su perfil: " + resumen(http("GET", "/services/identidad-acceso/api/v1/auth/me", a["access_token"])))
    ver("revocar sesión A: " + resumen(http("POST", "/services/identidad-acceso/api/v1/auth/revoke", data={"refresh_token": a["refresh_token"]})))
    ver("sesión A reusa su token: " + resumen(http("GET", "/services/identidad-acceso/api/v1/auth/me", a["access_token"])))
    ver("sesión A intenta renovarse: " + resumen(http("POST", "/services/identidad-acceso/api/v1/auth/refresh", data={"refresh_token": a["refresh_token"]})))
    ver("sesión B (otro dispositivo) sigue: " + resumen(http("GET", "/services/identidad-acceso/api/v1/auth/me", b["access_token"])))
    http("POST", "/services/identidad-acceso/api/v1/auth/logout", b["access_token"])
    mostrar("El token revocado da 401 de inmediato y no se puede renovar; las otras sesiones no se afectan.")


def invalida():
    titulo("Provocar una respuesta inválida")
    token = login("operator1")["access_token"]
    ver("JSON mal formado: " + resumen(http("POST", "/services/donantes/api/v1/donors", token, raw=b'{"folio": "X", ')))
    r = http("POST", "/services/donantes/api/v1/donors", token, data={"folio": 123, "blood_group": "Z+", "consent": "tal vez"})
    ver("tipos y valores inválidos: " + resumen(r) + f" — {r.get('message')}")
    ver("ruta con identificador inválido: " + resumen(http("GET", "/services/donantes/api/v1/donors/no-es-uuid", token)))
    http("POST", "/services/identidad-acceso/api/v1/auth/logout", token)
    mostrar("Cada error regresa con el mismo sobre JSON (error.code, message, details) y su correlation_id; nunca un 500.",
            "Las respuestas inválidas de un servicio a otro (HTML, JSON sin sobre, truncado) se cubren con "
            "apps/services/tests/test_dependency_timeout_unit.py: terminan en 503 dependency_unavailable.")


def inexistente():
    titulo("Consultar un archivo inexistente")
    token = login("operator1")["access_token"]
    falso = str(uuid4())
    ver(f"descargar archivo {falso[:8]}…: " + resumen(http("GET", f"/services/documentos/api/v1/files/{falso}/download", token)))
    ver("metadatos del documento: " + resumen(http("GET", f"/services/documentos/api/v1/documents/{falso}", token)))
    http("POST", "/services/identidad-acceso/api/v1/auth/logout", token)
    mostrar("404 not_found controlado; no revela rutas ni el bucket.")


def sobrecarga():
    titulo("Simular una sobrecarga (240 peticiones simultáneas de una cuenta)")
    t1 = login("operator1")["access_token"]
    t2 = login("operator2")["access_token"]
    with ThreadPoolExecutor(24) as pool:
        futuros = [pool.submit(http, "GET", "/services/donantes/api/v1/campaigns?page_size=1", t1) for _ in range(240)]
        otra = http("GET", "/services/donantes/api/v1/campaigns?page_size=1", t2)
        resultados = [f.result() for f in futuros]
    conteo = {}
    for r in resultados:
        conteo[r["status"]] = conteo.get(r["status"], 0) + 1
    ver(f"respuestas de operator1: {conteo}")
    limitada = next((r for r in resultados if r["status"] == 429), None)
    if limitada:
        ver(f"ejemplo de 429: código {limitada['code']}, Retry-After {limitada['retry_after']} s")
    ver("operator2 durante la ráfaga: " + resumen(otra))
    for t in (t1, t2):
        http("POST", "/services/identidad-acceso/api/v1/auth/logout", t)
    mostrar("La cuota por cuenta responde 429 rate_limit con Retry-After; el servicio sigue atendiendo a los demás.",
            "operator1 queda limitado unos 60 s; no usar esa cuenta en ese minuto.")


def permisos():
    titulo("Mostrar un intento sin permisos")
    op1 = login("operator1")["access_token"]
    op2 = login("operator2")["access_token"]
    donor = login("donor1")["access_token"]
    lista = http("GET", "/services/donantes/api/v1/donors?page_size=1", op1)
    items = (lista.get("data") or {}).get("items") or []
    if items:
        r = http("GET", "/services/donantes/api/v1/donors/" + items[0]["id"], op2)
        ver("operator2 (Hospital 2) abre un donante del Hospital 1: " + resumen(r) + f"  correlation_id {r['correlation_id']}")
    ver("donor1 intenta registrar inventario: " + resumen(http("POST", "/services/inventario/api/v1/resources", donor, data={
        "folio": "DEMO-PERM-" + uuid4().hex[:6], "kind": "BLOOD", "component": "RBC", "blood_group": "O-",
        "expires_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 172800))})))
    ver("sin token: " + resumen(http("GET", "/services/donantes/api/v1/donors")))
    for t in (op1, op2, donor):
        http("POST", "/services/identidad-acceso/api/v1/auth/logout", t)
    mostrar("403 forbidden por institución y por rol; 401 sin token. No se muestra ningún dato ajeno.",
            "El rechazo entre instituciones queda auditado (acción REJECTED; en Auditoría filtrar 'Todas las categorías').")


def logs():
    titulo("Explicar un error en los logs")
    op1 = login("operator1")["access_token"]
    op2 = login("operator2")["access_token"]
    items = ((http("GET", "/services/donantes/api/v1/donors?page_size=1", op1).get("data") or {}).get("items") or [])
    r = http("GET", "/services/donantes/api/v1/donors/" + (items[0]["id"] if items else str(uuid4())), op2)
    for t in (op1, op2):
        http("POST", "/services/identidad-acceso/api/v1/auth/logout", t)
    cid = r["correlation_id"]
    ver(f"error provocado: {resumen(r)}; correlation_id = {cid}")
    time.sleep(1)
    encontrada = "donantes-a"
    for replica in ("donantes-a", "donantes-b"):  # Nginx reparte entre las dos réplicas.
        salida = subprocess.run(["docker", "logs", "--since", "2m", "redhouse-parcial2-" + replica + "-1"],
                                capture_output=True, text=True)
        for linea in (salida.stdout + salida.stderr).splitlines():
            if cid and cid in linea:
                encontrada = replica
                ver(f"{replica}: {linea[:300]}")
    mostrar("El usuario ve el correlation_id (en el portal: 'Referencia'); con él se encuentra la línea exacta del log:",
            f"sudo docker logs redhouse-parcial2-{encontrada}-1 2>&1 | grep {cid}",
            "La línea trae ruta, estado HTTP, código de error y tiempo; nunca contraseñas ni tokens.")


def todo_restablecer():
    titulo("Restablecer todo")
    compose("unpause", "identidad-acceso-a", "identidad-acceso-b", check=False)
    resultado = subprocess.run(["python3", str(ROOT / "deployment/start.py")], capture_output=True, text=True)
    ver("start.py terminó con código " + str(resultado.returncode))
    estado()


CASOS = {
    "estado": (estado, "Salud de los 30 contenedores y de los 12 servicios"),
    "microservicio": (microservicio, "Detener un microservicio (Inventario, ambas réplicas)"),
    "token": (token, "Revocar un token"),
    "redis": (redis, "Desactivar temporalmente Redis"),
    "invalida": (invalida, "Provocar una respuesta inválida"),
    "inexistente": (inexistente, "Consultar un archivo inexistente"),
    "sobrecarga": (sobrecarga, "Simular una sobrecarga"),
    "permisos": (permisos, "Mostrar un intento sin permisos"),
    "logs": (logs, "Explicar un error en los logs"),
    "mongodb": (mongodb, "MongoDB no responde"),
    "postgres": (postgres, "PostgreSQL no responde"),
    "archivos": (archivos, "El servicio de archivos no está disponible"),
    "tiempo": (tiempo, "Una petición excede el tiempo máximo"),
}
RESTABLECIBLES = {"microservicio", "redis", "mongodb", "postgres", "archivos"}


def main():
    args = sys.argv[1:]
    if not args or args[0] not in CASOS and args[0] != "todo":
        print(__doc__)
        for nombre, (_, descripcion) in CASOS.items():
            extra = "   (luego: " + nombre + " restablecer)" if nombre in RESTABLECIBLES else ""
            print(f"  {nombre:14} {descripcion}{extra}")
        return
    if args[0] == "todo":
        todo_restablecer()
        return
    funcion = CASOS[args[0]][0]
    if len(args) > 1 and args[1] == "restablecer":
        if args[0] not in RESTABLECIBLES:
            print("Este caso termina solo; no hay nada que restablecer.")
            return
        funcion(restablecer=True)
    else:
        funcion()


if __name__ == "__main__":
    main()
