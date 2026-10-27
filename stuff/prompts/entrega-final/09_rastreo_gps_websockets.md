# Complemento 09 Rastreo GPS por WebSockets y mapa de Nuevo León

Esta especificación amplía los prompts de la entrega final por solicitud del usuario del 27 de octubre de 2026. Implementa rastreo autorizado del transportista durante sus traslados, con actualización real por WebSockets seguros y un mapa interactivo actual de Nuevo León. El GPS físico todavía no está disponible: entrega el receptor, contratos, adaptadores y pruebas con simulador, dejando identificada la integración física pendiente. Crear esta especificación no significa que el rastreo ya funcione.

## Cuándo utilizar este complemento

El número 09 identifica este archivo; **no indica que debas esperar a terminar el 08**. Léelo desde el prompt 01 junto con el contexto 00 y aplica sus responsabilidades durante las etapas 01 a 08. Los prompts y la guía ya lo incluyen como referencia obligatoria, por lo que no necesitas encargar dos veces las mismas funciones.

Si ya ejecutaste etapas sin este requisito, utiliza el prompt inicial del complemento 09 incluido en la guía para completar el rastreo sobre los componentes existentes antes de cerrar integración 07 y entrega 08. Registra las partes que dependan de clientes aún no construidos y revísalas cuando existan; no dupliques servicios, datos ni reglas ni marques esas integraciones como probadas antes de tiempo.

## Alcance y responsables

Transporte es propietario del rastreo y de su relación con dispositivo, transportista y traslado. Identidad gestiona credenciales/permisos; Monitoreo observa su salud. Justifica un proceso de conexiones persistentes si es necesario sin duplicar la autoridad de Transporte ni agregar servicios para completar una cifra.

| Etapa | Responsabilidad |
| --- | --- |
| 01 Backend | Dispositivos/asignaciones, recepción normalizada, WSS, mensajes JSON/XML, almacenamiento, cursores y simulador |
| 02 Algoritmos | Separar ubicación observada, ruta estimada y ETA calculada, con procedencia y limitaciones |
| 03 Web | Mapa operativo de Nuevo León y seguimiento autorizado con actualización WSS |
| 04 Android | GPS del teléfono cuando esté autorizado, integración con GPS externo según hardware y seguimiento JSON |
| 05 Escritorio | Mapa de coordinación y seguimiento XML/XSD en la consola PySide6 |
| 06 Infraestructura | WSS/gateway, sesiones largas, privacidad, reconexión entre réplicas y monitorización |
| 07 Pruebas | Recorrido de puntos a mapa, formatos, seguridad, retrasos, pérdidas y recuperación |
| 08 Entrega | Contratos, diagramas, manuales, evidencia con simulador y aceptación física pendiente |

WebSockets transporta telemetría; no sustituye las autorizaciones, contratos REST ni eventos de negocio de reserva, custodia o recepción. Su caída no debe detener las demás funciones ni convertir una posición antigua en actual. Conserva la autonomía web: prueba que su negocio y consulta histórica no adquieren una dependencia obligatoria de la API de rastreo.

## TRACK-01 GPS futuro y fuentes intercambiables

Define una interfaz de proveedor para normalizar posiciones del GPS físico, del teléfono Android o del simulador. El GPS físico y el teléfono son fuentes distintas; registra la procedencia y no cambies automáticamente entre ellas sin política explícita.

No inventes marca, precisión, conector ni capacidad de red del GPS que se adquirirá. Documenta los datos que faltan para integrarlo: modelo, protocolo, formato, conectividad, frecuencia, alimentación, autenticación y entorno de instalación. Un receptor GPS puede requerir un puente para transmitir; no asumas que el dispositivo ofrece WebSockets nativamente.

Entrega un adaptador de entrada y una herramienta/puente ejecutable con interfaz configurable. Si el futuro equipo emite serial/NMEA, HTTP, TCP u otro protocolo, su adaptador transforma ese formato al contrato normalizado y se autentica contra Transporte; no conecta a las bases. La conexión específica solo se declara verificada cuando se pruebe el equipo real.

Vincula dispositivo, responsable y traslado mediante asignaciones con vigencia. El servidor deriva institución/región y comprueba esa relación; no confía en que el GPS declare por sí mismo a qué traslado pertenece. Permite revocar/reasignar sin conservar acceso al traslado anterior.

## TRACK-02 Contrato de ubicación y eventos

