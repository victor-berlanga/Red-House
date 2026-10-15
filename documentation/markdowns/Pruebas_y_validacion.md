# Pruebas y validación

Los tests ejecutables permanecen junto al código. Los informes seleccionados están dentro de `documentation/historial/<entrega>/`, no en una carpeta independiente de evidencias.

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

Revisión del 15/10/2026: **19 pruebas web aprobadas en 444.23 s**, con 1 317 respuestas API registradas y sin respuestas 5xx desde las API. La única excepción de conexión web registrada corresponde al apagado deliberado de Identidad en su prueba de resiliencia. Se identificó suspensión por cierre de tapa durante la suite anterior con dos fallos: los logins de ambos casos coinciden con el intervalo de suspensión y despertares parciales. [Diagnóstico y límites](../historial/2026-10-15/resultados/diagnostico-503.json) y [JUnit web](../historial/2026-10-15/resultados/diagnostico-503-web.xml). Esta repetición cubre el módulo web completo; no sustituye una nueva ejecución de los 171 casos.

Reorganización del 14/10/2026: **164 pruebas aprobadas** en 597.68 s, **14 comprobaciones reales** del lanzador y **51 visitas de Chrome**. La comparación durante la migración conservó las filas de 111 tablas; se verificaron las 18 cadenas de custodia del entorno regional.

- [Estado y límites de la reorganización](../historial/2026-10-14/REORGANIZACION.md).
- [Validaciones anteriores](../historial/integracion/VALIDACION_HASTA_2026_10_12.md), con sus fechas; no acreditan por sí solas el código actual.

Conservar un informe por ejecución relevante y sus condiciones. No sumar casos repetidos ni declarar éxito por ausencia de errores en una captura. El CI remoto y las plataformas no ejecutadas deben identificarse como pendientes.
