# Seguridad y recuperación del portal — 13/14 de noviembre de 2026

I06-08 queda **PARCIAL**. A (cursor fuera de ventana), C (logout conectado) y D (expiración natural de familia) aprobaron individualmente. B (logout durante caída y recuperación de otra sesión autorizada) falló en ambos intentos. La regresión dirigida I06-07 aprobó por separado. No se cierra la etapa 06 ni se suman estos procesos como una suite de cinco casos aprobados.

La dirección inspeccionó las capturas de A, C, D y la recuperación de 07. También revisó los estados parciales de B. Las ejecuciones fueron locales, con bases sintéticas nuevas y procesos propios. La ventana pesada se devolvió a dirección después de cerrar esos procesos; no hubo pruebas adicionales tras B02.

## Ejecuciones independientes

| Caso | Intento | Fuente | Resultado | Duración JUnit | Evidencia |
| --- | --- | --- | --- | --- | --- |
| A: cursor fuera de ventana | 01 | S1 | 1/1 aprobado | 155,604 s | [JUnit](cursor-resync/intento-01/junit.xml), [revisión](cursor-resync/intento-01/review.json) |
| B: logout durante caída | 01 | S1 | 0/1; publicador recibió 502 | 133,934 s | [JUnit](logout-disconnected/intento-01/junit.xml), [diagnóstico inicial](logout-disconnected/intento-01/diagnosis.json) |
| B: observador recuperado antes de publicar | 02 | S2 | 0/1; publicador recibió 502 | 165,722 s | [JUnit](logout-disconnected/intento-02/junit.xml), [revisión](logout-disconnected/intento-02/review.json) |
| C: logout con mapa conectado | 01 | S1 | 1/1 aprobado | 111,090 s | [JUnit](logout-live/intento-01/junit.xml), [revisión](logout-live/intento-01/review.json) |
| D: expiración natural de familia | 01 | S1 | 1/1 aprobado | 189,569 s | [JUnit](session-expiry/intento-01/junit.xml), [revisión](session-expiry/intento-01/review.json) |
| Regresión I06-07 | 01 | S1 | 1/1 aprobado | 155,397 s | [JUnit](regresion-i06-07/intento-01/junit.xml), [revisión](regresion-i06-07/intento-01/review.json) |

Cada fila se ejecutó con un proceso pytest y entorno nuevos. Se revisó el ciclo de vida del fixture: el contexto autónomo cierra los listeners y su salida restaura las referencias y servidores. No se atribuye a una ejecución conjunta una independencia que no se ensayó. Las 1394 fuentes censadas coinciden antes/después de cada intento. [Índice legible por máquina](execution-index.json).

## Qué se comprobó

**A.** `TRACKING_REPLAY_WINDOW=2`; `context.setOffline` únicamente en el perfil observador emuló la pérdida de red. Se mantuvieron WSS y protocolo nativos. Tras publicar puntos suficientes fuera de ventana, llegaron `resync.required`, instantánea autorizada y aviso explícito de historial incompleto. El documento original mostró el punto 4 de la instantánea y después el punto 5 en vivo, sin inventar puntos intermedios. SQL y Mongo conservaron los cinco IDs/cursores, sin duplicados; outbox drenado y ambas réplicas sanas. Se aceptan recuperación y hueco visible; no continuidad completa del historial. [Hueco](cursor-resync/intento-01/portal-gateway-cursor_resync/security-03-resync-explicit-gap.png), [retorno en vivo](cursor-resync/intento-01/portal-gateway-cursor_resync/security-04-live-after-gap.png).

**C.** Logout real por el portal con mapa abierto: familia SQL revocada, sesión ausente en Redis y auditoría única. Dos publicaciones posteriores recibieron ACK `PERSISTED_SQL`; tres puntos finales coinciden en SQL/Mongo. La sesión cerrada quedó en login, sin mapa/historial privado ni recepción posterior. Volver al recurso protegido siguió denegado. [Pantalla final](logout-live/intento-01/portal-gateway-logout_live/security-03-protected-map-stays-denied.png).

**D.** Configuración exclusiva del laboratorio: acceso 330 s y familia de renovación 90 s. Esta inversión permite observar renovación real con `session.js` intacto: ventana fija de aviso de 300 s, tick de un segundo. Hubo dos renovaciones exitosas y avance del vencimiento del acceso; la familia original mantuvo su límite. El primer 401 llegó 3402 ms después del vencimiento SQL, cuando el JWT de acceso aún estaba vigente. Se prueba vencimiento de familia/estado Redis, **no vencimiento del JWT de acceso**. Las respuestas de autenticación observadas fueron `[200,200,200,200,200,401]`, sin 429/503 ocultos. SQL conservó familia vencida sin revocación explícita, Redis la retiró y no se produjo LOGOUT.

