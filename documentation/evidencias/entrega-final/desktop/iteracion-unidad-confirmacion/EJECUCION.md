# Confirmación documental de caducidad

13/11/2026, macOS 15.7.9 x86_64, Python 3.12.6. Esta comprobación Qt usa un doble local; no accede a servicios ni registra una unidad real. Las fechas visibles son sintéticas (+1 y −1 días respecto a la prueba) y no representan vida útil ni recomendación clínica.

Desde `apps/desktop`:

```sh
QT_QPA_PLATFORM=offscreen DESKTOP_CAPTURE_DIR=../../documentation/evidencias/entrega-final/desktop/iteracion-unidad-confirmacion .venv/bin/python -m pytest tests/test_ui.py -q -k resource_form_captures --tb=short --show-capture=no
```

Resultado observado: **1 passed, 11 deselected in 7.43s**, código 0. La prueba comprueba que el primer intento sin confirmación no registra nada y que después de confirmar se envían los campos seleccionados. Se inspeccionó [la captura](unidad-organo-sintetica.png) y no mostró recortes. `SHA256SUMS` identifica las fuentes y captura de este corte; no se guardó JUnit de esta repetición. El ensayo autenticado contra servidor fue anterior a la casilla y está documentado por separado en `iteracion-inventario-reportes`.
