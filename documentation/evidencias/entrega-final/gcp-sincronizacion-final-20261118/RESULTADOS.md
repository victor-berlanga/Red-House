# VM sincronizada con la rama `entrega-final` — 18/11/2026

**PASS.** Después de las publicaciones del día, el código de `/opt/redhouse` y los contenedores coinciden con el repositorio. Se compararon por SHA-256 los **411 archivos** de código y configuración y los **606 contratos** (JSON/XSD) versionados que existen en ambos lados (`apps/services`, `apps/web`, `deployment`, `compose.yaml`; sin pruebas ni Markdown). **Diferencias: 0.**

## Qué faltaba y se publicó

| Cambio | Commit | Efecto | Cómo se publicó |
|---|---|---|---|
| `apps/services/redhouse/openapi.py`: la 410 de la ruta de reautenticación retirada se comparte como `Error410` con ejemplo | `ddea219` (17/11) | Solo cambia el OpenAPI de Identidad (única ruta con esa 410) | Imagen `redhouse/identidad_acceso:openapi410-20261118-01` (`sha256:e7fd8b77…`), derivada de `xmlschema-20261116-01` con un `COPY`; `identidad-acceso-a/b` recreados |
| `apps/web/src/integration/routes/configuration.py`: alta de dispositivo con «Teléfono Android» y «Teléfono iOS» | `bac46ba` | Formulario de dispositivos del portal; el backend en la VM ya aceptaba `IOS` | Imagen `redhouse-web:web-config-ios-20261118-01` (`sha256:e9fc5f2a…`), derivada de `web-log-referencia-20261118-01`; `web` recreado |
| Scripts de instalación y operación (`provision.py`, `local.py`, `bootstrap.py`, `prepare_load.py`, `document.py`, `upgrade_documents.py`, `check_real_scanner.py`), copia de `redhouse.service` y `contracts/openapi.json` de Identidad | varios | No cambian lo que corre; dejan la copia de la VM igual al repo | Copiados a `/opt/redhouse` con el dueño y modo de cada original |

Respaldo de todo lo reemplazado: `/opt/redhouse/.local/compose/backups/sync-final-20261118/`, incluido `gcs.compose.yaml.orig`. **Reversa:** restaurar esos archivos y recrear `identidad-acceso-a/b` y `web`.

## Comprobación

- `docker ps` antes y después: solo cambiaron `identidad-acceso-a`, `identidad-acceso-b` y `web`. Siguen **30/30 sanos**.
- Dentro de los contenedores, `openapi.py` (`103f006d…`), `configuration.py` (`612e9044…`) y `integration/__init__.py` (`489a0f08…`) tienen el SHA-256 del repo.
- HTTPS: `/login`, `/health/live`, `/services/identidad-acceso/health/ready` y `/services/identidad-acceso/docs/` responden 200. El `openapi.json` servido por Identidad contiene `components.responses.Error410`.
- No hubo migraciones ni cambios de Nginx, TLS, IAM o buckets.

## Publicaciones del día en la VM

[Arranque con ClamAV (INC-437)](../gcp-arranque-clamav-20261118/RESULTADOS.md) · [GCS activado](../gcp-gcs-activacion-20261118/RESULTADOS.md) · [Referencia de error en el log (INC-438)](../gcp-web-log-referencia-20261118/RESULTADOS.md) · [fallo.py ensayado 12/12](../gcp-fallos-en-vivo-20261118/RESULTADOS.md) · esta sincronización.
