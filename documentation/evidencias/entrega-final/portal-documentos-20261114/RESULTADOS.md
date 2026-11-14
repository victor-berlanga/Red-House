# Documentos privados desde el portal — 14/11/2026

Chrome completó el recorrido funcional sobre el monolito autónomo: dos versiones de una acreditación sintética, carga real, análisis, descarga exacta de ambas y conservación de la primera. La bifurcación desde la versión sustituida recibió 412; otra institución recibió 403 en detalle y autorización de descarga; tras logout no se pudo solicitar una nueva descarga. [Resultado del navegador](intento-02/browser.json).

**La corrida pytest terminó con un fallo en su oráculo**, después de completar Chrome y comprobar versiones SQL. El test buscaba `FILE_PREPARED`; la operación de documentos emite `DOCUMENT_PREPARED`. Se conserva el [JUnit fallido](intento-02/junit.xml), su [salida](intento-02/pytest.txt) y las fuentes ejecutadas. No se contabiliza como un pytest aprobado ni se borra el fallo del arnés.

La [comprobación posterior de solo lectura](intento-02/oraculo-corregido.json) arrancó únicamente PostgreSQL del mismo fixture conservado, sin repetir el navegador, cargas ni verificaciones. Confirmó dos versiones encadenadas, dos archivos VERIFIED, análisis CLEAN para su generación/hash, tamaño/MIME y SHA-256 iguales a los bytes descargados, y exactamente un DOCUMENT_PREPARED y FILE_VERIFIED por archivo. La primera descarga y su descarga posterior fueron idénticas. Transacción SQL READ ONLY; PostgreSQL propio cerrado al finalizar. El [procedimiento](intento-02/oraculo-solo-lectura.py) conserva la ruta exacta de ese ensayo y no es un comando genérico de producción. La expectativa del test quedó corregida; no se volvió a ejecutar el caso completo solo para cambiar su contador.

## Entorno y evidencia

- PostgreSQL, MongoDB y Redis reales, privados y temporales; portal Flask/Jinja con `ApplicationKernel`. Todos los listeners API del fixture permanecieron detenidos durante Chrome. No se usó GCP ni se modificaron sus archivos.
- Almacenamiento LOCAL en directorio privado 0700, dos PNG sintéticos de 16 × 16. ClamD real 1.5.4, TZ=UTC; el test exigió detectar EICAR antes de abrir Chrome y aplicó la validación de vigencia del producto. No hubo doble de escáner.
- HTTPS local con certificado efímero; Chrome usó `ignoreHTTPSErrors` exclusivamente en contextos temporales de este ensayo. No acredita confianza TLS del sistema, Nginx, Docker ni GCS. El modo monolito resuelve la carga local por su propietario embebido.
- Fixture `TESTING=True`, cuotas ampliadas y cuentas ADMIN sintéticas. No es medición de capacidad, MFA ni una validación productiva completa.
- El caso consumió 124,34 s incluyendo preparación/cierre pytest; el envoltorio con arranque del escáner consumió 175,425 s. No son latencias de operación ni RTO.
- [1.305 fuentes](intento-02/fuentes.json) idénticas antes/después, comprobadas en [revisión](revision.json). Los dos manifiestos originales permanecen privados; se publica una copia porque son iguales. El cambio posterior del nombre de evento pertenece al arnés corregido, no a la corrida original.
- Los logs/configuraciones privados permanecen en `.local/artifacts/portal-documentos-20261114/`. No se publican contraseñas, capacidades de descarga ni DSN. ClamD y motores del ensayo terminaron; el oráculo posterior también cerró su único PostgreSQL.

Dirección inspeccionó las tres capturas completas: [documento verificado](intento-02/primera-version.png), [versión obsoleta](intento-02/version-obsoleta.png) e [institución ajena](intento-02/institucion-ajena.png). Las acciones y rechazos son legibles. Se detectaron etiquetas técnicas en inglés y orientación insuficiente tras conflicto de versión; su corrección de presentación se registra aparte y no invalida la cobertura de persistencia/autorización.

## Intentos y alcance

El [primer arranque](arranque-01.json) agotó los 30 segundos del envoltorio mientras ClamD cargaba firmas; pytest no comenzó y el proceso propio terminó. El segundo permitió hasta 120 segundos únicamente para ese arranque. No se amplió ningún timeout, cuota o permiso del producto.

Esto cubre el documento de acreditación y el versionado/ámbito del portal dentro de I06-02/03. No acepta por sí solo los documentos de laboratorio, evidencia de traslado, cambios de conservación/hold, EICAR mediante formulario, caída/recuperación del escáner ni reportes masivos. El EICAR directo es un control de disponibilidad del motor, no el caso de archivo infectado por UI. No se consultó MongoDB en el oráculo de este caso; los eventos comprobados aquí son SQL. No se afirma revocación instantánea de una capacidad ya emitida.

## Reproducción

Con ClamD real propio disponible en loopback, TZ=UTC y firmas vigentes, crear un directorio nuevo de resultados y ejecutar desde la raíz:

```sh
REDHOUSE_BROWSER_TESTS=1 \
REDHOUSE_TEST_CLAMD_PORT=13311 \
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_BROWSER_RESULTS="$PWD/.local/artifacts/portal-documentos-repeticion" \
PYTHONPATH=.:apps/services \
apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_portal_private_document_browser.py -q --tb=short \
  --junitxml=.local/artifacts/portal-documentos-repeticion/junit.xml
```

Chrome/Playwright debe estar disponible según las guías del laboratorio. No usar un escáner o almacén de terceros. Ruff, formato del test y `node --check` aprobaron; la comprobación final del cambio de expectativa fue estática y el oráculo separado descrito arriba.
