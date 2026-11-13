# Optimizar Red House conservando arquitectura, tecnologías y funcionalidades

## Encargo y alcance

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Optimiza el rendimiento real del monolito, los microservicios, PostgreSQL, MongoDB, Redis y la aplicación Android/iOS existentes. Reduce consultas y peticiones repetidas, tiempo de espera, ocupación de conexiones, transferencia innecesaria y trabajo que bloquea la interfaz. Implementa, mide y verifica los cambios; no entregues solamente recomendaciones cuando el usuario solicite ejecutar este prompt.

**La creación de este documento no ejecuta el encargo.** Es un prompt preparado el 11/11/2026 para una intervención posterior. Sus observaciones son una base de investigación, no una certificación del código que encuentres al comenzar ni evidencia de optimizaciones ya realizadas.

El usuario confirmó un límite estricto: **misma arquitectura, mismas tecnologías y mismas funcionalidades; únicamente optimización de lo existente**.

### Restricciones obligatorias

1. Conserva Flask/Jinja2/JavaScript/Highcharts, los servicios y propietarios actuales, PostgreSQL/MongoDB/Redis, GCS, Docker/GCE/gateway, Kotlin Multiplatform/Compose Multiplatform y sus adaptadores nativos. Mantén PySide6 como decisión de escritorio; este encargo no construye una aplicación de escritorio que todavía no exista.
2. No añadas frameworks, bibliotecas de producción, motores, extensiones de PostgreSQL, brokers, microservicios, bases, instancias Redis, CDN, clústeres ni servicios de nube. **`pg_trgm` y una segunda instancia Redis quedan fuera.** No añadas Room, otra biblioteca de paginación, un bundler o un sistema de observabilidad para resolver estas tareas. Usa las dependencias, herramientas y capacidades ya disponibles; no actualices versiones en bloque.
3. Se permiten refactorizaciones internas, SQL e índices nativos, procesamiento por lotes, uso de Redis existente, componentes Compose disponibles, configuración de assets y migraciones aditivas estrictamente necesarias dentro del propietario actual. Justifica cada cambio de esquema; conserva datos, historia, rollback de aplicación y compatibilidad temporal.
4. Conserva rutas y semántica de operaciones, filtros, orden, totales, formatos, reglas y acciones disponibles. Una consulta por lote o representación de resumen puede añadirse al propietario existente cuando esté justificada; debe ser compatible y conservar contratos JSON y XML/XSD/DTO. No rompas consumidores ni cambies silenciosamente totales exactos por aproximaciones.
5. El monolito continúa autónomo con las API independientes detenidas, mientras sus dependencias necesarias estén disponibles. Diferencia llamada interna del backend modular de petición HTTP. No conectes el navegador directamente a microservicios para acelerar el portal ni construyas un nuevo servicio agregador.
6. Android/iOS consumen JSON; escritorio consume XML/XSD. Los clientes no acceden directamente a PostgreSQL, MongoDB o Redis. Conserva WSS y la separación de autoridades. Una optimización de red no cambia reglas clínicas, permisos ni criterios de asignación.
7. Mantén JWT, consulta de autorización/revocación en Redis, MFA, reautenticación, aislamiento institucional, autorización por recurso, validación, auditoría, CSRF, idempotencia y confirmaciones obligatorias. No omitas controles para mejorar una medición ni confirmes una escritura que solo quedó en caché.
8. No aumentes timeouts, recursos de la VM, réplicas, conexiones o tamaños de página como sustituto de reducir trabajo. Ajustar un límite existente requiere medición y presupuesto global de procesos/réplicas; no cambia por sí solo el criterio de aceptación. No bajes frecuencia o cobertura requerida de seguimiento para presentar menos carga como optimización equivalente.
9. No borres historial ni datos para acelerar consultas. No cambies retención, durabilidad Redis, reglas de expiración de sesiones o política `noeviction` sin un encargo separado que autorice ese cambio; no forma parte de esta optimización.
10. Conserva cambios ajenos del repositorio. No despliegues, reinicies producción, ejecutes cargas destructivas o crees costes por el hecho de ejecutar este documento. Prepara y valida primero el resultado local/aislado. Aplica las autorizaciones vigentes a las acciones concretas; no supongas que un despliegue anterior autoriza nuevos ensayos sobre datos productivos.

## Lectura inicial y continuidad

Lee `AGENTS.md`, [PROJECT_STATUS.md](../../PROJECT_STATUS.md), [reglas comunes](entrega-final/00_contexto_y_reglas.md), [continuidad CONT-01…CONT-10 e integración](entrega-final/07_integracion_pruebas_y_rendimiento.md), [seguridad y continuidad](entrega-final/06_seguridad_infraestructura_y_continuidad.md) y [rastreo WSS](entrega-final/09_rastreo_gps_websockets.md). Utiliza CodeGraph antes de localizar o leer código si existe el índice. Revisa instrucciones locales aplicables.

Conserva las [reglas de diseño](instrucciones_diseno_ui_ux.md) y la [corrección de calidad visual](corregir_calidad_visual_web_movil.md). Este encargo permite cambiar cómo y cuándo se cargan los datos, pero no rediseña la identidad, elimina funciones o sustituye datos por pantallas decorativas. Una estructura de carga mejora la percepción; por sí sola no demuestra reducción del trabajo o del tiempo de respuesta.

