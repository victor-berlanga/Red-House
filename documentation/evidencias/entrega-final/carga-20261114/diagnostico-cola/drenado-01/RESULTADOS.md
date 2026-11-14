# Recuperación acotada de cola: parcial, exit 1

El 14/11/2026 se ejecutó una recuperación sobre la misma población conservada, con el parche de cadencia y las configuraciones originales, sin nuevas transacciones de cliente. **Terminó por límite de observación y conservó exit 1: la recuperación completa no está aprobada.** [Recibo saneado](receipt.json).

Workers reales Donantes/Auditoría; APIs Auditoría/Alertas; PostgreSQL, Redis y MongoDB propios. No Locust, nuevas cuentas, resembrado ni cambios de cuotas. El límite programado fue 120 s y 30 s sin progreso. La última muestra terminó a los 122,811 s por el intervalo de muestreo y la consulta; luego se solicitó parada y se permitió concluir el lote en curso. El total hasta cierre de workers fue 136,792 s. Se documenta este exceso de granularidad y cierre; no se extendió la observación ni se repitió la corrida. Todos los procesos propios terminaron sin kill forzado. Fuentes y artefactos originales sin cambios.

| Resultado | Antes | Después |
|---|---:|---:|
| Cola global y pertinente pendiente | 8192 | 7469 |
| Pendientes de otros servicios | 0 | 0 |
| Donantes → Auditoría | 459 | 0 |
| Donantes → Alertas | 175 | 0 |
| Auditoría → Auditoría | 565 | 513 |
| Auditoría → Mongo | 6993 | 6956 |
| Eventos de negocio faltantes | 175 | 0 |
| Avisos de negocio faltantes | 57 | 0 |
| Proyección Mongo de los 765 eventos de negocio | 0 | 0 |

Se comprobaron **765/765 eventos SQL y 121/121 avisos**, sin duplicados o avisos extra; la primera muestra completa de negocio fue a los 111,912 s. La FIFO histórica de Auditoría todavía precede a esos eventos en Mongo: esto no acepta su proyección eventual ni el ensayo original de carga.

Hubo 1234 entregas: Donantes 634 (459 a Auditoría y 175 a Alertas), Auditoría 600 (548 a Mongo y 52 a sí misma). La propagación añadió 511 filas a la outbox Mongo: 175 de acciones de citas y 336 READ. Balance: `8192 + 511 - 1234 = 7469`. Cero eventos de origen nuevos y cero recordatorios insertados/actualizados/eliminados durante el corte SQL observado. Los heartbeats sí se escribieron; no se afirma cero escrituras auxiliares.

Ritmo agregado, incluyendo cierre: aproximadamente 9,02 entregas/s; Auditoría 4,39/s. No son capacidad bajo carga ni comparación controlada con la versión anterior. Ambos heartbeats finales carecen de error. Auditoría mantuvo sus tres líneas históricas de error y Donantes su log vacío; no se observó un nuevo error técnico del worker. El resultado concreto es progreso insuficiente para vaciar el histórico en esta ventana, no pérdida de eventos ni bloqueo permanente de la cabeza.

La revisión posterior confirmó que las aplicaciones de worker seguían con pool SQL efectivo 0: una conexión por transacción. El [discriminante READ ONLY](../pool-readonly/RESULTADOS.md) separa ese coste sin modificar ni volver a drenar la cola.
