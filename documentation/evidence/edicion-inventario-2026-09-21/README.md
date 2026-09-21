# Edición unificada del inventario sanguíneo

## Criterios de aceptación

- Una tarjeta con datos de unidad y campos editables: estado y ubicación. Identificación, componente, grupo, fechas y referencia permanecen de consulta; historial separado.
- Motivo fuera del panel general: se captura en el diálogo de confirmación de guardar o dar de baja, obligatorio y con máximo de 240 caracteres. No se aceptan motivos vacíos o de solo espacios.
- Guardar muestra el resumen de valores anteriores y nuevos; sin cambios no abre confirmación ni envía la operación. Cancelar conserva la selección sin escribir en base de datos.
- Baja lógica con resumen de retiro e historial conservado; no aplica los cambios pendientes de los desplegables. Continúa bloqueada cuando existe movimiento posterior al alta.
- Permisos, CSRF, validaciones transaccionales y versiones vigentes siguen comprobándose en servidor. Captura rechazada conserva selecciones, motivo y versión enviada.
- El ojo permanece de solo lectura. Confirmaciones accesibles mediante diálogo nativo, foco en motivo, Escape/cierre/cancelación y retorno de foco.

## Verificación

Resultado: 30 pruebas aprobadas en la ejecución de 31 (`Tests.xml`, 64.86 s). La restante esperaba el antiguo texto «Dar de baja unidad»; se actualizó para comprobar la acción de baja y se añadió la verificación de motivo vacío en servidor. Su repetición pasó (`Retest.xml`, 1.83 s). Las 31 pruebas distintas quedan verificadas, conservando el resultado original para trazabilidad.

`tests/test_browser.py` y `tests/browser_smoke.cjs` cubren tarjeta única, motivo oculto inicialmente, resumen, cancelación, motivo obligatorio, rechazo de espacios, guardado real, historial, bloqueo de baja y confirmación de baja en móvil. `tests/test_monolith.py` comprueba persistencia, permisos, estados, concurrencia y rechazo de baja con motivo vacío. `tests/test_details.py` mantiene la regresión del ojo y el acceso directo protegido.

Ejecutar desde `apps/web-monolito01` con `TEST_POSTGRES_URL` apuntando a un clúster exclusivo de pruebas y `NODE_PATH` apuntando a Playwright:

```sh
.venv/bin/python -B -m pytest -q tests/test_monolith.py tests/test_browser.py tests/test_details.py --browser --tb=short
```

Evidencia: JUnit y capturas de esta carpeta. Entorno Chrome/macOS y PostgreSQL temporal, con datos ficticios; sin cambios en la base habitual ni reglas clínicas. Los diálogos requieren JavaScript; se informa si está deshabilitado.
