# Corregir y comprobar la etapa 03 del portal web

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Ejecuta las correcciones y su aceptación; no entregues únicamente un diagnóstico. Lee `AGENTS.md`, `PROJECT_STATUS.md`, `stuff/prompts/entrega-final/00_contexto_y_reglas.md`, `03_portal_web.md` y `09_rastreo_gps_websockets.md` de esa carpeta, además de las matrices y evidencias vigentes del portal.

## Alcance y línea base

Las etapas 01 y 02 ya fueron realizadas. Conserva su implementación, contratos y reglas; no las reconstruyas ni las declares incompletas por incorporar iOS. La etapa 03 está implementada pero pendiente de corrección y aceptación. Inspecciona cambios locales y conserva trabajo previo; consulta CodeGraph antes de localizar código si existe índice. Amplía un propietario backend solo cuando una operación del portal demuestre una carencia concreta, con contratos y regresión proporcionales.

Origen: auditoría del 06/11/2026 sobre `cbe3503b39a60b6b0a995f1284b2f5b1c3405cae` y cambios locales. Reportó 58 casos únicos aprobados (30 portal/HTTP/autonomía/identidad, 8 seguridad/documentos/laboratorio/destino, 19 rastreo/agenda y 1 confirmación perdida). Es antecedente, no ejecución nueva ni cobertura completa. El expediente se ubicó en `/private/tmp/rh-audit03-cogyvtz2/`; si ya no existe, reconstruye evidencia reproducible y declara su ausencia. No inventes resultados ni modifiques históricos.

Crea o actualiza en la documentación vigente una matriz por requisito: origen, estado actual, archivo/símbolo, acción, criterio, caso, entorno, resultado, evidencia y dependencia. Revalida los hallazgos: líneas y condiciones pueden cambiar. Mantén todos los criterios de `03_portal_web.md`; esta lista concreta sus brechas, no reduce el alcance.

## 1. Confirmación veraz e idempotencia — prioridad inmediata

Investiga `common.submit` en `apps/web/src/integration/routes/common.py` (línea 347 en la auditoría). Una reserva puede devolver `PENDING` tras perder confirmación y aun mostrar «operación completada».

Distingue aceptación, pendiente/resultado incierto, rechazo/fallo y finalización confirmada según el contrato de cada operación. No derives éxito solo de ausencia de excepción o de HTTP 2xx. Consulta el resultado antes de reintentar; conserva la misma clave e identidad del comando. Mantén valores y recuperación comprensible sin repetir efectos.

Aceptación: reproduce pérdida de respuesta después de escritura, muestra pendiente sin éxito falso, recupera el resultado y verifica una sola reserva/efecto persistido. Prueba doble envío, conflicto de versión, mismo ID con cuerpo distinto y recuperación tras reconexión. Incluye caso backend y recorrido real de formulario en navegador.

## 2. Completar operaciones del portal

- Público: publicación autorizada de instituciones/campañas y exclusión de datos privados.
- Donante: expediente propio, consentimiento/retirada/versiones, evaluación comunicada por personal autorizado, campañas e historial; rechazo de acceso cruzado.
- Agenda: selector utilizable de sede/horario sin exigir UUID manual, cupos/ocupación/asistencia, reprogramación, cancelación y recordatorios persistentes. Dos cuentas compiten por último cupo: solo una confirmación.
- Operador: colecta, procesamiento/fraccionamiento, identificación/etiquetas, componentes y linaje hasta inventario, con restricciones por facultades.
- Conservación: ubicaciones, cuarentena, vencimientos, frío, excursiones e incidencias y revisión documentada. No inventes umbrales clínicos; usa políticas sintéticas identificadas donde falte validación externa.
- Médico/laboratorio: listas de muestras, captura/revisión/corrección e historia, documentos privados, ABO/HLA, completitud/fuentes, dictamen y reserva autorizada con controles reforzados. Demuestra rechazo de evaluación incompleta.
- Destino final: recepción seguida de uso, devolución, descarte u otro cierre autorizado y pendientes de trazabilidad. `RECEIVED` no equivale al final del proceso.
- Coordinador/transportista: propuestas revisables, cobertura/tiempos y programación por ámbito; tarea propia, recolección–entrega–evidencia y custodia. Rechaza otras órdenes en acciones y descargas.
- Administración: configuración real, políticas versionadas, dispositivos y seguridad; corrige la redirección de configuración a usuarios señalada en `administration.py`. Sin autoasignación de facultades clínicas.
- Auditor: investigación, filtros, vínculos y exportación; atención y verificación con cuentas distintas, historia inmutable.
- Documentos: interfaz general de preparación/carga/análisis/verificación/versiones/retención/bloqueos y descarga autorizada del objeto/generación analizados. No limites el ciclo a evidencia de traslado. Conserva cuarentena ante motor o almacenamiento caídos.

Para cada función demuestra formulario, persistencia, resultado visible, auditoría/avisos aplicables y rechazo por perfil/ámbito. No basta con abrir paneles o probar endpoints.

## 3. Indicadores, reportes y presentación

Completa Highcharts con datos persistidos: donaciones, inventario, desperdicio/caducidad, solicitudes/tiempos, traslados, temperatura, cobertura y calidad. Define periodo, zona, población/denominador y actualización; ofrece tablas equivalentes accesibles. Prueba las gráficas activas, sin desactivarlas en el navegador de aceptación.

