#!/bin/bash
# Publica en la VM `red-house` el acceso por aplicación (rama entrega-final, cd6708e -> 989f2e7).
#
# Qué cambia (solo lo necesario, con el mismo patrón de las publicaciones del 18 y 19/11):
#   - Imagen derivada por servicio (FROM imagen vigente + COPY de los archivos cambiados, mismo
#     dueño y modo que el original), etiqueta acceso-app-20261120-01:
#       * 12 servicios: redhouse/security.py (cliente en sesión y JWT), shared_migrations.py
#         (LATEST_VERSION 22) y shared_migrations/022.sql.
#       * identidad-acceso además: ms_identidad_acceso/routes.py, mobile.py, contracts/openapi.json
#         y redhouse/openapi.py (cabecera X-RedHouse-Client en el contrato del login).
#       * web (monolito: trae todos los servicios embebidos): lo anterior + apps/web cambiados
#         (client.py manda X-RedHouse-Client: web, navigation.py, rutas y plantilla) + scripts.
#       * bootstrap: shared_migrations.py, 019-022.sql y scripts/revocar_sesiones_sin_cliente.py
#         (la imagen vigente es del 10/11 y no los tiene; solo se usa para migrar y revocar).
#   - Migración compartida 22 (aditiva: columna `client` en red_house.web_session y vista
#     access_identidad_acceso.sessions). Solo la parte SQL de scripts/upgrade_compose.py: aquel
#     script además reescribe documentos.json, ACL, web.json y state.json, y la configuración
#     vigente de la VM (MFA desactivado, GCS) no se debe tocar.
#   - Copia a /opt/redhouse de los 31 archivos de código/despliegue cambiados (sin pruebas ni .md).
#   - Revoca las sesiones vivas sin aplicación (scripts/revocar_sesiones_sin_cliente.py).
#
# No toca: configuración privada (apps/*.json, web.json, state.json), Nginx/TLS, IAM, buckets,
# storage-init, ClamAV, bases de datos fuera de la migración 22. No usa restore.py.
#
# Modos (como root dentro de la VM):
#   sudo bash /opt/redhouse/.local/compose/publicar_acceso_por_app.sh            # = verificar
#   sudo bash /opt/redhouse/.local/compose/publicar_acceso_por_app.sh verificar  # no cambia nada
#   sudo bash /opt/redhouse/.local/compose/publicar_acceso_por_app.sh aplicar
#   sudo bash /opt/redhouse/.local/compose/publicar_acceso_por_app.sh revertir
# «aplicar» y «revertir» conviene lanzarlos desacoplados de la sesión SSH y seguir el registro:
#   sudo systemd-run --unit=publicar-acceso-app --setenv=HOME=/root bash <este script> aplicar
#   sudo tail -f /opt/redhouse/.local/compose/backups/acceso-app-20261120/aplicar.log
#
# `verificar` solo lee. Incluye un ensayo de la migración 22 dentro de una transacción que
# termina en ROLLBACK (no queda nada escrito) con la imagen bootstrap vigente y los dos archivos
# nuevos montados de solo lectura.
#
# Requiere la carga útil (archivos de 989f2e7) en $PAYLOAD; el script comprueba su SHA-256
# contra el manifiesto de abajo antes de usarla.
set -Eeuo pipefail

MODO=${1:-verificar}
ROOT=/opt/redhouse
TAG=acceso-app-20261120-01
BK=$ROOT/.local/compose/backups/acceso-app-20261120
PAYLOAD=${PAYLOAD:-$ROOT/.local/compose/acceso-app-20261120-payload}
OVR=$ROOT/.local/compose/gcs.compose.yaml
IP=34.18.186.116
COMPOSE="docker compose --project-directory $ROOT -f $ROOT/compose.yaml -f $ROOT/.local/compose/gcs.compose.yaml -f $ROOT/.local/compose/public.compose.yaml"
PSQL="docker exec -i redhouse-parcial2-postgres-1 psql -U rh_bootstrap -d red_house -v ON_ERROR_STOP=1 -qAt"
# Orden de deployment/start.py (receptores de eventos primero); en cada grupo, réplica b antes que a.
START_ORDER="auditoria alertas custodia identidad-acceso donantes receptores compatibilidad priorizacion-geografia inventario transporte documentos monitoreo"
cd $ROOT

