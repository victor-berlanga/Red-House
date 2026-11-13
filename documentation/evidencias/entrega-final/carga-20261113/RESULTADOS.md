# Arnés de carga — 13/11/2026

Estado: **arnés funcional comprobado; rendimiento sostenido pendiente**. Locust 2.46.7 instalado. El arnés anterior no renovaba tokens ni revocaba sesiones y dejaba usuarios sin token en tareas vacías después de un login fallido. No es una comparación de rendimiento ni se modifica la evidencia histórica de aquellas mediciones.

El cliente nuevo valida contratos JSON/XML de respuesta, renueva anticipadamente de forma secuencial y revoca su último token de renovación al terminar. Una respuesta perdida de renovación no se reintenta ni provoca otro login silencioso. Los errores se registran mediante códigos fijos, sin cuerpos/tokens, y se eliminan credenciales locales incluso si falla la revocación. La carga solo admite IP de loopback con puerto explícito y requiere activar el modo de laboratorio. La comparación de caché usa `Cache-Control: no-cache` en lecturas; no desactiva Redis ni autorización.

La línea base reparte seis perfiles y usa XML completo para operador. Incluye agenda y feed público del donante, tareas/detalle autorizado del transportista y consultas de médico/coordinación/auditoría. El detalle utiliza el ID devuelto por el listado y la página siguiente depende del conteo del servidor. **Todavía no implementa carga transaccional completa de cita, reserva ni custodia y no cierra 07.**

Comprobación ligera, sin servicios ni red:

```sh
apps/services/.venv/bin/python -m pytest apps/services/tests/test_load_client.py -q --tb=short --junitxml=/private/tmp/redhouse-load-client-unit.xml
apps/services/.venv/bin/locust -f apps/services/tests/locustfile.py --list
```

Unitarias: **12 aprobadas en 2,04 s** con dobles, incluidos destinos rechazados, rotación JSON/XML, revocación, respuesta perdida sin reintento, identidad equivocada y contrato inválido. [JUnit](junit-cliente.xml). `fuentes-unitarias.sha256` se capturó después del ensayo; no se presenta como comparación antes/después. Ruff de errores y formato pasaron. `locust --list` terminó con código 0 y mostró `RegionalUser`; salida observada, sin log persistido.

## Ensayo funcional real

Primera ejecución: tres casos, **dos aprobados y uno fallido en 62,63 s**. Los dos aprobados pertenecen a búsqueda de dispositivos JSON/XML, documentados por separado en escritorio. El caso Locust falló al buscar las revocaciones en el CSV periódico: esa instantánea precedía al cierre. El proceso Locust terminó con código 0; su salida final privada contiene seis revocaciones sin error. No se convierte retrospectivamente ese caso en aprobado. Se preservan [JUnit y estadísticas originales](intento-1/junit.xml) y la fuente original del ensayo, reconstruida y contrastada con el hash capturado antes de ejecutarlo.

Corrección del arnés: usar `--json-file` y leer el JSON final que Locust 2.46.7 guarda después de `runner.quit()`. Se conserva el CSV temporal para analizar la serie; no se lo presenta como la última instantánea del cierre. No cambió el cliente de carga ni el servidor por este fallo.

Repetición dirigida: **1/1 aprobado en 57,17 s**, con PostgreSQL/MongoDB/Redis y doce servicios HTTP reales temporales. Seis usuarios, incorporación de dos por segundo y ventana programada de doce segundos; una rotación anticipada forzada por usuario. **Seis logins, seis renovaciones y seis revocaciones, cero fallos de petición/contrato** en el [resultado final](repeticion/smoke-summary.json). [JUnit](repeticion/junit.xml) y [estadísticas completas](repeticion/smoke-final.json). Cada ejecución conserva 963 hashes de fuentes/contratos antes y después, sin diferencias durante su intervalo. No se suman las dos ejecuciones como una suite nueva.

La repetición prueba lecturas reales de los seis perfiles y XML para operador; no modifica la expiración JWT del servidor. El dataset inicial no contenía traslados ni más de veinte campañas: las ramas de detalle de traslado y segunda página no se ejercitaron en este ensayo. Servidores Werkzeug con hilos y límites de consumo elevados del fixture, sin TLS/Nginx/réplicas; generador y servidor en el mismo Mac. No mide capacidad, estrés, seguridad de las cuotas ni flujos transaccionales completos. Los procesos temporales cerraron al terminar. Datos, credenciales y salida privada permanecen fuera del repositorio.

Reproducción dirigida (desde la raíz; requiere herramientas PostgreSQL/Redis y MongoDB del laboratorio):

```sh
RH_LOAD_ROOT=$(mktemp -d /private/tmp/rhl.XXXXXX)
export REDHOUSE_TEST_ROOT="$RH_LOAD_ROOT"
export REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_STARTUP_TIMEOUT=120
export REDHOUSE_LOAD_OUTPUT="$RH_LOAD_ROOT/results"
apps/services/.venv/bin/python -m pytest apps/services/tests/test_load_probe.py -q --tb=short --show-capture=no --basetemp="$RH_LOAD_ROOT/pytest" --junitxml="$RH_LOAD_ROOT/junit.xml"
```

La ejecución inicial añadió `apps/services/tests/test_device_search_scope.py` al mismo comando. La [planificación previa](PLAN.md) fija dataset, fases, límites y objetivos para las mediciones que siguen pendientes.

Base del uso de `on_start`, `on_stop`, `catch_response` y `HttpSession`: [documentación oficial de Locust](https://docs.locust.io/en/2.46.7/writing-a-locustfile.html). Los resultados propios anteriores proceden del JUnit local, no de esa documentación.
