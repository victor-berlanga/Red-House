# Fallos en vivo: ensayo local completo — 18 de noviembre de 2026

Base: `1ae1af5` (rama `entrega-final`). Instalación **nueva y desechable** clonada en `/private/tmp/rh-fallos-20261118`
con `bash install.sh` (34 s) y `bash start.sh` (19 s): 12/12 servicios con `/health/ready` 200 y portal en 200. Datos
sintéticos, procesos en `127.0.0.1`, sin GCP, sin Docker y sin tocar el laboratorio restaurado. Al terminar se detuvo con
`bash stop.sh` y se borró el directorio.

- Script: [demo_fallos_en_vivo.py](demo_fallos_en_vivo.py). Bitácora: [demo.json](demo.json), 113 pasos con hora, código
  HTTP, código de error, tiempo y `correlation_id`. La corrida final fue de 17:22:19 a 17:24:05 UTC: **11/11 casos
  aprobados**. Se hicieron cuatro corridas completas. La 1 falló solo en la comprobación final de sobrecarga, y las 2, 3 y 4
  aprobaron 11/11.
- Prueba automatizada de tiempo agotado y respuestas inválidas: [pytest_timeout.txt](pytest_timeout.txt), **11/11**.
- No se guardan contraseñas ni tokens. Se comprobó que `demo.json` y `pytest_timeout.txt` no contienen la contraseña ni
  las cadenas de conexión de `state.json`.
- Guion para la presentación: [Guion_fallos_en_vivo.md](../../../entrega-final/continuidad/Guion_fallos_en_vivo.md).

**Integridad.** Antes de los fallos se creó un donante testigo (`DEMO-TESTIGO-…`, Hospital 1). Después de cada caso se
comprobó que el testigo sigue con el mismo folio, nombre, versión y estado, y que existe una sola vez. También se revisó cada
alta intentada durante un fallo: existe 0 veces si fue rechazada y 1 si fue aceptada, nunca 2.

## Resultados por caso

En la columna «Cómo se provoca», `rh` equivale a `apps/services/.venv/bin/python <este directorio>/demo_fallos_en_vivo.py --repo .`.
Cada caso se puede repetir suelto con `rh caso <nombre>`.