No se modificaron relojes, timers, validadores ni Redis directamente. Se conservaron fechas SQL con microsegundos y su conversión a milisegundos; la precisión en segundos del token sigue siendo un límite al interpretar el borde temporal. El caché de permisos humanos estaba presente al vencer la familia. La credencial de dispositivo independiente obtuvo ACK para los puntos 2 y 3 **antes** del login técnico de restauración: la ausencia de datos tardíos no depende de que el publicador hubiese quedado inhabilitado.

Después de esas guardas se hizo un login técnico real para restaurar el fixture. Se volvió a comprobar que la familia antigua seguía vencida/ausente. Reponer en memoria las cookies antiguas produjo inicialmente GET protegido **302 hacia login**, seguido de página de login; no se aceptó un mapa 200 transitorio. No surgieron nuevos sockets, frames ni datos privados. La restauración técnica no se contabiliza como renovación de la sesión vencida. [Runtime](session-expiry/intento-01/portal-gateway-session_expiry/runtime.json), [login final](session-expiry/intento-01/portal-gateway-session_expiry/security-03-expired-protected-map-denied.png).

**Regresión 07.** Se repitió el recorrido completo sobre S1: una réplica caída y después ambas; cancelación de inscripción desde portal autónomo durante caída total, SQL/actor/auditoría comprobados; recuperación del mismo documento con tres IDs/cursores únicos en mapa, SQL y Mongo; restauración de ambas réplicas. La dirección revisó la captura 09. Es una regresión independiente del ensayo previo de 157,31 s y no reemplaza su expediente. La inscripción sintética no tiene horario asignado. [Runtime](regresion-i06-07/intento-01/portal-gateway/runtime.json).

SQL verifica `tracking_points.id/cursor`; la proyección real Mongo es `events.metadata.position.event_id/cursor`. No se usa la colección de custodia como sustituto de telemetría. Los ACK se comparan con el `event_id` y traslado publicados, además de exigir `state=PERSISTED_SQL`.

## B continúa fallido

B01 sí comprobó logout y eliminación de datos privados de la sesión revocada. No completó recuperación/publicación de la otra sesión: el nuevo publicador recibió 502. La terminación posterior del proceso Node fue limpieza tras el error Python, no la causa primaria.

Antes de B02 se aprobó una corrección acotada del arnés. Se guardó la frontera de sockets antes del corte. Tras restaurar B, se exigió un socket nuevo del perfil autorizado, mismo documento, `authenticated`, `subscribed cursor=1` y abierto. Solo entonces se permitió el primer publish, sin reintentos adicionales. Los listeners estaban instalados antes de las acciones.

B02 demostró esa recuperación real y aun así falló el handshake del publicador. Réplica A `127.0.0.1:58306` permaneció caída; B `127.0.0.1:58370` se restauró. Cronología UTC:

| Observación | Hora |
| --- | --- |
| Inicio de restauración B | 04:57:20.434420 |
| Salud directa B 200 | 04:57:26.902450 |
| Último rechazo de conexión explícito, dirigido a A | 04:57:50, precisión de segundos |
| Socket autorizado nuevo, autenticado/suscrito y abierto | 04:57:51.861 |
| Padre recibe confirmación y abre publicador; 502 en ese segundo | 04:57:51.862462 |

El error final Nginx fue `no live upstreams`; no quedó un nuevo `ECONNREFUSED` hacia B después de su salud. La línea de acceso 101 se escribe al cerrar la conexión y contiene duración, sin instante absoluto de handshake ni peer. No permite reconstruir su milisegundo por orden de líneas. [Log B02 saneado](logout-disconnected/intento-02/nginx-safe.log), [configuración y diagnóstico](nginx-diagnosis.json).

