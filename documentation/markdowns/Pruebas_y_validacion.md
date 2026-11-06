# Pruebas y validación

Los tests ejecutables permanecen junto al código. Los resultados históricos están en `documentation/historial/<entrega>/`. El cierre del segundo parcial usa [documentation/evidencias/segundo-parcial](../evidencias/segundo-parcial/RESULTADOS.md), con fecha, versión, fallos y repeticiones explícitos.

## Reproducción

```bash
apps/services/.venv/bin/python -m pip install -r apps/services/requirements-dev.txt
apps/services/.venv/bin/python -m pytest apps/services/tests -q
apps/services/.venv/bin/python apps/services/scripts/check_launcher.py --report /tmp/launcher.json
```

Requiere PostgreSQL, Redis y MongoDB locales. `REDHOUSE_TEST_MONGOD` permite indicar el binario de MongoDB. Las pruebas crean un entorno temporal propio; no recargan las bases del portal. Los recorridos de navegador del portal se encuentran en `apps/web/tests/`.

En macOS, mantener la tapa abierta durante toda la ejecución. Para evitar la suspensión por inactividad puede anteponerse `caffeinate -i` al comando de pytest; no evita la suspensión por cerrar la tapa. No aumentar timeouts ni repetir operaciones automáticamente para compensar un equipo suspendido.

Para investigar fallos intermitentes, añadir `--log-file=/private/tmp/redhouse-tests.log --log-file-level=INFO -o junit_logging=all -o junit_log_passing_tests=false --junitxml=/private/tmp/redhouse-tests.xml`. Los registros de las API incluyen servicio, ruta, estado, duración y correlación; el cliente web registra el tipo de excepción de transporte. El CI conserva el log y el JUnit incluso cuando falla la ejecución. En otros sistemas, ajustar la ruta temporal.

La suite cubre contratos JSON/XML/XSD, autenticación y permisos, migraciones, reserva/traslado/custodia, archivos, resiliencia, caché y portal integrado. La comprobación del lanzador recorre preparación, inicio, parada, conflictos y conservación de configuración.

## Resultados

Segundo parcial, 19/10/2026: [regresión final](../evidencias/segundo-parcial/regresion-final.xml) con **182 aprobadas**, cero fallos y cero omisiones, en **2005.90 s**, incluyendo GCS real. Después se añadió y ejecutó una [prueba complementaria de salud](../evidencias/segundo-parcial/salud-complementaria.xml), aprobada en **36.08 s**; se informa separada. Las [huellas de implementación](../evidencias/segundo-parcial/source-validation.json) coinciden con el código capturado en la regresión.

Docker aprobó [nueve controles de negocio y continuidad](../evidencias/segundo-parcial/docker-release/docker-results.json). Chrome verificó 20 páginas de siete perfiles, datos Highcharts, adaptación móvil, GCS y Swagger. El [expediente HTTP](../evidencias/segundo-parcial/http/index.html) contiene 284 métodos/rutas con éxito y captura, 240 con error y justificación para los 44 documentos fijos. El [respaldo restaurado](../evidencias/segundo-parcial/backup-restore.json) conserva conteos/hashes de SQL, MongoDB y usuarios/roles, además de una clave Redis con TTL. El informe de [resultados](../evidencias/segundo-parcial/RESULTADOS.md) conserva incidentes, repeticiones y límites; no se suman cifras históricas.

Revisión del 15/10/2026: **19 pruebas web aprobadas en 444.23 s**, con 1 317 respuestas API registradas y sin respuestas 5xx desde las API. La única excepción de conexión web registrada corresponde al apagado deliberado de Identidad en su prueba de resiliencia. Se identificó suspensión por cierre de tapa durante la suite anterior con dos fallos: los logins de ambos casos coinciden con el intervalo de suspensión y despertares parciales. [Diagnóstico y límites](../historial/2026-10-15/resultados/diagnostico-503.json) y [JUnit web](../historial/2026-10-15/resultados/diagnostico-503-web.xml). Esta repetición cubre el módulo web completo; no sustituye una nueva ejecución de los 171 casos.

Reorganización del 14/10/2026: **164 pruebas aprobadas** en 597.68 s, **14 comprobaciones reales** del lanzador y **51 visitas de Chrome**. La comparación durante la migración conservó las filas de 111 tablas; se verificaron las 18 cadenas de custodia del entorno regional.

