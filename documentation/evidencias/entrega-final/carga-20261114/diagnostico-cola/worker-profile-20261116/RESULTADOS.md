# Perfil de diez entregas reales — 16 de noviembre de 2026

Resultado: **10/10 entregas confirmadas; exit 0 del diagnóstico**. Esto no cambia el resultado fallido de la carga ni de las dos recuperaciones limitadas anteriores. La cola continúa pendiente.

Se reutilizó el laboratorio conservado, sin repoblar. Se arrancaron únicamente PostgreSQL, MongoDB, Redis y la API de Auditoría necesaria para una entrega dirigida a ese servicio. No hubo workers automáticos ni carga de usuarios. Cada llamada real `events.dispatch(limit=1)` conservó orden, bloqueo, reintentos y contenido del producto. El pool SQL se fijó a 1 solo en memoria, como el valor predeterminado del worker revisado.

## Medición

| Segmento | Mediana de las diez entregas |
|---|---:|
| Adquisición SQL | 0,401 ms |
| Ejecución SELECT | 30,985 ms |
| Decodificación de fila | 0,109 ms |
| UPDATE | 9,709 ms |
| Commit y devolución al pool | 1,227 ms |
| Total | 57,293 ms |

Las diez operaciones reutilizaron una conexión SQL. El preflight ya había calentado el pool; esta serie no mide conexión SQL fría. Nueve entregas fueron hacia MongoDB. Su primera llamada tardó 27,367 ms; las ocho siguientes tuvieron mediana de 1,568 ms. La única entrega HTTP a Auditoría tardó 143,918 ms en ese segmento; una muestra no permite generalizar su rendimiento. Los tiempos de Python incluyen espera del cliente y del servidor; no equivalen a CPU SQL aislada.

El plan real de `SELECT * FROM outbox ... ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1` utiliza `Seq Scan` sobre `red_house.service_outbox`, seguido de `Sort(created_at,id)`. Se repite para cada entrega. El índice parcial existente `shared_outbox_pending(service,next_attempt,created_at)` no satisface ese orden. El UPDATE utiliza la clave primaria `(service,id)`. EXPLAIN se ejecutó sin ANALYZE; no se ejecutaron UPDATE de diagnóstico.

Se observaron `synchronous_commit=on`, `fsync=on`, `full_page_writes=on` y `max_connections=100`. No se modificaron durabilidad, cuotas, configuración persistente ni fuentes.

## Oráculos y cierre

Las nueve proyecciones MongoDB coincidieron exactamente con el evento original y su `_id`. La entrega a Auditoría tuvo una única entrada inbox por event_id. Las diez filas terminaron entregadas, con attempts=1 y sin last_error.

La cola pendiente de Auditoría pasó de 5.742 a 5.733: MongoDB 5.402 a 5.394 y destino Auditoría 340 a 339. Se entregaron diez filas; consumir la dirigida a Auditoría generó una nueva proyección MongoDB. Este diagnóstico no repitió transacciones de negocio.

El recibo privado conserva identificadores y correlaciones; `perfil.json` publica tiempos, planes, conteos y hashes saneados. Los originales protegidos y las 63 fuentes capturadas conservaron sus hashes. Todos los procesos propios cerraron.

## Siguiente discriminante

Preparar, sin aplicarlo al producto, un índice parcial experimental `(service,created_at,id) WHERE delivered_at IS NULL`. Comparar el SELECT exacto antes y después sobre la misma cola, con rollback, planes y diez muestras calientes por condición. Eliminar únicamente ese índice experimental al terminar. Mantener el índice histórico, el filtro next_attempt, el orden y FOR UPDATE SKIP LOCKED. La mejora sigue siendo una hipótesis hasta medirla; este perfil no aprueba una migración ni declara resuelta la propagación bajo carga.
