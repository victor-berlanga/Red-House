# Migración 21 y recuperación de cola conservada — 16 de noviembre de 2026

**Resultado: exit 0.** La cola global pasó de 5.733 pendientes a cero. La observación de cola vacía ocurrió a los **75,284 s**, antes del límite de 120 s. Se solicitó parada a los 75,290 s; el tramo medido y cierre de workers terminó a los 79,209 s. El recibo final confirma el cierre de todos los procesos propios, fuentes estables y originales preservados.

## Alcance y preparación

Raíz ejecutó el runner revisado sobre el fixture sintético conservado, sin repoblar ni generar nuevas transacciones de cliente. Se iniciaron PostgreSQL, MongoDB y Redis propios, APIs Auditoría/Alertas y workers Donantes/Auditoría. Se conservaron cuotas, orden de entrega y reintentos. El límite fue 120 s, con corte de 30 s sin progreso; no se amplió. Las APIs mantuvieron pool 0 y cada worker pool 1.

El primer intento terminó con `AssertionError` durante el preflight, antes del respaldo nuevo, DDL y arranque de workers. PostgreSQL propio cerró. El runner exigía versiones 6–20, aunque el esquema base conserva 1–5. Se corrigió únicamente esa guarda a 1–20 y se añadieron frames sanitizados para errores futuros. El primer recibo no contiene traceback: no se atribuye retrospectivamente una línea exacta. Su resultado fallido permanece separado en `preparacion-fallida.json`.

La revisión automática rechazó inicialmente el reintento por contexto de autorización incompleto, antes de crear procesos. Raíz presentó el alcance verificable y la autorización previa del usuario para continuar el plan: fixture sintético local, respaldo, sin producción ni GCP. La misma ejecución recibió aprobación automática; no quedó pendiente una nueva aprobación humana.

## Conservación y migración

La copia fría se verificó contra su manifiesto: 2.002 archivos y 475.286.188 bytes, hashes coincidentes. No fue necesario restaurarla. Antes de migrar se creó un respaldo lógico privado de 12.803.622 bytes; `pg_restore --list` pudo leerlo. Su SHA-256 está en `recuperacion.json`. Este control no equivale a un ensayo de restauración del respaldo nuevo.

La conexión administrativa usó la base `red_house` del PostgreSQL propio. El migrador oficial `redhouse.shared_migrations.upgrade` se ejecutó con `SET ROLE rh_shared_owner` dentro de una transacción. Se comprobaron:

- Historial anterior 1–20 intacto, incluida descripción y fecha; única fila nueva, versión 21.
- Las 180.888 filas de 115 tablas físicas conservaron sus huellas lógicas antes/después de la migración. `schema_migration` se comprobó por separado.
- Se conservaron todos los índices anteriores del outbox. Único añadido: `shared_outbox_dispatch_order`, B-tree parcial `(service,created_at,id) WHERE delivered_at IS NULL`, propiedad de `rh_shared_owner`.
- Segunda invocación del migrador en la misma transacción devolvió 21 sin repetir DDL ni modificar el historial; después se confirmó la transacción.

Las huellas de filas usan SHA-256 sobre MD5 ordenados de `row_to_json`. Verifican conservación lógica; no son una copia física. Las filas del outbox cambiaron después, durante el drenado autorizado.

## Drenado y oráculos

| Control | Antes | Después |
|---|---:|---:|
| Cola global pendiente | 5.733 | 0 |
| Pendientes de otros servicios | 0 | 0 |
| Eventos originales presentes en Auditoría | 765/765 | 765/765 |
| Avisos originales, sin faltantes ni extras | 121/121 | 121/121 |
| Proyección Mongo de esos eventos | 0/765 | 765/765 |

Las entregas completadas aumentaron en 6.072: 5.733 hacia Mongo y 339 hacia Auditoría. Estas últimas generaron 339 entradas auxiliares `READ` hacia Mongo, también drenadas. No hubo nuevas transacciones de cliente; sí hubo esas escrituras auxiliares. No se observaron nuevos eventos de actividad ni recordatorios modificados/eliminados durante la recuperación. No quedaron destinos pendientes sin consumidor.

Los oráculos PostgreSQL correlacionan acción, recurso y actor de los intentos originales reconciliados, y recurso/destinatario de los avisos. Mongo comprueba presencia por `_id` de los 765 eventos correlacionados; este recibo no compara todo su payload. La muestra anterior al deadline ya contiene cola global vacía y los oráculos completos. El resultado no depende de entregas terminadas durante el cierre.

Las 64 fuentes capturadas y los 36 archivos originales protegidos conservaron sus hashes. No hubo procesos propios remanentes ni cierre forzado registrado. Se devolvió la ventana pesada para compilación móvil.

## Límites y continuidad

Esta ejecución acredita migración local y recuperación de la cola conservada con el índice justificado por el [benchmark previo](../worker-index-benchmark-20261116/RESULTADOS.md). Incluye los cambios anteriores de cadencia y pool; no es una comparación aislada del índice.

La carga transaccional original y los drenados anteriores conservan sus resultados fallidos. **No se repitió Locust ni se demuestra todavía la propagación dentro del plazo durante una nueva carga concurrente.** Tampoco se migró o publicó GCP. Los recibos completos, respaldo y logs permanecen privados; los JSON adjuntos contienen solo agregados, definiciones de índices y huellas.
