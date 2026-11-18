# Android: correcciones de UI en Avisos, accesibilidad y sesión móvil (17/11/2026 CST)

Continúa [«Ver detalle» Android C](../android-c-ver-detalle-20261117/RESULTADOS.md) en el Mac arm64 y reutiliza su laboratorio: fixture restaurado `kojcusww`, lanzador privado `serve_lab.py` `7d6cae8c…` sin workers y la misma CA privada. No se restauró, no se reinicializó, no se sembró nada y no se cambiaron relojes ni caducidades. Tampoco se repitieron worker, reserva, último cupo ni Qt/web. Para leer el detalle se volvió a abrir el aviso `543dbbb8…` de `donor1` sin escribir sobre él.

Fuente: `bc92f8d` con cambios en `apps/mobile` que no tienen commit (resumen abajo). AVD `RedHouse_API30_arm64` (`google_apis` arm64). Hay dos APK debug Lab (`-PmobileGateway=https://10.0.2.2:18443`): `2b86126b…` es el primero y `55427a64…` incluye la corrección del mensaje 401. Las capturas se tomaron con `adb emu screenrecord screenshot` por `FLAG_SECURE`. Ninguna muestra contraseñas, tokens ni la CA.

## Resultados

| Caso | Evidencia | Resultado |
| --- | --- | --- |
| Encabezado del detalle de Avisos | [04-ver-detalle.png](04-ver-detalle.png): un solo «Volver · Avisos» en la barra y ningún «Volver/Avisos» repetido en el contenido. Gateway: `GET /alerts/543dbbb8… 200`. Comparar con la [captura anterior](../android-c-ver-detalle-20261117/04-ver-detalle.png) | **PASS** |
| Severidad traducida | La lista ([03-avisos.png](03-avisos.png)) y el detalle muestran «Severidad del aviso: Informativo», ya no `INFO` | **PASS** |
| `ELIGIBLE` traducido | [07-expediente.png](07-expediente.png): «Estado: Elegible para donar» en el expediente propio de `donor1`, solo lectura | **PASS** |
| Volver desde el detalle | [05-tras-volver.png](05-tras-volver.png): vuelve a la bandeja | **PASS** |
| Pruebas JVM | `./gradlew :composeApp:testDebugUnitTest`: **80 casos, 0 fallos, 2 omitidos**. Las omitidas son `RealServicesTest`, que se salta explícitamente cuando no hay `lab.json` | **PASS** |
| Revocación desde el servidor con la app abierta, intento 1 (APK `2b86126b…`) | Con Avisos abierto, la sesión `22dd55c4…` se revocó en el servidor: se borró `session:<sid>` de Redis, igual que el modo `revoke` de `apps/services/tests/portal_security_probe.py`, y se marcó `revoked_at`. Al tocar «Actualizar»: `GET /alerts` 401 → `POST /auth/refresh` 401 → la app pide iniciar sesión. [10-tras-revocacion.png](10-tras-revocacion.png) muestra **«Cuenta o contraseña incorrectas.»** | **FAIL**: exige login, pero el mensaje es engañoso porque el usuario no escribió credenciales. Se conserva |
| Revocación, intento 2 (APK `55427a64…`, corregido) | Mismo procedimiento sobre la sesión `8c883d79…`: 401 → refresh 401 → [13-tras-revocacion-2.png](13-tras-revocacion-2.png) muestra «Sesión vencida o revocada. Inicia sesión.» y pide la contraseña de nuevo | **PASS** |
| Cambio de cuenta | `donor1` ve «Recordatorio de tu cita» ([14](14-avisos-donor1.png)) y cierra sesión ([16](16-cierre-donor1.png): `devices/…/revoke` 200 y `auth/revoke` 200). `donor2` entra: Avisos «Sin registros disponibles.» ([18](18-avisos-donor2.png)), cuenta `donor2` ([19](19-cuenta-donor2.png)) y expediente propio `24136e41…` «Donante sintetico Android 1611», con estado «Registro preliminar» ([20](20-expediente-donor2.png)). No aparece ningún dato de `donor1` (`72530dc9…`). El oráculo SQL confirma 0 avisos dirigidos a `donor2` | **PASS** |
| Enlace al aviso ajeno | Con la sesión de `donor2`, arranque en frío con `--es alert_id 543dbbb8…`: `GET /alerts/543dbbb8… 404`. [21](21-enlace-ajeno-donor2.png) muestra «Aviso no disponible para esta sesión.» y el inicio de `donor2` | **PASS** |
| Expiración natural | `ACCESS_TTL` 900 s (ya se acreditó la renovación en el [cierre Android C](../android-c-cierre-20261117/RESULTADOS.md)). `REFRESH_TTL` es de 86 400 s: la familia caduca 24 h después del login | **Pendiente**. Exige 24 h de espera con la app abierta, y no se cambiaron relojes ni caducidades |
| TalkBack (CONT-04) | El AVD `google_apis` arm64 no trae TalkBack (`pm list packages`: no está `com.google.android.marvin.talkback`) y no hay APK local. Instalarlo exige descargar un tercero o una imagen Play, lo que requiere autorización | **Pendiente (bloqueo)**. Abajo hay una inspección sustituta del árbol de accesibilidad, que **no** acredita TalkBack |
| Sin escrituras sobre el aviso | Oráculo final: `543dbbb8…` `OPEN` con `acknowledged_by` nulo. 110 avisos y 4 recordatorios, igual que antes | **PASS** |
| Sesiones y dispositivos propios | 5 sesiones en la ventana (4 de `donor1` y 1 de `donor2`): todas revocadas en SQL y ausentes en Redis. 0 activas por cuenta y 0 claves `session:*`. 3 dispositivos registrados en la ventana, todos inactivos | **PASS** |
| Auditoría | Quedaron 76 eventos en el outbox. Se entregaron solo con `redhouse.events.dispatch` (mismo `drain_outbox.py` que la ventana anterior): identidad 29, donantes 40, alertas 7 y auditoría 76; 0 fallos; outbox final en 0. No se ejecutaron recordatorios ni otros pasos del worker | **PASS** |
| Apagado | `emu kill`; gateway SIGTERM con `stopped.json`; `local.py stop`. Sin listeners en 18443 ni en los motores. Los datos quedan en disco | **PASS** |

