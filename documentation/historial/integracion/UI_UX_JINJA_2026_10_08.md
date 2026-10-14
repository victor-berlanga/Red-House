# UI/UX, fragmentos Jinja y caché autorizada

Corte: 08/10/2026. Rama `Microservicios`. Se conserva Flask/Jinja2, JavaScript y la identidad visual de Red House. No se incorporaron Docker ni frameworks de interfaz.

## Cambios y criterios de aceptación

| Área | Comportamiento implementado | Comprobación |
| --- | --- | --- |
| Acciones | Ojo abre consulta sin formularios; lápiz abre edición cuando rol y estado lo permiten. Activar/desactivar cuenta, cancelar cita y marcar aviso tienen etiquetas explícitas. | Pruebas HTTP y Chrome; la API mantiene la autorización final. |
| Consultas | Campañas, instituciones, rutas y catálogos tienen detalle de lectura. Resumen, expediente, eventos y referencias técnicas se presentan por secciones. Los datos anidados se muestran, no se sustituyen por «Información registrada». | Modal sin formularios/scripts, consulta completa y capturas. |
| Tablas | Columnas operativas, folios completos, estados y ABO diferenciados; institución regional cuando aporta contexto. Diseño adaptable a 390 px. | 36 páginas en Chrome, siete perfiles, sin errores JavaScript/estáticos ni desbordamiento del documento. |
| Filtros | GET parcial Jinja al escribir/seleccionar, espera de 300 ms, cancelación de consultas anteriores, paginación, foco, historial y reintento. | Marcador del documento conservado; ninguna petición de navegación durante el filtrado; Atrás restaura búsqueda y resultados. |
| Edición | `return_to` interno conserva filtros/página al cancelar o guardar. No admite redirecciones a sitios externos. Nullable de campos ocultos convertido en vacío en lugar de texto `None`. | Edición HTTP persistida con versión incrementada y regreso al listado; Chrome comprueba cancelar. |
| Permisos visibles | Receptores/Solicitudes publican indicador opcional `can_edit`, calculado por su propietario; registros con historia no muestran el lápiz. Entradas directas a edición comprueban rol y estado. | Historia clínica conservada, edición rechazada y usuarios consultables sin ejecutar desactivación. |
| Actualización | Casilla opcional cada 30 s en inventario, órganos, disponibilidad, solicitudes, traslados y avisos. Se pausa con pestaña oculta, consulta pendiente, modal o borrador. | Reloj controlado del navegador comprueba una petición parcial; no se añadieron conexiones push. |
| Panel | Accesos por tarea/perfil; gráficas con tabla de datos desplegable. Coordinación no solicita un resumen de Receptores que su rol no permite. | Recorrido por perfiles y gráficos reales en Chrome. |
| Entorno | Pie discreto de pruebas y nombres sin el sufijo repetido «». Procedencia y limitaciones de reglas clínicas conservadas; motivos de la carga inicial consultables de forma desplegable. | Capturas y expediente; no se reescribieron datos clínicos ni cargas existentes. |
| Caché | Inventario/resumen 10 s, disponibilidad 15 s, catálogos 30 s; clave por usuario, ámbito, rol, versión, servicio, ruta y filtros. JWT, sesión y auditoría se ejecutan antes del HIT. | Aislamiento, revocación, JSON/XML, bypass, invalidación al commit, rollback y consulta antigua en vuelo. |

## Arquitectura y límites

El navegador consume HTML de Flask; Flask consume los contratos HTTP de los microservicios. Jinja no desapareció y no necesita Redis directamente: recibe datos cuya lectura puede aprovechar la caché del propietario. El renderizado parcial evita transferir y reconstruir toda la página. No se cachea HTML clínico compartido ni se convierte la web en propietaria de reglas.

