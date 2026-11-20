# Guion: fallos pedidos en vivo

Este guion cubre las acciones de la consigna: detener un microservicio, revocar un token, desactivar Redis, provocar una
respuesta inválida, consultar un archivo inexistente, simular una sobrecarga, mostrar un intento sin permisos y explicar un
error en los logs. También cubre las del tercer parcial: MongoDB y PostgreSQL sin respuesta, servicio de archivos no
disponible y petición que excede el tiempo máximo.

Para cada caso se muestra que el sistema **detecta** el problema, lo **registra**, **informa** con un código claro, **no
corrompe datos** y **se recupera** al restablecer el servicio.

- **Ensayo local aprobado 11/11** el 18/11/2026, en una instalación desechable:
  [evidencia](../../evidencias/entrega-final/fallos-en-vivo-20261118/RESULTADOS.md) ·
  [bitácora](../../evidencias/entrega-final/fallos-en-vivo-20261118/demo.json).
- **Ensayo en la VM aprobado** el 18/11/2026 con el atajo `fallo.py`: los 12 casos, cada uno restablecido
  ([evidencia](../../evidencias/entrega-final/gcp-fallos-en-vivo-20261118/RESULTADOS.md)). Los comandos manuales de las
  secciones siguientes son equivalentes, pero el atajo es lo que se ensayó.

## Atajo en la VM: un comando por caso

Para la presentación en la nube basta con un comando, desde la terminal de la VM
(`gcloud compute ssh red-house --project=sistemas-integracion-01 --zone=me-central1-a`). El script es
[`deployment/gcp/fallo.py`](../../../deployment/gcp/fallo.py); solo usa Python estándar, se conecta a la propia VM, lee la
contraseña sintética de `state.json` y nunca la imprime. Cada caso imprime lo que pasó y un bloque **«Qué mostrar al
profesor»**.

```sh
F='sudo python3 /opt/redhouse/deployment/gcp/fallo.py'
$F                      # lista de casos
$F estado               # 30 contenedores y /health/ready de los 12 servicios
```

| Pedido del profesor | Provocar | Restablecer |
|---|---|---|
| Detener un microservicio | `$F microservicio` | `$F microservicio restablecer` |
| Revocar un token | `$F token` | termina solo |
| Desactivar temporalmente Redis | `$F redis` | `$F redis restablecer` |
| Provocar una respuesta inválida | `$F invalida` | termina solo |
| Consultar un archivo inexistente | `$F inexistente` | termina solo |
| Simular una sobrecarga | `$F sobrecarga` | termina solo (operator1 queda limitado ~60 s) |
| Mostrar un intento sin permisos | `$F permisos` | termina solo |
| Explicar un error en los logs | `$F logs` | termina solo |
| MongoDB no responde | `$F mongodb` | `$F mongodb restablecer` |
| PostgreSQL no responde | `$F postgres` | `$F postgres restablecer` |
| Servicio de archivos no disponible | `$F archivos` | `$F archivos restablecer` |
| Petición que excede el tiempo máximo | `$F tiempo` | termina solo (Identidad se congela unos segundos) |
| Si algo quedó a medias | — | `$F todo restablecer` (reanuda y corre `start.py`) |

Mientras Redis, MongoDB o PostgreSQL estén caídos, todo el equipo ve el efecto: restablecer en menos de un minuto. Las
secciones siguientes explican cada caso con detalle y los comandos manuales equivalentes.

## 0. Preparación

### Local (instalación desechable, nunca el laboratorio restaurado)

```sh
git clone --branch entrega-final <repositorio> /private/tmp/rh-demo && cd /private/tmp/rh-demo
bash install.sh && bash start.sh          # 12/12 listos, portal en http://127.0.0.1:5050
alias rh='apps/services/.venv/bin/python documentation/evidencias/entrega-final/fallos-en-vivo-20261118/demo_fallos_en_vivo.py --repo .'
rh estado                                  # /health/ready de los 12 servicios
```

