# Completar el portal web empresarial de Red House

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Implementa en `apps/web/` las funciones finales con Flask, Jinja2, HTML5, CSS3, JavaScript y Highcharts. Conserva el diseño y las mejoras actuales salvo un cambio necesario y justificado.

Integra los contratos/modelos de los prompts 01 y 02. Si falta una operación necesaria, complétala en su propietario con sus pruebas; no la simules en JavaScript ni conectes formularios directamente a tablas ajenas. Mantén backend modular autónomo y modo HTTP explícito compatibles.

## Acceso y experiencia común

- Sitio público con propósito, instituciones/campañas publicables, orientación general revisable y acceso al portal, sin inventar requisitos médicos.
- Login, MFA para perfiles que lo requieran, renovación, cierre de sesión y recuperación de contraseña completa con envío, token de un uso y confirmación. La ayuda de acceso existente no sustituye este flujo.
- Menú y panel por perfil, usuario/institución/ámbito visibles, bandeja de avisos, tareas y estados pendientes. Sin acceso clínico por el solo hecho de ser administrador o coordinador.
- Búsqueda, filtros combinables, orden, paginación y URLs compartibles dentro del ámbito autorizado. Contadores y exportaciones deben usar los mismos filtros.
- Formularios con ayuda de formato/límites, errores seguros por campo, resumen accesible, valores conservados, foco y confirmación contextual de acciones críticas. Preserva CSRF, versiones e idempotencia y la salida de formularios ya acordada sin restaurar avisos nativos innecesarios.
- Fechas en zona del usuario con almacenamiento UTC, formatos numéricos coherentes y campos desconocidos visibles como pendientes.
- Estados vacíos, carga, conflicto, operación pendiente, sesión vencida, falta de permisos y dependencia caída con acción de recuperación comprensible. No mostrar éxito antes de la confirmación requerida.

## Funciones por perfil

| Perfil | Operaciones exigidas |
| --- | --- |
| Donante | Registro preliminar y edición permitida, consentimiento y versiones, consulta propia de evaluación autorizada, campañas, agenda por sede/hora, reserva/reprogramación/cancelación, recordatorios e historial propio. |
| Operador de banco | Donaciones, procesamiento/fraccionamiento, identificación y etiquetas, muestras/resultados dentro de su competencia, inventario y ubicaciones, cuarentena, condiciones térmicas, preparación/recepción, incidencias y trazabilidad. No dictamen ni liberación médica por ese rol. |
| Médico autorizado | Receptores, solicitudes, prioridad documentada, evaluación y fuentes, resultados ABO/HLA, completitud, exclusiones, dictamen, liberación y reserva según permisos, reautenticación y documentación de uso/destino final. |
| Coordinador regional | Disponibilidad agregada, solicitudes operativas autorizadas, comparación logística, propuestas revisables, rutas, programación/asignación de traslados, alertas, cobertura, tiempos y seguimiento regional. |
| Transportista | Solo órdenes asignadas, datos logísticos mínimos, preparación que le corresponda, recolección/tránsito/entrega, ubicación autorizada, incidencias, evidencias e historia de su tarea. |
| Administrador | Instituciones/sedes/capacidades, usuarios, perfiles y permisos autorizados, catálogos, políticas/configuración, dispositivos y seguridad. Cambios auditados y sin autoasignación de facultades clínicas. |
| Auditor | Investigación y exportación minimizada, accesos sensibles, decisiones/versiones, secuencia por recurso y hallazgos con atención/verificación separadas. Conserva inmutabilidad y ámbitos vigentes. |

Si el laboratorio requiere facultades específicas, modela permisos explícitos y una matriz revisable; no conviertas al operador general en médico. No concedas acceso a toda la región para facilitar una pantalla.

## Pantallas y procesos completos