Haz equivalentes listado, contadores y PDF/CSV/XLSX en filtros, orden y ámbito. Revisa los filtros parciales de `quality.py` señalados por la auditoría. Incluye resumen de filtros/alcance/fecha/zona, evita truncamiento silencioso a 1.000 filas y comprueba exportación superior al límite anterior mediante trabajo paginado cuando corresponda. Reautoriza creación y descarga, prueba cambio de permiso entre ambas y protección contra fórmulas.

Verifica captura, listado, detalle y exportación en distintas zonas horarias, almacenamiento UTC, números y valores desconocidos sin convertirlos en cero o datos inventados.

## 4. Rastreo web y compatibilidad con el móvil futuro

La futura aplicación móvil funcionará en iOS y Android y será la fuente principal de ubicación. No construyas el móvil en esta corrección ni exijas GPS externo opcional. Conserva JSON móvil, XML/XSD escritorio y Transporte como autoridad. Recorre simulador → ingreso validado → persistencia → WSS real → mapa; deja aceptación desde teléfonos para 04/07.

Completa coordenadas institucionales autorizadas y marcadores origen/destino, proveedor configurable y cobertura real de Nuevo León. No inventes coordenadas: usa datos ficticios identificados en prueba y registra cualquier dato institucional pendiente. Comprueba cartografía en línea con atribución/procedencia; probar solo mosaicos bloqueados acredita degradación.

Parametriza frecuencia/antigüedad y demuestra trayecto multipunto, sin fijación, dato antiguo, desconexión sostenida, reconexión, eventos antes/durante/después del corte, recuperación de huecos y cursor caducado. No sustituyas WSS por polling ni extrapoles ubicaciones como mediciones.

Con mapa abierto prueba expiración, logout, revocación, cambio de rol y reasignación: cesa entrega a quien pierde permiso. Verifica administración de fuentes/dispositivos/asignaciones, historia autorizada, caída total y recuperación, conservando autonomía del portal. Correlaciona IDs y mide recepción–mapa; no presentes confirmación backend como latencia captura–mapa.

## 5. Aceptación real en navegador

Ejecuta por perfil acciones completas, no solo visitas: donante, operador, médico, laboratorio con facultades específicas, coordinador, transportista, administrador y auditor. Usa datos ficticios y PostgreSQL/Redis/MongoDB aislados. No detengas servicios ajenos ni alteres datos habituales.

- Login con MFA obligatorio según política, recuperación mediante SMTP de prueba real, token consumido, renovación, reautenticación, logout y sesión vencida.
- URL/IDs ajenos, acciones, búsquedas, conteos, documentos y exportaciones; cambios de rol e institución y sesión expirada. Ocultar botones no acredita seguridad.
- Formularios críticos: valores conservados, CSRF, errores por campo/resumen, foco, versiones, doble envío y respuesta perdida.
- Teclado, foco, etiquetas, contraste, tablas, diálogos, mensajes y gráficas con alternativa accesible. Comprueba 390/768/1440 px y documenta revisión automática y manual; ausencia de desbordamiento no acredita accesibilidad integral.
- Repite por separado modo modular con API detenidas y modo HTTP explícito: sangre hasta destino final; órgano con referencias/autorizaciones sintéticas identificadas; donación hasta procesamiento/componentes. Incluye historial de rastreo y resultado coherente, sin fallback automático tras escritura.

Los clientes Flask, pruebas API y mocks complementan, pero no sustituyen estos recorridos. Registra correlación, estado persistido y resultado de interfaz para cada caso.

## 6. Infraestructura y límites de aceptación

Verifica gateway WSS, GCS privado y antivirus real en entorno autorizado si están disponibles. No presentes TestBucket como GCS ni receptor ClamD de prueba como motor antivirus real. Si falta acceso/daemon/proxy, entrega configuración y ensayo local revisables, registra el criterio sin verificar y continúa trabajo independiente; no instales ni despliegues con gastos o efectos productivos sin autorización vigente.

Separa pruebas técnicas del portal de comprobaciones externas de infraestructura 06. SMTP institucional, medición física desde teléfonos en 04/07, GPS externo opcional y validación clínica externa llevan su estado propio. Su ausencia no permite aplazar pantallas o pruebas técnicas independientes de la 03, ni afirmar aceptación de infraestructura sin evidencia.

## Entregables y veredicto

Actualiza matrices, guía de operación, mapa pantalla–permiso–endpoint, evidencia en `documentation/evidencias/entrega-final/portal/` y `PROJECT_STATUS.md`. Conserva fechas, fuentes/commit o manifiesto, comandos, entornos, esperado/obtenido, capturas, JUnit y límites. Cuenta casos únicos y separa repeticiones e históricos.

Ejecuta regresión proporcional a los cambios, contratos afectados y verificaciones documentales. Entrega tabla por hallazgo: reproducido, corrección, prueba, resultado, evidencia y pendiente. No cierres con TODO críticos, listas fijas, mocks como integración o éxito supuesto.

Veredicto: **APTA** solo con todos los criterios técnicos obligatorios de 03 implementados y comprobados. **NO APTA** si quedan fallos, funciones ausentes o comprobaciones obligatorias sin ejecutar; identifica aparte dependencias externas y alcance aceptado. Un pendiente asignado a otra etapa no equivale a una prueba aprobada ni certificación productiva/clínica.
