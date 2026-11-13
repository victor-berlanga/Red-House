# Prompts para completar la entrega final de Red House

Estos prompts encargan la implementación completa de la plataforma final por componentes. Ejecutarlos significa desarrollar, integrar, probar y documentar cada incremento; no solamente redactar propuestas. Esta carpeta contiene instrucciones de trabajo, no acredita que las funcionalidades futuras ya existan.

## Estado de ejecución y alcance actualizado

Actualización del **11/11/2026**: 01 y 02 tienen implementación y evidencia previa que se conserva; sus verificaciones integrales pendientes siguen identificadas. 03 obtuvo aceptación local para continuar y conserva parciales transferidos a 06; 04 está en cierre con verificaciones técnicas y externas pendientes. La publicación web y la compilación móvil no acreditan aceptación integral. Comprueba siempre el estado más reciente en `PROJECT_STATUS.md`.

Los archivos 00–04 se conservan. La [continuidad obligatoria de 01–04](07_integracion_pruebas_y_rendimiento.md#continuidad-obligatoria-de-las-etapas-01-a-04) encarga sus correcciones posteriores mediante CONT-01…CONT-10: 05 desarrolla escritorio y resuelve sus dependencias, 06 completa controles/infraestructura compartidos, 07 corrige clientes y verifica integración, y 08 consolida evidencia y entregables. Ese bloque actualiza criterios antiguos incompatibles con decisiones posteriores sin eliminar requisitos ni reconstruir lo ya probado. Al ejecutar se mantiene un registro único en `documentation/entrega-final/continuidad/Matriz.md`; trasladar un pendiente no lo convierte en aprobado.

El complemento 09 conserva lo construido y amplía la integración móvil pendiente. Los nombres históricos de archivos se conservan para no romper enlaces; `04_aplicacion_android.md` exige Android e iOS. Android se acepta en emulador, sin teléfono; iOS se comprueba en iPhone físico autorizado, sin descargar runtime Simulator. Separa compilación, firma, instalación y ejecución.

La fuente principal prevista de ubicación es la aplicación móvil; GPS externo queda como extensión opcional. Distingue datos de emulador de medición física. No uses una simulación para acreditar uso del iPhone.

Las decisiones vigentes adicionales están en [reglas comunes](00_contexto_y_reglas.md): almacenamiento privado del servidor como modo operativo y GCS opcional con verificación académica independiente; sin modo offline universal; push FCM/APNs externo pendiente, con bandeja/adaptadores verificables; feed de campañas/citas para donante, mapa protagonista para transportista y revisión visual de pantallas/recorridos renderizados. Video, exposición, aclaración de «ubiquitous», reflexión y entrega individual son acciones humanas.

## Uso y orden de ejecución

Abre una conversación en la raíz de Red House y solicita ejecutar el archivo correspondiente. Cada prompt exige leer primero [las reglas comunes](00_contexto_y_reglas.md), conservando las decisiones y los datos existentes. No hace falta pegar todos los prompts en una sola conversación.

La [guía de ejecución y comprobación](GUIA_EJECUCION_Y_COMPROBACION.md) reúne, para cada etapa, un prompt inicial listo para copiar, otro de auditoría y los resultados que debes exigir antes de avanzar. Incluye veredictos, tratamiento de dependencias y un encargo para corregir pendientes.

En 05 y en las correcciones de presentación de 07 son obligatorias las [instrucciones de diseño](../instrucciones_diseno_ui_ux.md) y la [corrección de calidad visual](../corregir_calidad_visual_web_movil.md), adaptadas a cada plataforma. Su lectura no ordena repetir cambios ya implementados. La aceptación comprende tareas de todos los roles y familias de pantalla, además de evidencia técnica.

Lee también el [complemento 09 de rastreo GPS por WebSockets y mapa de Nuevo León](09_rastreo_gps_websockets.md) **desde el prompt 01**. Es obligatorio para las etapas correspondientes: define software funcional con simulador, integración móvil Android/iOS y extensión opcional de GPS externo, canal WSS, mensajes JSON/XML, privacidad, mapa actual y pruebas. El número identifica el archivo, no su ejecución después del 08; los prompts ya lo incorporan para evitar trabajo duplicado. La guía incluye un encargo específico para añadirlo si ya avanzaste sin ese requisito.

| Orden | Prompt | Resultado exigido |
| --- | --- | --- |
| 1 | [Backend y microservicios](01_backend_y_microservicios.md) | Cubrir las 24 responsabilidades de la retroalimentación mediante servicios y módulos justificados, datos reales y contratos JSON/XML |
| 2 | [Reglas clínicas y algoritmos](02_reglas_clinicas_y_algoritmos.md) | Registro HLA, evaluaciones explicables, control humano, logística, balanceo, caducidad e inconsistencias |
| 3 | [Portal web](03_portal_web.md) | Operación empresarial completa y autónoma, formularios, paneles, archivos y reportes |
| 4 | [Móvil Android/iOS](04_aplicacion_android.md) | Kotlin Multiplatform/Compose, JSON, cinco roles, QR/cámara/GPS, bandeja interna; Android emulador e iPhone físico |
| 5 | [Escritorio](05_aplicacion_escritorio.md) | Consola PySide6 con Python, XML/XSD, trabajo institucional, impresión y exportaciones |
| 6 | [Seguridad e infraestructura](06_seguridad_infraestructura_y_continuidad.md) | Endurecimiento, archivos analizados, GCP, continuidad, respaldos, recuperación y CI |
| 7 | [Integración y pruebas](07_integracion_pruebas_y_rendimiento.md) | Corregir/verificar CONT-01…CONT-10 heredados; tres procesos completos, coherencia entre clientes, fallos, seguridad, Locust y usabilidad |
| 8 | [Documentación y entrega](08_documentacion_y_entrega.md) | Informe, manuales, modelos, cumplimiento, instalables, video final, incidencias y reflexiones individuales auténticas |
| 09 transversal desde 01 | [Rastreo GPS y WebSockets](09_rastreo_gps_websockets.md) | Requisito incorporado durante las etapas: GPS móvil/simulador y extensión externa opcional, WSS y mapas actuales de Nuevo León; no se pospone al final |

El orden es por dependencias. Las pruebas y la documentación de cada componente se realizan durante su desarrollo. Los pasos 7 y 8 consolidan y verifican resultados; no aplazan la calidad hasta el final. Dentro del paso 1, implementa primero modelos y contratos necesarios para el paso 2. Dentro de los pasos 3 a 5, completa las extensiones de API que el cliente necesite antes de conectar sus pantallas. El paso 6 verifica también los controles construidos desde el paso 1.

## Decisiones confirmadas

- Móvil: **iOS y Android**, con Kotlin Multiplatform y Compose Multiplatform en el encargo actualizado del 6 de noviembre de 2026; sustituye el alcance Android anterior.
- Aceptación iOS: iPhone físico autorizado; no descargar Simulator mientras siga vigente esa decisión. Una compilación arm64 no sustituye los recorridos físicos.
- Escritorio: **PySide6 con Python**, confirmado por el usuario el 26 de octubre de 2026.
- PostgreSQL: conservar la base compartida `red_house`, permisos por propietario y datos existentes.
- Web: conservar Flask/Jinja2 y backend modular autónomo. Android e iOS consumen JSON; escritorio consume XML validado mediante XSD.
- El profesor recomendó una **arquitectura objetivo de 24 microservicios**. Deben cubrirse y mapearse sus 24 responsabilidades desde los once servicios actuales. No es obligatorio crear exactamente 24 microservicios independientes: toda agrupación o separación debe justificarse y evitar duplicar funciones, reglas o propietarios. La matriz conserva los 24 elementos del catálogo y distingue servicios independientes, módulos y réplicas.
- Ningún resultado automático autoriza elegibilidad, transfusión, liberación o asignación de órganos.

## Cobertura de la retroalimentación

| Tema solicitado | Responsabilidad principal | Verificación final |
| --- | --- | --- |
| HLA, pruebas, diferencias sangre/órganos y revisión profesional | 01 y 02 | 07 y 08 |
| Explicaciones, versiones, urgencia, tiempo y distancia | 02 | 07 |
| Veinticuatro responsabilidades, contratos y persistencia | 01 | 07 y 08 |
| Android/iOS, tareas por perfil y capacidades del dispositivo | 04 | 07 |
| Escritorio, XML/XSD, inventario, informes e impresión | 05 | 07 |
| Mejoras web, recuperación de contraseña, citas y reportes | 01 y 03 | 07 |
| Cadena de frío, uso o destino final y trazabilidad clínica | 01 y 02; interfaces 03 a 05 | 07 |
| Aislamiento institucional, MFA y documentos privados | 01 y 06; clientes 03 a 05 | 07 |
| Análisis de archivos, retención y almacenamiento caído | 01 y 06 | 07 |
| RTO/RPO, respaldos, dependencias y continuidad | 06 | 07 y 08 |
| GPS móvil, simulador, WebSockets y mapa actual de Nuevo León | 01, 03, 04, 05 y 06; logística 02 | 07 y 08 |
| Demostración integrada y participación real del equipo | 07 y 08 | 08 |

## Instrucción breve para iniciar

Para continuar hacia escritorio: «Ejecuta `stuff/prompts/entrega-final/05_aplicacion_escritorio.md`. Lee sus reglas comunes, las instrucciones de diseño y la continuidad de 01–04 definida en 07. Implementa y verifica lo solicitado, preserva el proyecto existente y registra las dependencias heredadas sin declararlas resueltas. Continúa el trabajo independiente.»

Sustituye el nombre del archivo para cada etapa. Los prompts son encargos futuros: crearlos no autoriza ahora cambios funcionales, despliegues ni operaciones sobre datos.

Para encargar la continuación: «Lee `stuff/prompts/entrega-final/README.md` y ejecuta los prompts 05 a 08 por sus dependencias, incluida la continuidad CONT-01…CONT-10 de las etapas anteriores y el complemento 09. Revisa el estado actual, conserva lo ya verificado y completa las correcciones, implementación, integración, pruebas y documentación. No termines con un plan. Registra por separado los bloqueos externos reales y continúa el trabajo independiente.»
