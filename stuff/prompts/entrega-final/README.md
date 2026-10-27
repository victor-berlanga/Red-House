# Prompts para completar la entrega final de Red House

Estos prompts encargan la implementación completa de la plataforma final por componentes. Ejecutarlos significa desarrollar, integrar, probar y documentar cada incremento; no solamente redactar propuestas. Esta carpeta contiene instrucciones de trabajo, no acredita que las funcionalidades futuras ya existan.

## Uso y orden de ejecución

Abre una conversación en la raíz de Red House y solicita ejecutar el archivo correspondiente. Cada prompt exige leer primero [las reglas comunes](00_contexto_y_reglas.md), conservando las decisiones y los datos existentes. No hace falta pegar todos los prompts en una sola conversación.

La [guía de ejecución y comprobación](GUIA_EJECUCION_Y_COMPROBACION.md) reúne, para cada etapa, un prompt inicial listo para copiar, otro de auditoría y los resultados que debes exigir antes de avanzar. Incluye veredictos, tratamiento de dependencias y un encargo para corregir pendientes.

Lee también el [complemento 09 de rastreo GPS por WebSockets y mapa de Nuevo León](09_rastreo_gps_websockets.md) **desde el prompt 01**. Es obligatorio para las etapas correspondientes: define software funcional con simulador, adaptación al GPS físico futuro, canal WSS, mensajes JSON/XML, privacidad, mapa actual y pruebas. El número identifica el archivo, no su ejecución después del 08; los prompts ya lo incorporan para evitar trabajo duplicado. La guía incluye un encargo específico para añadirlo si ya avanzaste sin ese requisito.

| Orden | Prompt | Resultado exigido |
| --- | --- | --- |
| 1 | [Backend y microservicios](01_backend_y_microservicios.md) | Cubrir las 24 responsabilidades de la retroalimentación mediante servicios y módulos justificados, datos reales y contratos JSON/XML |
| 2 | [Reglas clínicas y algoritmos](02_reglas_clinicas_y_algoritmos.md) | Registro HLA, evaluaciones explicables, control humano, logística, balanceo, caducidad e inconsistencias |
| 3 | [Portal web](03_portal_web.md) | Operación empresarial completa y autónoma, formularios, paneles, archivos y reportes |
| 4 | [Android](04_aplicacion_android.md) | Aplicación Kotlin con Jetpack Compose, JSON, perfiles, QR, cámara, GPS, push y sincronización segura |
| 5 | [Escritorio](05_aplicacion_escritorio.md) | Consola PySide6 con Python, XML/XSD, trabajo institucional, impresión y exportaciones |
| 6 | [Seguridad e infraestructura](06_seguridad_infraestructura_y_continuidad.md) | Endurecimiento, archivos analizados, GCP, continuidad, respaldos, recuperación y CI |
| 7 | [Integración y pruebas](07_integracion_pruebas_y_rendimiento.md) | Tres procesos completos, coherencia entre clientes, fallos, seguridad, Locust y usabilidad |
| 8 | [Documentación y entrega](08_documentacion_y_entrega.md) | Informe final, manuales, modelos, matriz de cumplimiento, instalables y demostración reproducible |
| 09 transversal desde 01 | [Rastreo GPS y WebSockets](09_rastreo_gps_websockets.md) | Requisito incorporado durante las etapas: GPS futuro/simulador, WSS y mapas actuales de Nuevo León; no se pospone al final |

El orden es por dependencias. Las pruebas y la documentación de cada componente se realizan durante su desarrollo. Los pasos 7 y 8 consolidan y verifican resultados; no aplazan la calidad hasta el final. Dentro del paso 1, implementa primero modelos y contratos necesarios para el paso 2. Dentro de los pasos 3 a 5, completa las extensiones de API que el cliente necesite antes de conectar sus pantallas. El paso 6 verifica también los controles construidos desde el paso 1.

## Decisiones confirmadas

- Android: **Kotlin con Jetpack Compose**, confirmado por el usuario el 26 de octubre de 2026.
- Escritorio: **PySide6 con Python**, confirmado por el usuario el 26 de octubre de 2026.
- PostgreSQL: conservar la base compartida `red_house`, permisos por propietario y datos existentes.
- Web: conservar Flask/Jinja2 y backend modular autónomo. Android consume JSON; escritorio consume XML validado mediante XSD.
- El profesor recomendó una **arquitectura objetivo de 24 microservicios**. Deben cubrirse y mapearse sus 24 responsabilidades desde los once servicios actuales. No es obligatorio crear exactamente 24 microservicios independientes: toda agrupación o separación debe justificarse y evitar duplicar funciones, reglas o propietarios. La matriz conserva los 24 elementos del catálogo y distingue servicios independientes, módulos y réplicas.
- Ningún resultado automático autoriza elegibilidad, transfusión, liberación o asignación de órganos.

## Cobertura de la retroalimentación

| Tema solicitado | Responsabilidad principal | Verificación final |
| --- | --- | --- |
| HLA, pruebas, diferencias sangre/órganos y revisión profesional | 01 y 02 | 07 y 08 |
| Explicaciones, versiones, urgencia, tiempo y distancia | 02 | 07 |
| Veinticuatro responsabilidades, contratos y persistencia | 01 | 07 y 08 |
| Android, tareas por perfil y capacidades del dispositivo | 04 | 07 |
| Escritorio, XML/XSD, inventario, informes e impresión | 05 | 07 |
| Mejoras web, recuperación de contraseña, citas y reportes | 01 y 03 | 07 |
| Cadena de frío, uso o destino final y trazabilidad clínica | 01 y 02; interfaces 03 a 05 | 07 |
| Aislamiento institucional, MFA y documentos privados | 01 y 06; clientes 03 a 05 | 07 |
| Análisis de archivos, retención y almacenamiento caído | 01 y 06 | 07 |
| RTO/RPO, respaldos, dependencias y continuidad | 06 | 07 y 08 |
| GPS futuro, simulador, WebSockets y mapa actual de Nuevo León | 01, 03, 04, 05 y 06; logística 02 | 07 y 08 |
| Demostración integrada y participación real del equipo | 07 y 08 | 08 |

## Instrucción breve para iniciar

«Ejecuta `stuff/prompts/entrega-final/01_backend_y_microservicios.md`. Lee también sus reglas comunes. Implementa y verifica lo solicitado, preserva el proyecto existente y continúa hasta completar los criterios técnicos o identificar una dependencia externa concreta.»

Sustituye el nombre del archivo para cada etapa. Los prompts son encargos futuros: crearlos no autoriza ahora cambios funcionales, despliegues ni operaciones sobre datos.

Para encargar el conjunto completo: «Lee `stuff/prompts/entrega-final/README.md` y ejecuta los prompts 01 a 08 por sus dependencias. Revisa el estado actual al comenzar cada etapa, conserva lo ya verificado y completa implementación, integración, pruebas y documentación. No termines con un plan. Registra por separado los bloqueos externos reales y continúa el trabajo independiente.»