- [Estado y límites de la reorganización](../historial/2026-10-14/REORGANIZACION.md).
- [Validaciones anteriores](../historial/integracion/VALIDACION_HASTA_2026_10_12.md), con sus fechas; no acreditan por sí solas el código actual.

Conservar un informe por ejecución relevante y sus condiciones. No sumar casos repetidos ni declarar éxito por ausencia de errores en una captura. El CI remoto y las plataformas no ejecutadas deben identificarse como pendientes.

## Captura reproducible del segundo parcial

```sh
GOOGLE_CLOUD_PROJECT=sistemas-integracion-01 \
REDHOUSE_GCS_TEST_BUCKET=red-house-evidencias-sistemas-integracion-01 \
REDHOUSE_HTTP_EVIDENCE=/private/tmp/redhouse-http-final \
REDHOUSE_RESULT_DIR=/private/tmp/redhouse-results-final \
apps/services/.venv/bin/python -m pytest apps/services/tests -q \
  --junitxml=/private/tmp/redhouse-final.xml
apps/services/.venv/bin/python scripts/build_http_evidence.py \
  /private/tmp/redhouse-http-final --output documentation/evidencias/segundo-parcial/http
node scripts/capture_http_evidence.cjs documentation/evidencias/segundo-parcial/http
```

GCS requiere ADC autorizado y el paquete `requirements-storage.txt`. Sin bucket se omite explícitamente la prueba real, no se sustituye por una nube simulada. El capturador diferencia HTTP real, WSGI y llamadas modulares, y conserva headers/cuerpo/correlación/versiones con secretos redactados. Las capturas corresponden al visor de transacciones reales; los JSON completos están enlazados, incluso cuando la pantalla requiere desplazamiento.

Las operaciones de escritura incluyen consulta posterior de idempotencia, operación, inbox o sesión Redis/SQL. Una verificación no disponible queda visible; no se infiere persistencia por recibir 200. Las pruebas adicionales verifican archivos privados, proyección MongoDB, rollback/reutilización de conexiones y continuidad web con listeners detenidos. Docker se certifica por separado mediante operaciones de negocio y recuperación; un readiness 200 no sustituye esas pruebas.

## Corrección de reglas y algoritmos — 0.4.3

[Expediente nuevo con JUnit, intentos y fuentes](../evidencias/entrega-final/algoritmos/correccion_comprobacion/20261101T042648Z/RESULTADOS.md). Pruebas aisladas reales de PostgreSQL/Redis/MongoDB, JSON/XML/XSD, navegador Chrome/TLS con API detenidas y controles reforzados; GCS privado real para documento de resultado, receptor TCP de análisis identificado como fixture. [Comandos, permisos, configuración y límites](../entrega-final/algoritmos/correccion/Operacion_y_reproduccion.md). Los casos históricos no se suman a los nuevos; aceptación clínica permanece externa.

## Revisión técnica local — 4 de noviembre de 2026

Se conservó el árbol previo, incluidos los archivos sin seguimiento. La revisión
utilizó CodeGraph antes de localizar código. No se hicieron commits, despliegues,
migraciones ni cambios en instalaciones habituales. Las bases y WSS de pruebas
se crearon en directorios temporales con puertos locales propios.

Cambios confirmados:

- `ms_compatibilidad/laboratory.py`: `completeness` leía dos veces las acciones de
  gobernanza, una desde `validity` y otra para el fingerprint. Ahora utiliza una
  misma lectura para vigencia, fingerprint y habilitación. Cada invocación vuelve
  a leer la base; no hay caché entre recursos ni peticiones. `evaluation_create`
  evita abrir una transacción vacía cuando el recurso no tiene perfil vinculado.
- `ms_transporte/tracking.py`: bajo el mismo bloqueo del traslado, `cursor == head`
  demuestra que el replay está vacío. Se omite solo esa consulta; permanecen la
  lectura de posición, vigencia de asignación, autorización y comprobación de la
  ventana. Un evento posterior al corte se recupera en el siguiente sondeo.
  `tracking_socket.py` centraliza la emisión de `position.updated`, incluyendo su
  reautorización inmediatamente anterior. No cambia la frecuencia de sondeo,
  Redis, cuotas, timeouts, buffers ni mensajes JSON/XML.
- `ms_priorizacion_geografia/academic.py`: las cinco ramas pasan a funciones
  privadas en el mismo módulo. `execute` conserva validación, salida común y
  despacho. Los cuerpos, versiones, cálculos y desempates se preservan.
