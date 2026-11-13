# Guía de ejecución y comprobación por etapa

Usa esta guía para encargar cada etapa de la entrega final y revisar si realmente cumple su objetivo. Cada sección contiene un prompt inicial para implementar, un prompt de comprobación para auditar y una lista de resultados que debes exigir al terminar la revisión.

Los bloques son encargos listos para copiar. Los requisitos completos permanecen en los archivos 01 a 08 y en el complemento transversal 09; estas listas los ayudan a comprobar y no sustituyen ni reducen su alcance. Este documento no indica que las etapas ya estén implementadas o aprobadas.

Incluye como requisito transversal el [complemento 09 de rastreo GPS por WebSockets y mapa de Nuevo León](09_rastreo_gps_websockets.md), aplicado **desde el prompt 01**. Distingue datos simulados de captura móvil: Android se prueba en emulador sin requerir teléfono; iOS en iPhone físico autorizado, sin descargar Simulator. GPS externo queda opcional. Esta dependencia no justifica entregar solo diseño, polling o puntos animados sin backend.

Aplica también las decisiones vigentes de `00_contexto_y_reglas.md`: archivos privados en servidor como modo operativo, GCS opcional para producto con verificación académica separada; sin offline universal; push FCM/APNs externo pendiente sin preparar cuentas, con bandeja/adaptadores verificables. macOS y Windows 11 son plataformas de trabajo; Linux es objetivo adicional por comprobar. Donante inicia en feed de campañas/citas y comparte texto público con selector nativo; transportista tiene mapa protagonista, tarea y siguiente acción. Conserva cinco roles. Revisión visual significa observar pantallas renderizadas y recorridos completos; métricas de píxeles no la sustituyen. Video, exposición, «ubiquitous», reflexiones y entrega individual requieren intervención humana.

## Cómo usar la guía

1. Abre el proyecto Red House y una conversación para la etapa que corresponda al estado vigente. No reinicies 01/02 si ya están implementadas; para la continuación revisada el 11/11/2026 aplica el bloque siguiente.
2. El archivo `00_contexto_y_reglas.md` se lee en todas las etapas. No requiere una ejecución separada.
   Lee también `09_rastreo_gps_websockets.md` desde la etapa 01; las siguientes ya lo referencian. Si aún no has empezado, basta seguir los prompts 01 a 08 con ese complemento. Si ya avanzaste sin rastreo, usa el encargo específico de la sección 09 antes de cerrar 07 y 08.
3. Cuando el agente termine, pega el prompt de comprobación de esa misma etapa. Puedes usar el mismo chat o un chat de revisión separado dentro del mismo proyecto para contrastar de manera independiente.
4. Si la revisión encuentra defectos, vuelve al chat de implementación para corregirlos y repite la comprobación de los criterios afectados.
5. Al pasar a la siguiente etapa, abre un chat nuevo en el mismo proyecto. No hace falta copiar toda esta conversación: los prompts, contratos, evidencias y `PROJECT_STATUS.md` deben conservar el contexto.
6. Si el agente se interrumpe antes de terminar una etapa, continúa esa implementación; no avances solamente porque produjo un mensaje final.

La ubicación del proyecto es `/Users/victorberlanga/Programacion/integracion/Red-House`. Los prompts siguientes usan rutas relativas a esa raíz.

## Continuación autorizada desde el cierre de 04 — 11/11/2026

