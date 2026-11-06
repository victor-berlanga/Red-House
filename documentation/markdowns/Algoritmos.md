# Algoritmos y límites

## Fuentes públicas — 02/11/2026, 0.4.4 / esquema 16

Se conservan las versiones históricas y las políticas académicas. Nuevos registros pueden seleccionar referencias normativas versionadas y catálogo HLA 3.66.0; reconocer nombres no interpreta inmunología. Para A entradas y K declaraciones, construir índices cuesta O(A) y memoria O(A), con hasta cuatro versiones en caché. Cada petición vuelve a leer/verificar B bytes (O(B)) y consulta K nombres (O(K) esperado).

ALG-02-GEO añade `REGIONAL-OSM-DIJKSTRA-3.0`, sobre `NL-OSRM-20261102`: **tres trayectos dirigidos** entre referencias urbanas de Monterrey, San Nicolás y Guadalupe. No representan todos los cruces de Nuevo León ni accesos de hospitales. Pesos y geometrías provienen de respuestas originales OSRM/OpenStreetMap, con URL, atribución, licencia, SHA-256 y descarga. `REGIONAL-DIJKSTRA-2.0` conserva grafos sintéticos y reproducción histórica.

Importación: leer manifiesto; verificar SHA-256 por archivo; exigir respuesta válida, pesos finitos positivos y LineString acotada; convertir metros/segundos a km/minutos; registrar grafo inmutable con procedencia. La entrada genérica no permite al cliente afirmar `synthetic=false`; la importación construye esos datos en servidor. Fuente desconocida: 422; ausente/corrupta: 503; vigencia técnica vencida: rechazo. La disponibilidad publicada comprueba integridad y fecha.

Cálculo: obtener grafo autorizado vigente; excluir aristas restringidas; Dijkstra por tiempo, con desempate por distancia y orden estable; conservar instantánea, geometrías elegidas, versión, duración y límites. Complejidad O((V+E) log V), más validación de P puntos O(P). Optimiza entre los trayectos importados; no promete la mejor ruta de toda la red vial estatal. El oráculo real usa distancia y duración directamente de la respuesta pública, separado del convertidor. Se conservan oráculos exhaustivos para grafos pequeños.

Ejemplo fijado: Monterrey→Guadalupe, 7,2893 km y 9,2966667 minutos modelados. No son mediciones de un traslado. La llegada estimada suma esos minutos al corte de simulación desde el origen planificado. El escenario conserva `synthetic=true`; el grafo importado registra `synthetic=false`. Procedencia vial real y escenario académico son dimensiones distintas.

