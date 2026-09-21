# Consulta y edición por fila — 21 de septiembre de 2026

## Alcance y criterios de aceptación

- Ojo: detalle completo que el perfil tiene autorizado, en una ventana sobre el listado; URL y filtros conservados, sin formularios ni controles de escritura.
- Lápiz: navegación a edición/gestión, únicamente con permisos y estado compatibles. Se reutilizan operaciones, validaciones y límites históricos; no se habilita edición clínica libre.
- Inventario y últimas unidades del panel; instituciones, usuarios, sedes, ubicaciones y componentes; donantes, receptores, donaciones, solicitudes, rutas y traslados utilizan acciones diferenciadas. Auditoría dispone de detalle de evidencia sin edición. Tablas de agregados e historiales sin expediente ofrecen consulta de los campos del resultado.
- Autorización en servidor al consultar y editar, incluidas URL manuales, ámbitos, datos sensibles y estados bloqueados. HTTP 403 con explicación y regreso al panel; 404 para recursos ajenos/no disponibles. Los errores son legibles sin JavaScript.
- Accesibilidad: diálogo nativo, nombre accesible, controles etiquetados, Escape, botón de cierre, fondo y devolución de foco. Carga, reintento, respuestas obsoletas y sesión vencida controladas; contenido retirado del diálogo al cerrarlo.
- Sin migraciones, cambios de credenciales o datos de negocio en la instalación habitual. Pruebas sobre bases aleatorias en un clúster temporal exclusivo.

## Verificación reproducible

Corrección posterior solicitada: el acceso directo denegado muestra el error únicamente en la página, sin duplicación modal. `Error_page_tests.xml` acredita una prueba de navegador aprobada en 12.38 s, con comprobación de diálogo cerrado, encabezado único y regreso al panel, además de los flujos de detalle y edición. `Acceso_denegado.png` refleja esta presentación final.

Resultados: `Tests.xml` contiene 99 pruebas de regresión aprobadas en 258.50 s. `Route_edit_tests.xml` acredita la prueba adicional de edición y versión de rutas. Después del ajuste final del título de consultas agregadas y estados administrativos traducidos, `Details_tests.xml` contiene las cuatro pruebas específicas aprobadas en 17.95 s, incluida la de rutas y Chrome. Ninguna de estas ejecuciones finales tiene fallos, errores u omisiones; cubren 100 pruebas distintas.

Desde `apps/web-monolito01`, con `TEST_POSTGRES_URL` dirigido a un clúster de pruebas con permiso CREATEDB y `NODE_PATH` dirigido a Playwright:

```sh
.venv/bin/python -B -m pytest -q --browser --tb=short
```

`tests/test_details.py` comprueba detalle completo, ausencia de formularios/secretos, acceso directo denegado, segregación institucional, edición de catálogos y versión optimista de rutas. `tests/details_browser.cjs` comprueba ventanas, navegación de edición, permisos, filtros, móvil, foco, reintento y sesión vencida en Chrome. La suite regional existente conserva el recorrido sanguíneo, privacidad, concurrencia y custodia.

Los archivos JUnit contienen el resultado y duración de cada prueba. `Details_browser.json` registra los criterios del navegador; `Detalle_inventario.png`, `Detalle_movil.png` y `Acceso_denegado.png` muestran los nuevos estados. Las demás capturas corresponden a regresiones existentes. Todos los datos de las capturas son ficticios.

## Límites

Chrome/macOS y PostgreSQL local de pruebas. No se declara prueba en Windows ni despliegue productivo. La ventana necesita JavaScript; el detalle autorizado se obtiene por GET con `X-Detail-Modal: 1`, sin navegar la página. El encabezado selecciona la presentación, nunca otorga permisos. Las rutas anteriores conservan compatibilidad y la autorización de servicios. Las tablas de agregados no representan expedientes editables.
