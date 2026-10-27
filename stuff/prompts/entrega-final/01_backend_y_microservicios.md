# Implementar el backend y los microservicios de la entrega final

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee primero `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Implementa las mejoras y nuevas capacidades del backend con persistencia real y contratos consumibles por web, Android JSON y escritorio XML. No construyas todavía las aplicaciones cliente.

## Diagnóstico y diseño ejecutable

El profesor recomendó una **arquitectura objetivo de 24 microservicios**, con un catálogo que describe las funciones de cada uno. Toma ese catálogo como referencia explícita para evolucionar los once servicios actuales. Para esta entrega se exige cubrir y delimitar sus 24 responsabilidades; no es obligatorio crear exactamente 24 microservicios independientes, procesos o contenedores. La cantidad final debe resultar de límites de negocio justificados y de evitar redundancia, no de completar una cuota.

Revisa servicios, rutas, DTO, XSD, migraciones, permisos, workers y pruebas mediante CodeGraph. Produce una **matriz de correspondencia de los once servicios actuales con las 24 responsabilidades recomendadas**. Conserva una fila por elemento del catálogo BE-01 a BE-24, aunque varios correspondan al mismo propietario final. Indica nombre recomendado, implementación existente, brecha, decisión de conservar/ampliar/agrupar/extraer/crear, propietario final, modalidad de servicio independiente o módulo, tablas/colecciones, contratos, consumidores, justificación y prueba. No reimplementes capacidades existentes como si faltaran.

Justifica qué responsabilidades permanecen agrupadas y cuáles requieren nuevos servicios. Considera cohesión, ciclo de vida, permisos, consistencia, carga y despliegue. No fuerces 24 procesos ni concentres todo en un servicio genérico. Una extracción debe migrar propiedad y referencias sin dejar dos autoridades para la misma operación. Preserva rutas v1 compatibles o implementa transición versionada explícita.

Por ejemplo, comprueba primero Instituciones dentro de Identidad, Citas/campañas dentro de Donantes y la coordinación de Solicitudes/reservas entre Receptores e Inventario. No crees otro CRUD, otra copia del dato ni una segunda regla de reserva únicamente para alcanzar 24 nombres. Si separas una responsabilidad, define qué conserva cada propietario y cómo migran sus consumidores. Si la mantienes agrupada, identifica sus límites, contratos y pruebas de forma verificable; agrupar no permite omitir funciones del catálogo.

## Cobertura funcional obligatoria

| ID | Responsabilidad | Funcionalidad que debes entregar |
| --- | --- | --- |
| BE-01 | Identidad y acceso | Login/logout, renovación rotativa, revocación, gestión institucional de usuarios/roles/permisos, registro/revocación de dispositivos, MFA para perfiles críticos y comprobante de reautenticación ligado a operación y recurso. Recuperación de contraseña con token de un uso, expiración, límites, respuesta que no enumere cuentas y revocación de sesiones según política documentada. |
| BE-02 | Instituciones | Hospitales, bancos y centros; sedes, responsables, contactos, horarios, capacidades, servicios y documentos de licencia/acreditación con emisor y vigencia. Registrar un documento no certifica autorización sanitaria. |
| BE-03 | Donantes | Registro preliminar, identidad mínima, vínculo con cuenta, antecedentes autorizados, consentimiento versionado con fecha/referencia/retiro, evaluaciones humanas y seguimiento. Conservar baja e historial existentes. |
| BE-04 | Receptores | Expediente mínimo institucional, necesidades sanguíneas o de órgano separadas, referencias autorizadas, prioridad clínica capturada por personal competente, estados y cambios históricos. |
| BE-05 | Inventario | Unidades y componentes, código único/QR, procedencia, ubicación, institución actual, disponibilidad, vencimiento capturado, cuarentena, liberación humana, movimientos, reserva y control de concurrencia. |
| BE-06 | Compatibilidad | Instantáneas ABO/Rh, resultados y HLA vinculados, completitud según perfil versionado, exclusiones, procedencia, límites, revisión humana e invalidación ante cambios de datos; detalle en prompt 02. |
| BE-07 | Priorización y geografía | Alternativas logísticas con fuente/fecha, distancia y tiempo estimado, factores/explicación, versiones y propuestas; diferenciar logística de asignación oficial. Conservar Hopcroft–Karp; ampliaciones en prompt 02. |
| BE-08 | Transporte | Orden, reserva asociada, ruta, responsables y asignación; preparación, recolección, tránsito, entrega y recepción; GPS limitado a la tarea, incidentes, evidencias y recuperación tras respuesta perdida. |
| BE-09 | Custodia | Identificadores escaneados, entrega entre responsables, secuencia, tiempo de captura/recepción, sellos y constancia de aceptación. Firma o confirmación electrónica autenticada con alcance documentado; no atribuirle certificación legal inexistente. |
| BE-10 | Alertas | Eventos clínico-operativos e infraestructura, severidad, destinatarios, deduplicación, reconocimiento, escalamiento configurable, recordatorios y cierre; bandeja interna más adaptadores email y push con registro de entrega/reintentos. |
| BE-11 | Auditoría | Accesos y cambios, decisiones y reglas, exportaciones, acciones rechazadas, correlación entre servicios, historia inmutable y hallazgos existentes; consulta y exportación restringidas/minimizadas. |
| BE-12 | Monitoreo | Salud de procesos, dependencias, workers/colas, versión, última comprobación, promedio y percentiles cuando existan muestras, errores, historial y avisos de caída/recuperación. No hacer obligatorio Monitoreo para operar negocio. |
| BE-13 | Donación y procesamiento | Colecta, bolsa, muestra, procesamiento, fraccionamiento y componentes derivados; relación padre/hijo, pérdidas/destino y responsables. El linaje debe reconstruirse desde una unidad a la donación y a sus derivados. |
| BE-14 | Laboratorio | Solicitud y recepción de muestras, identificadores, resultados estructurados, método, laboratorio, fechas, unidades, referencia documental, revisión/corrección versionada y autorización. ABO/Rh, pruebas inmunohematológicas, HLA y datos inmunológicos pertinentes mediante perfiles aprobados. |
| BE-15 | Cadena de frío | Equipos/contenedores y ubicación, perfiles por producto/órgano, lectura manual o sensor, unidad, fecha, procedencia/calibración disponible, excursiones y brechas de lectura. Bloqueo/cuarentena y revisión humana; umbrales clínicos solo con fuente/aprobación. |
| BE-16 | Solicitudes y asignaciones | Creación, revisión, aprobación/rechazo, propuestas, reserva, retención, vencimiento y cancelación; consistencia con cobertura y traslado. Registrar autorización externa/oficial de órganos cuando corresponda, sin asignación automática. |
| BE-17 | Caducidades | Detección periódica, vistas próximas/vencidas, bloqueo de uso no permitido, rotación operativa, alertas y registro de descarte/devolución/destino con motivo y revisión. No borrar el recurso vencido. |
| BE-18 | Trazabilidad clínica | Historia de donación, procesamiento, pruebas, liberación, almacenamiento, suministro, transporte, recepción y uso o destino final. Registrar eventos transfusionales y referencias autorizadas o cierre del órgano según protocolo, sin emitir órdenes clínicas. |
| BE-19 | Documentos | Consentimientos, resultados, acreditaciones, autorizaciones y evidencias; categoría, propietario, versión, hash, generación, privacidad, estado de análisis, retención/bloqueo y descarga privada. Generalizar el flujo GCS existente sin duplicar objetos ni autoridades. |
| BE-20 | Reportes | Inventario, solicitudes, caducidad, tiempos, custodia, actividad y trazabilidad; filtros, orden, paginación y trabajos exportables PDF/CSV/XLSX según permisos. Reportes regulatorios como formato identificado y sujeto a revisión, sin afirmar certificación. |
| BE-21 | Analítica | Demanda/consumo, desperdicio, escasez, tiempos y tendencias agregadas; pronóstico de riesgo de caducidad y propuestas de abastecimiento sin ejecución clínica. Calidad, ventana temporal y limitaciones visibles. |
| BE-22 | Citas y campañas | Campañas por sede, agenda por fecha/hora, cupos, reserva concurrente, confirmación/cancelación, reprogramación, recordatorios y asistencia. Una cita no equivale a elegibilidad aprobada. |
| BE-23 | Sincronización | Comandos permitidos, identificador persistente, idempotencia, versiones, resultado consultable, conflictos, cursor de cambios autorizado y bajas lógicas. Aplicar autorización actual al enviar y al recuperar resultados. |
| BE-24 | Interoperabilidad | JSON/XML de todas las operaciones de clientes, XSD verificables, ejemplos/error, mapeo de identificadores y adaptador de importación/exportación con validación y conciliación. No afirmar integración hospitalaria real sin contraparte; HL7/FHIR solo con necesidad definida. |

## Rastreo GPS por WebSockets

Implementa la [especificación de rastreo GPS y mapa de Nuevo León](09_rastreo_gps_websockets.md), TRACK-01 a TRACK-10, dentro de Transporte y sus dependencias justificadas BE-08/BE-12/BE-23. Entrega recepción normalizada de GPS/puente futuro, asignaciones y credenciales de dispositivo, persistencia, canal WSS, contratos JSON y XML/XSD, autorización por traslado, cursores, reconexión y simulador ejecutable. No es suficiente describir una API futura ni enviar puntos directamente del simulador a una pantalla. Prueba ingreso/persistencia/distribución con WebSockets reales y separa la aceptación pendiente del hardware de las pruebas del software.

## Modelos y estados

Implementa migraciones aditivas y catálogos versionados. Conserva UUID, relaciones e historiales. Para resultados, autorizaciones, consentimientos y políticas registra autor, institución, fecha efectiva, versión, fuente y sustitución/corrección. Separa estado operativo, resultado clínico registrado y autorización profesional.

Define diagramas de estados para donante, muestra, resultado, donación, componente, solicitud, retención/reserva, traslado, recepción, uso/destino, documento y alerta. Cada transición declara actor, datos obligatorios, versión, condición, evento y compensación. No habilites rutas alternativas que eviten cuarentena o dictamen.

Una recepción confirma un hecho logístico. El cierre de suministro no demuestra transfusión ni trasplante: registra por separado el uso/destino final y los pendientes de cierre. Conserva evidencia de incidentes y correcciones sin reescribir eventos.

## Contratos y operaciones

Reutiliza contratos v1 actuales y extiéndelos de forma compatible. Para cada recurso nuevo define operaciones de lista/detalle/alta y comandos de transición necesarios; no ofrezcas DELETE o PATCH genérico sobre registros inmutables. Incluye filtros, búsqueda, paginación, orden permitido, tipos, fechas UTC con zona, enumeraciones, campos opcionales, límites y errores.

Publica OpenAPI, ejemplos JSON/XML y XSD de entrada/salida por operación, incluida la validación de DTO que exige el formato XML actual. Tanto login, refresh y MFA como negocio, sincronización y errores deben admitir el formato de cada cliente. Negocia `Accept` y `Content-Type` de forma explícita.

Define semántica de 201/202 y estados pendientes, cabeceras de correlación/idempotencia y conflictos 409/412 según contrato. No cambies códigos actuales sin compatibilidad documentada. Las operaciones recuperables deben ofrecer consulta por ID/clave y no devolver éxito definitivo antes del compromiso correspondiente.

Para exportaciones asíncronas, preparación de documentos y sincronización usa cuerpos JSON/XML para control y autorización; entrega binarios por mecanismo privado documentado. Evita base64 de archivos grandes dentro del contrato. Garantiza que obtener una URL o un job de otra institución también exige autorización.

## Requisitos de implementación

- Responsabilidades comunes, JWT/Redis, permisos, XML seguro, eventos, idempotencia y privacidad según las reglas comunes.
- Cada servicio nuevo: paquete propio, configuración documentada, Dockerfile, worker cuando haga falta, pruebas, salud y despliegue individual; intégralo con gateway, web modular y Monitoreo.
- Mantén una versión autoritativa de reglas por dominio. Los clientes solo validan formato y muestran resultados.
- Entrega real de email/push mediante adaptadores configurables, con pruebas de integración autorizadas o receptor de pruebas. No presentes una fila de outbox como correo recibido.
- Sincronización multiusuario: rechaza comandos de otra identidad, datos fuera del ámbito, versiones obsoletas y claves repetidas con distinto cuerpo. No resuelvas conflictos críticos con último escritor.
- Nuevas funciones que requieran aprobación clínica deben poder probarse con perfiles sintéticos sin activar operación clínica real.

## Pruebas y aceptación

Demuestra al menos: contrato JSON/XML de cada operación nueva; migración desde copia de la versión actual y nueva instalación; permisos institucionales; rechazo de actor no autorizado para dictamen/liberación/reserva; solicitud incompleta bloqueada; donante sin evaluación impedido de avanzar; muestras/resultados faltantes que impiden aprobación; doble reserva con un solo resultado válido; vencimiento de retención sin pérdida de trazabilidad; unidad derivada ligada a su origen; excursión térmica y cuarentena; uso/destino final registrado; documento no analizado inaccesible; recordatorio y escalamiento deduplicados; comando repetido sin doble escritura y conflicto de versiones.

Comprueba que la web modular conserva operaciones al detener las API de negocio en entorno aislado. Verifica una API con una réplica caída y con todas sus réplicas caídas, sin confundir ambos resultados.

Entrega catálogo final de propietarios y puertos, modelos y estados, migraciones, contratos JSON/XML/XSD, matriz BE-01 a BE-24, evidencias y guía de reproducción. La aceptación debe comprobar cobertura de las 24 responsabilidades, justificación de cada agrupación o separación y ausencia de reglas/autoridades duplicadas. Informa por separado los 24 elementos recomendados, la cantidad real de microservicios independientes, los módulos agrupados y las réplicas desplegadas; no cuentes réplicas como servicios nuevos. Actualiza `PROJECT_STATUS.md`. No cierres BE-06 como motor HLA clínico si solo existe captura o preselección; distingue su integración posterior con el prompt 02.