Lee el [diagnóstico del 503 de monitoreo](../../documentation/evidencias/mantenimiento/monitoreo-503-20261111/RESULTADOS.md). En ese diagnóstico, la consulta de última muestra se canceló con límite de 5000 ms; una medición fue 5,172 s. El plan estimó 786.081 filas, sin ser un conteo exacto. MongoDB también agotó su tiempo en la agregación alternativa. Las API sanas no prueban que la consulta completa de la pantalla funcione. No atribuyas esos resultados históricos al entorno actual sin comprobarlo.

Las investigaciones también identificaron candidatos estáticos que deben revalidarse: N+1 de horarios/citas; evaluaciones en cadena; SQL durante esperas remotas; sondeo SQL por suscripción WSS; invalidación global de inventario; carga innecesaria de Highcharts; recargas móviles completas; disco/cifrado/imágenes en rutas de UI; ciclos de sincronización redundantes. No les atribuyas tiempos o ahorros que todavía no se midieron.

Ya existen mecanismos útiles: reutilización HTTP y Redis, pool PostgreSQL configurable, MGET de autorización, caché e invalidación transaccional de inventario, outbox con deduplicación, algunos cachés por petición, scripts web diferidos, filtros con cancelación/debounce, cifrado móvil, renovación coordinada y reconexión WSS. Confirma su estado y mejóralos; no los reconstruyas como si estuvieran ausentes.

## Método de ejecución y medición

### Línea base antes de modificar comportamiento

- Identifica fuentes mediante commit y/o manifiesto de hashes, cambios locales, esquema, versiones instaladas, configuración efectiva, imágenes, hardware, procesos y límites. Distingue configuración versionada de configuración desplegada. No copies secretos a evidencias.
- Usa un entorno aislado y datos ficticios reproducibles. Conserva un conjunto antes/después con los mismos roles, instituciones, distribución, volumen, páginas, tamaños de imágenes, rutas y concurrencia. Incluye referencias repetidas y distintas, instituciones ajenas y datos suficientes para revelar el coste observado.
- Para monitoreo incluye volumen histórico representativo del diagnóstico; para listados prueba primera página y páginas profundas; para N+1 prueba 1, 20 y, donde el contrato lo permita, 100 elementos. Para WSS compara varios espectadores del mismo traslado y de traslados distintos, con actividad e inactividad.
- Mide por tarea: llamadas internas y HTTP por separado; consultas SQL, tiempo acumulado, filas procesadas/devueltas, espera por pool/bloqueos; comandos Redis, HIT/MISS y reconstrucciones; bytes originales/transferidos; TTFB, contenido principal e interacción web; arranque, contenido útil, tareas largas, memoria y fluidez móvil según las herramientas disponibles.
- Registra repeticiones, calentamiento, tamaño de muestra, mediana y p95/p99 cuando la muestra permita interpretarlos. Separa caché fría/caliente, navegador con/sin assets previos, debug/release, emulador/teléfono y Android/iOS. No compares un antes frío con un después caliente como si fuera mejora del mismo escenario.
- Analiza planes SQL y agregaciones MongoDB con herramientas disponibles. `EXPLAIN ANALYZE` ejecuta la consulta: úsalo únicamente en el laboratorio controlado correspondiente. Si `pg_stat_statements` ya está instalado y autorizado, puedes consultarlo; no instales/actives extensiones nuevas para este encargo. Usa instrumentación mínima y logs de correlación existentes como alternativa.
- Antes de cada incremento, registra el problema, hipótesis, resultado que debe mantenerse, métrica de coste, objetivo justificado y comprobación de regresión. No inventes un SLA clínico ni prometas un porcentaje universal. Un objetivo no se rebaja después de un fallo para declarar aprobación.

### Incrementos pequeños

Atiende primero el 503 de monitoreo y el trabajo repetido/bloqueante demostrado. Continúa con lotes, WSS/Redis, carga web y móvil según la línea base. Implementa una causa o un conjunto estrechamente relacionado por incremento, compara y verifica antes de ampliar el alcance. Paralelizar indiscriminadamente puede trasladar la espera a la base de datos: mide carga y concurrencia total.

Mantén una matriz OPT-01…OPT-12 al ejecutar, con propietario, fuentes, hallazgo confirmado/no reproducido, acción, antes/después, criterio, pruebas, evidencia y estado. Los candidatos sin beneficio medible pueden descartarse con justificación y datos; no fuerces complejidad por completar una lista. Un defecto confirmado o un caso no ejecutado permanece explícito. Los pendientes CONT afectados se enlazan, sin declarar cerrados otros criterios de etapa 04/06/07 por optimizar una parte.

## OPT-01 — Último estado de monitoreo y estadísticas

**Inspecciona:** `apps/services/servicio_monitoreo/routes.py`, `apps/web/src/integration/routes/monitoring.py`, vistas/tablas físicas e índices de `checks`/`service_health_check`, y la proyección documental correspondiente.

