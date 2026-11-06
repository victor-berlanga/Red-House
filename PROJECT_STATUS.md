# Estado vigente de Red House

Actualizado: **4 de noviembre de 2026**. Leer junto con `AGENTS.md` y el [índice documental](documentation/README.md). El historial detallado está separado del estado actual.

## Comprobación posterior del prompt técnico — 04/11/2026

Se revisaron los nueve archivos de código que cambiaron respecto de la huella
conservada antes de la revisión, la prueba nueva `test_review_costs.py` y las
mediciones documentadas. Sin modificar código: gobernanza compartida dentro de
una misma completitud, eliminación de transacciones vacías, contexto del receptor
consultado una vez, replay vacío omitido bajo bloqueo, emisión WSS con autorización
por entrega, separación de cinco algoritmos y liberación de sesiones por hilo.
El alcance coincide con las mejoras conservadoras solicitadas.

Comprobación propia: **29 pruebas aprobadas en 87,00 s** de `test_review_costs.py`
y `test_review_unit.py`; **15 pruebas algorítmicas/oráculos aprobadas en 1,03 s**,
seleccionadas en `test_final_algorithms_hla.py` y `test_stage02_oracles.py` sin
arrancar almacenes. Total de esta comprobación: **44 casos**, cero fallos.
`document.py --check-openapi`, Ruff crítico y formato de los diez archivos Python
afectados aprobados. No se repitieron las 139 pruebas de la entrega anterior,
integración con almacenes, WSS real ni sus mediciones antes/después.

Aceptación acotada: mejoras y pruebas focalizadas coherentes; no se identificó un
nuevo defecto bloqueante en los cambios inspeccionados. Persiste costo lineal por
candidato y por suscripción. El benchmark de rastreo repite lecturas del mismo
traslado y no mide conexiones completas simultáneas con traslados distintos:
esa parte del prompt sigue pendiente. La reorganización del socket es parcial
(helper de entrega), sin demostrar necesidad de una reescritura mayor. Estos
límites no convierten la revisión en una certificación exhaustiva o productiva.

## Revisión técnica y correcciones locales — 04/11/2026

Se conservaron los cambios preexistentes y archivos sin seguimiento. CodeGraph
consultado antes de localizar código; sin commits, push, despliegues ni cambios
en datos/configuración productivos. Pruebas con almacenes temporales aislados.

Corregido: lectura duplicada de gobernanza en completitud y del contexto del
receptor al comprobar vigencia; transacciones vacías de candidatos sin perfil;
consulta de replay cuando el cursor ya está en cabecera; retención de sesiones
HTTP de hilos finalizados en servicios y web. La emisión `position.updated`
comparte un helper que conserva reautorización por entrega. Las cinco ramas de
`academic.execute` se separaron dentro del mismo módulo: cuerpos AST idénticos,
sin cambios de reglas, versiones, resultados, límites ni contratos.

Evidencia de costo: con 400 recursos instrumentados, 200 candidatos y 100 vinculados
a un perfil, transacciones **201→101** y SQL **603→503**. PostgreSQL real: completitud
**6→5 consultas/candidato**; 100 candidatos, mediana **2597,74→2521,36 ms**. Replay
vacío autorizado **5→4 consultas/snapshot**, sin reducir llamadas Redis. Los tiempos
de rastreo fueron mixtos; no se afirma mejora general de latencia ni saturación.

Criterios: reproducir antes de corregir; preservar aislamiento, vigencia,
contradicciones, fingerprints, replay, revocación y contratos; demostrar reducción
por contadores, equivalencia algorítmica y liberación de pools; conservar historia.
Resultados: línea base **56 aprobadas / 546,03 s**; regresión ampliada **139 aprobadas /
1011,64 s**; validación adicional de fuentes finales **36 aprobadas / 394,75 s**;
OpenAPI **12 aprobadas / 65,25 s** y generación reproducible. Cero fallos, errores u
omisiones en estas ejecuciones. Conteos solapados, no sumables. Los fallos iniciales
del sandbox por apertura de puertos y los fallos esperados de las pruebas nuevas
se conservan descritos en la documentación. Ruff, formato y diff aprobados.