- `redhouse/client.py` y `apps/web/src/integration/client.py`: el callback ligado
  registrado con `atexit` retenía la
  sesión de cada hilo finalizado hasta terminar el proceso. Una prueba con hilo,
  referencia débil y cierre instrumentado reproduce la retención. El finalizador
  débil conserva únicamente los adaptadores, permite liberar la sesión al salir
  del hilo y cierra ambos pools. Se conserva reutilización por hilo y eliminación
  de cookies entre llamadas.

No se retiraron controles de seguridad, migraciones ni compatibilidad histórica.
La inspección de `atomic`, `dispatch` y `consume` mostró bloqueo por clave,
resultado/efectos SQL atómicos y deduplicación por evento/fingerprint. La entrega
outbox mantiene una transacción durante HTTP; es un costo real de su modelo de
entrega y no se cambió sin demostrar un defecto. No se centralizaron reglas de
servicios independientes ni se añadieron reintentos.

Límites y pendientes: persiste costo lineal por candidato con perfil; reutilizar
perfiles entre recursos requiere definir el corte de gobernanza y las carreras
con resultados/correcciones. La mejora actual evita una lectura redundante sin
ampliar transacciones. El sondeo WebSocket conserva costo por suscripción;
introducir notificaciones o snapshots en lote exige probar recuperación entre
réplicas y revocación. No se acredita saturación, GPS físico ni operación clínica.

La revisión de `freshness.current` también reprodujo dos lecturas del contexto del
receptor cuando existía snapshot. Se reutiliza una lectura en la comparación y
la comprobación de completitud; los snapshots históricos sin contexto conservan
el motivo `RECIPIENT_LABORATORY_CHANGED`. Con cero perfiles del receptor, las
consultas de ese contexto bajan de seis a tres. No se reutiliza entre peticiones.

Medición instrumentada de `evaluation_create`, siete repeticiones por caso,
misma entrada antes/después, sin red ni persistencia de la evaluación; PostgreSQL
sustituido por filas sintéticas. La mitad del inventario queda fuera por componente;
la mitad restante son candidatos y uno de cada cuatro recursos tiene perfil.
Un único perfil compartido, sin resultados. Se incluye el contexto del receptor;
se excluye la transacción final de escritura y auditoría, que no cambia.

| Examinados | Candidatos | Con perfil | Transacciones antes/después | SQL antes/después | Mediana ms antes/después |
| --- | --- | --- | --- | --- | --- |
| 4 | 2 | 1 | 3 / 2 | 9 / 8 | 7,397 / 6,367 |
| 40 | 20 | 10 | 21 / 11 | 63 / 53 | 10,362 / 10,810 |
| 400 | 200 | 100 | 201 / 101 | 603 / 503 | 25,846 / 21,972 |

El caso intermedio no mejora tiempo; los contadores, no una promesa de latencia,
justifican el cambio. Los presupuestos y la clasificación se reproducen con
`tests/test_review_costs.py`, incluidos casos sin perfil, aislamiento y liberación
de sesiones. El benchmark instrumentado no mide latencia de red ni rendimiento
productivo. No hay reducción de consultas por compartir perfil entre candidatos:
se conserva deliberadamente una lectura vigente por cada candidato.

Medición adicional con PostgreSQL/Redis temporales reales, mismas filas y código
anterior conservado en copias temporales. Laboratorio: perfil sintético compartido
sin resultados, tres repeticiones, mediana; incluye abrir/cerrar cada transacción.

| Candidatos | Perfiles | SQL antes/después | Transacciones antes/después | Mediana ms antes/después |
| --- | --- | --- | --- | --- |
| 1 | 1 | 6 / 5 | 1 / 1 | 26,66 / 25,65 |
| 10 | 1 | 60 / 50 | 10 / 10 | 263,75 / 261,68 |
| 100 | 1 | 600 / 500 | 100 / 100 | 2597,74 / 2521,36 |

Rastreo: diez ciclos de autorización más snapshot con PostgreSQL/Redis reales.
Se repiten 1, 4 u 8 lecturas por ciclo sobre el mismo traslado sintético; esto
modela el costo de suscripciones, **no son ocho traslados ni ocho sockets
concurrentes**. Activo significa cursor con un evento por recuperar; inactivo,
cursor en cabecera. SQL y Redis son totales de diez ciclos; tiempo es mediana por
ciclo. La reautorización adicional al enviar, cuotas de socket y publicación no
están incluidas en estos contadores; permanecen sin cambios y se prueban en WSS.

