# I06-07: continuidad del portal y recuperación WSS

Resultado vigente: **1 caso aprobado de 1, sin errores ni omisiones, en 157,31 s**, en el [intento 04](intento-04/junit.xml). Ejecutado el 13/11/2026 en Monterrey; las observaciones del navegador corresponden al 14/11/2026 UTC. Los intentos 01, 02 y 03 se conservan separados y no se suman como aprobados. La dirección inspeccionó las capturas 05/06/08/09 y aceptó este recorrido acotado. **No cierra la etapa 06 ni los demás casos de aceptación integrada.**

## Recorrido comprobado

El laboratorio utilizó PostgreSQL, MongoDB y Redis temporales reales, portal Flask/Jinja con backend modular `monolith`, Nginx real y dos procesos separados de Transporte. El gateway se generó mediante `deployment/gcp/configure_public.py`; se adaptaron los destinos loopback, puertos efímeros, rutas TLS/temporales y Host con puerto local. Se conservaron las rutas y las políticas de fallo del proxy generado. Todos los listeners API de la fixture y su servidor TLS auxiliar de rastreo quedaron cerrados antes del recorrido del navegador. No se accedió a producción ni a GCP.

Chrome mantuvo abierto el mapa con la cuenta sintética TRANSPORT. Sus WebSocket nativos usaron `/services/transporte/ws/v1/tracking/json` por el mismo origen HTTPS de Nginx. No se sustituyó WebSocket ni se interceptaron o fabricaron sus respuestas. Se registraron **tres handshakes 101**, ocho intentos de socket incluyendo los fallidos durante el corte, eventos recibidos y `redhouse:position-rendered`. El navegador no registró errores JavaScript de página. [Observaciones del navegador](intento-04/portal-gateway/browser.json).

| Paso | Resultado observado y persistido |
|---|---|
| Dos réplicas | Primer punto con ACK `PERSISTED_SQL`, correlación de `event_id`/`shipment_id` y cursor 1; mapa «En vivo · SIMULADO». |
| Réplica A detenida | Mapa desconectado conservando el primer punto; botón «Reconectar» abrió conexión nativa nueva por B. Segundo punto con cursor 2 y mapa nuevamente en vivo. |
| Ambas réplicas detenidas | Gateway respondió 502 al Upgrade y rechazó la conexión WSS. Mapa abierto mostró desconexión y conservó sus dos filas/IDs y el marcador. No se publicaron posiciones durante este corte. |
| Mutación autónoma | En una segunda ventana/perfil Chrome, DONOR canceló su inscripción sintética con formulario y CSRF reales: GET 200, POST 302 y recarga del detalle 200. SQL quedó `CANCELLED`, con un evento `APPOINTMENT_CANCELLED` del actor correcto y un registro de auditoría. Los listeners API y ambas réplicas seguían cerrados al comprobarlo. |
| Restauración de B | Se reenviaron los dos puntos previos, un tercero nuevo y ese tercero repetido: ACK con cursores **1, 2, 3, 3**, todos `PERSISTED_SQL` y correlacionados con el mensaje publicado. El documento original reconectó automáticamente, sin botón, navegación, recarga ni polling HTTP del mapa. |
| Restauración de A | Ambas réplicas respondieron `live=200` y `ready=200`. El mapa original siguió en vivo con tres filas únicas; nueva captura sin navegar. |
| Persistencia final | Tres IDs/cursores iguales en SQL, MongoDB y filas del mapa; proyección drenada y cero posiciones pendientes en outbox. |

La instancia de documento conservó `performance.timeOrigin = 1794625340324.1` en todos los estados del mapa. La recuperación puede volver a disparar el evento de renderizado de un ID ya conocido; la unicidad comprobada corresponde a las filas DOM y a los registros SQL/Mongo, no al número de notificaciones de renderizado. [Resultado técnico](intento-04/portal-gateway/runtime.json).