1. Evita calcular el último estado por servicio mediante lectura y ordenamiento global en cada apertura. Evalúa primero consultas indexadas acotadas por servicio con orden/desempate compatibles. Comprueba el plan sobre tablas físicas, no solo el alias de una vista.
2. Si las consultas e índices nativos no resuelven el coste, considera una proyección interna de último estado en los almacenes existentes, actualizada con consistencia por su propietario y reconstruible desde el historial. No dupliques autoridad ni elimines observaciones.
3. Optimiza el pipeline MongoDB alternativo y sus índices nativos. Mantén la última muestra aunque sea antigua: debe mostrarse degradada por antigüedad, no desaparecer por limitar incorrectamente la búsqueda a 24 horas.
4. Reduce agregaciones repetidas de ventanas históricas con consultas agrupadas o resúmenes/caché acotados. Conserva límites temporales, denominadores, errores y antigüedad real. No obtengas percentiles globales promediando percentiles parciales.

**Aceptación:** mismo último evento, estado, desempate y estadísticas para datos conocidos; pantalla real sin 503 bajo la carga acordada y el límite vigente; menos lectura/ordenamiento o coste medido. Probar estado antiguo, servicio sin muestras, SQL indisponible, alternativa MongoDB, ambos almacenes no disponibles y recuperación. No sustituir una consulta fallida por datos inventados o disponibilidad aparente.

## OPT-02 — Listados, búsqueda, paginación y tamaño de respuestas

**Inspecciona:** `apps/services/redhouse/api.py`, `apps/services/redhouse/extension_contracts.py`, listados de cada propietario y sus contratos. La base investigada utiliza `count(*)`, `LIMIT/OFFSET`, `ILIKE '%texto%'` y columnas completas por defecto.

1. Ajusta filtros y orden al plan real; propone índices nativos compuestos o parciales solo para patrones demostrados. Considera institución, estado, fecha e identificador de desempate, sin indexar indiscriminadamente. Mide también coste de escritura y espacio.
2. Mantén la búsqueda textual existente. No habilites `pg_trgm` ni cambies una búsqueda por contenido a coincidencia exacta silenciosamente. Usa igualdad para rutas/campos que ya signifiquen identificador exacto y optimiza el resto con filtros autorizados y planes disponibles. Registra el límite residual si el stack actual no lo resuelve suficientemente.
3. Para historiales de gran volumen, evalúa cursor estable como capacidad aditiva. Conserva las rutas paginadas actuales, su orden y totales. No retires números de página ni cambies el contrato de clientes existentes. Evita duplicados/saltos por empates y prueba inserciones concurrentes.
4. Un conteo opcional o representación de resumen requiere contrato explícito compatible y consumidor identificado. Conserva conteos exactos donde hoy son necesarios. Selecciona columnas pertinentes y difiere detalles voluminosos sin quitar información accesible ni enviar datos ajenos.

**Aceptación:** resultados, filtros, orden y autorización equivalentes; acceso a registros posteriores a la primera página; lectura/transferencia reducidas en el escenario medido. Prueba páginas vacías/profundas, empates, cambio de filtros y formato JSON/XML con sus esquemas.

## OPT-03 — Horarios y citas sin consultas por fila

**Inspecciona:** `apps/services/ms_donantes/agenda.py`, `apps/web/src/integration/appointments.py`, `apps/web/src/integration/routes/people.py` y `apps/web/src/integration/routes/common.py`.

1. Sustituye el agregado de disponibilidad por cada horario por un agregado de los IDs de la página autorizada. Mantén la comprobación transaccional de cupo al reservar.
2. Obtén horario de cita, campaña, franja, sede y donante autorizado mediante consultas por lote o un resumen del propietario existente. No descargues todas las sedes para resolver las referencias de una página.
3. Conserva la deduplicación ya existente dentro de la petición. Si incorporas lotes, limita cantidad/tamaño y autoriza cada recurso; no habilites enumeración ni acceso cruzado por agrupar IDs.
4. Mantén información, orden, filtros, estados y errores. Los clientes continúan recibiendo JSON/XML compatibles; los comandos de agenda conservan idempotencia y versiones.

**Aceptación:** compara páginas de 1/20/100 elementos donde proceda, con referencias compartidas y distintas. Las consultas de enriquecimiento crecen por lotes necesarios, no con una petición por fila. Demuestra misma disponibilidad y un solo ganador al competir por el último cupo desde clientes reales.

## OPT-04 — Evaluaciones y llamadas entre propietarios

**Inspecciona:** `apps/services/ms_priorizacion_geografia/routes.py`, `apps/services/ms_compatibilidad/routes.py`, `apps/services/ms_compatibilidad/freshness.py` y `apps/services/redhouse/client.py`.

