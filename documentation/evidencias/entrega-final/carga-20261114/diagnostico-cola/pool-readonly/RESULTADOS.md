# Discriminante SQL de solo lectura: pool 0 frente a 1

**20/20 transacciones medidas**, diez por modalidad, usando `connection_scope()` real, la misma credencial runtime `rh_auditoria` y configuración del fixture conservado. Solo PostgreSQL propio; sin API, MongoDB, entregas ni escrituras de negocio. Se alternó el orden por pareja. `SET TRANSACTION READ ONLY` precedió a la consulta y cada fila verificó rol, base `red_house`, esquema `access_auditoria` y modo de solo lectura. [Recibo y muestras](receipt.json).

| Modalidad | PID distintos | Mediana caliente adquisición | Mediana SELECT | Mediana total |
|---|---:|---:|---:|---:|
| Pool 0 | 10 | 17,426911 ms | 1,299756 ms | 20,282372 ms |
| Pool 1 | 1 | 0,533613 ms | 0,484290 ms | 1,941899 ms |

Las medianas calientes usan las nueve operaciones posteriores a la primera de cada modalidad. Primera fría: 45,035684 ms total sin pool, 60,508733 ms con pool; la segunda incluye su creación inicial. El pool ya existente conservó `min_size=0`, máximo 1 conexión, espera de adquisición 2 s, comprobación de conexión, inactividad 30 s y un hilo de mantenimiento. No se alteraron las consultas ni los timeouts del producto.

El pool y PostgreSQL cerraron sin procesos restantes; configuraciones, fuentes y resúmenes originales conservan sus hashes. Iniciar PostgreSQL puede modificar sus archivos internos: «solo lectura» describe las transacciones, no una promesa de inmovilidad binaria de los archivos del motor. No se modificó ningún JSON de configuración.

`psycopg` 3.3.5 y `psycopg_pool` 3.3.3 ya están instalados. `apps/services/requirements.txt` exige `psycopg_pool>=3.3,<4`; el archivo de versiones verificadas fija 3.3.3. No hace falta una dependencia nueva. La configuración original no define `DATABASE_POOL_SIZE`; `settings()` tampoco añade esa clave y `connection_scope()` usa 0 por defecto.

El resultado confirma un coste evitable de conexión en este entorno. No atribuye todo el tiempo del drenado a ese coste ni demuestra aún capacidad de entrega con pool. La propuesta posterior se limita al proceso worker con máximo una conexión reutilizable; no cambia las APIs ni activa pools globales. **No aplicada en este discriminante.**
