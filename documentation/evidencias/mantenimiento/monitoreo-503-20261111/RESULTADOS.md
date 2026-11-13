# Diagnóstico del error 503 de monitoreo — 11/11/2026

Solicitud: revisar el error «Los almacenes de monitoreo no están disponibles» mostrado al auditor en GCP. Diagnóstico de lectura; sin cambios de código, configuración desplegada, índices o datos de negocio.

## Evidencia

- Doce rutas públicas `/services/<servicio>/health/ready`: HTTP 200, dependencias aplicables disponibles. Treinta contenedores activos y healthy.
- Login HTTPS como auditor1: 302; panel, notificaciones, auditoría, documentos y reportes: HTTP 200. `/monitoreo`: HTTP 503, reproducido con referencia `b24748f5-a876-4d03-b340-d20652418e89`. Logout: 302.
- Portal configurado como `monolith`: utiliza su backend modular propio. La salud del microservicio independiente no ejecuta la consulta completa de esta pantalla.
- Registro del portal: `database_unavailable service=monitoreo type=QueryCanceled sqlstate=57014`.
- Consulta real `SELECT DISTINCT ON (service) * FROM checks ORDER BY service,created_at DESC,id`: cancelada por statement_timeout de 5000 ms; medición de 5,172 s. Una ejecución anterior terminó al borde del límite, en 5,005 s de tiempo total medido. El plan estimó 786.081 filas, lectura secuencial paralela y ordenamiento de `red_house.service_health_check`. Es una estimación del plan, no un conteo exacto.
- Existen índices físicos por `(service, checked_at DESC)`; el plan observado realiza un ordenamiento que incluye `check_id`.
- Consulta de totales de 24 horas: 0,306 s, doce grupos.
- MongoDB permite lectura simple; la agregación alternativa usada por `documentary_status` provoca `NetworkTimeout`, medido en 3,008 s. El adaptador limita cada socket a 1500 ms; la medición completa puede incluir reintentos del controlador. La inspección inicial de listIndexes fue rechazada por privilegios; eso no prueba falta de permiso para leer. Se comprobó posteriormente find y la agregación real.

## Causa y acción pendiente

El estado de salud acredita conexión básica, pero la consulta histórica del panel excede su límite. La recuperación documental también agota su tiempo y la aplicación devuelve `monitor_storage_unavailable` (503). No acredita una caída general ni denegación general de acceso a los microservicios.

Pendiente: optimizar la selección de la última muestra por servicio y comprobar índices/plan con el volumen real; optimizar la agregación documental. Después, repetir aceptación HTTPS del panel y recuperación. No aumentar límites o borrar historial como sustituto de ese trabajo. No se aplicó una corrección en este diagnóstico.

Archivos: [comprobación HTTPS](comprobacion-https.json) y [mediciones de consultas](consultas.txt). Las sesiones creadas para el diagnóstico se cerraron. Clave SSH temporal retirada de OS Login y archivos locales eliminados; claves anteriores conservadas.
