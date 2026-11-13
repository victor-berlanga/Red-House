# Solicitud institucional: evidencia del incremento

13/11/2026. macOS 15.7.9 x86_64 y Python 3.12.6. Se usaron servicios efímeros, TLS con CA de laboratorio, datos sintéticos y un proveedor de clave de diario simulado. No se usó GCP para este registro.

Desde la raíz del repositorio:

```sh
PYTHONPATH=apps/services:apps/desktop:apps/desktop/.venv/lib/python3.12/site-packages QT_QPA_PLATFORM=offscreen DESKTOP_CAPTURE_DIR=documentation/evidencias/entrega-final/desktop/iteracion-solicitud apps/services/.venv/bin/python -m pytest apps/desktop/tests/test_real_lab.py -q -k medical_creates_request_through_qt --tb=short --show-capture=no --junitxml=/private/tmp/redhouse-request-junit.xml
```

Resultado observado: **1 passed, 11 deselected in 68.96s**. El [JUnit](junit-primera.xml) conserva esa ejecución. Incluyó inicio de sesión médico, búsqueda por folio, selección de receptor y creación de solicitud persistida; [captura del formulario](laboratorio-solicitud.png). Los hashes de esa primera iteración están en `SHA256SUMS-primera`.

Después se corrigió únicamente el aviso que seguía pidiendo seleccionar un receptor ya seleccionado. Desde `apps/desktop`, con doble de servicio:

```sh
QT_QPA_PLATFORM=offscreen DESKTOP_CAPTURE_DIR=../../documentation/evidencias/entrega-final/desktop/iteracion-solicitud .venv/bin/python -m pytest tests/test_ui.py -q -k 'request_picker or request_creation' --tb=short --show-capture=no
```

Resultado observado: **2 passed, 9 deselected in 8.13s**. La [captura corregida](solicitud-aviso-corregido.png) es sintética y no demuestra conexión al servidor. `SHA256SUMS-actual` identifica la versión posterior del código y pruebas. No se guardó JUnit de esta segunda ejecución. Las diferencias entre los hashes de `app.py` reflejan la línea de aviso corregida; el resto de la operación probada no cambió.

Pruebas separadas del diario: `cd apps/desktop && .venv/bin/python -m pytest tests/test_journal.py -q` devolvió **14 passed in 3.58s**. Cubren, entre otros casos, misma clave/cuerpo tras pérdida de respuesta y rechazo de una respuesta que no coincide con la intención. No sustituyen la prueba de interrupción de esta operación contra servidor real, revisión clínica, instalación Windows ni captura de otros perfiles.
