# Perfiles iOS renovados para la entrega — 17/11/2026

Después de que el usuario reautenticó su cuenta existente en Xcode, el segundo intento acotado aprobó ambas variantes iOS. Los perfiles renovados cubren el día 23 completo en Monterrey, cuyo límite de comprobación es `2026-11-24T06:00:00Z`.

| Variante | Vencimiento del perfil UTC | Instalación de este artefacto |
| --- | --- | --- |
| Red House | `2026-11-24T18:03:31Z` | No instalada |
| Red House Lab | `2026-11-24T18:03:22Z` | Actualización aprobada en el iPhone registrado |

Compilación y wrapper terminaron con salida 0. Las firmas estrictas, equipo, bundle, dispositivo autorizado, perfiles embebidos/caché y grupos Keychain fueron comprobados. No se crearon cuentas ni certificados nuevos. Los dos perfiles anteriores permanecen respaldados; el [primer intento fallido](../final-build-20261117/RESULTADOS.md) conserva su recibo y restauración originales.

Se reutilizaron los dos APK y las pruebas JVM aceptadas. Los frameworks normal/Lab conservan sus hashes del lote anterior; cambiaron los ejecutables firmados. El [resumen](resumen.json) identifica cada artefacto. Los archivos privados y el mapa de artefactos están en `.local/artifacts/mobile/profile-renewal-20261117-02/`.

`devicectl` instaló Lab como actualización del mismo bundle, sin desinstalar ni borrar datos. Este recibo no prueba aún apertura, recuperación de sesión, VoiceOver ni los recorridos de negocio del artefacto nuevo. Red House normal permanece sin actualizar en el teléfono. No se atribuye publicación en tienda ni distribución general: son perfiles de desarrollo para el dispositivo autorizado.