| Cursor | ID sintético conservado en SQL, Mongo y DOM |
|---|---|
| 1 | `96061936-3a50-425d-9150-edc14c59d961` |
| 2 | `3cba9837-e4dd-4837-a178-e30dda94005f` |
| 3 | `7c77ed5b-239d-4a8d-96d5-eadd20862308` |

La fuente física SQL es `tracking_points.id/cursor`. En Mongo, la proyección de posición se conserva en **`events.metadata.position.event_id/cursor`**, filtrada por `source=transporte` y `metadata.position.shipment_id`. La colección `shipment_tracking` representa secuencias de estado/custodia y no se confundió con posiciones GPS.

## Inspección y límites

Se revisaron las capturas de [caída total](intento-04/portal-gateway/05-all-replicas-stopped.png), [cita cancelada](intento-04/portal-gateway/06-appointment-cancelled-without-apis.png), [recuperación con B](intento-04/portal-gateway/08-recovered-same-map.png) y [ambas réplicas restauradas](intento-04/portal-gateway/09-both-replicas-restored-same-map.png). Los estados visibles coinciden con la evidencia estructurada. [Revisión de artefactos](intento-04/artifact-review.json).

- Los **tres puntos comparten latitud 25.6866 y longitud -100.3161**, precisión sintética 8 m y fuente `SIMULATOR`. Lo define [el helper `point`](../../../../apps/services/tests/test_final_tracking.py); el arnés lo llama con secuencias 1/2/3 sin sobrescribir coordenadas. Las capturas conservan esa misma coordenada. Se prueban identidad, cursor, deduplicación, conservación y reconexión; **no se prueba desplazamiento físico, GPS de dispositivo, geometría vial ni tráfico**.
- La inscripción cancelada pertenece a una campaña sintética **sin horario ni sede asignados**, camino permitido por el dominio. No acredita confirmación, reprogramación ni agenda detallada por sede/hora.
- La fixture usa `TESTING=True` y cuotas HTTP de prueba de **100000**; Transporte mantiene sus controles propios de conexión/mensajes. No es una medición de capacidad, saturación o disponibilidad productiva. Los 157,31 s incluyen preparación y cierre; no constituyen un RTO.
- Los recorridos Chrome usan DONOR y TRANSPORT. No se desactivó MFA de roles críticos para realizarlos; esta ejecución de fixture no acredita MFA ni una configuración de seguridad productiva completa.
- Python verificó TLS confiando explícitamente en el certificado efímero del ensayo. Chrome utilizó una excepción **SPKI limitada a ese certificado**, con perfiles efímeros separados; sin `ignoreHTTPSErrors`, bypass TLS global ni cambios al Keychain. No acredita una cadena CA confiada por el sistema operativo o un certificado público de producción.
- Los mosaicos OSM se bloquearon para evitar consumo masivo. La superficie gris y el aviso «Cartografía no disponible» son esperados. **La cartografía no queda aceptada** por este caso.
- El portal utilizó WSGI de prueba con la política real `TrustedProxy` para un peer loopback. Nginx y los dos procesos de Transporte fueron reales; no se acredita Docker DNS, Waitress productivo, redundancia de host o despliegue GCP.
- No se ensayaron cursor fuera de ventana, revocación durante desconexión, cambio de rol, expiración ni logout con mapa abierto; pertenecen a I06-08 y siguen pendientes.

## Intentos conservados

