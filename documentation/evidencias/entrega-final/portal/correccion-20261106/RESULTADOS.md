# Corrección y aceptación local del portal 03

Encargo: `stuff/prompts/correccion_comprobacion/03_correccion_y_comprobacion.md`.
Inicio: 6 de noviembre de 2026, America/Monterrey. Los JSON del navegador registran UTC.
Base Git: `cbe3503b39a60b6b0a995f1284b2f5b1c3405cae`, más cambios locales existentes y
esta corrección. No se creó commit ni se desplegó. Se conservan los cambios previos de prompts móviles. El manifiesto inicial conserva
los hashes del árbol recibido; los manifiestos de cada recorrido identifican el
código probado, incluidas fuentes nuevas sin seguimiento Git.

**Resultado consolidado: 90 casos únicos aprobados, sin omisiones pendientes en la selección final.**
Cinco casos usan Chrome real. La etapa sigue **NO APTA** por las comprobaciones obligatorias
externas indicadas al final; aprobar estos casos no acredita GCS/antivirus ni gateway de destino.

## Entorno y alcance de la evidencia

PostgreSQL, Redis y MongoDB temporales aislados; cuentas y expedientes ficticios.
Chrome real mediante Playwright. TLS local, ruta WSS real del mismo origen,
simulador publicando a Transporte y cartografía en línea. SMTP temporal real,
sin mensajes a personas. MFA obligatorio y reautenticación habilitados. En modo
modular se detienen exclusivamente las doce API del fixture; el negocio opera
mediante sus propietarios autónomos. HTTP se ensaya por separado.

Los eventos se correlacionan por identificadores de traslado y posición. El tiempo
registrado es recepción backend–renderizado del mapa; no mide captura física.
Los puntos y coordenadas institucionales son sintéticos identificados. Las líneas
unen observaciones, sin estimación vial, tráfico, ETA ni posiciones extrapoladas.

TestBucket y el receptor TCP compatible con ClamD son dobles explícitos. Sus pruebas
acreditan controles y contratos locales, no GCS ni un motor antivirus real. No se
habilita descarga alternativa cuando almacenamiento o análisis no están disponibles.

## Correcciones y pruebas específicas

| Hallazgo | Reproducción y corrección | Prueba y evidencia | Límite |
|---|---|---|---|
| Reserva pendiente presentada como éxito | Respuesta perdida después de escritura; estados explícitos y consulta de clave/huella antes de reenviar | `test_pending_confirmation_web_recovers_same_command_without_false_success`, `test_web_lost_entire_write_response_queries_result_without_second_post` | No se cambia automáticamente de backend. |
| Publicación y configuración incompletas | Presentación/campañas publicadas por responsable, configuración institucional versionada y mínima proyección pública | `test_configuration_publication_privacy_versions_and_metrics`, `test_publication_without_api_listeners` | Coordenadas privadas excluidas de página pública. |
| Exportación limitada y síncrona | Worker paginado, contexto de filtros/ámbito/zona y autorización cifrada temporal; rechazo explícito por encima de 50.000 filas | `test_paginated_export_over_thousand_filters_context_and_foreign_denial`: 1.003 filas | No acredita descarga real desde GCS. |
| Autorización de trabajo diferido | Revalidación de sesión/rol/ámbito antes de extracción y descarga; autorización temporal eliminada al materializar | `test_export_worker_rechecks_revoked_session_before_extraction` | Revocación deja trabajo recuperable, sin archivo autorizado. |
| Formatos y fechas | PDF/CSV/XLSX con contexto, zonas Monterrey/Madrid, ausencia distinta de cero y protección de fórmulas | `test_report_formats_preserve_scope_timezone_unknown_and_formula` | Validación de bytes generados, separada de entrega privada real. |
| Propuesta regional inaccesible al coordinador | Identidad determina instituciones autorizadas; proyección logística sin instantáneas clínicas | `test_coordinator_reads_regional_proposal_without_clinical_authority` | No concede creación, dictamen ni lectura clínica. |
| Constancias de órgano sin formulario | Captura versionada de referencia externa y vigencia; registro no emite autorización oficial | `test_organ_authorization_form_keeps_history` | Referencias de ensayo sintéticas; validación clínica externa. |
| Documentos generales y conservación | Centro por sujeto, versiones, análisis, retención y bloqueo; pendiente no descarga; ámbito ajeno rechaza | `test_document_conservation_form_pending_and_foreign_download` | Preparación con TestBucket; falta ciclo con GCS/ClamAV reales. |
| Contratos ampliados | Exportación de OpenAPI/JSON/XML/XSD de propietarios afectados | Doce parametrizaciones de `test_shared_openapi_matches_export_and_preserves_representations` | Contratos no sustituyen recorrido de interfaz. |
| Contraste en panel y resumen de errores | Axe detectó texto tenue sobre fondo; color de párrafo ajustado al contexto | Intentos `final-http` y `final-http3` conservados | Repetidos HTTP y modular: sin violaciones axe detectadas en el alcance descrito abajo. |

