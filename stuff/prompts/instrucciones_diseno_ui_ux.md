# Instrucciones de diseño UI/UX de Red House

Fecha de preparación: **10 de noviembre de 2026**.

Documento de referencia para el monolito, el móvil y la futura consola de escritorio. Se aplica junto con el [prompt de rediseño](redisenar_ui_ux_monolito_movil.md). Para escritorio, complementa el [encargo de etapa 05](entrega-final/05_aplicacion_escritorio.md); no sustituye su alcance funcional.

Estas instrucciones definen cómo presentar las capacidades autorizadas. No autorizan cambios de negocio, servicios, contratos, datos ni permisos. La elaboración de estos dos documentos no implementa el rediseño ni acredita el cierre de ninguna etapa.

## 1. Resultado que debe percibir el usuario

Red House debe sentirse como una misma plataforma institucional: reconocible, clara, sobria y preparada para trabajo real. Cada pantalla debe permitir entender **dónde estoy, qué estoy viendo, cuál es su estado y qué puedo hacer**.

La coherencia entre plataformas consiste en compartir identidad, vocabulario, jerarquía y significado de los estados. La composición se adapta al dispositivo: móvil para tareas breves y captura; web para gestión; escritorio para operación intensiva. No se exige igualdad de píxeles ni copiar la barra lateral web en un teléfono.

El acabado profesional debe proceder de claridad y consistencia. Nunca debe obtenerse ocultando limitaciones reales, datos sintéticos, falta de autorización, incertidumbre de una operación o necesidad de revisión médica.

## 2. Identidad visual que se conserva

La referencia es el monolito existente, no un tema genérico nuevo. Los valores siguientes proceden de [app.css](../../apps/web/src/presentation/static/css/app.css), contrastados con la portada y el acceso publicados y con capturas del portal privado.

| Función | Base actual | Regla de continuidad |
| --- | --- | --- |
| Marca y acción principal | Rojo `#c8102e` | Mantenerlo como ancla reconocible; usarlo con moderación. |
| Color secundario | Azul `#1e3a5f` | Apoyar navegación, vínculos y acciones secundarias según la superficie. |
| Navegación oscura | Azul profundo `#0f1b2d` | Conservar la personalidad institucional del portal y acceso. |
| Fondo de trabajo | `#f0f4f8` | Fondo claro y tranquilo para lectura prolongada. |
| Superficie | Blanco `#ffffff` | Agrupar contenido cuando exista una razón funcional. |
| Texto principal | `#0f172a` | Priorizar legibilidad y contraste. |
| Texto secundario | `#64748b` | Verificarlo sobre cada fondo; no usarlo para diluir información crítica. |
| Bordes | `#e2e8f0` | Separación discreta; no asumir que basta para identificar un control. |
| Tipografía web | Inter; títulos DM Sans | Conservar familia y jerarquía. En nativo, usar recursos licenciados compatibles o una equivalencia legible documentada. |
| Símbolo | Gota blanca sobre recuadro rojo; «Red House» / «RED REGIONAL» | Reutilizar los recursos existentes. No inventar otro logotipo. |

El móvil solo fija actualmente el primario `#a01832` en su tema Material. Debe adoptar una familia completa de colores derivada de la web: fondo, superficie, contenido, borde, selección, foco y estados. No basta con cambiar el color de los botones.

Definir tokens semánticos equivalentes en CSS, Compose y, en etapa 05, Qt. Por ejemplo: `brand.primary`, `surface.default`, `text.primary`, `action.secondary`, `status.warning`, `focus.ring`. Los nombres son una guía, no una obligación de instalar una biblioteca ni crear infraestructura compartida.

Los colores de marca no equivalen a estados de negocio. Diferenciar acción principal, acción destructiva y error mediante texto, icono y contexto. Revisar todos los estados: normal, foco, pulsado, seleccionado, deshabilitado, cargando y error. Ningún color aislado comunica autorización clínica.

