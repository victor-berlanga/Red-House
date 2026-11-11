# Verificar integración seguridad rendimiento y usabilidad de la plataforma final

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Integra y verifica backend, web, móvil Android/iOS con Kotlin Multiplatform y Compose Multiplatform y escritorio PySide6. Corrige defectos encontrados hasta completar los criterios técnicos; no entregues únicamente un plan de pruebas.

## Continuidad obligatoria de las etapas 01 a 04

**Actualización del 11/11/2026.** Este bloque encarga resolver en etapas posteriores lo pendiente o insuficientemente definido de 01–04, conservando sus archivos y la implementación comprobada. No ordena reconstruir esas etapas ni declara cumplidos sus pendientes. Prevalece para la continuidad sobre instrucciones antiguas de aceptación incompatibles con decisiones posteriores del usuario, especialmente la exigencia de iOS Simulator. El resto de sus requisitos funcionales, de seguridad y de formatos sigue vigente.

Lee antes de corregir:

- [Matriz vigente de algoritmos y fuentes públicas](../../../documentation/entrega-final/algoritmos/correccion/Matriz_fuentes_publicas.md), incluida la distinción entre mecanismo académico y habilitación clínica.
- [Matriz del portal](../../../documentation/entrega-final/portal/Matriz.md) y [aceptación integrada para 06](../../../documentation/entrega-final/portal/Aceptacion_integrada_06.md).
- [Matriz móvil](../../../documentation/entrega-final/mobile/Matriz.md), [dependencias externas](../../../documentation/entrega-final/mobile/Dependencias_externas.md) y [procedimiento de iPhone físico](../../../documentation/entrega-final/mobile/Prueba_fisica_iPhone.md).
- [Instrucciones de diseño](../instrucciones_diseno_ui_ux.md), [corrección de calidad visual](../corregir_calidad_visual_web_movil.md) y [resultados y límites del último incremento visual](../../../documentation/evidencias/uiux/20261110-calidad/RESULTADOS.md). Usa esos encargos como reglas y evidencia de presentación, sin repetir automáticamente intervenciones ya realizadas.
- `../stuff/retroalimentacionSegundoParcial.txt`, `../stuff/entregaSegundoParcial.txt` y `../stuff/entregas.txt`, desde la raíz del repositorio, si están disponibles. Conserva su procedencia y distingue el alcance específico de cada entrega.

Al ejecutar 05, 06 o 07, abre o actualiza un único registro en `documentation/entrega-final/continuidad/Matriz.md`. Incluye ID CONT, requisito original, brecha actual, componente propietario, etapa responsable de corregir, dependencia, acción, criterio previo de aceptación, caso, versión/entorno y evidencia. Usa APROBADO, PARCIAL, FALLIDO o NO VERIFICADO; clasifica aparte defecto técnico, decisión de alcance y dependencia externa. Una brecha resuelta después de esta revisión se cierra con evidencia aplicable, sin repetir por rutina ni sumar pruebas históricas como nuevas.

05 continúa el escritorio y registra dependencias que lo afecten; 06 resuelve infraestructura, autorización y servicios compartidos; 07 completa correcciones de clientes y verifica el conjunto. La lectura de este bloque desde 05/06 no exige haber ejecutado 07 primero. Avanza en trabajo independiente, pero no declares aceptado un recorrido que depende de un criterio pendiente. 08 consume este registro y no sustituye una corrección por un cambio de redacción.