1. Localiza cadenas que consultan cada evaluación y vuelven a solicitar solicitud, inventario y rutas. Usa lotes y consultas por IDs pertinentes dentro de los propietarios actuales.
2. Reutiliza durante una petición únicamente lecturas equivalentes de identidad, ámbito, filtros y versiones. No reutilices un dictamen o comprobación clínica para otra solicitud o para datos modificados.
3. Acorta la ocupación SQL durante HTTP: separa lectura local, obtención remota y revalidación final cuando sea compatible con la consistencia requerida. No retires bloqueos de escrituras atómicas ni muevas verificaciones críticas fuera de la transacción sin sustituir su garantía.
4. Conserva sesiones HTTP reutilizables, límites de tiempo y manejo de respuesta incierta. Si paralelizas lecturas independientes, fija concurrencia acotada y evita compartir contextos Flask/credenciales entre usuarios. No añadas reintentos generales de escrituras.

**Aceptación:** menos llamadas repetidas y menor tiempo de conexión/bloqueo ocupado; misma explicación, orden y exclusiones de candidatos. Probar datos modificados durante la espera remota, evaluación obsoleta, error de propietario y respuesta perdida tras commit. Ninguna propuesta se convierte en reserva o autorización automática.

## OPT-05 — WSS y Redis sin sondeo SQL por espectador

**Inspecciona:** `apps/services/ms_transporte/tracking.py`, `apps/services/ms_transporte/tracking_socket.py`, `apps/services/redhouse/db.py`, claves `tracking:last:*`, canales `tracking:channel:*` y ACL actuales.

La investigación encontró publicaciones Redis y última posición almacenada, pero consultas SQL periódicas por suscripción aproximadamente cada 0,5 s. `snapshot()` tomaba `FOR UPDATE` sobre el traslado incluso sin eventos nuevos. Comprueba que sigue ocurriendo antes de modificarlo.

1. Usa las señales Redis existentes para activar entrega a espectadores y compartir lecturas por traslado cuando sea seguro. Suscribe cada proceso/worker según su ciclo de vida; usa las bibliotecas actuales y ACL limitadas a los canales propios. No añadas un broker ni cambies el protocolo externo WSS JSON/XML.
2. Publica solo hechos persistidos después del commit. Redis Pub/Sub es un aviso efímero: conserva historial SQL, cursor, instantánea, deduplicación y reconciliación acotada ante avisos perdidos. Resuelve la carrera entre suscripción e instantánea y la reconexión de procesos.
3. Revisa bloqueos de lectura sin eliminar los necesarios para consistencia. Un espectador inactivo no debe tomar repetidamente un bloqueo exclusivo del traslado por falta de eventos nuevos.
4. Mantén comprobación de sesión, revocación, asignación y recurso antes de entregar datos. Compartir el dato interno entre conexiones no comparte permisos. Si falla la autorización, se rechaza/suspende entrega; un evento de canal no concede acceso.
5. Separa renovación de registros de conexión, heartbeat, autorización y frecuencia de datos. Reduce renovaciones redundantes y agrupa operaciones independientes con pipeline si corresponde. No alargues intervalos de seguridad ni cambies vencimientos para aparentar ahorro; mantén registro válido y recuperación ante caída del worker.
6. Conserva límites de mensajes, consumidores lentos y memoria; no mantengas historial ilimitado en cada conexión. Diferencia canal caído, fuente detenida, dato antiguo y cartografía indisponible.

**Aceptación:** con 1 y varios espectadores del mismo traslado, registrar consultas de datos, comandos Redis y comprobaciones de seguridad por separado. Durante inactividad, las consultas/bloqueos de posición dejan de multiplicarse por espectador. Probar publicación concurrente, aviso perdido, duplicado, desorden, cursor vencido, reinicio de réplica, cambio de transportista, revocación con socket abierto y Redis inaccesible. Todos los consumidores autorizados conservan mismos eventos/cursores y datos antiguos identificados.

## OPT-06 — Caché útil, invalidación y memoria en Redis existente

**Inspecciona:** `apps/services/redhouse/cache.py`, `apps/services/ms_inventario/queries.py`, `apps/services/ms_inventario/migrations/004.sql`, `apps/services/redhouse/portal_metrics.py`, `apps/services/redhouse/security.py`, configuración generada y configuración efectiva autorizada.

### Elegir datos y contratos de caché

Evalúa estos candidatos; implementar cada uno exige coste recurrente y beneficio comprobados:

| Candidato | Ámbito y regla mínima |
| --- | --- |
| Resúmenes/paneles de inventario | Institución/región, permisos efectivos, filtros, periodo y revisión de los datos. Disponibilidad mostrada no autoriza reservar. |
| Sedes, catálogos y campañas publicadas | Campos mínimos, visibilidad vigente y versión; invalidar al editar, retirar o cambiar alcance. |
| Contadores de avisos | Propietario y usuario autorizado; derivación reconstruible, deduplicación de eventos y actualización tras lectura/revocación. |
| Última posición y señal de actualización | Solo dentro de Transporte, período/tarea autorizados, fuente/hora y cursor; historial durable separado. |
| Referencias inmutables versionadas | Preferir reutilización acotada en memoria del proceso cuando evite viajes adicionales. Conservar verificación de integridad, versión y detección de cambio; no cachear dictámenes clínicos como si fueran catálogos. |

Para cada caché documenta propietario, datos, clave, ámbito, versión, tamaño máximo, TTL justificado, invalidación, reconstrucción y comportamiento de error. No fijes un TTL universal. Claves sin datos personales ni secretos. No almacenes tokens, XML clínico completo, archivos ni URLs firmadas reutilizables como caché de negocio.

