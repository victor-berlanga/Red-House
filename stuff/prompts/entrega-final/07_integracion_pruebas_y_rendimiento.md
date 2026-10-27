# Verificar integración seguridad rendimiento y usabilidad de la plataforma final

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Integra y verifica backend, web, Android Kotlin/Compose y escritorio PySide6. Corrige defectos encontrados hasta completar los criterios técnicos; no entregues únicamente un plan de pruebas.

## Preparación y trazabilidad

Construye una matriz que cubra requisitos originales, responsabilidades BE-01 a BE-24, algoritmos ALG-01 a ALG-05, módulos DESK-01 a DESK-14 y funciones móviles/web. Vincula cada criterio con código, contrato, caso, entorno, resultado y evidencia. No cambies la expectativa después de observar un fallo para declararlo aprobado.

Comprueba la correspondencia desde los once servicios iniciales con los 24 microservicios recomendados por el profesor. Debe haber cobertura verificable para cada responsabilidad y justificación de las agrupaciones/separaciones, sin exigir exactamente 24 servicios independientes. Rechaza tanto funciones omitidas por agrupar como reglas o autoridades duplicadas para completar el número. Distingue servicios, módulos y réplicas en el inventario de prueba.

Prepara instituciones/regiones, usuarios de todos los perfiles, donantes/receptores, sangre/componentes y órganos sintéticos, resultados ABO/HLA, políticas de prueba, unidades, rutas, campañas, tareas y documentos en entornos aislados. Usa identidades/IDs persistentes para seguir un caso entre clientes. Las aprobaciones ficticias quedan identificadas como escenarios académicos, nunca como validación clínica real.

Define entornos de prueba, límites de carga, versión de fuentes, dependencias y limpieza exclusiva de datos propios. No reinicialices la instalación habitual ni uses pacientes reales.

## E2E-A Solicitud urgente de sangre hasta uso o destino final

1. Operador registra una unidad con procedencia, componente, grupo, fechas, ubicación y condiciones; laboratorio documenta muestras/resultados pertinentes.
2. Médico autorizado revisa y libera mediante confirmación/reautenticación conforme al perfil sintético.
3. Médico del destino crea receptor y solicitud urgente; el sistema valida información y muestra opciones/exclusiones.
4. Profesional revisa candidatos y registra dictamen. Coordinación consulta factores logísticos; una propuesta no crea reserva automáticamente.
5. Dos usuarios intentan reservar la misma unidad: una sola reserva válida y cobertura correcta; prueba también dos unidades para el último cupo solicitado.
6. Coordinador programa y asigna traslado. Transportista Android verifica QR, recoge, registra GPS/incidencia/evidencia y entrega.
7. Operador del destino recibe desde escritorio XML. Se comprueba secuencia de custodia, condiciones, estados y avisos.
8. Personal autorizado registra uso, devolución, descarte u otro destino permitido. Se distingue recepción de transfusión y se reconstruye la historia hasta el cierre.
9. Auditor consulta todos los hechos, decisiones, fuentes/versiones y responsables autorizados sin poder modificarlos.

Incluye una variante con prueba faltante, una con unidad vencida, una excursión térmica y una entrega tardía. Ninguna produce aprobación clínica automática.

## E2E-B Coordinación de órgano y autorización profesional

1. Institución autorizada registra órgano, procedencia, datos disponibles, tiempos críticos capturados y documentos.
2. Laboratorio registra tipificación HLA y datos/pruebas pertinentes con versiones. Comprueba estados incompleto, pendiente, corregido y revisado.
3. La coincidencia ABO con HLA faltante no se presenta como trasplantabilidad. La completitud no se presenta como dictamen.
4. Registra referencias de autorización y procedimiento oficial aplicable mediante el profesional habilitado; el motor solo apoya coordinación.
5. Prepara reserva/logística según la autorización, traslado Android, custodia, condiciones de conservación y recepción XML desde escritorio.
6. Documenta cierre autorizado, auditoría y notificaciones; muestra la consulta coherente en web.