- `rh caso <nombre>` corre un caso suelto. Primero crea un donante testigo y al final comprueba la integridad y busca la
  línea de log de cada error. Imprime un renglón JSON por paso, con hora, código HTTP, código de error, segundos y
  `correlation_id`. La contraseña sintética se lee de `.local/runtime/state.json` y nunca se imprime.
- `rh demo --out demo.json` corre todo en unos 2 minutos.
- Al terminar: `bash stop.sh` y borrar `/private/tmp/rh-demo`.

### VM de GCP

**En la VM**, por SSH (`gcloud compute ssh red-house --project=sistemas-integracion-01 --zone=me-central1-a`):

```sh
DC='sudo docker compose -f /opt/redhouse/compose.yaml'
$DC ps --format 'table {{.Service}}\t{{.Status}}'      # 29 contenedores; las API dicen (healthy)
```

**En la laptop del presentador** (Bash). No proyectar mientras se escribe la contraseña:

```sh
B=https://34.18.186.116/services
read -rs RH_PASS     # contraseña sintética de la VM: registro privado /opt/redhouse/.local/compose/state.json
# Aplicación según el perfil: donor y transport entran como mobile; el resto, como web.
login() { printf '{"username":"%s","password":"%s"}' "$1" "$RH_PASS" | curl -sS -m 10 -H 'Content-Type: application/json' -H "X-RedHouse-Client: $(case "$1" in donor*|transport*) echo mobile;; *) echo web;; esac)" --data-binary @- "$B/identidad-acceso/api/v1/auth/login"; }
tok()   { login "$1" | python3 -c 'import sys,json; print(json.load(sys.stdin)["data"]["access_token"])'; }
api()   { local t="$1"; shift; curl -sS -m 15 -H "Authorization: Bearer $t" -H "X-Correlation-ID: $(uuidgen | tr A-Z a-z)" -D /tmp/rh-h -w '\nHTTP %{http_code} en %{time_total} s\n' "$@"; grep -i x-correlation-id /tmp/rh-h; }
OP1=$(tok operator1); OP2=$(tok operator2); DON=$(tok donor1); AUD=$(tok auditor1)
```

- Confirmar en `state.json` de la VM que esas cuentas existen. ADMIN, MEDICAL y COORDINATOR exigen MFA; por eso se usan
  operador, donante, transportista y auditor.
- **En la VM cada API tiene dos réplicas (`-a` y `-b`) detrás de Nginx.** Detener una sola no interrumpe nada, porque Nginx
  reintenta en la otra. Para «detener un microservicio» hay que detener **ambas**.
- **Nunca** usar `docker compose up` ni `down` en la demostración. `up` con solo el archivo base pierde la entrada HTTPS
  (`public.compose.yaml`); `down -v` borra los volúmenes. Solo `stop`, `start`, `pause` y `unpause`.
- La VM es compartida: mientras Redis o PostgreSQL estén caídos, **todos** ven el portal en 503. Mantener cada caída menos
  de un minuto.
- Testigo sin escribir datos: antes de empezar, anotar un registro existente y verlo de nuevo al final. Por ejemplo,
  `api $OP1 "$B/donantes/api/v1/donors?page_size=1"`, guardar `id`, `version` y `updated_at`, y al final comprobar con
  `api $OP1 "$B/donantes/api/v1/donors/<id>"` que no cambiaron.

## Resumen