### Evitar repetición y obsolescencia

1. Usa primero reutilización dentro de una petición para referencias idénticas, sin mezclar actores. Usa Redis para resultados que realmente se repiten entre peticiones/procesos. Mantén los cachés de clientes mínimos y separados de este mecanismo backend.
2. La caché actual puede incluir usuario aun para agregados idénticos. Solo comparte entre usuarios después de demostrar que ámbito, recursos visibles y campos son equivalentes. Mantén identidad en resultados personales. Reautoriza cada petición aunque haya HIT.
3. Evita que todos los MISS concurrentes recalculen la misma clave/generación. Si hace falta coordinación Redis, exige espera acotada, caducidad, propietario y liberación condicional; caída del productor recuperable. No conviertas ese mecanismo en autoridad de reservas. Evita esperas indefinidas y tormentas de reintentos.
4. La revisión global de inventario se actualiza transaccionalmente. Si su invalidación o contención demuestra coste, estudia revisiones por ámbito dentro de PostgreSQL existente. Una transferencia invalida origen, destino y agregados pertinentes. Una lectura anterior al commit no puede rellenar una generación utilizada por lecturas posteriores. TTL y avisos de invalidación son respaldo, no sustitución de esa garantía.
5. Mantén Redis de negocio prescindible cuando la autorización siga funcionando: un error exclusivo de caché debe permitir consultar la fuente autorizada. Una caída de Redis que impide verificar sesión/permisos sigue cerrando el acceso; no habilita un modo inseguro.
6. Acota duración, cardinalidad y tamaño de entradas. Mide memoria por familia, errores, HIT/MISS, expiraciones, tiempo de reconstrucción y coste de escritura/persistencia. Conserva instancia, aislamiento, `noeviction` y durabilidad actuales. No apliques `allkeys-lru`/`volatile-lru`: también hay claves de seguridad con TTL. Si el presupuesto compartido no permite una caché adicional, reduce su alcance o descártala; no crees otra instancia.

**Aceptación:** carga fría/caliente comparable; menos consultas en HIT y reconstrucciones concurrentes acotadas. Probar escritura simultánea con llenado, cambio institucional/de permisos, transferencia, logout/revocación, expiración, productor caído y error exclusivo de caché. Comparar valores con fuente autoritativa y mostrar antigüedad donde corresponda. No reducir auditoría ni llamadas obligatorias de autorización para lograr el objetivo.

## OPT-07 — Panel web, datos secundarios y comprobación de sesión

**Inspecciona:** `apps/web/src/integration/routes/dashboard.py`, `apps/web/src/integration/client.py`, `apps/web/src/integration/__init__.py`, `apps/web/src/integration/routes/auth.py`, `apps/web/src/presentation/static/js/session.js` y métricas de sus propietarios.

1. Confirma llamadas secuenciales del panel por rol. Consolida agregados compatibles en cada propietario. Renderiza tareas y resumen imprescindible antes de métricas secundarias cuando pueda conservarse la experiencia y sus estados.
2. Usa fragmentos/rutas del propio portal para carga posterior; no muevas el navegador a API independientes. Conserva errores parciales visibles, accesibilidad y autonomía del monolito. Reserva espacio para evitar saltos visuales y evita volver a solicitar lo ya incluido en el HTML.
3. `/sesion/estado` debe comprobar sesión, Redis y revocación sin preparar catálogos de instituciones o etiquetas visuales que no consume. Distingue esa preparación de la autorización obligatoria.
4. Reduce sondeos redundantes entre pestañas o destinos visibles usando mecanismos existentes/nativos. Conserva expiración, revalidación al recuperar visibilidad, logout y renovación coordinada. No compartas tokens mediante mensajes entre pestañas ni interpretes ausencia de sondeo como sesión válida.

**Aceptación:** comparar roles con/sin métricas, una y varias pestañas, primer HTML/contenido útil y final de todas las cargas. Misma información accesible y errores reales; menos llamadas bloqueantes. Probar API independientes detenidas, dependencia caída, expiración en pestaña oculta y cambio de permisos. Diferir trabajo no basta si el coste total aumenta o la tarea principal empeora.

## OPT-08 — Highcharts, assets y transferencia web

**Inspecciona:** `apps/web/src/presentation/templates/integration/dashboard.html`, `apps/web/src/presentation/templates/base.html`, `apps/web/src/presentation/static/js/charts.js`, configuración Flask, `deployment/nginx.conf` y `deployment/gcp/configure_public.py`.

