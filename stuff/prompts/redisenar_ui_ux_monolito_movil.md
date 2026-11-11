# Prompt: rediseñar UI/UX del monolito y móvil de Red House

**Modelo destinatario:** GPT-6 Astra, razonamiento high.

**Documento complementario obligatorio:** [Instrucciones de diseño UI/UX](instrucciones_diseno_ui_ux.md).

Este es un encargo para una ejecución futura. Su preparación solo crea este archivo y el documento complementario; no implementa cambios de interfaz.

---

Actúa como especialista en diseño de producto, UX y accesibilidad con capacidad de implementar cambios de presentación. Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`.

Rediseña la interfaz del monolito y la aplicación móvil existente para lograr una experiencia coherente, clara y profesional. Conserva la identidad de Red House definida por el monolito. Acerca el móvil a esa identidad mediante componentes nativos y una organización adecuada al teléfono.

No reduzcas el trabajo a cambiar colores, alinear píxeles o producir una maqueta. Debes resolver jerarquía, navegación, lenguaje, esfuerzo de interacción, densidad, estados y consistencia. El alcance es **exclusivamente UI/UX sobre funcionalidades existentes**.

## 1. Lectura inicial y contexto vigente

Lee `AGENTS.md`, `PROJECT_STATUS.md`, las [instrucciones de diseño](instrucciones_diseno_ui_ux.md), los README de [web](../../apps/web/README.md) y [móvil](../../apps/mobile/README.md), y los encargos [03](entrega-final/03_portal_web.md), [04](entrega-final/04_aplicacion_android.md) y [05](entrega-final/05_aplicacion_escritorio.md). Los encargos funcionales aportan contexto, no amplían este rediseño.

Inspecciona el estado de Git antes de editar. Conserva cambios previos, archivos sin seguimiento y evidencias. Si existe `.codegraph/`, usa CodeGraph antes de localizar o comprender código. No crees ni reconstruyas el índice CodeGraph. No reescribas la arquitectura; compila con las herramientas existentes cuando corresponda.

Hechos comprobados al preparar este prompt, el 10/11/2026:

- Monolito Flask/Jinja2, con recursos de presentación en `apps/web/src/presentation/`.
- Móvil Kotlin/Compose Multiplatform en `apps/mobile/`, con UI compartida Android/iOS. La compilación Android inspeccionada fue 0.3.1, código 3.
- La compilación móvil normal ya incorpora el gateway y no lo pide al usuario. El campo editable pertenece al laboratorio; no lo declares un defecto vigente del producto normal.
- La etapa 05 establece Python/PySide6 en `apps/desktop/`. No elijas otra tecnología ni desarrolles escritorio durante este encargo.
- La aceptación integral de móvil y otros pendientes se consulta en `PROJECT_STATUS.md`. El acabado visual no los convierte en terminados.

Revalida estos hechos al ejecutar el prompt: el repositorio puede haber cambiado.

## 2. Límite estricto de cambios

### Permitido

- Ajustar CSS, Jinja/HTML de presentación, iconografía y recursos visuales existentes.
- Reorganizar navegación, contenido, componentes y jerarquía sin retirar destinos o acciones autorizados.
- Mejorar etiquetas, ayudas, traducciones de estados, formato visible y mensajes sin cambiar su significado.
- Ajustar JavaScript exclusivamente de interacción visual, foco, accesibilidad y presentación.
- Refactorizar componentes Compose, tema, navegación visual y formato de datos en la capa de UI.
- Crear pruebas de presentación o adaptar pruebas de UI cuando la mejora lo requiera, preservando sus comprobaciones funcionales.
- Ajustar metadatos exclusivamente presentacionales fuera de esas carpetas solo si es imprescindible y su alcance está aislado y explicado.

### Prohibido

- Editar `apps/services/**`, microservicios, esquemas, migraciones, contratos, OpenAPI, JSON/XML/XSD o WebSockets.
- Cambiar reglas clínicas, algoritmos, prioridades, validadores de negocio, estados, transiciones o significado de resultados.
- Cambiar autenticación, MFA, JWT, autorización, segregación institucional, sesiones, revocación, auditoría, idempotencia, reintentos o protocolos offline.
- Modificar repositorios de datos, clientes HTTP, DTO, serialización contractual, workers, captura GPS/QR/cámara o adaptadores nativos para acomodar el diseño.
- Añadir endpoints, permisos, campos de negocio, funciones, dependencias de infraestructura, migraciones o registros de relleno.
- Completar carencias funcionales pendientes de 04, desarrollar 05, desplegar GCP, publicar paquetes o cambiar datos productivos.
- Desactivar protecciones como `FLAG_SECURE`, TLS, permisos del sistema o limpieza de credenciales para obtener capturas o facilitar pruebas.
- Reemplazar tecnologías, reescribir el monolito, introducir una WebView o convertir el encargo en una renovación arquitectónica.

**Ejemplo de excepción presentacional:** el catálogo `NAV` vive en `apps/web/src/integration/__init__.py`. Puede cambiar su orden, agrupación y texto visible si se conserva cada ruta y filtro de autorización. No modificar el resto del archivo por cercanía. Si un cambio no puede aislarse de lógica funcional, déjalo fuera del encargo y documenta el límite.

**Ejemplo de formato:** un selector de fecha puede entregar exactamente el valor que ya acepta el formulario. No se cambian el contrato, la zona, los límites temporales ni la validación para que acepte otro formato.

**Ejemplo de dato faltante:** si la UI solo recibe un identificador, usa un nombre ya disponible y autorizado o conserva la referencia con ayuda. No añadas servicios, consultas privilegiadas, catálogos ficticios o nuevas capacidades de backend.

## 3. Evidencia inicial: qué se revisó realmente

Usa esta revisión como punto de partida, no como sustituto de recorrer la versión que vayas a modificar.

| Evidencia | Alcance y límites |
| --- | --- |
| Chrome, 10/11/2026, portal publicado `https://34.18.186.116` | Portada y acceso respondieron 200. Se observaron capturas reales a 1440 px y acceso a 390 px. No se inició sesión ni se escribieron datos de negocio. |
| Android 0.3.1 en AOSP API 30 x86_64, 10/11/2026 | Se abrió el APK existente en un emulador temporal. Se leyó la jerarquía accesible del acceso. Se comprobaron textos y controles reales, no recorridos autenticados. |
| Protección Android | `FLAG_SECURE` impidió obtener una captura directa de la aplicación. No se desactivó. El aspecto posterior al login se analizó en fuente, no se presenta como inspección visual nueva. |
| Capturas del portal privado, 06/11/2026 | Se revisaron horarios, reserva pendiente, laboratorio y mapa, entre otras. Son evidencia histórica, apoyada por las fuentes actuales; no una sesión privada ejecutada de nuevo. |
| Código actual | Plantillas, CSS, navegación, componentes Compose y documentos de operación. Las fricciones derivadas del código se distinguen de lo observado en pantalla. |

Las capturas nuevas y las jerarquías de esta preparación quedaron como artefactos temporales fuera del repositorio en `/private/tmp/redhouse-uiux-review/`. No son una dependencia del encargo ni un expediente permanente. Si ya no existen, reproduce la observación; no inventes imágenes ni resultados.

Referencias históricas persistentes:

- [Horarios en escritorio](../../documentation/evidencias/gcp/portal03-20261106/layout/1440.png).
- [Horarios en pantalla estrecha](../../documentation/evidencias/gcp/portal03-20261106/browser-final3/horario-390.png).
- [Mapa publicado](../../documentation/evidencias/gcp/portal03-20261106/browser-final3/mapa-gateway.png).
- [Reserva pendiente del monolito](../../documentation/evidencias/entrega-final/portal/correccion-20261106/final-monolith3/browser/correcciones-operativas-monolith/reserva-pendiente.png).
- [Laboratorio del monolito](../../documentation/evidencias/entrega-final/portal/correccion-20261106/final-monolith3/browser/correcciones-operativas-monolith/laboratorio-corregido.png).

## 4. Hallazgos que debes revalidar y resolver

La prioridad indica riesgo de comprensión y esfuerzo, no una auditoría clínica. No atribuyas al usuario una confusión medida cuando solo existe una hipótesis de diseño.

| ID | Hallazgo y evidencia | Dirección de mejora |
| --- | --- | --- |
| U01 · Alta | La captura de reserva pendiente muestra un check junto a «Operación pendiente de confirmación». `base.html` usa `circle-check` para todos los flashes. | Diferenciar icono, tono y jerarquía según estado. Conservar incertidumbre y recuperación existente. |
| U02 · Alta | Laboratorio muestra `AUTHORIZED`, `CORRECTED`, `NOT_CHECKED`, «Entries» y referencias extensas. Evidencia histórica y plantillas genéricas. | Etiquetas por contexto y español consistente. Nunca equiparar autorización documental con aprobación clínica. |
| U03 · Alta | `App.kt` dispone encabezado, conexión, identidad, navegación, contenido y cuenta en una `Column` desplazable. | Crear estructura de pantalla y navegación estable por rol; que el contenido seleccionado aparezca donde se espera. |
| U04 · Alta | `App.kt` representa campos JSON con sus nombres, roles crudos, UUID institucional y rutas en recuperación de operaciones. Hallazgo de fuente. | Presentación específica por recurso, lenguaje humano y referencias secundarias accesibles. |
| U05 · Media | La navegación web repite «GENERAL», «BANCO DE SANGRE» y «LOGÍSTICA» en bloques separados. Fuente `NAV` y capturas. | Agrupar una sola vez y ordenar según trabajo del perfil, sin cambiar permisos ni retirar módulos. |
| U06 · Media | Horarios por sede muestra una fila rodeada de actualizar, exportar, recuento y dos paginadores. | Reducir contenedores y controles redundantes según resultados; mantener exportación, recuento y paginación real. |
| U07 · Media | En esa pantalla, la acción destacada es «Crear campaña», aunque el contenido son horarios. | Reubicar o reducir su prominencia. No renombrar la acción como si creara un horario. |
| U08 · Media | Vista rápida web seguida de «Abrir expediente completo» puede añadir un paso antes de trabajar. Hallazgo de fuente. | Dar acceso directo claro al expediente existente cuando la tarea lo requiera, conservando la vista rápida útil. |
| U09 · Media | `dashboard.html` sitúa filtros y gráficas antes de accesos de trabajo; pide fechas ISO con zona. | Priorizar tareas del perfil y hacer comprensibles los controles. Mantener Highcharts y toda semántica de periodos. |
| U10 · Media | Acceso web repite «¿Necesitas recuperar tu acceso?» como enlace y desplegable. La captura nueva muestra el desplegable azul poco distinguible sobre fondo oscuro. | Diferenciar recuperación de ayuda institucional y medir contraste. No afirmar incumplimiento numérico sin medirlo. |
| U11 · Media | El acceso Android real dice «Red: disponible; cada servicio se comprueba al consultar», «Usuario» y «Código MFA, si corresponde». | Unificar vocabulario con web y reducir el peso de explicación técnica sin afirmar que todos los servicios funcionan. |
| U12 · Media | Tema móvil con solo `primary = #a01832`; marca como texto. Fuente `App.kt`. | Tema completo derivado del monolito y marca existente, conservando controles nativos. |
| U13 · Alta | Agenda/programación móvil presenta fechas ISO, UUID y explicaciones del servidor. Fuentes `DonorScreen.kt` y `OperationalScreens.kt`. | Entradas comprensibles, resumen de acción y nombres ya disponibles. Mantener todos los requisitos y valores enviados. |
| U14 · Media | Activar/desactivar notificaciones, recuperación y logout aparecen al pie de la estructura móvil general. | Ubicar cada control en su contexto; conservar accesibilidad y todas sus acciones. |
| U15 · Media | El mapa histórico dispersa conexión, contexto, antigüedad, origen/destino y explicaciones alrededor de una superficie grande. | Resumen operativo compacto, mapa y datos relacionados. Mantener precisión, procedencia, límites y atribución. |
| U16 · Media | La portada actual combina un bloque inicial cuidado con instituciones/campañas en listas y vacíos de tratamiento distinto. | Integrar esas secciones en el mismo lenguaje visual. No inventar publicaciones, cifras ni contenido para rellenarlas. |
| U17 · Media | Hay etiquetas/metadatos pequeños y ayudas de contraste débil en algunos fondos. Fuente CSS y acceso observado. | Medir legibilidad, contraste y zoom en el contexto real; ajustar sin imponer una alineación por píxeles. |

No diagnostiques «Próximamente» solo porque existen `.future-*` o `planned-label` en las fuentes: su presencia no prueba que aparezcan en la interfaz actual. Tampoco presentes como ausentes los filtros web con debounce, historial y conservación de foco ya implementados.

## 5. Recorridos y medición antes/después

Recorre la aplicación como usuario: enlaces, menús, selección y formularios. No sustituyas esa revisión por inspección estática ni por capturas de una única portada.

Usa cuentas y datos de prueba autorizados. Las consultas de un entorno publicado no autorizan crear citas, reservas, traslados o evidencias productivas. Ejecuta las escrituras necesarias para verificar regresión en un entorno aislado existente y autorizado. No prepares infraestructura o modifiques servicios como parte del rediseño.

| Plataforma / perfil | Recorridos representativos |
| --- | --- |
| Web pública | Portada → acceso; recuperación frente a ayuda institucional; instituciones y campañas vacías o disponibles. |
| Web / operador | Localizar unidad con filtros → detalle → formulario existente; laboratorio → resultado e historia; consultar horarios. |
| Web / médico | Solicitud → evaluación/completitud → revisión autorizada; reconocer documento corregido y dato obsoleto. |
| Web / coordinador y transporte | Consultar traslado → contexto/mapa → custodia; reconocer una reserva pendiente sin duplicarla. |
| Web / donante | Campaña → horario → cita y seguimiento; mantener consentimiento y confirmaciones. |
| Web / administración y auditoría | Navegación por ámbito, consulta de configuración/historial/reportes autorizados. |
| Móvil / donante | Acceso → expediente/campañas/horarios → cita existente o reserva en pruebas → regreso a citas. |
| Móvil / transporte | Traslados → tarea → contactos/ruta → acciones existentes de escaneo/custodia; estado de ubicación y sincronización. |
| Móvil / operador, coordinador y médico | Consultas/capturas ya disponibles, navegación al detalle, filtros y regreso al listado. |
| Ambos | Cargando, vacío, sin coincidencias, error, falta de permiso, sesión expirada, desconexión y resultado incierto donde existan. |

Puntos estructurales encontrados en código, **no mediciones nuevas con usuarios**:

- Web: fila → vista rápida → expediente completo supone dos activaciones por esa ruta, antes de otra acción.
- Móvil: Traslados → Abrir tarea y mapa → Consultar contactos y ruta supone tres activaciones si la tarea ya está disponible.
- Móvil: Horarios → Agendar este horario → Confirmar supone tres activaciones, sin contar entrada, desplazamiento, permisos ni esperas.
- Móvil tiene también una entrada a agenda desde «Expediente, consentimiento y agenda». Resolver la duplicidad conceptual conservando sus funciones.

Registra por recorrido: versión, rol, dispositivo, punto inicial, pasos, clics/toques de navegación, confirmaciones obligatorias, desplazamientos, errores/desvíos y resultado. Si no se pudo ejecutar, marca «no medido» y explica el límite. No inventes tiempo ahorrado ni uses tres clics como cuota universal.

## 6. Método de rediseño e implementación

### A. Inventariar sin alterar comportamiento

Construye una matriz pantalla/rol/acción/datos/estado. Identifica qué es presentación y qué es regla o contrato. Incluye todos los módulos visibles del monolito y las pantallas móviles existentes; no cierres la revisión solo con login y dashboard.

Reproduce los hallazgos y registra evidencias actuales con sus límites. Lee las referencias externas del documento de diseño y explica qué patrón concreto adoptas. No copies marcas ni añadas funciones por imitar una referencia.

### B. Definir una dirección coherente

Antes de acumular estilos, define paleta semántica, tipografía, jerarquía de acciones, navegación por rol, lenguaje, tratamiento de estados y patrones de formulario/lista/detalle. Aplica las instrucciones compartidas. No abras varias propuestas cosméticas sin resolver las fricciones observadas.

La web es el ancla de marca. El móvil usa su propio espacio y ergonomía. El escritorio futuro hereda las reglas semánticas mediante el documento complementario, sin implementarse ahora.

### C. Implementar por familias de interfaz

1. Tema, marca, texto y estados compartidos.
2. Estructura y navegación web/móvil; acceso y recuperación visual.
3. Listas, filtros, tablas, tarjetas, vista rápida y detalle.
4. Formularios, fechas, errores y confirmaciones.
5. Paneles por perfil, agenda, inventario, laboratorio y solicitudes.
6. Traslados, mapa, custodia, evidencia y sincronización existentes.
7. Avisos, cuenta, administración, auditoría y reportes.
8. Adaptación, accesibilidad y regresión de los recorridos afectados.

Reutiliza componentes de presentación para evitar soluciones diferentes al mismo problema. No aproveches la reorganización visual para hacer limpiezas arquitectónicas o actualizar dependencias sin necesidad demostrada.

### D. Verificar sin degradar controles

Comprueba antes/después con el mismo alcance. Los botones deben seguir llamando a la misma operación autorizada y los formularios deben conservar campos, formatos y restricciones. Una captura no prueba persistencia ni ausencia de regresiones.

Prueba web amplia y compacta —por ejemplo 1440, 768 y 390 CSS px—, además de reflow, zoom y teclado según las instrucciones. Prueba Android real o emulado con tamaño compacto, fuente aumentada, teclado y orientación. Verifica que los cambios compartidos no rompen iOS; declara aparte lo no ejecutado. No descargues SDK ni runtimes como parte de una supuesta corrección de diseño.

Ejecuta las pruebas existentes pertinentes de UI y regresión, y comprobaciones dirigidas para cambios con riesgo: navegación con permisos, mapeo de estados, fechas y confirmaciones. No escribas pruebas de colores triviales que solo repitan constantes ni elimines aserciones funcionales para hacer pasar una nueva maqueta.

Si una prueba automatizada depende de un nombre accesible cambiado, actualiza el selector por el nuevo concepto sin debilitar su comprobación. Mantén los errores de intentos anteriores y distingue fallos del entorno de fallos del producto.

## 7. Criterios de aceptación

| ID | Debe quedar demostrado |
| --- | --- |
| UX-01 | Marca y paleta reconocibles entre web y móvil; sistema de estados y acciones coherente. |
| UX-02 | Navegación web sin grupos repetidos por fragmentación; todos los destinos y permisos anteriores conservados. |
| UX-03 | Móvil con navegación y contenido diferenciados; las tareas no quedan debajo de una lista completa de controles globales. |
| UX-04 | Etiquetas, estados y fechas comprensibles; sin JSON, rutas API o enums como interfaz principal. Las referencias necesarias siguen accesibles. |
| UX-05 | Resultado incierto, error, conflicto y éxito visualmente distintos y semánticamente fieles. |
| UX-06 | Cada contenedor tiene propósito; listas pequeñas, resúmenes y vacíos reciben un tratamiento proporcionado. |
| UX-07 | Acciones contextualizadas; sin CTA engañosos, rutas conceptuales duplicadas ni pasos adicionales evitables. |
| UX-08 | Recorridos representativos medidos antes/después; no aumentan pasos redundantes sin justificación; confirmaciones críticas intactas. |
| UX-09 | Accesibilidad visual, teclado, foco, objetivos táctiles y aumento de texto comprobados en el alcance modificado. |
| UX-10 | Formularios, operaciones, permisos, contratos, resultados y recuperación preservados; regresión pertinente con evidencia. |
| UX-11 | Sin cambios en microservicios, datos de negocio, infraestructura ni implementación de escritorio. Las excepciones presentacionales están aisladas. |
| UX-12 | Hallazgos resueltos o pendientes identificados; ninguna limitación real se ocultó para aparentar un producto terminado. |

## 8. Entrega de la ejecución futura

Entrega la implementación de presentación y una explicación breve que incluya:

- Qué fricciones resolviste y cómo se aprecia la mejora al usar el producto.
- Archivos modificados y justificación de cualquier cambio fuera de las carpetas de presentación.
- Evidencia antes/después por pantalla y recorrido, indicando fecha, entorno, rol y origen real o histórico.
- Mediciones de navegación y resultados de pruebas, con sus límites; sin promesas de validación por usuarios si no participaron.
- Pendientes estrictamente visuales y problemas funcionales detectados pero dejados fuera del alcance.
- Confirmación de que las reglas compartidas siguen aplicables a 05 sin sustituir PySide6, XML/XSD ni sus criterios de aceptación.

Durante esa implementación futura, actualiza la documentación de estado exigida por el repositorio de forma proporcional, sin declarar cerradas etapas funcionales por mejorar su apariencia. **Esta instrucción no autoriza modificar `PROJECT_STATUS.md` durante la preparación actual de los dos documentos.**

No despliegues ni publiques como parte del rediseño. La entrega debe ser revisable, ejecutable y comprobada dentro del alcance de UI/UX.