## Accesibilidad: inspección sustituta, no TalkBack

Recorrido como donante: inicio de sesión → Inicio → Avisos → Ver detalle → Volver → Cuenta → Cerrar sesión. En cada pantalla se volcó con `uiautomator dump` el árbol `AccessibilityNodeInfo` que expone Compose, y se tomó el orden de recorrido según el orden del árbol. TalkBack consume ese árbol, pero esta inspección no reproduce su agrupación, su lectura ni sus gestos. Los volcados son privados.

| Pantalla | Etiquetas habladas | Orden de foco (árbol) | Botones sin nombre | Observaciones |
| --- | --- | --- | --- | --- |
| Inicio de sesión ([08](08-tras-cerrar-sesion.png)) | Campos con etiqueta visible «Cuenta» y «Contraseña» (la contraseña marcada `password`). Botones «Iniciar sesión» y «Recuperar acceso» con texto | Marca → título → mensaje → Cuenta → Contraseña → Iniciar sesión → Recuperar acceso | Ninguno | El logotipo (Canvas) no tiene descripción; es decorativo y va junto a «Red House». H-03 |
| Inicio donante ([02](02-inicio.png)) | Botones «Explorar campañas», «Ver mis citas» y «Compartir campaña» con texto. Navegación «Inicio/Campañas/Avisos/Cuenta» con texto | Contenido de arriba abajo y después la barra inferior | Ninguno | «Compartir campaña» se repite en cada tarjeta sin nombrar la campaña. H-01 |
| Avisos ([03](03-avisos.png)) | Título, «Actualizar». Cada tarjeta: título, fecha, estado, «Severidad del aviso: Informativo», «Más información», «Ver detalle», «Marcar leído» | Tarjeta por tarjeta y después la barra | Ninguno | Los botones de la tarjeta no incluyen el aviso al que pertenecen. H-01 |
| Ver detalle ([04](04-ver-detalle.png)) | «Volver», «Avisos», Estado, Fecha, Severidad, Aviso, «Marcar leído» | Volver → título → campos → acción → barra | Ninguno | Corregido: antes se oían dos «Volver» y dos «Avisos» |
| Cuenta ([06](06-cuenta.png)) | Nombre, perfil «Donante», filas «Mi expediente», «Notificaciones», «Privacidad y permisos», «Información de la cuenta» y «Cerrar sesión» | De arriba abajo | Ninguno | El chevron «›» se excluye de la semántica a propósito |
| Tras cerrar sesión ([08](08-tras-cerrar-sesion.png)) | Mensaje «Sesión cerrada en este teléfono y en el servicio.» | Encabeza el formulario | Ninguno | El mensaje de estado del contenedor no es región viva. H-02 |

