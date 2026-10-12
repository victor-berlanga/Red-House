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
| Entorno | Pie discreto de pruebas y nombres sin el sufijo repetido « · DEMO». Procedencia y limitaciones de reglas clínicas conservadas; motivos de la carga inicial consultables de forma desplegable. | Capturas y expediente; no se reescribieron datos clínicos ni cargas existentes. |
| Caché | Inventario/resumen 10 s, disponibilidad 15 s, catálogos 30 s; clave por usuario, ámbito, rol, versión, servicio, ruta y filtros. JWT, sesión y auditoría se ejecutan antes del HIT. | Aislamiento, revocación, JSON/XML, bypass, invalidación al commit, rollback y consulta antigua en vuelo. |

## Arquitectura y límites

El navegador consume HTML de Flask; Flask consume los contratos HTTP de los microservicios. Jinja no desapareció y no necesita Redis directamente: recibe datos cuya lectura puede aprovechar la caché del propietario. El renderizado parcial evita transferir y reconstruir toda la página. No se cachea HTML clínico compartido ni se convierte la web en propietaria de reglas.

Inventario e Identidad tienen migración aditiva `004.sql`: `cache_revision` y triggers de sentencia incrementan la generación dentro de la transacción SQL del dato. Consultas iniciadas antes de un commit pueden terminar con su fotografía anterior, pero su llenado tardío no contamina la generación nueva. La revisión se consulta en PostgreSQL incluso en HIT. Una caída de la base sigue siendo visible. El paso del tiempo puede volver orientativa una lectura durante su TTL; reserva, liberación y demás operaciones críticas validan la fuente autoritativa.

La invalidación por namespace es conservadora y puede reducir la tasa de HIT si hay muchas escrituras. La consulta periódica tampoco garantiza inmediatez: depende del intervalo, la red y las proyecciones eventuales. No se certifica escalabilidad productiva con esta revisión.

Receptores añade campos opcionales sin cambiar `/api/v1` ni cuerpos de escritura. Cada paquete de servicio conserva su propia copia de utilidades; no se añadió dependencia de plantillas o sesiones del monolito. La integración no usa la base histórica del monolito.

## Evidencias reproducibles

- [Pruebas nuevas HTTP/caché](../tests/test_ui_cache.py).
- [Chrome: script](../../web-monolito01/tests/integrated_ui_browser.cjs), [informe](evidence/ui/report.json).
- Capturas: [inventario](evidence/ui/inventory-desktop.png), [móvil](evidence/ui/inventory-mobile.png), [consulta](evidence/ui/record-detail.png), [panel médico](evidence/ui/medical-dashboard.png).
- [Regresión completa del incremento](evidence/ui-cache-junit.xml): 117 aprobadas de 118; el único fallo fue una aserción de migración que esperaba versiones 1–3 y encontró correctamente 1–4. Se actualizó para verificar la nueva revisión inicial; la repetición específica se registra en [resultado final](evidence/ui-final-targeted.xml): **9 aprobadas en 62.82 s**, incluida la migración. No quedan fallos sin resolver de aquella ejecución.
- [Regresión del modo histórico](evidence/ui-legacy-junit.xml): **121 aprobadas y 8 omitidas en 305.03 s**. Las omisiones de esa batería requieren herramientas o entornos opcionales indicados por cada prueba; no se presentan como aprobadas.

Una ejecución inicial de 19 pruebas web tuvo seis fallos por timeout de 2 s del fixture. El fixture ahora usa los 8 s que ya usa el cliente normal; no se aumentó el timeout productivo. La batería completa posterior no reprodujo esos timeouts. Un primer recorrido del navegador contaba `pushState` como navegación; se corrigió para contar solicitudes de documento y comprobar además que el mismo documento y foco se conservan.

## Medición local y límites del rendimiento

Se compararon 30 pares alternados con la misma cuenta, autenticación y auditoría activas, en cada endpoint. [Disponibilidad](evidence/ui-cache-comparison.json): media con caché **108.795 ms**, sin caché **100.581 ms**. [Resumen](evidence/ui-summary-cache-comparison.json): **87.782 ms** y **85.993 ms**, respectivamente. Ambas mediciones tuvieron 29 HIT, un MISS y 30 BYPASS, sin errores. **Esta muestra no demuestra reducción de latencia por Redis**; no se presenta como una mejora de velocidad. La comprobación SQL de generación y los controles de acceso se conservan en HIT. Hacen falta mediciones con volumen y carga representativos antes de afirmar beneficio o escalabilidad.

En cambio, para los mismos 20 resultados de Inventario, el [HTML parcial](evidence/ui/fragment-size.json) pasó de **28 965 a 17 837 bytes**, aproximadamente **38.4 % menos HTML**. Es tamaño de contenido sin compresión, no tiempo de red ni reducción del coste de todas las consultas. Chrome comprobó que no se reconstruye el documento completo y se mantienen foco y filtros.

## Operación local

Se respaldaron y migraron por separado Inventario e Identidad en `.local/demo`; después se reiniciaron esos servicios, Receptores y el portal. No se borraron ni recargaron datos de negocio. Once servicios y portal respondieron disponibles tras la actualización. Respaldos privados en `.local/demo/backups`, excluidos de Git.

En otra instalación existente: ejecutar `scripts/upgrade.py --directory RUTA --service inventario` y el equivalente para `identidad_acceso` antes de arrancar su nuevo código. Luego actualizar Receptores y la web. El lanzador no debe tratarse como un migrador automático.

La matriz Excel del corte anterior conserva los roles y permisos de API; sus descripciones/capturas de la interfaz corresponden al corte previo. Este documento y `INTEGRACION.md` describen la interfaz actual. No se amplió ningún rol por facilitar la demostración visual.

## Corrección de controles tras la revisión del usuario

Se corrigió la regla CSS que mantenía visible Filtrar pese a la actualización automática. El botón queda como respaldo sin JavaScript; no se elimina la actualización manual de listados sin filtros. El pie repetitivo de marca/entorno fue retirado, y los avisos de resultados ya no duplican visualmente el contador (se mantiene la notificación accesible).

La paginación anterior tenía enlaces numéricos poco distinguibles. Ahora Anterior/Siguiente y números tienen tamaño, separación y estados explícitos, arriba y abajo de la tabla, conservando los filtros. Al desaparecer una página se recupera la última disponible.

El selector horario está al inicio de la página y se aplica al cambiarlo. Las fechas de consulta, modales y nuevos fragmentos mantienen su instante; los formularios convierten fechas sin perder borradores. Se probó guardar la preferencia, ausencia de navegación, conversión de fechas, conservación ante 503 y operación sin JavaScript. Se mantiene CSRF y una lista cerrada de zonas (UTC y America/Monterrey); no se cambian fechas almacenadas ni contratos de MS.

Evidencias: [14 pruebas HTTP aprobadas](evidence/ui-controls-junit.xml), [5 pruebas históricas aprobadas](evidence/ui-controls-legacy.xml), [Chrome](evidence/ui-controls/report.json), [captura escritorio](evidence/ui-controls/controls-desktop.png), [captura móvil](evidence/ui-controls/controls-mobile.png). Las capturas y mediciones de tamaño de la sección anterior corresponden al corte previo a esta corrección.
