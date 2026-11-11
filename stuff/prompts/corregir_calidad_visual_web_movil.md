# Segunda revisión UI/UX: calidad visual y navegación de Red House

**Destinatario:** GPT-6 Astra, razonamiento high.

**Fecha de preparación:** 10 de noviembre de 2026.

**Alcance:** corregir la presentación del monolito y la aplicación móvil existentes, en todas las vistas y perfiles aplicables. No implementar funcionalidades ni modificar microservicios.

Este documento constituye un nuevo prompt para ejecutar posteriormente. Su preparación solo crea este Markdown: no implementa las correcciones descritas. Conserva los dos documentos anteriores como antecedentes. Para las decisiones de diseño que aquí se precisan, **aplica esta segunda revisión**, sin repetir el primer encargo ni revertir mejoras que ya funcionan.

---

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House` como diseñador de producto y desarrollador de interfaces. El usuario rechazó el resultado visual de la primera intervención. Debes resolver los problemas de composición y uso, no limitarte a demostrar que compilan las plantillas, funcionan los enlaces o coinciden los colores.

El objetivo es una interfaz institucional cuidada: información jerarquizada, controles consistentes, acciones claras, espacios proporcionados y navegación adecuada a cada dispositivo. **La aplicación móvil comparte identidad con el monolito; no comparte su estructura de página web.**

## 1. Punto de partida y evidencia disponible

Lee `AGENTS.md`, `PROJECT_STATUS.md`, [las instrucciones de diseño](instrucciones_diseno_ui_ux.md), [el prompt anterior](redisenar_ui_ux_monolito_movil.md) y [el resultado de su implementación](../../documentation/evidencias/uiux/20261110/RESULTADOS.md). Usa CodeGraph antes de comprender o localizar código si el índice existe. Conserva todos los cambios previos. No regeneres índices ni reescribas la arquitectura.

El estado del proyecto registra un incremento visual y su [publicación web](../../documentation/evidencias/gcp/uiux-20261110/RESULTADOS.md), pero **la aceptación integral del rediseño sigue pendiente**. El nuevo tema móvil ya contiene rojo `#c8102e`, azul `#1e3a5f` y superficies institucionales. No presentes como corrección pendiente algo que ya existe ni confundas ese avance con una buena composición.

### Evidencia de esta segunda revisión

| Origen | Qué se observó | Qué no acredita |
| --- | --- | --- |
| Captura 1 del usuario: Notificaciones, donante | En cada fila se apilan «Abrir expediente», un ojo en botón y «Marcar como leída». Filas muy altas para poco contenido; varias franjas de herramientas. | No permite inferir que los avisos son duplicados incorrectos ni borrar registros. |
| Captura 2: Campañas, donante | Repite el patrón de acciones heterogéneas y filas sobredimensionadas. La cabecera del listado ocupa gran espacio antes de los datos. | No prueba que todas las campañas tengan los mismos datos ni que deba retirarse la paginación. |
| Captura 3: Documentos privados, donante | Etiquetas, selects y botones pegados a los bordes; dos cajas anchas sin jerarquía de formulario. | No prueba un fallo de autorización ni permite cambiar cómo se consultan expedientes. |
| Captura 4: acceso web | Ayudas permanentes de longitud de cuenta y contraseña; texto preventivo redundante. Ayuda institucional ya tiene nombre diferenciado. | No autoriza retirar MFA, validaciones o limpieza de contraseña. |
| Captura 5: Cuenta móvil | Cabecera «Secciones/Volver», menú de seis destinos, UUID institucional, mensajes rutinarios, activar/desactivar notificaciones y logout dominante. | No acredita por sí sola el sistema operativo ni todos los recorridos de ese dispositivo. |
| Inspección del código actual | Se revisaron componentes compartidos y variantes web/móviles; las causas se describen abajo. | Una ruta encontrada en código no equivale a una pantalla revisada en ejecución. |
| Emulador Android utilizado en esta preparación | AOSP API 30 x86_64, 360×720 dp, fuente del sistema 130 %. Se instaló el APK existente, se abrió y se observó el acceso mediante la ventana del emulador y su jerarquía accesible. | No se inició una nueva sesión autenticada ni se ejecutaron operaciones de negocio. La captura autenticada móvil procede del usuario. |

El APK inspeccionado fue `apps/mobile/composeApp/build/outputs/apk/debug/composeApp-debug.apk`, SHA-256 `31532ac2bc49be391b415e9aaa3e237fa5e4c14b231149e2e1c02780263fc017`. No se compiló ni cambió la aplicación para esta preparación. El emulador mostró inicialmente un aviso «System UI isn't responding»; se seleccionó esperar y después se observó el acceso. Es una incidencia del ensayo, no un diagnóstico probado del producto.

Se conservó `FLAG_SECURE`. La captura visual se obtuvo de la ventana visible de macOS, sin modificar la protección Android. Los artefactos temporales están en `/private/tmp/redhouse-uiux-correction/`; no son requisito para ejecutar este prompt. Las descripciones anteriores permiten entender los ejemplos aunque las imágenes de la conversación ya no estén disponibles. No copies pestañas del navegador, credenciales o información personal a evidencias públicas.

## 2. Diagnóstico: problemas concretos, no adjetivos