| Intento | Resultado propio | Interpretación y corrección |
|---|---|---|
| [01](intento-01/setup-result.json) | Error de setup, 3,66 s. Sandbox rechazó `bind` loopback antes de iniciar motores/navegador. | Bloqueo de entorno, sin resultado funcional. Repetición autorizada con escalación acotada. |
| [02](intento-02/diagnosis.json) | Fallo del arnés, 128,83 s. Llegó a mapa desconectado con dos IDs; no llegó a verificar la mutación. | Selector global `button[type=submit]` ambiguo en página autenticada. Se acotó al botón «Cancelar inscripción». La excepción original guardó tipo `Error`, sin texto; atribución al selector sustentada en plantilla/captura, no en un mensaje de error conservado. |
| [03](intento-03/diagnosis.json) | Fallo del arnés, 123,84 s. La captura mostró «Cambio registrado» y cita cancelada, pero agotó la espera de respuesta. | La plantilla usa `request.full_path`, que añade `?` vacío. El predicado exigía igualdad textual de URL. Se comparan ahora origen/ruta y método POST, manteniendo 302 y la recarga del detalle. La URL de la respuesta fallida no se conservó; esa atribución se documenta como inferencia apoyada por plantilla y comprobación Flask aislada. |
| [04](intento-04/pytest.txt) | **1/1 aprobado, 157,31 s.** | Recorrió mutación, SQL/auditoría, recuperación, ambas réplicas y Mongo. Única ejecución aceptada de este caso. |

Cada intento funcional conserva sus fuentes antes/después, capturas y fallos sanitizados. En el 04, **1394 archivos de fuentes/configuración tienen hashes idénticos antes y después**. El cotejo de procesos al cerrar no encontró candidatos del laboratorio; [comprobación de cierre](intento-04/cleanup-check.json). El examen de artefactos no encontró los patrones buscados de JWT, DSN o claves privadas; no equivale a una auditoría exhaustiva de secretos.

## Fuentes y reproducción

| Archivo | SHA-256 de la ejecución aceptada |
|---|---|
| [Test Python](../../../../apps/services/tests/test_portal_gateway_tracking.py) | `03d559809f7e055ed8366d0bdf71fb528d4e49d10a8d5b2f92a26072c1aeafc5` |
| [Runner Chrome](../../../../scripts/verify_portal_gateway_tracking.cjs) | `fa12fe02ca02c1850d0679bb4403f574eec80457654b7366cd54922c01faae3f` |
| [Manifiesto previo](intento-04/portal-gateway/sources-before.json) y [posterior](intento-04/portal-gateway/sources-after.json) | Ambos `23deb23952e0d2ab8e8e517e274780184e12e89cad4558ad126cc2198430847f` |

Se requieren dependencias Python del proyecto, PostgreSQL/Redis locales, MongoDB, Nginx, Chrome y Playwright instalado en `.local/gcp-public/browser/node_modules/playwright`. Los binarios usados fueron `.local/tools/nginx-1.30.6/sbin/nginx` y `.local/tools/mongodb-8.0.17/bin/mongod`. La comunicación de cortes Python–Node usa stdin/stdout, sin endpoint de control ni comandos recibidos por el navegador. Credenciales de fixture viajan por stdin privado y no se incorporan a la evidencia.

Comando de reproducción desde la raíz, **solo durante una ventana asignada** y con tapa abierta. La ejecución aceptada utilizó `intento-04`; el ejemplo usa `repeticion-01`, que debe ser un directorio nuevo. No sobrescribir los intentos conservados. La plataforma que restrinja sockets loopback requiere la misma escalación acotada autorizada para procesos propios.

```sh
REDHOUSE_BROWSER_TESTS=1 \
REDHOUSE_TEST_NGINX="$PWD/.local/tools/nginx-1.30.6/sbin/nginx" \
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_BROWSER_RESULTS="$PWD/documentation/evidencias/entrega-final/portal-gateway-20261113/repeticion-01" \
apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_portal_gateway_tracking.py -q --tb=short \
  --junitxml=documentation/evidencias/entrega-final/portal-gateway-20261113/repeticion-01/junit.xml
```

Ruff, formato Python, parseo AST, `node --check` y `git diff --check` aprobaron antes de la ejecución aceptada. No se modificó código del producto ni se ejecutaron pruebas adicionales para redactar este informe.
