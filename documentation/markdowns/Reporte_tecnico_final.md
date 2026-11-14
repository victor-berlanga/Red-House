# Red House: documento técnico final

Proyecto 6: Red regional de bancos de sangre y donación de órganos. Equipo 01. Universidad de Monterrey, Integración de Aplicaciones Computacionales. **Corte documental: 14 de noviembre de 2026. Estado: consolidación parcial verificable; aceptación integral pendiente.** La fecha identifica este corte, no una presentación efectuada ni la fecha de aprobación del producto.

Este informe reúne la implementación y evidencia disponibles. Conserva el [reporte del segundo parcial](Reporte_tecnico_segundo_parcial.md) como antecedente del 22 de octubre. Los resultados pertenecen a sus versiones y entornos; no se suman ejecuciones superpuestas ni se presenta una consolidación documental como prueba nueva. El [estado vigente](../../PROJECT_STATUS.md) y la [matriz única de continuidad](../entrega-final/continuidad/Matriz.md) registran cambios posteriores y disposición por criterio.

## 1. Resumen ejecutivo

Red House coordina instituciones que registran donaciones, recursos, necesidades, evaluaciones profesionales, reservas y traslados. Su propósito es reducir demoras por información dispersa y conservar una historia verificable de responsabilidades y estados. La plataforma muestra alternativas y restricciones; la autorización clínica sigue correspondiendo a profesionales e instituciones competentes.

La solución actual comprende un portal Flask/Jinja2 con backend autónomo, **doce servicios independientes**, una aplicación Kotlin Multiplatform/Compose Multiplatform para Android/iOS y una consola PySide6/Python. Móvil intercambia contratos JSON; escritorio utiliza XML/XSD. Ambos acceden mediante HTTPS/WSS y carecen de conexiones directas a PostgreSQL, MongoDB o Redis. El portal incorpora sus propios módulos y workers fijados; puede operar con las API detenidas si conserva sus dependencias de datos y seguridad.

PostgreSQL concentra compromisos transaccionales en una base compartida con permisos por propietario. MongoDB conserva eventos y proyecciones documentales; Redis mantiene sesiones, revocaciones, permisos y datos temporales. Los archivos operativos utilizan almacenamiento privado del servidor. GCS es opcional para el producto y conserva evidencia académica independiente. La VM GCE dispone de Docker, HTTPS, monitoreo y dos réplicas por API; los treinta contenedores sanos corresponden a comprobaciones puntuales publicadas, no a disponibilidad continua garantizada.

Hay evidencia de procesos reales sobre datos ficticios: laboratorio y evaluación XML, reserva recuperable, custodia Android, archivos intercliente, HLA con invalidación de versiones, rechazo de accesos y recuperación WSS. La primera carga sostenida de seis perfiles registró 1.029 lecturas sin errores en 120,005 s. **Todavía falta correlacionar y aceptar los tres procesos finales completos, ampliar carga/estrés, cerrar continuidad y verificar plataformas pendientes.** Los ensayos parciales no acreditan aceptación académica total ni habilitación clínica.

## 2. Problema, objetivos, beneficios y alcance

Una solicitud urgente pierde tiempo cuando las instituciones desconocen existencias, responsables, vigencia de datos o condiciones de traslado. Las reservas simultáneas pueden comprometer el mismo recurso. Una recepción sin trazabilidad impide reconstruir procedencia, pruebas, autorizaciones y destino. El sistema organiza esa coordinación y hace visibles estados pendientes, conflictos y decisiones humanas.

El objetivo general es apoyar procesos regionales trazables con persistencia real, autorización institucional y recuperación explícita. Los objetivos específicos son registrar donantes/receptores; consultar disponibilidad; documentar pruebas y faltantes; comparar alternativas explicables; impedir duplicación de reservas; coordinar traslado/custodia; registrar uso o destino autorizado; y medir continuidad y rendimiento de los componentes.

Los beneficios esperados son menor búsqueda manual, mejor visibilidad de caducidades y reconstrucción de eventos. No se han medido reducción de mortalidad, tiempos clínicos o desperdicio real; el laboratorio no permite atribuir esos resultados sanitarios al software.

Se separan sangre y órganos por producto, estados, perfiles y procedimientos. Un filtro ABO no demuestra compatibilidad clínica. La plataforma no declara automáticamente aptitud, no autoriza transfusiones y no determina asignaciones oficiales de órganos. La validación profesional de reglas, competencias, conservación y privacidad permanece externa; esta condición no invalida los mecanismos académicos comprobados con datos sintéticos.

## 3. Actores, requisitos y trazabilidad

Los requisitos del semestre, casos e historias conservan sus documentos editables: [requisitos funcionales/no funcionales](Requerimientos_funcionales_y_no_funcionales.md), [historias](Historias_de_usuario.md), [casos de uso](Casos_de_uso.md), [reglas de negocio](Reglas_de_negocio.md) y [trazabilidad](Matriz_de_trazabilidad.md). Sus cortes de planificación no sustituyen la evidencia reciente.

El seguimiento actual utiliza las matrices existentes: [BE-01…BE-24 y TRACK](../entrega-final/backend/correccion/Matriz_cierre.md), [algoritmos y fuentes](../entrega-final/algoritmos/correccion/Matriz_fuentes_publicas.md), [portal](../entrega-final/portal/Matriz.md), [móvil](../entrega-final/mobile/Matriz.md), [escritorio](../evidencias/entrega-final/desktop/MATRIZ.md) y [CONT-01…CONT-10](../entrega-final/continuidad/Matriz.md). Estas fuentes contienen criterios, implementación, propietario, dependencias y evidencia; este informe no crea una matriz paralela de cumplimiento.

Los requisitos transversales incluyen autorización por recurso/institución, JWT y revocación Redis, contratos versionados, validación de archivos, auditoría, consistencia, recuperación, búsquedas/paginación, accesibilidad y medición de rendimiento. Una interfaz renderizada, un contrato generado o una compilación tienen alcances distintos; cada uno necesita su prueba aplicable antes de cerrar un criterio funcional.

| Perfil | Acción y recurso | Ámbito y límite |
| --- | --- | --- |
| Donante | Expediente personal permitido, consentimiento, campañas, citas y avisos | Solo información propia autorizada; no modifica evaluación clínica |
| Operador de banco | Inventario, muestras, captura de pruebas, preparación y recepción | Institución participante; captura no equivale a liberación médica |
| Médico | Solicitud, evaluación, dictamen y autorizaciones críticas habilitadas | Institución/recurso, versión vigente y reautenticación cuando corresponda |
| Coordinador regional | Disponibilidad agregada, rutas, programación y seguimiento | Región/asignación autorizadas; no obtiene expedientes clínicos generales |
| Transportista | Tarea asignada, QR, recolección, traslado, evidencia y entrega | Asignación y periodo vigentes; ubicación no confirma custodia |
| Administrador | Cuentas, instituciones, perfiles y configuración autorizada | Administración no concede acceso clínico indiscriminado |
| Auditor | Reconstrucción de eventos y revisión restringida | Consulta minimizada por ámbito; historia inmutable bajo credenciales runtime |

La [matriz de perfiles y permisos](Matriz_de_perfiles_y_permisos.md) y los contratos de cada propietario precisan acciones por producto. Los cinco perfiles de móvil conservan interfaces diferenciadas; administrador y auditor tienen otros canales autorizados. Los botones visibles no constituyen la autoridad: el servidor comprueba rol, acción, institución, región y relación con el recurso.

