# Acceso por aplicación en la VM — 20/11/2026

**PASA.** Publicado el 20/11/2026 entre 15:18 y 15:32 UTC con `aplicar` (lanzado con `systemd-run`, unidad
`publicar-acceso-app`, `Result=success`). Tiempo sin servicio medido: **658 s**. Salida completa: [`aplicar.log`](aplicar.log).
El script lo construyó un agente y lo revisó otro antes de aplicarlo; la revisión corrigió un defecto bloqueante (la
trampa de error se ejecutaba dentro de un subshell y habría abortado la publicación a mitad del corte) y cinco más.

Publica en la VM `red-house` lo de `entrega-final` `cd6708e → 989f2e7` que afecta al servidor:
acceso por aplicación (`X-RedHouse-Client`, cliente en sesión y JWT, migración compartida 22) y el portal web
(navegación y cabecera `web`). Ver [Matriz de acceso por aplicación](../../../markdowns/Matriz_acceso_por_aplicacion.md).

Script: [`publicar_acceso_por_app.sh`](publicar_acceso_por_app.sh) (en la VM:
`/opt/redhouse/.local/compose/publicar_acceso_por_app.sh`, SHA-256 `8b409bc04e7472fec13779d4d8a2270ba8b38b83bb6d4d2141127066613f9776`). Carga útil: los 34 archivos de
`989f2e7` en `/opt/redhouse/.local/compose/acceso-app-20261120-payload/`; el script comprueba cada SHA-256 contra el
manifiesto que trae dentro. Salida de `verificar`: [`verificar.log`](verificar.log).

## 1. Inventario (solo lectura, 20/11 14:27–14:50 UTC)

- VM encendida 14:26 UTC; `redhouse.service` activo; **30/30 sanos**; disco libre **2.4 GB** de 20 GB.
- **Esquema compartido 21**; `red_house.web_session` sin columna `client`; 834 sesiones, **4 vivas**.
- Imágenes vigentes (todas derivadas con `COPY` sobre la anterior, según `docker history`):

| Servicio (a y b) | Imagen vigente |
| --- | --- |
| identidad-acceso | `redhouse/identidad_acceso:openapi410-20261118-01` |
| donantes, receptores, compatibilidad, priorizacion-geografia, custodia, monitoreo | `redhouse/<servicio>:xmlschema-20261116-01` |
| inventario | `redhouse/inventario:inventory-nplus1-20261117-01` |
| transporte | `redhouse/transporte:custody-clock-lab-labels-20261117-01` |
| alertas | `redhouse/alertas:alert-detail-20261117-01` |
| auditoria | `redhouse/auditoria:audit-catalog-20261118-01` |
| documentos | `redhouse/documentos:documents-reference-20261116-01` |
| web (monolito: trae los 12 servicios embebidos) | `redhouse-web:sin-segundo-factor-20261119-01` |
| bootstrap (perfil `install`, no corre) | `redhouse/bootstrap:mobile04-20261110` |
| storage-init (una sola vez) | `redhouse/documentos:security-20261113` (no se toca) |

**¿La VM está en `cd6708e`?** Sí, funcionalmente. Se compararon por SHA-256 los 1,223 archivos de código y despliegue
de `cd6708e` (sin pruebas ni `.md`) presentes en `/opt/redhouse` y el contenido `/app` de las 14 imágenes:

- `/opt/redhouse`: 1,213 idénticos. Los 10 distintos son 7 `.py` con **AST idéntico** (formato `ruff` de `3942b55`) y
  3 sin efecto en ejecución (`.env.example` ×2, `requirements-dev.txt`). Los 33 archivos de este cambio están en su
  versión `cd6708e` (o no existen, los nuevos).