| ID | Pendiente o alcance por precisar | Responsable y criterio de aceptación |
| --- | --- | --- |
| CONT-01 | Integración pendiente de backend y algoritmos/HLA de 01/02 | 07, con los propietarios existentes y soporte de 06 para archivos: comprobar que registro, completitud, evaluación y dictamen se mantienen distintos; consultar fuentes, versiones, razones y exclusiones; comprobar obsolescencia tras corregir datos y vínculo documental HLA completo. Reutilizar oráculos y contratos vigentes. Los perfiles académicos no autorizan clínica ni generan reservas automáticamente. Registrar aprobaciones institucionales externas sin inventarlas ni invalidar por sí solas el alcance académico autorizado. |
| CONT-02 | Aceptación integral del portal transferida a 06 | 06 ejecuta I06-01…09 del plan enlazado; 07 incorpora resultados y regresión afectada. Cubrir documentos, conservación, reportes, autorización, autonomía web y WSS. Verificar esquema, imágenes y dependencias actuales antes del ensayo: las referencias históricas al esquema 17 o a ClamAV/VM ausentes no ordenan retroceder el entorno. Una publicación visual o fixture no acredita todos los roles privados. |
| CONT-03 | Autenticación, permisos y operaciones móviles aún no comprobadas | 07 en clientes y 06 en controles compartidos: MFA nativa para perfiles que lo requieren; reautenticación solo en acciones permitidas que la exigen; expiración, renovación, revocación y cambio de cuenta. Ejecutar reserva/reprogramación/cancelación de citas y competencia por último cupo desde las interfaces Android e iOS, con un único resultado persistido y errores recuperables. Mantener las facultades reales del perfil médico móvil; no añadir autorizaciones clínicas para fabricar una prueba. |
| CONT-04 | Calidad de experiencia incompleta en web y móvil | 07 corrige presentación por familia y todos los roles autorizados, con las reglas enlazadas y los criterios de usabilidad de este prompt. Sustituir captura manual ISO habitual por controles apropiados de fecha/hora, conservando zona y serialización; mostrar nombres de sede, no UUID como identificación principal. Obtener referencias/versiones de consentimiento desde la fuente autorizada cuando corresponda; no exigir que el donante conozca datos técnicos ni inventar valores. Registrar cualquier carencia de API concreta antes de resolverla. Verificar lectores de pantalla, foco, escala, teclado, regreso y estados de carga/error/vacío/conflicto/incertidumbre. |
| CONT-05 | Edición permitida del registro del donante sin definición suficiente | 07, propietario Donantes: contrastar requisito de crear/actualizar con contratos y permisos; definir campos personales autogestionables y campos reservados al personal competente. Implementar la edición autorizada con versión, persistencia, auditoría y consulta coherente; rechazar expediente ajeno, campos clínicos protegidos y versión obsoleta. Si una ambigüedad requiere decisión del responsable, solicitarla y mantener el criterio abierto. Una reducción de alcance requiere aceptación explícita registrada; actualizar consentimiento por sí solo no demuestra editar el registro. |
| CONT-06 | Posible truncamiento de listados móviles a los primeros 100 elementos | 07 comprueba y corrige listados afectados con más de 100 elementos autorizados o más del tamaño real de página: campañas, horarios e historiales pertinentes. Poder localizar y abrir un registro posterior a la primera página mediante filtros/paginación del servidor, conservando ámbito, filtros y retorno al listado. No descargar todo para filtrar ni usar filtrado local para simular autorización. Marcar aprobado solo con recorrido nativo y respuesta/persistencia correlacionadas. |
| CONT-07 | Push sin proveedor FCM/APNs y recepción acreditada | 06 completa/configura la integración del propietario Alertas y el proveedor autorizado; 07 verifica recepción y apertura en ambos clientes, consentimiento, token renovado, destinatario, deduplicación/reintento y revocación. Conservar `event_id` para entrega/idempotencia y `alert_id` para abrir el recurso reautorizado. Un 2xx del adaptador o una fila de outbox no acredita recepción. Separar implementación del proveedor, accesos externos y prueba física. |
| CONT-08 | Evidencia documental móvil y HLA sin ciclo integral actual acreditado | 06 prepara/verifica GCS y análisis reales; 07 completa captura/carga/análisis/consulta autorizada desde clientes y vínculo HLA. Comparar generación/hash, estados, privacidad y recuperación; rechazar descarga operativa de pendiente/infectado y acceso ajeno. ClamAV local aprobado no equivale a ciclo GCS aprobado. Utilizar el prefijo aislado autorizado y mantener pendiente lo que carezca de autorización de ensayo. |
| CONT-09 | Aceptación iOS y artefactos posteriores al primer arranque | 07 ejecuta la versión vigente en el iPhone autorizado, documentando modelo/SO, versión/hash, firma, instalación, arranque y recorridos; 08 conserva el artefacto y las instrucciones. Revalidar el arranque después de la corrección del plist, sin extrapolar desde un paquete anterior. La decisión vigente es probar físicamente y no descargar runtime Simulator. La compilación arm64 ni los resultados Android sustituyen ejecución iOS. Simulator solo se incorpora si cambia expresamente esa decisión. |
| CONT-10 | Capacidades del dispositivo, desconexión y seguimiento pendientes de prueba física | 07, con canal y permisos de 06: QR/cámara/GPS reales, permisos denegados/revocados, bloqueo, segundo plano, suspensión, cierre forzado y reconexión por plataforma. Reautorizar pendientes, conservar identidad e idempotencia, mostrar interrupción y hora real; ningún dato antiguo se presenta como actual ni una observación confirma custodia. Correlacionar móvil → Transporte → WSS → mapas. Separar emulador, ubicación inyectada, equipo físico y fallo del arnés; GPS externo continúa opcional. |

