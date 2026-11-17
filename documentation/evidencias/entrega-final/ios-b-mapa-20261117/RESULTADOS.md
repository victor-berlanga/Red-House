# iOS B: mismo punto en mapas Qt y web mediante WSS — 17/11/2026

PASS del tramo de mapas en vivo. Los dos observadores estaban autenticados y suscritos antes de la publicación manual del usuario: Qt22:01:05,257UTC y web22:01:26,960UTC, ambos con cursor0 y baseline vacío. Recibieron el mismo evento `0b868dd5-687e-4f4d-865d-a88051ee060c`, cursor1, mediante `position.updated` en generación1. Ambos recibos passed/live_event=true, sin renovación ni snapshot de recuperación. Observadores y selector terminaron exit0 según los cierres de ejecución.

El selector eligió el primer punto IOS válido posterior a ambas suscripciones mediante SELECT READ ONLY. Se etiqueta SERVER_OBSERVED; no se capturó el ACK bruto del iPhone. Los observadores no publicaron ubicaciones. Sus oráculos coinciden: una fila SQL, un documento MongoDB y un evento de auditoría, relacionados con la proyección correcta. Dos familias observadoras propias cerradas SQL/Redis, una por cliente; fuentes antes/después idénticas y cero errores JavaScript.

Dirección abrió las dos capturas reales: marcador y textos correctos, encuadre regional en Qt y urbano en web. Imágenes, frames y coordenadas permanecen privados; resumen.json publica únicamente metadatos y hashes de procedencia.

| Medición puntual | Resultado | Origen y límite |
|---|---:|---|
| Qt: recepción observada a primer callback tras pintura | 31,39ms | time.monotonic del host, desde señal observada por ObservedSocket hasta primer callback programado después del despacho QEvent.Paint. No mide presentación física de pantalla. |
| Web: aviso de frame a callback del observador | 18,11ms | performance.now de Node entre Playwright framereceived y llegada a exposeBinding. Incluye planificación/instrumentación entre procesos; no equivale a latencia física de pintura. |
| Web: recepción del servidor a requestAnimationFrame | 416ms | Métrica receive_to_map_ms de tracking.js: Date.now del navegador menos received_at del servidor. Incluye entrega y planificación, y depende de la comparación de relojes. No empieza en la captura GPS ni en un ACK del teléfono. |

Primer callback conservado por(event_id,generación), sin sustituirlo al centrar el mapa o repintar tiles. Los tiempos del recibo concuerdan con los frames privados. Es una sola muestra; no se afirma p95, capacidad ni garantía de latencia. Las tres mediciones tienen orígenes distintos y no se suman.

Entorno LOCAL con gateway TLS/WSS Werkzeug, monolito web y consumidores XML en Qt/JSON en web. Este ensayo no pasó por Nginx ni acredita despliegue GCP. Conserva su evidencia propia y no modifica los FAIL anteriores de mapas iOS A. El resultado no cierra toda la etapa07 ni los restantes pasos de custodia del flujo iOS B.
