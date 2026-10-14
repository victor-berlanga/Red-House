# Datos y persistencia

El portal consume HTTP; cada servicio es propietario de sus registros. [Mapa de bases y SQL](../../data/database/README.md).

## Almacenamiento

- PostgreSQL: once bases lógicas en un servidor local. Conserva operaciones, estados, referencias, eventos transaccionales y pendientes de entrega.
- MongoDB: telemetría/documentos de Transporte, proyecciones de Custodia, Auditoría y sondeos de Monitoreo.
- Redis: sesiones, revocaciones, permisos temporales, límites de consumo y caché. Las expiraciones de estos datos no eliminan expedientes de PostgreSQL.
- SQLite privado del portal: sesiones cifradas y revocaciones pendientes, sin tablas de negocio.
- Google Cloud Storage: adaptador disponible; falta verificar el bucket real. Los archivos no se almacenan como binarios en las bases.

## Ciclo de vida

`install.sh` crea un entorno solo cuando no existe; carga dos instituciones y cuentas iniciales ficticias. Si ya está preparado, conserva los datos. `start.sh` y `stop.sh` operan procesos; no recargan registros. El entorno predeterminado es `.local/runtime/`.

La carga ampliada de Nuevo León es explícita y comprueba que no se duplique. Una prueba automatizada puede crear bases desechables independientes; no equivale al entorno usado por el portal.

## Migraciones

Cada servicio mantiene SQL numerado en `migrations/`. `schema_version` registra lo aplicado. Las actualizaciones se ejecutan con el propietario mediante `apps/services/scripts/upgrade.py`, que respalda antes de modificar cada base. El proceso HTTP no migra tablas.

Las migraciones de normalización cambian el código anterior de eritrocitos a `RBC` en Donantes, Receptores, Inventario y capacidades de Identidad. Conservan IDs, relaciones y filas, e incrementan las versiones modificadas. Una evaluación anterior puede requerir repetirse al cambiar la versión del recurso; los registros históricos y las cadenas firmadas no se reescriben.

Los valores anteriores aparecen exclusivamente donde son necesarios para identificar datos a migrar y probar la transición. No se deben ocultar ni alterar valores de auditoría para eliminar una etiqueta visual.