Ejercita por separado tipos de órgano soportados y reglas/perfiles correspondientes. Usa un caso sin aprobación externa para demostrar que el sistema conserva el registro pero bloquea una conclusión clínica no autorizada.

## E2E-C Donación voluntaria desde Android

1. Donante inicia sesión y registra o consulta su expediente propio y consentimiento.
2. Busca campaña/sede/fecha/hora, agenda una cita y recibe confirmación y recordatorio autorizado.
3. Compite con otra cuenta por el último cupo; una sola obtiene confirmación. Prueba reprogramación/cancelación.
4. Institución verifica identidad y consentimiento; médico documenta evaluación humana. Un donante sin aprobación no avanza a etapas que la exigen.
5. Operador/escritorio documenta colecta, bolsa, muestras, procesamiento/fraccionamiento y componentes derivados.
6. Pruebas y liberación autorizadas permiten incorporación a inventario, conservando vínculo de origen.
7. Donante solo ve información autorizada y avisos propios. Auditor reconstruye la cadena, sin exponer resultados privados al donante por defecto.

## Coherencia entre productos

Al menos un caso completo debe originarse en Android JSON, continuar por escritorio XML y observarse desde web con mismos IDs, estados, versiones y autorización. Verifica explícitamente que no hay conexiones cliente a PostgreSQL/MongoDB/Redis ni uso del portal como API privada.

Demuestra consumo real de al menos cuatro microservicios por Android y cuatro por escritorio, con evidencia de método/ruta/formato y persistencia. Incluye login/refresh/MFA y errores XML en escritorio; no basta con consultas de lectura en XML.

## Seguridad contratos y concurrencia

- Ejecuta contratos JSON/XML/XSD de éxito, error, paginación, tipos, límites y negociación; XML XXE/DTD/tamaño y JSON ambiguo/no finito.
- Prueba JWT alterado/expirado, firma/algoritmo/audiencia/emisor incorrectos, refresh reutilizado, logout, sesión/dispositivo revocado, MFA y reautenticación reutilizada o sobre otro recurso.
- Prueba por rol e institución todos los accesos horizontales: URL/cuerpo/query, selectores, conteos, mapas, trabajos, documentos, descargas, exportaciones, etiquetas y sincronización. Verifica evento auditado y minimización.
- Concurrencia de reservas, cobertura, cupos, edición por versión, cancelación y recepción. Comprueba restricciones SQL/efectos persistidos, no solo códigos HTTP.
- Pérdida de respuesta después del commit, mismo Idempotency-Key/mismo cuerpo y distinto cuerpo, reanudación, eventos duplicados/fuera de orden y compensación pendiente.
- Integridad de auditoría/custodia con rechazo UPDATE/DELETE del rol operativo. Explica alcance y límites de hashes sin atribuirles verdad física ni invulnerabilidad ante administrador.
- Archivos limpios/invalidos/en cuarentena, antimalware caído, firma expirada, objeto/generación ausente, tamaño máximo/exceso y datos de otra institución. Protege evidencias y exportaciones.

## Offline dispositivos y fallos

En Android y escritorio prueba borrador permitido offline, cierre/reinicio de proceso y reconexión: una sola aplicación del comando, resultado confirmado, conflicto visible y sin acción crítica falsamente confirmada. Prueba cambio de cuenta, token revocado mientras estaba offline, reloj alterado y recurso modificado por otro cliente.

Verifica QR/códigos, cámara, GPS, permisos denegados, push/deep links y detención del seguimiento al terminar tarea/logout. Distingue hardware real, emulador y dobles de prueba.

Detén en entorno aislado una réplica, todas las réplicas de un servicio, worker, gateway y dependencias PostgreSQL/Redis/MongoDB/GCS según la matriz del prompt 06. Comprueba detección, mensaje, ausencia de corrupción y recuperación. Inyectar una respuesta inválida es una prueba diferente de apagar un servicio real; registra ambas con precisión.

Demuestra operación web completa con API detenidas y clientes funcionando con una réplica fuera. Redis caído debe rechazar protección; PostgreSQL caído no debe generar escrituras simuladas. Recupera eventos, documentos y avisos sin duplicados. Repite ensayo de respaldo/restauración y mide RTO/RPO con datos conocidos.

