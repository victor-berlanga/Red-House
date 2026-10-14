# Capturas reales del portal integrado — 2026-10-07

Chrome real, datos ficticios persistidos en microservicios, escritorio 1440 × 1000 y móvil 390 × 844. Capturas del área visible sin montaje ni generación de imágenes. El recorrido comprobó 27 páginas, cero errores JavaScript, cero recursos estáticos fallidos y ausencia de desbordamiento horizontal del documento; las tablas móviles conservan desplazamiento propio.

| Captura | Evidencia visible |
| --- | --- |
| [Panel médico](01-panel-medico.png) | Institución autorizada, indicadores y gráficas Highcharts con datos reales de las API |
| [Inventario](02-inventario.png) | Folios, grupos, estado, ubicación, caducidad, filtros y paginación |
| [Disponibilidad regional](03-disponibilidad.png) | Recursos minimizados de la región; consulta orientativa con caché Redis |
| [Órganos](04-organos.png) | Ofertas separadas por tipo; HLA documental e interpretación humana |
| [Compatibilidad](05-compatibilidad.png) | Evaluación conservada, versión y candidatos; detalle continúa debajo del área visible |
| [Traslado](06-traslado-custodia.png) | Estado aceptado, origen/destino y secuencia física; la custodia completa continúa debajo |
| [Monitoreo](07-monitoreo.png) | Servicios y verificaciones mediante API |
| [Inventario móvil](08-inventario-movil.png) | Formulario de filtros responsive y tabla con desplazamiento horizontal propio |

[Informe reproducible](browser.json) · [Script de comprobación](../../../../apps/web/tests/integrated_browser.cjs) · [Guía de operación](../../../../apps/web/README.md).

Estas capturas documentan un corte local académico. No prueban funcionamiento de la aplicación Android, despliegue en nube ni validación clínica. Las capturas anteriores del monolito se conservan en su directorio histórico.
