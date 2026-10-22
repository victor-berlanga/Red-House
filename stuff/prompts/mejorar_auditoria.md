# Mejora del módulo de auditoría

Mejora el módulo de auditoría de Red House para que permita investigar operaciones y dar seguimiento a hallazgos.

Lee `AGENTS.md` y `PROJECT_STATUS.md`. Revisa los eventos, permisos y contratos existentes antes de modificar código.

Implementa:

1. **Acciones descriptivas.** Sustituye “Actividad registrada” por acciones concretas: inicio de sesión, creación, modificación, desactivación, cancelación, autorización, recolección o entrega. Usa el significado real del evento; no inventes datos históricos ausentes.

2. **Listado útil.** Muestra acción, responsable, institución, recurso o folio, fecha de ejecución y resultado. Conserva la fecha de centralización en el detalle.

3. **Filtros combinables.** Permite filtrar por fechas, categoría, acción, responsable, institución, recurso y resultado. Incluye controles para mostrar u ocultar:
   - Operaciones de negocio.
   - Decisiones y autorizaciones.
   - Incidentes de seguridad.
   - Sesiones.
   - Consultas de información.

   Muestra inicialmente las primeras tres categorías. Conserva sesiones y consultas, pero ocúltalas inicialmente. Separa los eventos técnicos rutinarios de la consulta operativa.

4. **Detalle y trazabilidad.** Presenta responsable, rol e institución registrados al ejecutar la acción, recurso afectado, resultado, motivo, cambios relevantes y correlación. Permite consultar eventos relacionados y reconstruir la secuencia de una solicitud, unidad o traslado, respetando permisos.

5. **Exportación coherente.** Aplica los mismos filtros al listado, contador, paginación y CSV. Conserva “Exportar página” y agrega “Exportar resultados filtrados”, con límites documentados. Mantén los filtros al navegar y regresar del detalle.

6. **Seguimiento de hallazgos.** Permite registrar un hallazgo vinculado con eventos o recursos, con descripción, evidencia, prioridad, responsable de atención y estados: abierto, en atención, pendiente de verificación y cerrado. Registra acciones correctivas y exige evidencia y motivo para cerrarlo. Define los permisos de cada transición.

El auditor debe consultar únicamente su ámbito autorizado. No debe modificar eventos originales, inventarios ni decisiones clínicas. Los hallazgos y sus cambios deben conservar historial auditable.

Mantén la independencia del portal, los contratos versionados JSON/XML/XSD, JWT, autorización con Redis y despliegue Docker. Evita que consultar la bitácora genere un ciclo de eventos que sature la vista principal.

Verifica con pruebas la clasificación de eventos, filtros, exportaciones, permisos, trazabilidad y ciclo de hallazgos. Usa migraciones que conserven los datos existentes. Actualiza documentación y `PROJECT_STATUS.md` con cambios, resultados y pendientes.