La superficie oscura de acceso puede conservarse. No convertir todo el espacio operativo en oscuro ni añadir un selector de temas como parte de este encargo.

## 3. Jerarquía, densidad y contenedores

1. Un título principal que nombre la tarea o el recurso. Evitar encabezados técnicos y subtítulos repetidos.
2. Contexto breve: institución, recurso, estado y fecha relevante, según el rol y los datos disponibles.
3. Acción principal clara cuando exista; acciones secundarias agrupadas junto al contenido al que afectan.
4. Información necesaria para decidir antes de detalles secundarios. La revisión clínica y la incertidumbre nunca quedan escondidas.
5. Un recuadro debe agrupar contenido relacionado, delimitar una interacción o comunicar una alerta. Si no cumple una de esas funciones, preferir espacio, título o separador.
6. Evitar tarjetas dentro de tarjetas, resúmenes enormes con un solo dato y bordes independientes alrededor de cada frase.
7. Evitar paneles donde toda acción compite con el mismo botón relleno. Cerrar sesión pertenece a cuenta; activar notificaciones pertenece a avisos o preferencias existentes.
8. Mantener una escala pequeña y coherente de espacios, radios, tipografía e iconos. Ajustarla por legibilidad y tarea, sin perseguir coincidencias de coordenadas.
9. No reducir letra ni áreas táctiles para hacer caber información. Priorizar, reagrupar o permitir desplazamiento localizado.
10. Los mensajes informativos recurrentes deben ocupar un lugar proporcionado. Las alertas que exigen actuar conservan visibilidad y persistencia.

## 4. Navegación y esfuerzo de interacción

Organizar por objetivos del usuario y responsabilidades de su perfil. No usar nombres de microservicios como arquitectura de información. Un concepto conserva el mismo nombre en todas las plataformas, aunque cambie su ubicación.

| Plataforma | Regla de composición |
| --- | --- |
| Monolito | Grupos de navegación únicos y estables, selección activa inequívoca y retorno al contexto. Reordenar vínculos sin cambiar rutas ni filtros de permisos. |
| Móvil | Separar navegación principal, contenido y cuenta. Usar barra de destinos cuando encajen entre tres y cinco destinos del mismo nivel; usar subniveles para el resto. |
| Escritorio 05 | Navegación persistente por módulos, espacio central de trabajo y detalle contextual cuando ayude a comparar. Optimizar para teclado y ratón. |

En móvil, tres a cinco es la capacidad recomendada para una barra de navegación, **no un límite al número de funciones**. El patrón procede de [Android: layouts y navegación](https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-and-nav-patterns).

Propuestas de agrupación, sujetas al inventario real de cada rol:

- Donante: citas, campañas, expediente y avisos; cuenta en un lugar estable.
- Transporte: traslados, pendientes de sincronización, avisos y cuenta.
- Operador, coordinador y médico: accesos a sus consultas y tareas existentes; no copiar los permisos de otro perfil para llenar un menú.

Al seleccionar un destino, su título y contenido deben resultar visibles sin atravesar de nuevo una larga lista de botones. Conservar estado, foco, selección y filtros cuando el comportamiento existente lo permita. No conservar datos sensibles después de cerrar sesión ni introducir almacenamiento nuevo de expedientes.

Para cada recorrido, medir por separado:

- Activaciones de navegación: clics o toques para alcanzar el recurso o la acción.
- Entrada de datos y cambios de filtro.
- Confirmaciones, reautenticación y revisión obligatorias.
- Desplazamientos, retrocesos, dudas de orientación y esperas.
- Resultado correcto y posibilidad de recuperar un error.

