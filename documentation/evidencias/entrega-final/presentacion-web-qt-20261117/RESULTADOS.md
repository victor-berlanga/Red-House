# Presentación web y Qt: laboratorio, conservación y traslado — 17/11/2026

**Cuatro fuentes integradas, con evidencia sintética de presentación. El GET real de laboratorio sigue pendiente.** Este lote no repitió negocio, inició sesiones ni publicó en GCP. No cierra etapas de aceptación, capacidad ni empaquetado final.

| Cambio integrado | Comprobación existente | Límite |
| --- | --- | --- |
| Resultado de laboratorio web | La etiqueta «Resultado informado» sustituye «Contacto» únicamente en la vista de resultado; estados como REPORTED se traducen a «Reportado». [Plantilla real con datos sintéticos](laboratorio-sintetico.png). | Conserva el catálogo global de contacto, texto libre, estados desconocidos y autorización. Candidato original common SHA `9c667b6cdf52e95752cf4e7149b24cfc46209c369561e800955ab0c57fffb5a3`, ahora integrado sin cambiar sus bytes. Falta GET autenticado del monolito. |
| Evento de conservación web | `RESOURCE_COLD_QUARANTINE` muestra «Bloqueo por conservación». [Detalle sintético](evento-conservacion-sintetico.png). | La unidad de la imagen permanece «En tránsito»: la etiqueta del evento no inventa un estado QUARANTINE. Se conserva el fallback para otros eventos desconocidos. |
| Navegación de conservación web | [Página completa con menú desplazado](conservacion-organo-navegacion-sintetica.png): «Órganos y HLA» resaltado para ORGAN; sangre conserva Inventario sanguíneo. | Usa el ID de navegación `organos`, distinto del Blueprint `organs`. Datos sintéticos y plantillas/NAV/CSS reales; no es una consulta autenticada del caso anterior. |
| Detalle y preparación Qt | [Fechas locales](qt-fechas-locales-cancelado.png) y [motivo completo](qt-motivo-cancelado.png), dos diálogos sintéticos cancelados. | Salida/llegada reutilizan el helper de fecha local existente. Preparación amplía ventana y campos; no cambia el cuerpo XML, confirmación o reglas. Cero llamadas API y comandos. Reconstrucción del paquete macOS pendiente. |

Los cambios Qt son dos líneas de producto: presentación local de `departure_at`/`eta` en `shipment_context`, y tamaño/política de crecimiento en `prepare_shipment`. Los otros tres archivos son web: `common.py`, `presentation.py` y `conservation.py`. El [patch conjunto](cambios.patch) y el [resumen con huellas](resumen.json) identifican su alcance exacto.

## Verificación visual y fallos conservados

El render nuevo de detalle/conservación utilizó las plantillas reales, datos inventados y una instancia mínima para contexto de render, sin fábrica de aplicación, actor real, cliente, runtime, base de datos o sesión. Verificó etiqueta del evento, conservación del estado En tránsito, fallback desconocido y navegación ORGAN/BLOOD. No modifica datos del ensayo iOS B.

La primera ejecución de captura web guardó dos imágenes sintéticas con JavaScript desactivado y HTTP/HTTPS bloqueado. La etiqueta y el estado eran visibles, pero el enlace activo del menú quedaba bajo el pliegue de la barra lateral. Ese límite y sus recibos originales se conservan. Dirección autorizó una única captura adicional de la misma página de conservación, sin repetir render; `scrollIntoView` desplazó el menú hasta «Órganos y HLA», que ahora aparece resaltado y legible en la imagen enlazada.

El candidato common conserva sus dos fallos iniciales de preparación del render y su posterior aceptación sintética; no se atribuye a esta integración un nuevo GET real. Qt conserva el primer arranque sandbox con salida 134 y la captura posterior aprobada con ambos formularios cancelados. No se suman capturas o controles de render como pruebas funcionales del servidor.

Los bytes integrados de las dos correcciones nuevas web coincidieron con sus candidatos; common mantiene su SHA original y la fuente Qt coincide con el candidato revisado por dirección. Ningún cambio afecta contratos de negocio, reglas de conservación, tiempos, datos clínicos, permisos, esquema o traducción global de Contacto.

## Pendientes delimitados

- GET real del resultado de laboratorio en el monolito, con su cierre propio, antes de aceptar ese recorrido sobre la fuente integrada.
- Publicación posterior revisada: agregar únicamente `presentation.py` y `conservation.py` a la misma imagen web prevista para common; el paquete de reloj de custodia mantiene su alcance separado. No se preparó ni ejecutó una nueva publicación en este corte.
- Reconstrucción macOS y validaciones restantes de matrices. Los cierres transaccionales previos conservan sus fuentes/capturas originales; este lote no los reejecuta ni los reetiqueta como capturas posteriores a la corrección.