La versión local exacta es **Nginx 1.30.6**. Su fuente de round robin excluye peers dentro de la ventana de fallo; al elegir una prueba tras el plazo actualiza `checked` sin limpiar ahí `fails`. El callback de liberación limpia fallos tras éxito y la conexión upgraded permanece abierta hasta finalizar el túnel. Esto proporciona un mecanismo compatible con los logs: el primer WSS recuperado podría conservar fallos previos mientras el segundo intenta seleccionar upstream. **Es inferencia sustentada, no lectura de `fails/checked/conns` en ejecución.** Esos valores internos no se capturaron. La revisión independiente coincidió con esta delimitación. [Documentación upstream](https://nginx.org/en/docs/http/ngx_http_upstream_module.html), [ciclo de vida del peer](https://nginx.org/en/docs/dev/development_guide.html).

La configuración observada usa dos workers, zona compartida `transporte`, `max_fails=1`, `fail_timeout=2s`, sin límite explícito `max_conns`; WSS y HTTP comparten upstream. No hay `tries=2` explícito en esas rutas. Queda propuesta separada, aún sin ejecutar ni aplicar en este expediente: grupo y zona exclusivos WSS, mismos destinos con `max_fails=0`, failover de handshake `error timeout` con dos intentos y conexión TCP de un segundo, preservando HTTP. Debe pasar primero una prueba discriminante real y simétrica de ambos peers, con primer WSS abierto y segundo inmediato. Un segundo de conexión TCP **no** limita todo el Upgrade: el timeout de lectura de 75 s puede demorar cabeceras de un peer TCP vivo. No hay replay de mensajes después de 101.

Compose declara `nginx:1.28-alpine`; no se cambió su imagen. El análisis y los ensayos locales de 1.30.6 no validan sintaxis ni recuperación de la imagen publicada. Una futura publicación requiere revisar versión/configuración efectiva y preservar los JSON de aplicaciones/almacenamiento. No se preparó acceso remoto ni se ejecutó configuración en GCP.

## Reproducción y fuentes

[Comandos exactos por proceso](commands.json) conserva entorno, nodeID y ruta de salida. Ejemplo A, desde la raíz y dentro de una ventana autorizada:

```sh
REDHOUSE_BROWSER_TESTS=1 \
REDHOUSE_TEST_NGINX="$PWD/.local/tools/nginx-1.30.6/sbin/nginx" \
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_BROWSER_RESULTS="$PWD/documentation/evidencias/entrega-final/portal-security-20261114/cursor-resync/intento-nuevo" \
apps/services/.venv/bin/python -m pytest \
'apps/services/tests/test_portal_gateway_tracking.py::test_portal_gateway_security_states[cursor_resync]' \
-q --tb=short --junitxml=/private/tmp/i0608-cursor-intento-nuevo.xml
```

Usar un directorio nuevo por intento; no sobrescribir los existentes. B02 añade `--basetemp` privado propio. Los logs completos originales permanecen privados; `pytest.txt`, JUnit, runtime y navegador públicos están saneados. No se incluyen credenciales, cookies, tokens ni DSN.

[Versiones y hashes completos](source-versions.json) vincula cada intento a sus dos fuentes. Base: `eac2c1a16ed78c636df204a507f87129682edc9a`. [Parche S1](harness-S1.patch) reconstruye las fuentes ejecutadas por A/B01/C/D/07 sobre esa base. [Parche S2](harness-S2.patch) transforma S1 en el arnés actual, ejecutado **solo por B02, fallido**. No se transfieren los aprobados S1 a S2 como regresiones recién ejecutadas.

| Fuente | S1 SHA-256 | S2 SHA-256 |
| --- | --- | --- |
| `apps/services/tests/test_portal_gateway_tracking.py` | `966b3c1f54c53d0b5bdcdf106ab71064c177289d90616d46936a582f70367c71` | `a8cbd562cadcf064279052a668454fba4a29f7bcc8849a912a4b662424d75f77` |
| `scripts/verify_portal_gateway_tracking.cjs` | `89d6e17757c3ff7c49e23eac7c12101ddd05db186e031b2d74eb7480c5cf94a5` | `d32ccc1e582e99d26413fd8348287dd975d89b9f8b59d249512740099cb59712` |

AST, Ruff, formato, sintaxis Node y aplicación limpia de los parches se verifican por separado, sin atribuirles un ensayo real. No cambió código de servicio ni configuración de producto durante este lote.

## Límites y conservación

- Chrome real y Nginx HTTPS/WSS real del mismo origen, sin reemplazar WebSocket ni inyectar resultados. Comunicación de control Python/Node por stdin/stdout, sin endpoint de control público.
- Fixture con PostgreSQL/MongoDB/Redis reales, `TESTING=True` y cuotas HTTP 100000. Usuarios de laboratorio DONOR/TRANSPORT sin MFA; no se rebajan roles críticos. No prueba capacidad, rate limiting ni MFA.
- Certificado efímero confiado explícitamente por Python; excepción Chrome limitada al SPKI del certificado y perfil efímero. No acredita cadena CA confiada por el sistema ni modifica Keychain global.
- Mosaicos OSM bloqueados para evitar consumo; fondo gris y aviso revisados. No acepta cartografía. WSGI de laboratorio, sin Docker ni GCP.
- Todos los puntos usan `25.6866,-100.3161`, precisión 8 y origen SIMULATOR. Se prueban IDs, cursores, persistencia y reconexión; no desplazamiento físico, GPS ni geometría vial. Los tiempos de replay incluyen cortes deliberados; no son un SLA de captura backend–mapa.
- Cambio de rol y revocación de asignación permanecen pendientes separados. B sigue fallido, I06-08 parcial y demás I06 abiertos según su evidencia propia.
- [Mejoras de texto posteriores](follow-up-ui.json): explicar historial incompleto sin exponer cursor/ventana/instantánea y trasladar la nota de configuración institucional fuera del flujo normal. No se alteraron producto ni selectores en esta aceptación.

[Asociación de entornos](environment-links.json) conserva rutas exactas, UID/modo y UUID público encontrado en la base propia. Son observaciones previas a la limpieza posterior. Dirección archivó/retiró A01, C01, D01 y regresión 07 tras guardas repetidas; **esas bases ya no están disponibles**. Logs y evidencia se conservan. B01/B02 permanecen para diagnóstico. [Registro de retiro](../limpieza-20261113/temporales.json), commit `e5f75d9`. Ningún archivo de estado/DSN privado se incorporó a esta evidencia.
