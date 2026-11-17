# Catálogo físico vigente — 17/11/2026

La captura real READ ONLY confirmó **esquema 21, 117 tablas, 227 índices y doce servicios**. PostgreSQL fue el único motor iniciado; cerró en 2,043 segundos y conservó state.json. No se consultaron filas de negocio ni se aplicaron migraciones.

Los [metadatos](postgresql-physical.json), el [cierre](captura-operacion.json) y la [validación](validacion-catalogo.json) conservan el resultado. El cambio frente al corte del 14/11 es el índice parcial `shared_outbox_dispatch_order`; no se retiraron índices. Tablas únicas, columnas ordenadas y destinos de claves foráneas existentes comprobados.

El builder actualizó catálogo físico, modelo relacional y fichas desde los metadatos y contratos reales. Las fuentes Mermaid y los SVG permanecieron idénticos; no se repitió su render. La captura y las exportaciones del 14/11 conservan su alcance histórico. Word/PDF del nuevo corte y revisión editorial siguen pendientes.
