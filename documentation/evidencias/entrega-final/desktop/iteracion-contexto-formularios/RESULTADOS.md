# Contexto de sesión en formularios

Los formularios operativos y sus consultas conservan el contexto de cuenta, institución, rol y SID durante la selección, la confirmación y la ejecución. Las respuestas y los errores tardíos de una sesión anterior no se aplican a la nueva. Se comprueba el contexto antes de iniciar el trabajo; el resultado de una petición ya iniciada permanece sujeto al diario original y no existe garantía de cancelación remota.

El candidato aprobado `0e25202b65934102ef75ca1b7afe9c1fce29d85bcc932e90e4e9038ed8e67342` se integró byte a byte. Los siete módulos y el test coinciden también con el entorno privado donde se ejecutaron los dobles. `fuentes.sha256` fija las fuentes finales.

- `unit-01`: 4/5. El nuevo caso de renovación falló por falta de `version` en el doble; se conservan salida y JUnit.
- `unit-02`: 5/5; cambios de sesión en formularios y renovación con el mismo SID.
- `unit-03`: 1/1; cambio de sesión antes de confirmar recepción impide el escaneo.
- `unit-04` y `unit-05`: 4/4 negativos y 4/4 positivos sintéticos de correlación de respuesta y diario.
- `unit-06`: 3/3; error de conexión tardío tras cambio de cuenta o SID y respuesta de evaluación tardía.
- `unit-07`: 9/9; regresión del complemento de sesión ya integrado.

Se usó `QT_QPA_PLATFORM=offscreen PYTHONPATH=<runtime-privado> apps/desktop/.venv/bin/python -m pytest -q <casos-dirigidos> --junitxml=<salida>`. Los logs incluyen los casos exactos y los JUnit registran sus nombres. Los XML públicos solo normalizan espacios finales; originales privados en `.local/artifacts/desktop/session-modal-rebased-20261116/`. No se repitieron pruebas tras verificar identidad byte a byte. Son dobles locales: no acreditan laboratorio, impresión física ni Windows.
