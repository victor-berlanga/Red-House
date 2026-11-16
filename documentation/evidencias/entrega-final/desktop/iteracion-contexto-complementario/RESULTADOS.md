# Contexto de sesión: recuperación, etiquetas y traslados

Se extiende el contexto de cuenta, institución, rol y SID a la reanudación y consulta de operaciones, emisión y recuperación de etiquetas, salida PDF/impresión y apertura de traslados. Los callbacks de otra sesión se descartan; un cliente invalidado limpia su sesión. La operación iniciada conserva su resultado en el diario original. Una impresión iniciada registra su resultado en ese mismo diario y no se reenvía automáticamente.

Prueba ligera Qt con dobles: **10/10**. Comando:

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=apps/desktop apps/desktop/.venv/bin/python -m pytest -q apps/desktop/tests/test_session_extra.py apps/desktop/tests/test_reservation_ui.py --junitxml=documentation/evidencias/entrega-final/desktop/iteracion-contexto-complementario/unidad-01/junit.xml
```

Salida y JUnit: `unidad-01/`. `fuentes.sha256` fija las fuentes ensayadas. Las pruebas incluyen cambio durante diálogos, antes del envío y tras respuesta, sesión invalidada, e impresión iniciada. No se inició laboratorio ni se probó impresora física; no existe garantía de cancelar una petición ya enviada. El parche independiente de otros formularios sigue pendiente.
