# Catálogo físico vigente — 17/11/2026

La captura real READ ONLY confirmó **esquema 21, 117 tablas, 227 índices y doce servicios**. PostgreSQL fue el único motor iniciado; cerró en 2,043 segundos y conservó state.json. No se consultaron filas de negocio ni se aplicaron migraciones.

Los [metadatos](postgresql-physical.json), el [cierre](captura-operacion.json) y la [validación](validacion-catalogo.json) conservan el resultado. El cambio frente al corte del 14/11 es el índice parcial `shared_outbox_dispatch_order`; no se retiraron índices. Tablas únicas, columnas ordenadas y destinos de claves foráneas existentes comprobados.

El builder actualizó catálogo físico, modelo relacional y fichas desde los metadatos y contratos reales. Las fuentes Mermaid y los SVG permanecieron idénticos; no se repitió su render. La captura y las exportaciones del 14/11 conservan su alcance histórico.

## Exportación del catálogo físico

[Word](../../../docx/Modelo_fisico_PostgreSQL_final.docx) y [PDF de 74 páginas Carta](../../../pdf/Modelo_fisico_PostgreSQL_final.pdf) aprobados para el corte del 17/11. Word conserva las 117 tablas y su ZIP íntegro. El PDF contiene los 117 títulos de tabla, folios consecutivos y el índice parcial nuevo en la página 65. La comprobación de texto cubrió las 74 páginas y no encontró palabras fuera de la página.

Se inspeccionaron visualmente las páginas 1, 65, 71, 72 y 74 del PDF. La muestra cubrió los conteos, la definición del índice nuevo, dos tablas de seguimiento, sus claves foráneas y las referencias finales. La [validación de la exportación](validacion-exportacion.json) conserva SHA-256, tamaños, salidas y alcance. LibreOffice emitió una advertencia de caché de Fontconfig y convirtió con salida 0. Se corrigió el selector de la muestra visual tras el primer fallo de búsqueda. Word y PDF se generaron una sola vez.

El informe técnico principal conserva pendiente su propia exportación y revisión editorial.