La suite específica inicial `final-features/features.xml` contiene **22 casos aprobados**,
sin fallos ni omisiones, en 158,04 segundos. No se suman sus repeticiones previas.
El expediente [INTENTOS.md](INTENTOS.md) conserva los fallos encontrados durante
la corrección, incluidos errores del comprobador. Los JUnit saneados eliminan
trazas con tokens temporales y conservan casos/estados; el SHA-256 identifica cada
original temporal. `ejecuciones.json` permite contar identidades sin duplicar suites.

## Dependencias externas separadas

| Dependencia | Estado | Comprobación de cierre |
|---|---|---|
| Bucket GCS privado y ClamAV real | NO VERIFICADO; no disponibles/configurados para este ensayo | Entorno autorizado: carga, generación, análisis limpio/infectado, cuarentena ante caída, versión/retención y descarga con permiso vigente; repetir desde navegador. |
| Gateway WSS de destino | NO VERIFICADO en infraestructura 06 | Ensayar TLS, Upgrade, timeouts, caída total, reconexión y permisos a través del proxy real; WSGI TLS local no lo acredita. |
| SMTP institucional | NO VERIFICADO en 06 | Entrega institucional, secretos, límites y recuperación; SMTP local ya permite prueba técnica de un uso. |
| Teléfonos iOS/Android | Pendiente explícito de 04/07 | Captura física, permisos, segundo plano y publicación por backend; no exigir equipo GPS externo opcional. |
| Reglas, coordenadas y autorización profesionales | Validación externa pendiente | Registrar fuentes institucionales y aprobación autorizada. Datos sintéticos no constituyen certificación. |

Los antecedentes de 58 casos de auditoría y 63 identidades del incremento previo
se conservan fuera de este conteo. No prueban por sí mismos el árbol modificado.
Matriz de requisitos y acciones: [Matriz.md](../../../../entrega-final/portal/Matriz.md).

## Recorridos completos ejecutados

| Ejecución | Resultado JUnit | Comprobación interna | Evidencia |
|---|---|---|---|
| HTTP explícito | 1 caso aprobado, 831,44 s | 57 comprobaciones; siete perfiles y facultades de laboratorio | [JUnit](final-http7/browser-http.xml), [resultado Chrome](final-http7/browser/correcciones-operativas-http/resultados.json), [persistencia](final-http7/browser/correcciones-operativas-http/persistencia.json) |
| Modular con doce API detenidas | 1 caso aprobado, 768,77 s | 57 comprobaciones equivalentes; PostgreSQL/Redis/MongoDB permanecen disponibles | [JUnit](final-monolith3/browser-monolith.xml), [resultado Chrome](final-monolith3/browser/correcciones-operativas-monolith/resultados.json), [persistencia](final-monolith3/browser/correcciones-operativas-monolith/persistencia.json) |

Cada parámetro es un caso pytest; sus 57 pasos no son 57 casos independientes.
Chrome 157.0.8103.39, Node v22.13.0, macOS 15.7.9 x64, axe-core 4.11.0.
Python 3.12.6, Flask 3.1.3, Jinja2 3.1.6, pytest 9.1.1, ReportLab 4.5.1;
PostgreSQL 14.23, Redis servidor 8.10.2 y MongoDB 8.0.17. Los dos recorridos
registraron cero errores de consola. Los errores HTTP 401/403/409 documentados
corresponden a rechazos esperados: MFA ausente, token de recuperación consumido,
cupo ocupado, facultades insuficientes, dictamen obsoleto, destino incompatible,
recurso transferido y órgano sin revisión/constancia. Se guardan sin convertirlos
en errores inesperados ni ocultarlos. En modular hubo una recuperación de navegación
GET por `ERR_TOO_MANY_RETRIES`; nunca se reenvía automáticamente un POST.

