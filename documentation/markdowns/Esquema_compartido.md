# Base PostgreSQL compartida

## Arquitectura implementada en el código

Todos los servicios se conectan a una base PostgreSQL, `red_house`. Las tablas físicas están en un único esquema, `red_house`; las relaciones entre instituciones, usuarios, donantes, solicitudes, recursos, evaluaciones y traslados se comprueban mediante claves foráneas.

Los esquemas `access_identidad_acceso`, `access_donantes`, etc. contienen **solo vistas y funciones**, no tablas ni copias de los registros. Adaptan nombres de columnas al contrato JSON/XML existente. Cada credencial puede usar únicamente sus vistas autorizadas; no obtiene acceso a contraseñas ni tablas de otros servicios por compartir servidor y base. El propietario estructural `rh_shared_owner` no inicia sesión. Compartir la base no exige compartir una credencial con permisos totales.

La coordinación HTTP y la recuperación de reservas existentes se conservan. Este cambio no convierte automáticamente todas las llamadas entre servicios en una única transacción. Sí permite integridad referencial y consultas/transacciones compartidas con permisos explícitos. Los clientes siguen consumiendo API.

## Diferencias respecto de main y de la propuesta inicial

Base fijada: `main` local, commit `44eeaf90c445b4d9564c2f0ab2dd3167f0296418`, esquema inicial y migraciones 002–004. Contiene **45 tablas**. Se conservan esas tablas y sus identificadores, agregando **26 tablas: 71 físicas en total**.

La propuesta preliminar de 60 tablas no cubría todos los contratos actuales. La adaptación ejecutable incorpora también recuperación de operaciones, deduplicación, historial de transiciones, cadenas, catálogos y versiones técnicas. No se borran datos del entorno anterior para hacerlo encajar en esa propuesta.

Tablas agregadas: `algorithm_run`, `allocation_operation`, `appointment`, `balance_proposal`, `blood_review`, `cache_revision`, `campaign`, `catalogue_entry`, `custody_chain`, `notification`, `ranking_run`, `request_hold`, `resource_review`, `schema_migration`, `service_activity_events`, `service_decisions`, `service_health_check`, `service_idempotency`, `service_inbox`, `service_outbox`, `service_schema_version`, `service_worker_health`, `shipment_transition`, `site_schedule`, `stored_file` y `transport_telemetry`.

Las cuatro tablas provisionales `event_inbox`, `event_outbox`, `request_idempotency` y `service_worker_health` se sustituyen durante la generación vacía por sus versiones operativas `service_*`. No son tablas que se eliminen de una instalación en uso.

## Adaptación de tablas existentes

| Tabla de main | Uso actual y cambios |
| --- | --- |
| `institution` | Identidad institucional compartida; añade región UUID, estado booleano y creador. |
| `user_account` | Conserva ID y hash; añade nombre de acceso, institución, perfil y estado booleano. Los campos de identidad de main no disponibles en el origen no se inventan. |
| `web_session` | Sesiones de identidad, con los mismos IDs y expiraciones del origen. |
| `donor`, `donor_review` | Expediente, cuenta de donante y dictámenes; el folio mantiene unicidad por institución. |
| `donation`, `donation_event` | Tipo de recurso, componente, grupo, estados y eventos de procesamiento actuales. |
| `recipient`, `blood_request` | Conservan expedientes y solicitudes; incorporan `kind`, órgano y prioridad numérica. Aunque la tabla heredada se llama `blood_request`, la API distingue explícitamente sangre/órganos mediante `kind`. |
| `resource` | Registro operativo de inventario: tipo, institución actual, donación, componente, grupo, vencimiento, ubicación y estado. |
| `blood_allocation`, `blood_movement` | Reservas y movimientos de la API actual, con referencias a solicitud, receptor, recurso, evaluación y ruta. El nombre heredado tampoco elimina la distinción por tipo del recurso relacionado. |
| `candidate_evaluation`, `regional_route` | Evaluaciones con entradas/resultados y rutas versionadas compartidas. |
| `shipment` | Traslados vinculados a la reserva, instituciones y transportista; estado, secuencia, caducidad y recuperación. |
| `custody_event` | Eventos originales con secuencia, contenido y hashes; no se recalculan hashes durante la copia. |
| `audit_event` | Conserva ID, actor e institución; incorpora fuente, región UUID y evento minimizado. |
| `parameter_version`, `blood_status_transition` | Renombra la etiqueta técnica redundante a `is_illustrative`, sin atribuir validación clínica. |