Inventario e Identidad tienen migración aditiva `004.sql`: `cache_revision` y triggers de sentencia incrementan la generación dentro de la transacción SQL del dato. Consultas iniciadas antes de un commit pueden terminar con su fotografía anterior, pero su llenado tardío no contamina la generación nueva. La revisión se consulta en PostgreSQL incluso en HIT. Una caída de la base sigue siendo visible. El paso del tiempo puede volver orientativa una lectura durante su TTL; reserva, liberación y demás operaciones críticas validan la fuente autoritativa.

La invalidación por namespace es conservadora y puede reducir la tasa de HIT si hay muchas escrituras. La consulta periódica tampoco garantiza inmediatez: depende del intervalo, la red y las proyecciones eventuales. No se certifica escalabilidad productiva con esta revisión.

Receptores añade campos opcionales sin cambiar `/api/v1` ni cuerpos de escritura. Cada paquete de servicio conserva su propia copia de utilidades; no se añadió dependencia de plantillas o sesiones del monolito. La integración no usa la base histórica del monolito.

## Evidencias reproducibles

- [Pruebas nuevas HTTP/caché](../../../apps/services/tests/test_ui_cache.py).
- [Chrome: script](../../../apps/web/tests/integrated_ui_browser.cjs), [informe](resultados/ui/report.json).
- Capturas: [inventario](resultados/ui/inventory-desktop.png), [móvil](resultados/ui/inventory-mobile.png), [consulta](resultados/ui/record-detail.png), [panel médico](resultados/ui/medical-dashboard.png).
- [Regresión completa del incremento](resultados/ui-cache-junit.xml): 117 aprobadas de 118; el único fallo fue una aserción de migración que esperaba versiones 1–3 y encontró correctamente 1–4. Se actualizó para verificar la nueva revisión inicial; la repetición específica se registra en [resultado final](resultados/ui-final-targeted.xml): **9 aprobadas en 62.82 s**, incluida la migración. No quedan fallos sin resolver de aquella ejecución.
- [Regresión del modo histórico](resultados/ui-legacy-junit.xml): **121 aprobadas y 8 omitidas en 305.03 s**. Las omisiones de esa batería requieren herramientas o entornos opcionales indicados por cada prueba; no se presentan como aprobadas.

Una ejecución inicial de 19 pruebas web tuvo seis fallos por timeout de 2 s del fixture. El fixture ahora usa los 8 s que ya usa el cliente normal; no se aumentó el timeout productivo. La batería completa posterior no reprodujo esos timeouts. Un primer recorrido del navegador contaba `pushState` como navegación; se corrigió para contar solicitudes de documento y comprobar además que el mismo documento y foco se conservan.

## Medición local y límites del rendimiento

Se compararon 30 pares alternados con la misma cuenta, autenticación y auditoría activas, en cada endpoint. [Disponibilidad](resultados/ui-cache-comparison.json): media con caché **108.795 ms**, sin caché **100.581 ms**. [Resumen](resultados/ui-summary-cache-comparison.json): **87.782 ms** y **85.993 ms**, respectivamente. Ambas mediciones tuvieron 29 HIT, un MISS y 30 BYPASS, sin errores. **Esta muestra no demuestra reducción de latencia por Redis**; no se presenta como una mejora de velocidad. La comprobación SQL de generación y los controles de acceso se conservan en HIT. Hacen falta mediciones con volumen y carga representativos antes de afirmar beneficio o escalabilidad.

En cambio, para los mismos 20 resultados de Inventario, el [HTML parcial](resultados/ui/fragment-size.json) pasó de **28 965 a 17 837 bytes**, aproximadamente **38.4 % menos HTML**. Es tamaño de contenido sin compresión, no tiempo de red ni reducción del coste de todas las consultas. Chrome comprobó que no se reconstruye el documento completo y se mantienen foco y filtros.

## Operación local

Se respaldaron y migraron por separado Inventario e Identidad en `.local/runtime`; después se reiniciaron esos servicios, Receptores y el portal. No se borraron ni recargaron datos de negocio. Once servicios y portal respondieron disponibles tras la actualización. Respaldos privados en `.local/runtime/backups`, excluidos de Git.