En cada modo: una reserva sanguínea y una de órgano, dos registros aditivos de
destino sanguíneo (uso y corrección), órgano `TRANSPLANTED`, hallazgo `CLOSED` por
cuenta distinta de quien lo atendió. El JSON de persistencia identifica expedientes,
evaluaciones, comandos, traslados y hallazgo. El procesamiento y sus derivados se
consultan por contrato real después del formulario. Las revisiones de laboratorio usan cuentas MEDICAL; la ausencia de reautenticación
recibe 403 del servidor. Los rechazos por perfil/ámbito tienen casos propios en la regresión.

La reserva con respuesta perdida presenta pendiente, conserva clave y valores,
consulta el resultado y termina con un único efecto. No usa un backend alternativo.
La recepción del traslado se distingue del uso/destino posterior.

### Mapa y autorización continua

Ocho eventos publicados mediante WSS y confirmados por Transporte en cada modo.
El JavaScript del portal suscribe mediante ticket opaco de lectura. El publicador
sintético del comprobador introduce una credencial de usuario de prueba por stdin
y memoria de Playwright; no es una credencial entregada por las vistas ni se guarda
en evidencia. La afirmación de no exponer JWT se refiere al portal, no a ese emisor
instrumentado del ensayo.
Siete identidades distintas tienen medición recepción–mapa; el tercer evento aparece
dos veces durante recuperación. El séptimo se pierde deliberadamente al caducar
el cursor y no se inventa: `resync.required` fuerza instantánea, que permite mostrar
el octavo. No se afirma que los ocho puntos hayan sido dibujados.

HTTP: mediciones registradas de 265 a 1.567 ms; modular: 252 a 1.526 ms.
Incluyen replay/reconexión y no constituyen benchmark, p95, captura física ni SLA.
Fuente `SIMULATOR`, sin fijación, dato antiguo, corte sostenido, reconexión, cursor
caducado y cartografía en línea con atribución quedaron comprobados. Los cinco
casos de pérdida de acceso con mapa abierto fueron asignación, expiración, revocación,
logout y cambio real de rol. Las coordenadas/historia se retiran o la sesión navega
a login automáticamente. La reasignación se induce mediante SQL del fixture; el
cambio de rol usa Identidad. Se comprueba la guardia, sin atribuir a ese SQL una
interfaz administrativa de reasignación.

Capturas: [mapa móvil](final-http7/browser/correcciones-operativas-http/mapa-390.png),
[tableta](final-http7/browser/correcciones-operativas-http/mapa-768.png),
[escritorio](final-http7/browser/correcciones-operativas-http/mapa-1440.png).
Se revisó visualmente el encuadre estatal y los controles: Nuevo León, zoom/detalle,
atribución, fuente y marca sintética. La invalidación de tamaño de Leaflet antes de
centrar corrige el encuadre después de cambiar de ancho.

### Accesibilidad y gráficas

Cada recorrido incluye 51 inspecciones axe (17 vistas/visitas en 390/768/1440 px),
sin violaciones de las reglas WCAG 2 A/AA y 2.1 AA ejecutadas. Highcharts permanece
activo; sus valores se contrastan con el JSON del servidor y existe tabla equivalente.
Se contrastan 176 instancias de gráficas por modo; las visitas repetidas no representan indicadores nuevos. Se comprueban desbordamiento,
etiquetas, contraste, foco visible y navegación Tab. Esta evidencia no certifica
conformidad integral ni sustituye una evaluación con lectores de pantalla.


### Complemento final de agenda, teclado y exportación

[JUnit `final-agenda3`](final-agenda3/agenda-browser.xml): **2 casos aprobados en
205,61 s**, uno HTTP y otro modular con las API del fixture detenidas. Ocho
comprobaciones internas por caso. Ambos parámetros comparten la sesión de almacenes
aislados, con cuentas y citas distintas; cada recorrido principal B usa un entorno nuevo. La preparación de sede/campaña/reserva usa API
real con cuentas ficticias; asistencia, lectura, renovación y descarga se realizan
en Chrome. No se atribuye el alta inicial del fixture a un formulario de usuario.

