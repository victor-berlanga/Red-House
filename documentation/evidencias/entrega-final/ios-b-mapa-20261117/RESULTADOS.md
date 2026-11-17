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

## Publicación manual nativa iOS y confirmación derivada

Esta consolidación no ejecuta otra prueba. Se compone la confirmación humana del mensaje «Ubicación guardada para este traslado» durante el caso B con el único punto IOS persistido, su mismo identificador recibido en vivo por web/Qt y la revisión del código correspondiente al artefacto Lab instalado. Los tres archivos móviles revisados coinciden exactamente con el manifiesto de fuentes del build; el mapa de artefactos de la renovación conserva la identidad del ejecutable y del framework instalados.

| Huella del corte Lab instalado | SHA-256 completo |
|---|---|
| Ejecutable `org.redhouse.mobile.lab` | `111a94fdd024be80c76279e89078214006a66d5f913a026657d0693b88f63097` |
| Framework compartido Lab | `301757062ade339eabdadbf8aba816a46d9b3acf2b5893177d4da5b190dcf015` |
| `TransportScreen.kt` | `137afdb8d2cbc4f99709c3596568a76c4aec3e910880afd84ae618b300027196` |
| `MobileRepository.kt` | `630a893812dbdf93b4372c18a82b85861fd29cda948e98a91a8939b087deff56` |
| `Tracking.kt` | `25ca167f9c6ed61a06f75d38172bc980d93ac48a829608c1b89be23d5dadaf40` |

El recorrido revisado es el siguiente:

- `TransportScreen.kt:248–250` usa `MobileRepository.startTracking/stopTracking` para autorizar o detener la sesión; `MobileRepository.kt:156–161` realiza esos comandos HTTP de autorización, no una publicación alternativa de la posición.
- `TransportScreen.kt:252–260` habilita «Capturar y publicar ubicación» con tarea autorizada y conexión viva. Llama directamente a `Tracking.publish`; solo después de que retorna muestra el mensaje confirmado por el usuario.
- `Tracking.kt:49–58` abre `wss://…/ws/v1/tracking/json`, autentica y suscribe. `Tracking.kt:113–122` envía `position.publish` por ese socket y espera como máximo diez segundos. No contiene fallback HTTP para publicar posiciones.
- `Tracking.kt:86–88` completa la espera únicamente cuando recibe `position.ack` con el `event_id` pendiente y estado `PERSISTED_SQL`. En servidor, `ms_transporte/tracking_socket.py:154–167` responde con ese ACK después de retornar `tracking.publish`; `ms_transporte/tracking.py:194–223` conserva el commit SQL anterior al retorno.

**Criterio cubierto:** publicación manual positiva desde iPhone físico por WSS y consumo de un ACK válido por la aplicación, como conclusión derivada del camino exclusivo de código pineado y las observaciones humanas/SQL/mapas existentes. La inferencia del ACK validado no es una captura de su frame ni una medición de su tiempo. Los observadores sí conservaron sus propios frames `position.updated`, como se describió arriba.

**Criterios no cubiertos por esta derivación:** latencia captura–ACK del teléfono, precisión física del sensor, inspección específica del marcador/zoom del mapa nativo iOS, envío periódico, interrupción/suspensión/cierre forzado, reconexión o negativos nativos. Los FAIL históricos y sus límites permanecen iguales. Esta cobertura no transforma los ensayos comunes/peer en ejecuciones nativas ni acredita Nginx/GCP.