## 4. Arquitectura ejecutable y evolución

El navegador consume HTML/Jinja y formularios del portal. En modo `monolith`, `ApplicationKernel` ejecuta módulos de aplicación mediante WSGI sin listeners internos. Los mismos módulos versionados validan contratos, JWT/Redis, permisos y transacciones. El modo HTTP es una selección explícita; no existe cambio automático de backend después de una escritura incierta.

Las API no dependen de vistas, cookies o sesiones internas del portal. Cada propietario mantiene contratos, permisos, imagen y proceso/worker propios. Las copias compartidas de utilidades se fijan al empaquetar; actualizar un contenedor no modifica el código que otro proceso ya cargó. El acceso SQL del portal pertenece a su backend autorizado, nunca a la aplicación móvil o de escritorio.

El profesor recomendó una arquitectura objetivo de **24 responsabilidades**, sin exigir 24 procesos. El segundo parcial partió de once servicios; la extracción de Documentos/Reportes produjo doce. La [decisión de fronteras](../entrega-final/backend/correccion/Arquitectura_y_decisiones.md) conserva la correspondencia completa y sus alternativas. Una réplica o un módulo no se cuenta como otro microservicio.

| Propietario independiente / puerto interno | Responsabilidades BE agrupadas |
| --- | --- |
| Identidad y acceso / 5101 | 01 Identidad, 02 Instituciones |
| Donantes / 5102 | 03 Donantes, 13 Colecta, 22 Citas/campañas |
| Receptores / 5103 | 04 Receptores, 16 Necesidad/retención |
| Inventario / 5104 | 05 Inventario, 13 Fraccionamiento, 15 Frío, 16 Reserva, 17 Caducidad, 18 Trazabilidad, 21 Analítica de stock, 24 Mapeos |
| Compatibilidad / 5105 | 06 Evaluación, 14 Laboratorio |
| Priorización/Geografía / 5106 | 07 Propuestas y rutas |
| Transporte / 5107 | 08 Transporte, 21 Tiempos, 23 Sincronización operativa y rastreo |
| Custodia / 5108 | 09 Cadena de custodia |
| Alertas / 5109 | 10 Avisos y adaptadores |
| Auditoría / 5110 | 11 Auditoría y revisión de hallazgos |
| Monitoreo / 5111 | 12 Salud y disponibilidad |
| Documentos / 5112 | 19 Archivos/documentos, 20 Reportes |

Las responsabilidades compartidas tienen fronteras concretas: Donantes registra colecta e Inventario crea derivados; Receptores controla cupo e Inventario compromete la reserva; cada consulta analítica usa datos de su propietario. No hay una segunda autoridad sobre el mismo recurso.

Identidad agrupa instituciones porque activación institucional y acceso comparten invariantes. Laboratorio y Compatibilidad comparten versiones/completitud que deben revalidarse al reservar. Frío, caducidad y reserva pertenecen a Inventario porque compiten por la misma unidad. Transporte reúne asignación, posición y comandos recuperables para evitar una autorización GPS desactualizada. Documentos se extrajo para separar renderizado, permisos de objetos y fallos de almacenamiento/antivirus del worker de traslado. Cada agrupación tiene costes de despliegue/escala compartidos, documentados; no se afirma que esta distribución sea óptima para toda carga futura.

Los diagramas de [fronteras y dependencias](../entrega-final/backend/correccion/Arquitectura_y_decisiones.md), [rastreo/secuencia](../entrega-final/backend/Rastreo.md), [almacenamiento autónomo](../entrega-final/continuidad/Rutas_almacenamiento_autonomas.md) y [despliegue](../../deployment/gcp/README.md) son fuentes editables. Las figuras del [segundo parcial](../segundo-parcial/README.md) se conservan como diagramas fechados; sus once propietarios/GCS principal no describen el corte ampliado. La exportación visual final de diagramas y su revisión editorial continúan pendientes.

## 5. Procesos de negocio e integración entre productos

Los siguientes tres procesos describen el comportamiento requerido y los mecanismos existentes. La secuencia narrativa no acredita una ejecución final integral. El [guion de demostración](../entrega-final/continuidad/Demostracion_final.md) ordena ensayos comprobados y conserva esa separación.

### 5.1 Solicitud y suministro de sangre

1. Un médico registra receptor/solicitud institucional con componente y necesidad. Receptores valida y persiste versión/estado; emite eventos durables para auditoría y avisos.
2. Compatibilidad consulta inventario y laboratorio autorizados, registra faltantes, versiones, rutas y explicaciones. Un candidato técnico permanece pendiente de dictamen profesional.
3. El médico revisa y confirma el dictamen. Priorización ofrece comparación operativa; la propuesta no crea reservas.
4. Inventario registra operación idempotente, solicita retención a Receptores, bloquea recurso y revalida versiones/estado. Restricciones impiden doble reserva y sobrecobertura.
5. Coordinación programa el traslado sobre reserva confirmada. Origen prepara; transportista escanea y registra recolección, tránsito y entrega. Destino acepta con su perfil y comprobaciones.
6. Inventario/solicitud reciben eventos por secuencia. El uso o destino posterior requiere registro y autorización propios; la recepción no representa transfusión realizada. Auditoría, Custodia y Alertas conservan el contexto minimizado.

Ante timeout se conserva resultado incierto y se consulta la operación antes de repetir con la misma clave/cuerpo. Un conflicto local puede compensar una retención; una recolección física no se deshace mediante una liberación automática. Una corrección de laboratorio invalida la evaluación vigente sin reescribir la histórica.

Hay evidencia Qt/XML de [evaluación](../evidencias/entrega-final/desktop/iteracion-evaluacion/RESULTADOS.md), [reserva recuperable](../evidencias/entrega-final/desktop/iteracion-reserva/RESULTADOS.md), [laboratorio](../evidencias/entrega-final/desktop/iteracion-laboratorio/RESULTADOS.md) y [custodia Android](../evidencias/entrega-final/mobile/RESULTADOS.md). Falta acreditar toda esta secuencia correlacionada hasta uso/destino entre productos con notificación y visualización final.

### 5.2 Coordinación de órgano

1. Personal institucional registra recurso y receptor/solicitud con la información autorizada. Se separan producto, órgano y procedimiento de sangre.
2. Laboratorio conserva muestras, resultados, HLA, fuentes/perfiles y estados de revisión. Faltantes o ambigüedad no se interpretan como resultados favorables.
3. El sistema conserva evaluación y explicaciones. La autoridad profesional y el procedimiento oficial determinan las autorizaciones; Red House registra el soporte y no asigna automáticamente un receptor.
4. Solo tras las autorizaciones aplicables se coordinan reserva y logística. Transporte/Custodia registran responsables, versiones, incidencias, tiempos y evidencias.
5. La institución receptora acepta y registra el cierre/destino permitido. La historia mantiene referencias y correcciones; una coordenada no confirma entrega ni trasplante.

La evidencia [HLA JSON/XML](../evidencias/entrega-final/cont01-hla-20261113/RESULTADOS.md) verifica faltantes, revisión, nueva evaluación e invalidación tras corrección. El [documento HLA con ClamD real](../evidencias/entrega-final/cont01-documentos-20261113/RESULTADOS.md) verifica asociación por muestra/resultado. Son ensayos separados; el E2E de órganos con todos los clientes y decisiones autorizadas sigue pendiente. Su eventual aprobación académica tampoco habilitará la operación clínica real.

