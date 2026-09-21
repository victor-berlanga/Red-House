# Regreso al listado después de crear registros

Fecha: 2026-09-21.

Criterio: al crear correctamente un registro, regresar a la tabla de su sección sin filtros heredados, conservando permisos, paginación, aviso de éxito y validación de errores.

Destinos comprobados en los recorridos existentes:

| Alta | Listado |
| --- | --- |
| Unidad de inventario o liberada desde donación | `/inventario` |
| Donante | `/sangre/personas/donor` |
| Receptor | `/sangre/personas/recipient` |
| Donación | `/sangre/donaciones` |
| Solicitud | `/sangre/solicitudes` |
| Reserva de asignación o programación de traslado | `/sangre/traslados` |

Administración ya redirigía a `/administracion/<entidad>` y rutas a `/sangre/rutas`. Las operaciones de edición y los eventos de expedientes existentes conservan su navegación contextual.

## Verificación

Desde `apps/web-monolito01`, con `TEST_POSTGRES_URL` dirigido exclusivamente a un clúster de pruebas con permiso CREATEDB y `NODE_PATH` apuntando a Playwright:

```sh
.venv/bin/pytest tests/test_monolith.py tests/test_regional.py -k 'not test_regional_browser or regional_browser.cjs' --browser -q
.venv/bin/pytest tests/test_browser.py --browser -q
```

Resultados observados:

```text
46 passed, 3 deselected in 96.35s (0:01:36)
1 passed in 20.04s
```

El navegador regional comprueba el listado y la fila creada antes de abrir explícitamente el detalle para continuar hasta recepción y cierre. El navegador de inventario comprueba el regreso, el aviso y la apertura con el lápiz. La prueba transaccional comprueba además el destino HTTP `/inventario`, la persistencia, el historial y la auditoría. No se añadieron casos nuevos: se adaptaron verificaciones existentes.

Entorno: macOS, Chrome y PostgreSQL 14 en el puerto exclusivo 55439; bases aleatorias creadas y retiradas por las pruebas. El intento inicial restringido no pudo conectar por el sandbox; se repitió con permisos y pasó. JUnit local: `/private/tmp/red-house-create-redirect-tests.xml` y `/private/tmp/red-house-create-inventory-browser.xml`.

Límites: el listado conserva orden y paginación, por lo que un alta puede quedar en otra página. No se modificaron esquemas, reglas clínicas, credenciales o datos de la instalación habitual. Su servidor no se reinició.
