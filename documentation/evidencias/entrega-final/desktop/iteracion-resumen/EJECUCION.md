# Ejecución de resumen y recuperación

13/11/2026. macOS 15.7.9 x86_64, Python 3.12.6, PySide6 6.10.1. El laboratorio creó servicios, PostgreSQL, Redis y MongoDB efímeros; la clave temporal se guardó y eliminó del llavero macOS real. No se emplearon credenciales ni datos productivos.

Desde la raíz del repositorio:

```sh
REDHOUSE_NATIVE_LAB=1 PYTHONPATH=apps/services:apps/desktop:apps/desktop/.venv/lib/python3.12/site-packages QT_QPA_PLATFORM=offscreen DESKTOP_CAPTURE_DIR=documentation/evidencias/entrega-final/desktop/iteracion-resumen apps/services/.venv/bin/python -m pytest apps/desktop/tests/test_real_lab.py -q -k 'summary_projections or authenticated_qt_inventory or native_keychain_recovers' --tb=short --show-capture=no
```

La salida observada en la herramienta fue `3 passed, 8 deselected in 86.58s`; código de salida 0. Incluyó consulta XML por rol, ventana Qt autenticada y recuperación de etiqueta tras salida abrupta con un único evento. La entrada del llavero se eliminó.

Desde `apps/desktop`:

```sh
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_ui.py -q -k summary_keeps
```

La salida observada fue `1 passed, 8 deselected in 2.97s`; código de salida 0. Este caso utilizó un doble de servicio para probar fallo parcial.

No se guardaron archivos de log ni JUnit durante estas ejecuciones. Estas líneas transcriben únicamente el resultado y el comando de las llamadas de herramienta; no son un JUnit ni una reproducción posterior. Las capturas sintéticas y los hashes de código/pruebas están en este directorio; no contienen JWT, contraseñas ni capacidades de descarga. La prueba no acredita Windows, impresión física ni recuperación tras reinicio frente a producción.