Hallazgos que quedan registrados sin corregir, porque no hay prueba ejecutable sin TalkBack o sin instrumentación de UI:

- **H-01 (bajo):** los botones repetidos en tarjetas («Ver detalle», «Marcar leído», «Compartir campaña») no nombran su elemento. En una lectura lineal el contexto queda justo antes, pero en el menú de controles de TalkBack serían ambiguos.
- **H-02 (medio):** el texto `status` de `App.kt` (por ejemplo «Sesión vencida o revocada…» o «Sesión cerrada…») no tiene `liveRegion`, así que TalkBack no lo anunciaría solo. `AppointmentRecovery` y el alta preliminar sí lo usan.
- **H-03 (informativo):** los títulos de pantalla no se marcan como encabezado (`heading()`), por lo que no se puede navegar por encabezados.

No se encontraron botones sin nombre en el recorrido.

## Cambios en `apps/mobile`

- `OperationalScreens.kt` / `App.kt`: `OperationalDetail` y `CoordinatorPlanning` ya no dibujan su propio «Volver» ni repiten el título de la barra. Si el título del detalle difiere del de la barra, se muestra como subtítulo (`detailSubtitle`), por ejemplo en Laboratorio → «Muestras autorizadas». La línea de estado vacía ya no ocupa espacio.
- `Presentation.kt`: `displayValue` traduce `severity` (INFO/WARNING/CRITICAL → Informativo/Advertencia/Crítico), `urgency` (LOW/MEDIUM/HIGH/CRITICAL → Baja/Media/Alta/Crítica) y los estados `ELIGIBLE`, `ACKNOWLEDGED` y `DISMISSED`. Un código desconocido y el texto libre se muestran sin cambios.
- `Api.kt` / `App.kt`: `failureMessage`. Un 401 `unauthorized` con la sesión abierta muestra «Sesión vencida o revocada. Inicia sesión.»; «Cuenta o contraseña incorrectas.» queda solo para el intento de login.
- Pruebas: `PresentationTest` suma 3 casos (traducciones, subtítulo sin repetición y mensaje 401). `DonorPaginationTest.requestedPageAndExistingFilterArePreserved` usa horarios completos según el contrato `campaign-slots` de `fd4fbcf`. `TransportNextStepTest.locationSummaryDoesNotImplyARecentFix` espera el texto vigente de `84b3394` («Ubicación no disponible en esta vista…») y que no aparezca «Última ubicación».

## Límites

- TalkBack, VoiceOver y la expiración natural de 24 h siguen pendientes. La inspección de árbol no sustituye a TalkBack.
- La revocación se inyectó directamente en Redis/SQL sobre la sesión propia de la app. No existe un endpoint administrativo que revoque una sola sesión, y desactivar la cuenta o cambiar su rol habría modificado datos de negocio de `donor1`.
- El lanzador sigue siendo la reconstrucción mínima sin workers, sin WSS de transporte ni guardas del original. La instrumentación Compose (`*JourneyTest`) no se ejecutó contra el APK nuevo.

Recibos privados fuera de Git, en `.local/rhlab/run-20261118-01/`: el cotejo, las dos revocaciones, el oráculo de cierre antes y después de entregar el outbox, el log del gateway (solo método, ruta y estado) y los volcados de accesibilidad. Sus huellas están en [resumen.json](resumen.json).
