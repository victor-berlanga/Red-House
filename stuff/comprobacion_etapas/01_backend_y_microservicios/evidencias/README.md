# Evidencias originales de la auditoría

Estos ocho archivos son copias íntegras de los artefactos generados durante la auditoría del 28 de octubre de 2026. Se copiaron desde `/tmp` para conservarlos junto al informe. No se regeneraron pruebas ni se editaron sus resultados al archivar.

| Archivo | Contenido |
| --- | --- |
| [redhouse-audit-01-manifest.json (archivo)](../../../../documentation/evidencias/archivo/detalles-20261104.tar.gz) | Commit, fecha, 3.105 rutas/hash y hash agregado de las fuentes |
| [redhouse-audit-01-current.xml](redhouse-audit-01-current.xml) | Intento completo, incluidos 202 errores de preparación y dos omisiones |
| [redhouse-audit-01-startup.xml](redhouse-audit-01-startup.xml) | Ocho casos de aceptación dirigida |
| [redhouse-audit-01-backend.xml](redhouse-audit-01-backend.xml) | 165 aprobados, una omisión y propiedades de medición WSS |
| [redhouse-audit-01-withdrawal.xml](redhouse-audit-01-withdrawal.xml) | 19 casos aprobados de baja/historial |
| [redhouse-audit-01-remaining.xml](redhouse-audit-01-remaining.xml) | 81 aprobados y una omisión del bloque restante |
| [redhouse-audit-01-schema.json](redhouse-audit-01-schema.json) | Instalación/restauración estructural y comprobaciones del esquema |
| [redhouse-audit-01-reconciliacion.json](redhouse-audit-01-reconciliacion.json) | Casos únicos, omisiones y comprobación de fuentes intactas al cierre |

[archivo_evidencias.json](archivo_evidencias.json) se generó al archivar. Mapea la ruta original de cada artefacto a su copia permanente y registra tamaño/SHA-256. Es un inventario de integridad, no una firma digital ni otra ejecución de pruebas.

Las rutas `/tmp` dentro de los originales se conservan como procedencia; no es necesario que sigan existiendo para leer este expediente. Los enlaces de la documentación apuntan a estas copias.

Los 321 casos aprobados y dos omitidos resultan de reconciliar las cinco ejecuciones, no de sumarlas. Las evidencias no acreditan correcciones F1–F11, GCS real, navegador, hardware, mapas ni despliegue GCP actual.

Leer [evidencias y reproducción](../04_evidencias_y_reproduccion.md) antes de reutilizar un resultado. Conservar los originales y crear archivos nuevos para una reauditoría.


## Archivo de detalles — 04/11/2026

Los manifiestos extensos, capturas de estado Git y muestras HTTP de este expediente se conservan sin alterar sus bytes en [el archivo comprimido](../../../../documentation/evidencias/archivo/detalles-20261104.tar.gz); el [índice](../../../../documentation/evidencias/archivo/detalles-20261104.json) identifica cada ruta original, tamaño y SHA-256. Los resultados, JUnit e incidencias siguen visibles. Antes de ejecutar verificadores históricos que lean esos detalles, restaurar las rutas desde la raíz del repositorio con `tar -xzf documentation/evidencias/archivo/detalles-20261104.tar.gz`. Extraer en una carpeta temporal para una consulta sin escrituras en el repositorio. Los hashes históricos corresponden al corte original, no al árbol actual.
