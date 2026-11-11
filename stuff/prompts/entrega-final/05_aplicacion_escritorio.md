# Construir la consola de escritorio con PySide6 y Python

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Implementa una aplicación nativa en `apps/desktop/` con **PySide6 y Python**, decisión confirmada por el usuario. Su función es la operación interna de banco y coordinación regional. No entregues una WebView, un navegador empaquetado ni una copia de las pantallas web.

Lee también las [instrucciones compartidas de diseño UI/UX](../instrucciones_diseno_ui_ux.md), especialmente su sección de etapa 05, y la [corrección de calidad visual web/móvil](../corregir_calidad_visual_web_movil.md). Aplica sus reglas de identidad, vocabulario, componentes y estados a la consola nativa. Esta lectura no encarga otro rediseño de web/móvil ni traslada su navegación a Qt.

## Preparación y continuidad

Antes de construir pantallas, completa la matriz DESK-01 a DESK-14 con rol/ámbito, tarea, servicio propietario, operación, contrato XML/XSD/DTO vigente, prueba disponible y dependencia pendiente. Distingue contrato existente comprobado, extensión necesaria y comprobación externa. Si falta una capacidad, documenta la carencia y completa la extensión mínima en su propietario antes de conectar la interfaz; conserva compatibilidad, permisos y regresión proporcional. No deduzcas disponibilidad por existir una pantalla web o una respuesta de ejemplo.

