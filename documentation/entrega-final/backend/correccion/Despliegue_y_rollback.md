# Preparación de despliegue correctivo 0.4.1 / esquema 13

Actualización 31/10/2026: el usuario autorizó el encendido y despliegue; la versión 0.4.1 / esquema 13 quedó publicada y comprobada. [Resultados del despliegue](../../../evidencias/gcp/correccion-20261031/RESULTADOS.md). Se respetó su instrucción posterior de demostración visible sin grabaciones ni capturas.

Estado histórico al 29/10/2026: preparación local. Entonces no existía autorización de publicación productiva. La instancia `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`, se consultó detenida. No se encendió ni se modificó infraestructura. La IP observada era 34.18.186.116; debe volver a verificarse antes de cualquier recorrido productivo. Un navegador sobre localhost no valida ese despliegue.

## Artefactos revisables

- Doce paquetes de propietario en `apps/services/`, nuevo `ms_documentos`.
- Versiones de código 0.4.1 y migraciones globales 012/013; `data/database/schema.sql` generado para instalación vacía.
- `compose.yaml`: dos réplicas de Documentos, secreto propio y gateway 5112 interno / 6112 loopback del host. Los puertos anteriores permanecen.
- Gateway público generado por `deployment/gcp/configure_public.py`: `/services/documentos/`; WSS permanece bajo Transporte.
- Migración local `apps/services/scripts/upgrade.py`, provisión incremental `upgrade_documents.py` y entrada explícita Compose `upgrade_compose.py`.
- Los manifiestos y resultados de cada intento se conservan en el directorio de ejecución. No reutilizar imágenes etiquetadas 0.3.0 como evidencia de 0.4.1.

## Secuencia operativa propuesta

1. Revisar los resultados finales y el manifiesto; validar la copia exacta de código a publicar. Actualizar consumidores de custodia y telemetría al contrato obligatorio antes de habilitar la nueva versión.
2. Confirmar autorización de encendido/despliegue y acceso a cuentas sintéticas. Registrar versiones de web/API/workers/esquema, URL real, imágenes y estado de colas. No enviar avisos externos a personas.
3. Crear respaldo privado PostgreSQL/MongoDB/Redis y configuración mediante el procedimiento vigente de `deployment/backup.py`; conservar también imágenes antiguas y metadatos de objetos GCS. No guardar respaldos ni credenciales en Git.
4. Poner la instalación en mantenimiento; detener web y todas las réplicas API/workers que escriben. Mantener los almacenes disponibles. Respaldar nuevamente PostgreSQL sin escritores y verificar que el archivo no está vacío.
5. Construir imágenes desde el manifiesto aprobado. Ejecutar la migración explícita con la imagen bootstrap nueva, `/run/install` montado y el respaldo privado accesible: `python /app/apps/services/scripts/upgrade_compose.py --backup /run/install/backups/RESPALDO.dump`. El comando aplica 012/013, crea solo la credencial nueva y conserva las claves existentes. Un arranque ordinario no migra automáticamente.
6. Transferir configuración GCS/ClamAV a Documentos mediante `deployment/configure_gcs.py` o `deployment/gcp/configure.py`, según el entorno. Revisar rutas privadas, firma impersonada y conectividad del escáner. No conceder al servicio nuevo acceso SQL a órdenes ni mantener acceso de Transporte a archivos.
7. Regenerar gateway y arrancar con `deployment/start.py`. Comprobar doce versiones API, workers, salud por dependencia, esquema 13, doce módulos web y sus permisos. La cola histórica de archivos sigue drenándose desde Transporte; las nuevas operaciones pertenecen exclusivamente a Documentos.
8. Recorrer con navegador la URL HTTPS real y cuentas sintéticas: MFA/reauth, laboratorio invalidado, reserva/traslado/custodia/destino, rol revocado, filtros/reportes/descarga privada, WSS por gateway y auditoría. Conservar capturas sin secretos, errores de consola/red y verificación de persistencia. Los mapas y clientes pendientes no se marcan aprobados.

## Comando explícito de migración Compose

Solo después de detener escritores, verificar el respaldo y recibir autorización productiva:

```sh
docker compose --profile install build bootstrap
docker compose --profile install run --rm --entrypoint python bootstrap \
  /app/apps/services/scripts/upgrade_compose.py \
  --backup /run/install/backups/RESPALDO.dump
```

`--directory` permite ensayar la misma estructura fuera de `/run/install`; en el contenedor se usa el valor predeterminado. El indicador de respaldo comprueba existencia/tamaño, no sustituye la validación de restauración ni detiene escritores automáticamente. El operador debe cumplir los pasos anteriores.

## Rollback

No volver solo a los binarios anteriores: 013 revoca acceso documental de Transporte y mueve claves idempotentes. Detener todos los escritores antes de restaurar el respaldo y sus configuraciones/imágenes compatibles. Si hubo nuevas escrituras después de migrar, no restaurar ciegamente: preservar un respaldo adicional y reconciliar operaciones, objetos y eventos con responsables autorizados. No borrar historia para ocultar pruebas ni reemitir automáticamente operaciones inciertas.

El ensayo `test_schema_11_extraction_backup_restore_and_idempotency` crea una base v11 con archivo, trabajo, idempotencia y outbox sintéticos; genera un `pg_dump` real, migra dos veces, comprueba conservación y restaura a otra base. `arquitectura-08.xml` registra su ejecución aprobada. Además, `test_correction_upgrade.py`, aprobado en `regresion-21.xml`, ejecuta dos veces la entrada `upgrade_compose.py` sobre una estructura privada equivalente con dump real, verifica ACL/credenciales nuevas, sesiones existentes y permisos SQL. No se levantó nuevamente la topología completa de 29 contenedores: ese ensayo sigue separado de las pruebas de migración, de construcción y del navegador con gateway real.

## Accesos y límites externos

GCS se probó con el bucket autorizado y credenciales existentes. ClamAV 1.4.6 oficial se extrajo en `/tmp`, después de verificar firma Apple/Cisco; se ajustó únicamente la ruta de bibliotecas de la copia temporal y se firmó localmente para ejecutarla fuera de `/usr/local`. FreshClam descargó firmas oficiales. `clamav-real.json` registra motor, rechazo EICAR, timeout controlado de transporte y recuperación del motor real. No se instaló un servicio permanente de ClamAV.

El navegador local aprobado usa un certificado sintético y Nginx 1.28.0 nativo, con cookies Secure y políticas operativas activas. La imagen Docker Nginx también entregó WSS/reconexión en un intento parcial; se pasó al binario nativo temporal para evitar la saturación de la VM local. Esto no acredita el despliegue Compose completo. El cliente ignora exclusivamente la confianza del certificado del entorno aislado. No se deshabilita CSRF ni se considera ese certificado apto para producción.