Comparar el mismo rol, punto de partida, recurso y condiciones. Reducir pasos redundantes, no controles de seguridad. No imponer «todo en tres clics» ni prometer mejoras porcentuales sin medición: [NN/g explica los límites de esa regla](https://www.nngroup.com/articles/3-click-rule/).

## 5. Lenguaje de producto

Usar español claro, verbos concretos y términos consistentes. Distinguir nombres de destino —«Inventario», «Traslados»— de acciones —«Registrar unidad», «Consultar traslado»—. Reservar las siglas clínicas necesarias, como ABO/Rh y HLA, para su contexto.

| Texto o representación detectada | Dirección de presentación | Límite que debe conservarse |
| --- | --- | --- |
| `display_name`, `scheduled_at`, `severity`, `tenant_id` | Etiquetas como «Nombre», «Fecha programada», «Prioridad» o «Institución», si corresponden al significado real | No renombrar campos del contrato ni confundir severidad de aviso con urgencia clínica. |
| Rol `OPERATOR`, `COORDINATOR`, etc. | Nombre del perfil en español | No cambiar el conjunto de permisos. |
| «Ver detalle autorizado» | «Ver detalle» o el nombre del recurso | Mantener autorización y ámbito. |
| «Código MFA, si corresponde» | «Código de segundo factor» y ayuda breve sobre el autenticador | Conservar el requisito real de MFA y su mecanismo. |
| «Desde ISO 8601 con zona» | «Desde», control comprensible de fecha/hora y zona visible | Serializar el mismo valor; mantener zona, precisión y semántica de los límites. |
| «Recuperar operación /api/…» | Nombre de operación y estado de confirmación | Conservar la misma operación, clave de idempotencia y recuperación existente. |
| «La app no inventa requisitos clínicos» | Orientación sobre quién informa los requisitos y dónde consultarlos | No inventar requisitos ni ocultar la evaluación profesional. |
| «No hay instituciones con publicación autorizada» | «No hay instituciones publicadas» en la vista pública, si expresa fielmente el resultado | No publicar instituciones ni fingir una falla del servicio. |
| UUID como título o selector | Nombre autorizado existente y referencia secundaria | Si falta el nombre, mostrar la referencia real con ayuda; no resolverlo mediante datos de otro ámbito. |

Estos ejemplos no constituyen un reemplazo global de cadenas. Revisar cada contexto. En particular, `AUTHORIZED` en un resultado documental no debe traducirse a «Aprobado clínicamente». `NOT_CHECKED`, rechazo, obsolescencia y dato ausente conservan significados diferentes.

No eliminar palabras como «simulado», «sintético» o «pendiente» cuando describen la realidad. Retirar lenguaje de desarrollo de la presentación normal solo cuando no comunica un límite operativo necesario. No añadir reseñas, métricas, instituciones, campañas o resultados ficticios para llenar espacios.

## 6. Formularios y confirmaciones

- Etiquetas persistentes; el placeholder solo aporta un ejemplo, nunca sustituye la etiqueta.
- Ayuda breve junto al campo; condiciones extensas donde se necesiten. No repetir documentación técnica en toda pantalla.
- Agrupar campos por tarea; distinguir lo obligatorio y lo opcional sin cambiar validadores.
- Fechas con entrada legible y zona explícita cuando afecta la decisión. Conservar el límite final exclusivo de los filtros que lo tengan.
- Errores junto al campo y resumen navegable cuando haya varios. Mantener foco y lectura accesible; conservar entradas permitidas y la limpieza segura de contraseñas existente.
- La confirmación identifica recurso, acción, consecuencia y destinatario pertinente. No usar un genérico «¿Seguro?» para una transferencia de custodia.
- Una operación enviada no se considera completada hasta recibir la confirmación prevista. El indicador de carga no cambia ese contrato.
- No añadir autoguardado, envíos automáticos, nueva captura de datos, operaciones masivas o validaciones clínicas bajo la etiqueta de UX.

La organización de errores toma como referencia el [resumen de errores de NHS](https://service-manual.nhs.uk/design-system/components/error-summary). Aplicar el patrón al sistema existente; no importar su framework ni duplicar la validación del servidor.

## 7. Listas, tablas, detalle y paneles

**Listas y tablas.** Encabezado claro, herramientas agrupadas, filtros activos reconocibles y cantidad de resultados con significado. Los campos principales deben ayudar a distinguir registros: tipo, identificador operativo, estado, ubicación y fecha según el recurso y permisos. Orden, búsqueda, filtros y paginación siguen utilizando los mecanismos existentes.

Reducir el peso visual de controles redundantes cuando existe una sola página. Conservar el recuento y el acceso a todas las funciones. La exportación debe seguir indicando su alcance real; «Exportar página CSV» no se renombra a «Exportar todo».

**Detalle.** Presentar contexto y acciones antes de secciones secundarias. Distinguir vista rápida de expediente completo. Si una tarea exige siempre abrir el expediente tras la vista rápida, ofrecer acceso claro al destino ya existente; no insertar otra confirmación ni ejecutar acciones al seleccionar una fila.

**Paneles.** Priorizar accesos y pendientes del perfil frente a gráficos extensos cuando esa sea su tarea principal. Conservar Highcharts en web, valores, filtros, periodos, denominadores, unidades y contexto. No reemplazar gráficas por adornos ni fabricar indicadores.

**Adaptación.** En teléfono, transformar listas en resúmenes cuando facilite lectura; en escritorio, conservar tablas para comparar. No ocultar campos esenciales solo para evitar desplazamiento. Una tabla o mapa puede tener desplazamiento propio sin desbordar toda la interfaz.

La [tabla de datos de IBM Carbon](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines) aporta organización de herramientas, densidad y detalle progresivo. Sus variantes no autorizan añadir ordenamiento, selección masiva o exportaciones que Red House no tenga.

## 8. Estados, alertas y confianza

| Estado real | Presentación exigida |
| --- | --- |
| Carga inicial | Indicar que se está consultando; no mostrar un cero como dato definitivo. |
| Vacío válido | Explicar qué no existe todavía y la acción disponible, si corresponde. |
| Sin coincidencias | Mostrar filtros aplicados y cómo ajustarlos con controles existentes. |
| Sin permiso | Mensaje seguro y salida útil, sin revelar datos restringidos. |
| Sin conexión o dependencia caída | Identificar la limitación en lenguaje operativo; conservar último dato con su antigüedad cuando ya esté disponible. |
| Pendiente local | Indicar que aún no se ha confirmado en servidor. |
| Resultado incierto | Mantener advertencia y recuperación existente; evitar check verde o invitación a repetir como nueva operación. |
| Conflicto o dato obsoleto | Explicar que cambió la información y presentar la salida autorizada existente. |
| Éxito confirmado | Acción y recurso reconocibles; comunicar solo lo que confirmó el sistema. |
| Error o rechazo | Explicación útil y siguiente paso disponible; no exponer trazas, secretos ni XML/JSON íntegro. |

Usar icono, texto y color coherentes. Los avisos de éxito no deben compartir automáticamente el mismo icono con advertencias o fallos. Los mensajes críticos no desaparecen por un temporizador breve. Separar estado de red, estado del servicio y resultado de la operación.

En rastreo, distinguir conexión, última posición recibida, antigüedad, precisión y procedencia. Mantener atribución del mapa y origen simulado cuando corresponda. Un trazo entre coordenadas no se presenta como ruta vial ni una estimación como tiempo medido.

En documentos, distinguir capturado, pendiente de carga, cargado, pendiente de verificación/análisis y disponible, según los estados reales. Una animación nunca acredita carga, análisis o entrega.

La separación semántica de colores se apoya en [NHS: Colour](https://service-manual.nhs.uk/design-system/styles/colour). Se adapta a la marca de Red House sin copiar colores institucionales ajenos.

## 9. Accesibilidad y uso real

Objetivo web: comprobar los criterios WCAG 2.2 AA aplicables al alcance modificado, sin declarar conformidad total por una herramienta automática. Referencia: [WCAG 2.2](https://www.w3.org/TR/WCAG22/).

- Contraste de texto de al menos 4,5:1, o 3:1 para texto grande según la definición WCAG; comprobar también ayudas, badges y enlaces sobre fondos oscuros.
- Contraste no textual de al menos 3:1 donde lo exige el criterio 1.4.11 para identificar controles y estados.
- Texto ampliable al 200 % y reflow a 320 CSS px, con las excepciones previstas para contenido bidimensional.
- Navegación completa con teclado, foco visible y no totalmente oculto por barras o diálogos; orden de lectura coherente.
- Objetivos de puntero web conformes al criterio 2.5.8 de 24×24 CSS px o sus excepciones. Preferir áreas cómodas, no diseñar alrededor de la excepción.
- En Android, áreas táctiles de al menos 48 dp y semántica comprobada con TalkBack, conforme a [Compose: accesibilidad de componentes](https://developer.android.com/develop/ui/compose/accessibility/api-defaults). No equiparar dp y CSS px.
- Etiquetar iconos interactivos. El tooltip no sustituye al nombre accesible ni a una etiqueta visible cuando el icono resulta ambiguo.
- Comprobar teclado virtual, barras del sistema, orientación y aumento de fuente. Los botones no pueden quedar inaccesibles bajo el teclado.
- Respetar reducción de movimiento. No introducir animaciones continuas, loaders decorativos o transiciones que retrasen la operación.
- En móvil compartido, no romper accesibilidad, áreas seguras ni adaptadores iOS. La verificación Android no acredita VoiceOver ni ejecución física iOS.

Estas medidas son umbrales de uso y accesibilidad. No convierten el trabajo en una auditoría de alineación milimétrica.

## 10. Aplicación específica al móvil

Conservar Compose Multiplatform y el comportamiento nativo. La cercanía al monolito debe verse en marca, paleta, vocabulario, componentes y estados; no en una WebView.

- Acceso con marca reconocible, campos claros y acción principal. Mantener visible la posibilidad de segundo factor cuando corresponda; no modificar el flujo de autenticación.
- Encabezado de trabajo con título y contexto breve. La conectividad debe ser discreta en situación normal y clara cuando limita una acción.
- Una tarea seleccionada ocupa el área principal. Separar cuenta, notificaciones y recuperación de operaciones del cuerpo de todas las pantallas.
- Donante: organizar cita, campañas y expediente sin duplicar rutas conceptuales ni retirar operaciones que hoy se alcanzan por entradas distintas.
- Transporte: mostrar recurso/tarea, origen, destino, estado y siguiente acción autorizada. Mantener QR, sello, contraparte, motivo y confirmaciones requeridos.
- Operador, coordinador y médico: adaptar las consultas y capturas existentes a sus permisos reales; no convertir al móvil en una consola clínica nueva.
- Sincronización: comunicar estado por observación con fecha y acción disponible. Nunca presentar una observación pendiente como una transferencia de custodia completada.
- Mantener las protecciones de pantalla y privacidad, incluida `FLAG_SECURE`. No desactivarlas para conseguir capturas de aceptación.

## 11. Reglas vinculantes para el diseño de etapa 05

La etapa 05 ya establece **Python y PySide6** en `apps/desktop/`. Este documento no desarrolla esa aplicación ni abre otra selección tecnológica. Sus reglas se incorporarán al ejecutar el encargo 05, junto con todos sus requisitos XML/XSD y de seguridad.

| Familia de trabajo de 05 | Regla de diseño |
| --- | --- |
| DESK-01 y DESK-12: panel y analítica | Datos, filtros, periodo y navegación relacionada claros; gráficos nativos compatibles con Qt. No imponer Highcharts ni copiar el dashboard web. |
| DESK-02: administración | Institución y alcance siempre identificables; separar acciones sobre cuentas de acceso clínico. |
| DESK-03, DESK-04 y DESK-05: inventario, laboratorio y solicitudes | Tablas comparables, filtros estables, selección visible y detalle contextual. Formularios agrupados por tarea. |
| DESK-06, DESK-07 y DESK-08: compatibilidad, logística y reservas | Separar recomendación, completitud, dictamen y asignación. Mostrar razones, versiones y revisión humana sin reducirlo a «Aprobado». |
| DESK-09, DESK-10 y DESK-11: custodia, frío y trazabilidad | Línea de eventos legible, responsables y tiempos; identificar alertas y pendientes sin alterar historia ni umbrales. |
| DESK-13: etiquetas e impresión | Vista previa clara, recurso, cantidad y destino. Distinguir generar un archivo, enviar un trabajo e imprimir físicamente. |
| DESK-14: auditoría y alertas | Consulta densa pero legible; filtros y referencias pertinentes para el rol autorizado. No mostrar XML bruto como interfaz operativa. |

Reglas transversales para la ventana nativa:

1. Marca, institución, perfil y módulo reconocibles. La densidad mayor no autoriza letra diminuta.
2. Operación por teclado con foco, tabulación lógica, atajos documentados y alternativas accesibles al doble clic.
3. Separar selección de fila, apertura de detalle y ejecución de una operación. Un clic de exploración nunca realiza una escritura de negocio.
4. Evitar cadenas de diálogos para consultar información relacionada. Usar paneles o vistas cuando conserven contexto.
5. Acciones frecuentes visibles; secundarias agrupadas; irreversibles con recurso y consecuencia antes de confirmar.
6. Progreso, cancelación y resultado de tareas largas conforme a lo exigido por etapa 05; no inventar porcentajes ni comunicar una cancelación no confirmada.
7. Presentar conflicto, desconexión y resultado incierto mediante los estados reales. No habilitar operaciones críticas offline por razones de comodidad.
8. Validar escalado del sistema, redimensionado, foco, lectura y uso prolongado en los sistemas efectivamente probados.
9. Mantener interfaz nativa. Un renderizador cartográfico justificado no convierte el producto en una web empaquetada.
10. Evaluar coherencia mediante tareas equivalentes y vocabulario compartido, no mediante capturas idénticas entre plataformas.

## 12. Referencias y fuerza de la evidencia

Referencias consultadas el **10/11/2026**. NHS aporta un sistema real para servicios de salud; Android documenta patrones de aplicaciones nativas; Carbon aporta patrones empresariales de IBM. WCAG establece criterios verificables; NN/g aporta análisis del costo de navegación.

Son referencias de diseño reales y documentadas. **No demuestran por sí mismas que el rediseño propuesto funciona para los usuarios de Red House.** Las adaptaciones de este documento son decisiones de diseño que deben contrastarse mediante recorridos y, cuando sea posible, usuarios representativos. No atribuirlas a una validación clínica ni a un estudio que no se realizó.

Transferir principios y comportamiento, no copiar marcas, textos, productos completos ni funcionalidades de los ejemplos. No instalar React, el frontend NHS u otra biblioteca ajena para imitar una referencia.

## 13. Puerta de aceptación visual y de uso

Un incremento cumple estas instrucciones cuando:

- Mantiene la identidad reconocible y explica los cambios de jerarquía.
- Cada ruta y acción previa autorizada sigue accesible para el mismo perfil.
- Los estados y textos describen el mismo hecho antes y después.
- Mejora una fricción identificada con evidencia; no se limita a recolorear.
- Conserva formularios, resultados, filtros y recuperación sin cambiar reglas, contratos ni datos.
- Los recorridos comparados indican clics/toques, desplazamientos, confirmaciones y resultado, sin cifras inventadas.
- La revisión visual incluye tamaño amplio y compacto, estados normales y degradados, teclado y aumento de texto.
- Distingue lo observado, lo inferido, lo probado y lo pendiente. Una captura atractiva no sustituye una tarea completada.
