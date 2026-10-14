# Capturas esenciales de la retroalimentación — 27 de septiembre de 2026

Actualmente se conservan **13 capturas**: cada una aporta evidencia visual distinta de un requisito. Se retiraron 70 imágenes redundantes, pasos intermedios ya visibles en los historiales y pantallas generales sin evidencia específica.

Son capturas reales de Chrome/Playwright con datos ficticios persistidos en bases aisladas. Las cuatro capturas de receptor, compatibilidad sanguínea y ambas custodias se volvieron a tomar directamente en Chrome a 1440 × 1000 píxeles, desplazando la página para mostrar los resultados con el menú lateral fijo completo. Las demás mantienen su vista superior de escritorio. No se generó contenido ni se combinaron partes de distintas pantallas. Las vistas muestran únicamente la región indicada, no toda la página.

| Punto de la retroalimentación | Captura | Evidencia visible |
| --- | --- | --- |
| Instituciones y capacidades | [Institucion_capacidades](Institucion_capacidades.png) | Ficha institucional con tipo, ubicación, contacto y capacidades declaradas. |
| Donante y evaluación humana | [Donante_revision](Donante_revision.png) | Seguimiento del expediente y evaluación de elegibilidad registrada. |
| Donación, recolección y procesamiento | [Donacion_procesamiento](Donacion_procesamiento.png) | Seguimiento con recolección y procesamiento completados, estado de unidad liberada y vínculo al expediente del donante. |
| Receptor independiente | [Receptor_expediente](Receptor_expediente.png) | Expediente de receptor con institución, folio, identidad, ABO/Rh, restricciones, requerimiento, estudios y estado activo. |
| Solicitud, compatibilidad y prioridad sanguínea | [Compatibilidad_priorizacion](Compatibilidad_priorizacion.png) | Solicitud con cantidad, urgencia y ABO/Rh; versión del algoritmo y dos candidatos con origen, distancia, tiempo, caducidad y factores explicativos. |
| Asignación, traslado y custodia sanguínea | [Cadena_custodia](Cadena_custodia.png) | Seguimiento hasta recepción, origen, destino, autorización, vehículo, ETA y seis eventos de custodia completos hasta la aceptación. |
| Recepción y cierre de solicitud | [Solicitud_cerrada](Solicitud_cerrada.png) | Solicitud cerrada con una unidad recibida y cero unidades pendientes. |
| Auditoría transversal | [Auditoria_regional](Auditoria_regional.png) | Bitácora consultada por auditor con actor, fecha, operación, entidad y resultado. |
| Inventario independiente de órganos | [01_disponibilidad](01_disponibilidad.png) | Disponibilidad registrada de riñón, hígado y corazón, separada del inventario sanguíneo. |
| Candidatos y prioridad de órganos | [06_candidatos](06_candidatos.png) | Candidato con factores de urgencia, espera, distancia, tiempo, límite registrado y versión de reglas ilustrativas. |
| Estudios, HLA y revisión humana | [07_revision_humana](07_revision_humana.png) | Estudios de donante y receptor, HLA documental y dictamen favorable registrado por personal médico. |
| Asignación, traslado, custodia y recepción de órganos | [15_auditor](15_auditor.png) | Estado de recepción aceptada, origen, destino, vehículo, ETA y siete eventos completos desde la reserva autorizada hasta la recepción aceptada. |
| Restricción de acceso por perfil | [17_permisos](17_permisos.png) | Respuesta 403 a un acceso del auditor a una operación restringida. |

Las capturas muestran resultados visibles; por sí solas no prueban concurrencia, rollback, inmutabilidad ni todos los permisos. Esas propiedades se respaldan con las comprobaciones de servidor registradas en PROJECT_STATUS.md. HLA se registra e interpreta por personal humano; no se acredita compatibilidad clínica automática.

## Resultados

- Nuevas capturas de escritorio: dos recorridos aprobados en 46.10 s, con Chrome y PostgreSQL aislado; cuatro imágenes revisadas visualmente. Sustituyen los recortes anteriores de esos archivos.

- Regresión completa: **128 aprobadas**, sin fallos ni omisiones, en 271.75 s. Incluye Chrome y PostgreSQL.
- Después del ajuste de conservación de formularios rechazados: **10 pruebas de órganos aprobadas**, en 41.53 s, incluida una nueva prueba del error y el recorrido de navegador.
- Capturas adicionales de sangre (expediente receptor, capacidades institucionales y demanda activa): recorrido aprobado en 31.78 s.
- Las repeticiones dirigidas no se suman como pruebas distintas de la regresión.
- Instalación local: migración 004 probada en copia restaurada y aplicada; 46 tablas, cuentas y datos anteriores conservados.
- Límite: presentación académica, no validación médica, aceptación docente ni prueba de producción. HLA se registra y evalúa por personal humano; el orden de candidatos es operativo y ilustrativo.