- Imágenes: `security.py`, `shared_migrations.py`, `ms_identidad_acceso/*` y los archivos web del cambio están en
  `cd6708e`. Divergencias previas, ajenas a este cambio y heredadas de publicaciones acotadas: `audit_catalog.py`,
  `cache.py` (`84f9dc2`, antes de `6d8b88d`) y `openapi.py` más antiguos en servicios que no los usan para lo que
  cambió; `run.py`/`codec.py` difieren solo en formato. No se corrigen aquí.
- `bootstrap` es del 10/11: sin `019–021.sql`, sin `022.sql` y sin el script de revocación.
- No están en la VM (nunca se desplegaron) `scripts/load_client.py` y `load_final.py`, que este cambio modifica, ni sus
  dependencias (`load_guard.py`, `load_workflows.py`…): **no se copian**.

## 2. Qué cambia

**Imágenes** (14, etiqueta `acceso-app-20261120-01`, `FROM` la vigente + un `COPY` por archivo con el dueño y modo del
original; los nuevos toman los de un hermano):

| Imagen | Archivos |
| --- | --- |
| 11 servicios | `redhouse/security.py`, `redhouse/shared_migrations.py`, `shared_migrations/022.sql` |
| identidad-acceso | lo anterior + `ms_identidad_acceso/routes.py`, `mobile.py`, `contracts/openapi.json`, `redhouse/openapi.py` |
| web | lo de identidad + 7 scripts (incluido `revocar_sesiones_sin_cliente.py`) + 10 de `apps/web` (con `navigation.py` nuevo y `client.py`, que manda `X-RedHouse-Client: web`) |
| bootstrap | `shared_migrations.py`, `019–022.sql`, `scripts/revocar_sesiones_sin_cliente.py` |

`security.py` es compartido: todos los servicios rechazan sesiones sin aplicación. Ningún otro servicio cambió de código.

**`/opt/redhouse`**: 31 archivos (28 reemplazados, 3 nuevos), incluidos los scripts de `deployment/` que hacen login
(`fallo.py`, `verify.py`, `populate_demo.py`…). **`gcs.compose.yaml`**: solo las etiquetas de imagen (storage-init y
clamav igual). **Base**: migración 22, aditiva.

**No cambia**: `apps/*.json` (MFA sigue desactivado), `web.json`, `state.json`, `public.*`, Nginx, TLS, IAM, buckets,
ClamAV, storage-init. `aplicar` lo comprueba comparando la huella de esos archivos antes y después.

## 3. Plan de `aplicar`

1. **a1.** Respaldo de archivos en `backups/acceso-app-20261120/`: `gcs.compose.yaml.orig`, `archivos/<ruta>.orig`,
   `nuevos.txt`, `ps-antes.txt`, `imagenes-antes.txt`, `config-antes.sha256`.
2. **b.** Copia de los 31 archivos con `install` (dueño y modo del original) y comprobación de SHA-256.
3. **c.** Construcción de las 14 imágenes **antes de detener nada** y cambio de etiquetas en el override.
4. Login de prueba con el servidor vigente (sin cabecera) para comprobar después el rechazo de una sesión previa.
5. **a2.** `deployment/backup.py --verify --leave-stopped` (el mecanismo documentado): detiene las 27 aplicaciones,
   vuelca PostgreSQL, Mongo y Redis, restaura en contenedores aislados y compara. **Desde aquí no hay servicio.**
6. **d.** Migración 22 con las aplicaciones detenidas (lo que exige `upgrade_compose.py`), con la imagen bootstrap
   nueva. Se usa **solo la parte SQL** de `upgrade_compose.py`: ese script además reescribe `documentos.json`, las
   ACL, `web.json` y `state.json`, y la consigna es no tocar la configuración vigente.
7. **e.** `start` de gateway y clamav; luego, en el orden de `start.py`, réplica **b antes que a**, con
   `up -d --wait --no-deps --no-build --force-recreate`; al final `web`.
