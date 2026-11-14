# Inventario y administración institucional: evidencia compuesta

El primer ensayo conjunto Qt/XML terminó **0/3 en 128,86 s**. Los tres casos habían llegado a sus comprobaciones SQL de negocio y a las ocho capturas antes de fallar al buscar auditoría en el esquema equivocado. La comprobación del 403 de operador estaba después del fallo y no se ejecutó. El [JUnit y la nota del intento](vertical-01/NOTA.md) conservan ese resultado; no se ha repetido el ensayo persistente con las pruebas corregidas.

Un oráculo independiente consultó después, en transacciones PostgreSQL de solo lectura, los tres fixtures originales. Correlacionó corrección, ubicación y versiones; donación procesada, linaje, origen retirado y dos derivados en cuarentena; sedes, capacidades y versiones. Comprobó eventos fuente con actor y recurso exactos. Sus límites, primer fallo de `search_path` y huellas constan en [oráculo SQL](oraculo-readonly-01/RESULTADOS.md). Esta comprobación complementa el ensayo Qt; no convierte el JUnit 0/3 en aprobado ni acredita el 403 pendiente.

Las capturas `vertical-01` se inspeccionaron, también por Dirección: selector de donación y alta vinculada, corrección de unidad, derivados y altas/correcciones de sede y capacidad. El nombre completo y la referencia separada se observan en el selector. La captura real de derivados mostró solo el primer elemento; una comprobación posterior con doble detectó compresión y llevó a corregir el área desplazable. El caso Qt final pasó **1/1**; Dirección inspeccionó ambas imágenes y aceptó la legibilidad del alcance mostrado. Muestra por separado [primer derivado](guardas-layout-doble-04/derivados-primero.png) y [segundo derivado](guardas-layout-doble-04/derivados-segundo.png). Los intentos `guardas-layout-doble-01`, `-02` y `-03` conservan los fallos y capturas; el último se debió a pedir desplazamiento hacia un campo ya visible. La corrección visual aún no tiene ensayo persistente nuevo ni prueba de ocho derivados o escala ampliada.

La guarda contra sustitución de sesión al cerrar el formulario de derivados pasó por separado con doble en `guardas-layout-doble-01`; no acredita revocación o cambio de usuario reales. Los dobles iniciales de los formularios pasaron 6/6 y los del selector de procedencia 2/2; sus carpetas documentan cambios posteriores de texto y presentación. Las pruebas de diario con dobles verifican correlación de respuestas y misma clave tras respuesta perdida; no son caída real de red ni reinicio real de proceso.

El comando del intento Qt original, ejecutado con dependencias locales y sockets de laboratorio autorizados, fue el siguiente. Para una reproducción se debe usar otro directorio de salida; los tests actuales incluyen correcciones posteriores y sus huellas difieren de las registradas en `vertical-01`.

```sh
export DESKTOP_CAPTURE_DIR="$PWD/documentation/evidencias/entrega-final/desktop/iteracion-inventario-institucional/vertical-nuevo"
export REDHOUSE_TEST_ROOT="$(mktemp -d /private/tmp/rh-desktop-three.XXXXXX)"
export REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_STARTUP_TIMEOUT=120 QT_QPA_PLATFORM=offscreen
export PYTHONPATH="$PWD/apps/desktop:$PWD/apps/services:$PWD/apps/desktop/.venv/lib/python3.12/site-packages"
mkdir -p "$DESKTOP_CAPTURE_DIR"
apps/services/.venv/bin/python -m pytest apps/desktop/tests/test_resource_edit_lab.py apps/desktop/tests/test_fractionation_lab.py apps/desktop/tests/test_institutional_catalogue_lab.py -q --tb=short --show-capture=no --basetemp="$REDHOUSE_TEST_ROOT/pytest" --junitxml="$DESKTOP_CAPTURE_DIR/junit.xml"
```

La comprobación de layout final usó `QT_QPA_PLATFORM=offscreen`, `PYTHONPATH="$PWD/apps/desktop"` y `apps/desktop/.venv/bin/python -m pytest apps/desktop/tests/test_fractionation_ui.py::test_two_derivatives_remain_reachable_in_scroll_area -q --tb=short`, con `DESKTOP_CAPTURE_DIR` apuntando a `guardas-layout-doble-04`. El caso separado de guarda fue `test_fractionation_ui.py::test_session_replaced_after_modal_never_prepares_command`. No hubo acceso a servicios en esas pruebas Qt.

Se usaron datos sintéticos, gateway TLS local, servicios `TESTING`, Qt offscreen y proveedor de clave doble. No se midió rendimiento, ni se acredita actuación clínica, lectura o impresión física. La negativa XML de operador queda preparada como prueba independiente pero pendiente de ejecución. Los cambios posteriores al paquete macOS anterior aún no están incluidos en un paquete reconstruido; Windows 11, instalación limpia, firma y notarización siguen sin verificarse.