### 5.3 Donación voluntaria y procesamiento

1. Donante consulta feed público/campañas y agenda desde móvil. El servidor autoriza cuenta/cupo y confirma la cita persistida; el cliente no confirma localmente.
2. La institución verifica identidad, consentimiento y evaluación humana. El donante modifica únicamente campos personales habilitados.
3. Personal autorizado registra colecta y procedencia de la unidad. Operador documenta procesamiento, muestra y resultados; el médico realiza las acciones profesionales que procedan.
4. Inventario registra componentes/derivados y su linaje, cuarentena/liberación o destino. Cambios conservan versiones y auditoría.
5. Avisos y visualizaciones consultan el mismo resultado autorizado desde web, JSON móvil y XML escritorio. El cierre por uso/destino conserva su hecho propio.

Los recorridos Android de agenda y edición tienen evidencia en [móvil](../evidencias/entrega-final/mobile/RESULTADOS.md), [próxima cita](../evidencias/entrega-final/mobile/next-appointment-20261113/RESULTADOS.md) y [edición personal](../evidencias/entrega-final/edicion-personal-20261113/RESULTADOS.md). El laboratorio/escritorio aporta captura posterior. Falta el recorrido final correlacionado donación→procesamiento→inventario con consulta de los demás productos, auditoría y aviso verificables.

## 6. Persistencia, modelos y archivos privados

### 6.1 PostgreSQL

Una base `red_house` conserva datos estructurados, relaciones y compromisos. Las vistas `access_<propietario>` y credenciales separadas limitan acceso; no contienen copias físicas de cada servicio. Las tablas técnicas delimitan colas/idempotencia por propietario. Historiales y acciones relevantes se agregan sin permitir sobrescritura por credenciales runtime.

La publicación vigente documenta **esquema 20**. Las cifras de 71 tablas/72 con tabla técnica pertenecen al segundo parcial; no se trasladan al esquema ampliado como conteo actual. [Modelo físico previo](../segundo-parcial/Modelo_fisico.md), [esquemas y migraciones](../../data/database/README.md), [modelo compartido](Esquema_compartido.md) y [persistencia](Datos_y_persistencia.md) conservan linaje y cortes. La regeneración y revisión del catálogo/diagramas finales con todas las migraciones es un pendiente editorial/técnico identificado, sin ejecutarla sobre la base activa para obtener secretos.

Las API no migran al recibir peticiones. Las migraciones se aplican con respaldo, permisos de propietario y verificación en copia aislada. Una base compartida permite claves foráneas; no convierte la coordinación HTTP entre servicios en una transacción ACID global. La reserva mantiene estado durable, retención remota y compensación limitada.

### 6.2 MongoDB

Transporte, Custodia, Auditoría y Monitoreo tienen ámbitos documentales separados. UUID/identificador de evento deduplica entregas de outbox. Auditoría y custodia conservan eventos inmutables; las proyecciones autorizadas pueden actualizarse por secuencia.

`rh_transporte.shipment_tracking` conserva la versión/estado observado por traslado. Una secuencia anterior no degrada la proyección; misma identidad con otro contenido es conflicto. Índices regionales y de secuencia, pipelines y reconstrucción constan en [persistencia](Datos_y_persistencia.md) y pruebas del [segundo parcial](../evidencias/segundo-parcial/RESULTADOS.md). Esas comprobaciones conservan su corte histórico. MongoDB no sustituye al propietario SQL ni contiene los binarios del expediente.

Monitoreo intenta registrar sondeos primero en MongoDB y luego en SQL; puede consultar el historial documental durante una caída SQL si sigue autorizando Redis. Si ambos almacenes fallan, no se promete conservar cada sondeo.

### 6.3 Redis

Redis mantiene sesión/familia, renovación rotativa, revocación, versión de permisos, nonce de llamadas internas, contadores de consumo y caché autorizada. Los prefijos y ACL separan propietarios. El JWT firmado no permite omitir la consulta de estado actual. Redis inaccesible provoca rechazo seguro.

La caché incluye usuario/ámbito, filtros y revisión; no decide reservas. El portal guarda credenciales cifradas y una cookie opaca; cierres pendientes tienen registro SQL. Los TTL, ACL y claves se describen en [arquitectura](Arquitectura.md) y [reporte base](Reporte_tecnico_segundo_parcial.md); los valores efectivos de laboratorio se conservan en cada resultado, sin presentarlos como configuración productiva. Restaurar una copia antigua de Redis exige invalidar sesiones según el procedimiento, para impedir resucitar revocaciones posteriores.

### 6.4 Archivos del servidor y GCS

**LOCAL es el proveedor operativo predeterminado y publicado.** Documentos conserva metadatos, propietario/sujeto, tipo, tamaño, hash, generación, privacidad, estado y análisis. El binario se guarda en volumen privado del servidor; autorización y capacidades de transferencia no exponen credenciales de almacén al cliente. Las [rutas separadas API/portal](../entrega-final/continuidad/Rutas_almacenamiento_autonomas.md) conservan autonomía de productos.

Preparar, cargar y verificar son acciones distintas. El backend comprueba tamaño/tipo/estructura/hash y exige análisis limpio vigente antes del uso permitido. Un objeto ausente, pendiente, rechazado, infectado o con análisis indisponible no adquiere estado limpio por reintentar. Android volvió a codificar el JPEG sin EXIF en su ensayo; iOS eliminó metadatos originales y conservó cinco etiquetas técnicas observadas, sin GPSIFD ni fechas observadas. No se atribuye ausencia total de EXIF a ambas plataformas. Idempotencia de carga y verificación permite recuperar incertidumbre sin crear otro objeto verificado.

[Almacenamiento local](../evidencias/entrega-final/almacenamiento-local-20261113/RESULTADOS.md), [vigencia del antivirus](../evidencias/entrega-final/antivirus-vigencia-20261113/RESULTADOS.md) y [foto Android consultada por XML](../evidencias/entrega-final/mobile/seguimiento-20261114/foto-intercliente/RESULTADOS.md) acreditan alcances específicos. Este último confirmó VERIFIED/CLEAN, hash/generación/bytes, ausencia de EXIF, eventos SQL/Mongo coincidentes y 403 al transportista no asignado. No ejecutó GUI de escritorio ni una captura nueva.

GCS continúa **opcional para operar** y mantiene requisito académico separado. El [ensayo GCS real sintético JSON/XML](../evidencias/entrega-final/gcs-sintetico-20261113/RESULTADOS.md) y la [prueba anterior de bucket/URLs firmadas](../evidencias/segundo-parcial/gcs-real.json) conservan su evidencia. Google Cloud describe la firma temporal de objetos privados en su documentación de V4; la firma no sustituye la autorización de aplicación (Google Cloud, 2026c, referencia heredada).

Los 34 objetos GCS históricos pendientes de análisis no se presentan como descargables ni limpios. Las políticas clínicas de retención, clasificación, eliminación y conservación necesitan aprobación institucional; un hash/scan no acredita esa aprobación ni hace inviolable el archivo ante un administrador del host.

## 7. Contratos, autenticación y consistencia

