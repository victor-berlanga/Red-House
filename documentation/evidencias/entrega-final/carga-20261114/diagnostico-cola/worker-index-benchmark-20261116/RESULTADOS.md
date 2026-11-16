# Índice del outbox: discriminante reversible — 16 de noviembre de 2026

**Resultado: exit 0, comparación válida.** La mediana del SELECT exacto con lectura de fila pasó de **31,618 ms a 0,822 ms**: 38,45 veces más rápido, reducción del 97,40 %. Esta medición justifica preparar el índice aditivo; no demuestra todavía un drenado completo ni el rendimiento de todos los destinos.

## Alcance

Una sola ejecución efectiva sobre PostgreSQL propio del laboratorio conservado. No se arrancaron MongoDB, Redis, APIs ni workers. No hubo entregas ni nuevas transacciones de negocio. Antes de arrancar hubo un fallo de preparación: la guarda confundía `database_owners` (bootstrap del fixture) con `DATABASE_URL` (rol de servicio). Se corrigió únicamente el script privado para validar ambos por separado; el log fallido se conserva.

Se ejecutó el SELECT literal de `events.dispatch`, comprobado contra su fuente actual, bajo el rol `rh_auditoria` y pool 1 en memoria:

```sql
SELECT * FROM outbox
WHERE delivered_at IS NULL AND next_attempt<=now()
AND NOT(target=ANY(%s))
ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1
```

Los parámetros fueron una lista vacía de destinos bloqueados, igual que al iniciar un lote. Cada SELECT utilizó una transacción con rollback inmediato. Cada condición tuvo un calentamiento excluido y diez muestras calientes. Todas seleccionaron la misma cabeza. Los EXPLAIN se obtuvieron sin ANALYZE. No se alteraron orden, filtro de reintento, bloqueo, configuración persistente ni índices existentes.

| Medición | Antes | Con índice experimental |
|---|---:|---:|
| Mediana de execute | 31,501 ms | 0,740 ms |
| Mediana de lectura/decodificación | 0,103 ms | 0,079 ms |
| Mediana total de SELECT y fila | 31,618 ms | 0,822 ms |
| Calentamiento excluido, total | 72,900 ms | 1,115 ms |

Los tiempos son del cliente y servidor combinados. El orden de condiciones fue antes/después, sin alternancia. El resultado corresponde a la cabeza actual, sin contención y con destinos desbloqueados; no generaliza a un lote lleno de reintentos futuros o destinos fallidos.

## Plan y reversión

El plan anterior utilizó `Seq Scan` y `Sort(created_at,id)`. Con el índice parcial experimental `(service,created_at,id) WHERE delivered_at IS NULL`, PostgreSQL eligió `Index Scan`, sin ordenación. Crear ese índice tardó 66,841 ms sobre este fixture.

Al terminar se eliminó exclusivamente `rh_profile_outbox_order_20261116`. El catálogo de índices coincidió exactamente con el inicial. Las **26.652 filas** de `service_outbox` conservaron la huella lógica ordenada, incluyendo sus payloads. La verificación usa SHA-256 de los MD5 de `row_to_json`, ordenados por service/id; no publica los contenidos.

Los originales protegidos y las fuentes conservaron sus hashes. PostgreSQL propio cerró; no quedaron procesos propios ni errores de limpieza. El recibo privado conserva identificadores y PID; `benchmark.json` los omite. La ventana se devolvió a raíz.

## Siguiente cambio propuesto

Migración aditiva para un índice parcial estable `(service,created_at,id) WHERE delivered_at IS NULL`, conservando el índice por next_attempt y la consulta actual. La migración está preparada en fuente; siguen pendientes revisión, aplicación PostgreSQL y recuperación limitada real. No se modifica la aceptación fallida de la carga original ni de los drenados anteriores.

## Migración preparada después de medir

`apps/services/redhouse/shared_migrations/021.sql` agrega `shared_outbox_dispatch_order` con la definición medida y registra versión 21. `shared_migrations.LATEST_VERSION` pasa a 21. El índice anterior permanece. No se modifican tablas, filas, vistas, permisos, orden ni reintentos en este incremento SQL.

El mecanismo existente aplica migraciones pendientes dentro de la transacción del llamador y adquiere un advisory lock. El actualizador administrativo usa `SET ROLE rh_shared_owner`; el índice pertenece al propietario de la tabla. No se conceden privilegios DDL a credenciales runtime. Se mantiene CREATE INDEX transaccional, sin CONCURRENTLY, coherente con ese mecanismo; su bloqueo durante creación debe considerarse al asignar ventana. La medición de 66,841 ms corresponde solo al fixture actual.

Tres pruebas puras comprobaron selección y omisión al reanudar, propagación de fallo antes de actualizar vistas/permisos y rechazo de una versión posterior desconocida. Pasaron en 0,15 s; Ruff y diff-check limpios. Estas pruebas no acreditan ejecución SQL ni sustituyen el ensayo PostgreSQL pendiente. El comprobador de salud pasa a exigir esquema 21: antes de iniciar APIs/worker nuevos sobre el fixture 20 se deberá aplicar la migración administrativa, conservando población y recibos fallidos.