- Renovación real: se aproxima únicamente el aviso de expiración web mediante una ruta del fixture; Identidad rota el token y conserva controles de expiración/revocación.
- Worker Donantes ejecutado dos veces: un recordatorio persistido y un evento, visible para el donante. `ATTENDED` persiste y la disponibilidad registra una asistencia.
- Donante fuerza `ATTEND` en el formulario y recibe 403 del servidor. Operador de otra institución recibe 403 por URL; su CSV no contiene la cita.
- La lista, el detalle y el diálogo muestran la sede y el horario exactos del propietario. El periodo de campaña se identifica aparte; registros sin horario no reciben fechas inventadas.
- Enter abre el diálogo, Tab/Shift+Tab permanecen dentro, Escape cierra y devuelve foco al enlace original. Errores conservan selección, enfocan resumen y el enlace enfoca el campo inválido.
- CSV de auditoría descargado por Chrome en UTC y Monterrey: filtro de un recordatorio, mismo recurso, conteo, ámbito y fecha convertida. Operador recibe 403 al intentar esa exportación.

Cada modo añade nueve inspecciones axe sin violaciones detectadas (diálogo, formulario
con errores y asistencia, a tres anchos). Se revisaron visualmente el diálogo móvil y
el detalle con horario/asistencia, además del mapa móvil, la reserva pendiente y el
formulario de custodia incompleto del recorrido principal. En este último se leen
los cuatro errores, el resumen enfocado y los valores conservados; la reserva muestra
«pendiente» y «Reanudar operación», sin mensaje de finalización confirmada.
[HTTP](final-agenda3/browser/agenda-http/resultados.json),
[modular](final-agenda3/browser/agenda-monolith/resultados.json),
[persistencia HTTP](final-agenda3/browser/agenda-http/persistencia.json),
[persistencia modular](final-agenda3/browser/agenda-monolith/persistencia.json),
[diálogo móvil](final-agenda3/browser/agenda-http/dialogo-390.png),
[asistencia](final-agenda3/browser/agenda-http/asistencia.png),
[CSV Monterrey](final-agenda3/browser/agenda-http/auditoria-America-Monterrey.csv),
[CSV UTC](final-agenda3/browser/agenda-http/auditoria-UTC.csv).

Los fallos previos del complemento quedan conservados: etiqueta de recordatorio
sin clasificar (corregida) y espera incorrecta del comprobador cuando la zona ya
estaba seleccionada (corregida). El CSV inmediato antes omitía contexto/conversión;
la evidencia de este complemento corresponde a su implementación corregida.

## Aplicabilidad de las fuentes y reproducción

Los recorridos principales congelaron fuentes antes/después y probaron el mismo
backend funcional. Después se corrigieron presentación de recordatorios/horarios y
CSV inmediato de auditoría; el complemento repite exactamente esas pantallas en
ambos modos. La regresión final valida sus relaciones con los recorridos existentes.
No se atribuye una captura previa a la nueva ficha de agenda.

La comparación de hashes identifica esos cinco archivos de aplicación:
`integration/appointments.py`, `presentation.py`, `routes/audit.py`,
`routes/common.py` y `routes/people.py`, además del comprobador nuevo y el wrapper.
Los propietarios clínicos, transporte/WSS, reservas y reportes diferidos no cambiaron
entre el recorrido completo y ese complemento. Después del complemento se precisó
únicamente el contexto del CSV genérico: perfil, institución de la cuenta, región y
autorización por recurso. La suite específica final comprueba ese cambio con datos
reales y rechazo ajeno. El CSV de auditoría descargado por Chrome no cambió. La última modificación del wrapper
solo permite configurar rutas de MongoDB/axe; sus valores predeterminados siguen
siendo los utilizados durante las pruebas.

Comandos desde la raíz, con los binarios locales declarados en la [guía de operación](../../../../entrega-final/portal/Operacion.md):

```sh
bash scripts/accept_portal.sh features /private/tmp/rh-portal-correction-20261106/final-features2
bash scripts/accept_portal.sh browser-http /private/tmp/rh-portal-correction-20261106/final-http7
bash scripts/accept_portal.sh browser-monolith /private/tmp/rh-portal-correction-20261106/final-monolith3
bash scripts/accept_portal.sh agenda-browser /private/tmp/rh-portal-correction-20261106/final-agenda3
bash scripts/accept_portal.sh regression /private/tmp/rh-portal-correction-20261106/final-regression
bash scripts/accept_portal.sh migration /private/tmp/rh-portal-correction-20261106/final-migration
bash scripts/accept_portal.sh browser-degraded /private/tmp/rh-portal-correction-20261106/final-degraded
```

