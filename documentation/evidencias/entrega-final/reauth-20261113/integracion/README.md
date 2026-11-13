# Integración de seguridad y proyección operativa

Base: `a8e54d3`, que reúne transporte nominal, reautenticación, rutas autónomas y formato del backend. PostgreSQL, Redis y MongoDB 8.0.17 efímeros en macOS; no GCP.

Primera ejecución: **cinco aprobados y un fallo, 79,06 s**. Pasaron los cuatro casos de transporte y el caso JSON de vínculo/recuperación; el caso XML descubrió una representación base64url no canónica aceptada. Los 1293 hashes de fuentes, contratos y pruebas registrados en `antes.json` y `despues.json` coinciden. OpenAPI `--check-openapi` pasó después de integrar ambos cambios.

Cambiar los bits no utilizados del último carácter podía conservar exactamente los mismos bytes de la firma Ed25519. No permitía firmar otro contenido ni cambiar usuario, sesión, cuerpo o ámbito, pero hacía no determinista el rechazo de una cadena alterada. `_decode` ahora exige que volver a codificar los bytes produzca la misma cadena recibida.

La prueba determinista comprueba bits sobrantes y truncamiento; los dos casos unitarios pasaron en **1,45 s**. Después se repitieron únicamente los dos casos JSON/XML afectados: **dos aprobados en 52,22 s**. No se presenta la primera ejecución como seis de seis ni se suman repeticiones como casos diferentes. `correccion-hashes.json` identifica los dos archivos corregidos.

El JUnit inicial expandió la contraseña aleatoria del fixture desechable en su aserción. El original se conserva privado; `junit-redactado.xml` sustituye únicamente ese valor y conserva el fallo. `redaccion.json` registra dos sustituciones y el hash del original. No son credenciales productivas; no se atribuye esta redacción a los otros JUnit.

## Reproducción

Desde la raíz, con las dependencias de servicios y herramientas locales instaladas:

```sh
export REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_STARTUP_TIMEOUT=120
apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_operational_handover_projection.py \
  apps/services/tests/test_reauthentication_single_use.py::test_bound_proof_replay_and_scope \
  -q --tb=short --show-capture=no --junitxml=/private/tmp/reauth-integracion-nueva.xml
apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_reauthentication_single_use.py::test_signed_challenge_binds_actor_session_and_normalized_body \
  apps/services/tests/test_reauthentication_single_use.py::test_challenge_encoding_requires_canonical_base64url \
  -q --junitxml=/private/tmp/reauth-codificacion-nueva.xml
apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_reauthentication_single_use.py::test_bound_proof_replay_and_scope \
  -q --tb=line --show-capture=no --junitxml=/private/tmp/reauth-repeticion-nueva.xml
```

Los nombres nuevos preservan la evidencia histórica. Los ensayos requieren sockets locales y no prueban publicación, ventanas de mantenimiento ni recepción física.
