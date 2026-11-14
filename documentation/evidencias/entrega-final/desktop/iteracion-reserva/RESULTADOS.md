# Reserva: resultados y antecedentes

El ensayo Qt/XML `ensayo-cesion-gil` pasó **1/1 en 67,04 s**, con fuentes idénticas antes y después y sin cambiar el plazo del servicio. El médico reservó una unidad sintética; el cliente recibió HTTP 202 y se le inyectó una excepción después de parsear la respuesta. El diario se reabrió con un proveedor de clave doble y recuperó usando la misma clave. La operación terminó `COMPLETED` y se comprobó exactamente una reserva `RESERVED`, los estados SQL del recurso, solicitud y retención, la sesión Redis y un evento de auditoría. También se verificaron la restricción física `UNIQUE (evaluation_id, resource_id)` y el rechazo 409 de un segundo dictamen.

Este ensayo no representa un corte real de red, reinicio real del proceso, recuperación con llavero nativo ni SEC/MFA. Las tres capturas de `ensayo-cesion-gil` se inspeccionaron: incertidumbre y confirmación son legibles. El pie de la captura previa a reservar conserva un texto inconsistente con el dictamen existente; se corrigió posteriormente.

Tras esa corrección, **5/5 pruebas Qt con dobles** pasaron en 4,71 s. Verifican el texto, la selección y que no se ofrezca sustituir un dictamen ya registrado ni reservar con dictamen desfavorable. Las capturas de `estados-doble-final` se inspeccionaron con doble; usan el tema Qt del fixture, distinto del `STYLE` de la corrida real. Su revisión cubre texto y estados, no el tema del producto ni la autorización del servidor.

SHA-256 de `app.py` en el ensayo real: `82e8fb04b3541fe4422d72bf39f6b4f0d3764841ce0cf96da0aed120b50a7fa6`; tras corregir el pie: `113469acbc9dad9547821d3c7c8f4bed841a5ee8b4ee6659896524553815ad32`. Prueba real: `4921eecfb1334c031c13f2ab8714dbdc384ac778129b6cdeef9b11102332d453`. Las huellas completas anteriores y posteriores al ensayo están en `ensayo-cesion-gil/fuentes-antes.sha256` y `fuentes-despues.sha256`.

El comando del ensayo, ejecutado desde la raíz del repositorio en macOS con las dependencias locales instaladas, fue:

```sh
export DESKTOP_CAPTURE_DIR="$PWD/documentation/evidencias/entrega-final/desktop/iteracion-reserva/ensayo-cesion-gil"
export REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_STARTUP_TIMEOUT=120
export QT_QPA_PLATFORM=offscreen
export PYTHONPATH="$PWD/apps/desktop:$PWD/apps/services:$PWD/apps/desktop/.venv/lib/python3.12/site-packages"
apps/services/.venv/bin/python -m pytest apps/desktop/tests/test_reservation_lab.py -q --tb=short --show-capture=no --junitxml="$DESKTOP_CAPTURE_DIR/junit.xml"
```

Para conservar la evidencia existente, una reproducción debe usar otro directorio en `DESKTOP_CAPTURE_DIR`. El fixture inicia servicios locales efímeros y requiere sockets disponibles; no usa GCP.

## Antecedentes

La primera ejecución Qt/XML terminó 0/1 en 125,90 s. Comprobó la restricción única física y el segundo dictamen 409, pero no alcanzó la inyección de respuesta perdida. `ensayo-inicial/junit.xml` y su captura conservan ese intento. Otro arranque se interrumpió durante colección; no ejecutó casos ni inició fixture.

Dos intentos diagnósticos terminaron 0/1 con `503 dependency_unavailable`, antes de la inyección. Las dos observaciones HTTP de entonces podían corresponder a cliente y proxy; no prueban dos envíos. Los JUnit están en `ensayo-diagnostico` y `ensayo-dependencia`. Una revisión por categorías de los logs privados encontró solo la violación única esperada en PostgreSQL y no halló mensajes de deadlock o timeout en los logs de PostgreSQL, Mongo y Redis. La representación de dependencias quedó abreviada en esos intentos.

La ejecución `ensayo-traza-final` terminó 0/1 en 84,60 s. Una llamada del cliente recibió 503: Inventario agotó la lectura de Compatibilidad al consultar la evaluación, con `ReadTimeout` a 3156 ms. En esa evaluación las consultas internas a Receptores, Inventario y rutas tardaron 1575, 722 y 311 ms, respectivamente; respondieron 200 con sobre válido. La evaluación continuó tras el timeout. El JSON saneado y el JUnit están en ese directorio; la traza identifica el salto que agotó su plazo, no la causa raíz de las demoras.

Una comparación sintética sin servidores alternó seis tramos de dos segundos con Python 3.12.6 y PySide6/Qt 6.10.1, en modo `offscreen`. Un hilo Python avanzó 44,3–44,8 veces por segundo durante `QTest.qWait(20)` y 636–671 durante `processEvents()` seguido de `time.sleep(0.020)`. Las medianas entre avances fueron 22,34–22,96 ms y 1,54–1,56 ms, respectivamente. El script y los datos están en `comparativa-gil`. El resultado respalda una hipótesis de contención en el fixture compartido; no demuestra que explique por sí sola el 503. El ensayo aprobado posterior usó el segundo ciclo de espera, con el mismo presupuesto de 40 segundos.

Una prueba Qt sin red anterior pasó 1/1 con un resultado `PENDING` proporcionado por un doble; no demostró persistencia real. La huella de la prueba en la primera ejecución fue `42792cdb820ae57e4910b4f5d64d8910fedcd628cc9e055181a641eee921ba3c`.