Para repetir, usar directorios **nuevos**; los anteriores identifican esta ejecución.
No lanzar estas suites simultáneamente ni modificar fuentes durante la captura.
`caffeinate -i` conserva activo el equipo durante el proceso. No se amplían TTL de JWT,
permisos o reglas para superar pruebas; el plazo de arranque de almacenes del fixture
se configura a 90 s. Las pruebas generan/detienen únicamente sus procesos temporales.

Los JUnit publicados están saneados; sus identidades/estados/duración se conservan.
`ejecuciones.json` identifica el hash de cada JUnit original. Los logs completos
permanecen en el expediente temporal porque pueden contener formularios de prueba.
No se incluyen credenciales, tokens o archivos `.env` reales en el paquete.

## Acciones pendientes de cierre

1. **Documentos y reportes privados (WEB-12/15/19/21):** disponer de bucket privado aislado y ClamAV real autorizados. Repetir desde Chrome preparación, subida, generación analizada, verificación, versiones/retención/bloqueo y descarga; comprobar archivo infectado, dependencia caída y permiso revocado entre creación y descarga. Mantener cuarentena y rechazo mientras falte el análisis. Los controles locales con dobles ya se ensayan y no habilitan una descarga alternativa.
2. **Caída total con mapa abierto (WEB-24/TRACK-09):** repetir corte y restauración a través del gateway WSS de destino, con pérdida de ambos procesos y recuperación de cursor, verificando que el negocio modular siga operando. La prueba local de procesos y la desconexión del navegador son evidencias complementarias; no se presenta su combinación como un recorrido del proxy real.
3. **Infraestructura 06:** verificar SMTP institucional, configuración de TLS/Upgrade/timeouts y secretos en el entorno autorizado. El SMTP temporal y el gateway WSGI TLS local solo acreditan este entorno.
4. **Integración posterior 04/07 y aprobación externa:** captura física iOS/Android, permisos/segundo plano, datos institucionales reales y validación profesional de reglas/fuentes. GPS externo es opcional. No reabrir 01/02 por ampliar los clientes móviles.

El punto 4 es posterior o externo y no bloquea por sí solo el alcance web con simulador.
Los puntos 1 y 2 dejan criterios de aceptación del portal sin verificar.
La ausencia de infraestructura no se usa para aprobar archivos o acciones sin protección.
Tampoco convierte los ensayos sintéticos en autorización normativa o certificación clínica.

## Regresión y preparación histórica

La ejecución conjunta [final-regression](final-regression/regression.xml) terminó con
**61 aprobados, un fallo y una omisión en 915,66 s**. El fallo ocurría al preparar el
ensayo 13→actual: `schema.sql` ya contenía versión 17, pero el fixture fijaba el
migrador en 13. Su rechazo de una versión futura era correcto. No se modificó esa
guardia ni la migración del producto.

Se conserva ahora el SQL histórico de versión 13 del commit de partida en un fixture
comprimido reproducible. SHA-256 del SQL: `d3c8f8a74181c1ce79317a91f8762001e6cff4acaa5d0c66e87265d7aeca515d`.
La prueba restaura ese esquema, crea registros ficticios y ejecuta la migración real
13→17 dos veces, comprobando filas e historia. [Repetición dirigida](final-migration/migration.xml):
**un caso aprobado en 39,13 s**. El fallo original permanece visible; no se presenta
la ejecución conjunta como una suite sin fallos.

La advertencia de pytest sobre `record_property` y JUnit xunit2 no es un fallo de
contrato JSON/XML. Los resultados WSS del navegador conservan sus mediciones e IDs
en JSON propio. La omisión correspondía al navegador anterior, que se ejecuta aparte
con un directorio nuevo para no sobrescribir evidencia histórica.

## Suite específica sobre las fuentes finales

[final-features2/features.xml](final-features2/features.xml): **23 casos aprobados en
155,88 s**, sin fallos ni omisiones. Incluye nueve casos de correcciones, dos de
documentos y doce contratos de propietarios. Es la repetición aplicable al manifiesto
final; los 22 casos de `final-features` no se suman otra vez.

