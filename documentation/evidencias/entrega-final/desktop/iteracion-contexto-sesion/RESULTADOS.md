# Contexto de sesión en comandos durables

El cliente y el diario originales quedan vinculados a la identidad, institución, rol y SID de la operación. Se verifica el contexto antes de preparar, reautenticar, enviar o reintentar; una respuesta tardía no se presenta a otra sesión. Un resultado definitivo se conserva en el diario original. Un envío sin resultado confirmado mantiene su clave y estado incierto. La renovación legítima conserva el SID; una sesión invalidada en el mismo cliente limpia la vista.

La protección no cancela una petición ya enviada ni asegura atomicidad remota. `resume_operation`, etiquetas y las guardas de otros diálogos permanecen fuera de este incremento. No se ejecutaron motores, laboratorio real, empaquetado ni Windows.

## Comprobaciones ligeras

- `unidad-01`: 28/28, incluyendo carreras del contexto, renovación y cliente. Comando: `QT_QPA_PLATFORM=offscreen PYTHONPATH=apps/desktop apps/desktop/.venv/bin/python -m pytest -q apps/desktop/tests/test_session_context.py apps/desktop/tests/test_session_refresh_context.py apps/desktop/tests/test_client.py --junitxml=.../unidad-01/junit.xml`.
- `unidad-02`: regresión de reserva y evaluación, 1/5; cuatro dobles antiguos carecían de la sesión o diario requeridos. `unidad-03`: 0/4, tras añadirlos faltaban atributos del doble al cerrar y la firma actual de `run`. Ambas salidas y JUnit se conservan.
- `unidad-04`: 4/4 casos afectados, con dobles actualizados. Comando: `QT_QPA_PLATFORM=offscreen PYTHONPATH=apps/desktop apps/desktop/.venv/bin/python -m pytest -q apps/desktop/tests/test_reservation_ui.py::test_reservation_button_prepares_and_sends_same_candidate apps/desktop/tests/test_evaluation_ui.py::test_candidate_actions_follow_server_validity apps/desktop/tests/test_evaluation_ui.py::test_reservation_requires_prior_favorable_review apps/desktop/tests/test_evaluation_ui.py::test_recorded_unfavorable_review_cannot_be_changed_or_reserved --junitxml=.../unidad-04/junit.xml`.

Cada directorio contiene salida y JUnit; `fuentes.sha256` identifica las fuentes finales. `git diff --check` y compilación Python dirigida pasaron. Estas pruebas usan dobles Qt y no sustituyen aceptación con servicios reales.

Los JUnit públicos tienen espacios finales normalizados; los logs conservan la salida de pytest. El XML original de `unidad-03` queda en `.local/artifacts/desktop/session-context-integracion-20261116/`; el original de `unidad-02` no se conservó separado antes de normalizar espacios.
