# Cierre de sesiones del arnés Locust

La [pasada final](final/junit.xml) aprobó **2/2 en 142,93 s**, con PostgreSQL, Redis y MongoDB aislados y datos sintéticos. El recorrido lector usó seis usuarios y registró seis inicios, seis renovaciones y seis revocaciones; el transaccional usó cuatro usuarios y registró cuatro de cada una, seis ciclos completos de cita y once unidades de inventario en cuarentena. Ambos reportaron cero fallos. Se comprobaron estados persistidos, auditoría y destinatarios de las alertas tras ejecutar explícitamente el despacho de eventos.

El endpoint de revocación tiene respuesta uniforme. Por eso, para cada recorrido se consultaron las familias de esas cuentas antes y después del subprocess Locust, se excluyeron las sesiones previas y se exigió una familia nueva por usuario con `revoked_at` en PostgreSQL y sin su clave de sesión en Redis. El resultado agregado es `session_revocation_verified: true` en los resúmenes [lector](final/smoke/smoke-summary.json) y [transaccional](final/transactions/smoke-summary.json); no se guardaron tokens ni identificadores de sesión en esos artefactos. No se probó una interrupción real de Redis durante la limpieza.

La limpieza se registra una vez por Environment y se ejecuta en `test_stop`, después del drenado de usuarios y antes del JSON final. Una transacción realmente interrumpida continúa marcada como fallo; un fallo o incertidumbre de limpieza produce una métrica CLEANUP fallida. Las [pruebas ligeras](unit-junit.xml) aprobaron **21/21**, incluyendo interrupción simulada, fallos de limpieza, sesión anterior excluida, clave Redis persistente y un runner Locust con cuatro usuarios sintéticos. No demuestran por sí solas la causa exacta de la revocación ausente del intento previo.

Se conservan los intentos anteriores sin reetiquetarlos. [Intento 1](intento-1/junit.xml): dos métricas TRANSACTION fallidas durante cierre, aunque las peticiones HTTP completadas no reportaron fallos. [Intento 2](intento-2/junit.xml): cero fallos HTTP y transacciones completas, pero solo tres de cuatro respuestas de revocación; el ensayo falló. La pasada posterior de 2/2 previa al control SQL/Redis solo acredita HTTP y estado de negocio; su evidencia original permanece en `.local/load-shutdown-20261113`. La [pasada final](final/sources-before.json) y su [manifiesto posterior](final/sources-after.json) coinciden para **1091 fuentes**; los manifiestos de cada intento se conservan con ese intento.

Cada carga activa duró 12 segundos; el tiempo total incluye inicio y cierre de infraestructura. Es un ensayo funcional acotado, no una medición de capacidad, estrés, disponibilidad ni latencia extremo a extremo. Las notificaciones y auditoría se verificaron después de la carga con despacho explícito; no se atribuye su latencia al tráfico concurrente.

Reproducción desde la raíz del repositorio, con sockets locales permitidos y un directorio temporal nuevo y privado:

```sh
RH_BASE=/Users/victorberlanga/Programacion/integracion/Red-House
RH_LAB="$(mktemp -d /private/tmp/rhload.XXXXXX)"
mkdir -p "$RH_LAB/p" "$RH_LAB/results"
export REDHOUSE_TEST_ROOT="$RH_LAB/p"
export REDHOUSE_TEST_MONGOD="$RH_BASE/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_STARTUP_TIMEOUT=120
export REDHOUSE_LOAD_OUTPUT="$RH_LAB/results"
"$RH_BASE/apps/services/.venv/bin/python" -m pytest \
  apps/services/tests/test_load_probe.py --basetemp="$RH_LAB/t" \
  --junitxml="$RH_LAB/junit.xml" -q --tb=short --show-capture=no
```

La primera colección ligera intentó cargar Locust después de SSL y falló por el monkey-patch tardío de gevent. La prueba posterior evita aplicar ese parche al proceso pytest y restaura la variable de entorno antes de lanzar Locust; el fallo inicial se informó al responsable y no se presenta como ejecución aprobada.