8. Comprobación de que la sesión abierta en el paso 4 recibe **401** en Identidad y en Donantes.
9. **f.** `revocar_sesiones_sin_cliente.py` en seco, `--aplicar` y otra vez en seco (debe dar 0), con
   `docker compose --profile install run --rm --no-deps -T --entrypoint python bootstrap -m scripts.revocar_sesiones_sin_cliente --directory /run/install [--aplicar]`.
   Respecto al comando del encargo se agregan `--no-deps` (no arrancar ni tocar las bases) y `-T` (sin TTY por SSH).
10. **g.** Verificación (ver §5).

Si algo falla con las aplicaciones detenidas y el esquema sigue en 21, el script vuelve a arrancar los contenedores
anteriores (sin recrearlos) y restaura el override. Si ya está en 22, `aplicar` se puede repetir: salta respaldo y
migración.

**Tiempo estimado (sin medir):** total 20–25 min. Construcción 2–3 min con servicio. **Sin servicio, 15–20 min**:
respaldo con restauración aislada (4–6 min), migración (segundos) y 25 recreaciones secuenciales con `--wait`
(≈30 s cada una). Con todo detenido, el orden b→a no aporta disponibilidad; recrear a y b juntos por grupo (como
`start.py`) dejaría el corte en ~10 min.

## 4. Salida de `verificar` (20/11/2026 14:49–14:50 UTC)

Completa en [`verificar.log`](verificar.log). Resumen:

- Carga útil: 34 archivos con el SHA-256 de `989f2e7`. Estado: 30/30 sanos, esquema 21, 4 sesiones vivas.
- Huella de la configuración privada: `95f1964eebdb4f29`, igual en las dos corridas.
- Por imagen: los archivos de §2 salen como `cambia` o `nuevo`. Ninguno sale `igual`, así que nada estaba publicado.
- `compose config` válido; el bootstrap resuelve a `redhouse/bootstrap:mobile04-20261110`.
- **Ensayo de la migración 22** (transacción con ROLLBACK, imagen bootstrap vigente con `shared_migrations.py` y
  `022.sql` montados de solo lectura):
  `{"antes": 21, "despues": 22, "latest": 22, "columna_client_tabla": 1, "columna_client_vista": 1, "identidad_puede_usar_client": true, "create_db_previo": false, "modo": "ensayo: ROLLBACK, nada escrito"}`.
  Después del ensayo el esquema sigue en 21. `rh_identidad_acceso` hereda los permisos de la vista sobre `client`.
- Después de `verificar`: 0 imágenes `acceso-app`, sin carpeta de respaldo, override sin cambios, 30/30 sanos.

## 5. Resultado de `aplicar` (20/11/2026 15:18–15:32 UTC)

- Respaldo `backup.py --verify --leave-stopped`: `backup` y `restore` = `passed`, en
  `/opt/redhouse/.local/compose/backups/20261120T152027Z` (113 MB). Disco libre después: 994 MB.
- 14 imágenes nuevas, cada una con SHA-256, dueño y modo de cada archivo comprobados y prueba de humo antes del corte:
  - `redhouse-web:acceso-app-20261120-01 sha256:b563c2450704`
  - `redhouse/bootstrap:acceso-app-20261120-01 sha256:2ec73ba40d60`
  - `redhouse/auditoria:acceso-app-20261120-01 sha256:2be71d212f9e`
  - `redhouse/alertas:acceso-app-20261120-01 sha256:6be961341d78`
  - `redhouse/custodia:acceso-app-20261120-01 sha256:72e10b0ef384`
  - `redhouse/identidad_acceso:acceso-app-20261120-01 sha256:cce727393646`
  - `redhouse/donantes:acceso-app-20261120-01 sha256:1721eeb96738`
  - `redhouse/receptores:acceso-app-20261120-01 sha256:5b73381cca5e`
  - `redhouse/compatibilidad:acceso-app-20261120-01 sha256:dbf743ccb47a`
  - `redhouse/priorizacion_geografia:acceso-app-20261120-01 sha256:25ca7bbe12d3`
  - `redhouse/inventario:acceso-app-20261120-01 sha256:8076ceb73b19`
  - `redhouse/transporte:acceso-app-20261120-01 sha256:78661ef1c26a`
  - `redhouse/documentos:acceso-app-20261120-01 sha256:82c435446549`
  - `redhouse/monitoreo:acceso-app-20261120-01 sha256:f9d38e6afb19`
