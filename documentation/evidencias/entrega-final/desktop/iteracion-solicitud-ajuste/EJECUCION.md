# Ajuste de solicitud y restricción de descarga GCS

13/11/2026, macOS 15.7.9 x86_64, Python 3.12.6. No se accedió a un servidor ni a GCS en estas pruebas. El selector Qt utilizó datos sintéticos y un doble de servicio.

Desde `apps/desktop`:

```sh
QT_QPA_PLATFORM=offscreen DESKTOP_CAPTURE_DIR=../../documentation/evidencias/entrega-final/desktop/iteracion-solicitud-ajuste .venv/bin/python -m pytest tests/test_ui.py -q -k 'request_picker or request_creation' --tb=short --show-capture=no
```

La salida observada fue `2 passed, 9 deselected in 7.72s`, código 0. Comprueba rol médico y cambio de cantidad de sangre a órgano y viceversa. Se inspeccionó [la captura sintética](solicitud-organo.png); el máximo se verifica en la prueba, no es visible como número máximo en la captura.

```sh
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_client.py tests/test_journal.py tests/test_download.py tests/test_tracking.py tests/test_ui.py tests/test_label_output.py -q
```

La salida observada fue `53 passed in 14.18s`, código 0. Incluye rechazos de bucket ajeno y rutas ambiguas, además del bucket configurado con query firmada sintética. La descarga GCS real, la selección de órgano con servidor y Windows no se probaron. No se guardó JUnit ni log: estas salidas están transcritas de las llamadas de herramienta. `SHA256SUMS` identifica código, pruebas y captura de este corte.
