# Publicación acotada en GCP: referencia de error en el log del portal — 18/11/2026

**PASS.** Se publicó la corrección `34e5579` (INC-438): el portal registra la «Referencia» que muestra en sus páginas de error de negocio. **Una imagen nueva y un contenedor actualizado (`web`)**; los otros 29 conservaron su ID. Siguen 30 de 30 sanos.

## Cambio y huellas

| Fuente | SHA-256 anterior (= `0c0f4eb`, igual al que corría) | SHA-256 publicada (= `34e5579`) |
|---|---|---|
| `apps/web/src/integration/__init__.py` | `b143d3ef5e83544096feb11171d89d3c27228bcc4648cfdedb1fa08307429e27` | `489a0f082a6aae3b864274500b4b2b330a5947bab22380d846959cf25cf097bb` |

- Imagen `redhouse-web:web-log-referencia-20261118-01` (`sha256:113147bc0e91…64285`), derivada de la imagen en uso `redhouse-web:custody-clock-lab-labels-20261117-01` con un solo `COPY` (propietario 0:0, modo 755, como el archivo original). No se reconstruyeron dependencias.
- Se actualizó la misma fuente en `/opt/redhouse` y la etiqueta de `web` en el override privado `gcs.compose.yaml`.
- Respaldo previo del override y de la fuente: `/opt/redhouse/.local/compose/backups/web-log-referencia-20261118/`. **Reversa:** restaurar ambos archivos y recrear `web` con el mismo comando.

## Publicación

`docker compose --project-directory /opt/redhouse -f compose.yaml -f .local/compose/gcs.compose.yaml -f .local/compose/public.compose.yaml up -d --wait --no-deps --no-build web`. `web` quedó `healthy`. La comparación de `docker ps` antes y después solo difiere en `redhouse-parcial2-web-1`. Dentro del contenedor el archivo tiene el SHA-256 publicado.

## Comprobación remota (HTTPS `34.18.186.116`)

- `/`, `/login` y `/health/live`: 200. Una ruta protegida sin sesión: 302 al acceso.
- `docker logs --since 5m` de web: sin errores después del cambio.
- La prueba `apps/services/tests/test_web_business_error_log_unit.py` falla con la versión anterior y pasa con la publicada: la referencia de la página aparece en una línea `web_business_error correlation=… status=… code=… endpoint=…`, sin el mensaje mostrado al usuario.

No hubo login, escritura de negocio, migración ni cambios de Nginx, TLS, permisos o buckets.
