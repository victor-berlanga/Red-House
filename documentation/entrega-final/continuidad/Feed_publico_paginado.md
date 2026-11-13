# Feed público paginado

Estado: backend JSON/XML verificado en laboratorio aislado: dos casos aprobados en 70,92 s. [JUnit, fuentes y límites](../../evidencias/entrega-final/feed-publico-20261113/RESULTADOS.md). No cierra CONT-06 nativo ni acredita despliegue.

`GET /api/v1/public/campaign-feed` publica únicamente título, inicio, fin, sede e información expresamente autorizada de campañas abiertas y vigentes. No expone expedientes, usuarios, instituciones, capacidad ni identificadores privados. Conserva `/api/v1/public/campaigns` para consumidores existentes.

El nuevo contrato acepta `page` (1–100000), `page_size` (1–100, predeterminado 20), `q` (hasta 100 caracteres, título o sede), `from_at` inclusivo y `until_at` exclusivo sobre el inicio de la campaña. Las fechas requieren zona horaria. El orden es inicio e identificador interno como desempate, sin publicar ese identificador. La respuesta `data` contiene `items`, `page`, `page_size` y `total`; usa el sobre habitual con correlación, servicio y versión. Se publica en OpenAPI y en `public_campaign_feed.response.json`, para JSON y XML.

La consulta parametrizada obtiene filas y total en una sola sentencia PostgreSQL para compartir snapshot. Rechaza parámetros desconocidos o duplicados, ventanas invertidas, paginación fuera de límites y caracteres de control. La búsqueda trata `%`, `_` y `\` como texto literal. Usa el límite de consumo público existente. La paginación por desplazamiento no congela el conjunto entre peticiones: publicaciones concurrentes pueden cambiar el total o mover registros entre páginas; cada página es coherente en su propia consulta.

Criterios de aceptación: recorrer 105 campañas sin truncamiento ni duplicados en un conjunto estable, conservar el orden, excluir campañas privadas/cerradas/canceladas/vencidas, validar ambos formatos y salida minimizada, comprobar página final/vacía, búsqueda literal y fechas, rechazar entradas inválidas y conservar el endpoint anterior. La preparación masiva sintética mediante SQL no acredita el flujo de creación de campañas. La interfaz móvil debe pedir cada página al servidor, conservar filtros y compartir solo estos cinco campos públicos.

Pendientes: recorrido nativo con más de 100 registros, revisión visual del artefacto actual y publicación en la VM Red House autorizada.
