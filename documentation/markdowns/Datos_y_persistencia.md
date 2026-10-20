# Datos y persistencia

## Almacenamiento

- PostgreSQL: una base compartida `red_house`. Las 71 tablas físicas están en el esquema `red_house`. Cada servicio usa credenciales propias y vistas de acceso; no hay una copia física por servicio.
- MongoDB: documentos/eventos de Transporte, Custodia, Auditoría y Monitoreo. Monitoreo escribe primero sus sondeos aquí para registrar caídas de PostgreSQL.
- Redis: sesiones, permisos, revocaciones, límites de consumo y caché. No sustituye los expedientes transaccionales.
- Portal: sesiones cifradas y bloqueos de renovación en Redis; una tabla técnica `web_runtime.session_revocations` en PostgreSQL conserva cierres y revocaciones pendientes. Las 71 tablas del esquema de dominio se mantienen; el total entre ambos esquemas es 72.
- Google Cloud Storage: bucket privado real `red-house-evidencias-sistemas-integracion-01`, acceso uniforme y bloqueo público. PostgreSQL conserva referencias, hash, tamaño, MIME, generación y estados. URLs firmadas de cinco minutos; [flujo y pruebas](Reporte_tecnico_segundo_parcial.md).

[Esquema y generación](../../data/database/README.md) · [Cambios respecto de main](Esquema_compartido.md).

## Ciclo de vida

La instalación nueva crea una única base y cuentas iniciales ficticias. Arrancar o detener procesos no reinicializa registros. El entorno privado es `.local/runtime/`, excluido de Git. La carga regional ampliada continúa siendo explícita.

Los entornos anteriores con once bases requieren `apps/services/scripts/migrate_shared.py`. No basta cambiar DATABASE_URL. El proceso crea respaldos, copia datos hacia una base nueva, compara filas y verifica relaciones antes de publicar configuraciones. Las bases antiguas permanecen intactas; no se usan como fallback del sistema nuevo.

## Versiones y permisos

`red_house.schema_migration` registra la versión global; la adaptación ejecutable es la versión 6. `service_schema_version` conserva el corte de las migraciones de origen por servicio. Las API no ejecutan migraciones al recibir peticiones. `upgrade.py` verifica la versión compartida; no aplica automáticamente SQL histórico sobre las vistas.

Las colas, inbox, idempotencia y latidos se guardan en tablas comunes con ámbito de servicio. Las claves y vistas impiden que un consumidor procese trabajo de otro. La caché mantiene revisiones independientes para catálogos e inventario. Los historiales siguen siendo anexables y las credenciales de ejecución no pueden cambiar versiones de esquema.

La adaptación conserva la coordinación HTTP de los procesos actuales. Tener una sola base no convierte por sí mismo una secuencia HTTP completa en una transacción SQL. Las claves foráneas sí verifican las referencias entre módulos.

## Verificaciones

El generador restaura el SQL en una base temporal y compara la estructura. Las pruebas de integración comprueban base única, permisos, claves foráneas, colas aisladas, conservación de datos y monitoreo con PostgreSQL inaccesible. Los resultados de la ejecución actual están en `PROJECT_STATUS.md`; los resultados anteriores no certifican una versión posterior.

## Incremento del segundo parcial

La colección mutable `rh_transporte.shipment_tracking` mantiene estado y secuencia por traslado; sus eventos de origen siguen siendo inmutables. Los índices `regional_state` y `shipment_sequence` acompañan consultas regionales y reconstrucción ordenada. La migración documental es aditiva y explícita (`scripts/migrate_documents.py`).

Docker usa volúmenes PostgreSQL, MongoDB y Redis propios y configuraciones en `.local/compose`; no monta archivos físicos de `.local/runtime`. `bootstrap` instala el esquema compartido v6 y cuentas ficticias una sola vez. Una repetición verifica la versión y conserva registros. [Modelo físico de 71 tablas](../segundo-parcial/Modelo_fisico.md) · [Operación y respaldo](../../deployment/README.md).

Una revocación cuyo contenido no puede descifrarse permanece pendiente hasta recuperar la clave o alcanzar su expiración; no se confirma ni se descarta como exitosa.