Cada propietario publica OpenAPI y esquemas JSON/XML/XSD en [su directorio de servicios](../../apps/services/README.md). La API conserva `/api/v1`, entradas tipadas, envoltura de respuesta, códigos HTTP y errores seguros. Los contratos describen obligatoriedad, ejemplos, filtros y paginación. Un cambio incompatible necesita versión/convivencia explícita; cambiar un archivo cliente no acredita interoperabilidad hasta validar sus operaciones afectadas.

Móvil solicita JSON por HTTPS. Escritorio solicita XML y valida tanto la envoltura XSD como DTO/tipos de la operación y versión permitida; XML dentro de JSON o JSON dentro de XML no satisface esa separación. El parser rechaza DTD/entidades externas. Las transferencias binarias usan capacidades autorizadas; no transforman el cliente en consumidor directo de una base o bucket con credenciales.

Identidad firma JWT de acceso breve; renovación rota secreto y la reutilización revoca la familia. Cada operación protegida comprueba sesión/permisos/revocación en Redis y autorización actual del recurso. Las llamadas internas usan identidad de servicio firmada y delegación del actor cuando corresponde. Correlación relaciona petición, operación, evento y auditoría sin registrar tokens.

Las escrituras recuperables conservan `Idempotency-Key`, cuerpo, identidad y versión. Repetir con otro cuerpo se rechaza. Un timeout posterior al envío puede haber confirmado el commit; el cliente consulta estado y recupera la misma operación. Outbox transaccional e inbox deduplicado permiten centralización eventual sin prometer entrega externa exactamente una vez.

Las colas locales solo admiten operaciones declaradas. Ningún modo offline confirma liberación, reserva, asignación clínica o cierre verificado de custodia. Toda sincronización reautoriza identidad, institución, versión y estado antes de confirmar en servidor. Los detalles están en [estados backend](../entrega-final/backend/Estados.md), [contratos/rastreo](../entrega-final/backend/Rastreo.md) y las guías de cada cliente.

## 8. Laboratorio, HLA y decisión profesional

El registro distingue resultado no realizado, pendiente, indeterminado, informado y corregido, así como captura y revisión/autorización. Un archivo adjunto no prueba un resultado ni una prueba faltante equivale a negativa. HLA conserva muestra, método/laboratorio, fecha, loci/alelos, resolución, ambigüedad, nomenclatura, catálogo y responsable declarados.

El catálogo IPD-IMGT/HLA **3.66.0** y su hash proceden del [expediente de adquisición](../evidencias/entrega-final/algoritmos/fuentes_publicas/20261102T143541Z/RESULTADOS.md). Comprueba pertenencia/nomenclatura a esa edición; no interpreta compatibilidad inmunológica. Baja resolución, grupo o entrada ausente no se convierten en alelo exacto. No se redistribuye el catálogo completo como una copia modificada; sus condiciones y atribución constan en el [registro de fuentes](Reglas_y_fuentes_clinicas.md).

Perfil, acciones y evaluación conservan versiones/huellas. La corrección añade historia e invalida el uso actual de evaluaciones obsoletas; reproducir una instantánea histórica mantiene sus entradas congeladas. Captura, completitud técnica, preselección, evaluación y dictamen son estados distintos. La gobernanza sintética prueba mecanismos, sin atribuir acreditación real a una cuenta ficticia.

El [registro clínico/normativo](Reglas_y_fuentes_clinicas.md) contiene fuentes primarias, jurisdicción, fechas, transición y limitaciones. Este informe las reutiliza documentalmente; no vuelve a certificar su vigencia ni interpreta sus disposiciones. La NOM de sangre no se extiende por analogía a órganos, y nomenclatura HLA no proporciona criterios de asignación. Activación clínica, protocolos por producto/órgano, competencia de aprobadores y retención requieren validación externa.

## 9. Algoritmos explicables

La especificación completa, pseudocódigo, límites, ejemplos, oráculos y métricas se mantiene en [Algoritmos](Algoritmos.md) y [operación/reproducción](../entrega-final/algoritmos/correccion/Operacion_y_reproduccion.md). Se conservan RBC-1.0, ORGAN-1.0 y LOGISTICS-1.0 históricos. LOGISTICS-1.0 ordena vencimiento/minutos/distancia/ID; no debe atribuirse el uso de urgencia/espera de versiones sintéticas posteriores.

| Algoritmo | Entradas y salida | Complejidad del núcleo y límite |
| --- | --- | --- |
| EXPLAIN-PROFILE-2.0 | Solicitud, perfil, laboratorio, recursos/rutas; motivos por candidato e instantánea | Recorrido O(U+R) más resultados examinados/consultas; no es complejidad de toda la infraestructura |
| LOGISTICS-OWNER-SIM-3.0 | Evaluaciones vigentes/política sintética; orden lexicográfico y factores | O(C log C), memoria O(C); no prioridad clínica oficial ni ranking de órganos |
| REGIONAL-DIJKSTRA-2.0 | Grafo dirigido versionado, costes no negativos/bloqueos; ruta y coste | O((V+E) log V) más ordenación determinista; memoria O(V+E) |
| COVERAGE-HK-1.0 | Grafo de cupos/candidatos revisados; matching máximo | Hopcroft–Karp O(E√V); cardinalidad, sin coste clínico ni reserva automática |
| DEMAND-OWNER-SES-2.0 | Destinos registrados, ventanas diarias, stock/lotes; pronóstico, MAE y sobrantes | O(H+B log B) del núcleo; extracción acotada separada |
| CONSISTENCY-OWNER-2.0 | Hechos de propietarios autorizados; anomalías potenciales y revisión | O(F+S) del detector; acceso SQL/Mongo/HTTP se mide aparte |

El matching usa BFS por capas y DFS de caminos aumentantes hasta no poder ampliar el conjunto. Si cupo A permite U1/U2 y B solo U1, puede producir dos parejas. No optimiza urgencia o coste. Su propuesta conserva `reservations_created=0`; Inventario revalida antes de comprometer recursos.

El ranking sintético excluye factores ausentes/restricciones incumplidas y ordena `(-urgencia,-espera,vencimiento,minutos,distancia,id)`. Guarda escala, política, fuente y corte. Son parámetros de simulación, sin pesos médicos inventados.

Dijkstra relaja mejoras estrictas con heap y reconstruye predecesores. Los oráculos enumeran caminos pequeños; pesos inválidos y ausencia de ruta producen rechazo o `UNREACHABLE`. La adquisición vial pública posterior conserva originales/hash y atribución, pero no demuestra actualidad vial, tráfico o ETA medida desde GPS. Se separan cartografía, ruta planificada, posición observada y ETA modelada.

SES divide cronológicamente entrenamiento/evaluación, selecciona alfa entre 0,2/0,5/0,8 solo en entrenamiento y compara MAE contra persistencia. Un día sin evento cuenta ausencia de registro, no ausencia física de demanda. Sin consumo registrado devuelve insuficiencia; no ejecuta transferencias ni prolonga caducidades. El detector de inconsistencias abre hallazgos potenciales deduplicados y requiere revisión; no corrige silenciosamente el pasado.

Los [benchmarks integrados](../evidencias/entrega-final/algoritmos/correccion_comprobacion/20261101T042648Z/benchmark-final.json) conservan tamaños, repeticiones, mediana/p95, asignaciones Python/RSS y alcance. No equivalen a latencia productiva, Locust sostenido o beneficio clínico. Las [fuentes públicas y resultados](../evidencias/entrega-final/algoritmos/fuentes_publicas/20261102T143541Z/RESULTADOS.md) registran fallos, correcciones y repeticiones sin borrar incidentes.

