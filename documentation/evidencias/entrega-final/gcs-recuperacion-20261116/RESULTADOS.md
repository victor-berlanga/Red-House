# Caída y recuperación GCS desde Chrome — 16/11/2026

I06-05, rama GCS: **1/1 aprobado**, 92,39 s de pytest/95,273 s de lanzador. Una acreditación PNG sintética propia se preparó/cargó antes del corte. Un proxy CONNECT aislado cortó únicamente la salida del SDK de Documentos hacia `storage.googleapis.com:443`, conservando validación TLS; sin MITM, cambio de IAM ni lectura de objetos históricos.

Chrome recibió 503 al verificar y 409 al intentar descargar. SQL mantuvo ERROR/storage_unavailable, sin análisis aceptado. Tras restablecer la conexión, el mismo UUID y generación quedaron VERIFIED/CLEAN mediante ClamD real. La descarga fue un archivo con SHA-256 exacto. Hubo una preparación y dos verificaciones; no se duplicó el documento. Dirección inspeccionó las pantallas reales de error y recuperación.

Bucket autorizado: `red-house-evidencias-sistemas-integracion-01`. La limpieza comprobó generación y eliminó únicamente el objeto del ensayo con precondición; consulta posterior confirmó ausencia. No se afirma vencimiento de la eliminación diferida física de GCS. Cuarenta y un procesos propios cerrados sin cierre forzado, 1.322 fuentes estables. Los recibos y huellas están en `intento-02/`.

Comando: `PYTHONPATH=.:apps/services REDHOUSE_BROWSER_TESTS=1 REDHOUSE_TEST_GCS_FAILURES=1 ... apps/services/.venv/bin/python -m pytest apps/services/tests/test_portal_gcs_failure_browser.py::test_gcs_outage_and_same_generation_recovery_in_browser -q`. El lanzador privado `.local/run_portal_gcs_recovery_20261116_02.py` fija el bucket autorizado, rutas nuevas, firmas 28185, motores y limpieza.

## Corrección y primer intento

El primer intento falló tras recuperar el documento: Chrome abrió la imagen dentro del navegador y el arnés esperaba una descarga. Su resultado y limpieza confirmada se conservan en `intento-01/`; no se presenta como aprobado.

La firma GET ahora incluye explícitamente la **generación analizada** y `response-content-disposition=attachment`. Construir un Blob con generación no bastaba para incluirla en la URL firmada por el SDK. Sin generación, la firma GET rechaza de forma segura. PUT conserva la condición de creación `x-goog-if-generation-match: 0`. Tres pruebas dirigidas usando el firmante del SDK, sin red, comprobaron esos límites; forman parte del JUnit dirigido del [expediente de reportes](../portal-reportes-20261116/render-unit-final.xml). Nueve pruebas previas del proxy se conservan como comprobación separada, sin nueva ejecución.

Alcance: monolito autónomo sin listeners API, TESTING/cuotas y certificado efímero web de laboratorio; GCS y ClamD reales. El corte sucede después de la carga. No acredita fallos durante PUT, retención nativa del bucket, despliegue de estas fuentes ni toda la etapa 06. El proveedor predeterminado del producto sigue siendo LOCAL.