| # | Pedido | Local | VM (en la VM salvo que se indique) | Se debe ver | Restablecer |
|---|---|---|---|---|---|
| 1 | Detener un microservicio | `bash components.sh detener inventario` | `$DC stop inventario-a inventario-b` | Monitoreo lo marca `down`; los demás siguen; el portal sigue | `components.sh reiniciar inventario` / `$DC start inventario-a inventario-b` |
| 2 | Revocar un token | `rh caso b_revocar_token` | Laptop: `/auth/revoke` o `/auth/logout` | 401 `unauthorized` al reutilizarlo | No aplica |
| 3 | Desactivar Redis | `rh detener-base redis` | `$DC stop redis` | 503 `redis_unavailable`; `ready` 503; `live` 200 | `bash components.sh bases` / `$DC start redis` |
| 4 | Respuesta inválida | `pytest tests/test_dependency_timeout_unit.py` | No se provoca en la VM | 503 `dependency_unavailable` | No aplica |
| 5 | Archivo inexistente | `rh caso g_archivo_inexistente` | Laptop: `GET …/documentos/api/v1/documents/<uuid>` | 404 `not_found` | No aplica |
| 6 | Sobrecarga | `rh caso h_sobrecarga` | Laptop: ráfaga de 240 con `operator1` | 429 `rate_limit` y `Retry-After: 60`; otra cuenta en 200 | Esperar a la siguiente ventana (≤ 60 s) |
| 7 | Sin permisos | `rh caso i_sin_permisos` | Laptop: `operator2` sobre un recurso del Hospital 1 | 403 `forbidden`, auditado | No aplica |
| 8 | Error en los logs | `grep -i <id> .local/runtime/*.log` | `$DC logs --timestamps <svc>-a <svc>-b \| grep -i <id>` | Línea JSON con ruta, estado, ms y código | No aplica |
| 9 | MongoDB no responde | `rh detener-base mongodb` | `$DC stop mongodb` | El negocio sigue; auditoría en la bandeja de salida; 503 `mongodb_unavailable` | `components.sh bases` / `$DC start mongodb` |
| 10 | PostgreSQL no responde | `rh detener-base postgres` | `$DC stop postgres` | `live` 200, `ready` 503, 503 `database_unavailable` | `components.sh bases` / `$DC start postgres` |
| 11 | Archivos no disponibles | `bash components.sh detener documentos` | `$DC stop documentos-a documentos-b` | La API cae; el portal sigue; `/health/storage` 503 si falta el almacén | `reiniciar documentos` / `$DC start …` |
| 12 | Tiempo máximo excedido | `rh pausar identidad_acceso` | `$DC pause identidad-acceso-a identidad-acceso-b` | 503 `dependency_unavailable` en ~3 s | `rh reanudar …` / `$DC unpause …` |

## 1. Detener un microservicio

- **Local:** `bash components.sh detener inventario`, o todo el caso con `rh caso a_microservicio_detenido`.
- **VM:**
  1. Primero `$DC stop inventario-a`. Decir: «con una réplica no pasa nada». Desde la laptop,
     `api $OP1 "$B/inventario/api/v1/resources?page_size=1"` responde 200.
  2. Luego `$DC stop inventario-b`.
- **Qué decir:** cada microservicio es independiente. Si uno cae, los demás siguen. Monitoreo lo detecta en su sondeo (cada
  30 s) y lo registra. Al volver, recupera el estado.
- **Qué se debe ver:**
  - La API de Inventario deja de responder: conexión rechazada en local; 502/503 de Nginx en la VM.
  - `api $OP1 "$B/donantes/api/v1/campaigns"` sigue en 200.
  - El portal web sigue mostrando `/inventario`, porque corre en modo monolito con las apps de dominio embebidas. Decirlo
    así, sin presentarlo como recuperación.
  - Monitoreo (`api $AUD "$B/monitoreo/api/v1/status"`) muestra `inventario` `down`, `unreachable_or_invalid_response`.
  - Ensayo local: detectado 1.6 s después de detenerlo; `up` 9 s después de reiniciarlo.
- **Restablecer:**
  - Local: `bash components.sh reiniciar inventario` (1.8 s).
  - VM: `$DC start inventario-a inventario-b` y esperar `(healthy)` en `$DC ps` (≈ 30–45 s por el `start_period`).
  - Registrar una unidad o repetir la consulta: 200/201.

## 2. Revocar un token

- **Local:** `rh caso b_revocar_token`.
- **VM (laptop):**

