# Mejoras operativas del monolito — 14 de septiembre de 2026

Este incremento implementa las trece mejoras aprobadas por el usuario. Conserva los servicios del monolito, PostgreSQL, las reglas ABO/Rh demostrativas y la autorización humana. No incluye migraciones ni cambios de datos en la base habitual.

## Resultado final

96 pruebas aprobadas en 141.23 s, sin fallos, errores ni omisiones. `Tests.xml` registra la suite completa con PostgreSQL y Chrome. `Performance.json` contiene las mediciones y las carpetas `regional`, `filters` e `improvements` conservan capturas reproducibles. `pip check` aprobó; UTC/Monterrey también se comprobó con `PYTHONTZPATH=''`.

## Criterios de aceptación y evidencia

| ID | Cambio y criterio verificable | Evidencia |
|---|---|---|
| M-01 | Los errores 400/409 del proceso regional vuelven al formulario, mantienen los campos y muestran el error; una versión obsoleta no se reemplaza silenciosamente. | `test_regional_validation_keeps_fields_and_locked_details`, captura `improvements/Captura_con_error_conservada.png`. |
| M-02 | Un doble envío inmediato produce una sola petición; el botón indica actividad y recupera su estado al volver por historial. | `improvements_browser.cjs`, regresiones de navegador. La integridad continúa validándose en PostgreSQL. |
| M-03 | Donaciones ofrece donantes con estado y última revisión favorables; solicitudes ofrece receptores activos. Búsqueda local por folio o nombre sobre opciones autorizadas. | `test_filters_options_permissions_and_dashboard_links`, navegador de mejoras. |
| M-04 | Donantes con donaciones y receptores con solicitudes muestran datos de consulta y motivo del bloqueo, sin formulario de actualización retrospectiva. | Prueba de capturas/bloqueo, `improvements/Expediente_consulta_mobile.png`. |
| M-05 | Sedes y Ubicaciones mantienen Instituciones activa en el menú; la etiqueta Centro de trasplantes reutiliza el diccionario de presentación. | Navegador de mejoras; plantillas `admin/list.html` y `views.py`. |
| M-06 | Antecedentes, estudios, motivos y observaciones admiten varias líneas con límites y escape; formularios agrupados y botones que nombran la operación. | Pruebas de validación y navegador; capturas regionales. |
| M-07 | Detalles de expedientes, donación, solicitud y traslado muestran etapa, siguiente paso y responsable; el seguimiento solo orienta, no autoriza. | Recorrido `regional_browser.cjs`; `workflow.py`. |
| M-08 | Seis indicadores abren el listado filtrado con permisos existentes; reservas y traslados respetan el ámbito de recepción que usa el contador. | Prueba de filtros/ámbito; navegador abre solicitudes urgentes desde el panel. |
| M-09 | Solicitudes filtra estado/urgencia; Donaciones filtra folio/estado; Traslados filtra recurso, solicitud, institución y estados. Todos se actualizan sin recarga. | Pruebas de filtros, navegador y capturas. Doce secciones con filtros automáticos. |
| M-10 | Panel con tres gráficas, siete días completos y ceros en días sin actividad; datos consultables en texto incluso sin Highcharts. | `Panel_con_graficas.png`, pruebas de series y navegador. |
| M-11 | Las peticiones automáticas reciben solo resultados/resumen. Inventario evita cargar opciones y no calcula agrupaciones descartadas. | `Performance.json`, `test_fragment_cost_and_batched_alerts`; regresiones de filtros, sesión y ausencia de JavaScript. |
| M-12 | Las alertas regionales usan una consulta conjunta y los mismos pares ABO/Rh del motor; conservan disponibilidad, región, ruta, viabilidad y ventana de caducidad. | Prueba de consultas con una y veinte solicitudes; `Performance.json`. |
| M-13 | UTC por defecto o America/Monterrey elegido explícitamente; fechas persistidas en UTC, límites del día de auditoría y tendencias según zona. Capturas pendientes requieren confirmación antes de cambiar horario. | Pruebas de fechas, horas históricas ambiguas/inexistentes, auditoría local y navegador. |

## Reproducción

Desde la raíz, con un clúster PostgreSQL exclusivo y Chrome/Playwright instalados:

```sh
export TEST_POSTGRES_URL='dbname=postgres host=/ruta/al/socket port=55439'
export NODE_PATH='/ruta/a/playwright/node_modules'
export BROWSER_ARTIFACTS="$PWD/documentation/evidence/mejoras-2026-09-14"
apps/web-monolito01/.venv/bin/python -m pytest apps/web-monolito01/tests -q --browser --tb=short --junitxml="$BROWSER_ARTIFACTS/Tests.xml"
```

Las pruebas crean y retiran bases con nombres aleatorios. `Performance.json` compara página completa/fragmento en una base de prueba y registra el número de consultas y tiempo local. No representa rendimiento de producción ni una prueba de carga. El proceso de auditoría permanece activo en ambas formas de consulta.

## Horarios y límites

La preferencia se guarda en una cookie sin datos personales. Cada formulario conserva su zona en `_timezone`, por lo que cambiar la preferencia en otra pestaña no reinterpreta una captura anterior. No se almacenan expedientes ni borradores en localStorage. No hay guardado automático: cambiar el horario recarga la página con confirmación cuando hay datos pendientes.

`tzdata==2026.4` proporciona la base de zonas de respaldo para sistemas sin datos IANA; se comprobó el funcionamiento con `PYTHONTZPATH=''`. Fuente del paquete: [Python Software Foundation en PyPI](https://pypi.org/project/tzdata/2026.4/). PostgreSQL continúa usando su propia base de zonas. No se ejecutó Windows nativo en esta revisión.

Los informes DOCX/PDF previos conservan su corte histórico; esta evidencia documenta el incremento posterior. Órganos/HLA y componentes distribuidos permanecen fuera de este cambio.

## Aplicación local

Monolito reiniciado en `http://127.0.0.1:5050`. Salud, acceso y archivo JavaScript respondieron HTTP 200; el recurso servido coincide byte a byte con el archivo actualizado. `Runtime_check.json` conserva esta comprobación. El clúster PostgreSQL temporal quedó detenido; la base habitual no fue migrada ni usada para generar datos de prueba.
