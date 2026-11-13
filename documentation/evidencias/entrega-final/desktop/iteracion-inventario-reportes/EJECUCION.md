# Inventario y descarga local de reporte

13/11/2026, macOS 15.7.9 x86_64, Python 3.12.6. Se usaron PostgreSQL/Redis/MongoDB efímeros, gateway TLS de laboratorio y ClamAV 1.5.4 real con firmas locales, sin GCP ni datos productivos. El certificado del gateway se confió explícitamente durante la prueba; no se deshabilitó TLS. La entrada de diario usó proveedor de clave simulado. ClamD lo operó otro agente, quien lo detuvo al terminar.

Desde la raíz del repositorio, con ClamD de laboratorio en `127.0.0.1:13310`:

```sh
REDHOUSE_TEST_CLAMD_PORT=13310 PYTHONPATH=apps/services:apps/desktop:apps/desktop/.venv/lib/python3.12/site-packages QT_QPA_PLATFORM=offscreen DESKTOP_CAPTURE_DIR=documentation/evidencias/entrega-final/desktop/iteracion-inventario-reportes apps/services/.venv/bin/python -m pytest apps/desktop/tests/test_real_lab.py -q -k 'operator_creates_organ or blood_components or real_local_report_download' --tb=short --show-capture=no --junitxml=/private/tmp/redhouse-inventory-report-junit.xml
```

Resultado: **2 passed, 1 failed, 12 deselected in 75.87s**; [JUnit](junit-primera.xml). Pasaron alta Qt de órgano y alta XML de plasma/plaquetas en cuarentena. Se inspeccionó [la captura Qt autenticada](laboratorio-unidad-organo.png). El reporte quedó `RETRYABLE`; la captura no demuestra reglas clínicas ni disponibilidad física del recurso. `SHA256SUMS-primera` contiene los hashes registrados antes de la ejecución y comprobados al finalizar.

Se repitió únicamente el reporte con el mismo comando y `-k real_local_report_download`, agregando al aserto el código de error: **1 failed, 14 deselected in 57.83s**, `storage_unavailable`, [JUnit de diagnóstico](junit-diagnostico.xml). `SHA256SUMS-diagnostico` se comprobó sin cambios al terminar. El fixture había creado la carpeta de objetos con permisos por defecto incompatibles con el requisito propietario de directorio privado 0700.

Se corrigió solo el fixture para crear esa carpeta con modo 0700. La misma selección dirigida, con JUnit en `/private/tmp/redhouse-report-fixed-junit.xml`, devolvió **1 passed, 14 deselected in 49.76s**: [JUnit corregido](junit-corregido.xml). Se generó CSV, se analizó con ClamAV real, se verificó metadata y SHA-256, se descargó por HTTPS mediante capacidad local y se rechazó la misma capacidad tras logout. Los nueve hashes de `SHA256SUMS-corregido` coincidieron antes y después. Entre pruebas se integraron otros cambios de backend; los tres archivos de hashes identifican cada corte.

El gateway TLS de escritorio en esta prueba es un proxy Flask efímero, no el Nginx de producción; ClamAV y el almacenamiento son reales locales. No se probaron GCS, impresión física, equipos clínicos, Windows ni paquete final de esta iteración. No se guardaron contenidos de reportes, JWT ni capacidades; los artefactos JUnit se inspeccionaron antes de copiarlos. En los dos JUnit fallidos se quitaron espacios finales del texto del traceback para mantener limpio el diff; los resultados y mensajes se conservaron.
