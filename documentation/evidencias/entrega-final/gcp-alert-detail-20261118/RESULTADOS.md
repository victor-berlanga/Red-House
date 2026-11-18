# Publicación acotada en GCP: detalle de Avisos — 18/11/2026

La publicación acotada terminó **PASS** en `sistemas-integracion-01`, VM `red-house` (ID `2861822465669755197`), zona
`me-central1-a`: **una imagen y dos contenedores actualizados** (`alertas-a`, `alertas-b`), treinta saludables y veintiocho
conservados. Publica la corrección `0edf74d` (`GET /api/v1/alerts/{identifier}`), validada antes en el
[AVD con el fixture conservado](../mobile/android-c-ver-detalle-20261117/RESULTADOS.md).

## Cambio y huellas

Las tres fuentes en ejecución coincidían exactamente con el commit `30e1a84` antes de publicar, así que la imagen nueva
solo cambia la corrección.

| Fuente | SHA-256 anterior (= `30e1a84`) | SHA-256 publicada (= `0edf74d`) |
|---|---|---|
| `apps/services/ms_alertas/routes.py` | `dd4c9215439279633192fbfac82f572b8f06016fe3825a90796a8491e9844d0e` | `2df7e63565c60ac7370651d69f9c5cea596b488f569e584c750e61fa2340b47a` |
| `apps/services/ms_alertas/outputs.json` | `23627924771d3b67cc5c75caf5ad017b626dc28737dea5eeeacd85be51b58581` | `9e1da866050ae5d29f55832d41dde0b12e94efea516c30e6312c297a2d9f2d3f` |
| `apps/services/ms_alertas/contracts/openapi.json` | `b988d4d17dbd1086661954dd0a07f94eacbecb947e018e928844dcc6a8c13e2c` | `27992e0958e5e01f72c3ef38949e72ec6593d438802fd02eb7b7ac95d8691dbf` |

| Imagen | ID publicado | Base conservada |
|---|---|---|
| `redhouse/alertas:alert-detail-20261117-01` | `sha256:68671cc80373cf488704840c3553f51ca7509a2520706ec2b34148c0cf8529e4` | `redhouse/alertas:xmlschema-20261116-01` (`sha256:f2f5e75b0f2ae3a08030d36508cddaa20bc4e54c73a3686ced5dc0f728a07dbe`) |

La imagen se derivó de la base en uso con un `Dockerfile` de tres `COPY` (propietario UID 10001), sin reconstruir
dependencias. Se actualizaron las mismas tres fuentes en `/opt/redhouse` y la etiqueta de `alertas-a/b` en el override
privado `gcs.compose.yaml`; el respaldo previo de ese override y de las fuentes quedó en
`/opt/redhouse/.local/compose/backups/alert-detail-20261118T023802Z/`.

## Publicación

Mismo comando que `deployment/start.py`, limitado a los dos destinos:
`REDHOUSE_COMPOSE_DIR=/opt/redhouse/.local/compose docker compose -f compose.yaml -f .local/compose/gcs.compose.yaml -f .local/compose/public.compose.yaml up -d --wait --no-deps --no-build alertas-a alertas-b`.
Ambos quedaron `healthy`. La comparación de `docker ps` antes/después solo difiere en esos dos contenedores; los otros 28
conservaron ID e imagen. No hubo login, escritura de negocio, migración, restauración, cambio de Nginx, TLS, permisos ni buckets.

## Comprobación remota (HTTPS `34.18.186.116`)

| Comprobación | Antes | Después |
|---|---|---|
| `GET /services/alertas/api/v1/alerts/<uuid>` sin sesión | **404** `http_error` (ruta inexistente en Alertas) | **401** `unauthorized` en 6 de 6 rondas (balanceo a/b): la ruta existe y exige sesión |
| `/services/alertas/health/live` y `/health/ready` | — | 200 / 200 |
| `/health/live` (web) y `/login` | — | 200 / 200 |
| `openapi.json` publicado de Alertas | sin la ruta | contiene `/api/v1/alerts/{identifier}` |

## Acceso

La conexión usó OS Login por IAP con la cuenta propia `alberto.reyna@udem.edu`. Al terminar se borraron los archivos
temporales de `/tmp` en la VM y se retiró la clave SSH temporal del perfil OS Login (quedan 0 claves) y sus archivos
locales. El certificado TLS no se tocó; su vencimiento sigue en el 24/11/2026 14:08:33 UTC.
