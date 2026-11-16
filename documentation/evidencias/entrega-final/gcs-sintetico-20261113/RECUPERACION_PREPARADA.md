# I06-05: corte de salida GCS y recuperación — preparación del 16/11

**Estado: preparado, sin ejecución real.** No acredita todavía recuperación GCS.
La evidencia previa de este directorio conserva sus dos casos JSON/XML; no se repiten.

El nuevo caso `apps/services/tests/test_portal_gcs_failure_browser.py` reutiliza el
fixture monolítico, ClamD propio y el navegador de documentos. Crea una acreditación
y un PNG sintéticos. Prepara un solo UUID y carga un solo objeto con
`x-goog-if-generation-match: 0`, conservando la generación confirmada por GCS en
un diario privado sincronizado a disco. No utiliza registros históricos.

Un proxy CONNECT en `127.0.0.1` permite exclusivamente
`storage.googleapis.com:443`. Solo la `AuthorizedSession` del SDK de Documentos
usa ese proxy; no se modifica `HTTPS_PROXY`, ADC, IAM, ACL, bucket ni configuración
persistente. Primero confirma acceso al objeto por ese túnel. Después deniega
conexiones y cierra los túneles propios existentes. El contenido TLS no se
descifra, sustituye ni registra. El cliente conserva validación CA.

Chrome abre el documento preparado, intenta verificarlo y exige HTTP 503. La
descarga debe permanecer bloqueada con 409. El oráculo SQL READ ONLY exige
`ERROR`, un `FILE_ERROR/storage_unavailable`, ninguna generación verificada y
cero análisis. Tras reabrir el proxy, Chrome verifica **el mismo UUID**, descarga
los bytes exactos y el oráculo exige la **misma generación GCS**, `VERIFIED`, un
análisis real `CLEAN`, un único `DOCUMENT_PREPARED` y un único `FILE_VERIFIED`.
Los eventos deben corresponder al actor y servicio esperados.

La preparación y PUT preceden al corte y usan el contrato real, fuera del
navegador. La web usa un cliente HTTP diferente, con `trust_env=False`; este caso
no afirma probar una caída durante su PUT ni una indisponibilidad global de GCS.
Prueba la presentación del fallo y recuperación de la verificación en Chrome,
el acceso real GCS del backend y la descarga final real del navegador. Chrome
mantiene validación CA de GCS; solamente el certificado efímero del portal local
se admite mediante su SPKI exacto. No se usa `ignoreHTTPSErrors` en este escenario.

La limpieza restaura primero la sesión del SDK. Comprueba SHA-256 y elimina
exclusivamente el objeto propio con `if_generation_match` de la generación
confirmada; confirma después ausencia del objeto activo. No afirma eliminar
versiones retenidas por soft-delete. Una carga incierta, una generación no
confirmada o una limpieza fallida conserva el diario privado para reconciliar.
Se cierran Chrome, servidor HTTPS, proxy, cliente GCS y ClamD propios incluso
ante fallos. La infraestructura del fixture conserva su cierre habitual.

## Preparación comprobada

- Nueve pruebas puras de autoridad CONNECT, cierre, carrera deny/allow y destino
  firmado: aprobadas, 1,09 s. Sin sockets ni ADC.
- Ruff, `node --check` y colección del caso real: aprobados.
- Base ClamAV local comprobada por lectura de cabecera: daily 28185,
  16/11/2026 06:24 UTC. El ensayo vuelve a exigir frescura de 172800 s mediante
  el escaneo real; no renueva firmas ni suaviza esa política.
- No se arrancaron motores, Chrome, proxy ni conexiones GCS durante preparación.

## Ejecución posterior, únicamente con ventana asignada

Adaptar el wrapper existente de huellas antes/después, log privado, JUnit y cierre
al siguiente selector. Usar una raíz temporal corta y una salida nueva. Conservar
la ADC impersonada ya disponible; el caso rechaza otra clase de credencial.

```sh
REDHOUSE_BROWSER_TESTS=1 \
REDHOUSE_TEST_GCS_FAILURES=1 \
REDHOUSE_TEST_GCS_BUCKET=red-house-evidencias-sistemas-integracion-01 \
REDHOUSE_TEST_CLAMD_DATABASE="$PWD/.local/clamav-vigencia-20261113/database" \
REDHOUSE_TEST_ROOT="/private/tmp/rh-gcs-<sufijo-nuevo>" \
REDHOUSE_BROWSER_RESULTS="$PWD/.local/artifacts/gcs-recovery-<sufijo-nuevo>" \
apps/services/.venv/bin/pytest -q \
  apps/services/tests/test_portal_gcs_failure_browser.py::test_gcs_outage_and_same_generation_recovery_in_browser \
  --junitxml=".local/artifacts/gcs-recovery-<sufijo-nuevo>/junit.xml"
```

Los marcadores `<sufijo-nuevo>` deben sustituirse antes de ejecutar. Invocar con
la escalación autorizada desde el inicio para sockets y procesos propios. No
ejecutar en paralelo con builds o fixtures pesados. El límite del recorrido
Chrome es 180 s; no cambia ningún timeout de producto. Conservar los recibos
`browser.json`, `persistencia.json`, `limpieza.json`, dos capturas y cualquier
diario privado pendiente. La aprobación del caso requiere también limpieza
confirmada y fuentes estables.