Las restricciones de los prompts de diseño rigen los cambios de presentación. Las correcciones funcionales anteriores se realizan bajo este encargo de integración, por su propietario y con pruebas proporcionales; no se ocultan dentro de un cambio visual. Conserva JSON móvil, XML/XSD escritorio, permisos, confirmaciones y reglas clínicas. No retires funciones ni agregues servicios genéricos para simplificar el cierre.

## Preparación y trazabilidad

Construye una matriz que cubra requisitos originales, responsabilidades BE-01 a BE-24, algoritmos ALG-01 a ALG-05, módulos DESK-01 a DESK-14 y funciones móviles/web. Vincula cada criterio con código, contrato, caso, entorno, resultado y evidencia. No cambies la expectativa después de observar un fallo para declararlo aprobado.

Comprueba la correspondencia desde los once servicios iniciales con los 24 microservicios recomendados por el profesor. Debe haber cobertura verificable para cada responsabilidad y justificación de las agrupaciones/separaciones, sin exigir exactamente 24 servicios independientes. Rechaza tanto funciones omitidas por agrupar como reglas o autoridades duplicadas para completar el número. Distingue servicios, módulos y réplicas en el inventario de prueba.

Prepara instituciones/regiones, usuarios de todos los perfiles, donantes/receptores, sangre/componentes y órganos sintéticos, resultados ABO/HLA, políticas de prueba, unidades, rutas, campañas, tareas y documentos en entornos aislados. Usa identidades/IDs persistentes para seguir un caso entre clientes. Las aprobaciones ficticias quedan identificadas como escenarios académicos, nunca como validación clínica real.

Define entornos de prueba, límites de carga, versión de fuentes, dependencias y limpieza exclusiva de datos propios. No reinicialices la instalación habitual ni uses pacientes reales.

## E2E-A Solicitud urgente de sangre hasta uso o destino final

1. Operador registra una unidad con procedencia, componente, grupo, fechas, ubicación y condiciones; laboratorio documenta muestras/resultados pertinentes.
2. Médico autorizado revisa y libera mediante confirmación/reautenticación conforme al perfil sintético.
3. Médico del destino crea receptor y solicitud urgente; el sistema valida información y muestra opciones/exclusiones.
4. Profesional revisa candidatos y registra dictamen. Coordinación consulta factores logísticos; una propuesta no crea reserva automáticamente.
5. Dos usuarios intentan reservar la misma unidad: una sola reserva válida y cobertura correcta; prueba también dos unidades para el último cupo solicitado.
6. Coordinador programa y asigna traslado. Transportista desde Android o iOS verifica QR, recoge, registra GPS/incidencia/evidencia y entrega.
7. Operador del destino recibe desde escritorio XML. Se comprueba secuencia de custodia, condiciones, estados y avisos.
8. Personal autorizado registra uso, devolución, descarte u otro destino permitido. Se distingue recepción de transfusión y se reconstruye la historia hasta el cierre.
9. Auditor consulta todos los hechos, decisiones, fuentes/versiones y responsables autorizados sin poder modificarlos.

