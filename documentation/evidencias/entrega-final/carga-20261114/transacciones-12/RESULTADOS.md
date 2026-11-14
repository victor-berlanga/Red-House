# Carga transaccional de doce identidades — 14/11/2026

**Resultado integral fallido por propagación pendiente.** Locust terminó con código 0; el comprobador final terminó con código 1 porque faltaron eventos en Auditoría y avisos después de los 30 segundos previstos. No se cambia el oráculo ni se amplía ese plazo. [Métricas originales](metricas.json), [diagnóstico posterior READ ONLY](diagnostico-eventos.json).

## Preparación y alcance

Se conservó la población de la serie previa: 2.000 donantes, 10.000 recursos y 100.000 eventos SQL. Se añadieron una sola vez doce cuentas sintéticas independientes, seis expedientes, una sede del catálogo, una campaña, dos horarios y un perfil DRAFT sin habilitación clínica. La preparación real y su reanudación conservaron cantidades y manifiesto: [recibo](preparacion.json).

Dos intentos anteriores terminaron antes de iniciar usuarios: [sede en tabla histórica incompatible con la FK](transactions-20261114T204712Z.log) y [comparación textual de UTC con hora de Monterrey](transactions-20261114T205124Z.log). Ambos se conservan. La corrección usa el catálogo vigente y compara instantes completos con zona y microsegundos. Nueve pruebas puras dirigidas aprobaron en 0,72 s; no sustituyen la preparación real posterior.

Seis donantes JSON consultaron, reservaron, reprogramaron y cancelaron citas; seis operadores XML/XSD registraron unidades en cuarentena y muestras, recibieron las muestras y consultaron el resultado. Se mantuvieron cuotas, usuarios runtime y validación de contratos. Diario de intentos privado. La [topología](topologia.json) usa procesos locales reales, sin TESTING; no mide GCP ni TLS público. No se modificaron reglas clínicas.

## Medición

Calentamiento de 30 segundos mínimos: doce usuarios disponibles, 396 solicitudes y cero fallos. Medición de **120,0118 segundos**, seguida de drenado separado.

| Medida | Resultado |
| --- | --- |
| HTTP durante medición | 1.291 peticiones, cero fallos, 10,7573 peticiones/s |
| Recorridos completos dentro de medición | 199; 1,6582 recorridos/s |
| Mayor p95 de GET | 500 ms; objetivo inferior a 2.000 ms |
| Operador | 105 recorridos; media 1.813,1 ms, mediana 1.800, p95 2.600, p99 3.100 |
| Donante | 94 recorridos; media 2.499,5 ms, mediana 2.500, p95 3.300, p99 4.000 |
| Objetivo por recorrido | p95 inferior a 5.000 ms; ambos cumplieron |
| Respuestas 429 | 0 |

[Filas por método/operación](measurement.json), [CSV final](run_stats.csv), [historia CSV](run_stats_history.csv), [fase y límites temporales](phase.json). HTTP y recorridos no se suman como peticiones. Los diccionarios históricos `counts`/`measurement_counts` usan solo el nombre y colisionan entre TRANSACTION/DRAIN; los recorridos se obtienen de las filas TRANSACTION, `business_completed` y la conciliación del diario, coincidentes en 199. CSV con celdas idénticas tras normalizar CRLF a LF; [huellas originales](originales-sha256.json).

Incluidos calentamiento y drenado: **765 intentos comprometidos**, cero inciertos/sin confirmar, 255 ciclos completos (121 donante y 134 operador), doce repeticiones idempotentes confirmadas. Doce familias nuevas revocadas y ausentes en Redis. La validación de filas, versiones, identidades y efectos extra no produjo errores; el único error final fue `event_propagation`.

## Propagación pendiente real

La lectura posterior no inició workers ni repitió escrituras. Faltaban en Auditoría **175 eventos de Donantes**: 57 reservas, 59 reprogramaciones y 59 cancelaciones. Los eventos de origen existen una vez con actor, recurso y acción esperados. Había **64 de 121 avisos** esperados. Inventario y Compatibilidad tenían sus 134 altas, 134 muestras y 134 recepciones en Auditoría.

Para el conjunto consultado, el outbox conservaba 292 entregas pendientes de Donantes a Auditoría, 175 a Alertas y 1.119 de Auditoría a MongoDB, sin intento registrado ni error. Incluyen lecturas auditadas, por lo que no equivalen uno a uno a los 175 eventos de negocio faltantes. Esto demuestra cola pendiente, sin demostrar pérdida. La consulta se limitó a recursos de esta corrida; no descarta una cola global anterior. Causa y recuperación requieren comprobación posterior separada.

Resúmenes fallidos y diagnóstico intactos. La [salida del comprobador](transactions-20261114T205421Z.log) conserva el fallo. Una recuperación posterior no convertirá retroactivamente esta medición en aprobada.

## Recursos y límites

72 muestras: mínimo libre de disco 10.226.216.960 bytes, máximo propio 509.516.435 bytes y máximo RSS sumado 2.348.320 KiB. RSS puede contar memoria compartida varias veces. Generador, diario con fsync y servicios comparten equipo; no se atribuye todo su coste al servidor.

Las [946 fuentes y huellas de runtime/configuración](fuentes.json) permanecieron iguales. El alcance excluye archivos ocultos, enlaces y otros productos; no representa todo el monorepo. Procesos de carga y PostgreSQL del diagnóstico cerrados. No se repitió la serie de lectura ni se midieron reservas clínicas, custodia, GPS o volumen Mongo. Etapa 07 sigue abierta.
