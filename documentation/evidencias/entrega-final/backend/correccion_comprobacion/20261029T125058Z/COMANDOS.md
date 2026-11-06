# Reproducción de la corrección

Los comandos se ejecutan desde la raíz; usar un directorio nuevo por intento. No requieren ni usan la base habitual. MongoDB, PostgreSQL y Redis son procesos temporales. `REDHOUSE_GCS_TEST_BUCKET` debe apuntar únicamente a un bucket autorizado; ADC y configuración privada permanecen fuera de Git.

```sh
export REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_BROWSER_TESTS=1
export REDHOUSE_BROWSER_RESULTS="$PWD/RUTA_NUEVA/browser"
export REDHOUSE_GCS_TEST_BUCKET=BUCKET_AUTORIZADO
export GOOGLE_CLOUD_PROJECT=PROYECTO_AUTORIZADO
export CLAMD_HOST=127.0.0.1
export CLAMD_PORT=33310
apps/services/.venv/bin/python -m pytest apps/services/tests -k 'not operational_browser_corrections' -q --tb=short -p no:cacheprovider --junitxml=RUTA_NUEVA/regresion.xml
# Requiere Docker Desktop/Engine para el Nginx temporal, Chrome y Playwright.
apps/services/.venv/bin/python -m pytest apps/services/tests/test_correction_browser.py -xq --tb=short -p no:cacheprovider --junitxml=RUTA_NUEVA/browser.xml
apps/services/.venv/bin/python apps/services/scripts/document.py --contracts-only
apps/services/.venv/bin/python scripts/build_shared_schema.py --check
```

No ejecutar ambas suites simultáneamente en máquinas con presión de memoria. Los esperados 401/403/409/412/422 y las caídas intencionales se distinguen de errores inesperados. El navegador del gateway usa un certificado sintético de localhost y cookies Secure; el navegador productivo debe usar HTTPS real sin ignorar TLS.

La prueba `test_correction_upgrade` crea un entorno real desechable, elimina solo la credencial sintética del propietario extraído, ejecuta su provisión dos veces, comprueba aislamiento y sesiones, genera un dump real y ejecuta la misma entrada Compose dos veces. `test_schema_11_extraction_backup_restore_and_idempotency` prueba v11→v13 y restaura un dump en otra base. Ninguna prueba instala sobre los datos locales existentes.

Durante la regresión 21 se añadieron etiquetas españolas y clasificación de eventos dinámicos, además de dos variantes de reasignación WSS. La ejecución focalizada posterior debe incluir `test_final_operations`, `test_final_quality` y los casos `reassigned`/`new_event_classification` de `test_correction_backend`. Sus resultados complementan la regresión, no se suman duplicados. La reasignación de responsable se inyecta explícitamente en el PostgreSQL temporal: prueba revalidación de autoridad, no un comando público de reasignación inexistente.

Regresión 21: 356 aprobados / 9 fallidos / 1 excluido explícitamente (gateway operativo). Sin skips. Cuatro entradas incompletas de telemetría se corrigieron y sus 16 variantes numéricas pasaron en `limites-22.xml`. Las otras cinco pruebas anteriores omitían custodia o consultaban storage en Transporte; la repetición focalizada usa los contratos actuales y Documentos. Durante esa revisión se corrigió también la generación del UUID del formulario de ubicación.

La rama adicional de navegador de ubicación se activa con `REDHOUSE_BROWSER_MODULES="$PWD/.local/gcp-public/browser/node_modules"` y guarda sus resultados bajo `REDHOUSE_BROWSER_RESULTS`. Usa fuente `SIMULATOR`, dispositivo/asignación reales temporales y verifica que existe exactamente un punto persistido tras guardar. No sobrescribe capturas históricas.

### Intentos 24–26 y gateway nativo

Docker Desktop se reinició sin borrar volúmenes/imágenes. El intento 24 con la imagen Nginx aprobó laboratorio, custodia y WSS/reconexión, pero terminó fallido por espera agotada del worker y respuestas 504 en recursos estáticos bajo saturación del host. Se conservaron informe/JUnit/capturas; los detalles de petición de Playwright se redactaron para eliminar cookies. El script ahora conserva solo la primera línea del error.

Se compiló Nginx 1.28.0 desde `https://github.com/nginx/nginx/archive/refs/tags/release-1.28.0.tar.gz`, con TLS verificado, en `/tmp/nginx-release-1.28.0`. El intento de descarga desde nginx.org falló por cadena TLS y no se desactivó la verificación. Fuente/binario/configuración: `nginx-nativo.json`. Compilación temporal, sin instalación permanente:

