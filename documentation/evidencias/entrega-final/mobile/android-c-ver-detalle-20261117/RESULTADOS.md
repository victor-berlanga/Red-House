# Android C — «Ver detalle» del recordatorio persistido y reapertura, 17/11/2026

Continuación del [cierre Android C](../android-c-cierre-20261117/RESULTADOS.md) en el Mac nuevo (Darwin arm64), después de la corrección de backend `0edf74d` (`GET /api/v1/alerts/{identifier}`). Se reabrió **el mismo aviso** que generó el worker de las 17:46; no se repitieron worker, reservas, último cupo ni Qt/web.

## Laboratorio restaurado

| Paso | Evidencia | Resultado |
| --- | --- | --- |
| Integridad del paquete privado | `shasum -a 256 -c` sobre `SHA256SUMS` sin bundle ni fuentes | OK: APK Lab, `lab-cold`, `portable-lab`, manifiestos y recibos. `private-continuity.tar.gz` **no estaba descargado** (ver límites) |
| Copia fría final | `lab-cold.tar.gz`: PostgreSQL detenido limpio a las 17:59:11 CST, RDB/AOF de las 17:59, posterior al export portable de las 17:56 | Restaurada en `.local/` del clon, fuera de Git; el archivo maestro permanece intacto |
| Reubicación | Reemplazo textual de ruta equivalente a `apps/services/scripts/relocate.py` en `state.json` y `redis.conf`; binarios revinculados a Homebrew arm64; PID previos vaciados | Sin cambios en bytes de las bases. Se recrearon 12 directorios vacíos estándar de PostgreSQL que el tar omitió y permisos `0700` |
| Motores | `scripts/local.py start-infrastructure` | PostgreSQL 14.25 (copia de 14.23), MongoDB 8.0.38 (copia de 8.0.17) y Redis 8.10.2 arrancaron sobre los datos x86_64 originales sin reinicializar, sembrar ni migrar |
| Runtime | Lanzador privado nuevo: 12 apps Flask del clon en `ddea219` (incluye `0edf74d`), puertos del `state.json`, gateway HTTPS `127.0.0.1:18443` con montaje `/services/<servicio>` como `apps/mobile/tests/real_backend.py`. `TESTING=False`, `OPERATION_SCOPE=ACADEMIC` | **Sin workers**: no se ejecutó `reminders()` ni ningún otro paso del worker |
| TLS | CA efímera nueva (SAN `10.0.2.2`, `127.0.0.1`, `localhost`, vigencia 2 días), privada en `.local/` | No se publica la clave ni la CA |

## Aviso reabierto

El aviso se identificó por consulta SQL de solo lectura: `APPOINTMENT_REMINDER` `543dbbb8…`, creado a las 17:46:17 CST, destinatario `donor1` (DONOR), referido a la cita `a3bf0a00…` del horario de las **18:19:21**. Coincide con la reserva nativa del cierre anterior y con la tarjeta «Recordatorio de tu cita» de las 17:46. El preflight original encontró dos citas elegibles; la otra pertenece a la cuenta rival.

## Resultados

| Criterio | Evidencia | Resultado |
| --- | --- | --- |
| Detalle por HTTP para su destinatario | Login `donor1` → bandeja 200 (contiene el aviso) → `GET /alerts/543dbbb8…` **200** JSON: `APPOINTMENT_REMINDER`, `OPEN`, `INFO`, `DONOR`, recurso `a3bf0a00…` | **PASS** |
| Negativas del mismo GET | `donor2` sobre el mismo aviso: 404 `not_found`; `donor1` sobre UUID inexistente: 404 `not_found` | **PASS** |
| Avisos en Android | [03-avisos.png](03-avisos.png): «Recordatorio de tu cita», 17 nov 2026 · 17:46, Abierta | **PASS** |
| «Ver detalle» en Android | Un toque. Gateway: `GET /services/alertas/api/v1/alerts/543dbbb8… 200`. [04-ver-detalle.png](04-ver-detalle.png): Estado Abierta, fecha 17:46, severidad, «Aviso: Recordatorio de tu cita», sin «Respuesta no válida del servicio» | **PASS** |
| Reapertura tras `am force-stop` | Proceso ausente tras force-stop; `am start` COLD con PID nuevo; `/auth/me` 200 sin nuevo login. [05-reapertura-tras-force-stop.png](05-reapertura-tras-force-stop.png) muestra el inicio de la sesión restaurada | **PASS** |
| Detalle después del reinicio | Avisos → «Ver detalle»: nuevo `GET …/alerts/543dbbb8… 200`. [07-detalle-tras-reinicio.png](07-detalle-tras-reinicio.png) | **PASS**. Pantalla idéntica a la 04, con la misma hora del reloj; el log del gateway separa las dos lecturas: 02:18:10Z y 02:18:48Z |
| Enlace de aviso en arranque frío (`App.kt`) | force-stop → `am start --es alert_id 543dbbb8…` COLD → `/auth/me` 200 y `GET …/alerts/543dbbb8… 200`. [08-enlace-aviso-arranque-frio.png](08-enlace-aviso-arranque-frio.png) | **PASS** |
| Sin escrituras sobre el aviso | No se tocó «Marcar leído». Oráculo final: aviso `OPEN`, `acknowledged_by` nulo; 110 avisos y 4 recordatorios, igual que antes | **PASS** |
| Cierre de sesión | Un toque en «Cerrar sesión»: `devices/…/revoke` 200 y `auth/revoke` 200. [10-tras-cerrar-sesion.png](10-tras-cerrar-sesion.png): «Sesión cerrada en este teléfono y en el servicio.» | **PASS** |
| Familias propias cerradas | Tres sesiones creadas en la ventana (`donor1` HTTP, `donor2` HTTP, `donor1` app): revocadas en SQL y ausentes en Redis; `donor1` sin sesiones activas; 0 claves de sesión en Redis | **PASS** |
| Auditoría de la ventana | Sin workers, 37 eventos quedaron en outbox: LOGIN/LOGOUT ×3, READ, DEVICE_REGISTERED y DEVICE_REVOKED. Se entregaron solo con `redhouse.events.dispatch` (equivalente a `drain()` de `conftest`), sin recordatorios ni otros pasos del worker: 37 + 37 hacia Mongo, cero fallos y outbox final en cero. Antes de la ventana había cero pendientes | **PASS** |
| Apagado | Emulador `emu kill`; gateway SIGTERM con `stopped.json`; `local.py stop`: PostgreSQL, Redis y MongoDB cerraron limpio y sin listeners | **PASS**. Datos conservados en disco |