```sh
J=$(login transport1); ACC=$(python3 -c 'import sys,json;print(json.loads(sys.argv[1])["data"]["access_token"])' "$J"); REF=$(python3 -c 'import sys,json;print(json.loads(sys.argv[1])["data"]["refresh_token"])' "$J"); unset J
api $ACC "$B/identidad-acceso/api/v1/auth/me"                                   # 200
printf '{"refresh_token":"%s"}' "$REF" | curl -sS -H 'Content-Type: application/json' --data-binary @- "$B/identidad-acceso/api/v1/auth/revoke"   # {"revoked": true}
api $ACC "$B/identidad-acceso/api/v1/auth/me"                                   # 401 unauthorized
```

  Variante con cierre de sesión, con un token nuevo: `api $ACC -X POST -H "Idempotency-Key: $(uuidgen)"
  "$B/identidad-acceso/api/v1/auth/logout"` y reutilizar el token → 401. Sin `Idempotency-Key` responde 400
  `idempotency_required`; comprobado en local.
- **Qué decir:**
  - El JWT sigue firmado y sin vencer, pero cada servicio consulta en Redis la sesión y la lista de revocados. La revocación
    surte efecto de inmediato en los 12 servicios, sin esperar a que el token expire.
  - Se revoca la familia de esa sesión, no todas las sesiones del usuario.
- **Qué se debe ver:**
  - 401 `unauthorized` al reutilizar el token, y también al renovar con el token de renovación revocado.
  - Ensayo local: otra sesión del mismo usuario siguió en 200, y el token revocado **siguió revocado tras reiniciar Redis**.

## 3. Desactivar temporalmente Redis

- **Local:** `rh detener-base redis`, o el caso completo con `rh caso c_redis`.
- **VM:** `$DC stop redis`.
- **Qué decir:** Redis guarda sesiones, revocaciones y cuotas. Sin Redis no se puede verificar quién es quién. Por eso el
  sistema **falla cerrado**: responde 503 controlado. No deja pasar sin verificar ni se queda colgado.
- **Qué se debe ver:**
  - `api $OP1 "$B/donantes/api/v1/campaigns"` → **503** `redis_unavailable`, rápido (ensayo local: ≤ 15 ms).
  - El inicio de sesión también da 503 `redis_unavailable`.
  - `curl -s $B/donantes/health/live` → 200 y `/health/ready` → 503, con `redis: down`. En la VM, si la entrada pública no
    expone `ready`, usar `$DC ps`: las API pasan a `(unhealthy)` en ≤ 75 s.
  - El portal muestra «No fue posible completar la operación» (503) con una «Referencia».
- **Restablecer:**
  - Local: `bash components.sh bases` (1.3 s); `rh estado` da 12/12.
  - VM: `$DC start redis`.
  - En local, **el mismo token vuelve a servir**, porque Redis persiste con AOF. En la VM depende de la configuración
    privada de Redis: si pide iniciar sesión otra vez, explicarlo como cierre seguro.
- **Integridad:** el alta intentada durante la caída no existe (0); el testigo no cambió.

## 4. Provocar una respuesta inválida

- **No hay forma limpia de provocarla en vivo sin cambiar código o configuración.** Se muestra la prueba automatizada,
  que levanta servidores HTTP reales que responden HTML, HTML 502, una lista, JSON sin `meta` o sin `data`, JSON truncado,
  o que cierran la conexión:

```sh
cd apps/services && <python con pytest> -m pytest -v tests/test_dependency_timeout_unit.py      # 11 passed
```

  En la instalación nueva no viene pytest; se usó el entorno del repositorio de trabajo. Ver
  [pytest_timeout.txt](../../evidencias/entrega-final/fallos-en-vivo-20261118/pytest_timeout.txt).
- **Qué decir:** el cliente interno (`redhouse/client.py`) valida el tipo de contenido y el sobre JSON (`data` y `meta`).
  Cualquier cosa distinta se convierte en 503 `dependency_unavailable` y no se propaga como 500. Un error legítimo de la
  dependencia (por ejemplo 409) conserva su código.
