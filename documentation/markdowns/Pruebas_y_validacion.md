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
