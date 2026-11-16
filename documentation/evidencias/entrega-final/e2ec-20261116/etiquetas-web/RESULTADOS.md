# Etiquetas del linaje: ajuste posterior al E2E

Se añadieron únicamente dos usos del filtro existente `portal_html` en
`integration/lineage.html`: producto y estado del componente. El filtro ya
traduce `RBC`, `AVAILABLE` y `QUARANTINE` como «Eritrocitos», «Disponible» y
«Cuarentena». No cambian rutas, permisos, contratos ni lógica de inventario.

Validación local del 16/11/2026: el template real, sus macros, base y CSS se
renderizaron con dos filas sintéticas. Las comprobaciones de texto pasaron;
`time.datetime` conserva `2026-11-20T18:00:00+00:00` y la representación en
Monterrey es `20/11/2026 · 12:00`. Una captura Chrome de 1440×900 confirmó las
etiquetas legibles y ausencia de desbordamiento horizontal. La captura fue
inspeccionada visualmente y el navegador cerró al terminar.

- [Captura sintética](linaje-etiquetas-sinteticas.png).
- [Recibo y hashes de las fuentes renderizadas](render.json).
- Reproducción: ejecutar `render.py` con el entorno Python de servicios y después
  `node capture.cjs`, desde la raíz del repositorio. Chrome necesita el permiso
  local habitual para iniciar su proceso; no necesita servidor HTTP.

**Límite:** es una comprobación de presentación posterior e independiente del
E2E-C. No vuelve a probar autenticación, consultas reales, permisos, enlaces ni
persistencia. Usa un principal sintético y enlaces de vista previa; JavaScript
está desactivado y el navegador bloquea solicitudes HTTP/HTTPS. No se abrieron
bases, fixtures ni APIs. La evidencia funcional anterior se conserva sin cambios.

Se leyó la skill `ui-ux-pro-max`. Sus dos búsquedas dirigidas no ofrecieron una
regla específica pertinente para estos códigos; se mantuvo la presentación
existente y se aplicó su criterio general de consistencia y legibilidad.