# --- Manifiesto: SHA-256 de cada archivo en 989f2e7 -------------------------------------------
MANIFIESTO='67a0d6bda163732a5022fd250faca8eeaa480d4d75024d529ccf8306996f973f apps/services/ms_identidad_acceso/contracts/openapi.json
63f90479c3bcfac7556cdfd643422991c8a991cf2050b06f31d24fd38d1d698b apps/services/ms_identidad_acceso/mobile.py
6d36053ad7e105fb07fc30d49b0033a175a669f4cf680363e29043f7052feae4 apps/services/ms_identidad_acceso/routes.py
7d7629b3d2d22c6d18fc96c8fd00d0ed0d8d9cfb12e1a3728438a49d6a152afe apps/services/redhouse/openapi.py
dcec239c6e20f2d5727c4b2c123754b6858b6c31ff1a06552e43c32f98eaaa90 apps/services/redhouse/security.py
fa33d6b02b64c5bdc3c68a76f1c88ca5205e8f902ed61cfb82cfc204f36bd9f6 apps/services/redhouse/shared_migrations.py
7eb1cd6c4665ae052c77a00fd08b48ace07d67f1cd299391d1b8663e77c2e741 apps/services/redhouse/shared_migrations/019.sql
d0ccd9fa271cba74abc97bbd25d24eb9e5ba96601f132c3e6f86aa0717ee5b1c apps/services/redhouse/shared_migrations/020.sql
5d545fcc1df28034904dbcbbbd51cb65de062693328c4e92344b401d8945101d apps/services/redhouse/shared_migrations/021.sql
f2fb7cc2a4be040327eca6df183aeca5071efc2c64018838b148c37d73f37212 apps/services/redhouse/shared_migrations/022.sql
38d7536624fa270282ec2222a165d5cf78ff6ca8b287688c214a2ecbc56e91d5 apps/services/scripts/benchmark_cache.py
be9cbd764b2c880c67efa88cb7204db238e140b2d0fe4dbc7f184ce378c2b384 apps/services/scripts/check_independence.py
385fbb25b9570aabbece7dd71b60a53adec5aa1d89e920d5868add2c4d4b869a apps/services/scripts/check_integrated.py
4dfe7cc1074d084f3d3e298afbadf8418fb9f86e1b9e5ee750f0ed24e54a41c7 apps/services/scripts/check_launcher.py
47f18a2afc29507e8c21a4c0e8640d5a346d46da25398c0e4366605adc6cbe13 apps/services/scripts/revocar_sesiones_sin_cliente.py
cafe54207e7104984dac191bc7e4a93e63ff74c478dd3716be3e2f6fc9ee3a0a apps/services/scripts/seed_catalogues.py
deef5c88f5436710e35513b8e7bb5eb63c69da0829430e92bdadefbd9c52a5d2 apps/services/scripts/seed_nuevo_leon.py
c0ffa4ffdecfaa9757280451dbccdcc95613c2bb6ef12e3bd91806553d24b169 apps/web/src/integration/__init__.py
ec1b082d781de6ffc25b079fa200856e7b6e99bc62568f1dd8d6a0ea518b4ae7 apps/web/src/integration/client.py
48118ec567a704308b47140734879be0b5e69680b1d2650adec3fd1bb78e9a76 apps/web/src/integration/maintenance.py
a09af7491c808bfff0897bab555af3c9641770b3f2cb50e1564bc67a49ffacc7 apps/web/src/integration/navigation.py
8d3d7d2f4266f2ec98d183ffdb475caf23788fa2f01978e15ec69598ae2ce86b apps/web/src/integration/presentation.py
20f8177491a6d5813f3fa2fbe73a21646a153b4313b4cc4c32286bff84ad461b apps/web/src/integration/routes/__init__.py
49c1c25516ec8963e89de77913804efef8c6f6b41528f4cc500a86769e910bd7 apps/web/src/integration/routes/conservation.py
0a1f6540e2946c0f65dce947950da42a66cf2af1dc6ec77c93ef08829b3d1e36 apps/web/src/integration/routes/inventory.py
0525b453228269b59cbfa0eed2463cedddd0f5a7fe7a8195acec419ea32f2bef apps/web/src/integration/routes/quality.py
eef752672ef38380b848d66b19e41a160f7aeed69f2764fdc3051b1999bdae11 apps/web/src/presentation/templates/base.html
005f5908c164ebdcb4280781905332e72800f79e03727749d6c8578a42f70154 deployment/gcp/fallo.py
79d355f505d0ee3a7f9909c038d3a9a6f6b0c34afcb05816f22a2cfae00a9220 deployment/gcp/populate_demo.py
06a652e352f5fb47955b2cf692dd069d0fa7a822f80702f7727d0d45f2b8f8c0 deployment/gcp/prepare_correction_demo.py
e11d9bec7359a6190785769c971bc8239af8073a9ddce40d1da24e2e0efb18fe deployment/gcp/verify_audit_forms.py
55a5ee3359d5273c47215bd4633e35a2e8823ee0870e3aadba5ba4ea7d9bb852 deployment/gcp/verify_donor_withdrawal.cjs
1cd28bf015301a497d7ece67e12ab72768687f10e92fa74b24d7fa0779bcddaf deployment/gcp/verify_public.cjs
907d54f4c20d2ca682f74ffcb6973e55388977770fde2a41b0a1e0e551e143d2 deployment/verify.py'

# --- Qué archivo va a qué imagen ---------------------------------------------------------------
F_SVC="apps/services/redhouse/security.py apps/services/redhouse/shared_migrations.py apps/services/redhouse/shared_migrations/022.sql"
F_ID="apps/services/ms_identidad_acceso/routes.py apps/services/ms_identidad_acceso/mobile.py apps/services/ms_identidad_acceso/contracts/openapi.json apps/services/redhouse/openapi.py"
F_SCRIPTS="apps/services/scripts/benchmark_cache.py apps/services/scripts/check_independence.py apps/services/scripts/check_integrated.py apps/services/scripts/check_launcher.py apps/services/scripts/seed_catalogues.py apps/services/scripts/seed_nuevo_leon.py apps/services/scripts/revocar_sesiones_sin_cliente.py"
F_WEB=$(echo "$MANIFIESTO" | awk '{print $2}' | grep '^apps/web/' | tr '\n' ' ')
F_BOOT="apps/services/redhouse/shared_migrations.py apps/services/redhouse/shared_migrations/019.sql apps/services/redhouse/shared_migrations/020.sql apps/services/redhouse/shared_migrations/021.sql apps/services/redhouse/shared_migrations/022.sql apps/services/scripts/revocar_sesiones_sin_cliente.py"
# En /opt/redhouse: todo el manifiesto salvo 019-021.sql (ya están allí, idénticos).
F_HOST=$(echo "$MANIFIESTO" | awk '{print $2}' | grep -v -E 'shared_migrations/0(19|20|21)\.sql$' | tr '\n' ' ')