```sh
./auto/configure --prefix=/tmp/redhouse-nginx --with-http_ssl_module \
 --with-cc-opt=-I/usr/local/opt/openssl@3/include \
 --with-ld-opt=-L/usr/local/opt/openssl@3/lib \
 --without-http_rewrite_module --without-http_gzip_module
make -j2
```

El intento 25 descubrió una ruta incorrecta en el verificador Compose nuevo (`/api/v1/reports`); se corrigió a `/api/v1/export-jobs`. El verificador ya envía custodia completa y no llama helpers que requieren conexiones del fixture.

Ejecución 26, con Docker detenido, mismo backend completo temporal, Nginx nativo, Chrome, cookies Secure y políticas MFA/reauth/perfil/constancia externa activas. Añade sesión vencida en servidor y reporte privado de otra institución:

```sh
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_NGINX=/tmp/nginx-release-1.28.0/objs/nginx \
REDHOUSE_BROWSER_TESTS=1 \
REDHOUSE_BROWSER_RESULTS="$PWD/documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z/browser-26" \
REDHOUSE_GCS_TEST_BUCKET=red-house-evidencias-sistemas-integracion-01 \
GOOGLE_CLOUD_PROJECT=sistemas-integracion-01 CLAMD_HOST=127.0.0.1 CLAMD_PORT=33310 \
apps/services/.venv/bin/python -m pytest \
 apps/services/tests/test_correction_deploy_verifier.py \
 apps/services/tests/test_correction_browser.py -xv --tb=short -p no:cacheprovider \
 --junitxml=documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z/browser-verificador-26.xml
```

La alternativa nativa ejecuta un gateway Nginx real con TLS/WSS; no acredita la topología Compose completa ni sustituye la aceptación productiva. Los endpoints `/test/*` existen exclusivamente en el fixture de navegador.

### Repetición 27

Se conserva el intento 26: los dos flujos del verificador pasan; el navegador capturó una renovación automática de sesión en lugar del POST del formulario al comprobar el rechazo. Se restringió la espera a la ruta del formulario. La ejecución 27 repite el navegador completo con las mismas variables de 26, salida `browser-27`, JUnit `browser-27.xml` y `caffeinate -i` durante el comando para impedir suspensión por inactividad. No se relajó el código HTTP esperado ni una regla del backend.

### Repeticiones 28 y 29

El intento 27 pasó hasta revocación de rol y expiración de sesión; el caso de búsqueda debía pedir `status=WITHDRAWN`, porque el destino final retira la unidad y el listado predeterminado excluye retiradas. El intento 28 añadió ese filtro y pasó la búsqueda, pero omitió seleccionar `order` en el formulario de reporte. El mensaje de validación quedó visible; no hubo creación indebida. El intento 29 completa `order=DATE_DESC` y solicita CUSTODY/CSV del traslado aceptado; comprueba que el archivo descargado contiene `SHIPMENT_ACCEPTED`. Mismas variables y comando de navegador, cambiando rutas de resultados/JUnit a `browser-29`.

El recorrido conserva rechazos 401/403/409 esperados. Ninguno de esos ajustes relaja autorización, validación ni el resultado esperado del backend.

### Repetición 30 y verificación de imágenes

El intento 29 completó 26 comprobaciones, incluida la descarga CSV privada desde GCS con `SHIPMENT_ACCEPTED` y la auditoría responsive. El selector de salida encontró los dos formularios del diseño responsive. La ejecución 30 vuelve a escritorio y selecciona el botón visible; repite el flujo completo con salida/JUnit `browser-30`.

Las imágenes finales se construyen después del navegador con Compose `--parallel 1`, sin otras pruebas activas. BuildKit comparte y puede ejecutar etapas internas en paralelo. `build_images.py` preserva cualquier etiqueta previa bajo `before-correction-20261029T125058Z`; `verify_images.py` inspecciona versiones, paquete único, usuario sin privilegios, liveness/OpenAPI y hashes de fuentes/SQL/scripts de arranque dentro de cada imagen:

```sh
python3 documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z/build_images.py
python3 documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z/verify_images.py
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
apps/services/.venv/bin/python apps/services/tests/check_document_image.py \
 --output documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z/documentos-contenedor.json
```

La última comprobación usa el entrypoint real, PostgreSQL/Redis temporales y lecturas autenticadas JSON/XML. Detiene antes la API documental del fixture. No consume configuración ni volúmenes de la instalación habitual; sus credenciales temporales no se imprimen. La topología completa Compose no se vuelve a desplegar.