Define un esquema versionado de posición con `event_id`, `schema_version`, `shipment_id`, `device_id`, fuente, secuencia por origen, fecha de captura y recepción, latitud, longitud, indicador de fijación válida y precisión cuando el equipo la reporte. Velocidad, rumbo, altitud y batería son opcionales y llevan unidades explícitas; no inventes valores faltantes.

Define WGS84 para las coordenadas normalizadas, documenta cualquier transformación y diferencia orden latitud/longitud de formatos geográficos que usan longitud/latitud. Valida rangos, tipos finitos, tamaños, fechas, duplicados y desfase temporal; una coordenada `0,0` no equivale a ausencia de señal.

Publica contratos para autenticar, suscribirse/cancelar, enviar/recibir posiciones, reconocer recepción/persistencia, recuperar una instantánea/cursor, informar estado y errores. Define mensajes como `position.updated`, `tracking.status`, `resync.required` y errores seguros, o equivalentes compatibles documentados. No expongas nombres de pacientes, donantes, órganos o tokens en los mensajes de posición.

Android utiliza JSON. Escritorio utiliza **XML validado con XSD y DTO**, también para autenticación de socket, suscripción, posición, estados y errores. Web consume la representación autorizada para su interfaz. Usa subprotocolos o rutas WSS diferenciados por formato y versiona su esquema; no envíes JSON a PySide6 por conveniencia.

Mantén OpenAPI para HTTP y documenta por separado el contrato de eventos WebSocket, con ejemplos JSON/XML, permisos, dirección de mensajes, límites, cierres y reconexión. El hecho de describir un handshake HTTP no documenta todos los eventos de una conexión.

## TRACK-03 Canal WSS y autorización continua

Usa `wss://` en despliegue, con TLS válido y autenticación antes de entregar información protegida. Los usuarios conservan JWT y comprobación de sesión/permisos Redis. El navegador puede obtener mediante el portal autorizado una credencial efímera de alcance limitado; el cliente nativo usa un mecanismo compatible documentado. Nunca incluyas tokens duraderos en URL, logs, rutas de mosaicos o mensajes de diagnóstico.

Para un GPS/puente sin usuario interactivo define identidad de dispositivo revocable y permisos mínimos de publicación; no le entregues credenciales de administrador ni dependas de una sesión personal indefinida. Su autorización en Redis no permite consultar expedientes ni otros traslados.

Autoriza cada publicación/suscripción y vuelve a comprobar permiso vigente antes de entregar posiciones protegidas. Cierra o suspende el canal ante expiración, revocación, logout, reasignación o indisponibilidad de la autorización. No basta autenticar el handshake y dejar una suscripción indefinida con permisos antiguos.

Permite al transportista ver/publicar solo su tarea vigente; coordinación y personal institucional ven únicamente los traslados de su ámbito y necesidad funcional. El donante no accede al mapa operativo. Aplica lista permitida de orígenes del navegador y reglas explícitas para clientes nativos/dispositivos; Origin no sustituye autenticación.

Establece límites de conexiones, suscripciones, frecuencia/tamaño de mensajes, timeout de autenticación e inactividad. Protege XML frente a XXE/DTD. Registra conexiones, accesos/rechazos y errores minimizados, sin almacenar posiciones completas en logs generales.

## TRACK-04 Persistencia orden y recuperación

Define almacenamiento durable del historial en MongoDB u otro propietario persistente justificado, referencias/asignaciones transaccionales en PostgreSQL y última posición/canales temporales en Redis con TTL. La posición en Redis no es la única copia del historial que se deba conservar.

El ID de evento y la identidad del origen permiten deduplicar reenvíos. Las posiciones atrasadas no hacen retroceder el marcador actual. Define un cursor de servidor para la recuperación del flujo; no asumas que la secuencia de un dispositivo sirve para ordenar todas las fuentes. Conserva fechas de captura y recepción, fuente y calidad para distinguir telemetría tardía.

Define cuándo se reconoce `RECIBIDO` y cuándo `PERSISTIDO`, o estados equivalentes. No reconozcas persistencia durable si solo hay un mensaje en memoria o un caché temporal. Si una dependencia necesaria falla, devuelve el estado real y conserva/reintenta únicamente según el mecanismo durable definido.

Al reconectar, el cliente obtiene instantánea de última posición y eventos desde cursor con autorización actual. Resuelve la carrera entre instantánea y suscripción y deduplica por evento/cursor. Si el cursor expiró, indica resincronización y recuperación histórica autorizada; no inventes puntos perdidos.

