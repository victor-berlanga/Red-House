# Estado vigente de Red House

Actualizado: **14 de octubre de 2026**. Leer junto con `AGENTS.md` y el [índice documental](documentation/README.md). El historial detallado está separado del estado actual.

## Sistema actual

- `apps/web/`: portal Flask/Jinja2 que consume HTTP. El backend SQL histórico y sus instaladores fueron retirados; no hay doble escritura ni fallback local.
- `apps/services/`: diez microservicios y Monitoreo, con contratos JSON/XML, JWT, Redis, PostgreSQL y MongoDB.
- PostgreSQL conserva once bases persistentes con propietarios separados. MongoDB conserva documentos/proyecciones; Redis mantiene sesiones y datos temporales. La web conserva sesiones técnicas cifradas en SQLite privado.
- La carga regional es ficticia, pero sus operaciones y almacenamiento son reales. No se reinicializa al arrancar. Las reglas de compatibilidad y priorización no sustituyen la revisión médica.
- Android, escritorio, Docker y GCP permanecen en una etapa posterior; no se eligieron nuevas tecnologías cliente.

## Operación

Desde la raíz: `bash install.sh`, `bash start.sh`, `bash components.sh estado` y `bash stop.sh`. Los BAT de Windows utilizan WSL/Ubuntu; no son un port nativo.

El entorno predeterminado es `.local/runtime/`, privado y excluido de Git. El origen del traslado y los respaldos previos a las migraciones se conservaron. No ejecutar simultáneamente copias del mismo entorno. Portal: http://127.0.0.1:5050.

[Instalación y diagnóstico](documentation/markdowns/Instalacion_y_operacion.md) · [Datos y migraciones](documentation/markdowns/Datos_y_persistencia.md) · [Mapa de bases](data/database/README.md).

## Reorganización y validación

- Directorios principales `apps/`, `data/`, `documentation/` y `stuff/` conservados como hermanos. Análisis, requisitos, planificación semestral y modelos lógicos conservados en sus carpetas por formato; guías vigentes consolidadas. Entregas de implementaciones anteriores, bitácora y resultados agrupados en `documentation/historial/`.
- Rutas web, lanzadores, requisitos, CI, generadores y contratos actualizados. Identificadores redundantes normalizados con migraciones, conservando auditoría y cadenas firmadas.
- 39 pruebas del lanzador aprobadas; Chrome recorrió 51 páginas sin errores registrados. Once servicios y portal respondieron HTTP 200 con los registros regionales conservados; 18 cadenas de custodia verificadas.
- Comparación de 111 tablas durante la migración: ninguna fila perdida ni cambio inesperado; usuarios e historiales preservados.
- Regresión final: **164 pruebas aprobadas**, cero fallos/errores/omisiones, 597.68 s. Ciclo de vida real del lanzador: **14 comprobaciones aprobadas**. Enlaces, contratos, sintaxis y formato verificados.

[Criterios, cambios, resultados y límites de esta entrega](documentation/historial/2026-10-14/REORGANIZACION.md). [Historial anterior](documentation/historial/README.md).

## Pendientes

- Validación clínica/normativa de reglas, HLA, elegibilidad, asignación, retención y acceso institucional.
- Agenda por sede/hora, recuperación de acceso, email/push y administración institucional definitiva.
- Bucket GCS real, archivos grandes, firmas y fallos de nube.
- Android, escritorio XML, contenedores, HTTPS, GCP, supervisión y operación productiva.
- Carga sostenida, saturación, alta disponibilidad y ejecución de CI remoto. Windows/WSL y Ubuntu completos no están certificados por las pruebas de este Mac.
- Diagramas físicos actuales por servicio y nueva edición del reporte integral Word/PDF para el sistema integrado. Los modelos 0FN–4FN y las once ediciones Word de planificación siguen siendo referencias del semestre; el reporte del monolito permanece como antecedente.

## Revisión documental del 14 de octubre

Se restituyeron once documentos de planificación con sus once Word y diez archivos de diseño/normalización. Avisos de alcance, índices y enlaces corregidos. Verificación: cero enlaces locales rotos, once Word íntegros y validador de normalización aprobado con 49 diagramas. El backlog conserva explícitamente su corte original; no es un tablero actualizado de ejecución.

## Revisión de la entrega del segundo parcial (14 de octubre)

Se contrastó el enunciado externo `entregaSegundoParcial.txt` (entrega 22/10) con el árbol de trabajo, contratos, código y evidencia. [Informe de cumplimiento y pendientes](documentation/markdowns/Revision_segundo_parcial.md). Docker es obligatorio para esta entrega, aunque la implementación actual y las guías lo mantienen pendiente. También faltan actualizaciones/pipelines funcionales MongoDB, expediente exhaustivo request/response, reporte integral vigente, evidencia de archivos reales y presentación/YouTube; se debe resolver la interpretación de independencia de la web. Android y escritorio están excluidos expresamente del parcial.

Criterio de aceptación de esta revisión: cubrir los apartados del enunciado, distinguir implementación de evidencia y proponer cierres verificables. Evidencia nueva: 19 pruebas unitarias/contratos/algoritmos aprobadas en 32.95 s, [JUnit](documentation/historial/2026-10-14/resultados/revision-segundo-parcial-unit.xml); once servicios respondieron 200 en readiness, Swagger y OpenAPI usando sus puertos reales, y la página pública del portal respondió 200. Los 164 casos de regresión son evidencia previa, no una nueva ejecución. Se contabilizaron 127 operaciones OpenAPI (107 API y 20 internas). No se cambió código funcional ni se declara terminado el parcial. Riesgo: la evidencia y las pruebas locales actuales no acreditan todavía el futuro despliegue Docker.

## Mantenimiento

Actualizar el documento vigente de cada tema. Registrar cambios y resultados por entrega en el historial, sin crear un documento nuevo por conversación. Conservar las migraciones y pruebas necesarias; retirar duplicados comprobados. No publicar secretos ni confundir un resultado histórico con una verificación actual.