## 10. Aplicación Android/iOS

Kotlin Multiplatform comparte sesión, contratos JSON, estado y reglas de presentación; Compose Multiplatform aporta UI y puentes nativos para cámara, ubicación, mapas y almacenamiento. Los cinco perfiles son donante, operador, transportista, coordinador y médico. La app no replica la autoridad del backend ni usa sesiones web.

El donante entra a feed/campañas y próxima cita; compartir publica únicamente texto público mediante selector nativo. Transportista prioriza mapa, tarea y siguiente acción, con QR previo a transferencias. Médico consulta datos autorizados; no se habilita un dictamen clínico móvil por la mera existencia del perfil. El resto de operaciones se filtra por servidor y ámbito.

Android protege sesión/diario con Keystore/AES-GCM; iOS utiliza Keychain con acceso ligado al dispositivo y cubierta al salir de primer plano. La contraseña no se persiste. Observaciones permitidas y comandos interactivos inciertos tienen tratamientos separados; un reintento de custodia conserva clave/cuerpo y nunca se transforma en confirmación offline. Logout detiene captura/trabajos y solicita revocación; si falta red, informa que el cierre remoto no está confirmado.

Android se verifica en emulador, sin exigir teléfono. Hay recorridos de donante/agenda, permisos, paginación, recreación, sincronización, QR óptico de escena virtual, custodia y fotografía con recuperación. [Resultados por intento](../evidencias/entrega-final/mobile/RESULTADOS.md) conservan versiones y omisiones. La cámara/posición emuladas no acreditan hardware Android físico.

La app normal iOS fue firmada, actualizada y abierta en **iPhone 16 Pro**, y se inspeccionó sesión donante/calendario en recorridos identificados. El [paquete normal del corte d735668](../evidencias/entrega-final/mobile/seguimiento-20261114/paquetes.md) acredita firma/instalación/arranque, sin nueva operación de negocio ni prueba de continuidad de sesión. El perfil vence el **17/11/2026 a las 22:39 UTC**, antes de la entrega del día 23; renovar la firma sigue pendiente. Compilar arm64, firmar, instalar, abrir y completar un recorrido son evidencias distintas.

El [laboratorio físico iOS del 14/11](../evidencias/entrega-final/mobile/ios-lab-20261114/RESULTADOS.md) ejecutó una variante separada `org.redhouse.mobile.lab`, con cuentas sintéticas introducidas manualmente. El oráculo confirmó dos escaneos del mismo recurso/traslado, fotografía CLEAN con tamaño/hash/generación coincidentes y dos posiciones iOS correlacionadas en SQL/MongoDB/Redis. El seguimiento terminó detenido; el traslado permaneció PREPARED y no se ejecutó custodia completa. El servidor no conservó indicador explícito `simulated=false`; el resultado no acredita esa propiedad ni una precisión determinada.

El cierre de transporte revocó su familia SQL y eliminó su clave Redis, conservando otra familia del fixture. Donante modificó nombre propio a versión 2 con auditoría; la campaña 105 se encontró mediante búsqueda, **sin probar navegación hasta página 6**. HTTPS positivo pasó; negativos de CA ajena, vencimiento, hostname/origen y validación WSS de esta variante permanecen pendientes. Las siete comprobaciones de identidad pasaron. El perfil lab vence el 21/11; tampoco sirve como firma vigente para el 23. La nueva compilación normal conservó origen de producción y ausencia de CA de laboratorio, pero no se instaló. Este ensayo no se atribuye a la app normal ni cierra la etapa 04.

La bandeja interna y adaptadores tienen alcance verificable aislado. La recepción física **FCM/APNs permanece pendiente externa por decisión humana**; no se configuraron cuentas/proyectos/certificados para aparentar entrega. No se descarga runtime Simulator. Las [dependencias y límites](../entrega-final/mobile/Dependencias_externas.md), [matriz móvil](../entrega-final/mobile/Matriz.md) y [guía de compilación](../../apps/mobile/README.md) se leen junto a sus cortes: algunas notas iniciales de firma/iPhone de la guía quedaron superadas por el expediente reciente.

## 11. Consola de escritorio

PySide6/Python atiende procesos internos con tablas, búsqueda/paginación, captura, evaluación, comparación, reserva, custodia, reportes y etiquetas. La consola utiliza HTTPS/XML, XSD y DTO por operación; copia contratos versionados y no necesita el código servidor para ejecutarse. La red se procesa fuera del hilo principal. Las escrituras requieren diario cifrado por cuenta y llavero disponible; no existe cola universal de negocio offline.

Los expedientes acreditan [captura/revisión de laboratorio](../evidencias/entrega-final/desktop/iteracion-laboratorio/RESULTADOS.md), [evaluación](../evidencias/entrega-final/desktop/iteracion-evaluacion/RESULTADOS.md), [reserva recuperable](../evidencias/entrega-final/desktop/iteracion-reserva/RESULTADOS.md), [cobertura](../evidencias/entrega-final/desktop/iteracion-cobertura-doble/RESULTADOS.md) y otros recorridos especificados en [DESK-01…14](../evidencias/entrega-final/desktop/MATRIZ.md). Las pruebas de cliente y una ventana Qt aislada no sustituyen todos los recorridos funcionales.

El [ensayo de caída/restauración](../evidencias/entrega-final/desktop/iteracion-recuperacion-servicio/RESULTADOS.md) pasó 1/1 en 42,087 s: consulta persistida, detención del listener de Priorización, error visible con limpieza de resultados, restauración y recuperación de una sola propuesta SQL. Qt se renderizó offscreen sobre fixture TESTING/WSGI; la clave del diario fue efímera. No acredita caída productiva ni todas las latencias. El mensaje posterior se revisó con un doble, separado del recorrido real.

El [paquete macOS x86_64](../evidencias/entrega-final/desktop/paquete-mac-20261114/RESULTADOS.md) conserva app/ZIP privados, hash y arranque, con acceso inspeccionado sin iniciar sesión. No está certificado como distribución notarizada. **Windows 11, macOS arm64, Linux e impresión/lector físicos no se presentan como probados.** El runner previsto no acredita una ejecución Windows; los BAT de servidor mediante WSL no son instalables nativos de esta consola. [Distribución](../entrega-final/continuidad/Distribucion_escritorio.md) y [manual](../../apps/desktop/README.md) conservan requisitos y pendientes.

## 12. Rastreo WSS y cartografía

Transporte autoriza dispositivo/usuario, asignación, periodo y estado por cada publicación/entrega. El punto válido se compromete en SQL junto con cursor/outbox; solo entonces se responde `PERSISTED_SQL`. MongoDB proyecta después y Redis conserva datos temporales/avisos. UUID/secuencia/cuerpo permiten deduplicar; un dato atrasado puede conservarse sin hacer retroceder la última observación.

HTTP, mensajes WSS y esquemas están separados en [contratos de rastreo](../../apps/services/ms_transporte/contracts/websocket/). JSON usa `/ws/v1/tracking/json`; escritorio usa XML/XSD por `/ws/v1/tracking/xml`, con prefijo público del gateway. Primero se autentica; no se pasan credenciales en query string. Suscripción por cursor, heartbeat, ACK, estado y `resync.required` permiten recuperar huecos con límites de ventana/memoria. Una conexión existente no migra de réplica: el cliente reconecta y recupera cursor.