Usa heartbeat, reconexión con espera progresiva y variación, ventanas acotadas y control de consumidores lentos. El mecanismo entre réplicas puede reutilizar Redis, pero si usa Pub/Sub efímero debe recuperar los huecos desde historial durable: no lo presentes como cola persistente.

## TRACK-05 Mapa actual de Nuevo León

Implementa un **mapa interactivo con cartografía vigente al implementar**, centrado y ajustable a la extensión de Nuevo León; no una imagen estática ni un dibujo generado. Debe permitir zoom/desplazamiento y detalle de calles/localidades suficiente para visualizar los traslados, tanto en Monterrey y su zona metropolitana como en el resto del estado.

Selecciona y documenta proveedor/SDK y estilo/capas con cobertura real, términos, atribución, conectividad y costes. Usa una fuente territorial oficial vigente, por ejemplo el producto de INEGI que corresponda, si incluyes límites estatales/municipales. Verifica acceso/licencia/versiones al implementar; no asumas que cualquier visor oficial ofrece una API reutilizable ni que un mapa base trae todos los hospitales.

Registra proveedor, versión o fecha de actualización publicada y fecha de consulta; si el proveedor no expone actualización exacta, declara ese límite. Un mapa reciente no garantiza precisión absoluta, tráfico en vivo ni una ETA real. La ruta planificada, el trayecto observado y una estimación de llegada se representan por separado.

Usa una capa de datos propia para posiciones y marcadores de origen/destino/instituciones autorizadas. No envíes expedientes, IDs privados, tokens ni historial GPS a un proveedor cartográfico innecesariamente. Evalúa qué información revelan las solicitudes de mapas y documenta el tratamiento apropiado.

Si eliges datos/mosaicos basados en OpenStreetMap, respeta atribución, identificación y políticas del proveedor. No presupongas que los servidores comunitarios son infraestructura ilimitada o permiten descarga masiva/offline; utiliza un proveedor o alojamiento autorizado para la carga y las capacidades requeridas. Mantén el proveedor configurable.

Una posición fuera de Nuevo León no se descarta silenciosamente ni se corrige para encajar en el mapa: conserva el hecho y muestra aviso/encuadre según el traslado y las reglas de acceso. La región geográfica visible no concede permisos sobre los transportistas que aparezcan allí.

## TRACK-06 Presentación del seguimiento

En web y escritorio, incorpora mapa de coordinación con selección/filtros de traslados autorizados. En Android, muestra tarea propia y las vistas operativas permitidas. Todos actualizan marcador y recorrido por mensajes WSS, sin exigir recargar la pantalla ni sustituir silenciosamente WebSockets por polling.

Muestra última ubicación, hora de captura, antigüedad, precisión disponible, fuente y estado: en vivo, sin fijación GPS, retrasado, desconectado, pendiente de sincronización o finalizado. Define frecuencia de envío y umbral de antigüedad como parámetros operativos justificados, no como reglas clínicas.

No animes ni extrapoles el marcador como si fueran mediciones reales cuando no llegan puntos. Diferencia visualmente datos del simulador y del GPS físico/teléfono. Conserva una alternativa accesible de texto/lista con posición/estado cuando la cartografía no esté disponible, sin presentar esa alternativa como mapa funcionando.

En PySide6 no sustituyas la aplicación por el portal. El componente de mapa puede usar un SDK o renderizador embebido justificado; si emplea motor web, recibe únicamente la geometría ya autorizada mediante puente local, con red/recursos controlados. El cliente de negocio y WebSocket de escritorio mantiene XML/XSD; no introduces consumo JSON de microservicios dentro del mapa para eludir esa restricción.

## TRACK-07 Captura y privacidad

Activa el rastreo solo durante la asignación y periodo autorizados. Al finalizar, revocar o reasignar la tarea, detén captura/publicación de esa tarea y las suscripciones correspondientes. El historial se conserva según política, separado de la visualización en vivo.

Android respeta permisos del sistema y seguimiento visible cuando corresponda. Si la fuente es un GPS externo autónomo, logout del teléfono no apaga físicamente ese equipo: el backend debe cerrar la autorización de la tarea/dispositivo cuando proceda. No mantengas rastreo personal ilimitado fuera de servicio.

Minimiza identidad en el mapa, limita la consulta histórica, define retención/eliminación por finalidad y protege localmente los lotes pendientes. Las lecturas recuperadas offline se etiquetan con su hora real y no aparecen como posición actual. El rastreo no confirma recolección, entrega o custodia por el solo hecho de llegar a unas coordenadas.