- Migración: `{"antes": 21, "despues": 22, ..., "modo": "aplicado (COMMIT)"}`.
- Tiempo sin servicio (del respaldo a `web` sano): **658 s**.
- Sesión previa: el script no pudo abrir su sesión de prueba antes del corte y omitió esa comprobación en vivo
  (la cubre `test_acceso_por_aplicacion.py::test_session_issued_before_the_change_is_rejected_and_the_script_revokes_it`).
- Revocación: 5 en seco → 5 revocadas → 0.
- 30/30 sanos; imagen y SHA-256 de `security.py` correctos en los 25 contenedores de aplicación.
- HTTPS `/login` 200, `/health/live` 200 y `/health/ready` 200 en los 12 servicios. Esquema 22, columna `client`.
- `gcs.compose.yaml`: 26 etiquetas cambiadas; `storage-init` y `clamav` intactos. Configuración privada sin cambios
  (el MFA sigue desactivado).
- Login por API: 200 (admin1 y auditor1 en web; operator1 y medical1 en desktop; donor1 y transport1 en mobile);
  403 `client_not_allowed` (donor1 en web, admin1 y auditor1 en desktop, operator1 en mobile, transport1 en
  desktop); 400 `client_required` (sin cabecera y con `WEB`).
- Portal: `GET /login` 200, `POST /login` admin1 → 302 `/panel` → 200.
- Comprobación manual posterior (desde la VM, contraseña leída de `state.json` sin imprimirla): con el token nuevo de
  donor1 (mobile), transport1 (mobile), operator1 (desktop) y auditor1 (web): `/auth/me` 200; Donantes `/donors`,
  Transporte `/summary`, Inventario `/resources` y Auditoría `/events` 200; `/auth/logout` 200.

## 6. Reversa

`sudo bash /opt/redhouse/.local/compose/publicar_acceso_por_app.sh revertir`: restaura `gcs.compose.yaml` y los 28
archivos, quita los 3 nuevos y recrea con las imágenes anteriores: primero los servicios que no son Identidad, luego
Identidad y al final `web`. Así nunca queda la web vieja (sin cabecera) frente a una Identidad nueva. No hace falta
detener nada: el código anterior ignora la columna `client` y su readiness acepta 22 ≥ 21.

- **La migración 22 se deja** (aditiva). Su reversa SQL manual está en los comentarios de `022.sql` y solo aplica si el
  código se retira para siempre. Tras revertir, las herramientas viejas de migración (`LATEST_VERSION=21`) rechazarán
  la base en 22.
- Las sesiones revocadas siguen revocadas: basta iniciar sesión. Las imágenes `acceso-app-20261120-01` se conservan.
- No se usa `restore.py`. El respaldo de `backup.py` queda en `backups/<fecha UTC>/` para un caso extremo.

## 7. Riesgos y límites

- **Clientes ya distribuidos** (APK y escritorio anteriores) no mandan la cabecera y no podrán iniciar sesión (400).
  Hay que generar APK y paquetes de escritorio nuevos (pendiente en `PROJECT_STATUS.md`).
- Todas las sesiones abiertas se cierran: cada persona inicia sesión de nuevo.
- `prepare_correction_demo.py` y `sustained_read.py` siguen suponiendo MFA activo (nota del 19/11).
- Disco: quedaron 994 MB libres. `backup.py` no borra sus contenedores de restauración: hay juegos viejos detenidos
  (`redhouse-restore-*`, unos 2.4 GB) que conviene eliminar con acuerdo del equipo. El script exige ≥2 GB para empezar.
- Tiempo sin servicio medido: 658 s.