El [manual de receptor/simulador](../entrega-final/backend/Rastreo.md) reúne TRACK-01…TRACK-10, adaptador JSON/NMEA RMC, escenarios de duplicado/desorden/sin fijación/reconexión, parámetros y procedencia. El simulador entra por WSS real y no escribe directamente en bases. El hardware GPS externo es opcional; no se declara comprado, conectado ni aceptado.

Las vistas distinguen posición/fuente/hora/precisión, antigüedad y desconexión; el mapa no inventa observaciones ni entrega física. Web/Android utilizan cartografía con atribución OSM; iOS integra MapKit. La geometría del mapa de escritorio pasa por puente local autorizado, manteniendo XML en su cliente de negocio. La disponibilidad de mosaicos no prueba actualización del grafo vial ni tráfico. Una alternativa textual conserva estado cuando falla la cartografía, sin presentarse como mapa operativo.

I06-07 comprobó caída/recuperación con Nginx/Chrome WSS y eventos SQL/Mongo. I06-08 tiene A/C/D y B03 aprobados por separado. B03 verificó cierre durante caída, recuperación autorizada y ausencia de datos privados para sesión revocada. El fix WSS se [publicó con Nginx efectivo 1.28.3](../evidencias/gcp/proxy-wss-20261114/RESULTADOS.md). Los [intentos previos](../evidencias/entrega-final/portal-security-20261114/RESULTADOS.md) conservan B01/B02 fallidos; cambio de rol/asignación en las combinaciones exactas pendientes no se declara cubierto por logout. Falta correlacionar todos los mapas/clientes y medir latencia extremo a extremo/concurrencia sostenida; TRACK integral permanece abierto.

## 13. Seguridad, privacidad y auditoría

Las contraseñas se almacenan con hash; secretos, ADC, claves de firma, tokens y respaldos privados permanecen fuera de Git. El servidor conserva JWT/renovación/revocación, permisos actuales, rate limiting, registro de intentos y autorización institucional. La web añade CSRF y escape de presentación. SQL usa consultas parametrizadas; JSON/XML y archivos se validan según contrato. HTTPS/WSS conserva verificación TLS.

MFA y reautenticación protegen acciones críticas. El reto se liga a intención, clave idempotente, cuerpo y sesión; recuperar una misma operación no permite cambiar esos datos. La [integración de reautenticación](../evidencias/entrega-final/reauth-20261113/integracion/README.md) conserva el defecto base64url no canónico y sus pruebas dirigidas; no se presenta la pasada inicial con fallos como íntegramente aprobada.

Auditoría conserva accesos sensibles, rechazos, acciones, versiones y correlación minimizados. Custodia conserva transferencias y hashes encadenados. Append-only y hash detectan alteraciones dentro del modelo de confianza; no certifican verdad física, firma legal ni resistencia absoluta al superusuario. Una corrección agrega evento, sin borrar el anterior.

ClamD real analiza archivos con versión/fecha de firmas y límite de antigüedad. La [vigilancia operativa](../entrega-final/continuidad/CLAMD_VIGENCIA.md) y [publicación del esquema 20](../evidencias/gcp/scanner20-20261113/RESULTADOS.md) distinguen firmas cargadas de archivos descargados. Un escáner indisponible/antiguo falla seguro; no se marca CLEAN para continuar un traslado. El análisis malware no acredita política clínica de retención.

La ubicación se captura solo para tarea/periodo autorizado y se detiene al salir del alcance según plataforma. Las pruebas sintéticas no certifican políticas institucionales de privacidad. Capturas, logs y demostración deben ocultar tokens, expedientes y actividades ajenas del dispositivo.

## 14. Infraestructura, operación y recuperación

El entorno desplegado conocido es **sistemas-integracion-01 / red-house / me-central1-a**, origen HTTPS `https://34.18.186.116`. Las [comprobaciones publicadas](../evidencias/gcp/proxy-wss-20261114/RESULTADOS.md) identifican versión/configuración, treinta contenedores sanos y almacenamiento LOCAL. El esquema 20 y la alineación de escáner tienen [expediente propio](../evidencias/gcp/scanner20-20261113/RESULTADOS.md). No se atribuye a GCP una prueba local ni se asegura que todo cambio cliente/local esté desplegado.

Compose separa web, gateway, veinticuatro réplicas API/worker, PostgreSQL, MongoDB, Redis y antivirus. El bootstrap es un trabajo de instalación. Credenciales/puertos/firewall limitan acceso a almacenes; el gateway termina HTTPS y enruta HTTP/WSS. Los puertos internos no constituyen exposición pública autorizada.

Salud distingue proceso, readiness, PostgreSQL, Redis, MongoDB y archivos; Monitoreo conserva versión, última verificación, errores, tiempos y dependencia. La salud consultada es un instante. Un worker/cola atrasado y una dependencia inaccesible deben mostrarse degradados, sin convertir un `/health/live` exitoso en salud de toda la plataforma.

Dos réplicas en un host toleran ciertas caídas de proceso; gateway, almacenes y host siguen siendo puntos comunes. No existe evidencia de alta disponibilidad multizona o tolerancia total a pérdida del host. Redis caído deniega acceso protegido; SQL caído impide nuevos compromisos; MongoDB caído deja centralización pendiente en outbox; archivos indisponibles bloquean su ciclo y no todos los procesos sin archivo. Al recuperar se consulta estado antes de repetir escrituras.

El [ensayo coordinado aislado](../evidencias/entrega-final/recuperacion-20261113/RESULTADOS.md) restauró SQL, MongoDB, Redis y volumen privado con datos sintéticos. Observó **RTO 21,733 s** hasta descarga autorizada y **RPO 23,787 s** del documento conservado. Cerró escritores/listeners para el corte e invalidó explícitamente sesiones restauradas. No probó detección, host perdido, transferencia externa, claves perdidas, proxy/TLS, escrituras concurrentes ni GCS. Estos valores son observaciones, **no objetivos aprobados ni SLA**. El [procedimiento y límites](../entrega-final/continuidad/Plan_recuperacion_coordinada.md) conserva requisitos de una recuperación real.

Instalación/arranque y diagnóstico se mantienen en [operación local](Instalacion_y_operacion.md), [Docker](../../deployment/README.md) y [GCE](../../deployment/gcp/README.md). No se debe ejecutar un procedimiento remoto histórico genéricamente: depende de respaldo, configuración y versión exactos. CI tiene configuración reproducible; los pases locales no acreditan ejecución remota del workflow.

## 15. Pruebas y resultados de rendimiento

Cada expediente conserva fecha, versión/manifiesto, entorno, comando, esperado/obtenido, incidencias y límites. Esta edición **no ejecuta motores, regresiones funcionales ni carga**; reúne resultados existentes y realiza [verificación editorial ligera de fuente/generador](../evidencias/entrega-final/documentacion-20261114/validacion-fuente.json), incluida exportación Word temporal y conservación del modo histórico. Se retiene cobertura aplicable cuando un cambio posterior no la invalida.

La evidencia anterior de [segundo parcial](../evidencias/segundo-parcial/RESULTADOS.md) incluye regresión, contratos, navegador, Docker, clon limpio y restauración. Su clon limpio no certifica instalación nueva del paquete final ampliado. Las ejecuciones recientes por componente se enlazan en las secciones anteriores y en [pruebas/validación](Pruebas_y_validacion.md); una cantidad agregada de tests no sustituye tres procesos E2E aceptados.

