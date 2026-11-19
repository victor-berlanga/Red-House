# Demostración sin segundo factor en la VM — 19/11/2026

**PASS.** A pedido del equipo (Víctor Berlanga, 19/11), el inicio de sesión de la VM ya no pide el «Código de segundo factor». Así la demostración no depende del autenticador. Es un cambio de **configuración y datos de la VM**: no se tocó código, imágenes, Nginx, TLS ni esquema. El segundo factor sigue implementado (`apps/services/ms_identidad_acceso/strong_auth.py`) y se puede reactivar con un comando.

## Qué se cambió

| Dónde | Antes | Después |
|---|---|---|
| `/opt/redhouse/.local/compose/apps/identidad_acceso.json` (secreto `config` de `identidad-acceso-a/b`) | `MFA_REQUIRED_ROLES` sin definir → por omisión `ADMIN`, `MEDICAL`, `COORDINATOR` (`redhouse/config.py`) | `MFA_REQUIRED_ROLES: []` |
| `red_house.security_factors.active` | 4 factores activos: `admin1`, `coordinator1`, `medical1`, `medical2` | 0 activos (las filas se conservan) |

`enforce_login` solo pide el código si el usuario tiene un factor activo o si su rol está en `MFA_REQUIRED_ROLES`. Con los dos cambios, el login y la reautenticación de acciones críticas piden solo la contraseña. El campo del formulario web sigue visible, pero se puede dejar vacío.

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

## Respaldo y reversa

Respaldo en `/opt/redhouse/.local/compose/backups/sin-mfa-20261119/`: la configuración original (`identidad_acceso.json.orig`) y los ids de los 4 factores que estaban activos (`factores_activos.txt`).

**Reversa**, dentro de la VM:

```sh
sudo bash /opt/redhouse/.local/compose/quitar_mfa.sh revertir
```

Restaura la configuración, reactiva solo esos 4 factores (con los mismos secretos, así que los autenticadores ya enrolados siguen sirviendo) y recrea `identidad-acceso-b/a`.

## Efecto en otras evidencias

- `fallo.py` ya usaba cuentas sin MFA, así que no cambia.
- `prepare_correction_demo.py` y `scripts/sustained_read.py` (comprobación de roles MFA) suponen el segundo factor activo. Antes de volver a correrlos en esta VM hay que aplicar la reversa.
