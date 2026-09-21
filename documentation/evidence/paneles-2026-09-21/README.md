# Paneles unificados y confirmación de operaciones

## Alcance y criterios de aceptación

- Expedientes y rutas: datos y campos editables en una tarjeta, sin duplicar sus valores como detalle y formulario. La institución del expediente, el origen/destino de la ruta y las referencias institucionales no reasignables permanecen de lectura.
- Donaciones, solicitudes y traslados: operaciones autorizadas junto a los datos del registro. Revisión médica, liberación, reserva, programación, cancelación y custodia mantienen sus formularios y permisos propios. Historias, candidatos y seguimiento no se convierten en campos editables.
- Administración: instituciones, sedes, ubicaciones, componentes y usuarios conservan un solo recuadro, con confirmación de cambios e inactivaciones. El parámetro de aviso compara las horas anteriores con las nuevas; no cambia la caducidad de las unidades.
- El motivo o referencia requerida aparece dentro del diálogo al confirmar, no en el panel general. Cancelar, Escape y cerrar no envían la operación; se conserva el borrador y se devuelve el foco. No se envían ediciones sin cambios.
- Los resúmenes no reproducen contraseñas ni contenidos clínicos. Modificar una cuenta advierte que se revocan sus sesiones. Las autorizaciones médicas explícitas no son sustituidas por el botón genérico de confirmación.
- Motivos administrativos nuevos de hasta 240 caracteres: ediciones administrativas, expedientes, rutas, programación de traslados y parámetros. Se validan en servidor y se guardan en `audit_event.reason`, dentro de la transacción de la operación. Los fundamentos clínicos y de custodia existentes permanecen en sus registros restringidos; no se copian a la auditoría general.
- Ojo, permisos por perfil/institución/recurso, conflictos de versión y bloqueo de expedientes históricos se conservan. Auditoría, historiales y tableros siguen siendo de consulta. Los errores de acceso directo no abren una ventana redundante.

La evaluación de candidatos confirma el cálculo sin inventar un motivo clínico; las altas ordinarias de expedientes y catálogos no se transforman en ediciones. El registro/actualización de rutas sí requiere motivo porque también actualiza estimaciones existentes. No hay migraciones ni cambios de datos habituales.

## Verificación reproducible

Resultado: **110 pruebas distintas comprobadas**. La regresión completa registró 109 aprobadas y un timeout de 200 s al finalizar el proceso de Chrome de filtros (393.76 s totales). Las comprobaciones de filtros ya habían producido `Browser_results.json` con resultado PASS; su repetición aislada aprobó en 67.74 s. Tras hacer explícito el cierre de sus contextos, la revisión final de filtros y paneles aprobó dos pruebas en 34.13 s. Se conservan los resultados originales y las repeticiones; no se presenta la primera ejecución como libre de fallos.

Pruebas sobre PostgreSQL temporal, con una base aleatoria aislada por prueba y eliminación de esa base al terminar. Navegador: Chrome mediante Playwright. Todas las cuentas y registros de las capturas son de prueba; no se utilizaron datos habituales ni credenciales reales del portal.

Desde `apps/web-monolito01`, con `TEST_POSTGRES_URL` apuntando a un clúster de pruebas con permiso de crear bases y `NODE_PATH` a una instalación de Playwright:

```sh
BROWSER_ARTIFACTS=../../documentation/evidence/paneles-2026-09-21 .venv/bin/python -B -m pytest -q --browser --tb=short --junitxml=../../documentation/evidence/paneles-2026-09-21/Tests.xml
```

`tests/test_edit_panels.py` comprueba motivo vacío, espacios, longitud máxima, conservación de versiones y reversión atómica; persistencia del motivo en administración, expedientes, parámetros, rutas y programación. `tests/panels_browser.cjs` cubre los cinco catálogos, parámetros y rutas, incluyendo foco, cancelación, motivo obligatorio, contraseñas ocultas, advertencias, un solo envío y pantalla móvil. El flujo regional de navegador incluye también la edición de donante y receptor, etapas, liberación, reserva, traslado, custodia y cierre.

Las ventanas requieren JavaScript y soporte de `dialog`; sin JavaScript, los formularios regionales/administrativos mantienen visible el motivo y conservan las validaciones del servidor. No se altera el comportamiento previo del inventario.

## Evidencia

- `Tests.xml`: resultado de la regresión completa.
- `Filters_retest.xml`: repetición aprobada de filtros.
- `Browser_retest.xml`: revisión final aprobada de filtros y paneles.
- `panels/`: confirmación administrativa, parámetro móvil y ruta unificada.
- `regional/`: recorrido completo de donación a recepción y cierre, por los perfiles autorizados.
- El resto de capturas corresponde a las pruebas existentes de inventario, detalle, permisos, filtros y formularios recuperables.