La [línea base sostenida del 14/11](../evidencias/entrega-final/carga-20261114/baseline-6/RESULTADOS.md) utilizó seis perfiles, 30 s de calentamiento y 120,005 s medidos; **1.029 lecturas, cero errores y 8,575 peticiones/s**. El mayor p95 por endpoint fue **430 ms**; el p99 de Auditoría fue **680 ms**, mayor entre las operaciones informadas. La mediana del corte exacto no se conservó. No se sustituye el corte por CSV de drenado ni se suman calentamiento y medición como otra corrida.

Se usaron 2.000 donantes, 10.000 recursos y 100.000 eventos **SQL**, no ese volumen MongoDB. Mac Intel de 16 GiB, generador/servidores en el mismo host, una instancia por servicio en loopback, sin Nginx ni réplicas. Procesos reales con cuotas/MFA de producto; operador XML/XSD y restantes perfiles JSON. Se verificó revocación de seis familias en SQL/Redis. El entorno conservó guardas de disco y cerró sus motores propios.

| Operación de muestra | Peticiones | Media ms | p95 ms | p99 ms |
| --- | ---: | ---: | ---: | ---: |
| Auditoría / Bitácora | 92 | 273,7 | 430 | 680 |
| Inventario propio | 81 | 254,4 | 430 | 540 |
| Transporte / Traslados | 72 | 239,0 | 420 | 580 |
| Disponibilidad regional | 85 | 232,8 | 400 | 470 |
| Feed público | 73 | 116,8 | 180 | 210 |

La tabla resume operaciones del mismo corte, no escenarios independientes. [Measurement](../evidencias/entrega-final/carga-20261114/baseline-6/measurement.json), [topología](../evidencias/entrega-final/carga-20261114/baseline-6/topology.json) y CSV conservan el detalle. Preparación/datos incluye guardas y no mide inserción SQL pura. RSS/CPU sumados tienen límites de doble conteo y muestreo descritos en el resultado.

La [serie posterior planificada](../evidencias/entrega-final/carga-20261114/serie-plan.md) **no tiene resultado incorporado en este corte**. Faltan niveles superiores, comparación con/sin caché, transacciones, saturación/estrés, recuperación y escalabilidad. La línea base no mide capacidad GCP, carga de escritura ni validez clínica. Los [intentos fallidos del 13/11](../evidencias/entrega-final/carga-20261113/RESULTADOS.md) conservan su expediente y no se borran por una corrida posterior aprobada.

## 16. Manuales, artefactos y reproducción

Los siguientes comandos orientan la reproducción desde la raíz; requieren los prerrequisitos y permisos de cada guía. Este informe no los ejecutó ni autoriza intervenir una instalación ajena.

```sh
# Servidor local; revisar antes requisitos/variables privadas de la guía vigente.
bash install.sh
bash start.sh
bash components.sh estado
bash stop.sh

# Docker de desarrollo separado; no reutilizar volúmenes privados habituales.
python3 deployment/start.py

# Android: compilar pruebas JVM y APK de desarrollo.
./apps/mobile/gradlew -p apps/mobile :composeApp:testDebugUnitTest :composeApp:assembleDebug

# Escritorio: contratos de la copia del cliente, sin iniciar motores.
apps/desktop/.venv/bin/python apps/desktop/sync_contracts.py --check
```

El [manual móvil](../../apps/mobile/README.md) registra JDK/SDK/Gradle y Xcode/firmas. El [manual escritorio](../../apps/desktop/README.md) registra Python 3.12.6/macOS x86_64 y dependencias fijadas para ese entorno. Las guías no deben interpretarse como comprobaciones de otras plataformas. Los empaquetados recientes se identifican en [móvil](../evidencias/entrega-final/mobile/seguimiento-20261114/paquetes.md) y [Mac](../evidencias/entrega-final/desktop/paquete-mac-20261114/RESULTADOS.md); sus archivos privados no se publican mediante este documento.

El paquete final todavía requiere manifiesto liberable consolidado, instrucciones/artefactos por plataforma realmente verificada y evidencia de clon limpio/actualización final. Android debug no es firma de distribución; iOS normal tiene vencimiento anterior al día 23; Mac no acredita Windows ni notarización. Licencias, atribuciones de mapas y condiciones HLA deben conservarse al distribuir, sin incluir secretos, `.env` real, ADC, claves privadas, dumps ni datos clínicos.

### Generación del documento Word/PDF

Se reutiliza `scripts/export_partial_report.py`, que conserva diseño institucional, carta, estilos, tablas, pie e índice enlazado del reporte anterior. La opción `--final` selecciona este archivo y una portada con corte propio; no importa capítulos, fecha ni declaración de autoría de la entrega histórica. Los anexos actuales se consultan por enlaces en el cuerpo. El modo anterior sigue disponible para regenerar el segundo parcial.

Dependencias del entorno editorial: `python-docx`, `Markdown`, `lxml`, `Pillow`; para PDF, `PyMuPDF` y `soffice`/LibreOffice en PATH. El [archivo de dependencias fijadas](../../scripts/requirements-docs.txt) registra el entorno preparado con Python 3.12.6/macOS x86_64; no acredita compatibilidad de otras plataformas. Desde la raíz:

```sh
# Preparación editorial aislada; --only-binary evita compilaciones de dependencias.
python3 -m venv .local/venv-docs
.local/venv-docs/bin/python -m pip install --only-binary=:all: -r scripts/requirements-docs.txt

# Word de trabajo; índice sin páginas definitivas.
.local/venv-docs/bin/python scripts/export_partial_report.py --final

# Word y PDF; conversión LibreOffice hasta estabilizar índice y páginas.
.local/venv-docs/bin/python scripts/export_partial_report.py --final --pdf
```

Destinos: `documentation/docx/Reporte_tecnico_final.docx` y `documentation/pdf/Reporte_tecnico_final.pdf`. **Este corte prepara fuente/generador; no ejecuta render pesado ni declara revisión visual de esos artefactos.** Antes de liberarlos deben comprobarse integridad, enlaces, índice, tablas/figuras y texto dentro de página, e inspeccionarse el PDF. Un archivo generado no basta para dar por terminada la calidad editorial.

## 17. Incidencias, participación y entrega académica

Los incidentes se conservan en su expediente original con intentos y resultados; la [matriz de continuidad](../entrega-final/continuidad/Matriz.md) relaciona pendientes y evidencia. Los fallos B01/B02 del portal, las firmas antiguas del escáner, incidencias de compilación/arnés y preparaciones fallidas de carga tienen resoluciones o límites distintos. No se reescriben como pruebas nuevas ni se atribuyen defectos de producto a un fallo del arnés sin diagnóstico.

Se reutiliza el [guion de demostración](../entrega-final/continuidad/Demostracion_final.md). La versión final debe mostrar problema/arquitectura, web, Android/iOS, escritorio, contratos reales, Swagger, monitoreo/GCP, algoritmo, carga y procesos con rechazo/recuperación. Los ensayos parciales actuales sirven de soporte fechado; no sustituyen una grabación final completa.

El registro nominal de responsabilidades/contribuciones y las reflexiones necesitan aportes y confirmación de cada integrante. Este informe no infiere dominio técnico por cantidad de commits ni redacta experiencias personales en nombre del equipo. La defensa requiere explicar decisiones, localizar contratos/migraciones/pruebas y resolver un cambio pequeño en entorno de prueba.

