# Administración de dispositivos: avance

Capturas `lista-doble.png` y `registro-doble.png`: widgets Qt con datos sintéticos y cliente doble, inspeccionados el 13/11/2026. No demuestran comunicación con Identidad ni autorización del servidor. El listado desactiva la búsqueda porque la consulta propietaria busca por identificador, no por el nombre presentado.

La prueba Qt dirigida comprueba que las acciones quedan habilitadas para ADMIN y deshabilitadas para otros perfiles. La prueba del diario conserva clave y cuerpo tras reinicio y rechaza una respuesta de alta con identificador distinto. Ambos cuerpos de solicitud se validaron con los XSD copiados de Identidad. Las pruebas de UI y diario anteriores al último ajuste visual dieron 26/26; las dos pruebas nuevas dieron 2/2.

El ensayo `test_devices_lab.py` pasó 1/1 en 76,93 s con los servicios aislados y XML; el JUnit se adjunta. Creó una administradora sintética, inició sesión desde Qt y registró y revocó un dispositivo para un transportista sintético. `registro-qt.png` y `dispositivos-qt.png` proceden de esa ejecución. El nombre del dispositivo quedó parcialmente oculto por el ancho del campo; se amplió después el formulario. `registro-ancho-corregido.png` muestra esa corrección con cliente doble; no es una segunda ejecución real.

```sh
PYTHONPATH=apps/services:apps/desktop:apps/desktop/.venv/lib/python3.12/site-packages QT_QPA_PLATFORM=offscreen REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" DESKTOP_CAPTURE_DIR="$PWD/documentation/evidencias/entrega-final/desktop/iteracion-dispositivos" apps/services/.venv/bin/python -m pytest apps/desktop/tests/test_devices_lab.py -q --tb=short --show-capture=no --junitxml=/private/tmp/redhouse-devices-junit.xml
```

SHA-256 durante el ensayo: `app.py` `385750df035209e986bff1560dd783dcd7510fd02baacc14855ec454dcdf2177`; `durable_commands.py` `ac719147149311dd4ed3b0e32cf9e2283207bf79dd880a00a9060e63f2de324c`; `test_devices_lab.py` `e17559925e140cf279af21606c88d8a01ffbb678a7ecc52351a75628bf8ed3c9`; `routes.py` de Identidad `7cc4902a8f090f0cadbc6b299efa88b53d7d3ee0dcff087f4ff7977307977c27`; `devices.py` `186d4fc168a53e9520cd2fe0646afa82226a7c1172cfd3af8e961c74453068dc`. El único cambio posterior fue el tamaño de los diálogos: `app.py` final `b88e19fd1133f4e27de5c99eba5e6f25ff7cafdc9ddfda594107dc8efc832366`.

La operación de registro no emite credenciales de dispositivo. La revocación vigente en el servidor controla versión pero no ofrece replay idempotente mediante `atomic`; una respuesta perdida puede terminar en conflicto y requiere revisión. Faltan pruebas reales de otros perfiles y conflictos. El alta de usuario requiere además recuperación sin conservar contraseña en el diario.