1. No incluyas Highcharts/accesibilidad en vistas sin gráficas. Conserva Highcharts donde es requerido y su accesibilidad. Construye gráficas secundarias cuando sean necesarias, evitando instancias/observadores duplicados al actualizar fragmentos. Mantén tablas equivalentes, dimensiones reservadas, exportación/impresión y todas las series.
2. Genera huellas de contenido y referencias reproducibles para assets mediante herramientas ya presentes. Aplica caché prolongada solo a archivos públicos inmutables. Conserva `no-store` y controles de acceso en HTML/API/documentos privados; no caches páginas autenticadas globalmente.
3. Verifica configuración y encabezados efectivos antes de afirmar que falta compresión. Aprovecha gzip nativo si está disponible para JS/CSS/SVG públicos; no instales módulos nuevos, añadas CDN ni comprimas indiscriminadamente respuestas sensibles. La configuración versionada no acredita producción.
4. Conserva fuentes WOFF2 locales, `font-display: swap`, scripts `defer`, debounce/cancelación y protecciones de formularios ya existentes. No empaquetes o cambies dependencias para rehacer lo resuelto.

**Aceptación:** panel sin gráficas no descarga sus bibliotecas; medir bytes originales y transferidos por separado, caché fría/caliente, tareas largas y renderizado. Verificar CSP, carga fallida, actualización de versión y rollback sin referencias rotas. Las páginas privadas no adquieren caché compartida y una nueva versión sirve sus assets correctos.

## OPT-09 — Móvil: carga por sección, estado y cliente HTTP

**Base común:** `apps/mobile/composeApp/src/commonMain/kotlin/org/redhouse/mobile/`. Revisa `App.kt`, `Api.kt`, `DonorScreen.kt`, `MobileRepository.kt` y el ciclo de vida Android/iOS.

1. Divide recargas completas por secciones y dependencias reales. Después de reservar/cancelar, actualiza citas y disponibilidad afectada sin volver a cargar todos los catálogos y expedientes. Comparte peticiones idénticas en curso solo dentro de la misma identidad/gateway/ámbito.
2. Conserva página, filtros, selección y desplazamiento al volver. Usa caché mínima/acotada de resultados autorizados cuando proceda, con antigüedad explícita e invalidación por escritura, cambio de cuenta/gateway, logout y pérdida de permiso. No presentes datos anteriores como actuales ni uses filtrado local como autorización.
3. Revisa el `busy` global: permite navegación y cancelación de lecturas por destino sin liberar escrituras críticas en curso. Una respuesta tardía no actualiza otra pantalla o identidad. Cancelar la espera de un comando no revierte un commit: conserva clave estable, estado incierto y recuperación.
4. Define propietario/ciclo de vida de `HttpClient`; reutiliza transporte sin mezclar sesiones y cierra instancias descartadas tras restauración/login fallidos, reemplazo o destrucción. Conserva TLS, validación JSON, renovación coordinada y tratamiento de revocación. No añadas reintentos generales de comandos.
5. Pagina realmente listas que superan la primera página. Usa `LazyColumn` y claves estables ya disponibles en colecciones que crecen, sin introducir bibliotecas ni anidar scrolls verticales ilimitados. No optimices una lista pequeña a costa de complejidad sin beneficio.

**Aceptación:** tareas equivalentes de los cinco perfiles móviles, con consultas/peticiones registradas; volver a una lista conserva contexto y evita cargas redundantes. Probar navegación rápida, respuestas fuera de orden, rotación/recreación, red lenta, doble toque, pérdida de respuesta después de commit y cambio de cuenta. Repetir login/logout/restauración sin crecimiento injustificado de clientes o trabajos activos. No retirar funciones ni alterar permisos para reducir datos.

## OPT-10 — Móvil: disco, cifrado, JSON y fotografías

**Inspecciona:** `Api.kt`, `MobileRepository.kt` y `TransportScreen.kt` dentro de la base común de OPT-09; `Platform.kt` y `AndroidDeviceAccess.kt` en `apps/mobile/composeApp/src/androidMain/kotlin/org/redhouse/mobile/`; adaptadores en `apps/mobile/composeApp/src/iosMain/kotlin/org/redhouse/mobile/`, `apps/mobile/iosApp/AppDelegate.swift` y `apps/mobile/iosApp/IOSDeviceAccess.swift`.

1. Separa del hilo principal disco, cifrado, parseo/validación costosos y procesamiento de imágenes usando mecanismos existentes compatibles con cada plataforma. `suspend` no cambia por sí solo el hilo. Respeta las APIs que requieren el hilo principal y publica allí únicamente el estado visual pertinente.
2. Evita leer/descifrar el mismo estado repetidamente si puede mantenerse una representación segura en memoria, con propietario, exclusión y actualización coherente con workers. No prolongues credenciales cerradas ni pierdas revocación/logout por reutilizar estado.
3. Normaliza/comprime una vez por captura y reutiliza la vista previa decodificada mientras no cambie la imagen. Conserva orientación, dimensiones/tamaño permitidos, eliminación de metadatos, hash del archivo finalmente enviado, privacidad y borrado temporal. No relajes calidad o límites sin conservar el requisito original.
4. Un resultado tardío de cámara/procesamiento no se asocia a otro traslado o cuenta. Evita crecimiento de bitmaps/bytes y libera previews descartadas. Conserva `FLAG_SECURE` y protecciones iOS; no las retires para conseguir evidencia.

**Aceptación:** trazas/mediciones disponibles muestran reducción del trabajo costoso en UI y ausencia de pausas atribuibles al incremento. Compara captura, vista previa, eliminación y carga autorizada con la misma imagen/dispositivo. Probar cancelación, imagen inválida/grande, orientación, cambio de tarea y logout. Comparar hash enviado con evidencia verificada; ninguna mejora cambia el archivo inadvertidamente después de calcularlo.

