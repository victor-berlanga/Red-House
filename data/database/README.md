# Base de datos compartida

[**schema.sql**](schema.sql) es el esquema ejecutable para una base PostgreSQL vacía: **107 tablas físicas de dominio** en `red_house`, con vistas `access_*` para los doce servicios. Estas vistas no guardan datos separados. La configuración nueva conecta todos los servicios a la base `red_house`, con credenciales y permisos distintos.

El esquema conserva las 45 tablas de main, ampliadas para los contratos actuales, y agrega 26. La propuesta preliminar de 60 tablas fue ajustada durante la integración. [Detalle de tablas, columnas y límites](../../documentation/markdowns/Esquema_compartido.md).

## Fuentes y generación

- Main fijado en `44eeaf90c445b4d9564c2f0ab2dd3167f0296418`: esquema inicial y migraciones 002–004.
- [Ampliación inicial](shared/005_services.sql).
- [Correspondencia de tablas y columnas](../../apps/services/redhouse/shared.py).
- [Adaptación ejecutable de tablas, claves, índices y vistas](../../apps/services/redhouse/shared_schema.py).
- Migraciones históricas de los servicios: especificación de los campos que sus API consumen; se aplican en esquemas temporales durante la generación, no en cada arranque.

```sh
apps/services/.venv/bin/python scripts/build_shared_schema.py
apps/services/.venv/bin/python scripts/build_shared_schema.py --check
```

Requiere dependencias Python de servicios y herramientas PostgreSQL 14 (`initdb`, `pg_ctl`, `pg_dump`, `psql`). Admite `--pg-bin`. El generador trabaja en un clúster temporal, sin conectarse al entorno privado, y prueba la restauración del resultado. El SQL contiene catálogos estructurales, no cuentas, contraseñas ni datos clínicos. No editar manualmente el archivo generado.

## Instalación y migración

`install.sh` prepara la base compartida en instalaciones nuevas. Los BAT ejecutan el flujo dentro de WSL/Ubuntu. El entorno ya preparado de once bases requiere el [migrador](../../apps/services/scripts/migrate_shared.py), con APIs, workers y portal detenidos; PostgreSQL debe permanecer iniciado:

```sh
apps/services/.venv/bin/python apps/services/scripts/migrate_shared.py --directory .local/runtime
```

Respalda bases y configuración, conserva las bases de origen, copia registros, valida claves foráneas y compara todas las filas antes de cambiar las conexiones. No sobrescribe un destino existente. La versión nueva rechaza arrancar un entorno sin migrar para evitar mezclar configuraciones.

Los usuarios PostgreSQL y permisos los administra el instalador. Compartir base no autoriza a un servicio a leer contraseñas o modificar historiales ajenos. Los clientes web/móvil/escritorio siguen usando las API.

## Referencias anteriores

`postgresql/` conserva las once exportaciones estructurales de la distribución anterior, útiles para revisar la conversión. No son el esquema de una instalación nueva. `scripts/export_schemas.py` reproduce esas exportaciones antiguas; el generador vigente es `build_shared_schema.py`.

El [SQL del monolito original](../../documentation/historial/primer-parcial/database/schema.sql) conserva la etapa histórica. El estado operativo y la migración verificada se registran en [PROJECT_STATUS.md](../../PROJECT_STATUS.md).

## Sesiones técnicas del portal

El instalador aplica también [web_sessions.sql](web_sessions.sql): una tabla `web_runtime.session_revocations` en la misma base. Son 71 tablas del dominio y una técnica, 72 en total. La credencial `rh_web_sessions` solo consulta y modifica esta tabla; carece de acceso a los esquemas del dominio. Sesiones activas y bloqueos del portal se guardan en Redis con ACL propia.

## Corrección 0.4.1 — esquema 13

Las migraciones 012/013 protegen valores históricos de laboratorio y trasladan la propiedad documental a `access_documentos`. `stored_file`, `document_metadata`, `file_scans` y `export_jobs` conservan su única copia física; Transporte pierde sus permisos y conserva sus eventos/outbox históricos. Las claves idempotentes de operaciones documentales pasan al propietario nuevo. No se copia ni se elimina historia. [Arquitectura y fronteras](../../documentation/entrega-final/backend/correccion/Arquitectura_y_decisiones.md), [actualización y rollback](../../documentation/entrega-final/backend/correccion/Despliegue_y_rollback.md).

El ensayo de v11 a v13 incluye aplicación repetida, conservación de archivo/trabajo/idempotencia/outbox y restauración real de `pg_dump` en otra base. La matriz correctiva distingue ese ensayo de la aceptación productiva pendiente.
