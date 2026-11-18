# Instalación desde un clon limpio — 18/11/2026 (UTC)

Resultado global: **FAIL de la ruta documentada sin intervención; PASS funcional tras dos correcciones manuales de configuración**.

> **Actualización 18/11:** D1 y D2 quedaron corregidos en el código y una reinstalación desde copia limpia pasó sin intervención manual; ver [pruebas de fallas](../fallos-consigna-20261118/RESULTADOS.md#3-defecto-corregido-en-este-bloque-clon-limpio).
Ventana: 2026-11-18 03:02–03:33 UTC (17/11 21:02–21:33 CST). Equipo: Mac M1 arm64, 8 GB RAM; Docker Desktop
`desktop-linux` con 3.825 GiB y 8 CPU, compartido con contenedores de otros proyectos.

## Revisión probada

| Dato | Valor |
|---|---|
| Origen | `git clone --branch entrega-final https://github.com/victor-berlanga/Red-House.git` (clon nuevo, no copia del checkout de trabajo) |
| `git rev-parse HEAD` del clon | `9918724ad2205d6b4d72b41126f259b7e18234cc` |
| HEAD remoto al clonar (`git ls-remote`) | `9918724ad2205d6b4d72b41126f259b7e18234cc` (coincide) |
| HEAD remoto al cerrar | `2f6fe7867e7261de3e0ecab1405c83a1f1f4fda6`; solo cambia `Registro_incidencias.md` y `Matriz.md` (sin código ni despliegue) |
| Estado del clon al terminar | `git status --porcelain --untracked-files=all` vacío: la instalación no modificó archivos versionados |

Se probaron las dos rutas documentadas, en el mismo clon y con datos nuevos: **A**, ejecución local de la raíz
(`install.sh`/`start.sh`/`components.sh`/`stop.sh`, [README](../../../../README.md)); **B**, Compose aislado
([deployment/README.md](../../../../deployment/README.md)) siguiendo el plan preparado del 17/11 (proyecto, etiqueta de imagen
y configuración propios). No se usó el fixture ni el laboratorio `.local/rhlab`; no se tocó GCP.

## A. Ruta local de la raíz (sin Docker)

Dependencias del sistema ya presentes (PostgreSQL 14.25, Redis, MongoDB 8.0 de Homebrew; Python 3.12.15); no se instalaron
paquetes del sistema. Directorio de datos: `.local/runtime` del clon, puertos libres asignados por el instalador.

| Paso | Comando | Tiempo | Resultado |
|---|---|---|---|
| A1 | `bash install.sh` | 41.7 s | **PASS**: dos venv, PostgreSQL/Redis/MongoDB inicializados, 2 instituciones y 14 cuentas ficticias nuevas |
| A2 | `bash start.sh` | 9.5 s | **FAIL** (salida 1): `documentos` API y worker terminan con `ModuleNotFoundError: No module named 'google'`; el portal no llega a iniciarse |
| A2' | Corrección 1 (ver D1) y `bash start.sh` | 58.7 s | **FAIL** (salida 1): `Procesos iniciados pero sin readiness: documentos`; `/health/ready` = 503, `storage: down` |
| A2'' | Corrección 2 (ver D2), `bash components.sh reiniciar documentos` y `reiniciar web` | — | PASS |
| A3 | `bash components.sh estado` | 1.3 s | **PASS** tras correcciones: 12/12 servicios `200 up` y portal `200` |
| A4 | Humo (cuenta nueva `operator1`, ver C) | — | **PASS** |
| A5 | `bash stop.sh` | 6.3 s | **PASS**: 0 procesos del clon; `estado` muestra 12 `down` y portal `down` |
| A6 | Reinicio sin reinicialización: `bash start.sh`, humo y `bash stop.sh` | 9.6 s | **PASS**: 13 componentes arriba, login otra vez correcto; la respuesta XML de instituciones es idéntica salvo `correlation_id` |

Recursos de la ruta A: 28 procesos con 430 MiB de RSS en total, según `ps`; 77 MiB de datos en `.local`, y 180 + 193 MiB en
los venv.

## B. Compose aislado (plan del 17/11)

Variables: `COMPOSE_PROJECT_NAME=redhouse-clean-20261118`, `REDHOUSE_TAG=clean-20261118`,
`REDHOUSE_COMPOSE_DIR=<clon>/.local/compose`; override privado `public.compose.yaml` que solo cambia la etiqueta de
`mongodb` (como `run.py` del plan). Puertos 6050 y 6101–6112 libres antes de empezar. Las imágenes base de las aplicaciones
reutilizaron capas del caché BuildKit del equipo; sí se descargaron `postgres:14-bookworm`, `redis:7.4-bookworm` y
`nginx:1.28-alpine`.

| Paso | Comando | Tiempo | Resultado |
|---|---|---|---|
| B1 | `python3 deployment/prepare.py` | <1 s | PASS |
| B2 | `docker compose --profile install --parallel 2 build bootstrap mongodb` | 90 s | PASS |
| B3 | `docker compose up -d --wait postgres redis mongodb` | 33 s | PASS (3 healthy) |
| B4 | `docker compose --profile install run --rm bootstrap` | 4 s | PASS: «Base compartida, ACL, claves y 14 cuentas ficticias creadas» |
| B5 | `docker compose --parallel 2 build` | 9 s | PASS: 13 imágenes `redhouse/*:clean-20261118` |
| B6 | `python3 deployment/start.py` | 184 s | **FAIL**: `documentos-a/b` unhealthy, `storage: down` (D2) |
| B6' | Corrección D2 en `apps/documentos.json` y `up -d --wait --no-deps --force-recreate documentos-a documentos-b` | 33 s | PASS (2 healthy) |
| B6'' | `python3 deployment/start.py` (repetido) | 266 s | **FAIL por límite de memoria** (D3): falla `up --wait monitoreo-a monitoreo-b`; quedan 24 healthy, 4 unhealthy y la web sin iniciar |
| B7 | Modo reducido: `docker compose stop` de las 12 réplicas `-b` y `up -d --wait --no-deps web` | 98 + 15 s | PASS: 17 healthy (3 bases, gateway, 12 réplicas `-a`, web) |
| B8 | Humo por gateway 6101–6112 y portal 6050 (ver C) | — | **PASS** |
| B9 | Oráculos antes del reinicio: esquema 21, 14 `user_account`, 2 `institution`, 4 volúmenes e ID de contenedor/imagen | — | Registrados |
| B10 | `docker compose stop` y arranque reducido en el orden de `start.py`, solo `-a` | 11 + 97 s | PASS |
| B11 | Oráculos después del reinicio | — | **PASS**: idénticos (`diff` vacío), con los mismos ID de contenedor e imagen; humo otra vez PASS y XML igual salvo `correlation_id` |
| B12 | `docker compose stop` | 4 s | PASS: 0 contenedores activos del proyecto |

**El Compose completo de 29 servicios duraderos no quedó sano dentro de 3.825 GiB.** Este ensayo no demuestra las dos
réplicas por API en este equipo. B7–B11 demuestran la instalación con una réplica por API, un modo que la guía no documenta
como perfil.

## C. Comprobaciones con datos nuevos

Mismo script de humo en A y B, con datos que creó la instalación. Las credenciales se leyeron de `state.json` privado y
nunca se imprimieron.

| Comprobación | A (local) | B (Compose, reducido) |
|---|---|---|
| `/health/ready` de las 12 API | 12 × 200 `up` | 12 × 200 `up` (gateway) |
| Swagger `/docs/` | 12 × 200 con Swagger UI | 12 × 200 con Swagger UI |
| `/openapi.json` | 12 × 200, OpenAPI 3.1.0 (56/27/14/40/22/17/35/2/10/13/3/12 rutas) | idéntico |
| Portal `/` | 200, 6329 bytes | 200, 6329 bytes (6050) |
| Login `POST /api/v1/auth/login`, cuenta `operator1` (OPERATOR) creada por la instalación | 200, `access_token` + `refresh_token` | 200 |
| `GET /api/v1/auth/me` JSON | 200, `operator1`/`OPERATOR` | 200 |
| Lectura JSON `GET /api/v1/institutions` | 200 `application/json`, 2 instituciones | 200, 2 |
| Lectura XML `GET /api/v1/institutions` | 200 `application/xml`; `validate_response.py identidad_acceso institutions` válido | 200; válido |
| Lectura XML `GET /api/v1/resources` (Inventario) | 200; `validate_response.py inventario resources_list` válido (0 recursos, instalación nueva) | 200; válido |

Login por formulario del portal y flujo transaccional no ejecutados. Siguiendo el plan, no se corrió `verify.py`. Tampoco
se usó `check_clean_clone.py`: escribe sobre `documentation/evidencias/segundo-parcial/clean-clone.json`, ejecuta
`verify.py --phase smoke` y depende de `start.py`, que falla por D2 y D3. Sus pasos de instalación se ejecutaron uno por uno
en B1–B6.

## D. Defectos y límites

**D1. Falta `google-cloud-storage` en el venv local de servicios (afecta A).** `scripts/manage.py` instala
`apps/services/requirements.txt`, pero `ms_documentos/local_objects.py` importa `google.api_core` al cargar el módulo. Ese
paquete solo viene en `requirements-storage.txt`, que el Dockerfile sí instala. El venv del checkout de trabajo ya lo tenía
y ocultaba el fallo. Corrección manual aplicada (solo en el venv ignorado del clon):
`apps/services/.venv/bin/python -m pip install -r apps/services/requirements-storage.txt`. Propuesta: en
`scripts/manage.py`, `ensure_python()`, usar `requirements-storage.txt` para `SERVICES_ROOT`, que ya incluye
`-r requirements.txt`. Otra opción es diferir el import de `google.api_core` en `local_objects.py` al uso de GCS.

**D2. Una instalación nueva deja Documentos sin almacenamiento (afecta A y B).** Ni `provision.py` (local) ni
`bootstrap.py` (Compose) escriben `STORAGE_PROVIDER`/`STORAGE_LOCAL_ROOT` en `documentos.json`. Por eso `/health/ready`
responde 503 con `storage: down`, y `start.sh`/`start.py` terminan con error, aunque `Instalacion_y_operacion.md` describe el
almacenamiento local privado como predeterminado. El paso manual solo aparece en `apps/services/ms_documentos/README.md`,
indicado para instalaciones existentes. Correcciones aplicadas:
- A: `python3 deployment/configure_local_storage.py --config <runtime>/documentos.json --directory <runtime>/private-files --origin https://127.0.0.1:5050`.
  La herramienta rechaza el origen real del portal local, `http://127.0.0.1:5050`, porque exige HTTPS.
- B: escribir `STORAGE_PROVIDER=local`, `STORAGE_LOCAL_ROOT=/var/lib/redhouse-private` y `STORAGE_PUBLIC_BASE_URL=https://127.0.0.1:6050` en `.local/compose/apps/documentos.json`, y recrear `documentos-a/b`.

Propuesta: que `provision.py` cree `<directory>/private-files` con modo 0700 y escriba `STORAGE_PROVIDER=local` y
`STORAGE_LOCAL_ROOT`. Que `bootstrap.py` escriba `/var/lib/redhouse-private`. Que el origen público acepte `http://127.0.0.1`
en loopback o lo tome de `web_url`. Además, el paso debe documentarse en el README raíz y en `deployment/README.md`.

**D3. Límite de memoria de Docker Desktop (B, no es defecto del código).** Con el stack completo, los 28 contenedores del
proyecto sumaban 2504 MiB y los de otros proyectos 253 MiB. La VM tenía 66 MB libres, `MemAvailable` de 427 MiB, swap de
1 GiB agotado (`SwapFree` 128 kB), presión de memoria `full avg300=9.79` y carga de 36. PostgreSQL entró dos veces en
recuperación. A las 03:17:28 UTC un backend terminó con código 2 y después el colector de estadísticas recibió SIGKILL. A
las 03:19:55 UTC otro backend terminó con `signal 13`. Las réplicas `donantes-b`, `receptores-b`, `inventario-b` y `transporte-b` quedaron unhealthy por `PoolTimeout`
y el sondeo excedió 8 s. En modo reducido (17 contenedores, 1935 MiB) la VM recuperó 728 MiB disponibles y el arranque fue
estable. No se cambió la configuración de Docker Desktop. Para el Compose completo se necesita más memoria para Docker
Desktop, o detener los demás proyectos durante la ventana; esa decisión le corresponde al usuario. La guía no documenta un
perfil reducido.

**Efecto colateral.** El contenedor ajeno `spg-local-odoo` (política `unless-stopped`) reinició dos veces durante la
saturación; arrancó de nuevo a las 03:20:23 UTC. No se intervino: se recuperó solo y `/web/health` respondía 200 al cerrar.

## E. Recursos y limpieza

- Disco libre: 17.7 GiB al inicio y unos 13 GiB en el pico (imágenes y clon). Al cerrar, antes de borrar el clon, quedaban
  15 GiB, y 16 GiB después de borrarlo. El caché BuildKit creció de 7.958 a 9.651 GB y no se limpió: no se puede separar por proyecto y `builder prune`
  afectaría el caché de otros.
- Eliminado, en orden:
  1. `docker compose -p redhouse-clean-20261118 --profile install down --volumes --remove-orphans`: 30 contenedores, las
     redes `_data` y `_edge`, y los volúmenes `_postgres`, `_mongodb`, `_redis` y `_private-files`.
  2. `docker rmi`: las 13 imágenes `redhouse/*:clean-20261118`, `redhouse/mongodb-health:clean-20261118`,
     `redhouse-clean-20261118-bootstrap:latest`, `postgres:14-bookworm`, `redis:7.4-bookworm` y `nginx:1.28-alpine`. Las
     tres últimas se etiquetaron durante el ensayo (`LastTagTime` posterior a 03:08 UTC) y ningún otro contenedor las usa.
  3. El directorio del clon `/private/tmp/rh-clean-20261118` (1.1 GB), con su `.local/runtime` y `.local/compose`
     privados.
- Verificación: imágenes 307 (14.57 GB), contenedores 10 y volúmenes 9, igual que antes del ensayo. Siguen activos los
  4 contenedores ajenos.
- No se hizo commit ni push, ni se modificó código de `apps/` o `deployment/` del checkout de trabajo.
