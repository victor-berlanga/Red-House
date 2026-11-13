# Regresión documental — 13 de noviembre de 2026

La regresión existente `test_result_private_document_binding_generation_analysis_and_scope` aprobó **2 casos JSON/XML en 80,31 s** con PostgreSQL, MongoDB y Redis reales en un fixture aislado. Usó dobles explícitos de GCS y ClamD: no demuestra el proveedor ni el antivirus reales. Comprobó asociación documental válida a un resultado de la misma prueba, SHA/generación, análisis de prueba, rechazo antes de verificar, separación institucional y negativa a asociar documento de otra muestra.

El primer intento registró **2 errores de preparación** antes de ejecutar los casos: la ruta del socket Unix de PostgreSQL superaba 103 bytes. Está preservado en `inicio-socket-junit.xml`. Se repitió con ruta temporal más corta: `junit.xml` conserva el resultado aprobado. Los manifiestos `antes.sha256` y `despues.sha256` coinciden para las fuentes listadas; no demuestran identidad de todo el árbol.

Al capturar el manifiesto previo al primer intento, `git rev-parse HEAD` devolvió `9648bf4c0cb857498566e2f3a68c253887deb13f`. Durante la ventana entraron commits ajenos de escritorio y documentación; no se registró HEAD inmediatamente antes de la repetición. Los hashes de las nueve fuentes verificadas, no una suposición sobre HEAD del segundo intento, son la autoridad para el código ensayado. El fixture cerró y se eliminaron exclusivamente los dos directorios temporales propios.

Reproducción desde la raíz, en entorno autorizado para sockets locales; guardar el JUnit con nombre nuevo y usar una ruta corta:

```sh
RH_BASE=/Users/victorberlanga/Programacion/integracion/Red-House
RH_LAB="$(mktemp -d /tmp/rh-hla.XXXXXX)"
mkdir -p "$RH_LAB/p"
REDHOUSE_TEST_ROOT="$RH_LAB/p" \
REDHOUSE_TEST_MONGOD="$RH_BASE/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_STARTUP_TIMEOUT=120 \
"$RH_BASE/apps/services/.venv/bin/python" -m pytest \
  apps/services/tests/test_stage02_corrections.py::test_result_private_document_binding_generation_analysis_and_scope \
  --basetemp="$RH_LAB/t" --junitxml=/ruta/privada/nueva/cont01-regresion.xml -q --tb=short
```

La prueba no accedió a GCP ni acredita validez clínica, navegador, TLS o disponibilidad del bucket. Verificar que el fixture haya terminado antes de borrar exclusivamente el directorio temporal creado para reproducirla.