Incluye una variante con prueba faltante, una con unidad vencida, una excursión térmica y una entrega tardía. Ninguna produce aprobación clínica automática.

## E2E-B Coordinación de órgano y autorización profesional

1. Institución autorizada registra órgano, procedencia, datos disponibles, tiempos críticos capturados y documentos.
2. Laboratorio registra tipificación HLA y datos/pruebas pertinentes con versiones. Comprueba estados incompleto, pendiente, corregido y revisado.
3. La coincidencia ABO con HLA faltante no se presenta como trasplantabilidad. La completitud no se presenta como dictamen.
4. Registra referencias de autorización y procedimiento oficial aplicable mediante el profesional habilitado; el motor solo apoya coordinación.
5. Prepara reserva/logística según la autorización, traslado desde Android o iOS, custodia, condiciones de conservación y recepción XML desde escritorio.
6. Documenta cierre autorizado, auditoría y notificaciones; muestra la consulta coherente en web.

Ejercita por separado tipos de órgano soportados y reglas/perfiles correspondientes. Usa un caso sin aprobación externa para demostrar que el sistema conserva el registro pero bloquea una conclusión clínica no autorizada.

## E2E-C Donación voluntaria desde Android o iOS

1. Donante inicia sesión y registra o consulta su expediente propio y consentimiento.
2. Busca campaña/sede/fecha/hora, agenda una cita y recibe confirmación y recordatorio autorizado.
3. Compite con otra cuenta por el último cupo; una sola obtiene confirmación. Prueba reprogramación/cancelación.
4. Institución verifica identidad y consentimiento; médico documenta evaluación humana. Un donante sin aprobación no avanza a etapas que la exigen.
5. Operador/escritorio documenta colecta, bolsa, muestras, procesamiento/fraccionamiento y componentes derivados.
6. Pruebas y liberación autorizadas permiten incorporación a inventario, conservando vínculo de origen.
7. Donante solo ve información autorizada y avisos propios. Auditor reconstruye la cadena, sin exponer resultados privados al donante por defecto.

## Coherencia entre productos

Al menos un caso completo debe originarse en móvil Android/iOS JSON, continuar por escritorio XML y observarse desde web con mismos IDs, estados, versiones y autorización. Verifica explícitamente que no hay conexiones cliente a PostgreSQL/MongoDB/Redis ni uso del portal como API privada.

Demuestra consumo real de al menos cuatro microservicios por cada plataforma móvil y cuatro por escritorio, con evidencia de método/ruta/formato y persistencia. Incluye login/refresh/MFA y errores XML en escritorio; no basta con consultas de lectura en XML.

## Seguridad contratos y concurrencia

- Ejecuta contratos JSON/XML/XSD de éxito, error, paginación, tipos, límites y negociación; XML XXE/DTD/tamaño y JSON ambiguo/no finito.
- Prueba JWT alterado/expirado, firma/algoritmo/audiencia/emisor incorrectos, refresh reutilizado, logout, sesión/dispositivo revocado, MFA y reautenticación reutilizada o sobre otro recurso.
- Prueba por rol e institución todos los accesos horizontales: URL/cuerpo/query, selectores, conteos, mapas, trabajos, documentos, descargas, exportaciones, etiquetas y sincronización. Verifica evento auditado y minimización.
- Concurrencia de reservas, cobertura, cupos, edición por versión, cancelación y recepción. Comprueba restricciones SQL/efectos persistidos, no solo códigos HTTP.
- Pérdida de respuesta después del commit, mismo Idempotency-Key/mismo cuerpo y distinto cuerpo, reanudación, eventos duplicados/fuera de orden y compensación pendiente.
- Integridad de auditoría/custodia con rechazo UPDATE/DELETE del rol operativo. Explica alcance y límites de hashes sin atribuirles verdad física ni invulnerabilidad ante administrador.
- Archivos limpios/invalidos/en cuarentena, antimalware caído, firma expirada, objeto/generación ausente, tamaño máximo/exceso y datos de otra institución. Protege evidencias y exportaciones.

