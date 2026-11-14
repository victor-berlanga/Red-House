# Recepción y revisión de laboratorio

El 13/11/2026 la primera prueba Qt/XML autenticada pasó 1/1 en 120,74 s: una persona operadora recibió una muestra y capturó un resultado, el servidor rechazó la revisión por el operador y una persona médica lo autorizó. El fixture usó unidad, perfil y datos sintéticos sin uso clínico. La prueba comprobó también conflicto por versión previa y fecha seleccionada; aún no correlacionaba el resultado por `sample_id` ni verificaba auditoría en SQL, por lo que no acredita esas comprobaciones. Se conserva `junit-inicial.xml` y las capturas `recepcion-qt.png`, `captura-qt.png` y `revision-qt.png`.

La primera captura de recepción muestra el motivo desplazado por falta de ancho. Se amplió después el diálogo; `recepcion-ancha-doble.png` muestra la corrección con cliente doble. `captura-doble.png`, `captura-zona-doble.png` y `revision-doble.png` son inspecciones Qt sin servicio. La medición se introduce en hora local con segundos, se confirma explícitamente y se envía en UTC; el servidor valida los límites temporales. La revisión requiere elegir autorización o rechazo y documentar motivo.

Pruebas locales Qt posteriores: 3/3. La repetición pasó 1/1 en 123,46 s con vínculo por `sample_id`, verificación de estado, versión e instante en Compatibilidad y los tres eventos de recepción, captura y autorización en Auditoría tras drenado. `repeticion-final/junit.xml` y sus tres capturas corresponden a esa segunda ejecución; fueron inspeccionadas y el motivo de recepción se ve completo. Las consultas SQL pertenecen solo a las pruebas y no al cliente. No se agregaron reglas clínicas ni se acredita despliegue o uso con datos clínicos.

SHA-256 de la primera ejecución: `app.py` `7e4b199bb9e1b4abdc2efbdae95df266b776d29e6762ef3d9e5c3847017dcdbd`; `durable_commands.py` `ac719147149311dd4ed3b0e32cf9e2283207bf79dd880a00a9060e63f2de324c`; `client.py` `f96b768385d476a1d600658b37962200ce00a2dfa7548ed16d3122e9da067777`; prueba `8fffd4aebe4449e0bb813f836b439bb3413e50d2e5e9f3b553995de8d023d9b2`; servicio `laboratory.py` `10a06112b460fa1fe5da37f96f5950fe3fc13e9b854701a1147c0974715843c2`.

La repetición utilizó el mismo comando con `DESKTOP_CAPTURE_DIR` en `iteracion-laboratorio/repeticion-final` y JUnit en `/private/tmp/redhouse-laboratory-final-junit.xml`:

```sh
PYTHONPATH=apps/services:apps/desktop:apps/desktop/.venv/lib/python3.12/site-packages QT_QPA_PLATFORM=offscreen REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" DESKTOP_CAPTURE_DIR="$PWD/documentation/evidencias/entrega-final/desktop/iteracion-laboratorio/repeticion-final" apps/services/.venv/bin/python -m pytest apps/desktop/tests/test_laboratory_lab.py -q --tb=short --show-capture=no --junitxml=/private/tmp/redhouse-laboratory-final-junit.xml
```

SHA-256 iguales antes y después de la repetición: `app.py` `9494a12bb4daa252b9c6a696fe1902cce30a410230fcf803c8773c890443cd4c`; prueba `e97167d500a1893744e3acaa5456564e56792b2b51f984e2e449554fc25536cb`; `durable_commands.py`, `client.py` y servicio conservan los hashes anteriores. No se suman las dos ejecuciones ni se acredita SEC o MFA en esta prueba.
