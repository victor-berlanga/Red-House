# Evidencia de la ampliación regional del monolito

Fecha: 13 de septiembre de 2026. Alcance: flujo sanguíneo académico previo a microservicios. Datos de prueba ficticios.

## Resultados

- **89 pruebas aprobadas**, 0 fallos, 0 errores y 0 omisiones, en **92.68 segundos**.
- La suite incluye la regresión del monolito, instalación, migración desde el esquema anterior, validación ABO/Rh, integración, permisos, dos reservas concurrentes, rollback de auditoría, custodia y dos recorridos de navegador.
- El recorrido nuevo de Chrome completa donante → revisión → donación → recolección → procesamiento → unidad → receptor/solicitud de otra institución → candidatos → autorización/reserva → asignación → traslado → custodia → recepción → cierre.
- Se verifican siete cuentas de prueba, Highcharts, pantallas a 1440 y 390 px, ausencia de errores JavaScript y recursos locales faltantes.
- La actualización local se probó restaurando un respaldo en un clúster exclusivo antes de aplicarse. Preserva las cuatro cuentas, contraseñas, 36 unidades e historial anteriores. Se habilitan tres perfiles adicionales, sin crear cuentas nuevas durante la migración.
- El catálogo posterior contiene **38 tablas**. El esquema inicial conserva 23; la ampliación añade 14 tablas de negocio y una técnica de migraciones.

## Artefactos

| Archivo | Contenido |
| --- | --- |
| [Tests.xml](Tests.xml) | Informe JUnit de la suite completa de esta versión |
| [Upgrade_check.json](Upgrade_check.json) | Restauración de copia, migración, repetición y preservación mediante huellas por tabla |
| [Physical_schema.json](Physical_schema.json) | Columnas, claves, restricciones e índices obtenidos del catálogo real |
| [Report_build.json](Report_build.json) | Secciones, tablas, figuras y huellas de Word/PDF generados |
| [Report_review.json](Report_review.json) | Integridad de Word, contenido PDF y revisión de maquetación |
| [regional/](regional/) | Capturas del flujo nuevo; archivos completos y versiones de primera pantalla para el reporte |

Las capturas adicionales de nivel superior corresponden al recorrido de regresión. Los artefactos anteriores del primer parcial permanecen en su directorio histórico y no sustituyen estas pruebas. El respaldo privado de la base no se incluye en el repositorio; `Upgrade_check.json` identifica su ruta local y permisos.

## Repetición de pruebas

Usar un clúster PostgreSQL exclusivo, con permiso para crear bases de prueba, y un entorno Python con `requirements-dev.txt`. Playwright debe estar disponible mediante `NODE_PATH`, con Chrome instalado. Desde `apps/web-monolito01`:

```sh
python -m pytest -q --browser -p no:cacheprovider --tb=short --junitxml=/ruta/nueva/Tests.xml
```

Definir `TEST_POSTGRES_URL` hacia el clúster exclusivo y `BROWSER_ARTIFACTS` hacia una carpeta nueva. No sobrescribir este corte ni dirigir las pruebas a la base funcional. Cada caso crea y retira únicamente su base aleatoria.

## Generación del reporte

En un entorno documental separado, instalar `documentation/scripts/requirements-report.txt`. Proporcionar Mermaid y Playwright a Node. Desde la raíz:

```sh
node documentation/scripts/render_report_diagrams.cjs
python documentation/scripts/build_first_report.py
```

El primer script exporta doce fuentes Mermaid a SVG/PNG. El segundo integra la fuente Markdown, el diccionario físico, los resultados y las figuras en Word/PDF; rechaza informes de pruebas con fallos u omisiones y figuras faltantes. En macOS usa las fuentes Arial del sistema; en otro sistema se debe adaptar la ubicación de las fuentes del generador PDF.

## Límites

No se ejecutaron Windows nativo, Locust, volumen considerable, GCP, MongoDB o Redis en esta revisión. El motor es demostrativo y solo cubre eritrocitos. La custodia conserva referencias documentales, sin carga de archivos. Órganos/HLA permanece separado y pendiente. La confirmación docente de aceptación no se infiere de las pruebas técnicas.
