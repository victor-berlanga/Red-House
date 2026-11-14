# GCS real con dos objetos sintéticos — 13/14 de noviembre de 2026

La [prueba aislada](junit-intento1.xml) pasó **2/2 en 81,89 s**, con JSON y XML. Documentos preparó dos objetos nuevos, uno por caso, en el bucket `red-house-evidencias-sistemas-integracion-01`, bajo identificadores UUID generados por el fixture; se usaron la identidad **ADC impersonada local**, un firmador IAM real, ClamD 1.5.4 con firmas 28182 y PostgreSQL/MongoDB/Redis desechables. No se accedió a objetos históricos ni se cambió la configuración o el proveedor de producción. El resultado no acredita la identidad adjunta a la VM ni usa su proceso Documentos.

Cada caso comprobó idempotencia de preparación y verificación, PUT HTTPS con `x-goog-if-generation-match: 0`, rechazo 412 de la repetición, resultado CLEAN real, SHA-256, tamaño, MIME y generación, autorización por institución y descarga de bytes idénticos. Tras logout, Documentos rechazó emitir otra URL con el JWT revocado; la URL GCS emitida previamente continuó funcionando dentro de su plazo firmado de **300 segundos**. Esa capacidad directa no dispone de revocación inmediata por logout.

Ambos PUT devolvieron éxito y generación. El fixture comprobó el hash, borró únicamente el objeto propio con condición de esa generación y verificó que dejara de estar disponible por su nombre; no quedaron diarios de limpieza pendientes en el directorio del ensayo. Esto no demuestra eliminación física de versiones sujetas a soft-delete, retención o versionado. ClamD y los servicios aislados terminaron. Tras comprobar que los PID de infraestructura habían terminado y que no había diarios pendientes, se eliminó únicamente el directorio temporal propio del ensayo; JUnit y manifiestos se conservaron aparte.

Los [35 hashes anteriores](antes.sha256) y [posteriores](despues.sha256) coinciden para las fuentes listadas. La prueba no acredita volumen, carga, renovación de firmas, los objetos históricos ni comportamiento de almacenamiento GCS bajo caída. La prueba de acceso anterior solo consultó permisos y firmó una ruta inexistente; la consulta con ADC local devolvió permisos de crear, leer y borrar objetos, no `storage.buckets.get`.

Reproducción desde el worktree revisado y un entorno autorizado para sockets locales y GCS; usar una base de firmas con antigüedad menor a 48 horas, iniciar ClamD en loopback con `TZ=UTC` y no reutilizar el directorio temporal:

```sh
RH_BASE=/Users/victorberlanga/Programacion/integracion/Red-House
RH_LAB="$(mktemp -d /tmp/rhgcs.XXXXXX)"
mkdir -p "$RH_LAB/p"
export REDHOUSE_TEST_ROOT="$RH_LAB/p"
export REDHOUSE_TEST_MONGOD="$RH_BASE/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_STARTUP_TIMEOUT=120
export REDHOUSE_TEST_CLAMD_PORT=13311
export REDHOUSE_TEST_GCS_BUCKET=red-house-evidencias-sistemas-integracion-01
"$RH_BASE/apps/services/.venv/bin/python" -m pytest \
  apps/services/tests/test_gcs_real_isolated.py --basetemp="$RH_LAB/t" \
  --junitxml=/ruta/privada/nueva/gcs.xml -q -x --tb=short --show-capture=no
```

No imprimir ni conservar las URLs firmadas. Si la respuesta de PUT es incierta, falta la generación o falla la limpieza, conservar el directorio privado y su diario para revisar exclusivamente ese objeto; no eliminar objetos por prefijo ni asumir que la ausencia de respuesta implica que no se creó. La [descripción del alcance](../../../entrega-final/continuidad/PLAN_GCS_REAL.md) explica las salvaguardas y límites.