## Artefacto y entorno

- AVD nuevo `RedHouse_API30_arm64` (`system-images;android-30;google_apis;arm64-v8a`, emulador 37.2.13). El AVD de origen era AOSP API 30 x86_64; la arquitectura cambió con el host.
- APK debug Lab compilado desde `apps/mobile` con `-PmobileGateway=https://10.0.2.2:18443 -PmobileLabDirectory=<privado>`. SHA-256 `f85fcb7ad9482ad84e6af42cef8d60ea7c14a7c7532a5bd479e1f3d0640bee84`. Contiene `mobile_lab_ca.pem` y la política de red Lab, sin `lab.json` ni credenciales. No se instaló el APK Lab del paquete porque apunta a la red del laboratorio original.
- La app aplica `FLAG_SECURE`, así que `adb exec-out screencap` produce archivos vacíos. Las capturas se tomaron con `adb emu screenrecord screenshot`, que lee el framebuffer del emulador en el host. No hay captura del formulario con contraseña en esta carpeta.
- `./gradlew :composeApp:testDebugUnitTest`: **78 casos, 2 FAIL y 2 omitidos**. Ninguno es de Avisos y no se modificó código móvil:
  - `DonorPaginationTest.requestedPageAndExistingFilterArePreserved`: el doble devuelve horarios sin los campos que exige el contrato de `campaign-slots` desde `fd4fbcf`.
  - `TransportNextStepTest.locationSummaryDoesNotImplyARecentFix`: espera «Sin ubicación»; el lote final cambió el texto a «Ubicación no disponible en esta vista…».

  El lote final del 17/11 no repitió estas pruebas. Queda pendiente actualizarlas por separado. `assembleDebug` terminó con salida 0.

## Límites y pendientes

- `private-continuity.tar.gz` no estaba en la carpeta descargada. Por eso no se consultaron `reminder-oracle.private.json`, `worker-once.private.json` ni el launcher `serve_preserved_local_wss_arrivals.py`. El aviso se identificó solo por la base restaurada. No se cotejó con las huellas del oráculo `7383f512…` ni del worker `c23e56d2…` del [resumen anterior](../android-c-cierre-20261117/resumen.json). El lanzador usado es una reconstrucción mínima, no el original con hash conocido. Tampoco reproduce LOCAL storage, WSS de transporte ni las guardas de PID/propietario del original.
- La salud de servicios reporta `worker: down` por diseño de esta ventana. Las lecturas no dependen del worker.
- Siguen pendientes, sin cambios en este ensayo: traducción de `INFO`/`ELIGIBLE`, encabezado duplicado «Volver/Avisos» en el detalle, entrega push FCM, TalkBack y la recuperación de procesos con `ProcessRecoveryTest` instrumentado. La reapertura aquí es manual, con force-stop y arranque frío.
- La restauración física x86_64 → arm64 funcionó para este caso de lectura. No acredita por sí sola la equivalencia de todos los casos ni del `load-cold`.

Recibos privados, fuera de Git: `http-probe.private.json` `8373b1619525aff2aa2b19cfc12330ef602f32f9e63db5ce015c9b85cc5954c5`, `close-oracle.private.json` `3961398c5812223c7167e745e3d3274623132f1985f61cd6b9178e9069887343` y lanzador `serve_lab.py` `7d6cae8c1ec9eeb50afdb3fbe8e938f867c54295a4b8778d266275888b1397f5`. Las huellas de las capturas están en [resumen.json](resumen.json).