## Rastreo GPS WSS y mapa de Nuevo León

Verifica TRACK-01 a TRACK-10 de la [especificación de rastreo GPS por WebSockets](09_rastreo_gps_websockets.md). Ejecuta el simulador a través del ingreso/validación/persistencia de Transporte y conexiones WSS reales. Comprueba en mapas interactivos actuales de Nuevo León el mismo traslado/evento en web, Android JSON y escritorio XML/XSD, sin recarga ni sustitución por polling. Incluye cobertura fuera del área metropolitana y datos fuera del estado sin descarte silencioso.

Prueba pérdida de señal, retrasos, duplicados/desorden, cursor vencido, reconstrucción de instantánea y reconexión al perder una réplica, así como caída de datos/autorización/cartografía. Rechaza dispositivos no asignados, suscripciones de otra institución, donantes y sesiones revocadas; comprueba la salida de quien pierde permiso durante un socket abierto. Mide emisores/suscriptores concurrentes, frecuencia, latencia captura/recepción/mapa, consumo y consumidores lentos. Identifica eventos simulados y la prueba física futura como pendiente; el éxito del simulador solo acredita el software y su integración.

## Volumen rendimiento y Locust

Diseña un dataset sintético reproducible con semilla, relaciones y distribución regional, estados y fechas coherentes. Define cantidades y justificación antes de medir; como escala inicial evaluable considera decenas de miles de expedientes, cien mil recursos y al menos un millón de eventos, ajustando al dominio y capacidad documentados sin inflar la cifra con filas sin uso.

Mide inserción, búsqueda/listado paginado, índices/planes, lectura de disponibilidad, caché HIT/MISS, algoritmo, reserva/cupo concurrentes, backlog y reconstrucción documental. Compara con/sin caché Redis manteniendo **autenticación y permisos Redis activos**; no apagues seguridad para construir la comparación.

Configura Locust con varios perfiles y flujos reales, renovación de sesión, pausas y distribución documentadas: donante/citas, banco/inventario, médico/solicitudes/evaluación/reserva, coordinador/traslados y transportista/custodia. Identifica JSON/XML y verifica que las tareas utilizan respuestas previas y recursos propios.

Define previamente niveles graduales de usuarios concurrentes, duración de calentamiento/carga sostenida/estrés/recuperación y criterios de error/latencia justificados para el entorno académico. No impongas un SLA clínico inventado. Saturación solo en entorno aislado con límites y presupuesto autorizados.

Reporta usuarios, peticiones/s, transacciones de negocio/s cuando difieran, media, mediana, p95/p99, errores por clase, endpoints lentos, CPU/memoria/conexiones/IO, colas, fallos y recuperación. Conserva datos brutos, configuración y gráficas. Explica límites del equipo y del dataset. No compares mediciones realizadas con condiciones distintas como si fueran equivalentes.

## Usabilidad y evidencia real

Ejecuta tareas en navegador, Android y GUI PySide6, no solo HTTP. Para cada perfil mide éxito de tarea, errores, tiempo y observaciones; verifica teclado, foco, tamaño de pantalla y mensajes. Con personas del equipo identifica participante y tarea con consentimiento; si solo hubo automatización, informa ese alcance y no lo llames estudio con usuarios.

Capturas/grabaciones deben proceder de ejecuciones reales, con datos ficticios y secretos redactados. No generes pantallas de evidencia mediante IA ni uses ejemplos estáticos como respuesta ejecutada. Vincula los resultados de interfaz con persistencia, correlación e historia.

## Cierre

Entrega regresión actual identificada, resultados por componente, contratos, seguridad, fallos, rendimiento y usabilidad, con comandos reproducibles y defectos corregidos. Conserva intentos fallidos relevantes y repeticiones sin sumar casos como si fueran distintos.

Clasifica cada criterio como aprobado, fallido o pendiente con causa. Un flujo no ejecutado, un push sin proveedor o una plataforma no compilada no se marcan aprobados. Actualiza documentación y `PROJECT_STATUS.md`; prepara la matriz final que usará el prompt 08.
