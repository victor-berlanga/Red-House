# Publicación acotada en GCP: catálogo de auditoría (INC-446) — 18/11/2026

**PASS.** Se publicó la corrección `a4af39c` (INC-446): los 7 eventos que el visor de la bitácora mostraba como «Evento sin clasificación» ya tienen nombre, categoría y resultado. **Una imagen nueva y dos contenedores actualizados (`auditoria-a`, `auditoria-b`)**; los otros 28 conservaron su ID. Siguen 30 de 30 sanos.

## Por qué solo Auditoría

La etiqueta, la categoría y el resultado que ve el usuario los calcula `ms_auditoria` al consultar (`queries.py`: `present()` y el `CASE` de `BASE`), con el catálogo de su propia imagen. Por eso el cambio también corrige los eventos ya guardados. Los demás servicios copian el catálogo solo para un campo `metadata.audit.result` que nada lee (búsqueda en `apps/services` y `apps/web` sin coincidencias), así que no se reconstruyeron.

## Cambio y huellas

| Fuente | SHA-256 anterior (el que corría) | SHA-256 publicada (= `a4af39c`) |
|---|---|---|
| `apps/services/redhouse/audit_catalog.py` | `401ce01ba88b73d433eec39e1cf3dd61fed2883f39acf37a47a4ca0aee009a7c` | `3bef3ed2c929a9b74e5ca8099bab977cc4defd84e9304f641d6ded412f3d4fa2` |

- Imagen `redhouse/auditoria:audit-catalog-20261118-01` (`sha256:51c1ffa99f17…a128b`), derivada de la imagen en uso `redhouse/auditoria:xmlschema-20261116-01` con un solo `COPY` (propietario 0:0, modo 755, como el original en `/app/apps/services/redhouse/audit_catalog.py`). No se reconstruyeron dependencias.
- Se actualizó la misma fuente en `/opt/redhouse` y la etiqueta de `auditoria-a/b` en el override privado `gcs.compose.yaml`.
- Respaldo previo: `/opt/redhouse/.local/compose/backups/audit-catalog-20261118/` (override, fuente y `docker ps` antes y después). **Reversa:** restaurar `gcs.compose.yaml.orig` y `audit_catalog.py.orig` y recrear `auditoria-b` y luego `auditoria-a` con el mismo comando.
- Script exacto: [`publicar.sh`](publicar.sh). Salida: [`publicacion.log`](publicacion.log).

## Publicación

`docker compose … up -d --wait --no-deps --no-build` primero sobre `auditoria-b` y después sobre `auditoria-a`, para que siempre hubiera una réplica sana. La comparación de `docker ps` antes y después solo difiere en esos dos contenedores. Dentro de ambos, el archivo tiene el SHA-256 publicado y `describe()` devuelve la clasificación nueva de los 7 eventos (ver el log).

## Comprobación remota (HTTPS `34.18.186.116`)

- `/`, `/login`, `/health/live`, `/services/auditoria/health/ready` y `/services/auditoria/docs/`: 200.
- `docker logs --since 10m` de las dos réplicas: solo peticiones 200 con `"error": null`.

## Certificado TLS

El certificado vigente (Let's Encrypt, perfil `shortlived`) vence el **24/11/2026 14:08 UTC**. `redhouse-certbot.timer` está habilitado, corre cada seis horas con `Persistent=true` (al encender la VM recupera la corrida perdida; corrió a las 04:49 UTC y no renovó porque aún faltaban 5 días) y el hook `/etc/letsencrypt/renewal-hooks/deploy/redhouse` recarga el proxy tras renovar. Basta con encender la VM para que renueve.

No hubo login, escritura de negocio, migración ni cambios de Nginx, TLS, permisos o buckets. La VM se apagó al terminar.
