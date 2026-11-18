# GCS activado como proveedor de archivos en la VM — 18/11/2026

**Desde las 17:30 UTC aproximadamente del 18/11, los archivos nuevos de la VM `red-house` se guardan en Google Cloud Storage con URLs firmadas V4. Los archivos anteriores siguen en el volumen privado y se descargan igual que antes.** Datos sintéticos; no se imprimieron credenciales ni URLs firmadas.

## Cambio aplicado

- Bucket `red-house-evidencias-sistemas-integracion-01` (US-CENTRAL1, acceso uniforme, `public_access_prevention: enforced`, soft delete de 7 días). Ya existía y tenía 38 objetos VERIFIED de la etapa GCS de octubre.
- Identidad: la cuenta de servicio adjunta a la VM, `red-house-archivos`, con `roles/storage.objectUser` sobre el bucket y `roles/iam.serviceAccountTokenCreator` sobre sí misma para firmar (`signBlob`). Sin claves JSON descargadas. No se cambió IAM.
- `/opt/redhouse/.local/compose/apps/documentos.json`: `STORAGE_PROVIDER` de `local` a `gcs`. `GCS_BUCKET`, `GCS_PROJECT` y `STORAGE_LOCAL_ROOT` ya estaban y no cambiaron.
- Solo se recrearon `documentos-a` y `documentos-b` (`up -d --no-deps --force-recreate --wait`). Siguen **30/30 contenedores sanos**.
- Respaldo del archivo original: `/opt/redhouse/.local/compose/backups/gcs-activacion-20261118/documentos.json.orig`.
- **Reversa:** copiar ese respaldo sobre `apps/documentos.json` y recrear `documentos-a` y `documentos-b`. Los archivos creados en GCS mientras estuvo activo se seguirán sirviendo, porque cada fila guarda su propio `storage_provider`.

## Comprobaciones

1. **Firma con la identidad de la VM**, dentro del contenedor de Documentos: `signBlob` aceptado; PUT firmado 200, GET firmado 200 con el mismo contenido y GET anónimo 403. El objeto de prueba se borró con precondición de generación. Mis tres primeros intentos dejaron tres objetos de 58 bytes en `_deployment-checks/` porque la prueba no recargaba la generación antes de pedir la URL GET; se identificaron por nombre y hora y se borraron. El prefijo quedó vacío.
2. **Salud:** `/services/documentos/health/ready` 200 con `storage: {state: up, provider: gcs}`.
3. **Recorrido real por la API pública** con `donor1` ([recorrido_gcs.py](recorrido_gcs.py)):

| Paso | Resultado |
| --- | --- |
| Login | 200 |
| `POST /api/v1/documents` (consentimiento, PNG sintético de 1×1) | 201; `upload_url` en `storage.googleapis.com` |
| PUT del binario con la URL firmada | 200 |
| Repetir el mismo PUT | **412**: la precondición `x-goog-if-generation-match: 0` impide sobrescribir |
| `POST /files/{id}/verify` (tamaño, MIME, SHA-256 y ClamAV) | 200, `VERIFIED` |
| `GET /files/{id}/download` | 200; `download_url` en `storage.googleapis.com` |
| GET de la URL firmada | 200, mismo SHA-256 |
| GET del objeto sin firma | **403** |
| Logout | 200 |

   Documento creado: `4afefb37-e945-4524-a0df-d19cebec11b1`, con referencia `PRUEBA SINTETICA GCS 18/11/2026`. Se conserva como evidencia.
4. **Archivos LOCAL anteriores** ([descarga_local_previa.py](descarga_local_previa.py)): los dos archivos `local`/`VERIFIED` del traslado `baac4371…`, descargados por `transport1`: API 200, URL en el origen del portal (`34.18.186.116`), GET 200 con 1,555 y 1,553 bytes.

Conteo en `access_documentos.files` antes del recorrido: `gcs/VERIFIED` 38, `local/VERIFIED` 2.

## Límites

- Las URLs GCS ya emitidas siguen funcionando sus 5 minutos aunque el usuario cierre sesión; logout impide emitir otras nuevas. Con LOCAL la revocación es inmediata ([PLAN_GCS_REAL](../../../entrega-final/continuidad/PLAN_GCS_REAL.md)).
- `deployment/backup.py` respalda el volumen local; los objetos de GCS dependen del soft delete de 7 días del bucket, no del respaldo de la VM.
- El portal web, la app móvil y el escritorio ya aceptan el host `storage.googleapis.com` (`storage_client.py`, `MobileRepository.kt`, `document_upload.py`/`download.py`). Hoy solo se recorrió la API pública con un script; no se repitió la carga desde cada cliente.