El caso nuevo `test_page_csv_distinguishes_account_institution_from_authorized_scope`
comprueba un recurso real exportado por coordinador, filtros/conteo idénticos y
contexto que distingue institución de la cuenta, región y autorización por recurso.
Otra institución obtiene un CSV sin ese recurso; donante recibe 403. El ajuste del
contexto no amplía permisos ni cambia las consultas de los propietarios.

## Cartografía degradada y cierre del conteo

[final-degraded/browser-degraded.xml](final-degraded/browser-degraded.xml): **un caso
aprobado en 103,56 s**, Highcharts habilitado. Se bloquean mosaicos, se publica una
posición por WSS real y se comprueba marcador, reconexión, aviso cartográfico y tres
anchos. El listado y el detalle privado del traslado persistido siguen accesibles;
un donante recibe 403. No hubo errores JavaScript capturados.
[Resultado](final-degraded/browser/cartografia-degradada/browser.json) y
[captura móvil](final-degraded/browser/cartografia-degradada/map-390.png).
Este comprobador usa TLS directo y sustituye el destino WSS en su fixture. Su
propósito es degradación cartográfica; **no** se usa como evidencia del gateway ni
de mosaicos en línea. Los recorridos principales sí verificaron WSS del mismo
origen sin sustitución y mosaicos del proveedor en línea.

| Ejecución seleccionada | Aprobados | Fallos | Omitidos | Revalidación |
|---|---:|---:|---:|---|
| `final-features2` | 23 | 0 | 0 | Correcciones, CSV regional, documentos y contratos finales. |
| `final-http7` | 1 | 0 | 0 | Recorrido completo HTTP. |
| `final-monolith3` | 1 | 0 | 0 | Recorrido completo con doce API detenidas. |
| `final-agenda3` | 2 | 0 | 0 | Agenda, renovación, teclado y CSV de auditoría en ambos modos. |
| `final-regression` | 61 | 1 | 1 | Fallo de preparación y omisión conservados; revalidados en las dos filas siguientes. |
| `final-migration` | 1 | 0 | 0 | Mismo caso de migración, con esquema 13 histórico real. |
| `final-degraded` | 1 | 0 | 0 | Mismo caso de navegador omitido, con evidencia nueva y cartografía caída. |

**90 identidades únicas aprobadas** al resolver el fallo y la omisión con sus
repeticiones dirigidas. No se declara que la suite conjunta haya pasado sin fallos.
[Conteo reproducible](conteo-final.json) y [todas las ejecuciones](ejecuciones.json).
Los 57 pasos de cada recorrido y las instancias de gráficas no son casos independientes.
Los antecedentes de 58/63 y los intentos previos quedan fuera de este total.

[Manifiesto final](sources-final.json), [comparación de aplicabilidad](aplicabilidad.json)
y manifiestos por ejecución: todas las fuentes permanecieron idénticas durante cada
prueba acreditada. El JSON detalla archivos cambiados después, incluyendo el fixture
histórico y la precisión del CSV. No se ocultan bajo un commit que todavía no existe.

## Integridad del expediente

La [verificación documental](verificacion-documental.json) confirma 1.234 fuentes
coincidentes con el manifiesto final, 19 archivos protegidos sin cambios y 151 enlaces
locales válidos antes de añadir estos dos enlaces de cierre. El conteo se reconstruyó
desde los JUnit y coincide exactamente con las 90 identidades publicadas. Ruff pasó
las comprobaciones críticas `E9,F821,F822,F823` en 52 archivos Python; Node verificó
la sintaxis de diez archivos JavaScript, Bash la del ejecutor y `git diff --check`
no encontró errores. No se detectaron JWT, claves privadas ni firmas GCS con los
patrones revisados en los artefactos textuales; esto no acredita una auditoría
completa de secretos. El [manifiesto de artefactos](artefactos-sha256.json) permite
comprobar la integridad del expediente, excluyéndose a sí mismo.

## Veredicto

**NO APTA PARA CONTINUAR.** Faltan las verificaciones obligatorias del ciclo privado
con GCS/ClamAV reales y la caída total/recuperación con mapa abierto por el gateway
de destino. Las acciones y criterios de cierre están enumerados arriba y en la matriz.
El alcance técnico local descrito sí tiene evidencia aplicable. Pueden avanzar las
tareas independientes o necesarias para resolver esas dependencias; no se aprueba
la etapa cerrada, infraestructura productiva ni una decisión clínica.