1. **Donación y procesamiento:** expediente, consentimiento, evaluación humana, campaña/cita, colecta/bolsa, muestra, procesamiento y componentes derivados. Mostrar linaje e impedimentos para incorporar una donación no procesada.
2. **Laboratorio y compatibilidad:** listas de muestras y resultados, captura/revisión/corrección con historia, documentos privados y estado de completitud. Vista separada de preselección, evaluación y dictamen; HLA faltante nunca se convierte en aprobación.
3. **Inventario y conservación:** unidad, código, institución, ubicación, producto/órgano, grupo, fechas, estado, condiciones y movimientos. Tableros de cuarentena, próximos a vencer, vencidos y excursiones térmicas, con revisión documentada.
4. **Solicitudes y asignaciones:** alta/revisión, candidatos explicados, fuentes/versiones, ranking operativo, propuesta de cobertura, revisión humana, reserva y recuperación. Mostrar conflictos y versiones obsoletas sin sobrescribir cambios ajenos.
5. **Transporte y custodia:** ruta/origen/destino, asignación, secuencia y responsables, mapa con procedencia y antigüedad de ubicación, incidentes, evidencia, recolección, entrega y aceptación. No confundir ubicación pasada con posición actual.
6. **Uso o destino final:** registrar recepción, verificaciones y posterior uso, devolución, descarte u otro cierre autorizado. Distinguir cierre del suministro de documentación de transfusión o trasplante. Mostrar pendientes de trazabilidad y relaciones con donación/resultados.
7. **Documentos:** preparar, cargar, analizar, verificar, versionar, consultar y descargar archivos según estado y permisos. Mostrar análisis pendiente/rechazado y conservación/bloqueos; no permitir descarga de archivos en cuarentena.
8. **Agenda y campañas:** calendario/lista por sede/hora/cupo, ocupación y asistencia, cambios y recordatorios. Garantizar una sola confirmación cuando dos usuarios compiten por el último cupo.
9. **Auditoría y hallazgos:** conservar filtros, historial y exportación completa autorizada ya implementados; integrar operaciones nuevas y comprobación de vínculos. Sin edición o borrado de historia.
10. **Configuración y salud:** políticas versionadas, parámetros operativos, instituciones y capacidades; monitoreo por rol, dependencia, worker, versión, latencia y error seguro. Una configuración técnica no equivale a autorización normativa.

## Seguimiento en vivo sobre Nuevo León

Implementa la [especificación de rastreo GPS por WebSockets](09_rastreo_gps_websockets.md). Incorpora mapa interactivo actual de Nuevo León con zoom/detalle local y cobertura estatal, marcadores autorizados de origen/destino, ubicación del transportista y trayecto recibido por **WSS** sin recargar la pantalla. Muestra fuente, hora, antigüedad, precisión disponible y estados en vivo/sin señal/retrasado/desconectado/simulado, con recuperación de instantánea/cursor al reconectar. El mapa es para coordinación y perfiles autorizados; no para donantes ni usuarios ajenos al traslado.

Comprueba que una caída del socket o de cartografía mantiene el último dato claramente identificado y no derriba el negocio web autónomo. No conviertas polling o una animación local en prueba de WebSockets. La validación inicial utiliza el simulador a través del backend real y deja pendiente el GPS físico; conserva atribución y fecha/procedencia de cartografía según el proveedor.

## Paneles y reportes

Implementa Highcharts alimentado con datos persistidos y agregados por el servidor: inventario por institución/componente, solicitudes/tiempos, caducidad y desperdicio, flujo de donaciones, traslados, condiciones térmicas, cobertura y calidad de datos. Define periodo, zona horaria, denominadores y actualización.

Ofrece tablas equivalentes accesibles y explica el significado de cada indicador. No muestres porcentajes sin población definida ni series sintéticas como resultados reales. Las proyecciones del prompt 02 se distinguen de observaciones históricas.

Genera PDF, CSV y XLSX con filtros, alcance y fecha; procesa exportaciones grandes como trabajos si corresponde. Reautoriza creación y descarga, minimiza datos y protege CSV/XLSX contra fórmulas inyectadas. Los formatos regulatorios deben identificar versión y estado de revisión, sin prometer certificación.

## Calidad y aceptación

Prueba en navegador real todos los perfiles y al menos anchos de móvil, tableta y escritorio. Verifica teclado, foco, etiquetas, contraste, tablas, diálogos, mensajes y gráficas con datos del servidor. No incorpores detalles de persistencia, hashes o versiones en pantallas operativas salvo cuando ayuden a resolver una decisión/conflicto; auditoría y diagnóstico conservan los detalles autorizados.

Demuestra el flujo sanguíneo hasta uso/destino, coordinación de órgano con referencias oficiales y donación con agenda/procesamiento. Comprueba CSRF, acceso horizontal por URL y exportación, doble envío, pérdida de respuesta, expiración de sesión, documento sin analizar y fallos de almacenamiento.

Ejecuta los flujos de negocio del portal con todas las API detenidas en un entorno de prueba, manteniendo sus dependencias necesarias; una página pública accesible no satisface autonomía. Prueba también el modo HTTP, conservando semántica y sin fallback automático tras una escritura.

Entrega pruebas/capturas reales, guía por perfil, mapa de pantallas a permisos/endpoints y evidencias de persistencia. Actualiza documentación, trazabilidad y `PROJECT_STATUS.md`. No reemplaces la aplicación web con una SPA ni construyas un escritorio embebiendo estas mismas páginas.