| Lecturas/ciclo | Estado | SQL antes/después | Redis antes/después | Mediana ms antes/después |
| --- | --- | --- | --- | --- |
| 1 | Activo | 50 / 50 | 10 / 10 | 23,96 / 26,78 |
| 1 | Inactivo | 50 / 40 | 10 / 10 | 24,54 / 27,90 |
| 4 | Activo | 200 / 200 | 40 / 40 | 112,48 / 125,27 |
| 4 | Inactivo | 200 / 160 | 40 / 40 | 110,91 / 108,01 |
| 8 | Activo | 400 / 400 | 80 / 80 | 224,16 / 222,43 |
| 8 | Inactivo | 400 / 320 | 80 / 80 | 226,08 / 268,24 |

Cero errores en las mediciones. La reducción SQL es reproducible; los tiempos
mixtos no demuestran mejora general de latencia. Sigue pendiente medir conexiones
completas con distintos traslados bajo carga sostenida. No se atribuye a este
microbenchmark la cobertura de concurrencia de las pruebas WSS independientes.

Validación y aceptación:

- Primer intento dentro del sandbox: **30 aprobadas, un fallo y ocho errores,
  63,54 s**; todos los bloqueos ocurrieron al abrir puertos temporales
  (`PermissionError` en `free_port`). WSS separado: un error de preparación,
  2,62 s, por la misma restricción. No son regresiones del código.
- Línea base con permiso para localhost, antes de editar: **56 aprobadas,
  546,03 s**, cero fallos/errores. Selección: `test_stage02_oracles.py`,
  `test_review_unit.py`, `test_final_algorithms_hla.py`, `test_final_tracking.py`.
- Las pruebas nuevas reprodujeron primero cuatro fallos: gobernanza duplicada,
  dos variantes de replay vacío y sesión de servicios retenida. Después se
  reprodujeron individualmente la lectura duplicada del receptor y la retención
  equivalente en web. No se cambiaron las expectativas para aprobar.
- Regresión ampliada: **139 aprobadas, 1011,64 s**, cero fallos/errores/omisiones.
  Incluye la selección base, los siete casos focalizados iniciales,
  `test_stage02_corrections.py`, `test_security_contracts.py`,
  `test_resilience.py` y dos mediciones temporales. Cubre JSON/XML/XSD, aislamiento,
  expiración/revocación, WSS real con dos procesos, replay, concurrencia,
  idempotencia, fallos de dependencias, contradicciones, sucesores y correcciones
  de laboratorio. El arnés temporal de comparación no se incorpora al producto.
- Los cambios posteriores de `freshness.current` y del cliente web se verificaron
  con una ejecución independiente sobre las fuentes finales: **36 aprobadas,
  394,75 s**, cero fallos/errores/omisiones. Incluye los 14 casos de
  `test_review_costs.py`, todo `test_web_integration.py`, las dos representaciones
  de `test_recipient_lab_change_invalidates_review_detail_and_reserve` y
  `test_recipient_correction_serializes_with_reservation_commit`.
- OpenAPI: **12 aprobadas, 65,25 s** en `test_openapi_documentation.py`;
  `python apps/services/scripts/document.py --check-openapi` terminó con código 0.
  No se regeneraron contratos ni se alteraron `$ref` o esquemas persistentes.
- Los 14 casos focalizados finales también pasaron aisladamente en **1,28 s**.
  Estos conteos se solapan; no se suman como pruebas únicas.
- AST de las cinco ramas idéntico; Ruff con la selección de CI
  `--select E9,F63,F7,F82` sobre servicios e integración web, formato de los diez
  archivos Python modificados y `git diff --check` aprobados. Se comprobaron las
  rutas previas de Git y los diffs fuera del alcance; no se eliminó trabajo previo.

Reproducción de la selección final adicional, desde la raíz:

```bash
apps/services/.venv/bin/pytest -q \
  apps/services/tests/test_review_costs.py \
  apps/services/tests/test_web_integration.py \
  apps/services/tests/test_stage02_corrections.py::test_recipient_lab_change_invalidates_review_detail_and_reserve \
  apps/services/tests/test_stage02_oracles.py::test_recipient_correction_serializes_with_reservation_commit
```

El fixture crea y detiene PostgreSQL, MongoDB, Redis y servidores locales propios;
requiere permiso para puertos localhost. No se aumentaron timeouts ni se omitieron
casos para obtener estos resultados. La suite completa del repositorio, CI remoto,
GCP, navegador físico y carga sostenida no se ejecutaron en esta revisión.
