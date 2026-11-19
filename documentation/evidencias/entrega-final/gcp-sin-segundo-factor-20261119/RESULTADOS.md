# Demostración sin segundo factor en la VM — 19/11/2026

**PASS.** A pedido del equipo (Víctor Berlanga, 19/11), el inicio de sesión de la VM ya no pide el «Código de segundo factor». Así la demostración no depende del autenticador. Es un cambio de **configuración y datos de la VM**: no se tocó código, imágenes, Nginx, TLS ni esquema. El segundo factor sigue implementado (`apps/services/ms_identidad_acceso/strong_auth.py`) y se puede reactivar con un comando.

## Qué se cambió

| Dónde | Antes | Después |
|---|---|---|
| `/opt/redhouse/.local/compose/apps/identidad_acceso.json` (secreto `config` de `identidad-acceso-a/b`) | `MFA_REQUIRED_ROLES` sin definir → por omisión `ADMIN`, `MEDICAL`, `COORDINATOR` (`redhouse/config.py`) | `MFA_REQUIRED_ROLES: []` |
| `red_house.security_factors.active` | 4 factores activos: `admin1`, `coordinator1`, `medical1`, `medical2` | 0 activos (las filas se conservan) |

`enforce_login` solo pide el código si el usuario tiene un factor activo o si su rol está en `MFA_REQUIRED_ROLES`. Con los dos cambios, el login y la reautenticación de acciones críticas piden solo la contraseña. En la segunda parte también se quitó el campo del portal web (ver abajo).

Después se recrearon `identidad-acceso-b` y luego `identidad-acceso-a` (`up -d --wait --no-deps --no-build --force-recreate`), para que siempre hubiera una réplica sana. Al terminar había 30 de 30 contenedores sanos y las dos réplicas leían `MFA_REQUIRED_ROLES=[]`.

Script exacto: [`quitar_mfa.sh`](quitar_mfa.sh). En la VM está en `/opt/redhouse/.local/compose/quitar_mfa.sh`.

## Comprobación

Se hizo login por HTTPS (`/services/identidad-acceso/api/v1/auth/login`) **sin código**, con la contraseña privada de `state.json`, que no se imprimió:

| Usuario | Resultado |
|---|---|
| admin1 | HTTP 200, con token |
| coordinator1 | HTTP 200, con token |
| medical1 | HTTP 200, con token |
| medical2 | HTTP 200, con token |
| operator1 (nunca tuvo factor) | HTTP 200, con token |

## Segunda parte: portal web sin el campo

Víctor pidió quitar también el campo de la pantalla. Cambio de código en la rama:
- `apps/web/src/presentation/templates/login.html`: se quitó «Código de segundo factor».
- `apps/web/src/integration/routes/common.py`: el diálogo «Confirma tu contraseña» de las acciones críticas ya no muestra «Código nuevo de segundo factor» y envía solo la contraseña.

Las pruebas locales `test_web_integration`, `test_web_reauthentication_challenge` y `test_web_sessions` pasaron (29 de 29), igual que `ruff check` y `ruff format --check` del CI.

Antes de publicar se compararon las huellas en la VM. `login.html` era idéntico al del repo. El `common.py` que corría solo difería por formato: una línea partida por `ruff format`, sin cambio de lógica.

**Publicación:** se construyó la imagen `redhouse-web:sin-segundo-factor-20261119-01` (`sha256:3d909327dacabebc74f6b7e4adfbec77ad72ccf4279062244176f5ff3626dcb4`), derivada de `redhouse-web:web-config-ios-20261118-01` con dos `COPY` (dueño 0:0, modo 644, como el original). Solo cambió el contenedor `web`; siguen 30 de 30 sanos. Dentro del contenedor, los SHA-256 son `login.html` `5d02b9ea…` y `common.py` `2d6d19cb…`, iguales a la rama. Script: [`publicar_web_sin_mfa.sh`](publicar_web_sin_mfa.sh). Salida: [`publicacion_web.log`](publicacion_web.log).

**Comprobación:**
- `GET /login` por HTTPS: 200, con solo «Cuenta institucional» y «Contraseña»; 0 coincidencias de «segundo factor» o `id="otp"`.
- Login por el formulario (con CSRF y sin código) de `admin1` y `medical1`: `POST /login` → 302 `/panel` → 200.

Escritorio y móvil no se cambiaron. Su campo de código ya estaba oculto y solo aparece si el servidor responde `mfa_required`, cosa que ya no pasa con la primera parte. El diálogo de reautenticación de escritorio conserva un campo opcional «Si tu cuenta lo requiere», que se puede dejar vacío.

Los scripts históricos con Playwright (`scripts/verify_stage02.cjs`, `verify_backend_corrections.cjs`, `demonstrate_gcp_corrections.cjs`) llenan `#otp`. Son evidencia de cortes anteriores y no se usan en la demostración.

## Respaldo y reversa

Respaldo en `/opt/redhouse/.local/compose/backups/sin-mfa-20261119/`: la configuración original (`identidad_acceso.json.orig`) y los ids de los 4 factores que estaban activos (`factores_activos.txt`).

**Reversa**, dentro de la VM:

```sh
sudo bash /opt/redhouse/.local/compose/quitar_mfa.sh revertir
```

Para el portal: `sudo bash /opt/redhouse/.local/compose/publicar_web_sin_mfa.sh revertir`. Restaura la imagen anterior en el override y las fuentes desde `backups/web-sin-mfa-20261119/`, y recrea `web`.

El primer comando restaura la configuración, reactiva solo esos 4 factores (con los mismos secretos, así que los autenticadores ya enrolados siguen sirviendo) y recrea `identidad-acceso-b/a`.

## Efecto en otras evidencias

- `fallo.py` ya usaba cuentas sin MFA, así que no cambia.
- `prepare_correction_demo.py` y `scripts/sustained_read.py` (comprobación de roles MFA) suponen el segundo factor activo. Antes de volver a correrlos en esta VM hay que aplicar la reversa.