El requisito textual «Sistema desplegado en la nube y en ubiquitous» se interpreta según la aclaración vigente: **Ubiquitous es la plataforma humana de entrega**, no otro despliegue técnico. Quedan pendientes confirmación de subida, video final, presentación efectuada y entregas/reflexiones individuales. La presentación/video del segundo parcial confirmados por el equipo son antecedentes, no evidencia de esos eventos finales. No se incorpora enlace de video inventado ni declaración de envío sin comprobante humano.

## 18. Limitaciones, riesgos y trabajo pendiente

La disposición por requisito permanece en la [matriz única](../entrega-final/continuidad/Matriz.md). El corte conserva estos límites principales:

- **Integración:** faltan los tres procesos finales correlacionados entre productos, con sus errores, auditoría, avisos y visualización; no se cierra por concatenar ensayos independientes.
- **Continuidad:** I06 y combinaciones pendientes de rol/asignación necesitan su evidencia; dos réplicas en un host no toleran pérdida total de infraestructura.
- **Rendimiento:** la línea base de seis perfiles es lectura local acotada; la serie mayor, caché, transacciones, estrés y recuperación no tienen resultado integrado aquí.
- **Plataformas:** Windows 11 nativo no probado; Linux adicional, Mac arm64 e impresión/lector físicos sin aceptación. Android se acepta en emulador; laboratorio físico iOS conserva identidad y alcance separados, con paginación por seis páginas, negativos TLS y otros recorridos pendientes.
- **Firma/distribución:** perfil normal iOS vence el 17/11, antes del 23; renovar firma y actualizar artefactos. El APK es debug y Mac no tiene certificación de distribución notarizada.
- **Avisos:** recepción física FCM/APNs pendiente externa por decisión humana, sin inventar cuentas/configuración. Bandeja/adaptadores no acreditan entrega de proveedor.
- **Clínica y privacidad:** protocolos, aprobación profesional, criterios oficiales de asignación y políticas de retención siguen externos. Los perfiles sintéticos verifican mecanismos, sin habilitar práctica clínica.
- **Archivos:** GCS opcional y prueba académica separada; objetos históricos sin análisis no adquieren CLEAN. El volumen local y sus secretos necesitan recuperación/operación con política institucional aprobada.
- **Expediente:** faltan actualización editorial completa de modelos/diagramas, render/inspección Word/PDF, paquete final reproducible y aportes humanos de video, exposición, participación/reflexiones/Ubiquitous.

Las prioridades técnicas son completar los flujos integrales faltantes, cerrar continuidad/medición, integrar evidencia por plataforma y consolidar artefactos. Las decisiones externas conservan responsable humano o institucional; enumerarlas no las aprueba. Las funcionalidades no afectadas mantienen su cobertura histórica aplicable, evitando repetir auditorías completas por un ajuste documental.

## 19. Conclusiones técnicas sustentadas

La evidencia disponible demuestra coordinación persistente, contratos JSON/XML, controles institucionales, procesos de cliente reales y recuperación en escenarios definidos. La separación entre propuesta algorítmica, compromiso transaccional y decisión humana está expresada en estados y pruebas. La consulta XML de una fotografía producida desde Android comprueba una capacidad intercliente concreta.

El alcance probado continúa siendo académico, con datos ficticios y entornos identificados. Los resultados no justifican aceptación integral, rendimiento productivo, alta disponibilidad multizona ni certificación clínica. El cierre exige completar los criterios técnicos pendientes y las acciones humanas del expediente. Esta conclusión es una síntesis del material verificable, no una reflexión individual atribuida a integrantes.

## 20. Referencias y procedencia

Las citas técnicas/normativas siguientes se reutilizan de los registros existentes. **Esta edición no realizó una nueva consulta web ni certifica vigencia legal o compatibilidad actual de dependencias.** Fechas/versiones de adquisición y sus hashes permanecen en el [registro clínico](Reglas_y_fuentes_clinicas.md), [fuentes públicas](../evidencias/entrega-final/algoritmos/fuentes_publicas/20261102T143541Z/RESULTADOS.md), [dependencias móviles](../entrega-final/mobile/Dependencias_externas.md) y expedientes enlazados. Las fuentes previas en [APA del segundo parcial](../segundo-parcial/Referencias.md) conservan su corte; la revisión final de referencias sigue abierta.

Apple. (s. f.). *Keychain services*. Apple Developer Documentation. [Documentación oficial](https://developer.apple.com/documentation/security/keychain-services).

Docker. (s. f.). *Networking in Compose*. Docker Docs. [Documentación oficial](https://docs.docker.com/compose/how-tos/networking/).

Google Cloud. (2026c, 21 de octubre). *V4 signing process with Cloud Storage tools*. [Referencia conservada del segundo parcial](https://docs.cloud.google.com/storage/docs/access-control/signing-urls-with-helpers).

IPD-IMGT/HLA. (2026). *IPD-IMGT/HLA Database* (edición 3.66.0). European Bioinformatics Institute. [Licencia y atribución](https://www.ebi.ac.uk/ipd/imgt/hla/licence/). Adquisición documentada el 02/11/2026; edición/hash en el expediente del proyecto.

JetBrains. (s. f.). *Multiplatform compatibility guide*. Kotlin Documentation. [Guía oficial](https://kotlinlang.org/docs/multiplatform/multiplatform-compatibility-guide.html).

NGINX. (s. f.). *WebSocket proxying*. [Documentación oficial](https://nginx.org/en/docs/http/websocket.html).

OpenStreetMap Foundation. (s. f.). *Tile usage policy*. [Política oficial](https://operations.osmfoundation.org/policies/tiles/).

OWASP Foundation. (s. f.). *WebSocket security cheat sheet*. OWASP Cheat Sheet Series. [Guía oficial](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html).

PostgreSQL Global Development Group. (s. f.). *Explicit locking*. PostgreSQL Documentation. [Documentación oficial](https://www.postgresql.org/docs/current/explicit-locking.html).

Qt Group. (s. f.). *Getting started*. Qt for Python Documentation. [Guía oficial](https://doc.qt.io/qtforpython-6/gettingstarted.html).

Secretaría de Salud. (2012). *NOM-253-SSA1-2012, para la disposición de sangre humana y sus componentes con fines terapéuticos*. Diario Oficial de la Federación. [Texto oficial enlazado por el registro clínico](https://dof.gob.mx/normasOficiales/4917/salud3a/salud3a.html). Su aplicabilidad y transición requieren revisión competente; no se deriva aquí una regla clínica.

Secretaría de Salud. (2014). *Reglamento de la Ley General de Salud en materia de trasplantes*. [Texto oficial conservado en referencias](https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_LGS_MT.pdf). El proyecto no sustituye sus procedimientos por un ranking local.

La consigna de entrega final y la retroalimentación docente están disponibles en `../stuff/` respecto de la raíz del repositorio del entorno original. Sus requisitos se conservan en los [prompts de entrega final](../../stuff/prompts/entrega-final/README.md), en especial [documentación/entrega](../../stuff/prompts/entrega-final/08_documentacion_y_entrega.md) y [rastreo](../../stuff/prompts/entrega-final/09_rastreo_gps_websockets.md), para que el expediente no dependa de distribuir archivos externos.