Consulta la [continuidad de las etapas 01–04](07_integracion_pruebas_y_rendimiento.md#continuidad-obligatoria-de-las-etapas-01-a-04). Al ejecutar, abre o actualiza `documentation/entrega-final/continuidad/Matriz.md` con las dependencias CONT que afecten a DESK. Conserva sus evidencias y atribuye cada dependencia a los módulos afectados; no reejecutes etapas completas ni declares resueltos sus pendientes por construir escritorio. La falta de una prueba móvil física, proveedor o periférico no impide desarrollar y comprobar las partes independientes de 05. Registra lo que falta y conserva abierto el criterio afectado hasta verificarlo.

Identifica al inicio el sistema operativo y arquitectura de la demostración, su forma de instalación y los periféricos disponibles: lector e impresora, si aplican. Usa las decisiones vigentes del proyecto. Si falta una decisión, prepara una propuesta concreta con el entorno disponible, artefacto previsto, alcance comprobable y decisión pendiente; continúa el trabajo independiente sin atribuir soporte a plataformas no verificadas. Registra las condiciones de la prueba visual y del empaquetado antes de realizarlas.

## Arquitectura y contratos XML

Inspecciona API v1, ejemplos XML, XSD y DTO por operación de los prompts 01 y 02. La aplicación usa exclusivamente XML para autenticación, MFA, renovación, negocio, sincronización y errores, mediante HTTPS y JWT. Consume al menos cuatro microservicios reales y documenta una matriz módulo/servicio/operación/permiso.

Define capas de widgets/modelos de Qt, casos de uso de interfaz, cliente HTTP XML, validadores y almacenamiento seguro local. Evita llamadas de red en el hilo de interfaz; usa workers/señales o mecanismo compatible documentado, con cancelación, progreso y timeout.

Usa `Accept: application/xml` y el `Content-Type` correspondiente. Construye XML con biblioteca segura y escape, valida solicitudes/respuestas/errores con XSD y el DTO específico de la operación. Reutiliza esquemas versionados distribuidos con la aplicación o recuperados por un mecanismo confiable; no descargues e invoques esquemas arbitrarios indicados por el documento recibido.

Deshabilita DTD, entidades externas y red del parser; limita tamaño/profundidad/nodos. Una respuesta JSON inesperada, XML malformado, DTO equivocado o versión incompatible produce error de contrato seguro. No conviertas un fallo de validación en éxito parcial.

No importes módulos backend para ejecutar reglas ni incluyas controladores/credenciales de PostgreSQL, MongoDB o Redis. Los archivos binarios y reportes pueden transferirse mediante enlaces privados autorizados por contratos XML, conservando validación TLS y estado de descarga.

## Sesión y permisos

Login, MFA para perfiles críticos, renovación rotativa coordinada, consulta de perfil, registro/revocación de dispositivo cuando corresponda y logout con limpieza local. Guarda secretos mediante el almacén seguro del sistema operativo; si no está disponible, informa y utiliza una sesión en memoria o alternativa cifrada justificada, nunca texto plano.

Reautentica acciones críticas según el contrato de servidor, con desafío de un uso y alcance de operación/recurso. Ningún usuario obtiene privilegios por cambiar la interfaz, editar un XML o modificar un identificador. Bloquea acciones mientras se renueva/cierra la sesión sin duplicar comandos.

El perfil Operador no dicta compatibilidad ni libera clínicamente. El Coordinador no adquiere facultades médicas. Médico, administrador y auditor acceden solo a módulos y acciones expresamente autorizados. La visibilidad y el permiso de ejecución se comprueban también en servidor.

## Módulos obligatorios

| ID | Módulo | Funciones específicas |
| --- | --- | --- |
| DESK-01 | Panel regional | Inventario por institución/recurso, solicitudes, próximos a vencer, traslados y alertas; filtros de periodo y región, datos agregados y navegación a recursos autorizados. |
| DESK-02 | Administración institucional | Instituciones/sedes/capacidades y documentos, usuarios/perfiles/permisos dentro del ámbito autorizado, dispositivos y registro de cambios. No acceso clínico general por administrar cuentas. |
| DESK-03 | Inventario avanzado | Tabla con búsqueda/orden/filtros/paginación del servidor; alta y edición permitida de unidad, producto, grupo, ubicación, fechas y procedencia; cuarentena, liberación por médico, movimientos e historial. |
| DESK-04 | Donación y laboratorio | Captura detallada de colecta/procesamiento/derivados, muestras, resultados, documentos, corrección versionada y revisión profesional. Lista de trabajo con pendientes e información faltante. |
| DESK-05 | Receptores y solicitudes | Consulta/captura autorizada, tipo de recurso, necesidades, urgencia documentada, estados, versiones, historia y restricciones de retenciones/reservas. |
| DESK-06 | Compatibilidad | Resultados ABO/Rh y HLA, perfil de completitud, exclusiones, datos/fuentes/versiones, límites e historial de evaluaciones. Dictamen solo por profesional autorizado y con motivo. |
| DESK-07 | Logística y cobertura | Comparar candidatos, distancia/tiempo/procedencia y factores, consultar propuestas de balanceo y explicar diferencias entre propuesta, prioridad operativa y autorización clínica. |
| DESK-08 | Reservas y asignaciones | Aprobación humana autorizada, confirmar/cancelar cuando proceda, vigencia, concurrencia, consulta/reanudación de operaciones y rechazo de datos obsoletos. Órganos requieren referencias del procedimiento oficial. |
| DESK-09 | Transporte y custodia | Planificar/asignar, tareas y secuencia, origen/destino, responsables, incidencias, evidencia, recepción y mapa autorizado. Reconstruir transferencias y verificar integridad sin alterar historia. |
| DESK-10 | Caducidad y frío | Lecturas/condiciones por recurso, perfiles y procedencia, excursiones, alertas, cuarentenas/bloqueos, revisión y destino final. No fijar umbrales clínicos arbitrarios en cliente. |
| DESK-11 | Uso y trazabilidad | Reconstruir donación a unidad/derivados, pruebas, suministro y recepción hasta uso/devolución/descarte u otro destino autorizado; registrar cierres pertinentes por rol y pendientes documentales. |
| DESK-12 | Reportes y analítica | Tablas y gráficas nativas de inventario/demanda/caducidad/tiempos, filtros coherentes, PDF/CSV/XLSX, seguimiento de trabajos y exportación minimizada. |
| DESK-13 | Etiquetas e impresión | Plantilla de unidad/bolsa/muestra según identificadores y aprobación disponible, QR/código de barras, vista previa, impresión individual/lote y reimpresión con motivo/auditoría. Sin datos personales innecesarios. |
| DESK-14 | Auditoría y alertas | Historial de accesos/cambios/decisiones, búsquedas por correlación/recurso, consulta/exportación restringida, avisos y reconocimiento/escalamiento; integrar hallazgos existentes sin editar eventos. |

Las gráficas de escritorio pueden usar componentes nativos compatibles con PySide6; Highcharts permanece obligatorio en web. No añadas un motor web solo para copiar el dashboard existente.

## Mapa regional y rastreo por WebSockets

Implementa la [especificación de rastreo GPS y mapa de Nuevo León](09_rastreo_gps_websockets.md) dentro del módulo DESK-09 y las vistas autorizadas de coordinación. Muestra mapa interactivo actual de Nuevo León, traslados permitidos, origen/destino, última posición y recorrido por **WSS**, con estados de señal/antigüedad y recuperación desde cursor. Autenticación, suscripción, posiciones, estados y errores del socket conservan **XML/XSD**; no abras un consumidor JSON de microservicios dentro de la capa cartográfica.

El componente de mapa puede emplear un SDK o renderizador embebido justificado, sin convertir la aplicación en copia del portal. La interfaz continúa nativa y el módulo XML valida/autoriza los datos antes de pasarlos al renderizador local. Verifica permisos por traslado, revocación, caída del socket/proveedor y actualización sin recarga. Prueba con el simulador del backend y registra aparte la integración física comprobada y la que permanezca pendiente.

## Operación intensiva y experiencia

Define componentes nativos comunes antes de extender los catorce módulos: navegación por tarea y rol, tabla y acciones de fila, filtros, formulario, detalle, mensajes y progreso. Conserva la marca y los colores semánticos compartidos. Adapta densidad y jerarquía al trabajo de escritorio; evita una pantalla genérica que imprima todos los campos del contrato, UUID dominantes o cadenas de diálogos para consultar información relacionada. Distingue selección, apertura de detalle y escritura de negocio. Las acciones por icono deben tener nombre accesible, ayuda y operación por teclado; aplica un patrón consistente a todas las tablas.

- Ventana principal con institución/rol/sesión, navegación por módulos y área de trabajo; tablas Qt apropiadas para volumen, selección y atajos de teclado.
- Formularios con validación, errores por campo, datos conservados y confirmación contextual de operaciones irreversibles. Evita mostrar códigos internos al personal operativo cuando no ayuden a corregir un problema.
- Consultas paginadas por servidor; no descargues todo un expediente regional para filtrar localmente. Separa permisos de consulta, exportación, impresión y modificación.
- Edición con versión base, rechazo de conflicto y comparación/recarga antes de reintentar. No sobrescribas cambios ajenos ni repitas comandos con claves nuevas tras timeout.
- Historial visual de operaciones con fecha, acción, resultado y recuperación, limitado al ámbito del usuario; no registra secretos ni XML clínico completo en archivos de diagnóstico.
- Descargas y exportaciones con progreso, destino escogido, confirmación de sobrescritura, hash cuando aplique y limpieza de temporales. Protege CSV/XLSX contra fórmulas y reautoriza trabajos privados.
- Lectura de códigos mediante lector de teclado y entrada manual controlada; cámara opcional según hardware. Verifica el recurso en servidor, no solo el formato del código.
- Etiquetas verificables al volver a escanear; la vista previa/PDF prueba generación, y la impresión física solo se declara probada cuando se ejecutó en una impresora identificada.

## Desconexión y recuperación

Indica conectividad y antigüedad de datos. Permite borradores/observaciones expresamente autorizados, cifrados y separados por usuario/institución. No confirma liberación, dictamen, asignación, reserva ni custodia durante desconexión.

Utiliza el protocolo de sincronización del backend para comandos permitidos: ID e idempotencia persistentes, versión base, estado pendiente y resultado consultable. Prueba reinicio de la aplicación, pérdida de respuesta, reintentos, conflicto, sesión expirada y cambio de usuario. Los comandos se reautorizan antes de aplicar; no se envían bajo la siguiente cuenta que inicia sesión.

Comprueba primero qué permite ese protocolo. En la base revisada el 11/11/2026, `apps/services/ms_transporte/synchronization.py` admite `TRANSPORT_OBSERVATION` vinculada a traslado/dispositivo y restringe sus comandos/resultados a `TRANSPORT`; el registro de dispositivos existente identifica fuentes GPS. Esto no acredita sincronización para borradores de operador, médico o coordinador. Revalida el código vigente y define por cada borrador permitido su contenido, rol, propietario, operación y reglas de conflicto/retención. Si necesita ampliación, impleméntala de forma compatible y con permisos de servidor explícitos para esa operación; no amplíes permisos de transporte indiscriminadamente ni registres una consola como Android/GPS para sortear el contrato. Un borrador guardado localmente debe seguir identificado como local hasta confirmar su operación real; no demuestra sincronización terminada.

## Instalación y entrega

Entrega entorno/dependencias reproducibles, punto de entrada, configuración HTTPS sin secretos, icono, versión, manual y paquete ejecutable para la plataforma de demostración identificada. Incluye scripts/CI de empaquetado para los sistemas objetivo documentados y las condiciones de firma/distribución; no afirmes compatibilidad Windows/macOS/Linux sin prueba en cada uno.

Comprueba arranque desde instalación limpia sin herramientas de desarrollo del repositorio, persistencia segura de configuración y limpieza de sesión. El instalador no incorpora bases, credenciales de servicio ni datos clínicos. No publica ni instala en equipos de terceros sin autorización.

## Pruebas y aceptación

Prueba validación XSD de login/refresh/MFA, consultas, comandos y errores; rechazo XXE, XML grande/incorrecto, JSON inesperado, token revocado, permisos y acceso horizontal por ID. Verifica que todo intercambio de negocio sea XML y que al menos cuatro servicios reales participen.

Ejecuta recorridos GUI reales con PySide6: operador registra/localiza unidad y muestra etiqueta, médico revisa y reserva, coordinador programa traslado, operador recibe, auditor reconstruye historia. Comprueba filtros/paginación, exportaciones, conflictos concurrentes y recuperación de escritura incierta.

Antes de implementar cada familia de pantallas, registra sus tareas y criterios visuales de aceptación. Cubre todos los módulos y roles aplicables, incluida administración; una captura del panel o una tabla reutilizada no verifica sus variantes. Comprueba:

- Jerarquía, términos y acciones coherentes entre tablas, formularios, detalles, paneles, trazabilidad, mapa y etiquetas; sin ayudas técnicas redundantes ni controles pegados a los bordes.
- Recorridos autenticados por teclado, foco visible y orden lógico; selección y apertura nunca ejecutan una operación de negocio. Documenta pasos, retrocesos y cambios de contexto para las tareas elegidas, sin imponer un número universal de clics.
- Redimensionado y escalado normal/ampliado del sistema realmente probado, con valores registrados: contenido legible, controles alcanzables y formularios sin recortes ni pérdida de datos.
- Carga, vacío, error por campo, falta de permiso, desconexión, conflicto y resultado incierto con mensajes y recuperación correspondientes al estado real. Las tareas largas mantienen la ventana utilizable; no muestran porcentajes o cancelaciones no confirmados.
- Evidencia visual y funcional por familia/rol, con entorno, tarea, esperado, obtenido y pendientes. No declares aceptada una variante solo porque compila, responde la API o se ejecutó otra pantalla del mismo componente.

Integra un flujo iniciado por móvil Android/iOS JSON y consultado/continuado por escritorio XML con mismos IDs, estado/versiones y permisos, visible también en web. Captura evidencia de interfaz y persistencia, pruebas automáticas relevantes y procedimiento reproducible. Actualiza matriz DESK-01 a DESK-14, manuales y `PROJECT_STATUS.md`.

## Alcance móvil actualizado — 6 de noviembre de 2026

Comprueba el mismo contrato de seguimiento XML/XSD con posiciones producidas por el móvil Android y por iOS. La integración con esos clientes se acepta en 07; conserva backend y simulador existentes.
