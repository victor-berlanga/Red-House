# Documentación

Los documentos se organizan por su función y formato. Haber sido elaborados en el primer parcial no vuelve obsoletos el análisis, los requisitos ni la planificación del semestre. El [estado del proyecto](../PROJECT_STATUS.md) distingue lo implementado de lo pendiente.

## Análisis y planificación del semestre

Estas fuentes permanecen activas como referencia de alcance. Sus fases son las del plan original; no certifican que cada requisito esté implementado. Las reglas clínicas y las hipótesis institucionales conservan sus condiciones de validación.

| Tema | Fuente Markdown | Edición Word |
| --- | --- | --- |
| Problema, objetivos y alcance | [Análisis](markdowns/Analisis_del_problema.md) | [Word](docx/Analisis_del_problema.docx) |
| Requisitos funcionales y no funcionales | [Requisitos](markdowns/Requerimientos_funcionales_y_no_funcionales.md) | [Word](docx/Requerimientos_funcionales_y_no_funcionales.docx) |
| Historias y criterios de aceptación | [Historias](markdowns/Historias_de_usuario.md) | [Word](docx/Historias_de_usuario.docx) |
| Interacciones y procesos | [Casos de uso](markdowns/Casos_de_uso.md) | [Word](docx/Casos_de_uso.docx) |
| Relación entre requisitos y verificación | [Trazabilidad](markdowns/Matriz_de_trazabilidad.md) | [Word](docx/Matriz_de_trazabilidad.docx) |
| Perfiles y autorización previstos | [Permisos](markdowns/Matriz_de_perfiles_y_permisos.md) | [Word](docx/Matriz_de_perfiles_y_permisos.docx) |
| Restricciones del negocio | [Reglas](markdowns/Reglas_de_negocio.md) | [Word](docx/Reglas_de_negocio.docx) |
| Fundamentos tecnológicos | [Tecnologías](markdowns/Tecnologias.md) | [Word](docx/Tecnologias.docx) |
| Arquitectura objetivo del semestre | [Diseño arquitectónico](markdowns/Diseno_arquitectonico.md) | [Word](docx/Diseno_arquitectonico.docx) |
| Etapas, dependencias y entregables | [Plan de trabajo](markdowns/Plan_de_trabajo.md) | [Word](docx/Plan_de_trabajo.docx) |
| Paquetes de trabajo y criterios de cierre | [Backlog](markdowns/Sprint_backlog.md) | [Word](docx/Sprint_backlog.docx) |

El backlog conserva el estado registrado al cierre del primer parcial; el avance posterior está en `PROJECT_STATUS.md`. No se declaran paquetes completos por el solo hecho de que existan algunos de sus componentes. Las ediciones Word conservan el contenido y formato de la línea base con su aviso de alcance actualizado; Markdown es la fuente de mantenimiento, no se presume sincronización editorial completa entre formatos.

## Diseño de datos y sistema implementado

| Tema | Documento |
| --- | --- |
| Normalización y diseño lógico académico | [Modelos 0FN–4FN](database-diagrams/README.md) |
| Arquitectura ejecutable y responsabilidades | [Arquitectura](markdowns/Arquitectura.md) |
| Base compartida objetivo y cambios respecto de main | [Esquema compartido](markdowns/Esquema_compartido.md) |
| Bases, migraciones y persistencia | [Datos y persistencia](markdowns/Datos_y_persistencia.md) |
| Preparación y operación | [Instalación y operación](markdowns/Instalacion_y_operacion.md) |
| Portal y contratos HTTP | [Integración web](markdowns/Integracion_web.md) |
| Algoritmos y límites | [Algoritmos](markdowns/Algoritmos.md) |
| Pruebas y resultados | [Validación](markdowns/Pruebas_y_validacion.md) |
| Matriz de roles con fecha de corte | [Excel](excel/Matriz_Roles_Permisos_Red_House.xlsx) |

## Segundo parcial: implementación 0.3.0

- [Reporte técnico integral](markdowns/Reporte_tecnico_segundo_parcial.md), con arquitectura, procesos, requisitos y decisiones.
- [Fichas de los once servicios](segundo-parcial/Fichas_microservicios.md) y [modelo físico PostgreSQL](segundo-parcial/Modelo_fisico.md).
- [Diagramas actuales](segundo-parcial/diagramas/), incluida la relación física completa en SVG ampliable.
- [Matriz de cumplimiento y fallos](markdowns/Cierre_segundo_parcial.md), [resultados](evidencias/segundo-parcial/RESULTADOS.md) y [expediente HTTP por endpoint](evidencias/segundo-parcial/http/index.html).
- [Instalación Docker, respaldo y restauración](../deployment/README.md) y [guion presencial/video](../stuff/presentacion/Guion_segundo_parcial.md).
- [VM GCP, túnel SSH y administración](../deployment/gcp/README.md), con [resultados del despliegue](evidencias/gcp/RESULTADOS.md).
- Ediciones de entrega: [Reporte Word](docx/Reporte_tecnico_segundo_parcial.docx), [Reporte PDF](pdf/Reporte_tecnico_segundo_parcial.pdf), [modelo físico Word](docx/Modelo_fisico_PostgreSQL.docx) y [modelo físico PDF](pdf/Modelo_fisico_PostgreSQL.pdf).

## Entregas anteriores

La [revisión del segundo parcial](markdowns/Revision_segundo_parcial.md) conserva el diagnóstico del 14/10/2026 y enlaza la matriz vigente. Sus faltantes originales no describen el cierre actual.

El [historial](historial/README.md) conserva resultados fechados y documentos de implementaciones anteriores. Las fuentes de planificación del semestre mantienen su fecha de corte; el informe integral 0.3.0 y sus evidencias describen el incremento actual.

Actualizar el documento correspondiente a cada tema; no crear un documento nuevo por conversación. Un cambio de implementación puede requerir revisar una sección sin retirar todo el documento de planificación.
