# Recibo de alta de usuario: laboratorio aislado

El 13/11/2026 se ejecutó `test_user_creation_receipt.py` en este worktree, con PostgreSQL, Redis y MongoDB aislados. La primera corrida terminó 7/8 en 70,78 s: pasaron JSON/XML, actor e institución distintos, sesión revocada, contraseña distinta con la misma clave, otra operación, concurrencia antes y después del commit, redacción de clave y divergencia SQL frente a caché. El único fallo fue la preparación del caso de cambio de rol: la API prohíbe cambiar un ADMIN a rol operativo, y respondió 403 antes de consultar el recibo.

Se corrigió exclusivamente ese caso para simular una divergencia de rol con SQL propietario en el fixture aislado. La repetición dirigida pasó 1/1 en 49,19 s. No se suman ambas corridas como una suite 8/8. Los JUnit originales se adjuntan. La consulta revalida Redis, cuenta y sesión SQL, pero no se afirma atomicidad entre Redis y PostgreSQL. Ausencia de recibo permanece incierta; no hay plazo de retención garantizado.

Comandos desde la raíz del worktree, con `PYTHONPATH=apps/services` y `REDHOUSE_TEST_MONGOD` apuntando al MongoDB local de pruebas:

```sh
/ruta/al/entorno-servicios/bin/python -m pytest apps/services/tests/test_user_creation_receipt.py -q --tb=short --show-capture=no --junitxml=/private/tmp/redhouse-receipt-junit.xml
/ruta/al/entorno-servicios/bin/python -m pytest apps/services/tests/test_user_creation_receipt.py::test_receipt_rejects_changed_role -q --tb=short --show-capture=no --junitxml=/private/tmp/redhouse-receipt-role-junit.xml
```

SHA-256 antes y después de las dos ejecuciones: `routes.py` `5a4a7c6844bdd5516e398277c6b70c48717c6a1f069b6379044c97df3c539c05`; `redhouse/openapi.py` `eb7639dd6cff0ab13e0881a92add1a3899aff8e17e04a2536783afd7a39cedcf`; `redhouse/evidence.py` `d1497d608ddbaa3a54011e5c74b085144867f6cc59c864593a4115ba29fb39fa`; OpenAPI de Identidad `9dbbe6fb06f0eb3bb0564ee4f08bc4ccd6c1faea3f82318dcb324e46f3b95f07`; DTO `6453b92d4ae1c44a5e998fd758d70e772a857f21137f2f1e408af7a39f871bdd`. El archivo de prueba inicial fue `8241a1a126f616562773be3a0a140d417a2524d62cf57ea21aa7ee13182465e3`; tras corregir la preparación del caso de rol, `5e987e056bbb9e1f9476485d533b10b6591a3bbf817cd93ba2f5323302c328a5`.

`document.py --check-openapi` y Ruff de los archivos modificados pasaron antes de las pruebas. No hay despliegue ni integración con la consola en este resultado.