Las heurísticas son criterios de evaluación, no una etiqueta de «cumple/no cumple todo». Relaciona cada corrección con una fricción observable. Referencia: [heurísticas de Nielsen](https://www.nngroup.com/articles/ten-usability-heuristics/).

| ID | Fallo | Causa comprobada o alcance | Criterio afectado |
| --- | --- | --- | --- |
| C01 | Acciones visualmente incompatibles en una fila | `integration/list.html` combina enlace, icono y acciones textuales. `integration.css` limita la columna a 100 px y `app.css` permite `flex-wrap: wrap`. | Consistencia; reconocimiento; economía visual. |
| C02 | Filas altas sin contenido que lo justifique | La columna de acciones apiladas determina la altura de toda la fila. | Eficiencia de lectura y comparación. |
| C03 | Herramientas dispersas antes de la tabla | Filtros, actualizar, refresco automático, total, exportar y paginación ocupan varias bandas. | Jerarquía y relevancia. |
| C04 | Formulario sin espacio interior | `documents.html` coloca controles directamente en `form.card`; `.card` aporta superficie/borde, no cuerpo acolchado. | Agrupación visual y consistencia de componentes. |
| C05 | Mismo concepto con tratamientos distintos | Documentos y otras vistas usan formularios/tablas propios fuera del patrón genérico. | Consistencia interna. |
| C06 | Login describe reglas que no ayudan a iniciar sesión | `login.html` muestra longitud y recomendación de reescritura incluso sin error. | Lenguaje pertinente y diseño minimalista. |
| C07 | Menú móvil replica una navegación web | `App.kt` usa cabecera azul, `DropdownMenu` «Secciones» y «Cuenta/Volver». | Convenciones móviles y reconocimiento de destinos. |
| C08 | Información secundaria domina el móvil | Estado global y red sobre todas las pantallas; UUID; controles globales; contenido genérico de campos. | Jerarquía, pertinencia y claridad de contexto. |
| C09 | Funciones expuestas todas a la vez | Agenda/expediente y tarea de transporte reúnen demasiadas consultas y formularios en una columna. | Divulgación progresiva y esfuerzo cognitivo. |
| C10 | Verificación técnica confundida con calidad visual | La evidencia previa reconoce recorridos privados/nativos y revisión visual incompletos. | Validación del resultado, no solo del código. |

El helper de listas compartido tiene decenas de consumidores —43 llamadas identificadas durante la revisión—. Los ejemplos del donante son **casos de un problema transversal**. Revisa todos los roles y todas las familias de pantalla, incluidas las que no usan ese helper.

## 3. Dirección visual obligatoria

Conserva el logotipo, nombre y paleta del monolito. No hagas un cambio de marca. En web, conserva Inter/DM Sans y el contraste entre navegación institucional oscura y área operativa clara. En móvil, usa tipografía y controles nativos con esa identidad, sin convertir la cabecera azul en protagonista de cada pantalla.

La calidad visual se obtendrá mediante estas decisiones:

- Una estructura reconocible para cada familia: listado, detalle, formulario, panel, avisos y cuenta.
- Título, información principal y acción correspondiente claramente diferenciados.
- Texto principal oscuro y legible; secundario realmente secundario. No volver gris y uniforme todo el contenido ni usar rojo para llamar la atención sobre cada elemento.
- Separación por proximidad y espacio; bordes y tarjetas solo donde agrupen una unidad útil.
- Mismo componente para la misma función. No fabricar variantes de select, botón, fila o estado en cada plantilla.
- Una acción primaria por tarea cuando exista. Acciones equivalentes con la misma jerarquía; logout nunca es la acción principal de Cuenta.
- Iconografía lineal de una misma familia, con tamaño, grosor y significado coherentes. Sin emojis como sustituto de iconos operativos.

### Escala inicial de diseño

Son decisiones de proyecto para dar consistencia, **no normas universales ni órdenes de alinear píxeles**. Úsalas como tokens y ajústalas de forma global si la lectura real lo exige.

| Elemento | Web | Móvil |
| --- | --- | --- |
| Ritmo de espacio | Escala 4, 8, 12, 16, 24 y 32 CSS px | Escala 4, 8, 12, 16 y 24 dp |
| Cuerpo de formulario | 24 px de espacio interior amplio; 16 px compacto | 16 dp laterales; 24 dp entre secciones |
| Etiqueta y control | 6–8 px de separación | 8 dp entre elementos relacionados |
| Campos consecutivos | 16–24 px | 16–24 dp según agrupación |
| Texto de lectura | 14–16 px; encabezados con jerarquía clara | 16 sp cuerpo, 14 sp secundario, título alrededor de 24 sp |
| Fila sencilla de tabla | Base de 56 px; dos líneas alrededor de 72 px | No copiar una tabla de escritorio dentro del teléfono |
| Acción de fila | Icono 18–20 px dentro de objetivo de 36–40 px para puntero preciso; ampliar a 44–48 px en táctil | Objetivo mínimo 48 dp |
| Controles de formulario | Altura mínima coherente alrededor de 44 px | Componentes nativos y altura accesible |

Las alturas de fila son referencias a escala normal, nunca límites que recorten texto. Con fuente ampliada o contenido legítimamente largo, deja crecer la fila. No reduzcas la tipografía para alcanzar una cifra. El contraste y las áreas interactivas se verifican aparte.

## 4. Web: contrato único de acciones de fila

**La columna Acciones será de iconos, según la preferencia expresa del usuario.** Esto no elimina nombres accesibles, tooltips ni texto en menús. Tampoco convierte en iconos solos los botones de formularios o la navegación móvil.

Implementa una única composición reutilizable:

1. Banda horizontal, centrada verticalmente, sin saltos de línea en escritorio.
2. Hasta dos acciones frecuentes visibles; si existen más, un botón «Más acciones» con menú contextual. No agregues el menú cuando no tenga contenido.
3. Todos los controles directos usan la misma superficie, tamaño, radio, iconografía y comportamiento de foco. Estado normal discreto; hover/foco claros. No mezclar una frase larga, un ojo encuadrado y otra frase debajo.
4. Reserva el ancho necesario según controles reales; elimina la combinación de 100 px insuficientes y wrapping. No sacrifiques el ancho útil del nombre del registro.
5. Orden semántico estable: consulta/vista rápida, acción habitual contextual, más opciones. Las destructivas o poco frecuentes van al menú con su nombre explícito y confirmación existente.
6. Cada icono tiene nombre accesible por acción y recurso, por ejemplo «Vista rápida de Campaña H1 01». Tooltip al pasar el puntero **y al recibir foco**, sin depender solo del atributo `title`.
7. Los controles siguen accesibles sin hover. En táctil, no requieren pulsación larga para descubrir la única ruta disponible. Las operaciones ambiguas se resuelven mediante el menú con etiquetas.
8. Abrir/cerrar el menú debe respetar teclado, Escape, retorno del foco y relación con su disparador. No encerrar el foco en una celda.
9. Mantén enlaces para navegar y botones/formularios para escribir. Conservar POST, CSRF, recurso, versión e idempotencia donde ya existan. No conviertas «Marcar como leída» en un GET.
10. No dispares una operación de negocio al pulsar el fondo de la fila ni uses un check que parezca aprobación médica para representar lectura.

### Resolver «Abrir expediente» frente a «Vista rápida»

Son comportamientos distintos. La solución preferida es **nombre del registro como enlace al detalle completo** y ojo para la vista rápida en Acciones. En la columna no queda el texto «Abrir expediente». Si un registro no tiene un nombre adecuado para enlazar, usa un icono de apertura distinto del ojo con nombre accesible inequívoco.

No uses el mismo ojo para dos destinos, no retires el acceso al expediente y no añadas un paso modal obligatorio. El nombre visible debe responder al recurso: «Ver campaña», «Ver aviso» o «Ver unidad» cuando corresponda; no llamar expediente a todo.

### Aplicación a los ejemplos

- **Campañas:** nombre enlazado, fechas/cupo/estado legibles y un ojo para vista rápida; más acciones solo si el rol dispone de otras. Una única fila de controles.
- **Avisos:** asunto enlazado, estado de negocio y fecha; ojo para vista rápida y sobre abierto para la acción existente «Marcar como leída», cuando esté permitida. No inventar «Marcar como no leída» si no existe.
- **Inventario, personas, solicitudes y administración:** mismo patrón, con acciones autorizadas de ese recurso. No usar la apariencia del donante para decidir permisos de otros perfiles.

No traduzcas el estado «Abierta» de un aviso a «No leída» sin verificar que representan el mismo dato. Lectura, estado operativo y urgencia pueden ser propiedades distintas.

El [ejemplo real de Gmail](https://support.google.com/mail/answer/2473038?hl=en) muestra acciones frecuentes por iconos y secundarias agrupadas. No copies operaciones ni ocultes todos los botones hasta hover. La [investigación sobre iconos de NN/g](https://www.nngroup.com/articles/icon-usability/) obliga a conservar medios de identificación: iconos solos no son universalmente más comprensibles.

## 5. Web: tablas compactas y herramientas proporcionadas

Corrige primero la estructura de acciones; después ajusta la densidad. No soluciones las filas enormes con `height`, `overflow:hidden` o letra pequeña.

- Una fila sencilla tiene una línea principal y, solo si aporta algo, una secundaria. Datos y controles alineados al centro vertical. Los nombres extensos pueden ocupar más líneas sin cortar información indispensable.
- Encabezados claros, fechas legibles y números comparables. Estado en etiqueta discreta, no en una tarjeta adicional.
- Cada tabla conserva el mismo estilo de cabeceras, separadores, hover, foco, vacíos, carga y paginación.
- Unifica las herramientas en una barra que se adapte al espacio. Si hay filtros complejos, permite una segunda línea justificada; no una franja completa por cada herramienta.
- Usa icono de recarga para «Actualizar». La lupa corresponde a búsqueda, no a refrescar una lista sin filtros.
- Actualización automática conserva su intervalo y comportamiento; se presenta junto al refresco como control secundario. No forzar `flex-basis:100%` por defecto.
- Recuento y exportación ocupan posiciones estables y secundarias. Conserva «Exportar página» cuando ese sea el alcance real; no inventes exportación total.
- Un paginador principal al pie, con página y total. Repetirlo arriba solo si la longitud real lo justifica. En una página no mostrar controles inútiles deshabilitados ocupando una franja.
- Al refrescar, filtrar o paginar, conservar contexto y comportamiento existentes. No introducir autoselección, reordenamiento o acciones masivas.

Composición de referencia para un listado sin filtros complejos:

```text
Título de la vista                         Acción de creación, si procede

[Búsqueda/filtros existentes] [Actualizar] [Autoactualizar]   Exportar página
31 registros

Nombre / evento                 Estado       Fecha              Acciones
Nombre enlazado                  Estado       Fecha              [ojo] [sobre]
Nombre enlazado                  Estado       Fecha              [ojo] [sobre]

Página 1 de 2                                      Anterior  1  2  Siguiente
```

Es un esquema de jerarquía, no una especificación de coordenadas. Si no hay búsqueda, no inventes una. Ajusta los controles a la anchura sin recrear las bandas vacías de las capturas.

En ancho compacto, usa resúmenes por registro si ayudan a la tarea. Para comparación tabular que lo requiera, conserva desplazamiento horizontal localizado. Ninguna opción permite que las acciones se apilen accidentalmente, que toda la página desborde o que desaparezcan datos esenciales.

Referencia: [tablas de IBM Carbon](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines). Adopta densidad coherente, herramientas agrupadas y detalle progresivo; no copies todas sus funciones ni instales su framework.

## 6. Web: formularios y Documentos privados

Define dos superficies diferentes:

- **Superficie de formulario o contenido:** encabezado opcional, cuerpo con espacio interior y pie de acciones coherente.
- **Superficie de tabla:** herramientas y tabla con tratamiento propio; puede tener separadores al ras del contenedor.

No arregles Documentos mediante `.card { padding: 24px }` global: perjudicaría tablas y otros componentes. Usa cuerpos/clases semánticas compartidas. Revisa controles personalizados y genéricos, no solo la plantilla de la captura.

Cada campo tendrá etiqueta persistente, control, ayuda necesaria y error contextual. Misma altura mínima, borde, foco, radio y espaciado en todos los módulos. No usar placeholders como únicas etiquetas ni controles deshabilitados casi invisibles.

### Composición requerida en Documentos

1. Título «Documentos» o «Documentos privados», consistente con la navegación.
2. Una descripción útil como «Consulta los documentos de un expediente». Evitar explicar autorizaciones internas en cada renglón.
3. Un área de formulario de ancho contenido —referencia 640–720 px en escritorio—, sin extender dos selects por toda la ventana.
4. Grupo de tipo de expediente y grupo de expediente dentro de una secuencia visual coherente. Los campos no tocan el borde ni el botón toca la etiqueta.
5. Si hay varios tipos autorizados, selector y acción de cambio existentes, presentada como secundaria. Si solo hay uno, representar ese tipo como contexto en lugar de aparentar una elección; conservar su valor y cualquier paso de consulta necesario.
6. «Expediente» como etiqueta, sin repetir «propio autorizado». El permiso sigue aplicándose igual.
7. «Consultar documentos» como acción principal, junto al grupo que completa la consulta.
8. Resultados debajo con el patrón común de tabla/lista, estados de documento, paginación y acciones autorizadas.

Los formularios actuales tienen consultas GET dependientes. La mejora visual no permite fusionarlas a ciegas, añadir solicitudes al servidor, eliminar un paso necesario ni asumir resultados disponibles. Si conservas dos envíos, preséntalos como dos grupos del mismo proceso con continuidad visual. Un tipo fijo no autoriza seleccionar automáticamente un expediente distinto.

Revisa también subida de documentos, conservación, linaje, evaluación, etiquetas y espacios de trabajo. Deben pertenecer al mismo sistema de componentes aunque su contenido cambie.

## 7. Acceso: información mínima y pertinente

Retira del estado inicial del login, en todas sus variantes, estas frases:

- «Entre 3 y 80 caracteres».
- «Entre 12 y 128 caracteres. Vuelve a escribirla si el acceso se rechaza».

No las traslades a otra tarjeta visible ni las sustituyas por otro párrafo técnico. Las restricciones siguen en atributos, validadores y servidor. Si se elimina una ayuda, ajusta `aria-describedby` para no referenciar un elemento inexistente.

La composición debe ser: marca; título; cuenta; contraseña con mostrar/ocultar; segundo factor con una ayuda breve cuando corresponda al flujo actual; recuperación; «Iniciar sesión»; ayuda institucional secundaria. Usa «Iniciar sesión» como título o CTA con claridad, sin acumular slogans dentro del formulario.

No cambies a un login de dos pasos, no consultes si una cuenta existe para decidir mostrar MFA y no retires el segundo factor para simplificar. Conserva el flujo actual, autocompletado, gestores de contraseñas, reglas de validación y errores de autenticación seguros.

Cuando haya un error, informa entonces lo necesario para corregirlo, sin revelar cuál credencial es válida. Mantén recuperación y ayuda institucional diferenciadas. La sección editorial del acceso web puede conservarse en escritorio si no compite con el formulario; en compacto, la tarea de acceso tiene prioridad.

En móvil, elimina el bloque rutinario «Conexión de red disponible» del acceso normal. Usa una cabecera nativa sencilla con marca, campos de ancho útil y CTA claro. No comprimas el contenido ni bajes la escala de fuente para evitar scroll: a 130–200 % se permite desplazamiento. Mantén avisos clínicos necesarios, pero no una declaración genérica extensa ocupando el espacio principal de cada pantalla.

Referencia: [ayuda contextual de NHS](https://service-manual.nhs.uk/design-system/components/hint-text). La decisión específica de retirar esas frases procede del contexto de acceso y la solicitud del usuario, no de una prohibición universal de ayudas.

## 8. Móvil: arquitectura propia, centrada en tareas

**Sustituye «Secciones» como navegación principal.** Tampoco basta con mover su lista completa a otro menú. Reorganiza los destinos por objetivos, usando navegación inferior nativa con icono y etiqueta, selección inequívoca y estado conservado según el comportamiento existente.

Una barra superior móvil sigue siendo válida para título y regreso contextual. Lo que se elimina es la cabecera de sitio web con marca, menú general y «Volver» compitiendo como navegación principal. No hay botón Volver en la raíz; en una subpantalla, usar regreso al contexto real. El botón del sistema debe respetar esa jerarquía.

### Destinos definidos por rol

Esta tabla es una decisión concreta para Red House. Son agrupaciones visuales de funciones existentes, no nuevos módulos ni permisos.

| Perfil | Navegación principal | Contenido secundario |
| --- | --- | --- |
| Donante | **Citas · Campañas · Avisos · Cuenta** | Horarios dentro del recorrido de reserva; expediente y consentimiento en Cuenta; historial dentro de Citas. |
| Transporte | **Traslados · Pendientes · Avisos · Cuenta** | Ruta/contactos, escaneo, custodia, evidencia y ubicación dentro de la tarea seleccionada. |
| Operador | **Inventario · Traslados · Avisos · Cuenta** | Lectura térmica y detalle dentro de unidad; preparación/recepción dentro de traslado. |
| Coordinador | **Traslados · Región · Avisos · Cuenta** | Región agrupa disponibilidad, solicitudes agregadas y reservas existentes; programación desde el contexto pertinente. |
| Médico | **Solicitudes · Laboratorio · Avisos · Cuenta** | Laboratorio agrupa muestras/resultados; completitud dentro de la muestra correspondiente. |

No conviertas Región o Laboratorio en un dashboard nuevo ni agregues métricas. Si un perfil adicional solo dispone actualmente de Perfil y Avisos, organiza esas dos opciones con un control nativo adecuado; no inventes un tercer destino ni le habilites los módulos de otro rol.

Al entrar, abrir el primer destino de trabajo del perfil. No dejar «Elige una sección» como bienvenida ni solicitar al usuario que descubra un desplegable. No cargar todos los módulos para decorar una pantalla de inicio.

Las opciones de menor frecuencia siguen accesibles en destinos secundarios claramente nombrados. Simplificar significa **mostrar menos simultáneamente**, no borrar funciones, filtros, datos necesarios o controles de seguridad.

Patrones reales de referencia: [NHS App: pantallas principales](https://design-system.nhsapp.service.nhs.uk/patterns/hub-page/), [sus niveles secundarios](https://design-system.nhsapp.service.nhs.uk/patterns/sub-hub-page/) y [Google Chat en Android](https://support.google.com/chat/answer/14170781?co=GENIE.Platform%3DAndroid&hl=en). Aportan separación entre trabajo, mensajes y cuenta. No se importan sus funciones clínicas ni su apariencia de marca.

### Regla para información visible

Una pantalla de tarea debe mostrar: título, resumen necesario, estado operativo y siguiente acción. Detalles técnicos, antecedentes y herramientas ocasionales se consultan bajo demanda. No convertir cada destino en una lista de todos los campos de su respuesta JSON.

No mantengas «Conexión disponible», «Consulta confirmada · página…», usuario/rol y título como cuatro renglones antes de cada contenido. La red normal puede no requerir un aviso. La carga se muestra en su zona; la actualización ordinaria no necesita un mensaje permanente. Desconexión, datos antiguos, rechazo y operación incierta conservan señales visibles y específicas. No escondas fallos reales para limpiar la pantalla.

## 9. Móvil: composición exacta de las pantallas principales

### Cuenta

```text
Cuenta

Nombre disponible o cuenta institucional
Perfil · Institución legible, si está disponible

Mi expediente                        >  solo donante
Notificaciones                       >
Privacidad y permisos                >
Información de la cuenta             >
Operaciones pendientes (cantidad)     >  si existen

Cerrar sesión                           acción secundaria

[Citas] [Campañas] [Avisos] [Cuenta]      ejemplo donante
```

Usa una lista de ajustes con grupos y separadores discretos, no una pila de botones rojos. El UUID completo pasa a «Información de la cuenta», accesible cuando sea necesario. Si no existe nombre autorizado de institución, no lo inventes ni rotules un UUID como si fuera un nombre humano.

«Notificaciones» abre la gestión existente. No mostrar Activar y Desactivar a la vez en la raíz. Una sola acción contextual o un switch solo son válidos cuando se conoce el estado real y su actualización; de lo contrario, usar una subvista de gestión con acciones explícitas y estado honesto. El permiso del sistema no prueba que el proveedor push esté registrado ni que entregue avisos.

«Operaciones pendientes» no aparece como título huérfano. Mostrar una entrada con cantidad real si existen; su pantalla distingue cada estado y recuperación. Logout queda al final con tratamiento secundario, conservando revocación, limpieza y avisos de resultado incierto.

### Donante: Citas y Campañas

- **Citas:** título «Mis citas», resumen de las citas disponibles y estado legible. Cada elemento prioriza fecha/hora, sede y estado; una acción de consulta. No listar veinte pares `etiqueta: valor`.
- No afirmar «próxima cita» o «sin citas» sobre datos incompletos de una página sin comprobar el alcance. No crear un resumen con citas falsas para llenar el inicio.
- El vacío real tiene una frase breve y acceso al recorrido existente de horarios. Si falla la consulta, mostrar fallo, no vacío.
- Detalle de cita con información y acciones actuales según estado: confirmar asistencia prevista, reprogramar o cancelar cuando estén autorizadas. Mantener confirmación y consentimiento.
- Historial en una sección secundaria dentro de Citas, sin competir con la cita vigente.
- **Campañas:** título de campaña, fecha/periodo, sede si existe y estado/cupo solo cuando aportan información disponible. Acción «Ver campaña» o acceso existente a horarios cuando la relación esté confirmada.
- Horarios no compite como quinta pestaña: se alcanza durante la búsqueda/reserva. No inventar asociaciones campaña–horario por nombres parecidos ni filtros que el contrato no admite.
- Expediente y consentimiento se consultan desde Cuenta. Si un trámite exige consentimiento, se presenta en ese momento sin eliminar el requisito. No imprimir todo el formulario delante de cada lista de citas.

### Transporte: Traslados y tarea

- **Lista:** referencia operativa, origen/destino disponibles, estado y fecha relevante. Nombres legibles cuando existan; referencias técnicas secundarias cuando no.
- **Detalle:** resumen del traslado y próxima acción que realmente permita el estado. Un botón principal con verbo y objeto, por ejemplo «Confirmar recolección»; no una cuadrícula de todos los comandos.
- Escaneo, sello, contraparte, motivo y confirmación siguen siendo obligatorios donde lo eran. Una mejora de densidad no reduce la cadena de custodia.
- Accesos secundarios claros: «Contactos y ruta», «Evidencia», «Ubicación» e «Historial». Incidencias permanecen localizables por su relevancia operativa.
- La ubicación muestra autorización, conexión, última observación, antigüedad, precisión y procedencia en su contexto. No confundir red disponible con recepción remota.
- **Pendientes:** separar «Observaciones por sincronizar» de «Operaciones por confirmar», con sus estados y recuperaciones respectivos. No añadir «Reintentar todo» ni convertir operaciones inciertas en envíos nuevos. Cuando Cuenta y Pendientes presenten la misma operación, reutilizar su componente y destino de detalle. Un registro local no implica traslado confirmado ni custodia completada.

Separar visualmente `TransportScreen` puede afectar sus efectos de ciclo de vida. **No cambies duración, autorización, cancelación o actividad GPS/WSS por mover una vista.** No mantener captura oculta ni enviar en segundo plano. Verifica que el resultado conserva el comportamiento funcional existente; si no puedes aislarlo, registra el límite y no alteres adaptadores.

### Operador, coordinador y médico

- Inventario: unidad identificable, tipo/grupo cuando corresponda, estado y ubicación. Detalle y captura térmica se abren desde el recurso, no como formularios globales.
- Región: grupos claros para disponibilidad, solicitudes agregadas y reservas que ya existen. No exponer consultas individuales restringidas ni una pantalla de métricas inventadas.
- Programación: dentro del contexto de reserva/traslado correspondiente. «Programar traslado» no aparece sobre Avisos, Cuenta o cualquier listado por una condición global de rol.
- Solicitudes y Laboratorio: lista de trabajo legible, referencia, estado y fecha. Muestra/resultado/completitud en sus vistas; mantener distinción entre documento autorizado y decisión clínica.

### Avisos

Lista nativa con asunto, fecha y estado pertinente, acceso al detalle y lectura cuando exista. Preferencias push en Cuenta, sin botones globales insertados al pie de cada bandeja. No retirar auditoría, reconocimiento ni separación de estados.

## 10. Contratos visuales reutilizables y alcance técnico

No añadas un parche distinto para cada captura. Define componentes y migra sus consumidores, incluidas plantillas específicas. Los nombres siguientes describen responsabilidades, no obligan a una arquitectura o biblioteca nueva:

| Componente | Invariantes |
| --- | --- |
| Acción de fila | Icono uniforme, nombre accesible, tooltip, misma área, orden y semántica HTTP. |
| Barra de listado | Filtros/refresco/exportación agrupados; distribución adaptativa sin bandas vacías. |
| Tabla y paginación | Densidad coherente, encabezados, foco, vacíos y alcance de resultados. |
| Cuerpo de formulario | Espacio interior, campos, ayudas/errores y pie de acciones comunes. |
| Cabecera de página | Título, contexto útil y acción principal; sin duplicaciones. |
| Estado/alerta | Significado, icono y tono coherentes; incertidumbre distinta de éxito. |
| Estructura móvil | Título, contenido y navegación inferior; regreso contextual y áreas seguras. |
| Resumen móvil de recurso | Información elegida por tarea y tipo, no volcado genérico de campos. |
| Ajuste de cuenta | Fila con etiqueta y destino/estado; no botón primario por cada preferencia. |

Archivos que deben orientar la revisión, sujetos a revalidar en el árbol actual:

- Web: `apps/web/src/presentation/templates/integration/list.html`, `documents.html`, `form.html`, `detail.html`, `dashboard.html`, `workspace.html`, `label.html`, `decision_support.html`, `evaluation.html`, `conservation.html`, `lineage.html`, `tracking.html`, `document_upload.html`; además `login.html`, `base.html` y CSS/JS de presentación.
- Móvil: `App.kt`, `Presentation.kt`, `DonorScreen.kt`, `TransportScreen.kt`, `OperationalScreens.kt` y `SyncScreen.kt`, dentro de `apps/mobile/composeApp/src/commonMain/kotlin/org/redhouse/mobile/`.

Se encontraron 27 plantillas en `templates/integration/` al preparar este documento. Recuéntalas: no cierres la revisión solo por editar la lista genérica. Documentos, evaluación, conservación y linaje tienen variaciones de tabla o contenedor que requieren revisión propia.

Mantén `.card` como superficie si ese es su contrato actual y crea/reutiliza un cuerpo apropiado. Revisa la cascada entre `app.css` e `integration.css`. No acumules overrides al final ni uses `!important` para ocultar el conflicto sin corregir el patrón que lo causa.

Cambios permitidos: composición, estilos, recursos visuales, texto, nombres accesibles, navegación de presentación y componentes UI. Se permiten pruebas correspondientes y ajustes aislados de metadatos presentacionales si conservan rutas y permisos.

**Fuera de alcance:** `apps/services/**`, contratos, DTO, clientes HTTP, bases, migraciones, reglas clínicas, validadores de negocio, permisos, JWT/MFA/sesión, idempotencia, workers, sincronización, GPS/QR/cámara, infraestructura y despliegue. No cambiar datos productivos ni completar funciones pendientes para que un diseño parezca terminado. Mantener JSON móvil y XML/XSD del futuro escritorio.

Se puede presentar una fecha con un control comprensible que entregue exactamente el valor contractual actual. No se autoriza cambiar zonas, precisión requerida, límites, payloads ni validación para acomodar ese control. Las referencias y precisión necesarias permanecen disponibles donde informan una decisión.

## 11. Cobertura: todas las vistas y todos los roles aplicables

Construye una matriz **ruta o pantalla × rol autorizado × familia visual × estado relevante × tamaño revisado**. No marques un rol completo por probar su panel. No marques una ruta como revisada visualmente solo porque Jinja compila o un test comprueba un enlace.

| Perfil o superficie | Familias mínimas que debes localizar y revisar |
| --- | --- |
| Público | Portada, acceso, recuperación, ayuda y estados sin contenido. |
| Donante web | Panel, campañas, horarios, inscripciones/citas, expediente, documentos, avisos, cuenta y reportes que realmente tenga autorizados. |
| Operador web | Inventario/altas, donaciones/procesamiento, laboratorio, conservación, campañas, preparación/recepción y documentos. |
| Médico web | Receptores, solicitudes, resultados, completitud, evaluación, compatibilidad, revisión, reservas y destino autorizado. |
| Coordinador web | Disponibilidad, propuestas, reservas, rutas, traslados, mapas y hallazgos permitidos. |
| Transporte web | Tareas, contactos, custodia, mapas, incidencias y evidencias. |
| Administrador web | Usuarios, instituciones, catálogos, dispositivos, configuración, monitoreo y vistas de gestión permitidas. |
| Auditor web | Eventos, detalle, filtros, hallazgos, informes y exportación permitida. |
| Móvil | Las cinco arquitecturas por rol descritas arriba, acceso y superficies adicionales que efectivamente existan. No copiar los siete perfiles web como siete módulos móviles nuevos. |

Para cada vista disponible, verificar estructura y navegación en amplio y compacto. Los estados de carga, vacío, error, conflicto e incertidumbre se ensayan en las familias donde existan; no inventar estados ni reproducir todos los casos mediante datos de relleno. Si una misma plantilla cambia acciones según el rol, revisar esas variantes.

### Tamaños y navegadores

- Web: 1440, 1024, 768, 390 y 320 CSS px como puntos de control de composición; la adaptación debe funcionar entre ellos.
- Revisar Safari, porque las capturas del usuario proceden de ese navegador, y Chrome. No culpar a Safari sin comprobar la causa; WebKit automatizado no equivale a una prueba real de Safari.
- Móvil: Android en 360 y aproximadamente 412 dp, fuente normal y aumentada a 130 % y 200 %, teclado abierto y orientación cuando el flujo lo permita. No cambiar la configuración del usuario para hacer caber la interfaz.
- Al ser Compose compartido, comprobar el efecto en iOS sin afirmar ejecución que no ocurrió. No descargar runtimes o cambiar SDK por este encargo de presentación.

### Accesibilidad verificable

Comprobar nombres, foco, lectura, teclado, áreas táctiles, contraste y ausencia de recortes. La [documentación Compose](https://developer.android.com/develop/ui/compose/accessibility/api-defaults) establece la referencia táctil de 48 dp. Para web, aplicar [WCAG 2.2](https://www.w3.org/TR/WCAG22/): contraste textual 4,5:1 o 3:1 para texto grande, reflow a 320 CSS px, texto al 200 %, foco visible y requisitos aplicables de contraste no textual y objetivos de puntero. No equiparar dp con CSS px ni declarar conformidad total por un análisis automático.

Preservar navegación por teclado en menús, retorno del foco tras vista rápida y datos del formulario tras errores donde corresponda. Las ayudas de icono deben funcionar con foco; las etiquetas móviles permanecen visibles. No usar tooltips como único acceso a información crítica.

## 12. Método de trabajo que evita otra corrección superficial

1. **Reproducir e inventariar.** Captura el estado actual y revisa las causas de C01–C10. Distingue capturas del usuario, evidencia histórica, ejecución nueva y fuente.
2. **Construir los patrones compartidos.** Acciones/tabla; formulario; login; navegación móvil; resumen de recurso y Cuenta. Resuelve estas familias antes de propagar excepciones.
3. **Validar ejemplos completos.** Campañas, Avisos y Documentos del donante; un listado operativo con más acciones; Cuenta/Citas móvil y un detalle de traslado. Inspecciona el resultado real, no solo código o árbol accesible.
4. **Aplicar a todas las variantes.** Recorrer el inventario completo y resolver vistas personalizadas. No dejar módulos con el patrón anterior porque no aparecieron en las capturas.
5. **Comparar y corregir.** Misma ruta, rol, datos, tamaño y escala. Si permanece cualquiera de los defectos descritos, vuelve a la composición. Un test verde no invalida un fallo visible.
6. **Verificar regresión proporcional.** Operaciones, formularios, permisos, filtros, foco, regreso y estados mantienen comportamiento. Ajustar selectores accesibles de tests sin eliminar aserciones funcionales.
7. **Entregar evidencia honesta.** Registrar cobertura y límites. No declarar terminado un rediseño móvil basándose solo en acceso, compilación o tests JVM.

No necesitas un estudio formal para corregir un control pegado al borde. Tampoco debes afirmar que la nueva experiencia fue validada por usuarios si solo la revisó un agente. Los patrones de referencias reales orientan; la revisión de Red House comprueba su aplicación.

Usa datos de prueba y entornos autorizados. Consultar producción no autoriza crear citas, publicar documentos o cambiar custodia. No alteres servicios para obtener capturas. Si una dependencia impide recorrer una pantalla, registra el bloqueo concreto y continúa con las familias independientes; no presentes el resultado bloqueado como aprobado.

## 13. Criterios de aceptación y rechazo

| ID | Evidencia requerida | Rechazar si… |
| --- | --- | --- |
| V01 | Acciones uniformes en campañas, avisos y listados operativos | Persiste texto «Abrir expediente» mezclado con botones/links apilados en la columna. |
| V02 | Filas comparables, tipografía y controles legibles | La altura depende de acciones en tres niveles, o se reduce mediante recorte/letra pequeña. |
| V03 | Herramientas compactas y paginación proporcionada | Hay una banda vacía por cada control o una lupa para una acción de refresco. |
| V04 | Documentos y formularios personalizados con cuerpo, campos y pie comunes | Cualquier etiqueta, select o botón toca el borde; se solucionó solo con padding global de `.card`. |
| V05 | Login inicial limpio, MFA y recuperación intactos | Continúan ayudas de longitud y reescritura como contenido permanente, o se dejaron referencias ARIA rotas. |
| V06 | Arquitectura móvil por rol implementada | «Secciones» sigue siendo la única navegación principal o se entra en «Elige una sección». |
| V07 | Cuenta móvil organizada en grupos, identidad breve y logout secundario | UUID domina la pantalla, hay Activar/Desactivar simultáneos en raíz o logout es el CTA principal. |
| V08 | Listas móviles con jerarquía por recurso | Se sigue imprimiendo una tarjeta genérica con todos los campos traducidos. |
| V09 | Agenda y transporte divididos por objetivos | Formularios y herramientas de todo el flujo siguen expuestos simultáneamente. |
| V10 | Estados situados en su contexto | Red correcta y consulta confirmada ocupan siempre dos párrafos; se ocultan fallos o incertidumbre. |
| V11 | Matriz de todas las rutas/perfiles aplicables y revisión de variantes | Se afirma cobertura total por revisar solo donante, login, panel o plantilla genérica. |
| V12 | Safari/Chrome, tamaños compactos, fuente ampliada y accesibilidad | Hay acciones inaccesibles, controles cortados o se afirma Safari/iOS sin ejecución real. |
| V13 | Correspondencia de acciones/datos/contratos antes y después | Se retiraron funciones, confirmaciones o permisos para simplificar el diseño. |
| V14 | Componentes consistentes y evidencia visual comparable | La solución acumula estilos particulares, cambia colores otra vez o entrega solo un informe técnico. |

Para Campañas y Avisos, compara cuántas filas completas se ven antes/después en el mismo viewport. La mejora debe proceder de acciones horizontales y espacios proporcionados, no de reducir la escala del navegador. Registra también pasos de navegación, retrocesos y desplazamiento para localizar un registro, abrirlo, leer un aviso y acceder a documentos. No inventes porcentajes ni impongas «todo en tres clics».

En móvil, verifica al menos un recorrido autenticado por cada uno de los cinco perfiles existentes. Cuenta y navegación inferior deben revisarse dentro de una sesión real. Una captura aportada por el usuario identifica un problema; no demuestra que la implementación nueva lo corrigió.

## 14. Referencias concretas y cómo utilizarlas

Consultadas el **10/11/2026**. Son ejemplos reales y documentación de sus autores; no equivalen a una prueba de usabilidad de Red House. Las medidas y composición de este prompt son decisiones propias de diseño, apoyadas por estos patrones.

| Referencia | Patrón que se utiliza | Qué no copiar |
| --- | --- | --- |
| [Gmail: barra de acciones](https://support.google.com/mail/answer/2473038?hl=en) | Acciones frecuentes consistentes y opciones secundarias agrupadas. | Funciones de correo, selección masiva o iconos ambiguos sin identificación. |
| [NHS App: hubs](https://design-system.nhsapp.service.nhs.uk/patterns/hub-page/) | Separación de tareas, mensajes y perfil; navegación inferior y ajustes agrupados. | Marca, datos personales del ejemplo, servicios clínicos ajenos o resultados de investigación atribuidos a Red House. |
| [NHS App: sub-hubs](https://design-system.nhsapp.service.nhs.uk/patterns/sub-hub-page/) | Segundo nivel coherente y opciones relacionadas bajo demanda. | Menús profundos innecesarios ni una copia de su catálogo sanitario. |
| [Google Chat Android](https://support.google.com/chat/answer/14170781?co=GENIE.Platform%3DAndroid&hl=en) | Destinos frecuentes inferiores y opciones secundarias separadas. | Convertir cada módulo backend en una pestaña. |
| [Android: navegación](https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-and-nav-patterns) | Destinos del mismo nivel y adaptación por tamaño de ventana. | Una navbar web comprimida; iconos sin etiquetas en navegación principal. |
| [Compose: icon buttons](https://developer.android.com/develop/ui/compose/components/icon-button) | Controles nativos para acciones reconocibles con semántica. | Reducir áreas táctiles para parecerse a una tabla web. |
| [Carbon: tablas](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines) | Densidad, herramientas y acciones consistentes. | Todo su repertorio de funciones, dependencias React o alturas rígidas que recorten datos. |
| [NHS: hint text](https://service-manual.nhs.uk/design-system/components/hint-text) | Ayuda breve que resuelve una duda real del campo. | Documentación técnica siempre visible. |
| [NN/g: divulgación progresiva](https://www.nngroup.com/articles/progressive-disclosure/) | Menos opciones iniciales y acceso claro a las secundarias. | Borrar capacidades o esconder alertas necesarias. |
| [NN/g: iconos](https://www.nngroup.com/articles/icon-usability/) | Reconocer límites de comprensión; mantener identificación accesible. | La afirmación de que iconos solos siempre son mejores. |

Se inspeccionaron visualmente el [Inicio oficial de NHS App](https://design-system.nhsapp.service.nhs.uk/assets/images/hub-pages-image1.png) y su [Perfil](https://design-system.nhsapp.service.nhs.uk/assets/images/hub-pages-image4.png). Observa la agrupación, separación y jerarquía; el objetivo no es copiar sus colores ni sus pantallas completas. NHS describe investigación propia sobre su organización: eso no certifica la propuesta de Red House.

## 15. Entrega de la ejecución futura

Entrega cambios reales de presentación, con:

- Relación C01–C10 y V01–V14: resuelto, pendiente o bloqueado, con evidencia concreta.
- Inventario de rutas/roles revisados y variantes que quedan fuera, sin ocultarlas en una afirmación general.
- Comparaciones antes/después de los cinco ejemplos y de otras familias/roles; imágenes de tamaño y escala equivalentes.
- Recorridos web y móviles realizados, pasos medidos, pruebas de regresión y límites de entorno.
- Archivos cambiados y comprobación de que no hubo cambios funcionales, de microservicios, contratos o datos productivos.

Durante esa ejecución futura, documenta el estado proporcionalmente a las reglas del repositorio. No cierres etapas funcionales por una mejora visual. No despliegues ni publiques sin autorización específica.

La futura etapa 05 conserva Python/PySide6, XML/XSD y su alcance. Debe heredar estos contratos de componentes y semántica —tablas, acciones, campos, estados— con ergonomía de escritorio. No debe heredar la barra inferior móvil ni implementarse ahora.

**Condición final:** no declares «rediseño completado» mientras sigan presentes defectos de las capturas, variantes sin revisar o recorridos necesarios sin comprobar. Una entrega parcial debe llamarse parcial y explicar exactamente qué falta.