Conserva los archivos de prompts 00–04. Las correcciones y verificaciones heredadas se encargan mediante [Continuidad obligatoria de las etapas 01 a 04](07_integracion_pruebas_y_rendimiento.md#continuidad-obligatoria-de-las-etapas-01-a-04), con diez criterios CONT y registro único en `documentation/entrega-final/continuidad/Matriz.md` al ejecutar. 05 registra/resuelve dependencias de escritorio; 06 completa controles, proveedores y ensayos compartidos; 07 corrige clientes y comprueba integración; 08 recibe los resultados y entrega los artefactos. Leer ese bloque desde 05/06 no requiere ejecutar antes toda la etapa 07.

Este traslado fue solicitado para continuar en etapas posteriores; no acredita cierre de 03/04 ni permite omitir defectos. Conserva criterio abierto con dueño y aceptación. Reutiliza evidencia aplicable y repite solo lo afectado/no comprobado. Android se acepta en emulador; iOS en iPhone autorizado, sin descargar Simulator. Compilar, firmar, instalar y ejecutar son comprobaciones distintas.

Para diseño en 05 y correcciones de UI en 07, lee [instrucciones UI/UX](../instrucciones_diseno_ui_ux.md) y [corrección de calidad visual](../corregir_calidad_visual_web_movil.md). Exige criterios previos y recorridos por familia/rol; una captura o compilación no acredita experiencia terminada.

## Protocolo de comprobación

Todos los prompts de comprobación de esta guía deben aplicar este protocolo:

- Lee `AGENTS.md`, `PROJECT_STATUS.md`, `stuff/prompts/entrega-final/00_contexto_y_reglas.md` y el archivo de la etapa completo. Consulta CodeGraph antes de localizar o leer código cuando exista el índice.
- Desde 05, contrasta también CONT-01…CONT-10 de 07 y su registro de continuidad cuando exista. Si aún no existe, informa esa brecha sin crearlo durante una auditoría de solo lectura. Aplica las decisiones vigentes de plataforma y los criterios de diseño; no reinicies encargos históricos para sustituir el traspaso.
- Revisa también `stuff/prompts/entrega-final/09_rastreo_gps_websockets.md` y sus criterios TRACK-01 a TRACK-10 según la etapa. Distingue mapa actual, conexiones WSS reales, origen simulado/teléfono y resultados de integración móvil; GPS externo opcional; mantén JSON en Android/iOS y XML/XSD en escritorio.
- Realiza una auditoría del estado real. No implementes correcciones, cambies requisitos ni edites código, contratos, documentación o `PROJECT_STATUS.md` durante la comprobación. Entrega el informe en el chat; el usuario podrá encargar después las correcciones.
- Puedes ejecutar pruebas existentes únicamente con datos ficticios en un entorno temporal aislado, sin modificar los datos habituales, detener servicios activos ajenos, desplegar o publicar. Si ese entorno no está disponible, revisa la evidencia existente e identifica expresamente qué no pudo verificarse. No uses producción como entorno de prueba.
- Contrasta cada requisito con implementación, contrato, prueba y resultado. Comprueba fecha, versión/commit o manifiesto/hash de fuentes de la evidencia; los cambios sin commit también deben quedar identificados. Un resultado histórico no demuestra que el código modificado siga funcionando.
- Distingue inspección estática, prueba recién ejecutada y evidencia previa aplicable. Un mock, una pantalla, un readiness 200 o una compilación no bastan para acreditar un flujo con persistencia y autorización.
- No inventes umbrales de aceptación, requisitos clínicos o autorizaciones. Separa lo exigible ahora de lo que el prompt remite expresamente a una etapa posterior.
- Para cada requisito usa uno de estos estados: **APROBADO**, **PARCIAL**, **FALLIDO** o **NO VERIFICADO**. Registra las dependencias externas aparte; no las conviertas en aprobaciones.

El informe debe incluir esta estructura:

| Campo | Qué debe contener |
| --- | --- |
| Requisito | ID o criterio concreto del prompt, incluyendo sus requisitos obligatorios |
| Estado | Aprobado, parcial, fallido o no verificado |
| Implementación | Archivo/símbolo, contrato, migración, pantalla o artefacto verificable |
| Evidencia | Caso/comando, fecha, entorno, fuentes probadas y archivo/resultado |
| Brecha | Qué falta o qué prueba no pudo reproducirse |
| Dependencia | Técnica de esta etapa, etapa posterior explícita o requisito externo |
| Acción de cierre | Corrección o verificación concreta, en orden de prioridad |

Termina con uno de estos veredictos:

- **APTA PARA CONTINUAR:** todos los criterios obligatorios de la etapa tienen evidencia aplicable y no hay defectos que bloqueen las siguientes.
- **NO APTA PARA CONTINUAR:** falta una función requerida, existe un fallo o no se ha verificado un criterio obligatorio necesario para la siguiente etapa. Enumera los bloqueos.
- **CONTINUACIÓN PARCIAL POR DEPENDENCIA DECLARADA:** hay una dependencia externa o una comprobación que requiere un componente de una etapa posterior identificada. La etapa sigue sin cerrarse; solo se puede avanzar en tareas independientes o necesarias para resolver esa dependencia. Explica exactamente qué debe retomarse. No uses esta opción para aplazar defectos del componente actual.

La aprobación de una etapa no equivale a aprobación de toda la plataforma ni a certificación clínica. Los puntos abiertos deben volver a comprobarse en la integración y en el cierre final. Para la etapa 08, un pendiente obligatorio impide declarar completa la entrega.

## 01 Backend y microservicios

Requisito completo: [Backend y microservicios](01_backend_y_microservicios.md).

### Prompt inicial

```text
Lee y ejecuta stuff/prompts/entrega-final/01_backend_y_microservicios.md.
Lee también AGENTS.md, PROJECT_STATUS.md y stuff/prompts/entrega-final/00_contexto_y_reglas.md.
Completa implementación, integración, pruebas y documentación. No te limites a un plan.
Conserva la base compartida y los datos existentes. Cubre las 24 responsabilidades recomendadas, justificando agrupaciones o separaciones sin imponer 24 procesos ni duplicar reglas.
Incluye el receptor/adaptador GPS móvil, simulador, contratos WSS JSON/XML, persistencia y recuperación definidos en la especificación de rastreo.
Actualiza PROJECT_STATUS.md con criterios cumplidos, evidencias y pendientes reales.
```

### Prompt de comprobación

```text
Audita la etapa 01 contra stuff/prompts/entrega-final/01_backend_y_microservicios.md completo.
Aplica el Protocolo de comprobación de stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md. Revisa, no implementes correcciones.
Comprueba BE-01 a BE-24, la evolución desde los once servicios iniciales, límites y propietarios, contratos JSON/XML/XSD, persistencia, migraciones, permisos, eventos e idempotencia.
Verifica reservas y cupos concurrentes, rechazo institucional, revisión humana y recuperación de escrituras inciertas. No cuentes réplicas como servicios ni capacidades futuras como implementadas.
Comprueba ingreso GPS simulado, asignación del emisor, canal WSS real, persistencia, formatos JSON/XML, cursor y reconexión; la captura física móvil se acepta en 04/07; GPS externo es opcional.
Distingue la infraestructura técnica de HLA de la evaluación detallada de la etapa 02 y de cualquier aprobación clínica externa.
Entrega la matriz de requisitos, evidencia aplicable al código actual, brechas y acciones de cierre. Termina con el veredicto definido en el protocolo.
```

### Qué debes obtener de la comprobación

- Una matriz con los **24 elementos BE-01 a BE-24**, propietario actual/final, decisión de agrupación o extracción y evidencia por función.
- Cantidad real de servicios independientes, módulos y réplicas, contados por separado, sin reglas ni autoridades duplicadas.
- Evidencia de altas/consultas/comandos persistidos y de contratos JSON/XML/XSD, incluidos errores y autenticación.
- Resultado de migración/instalación y conservación de datos, permisos e historia; no solo SQL escrito.
- Pruebas de que un usuario ajeno no dicta/libera/reserva y de que dos intentos concurrentes no generan doble reserva o sobrecobertura.
- Comprobación de estados pendientes, eventos y reanudación tras pérdida de respuesta; dependencias inaccesibles no producen éxito falso.
- Contratos y prueba ejecutada de ingreso GPS normalizado, WSS, persistencia y recuperación con simulador, distinguiendo permisos de emisor/suscriptor e integración física pendiente.
- Lista exacta de lo que impide cerrar el backend y de lo expresamente pendiente de las etapas 02 o 06, sin ocultar faltantes de BE-01 a BE-24.

Señales de etapa incompleta: endpoints vacíos, autoridad duplicada para reservar, contratos solo JSON, migraciones no ensayadas o una responsabilidad omitida por agruparla con otra.

## 02 Reglas clínicas y algoritmos

Requisito completo: [Reglas clínicas y algoritmos](02_reglas_clinicas_y_algoritmos.md).

### Prompt inicial

```text
Lee y ejecuta stuff/prompts/entrega-final/02_reglas_clinicas_y_algoritmos.md.
Lee también AGENTS.md, PROJECT_STATUS.md y stuff/prompts/entrega-final/00_contexto_y_reglas.md.
Implementa, integra, prueba y documenta las ampliaciones HLA y los algoritmos explicables, conservando versiones e historia.
Separa ubicación GPS observada, recorrido recibido por WebSockets, ruta planificada y ETA; documenta fuente, antigüedad y calidad.
No inventes reglas clínicas ni aprobaciones profesionales. Completa los mecanismos técnicos y los casos sintéticos permitidos; identifica las dependencias clínicas externas.
Actualiza PROJECT_STATUS.md con resultados y pendientes verificables.
```

### Prompt de comprobación

```text
Audita la etapa 02 contra stuff/prompts/entrega-final/02_reglas_clinicas_y_algoritmos.md completo.
Aplica el Protocolo de comprobación de stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md. Revisa, no implementes correcciones.
Comprueba registro HLA y datos inmunológicos, procedencia/versiones, completitud, evaluación y dictamen como conceptos separados. Verifica que ABO coincidente o HLA completo no generan aprobación automática.
Audita ALG-01 a ALG-05, sus explicaciones, fuentes, restricciones, política operativa, oráculos, métricas y límites. Comprueba qué factores realmente cambian cada resultado y la obsolescencia de evaluaciones ante cambios críticos.
Verifica que cartografía actual o posiciones GPS no se presenten como tráfico, ETA medido, entrega o decisión clínica sin su fuente correspondiente.
No certifiques reglas clínicas por existir una cita normativa ni por pasar casos sintéticos.
Entrega la matriz de requisitos, evidencia aplicable al código actual, brechas y acciones de cierre. Termina con el veredicto definido en el protocolo.
```

### Qué debes obtener de la comprobación

- Evidencia de captura/consulta de resultados HLA vinculados a muestra y sujeto/recurso, con laboratorio, método, fechas, revisión e historia de correcciones.
- Pruebas de diferencias entre dato registrado, faltante/indeterminado, completitud, preselección/evaluación y dictamen humano.
- Catálogo de reglas con fuentes, versión, alcance y estado real de aprobación; perfiles sintéticos identificados y sin activación clínica indebida.
- Verificación de los cinco algoritmos: evaluación, logística/priorización, cobertura/balanceo, riesgo de caducidad e inconsistencias.
- Casos independientes que contrasten resultados, cambios de urgencia cuando la política la utiliza, desempates, exclusiones y obsolescencia.
- Métricas reproducibles y explicaciones en contratos JSON/XML, conservando evaluaciones históricas y sin crear reservas automáticamente.
- Separación verificable entre posición observada, trayecto, ruta y ETA, sin inventar movimiento ni usar puntos antiguos como mediciones actuales.
- Brechas técnicas separadas de las aprobaciones profesionales externas, con acciones precisas para cerrar cada una.

Señales de etapa incompleta: HLA reducido a texto libre sin procedencia, presentar ABO como trasplantabilidad, un ranking que afirma usar urgencia pero no la utiliza o ausencia de pruebas independientes de algoritmos.

## 03 Portal web

Requisito completo: [Portal web](03_portal_web.md).

### Prompt inicial

```text
Lee y ejecuta stuff/prompts/entrega-final/03_portal_web.md.
Lee también AGENTS.md, PROJECT_STATUS.md y stuff/prompts/entrega-final/00_contexto_y_reglas.md.
Completa las funcionalidades por perfil con persistencia real, privacidad, formularios, paneles y reportes.
Verifica los recorridos en navegador y conserva el backend modular autónomo y el modo HTTP explícito, sin fallback inseguro tras una escritura.
Implementa mapa interactivo actual de Nuevo León y rastreo del transportista por WSS, con permisos, fuente, antigüedad y reconexión.
Actualiza pruebas, documentación y PROJECT_STATUS.md con evidencias y pendientes reales.
```

### Prompt de comprobación

```text
Audita la etapa 03 contra stuff/prompts/entrega-final/03_portal_web.md completo.
Aplica el Protocolo de comprobación de stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md. Revisa, no implementes correcciones.
Comprueba tareas, pantallas y permisos de cada perfil, recuperación de acceso/MFA, formularios, agenda, inventario, laboratorio, evaluación, traslado, trazabilidad, documentos, auditoría, Highcharts y exportaciones.
Exige recorridos reales en navegador con persistencia, accesibilidad y rechazo por URL/exportación de datos ajenos. Una pantalla o un botón oculto no prueban autorización.
Verifica negocio web con las API detenidas en entorno aislado y el modo HTTP por separado. Distingue dependencias de infraestructura posteriores sin aprobar descargas o acciones no protegidas.
Comprueba posiciones sobre el mapa de Nuevo León mediante WSS real sin recarga/polling, con acceso por traslado y estados de dato antiguo, fuente simulada y desconexión.
Entrega la matriz de requisitos, evidencia aplicable al código actual, brechas y acciones de cierre. Termina con el veredicto definido en el protocolo.
```

### Qué debes obtener de la comprobación

- Mapa de pantallas/tareas/permisos para los siete perfiles, con pruebas de acceso positivo y negativo por institución.
- Recorridos en navegador de donación/procesamiento, solicitud/reserva/traslado y uso o destino final, con referencias a sus registros persistidos.
- Evidencia de validación por campo, valores conservados, CSRF, conflictos de versión, doble envío y recuperación de operación pendiente.
- Confirmación de que Highcharts y tablas/reportes representan datos autorizados y que filtros, totales y exportaciones son coherentes.
- Pruebas de documentos privados, estados pendientes/rechazados y restricciones de descarga.
- Resultado de autonomía funcional con API detenidas, no solamente acceso a página pública; y resultado independiente del modo HTTP.
- Mapa actual de Nuevo León con cobertura estatal/detalle local y actualización WSS autorizada; fuente y antigüedad visibles, reconexión y cartografía caída comprobadas.
- Capturas reales y resultados de teclado, tamaños de pantalla y errores JavaScript, con brechas y comandos para reproducir.

Señales de etapa incompleta: formularios sin guardar, reportes ficticios, recuperación de contraseña limitada a ayuda, acceso clínico por ser administrador o web que pierde todas sus funciones al detener las API.

## 04 Aplicación móvil Android/iOS

Requisito completo: [Móvil iOS y Android con Kotlin Multiplatform y Compose Multiplatform](04_aplicacion_android.md).

### Prompt inicial

```text
Lee y ejecuta stuff/prompts/entrega-final/04_aplicacion_android.md.
Lee también AGENTS.md, PROJECT_STATUS.md y stuff/prompts/entrega-final/00_contexto_y_reglas.md.
Construye una sola aplicación Kotlin Multiplatform con Compose Multiplatform, con vistas y operaciones por perfil, conectada a microservicios reales exclusivamente mediante JSON.
Completa sesión segura, QR, cámara, GPS, bandeja y adaptadores push, pruebas, APK para emulador y compilación/arranque en iPhone físico. No prepares cuentas FCM/APNs; su recepción física queda pendiente externa. No uses WebView.
Integra seguimiento WSS JSON y mapa de Nuevo León, diferenciando GPS de iPhone, emulador y adaptador para GPS externo futuro. Donante inicia en feed de campañas/citas y comparte texto público con selector nativo. Transportista usa mapa protagonista con tarea y siguiente acción.
Actualiza documentación y PROJECT_STATUS.md con resultados, plataformas verificadas y pendientes reales.
```

### Prompt de comprobación

```text
Audita la etapa 04 contra stuff/prompts/entrega-final/04_aplicacion_android.md completo.
Aplica el Protocolo de comprobación de stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md. Revisa, no implementes correcciones.
Comprueba APK/arranque Android en emulador y compilación/instalación/arranque en iPhone físico, aplicación multiplataforma con los cinco roles, consumo JSON real de al menos cuatro servicios y ausencia de conexión a bases/Redis o sesiones web internas.
Verifica feed/citas del donante, mapa/tarea/siguiente acción del transportista, operador/recepción y vistas de los otros roles; QR, cámara y GPS con alcance real. Verifica bandeja/adaptadores; FCM/APNs y recepción física quedan pendientes externos. Comprueba almacenamiento protegido, renovación/logout y privacidad.
Comprueba mapa de Nuevo León y WSS JSON real con reconexión y permisos. Datos de emulador se identifican; no equivalen a captura física iOS. Registra Android emulador e iPhone físico; GPS externo opcional.
Prueba pérdida de conexión solo para operaciones que admitan borrador/caché. Ninguna tarea local confirma reserva, liberación o cierre de custodia.
Distingue emulador, iPhone físico, proveedor externo y escritorio. Revisa visualmente pantallas renderizadas y completa recorridos reales; no uses métricas de píxeles como aceptación.
Entrega la matriz de requisitos, evidencia aplicable al código actual, brechas y acciones de cierre. Termina con el veredicto definido en el protocolo.
```

### Qué debes obtener de la comprobación

- Comando de compilación, resultado, APK identificable y prueba en emulador Android; añade evidencia de compilación, firma, instalación, arranque y recorrido en iPhone físico. No descargues Simulator ni exijas teléfono Android.
- Una app con vistas por perfil y evidencia JSON de al menos cuatro microservicios, sin credenciales o conexiones directas a almacenes.
- Recorridos reales de cita y traslado, con verificación QR, evidencia de cámara, ubicación y recepción/resultado autorizado.
- Prueba de bandeja/adaptadores push y apertura reautorizada; FCM/APNs y recepción física quedan pendientes externas. No prepares cuentas de proveedor.
- Verificación de almacenamiento cifrado, renovación coordinada, limpieza al salir y separación entre cuentas.
- Evidencia de borrador/caché solo para operaciones autorizadas, reconexión sin duplicación y rechazo de acciones críticas sin validación central; no exijas modo offline universal.
- Seguimiento JSON por WSS sobre mapa actual de Nuevo León, fuente distinguible, datos atrasados identificados y resultados físicos separados por teléfono; conserva pendientes los no comprobados. GPS externo opcional.
- Lista de pruebas que requieren el escritorio de la etapa 05 o integración de la 07; quedan abiertas hasta su ejecución, no se marcan aprobadas.

Señales de etapa incompleta: APK o compilación iOS no generados, pantallas con listas fijas, cámara/push no verificados, puntos animados sin WSS/backend, simulador presentado como GPS físico probado, tokens en texto plano o marca de entrega confirmada sin respuesta del servidor.

## 05 Aplicación de escritorio

Requisito completo: [Escritorio con PySide6 y Python](05_aplicacion_escritorio.md).

### Prompt inicial

```text
Lee y ejecuta stuff/prompts/entrega-final/05_aplicacion_escritorio.md.
Lee también AGENTS.md, PROJECT_STATUS.md y stuff/prompts/entrega-final/00_contexto_y_reglas.md.
Lee instrucciones_diseno_ui_ux.md y corregir_calidad_visual_web_movil.md en stuff/prompts, y la continuidad de 01–04 definida en 07. Adapta las reglas visuales a Qt sin ejecutar otro rediseño global.
Identifica contratos/roles por módulo y plataforma/arquitectura de entrega. Resuelve la sincronización de borradores con su propietario; no reutilices permisos TRANSPORT ni registres escritorio como GPS.
Construye una sola aplicación nativa PySide6 con Python, con módulos y operaciones por perfil, conectada a microservicios reales mediante XML/XSD.
Completa captura interna, inventario, evaluación autorizada, logística, impresión, reportes, sincronización permitida, pruebas y paquete ejecutable. No copies el portal en una WebView.
Incluye mapa actual de Nuevo León y seguimiento WSS XML/XSD, con acceso por traslado, recuperación y distinción entre datos simulados y GPS físico.
Actualiza documentación y PROJECT_STATUS.md con evidencias, plataformas probadas y pendientes reales.
```

### Prompt de comprobación

```text
Audita la etapa 05 contra stuff/prompts/entrega-final/05_aplicacion_escritorio.md completo.
Aplica el Protocolo de comprobación de stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md. Revisa, no implementes correcciones.
Comprueba reglas de diseño por familia y rol, tareas, teclado, foco, escalado y estados de error/conflicto/incertidumbre. Revisa la matriz inicial de contratos y el permiso real de cada borrador sincronizable.
Comprueba DESK-01 a DESK-14, aplicación nativa PySide6 por perfiles, uso XML de al menos cuatro servicios y validación XSD/DTO también para login, refresh, MFA y errores.
Verifica que no usa bases/Redis ni lógica clínica backend local; exige pruebas GUI reales, persistencia, permisos, concurrencia, tablas, exportaciones, etiquetas, recuperación y protección de credenciales.
Comprueba rechazo de XXE, XML inválido y JSON inesperado. Revisa offline/cambio de cuenta y coherencia con móvil Android/iOS JSON y web.
Verifica el mapa actual de Nuevo León actualizado por WSS XML/XSD, sin consumo JSON oculto de microservicios dentro del componente de mapa, con permisos/reconexión y antigüedad visibles.
Distingue generación de PDF de impresión física y paquete construido de plataforma realmente probada.
Entrega la matriz de requisitos, evidencia aplicable al código actual, brechas y acciones de cierre. Termina con el veredicto definido en el protocolo.
```

### Qué debes obtener de la comprobación

- Matriz de los **14 módulos DESK-01 a DESK-14**, con pantalla, rol, permiso, operación XML y prueba.
- Criterios y resultados visuales por familia/rol, con tareas, teclado, escalado y estados; dependencias CONT identificadas sin aceptación ficticia.
- Evidencia XML/XSD/DTO de al menos cuatro servicios, incluidos autenticación, comandos y errores; rechazo de XXE y formato inesperado.
- Recorridos GUI de captura/inventario, revisión/reserva, programación/recepción y auditoría, según las facultades de cada perfil.
- Resultado de búsqueda/filtros/paginación, exportaciones PDF/CSV/XLSX, etiquetas escaneables y vista previa; impresión física identificada o pendiente explícito.
- Pruebas de conflicto de versión, escritura incierta, renovación/logout, credenciales protegidas y borradores permitidos sin confirmación crítica offline.
- Un paquete ejecutable e instrucciones de instalación/arranque, con sistemas operativos realmente verificados y dependencias declaradas.
- Un caso relacionado con móvil Android/iOS JSON y web, conservando identificadores, estado y ámbito, o una dependencia de integración documentada que no se presenta como prueba aprobada.
- Mapa y trayecto en vivo por WSS XML/XSD con mismos eventos que web/Android, diferenciando datos simulados, desconexión y cartografía caída, sin convertir la consola en copia del portal.

Señales de etapa incompleta: login en JSON aunque las consultas usen XML, interfaz bloqueada durante red, módulos vacíos, reglas de compatibilidad copiadas al cliente o afirmación de soporte Windows sin haberlo comprobado.

## 06 Seguridad infraestructura y continuidad

Requisito completo: [Seguridad e infraestructura](06_seguridad_infraestructura_y_continuidad.md).

### Prompt inicial

```text
Lee y ejecuta stuff/prompts/entrega-final/06_seguridad_infraestructura_y_continuidad.md.
Lee también AGENTS.md, PROJECT_STATUS.md y stuff/prompts/entrega-final/00_contexto_y_reglas.md.
Lee la continuidad de 01–04 definida en 07 y documentation/entrega-final/portal/Aceptacion_integrada_06.md. Comprueba entorno vigente y resuelve I06-01…09 y CONT aplicables, sin asumir ausencias o esquemas históricos.
Completa y verifica almacenamiento privado servidor/ClamAV. Verifica GCS como criterio académico independiente si hay acceso autorizado; es opcional en el producto. No prepares cuentas FCM/APNs: comprueba bandeja/adaptadores y marca recepción física pendiente externa.
Completa y verifica seguridad, MFA/reautenticación, privacidad, análisis de archivos, infraestructura, monitoreo, respaldos y recuperación con RTO/RPO.
Configura y prueba WSS/gateway, autorización continua del rastreo GPS, reconexión entre réplicas, retención de ubicación y fallo de cartografía.
Conserva datos y autorizaciones vigentes. Ensaya fallos/restauraciones en entornos aislados; no publiques cambios productivos sin autorización vigente.
Actualiza evidencias, documentación y PROJECT_STATUS.md distinguiendo implementación, prueba real, diseño futuro y pendiente externo.
```

### Prompt de comprobación

```text
Audita la etapa 06 contra stuff/prompts/entrega-final/06_seguridad_infraestructura_y_continuidad.md completo.
Aplica el Protocolo de comprobación de stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md. Revisa, no implementes correcciones.
Comprueba I06-01…09 y CONT aplicables con entorno/versión actuales. Exige ciclo documental del servidor y prueba GCS académica independiente. Separa bandeja/adaptadores push de recepción física FCM/APNs pendiente.
Comprueba SEC-01 a SEC-03 e INF-01 a INF-04 con evidencia: MFA, reautenticación, JWT/Redis, aislamiento institucional, documentos privados/antimalware, contenedores, HTTPS, workers y CI.
Verifica caída de una réplica, servicio completo, PostgreSQL/Redis/MongoDB y almacenamiento privado. Prueba GCS caído como escenario separado/opcional cuando aplique. Confirma rechazo seguro y recuperación sin duplicados.
Audita WSS, orígenes web, identidad de GPS/puente, suscripción por traslado, revocación con socket abierto, reconexión/cursor y límites; Redis inaccesible no autoriza continuar entregando posiciones protegidas.
Exige respaldo restaurado, comparación de datos/permisos/objetos y objetivos frente a RTO/RPO medidos; no aceptes como restauración un archivo de backup existente.
Identifica lo realmente desplegado, lo probado localmente, lo solo diseñado y las dependencias externas pendientes.
Entrega la matriz de requisitos, evidencia aplicable al código actual, brechas y acciones de cierre. Termina con el veredicto definido en el protocolo.
```

### Qué debes obtener de la comprobación

- Matriz de seguridad con intentos rechazados por rol, institución, asignación, sesión/dispositivo revocado y reautenticación reutilizada.
- Resultado de I06-01…09 y criterios CONT a cargo de 06; bandeja/adaptadores, push físico externo pendiente y prueba académica GCS separados en el registro.
- Evidencia de que archivos pendientes/rechazados no se descargan como limpios, del motor antimalware y de la recuperación cuando falla el análisis o GCS.
- Inventario desplegable de imágenes, procesos, workers, puertos, secretos y redes, conservando PostgreSQL compartido y mínimo privilegio.
- Matriz de fallos con esperado/obtenido: réplica, servicio completo, almacenes, gateway, worker y host, señalando lo probado frente a lo diseñado.
- Ensayo de restauración aislada con conteos/hashes/relaciones, permisos, TTL, referencias/objetos y operaciones pendientes; objetivos numéricos y mediciones RTO/RPO sustentados.
- Estado real de CI, HTTPS, renovación, monitoreo y alertas, sin atribuir éxito remoto a una configuración que no se ejecutó.
- Límites explícitos de infraestructura y pendientes externos, con prioridades de cierre y sin prometer multizona o certificación clínica inexistentes.
- Evidencia WSS de autorización continua y rechazo de dispositivos/usuarios ajenos, recuperación de réplica y distinción entre GPS sin señal, canal caído, persistencia caída y proveedor cartográfico inaccesible.

Señales de etapa incompleta: permisos solo en botones, Redis caído con acceso protegido permitido, PostgreSQL caído con escrituras confirmadas, antivirus sustituido por comprobar MIME o respaldos nunca restaurados.

## 07 Integración pruebas y rendimiento

Requisito completo: [Integración y pruebas](07_integracion_pruebas_y_rendimiento.md).

### Prompt inicial

```text
Lee y ejecuta stuff/prompts/entrega-final/07_integracion_pruebas_y_rendimiento.md.
Lee también AGENTS.md, PROJECT_STATUS.md y stuff/prompts/entrega-final/00_contexto_y_reglas.md.
Resuelve CONT-01…CONT-10 de la sección Continuidad obligatoria de las etapas 01 a 04; conserva sus prompts y evidencia, corrige brechas concretas y actualiza documentation/entrega-final/continuidad/Matriz.md.
Aplica las reglas de diseño compartidas y verifica tareas de todos los roles, edición personal autorizada del donante, paginación superior a 100, MFA/accesibilidad, archivos, push y capacidades físicas. iOS se acepta en el iPhone autorizado; no descargues Simulator por una instrucción histórica.
Ejecuta los procesos completos entre web, móvil Android/iOS JSON y escritorio XML, con persistencia y permisos reales. Corrige los defectos técnicos encontrados.
Completa contratos, concurrencia, sincronización, fallos, restauración, volumen, Locust y usabilidad, conservando resultados actuales y reproducibles.
Demuestra GPS simulado a través del backend y WSS reales hasta los mapas de Nuevo León de web, móvil Android/iOS JSON y escritorio XML/XSD, con pruebas de seguridad, retrasos y recuperación.
Actualiza la matriz de cumplimiento, documentación y PROJECT_STATUS.md; no sumes ejecuciones repetidas como casos diferentes.
```

### Prompt de comprobación

```text
Audita la etapa 07 contra stuff/prompts/entrega-final/07_integracion_pruebas_y_rendimiento.md completo.
Aplica el Protocolo de comprobación de stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md. Revisa, no implementes correcciones.
Comprueba CONT-01…CONT-10, origen de cada brecha, propietario, criterio y evidencia actual. Una reducción de alcance requiere decisión explícita; no confundas aprobación clínica externa con defecto del mecanismo académico.
Comprueba E2E-A, E2E-B y E2E-C completos por Android e iOS, consulta entre productos con mismos IDs/estados/versiones, cuatro servicios por cliente y tareas reales en navegador/Android/iOS/PySide6.
Verifica criterios de usabilidad definidos antes de medir, todos los roles/familias, formatos comprensibles, accesibilidad y paginación sin truncamiento. Distingue lectura de código, fixtures y ejecución nativa/física.
Verifica contratos, roles/privacidad, concurrencia, borradores/cachés permitidos, revocación, recuperación y ausencia de confirmaciones falsas o efectos duplicados. No presupongas offline universal.
Comprueba TRACK-01 a TRACK-10: fuente simulada, ingreso/persistencia, WSS, mapa actual de Nuevo León, JSON/XML, orden/cursor, permisos y latencia extremo a extremo. No aceptes polling como WebSockets ni simulación como prueba física.
Audita dataset, condiciones y datos brutos de Locust: perfiles, usuarios, tasa, media/p95/p99, errores, recursos, saturación y recuperación. La comparación sin caché debe mantener seguridad Redis.
Vuelve a revisar los pendientes de etapas previas; no los consideres resueltos por haber llegado a integración. Distingue pruebas actuales, históricas, simuladas y no ejecutadas.
Entrega la matriz de requisitos, evidencia aplicable al código actual, brechas y acciones de cierre. Termina con el veredicto definido en el protocolo.
```

### Qué debes obtener de la comprobación

- Tres expedientes integrales: sangre hasta uso/destino, coordinación de órgano con autorizaciones registradas y donación desde Android o iOS hasta procesamiento/inventario.
- Al menos un caso que cruce móvil Android/iOS JSON, escritorio XML y web, con IDs, versiones, permisos y persistencia relacionados.
- Informe de regresión actual y matrices de contratos, seguridad, concurrencia y fallos, conservando errores/repeticiones sin inflar resultados.
- Demostración de recuperación tras desconexión para operaciones que admitan borrador/caché, sin duplicación ni confirmación crítica local, y recuperación segura ante caída de servicio/almacenes.
- Dataset reproducible, configuración Locust y resultados brutos con concurrencia, peticiones/s, latencias media/p95/p99, errores, recursos y recuperación.
- Recorridos de interfaz y usabilidad con alcance identificado: automatización o participantes reales, dispositivos y plataformas efectivamente probados.
- Expediente completo del rastreo con simulador, mensajes WSS reales, mapas de Nuevo León, seguridad/recuperación y métricas de emisores/suscriptores; aceptación móvil física diferenciada; GPS externo opcional.
- Matriz CONT-01…CONT-10 con resolución o pendientes heredados, separando fallos técnicos, decisiones de alcance y verificaciones externas; sin un aprobado global que oculte etapas incompletas.

Señales de etapa incompleta: solo pruebas de endpoints aislados, carga contra un único health check, p95/p99 sin datos brutos, apagar Redis para medir sin caché o E2E que nunca utiliza los clientes reales.

## 08 Documentación y entrega final

Requisito completo: [Documentación y entrega](08_documentacion_y_entrega.md).

### Prompt inicial

```text
Lee y ejecuta stuff/prompts/entrega-final/08_documentacion_y_entrega.md.
Lee también AGENTS.md, PROJECT_STATUS.md y stuff/prompts/entrega-final/00_contexto_y_reglas.md.
Recibe la matriz CONT-01…CONT-10 y resultados de 06/07; conserva los prompts 01–04. No cierres pendientes mediante cambios de redacción ni reiteres toda prueba vigente sin causa.
Consolida la entrega comprobada: informe editable/Word/PDF, manuales, modelos, diagramas, contratos, instalables, evidencias y guion de demostración.
Completa video final verificable, registro consolidado de incidencias, participación y reflexiones auténticas de cada integrante. Registra la aclaración de ubiquitous sin inventar plataforma o dispensa. Respeta la ruta autorizada de iOS físico.
Contrasta todo con código y resultados actuales; corrige defectos técnicos antes de describirlos como entregados. No inventes aprobaciones, participación, plataformas probadas ni enlaces de publicación.
Verifica los artefactos e instalaciones y actualiza PROJECT_STATUS.md con lo entregado y las brechas reales.
Incluye contratos WSS JSON/XML, manual del simulador/adaptador GPS, evidencia del mapa actual de Nuevo León y pruebas Android/iOS y aceptación de equipo externo solo si se incorpora.
```

### Prompt de comprobación

```text
Audita la etapa 08 y el cierre global contra stuff/prompts/entrega-final/08_documentacion_y_entrega.md completo y los criterios obligatorios de las etapas 01 a 07.
Aplica el Protocolo de comprobación de stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md. Revisa, no implementes correcciones.
Comprueba disposición final de CONT-01…CONT-10, incidencias, reflexiones individuales, checklist y artefacto del video final, y resolución o pendiente explícito de ubiquitous. No atribuyas al equipo testimonios ni autorizaciones inexistentes.
Comprueba que informe, manuales, modelos, diagramas, contratos, instalables y evidencia corresponden a la misma versión y describen lo realmente implementado.
Verifica matriz de las 24 responsabilidades sin imponer 24 procesos, instalación limpia, actualización/restauración, APK y compilación iOS, escritorio y demostración integrada. Revisa visualmente PDF y artefactos cuando sea posible, además de enlaces/índice/tablas.
Comprueba la documentación del GPS futuro, contratos/eventos WSS, permisos, mapa actual de Nuevo León con proveedor/actualización/atribución y evidencia del software con simulador, sin afirmar integración física inexistente.
Contrasta fuentes, límites clínicos, continuidad, RTO/RPO, contribuciones y publicación; no aceptes datos inventados ni cierre por existir documentos.
Lista todo criterio obligatorio pendiente. No declares completa la entrega final mientras falte implementación o verificación requerida.
Entrega la matriz de requisitos, evidencias aplicables, brechas y acciones de cierre. Concluye si la entrega está lista y bajo qué condiciones de operación demostradas.
```

### Qué debes obtener de la comprobación

- Índice navegable de archivos/artefactos y matriz final requisito/componente/permiso/prueba/evidencia/resultado, incluyendo los pendientes anteriores.
- Informe fuente, Word y PDF íntegros y coherentes, con portada real, referencias, índice, tablas/figuras y revisión visual documentada.
- Manuales ejecutables de instalación/operación, usuario por perfil, Android/iOS, escritorio, técnico y recuperación; sin secretos ni rutas privadas imprescindibles.
- Modelos y diagramas correspondientes al esquema/contratos y despliegue final, diferenciando infraestructura futura de la realmente desplegada.
- APK, artefacto iOS y paquete de escritorio identificados con versión, firma/instalación/ejecución diferenciadas y plataformas verificadas; evidencia de clon limpio, actualización y restauración del conjunto final. No exigir Simulator contra la decisión vigente.
- Video final con cobertura y segmentos verificables, presentación, registro de participación, incidencias consolidadas y reflexiones aportadas por sus autores; enlaces reales solo cuando existan. El video del parcial no acredita la entrega final.
- Trazabilidad del requisito «ubiquitous», con aclaración/decisión respaldada o pendiente explícito; ninguna plataforma ni dispensa inferida.
- Veredicto global con pendientes obligatorios enumerados. La entrega no está completa si faltan funciones o pruebas requeridas, aunque los documentos estén terminados.
- Alcance de rastreo documentado y demostrado: WSS real, mapa con procedencia/actualización, simulador y resultados físicos separados por teléfono; GPS externo solo si se encargó esa extensión. No atribuir evidencia a equipo no probado.

Señales de etapa incompleta: PDF con cifras antiguas, manuales que no permiten instalar, enlaces rotos, instalables ausentes, secretos en el paquete o reporte que afirma aprobación clínica/alta disponibilidad no demostradas.

## Qué hacer cuando la comprobación encuentre pendientes

Lleva el informe al chat donde implementaste la etapa y usa este encargo:

```text
Corrige los pendientes de la auditoría que adjunto para esta etapa. Lee el prompt original, las reglas comunes y PROJECT_STATUS.md.
Atiende primero fallos de seguridad, integridad y funcionamiento. No rebajes requisitos, elimines pruebas ni cambies el resultado esperado para obtener aprobación.
Implementa las correcciones, ejecuta las pruebas pertinentes y actualiza evidencias, documentación y PROJECT_STATUS.md.
Identifica qué puntos se cerraron y cuáles siguen pendientes por una dependencia concreta. No declares la etapa completa sin evidencia.
```

Acompaña ese encargo con el informe real de comprobación. Después vuelve a usar el prompt de comprobación de la etapa. Mantén abierta cualquier dependencia que no se haya resuelto; avanzar a trabajo independiente no la convierte en terminada.

## 09 Rastreo GPS y WebSockets como complemento transversal

Requisito completo: [Complemento 09 de rastreo GPS y mapa de Nuevo León](09_rastreo_gps_websockets.md).

Si empiezas desde cero, no necesitas ejecutar este encargo aparte: el 01 y las etapas siguientes ya exigen este complemento. Úsalo como encargo específico si ya tienes componentes implementados sin rastreo o necesitas retomar esta funcionalidad. El número 09 no cambia las dependencias ni permite cerrar la entrega 08 antes de completar las integraciones de rastreo exigibles.

### Prompt inicial

```text
Lee y aplica stuff/prompts/entrega-final/09_rastreo_gps_websockets.md junto con AGENTS.md, PROJECT_STATUS.md y stuff/prompts/entrega-final/00_contexto_y_reglas.md.
Revisa qué partes del rastreo ya existen e implementa las brechas sobre los componentes actuales, sin duplicar servicios, datos, contratos ni reglas.
Completa receptor/adaptador GPS móvil, simulador, WSS seguro, mensajes JSON para Android y XML/XSD para escritorio, mapa actual de Nuevo León, permisos, persistencia y recuperación.
Integra lo correspondiente a cada etapa implementada y registra las dependencias de clientes aún no construidos para completarlas cuando existan, antes de cerrar 07 y 08.
Prueba el recorrido completo disponible y actualiza evidencia, documentación y PROJECT_STATUS.md. No declares probado el GPS físico mientras no esté disponible.
```

### Prompt de comprobación

```text
Audita TRACK-01 a TRACK-10 de stuff/prompts/entrega-final/09_rastreo_gps_websockets.md.
Aplica el Protocolo de comprobación de stuff/prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md. Revisa, no implementes correcciones.
Comprueba ingreso/asignación del GPS simulado, persistencia, WSS real, mensajes JSON/XML, mapa actual de Nuevo León, privacidad por traslado, reconexión/cursor y datos antiguos.
Contrasta la implementación con las etapas 01 a 08 afectadas; no apruebes integraciones de clientes inexistentes ni cuentes polling como WebSockets.
Entrega matriz por TRACK, evidencia aplicable al código actual, brechas y acciones de cierre. Distingue software probado con simulador de resultados nativos y físicos por plataforma; GPS externo opcional.
Termina con el veredicto definido en el protocolo y señala qué bloquea el cierre de 07 y 08.
```

### Qué debes obtener de la comprobación

- Matriz TRACK-01 a TRACK-10 con propietario, componente, prueba y resultado, conservando las dependencias de las etapas consumidoras.
- Recorrido comprobado desde simulador/adaptador a ingreso, validación, persistencia y distribución WSS real; sin duplicar la autoridad de Transporte.
- Mapas interactivos actuales de Nuevo León en los clientes implementados, con formatos JSON/XML correctos y misma identidad de evento/traslado.
- Pruebas de autorización continua, revocación, señal perdida, dato antiguo, reconexión y recuperación desde cursor.
- Separación clara entre integraciones de software aprobadas, resultados físicos por teléfono y pendientes reales; prueba de GPS externo solo si se incorpora esa extensión.

Señales de complemento incompleto: mapa estático, marcador animado sin backend, polling como único transporte, mensajes JSON en escritorio, suscripciones ajenas o simulador presentado como GPS físico probado.

## Alcance móvil actualizado — 6 de noviembre de 2026

Las etapas 01/02 tienen implementación previa: no reejecutarlas por ampliar móvil. Kotlin Multiplatform/Compose Multiplatform, JSON y ambos destinos siguen vigentes. Para la continuación autorizada del 11/11/2026, los pendientes de 01–04 se resuelven mediante CONT-01…CONT-10 en 05–07 y se consolidan en 08. La ruta iOS vigente es Xcode e iPhone físico autorizado, sin descargar runtime Simulator; APK ni compilación arm64 acreditan ejecución iOS. En 07 verifica los flujos y captura/publicación GPS WSS desde ambos sistemas con evidencia aplicable. La fuente principal es el teléfono; GPS externo es opcional. Mantén separadas aceptación del portal, simulación, ejecución nativa y prueba física.