archivos_de() { # servicio de compose (sin -a/-b) o web/bootstrap -> archivos que lleva su imagen
  case $1 in
    identidad-acceso) echo "$F_SVC $F_ID" ;;
    web) echo "$F_SVC $F_ID $F_SCRIPTS $F_WEB" ;;
    bootstrap) echo "$F_BOOT" ;;
    *) echo "$F_SVC" ;;
  esac
}
referencia() { # archivo hermano para dueño/modo de un archivo nuevo
  case $1 in
    */shared_migrations/0*.sql) echo "${1%/*}/018.sql" ;;
    */scripts/*.py) echo "${1%/*}/upgrade_compose.py" ;;
    */integration/*.py) echo "${1%/*}/presentation.py" ;;
    *) echo "$1" ;;
  esac
}
sha_esperado() { echo "$MANIFIESTO" | awk -v p="$1" '$2==p{print $1}'; }
imagen_actual() { python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["services"][sys.argv[2]]["image"])' "$OVR" "$1"; }
imagen_nueva() { local old; old=$(imagen_actual "$1"); echo "${old%%:*}:$TAG"; }
servicios_imagen() { echo web bootstrap; for s in $START_ORDER; do echo "$s"; done; }
esquema() { $PSQL -c "SELECT max(version) FROM red_house.schema_migration"; }
sanos() { echo "$(docker ps --format '{{.Status}}' | grep -c '(healthy)' || true) de $(docker ps -q | wc -l)"; }
t() { date -u +%H:%M:%S; }

# Metadatos dentro de una imagen: ruta|existe/nuevo|uid:gid|modo|sha256
meta_imagen() {
  local img=$1; shift; local specs=()
  for f in "$@"; do specs+=("$f|$(referencia "$f")"); done
  docker run --rm --network none --entrypoint sh "$img" -c '
    for spec in "$@"; do p=${spec%%|*}; r=${spec#*|}
      if [ -e "/app/$p" ]; then echo "$p|existe|$(stat -c "%u:%g|%a" "/app/$p")|$(sha256sum "/app/$p" | cut -d" " -f1)"
      else echo "$p|nuevo|$(stat -c "%u:%g|%a" "/app/$r")|-"; fi
    done' sh "${specs[@]}"
}
meta_host() { # mismo formato, en /opt/redhouse
  for f in "$@"; do
    if [ -e "$ROOT/$f" ]; then echo "$f|existe|$(stat -c '%u:%g|%a' "$ROOT/$f")|$(sha256sum "$ROOT/$f" | cut -d' ' -f1)"
    else echo "$f|nuevo|$(stat -c '%u:%g|%a' "$ROOT/$(referencia "$f")")|-"; fi
  done
}

comprobar_payload() {
  local mal=0
  while read -r sha f; do
    [ -f "$PAYLOAD/$f" ] && [ "$(sha256sum "$PAYLOAD/$f" | cut -d' ' -f1)" = "$sha" ] || { echo "  NO COINCIDE: $f"; mal=1; }
  done <<< "$MANIFIESTO"
  [ $mal = 0 ] || { echo "Carga útil incompleta o distinta de 989f2e7: no se sigue."; exit 1; }
  echo "  carga útil: $(echo "$MANIFIESTO" | wc -l) archivos, SHA-256 = 989f2e7"
}

huella_config() { # huella conjunta de la configuración privada (no imprime contenido)
  (cd $ROOT/.local/compose && sha256sum state.json web.json installation.json gcs.compose.yaml public.compose.yaml public.nginx.conf apps/*.json tls/*) > "$1"
}

# Prueba de humo: importa el código nuevo dentro de una imagen (sin red). $1=imagen $2=web|bootstrap|identidad-acceso|otro.
# Con MONTAR=1 monta los archivos de la carga útil de solo lectura sobre la imagen vigente (verificar);
# sin MONTAR prueba la imagen nueva ya construida (aplicar, antes de detener nada).
humo() {
  local img=$1 s=$2 mods="redhouse.security redhouse.shared_migrations" vols=()
  case $s in
    identidad-acceso) mods="$mods redhouse.openapi ms_identidad_acceso.routes ms_identidad_acceso.mobile" ;;
    web) mods="$mods redhouse.openapi ms_identidad_acceso.routes ms_identidad_acceso.mobile src.integration src.integration.navigation src.integration.routes src.integration.routes.conservation src.integration.routes.inventory src.integration.routes.quality src.integration.maintenance src.integration.client scripts.revocar_sesiones_sin_cliente" ;;
    bootstrap) mods="redhouse.shared_migrations scripts.revocar_sesiones_sin_cliente" ;;
  esac
  if [ "${MONTAR:-0}" = 1 ]; then for f in $(archivos_de $s); do vols+=(-v "$PAYLOAD/$f:/app/$f:ro"); done; fi
  docker run --rm --network none "${vols[@]}" -w /app --entrypoint python "$img" -c '
import importlib, sys
for m in sys.argv[1:]: importlib.import_module(m)
from redhouse.shared_migrations import LATEST_VERSION
assert LATEST_VERSION == 22, LATEST_VERSION
print(len(sys.argv) - 1, "módulos importados, LATEST_VERSION", LATEST_VERSION)' $mods
}

# --- Código Python que corre DENTRO de la imagen bootstrap ------------------------------------
# Parte SQL de scripts/upgrade_compose.py, sin reescribir configuración. ENSAYO=1 => ROLLBACK.
read -r -d '' MIGRAR_PY <<'PY' || true
import json, os, psycopg
from psycopg import sql
from redhouse.shared_migrations import upgrade, LATEST_VERSION
ensayo = os.environ.get("ENSAYO") == "1"
state = json.load(open("/run/install/state.json"))
dsn = next(iter(state["database_owners"].values()))
def q(conn, text):
    return conn.execute(text).fetchone()[0]
with psycopg.connect(dsn) as conn:
    conn.execute("SET lock_timeout = '3s'" if ensayo else "SET lock_timeout = '30s'")
    antes = q(conn, "SELECT max(version) FROM red_house.schema_migration")
    database, had_create = conn.execute(
        "SELECT current_database(), has_database_privilege('rh_shared_owner', current_database(), 'CREATE')"
    ).fetchone()
    if not had_create:
        conn.execute(sql.SQL("GRANT CREATE ON DATABASE {} TO rh_shared_owner").format(sql.Identifier(database)))
    conn.execute("SET LOCAL ROLE rh_shared_owner")
    version = upgrade(conn)
    conn.execute("RESET ROLE")
    if not had_create:
        conn.execute(sql.SQL("REVOKE CREATE ON DATABASE {} FROM rh_shared_owner").format(sql.Identifier(database)))
    r = {
        "antes": antes,
        "despues": q(conn, "SELECT max(version) FROM red_house.schema_migration"),
        "latest": LATEST_VERSION,
        "columna_client_tabla": q(conn, "SELECT count(*) FROM information_schema.columns WHERE table_schema='red_house' AND table_name='web_session' AND column_name='client'"),
        "columna_client_vista": q(conn, "SELECT count(*) FROM information_schema.columns WHERE table_schema='access_identidad_acceso' AND table_name='sessions' AND column_name='client'"),
        "identidad_puede_usar_client": q(conn, "SELECT has_column_privilege('rh_identidad_acceso','access_identidad_acceso.sessions','client','INSERT,SELECT,UPDATE')"),
        "create_db_previo": had_create,
    }
    if ensayo:
        conn.rollback()
        r["modo"] = "ensayo: ROLLBACK, nada escrito"
    else:
        r["modo"] = "aplicado (COMMIT)"
print(json.dumps(r, ensure_ascii=False))
PY

# --- Pruebas HTTPS (corren en el host; la contraseña se lee de state.json y nunca se imprime) ----
read -r -d '' HTTPS_PY <<'PY' || true
import http.cookiejar, json, os, re, ssl, sys, urllib.error, urllib.parse, urllib.request, uuid
BASE = "https://" + os.environ["IP"]
TLS = ssl.create_default_context()
PW = json.load(open("/opt/redhouse/.local/compose/state.json"))["password"]
LOGIN = "/services/identidad-acceso/api/v1/auth/login"
fallos = []

def api(method, path, token=None, data=None, client=None, full=False):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method)
    req.add_header("Accept", "application/json")
    req.add_header("Idempotency-Key", uuid.uuid4().hex)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if client is not None:
        req.add_header("X-RedHouse-Client", client)
    try:
        with urllib.request.urlopen(req, context=TLS, timeout=30) as r:
            status, text = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read()
    try:
        payload = json.loads(text)
    except ValueError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    err = payload.get("error")
    code = err.get("code") if isinstance(err, dict) else None
    if full:  # nunca se imprimen: el mensaje es texto de error público, los tokens solo se devuelven
        msg = err.get("message") if isinstance(err, dict) else None
        return status, code, payload.get("access_token"), msg, payload.get("refresh_token")
    return status, code, payload.get("access_token")

def check(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"  {'OK   ' if ok else 'FALLA'} {nombre}: {obtenido} (esperado {esperado})")
    if not ok:
        fallos.append(nombre)

def previo(modo):
    """modo=crear: login con el servidor anterior (sin cabecera); modo=probar: esa sesión debe dar 401.

    El JWT de acceso dura 15 min (ACCESS_TTL=900) y el corte puede durar más: un 401 en /auth/me
    podría ser solo por vencimiento. La prueba decisiva es la renovación (REFRESH_TTL=24 h), que el
    código nuevo rechaza con el mensaje de «sesión anterior al acceso por aplicación»."""
    if modo == "crear":
        s, _, tok, _, ref = api("POST", LOGIN, data={"username": "operator2", "password": PW}, full=True)
        print(tok + " " + ref if s == 200 and tok and ref else "")
        return
    tok, _, ref = os.environ.get("TOKEN_PREVIO", "").partition(" ")
    if not tok:
        print("  (sin sesión previa: prueba omitida)")
        return
    s, c, _, msg, _ = api("POST", "/services/identidad-acceso/api/v1/auth/refresh", data={"refresh_token": ref}, full=True)
    check("renovación de la sesión previa", (s, c, "anterior al acceso por aplicación" in (msg or "")), (401, "unauthorized", True))
    for nombre, path in [("Identidad /auth/me", "/services/identidad-acceso/api/v1/auth/me"), ("Donantes /campaigns", "/services/donantes/api/v1/campaigns")]:
        s, c, _, msg, _ = api("GET", path, tok, full=True)
        motivo = "sin aplicación" if "anterior al acceso" in (msg or "") else "JWT vencido" if "vencido" in (msg or "") else "otro"
        check(f"token previo en {nombre} ({motivo})", (s, c), (401, "unauthorized"))

def completo():
    print("- login por API con la cabecera X-RedHouse-Client")
    tokens = {}
    for user, client in [("admin1", "web"), ("auditor1", "web"), ("operator1", "desktop"), ("medical1", "desktop"), ("donor1", "mobile"), ("transport1", "mobile")]:
        s, _, tok = api("POST", LOGIN, data={"username": user, "password": PW}, client=client)
        check(f"{user} en {client}", s, 200)
        tokens[(user, client)] = tok
    for user, client in [("donor1", "web"), ("admin1", "desktop"), ("auditor1", "desktop"), ("operator1", "mobile"), ("transport1", "desktop")]:
        s, c, _ = api("POST", LOGIN, data={"username": user, "password": PW}, client=client)
        check(f"{user} en {client} (app equivocada)", (s, c), (403, "client_not_allowed"))
    for nombre, client in [("operator1 sin cabecera", None), ("operator1 con valor desconocido «WEB»", "WEB")]:
        s, c, _ = api("POST", LOGIN, data={"username": "operator1", "password": PW}, client=client)
        check(nombre, (s, c), (400, "client_required"))
    print("- peticiones protegidas con los tokens nuevos (Identidad y otro servicio)")
    for (user, client), tok in tokens.items():
        if tok:
            check(f"/auth/me {user}/{client}", api("GET", "/services/identidad-acceso/api/v1/auth/me", tok)[0], 200)
    for key in [("operator1", "desktop"), ("donor1", "mobile")]:
        if tokens.get(key):
            check(f"donantes /campaigns {key[0]}/{key[1]}", api("GET", "/services/donantes/api/v1/campaigns", tokens[key])[0], 200)
    print("- portal web: formulario de login con CSRF")
    jar = http.cookiejar.CookieJar()

    class SinRedireccion(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), urllib.request.HTTPSHandler(context=TLS), SinRedireccion)

    def web(method, path, form=None):
        data = urllib.parse.urlencode(form).encode() if form else None
        req = urllib.request.Request(BASE + path, data=data, method=method)
        req.add_header("Referer", BASE + "/login")
        try:
            with opener.open(req, timeout=30) as r:
                return r.status, r.headers.get("Location"), r.read().decode(errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Location"), e.read().decode(errors="replace")

    s, _, html = web("GET", "/login")
    check("GET /login", s, 200)
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    form = {"csrf_token": m.group(1) if m else "", "_timezone": "America/Monterrey", "login_email": "admin1", "password": PW}
    s, loc, _ = web("POST", "/login", form)
    check("POST /login admin1", s, 302)
    check("redirige a", urllib.parse.urlsplit(loc or "").path, "/panel")
    check("GET /panel con la sesión", web("GET", "/panel")[0], 200)
    print("- cierre de las sesiones de prueba por API")
    for (user, client), tok in tokens.items():
        if tok:
            check(f"logout {user}/{client}", api("POST", "/services/identidad-acceso/api/v1/auth/logout", tok)[0], 200)

{"crear": lambda: previo("crear"), "probar": lambda: previo("probar"), "completo": completo}[sys.argv[1]]()
if sys.argv[1] != "crear":
    print("  pruebas HTTPS:", "PASA" if not fallos else "FALLA en " + "; ".join(fallos))
sys.exit(1 if fallos else 0)
PY
https_py() { IP=$IP python3 -c "$HTTPS_PY" "$@"; }

esperar_clamav() { # como deployment/start.py: espera sano y pide RELOAD si quedó con firma vieja
  local fin=$((SECONDS + 480)) recargado=0 st
  while [ $SECONDS -lt $fin ]; do
    st=$(docker inspect -f '{{.State.Health.Status}}' redhouse-parcial2-clamav-1 2>/dev/null || echo missing)
    [ "$st" = healthy ] && { echo "  clamav sano"; return 0; }
    if [ "$st" = unhealthy ] && [ $recargado = 0 ]; then
      $COMPOSE exec -T clamav sh -c "printf 'RELOAD\n' | nc -w 5 localhost 3310" || true; recargado=1; fi
    sleep 10
  done
  echo "  ClamAV no quedó sano en 8 min"; return 1
}

recrear() { $COMPOSE up -d --wait --wait-timeout 420 --no-deps --no-build --force-recreate "$@"; }

restaurar_archivos() { # override y archivos de $ROOT como estaban; no toca contenedores
  [ -f $BK/gcs.compose.yaml.orig ] && cp -p $BK/gcs.compose.yaml.orig $OVR
  for f in $F_HOST; do if [ -f $BK/archivos/$f.orig ]; then cp -p $BK/archivos/$f.orig $ROOT/$f; fi; done
  if [ -f $BK/nuevos.txt ]; then while read -r f; do if [ -n "$f" ]; then rm -f -- "$ROOT/$f"; fi; done < $BK/nuevos.txt; fi
  echo "  gcs.compose.yaml y $(find $BK/archivos -name '*.orig' 2>/dev/null | wc -l) archivos restaurados; $(grep -c . $BK/nuevos.txt 2>/dev/null || true) nuevos quitados"
}

reanudar_contenedores_actuales() { # si algo falla antes de migrar: vuelve a arrancar lo que había
  echo "!!! Reanudando los contenedores anteriores (sin recrearlos) en el orden de backup.py"
  restaurar_archivos || true
  $COMPOSE start gateway || true
  $COMPOSE start clamav || true; esperar_clamav || true
  for s in $START_ORDER; do $COMPOSE start --wait $s-a $s-b || true; done
  $COMPOSE start --wait web || true
  echo "--- sanos: $(sanos)"
}

FASE=inicio
al_fallar() {
  local rc=$?
  # Con `set -E` la trampa también corre dentro de $(...) y de los lados de una tubería. Ahí solo se
  # propaga el código: la recuperación corre una sola vez, en el proceso principal. Sin esta guarda,
  # un `grep` vacío dentro de $(...) reanudaba los contenedores viejos a mitad de «aplicar».
  [ "$BASHPID" = "$$" ] || exit $rc
  trap - ERR
  set +e
  echo "!!! Falló en la fase «$FASE» (código $rc) a las $(t) UTC"
  case $FASE in
    detenido|migracion)
      if [ "$(esquema 2>/dev/null)" = 21 ]; then reanudar_contenedores_actuales
      else echo "El esquema ya es 22: no se reanuda lo anterior. Opciones: repetir «aplicar» (es reanudable) o «revertir»."; fi ;;
    recreacion|revocacion|verificacion) echo "--- sanos: $(sanos)"; echo "Opciones: repetir «aplicar» (reanudable) o «revertir»." ;;
    respaldo-archivos|copia|imagenes)
      if [ "${ESQ:-}" = 21 ]; then
        echo "Ningún contenedor se detuvo; se deshacen override y archivos de $ROOT (las imágenes $TAG quedan)."
        restaurar_archivos
      else echo "Reanudación con esquema 22: no se deshace nada. Opciones: repetir «aplicar» o «revertir»."; fi ;;
    *) echo "Ningún contenedor se detuvo y no se cambió ningún archivo." ;;
  esac
  exit $rc
}

# ================================================================================================
plan_y_comprobaciones() { # común a verificar y aplicar; solo lee
  echo "=== $(t) UTC · modo $MODO · etiqueta $TAG"
  echo "--- 1. Carga útil ($PAYLOAD)"; comprobar_payload
  echo "--- 2. Estado de la VM"
  echo "  redhouse.service: $(systemctl is-active redhouse || true) · contenedores sanos: $(sanos)"
  echo "  esquema compartido: $(esquema) · columna client en web_session: $($PSQL -c "SELECT count(*) FROM information_schema.columns WHERE table_schema='red_house' AND table_name='web_session' AND column_name='client'")"
  echo "  sesiones vivas (todas sin aplicación hoy): $($PSQL -c "SELECT count(*) FROM red_house.web_session WHERE revoked_at IS NULL AND expires_at>now()")"
  echo "  disco libre en /: $(df -h --output=avail / | tail -1 | tr -d ' ') · respaldo previo de esta publicación: $([ -d $BK ] && echo "existe ($BK)" || echo no)"
  echo "  huella conjunta de la configuración privada: $(huella_config /dev/stdout | sha256sum | cut -c1-16) (state.json, web.json, apps/*.json, overrides, nginx)"
  echo "--- 3. Imágenes: vigente -> nueva (archivos que entran con COPY; dueño y modo del original)"
  for s in $(servicios_imagen); do
    local key=$s; case $s in web|bootstrap) ;; *) key=$s-a;; esac
    local old new; old=$(imagen_actual $key); new=$(imagen_nueva $key)
    if [ $key != web ] && [ $key != bootstrap ] && [ "$old" != "$(imagen_actual $s-b)" ]; then echo "  $s: las réplicas a/b no comparten imagen; no se sigue"; exit 1; fi
    local ex; ex=$(docker image inspect "$new" >/dev/null 2>&1 && echo " (YA EXISTE)" || true)
    echo "  [$s] $old -> $new$ex"
    meta_imagen "$old" $(archivos_de $s) | while IFS='|' read -r f est own mode sha; do
      local nuevo; nuevo=$(sha_esperado "$f")
      if [ "$est" = nuevo ]; then echo "      nuevo   $f ($own $mode)"
      elif [ "$sha" = "$nuevo" ]; then echo "      igual   $f (ya en 989f2e7)"
      else echo "      cambia  $f ($own $mode) ${sha:0:12} -> ${nuevo:0:12}"; fi
    done
  done
  echo "--- 4. Archivos en $ROOT (cd6708e -> 989f2e7, sin pruebas ni .md)"
  meta_host $F_HOST | while IFS='|' read -r f est own mode sha; do
    local nuevo; nuevo=$(sha_esperado "$f")
    if [ "$est" = nuevo ]; then echo "      nuevo   $f ($own $mode)"
    elif [ "$sha" = "$nuevo" ]; then echo "      igual   $f"
    else echo "      cambia  $f ($own $mode) ${sha:0:12} -> ${nuevo:0:12}"; fi
  done
  echo "--- 5. Compose"
  $COMPOSE --profile install config -q; echo "  compose config: válido"
  echo "  bootstrap resuelve a: $($COMPOSE --profile install config --format json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)["services"]["bootstrap"]["image"])')"
}

humo_vigentes() { # verificar: importa el código nuevo montado sobre cada imagen vigente
  echo "--- 5b. Prueba de humo: el código nuevo importa en cada imagen vigente (montado de solo lectura, sin red)"
  local s key out
  for s in $(servicios_imagen); do
    key=$s; case $s in web|bootstrap) ;; *) key=$s-a;; esac
    out=$(MONTAR=1 humo "$(imagen_actual $key)" $s 2>&1) || { echo "  FALLA la prueba de humo en $s:"; echo "$out" | tail -5; exit 1; }
    echo "  [$s] ${out##*$'\n'}"
  done
  out=$(docker run --rm --network none -w /app -v $PAYLOAD/apps/services/scripts/revocar_sesiones_sin_cliente.py:/app/apps/services/scripts/revocar_sesiones_sin_cliente.py:ro \
    --entrypoint python "$(imagen_actual bootstrap)" -m scripts.revocar_sesiones_sin_cliente --help 2>&1) || { echo "  FALLA: el script de revocación no arranca en bootstrap"; exit 1; }
  echo "  [bootstrap] python -m scripts.revocar_sesiones_sin_cliente --help: ${out%%$'\n'*}"
}

ensayo_migracion() { # ROLLBACK: no deja nada escrito
  local net; net=$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' redhouse-parcial2-postgres-1 | tr ' ' '\n' | grep '_data$')
  echo "--- 6. Ensayo de la migración 22 en una transacción con ROLLBACK (imagen $(imagen_actual bootstrap), red $net)"
  docker run --rm --network "$net" -e ENSAYO=1 \
    -v $ROOT/.local/compose:/run/install:ro \
    -v $PAYLOAD/apps/services/redhouse/shared_migrations.py:/app/apps/services/redhouse/shared_migrations.py:ro \
    -v $PAYLOAD/apps/services/redhouse/shared_migrations/022.sql:/app/apps/services/redhouse/shared_migrations/022.sql:ro \
    --entrypoint python "$(imagen_actual bootstrap)" -c "$MIGRAR_PY" | sed 's/^/  /'
  echo "  esquema después del ensayo: $(esquema) (debe seguir en 21)"
}

pasos() {
  cat <<EOF
--- 7. Lo que haría «aplicar» (en este orden)
  a1. Respaldo de archivos en $BK: gcs.compose.yaml.orig, cada archivo de $ROOT que se reemplaza
      (archivos/<ruta>.orig), lista de nuevos, docker ps e imágenes antes, huella de la configuración.
  b.  Copia a $ROOT de $(echo $F_HOST | wc -w) archivos (dueño y modo del original o de su hermano si es nuevo).
  c.  Construye $(servicios_imagen | wc -w) imágenes derivadas «FROM vigente + COPY» con etiqueta $TAG
      y comprueba en cada una SHA-256, dueño y modo de cada archivo y la prueba de humo (importar el código).
      Todo antes de detener nada; si falla, deshace override y archivos y la VM sigue igual.
      Se apunta gcs.compose.yaml a las nuevas. Exige 30/30 sanos y más de 2 GB libres.
  -   Abre una sesión de prueba con el servidor vigente (operator2, sin cabecera) para comprobar luego el 401
      (la renovación con su refresh token debe responder «sesión anterior al acceso por aplicación»).
  a2. Respaldo verificado: deployment/backup.py --verify --leave-stopped (detiene las 27 aplicaciones,
      vuelca PostgreSQL/Mongo/Redis, restaura en contenedores aislados y compara conteos y hashes).
      Informe en $BK/respaldo.json. SIN SERVICIO desde aquí.
  d.  Migración 22 (parte SQL de upgrade_compose.py) con la imagen bootstrap nueva, aplicaciones detenidas:
      $COMPOSE --profile install run --rm --no-deps -T --entrypoint python bootstrap -c <MIGRAR_PY>
  e.  Arranca gateway y clamav (mismos contenedores), luego recrea por grupo, réplica b antes que a:
      $START_ORDER, y al final web, con:
      $COMPOSE up -d --wait --no-deps --no-build --force-recreate <servicio>
  f.  Revoca sesiones previas: primero en seco y luego --aplicar; la tercera corrida en seco debe dar 0 o falla:
      $COMPOSE --profile install run --rm --no-deps -T --entrypoint python bootstrap -m scripts.revocar_sesiones_sin_cliente --directory /run/install [--aplicar]
  g.  Verificación: 30/30 sanos, imagen y SHA-256 de security.py en cada contenedor, /login 200, /health/ready
      de los 12 servicios por HTTPS, esquema 22, huella de configuración igual a la de antes, login por API
      (200 en su app, 403 client_not_allowed en otra, 400 client_required sin cabecera), sesión previa 401 (antes de f),
      login del portal por formulario, cierre de las sesiones de prueba y gcs.compose.yaml con solo 26 etiquetas cambiadas.
EOF
}

verificacion_final() {
  FASE=verificacion
  echo "=== g. Verificación $(t) UTC"
  local fallo=0
  echo "  contenedores sanos: $(sanos)"; [ "$(sanos)" = "30 de 30" ] || fallo=1
  for s in $START_ORDER; do for r in b a; do
    local c=redhouse-parcial2-$s-$r-1 img; img=$(docker inspect -f '{{.Config.Image}}' $c || true)
    local sha; sha=$(docker exec $c sha256sum /app/apps/services/redhouse/security.py | cut -d' ' -f1 || true)
    [ "$img" = "$(imagen_nueva $s-a)" ] && [ "$sha" = "$(sha_esperado apps/services/redhouse/security.py)" ] || { echo "  FALLA $c: $img ${sha:0:12}"; fallo=1; }
  done; done
  local w; w=$(docker exec redhouse-parcial2-web-1 sh -c 'sha256sum /app/apps/web/src/integration/client.py /app/apps/services/redhouse/security.py' | cut -d' ' -f1 | paste -sd' ' - || true)
  [ "$w" = "$(sha_esperado apps/web/src/integration/client.py) $(sha_esperado apps/services/redhouse/security.py)" ] || { echo "  FALLA web: $w"; fallo=1; }
  echo "  imágenes y SHA-256 dentro de los 25 contenedores de aplicación: $([ $fallo = 0 ] && echo OK || echo revisar)"
  local cl cv; cl=$(curl -s -o /dev/null -w '%{http_code}' https://$IP/login || true); cv=$(curl -s -o /dev/null -w '%{http_code}' https://$IP/health/live || true)
  echo "  HTTPS /login: $cl · /health/live: $cv"; [ "$cl" = 200 ] && [ "$cv" = 200 ] || fallo=1
  for p in identidad-acceso donantes receptores inventario compatibilidad priorizacion-geografia transporte custodia alertas auditoria monitoreo documentos; do
    local code; code=$(curl -s -o /dev/null -w '%{http_code}' https://$IP/services/$p/health/ready || true); printf '  /services/%s/health/ready %s\n' $p "$code"; [ "$code" = 200 ] || fallo=1
  done
  # gcs.compose.yaml: solo cambian las etiquetas de imagen de los 26 servicios propios.
  python3 - $BK/gcs.compose.yaml.orig $OVR "$TAG" <<'PY' || fallo=1
import json, sys
a, b, tag = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), sys.argv[3]
cambiadas = [k for k in a["services"] if a["services"][k].get("image") != b["services"][k].get("image")]
for d in (a, b):
    for v in d["services"].values():
        v.pop("image", None)
ok = a == b and len(cambiadas) == 26 and "storage-init" not in cambiadas and "clamav" not in cambiadas
print(f"  gcs.compose.yaml: {len(cambiadas)} etiquetas cambiadas a {tag}; resto idéntico: {a == b}; storage-init y clamav intactos: {'storage-init' not in cambiadas and 'clamav' not in cambiadas}")
sys.exit(0 if ok else 1)
PY
  echo "  esquema: $(esquema) · columna client: $($PSQL -c "SELECT count(*) FROM information_schema.columns WHERE table_schema='red_house' AND table_name='web_session' AND column_name='client'")"
  [ "$(esquema)" = 22 ] || fallo=1
  huella_config $BK/config-despues.sha256
  # gcs.compose.yaml cambia a propósito (etiquetas); el resto de la configuración privada debe quedar igual.
  local cambio; cambio=$(diff <(grep -v gcs.compose.yaml $BK/config-antes.sha256) <(grep -v gcs.compose.yaml $BK/config-despues.sha256) | awk '/^[<>]/{print $3}' | sort -u | paste -sd' ' - || true)
  if [ -z "$cambio" ]; then echo "  configuración privada (state.json, web.json, apps/*.json, public.*): sin cambios"
  else echo "  FALLA: cambió la configuración privada: $cambio"; fallo=1; fi
  [ "${FALLO_PREVIO:-0}" = 0 ] || { echo "  FALLA: la prueba del token previo no pasó (ver arriba)"; fallo=1; }
  https_py completo || fallo=1
  echo "=== RESULTADO: $([ $fallo = 0 ] && echo PASA || echo FALLA) · $(t) UTC"
  return $fallo
}

# ================================================================================================
case $MODO in
verificar)
  plan_y_comprobaciones
  humo_vigentes
  ensayo_migracion
  pasos
  echo "=== verificar terminó sin cambiar nada · $(t) UTC"
  ;;

aplicar)
  trap al_fallar ERR
  # Si se cae la sesión SSH no debe morir a mitad del corte: se ignora SIGHUP y `tee -p` sigue
  # escribiendo el registro aunque se rompa la salida. Mejor aún: lanzarlo con systemd-run (ver RESULTADOS).
  trap '' HUP
  mkdir -p $BK/archivos $BK/ctx; chmod 700 $BK
  exec > >(tee -p -a $BK/aplicar.log) 2>&1
  plan_y_comprobaciones
  ESQ=$(esquema)
  case $ESQ in 21|22) ;; *) echo "Esquema $ESQ inesperado (21 o 22): no se sigue."; exit 1;; esac
  [ "$ESQ" = 22 ] && echo "  El esquema ya es 22: se reanuda (sin respaldo ni migración nuevos)."
  if [ "$ESQ" = 21 ]; then
    [ "$(sanos)" = "30 de 30" ] || { echo "No están los 30 sanos: no se sigue."; exit 1; }
    # backup.py --verify deja tres contenedores de restauración con volúmenes (el último ocupó ~0.45 GB de
    # PostgreSQL + ~0.35 GB de Mongo) más ~0.1 GB de volcados; las 14 imágenes son capas de KB.
    libre=$(df --output=avail -k / | tail -1); [ "$libre" -gt 2097152 ] || { echo "Menos de 2 GB libres: no se sigue."; exit 1; }
  fi

  FASE=respaldo-archivos; echo "=== a1. Respaldo de archivos $(t)"
  [ -f $BK/gcs.compose.yaml.orig ] || cp -p $OVR $BK/gcs.compose.yaml.orig
  [ -f $BK/config-antes.sha256 ] || huella_config $BK/config-antes.sha256
  [ -f $BK/ps-antes.txt ] || docker ps --format '{{.Names}} {{.ID}} {{.Image}}' | sort > $BK/ps-antes.txt
  [ -f $BK/imagenes-antes.txt ] || for s in $(servicios_imagen); do k=$s; case $s in web|bootstrap);; *) k=$s-a;; esac
      echo "$s $(imagen_actual $k) $(docker image inspect -f '{{.Id}}' "$(imagen_actual $k)")"; done > $BK/imagenes-antes.txt
  touch $BK/nuevos.txt
  for f in $F_HOST; do
    if [ -e $ROOT/$f ]; then [ -f $BK/archivos/$f.orig ] || { mkdir -p "$(dirname $BK/archivos/$f)"; cp -p $ROOT/$f $BK/archivos/$f.orig; }
    else grep -qxF "$f" $BK/nuevos.txt || echo "$f" >> $BK/nuevos.txt; fi
  done
  echo "  $(find $BK/archivos -name '*.orig' | wc -l) originales y $(wc -l < $BK/nuevos.txt) nuevos anotados"

  FASE=copia; echo "=== b. Copia a $ROOT $(t)"
  meta_host $F_HOST | while IFS='|' read -r f est own mode sha; do
    install -o "${own%:*}" -g "${own#*:}" -m "$mode" "$PAYLOAD/$f" "$ROOT/$f"
  done
  for f in $F_HOST; do [ "$(sha256sum $ROOT/$f | cut -d' ' -f1)" = "$(sha_esperado $f)" ] || { echo "  no coincide $f"; false; }; done
  echo "  $(echo $F_HOST | wc -w) archivos con el SHA-256 de 989f2e7"

  FASE=imagenes; echo "=== c. Imágenes derivadas $(t)"
  for s in $(servicios_imagen); do
    k=$s; case $s in web|bootstrap);; *) k=$s-a;; esac
    old=$(awk -v s=$s '$1==s{print $2}' $BK/imagenes-antes.txt); new=$(imagen_nueva $k)
    ctx=$BK/ctx/$s; mkdir -p $ctx; printf 'FROM %s\n' "$old" > $ctx/Dockerfile; n=0
    meta=$(meta_imagen "$old" $(archivos_de $s))   # asignación: si falla, salta la trampa
    esperado=""
    while IFS='|' read -r f est own mode sha; do
      n=$((n+1)); cp "$PAYLOAD/$f" $ctx/f$n
      printf 'COPY --chown=%s --chmod=%s f%s /app/%s\n' "$own" "$mode" $n "$f" >> $ctx/Dockerfile
      esperado+="$f|existe|$own|$mode|$(sha_esperado "$f")"$'\n'
    done <<< "$meta"
    [ $n = $(archivos_de $s | wc -w) ] || { echo "  $s: $n archivos leídos de $(archivos_de $s | wc -w)"; false; }
    DOCKER_BUILDKIT=1 docker build -q -t "$new" $ctx >/dev/null
    # La imagen nueva debe tener cada archivo con el SHA-256 de 989f2e7 y el dueño/modo del original.
    real=$(meta_imagen "$new" $(archivos_de $s))
    [ "$real"$'\n' = "$esperado" ] || { echo "  $new no quedó como se esperaba:"; diff <(echo "$real") <(printf '%s' "$esperado") || true; false; }
    hum=$(humo "$new" $s 2>&1) || { echo "  $new no pasa la prueba de humo:"; echo "$hum" | tail -5; false; }
    echo "  $new $(docker image inspect -f '{{.Id}}' $new | cut -c1-19) (de $old, $n archivos con SHA-256, dueño y modo correctos; ${hum##*$'\n'})"
  done
  python3 - "$OVR" "$TAG" <<'PY'
import json, sys
p, tag = sys.argv[1], sys.argv[2]
d = json.load(open(p))
for name, svc in d["services"].items():
    img = svc.get("image", "")
    if (img.startswith("redhouse/") or img.startswith("redhouse-web:")) and name != "storage-init":
        svc["image"] = img.split(":")[0] + ":" + tag
open(p, "w").write(json.dumps(d, indent=2) + "\n")
PY
  echo "  gcs.compose.yaml apunta a $TAG (storage-init y clamav sin cambio)"
  $COMPOSE --profile install config -q

  if [ "$ESQ" = 21 ]; then
    TOKEN_PREVIO=$(https_py crear || true); echo "  sesión previa de prueba: $([ -n "$TOKEN_PREVIO" ] && echo creada || echo 'no se pudo crear (se omite esa prueba)')"
    FASE=detenido; echo "=== a2. Respaldo verificado (aplicaciones detenidas desde aquí) $(t)"
    INICIO_CORTE=$SECONDS
    python3 $ROOT/deployment/backup.py --directory $ROOT/.local/compose --verify --leave-stopped --output $BK/respaldo.json | tee $BK/respaldo.stdout
    python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));assert d["backup"]=="passed" and d.get("restore")=="passed", d.get("restore");print("  respaldo:",d["backup"],"· restauración aislada:",d["restore"],"·",d["private_path"])' $BK/respaldo.json
    privado=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["private_path"])' $BK/respaldo.json)
    test -s "$privado/postgres.dump"
    echo "  disco libre después del respaldo: $(df -h --output=avail / | tail -1 | tr -d ' ') · respaldo: $(du -sh "$privado" | cut -f1)"
    # grep -c con || true: con 0 coincidencias grep sale con 1 (antes, dentro de $(...), eso disparaba la trampa).
    en_marcha=$(docker ps --format '{{.Names}}' | grep -c -v -E '^redhouse-parcial2-(postgres|mongodb|redis)-1$' || true)
    echo "  aplicaciones en marcha: $en_marcha (deben ser 0)"
    [ "$en_marcha" = 0 ]

    FASE=migracion; echo "=== d. Migración 22 $(t)"
    $COMPOSE --profile install run --rm --no-deps -T --entrypoint python bootstrap -c "$MIGRAR_PY" | tee $BK/migracion.json
    [ "$(esquema)" = 22 ]
  fi

  FASE=recreacion; echo "=== e. Recreación $(t)"
  $COMPOSE start gateway; $COMPOSE start clamav; esperar_clamav
  for s in $START_ORDER; do
    [ $s = documentos ] && esperar_clamav
    for r in b a; do recrear $s-$r; echo "  $s-$r $(t)"; done
  done
  recrear web; echo "  web $(t)"
  [ -n "${INICIO_CORTE:-}" ] && echo "  tiempo sin servicio (desde el respaldo hasta web sano): $((SECONDS - INICIO_CORTE)) s"
  docker ps --format '{{.Names}} {{.ID}} {{.Image}}' | sort > $BK/ps-despues.txt
  echo "--- sesión abierta antes de publicar (sin aplicación) contra los servicios nuevos"
  FALLO_PREVIO=0; TOKEN_PREVIO="${TOKEN_PREVIO:-}" https_py probar || FALLO_PREVIO=1

  FASE=revocacion; echo "=== f. Sesiones previas $(t)"
  REV="$COMPOSE --profile install run --rm --no-deps -T --entrypoint python bootstrap -m scripts.revocar_sesiones_sin_cliente --directory /run/install"
  $REV; $REV --aplicar
  quedan=$($REV | tee /dev/stderr | sed -n 's/^Sesiones vivas sin aplicación registrada: //p')
  [ "$quedan" = 0 ] || { echo "  Quedan $quedan sesiones vivas sin aplicación"; false; }

  verificacion_final
  ;;

revertir)
  [ -f $BK/gcs.compose.yaml.orig ] || { echo "No hay respaldo en $BK"; exit 1; }
  trap '' HUP
  exec > >(tee -p -a $BK/revertir.log) 2>&1
  echo "=== revertir $(t) UTC"
  restaurar_archivos
  # Si «aplicar» falló con todo detenido, gateway y ClamAV pueden estar parados: arrancarlos (no-op si corren).
  $COMPOSE start gateway || true; $COMPOSE start clamav || true; esperar_clamav || true
  # Orden: primero los servicios que no son Identidad (las imágenes viejas aceptan los tokens nuevos),
  # luego Identidad y al final web (la web vieja no manda la cabecera; con Identidad vieja no hace falta).
  for s in $START_ORDER; do [ $s = identidad-acceso ] && continue; for r in b a; do recrear $s-$r; echo "  $s-$r $(t)"; done; done
  for r in b a; do recrear identidad-acceso-$r; echo "  identidad-acceso-$r $(t)"; done
  recrear web; echo "  web $(t)"
  echo "--- sanos: $(sanos) · /login $(curl -s -o /dev/null -w '%{http_code}' https://$IP/login || true) · esquema $(esquema)"
  for p in identidad-acceso donantes receptores inventario compatibilidad priorizacion-geografia transporte custodia alertas auditoria monitoreo documentos; do
    printf '  /services/%s/health/ready %s\n' $p "$(curl -s -o /dev/null -w '%{http_code}' https://$IP/services/$p/health/ready || true)"
  done
  echo "La migración 22 se deja (aditiva; el código anterior ignora la columna y su readiness acepta 22 >= 21)."
  echo "Reversa SQL manual, solo si se retira el código para siempre: ver comentarios de shared_migrations/022.sql."
  echo "Las imágenes $TAG se conservan; las sesiones revocadas siguen revocadas (basta iniciar sesión)."
  ;;

*) echo "Modo desconocido: $MODO (verificar | aplicar | revertir)"; exit 2 ;;
esac