| Caso | Cómo se provoca | Detecta / registra / informa | Recuperación | Integridad |
|---|---|---|---|---|
| **a. Microservicio detenido** (`inventario`) | `bash components.sh detener inventario` | Los otros 11 siguen con `ready` 200. Donantes responde 200. La API de Inventario rechaza la conexión. **Monitoreo** registra `inventario` `down` (`unreachable_or_invalid_response`) en el sondeo siguiente, 1.6 s después de detenerlo. El portal (monolito) muestra `/inventario` con 200 | `bash components.sh reiniciar inventario` tarda 1.8 s. Al reiniciarse registra una unidad (201) y Monitoreo marca `up` 9 s después | Testigo íntegro |
| **b. Revocar un token** | `POST /api/v1/auth/revoke` con el token de renovación y `POST /api/v1/auth/logout` | Tras revocar, el token de acceso da **401** `unauthorized` y la renovación también da 401. Otra sesión del mismo usuario sigue en 200, porque se revoca solo esa familia. Tras `logout`, el token da 401 | No aplica. El token revocado **sigue revocado** después de reiniciar Redis (caso c) | No aplica |
| **c. Redis detenido** | `rh detener-base redis` | Las peticiones autenticadas, el inicio de sesión y las altas responden **503** `redis_unavailable` en ≤ 15 ms, sin colgarse. `/health/live` responde 200 y `/health/ready` 503 en los 12 servicios (`redis` down). El portal muestra una página 503 con «Referencia» | `bash components.sh bases` tarda 1.3 s, y los 12 servicios responden `ready` en 0.2 s. **El mismo token vuelve a servir** (sesiones persistidas en AOF) y el portal vuelve con la misma sesión | Testigo íntegro. El alta rechazada existe 0 veces |
| **d. MongoDB detenido** | `rh detener-base mongodb` | `ready` 503 solo en transporte, custodia, auditoría y monitoreo. El resto y el portal siguen en 200. Un **alta de donante sí se acepta** (201), porque el negocio vive en PostgreSQL. La auditoría queda **retenida en la bandeja de salida** (35 eventos pendientes hacia MongoDB). La bitácora SQL de auditoría responde 200 y la proyección documental 503 `mongodb_unavailable` | `bash components.sh bases`: la bandeja se vacía en ≤ 2 s y todos los servicios quedan `ready`. La proyección documental pasa de 899 a 936 eventos, y el evento `DONOR_REGISTERED` del alta queda **una sola vez** en MongoDB | Testigo íntegro. El alta existe 1 vez |
| **e. PostgreSQL detenido** | `rh detener-base postgres` (apagado rápido) | `/health/live` responde 200, `/health/database` 503 y `/health/ready` 503 en los 12 servicios (`database`, `worker`). Lectura, alta e inicio de sesión responden **503** `database_unavailable` en ≤ 15 ms. El portal muestra una página 503. Los workers registran 15 `worker_failure` en 12 s | `bash components.sh bases` tarda 1.3 s, con `ready` en 0.2 s. La misma lectura y el portal, con la misma sesión, vuelven a 200 | Testigo íntegro. El alta rechazada existe 0 veces |
| **f. Tiempo excedido** | `rh pausar identidad_acceso` (SIGSTOP: acepta conexiones y no responde) | Inventario, que valida la ubicación en Identidad, responde **503** `dependency_unavailable` en **3.05 s**, el límite de lectura de 3 s. Un alta que no depende de Identidad responde 201. El inicio de sesión directo agota el tiempo del cliente | `rh reanudar identidad_acceso`. La misma petición llega a Identidad y responde 404 `not_found`, porque la ubicación es ficticia | Ninguna unidad con el folio del intento |
| **f'. Respuesta inválida** | Sin forma limpia en vivo: `pytest tests/test_dependency_timeout_unit.py` | Con HTML, HTML 502, lista, sin `meta`, sin `data`, JSON truncado o conexión cerrada, la respuesta es **503** `dependency_unavailable`. Un 409 legítimo conserva su código | No aplica | 11/11 pruebas |
| **g. Archivo inexistente** | `GET /api/v1/documents/<uuid nuevo>` y `GET /api/v1/files/<uuid>/download` | **404** `not_found` en ambos. Un identificador mal formado da 400 `validation` | No aplica | No aplica |
| **h. Sobrecarga** | 240 `GET /api/v1/campaigns` de `operator1`, con 24 en paralelo | En 0.94 s hubo 160 respuestas 200 y **80 respuestas 429** `rate_limit`, con `Retry-After: 60` (cuota de 180 por minuto por cuenta y servicio). Durante la ráfaga, `operator2` recibe 200 y `/health/ready` 200. Latencia máxima: 0.14 s | Al cambiar la ventana de un minuto, `operator1` vuelve a ser atendido; esta vez a los 25 s | Testigo íntegro |
| **i. Sin permisos** | `operator2` (Hospital 2) abre el donante testigo del Hospital 1. `donor1` registra inventario. `auditor1` registra un donante | **403** `forbidden` en los tres casos, y 401 sin token. El rechazo entre instituciones queda **auditado** (`REJECTED`) con el mismo `correlation_id` | No aplica | Testigo íntegro |
| **j. Servicio de archivos no disponible** | `bash components.sh detener documentos`; luego, almacén privado sin permisos (`chmod 000 .local/runtime/private-files`) | Sin el proceso, los otros 11 siguen en 200 y la API rechaza la conexión. El portal (monolito) sigue mostrando los documentos del testigo (200). Con el almacén inaccesible, `/health/storage` y `/health/ready` de Documentos responden **503** (`storage` down) | `bash components.sh reiniciar documentos` (1.6 s) y `chmod 700`: `/health/storage` `up` (`local`) | Testigo íntegro |
| **k. Explicar un error en los logs** | `grep <correlation_id> .local/runtime/<servicio>.log` | Se encontró la línea de **10 de 10** errores provocados (ver abajo). Cada línea JSON trae servicio, `correlation_id`, método, ruta, estado, milisegundos y código de error, sin cuerpo, token ni datos personales | No aplica | No aplica |

### Cómo encontrar un error en los logs

1. Toda respuesta trae `X-Correlation-ID` en la cabecera y `meta.correlation_id` en el cuerpo. El cliente también puede
   enviar su propio `X-Correlation-ID`, siempre que sea un UUID. El portal muestra el mismo dato como «Referencia».