Las columnas de main que las API actuales no capturan permanecen como antecedentes opcionales. Se retira su obligatoriedad cuando no existe un valor de origen; no se rellenan campos médicos con valores ficticios para satisfacer una restricción. Se conservan las tablas históricas detalladas de sangre y órganos, pero los nuevos servicios usan los registros operativos identificados en la tabla anterior. No existe doble escritura del inventario en `resource` y `blood_unit`/`organ_offer`.

Las restricciones de columnas operativas se reconstruyen desde las migraciones vigentes de los servicios y se añaden relaciones entre módulos. Los campos y estados antiguos no deben interpretarse como la fuente operativa de las API actuales. La vista antigua `blood_inventory` se retira; las consultas vigentes usan `access_inventario.resources`. Los algoritmos, autorizaciones clínicas y contratos no se sustituyen por los defaults del monolito.

El detalle reproducible de cada nombre/columna está en [shared.py](../../apps/services/redhouse/shared.py); la construcción de columnas, restricciones, índices y vistas está en [shared_schema.py](../../apps/services/redhouse/shared_schema.py).

## Colas, permisos y caché

Los registros comunes `service_*` incluyen el servicio en sus claves. Las vistas filtran ese ámbito y sus inserciones lo fijan explícitamente. Un worker no puede consumir entregas ni latidos de otro. Las funciones de inserción usan `SECURITY DEFINER`, rutas SQL calificadas y `search_path=pg_catalog`; las credenciales de aplicación no tienen privilegios sobre las tablas físicas.

Los historiales inmutables mantienen restricciones y revocación de UPDATE/DELETE. La versión de esquema es de solo lectura para credenciales de ejecución. La caché conserva revisiones independientes `catalogues` e `inventory`, actualizadas en la misma transacción que los datos.

## Monitoreo cuando PostgreSQL falla

Monitoreo guarda primero cada sondeo en MongoDB, antes de intentar persistirlo en PostgreSQL. Si MongoDB falla pero SQL funciona, deja la entrega pendiente en outbox. El endpoint de estado puede consultar MongoDB cuando PostgreSQL está inaccesible. Conserva JWT, permisos y validación de sesión Redis; una falla simultánea de Redis puede impedir consultar ese endpoint protegido. Si ambos almacenes están caídos, el proceso registra el fallo técnico en logs; no promete persistencia histórica íntegra en ese caso.

## Generar y verificar

```sh
apps/services/.venv/bin/python scripts/build_shared_schema.py
apps/services/.venv/bin/python scripts/build_shared_schema.py --check
```

[El SQL resultante](../../data/database/schema.sql) instala una base **vacía**. El generador reconstruye main, aplica `shared/005_services.sql` y adapta las tablas mediante `shared_schema.py`. Las migraciones antiguas de los servicios sirven de especificación de sus contratos de almacenamiento; no se aplican sobre las vistas en cada arranque. Se necesita el commit base en Git y PostgreSQL 14 con sus herramientas; `--pg-bin` permite elegir la instalación.

## Trasladar el entorno de once bases

El [migrador](../../apps/services/scripts/migrate_shared.py) requiere APIs, portal y workers detenidos; PostgreSQL debe permanecer iniciado. Crea respaldos privados de las once bases y configuraciones, construye una base destino nueva, copia datos conservando IDs, contraseñas hasheadas, fechas y eventos, y compara el contenido de cada tabla visible para cada servicio. Solo publica las conexiones cuando toda la copia y las claves foráneas son válidas.

```sh
apps/services/.venv/bin/python apps/services/scripts/migrate_shared.py --directory .local/runtime
```

No sobrescribe un destino existente ni borra bases anteriores. Una repetición sobre un entorno ya migrado no duplica registros. El respaldo incluye configuración anterior y comparación de filas. Para revertir, detener procesos y restaurar esas configuraciones junto con la versión anterior del código; las bases de origen permanecen disponibles. Cualquier escritura posterior al cambio requiere reconciliación antes de volver al origen.

Este migrador convierte el entorno de once bases de microservicios; no es un importador automático de una base monolítica de main que contenga otros datos. Tampoco modifica MongoDB, Redis ni las sesiones privadas del portal.

## Estado comprobado del entorno local

Conversión ejecutada el 15 de octubre de 2026: 111 tablas de origen, 118 428 filas comparadas sin diferencias y once conexiones verificadas hacia `red_house`. Los once servicios y el portal respondieron 200; las 18 cadenas de custodia conservaron sus hashes. Los once respaldos se restauraron satisfactoriamente en bases temporales. La regresión obtuvo 169/171 aprobados; los dos casos con 503 en preparación de sesión pasaron al repetirse aislados. Véase [estado, resultados y limitaciones](../../PROJECT_STATUS.md#migración-operativa-a-una-base-compartida-15-de-octubre).