En otra instalación existente: ejecutar `scripts/upgrade.py --directory RUTA --service inventario` y el equivalente para `identidad_acceso` antes de arrancar su nuevo código. Luego actualizar Receptores y la web. El lanzador no debe tratarse como un migrador automático.

La matriz Excel del corte anterior conserva los roles y permisos de API; sus descripciones/capturas de la interfaz corresponden al corte previo. Este documento y `INTEGRACION.md` describen la interfaz actual. No se amplió ningún rol por facilitar la presentación visual.

## Corrección de controles tras la revisión del usuario

Se corrigió la regla CSS que mantenía visible Filtrar pese a la actualización automática. El botón queda como respaldo sin JavaScript; no se elimina la actualización manual de listados sin filtros. El pie repetitivo de marca/entorno fue retirado, y los avisos de resultados ya no duplican visualmente el contador (se mantiene la notificación accesible).

La paginación anterior tenía enlaces numéricos poco distinguibles. Ahora Anterior/Siguiente y números tienen tamaño, separación y estados explícitos, arriba y abajo de la tabla, conservando los filtros. Al desaparecer una página se recupera la última disponible.

El selector horario está al inicio de la página y se aplica al cambiarlo. Las fechas de consulta, modales y nuevos fragmentos mantienen su instante; los formularios convierten fechas sin perder borradores. Se probó guardar la preferencia, ausencia de navegación, conversión de fechas, conservación ante 503 y operación sin JavaScript. Se mantiene CSRF y una lista cerrada de zonas (UTC y America/Monterrey); no se cambian fechas almacenadas ni contratos de MS.

Evidencias: [14 pruebas HTTP aprobadas](resultados/ui-controls-junit.xml), [5 pruebas históricas aprobadas](resultados/ui-controls-legacy.xml), [Chrome](resultados/ui-controls/report.json), [captura escritorio](resultados/ui-controls/controls-desktop.png), [captura móvil](resultados/ui-controls/controls-mobile.png). Las capturas y mediciones de tamaño de la sección anterior corresponden al corte previo a esta corrección.

## Limpieza del portal por tareas — 12/10/2026

Este incremento atiende la revisión del usuario sobre pantallas de aspecto ilustrativo. Sustituye las descripciones anteriores del menú, las confirmaciones y la ubicación del selector horario para el modo integrado. El modo histórico conserva sus funciones propias.