El proveedor no informó `data_version`: antigüedad del mapa desconocida, aunque la descarga tenga fecha. `road_reference` conserva `source_age_seconds`, `map_age_seconds=null`, `observed_gps_used=false` y `traffic_measured=false`. Vigencia técnica de la demostración: hasta 02/12/2026; no certifica actualización vial. [API OSRM](https://project-osrm.org/docs/v5.24.0/api/), [condiciones demo](https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server), [atribución OSM](https://www.openstreetmap.org/copyright). No hay garantía de disponibilidad ni tráfico actual.

Las peticiones usan instantáneas instaladas, sin acceso a Internet. Un fallo externo no impide reproducir lo guardado; un archivo local corrupto impide nueva importación. Renovación exige adquisición explícita, revisión y nueva versión. Posición observada, historial de Transporte, ruta, ETA, entrega y dictamen permanecen separados. GPS físico no integrado ni probado en este incremento.

[Evidencia nueva](../evidencias/entrega-final/algoritmos/fuentes_publicas/20261102T143541Z/RESULTADOS.md): fuentes, intentos, regresión, navegador y revisión independiente. Los benchmarks anteriores siguen siendo mediciones históricas; no acreditan rendimiento nuevo de 0.4.4.

## Preselección

RBC-1.0 conserva el filtro ABO/RhD para eritrocitos documentado en el monolito. No aplica a plasma, plaquetas u órganos y no interpreta anticuerpos ni pruebas cruzadas. ORGAN-1.0 conserva preselección por mismo tipo y ABO idéntico, con RhD excluido de ese filtro. Ninguno certifica compatibilidad clínica; reserva exige dictamen médico favorable.

Entradas: solicitud, receptor mínimo, recursos disponibles y rutas capturadas por sus propietarios. Se conservan versiones, límites de conservación capturados, procedencia y candidatos descartados por falta de ruta/tiempo. Complejidad del recorrido: O(U + R), construyendo un mapa de rutas; las consultas HTTP y PostgreSQL se miden separadamente. El endpoint registra tiempo total de evaluación.

## Orden operativo

LOGISTICS-1.0 ordena candidatos por límite de conservación capturado, minutos, distancia e identificador estable; registra urgencia y tiempo de solicitud como contexto. Complejidad O(C log C). No aplica ponderaciones ni prioridad clínica oficial y no optimiza rutas geográficas mediante un proveedor externo.

## Propuestas de cobertura

COVERAGE-HK-1.0 construye un grafo bipartito: un nodo por cupo solicitado y un nodo por recurso, con aristas únicamente para candidatos con dictamen favorable en su evaluación. Hopcroft–Karp busca caminos aumentantes y produce matching de cardinalidad máxima.

Problema: asignar primero un recurso flexible a un paciente flexible puede dejar sin propuesta a otro paciente que únicamente admite ese recurso. Un camino aumentante reasigna la propuesta del flexible, aumentando cobertura sin repetir recursos.

Pseudocódigo:

```text
crear grafo de cupos -> recursos aprobados
inicializar matching vacío
mientras BFS encuentre una capa de caminos aumentantes más cortos:
    para cada cupo libre:
        DFS sobre esas capas
        si existe camino aumentante, invertir sus parejas
devolver propuestas, versiones y explicaciones
```

Entradas: máximo 100 evaluaciones de solicitudes propias, sin repetir solicitud; máximo 500 cupos y 100 000 aristas. Salida: parejas solicitud/recurso, cantidad cubierta, versiones originales, explicación y tiempo. Tiempo teórico O(E √V), memoria O(V + E). El orden de nodos/aristas es determinista.

Restricciones y límites: una propuesta no reserva ni autoriza, no ejecuta prioridad clínica, no considera datos HLA ni conflictos normativos no modelados. Puede quedar obsoleta; Inventario vuelve a validar versiones, estado, capacidad y viabilidad temporal. La expansión de cupos se basa en la cantidad de la instantánea, no promete cobertura neta de asignaciones posteriores. Las reglas oficiales de balanceo, urgencia y conservación siguen pendientes de validación.

Pruebas: un caso donde falla un orden voraz; comparación independiente con búsqueda exhaustiva en los 512 grafos bipartitos 3×3; persistencia de una propuesta por API sin crear reservas. La matriz RBC se contrasta completa para los ocho grupos del ejercicio. Resultados vigentes en [VALIDACION](Pruebas_y_validacion.md).

## Ampliación académica reproducible — 31/10/2026

Las cuatro versiones anteriores permanecen intactas. El [registro de reglas y fuentes](Reglas_y_fuentes_clinicas.md) distingue vigencia normativa de aprobación profesional. El esquema 14 incorpora HLA declarado y `algorithm_runs` inmutable, con autor, institución, versión, fuente, instantánea completa, SHA-256, resultado y duración. Corregir laboratorio cambia su fingerprint; las comprobaciones existentes rechazan una revisión o reserva basada en información obsoleta.

API: `POST/GET /api/v1/algorithm-runs` y `GET /api/v1/algorithm-runs/{id}` en Priorización/Geografía. JSON y XML/XSD, JWT/Redis, rol MEDICAL/COORDINATOR, alcance institucional, idempotencia y auditoría. Solo datos sintéticos (`synthetic=true`); no consulta expedientes ajenos. El catálogo de contratos publica límites y tipos. El portal ofrece `/algoritmos`, detalle y formulario `/algoritmos/demanda`; muestra datos, resultados y ausencia de dictamen sin recalcular. Laboratorio permite corregir tipificación declarada, conservando antecedentes.

### ALG-01: EXPLAIN-ACADEMIC-1.0

Problema: distinguir completitud técnica y exclusiones de una decisión clínica. Entradas: versión de perfil, pruebas exigidas y candidatos sintéticos con componente, disponibilidad, vencimiento, incidencia térmica y pruebas presentes. Salida: cada candidato considerado, motivos `MISSING`, `OTHER_COMPONENT`, `UNAVAILABLE`, `EXPIRED`, `THERMAL_REVIEW`; completo o pendiente de revisión. No realiza comparación clínica de alelos.

Pseudocódigo: por candidato, calcular diferencia de conjuntos de pruebas; agregar restricciones técnicas; conservar motivos o `NO_CLINICAL_INFERENCE`. Tiempo O(C × (T + R log R)), memoria O(CR) en salida, con C candidatos, T pruebas aportadas y R requeridas. Máximo 2.000 candidatos/80 pruebas exigidas. Ejemplo: ABO presente y HLA ausente devuelve `MISSING:HLA`, nunca aptitud. La captura de HLA usa loci definidos por perfil, sin lista clínica universal ni inferencia PRA/cPRA.

### ALG-02: simulación y rutas

`LOGISTICS-SIM-2.0`: primero excluye recursos indisponibles/vencidos/con incidencia y factores ausentes. Después ordena urgencia y espera descendentes, vencimiento, minutos, distancia e identificador ascendentes. Registra valores de cada factor. O(C log C), memoria O(C). El ejemplo con dos candidatos iguales salvo urgencia coloca primero el de mayor valor **solo en esta política sintética**. La referencia de urgencia es declarada, no acreditación; no genera ranking oficial ni admite órganos.

`ROUTE-DIJKSTRA-1.0`: grafo dirigido versionado por `profile_version`, fuente y fecha. Aristas con tiempo/distancia no negativos y bloqueo explícito. Cola de prioridad ordenada por (minutos, distancia, nodo); relajar únicamente mejoras estrictas, conservar predecesor, reconstruir desde destino. O((V+E) log E + suma de ordenamientos de adyacencias), memoria O(V+E). Límite 10.000 aristas. Aristas paralelas y ciclos de coste cero admitidos; pesos negativos/no finitos rechazados. Sin camino, devuelve `UNREACHABLE`. Oráculo independiente enumera caminos simples en 80 grafos pequeños deterministas, incluidos ciclos y costes cero.

Se conservan cuatro elementos diferentes:

- **GPS observado:** posición, fuente, captura, recepción, exactitud declarada y bandera de simulador; se informa antigüedad en segundos respecto a `as_of`. No se extrapola posición.
- **Recorrido recibido por WebSockets:** lista de observaciones de entrada separada; conservar puntos no acredita que esta simulación haya establecido una conexión WSS. El transporte WSS operativo pertenece al módulo de rastreo existente.
- **Ruta planificada:** secuencia de nodos del grafo y coste; fuente/fecha/versión pertenecen a la instantánea. Es un grafo sintético, no evidencia de ruta vial real.
- **ETA:** hora calculada como corte de simulación más minutos desde el origen del grafo. `eta_basis=SIMULATED_DEPARTURE_AT_AS_OF_FROM_GRAPH_ORIGIN`; no es ETA desde GPS, tráfico actual o confirmación de entrega. Sin ruta, ETA nula. La incertidumbre de pesos no se conoce y se declara; precisión GPS no convierte los pesos en mediciones.

### ALG-03: cobertura

Reutiliza COVERAGE-HK-1.0 y el oráculo exhaustivo anterior. No se añadió coste mínimo ni atribución de prioridad. Las propuestas conservan versiones y no reservan. La revalidación final continúa en Inventario; una propuesta histórica no promete que siga disponible su cobertura.

### ALG-04: DEMAND-SES-1.0

Problema: estimar consumo siguiente y exceso orientativo de stock por institución/componente. Entrada: al menos seis ventanas históricas completas, contiguas, de duración `window_days`, terminadas al corte `as_of`; stock. Los datos aportados son sintéticos, no extracción automática del inventario. Salida: alfa, número de ventanas de entrenamiento/prueba, MAE, MAE de referencia, pronóstico siguiente y exceso de stock.

Pseudocódigo: separar cronológicamente 2/3 para entrenamiento; seleccionar alfa entre 0.2, 0.5 y 0.8 minimizando error absoluto de predicción a un paso **solo en entrenamiento**; evaluar ventana siguiente antes de actualizar el nivel; comparar con último valor observado; actualizar secuencialmente; pronosticar una ventana. O(N), memoria O(N) contando entrada/errores. Máximo 10.000 ventanas. Parámetros reproducibles propios de un estimador académico, no ponderaciones clínicas. Cambiar el segmento de prueba no cambia alfa. MAE conserva unidades de consumo y permite comparar contra persistencia; no se garantiza superioridad.

Exceso = max(stock − pronóstico, 0), una señal para revisar rotación. Con lotes opcionales cuya suma coincide con stock, ordena por fecha/ID y estima consumo antes de cada vencimiento mediante tasa constante y descuento del consumo ya asignado. Devuelve sobrante estimado por lote para revisión; no garantiza demanda futura. El recorrido agrega O(L log L), memoria O(L). Lotes vencidos tienen consumo futuro cero. La conexión a lotes operativos reales permanece pendiente. Sin intervalo probabilístico calibrado ni validación con consumo real. Nunca prolonga caducidad ni ejecuta transferencias.

### ALG-05: CONSISTENCY-1.0

Problema: señalar inconsistencias técnicas sin reescribir registros. Entrada: instantánea sintética ordenada por secuencia por recurso. Recorrer manteniendo conjuntos de identificadores/reservas y último número por recurso. Señalar identificador duplicado, doble reserva, cantidad superior a disponible, salto/repetición de secuencia, procedencia ausente, muestra de otro sujeto, incoherencia térmica declarada y versión de proyección distinta de la fuente. O(N), memoria O(N), máximo 10.000 registros. Salida: anomalías potenciales con motivos, no incidentes confirmados. El flag térmico no deriva umbrales clínicos. Falta conectar esta ejecución a extracción autoritativa y apertura del expediente de revisión de Auditoría; las ejecuciones mismas quedan auditadas.

### Reproducción y evidencia

Desde la raíz:

```sh
apps/services/.venv/bin/python -m pytest apps/services/tests/test_final_algorithms_hla.py apps/services/tests/test_algorithms.py apps/services/tests/test_final_quality.py -q
apps/services/.venv/bin/python apps/services/scripts/benchmark_academic.py
apps/services/.venv/bin/python apps/services/scripts/document.py --contracts-only
```

[Expediente de esta ampliación](../evidencias/entrega-final/algoritmos/RESULTADOS.md). Métricas de tiempo y pico de asignaciones Python son de ejecución local con `tracemalloc`, no latencia HTTP ni RSS del servicio. No representan carga sostenida, hardware GPS ni validación profesional.

El estimador operativo anterior `EMPIRICAL-USE-1` de Inventario se conserva: `/api/v1/analytics/inventory` consulta destinos vigentes y stock institucional y estima excedente con tasa empírica. Su prueba `test_empirical_forecast_positive_independent_oracle` contrasta 14 usos/30 días y diez unidades próximas a vencer contra excedente seis. SES es una ampliación sintética separada, todavía sin importación automática de ese historial operativo; no debe describirse como reemplazo ni como ausencia del estimador existente.

## Corrección integrada 0.4.3 / esquema 15 — 01/11/2026 UTC

Esta sección describe el código correctivo actual. La ampliación 0.4.2 anterior y sus mediciones son historia, no evidencia de cierre de este incremento. Se conservan las ejecuciones y `RBC-1.0`, `ORGAN-1.0`, `LOGISTICS-1.0`, `COVERAGE-HK-1.0`. La nueva entrada integrada es `decision-runs`; `algorithm-runs` conserva el laboratorio académico explícito. [Operación, contratos, estados y reproducción](../entrega-final/algoritmos/correccion/Operacion_y_reproduccion.md) · [matriz de cierre](../entrega-final/algoritmos/correccion/Matriz_cierre.md).

### ALG-01 — EXPLAIN-PROFILE-2.0

Problema: explicar la selección bajo requisitos técnicos registrados sin emitir autorización clínica. Entrada: UUID de solicitud y UUID opcional de perfil inmutable; para la rama integrada el perfil es obligatorio. Compatibilidad obtiene receptor/solicitud de Receptores, recursos disponibles no vencidos de Inventario y opciones de ruta de Geografía. Ese es el universo autorizado: no todos los expedientes ni unidades en cuarentena. Los estados y caducidad se vuelven a comprobar al consumir.

Salida: cada recurso considerado, versión, entrada determinante, admisión/exclusión y motivo individual: producto distinto, filtro ABO/RhD académico de RBC, ABO de órgano, ruta ausente, tiempo insuficiente, laboratorio faltante o requisitos del perfil. La comparación no usa RhD para órganos. Plasma/plaquetas usan revisión manual con perfil obligatorio; productos desconocidos no adquieren reglas RBC. También se conserva contexto del receptor, huella de sus resultados, perfil y acciones, fuente, fecha, duración y candidatos. La explicación de revisión manual no afirma haber ejecutado un filtro clínico.

```text
validar solicitud, institución, producto y perfil vigente
capturar receptor/resultados/perfiles/acciones
indexar rutas por origen-destino
para cada recurso del universo autorizado:
    registrar recurso/versiones
    comprobar producto y filtro académico aplicable
    comprobar ruta y viabilidad temporal
    comprobar completitud y requisitos de la versión de perfil
    guardar cada exclusión o candidato pendiente de dictamen
persistir instantánea; jamás insertar dictamen automáticamente
```

Tiempo del recorrido O(U+R) más consultas de laboratorio O(sumatoria de resultados examinados) y acceso por candidato; memoria O(U+R+L) según instantánea. No se atribuye O(U+R) a toda la infraestructura SQL/HTTP. La reproducción principal `evaluations/{id}/reproduce` recalcula motivos desde entradas congeladas, sin consultar estado actual. `decision-runs` guarda además una agrupación de evaluaciones y la reproduce. Cambiar el perfil después invalida usos actuales, pero no cambia el resultado histórico. Pruebas: exclusiones al añadir IMMUNO a un sucesor, reproducción idéntica, tres productos, autorización institucional, laboratorio del receptor y recurso obsoleto.

### ALG-02 — LOGISTICS-OWNER-SIM-3.0

Problema: comparar opciones logísticas con fuentes autoritativas sin crear prioridad oficial. Requiere evaluaciones vigentes de solicitudes distintas y `policy_id` registrado, vigente y del mismo producto. La política implementada declara `URGENCY_WAIT_EXPIRY_TIME_DISTANCE_ID` y escala `CAPTURED_1_3_SYNTHETIC`; no existe política clínica aprobada. Se conserva política y gobernanza en instantánea. El núcleo es LOGISTICS-SIM-2.0; LOGISTICS-1.0 sigue sin utilizar urgencia/espera.

Entradas determinantes: urgencia 1..3 capturada en Receptores por MEDICAL; minutos de espera desde creación de solicitud; minutos hasta vencimiento; tiempo y distancia de ruta de su propietario. Orden lexicográfico: urgencia descendente, espera descendente, vencimiento ascendente, tiempo ascendente, distancia ascendente e identificador estable. No hay pesos clínicos. Factores faltantes o restricciones incumplidas excluyen y explican; no se sustituyen por cero. Órganos requieren el procedimiento externo y no obtienen este ranking.

```text
cargar política y evaluaciones vigentes
extraer factores del corte/solicitud/recurso/ruta
excluir faltantes, producto distinto y restricciones
ordenar por (-urgencia,-espera,vencimiento,minutos,distancia,id)
guardar factores, escala, política, corte y resultado sintético
```

O(C log C), memoria O(C). Pruebas independientes cambian cada factor con los anteriores empatados, incluido identificador; invierten entradas y mantienen orden; cada factor ausente excluye. El orden sintetiza una comparación de prueba, no justifica prioridad médica ni utilidad clínica real.

### ALG-02-GEO — REGIONAL-DIJKSTRA-2.0

Problema: ruta de mínimo tiempo sobre grafo regional registrado; distancia desempata. Entradas: UUID/versionado de grafo de Nuevo León, nodos origen/destino, aristas dirigidas con minutos/distancia no negativos y bloqueos, fuente, observación, vigencia y calidad. Hasta 2.000 nodos/10.000 aristas. El adaptador importa un archivo a la API, no directamente a PostgreSQL. La versión disponible admite exclusivamente fuente sintética identificada; falta fuente vial externa autorizada.

Dijkstra usa heap, descarta aristas bloqueadas, relaja costes `(minutos,km)` y reconstruye padres. Tiempo O((V+E) log V) más ordenación determinista de adyacencias; memoria O(V+E). Oráculo independiente enumera caminos simples en grafos pequeños; se mantienen casos inaccesibles, pesos inválidos, cero, vacío y límites. La ruta y ETA parten del origen planificado y corte declarado. GPS y recorrido no cambian esos pesos. No se atribuye ajuste al grafo, tráfico ni tiempo medido.

Transporte devuelve snapshot y hasta 20 páginas de 100 eventos autorizados hasta `head`; `history_complete=false` informa truncamiento. Se conservan fuente, captura, recepción, precisión y estado. NO_FIX/NO_DATA no generan mediciones; STALE conserva antigüedad. La prueba de socket WSS real publica SIMULATOR, comprueba persistencia y lectura por este cálculo. La antigua lista HTTP `websocket_track` sigue siendo entrada declarada; `declared_track_points` no demuestra recepción WSS.

### ALG-03 — COVERAGE-HK-1.0 integrado

El núcleo, pseudocódigo y oráculo exhaustivo descritos arriba permanecen. `decision-runs` toma evaluaciones actuales y aristas con dictamen favorable; hasta 100 evaluaciones, 500 cupos y 100.000 aristas. Conserva cantidades y versiones. Salida declara `reservations_created=0` y `MAXIMUM_CARDINALITY_ONLY`. No optimiza costes, urgencia ni HLA. La ruta existente de propuestas filtra candidatos obsoletos; la confirmación pasa por Inventario y revalida.

Ejemplo de oráculo: cupo A permite U1/U2, B permite solo U1; el camino aumentante produce dos parejas. Una reserva concurrente o cambio de entrada requiere nueva comprobación, no altera el matching histórico. Pruebas de doble reserva, sobrecobertura y compensación siguen en la regresión de etapa 01.

### ALG-04 — DEMAND-OWNER-SES-2.0

Problema: estimar consumo documentado y sobrantes por caducidad para revisión logística. Inventario extrae destinos no sustituidos de su institución/producto, ventanas diarias UTC completas y stock/lotes actuales. `history_until` es el último límite diario; `as_of` es la captura actual usada para caducidades, sin atribuir a stock actual disponibilidad retrospectiva. Cada observación conserva eventos, fechas, fuente y calidad. Ventana de 6..365 días; extracción limitada, no silenciosamente truncada.

Se valida orden, continuidad de 24 horas, fechas únicas y ausencia de futuro. Política RECORDED-DAILY-1: día sin evento registrado vale cero **solo como conteo del registro**, sin inferir ausencia física de demanda. Sin consumos en toda la ventana: `INSUFFICIENT_RECORDED_USE`, no pronóstico cero.

```text
separar primeros 2/3 para entrenamiento; resto evaluación temporal
elegir alpha de {0.2,0.5,0.8} por error absoluto de entrenamiento
predecir evaluación un paso antes de observar cada valor; actualizar nivel
comparar MAE contra último consumo observado (persistencia)
pronosticar siguiente ventana con nivel final
ordenar lotes por vencimiento e id
asignar consumo acumulado hasta cada vencimiento sin reutilizarlo
devolver sobrantes y sugerencia de revisión; no ejecutar transferencias
```

Núcleo DEMAND-SES-1.0: O(H+B log B), memoria O(H+B). Extracción de ventanas actualmente O(D×E) sobre hechos acotados, separada del núcleo. No hay intervalo probabilístico calibrado, estacionalidad, demanda no atendida ni validación con datos físicos reales. Oráculo completo independiente de alpha, nivel, MAE y referencia; modificación solo del tramo de evaluación no cambia alpha. Oráculo de lotes con demanda constante 2/día y capacidades acumuladas 0/1/2/6 cubre vencido, distintos vencimientos, stock escaso y sobrante. No prolonga caducidades ni modifica conservación.

### ALG-05 — CONSISTENCY-OWNER-2.0

Problema: abrir revisión ante hechos técnicos incoherentes. Los cinco propietarios devuelven identificadores mínimos y estados persistidos; el cliente no aporta banderas de temperatura/procedencia. Se comprueba folio repetido entre recursos presentes, reservas múltiples, cantidad retenida superior a solicitud, donación inexistente/no procesada/sin historia o de sujeto ajeno, linaje inconsistente, muestra de otra institución o pareja cruzada incorrecta, temperatura fuera del perfil **sintético capturado**, captura posterior a recepción, secuencia rota y versión Mongo distinta de la transición fuente.

```text
obtener hechos acotados de cada propietario autorizado
indexar recursos/donaciones; agrupar reservas y cantidades
comparar asociaciones, secuencias, lecturas y proyección
por cada hallazgo: evidencia mínima + versión + POTENTIAL_ANOMALY
persistir ejecución y outbox atómicos
Auditoría deduplica por institución/huella, asigna responsable y abre revisión
AUDITOR autorizado confirma/descarta con motivo; conserva evidencia e historia
```

O(F+S) en memoria/tiempo del detector sobre hechos y secuencias; consultas de propietarios y MongoDB se miden aparte. Límites de 10.000 hechos por conjunto y 1.000 traslados; falla explícitamente si excede. Falta de autoridad/dato no se sustituye por una declaración del cliente. Duplicado es anomalía potencial, no prueba de corrupción clínica; un folio puede requerir desambiguación institucional. Ningún hallazgo corrige automáticamente los hechos.

La prueba siembra las nueve clases en almacenes temporales desde conexión administrativa exclusiva del fixture, sin endpoint de corrupción. Los índices de exclusión de reservas se suspenden/restauran solo en esa base desechable para ensayar detección defensiva; las API habituales mantienen esos índices. Se ensaya Auditoría inaccesible, recuperación de outbox, deduplicación, permiso de resolución e inmutabilidad de evidencia bajo runtime.

### Obsolescencia y métricas del incremento

`validity` actual compara solicitud/receptor, estados, resultados de ambos sujetos, perfiles/acciones, unidad, ruta y viabilidad temporal; no reescribe instantánea. Inventario mantiene bloqueos de laboratorio, perfiles y versiones críticas hasta el commit de reserva, además de exclusión/cupo y compensación existentes. Una corrección concurrente se serializa con ese commit; un cambio posterior deja historia consultable y exige revisión para usos posteriores.

Mediciones nuevas: [benchmark-final.json](../evidencias/entrega-final/algoritmos/correccion_comprobacion/20261101T042648Z/benchmark-final.json), cinco repeticiones por tamaño/forma, mediana/p95 por rango, asignaciones Python y máximo RSS del proceso; incluye núcleos y reproducción/detector/ventanas integradas. [HTTP (archivo)](../evidencias/archivo/detalles-20261104.tar.gz) registra endpoints normalizados, estados y distribución. Estos ensayos secuenciales no acreditan carga sostenida, p99 productivo ni capacidad clínica. [Resultados consolidados](../evidencias/entrega-final/algoritmos/correccion_comprobacion/20261101T042648Z/RESULTADOS.md) identifica casos, intentos y aplicabilidad de fuentes.

## Mantenimiento del despachador académico — 4 de noviembre de 2026

`academic.execute` conserva la entrada validada y la salida común. Las cinco
implementaciones existentes se separan en `_explain`, `_logistics`, `_route`,
`_demand` y `_anomalies`, dentro del mismo módulo. La comparación AST de cada
cuerpo contra el árbol previo dio igualdad en las cinco ramas; no se cambian
versiones, fórmulas, desempates, límites, métricas ni explicaciones históricas.
Los resultados de regresión y costos figuran en [Pruebas y validación](Pruebas_y_validacion.md).