- **En la VM:** lo más cercano es el caso 1. Con las dos réplicas detenidas, la pasarela interna devuelve un 502 en HTML,
  que es una respuesta inválida para el cliente. El servicio que depende de ella la traduce a 503 `dependency_unavailable`.

## 5. Consultar un archivo inexistente

- **Local:** `rh caso g_archivo_inexistente`.
- **VM (laptop):**

```sh
api $OP1 "$B/documentos/api/v1/documents/$(uuidgen | tr A-Z a-z)"              # 404 not_found
api $OP1 "$B/documentos/api/v1/files/$(uuidgen | tr A-Z a-z)/download"         # 404 not_found
api $OP1 "$B/documentos/api/v1/documents/no-es-uuid"                           # 400 validation
```

- **Qué decir:** el identificador se valida antes de consultar. Si es válido pero no existe, se responde 404 con el sobre
  estándar y sin revelar rutas internas del almacén.

## 6. Simular una sobrecarga

- **Local:** `rh caso h_sobrecarga`. Hace 240 peticiones de `operator1`, 24 en paralelo; dura unos 30 s porque espera la
  ventana siguiente.
- **VM (laptop)**, solo con peticiones **autenticadas**. Las anónimas comparten cuota por IP y podrían bloquear el inicio de
  sesión de todos durante un minuto:

```sh
seq 240 | xargs -P 24 -I{} curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $OP1" "$B/donantes/api/v1/campaigns?page_size=1" | sort | uniq -c
api $OP2 "$B/donantes/api/v1/campaigns?page_size=1"                            # otra cuenta: 200
api $OP1 "$B/donantes/api/v1/campaigns?page_size=1"                            # 429 rate_limit, Retry-After: 60
```

- **Qué decir:** la cuota es de 180 peticiones por minuto por cuenta y por servicio, compartida entre réplicas porque vive
  en Redis. Quien abusa recibe 429 con `Retry-After`, y los demás siguen atendidos.
- **Qué se debe ver:**
  - Ensayo local: 160 respuestas 200 y 80 respuestas 429 en 0.94 s; latencia máxima 0.14 s.
  - Durante la ráfaga, `operator2` y `/health/ready` siguieron en 200.
  - `operator1` volvió a ser atendido al cambiar la ventana (25 s).
  - En la VM, la entrada pública puede tener su propio límite. Si aparece un código distinto de 429, revisar quién lo emitió
    con el log (caso 8).

## 7. Mostrar un intento sin permisos

- **Local:** `rh caso i_sin_permisos`.
- **VM (laptop):** se necesita el `id` de un donante del Hospital 1, por ejemplo el testigo.

```sh
api $OP2 "$B/donantes/api/v1/donors/<id_hospital_1>"                           # 403 forbidden (otra institución)
api $DON -X POST -H 'Content-Type: application/json' -H "Idempotency-Key: $(uuidgen)" -d '{"folio":"DEMO-PERM","kind":"BLOOD","component":"RBC","blood_group":"O-","expires_at":"2030-01-01T00:00:00Z"}' "$B/inventario/api/v1/resources"   # 403: rol sin permiso
curl -s -o /dev/null -w '%{http_code}\n' "$B/donantes/api/v1/donors"            # 401 sin token
```

- **Qué decir:** hay dos capas, rol (qué puede hacer el perfil) y ámbito (de qué institución es el recurso). El rechazo
  entre instituciones queda en la auditoría con el mismo `correlation_id`:
  `api $AUD "$B/auditoria/api/v1/events?categories=ALL&correlation_id=<id>"` muestra `REJECTED`.
- **Ojo:** `REJECTED` aparece en la categoría técnica, no en la vista predeterminada; hay que filtrar con `categories=ALL`.
  El 403 por rol queda solo en el log del servicio.