| Área | Criterio de aceptación y resultado |
| --- | --- |
| Administración | «Roles y parámetros» desaparece del menú; `/configuracion` redirige a Usuarios comprobando el rol. Catálogos abre Sedes; la antigua portada redirige al mismo destino. Se retiraron las dos plantillas informativas. |
| Acceso | La orientación para recuperar acceso está dentro del login; el enlace histórico abre esa ayuda. No se presenta como un restablecimiento automático. |
| Formularios | La versión de cuenta es oculta y procede del listado autorizado; la API conserva el control de concurrencia. Horarios utiliza días con nombre y controles de hora, enviando los tipos requeridos por el contrato. |
| Notificaciones y auditoría | Eventos y servicios tienen etiquetas legibles, también en CSV. Las notificaciones ofrecen acceso al registro relacionado cuando el perfil dispone de esa consulta. Las lecturas se confirman desde el listado mediante POST con CSRF e idempotencia. |
| Confirmaciones | Cancelar inscripción, evaluar candidatos, ordenar candidatos y reanudar pueden abrirse en un diálogo contextual. El GET no modifica datos; el formulario conserva destino explícito, CSRF y POST. Cerrar devuelve el foco; sin JavaScript existe la página completa. Los formularios sin campos visibles no anuncian campos obligatorios. |
| Detalles y evaluación | Se retiraron los ojos que únicamente duplicaban la fila. Usuarios e inscripciones tienen consultas autorizadas. Las referencias de expedientes/solicitudes/recursos se resuelven por sus API según perfil; ante referencia inaccesible se conserva una etiqueta sin enlace. Versiones y tiempos del algoritmo están en trazabilidad desplegable. Las limitaciones clínicas y las decisiones humanas permanecen. |
| Inscripciones | `/citas` representa explícitamente reserva de cupo en campaña, con campaña, periodo y estado; el operador también ve al donante. Consulta y cancelación buscan exclusivamente en el listado autorizado. El periodo de campaña no se presenta como una cita individual. |
| Paneles | Donante muestra inscripciones personales recientes; Auditor muestra actividad regional reciente. Se retiró el contador genérico de instituciones de esos perfiles. |
| Monitoreo | Presenta disponibilidad de operaciones primero y diagnóstico técnico desplegable, conservando dependencias, error, versión y métricas. Los permisos permanecen. |
| Horario y estados vacíos | Un único selector dentro de la cabecera conserva cambio asíncrono, conversión de fechas, borradores, CSRF y alternativa sin JavaScript. Los listados vacíos sin filtros no sugieren filtrar ni muestran paginación o exportación vacías. |
| Ubicación | El transportista puede solicitar una captura puntual del navegador solo en un traslado propio recolectado/en tránsito. `Permissions-Policy` permite geolocalización propia exclusivamente en esa pantalla autorizada. Completa coordenadas/fecha, informa precisión y requiere guardar explícitamente. Permiso denegado mantiene captura manual. Se coordinan captura y cambio horario para evitar sobrescrituras simultáneas. No hay seguimiento de fondo. |

### Evidencia y reproducción

- [Regresión HTTP](resultados/product-ui-junit.xml): **34 aprobadas**, incluyendo flujos sangre/órganos, permisos, aislamiento, sesión, formularios, CSRF, caché y paginación, 214.46 s.
- [Repetición de los cinco casos nuevos](resultados/product-ui-flows-junit.xml): **5 aprobadas**, 95.15 s, sobre los ajustes finales de inscripciones y captura. Son casos incluidos en las 34 anteriores, no cinco casos únicos adicionales.
- [Comprobación final focalizada](resultados/product-ui-final-junit.xml): **2 aprobadas**, 47.55 s, después de ajustar el texto del botón de ubicación y los estados vacíos. [Estado vacío móvil](resultados/product-ui/empty-state-report.json) comprobado y captura actualizada.
- [Recorrido Chrome](resultados/product-ui/report.json): **51 visitas**, siete perfiles, escritorio/móvil, confirmación contextual, error 503, conservación de foco/borrador/instante y alternativa sin JavaScript; cero errores JavaScript/estáticos o desbordamientos detectados. [Script](../../../apps/web/tests/product_ui_browser.cjs).
- [Ubicación en Chrome](resultados/product-ui/location-report.json): permiso y coordenadas simulados por el navegador, ninguna escritura automática, denegación recuperable y guardado real de una muestra en un traslado **temporal** de pruebas. [Script](../../../apps/web/tests/location_browser.cjs), invocado por `test_product_ui.py`. No certifica precisión GPS física.
- Capturas: [catálogos](resultados/product-ui/catalogues.png), [confirmación](resultados/product-ui/cancel-dialog.png), [donante](resultados/product-ui/donor1-panel.png), [auditor](resultados/product-ui/auditor1-panel.png), [horario móvil](resultados/product-ui/timezone-mobile.png), [inscripciones móvil](resultados/product-ui/registrations-mobile.png) y [ubicación móvil](resultados/product-ui/location-mobile.png).
- Ruff con la selección de CI y formato aprobados; sintaxis Python/Jinja/JavaScript y `git diff --check` comprobados.

Desde la raíz, con dependencias ya preparadas:

```sh
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" apps/services/.venv/bin/python -m pytest apps/services/tests/test_product_ui.py apps/services/tests/test_web_integration.py apps/services/tests/test_maintenance_web.py apps/services/tests/test_ui_cache.py -q
NODE_PATH=/ruta/node_modules node apps/web/tests/product_ui_browser.cjs --state .local/runtime/state.json --output /tmp/red-house-product-ui
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" REDHOUSE_BROWSER_MODULES=/ruta/node_modules apps/services/.venv/bin/python -m pytest apps/services/tests/test_product_ui.py -q
```

`NODE_PATH`/`REDHOUSE_BROWSER_MODULES` debe contener Playwright; los scripts utilizan Chrome instalado. Las pruebas HTTP crean servicios y bases desechables. La prueba de ubicación crea un servidor web temporal, pasa una sesión temporal en archivo privado y elimina ese archivo al terminar. El recorrido de el entorno inicia sesiones y consulta datos, pero no cancela inscripciones ni registra ubicaciones en ella.

### Alcance y pendientes conservados

No se modificaron reglas clínicas, contratos de API ni datos de negocio de el entorno. Se reinició el portal y su worker de sesiones para cargar el código. Al finalizar se detectó el entorno completo detenido mediante el comando de estado; se inició nuevamente la configuración existente para dejar disponible el portal, sin inicializar datos ni migrar bases. La agenda individual por sede/hora, el restablecimiento automático de contraseña, la validación clínica del motor, Android, escritorio y nube siguen pendientes. No se ocultaron sus limitaciones para aparentar funcionalidad terminada. Resolver campañas, donantes y referencias añade lecturas autorizadas; se reutilizan etiquetas dentro de cada petición, sin crear caché clínica compartida. Las consultas individuales de cuentas/inscripciones recorren el listado autorizado porque las API actuales no tienen esos endpoints de detalle; no se certifica su rendimiento con volúmenes masivos.

## Renovación de sesión según actividad — 12/10/2026

La web renueva en segundo plano cuando el token entra en sus últimos cinco minutos y hubo interacción real en los últimos cinco minutos. Teclado, captura, puntero, desplazamiento y toque en una pestaña visible actualizan esa actividad; las consultas periódicas, los eventos sintéticos y la mera visibilidad no la actualizan. Abrir una página visible inicia su ventana de actividad. El aviso de inactividad solo aparece cerca del vencimiento cuando no hay actividad reciente; no se ha definido un nuevo plazo fijo de inactividad independiente del JWT.

Las pestañas comparten únicamente avisos y la hora de actividad mediante BroadcastChannel. Los borradores permanecen en la página. Se reutiliza el POST protegido por CSRF y la rotación existente, manteniendo expiración, revocación y límite absoluto del backend. Un 409 de renovación concurrente consulta el estado antes de reintentar; un fallo de conexión informa del problema y limita reintentos automáticos a uno cada 30 segundos. Tras suspender una pestaña se consulta el vencimiento del servidor antes de salir por un plazo local obsoleto. El script es compartido por los dos modos web; no cambia sus contratos ni almacenes.

Evidencia: [escenarios Chrome con reloj acelerado y API simulada](resultados/session-activity-browser.json), incluido uso activo durante 36 minutos, inactividad real, continuación manual, errores 503/409/401 y coordinación entre pestañas. [Prueba HTTP integrada aprobada](resultados/session-renewal-junit.xml): renovación y cierre con servicios y bases temporales reales, tokens sin exposición y acceso revocado. No se modificaron registros de negocio en el entorno. Sin JavaScript se conserva el vencimiento del backend; la renovación automática requiere el script.

Reproducción desde la raíz:

```sh
NODE_PATH=/ruta/node_modules node apps/web/tests/session_activity_browser.cjs documentation/historial/integracion/resultados/session-activity-browser.json
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" apps/services/.venv/bin/python -m pytest apps/services/tests/test_web_integration.py::test_renewal_and_logout_revoke_backend_session_without_exposing_tokens -q
```