## Offline dispositivos y fallos

En Android, iOS y escritorio prueba borrador permitido offline, cierre/reinicio de proceso y reconexión: una sola aplicación del comando, resultado confirmado, conflicto visible y sin acción crítica falsamente confirmada. Prueba cambio de cuenta, token revocado mientras estaba offline, reloj alterado y recurso modificado por otro cliente.

Verifica QR/códigos, cámara, GPS, permisos denegados, push/deep links y detención del seguimiento al terminar tarea/logout. Distingue hardware real, emulador y dobles de prueba.

Detén en entorno aislado una réplica, todas las réplicas de un servicio, worker, gateway y dependencias PostgreSQL/Redis/MongoDB/GCS según la matriz del prompt 06. Comprueba detección, mensaje, ausencia de corrupción y recuperación. Inyectar una respuesta inválida es una prueba diferente de apagar un servicio real; registra ambas con precisión.

Demuestra operación web completa con API detenidas y clientes funcionando con una réplica fuera. Redis caído debe rechazar protección; PostgreSQL caído no debe generar escrituras simuladas. Recupera eventos, documentos y avisos sin duplicados. Repite ensayo de respaldo/restauración y mide RTO/RPO con datos conocidos.

## Rastreo GPS WSS y mapa de Nuevo León

Verifica TRACK-01 a TRACK-10 de la [especificación de rastreo GPS por WebSockets](09_rastreo_gps_websockets.md). Ejecuta el simulador a través del ingreso/validación/persistencia de Transporte y conexiones WSS reales. Comprueba en mapas interactivos actuales de Nuevo León el mismo traslado/evento en web, móvil Android/iOS JSON y escritorio XML/XSD, sin recarga ni sustitución por polling. Incluye cobertura fuera del área metropolitana y datos fuera del estado sin descarte silencioso.

Prueba pérdida de señal, retrasos, duplicados/desorden, cursor vencido, reconstrucción de instantánea y reconexión al perder una réplica, así como caída de datos/autorización/cartografía. Rechaza dispositivos no asignados, suscripciones de otra institución, donantes y sesiones revocadas; comprueba la salida de quien pierde permiso durante un socket abierto. Mide emisores/suscriptores concurrentes, frecuencia, latencia captura/recepción/mapa, consumo y consumidores lentos. Identifica eventos simulados y registra el resultado de las pruebas físicas por plataforma; conserva pendientes únicamente las no comprobadas. El éxito del simulador solo acredita el software y su integración.

## Volumen rendimiento y Locust

Diseña un dataset sintético reproducible con semilla, relaciones y distribución regional, estados y fechas coherentes. Define cantidades y justificación antes de medir; como escala inicial evaluable considera decenas de miles de expedientes, cien mil recursos y al menos un millón de eventos, ajustando al dominio y capacidad documentados sin inflar la cifra con filas sin uso.

Mide inserción, búsqueda/listado paginado, índices/planes, lectura de disponibilidad, caché HIT/MISS, algoritmo, reserva/cupo concurrentes, backlog y reconstrucción documental. Compara con/sin caché Redis manteniendo **autenticación y permisos Redis activos**; no apagues seguridad para construir la comparación.

Configura Locust con varios perfiles y flujos reales, renovación de sesión, pausas y distribución documentadas: donante/citas, banco/inventario, médico/solicitudes/evaluación/reserva, coordinador/traslados y transportista/custodia. Identifica JSON/XML y verifica que las tareas utilizan respuestas previas y recursos propios.

Define previamente niveles graduales de usuarios concurrentes, duración de calentamiento/carga sostenida/estrés/recuperación y criterios de error/latencia justificados para el entorno académico. No impongas un SLA clínico inventado. Saturación solo en entorno aislado con límites y presupuesto autorizados.

Reporta usuarios, peticiones/s, transacciones de negocio/s cuando difieran, media, mediana, p95/p99, errores por clase, endpoints lentos, CPU/memoria/conexiones/IO, colas, fallos y recuperación. Conserva datos brutos, configuración y gráficas. Explica límites del equipo y del dataset. No compares mediciones realizadas con condiciones distintas como si fueran equivalentes.