## 8. Explicar un error en los logs

- **Cómo obtener el identificador:** cada respuesta trae `X-Correlation-ID` en la cabecera y `meta.correlation_id` en el
  cuerpo. `api` lo imprime, y en la VM además lo envía.
- **Local:** `grep -i <correlation_id> .local/runtime/*.log`. Hay un archivo por API (`<servicio>.log`), por worker
  (`<servicio>-worker.log`) y por base (`postgres.log`, `redis.log`, `mongodb.log`).
- **VM:** buscar en **las dos réplicas**, porque cualquiera pudo atender:
  `$DC logs --since 15m --timestamps --no-log-prefix inventario-a inventario-b | grep -i <correlation_id>`.
- **Ejemplo del ensayo**, el caso 12:

```text
{"service": "inventario", "correlation_id": "…", "method": "POST", "route": "/api/v1/resources", "status": 503, "elapsed_ms": 3031.8, "error": "dependency_unavailable"}
```

- **Qué decir:**
  - El servicio, la ruta y el estado dicen qué falló; `error` dice por qué. Aquí, una dependencia no respondió.
  - `elapsed_ms` prueba que se cortó en el límite de 3 s y no se quedó colgado.
  - La línea no trae cuerpo, token ni datos personales.
  - Para las bases: `worker_failure service=<x> exception_type=APIError` en los workers y
    `FATAL: terminating connection due to administrator command` en `postgres.log`.
- **Límite conocido:** la «Referencia» de la página de error del portal **no aparece en los logs** (`web.log` vacío en el
  ensayo). Para este punto, usar una llamada a la API, no el portal.

## 9. MongoDB no responde

- **Local:** `rh detener-base mongodb`, o `rh caso d_mongodb`.
- **VM:** `$DC stop mongodb`.
- **Qué decir:**
  - MongoDB guarda la proyección documental de auditoría y el monitoreo; el negocio vive en PostgreSQL. Por eso las
    operaciones siguen.
  - La auditoría no se pierde: queda en la **bandeja de salida** (outbox) de PostgreSQL y se reproduce al volver Mongo, sin
    duplicarse (el `_id` es el id del evento).
- **Qué se debe ver:**
  - `/health/ready` da 503 solo en transporte, custodia, auditoría y monitoreo; los demás y el portal siguen en 200.
  - Un alta de negocio da 201.
  - `api $AUD "$B/auditoria/api/v1/events?page_size=5"` → 200 (bitácora SQL).
  - `api $AUD "$B/auditoria/api/v1/documentary-events"` → **503** `mongodb_unavailable`.
  - Pendientes en la bandeja de salida (en la VM):
    `$DC exec -T postgres psql -U rh_bootstrap -d red_house -Atc "SET search_path=access_auditoria,pg_catalog; SELECT count(*) FROM outbox WHERE target='mongodb' AND delivered_at IS NULL"`.
    En el ensayo local fueron 35.
- **Restablecer:**
  - Local: `bash components.sh bases`.
  - VM: `$DC start mongodb`.
  - La bandeja de salida llega a 0 (local: ≤ 2 s) y `documentary-events` vuelve a 200 con más eventos (899 → 936). El
    evento del alta quedó **una sola vez**.

## 10. PostgreSQL no responde

- **Local:** `rh detener-base postgres` (apagado rápido), o `rh caso e_postgresql`.
- **VM:** `$DC stop postgres`. La imagen oficial se detiene con SIGINT, que es apagado rápido.
- **Qué decir:** el proceso sigue vivo (`live` 200) pero no está listo (`ready` 503). El orquestador o el balanceador sabe
  que no debe enviarle tráfico. Las escrituras se rechazan completas, sin quedar a medias.
- **Qué se debe ver:**
  - `curl -s $B/donantes/health/live` → 200 y `/health/database` → 503.
  - `api $OP1 "$B/donantes/api/v1/campaigns"` → **503** `database_unavailable` (≤ 15 ms).
  - El inicio de sesión da 503 y el portal muestra la página 503.
  - En los logs de los workers aparece `worker_failure` (15 en 12 s en el ensayo).