## OPT-11 — Móvil: sincronización, diario y rastreo

**Inspecciona:** `App.kt`, `TransportScreen.kt`, `ObservationQueue.kt`, `MobileRepository.kt` y `Tracking.kt` dentro de la base común de OPT-09; `apps/mobile/composeApp/src/androidMain/kotlin/org/redhouse/mobile/ObservationWorker.kt` y adaptadores de segundo plano/mapa Android/iOS.

1. Elimina ciclos de sincronización redundantes de interfaz y coordina un ejecutor efectivo por identidad con los trabajadores existentes. Activa trabajo por pendientes, conectividad y ciclo de vida; conserva restricciones de red, backoff, expiración y límites de intentos.
2. Evita mantener el mutex de almacenamiento durante toda la espera HTTP cuando pueda separarse selección/persistencia/envío/confirmación. El ID, cuerpo, identidad y estado incierto deben quedar durables antes de enviar. Una carrera UI/worker no puede producir dos efectos ni perder la propiedad del trabajo. Las retransmisiones necesarias conservan identidad, clave y cuerpo; el servidor mantiene la idempotencia.
3. Reduce reescrituras del diario completo solo si conserva cifrado, atomicidad y recuperación ante cierre forzado. No añadas Room ni otro almacén. No retrases una escritura necesaria para la idempotencia con el fin de mejorar tiempos.
4. Conserva JSON/WSS, consentimiento, tarea/dispositivo, fuente, hora original, cursor y ACK durable. Optimiza recomposición/anotaciones del mapa solo con evidencia; no inventes posiciones ni disminuyas precisión/cadencia exigida. El GPS no confirma custodia.

**Aceptación:** un coordinador efectivo sin ciclos UI duplicados; menor trabajo en reposo y captura/navegación no detenidas por toda la sincronización. Probar varios pendientes, cierre después de persistir/antes de enviar/después de commit, red intermitente, worker e interfaz simultáneos, logout y cambio de identidad. Una sola aplicación de cada comando con la misma clave y cuerpo, pendientes recuperables y nunca enviados bajo otra cuenta.

## OPT-12 — Outbox, conexiones y trabajos de fondo

**Inspecciona:** `apps/services/redhouse/events.py`, `apps/services/redhouse/db.py`, workers actuales y límites por proceso/réplica.

1. Mide transacciones/conexiones retenidas mientras se envían eventos a HTTP/MongoDB. Conserva outbox PostgreSQL, deduplicación, `SKIP LOCKED`, reintentos y manejo de destinos degradados.
2. Prefiere ajustes acotados y medidos de lotes/concurrencia. Si es necesario enviar fuera de la transacción, reclama trabajo con concesión persistida recuperable, vencimiento y confirmación condicionada a su propietario. Conserva orden por recurso cuando importe y entrega al menos una vez sin efectos duplicados.
3. No sustituyas outbox por Pub/Sub ni por una cola nueva. Fallo después de enviar y antes de confirmar debe poder repetir de forma segura. Un productor/worker caído no deja trabajo perdido o bloqueado indefinidamente.
4. Presupuesta conexiones considerando todos los procesos y réplicas existentes. Mantén reutilización HTTP/Redis/PostgreSQL; evita aumentar cada pool de forma independiente hasta saturar los almacenes. Comprueba que un ajuste de workers no perjudique tareas interactivas.

**Aceptación:** menor ocupación durante esperas externas y backlog/edad de eventos controlados bajo la misma carga. Probar caída después de reclamar, después de enviar y antes de confirmar, destino lento y recuperación. Comparar IDs persistidos/entregados y efectos, sin pérdida de auditoría, notificaciones ni cadena de custodia.

## Verificación transversal y límites de plataforma

Ejecuta pruebas proporcionales a los cambios, apoyadas en las existentes. No escribas tests que solo repitan la implementación. Comprueba:

- Equivalencia de resultados, autorización por rol/recurso/institución, formatos JSON/XML/XSD, validación y errores. Incluye acceso ajeno, revocación con caché caliente y cambio de permisos durante una petición/socket.
- Concurrencia de último cupo, reserva, versiones e idempotencia; respuesta perdida después de commit. Mantén motivos, confirmaciones, auditoría y rechazo de operaciones críticas offline.
- Fallo exclusivo de caché frente a fallo de autorización Redis; caída de SQL/MongoDB, canal WSS, worker y red según los incrementos afectados. No uses una respuesta falsa como sustituto de una dependencia realmente detenida sin identificar el doble de prueba.
- Web autónoma con API independientes detenidas, y clientes por sus contratos normales. No conviertas consultas rápidas en acceso directo a almacenes o reglas duplicadas.
- Caché fría/caliente, expiración simultánea, invalidación concurrente, productor de caché caído, tamaño/cardinalidad acotados y memoria estable durante recorridos repetidos.
- Android e iOS por separado. La decisión vigente es **iPhone físico autorizado, sin descargar runtime Simulator**. Registra equipo/SO, build, firma/instalación y tareas. Emulador, ubicaciones inyectadas, compilación arm64 y pruebas JVM no acreditan por sí solos ejecución física, batería ni fluidez iOS. Continúa trabajo independiente si falta acceso y conserva ese criterio no verificado.
- Mantén navegación accesible, foco/lectores de pantalla, escala y datos de todos los roles al cambiar renderizado o carga diferida. No uses capturas para demostrar rendimiento ni un indicador de carga para simular éxito de una operación.