[Hallazgos, metodología, tablas antes/después, comandos y límites](documentation/markdowns/Pruebas_y_validacion.md#revisión-técnica-local--4-de-noviembre-de-2026).
Persiste costo lineal por candidato con perfil y por suscripción. No se introdujo
caché clínica ni una transacción global; precarga entre candidatos y medición de
conexiones completas con distintos traslados quedan pendientes justificados.
La revisión de idempotencia/outbox no justificó retirar sus bloqueos o reintentos.
No equivale a revisión exhaustiva, validación clínica ni certificación productiva.


## Depuración de evidencias y revisión estática — 04/11/2026

Por solicitud del usuario se ordenaron evidencias y se revisó el código sin
modificarlo. Se archivaron 19 detalles textuales extensos y dos capturas duplicadas
en un TAR.GZ versionable. Los 21 miembros conservan los bytes originales; el índice
registra ruta, tamaño, SHA-256 y copia canónica de las capturas. Se preservaron
resultados finales, JUnit, resúmenes e intentos fallidos. No se alteraron manifiestos
históricos ni se recalcularon sus hashes. Los verificadores históricos que leen
detalles archivados requieren restaurarlos antes de su ejecución; el procedimiento
queda en el [índice documental](documentation/README.md#consulta-de-evidencias-voluminosas).

Volumen seleccionado: **33 652 líneas textuales**, 4 226 691 bytes originales;
archivo de **1 484 094 bytes**, más índice de 29 líneas y avisos de consulta.
La reducción proviene de archivar detalles preservados, no de eliminar pruebas ni
de minificar JSON. Los enlaces Markdown afectados apuntan al archivo o a la captura
canónica. No se ha borrado código de reproducción, incluidas las fuentes de los
verificadores históricos.

Revisión estática acotada, sin medición de rendimiento ni certificación funcional:

- **Prioridad media — consultas repetidas por candidato:**
  `apps/services/ms_compatibilidad/routes.py:165` abre una transacción por recurso
  que supera los filtros. `completeness` consulta perfil, resultados, vigencia,
  acciones y contradicciones. Con muchos candidatos se repiten viajes a PostgreSQL
  y lecturas de perfiles compartidos. Conviene medir consultas/latencia por tamaño
  y evaluar precarga por lote, preservando consistencia, permisos y trazabilidad.
- **Prioridad media — sondeo y responsabilidades WebSocket:**
  `apps/services/ms_transporte/tracking_socket.py:63` reúne 248 líneas de
  autenticación, cuotas, publicación, suscripción, replay y entrega. El bucle usa
  recepción con timeout de 0,5 s y consulta snapshots por suscripción incluso sin
  mensajes nuevos; repite la construcción de `position.updated` en replay y
  entrega continua. Conviene medir el costo por conexión/suscripción y separar
  procesamiento de mensajes y entrega; no retirar revalidaciones de permisos.
- **Prioridad media de mantenimiento — despacho algorítmico extenso:**
  `apps/services/ms_priorizacion_geografia/academic.py:168` reúne cinco algoritmos
  en `execute`, con 243 líneas. Son responsabilidades distintas detrás de un
  contrato común; separar implementaciones puras por versión haría más local la
  revisión y las pruebas, conservando entradas/salidas y explicaciones. La longitud
  no demuestra que los algoritmos sean innecesarios ni incorrectos.
- **Complejidad justificada, no retirar sin análisis:**
  `redhouse/shared_schema.py:63` y `scripts/migrate_shared.py:45` contienen lógica
  extensa de transición/preservación de esquemas. Se distinguen construcción de
  esquema y migración de datos; no se comprobó que sean duplicados prescindibles.

El análisis AST de funciones de al menos 12 líneas no encontró funciones completas
idénticas entre los archivos Python de servicios/web inspeccionados, excluyendo
pruebas. Esto no descarta duplicación parcial o con nombres distintos. No se
detectó base para calificar toda la arquitectura como complejidad absurda ni se
modificaron código, configuración, contratos o pruebas durante esta revisión.

Criterios de aceptación: recuperar cada original con su mismo hash; mantener
enlaces documentales de los artefactos movidos; comprobar que ningún archivo de
código cambió durante esta tarea; documentar hallazgos con ubicaciones y límites.
Validación: **21 originales restaurados y cotejados por SHA-256**, incluidos los
JSON parseados y las dos capturas contra sus copias canónicas; SHA-256 del TAR.GZ
correcto. **1 224 archivos de código/configuración/recursos sin cambios** frente al
inicio de esta tarea. **21 enlaces Markdown al archivo/índice comprobados**, cero
enlaces Markdown a las rutas retiradas. La regresión funcional no corresponde a
este cambio documental y de archivo; no se presenta una nueva ejecución de pruebas
de aplicación.

## Compactación de contratos OpenAPI — 04/11/2026

Los doce OpenAPI permanecen versionados y legibles. El generador comparte las 13 respuestas de error por servicio en `components.responses` y declara los esquemas de salida una sola vez en `components.schemas`, con referencias locales `$ref`. Se conservaron rutas, métodos, parámetros, restricciones, seguridad, códigos HTTP y ejemplos JSON/XML. Las evidencias históricas permanecen como estaban.

Criterios de aceptación: reducir repetición sin alterar los contratos al resolver referencias; validar OpenAPI 3.1 y la entrega por Flask/Swagger; regeneración reproducible sin bases ni secretos. Los doce archivos bajaron de **204 772 a 86 934 líneas**, reducción de **117 838 (57,55 %)** frente al árbol de trabajo previo a esta tarea. La comparación recursiva de todas las rutas, expandiendo referencias locales antes/después, resultó idéntica en los doce servicios. `document.py --openapi-only` regenera solo OpenAPI; `--check-openapi` verifica sin escribir y queda incorporado a CI. [Comandos](apps/services/README.md).

Validación: generación y comprobación de reproducibilidad aprobadas; Ruff y formato aprobados. La prueba parametrizada `test_openapi_documentation.py` verifica los doce servicios sin levantar dependencias: validez del documento, igualdad con el exportado y con `/openapi.json` y `/docs/swagger.json`, referencias de error y representaciones JSON/XML. **12 pruebas aprobadas en 66,12 s**, cero fallos. No se ejecutó la regresión funcional completa ni se desplegaron cambios; consumidores propios deben resolver `$ref` según OpenAPI. CI remoto pendiente.

## Demostración con controles nativos en GCP — 04/11/2026

Se grabó el portal publicado mediante cursor, teclado y desplazamiento reales de macOS, Chrome a pantalla completa y captura física AVFoundation. Traducción automática desactivada para evitar el aviso que tapaba el acceso. Durante las tomas se navega por menús, enlaces, búsquedas y formularios, sin escribir URLs. Montaje de **24 min 41 s**, 62 capítulos, H.264 1440×944, sin audio; títulos por funcionalidad, notas sobre reglas y cortes de credenciales/MFA. Las tomas y el MP4 permanecen privados en `.local/video-gcp-20261104/`.

Se muestran laboratorio/HLA, fuentes y completitud, seis ramas algorítmicas académicas, solicitud/revisión, corrección e invalidación de evaluación, reserva, traslado completo, custodia, destino con historia, reporte GCS, auditoría y módulos por perfil. El tramo final principal obtuvo **50 comprobaciones**, descarga privada y cero errores de JavaScript/HTTP registrados en ese tramo; no se suman reintentos ni se presenta como certificación de todos los módulos. La consulta de completitud del complemento devolvió `clinical_approval=false`. Portal vivo y Compatibilidad 0.4.4 confirmados por HTTPS al terminar. No se modificó ni desplegó código de la aplicación.

Pendiente observado: el diálogo de detalle del perfil `7bf03011-eb76-4438-9fe8-73d1be0a257a` mostró un fallo de carga desde `/laboratorio/perfiles`; causa sin determinar. Reproducir con el mismo rol y revisar la petición del diálogo. Se documentan además interrupciones del controlador de grabación; los fragmentos interrumpidos no se presentan como exitosos. La demostración no sustituye auditoría independiente, validación clínica, carga ni pruebas exhaustivas. GPS físico/WSS no se ejecutaron; ruta y ETA no representan tráfico ni entrega física.

[Video, índice, comprobaciones e incidencias](documentation/evidencias/gcp/demostracion-nativa-20261104/RESULTADOS.md). Decodificación completa del MP4 sin errores, hash coincidente, cero solapamientos con intervalos privados marcados y textos inferiores sin truncamiento; revisión visual por muestreo. Se conservan las versiones, registros e historia anteriores; no cambia el veredicto clínico ni el alcance de las verificaciones previas.

## Publicación de etapa 02 en GCP — 02/11/2026

Por instrucción expresa «Antes que nada, sube todo a gcp», se encendió y actualizó la VM existente `red-house` (`sistemas-integracion-01`, `me-central1-a`). Portal disponible en **https://34.18.186.116**. Release **0.4.4 / esquema 16**, con imágenes de aplicación etiquetadas 0.4.4. Compatibilidad/Geografía anuncian 0.4.4; los otros diez módulos conservan su versión propia 0.4.1, cotejada contra código. Todos usan las fuentes actuales empaquetadas; no se desplegó el main antiguo.

**Respaldo y restauración aislada PostgreSQL/MongoDB/Redis aprobados antes de migrar.** Código/configuración/imágenes anteriores conservados. Tras 13→16: 106 tablas de dominio idénticas en sus columnas históricas y solo `schema_migration` cambia según lo previsto; 73 campos/archivos sensibles conservados. No se sustituyeron datos remotos por bases locales. Catálogo HLA 3.66.0 montado de solo lectura, integridad comprobada en web y ambas réplicas.

**Comprobado en GCP:** 30 contenedores sanos, 3.565 fuentes cotejadas, imágenes con código coincidente, 24 consultas HTTPS de salud y 28 respuestas JSON/XML validadas. Registro HLA ficticio reconocido/persistido sin dictamen, fuente vial pública importada y ejecución reproducida. GCS real con identidad adjunta: subida/descarga firmadas, rechazo anónimo y eliminación del objeto temporal propio. Chrome público: **8 comprobaciones**, MFA/cookie Secure, fuentes, resultados/completitud/ruta/perfiles, recarga; sin errores de consola/red ni grabaciones/capturas.

La operación sigue **ACADEMIC**, con MFA/reautenticación y controles de laboratorio/órganos. Publicar no habilita clínica. GPS físico, protocolos/aprobaciones clínicas y cobertura vial operativa permanecen pendientes. No se volvió a ejecutar toda la suite local, carga, WSS ni el recorrido documental HLA completo en GCP. La comprobación independiente previa no se atribuye al despliegue nuevo.

[Expediente de publicación, versiones, incidencias y rollback](documentation/evidencias/gcp/etapa02-20261102/RESULTADOS.md). Los apartados siguientes son historia fechada; sus pendientes de publicación 0.4.4 quedan resueltos en el alcance aquí descrito.

## Fuentes públicas y comprobación técnica — 02/11/2026

Código local **0.4.4 / esquema 16**; sin despliegue GCP ni cambios en instalaciones habituales. El usuario dejó el GPS físico para el final y autorizó otro agente auditor, sin edición de archivos. No se inventaron aprobadores, protocolos ni prioridades clínicas.

Implementado: cinco referencias documentales primarias con ID/versión/sección/ámbito/vigencia, snapshot y SHA-256 en perfiles; pertenencia HLA contra IPD-IMGT/HLA 3.66.0 fijada por commit/hash, separada de sintaxis, resolución y dictamen; política opcional de catálogo obligatorio, errores cerrados ante fuente ausente/corrupta y correcciones históricas. El catálogo original se instala mediante descarga explícita, no se redistribuye modificado. Se integraron tres trayectos urbanos reales OSRM/OpenStreetMap mediante manifiesto, licencia, geometría, pesos y procedencia, importación autorizada JSON/XML y formularios web. La antigüedad del mapa sigue desconocida; la descarga tiene fecha. ETA modelada no usa GPS ni tráfico medido.

Validación: **110 casos únicos aprobados** (109 de regresión + un caso de navegador con **23 comprobaciones**), sin sumar reintentos. La ejecución de 109 tuvo 108 aprobados y un 503 de Redis; el caso afectado pasó en entorno aislado posterior, sin cambios de código. Ambos intentos se conservan; causa raíz de esa indisponibilidad puntual no determinada. Chrome verificó MFA/reauth, roles/tenants, seis ramas, HLA/fuentes/ruta real, persistencia y autonomía con APIs detenidas; único error HTTP registrado fue el 409 esperado de reserva obsoleta. El auditor ejecutó **22 pruebas independientes** y verificó el cierre de dos hallazgos: catálogo obligatorio eludible mediante `CUSTOM_HLA`, y disponibilidad vial que omitía integridad. Esas pruebas no se suman al total único. Hubo también un fallo inicial de presentación HLA, corregido antes del navegador final.

Migración/restauración aislada 14/15→16 con repetición y comparación de historia; **1.993 archivos de evidencia anterior intactos**. Manifiesto de **1.117 fuentes** identifica el árbol sin commit. Descarga HLA reproducida con hash exacto y renovación vial real comprobada sin sustituir el paquete instalado. Ruff pasó. CI incorpora adquisición de HLA, pero no se ejecutó CI remoto. No se repitió GCS real ni se verificó producción en este incremento; GCP conocido sigue 0.4.1/esquema 13 según evidencia previa, sin nueva consulta.

[Resultados y comandos](documentation/evidencias/entrega-final/algoritmos/fuentes_publicas/20261102T143541Z/RESULTADOS.md) · [Matriz vigente](documentation/entrega-final/algoritmos/correccion/Matriz_fuentes_publicas.md) · [Instalación de fuentes y límites](documentation/entrega-final/algoritmos/correccion/Operacion_y_reproduccion.md).

Contraste final del auditor: 1.117 hashes coincidentes, 1.993 evidencias conservadas, consolidación de 110 identidades respaldada por JUnit y 23 comprobaciones Chrome coherentes. Sin nuevos bloqueos confirmados: **APTA PARA CONTINUAR para el incremento técnico académico 0.4.4/esquema 16**. No repitió independientemente la suite completa ni el navegador; verificó sus artefactos y mantuvo separados sus 22 casos propios. Recomendó vigilar recurrencias del 503 de Redis, sin afirmar que el reintento elimine su causa.

Alcance: los cambios públicos/técnicos pedidos están completados localmente. La revisión independiente acredita los mecanismos revisados, no toda la plataforma ni certificación médica. Protocolos, política clínica y acreditaciones reales siguen siendo dependencias para operación clínica; no bloquean los perfiles académicos que permite el prompt. Tres trayectos públicos no acreditan cobertura hospitalaria ni actualidad vial operativa. Para cerrar la etapa en entorno publicado, revalidar GCS y versión desplegada y completar la comprobación integral final. GPS físico permanece aplazado expresamente. **CONTINUACIÓN PARCIAL POR DEPENDENCIA DECLARADA** para el cierre completo de etapa 02; no se afirma cierre clínico/productivo.

## Revisión de cierre de prompts 01 y 02 — 02/11/2026

Revisión de alcance y evidencia, sin nueva ejecución funcional ni acceso a GCP. El prompt 01 exige backend y contratos; excluye construir todavía los clientes. Por tanto, Android/escritorio/mapa de consumidores y aceptación del hardware no se contabilizan como defectos del backend por sí solos. La matriz backend del 29/10 conserva pendientes productivos desactualizados: la evidencia GCP del 31/10 documenta despliegue 0.4.1/esquema 13, restauración, 30 contenedores, contratos y recorrido visible. No debe reutilizarse para acreditar 0.4.3/esquema 15. La aceptación independiente completa del backend actual sigue sin constancia; la evidencia de 370 casos corresponde al árbol anterior.

El prompt 02 permite explícitamente perfiles académicos con aplicación clínica desactivada cuando falta aprobación profesional, y simulaciones si falta política aprobada. Esas dependencias no demuestran por sí solas incumplimiento técnico. Existe evidencia local de 117 casos sobre las fuentes finales y los 1.050 hashes continúan coincidiendo. La repetición independiente anterior aprobó 12 oráculos y 44 casos adicionales, pero se interrumpió en PostgreSQL; no acredita la suite completa. La geografía documentada sigue usando un grafo sintético; falta comprobar la fuente vial real para operación real. No hay aprobación clínica ni nueva comprobación productiva de 0.4.3.

Veredicto: no se certifica cumplimiento total de ambos prompts. Backend implementado con evidencia de despliegue anterior; etapa 02 implementada en alcance académico local con límites declarados. Pendientes de cierre verificable: reconciliar matriz backend con evidencia posterior, completar regresión independiente del árbol vigente y verificar integraciones pendientes según alcance; mantener separada la habilitación clínica externa. No se detectó un nuevo defecto funcional mediante esta revisión documental/estática; tampoco se afirma ausencia de defectos. No se modificó código funcional.

## Comprobación independiente de etapa 02 — 01/11/2026

Se contrastó el prompt original con la matriz correctiva, gobierno de perfiles y evidencia final. Los SHA-256 actuales coinciden con los 1.050 archivos de `sources-final.json`; los cuatro JUnit finales contienen 117 casos sin fallos registrados. Esto comprueba correspondencia con la evidencia histórica, no una nueva ejecución de los 117 casos.

Repetición independiente: `test_stage02_oracles.py` aprobó 12 casos en 129,40 s (`/tmp/independent-stage02-oracles.xml`). La suite adicional de correcciones, migración, HLA y calidad aprobó 44 casos antes de interrumpirse tras 474,27 s, esperando en `psycopg/connection.py:300`; salida 2 por KeyboardInterrupt. No se declara aprobada la suite completa ni se atribuye la espera a un defecto funcional confirmado. No se repitieron Chrome, GCS, WSS ni despliegue. No se modificó código funcional.

Veredicto limitado: existe implementación técnica local comprobable; no se acredita cierre total del prompt. Continúan dependencias clínicas/geográficas declaradas y queda pendiente completar la repetición interrumpida y la comprobación productiva.

## Corrección ejecutada de etapa 02 — 01/11/2026 UTC

Código local **0.4.3 / esquema 15**; doce servicios y web modular, sin nuevo despliegue ni cambios en instalaciones habituales. El estado de GCP descrito abajo corresponde al incremento anterior. Se conservaron los cambios locales preexistentes, las evaluaciones y las versiones RBC-1.0, ORGAN-1.0, LOGISTICS-1.0 y COVERAGE-HK-1.0.

Implementado: gobierno de perfiles inmutables con acciones/retiro y segregación; sintaxis HLA por versión soportada y grupos parciales; asociaciones órgano/sujeto/solicitud y pruebas cruzadas estructuradas; documento privado verificado; completitud con vigencia, antigüedad y contradicciones; separación operativa académica/clínica y obsolescencia del laboratorio de ambos sujetos. Inventario bloquea uso clínico de datos académicos y serializa correcciones con el commit de reserva. Plasma/plaquetas tienen flujo manual con perfil, sin heredar RBC.

ALG-01 usa perfiles registrados y reproduce exclusiones desde instantánea. ALG-02 usa política sintética registrada y factores de propietarios; urgencia/espera no se atribuyen a LOGISTICS-1.0. Dijkstra usa grafo regional versionado de Nuevo León, con adaptador/fixture identificado y lectura autorizada de Transporte; distingue observación, recorrido, ruta y ETA estimada. HK conserva cardinalidad máxima sin reservas automáticas. SES consume historia por institución/producto/ventana; anomalías parten de hechos de cinco propietarios y abren revisión deduplicada en Auditoría mediante outbox. Formularios web para las seis ramas, laboratorio, perfiles, completitud y revisión de anomalías.

**Comprobado: 117 casos distintos aprobados, cero fallos/errores pendientes y cero omitidos**, consolidados por identidad entre cuatro ejecuciones finales con aplicabilidad de fuentes documentada. Chrome real: **20 comprobaciones**, MFA/reauth y laboratorio/órganos activos, APIs detenidas, roles/tenants, completitud, seis ramas, obsolescencia, reserva y resolución. GCS real: carga/descarga privada, generación/hash y rechazos; WSS real con SIMULATOR; migración/restauración de copia ficticia 14→15 repetible. Benchmark: 31 combinaciones × cinco repeticiones, tiempo/memoria y HTTP separados; no capacidad productiva. [Expediente, intentos y límites](documentation/evidencias/entrega-final/algoritmos/correccion_comprobacion/20261101T042648Z/RESULTADOS.md). No se suman N1/N2 ni casos históricos. **CONTINUACIÓN PARCIAL POR DEPENDENCIA DECLARADA**: mecanismos técnicos comprobados; etapa sin cierre clínico/geográfico externo. Nueva comprobación independiente requerida.

Dependencias externas: protocolos y aprobadores clínicos institucionales reales, política oficial por producto/órgano, catálogo HLA institucional, fuente vial autorizada y GPS físico; no bloquean el registro/simulación técnica completados. Datos de consumo de prueba no acreditan utilidad clínica real. Pendientes separados: nueva comprobación independiente y autorización/comprobación productiva del incremento 0.4.3; no se reutiliza la publicación 0.4.1 como evidencia actual.

[Matriz correctiva](documentation/entrega-final/algoritmos/correccion/Matriz_cierre.md) · [Operación, contratos, configuración y rollback](documentation/entrega-final/algoritmos/correccion/Operacion_y_reproduccion.md) · [Algoritmos](documentation/markdowns/Algoritmos.md) · [Fuentes](documentation/markdowns/Reglas_y_fuentes_clinicas.md).

## Historial: prompt correctivo de etapa 02 — 31/10/2026

Por solicitud del usuario se creó [el encargo correctivo de reglas y algoritmos](stuff/prompts/correccion_comprobacion/02_corregir_reglas_clinicas_y_algoritmos.md), basado en la auditoría comunicada y en el prompt original. Cubre registro/aprobación de perfiles, HLA, asociaciones, vigencia, separación académica/clínica, obsolescencia de ambos sujetos, productos, ALG-01–05, geografía/Transporte, documentos y API/web. Exige reproducciones, oráculos, configuración operativa reforzada, navegador, migraciones, regresión y evidencia final. Criterio documental: cobertura explícita de las 21 etiquetas de auditoría y referencias locales verificables. Este cambio solo guarda instrucciones: no aplica correcciones, ejecuta pruebas funcionales ni cambia el veredicto de etapa 02 comunicado por el usuario: **NO APTA PARA CONTINUAR**.

## Historial: ampliación local de HLA y algoritmos — 31/10/2026

Compatibilidad y Priorización/Geografía **0.4.2**, esquema aditivo **14**, únicamente en código y entornos temporales de prueba. Se preservaron los cambios locales anteriores y las evaluaciones históricas; `RBC-1.0`, `ORGAN-1.0`, `LOGISTICS-1.0` y `COVERAGE-HK-1.0` mantienen su comportamiento. No se actualizó GCP ni la instalación habitual.

Implementado: HLA declarado por loci/alelos, ambigüedad, nomenclatura/resolución, emisión y documento privado de la misma muestra; estados no realizado/pendiente/indeterminado/informado/corregido. Perfiles académicos versionados con propósito, pruebas/loci exigidos y sustitución; clínica deshabilitada. La completitud no emite dictamen y una corrección conserva el antecedente. SQL protege los valores históricos y las nuevas ejecuciones.

Nuevas simulaciones persistidas: motivos de completitud/exclusión, política operativa con urgencia/espera, Dijkstra contrastado con oráculo, demanda SES con partición temporal/MAE frente a persistencia y estimación de sobrantes por lote, detección técnica de inconsistencias. API JSON/XML/XSD con JWT/Redis y alcance institucional; web con consulta, formulario de demanda y corrección HLA. Se distinguen GPS observado, recorrido recibido, ruta del grafo y ETA calculada desde su origen, con fuente, fecha, precisión y límites; no se presenta tráfico ni GPS físico como comprobados.

**Evidencia: 68 casos distintos aprobados según su última ejecución**, no una corrida única: regresión 63/64, ampliación final 12/12 y repetición correctiva de auditoría 1/1, con solapamientos reconciliados. Nueva instalación y ensayo v13→v14 con unidad/resultado ficticios conservados y migración repetible; formulario HTTP real con almacenes aislados; oráculos de rutas y matching; tiempo/memoria Python en tamaños 10/100/1.000 para seis ejecuciones algorítmicas. Ruff y diff sin errores. El fallo original de clasificación de evento y los intentos de preparación se conservan. [Resultados y límites](documentation/evidencias/entrega-final/algoritmos/RESULTADOS.md), [matriz](documentation/markdowns/Matriz_de_trazabilidad.md), [reglas y fuentes](documentation/markdowns/Reglas_y_fuentes_clinicas.md).

**Prompt 02 todavía incompleto.** Pendientes técnicos: mecanismo institucional de activación de perfiles aprobados; trazas individualizadas en una nueva versión de preselección operativa; conexión de las nuevas simulaciones con extracción autoritativa, rastreo y expedientes de Auditoría. El estimador existente `EMPIRICAL-USE-1` de Inventario permanece operativo; SES todavía usa entradas sintéticas declaradas. Pendientes externos: protocolos por producto/órgano, aprobación competente y catálogo HLA institucional, datos reales de consumo, grafo vial autorizado y GPS físico. Pendientes de verificación: vínculo documental nuevo con GCS real, navegador visual, monolito con APIs detenidas y despliegue. El ensayo de migración no fue sobre respaldo productivo restaurado.

Fuentes oficiales consultadas el 31/10: NOM-253-SSA1-2012 vigente según PLATIICA y norma sucesora NOM-253-SSA1-2025 publicada, con entrada prevista 10/04/2027; reglamento de trasplantes y nomenclatura HLA. Se documenta la transición y el alcance separado sangre/órganos, sin convertir una consulta normativa en aprobación profesional.

## Publicación correctiva y demostración GCP — 31/10/2026

Por autorización expresa del usuario se encendió y actualizó la VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`. Portal publicado en **https://34.18.186.116**, código **0.4.1 / esquema 13**. Se desplegaron las fuentes locales conservando todos los cambios previos, sin reemplazarlas por el `main` anterior de GitHub.

Respaldo coordinado y restauración real de PostgreSQL, MongoDB y Redis aprobados antes de migrar desde esquema 7; código, configuración, imágenes anteriores y metadatos GCS conservados. Las 75 tablas originales permanecen; ahora hay 108. Se corrigió compatibilidad del migrador con permisos y configuración Redis de la instalación antigua; prueba aislada repetible aprobada. Un fallo inicial se revirtió completo. Se corrigieron permisos de directorios nuevos en el empaquetado y se reconstruyeron imágenes antes de publicar la web.

**30 contenedores sanos**, incluidos 24 API/worker, web, gateway, tres almacenes y ClamAV. Doce API 0.4.1 y web respondieron por HTTPS con dependencias disponibles. Certificado renovado y timer habilitado. ClamAV privado real acepta contenido limpio y rechaza EICAR. GCS utiliza identidad adjunta a la VM; no se transfirieron ADC ni secretos del servidor. La demostración usó la copia local preexistente de credenciales y cuentas ficticias, con MFA y reautenticación activos, sin SMTP/push externos.

**Demostración visible completada, sin vídeo, capturas, HAR ni trazas:** 26 comprobaciones distintas consolidadas entre dos intentos; el segundo terminó aprobado con 24. Incluyó laboratorio corregido, dictamen obsoleto rechazado, reserva, traslado/custodia, WSS y reconexión, destino e historial, revocación por cambio de rol, reporte privado descargado desde GCS y auditoría responsive. El primer intento se detuvo por búsqueda UUID en un selector por nombre; se reanudó con el mismo recurso. Además, 24 respuestas de doce servicios, JSON y XML, validaron sus contratos JSON Schema y XSD/DTO. No se forzó expiración de sesión productiva ni se repitió la regresión completa de 370 casos.

[Evidencia del despliegue, incidencias y límites](documentation/evidencias/gcp/correccion-20261031/RESULTADOS.md). El encendido y publicación ya no están pendientes de autorización. **La aceptación independiente de la etapa permanece pendiente**, junto con mapas/clientes, GPS físico, HLA ampliado y aprobaciones institucionales. La VM única no ofrece alta disponibilidad de infraestructura.

## Corrección backend y arquitectura — 29/10/2026

Implementación local **0.4.1 / esquema 13**. F1–F11 corregidos y comprobados en aislamiento. Documentos/Reportes se extrajo como duodécimo servicio: 11 propietarios de dominio y Monitoreo; 24 réplicas API/worker, 29 contenedores permanentes con web/gateway/almacenes. Conserva puertos anteriores; Documentos usa 5112/6112. Contratos JSON/XML/XSD, SQL/ACL, gateway, workers, configuración local/Docker/GCP y módulos web actualizados. La web conserva autonomía con API detenidas.

**370 casos distintos aprobados, cero fallos pendientes y cero omitidos**, consolidados por identidad entre ejecuciones sobre los cambios finales. No se presenta como una única corrida completa. Navegador Chrome real: **27 comprobaciones** con Nginx/TLS/WSS, cookies Secure, MFA/reauth/perfil/constancia externa activos; flujo completo, rechazo de dictamen obsoleto, custodia/destino, rol revocado, sesión vencida, reporte privado GCS y auditoría responsive. GCS y ClamAV con firmas reales comprobados; errores e intentos previos conservados. Doce paquetes independientes y 14 imágenes construidas; liveness/OpenAPI y hashes de fuentes verificados por imagen; Documentos también ejecutó su entrypoint/API/worker reales contra almacenes temporales. La migración/restauración SQL y la entrada Compose/configuración/ACL se ensayaron; no se repitió la topología completa de 29 contenedores.

[Resultados, límites y evidencia](documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z/RESULTADOS.md) · [Matriz de 50 criterios](documentation/entrega-final/backend/correccion/Matriz_cierre.md) · [Arquitectura y decisiones](documentation/entrega-final/backend/correccion/Arquitectura_y_decisiones.md) · [Despliegue y rollback](documentation/entrega-final/backend/correccion/Despliegue_y_rollback.md).

**Estado histórico al 29/10: etapa NO APTA / aceptación productiva pendiente.** La publicación y su autorización se resolvieron el 31/10, según la sección anterior; la aceptación independiente permanece pendiente. En aquella revisión la VM se observó TERMINATED; navegador HTTPS productivo agotó espera, sin comprobar versión correctiva. No se encendió/desplegó/migró producción ni la instalación habitual. Falta autorizar encendido/coste, publicación/migración y cuentas/datos sintéticos; después comprobar HTTPS y versiones web/API/workers/esquema. También quedan límites de etapas posteriores: mapas/clientes, GPS físico, HLA clínico ampliado, aprobaciones institucionales y rendimiento sostenido. La autoevaluación requiere nueva comprobación independiente.

Se conservaron los cambios locales iniciales, el expediente histórico y los 3.123 archivos de partida; cero archivos iniciales ausentes, respaldo privado y manifiestos disponibles. Las secciones anteriores al 29 de octubre son historial, no sustituyen este estado correctivo.

## Prompt de corrección y revisión arquitectónica (28 de octubre)

Por solicitud del usuario se añadió el [encargo de corrección de etapa 01 y revisión de arquitectura](stuff/prompts/correccion_comprobacion/01_corregir_backend_y_arquitectura.md). Exige corregir F1–F11, completar evidencia pendiente BE-21 y criterios transversales, comparar agrupaciones/extracciones mediante dependencias y fronteras transaccionales, e implementar separaciones justificadas sin conservar once ni imponer veinticuatro como cuota. Incluye navegador real aislado y comprobación HTTPS de la versión correctiva en producción, con cuentas/datos sintéticos autorizados, evidencia y distinción de accesos o despliegue pendientes.

Criterios documentales: referencias existentes, cobertura explícita F1–F11 y BE/TRACK, análisis arquitectónico verificable, conservación de evidencia histórica y aceptación productiva separada de localhost. Verificación: rutas de referencia y cobertura del prompt comprobadas; diff sin errores de espacios. Este cambio solo crea instrucciones y registra su alcance: no corrige código, ejecuta pruebas funcionales, despliega ni cambia el veredicto **NO APTA PARA CONTINUAR** de la comprobación archivada.

## Comprobación independiente de etapa 01 y archivo del informe (28 de octubre)

**Veredicto vigente: NO APTA PARA CONTINUAR.** El [expediente de comprobación](stuff/comprobacion_etapas/01_backend_y_microservicios/README.md) conserva matrices BE-01 a BE-24 y TRACK-01 a TRACK-10, once hallazgos F1–F11, acciones de cierre, dependencias, comandos y ocho evidencias originales. La regresión reconciliada sobre las fuentes locales 0.4.0 terminó con **321 casos distintos aprobados y dos omitidos**, de 323 recolectados mediante varias ejecuciones. Las omisiones son GCS real y navegador. El manifiesto identifica el commit `8909baf` más cambios locales; las fuentes permanecieron intactas durante la auditoría.

Las pruebas existentes no cubren todas las variantes defectuosas: corrección de destino, vigencia de dictamen tras cambiar laboratorio, custodia opcional, autorización GPS durante replay, telemetría paralela, histórico fuera de ventana, eventos/inmutabilidad, gestión de roles y reportes/consultas. Tampoco se acreditó caída total de todas las réplicas de una API; la prueba detiene listeners WSS mientras otra API Transporte sigue activa. El detalle y los criterios de cierre están en el expediente. El pronóstico positivo de BE-21 requiere evidencia adicional.

Este registro y el expediente se añadieron **después de la auditoría, por solicitud de archivado del usuario**. No se aplicaron correcciones, migraciones ni nuevas pruebas funcionales al archivar. La sección siguiente describe la implementación y evidencia previas; no equivale a aceptación de la etapa. Se mantienen separados HLA detallado de etapa 02, clientes/mapas, despliegue, GPS físico y aprobaciones externas. Tras corregir corresponde una nueva comprobación con fuentes y resultados actualizados.

## Backend y microservicios de entrega final (28 de octubre)

Implementados el prompt 01 y el alcance backend del complemento 09. Código local **0.4.0**, API **v1**, esquema compartido **11**. Se conservan los **once servicios independientes** (diez de dominio y Monitoreo), sus puertos 5101–5111 y las autoridades existentes. La [matriz BE-01 a BE-24](documentation/entrega-final/backend/Matriz_BE.md) conserva 24 filas, detalla módulos/propietarios/datos/contratos/consumidores, justifica agrupaciones y señala las dependencias posteriores. No se cuentan réplicas como servicios.

Ampliaciones funcionales: dispositivos revocables, MFA TOTP, comprobantes de reautenticación ligados a operación/recurso y recuperación de contraseña con contacto verificado/token de un uso; responsables/servicios y acreditaciones; consentimiento versionado, agenda por sede, cupo concurrente y recordatorios; laboratorio con muestra, resultados y correcciones autorizadas; perfiles sintéticos de frío, lecturas, cuarentena y detección periódica de caducidad; linaje de componentes, autorización externa de órgano, consulta de trazabilidad y destino final separado de recepción. Alertas incorporan políticas versionadas, severidad, recordatorio/escalamiento/cierre y adaptadores SMTP/push con reintentos. Documentos reutilizan GCS y añaden categorías/versiones, análisis ClamD de generación exacta y descarga privada. Reportes generan jobs PDF/CSV/XLSX; analítica incorpora consumo/descarte/demanda y tiempos; sincronización permite observaciones no clínicas con resultado/cursor; conciliación externa conserva el recurso canónico.

**Rastreo:** receptor normalizado v1, puente JSON/NMEA RMC y simulador ejecutable metropolitano/regional; WSS real JSON y XML/XSD, asignación dispositivo/responsable/traslado con vigencia, reautorización, límites y revocación. PostgreSQL confirma historial/cursor antes del ACK; Redis mantiene caché temporal y permisos; MongoDB recibe proyección recuperable por outbox. Hay replay, deduplicación, orden de captura/recepción, estados de señal/antigüedad y spool local cifrado. Se ejecutaron CLI, caídas de almacenes, dos procesos gevent con TLS y caída de una/todas las réplicas de prueba. [Manual y matriz TRACK](documentation/entrega-final/backend/Rastreo.md).

**Datos conservados:** migraciones 008–011 aditivas, 33 tablas nuevas sobre las 74 existentes: **107 de dominio y una técnica web**. Vistas/credenciales por propietario y ACL Redis ampliadas sin rotar contraseñas ni borrar sesiones. Se probó migración repetible de copias estructurales v6/v7 con registros ficticios conservados, instalación nueva, restauración estructural idéntica y respaldo de 108 tablas. `scripts/upgrade.py` respalda antes de aplicar. **La base habitual, sus datos, la configuración privada y el despliegue GCP no fueron migrados ni modificados en esta intervención.**

**Criterios y evidencia:** [expediente reproducible](documentation/evidencias/entrega-final/backend/RESULTADOS.md), [modelos/estados](documentation/entrega-final/backend/Estados.md), [manual backend](documentation/entrega-final/backend/README.md). La regresión tuvo 280 aprobadas, un fallo de ejemplos MFA corregido y dos omisiones explícitas. La suite de cierre terminó **53/53 aprobadas**. Tras ampliar políticas, se corrigieron dos fallos JSON/XML de bloqueo de lectura sobre perfil inmutable; la reejecución de aceptación terminó **8/8 aprobadas**. Autonomía web con todas las API detenidas, contratos y salud: **8/8 aprobadas**. Los informes conservan intentos y correcciones; no se suman ejecuciones superpuestas ni se afirma una nueva regresión completa posterior. Todos los fallos funcionales observados tienen reejecución aprobada.

Contratos: **238 operaciones HTTP**, **104 pares de ejemplos de entrada JSON/XML** validados contra DTO/XSD y **13 pares de frames WSS**; estos conteos no equivalen a procesos ni a operaciones clínicas aprobadas. Prueba WSS acotada: dos emisores, dos suscriptores JSON/XML con lectura retrasada, 24 puntos y cursores íntegros; media de ACK 304.948 ms, p95 427.112 ms. No mide mapa, hardware ni capacidad sostenida. Ruff crítico, formato de 198 archivos y diff aprobados; corregido el formato pendiente de `ms_auditoria/findings.py`.

**Pendientes reales:** GPS físico y aceptación de su protocolo/conectividad/energía/precisión; mapas y clientes web/Android/PySide6 de las etapas 03/04/05, incluida interfaz MFA y permisos de captura; motor HLA clínico y ampliaciones del prompt 02; perfiles y políticas sanitarias aprobados; retención/eliminación institucional; SMTP/push productivos, ClamAV real con firmas y GCS autorizado para los nuevos flujos; despliegue nuevo, RTO/RPO y estrés sostenido. Las pruebas nuevas de adaptadores usan receptores locales; GCS usa doble de SDK. Se conservan como omisiones GCS real y recorrido opcional de navegador. No se presenta registro de acreditación como certificación, aceptación SMTP como lectura ni recepción como transfusión/trasplante.

Políticas operativas predeterminadas: MFA para ADMIN/MEDICAL/COORDINATOR, reautenticación en operaciones críticas, perfil de laboratorio y autorización externa de órgano obligatorios. El modo académico de pruebas mantiene compatibilidad de los flujos anteriores. Preparar enrolamiento/configuración y consumidores antes de activar el endurecimiento en una instalación existente; los clientes antiguos no incorporan automáticamente los campos/formularios nuevos. Las rutas v1 se conservan y los cambios de política están documentados.

## Verificación de main después del merge (27 de octubre)

Criterios: integración íntegra de `Microservicios`, sincronización con GitHub, ausencia de conflictos y regresión funcional local. El reflog confirma un merge fast-forward desde `44eeaf9` hasta `8909baf`; después de `git fetch origin`, `main`, `Microservicios` y `origin/main` apuntan a `8909baf`, con árbol idéntico `8a1f47998c774311fe9bb4a9de1e1ccb88aaf9fb`. La copia de trabajo estaba limpia, sin entradas de conflicto ni marcadores en código, scripts y despliegue.

La [regresión actual de main](documentation/evidencias/main-regresion.xml) terminó con **281 aprobadas, cero fallos, cero errores y dos omisiones**, de 283 casos, en **1175.92 s**. Usó PostgreSQL, MongoDB y Redis temporales aislados, sin modificar el entorno habitual. El primer intento fue interrumpido por restricciones del sandbox al abrir puertos; la ejecución completa autorizada terminó correctamente. Se omiten explícitamente GCS real por ausencia de bucket/ADC de prueba configurados y el recorrido opcional de navegador por no activar `REDHOUSE_BROWSER_TESTS=1`. La evidencia XML conserva resultados por caso y omite salidas capturadas y nombre del equipo.

Análisis estático crítico Ruff, configuración Docker Compose, sintaxis de diez scripts shell y `git diff --check` aprobados. **Pendiente previo al merge:** `ruff format --check apps/services apps/web/src/integration` falla únicamente en `apps/services/ms_auditoria/findings.py:213`; los otros 162 archivos cumplen. El mismo formato está en el commit anterior `e1d57f5` y ya se documentó el 22 de octubre; haría fallar la etapa de formato de CI. Esta revisión no modifica código funcional ni aplica esa corrección. No se repitieron despliegue Docker, recorridos de navegador, pruebas reales GCS ni validación del servidor GCP; tampoco se certifica aquí CI remoto. Los únicos cambios de esta revisión son este registro y su evidencia.

## Requisito de rastreo GPS por WebSockets y mapa de Nuevo León 27 de octubre

Por solicitud del usuario se añadió la [especificación transversal de rastreo GPS por WebSockets](stuff/prompts/entrega-final/09_rastreo_gps_websockets.md), integrada en contexto, ocho prompts, índice y guía de comprobación. Exige mapa interactivo actual de Nuevo León, recepción normalizada desde GPS/puente futuro, simulador ejecutable, canal WSS real, mensajes JSON para Android y XML/XSD para escritorio, permisos por traslado, persistencia, recuperación desde cursor, señal/antigüedad visibles y pruebas de privacidad/fallos. Las capas cartográficas deben documentar proveedor, procedencia/actualización y términos; no se confunde ruta, ubicación observada y ETA.

**Disponibilidad confirmada por el usuario:** el GPS físico todavía no está disponible y se incorporará posteriormente. No se eligió marca/protocolo ni proveedor cartográfico; su selección/verificación pertenece a la implementación. El software deberá probarse con simulador identificado sin presentar esa prueba como integración del equipo físico. La especificación cita documentación primaria de seguridad WSS y política cartográfica; la integración física queda como aceptación futura explícita.

Criterios de aceptación documental: diez requisitos TRACK-01 a TRACK-10, incorporación consistente a las ocho etapas y sus comprobaciones, conservación de formatos/roles/autonomía web y vínculos válidos. Verificación aprobada: doce Markdown, 29 enlaces relativos, diez requisitos TRACK, ocho pares de encargos/comprobaciones y las 24 responsabilidades BE conservadas; formato del diff sin errores. Este cambio modifica únicamente prompts/documentación; no implementa WebSockets, mapa ni receptor GPS, no despliega y no modifica datos o servicios.

Por solicitud posterior del usuario, el archivo de rastreo se numeró como `09_rastreo_gps_websockets.md` y se actualizaron sus referencias. Se lee desde el prompt 01 como complemento transversal; no se pospone hasta después de la entrega 08. Índice y guía explican cuándo usarlo e incluyen un par adicional de encargo/comprobación y expectativas para incorporar el rastreo a componentes ya implementados sin duplicarlo. Cambio exclusivamente documental, sin ejecutar el complemento.

## Guía de ejecución y comprobación por etapa 27 de octubre

Por solicitud del usuario se añadió una [guía Markdown de ejecución y comprobación](stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md), enlazada desde el índice de prompts. Contiene ocho prompts iniciales, ocho de auditoría, resultados esperados y señales de etapa incompleta por componente, además de un encargo para corregir los pendientes encontrados. Las comprobaciones distinguen evidencia del código actual, pruebas históricas aplicables, dependencias posteriores y aprobación clínica externa; no ejecutan correcciones ni modifican la instalación habitual.

Criterios de aceptación: ocho etapas enlazadas a sus requisitos completos, bloques copiables, formato de informe y veredictos explícitos, instrucciones sobre lectura del contexto 00 y uso de conversaciones por etapa. Verificación documental aprobada: ocho pares de prompts inicial/comprobación, ocho listas de expectativas, 17 bloques copiables y 18 enlaces relativos válidos entre los once Markdown de la carpeta; formato del diff sin errores. Sin ejecución de los encargos, pruebas de aplicación, cambios de código funcional, datos ni servicios. La creación de esta guía no modifica el estado de implementación de las etapas.

## Prompts de implementación para la entrega final 26 de octubre

Por solicitud del usuario se preparó una [guía con ocho prompts de ejecución](stuff/prompts/entrega-final/README.md) y contexto común: backend/microservicios, reglas clínicas/algoritmos, portal web, Android, escritorio, seguridad/infraestructura, integración/pruebas/rendimiento y documentación/entrega. Cubren las 24 responsabilidades funcionales propuestas por la retroalimentación, sin imponer 24 procesos ni duplicar capacidades existentes. Son instrucciones para trabajo futuro; no constituyen implementación ni cierre funcional.

Precisión posterior solicitada por el usuario: los prompts identifican expresamente la recomendación docente de una arquitectura objetivo de **24 microservicios**, sin convertirla en obligación de implementar exactamente 24 servicios independientes. Exigen matriz de evolución desde los once actuales, cobertura de cada una de las 24 responsabilidades, justificación de agrupaciones/extracciones y separación entre servicios, módulos y réplicas. Criterio de aceptación: coherencia entre guía, contexto, backend, pruebas y documentación, sin duplicar reglas ni propietarios para alcanzar una cifra. Este ajuste es únicamente documental.

**Decisiones confirmadas por el usuario en esta conversación:** Android se desarrollará con **Kotlin y Jetpack Compose**; escritorio con **PySide6 y Python**. Se conservan la base PostgreSQL compartida, web autónoma y consumo JSON/XML por los clientes. Los prompts incorporan HLA registrado/completitud/evaluación/dictamen separados, revisión profesional, trazabilidad hasta uso/destino, cadena de frío, archivos analizados, MFA, offline restringido y continuidad con RTO/RPO.

Criterios de aceptación del cambio documental: ocho encargos específicos con funciones, dependencias, pruebas y entregables; decisiones tecnológicas coherentes; cobertura de la retroalimentación y vínculos locales válidos. Verificación documental aprobada: diez archivos, nueve enlaces relativos, 24 responsabilidades backend, cinco algoritmos y 14 módulos de escritorio; `git diff --check` sin errores. No se ejecutaron pruebas de aplicación ni se modificaron código funcional, datos, contratos desplegados o servicios. La implementación de estos prompts permanece pendiente; aprobaciones clínicas y recursos externos se distinguirán de los criterios técnicos.

## Revisión del paquete en Downloads (22 de octubre)

Revisado `/Users/victorberlanga/Downloads/Red-House-Microservicios` por solicitud del usuario, sin modificar esa carpeta ni iniciar servicios. Al comenzar, sus **2770 archivos comparables eran idénticos por SHA-256** a la copia de trabajo; faltaban únicamente `AGENTS.md` y el `.env` privado de la web. La omisión del entorno privado es correcta. La carpeta contiene los Word/PDF finales y la plantilla histórica usada para regenerarlos.

Criterios: integridad respecto del origen, sintaxis/configuración válidas, contratos y algoritmos comprobables sin bases y ausencia de secretos bajo los patrones buscados. **19 pruebas aprobadas en 60.71 s**, con dependencias del venv existente del origen; **197 Python, 1222 JSON, diez shell y 16 archivos Office/ZIP** íntegros. Docker Compose y Ruff de errores críticos aprobados; búsqueda de claves privadas/credenciales bajo los patrones utilizados sin candidatos. De 745 enlaces locales, uno histórico apunta a `AGENTS.md` omitido. Ruff de formato falla en `apps/services/ms_auditoria/findings.py:213` y haría fallar ese paso de CI; 162 archivos ya tienen formato correcto. Ambos detalles siguen sin modificar.

[Detalle y límites](documentation/evidencias/revision-paquete/revision.json) · [JUnit](documentation/evidencias/revision-paquete/tests.xml). La revisión no ejecutó instalación, arranque, regresión completa ni pruebas reales contra PostgreSQL/MongoDB/Redis/GCS desde el paquete; no certifica esos recorridos. Los `.DS_Store` incluidos no afectan ejecución. Este registro se agregó después de comparar las dos carpetas.

## Cierre de presentación y video (22 de octubre)

El usuario confirma que el guion, la presentación, la participación del equipo y la grabación/publicación del video de YouTube ya están realizados. Se retiran de los pendientes vigentes. La sección 12 del reporte queda titulada «Limitaciones del alcance» y describe únicamente límites clínicos, de infraestructura y de validación de rendimiento. La confirmación del equipo es la fuente de este cierre; no se ha comprobado de forma independiente una URL del video.

Criterios de aceptación: ausencia de tareas de presentación o video pendientes en el reporte final, conservación de limitaciones técnicas justificadas, Word/PDF regenerados e índice coherente. La evidencia editorial se actualiza en `documentation/evidencias/segundo-parcial/formato-reporte-validacion.json`.

## Formato del reporte del segundo parcial (22 de octubre)

Por solicitud del usuario, el [reporte PDF](documentation/pdf/Reporte_tecnico_segundo_parcial.pdf) y su [Word editable](documentation/docx/Reporte_tecnico_segundo_parcial.docx) adoptan el diseño del reporte del primer parcial: portada original completa, Arial, jerarquía de títulos rojos/grises, márgenes carta, tablas con encabezado rojo y letras blancas, bordes negros y pie de página «Equipo 01». Se conserva literalmente la portada, incluida su fecha original. Una revisión editorial posterior elimina notas de actualización, comparaciones antes/después y narraciones de incidentes; conserva arquitectura, contratos, resultados de aceptación y límites de la edición 0.3.0. Las bitácoras de cierre y pruebas permanecen intactas como fuentes independientes, sin anexarse completas al reporte.

Criterios de aceptación y evidencia final: **40 páginas y 27 tablas**, portada idéntica píxel a píxel a 72 ppp y seis imágenes conservadas por hash, incluido el logo. Índice en la página 2 con **25 entradas**, números y enlaces PDF contrastados con los destinos. Una sola sección de referencias al final, desde la página 39: **siete fuentes web en APA 7**, con metadatos consultados en sus páginas oficiales, títulos en cursiva, sangría francesa y citas autor-fecha en el cuerpo; 53 rutas internas únicas comprobadas. Todos los textos de los párrafos/celdas exportados aparecen en el PDF y no hay palabras fuera de página. [Verificación estructurada](documentation/evidencias/segundo-parcial/formato-reporte-validacion.json). La primera revisión de formato tuvo 48 páginas y conservaba las bitácoras completas; queda sustituida por esta edición final.

`scripts/export_partial_report.py --pdf` reutiliza el Word histórico como plantilla, incorpora las fuentes editoriales del reporte, las fichas y `documentation/segundo-parcial/Referencias.md`, y pagina con LibreOffice hasta estabilizar el índice; dos pasadas comprobadas. El catálogo físico conserva su formato. Ruff y formato aprobados. Cambio documental, sin modificaciones funcionales ni nueva ejecución de pruebas de aplicación. La portada depende del Word histórico y los números del índice deben regenerarse después de editar contenido. LibreOffice necesitó ejecución fuera del sandbox por acceso al entorno gráfico de macOS; no se cambiaron servicios ni configuraciones de la aplicación.

## Capturas reales de Swagger público (21 de octubre)

Por solicitud del usuario se ejecutaron las **119 operaciones públicas** de los once microservicios desde Swagger UI contra HTTPS GCP. Se conservaron **130 capturas nativas de Chrome**: un éxito HTTP 2xx por operación y un rechazo 401 sin JWT por servicio. [Índice visual](documentation/evidencias/gcp/swagger-endpoints/index.html), [cobertura](documentation/evidencias/gcp/swagger-endpoints/coverage.json), [detalle y reproducción](documentation/evidencias/gcp/swagger-endpoints/README.md) y [ZIP](stuff/capturas_swagger.zip). Las 21 operaciones internas del inventario OpenAPI quedan excluidas por aclaración expresa del usuario; las capturas finales utilizan el acceso público sin túneles ni exposición de puertos internos.

Criterios de aceptación: imágenes de ejecuciones reales en Swagger, respuestas exitosas por método/ruta pública, una respuesta fallida adicional por servicio, organización por propietario y ausencia de imágenes generadas por IA. Credenciales, tokens y URLs firmadas se enmascaran; los ejemplos estáticos y Curl se ocultan para distinguir la respuesta ejecutada y proteger credenciales. Las imágenes provienen de Chrome automatizado, no de la sesión de navegador que el usuario tenía abierta.

La demostración creó registros ficticios propios, con folios `SW-mvivbj7j-*` y nombres Swagger: institución/cuentas, catálogos, donante, campaña/cita, donación, receptor/solicitudes, ruta, recursos, reservas, traslado y hallazgo. Se capturaron ediciones, cancelaciones y bajas sobre esos registros, más recepción interhospitalaria, custodia, archivo PNG privado en GCS y ciclo de hallazgo cerrado. Los datos ficticios y el objeto GCS se conservan; no se modificó código de aplicación ni se publicaron configuraciones o credenciales privadas. Los checkpoints están en `.local/swagger-capture`, fuera del expediente público.

[Verificación](documentation/evidencias/gcp/swagger-endpoints/validation.json): cobertura 119/119, once errores 401, 130 PNG íntegros y distintos con hashes, comprobación de patrones de secretos en artefactos de texto y ZIP íntegro de 22.335.076 bytes. Se inspeccionaron visualmente capturas de autorización, liberación e inicio de sesión. Sintaxis JavaScript y Ruff del generador del índice aprobados. Se conservan en el manifiesto los intentos fallidos de automatización y su reanudación; no se presentan como una nueva ejecución de la suite de regresión.

## Auditoría investigable y validación de formularios (21 de octubre)

Implementados los prompts `mejorar_auditoria.md` y `mejorar_validacion_formularios.md`. La bitácora incorpora acciones concretas, responsable/institución/recurso, ejecución y resultado, filtros combinables, detalle histórico y secuencia relacionada. Inicialmente muestra negocio, decisiones y seguridad; conserva sesiones, consultas y técnicos fuera de esa vista inicial. Contador, paginación y CSV comparten filtros; la exportación completa admite 5.000 eventos. Los datos históricos ausentes no se inventan.

Los hallazgos permiten documentar hechos, evidencia, prioridad y coordinador responsable, con atención y verificación separadas. El auditor regional registra y verifica; el coordinador solo atiende lo asignado. El cierre exige evidencia, motivo y confirmación humana. Eventos, vínculos e historial permanecen protegidos; ninguna transición modifica inventario o decisiones clínicas.

Los formularios muestran ayuda y límites del backend, resumen accesible con foco/enlaces y errores por campo después de enviar. Conservan valores, selecciones paginadas/múltiples, confirmaciones e idempotencia; omiten contraseñas y avisan de la reselección de archivos. Se distinguen causas de fechas, cupos, inventario, traslados y archivos. Errores JSON/XML conservan estructura compatible y agregan mensajes/límites seguros. El portal sigue funcionando por HTTP y como monolito con las API detenidas.

**Verificación local: 176 casos únicos aprobados según su última ejecución**, con intentos anteriores y correcciones conservados en los informes; no equivale a ejecutar toda la suite del repositorio. Chrome comprobó cuatro grupos de recorridos, teclado/foco, móvil, CSV y ciclo completo de hallazgos, sin errores JavaScript. Se comprobaron límites de 5.000/5.001 eventos, permisos, historial inmutable, migración repetible y conservación de un donante/evento en una copia v6. La nueva estructura se generó y restauró. [Resultados, capturas, cobertura y reproducción](documentation/evidencias/auditoria-formularios/RESULTADOS.md).

Criterios de aceptación cubiertos: investigación dentro de la región autorizada, filtros/exportación coherentes, seguimiento con permisos y evidencia, errores útiles sin escrituras parciales, corrección/reenvío y conservación de JWT/Redis/CSRF y contratos JSON/XML/XSD. [Guía funcional y técnica](documentation/markdowns/Auditoria_y_formularios.md).

**Desplegado en GCP por solicitud posterior del usuario:** [https://34.18.186.116](https://34.18.186.116). Migración global **6→7** y Auditoría **2→3**, con **74 tablas de dominio y 75 con sesiones del portal**. Se respaldaron PostgreSQL, roles, MongoDB, Redis y configuración; la restauración en contenedores aislados pasó y la migración se ensayó sobre esa copia antes de aplicarla. Las 70 tablas ajenas al control de versiones conservaron sus conteos y hashes durante la migración; MongoDB y credenciales también se conservaron. Se reconstruyeron las doce imágenes de aplicación y se comprobaron 2.389 archivos dentro de las 23 instancias de aplicación.

Verificación pública: **27 contenedores saludables, once readiness 200, 38 controles API aprobados y cuatro grupos de recorridos Chrome sin errores JavaScript**. Los cuatro errores de donantes reproducidos previamente ahora identifican el campo y la corrección, conservando valores y consentimiento. Un hallazgo ficticio completó alta, atención, verificación y cierre; quedan una fila, un vínculo y cuatro acciones como evidencia. Después de las pruebas, 60 tablas permanecieron idénticas y los **7.928 eventos de auditoría anteriores conservaron conteo y hash**. Los cambios restantes corresponden a versiones, sesiones, notificaciones y registros técnicos de la verificación. [Resultados públicos, respaldo, capturas y límites](documentation/evidencias/gcp/auditoria-formularios/RESULTADOS.md).

Incidencia resuelta durante la publicación: el empaquetado temporal asignó permisos 0700 a directorios de código y bloqueó readiness. Se corrigieron a 0755, se reconstruyeron las imágenes y se comprobó su contenido con el usuario ordinario del contenedor. Los datos no se restauraron encima de la instalación ni se reinicializaron. No se repitió carga/descarga GCS ni la suite completa de 176 casos en la VM. Los hallazgos usan evidencia textual/referencias; reasignación y adjuntos nuevos quedan fuera de este incremento.

## Revisión de mensajes de validación de donantes (21 de octubre)

Se reprodujo por HTTPS el envío del formulario publicado con campos obligatorios válidos y cuatro variantes opcionales inválidas: restricciones de tres caracteres, antecedentes de cuatro, referencia de consentimiento sin fecha y consentimiento futuro. Las cuatro devolvieron 422 y el mismo aviso «La solicitud no cumple el contrato», sin identificar el campo ni explicar cómo corregirlo. Se conservó el nombre capturado; no se marcaron campos con `aria-invalid`. [Resultados](documentation/evidencias/gcp/validacion-donantes.json). Criterio de esta revisión: reproducir el problema señalado, identificar su causa y conservar evidencia sin credenciales. No se modificó la aplicación ni se crearon donantes en estos cuatro envíos rechazados.

El modelo exige entre 6 y 1000 caracteres para restricciones/antecedentes, referencia y fecha de consentimiento juntas y fecha no futura. En el despliegue observado, el serializador reducía los errores a campo/código y un mensaje genérico; el cliente web descartaba los detalles y la plantilla mostraba únicamente el aviso superior. La corrección posterior, ya publicada y comprobada por HTTPS, está documentada en la sección anterior. Esta reproducción inicial utilizó solicitudes HTTP del formulario, sin automatizar un navegador.

## Icono de papelera y mensajes del portal (21 de octubre)

Por solicitud del usuario, la acción de retirar donantes aparece como **icono de papelera** en el listado y el expediente, con etiqueta accesible y ayuda «Retirar donante». La confirmación identifica nombre y folio y explica únicamente el resultado operativo: dejará de aparecer en la lista y sus citas pendientes se cancelarán. Se conserva la captura del motivo y la confirmación explícita.

Se simplificaron textos de reservas, propuestas de cobertura, traslados, archivos y fallos de consulta. Los perfiles operativos ya no reciben bloques de versiones, hashes, identificadores técnicos o claves internas del historial; administración y auditoría conservan los detalles de diagnóstico disponibles en sus vistas autorizadas. Las fechas, responsables, motivos, antecedentes, dictámenes y advertencias clínicas permanecen visibles. La preferencia vigente es explicar acciones y consecuencias al usuario, sin describir persistencia, algoritmos ni depuración dentro de los formularios habituales.

Criterios de aceptación: papelera reconocible y accesible con teclado, confirmación breve, conservación de avisos útiles y permisos, ausencia de detalles de implementación en las pantallas revisadas. Desplegado en **https://34.18.186.116** reconstruyendo solo `web`, con copia previa de fuentes e imagen. [Evidencia de presentación](documentation/evidencias/gcp/bajas-donantes/RESULTADOS.md#ajuste-posterior-de-presentación): **27 páginas y diez controles en Chrome**, siete cuentas de seis perfiles, cero errores JavaScript, diálogos o escrituras de negocio durante la revisión; **27 contenedores saludables y once readiness 200**. Archivos comprobados por hash dentro del contenedor; donantes, dictámenes, donaciones y citas idénticos por conteo/hash antes y después del despliegue. Sintaxis Python/Jinja/JavaScript y Ruff comprobados. No se cambiaron reglas de baja, API ni esquema; no se repitió la suite funcional anterior de 27 casos ni se iniciaron servicios locales.

## Baja de donantes y salida de formularios (21 de octubre)

Por solicitud del usuario, el perfil médico dispone de baja en el listado y el detalle de donantes de su institución (ahora mediante el icono de papelera descrito arriba). Sin dictámenes, donaciones, citas ni correcciones documentadas se elimina la fila del donante; con cualquiera de esos antecedentes se conserva como `INACTIVE`, se incrementa su versión y se cancelan las citas pendientes sin borrar sus filas. Ambos casos conservan motivo y auditoría. Los inactivos desaparecen de listados, selectores e indicadores, rechazan operaciones nuevas y mantienen el detalle autorizado para consulta histórica. No se elimina la cuenta de acceso ni se modifican donaciones anteriores. La operación JSON/XML está documentada en Swagger y usa JWT/Redis, rol, institución, versión, confirmación humana e idempotencia. No requiere migración del esquema existente.

Se retiró el manejador `beforeunload`: Volver, Cancelar y recargar descartan los cambios pendientes sin el aviso nativo del navegador. Se conservan la validación de formularios, CSRF y las confirmaciones de operaciones. Criterios de aceptación: baja física únicamente sin historia, conservación de relaciones en la baja lógica, exclusión de activos, rechazo entre instituciones/perfiles, repetición segura y ausencia del aviso al salir.

Desplegado en **https://34.18.186.116** actualizando el monolito y las dos réplicas de Donantes, con respaldo PostgreSQL previo y copia de código/imágenes anteriores. [Resultados y evidencia](documentation/evidencias/gcp/bajas-donantes/RESULTADOS.md): **27 pruebas aprobadas** en motores aislados dentro de GCP, incluidos JSON/XML, concurrencia, CSRF y ambos modos del portal; cinco controles en Chrome sin diálogos ni errores JavaScript. La consulta SQL confirmó una fila de prueba eliminada y otra inactiva con su dictamen conservado, cada una con auditoría central. Los 70 donantes, 64 dictámenes, 60 donaciones y 118 citas preexistentes conservan conteos y hashes. Las nuevas verificaciones agregan un expediente inactivo y un dictamen; esos registros permanecen fuera del listado activo.

Estado final: **27 contenedores saludables y once readiness 200**, archivos funcionales comprobados por hash en web y ambas réplicas. El entorno de pruebas temporal se retiró; no se iniciaron servicios locales. Respaldo validado por listado, sin una nueva prueba de restauración. No se implementó reactivación de expedientes ni se modificaron reglas clínicas.

## Normalización de etiquetas de los datos agregados (21 de octubre)

Por solicitud del usuario se retiró la etiqueta `DEMO` de los registros actuales creados en la carga anterior. Se normalizaron **743 registros**: 68 donantes, 120 receptores, 120 recursos, 60 campañas, 300 entradas de catálogos, 28 instituciones, 16 cuentas nuevas y 31 referencias de rutas. Los folios usan `RH26`; las cuentas adicionales ahora son `donor_1_01`–`donor_1_08` y `donor_2_01`–`donor_2_08`. Las cuentas originales y todas las contraseñas se conservaron. Se quitaron también frases repetitivas de presentación en los textos actuales del conjunto.

Criterios de aceptación: limpiar nombres, folios, títulos y textos de ese conjunto; conservar cantidades, UUID, relaciones, estados, fechas, versiones y hashes de contraseñas; verificar visibilidad y autenticación; evitar que el generador vuelva a introducir esas etiquetas. [Informe de la corrección](documentation/evidencias/gcp/datos-demo/RESULTADOS.md#normalización-posterior-de-etiquetas). La API bloquea correcciones amplias de expedientes con historia; se usó una transacción administrativa acotada a columnas de texto e IDs del checkpoint, con respaldo PostgreSQL previo, comprobación de concurrencia, hashes del resto de cada fila y auditoría nueva. No se modificaron dictámenes, evaluaciones históricas, cadenas ni respuestas guardadas de idempotencia.

Validación: cantidades iguales en las ocho tablas intervenidas, segunda revisión con cero cambios pendientes, 13 controles API (incluidos accesos con cuentas renombradas) y 34 páginas en Chrome sin etiquetas anteriores en sus listados ni errores JavaScript. Las 30 cadenas y proyecciones de traslado siguen válidas, con 27 contenedores saludables y once readiness 200. El generador y la verificación del portal quedaron adaptados a los nombres actuales. Los datos siguen siendo académicos; los documentos y eventos históricos conservan el contexto original y pueden contener la etiqueta anterior.

## Ampliación de datos de demostración en GCP (21 de octubre)

Por solicitud del usuario se cargaron datos ficticios con un objetivo de **al menos 30 registros por tabla operativa**, conservando los datos anteriores. [Resultados, capturas y excepciones](documentation/evidencias/gcp/datos-demo/RESULTADOS.md). Totales: 68 donantes, 60 campañas, 118 citas, 60 donaciones, 140 recursos, 138 receptores y solicitudes, 48 reservas y traslados, 33 archivos verificados, 30 instituciones y 30 usuarios. Cada hospital original dispone de 34 donantes, 30 campañas, 59 citas y 30 donaciones; `donor1` y `donor2` tienen expediente propio y 30 citas cada uno.

Criterios de aceptación: poblar los listados vacíos de ambas instituciones con relaciones válidas; conservar aislamiento y permisos; incluir estados variados, custodia, auditoría, notificaciones y archivos reales; alcanzar 30 filas en las tablas de negocio utilizadas; explicar las excepciones del esquema. Hay **38 de 72 tablas físicas con al menos 30 filas**; las restantes son 27 tablas heredadas sin uso y siete catálogos cerrados o tablas técnicas. No se rellenaron roles, migraciones, revocaciones ni tablas antiguas para simular actividad. Los catálogos de la interfaz contienen 300 entradas, 30 por categoría y hospital.

La carga se realizó por API autenticada desde la VM, con respaldo previo PostgreSQL/MongoDB, checkpoint privado y 1 755 operaciones completadas. Se agregaron 30 traslados: diez recibidos, diez en tránsito, cinco recolectados y cinco planeados, cada uno con una evidencia ficticia pequeña en GCS. Una desconexión de autenticación interrumpió la primera ejecución; se corrigieron los reintentos del cliente de carga y se reanudó sin duplicar. No cambió la lógica de los servicios ni el modo monolítico del portal.

Validación: **34 páginas en Chrome**, totales y paginación correctos para cuatro perfiles en ambos hospitales, cero errores JavaScript; 30 cadenas con hashes válidos y 30 proyecciones MongoDB coincidentes; 30 archivos verificados y dos descargas con hash correcto/acceso anónimo rechazado; 139 claves foráneas y cero restricciones sin validar; cero entregas pendientes mayores de 30 segundos. **27 contenedores saludables y once readiness 200**. Repetir la carga conservó las cantidades de 64 tablas y las mismas 1 755 operaciones. Código y comandos en la [guía GCP](deployment/gcp/README.md#datos-para-la-demostración).

Todo el procesamiento y la persistencia permanecen en GCP; el navegador local se usó solo como cliente y se cerró. Las cuentas originales se conservaron. Las fechas de campaña/caducidad corresponden a esta demostración y no se renuevan al repetir el script. Los respaldos en línea se generaron y el archivo PostgreSQL validó su listado; no se ensayó una restauración nueva ni se afirma una instantánea consistente entre los dos motores. La validación clínica y la operación productiva siguen pendientes.

## VM Google Compute Engine con acceso público (20 de octubre)

El sistema implementado está disponible en **https://34.18.186.116**. HTTP redirige a HTTPS. Monolito, once propietarios de API con dos réplicas, workers, PostgreSQL, MongoDB y Redis se ejecutan en la VM; los archivos privados residen en GCS. No requiere túneles ni procesos locales. La IP quedó reservada como `red-house-public`; Nginx publica únicamente TCP 80/443 y mantiene los puertos de diagnóstico en loopback. Las bases no tienen puertos publicados. [Guía y comandos](deployment/gcp/README.md).

La VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`, conserva las características comprobadas de `maquina01`: CentOS Stream 10, `e2-standard-2`, 2 vCPU, 8 GB RAM y disco `pd-standard` de 20 GB. La instancia original no se modificó. La copia inicial conservó **15 263 filas de 72 tablas SQL y 7 721 documentos MongoDB**, con conteos/hashes iguales, además de Redis y permisos. Las pruebas posteriores agregan datos ficticios; esas cifras no representan el conteo actual.

Criterios del acceso público: abrir todo el portal desde la IP sin dependencias locales; mantener JWT, CSRF y archivos privados; permitir las API y Swagger en `/services/<servicio>/`; conservar las bases privadas; renovar TLS automáticamente y detener los servicios locales. [Resultados](documentation/evidencias/gcp/RESULTADOS.md): **27 contenedores saludables**, sistema habilitado al arranque, cuatro controles HTTP aprobados (sangre por API, JSON/XML de once servicios, sangre por web y GCS), **20 páginas de siete perfiles** en Chrome, gráficas, cookies seguras, renovación/cierre de sesión, rechazo de cookie cerrada y ejecución Swagger 200. Once servicios pasaron readiness, documentación, OpenAPI y XSD por HTTPS; ocho puertos internos no resultaron accesibles desde el cliente externo.

Let's Encrypt emitió un certificado válido para la IP. Certbot 5.8.0 comprueba la renovación cada seis horas mediante systemd; la simulación de renovación y recarga de Nginx pasó. La web declara HTTPS explícitamente en Waitress y usa cookies `Secure`, `HttpOnly`, `SameSite=Lax`. OpenAPI/Swagger reconoce los prefijos públicos; las rutas internas están bloqueadas en la entrada externa. No se agregaron motores de datos ni se cambió la lógica clínica.

La VM queda encendida en `/opt/redhouse`. Docker Desktop, el contenedor auxiliar de compilación y PostgreSQL de Homebrew quedaron detenidos en el equipo local; tampoco hay portal, APIs ni túneles de Red House ejecutándose localmente. Código y datos locales se conservan como copia independiente. La verificación de navegador actúa únicamente como cliente externo y termina al finalizar.

GCS utiliza identidad adjunta de Compute Engine y firma IAM acotada, sin ADC personales ni claves privadas de cuenta de servicio. Las cuentas de aplicación conservan las del Docker copiado. Se mantiene la evidencia anterior del túnel como primera etapa, reemplazada por este acceso público. No se ensayó un reinicio completo de la VM ni se certifican redundancia entre hosts, carga sostenida u operación clínica/productiva. Las ediciones Word/PDF anteriores conservan su fecha y alcance.

## Guiones de demostración presencial y video (20 de octubre)

Se agregaron dos guiones en `stuff/demostracion_segundo_parcial/`, en [español](stuff/demostracion_segundo_parcial/guion_es.md) e [inglés](stuff/demostracion_segundo_parcial/guide_en.md), a partir de la consigna de presentación compartida por el usuario. Ambos cubren qué decir y qué enseñar en clase y en YouTube, sin portada ni nombres. El índice de `stuff` enlaza el nuevo material.

Criterios de aceptación: cubrir sistema web, microservicios, JSON/XML, Swagger, JWT, MongoDB, Redis, Docker y proceso de negocio con evidencias reales; conservar equivalencia entre idiomas; repartir responsabilidades entre todos los integrantes; indicar publicación pública u oculta. El recorrido propone un traslado preparado y un alta por Swagger seguida por identificador y correlación hasta el portal, PostgreSQL, MongoDB y logs Docker. Redis se demuestra mediante existencia/TTL de sesión antes y después del logout. Se distingue expresamente el portal monolítico del consumo HTTP de las API, la bitácora SQL del documento MongoDB y los indicadores de salud de una petición de negocio.

Validación documental: 28 enlaces locales comprobados entre los nuevos guiones y el índice; sintaxis correcta en diez bloques shell, seis fragmentos Python embebidos y dos plantillas JSON. Comandos iguales entre idiomas; cinco métodos/rutas contrastados con OpenAPI y cuatro nombres de servicios con Compose. Las consultas usan las vistas y permisos existentes y muestran campos seleccionados. No se ejecutaron los comandos de demostración ni se alteró GCP, datos o servicios locales. La participación, grabación y publicación fueron confirmadas como realizadas por el equipo el 22 de octubre; la validación documental del guion no verificó esas actividades.

## Material breve para la exposición (20 de octubre)

Se agregaron [cuatro guías de presentación](stuff/presentacion/README.md): nivel general y técnico, cada uno en español e inglés. Cada guía tiene ocho bloques, notas para hablar y demostración propuesta; duración orientativa de 8–10 o 12–15 minutos según el nivel. Se actualizaron el índice de `stuff`, la lectura inicial y el enlace al guion ampliado.

Criterios de aceptación: resumir avances y funcionamiento del parcial, mantener equivalencia entre idiomas, omitir portada e integrantes y distinguir lo implementado de lo pendiente. Las guías reflejan el portal autónomo, Docker, sesiones Redis/PostgreSQL, archivos privados y resultados fechados; las cantidades de distintas ejecuciones no se suman como casos únicos.

Validación documental: las cuatro guías conservan ocho bloques; 41 enlaces locales comprobados en los siete Markdown de presentación e índice, sin destinos ausentes. Se revisaron cifras, equivalencia de contenido y formato. Solo se modificó documentación; no se repitieron pruebas de aplicación ni se iniciaron servicios. Ensayo, exposición y grabación siguen a cargo del equipo.

## Sesiones del portal en Redis (20 de octubre)

Por solicitud del usuario se retiró el almacenamiento local de sesiones de la aplicación. Redis conserva tokens cifrados con TTL de hasta 86400 s y concesiones de renovación de 60 s. PostgreSQL conserva cierres y revocaciones pendientes en `web_runtime.session_revocations`. Credenciales separadas: ACL `web_sessions` limitada al prefijo del portal y rol `rh_web_sessions` limitado a la tabla técnica. El esquema del dominio mantiene 71 tablas; con la tabla técnica son 72 en la misma base.

Criterios: no importar ni montar el almacén anterior; preservar cookie opaca, cifrado, expiración, permisos, concurrencia y cierre seguro; actualizar instalaciones local/Docker sin modificar filas del dominio; conservar pendientes ante fallos y documentar la operación. [Resultados y reproducción](documentation/evidencias/sesiones-redis/RESULTADOS.md): **121 pruebas de regresión aprobadas** (798.33 s) y **9 pruebas finales del módulo** (82.26 s), incluido rechazo de revocaciones indescifrables. Las ocho pruebas originales del módulo se repiten; no se suman como casos únicos.

Migración aplicada a `.local/runtime` y `.local/compose`: 120 681 y 15 122 filas de dominio conservadas respectivamente; bootstrap Docker repetido sin rotar credenciales. No existían sesiones o revocaciones antiguas vigentes. Respaldos privados conservados. Docker comprobó login, renovación y logout por HTTP con todas las API detenidas, cifrado/TTL Redis y rechazo de cookie cerrada; sin volumen local de sesiones. Respaldo restaurado en motores nuevos: **15209 filas de 72 tablas** idénticas y permisos del portal conservados. Word/PDF y guías actualizados.

Límites: PostgreSQL es necesario para verificar las marcas de cierre; ante su caída, acceso protegido y cierre global responden 503, aunque se elimina la cookie del navegador. Si Redis cae, la marca se conserva y el worker completa la revocación al recuperarse. Si falta la clave de cifrado, el pendiente se conserva. Los usuarios deben iniciar sesión nuevamente. Los entornos intervenidos quedan detenidos con datos conservados. Las evidencias del cierre del 19 de octubre son antecedentes y no se atribuyen a esta revisión.

## Segundo parcial: cierre técnico documentado (19 de octubre)

Aplicación **0.3.0**. Se completó el incremento de `stuff/prompts/completar_segundo_parcial.md`, con los límites y pendientes externos indicados en la [matriz final](documentation/markdowns/Cierre_segundo_parcial.md). El entorno habitual `.local/runtime` y sus datos permanecen separados de las pruebas.

Implementado: backend web modular autónomo con reglas/JWT/Redis compartidos y workers propios; Dockerfiles por servicio/web, dos instancias por API incluyendo Identidad/Monitoreo, gateway DNS, volúmenes y secretos privados; proyección MongoDB versionada/reconstruible; flujo web GCS privado con validación de contenido/hash, estados y firmas; expediente HTTP con persistencia y capturas. El [informe integral](documentation/markdowns/Reporte_tecnico_segundo_parcial.md), once fichas, diagramas y catálogo físico de 71 tablas/145 índices se entregan en [Word/PDF](documentation/segundo-parcial/README.md), sin portada ni nombres.

Pruebas finales verificadas:

- [Regresión](documentation/evidencias/segundo-parcial/regresion-final.xml): **182 aprobadas**, cero fallos y omisiones, **2005.90 s**, con GCS real. Incluye 40 pruebas del lanzador. [Salud complementaria](documentation/evidencias/segundo-parcial/salud-complementaria.xml): una prueba posterior aprobada en **36.08 s**, informada por separado.
- [HTTP](documentation/evidencias/segundo-parcial/http/index.html): **284/284 métodos/rutas con éxito y captura**, 240 con error; 44 documentos fijos con justificación de no aplicabilidad. Todas las escrituras capturadas tienen comprobación de persistencia.
- [Docker](documentation/evidencias/segundo-parcial/docker-release/docker-results.json): **nueve controles aprobados**. Sangre por API; órganos y JSON/XML de once propietarios sin las réplicas A; sangre/órganos por web con las 22 API apagadas; gateway 502 sin autoridades; ambas imágenes de Inventario sustituidas con **100 consultas continuas 200** y altas persistidas; reinicio de los tres almacenes con SQL conservado y lecturas recuperadas.
- [Navegador](documentation/evidencias/segundo-parcial/browser/browser-results.json): **20 páginas de siete perfiles**, series Highcharts contrastadas con datos del servidor, ancho 390 sin desbordamiento, carga GCS verificada y Swagger ejecutado 200; sin errores JavaScript.
- [Respaldo/restauración](documentation/evidencias/segundo-parcial/backup-restore.json): **15 122 filas SQL de 71 tablas**, **7 632 documentos MongoDB**, cinco usuarios y cuatro roles documentales iguales por conteo/hash; clave Redis restaurada con TTL 3575 s. Motores nuevos, sin puertos publicados.
- [Clon limpio](documentation/evidencias/segundo-parcial/clean-clone.json): **ocho etapas aprobadas**, secretos y volúmenes nuevos, **27 contenedores saludables**, sangre por API y JSON/XML de once propietarios; bootstrap repetido. Instantánea Git temporal local, sin publicar commits. [630 archivos de aplicación/despliegue idénticos](documentation/evidencias/segundo-parcial/source-validation.json) y hashes de servicios iguales a los capturados en la regresión.

GCP autorizado: bucket privado `red-house-evidencias-sistemas-integracion-01`, Standard, `us-central1`, acceso uniforme y bloqueo público; cuenta `red-house-archivos`, permisos de objetos limitados al bucket y firma limitada a esa cuenta. ADC impersonada, sin claves privadas descargadas. [Prueba real](documentation/evidencias/segundo-parcial/gcs-real.json): carga, descarga/hash, rechazo público, archivo inválido, objeto ausente, expiración `400 ExpiredToken`, fallo 503 y recuperación 200. La evidencia ficticia del navegador permanece para demostración; la prueba automatizada limpió sus propios objetos.

Los [resultados](documentation/evidencias/segundo-parcial/RESULTADOS.md) conservan los incidentes y sus correcciones: esperas GCS, configuración Docker, conexiones SQL, sondeos de salud, datos de captura, autenticación durante restauración MongoDB, orden del agregado SQL y DNS del primer clon. La restauración final de las API incluyó cierre de tapa de 11:24:40 a 12:16:02; [registro](documentation/evidencias/segundo-parcial/docker-release/host-suspension.json). Esa duración de pared no mide RTO. No se ampliaron deadlines para aprobar.

[Revisión final de artefactos](documentation/evidencias/segundo-parcial/validacion-artefactos.json): informe de 36 páginas y catálogo físico de 41, Word íntegros, figuras/tablas inspeccionadas y sin texto fuera de página; 2214 enlaces locales válidos, 1204 archivos de evidencia revisados sin los patrones de credenciales buscados. Ruff y formato de 163 archivos, sintaxis JavaScript, `git diff --check` y sincronización CodeGraph aprobados.

Los Compose de demostración y prueba quedan **detenidos**, con datos y respaldos privados conservados. Inicio del principal: `python3 deployment/start.py`. La presentación y el video ya fueron realizados por el equipo, según su confirmación del 22 de octubre. Los límites funcionales y productivos figuran abajo y en la matriz; no se declara completa la entrega académica externa.

## Decisión de arquitectura (15 de octubre)

Por indicación del usuario se implementa una base PostgreSQL compartida por todos los servicios, como Bookstore. El [nuevo esquema compartido](data/database/schema.sql) deriva de main local `44eeaf90c445b4d9564c2f0ab2dd3167f0296418` y conserva sus 45 tablas, agregando 26 (71 en total) tras adaptar los contratos ejecutables. La propuesta inicial de 60 tablas quedó ampliada. [Cambios y correspondencia por servicio](documentation/markdowns/Esquema_compartido.md). La base inicial de main tiene 23 tablas y sus migraciones 002–004 agregan 22; las menciones previas a 46 no coinciden con ese SQL fijado.

**Implementado y aplicado al entorno local:** instalador, acceso SQL, colas y migrador utilizan `red_house`, con tablas físicas compartidas y vistas de permisos por servicio. La conversión verificó **111 tablas de origen y 118 428 filas sin diferencias** antes de publicar conexiones. Las once bases antiguas y sus respaldos privados permanecen conservados; las aplicaciones ya no las utilizan. Los SQL por servicio quedan como referencia del origen.

## Sistema actual

- `apps/web/`: portal Flask/Jinja2 con backend modular propio o consumo HTTP explícito. El backend histórico permanece retirado; no hay doble escritura ni cambio automático de backend tras un fallo.
- `apps/services/`: diez microservicios y Monitoreo, con contratos JSON/XML, JWT, Redis, PostgreSQL y MongoDB.
- PostgreSQL conserva una base operativa compartida, `red_house`, con 71 tablas y credenciales separadas por servicio. MongoDB conserva documentos/proyecciones; Redis mantiene sesiones y datos temporales. La web conserva sesiones técnicas cifradas y bloqueos en Redis; una tabla técnica adicional en `web_runtime` conserva cierres y revocaciones pendientes (72 tablas totales entre ambos esquemas).
- La carga regional es ficticia, pero sus operaciones y almacenamiento son reales. No se reinicializa al arrancar. Las reglas de compatibilidad y priorización no sustituyen la revisión médica.
- Android y escritorio están fuera de este parcial. Docker, bucket GCS y VM GCE con acceso por IP y HTTPS están implementados; operación productiva y redundancia continúan pendientes.

## Operación

Acceso habitual: **https://34.18.186.116**, con todo el procesamiento en GCP. Los comandos siguientes son para desarrollo local opcional y no son necesarios para usar la VM.

Desde la raíz: `bash install.sh`, `bash start.sh`, `bash components.sh estado` y `bash stop.sh`. Los BAT de Windows utilizan WSL/Ubuntu; no son un port nativo.

El entorno predeterminado es `.local/runtime/`, privado y excluido de Git. El origen del traslado y los respaldos previos a las migraciones se conservaron. No ejecutar simultáneamente copias del mismo entorno. Portal: http://127.0.0.1:5050.

[Instalación y diagnóstico](documentation/markdowns/Instalacion_y_operacion.md) · [Datos y migraciones](documentation/markdowns/Datos_y_persistencia.md) · [Mapa de bases](data/database/README.md).

## Reorganización y validación del 14 de octubre

- Directorios principales `apps/`, `data/`, `documentation/` y `stuff/` conservados como hermanos. Análisis, requisitos, planificación semestral y modelos lógicos conservados en sus carpetas por formato; guías vigentes consolidadas. Entregas de implementaciones anteriores, bitácora y resultados agrupados en `documentation/historial/`.
- Rutas web, lanzadores, requisitos, CI, generadores y contratos actualizados. Identificadores redundantes normalizados con migraciones, conservando auditoría y cadenas firmadas.
- 39 pruebas del lanzador aprobadas; Chrome recorrió 51 páginas sin errores registrados. Once servicios y portal respondieron HTTP 200 con los registros regionales conservados; 18 cadenas de custodia verificadas.
- Comparación de 111 tablas durante la migración: ninguna fila perdida ni cambio inesperado; usuarios e historiales preservados.
- Regresión final: **164 pruebas aprobadas**, cero fallos/errores/omisiones, 597.68 s. Ciclo de vida real del lanzador: **14 comprobaciones aprobadas**. Enlaces, contratos, sintaxis y formato verificados.

[Criterios, cambios, resultados y límites de esta entrega](documentation/historial/2026-10-14/REORGANIZACION.md). [Historial anterior](documentation/historial/README.md).

## Pendientes

- Validación clínica/normativa de reglas, HLA, elegibilidad, asignación, retención y acceso institucional.
- Agenda detallada por sede/hora, recuperación automatizada de contraseña, email/push y reportes regulatorios certificados.
- Android, escritorio XML, operación productiva y redundancia de infraestructura; la VM GCE académica ya ejecuta Docker con supervisión por instancia y HTTPS público.
- Carga sostenida, saturación, alta disponibilidad y ejecución de CI remoto. Windows/WSL y Ubuntu completos no están certificados por las pruebas de este Mac.

El diagrama físico compartido, catálogo de 71 tablas, informe integral y evidencias de archivos/continuidad pertenecen al incremento actual descrito al inicio. Los modelos 0FN–4FN y las once ediciones Word de planificación se conservan como referencias del semestre; el reporte del monolito anterior es un antecedente.

## Revisión documental del 14 de octubre

Se restituyeron once documentos de planificación con sus once Word y diez archivos de diseño/normalización. Avisos de alcance, índices y enlaces corregidos. Verificación: cero enlaces locales rotos, once Word íntegros y validador de normalización aprobado con 49 diagramas. El backlog conserva explícitamente su corte original; no es un tablero actualizado de ejecución.

## Revisión de la entrega del segundo parcial (14 de octubre)

Se contrastó el enunciado externo `entregaSegundoParcial.txt` (entrega 22/10) con el árbol de trabajo, contratos, código y evidencia. [Informe de cumplimiento y pendientes](documentation/markdowns/Revision_segundo_parcial.md). Docker es obligatorio para esta entrega, aunque la implementación actual y las guías lo mantienen pendiente. También faltan actualizaciones/pipelines funcionales MongoDB, expediente exhaustivo request/response, reporte integral vigente, evidencia de archivos reales y presentación/YouTube; se debe resolver la interpretación de independencia de la web. Android y escritorio están excluidos expresamente del parcial.

Criterio de aceptación de esta revisión: cubrir los apartados del enunciado, distinguir implementación de evidencia y proponer cierres verificables. Evidencia nueva: 19 pruebas unitarias/contratos/algoritmos aprobadas en 32.95 s, [JUnit](documentation/historial/2026-10-14/resultados/revision-segundo-parcial-unit.xml); once servicios respondieron 200 en readiness, Swagger y OpenAPI usando sus puertos reales, y la página pública del portal respondió 200. Los 164 casos de regresión son evidencia previa, no una nueva ejecución. Se contabilizaron 127 operaciones OpenAPI (107 API y 20 internas). No se cambió código funcional ni se declara terminado el parcial. Riesgo: la evidencia y las pruebas locales actuales no acreditan todavía el futuro despliegue Docker.

## Esquemas físicos PostgreSQL (15 de octubre)

Se añadieron once [esquemas SQL consolidados](data/database/README.md), uno por servicio, generados desde el esquema común y todas las migraciones mediante `scripts/export_schemas.py`. Incluyen 111 tablas y sus índices, restricciones, funciones y disparadores. Las migraciones continúan como fuente ejecutable; los SQL generados son referencias estructurales sin datos, propietarios, permisos ni registros de versiones.

Criterios de aceptación: generación aislada sin leer bases del entorno, restauración de cada SQL en una base vacía y comparación estructural, reproducibilidad y enlaces válidos. La generación y las once restauraciones pasaron con PostgreSQL 14.23; una segunda ejecución con `--check` volvió a restaurar las once bases y confirmó que todos los archivos coinciden. Se verificaron enlaces y análisis estático del generador. No se cambiaron las bases persistentes ni el código de la aplicación. Los diagramas físicos por servicio continúan pendientes; estos archivos no sustituyen el instalador ni sus permisos.

## Validación de la propuesta inicial del esquema compartido

Criterios: preservar tablas y columnas de main salvo dos renombres explícitos; aplicar la ampliación sin eliminar la estructura heredada; importar el SQL resultante en una base vacía; comprobar relaciones, historial y catálogos, y regenerar de forma reproducible. El generador `scripts/build_shared_schema.py` reconstruye el commit fijado más `shared/005_services.sql` en PostgreSQL temporal aislado, sin leer el entorno privado.

Generación y segunda ejecución `--check` aprobadas con SQL idéntico (PostgreSQL 14.23): 45 tablas heredadas, 15 nuevas, 60 restauradas; claves foráneas rechazan huérfanos, traslado exige exactamente una asignación, historial no admite modificaciones, caché incrementa su revisión y existen cinco versiones estructurales/siete perfiles habilitados. Durante la verificación se corrigió una referencia no calificada del disparador de caché y se normalizó la representación de casts de arrays varchar de PostgreSQL 14 al exportar/restaurar. No se cambiaron reglas clínicas ni se ejecutó la aplicación sobre esta base; esa integración sigue pendiente.

## Migración operativa a una base compartida (15 de octubre)

Criterios de aceptación: una sola base PostgreSQL para once conexiones de servicios; conservar contratos JSON/XML, permisos, datos, fechas, auditoría y hashes; integrar referencias entre módulos; instalar desde cero y migrar con respaldo sin sobrescribir el origen; mantener el estado de Monitoreo consultable desde MongoDB cuando falla PostgreSQL.

Implementación: se preservan las 45 tablas de main y se agregan 26, con 50 relaciones adicionales entre módulos. Los esquemas `access_*` contienen vistas y funciones, **cero tablas físicas**. Las colas técnicas comparten tablas con claves delimitadas por servicio. La coordinación entre APIs continúa por HTTP; este cambio no transforma esos flujos en una transacción SQL global. [Detalle de tablas, columnas y límites](documentation/markdowns/Esquema_compartido.md).

Validación del código: el generador restauró y reprodujo el SQL de 71 tablas con `--check`; Ruff y formato aprobados; 40 pruebas del lanzador aprobadas. La [regresión de 171 casos](documentation/historial/2026-10-15/resultados/base-compartida-regresion.xml) obtuvo **169 aprobados y dos fallos 503 en preparación de sesiones web**, en 1158.479 s. Los [dos casos repetidos aisladamente](documentation/historial/2026-10-15/resultados/base-compartida-sesiones.xml) pasaron en 75.04 s. No se presenta esa ejecución completa como libre de fallos: la investigación posterior identificó suspensión del equipo coincidente con ambos fallos (véase diagnóstico más abajo). Pasaron los cuatro flujos de sangre/órganos desde el portal, XML, permisos SQL, rechazo de huérfanos, aislamiento de colas, migración de datos y Monitoreo con PostgreSQL inaccesible. Los tokens del fixture se renuevan entre pruebas cuando vencen; la duración de tokens de producción no cambió.

Migración local: se detuvieron portal, APIs y workers; se exportaron once respaldos y configuraciones privados en `.local/runtime/backups/shared-20261015T174321780766Z/`; se creó `red_house`, se copiaron y compararon 111 tablas/118 428 filas y se publicaron las conexiones. El origen permanece íntegro para recuperación. Los IDs, fechas y contenidos comparados incluyen historiales y versiones; no se recalcularon hashes. El instalador crea directamente la base compartida y el lanzador rechaza entornos antiguos pendientes de convertir.

Verificación posterior: las once credenciales consultaron `current_database() = red_house`, las 71 tablas están en el esquema común y `access_*` no contiene tablas. Once servicios y portal respondieron HTTP 200; conteos funcionales conservados, 18 cadenas de custodia válidas y caché de inventario HIT. Auditoría creció por las consultas de verificación, como corresponde. [Informe sin secretos](documentation/historial/2026-10-15/resultados/base-compartida-entorno.json). Los once respaldos se restauraron en bases desechables y conservaron sus datos al repetir migraciones: [resultado](documentation/historial/2026-10-15/resultados/base-compartida-respaldos.json).

Los respaldos contienen secretos y datos; no se versionan. Volver al origen después de nuevas escrituras requiere reconciliar datos y restaurar también el código/configuración anteriores. La migración ejecutada convierte el entorno de microservicios anterior, no una base poblada arbitraria de main. Windows/WSL, Ubuntu, Docker y GCP no quedan certificados por esta validación local.

## Diagnóstico de los dos 503 (15 de octubre)

Se revisaron código, orden de pruebas, registros del sistema y auditoría del PostgreSQL temporal de la suite fallida. `pmset -g log` registró cierre de tapa (`Clamshell Sleep`) a las 11:24:26, seguido de despertares parciales y nuevas suspensiones. A las 11:27:22 comenzó una suspensión de 73 segundos; los logins de las dos pruebas fallidas están registrados a las **11:27:23.721634 y 11:27:42.763976**, respectivamente. El primero corresponde al login que devolvió 503; el segundo precede al GET de formulario que devolvió 503. La consulta histórica usó exclusivamente el clúster temporal de pruebas, iniciado en modo de lectura y detenido al terminar.

La ejecución sufrió suspensión del equipo, incompatible con probar disponibilidad mediante deadlines de 1 s de conexión y 8 s de lectura HTTP, además de deadlines de dependencias. La atribución anterior a carga era una hipótesis; ahora hay evidencia directa de suspensión coincidente con los fallos. **Límite:** el reporte original no conservó la excepción concreta de cada 503; no puede afirmarse si cada uno agotó HTTP, Redis o PostgreSQL. No se ha cambiado lógica, tiempos de espera ni reintentos para ocultar los fallos.

La nueva ejecución del módulo web completo terminó con **19 aprobados, cero fallos**, en 444.23 s. Registró 1 317 respuestas API, ninguna 5xx, y máximo observado de 1 512.914 ms. La única excepción de conexión web fue la esperada al detener Identidad deliberadamente. [JUnit](documentation/historial/2026-10-15/resultados/diagnostico-503-web.xml) · [Diagnóstico estructurado](documentation/historial/2026-10-15/resultados/diagnostico-503.json). No se declara repetida la suite completa de 171 casos.

Medidas: guía de pruebas actualizada para mantener la tapa abierta; `caffeinate -i` evita inactividad, pero no el cierre de tapa. CI actualizado para conservar logs INFO y captura de fallos JUnit junto al reporte. Criterios de aceptación: localizar los horarios reales, distinguir hechos de inferencias, repetir todo el módulo web y conservar contexto técnico útil para futuros fallos sin publicar secretos. La ejecución remota del CI permanece pendiente.

## Índice CodeGraph (15 de octubre)

Se inicializó CodeGraph 1.6.2 en la raíz mediante `codegraph init --yes .`. El índice local `.codegraph/` contiene 242 archivos, 2 222 nodos y 6 133 relaciones; `codegraph status` confirmó que está actualizado. Se verificó una consulta `codegraph explore 'redhouse.security authenticate'`, que devolvió código y relaciones entre autenticación, API y sesiones web. Criterio de aceptación: índice creado y consultable desde este repositorio. No se modificó lógica de negocio. Para consultar: `codegraph explore "símbolo o pregunta"`; para actualizar tras cambios: `codegraph sync`; para comprobar estado: `codegraph status`. El índice es una ayuda de navegación, no una prueba de funcionamiento ni cobertura exhaustiva del proyecto.

## Mantenimiento

Actualizar el documento vigente de cada tema. Registrar cambios y resultados por entrega en el historial, sin crear un documento nuevo por conversación. Conservar las migraciones y pruebas necesarias; retirar duplicados comprobados. No publicar secretos ni confundir un resultado histórico con una verificación actual.