- **Restablecer:**
  - Local: `bash components.sh bases`; 12/12 `ready` en 0.2 s.
  - VM: `$DC start postgres`; esperar `(healthy)`.
  - La misma lectura y el portal, con la misma sesión, vuelven a 200.
  - El alta intentada durante la caída no existe.

## 11. El servicio de archivos no está disponible

- **Local:** `bash components.sh detener documentos`, o `rh caso j_archivos_no_disponibles`. Ese caso también deja el
  almacén privado sin permisos un instante (`chmod 000 .local/runtime/private-files` y luego `chmod 700`).
- **VM:** `$DC stop documentos-a documentos-b`. No tocar los permisos del volumen en la VM.
- **Qué decir:**
  - Documentos es un servicio aparte. Si cae, el resto sigue.
  - Si lo que falla es el almacenamiento y no el proceso, Documentos lo detecta en `/health/storage` y deja de declararse
    listo. Así nadie intenta subir o descargar archivos a un almacén roto.
- **Qué se debe ver:**
  - La API `/services/documentos/...` no responde: 502/503 de Nginx en la VM, conexión rechazada en local.
  - Los demás servicios siguen en 200.
  - El portal sigue mostrando `/documentos`, porque corre en modo monolito.
  - Con el almacén inaccesible, `GET /health/storage` responde 503 y `ready` 503 (`storage` down).
- **Restablecer:**
  - Local: `bash components.sh reiniciar documentos` y `/health/storage` `up` (`local`).
  - VM: `$DC start documentos-a documentos-b`.

## 12. Una petición excede el tiempo máximo

- **Local:** `rh pausar identidad_acceso`, o `rh caso f_tiempo_agotado`. El proceso queda congelado: acepta conexiones y
  no responde.
- **VM:** `$DC pause identidad-acceso-a identidad-acceso-b`. **Reanudar en menos de 30 s.** El portal no se afecta porque
  usa la identidad embebida.
- **Provocar la petición** (laptop): un alta de inventario con una ubicación ficticia, que obliga a Inventario a consultar
  Identidad.

```sh
api $OP1 -X POST -H 'Content-Type: application/json' -H "Idempotency-Key: $(uuidgen)" -d "{\"folio\":\"DEMO-TO-$RANDOM\",\"kind\":\"BLOOD\",\"component\":\"RBC\",\"blood_group\":\"O-\",\"expires_at\":\"2030-01-01T00:00:00Z\",\"location_id\":\"$(uuidgen | tr A-Z a-z)\"}" "$B/inventario/api/v1/resources"
```

- **Qué decir:** las llamadas entre servicios tienen 1 s para conectar y 3 s para leer. Si se excede, se corta y se responde
  503 `dependency_unavailable`. Nunca se deja al usuario esperando indefinidamente.
- **Qué se debe ver:**
  - **503** `dependency_unavailable` en ~3 s (local: 3.05 s).
  - Una alta sin ubicación da 201, porque no depende de Identidad.
  - No hay que llamar directamente a la API pausada desde la laptop: el cliente esperaría hasta su propio límite.
- **Restablecer:**
  - Local: `rh reanudar identidad_acceso`.
  - VM: `$DC unpause identidad-acceso-a identidad-acceso-b`.
  - La misma petición responde 404 `not_found`, porque llegó a Identidad y la ubicación no existe. No se creó ninguna unidad
    con ese folio.

## Cierre de la demostración

1. Comprobar que todo está listo: `rh estado` (12×200) o `$DC ps` (todo `(healthy)`).
2. Comprobar el testigo anotado al inicio: mismo `version` y `updated_at`.
3. **No hacer** en la presentación: `docker compose up` o `down`; `restore.py`; `backup.py`; reiniciar la VM; ráfagas sin
   token.