## TRACK-08 Simulador y GPS físico pendiente

Entrega un simulador ejecutable con credenciales de dispositivo de prueba y trayectorias sintéticas configurables dentro de Nuevo León, incluyendo Monterrey, su zona metropolitana y un recorrido fuera de ella. Envía por el mismo receptor/normalización, autorización y persistencia que utilizará el adaptador físico; la distribución a clientes debe utilizar conexiones WebSocket reales.

Incluye inicio/parada, intervalo configurable, identificador de traslado, semilla/archivo de puntos y escenarios de señal perdida, retrasos, duplicados, desorden y reconexión. No escribas directamente en bases ni muevas el marcador con un temporizador que evite el backend. Etiqueta cada evento y pantalla como simulación cuando corresponda.

Demuestra el circuito fuente sintética, ingreso, validación, persistencia, WSS y mapa. La aceptación física posterior debe probar decodificación real, precisión reportada, conectividad, energía, pérdida de señal y revocación del equipo elegido. Hasta entonces la conclusión es «software integrado con simulador; GPS físico pendiente», nunca «GPS físico probado».

## TRACK-09 Continuidad y monitorización

Configura gateway para upgrade WebSocket, TLS, timeouts y drenaje/reconexión al actualizar una réplica. Evalúa afinidad solo si el framework/protocolo la exige y documenta el motivo. Un socket ya abierto no migra automáticamente de proceso: el cliente debe reconectar y recuperar su cursor.

Monitoriza conexiones, autenticación fallida, frecuencia de puntos, último dato por tarea, latencia captura/recepción/mapa, rezago de persistencia, colas/buffers y reconexiones. Separa pérdida de señal GPS, falta de datos del emisor, corte WSS, caída de autorización/persistencia y error de cartografía.

Prueba caída de una réplica y caída total del rastreo, de Redis, PostgreSQL y MongoDB, además de indisponibilidad del proveedor del mapa. El cliente informa último dato y degradación sin inventar continuidad. No omitas controles que dependan de un almacén caído para mantener puntos fluyendo; el resto del negocio conserva el comportamiento acordado para sus dependencias.

## TRACK-10 Pruebas y cierre

- Posiciones válidas aparecen en el mapa de Nuevo León por WSS sin recargar, con mismo evento/traslado y permisos en web, Android JSON y escritorio XML/XSD.
- Se rechazan emisor no asignado, suscriptor de otra institución/traslado, donante, credenciales expiradas/revocadas, origen web no permitido y mensaje inválido o excesivo; no se filtran datos antes de autenticar.
- Duplicados/desorden no corrompen historial ni posición actual. La reconexión desde cursor recupera los huecos permitidos y detecta cursor caducado, con límites de memoria y consumo.
- Se distinguen sin señal, dato antiguo, cartografía caída y WSS caído; una medición atrasada no aparece como tiempo real.
- Reasignación, cierre y revocación dejan de entregar posiciones a quien perdió permiso. Datos offline no confirman eventos de negocio.
- Se verifica mapa con cobertura estatal y detalle local, atribución visible, procedencia/actualización documentadas y proveedor configurable; no se afirma tráfico/ETA real sin su fuente.
- Se mide frecuencia, latencia extremo a extremo y comportamiento con emisores/suscriptores concurrentes y consumidores lentos en entorno aislado. El polling no cuenta como prueba de WebSockets.
- Se entrega simulador, adaptador/contrato del GPS futuro, manual, ejemplos JSON/XML, diagrama de flujo y evidencia real de conexiones/capturas con datos ficticios. La prueba con hardware queda identificada hasta disponer de él.

Relaciona TRACK-01 a TRACK-10 con la matriz BE-08/BE-12/BE-23 y las etapas consumidoras. No cierres el software de rastreo con un diseño sin ejecutar ni el hardware con una simulación. Actualiza `PROJECT_STATUS.md` al implementar y probar, conservando fuentes/fechas de la cartografía y los límites del entorno.

## Fuentes técnicas para la implementación

- [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html): transporte seguro, autenticación, autorización y límites de conexiones/mensajes. Consultada el 27 de octubre de 2026; vuelve a verificarla al implementar.
- [Política de mosaicos de OpenStreetMap Foundation](https://operations.osmfoundation.org/policies/tiles/): condiciones del servicio comunitario si se elige ese proveedor. Consultada el 27 de octubre de 2026; no sustituye la revisión de otro proveedor elegido.
