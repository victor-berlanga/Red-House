# Disponibilidad regional sin consultas por unidad — 17/11/2026

El ensayo finito de tres perfiles conservó un fallo 503 en el dictamen médico. Inventario tardó 3.189 ms en responder a la consulta interna de disponibilidad; el cliente interno tiene un límite de lectura de 3 segundos. La consulta hacía una lectura adicional de controles por cada unidad. El tiempo observado y ese patrón sustentan la corrección, sin atribuir todavía resolución al recorrido HTTP completo.

`available()` ahora incorpora `lab_profile_id` mediante `LEFT JOIN resource_controls` en una sola consulta. La clave primaria de controles impide multiplicar filas. Conserva región parametrizada, estado AVAILABLE, caducidad, orden y valores nulos; no cambia permisos, contratos ni límites de tiempo. El único consumidor es el endpoint interno de disponibilidad. Una consulta observa un único snapshot; antes podían observarse cambios de controles entre sentencias bajo READ COMMITTED.

## Verificaciones

Diecisiete pruebas dirigidas aprobaron en 2,188 segundos. Incluyen tamaños 0, 3 y 400 para detectar nuevas lecturas por unidad y regresiones previas de costos. Los dobles no acreditan SQL real.

La comparación posterior usó PostgreSQL real del fixture local conservado, una transacción REPEATABLE READ READ ONLY y la misma región. Ejecutó el original y el candidato en orden alternado AB/BA. Los cuatro resultados contienen exactamente las mismas 4.502 filas, con idéntico orden, valores, tipos y 4.499 perfiles nulos.

| Par | Original, incluidas lecturas por unidad | JOIN |
| --- | ---: | ---: |
| Original antes de JOIN | 1.297,50 ms | 43,91 ms |
| JOIN antes del original | 732,73 ms | 74,14 ms |

Las listas completas se compararon antes de guardar tiempos. El hash ordenado coincide en las cuatro mediciones. Son dos comparaciones locales de SQL, no un percentil de carga ni una garantía de latencia HTTP. El tamaño del resultado regional sigue creciendo con la población.

Se inició exclusivamente PostgreSQL y se cerró con salida 0. No hubo APIs, workers, Redis ni MongoDB activos en esta comparación. La transacción terminó con rollback explícito, sin escrituras de negocio; `state.json` permaneció idéntico y se retiró el bloqueo propio.

## Continuidad y límites

El ensayo de carga fallido y sus nueve casos se conservan. Coordinación y transporte ya completaron sus preflights; el médico conserva una evaluación y un dictamen no persistido. La continuación debe conservar evaluación, cuerpo, actor y clave originales, completar la reserva pendiente y medir solo los seis casos intactos. No volver a sembrar ni reinterpretar el fallo como una medición exitosa.

[Resultados estructurados](resumen.json). Evidencia privada en `.local/artifacts/inventory-query-20261117/`, incluidos JUnit, fuentes fijadas y comparación reproducible `continuation/benchmark.py`. La aceptación del recorrido HTTP y la publicación en GCP siguen pendientes; este resultado no cierra carga ni etapa 07.
