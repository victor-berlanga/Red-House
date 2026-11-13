# Seguimiento WSS y mapa de escritorio

El 13 de noviembre de 2026, el ensayo `test_qt_wss_replay_revocation_and_native_map` pasó 1/1 en 96,15 s. El JUnit adjunto procede de esa ejecución. Se usaron servicios y datos sintéticos aislados, TLS con certificado efímero y cliente Qt real. El cliente rechazó el certificado sin confianza y conectó después de añadir la CA de laboratorio, sin desactivar la verificación TLS. Se verificaron reconexión con cursor, snapshot `NO_FIX` seguido de replay, retorno a `LIVE`, revocación y limpieza del mapa. La selección de la última observación usa la misma función que la ventana.

La prueba conecta directamente con el servicio de transporte; no verifica el WSS del gateway ni la ventana completa autenticada. Se desactivó la descarga de mosaicos y la captura muestra el aviso de cartografía no disponible; no demuestra disponibilidad de OSM. `mapa-wss-sintetico.png` es la captura obtenida durante el ensayo real. Sus etiquetas se superponen en el zoom regional.

Después se ajustaron las alturas de las etiquetas. `mapa-etiquetas-corregidas.png` muestra la revisión visual del widget Qt con datos sintéticos y sin laboratorio; no es una segunda ejecución WSS. Las etiquetas son legibles en esa imagen. La impresión física, Windows y el paquete reconstruido no forman parte de esta prueba.

Comando del ensayo, desde la raíz (el certificado y las credenciales de prueba son efímeros):

```sh
PYTHONPATH=apps/services:apps/desktop:apps/desktop/.venv/lib/python3.12/site-packages QT_QPA_PLATFORM=offscreen REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" DESKTOP_CAPTURE_DIR="$PWD/documentation/evidencias/entrega-final/desktop/iteracion-wss" apps/services/.venv/bin/python -m pytest apps/desktop/tests/test_tracking_lab.py -q --tb=short --show-capture=no --junitxml=/private/tmp/redhouse-wss-junit.xml
```

Pruebas ligeras de `tests/test_tracking.py`: 7/7. Incluyen rechazo y limpieza por fallo TLS/XML y selección de observación reciente frente a replay. `git diff --check` pasó.

SHA-256 durante el ensayo WSS: `app.py` `87d6e9fa46ae1d2eec3a44bbc16c2553ed916b60617cbb289ae779d669208c47`; `tracking.py` `cc50e4e1a7a6cea65decf735e406591b66e3b21f4b7386eadd14e7d18c729e71`; `native_map.py` `0562eba198a9e54e5fc2603296fdc08193d87173e1b0a27850f0f97f8074ffea`; `test_tracking_lab.py` `153fb7a71ff98b0e8f5758aeee2c93553b56a8f0a408c98d60c532d5d4defaa9`. El ajuste posterior de etiquetas cambió únicamente `native_map.py`, cuyo SHA-256 final es `c7ad2356299cd53e04c721332d67bbb959b4fa835c6a46d88c31d8dacfd617d9`.