## Usabilidad y evidencia real

Antes de medir, define tareas, entrada, resultado esperado, criterio de éxito y límites justificados de pasos/tiempo por perfil. Registra una referencia inicial comparable; cuenta por separado navegación, captura y confirmaciones obligatorias. Los límites son objetivos de diseño para esas tareas, no una cuota universal de clics ni motivo para retirar controles clínicos o de seguridad. Si no existe medición inicial, decláralo y no inventes una mejora porcentual.

Ejecuta tareas en navegador, Android, iOS y GUI PySide6, no solo HTTP. Para cada perfil mide éxito de tarea, errores, tiempo y observaciones; verifica teclado, foco, tamaño de pantalla y mensajes. Con personas del equipo identifica participante y tarea con consentimiento; si solo hubo automatización, informa ese alcance y no lo llames estudio con usuarios.

Incluye localizar una campaña y reservar/reprogramar cita; identificar tarea y siguiente acción de transporte; consultar/registrar inventario autorizado; revisar información clínica sin confundir propuesta con dictamen; y reconstruir una operación como auditor. Añade las tareas administrativas de los roles que las tengan. Revisa navegación y componentes equivalentes en todas las familias, no solamente donante. El móvil prioriza tareas pertinentes y revela detalles bajo demanda, preservando acceso a funciones autorizadas; no copia la navegación superior del portal. Las acciones de fila por iconos conservan nombre accesible, foco y ayuda; un icono ambiguo no se acepta por ocupar menos espacio.

Comprueba controles de fecha y selectores, nombres de instituciones, mensajes comprensibles, filas y formularios legibles, estados persistidos y recuperación. Ninguna tarea habitual debe exigir UUID, XML/JSON, versión técnica o formato ISO escrito a mano cuando pueda resolverse mediante selección autorizada. No inventes valores ni alteres contratos para ocultar el dato. Prueba TalkBack/VoiceOver y accesibilidad de escritorio en plataformas disponibles; registra por separado los pendientes reales y el problema de captura/composición de Avisos de transporte si aún persiste. Compilación, ausencia de desbordamiento o capturas de fixtures no sustituyen éxito de tarea ni permisos reales.

Capturas/grabaciones deben proceder de ejecuciones reales, con datos ficticios y secretos redactados. No generes pantallas de evidencia mediante IA ni uses ejemplos estáticos como respuesta ejecutada. Vincula los resultados de interfaz con persistencia, correlación e historia.

## Cierre

Entrega regresión actual identificada, resultados por componente, contratos, seguridad, fallos, rendimiento y usabilidad, con comandos reproducibles y defectos corregidos. Conserva intentos fallidos relevantes y repeticiones sin sumar casos como si fueran distintos.

Clasifica cada criterio como APROBADO, PARCIAL, FALLIDO o NO VERIFICADO, con causa y dependencia separadas. Entrega también CONT-01…CONT-10 con sus referencias a BE/ALG/WEB/MOV/DESK/TRACK y a los casos I06 que correspondan, sin duplicar conteos. Un flujo no ejecutado, un push sin recepción verificada o una plataforma solo compilada no se marcan aprobados. Actualiza documentación y `PROJECT_STATUS.md`; prepara la matriz final que usará el prompt 08. Los pendientes obligatorios conservan dueño y acción de cierre; su traslado entre etapas no constituye aceptación.

## Alcance móvil actualizado — 6 de noviembre de 2026

Ejecuta E2E-A/B/C por separado desde Android y desde iOS, conservando JSON y mismos contratos. Cada plataforma consume al menos cuatro servicios. Prueba captura real autorizada del teléfono y publicación WSS hasta los mapas web/escritorio, correlacionando evento y latencia. Separa simulación de ubicación de medición física, y prueba bloqueo/segundo plano/suspensión/cierre forzado y recuperación. El simulador sigue verificando fallos reproducibles; GPS externo es opcional.
