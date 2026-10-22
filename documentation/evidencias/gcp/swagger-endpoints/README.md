# Capturas reales de Swagger

[Abrir índice visual](index.html). Las imágenes son capturas nativas de Chrome de peticiones ejecutadas en Swagger UI contra el despliegue público GCP. No se generaron imágenes con IA ni se fabricaron respuestas.

Cobertura: **119/119 endpoints públicos con éxito**, **11 errores de autorización** y **130 PNG**. [Detalle verificable](coverage.json).

Por cada servicio se captura un endpoint protegido sin JWT y después con autorización. Los demás endpoints públicos se capturan únicamente con resultado exitoso. Método y ruta identifican cada operación; GET y POST de una misma ruta cuentan por separado.

Se ocultan credenciales, tokens y URLs firmadas. También se ocultan los ejemplos estáticos y el bloque Curl con credenciales; se conserva visible el código HTTP real. Los cuerpos de emisión/renovación de tokens y entrega de URLs firmadas se enmascaran para no publicar secretos.

Las rutas `/internal/v1/` están excluidas por la aclaración del usuario: este recorrido usa únicamente Swagger público, sin SSH. Los documentos Swagger se inventariaron en `inventory.json`; las capturas y sus fechas constan en `manifest.json`.

Las escrituras utilizan datos ficticios propios de esta ejecución, identificados como Swagger o por folios SW-. La preparación de relaciones y las transiciones adicionales también utiliza peticiones reales. Los checkpoints y las credenciales se conservan únicamente en `.local/swagger-capture`, fuera del expediente público.

Reproducción desde la raíz: instalar Playwright en un entorno privado, indicar `REDHOUSE_PLAYWRIGHT` si corresponde y ejecutar `node scripts/capture_swagger_endpoints.cjs`. Requiere Chrome, acceso HTTPS y la configuración privada de cuentas de demostración. El script reanuda usando su checkpoint; no es un comando de solo lectura. Reconstruir el índice con `python3 scripts/build_swagger_capture_index.py`.

| Servicio | Endpoints públicos | Éxitos | Errores |
| --- | ---: | ---: | ---: |
| identidad-acceso | 34 | 34 | 1 |
| donantes | 19 | 19 | 1 |
| receptores | 10 | 10 | 1 |
| inventario | 14 | 14 | 1 |
| compatibilidad | 4 | 4 | 1 |
| priorizacion-geografia | 10 | 10 | 1 |
| transporte | 13 | 13 | 1 |
| custodia | 1 | 1 | 1 |
| alertas | 2 | 2 | 1 |
| auditoria | 10 | 10 | 1 |
| monitoreo | 2 | 2 | 1 |