2. Los logs de la instalación local están en `.local/runtime/`: `<servicio>.log` para la API, `<servicio>-worker.log` para el
   worker, y además `postgres.log`, `redis.log` y `mongodb.log`.
3. Para encontrarlo: `grep -i <correlation_id> .local/runtime/*.log`. Ejemplos de esta corrida:

```text
inventario.log  {"service": "inventario", "method": "POST", "route": "/api/v1/resources", "status": 503, "elapsed_ms": 3031.8, "error": "dependency_unavailable"}
donantes.log    {"service": "donantes", "method": "GET", "route": "/api/v1/campaigns", "status": 503, "elapsed_ms": 6.8, "error": "redis_unavailable"}
auditoria.log   {"service": "auditoria", "method": "GET", "route": "/api/v1/documentary-events", "status": 503, "elapsed_ms": 1159.0, "error": "mongodb_unavailable"}
donantes.log    {"service": "donantes", "method": "GET", "route": "/api/v1/donors/<identifier>", "status": 403, "elapsed_ms": 23.3, "error": "forbidden"}
donantes.log    {"service": "donantes", "method": "GET", "route": "/api/v1/campaigns", "status": 429, "elapsed_ms": 14.7, "error": "rate_limit"}
donantes-worker.log  ERROR:root:worker_failure service=donantes exception_type=APIError   (durante la caída de PostgreSQL)
postgres.log    FATAL:  terminating connection due to administrator command
```

(Se omitió el `correlation_id` de cada línea; está completo en [demo.json](demo.json).)

Cómo explicarlo: el servicio, la ruta y el estado dicen qué falló. El código de error dice por qué: `dependency_unavailable`
es otra API que no respondió, `redis_unavailable` y `database_unavailable` son bases caídas, `rate_limit` es la cuota y
`forbidden` es el permiso. `elapsed_ms` muestra que no se quedó colgado: 3,032 ms corresponde al límite de lectura de 3 s.

## Límites y hallazgos

- **Hallazgo (observabilidad del portal, no corregido).** La página de error del portal muestra una «Referencia», que es el
  `correlation_id`, pero esa referencia **no aparece en ningún log** local: `web.log` quedó vacío en toda la corrida. El
  manejador de `BusinessError` en `apps/web/src/integration/__init__.py` no registra nada, y `apps/web/scripts/run_web.py`
  no configura `logging`. En modo monolito, las apps de dominio embebidas tampoco emiten su línea de petición. Por eso, para
  «explicar un error en los logs» conviene usar una llamada a la API, no la referencia del portal.
- **Hallazgo menor.** El rechazo 403 entre instituciones se audita como `REJECTED`, pero esa acción no está en
  `redhouse/audit_catalog.py`. Queda en la categoría `TECHNICAL`/`UNKNOWN` y no aparece en la vista predeterminada del
  auditor (`BUSINESS`, `DECISION`, `SECURITY`). Hay que filtrar con `categories=ALL`. El 403 por rol se rechaza antes de
  identificar al actor y solo queda en el log del servicio.
- Las líneas de log locales no traen marca de tiempo: ni el JSON de petición ni `worker_failure`. El orden se reconstruye
  por `correlation_id` y por la hora de `demo.json`. En la VM, `docker compose logs --timestamps` agrega la hora.
- `components.sh` no tiene un comando para detener **una** base. Para eso se usa `rh detener-base`, que señala solo el PID
  verificado de esta instalación. El reinicio sí es el documentado: `bash components.sh bases`.
- En la instalación local cada API tiene un solo proceso. Detenerlo deja su API sin respuesta, porque no hay pasarela que
  responda 502 o 503. El portal no se afecta porque corre en modo monolito con las apps de dominio embebidas. En la VM hay
  dos réplicas por API detrás de Nginx; ver el guion.
- La respuesta inválida no se provoca en vivo: se demuestra con la prueba automatizada.
- Las caídas sostenidas duraron 12 a 15 s. No se midió una caída larga (minutos) ni la alerta `SERVICE_DEGRADED` que
  Monitoreo emite hacia Alertas.
- Todo es local. El guion para la VM de GCP no se ejecutó en este bloque.
