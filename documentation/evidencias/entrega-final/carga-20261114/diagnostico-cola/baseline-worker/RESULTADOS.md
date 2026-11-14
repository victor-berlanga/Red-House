# Entregas baseline y parche de cadencia — 14/11/2026

Dos diagnósticos reales y separados sobre la población conservada entregaron **una fila cada uno**, antes de aplicar el parche. No son una repetición de carga ni convierten su resultado original fallido en aprobado. Configuración y cuotas originales; orden de selección y `dispatch(limit=1)` del producto, con lectura de cabeza mediante `redhouse.db.transaction()` y credencial runtime del servicio.

| Servicio | Resultado baseline | Persistencia antes → después |
|---|---|---|
| [Auditoría → MongoDB](auditoria.json) | 1 entregada, 0 fallos; 0,158018 s | Cabeza histórica con `mongodb_unavailable`, attempts 1 → 2 y delivered. Objeto Mongo ausente → presente con payload exacto. Pendientes hacia Mongo 6993 → 6992. Insert Mongo real: 20,515 ms. |
| [Donantes → Auditoría](donantes.json) | 1 entregada, 0 fallos; 0,197205 s | Cabeza real hacia Auditoría; inbox 0 → 1, attempts 0 → 1 y delivered. Pendientes a Auditoría 460 → 459. Las 175 entregas pendientes hacia Alertas no se tocaron. |

Auditoría inició solo PostgreSQL/MongoDB; Donantes PostgreSQL/Redis y APIs Auditoría/Alertas. Sin workers autónomos, usuarios nuevos, resembrado o nuevas transacciones de cliente. Ambas ejecuciones cerraron todos sus procesos propios y conservaron los hashes de manifiesto, estado, recibos originales y fuentes. Los diagnósticos sí mutaron las entregas indicadas y sus proyecciones/inbox; no se describen como READ ONLY. Las consultas de verificación fueron READ ONLY. Credenciales, payloads e identificadores de cabeza permanecen privados.

La distribución de `delivered_at` aclara el retraso histórico: antes de estos diagnósticos, Auditoría había entregado **381 filas hacia Mongo y 40 hacia sí misma** desde el inicio de la carga transaccional. La última entrega Mongo fue a las 20:58:37,308566 UTC. Donantes había entregado 190 hacia Alertas y 510 hacia Auditoría en ese período. Por tanto, una cabeza antigua al cierre no prueba que esa misma cabeza permaneciera bloqueada durante todos los heartbeats. Los payloads y permisos de estas dos entregas funcionan ahora; no se infiere causalidad única, capacidad sostenida ni integridad de toda la cola a partir de ellas.

## Parche aplicado; recuperación real pendiente

El worker ya no duerme cinco segundos después de cada lote lleno que progresa. Tras procesar al menos 100 filas con alguna entrega exitosa, espera 0,1 s. Las vueltas adicionales ejecutan únicamente outbox/heartbeat; recordatorios, recuperación, exportaciones y sondeos conservan su planificación ordinaria. Un lote incompleto, sin progreso o una excepción espera el intervalo ordinario completo, incluso si el despacho cruzó el siguiente vencimiento. Se mantiene un hilo por worker y los bloqueos, deduplicación y reintentos existentes.

[13 pruebas puras](parche-junit.xml) aprobaron en 0,31 s (JUnit 0,302 s); cubren lotes llenos/parciales, cero progreso, error, parada, tareas periódicas y despacho lento que cruza el vencimiento. [Fuentes del parche](parche-fuentes.json). No hubo motores durante esas pruebas. Esto acredita el control de cadencia, **no todavía su mejora de rendimiento o recuperación real**. Sin publicación GCP.

La recuperación preparada conserva la misma población y no genera transacciones nuevas de cliente. Arrancará solo workers Donantes/Auditoría y sus destinatarios necesarios. Se observarán por separado cola pertinente, cola global y cualquier fila de otro servicio sin worker. El último inventario global solo tenía pendientes de Donantes/Auditoría, pero se verificará otra vez antes del drenado. Eventos y recordatorios que produzcan los trabajos periódicos se registrarán aparte: no se promete cero escrituras auxiliares.

Ventana máxima de observación: 120 s; corte a los 30 s sin progreso pertinente. No se ampliará automáticamente. El oráculo conserva los intentos originales y separa los 175 eventos de negocio/57 avisos inicialmente faltantes de las miles de entregas históricas. La proyección Mongo se comprobará por los IDs de negocio correlacionados. Cola pertinente vacía no equivale a cola global vacía si aparecen otros servicios. Cualquier recuperación posterior se documentará separada del ensayo original y de estas dos entregas baseline.
