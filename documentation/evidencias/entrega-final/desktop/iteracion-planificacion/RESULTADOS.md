# Planificación de traslado: resultado y límites

El recorrido Qt/XML sintético `ensayo-02` pasó **1/1 en 47,50 s**: coordinación eligió reserva y cuenta de traslado de origen, confirmó horarios y motivo, creó un traslado `PLANNED` y lo consultó por XML. La prueba correlacionó reserva y responsable con la fila de Transporte en PostgreSQL. Las capturas `ensayo-02/planificacion-qt.png` y `ensayo-02/traslado-qt.png` se inspeccionaron; la primera conserva el texto anterior a la corrección descrita abajo. Las huellas de fuentes antes y después del ensayo coinciden.

Las pruebas de diario y Qt con dobles pasaron **3/3** en el intento `ensayo-01`. El caso real de esa ejecución no arrancó porque el sandbox denegó un socket local; su JUnit conserva el error. La repetición real usó acceso autorizado a sockets locales y un fixture distinto. Después se corrigió el aviso inferior del formulario, que seguía pidiendo seleccionar datos ya elegidos. Solo se repitió la prueba Qt con doble: **1/1 en 2,98 s**, con captura inspeccionada `doble-mensaje/planificacion-doble.png`. SHA-256 posterior de `shipment_planning.py`: `d9ad61e18aa0cd252fc8163e939ab75ab0a741874e94c79bb183b4ba04ecf87a`.

Los dobles verifican que una respuesta perdida conserve la clave, que el estado pendiente no se marque completado y que una consulta correlacionada pueda cerrar el diario. La prueba real no inyecta pérdida, no fuerza `inventory_pending`, no acredita MFA ni reinicio del proceso. Se usaron datos sintéticos, servicios en `TESTING`, gateway local TLS, Qt offscreen y proveedor de clave doble. La prueba no demuestra entrega o recepción física; estas se describen por separado en la matriz. El fixture terminó y no quedaron procesos asociados a su directorio.

Comando del ensayo real, desde la raíz y con dependencias locales instaladas; para reproducirlo se debe usar otro directorio de evidencia:

```sh
export DESKTOP_CAPTURE_DIR="$PWD/documentation/evidencias/entrega-final/desktop/iteracion-planificacion/ensayo-nuevo"
export REDHOUSE_TEST_ROOT="$(mktemp -d /private/tmp/rh-desk09.XXXXXX)"
export REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_STARTUP_TIMEOUT=120 QT_QPA_PLATFORM=offscreen
export PYTHONPATH="$PWD/apps/desktop:$PWD/apps/services:$PWD/apps/desktop/.venv/lib/python3.12/site-packages"
mkdir -p "$DESKTOP_CAPTURE_DIR"
apps/services/.venv/bin/python -m pytest apps/desktop/tests/test_shipment_planning_lab.py -q --tb=short --show-capture=no --basetemp="$REDHOUSE_TEST_ROOT/pytest" --junitxml="$DESKTOP_CAPTURE_DIR/junit.xml"
```

El listado de traslados no filtra por reserva. Ante conflicto tras pérdida de respuesta, la consulta manual de reserva puede mostrar un traslado vinculado; no demuestra que sea el mismo intento y no elimina el conflicto ni genera otra clave.

La dirección (`root`) inspeccionó las dos capturas del ensayo real y la captura posterior con doble: tablas, selección, fechas y confirmación legibles. No se extrapola esa revisión a Windows o impresión física.
