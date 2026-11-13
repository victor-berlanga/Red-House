# Proyección nominal de transporte: laboratorio aislado

Fecha: 13 de noviembre de 2026. macOS x86_64; Python del entorno local aislado de servicios. La prueba usó PostgreSQL, Redis y MongoDB 8.0.17 locales efímeros y servicios reales del worktree. No se usaron datos productivos ni se invocó GCP.

Desde la raíz del worktree, con `SERVICE_PYTHON` apuntando al Python del entorno aislado de servicios y `REDHOUSE_TEST_MONGOD` al binario local compatible:

```sh
PYTHONPATH=apps/services "$SERVICE_PYTHON" -m pytest apps/services/tests/test_operational_handover_projection.py -q --tb=short --show-capture=no --junitxml=/private/tmp/redhouse-handover-junit.xml
```

Resultado: 4 pruebas aprobadas en 69,48 s; [JUnit](junit.xml). Cubre contrato JSON/XML, acceso por rol y ámbito, acceso interno no autorizado y reasignación concurrente durante consulta. Las entradas son sintéticas. [SHA256SUMS](SHA256SUMS) fija el contenido de código, contratos, prueba y JUnit de esta ejecución. `git diff --check` terminó sin advertencias; el archivo de prueba nuevo también se revisó con `git diff --no-index --check`.

El resultado no demuestra recepción física, identidad legal, lectura de códigos ni despliegue. El nombre es de cuenta operativa; los clientes deben comprobar versión del traslado e identificador del transportista contra el contexto autorizado. La ruta previa conserva su contrato sin cambios.