Valida migraciones e índices en copia aislada, conservación de datos y compatibilidad con la versión previa. Prepara reversión concreta y límites: revertir aplicación no deshace automáticamente nuevas escrituras. Una configuración local aprobada no acredita que se haya publicado ni que GCP use los mismos valores.

## Entregables al ejecutar y criterio de cierre

Al implementar este encargo, guarda evidencia en las carpetas existentes o en `documentation/evidencias/optimizacion/<fecha>/` y la matriz en `documentation/entrega-final/optimizacion/Matriz.md`. Estas rutas son entregables futuros, no archivos que deban inventarse al redactar el prompt.

Entrega:

1. Matriz OPT-01…OPT-12 con requisitos invariantes, hallazgo vigente, decisión, archivos, métrica antes/después, comandos/casos, fuentes, entorno y resultado. Relaciona CONT/WEB/MOV/TRACK afectados sin duplicar resultados históricos.
2. Datos brutos y resumen de coste por tarea, planes relevantes, trazas/minimización de payloads y clasificación de caché, simulación y dispositivos. Un error corregido o una prueba repetida no se cuenta como un caso nuevo.
3. Cambios pequeños revisables, pruebas relevantes aprobadas, regresiones pendientes y explicación de candidatos descartados. Un objetivo no medido queda NO VERIFICADO; un candidato descartado no se declara optimizado.
4. Comprobación de dependencias/arquitectura: ninguna tecnología, extensión, instancia, servicio ni acceso directo nuevo; mismos contratos y funcionalidades. Documenta cualquier ampliación compatible estrictamente necesaria dentro de un propietario.
5. Configuración y procedimientos reproducibles de compilación/ensayo/reversión; publicación solo con autorización vigente para esa acción. Ningún secreto ni dato clínico real en archivos, logs o capturas.
6. Actualización de `PROJECT_STATUS.md` con lo implementado, probado, no medido y pendiente externo. El cierre de optimización no cierra automáticamente 04, 06, 07 u otros requisitos de producto.

Declara mejora solo si reduce el coste objetivo bajo condiciones comparables y conserva comportamiento y seguridad. No mantengas una complicación sin beneficio demostrado; simplifícala o revierte ese incremento, preservando cambios ajenos. Una mejora de latencia que dispara consultas, memoria, errores o antigüedad debe justificar el intercambio y respetar los límites registrados previamente. No prometas un porcentaje global a partir de una única pantalla.

La respuesta final al ejecutar debe indicar qué tareas mejoraron, con cifras comparables; qué se conservó; qué pruebas pasaron; qué no pudo medirse; y qué sigue pendiente. No basta con «se agregó caché» o «compila».

## Referencias técnicas para aplicar con las versiones instaladas

Referencias oficiales consultadas durante la investigación del 11/11/2026. Verifica compatibilidad con las versiones del proyecto al ejecutar; leer una documentación reciente no autoriza actualizar dependencias ni incorporar tecnologías.

- [PostgreSQL: EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html): interpretar planes, filas estimadas/reales y coste de ejecución.
- [PostgreSQL: LIMIT/OFFSET](https://www.postgresql.org/docs/current/queries-limit.html): orden estable y coste de desplazamientos grandes.
- [PostgreSQL: índices y orden](https://www.postgresql.org/docs/current/indexes-ordering.html): relación entre índices, orden y límites.
- [Redis: Pub/Sub](https://redis.io/docs/latest/develop/pubsub/): entrega efímera; conservar recuperación durable propia.
- [Redis: pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/): agrupar operaciones sin confundir transporte por lotes con atomicidad.
- [Redis: políticas de memoria](https://redis.io/docs/latest/develop/reference/eviction/): presupuesto y consecuencias de expulsar claves; no cambiar la política de seguridad existente.
- [MDN: carga diferida](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Lazy_loading) y [caché HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching): recursos necesarios, versionado y caché de assets.
- [Flask: configuración de archivos estáticos](https://flask.palletsprojects.com/en/stable/config/#SEND_FILE_MAX_AGE_DEFAULT) y [Nginx: gzip](https://nginx.org/en/docs/http/ngx_http_gzip_module.html): verificar capacidades y encabezados efectivos, sin módulos adicionales.
- [Android: coroutines](https://developer.android.com/kotlin/coroutines/coroutines-best-practices), [Compose: rendimiento](https://developer.android.com/develop/ui/compose/performance/bestpractices) y [Ktor: HttpClient](https://ktor.io/docs/client-create-and-configure.html): contexto de ejecución, cálculos/listas y ciclo de vida del transporte. No extrapolar estas guías como prueba del adaptador iOS.
