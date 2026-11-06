# Comprobación de etapa 01: backend y microservicios

**Veredicto: NO APTA PARA CONTINUAR.** Hay defectos del componente actual, además de dependencias externas y de etapas posteriores.

Este expediente archiva la auditoría entregada en el chat el **28 de octubre de 2026**, por solicitud posterior del usuario. Organiza toda la información para continuar sin depender del chat ni de archivos temporales. El archivado no implementa correcciones, ejecuta nuevas pruebas funcionales ni cambia el veredicto.

## Orden de lectura

1. [Informe, alcance y arquitectura](01_informe_y_arquitectura.md): fuentes auditadas, método, resultados, servicios, módulos, propietarios y persistencia.
2. [Matrices de requisitos](02_matrices_requisitos.md): BE-01 a BE-24, criterios transversales y TRACK-01 a TRACK-10, con los siete campos del protocolo.
3. [Hallazgos y plan de cierre](03_hallazgos_y_cierre.md): F1 a F11, ubicación del código, comportamiento observado, impacto, orden y aceptación pendiente.
4. [Evidencias y reproducción](04_evidencias_y_reproduccion.md): ejecuciones, comandos, pruebas concretas, límites y comprobación de integridad.
5. [Dependencias y reanudación](05_dependencias_y_reanudacion.md): pendientes de esta etapa, etapas posteriores, requisitos externos y encargos preparados para retomar.
6. [Evidencias originales](evidencias/README.md): copias íntegras de los ocho artefactos de la auditoría.

## Estado comprobado

- Fuentes: commit `8909baf8458dff797d40d15541c57c66c14ef964` **más cambios locales sin commit**; versión local **0.4.0**, API **v1**, esquema **11**.
- [Manifiesto original (archivo)](../../../documentation/evidencias/archivo/detalles-20261104.tar.gz): **3.105 archivos**, hash agregado SHA-256 `d7f5ec0024d6ce058616fee97973f28895c312a9c8d59e98db7a1eec63370184`.
- Regresión reconciliada: **321 casos distintos aprobados y 2 omitidos**, de 323 recolectados. Hubo varias ejecuciones superpuestas, no una única corrida completa aprobada.
- Omisiones: GCS real sin bucket/ADC de prueba; recorrido de navegador no activado.
- Arquitectura: **24 responsabilidades, 11 servicios independientes, 18 módulos Python añadidos**, sin servicios nuevos. Réplicas desplegadas actualmente: **NO VERIFICADO**; se probaron dos procesos WSS temporales.
- No se modificaron las fuentes auditadas, la base habitual ni sus datos durante la comprobación. Antes de archivar se volvió a verificar que los 3.105 archivos seguían coincidiendo.
- Este archivado añade documentación y una referencia en `PROJECT_STATUS.md`. Esa referencia es posterior a la auditoría; el manifiesto original conserva el estado anterior y no se reescribe para ocultar la diferencia documental.

## Bloqueos

| Grupo | Hallazgos | Qué impide cerrar |
| --- | --- | --- |
| Integridad y revisión | F1, F2, F3, F7 | Destinos incompatibles, dictámenes que no caducan ante resultados corregidos, custodia opcional y auditoría/historia incompletas |
| Rastreo | F4, F5, F6 | Autorización durante replay, entrada paralela y recuperación histórica fuera de ventana |
| Funciones y contratos | F8, F9, F11 | Gestión de roles, reportes y consultas nuevas incompletos |
| Comprobación obligatoria | F10 | Caída de una réplica API y de todas sus réplicas no demostrada |

Las pruebas aprobadas no contradicen los hallazgos: las variantes defectuosas no están cubiertas por las aserciones existentes. Los casos propuestos para cerrarlas **no se ejecutaron ni se implementaron durante la auditoría**.

La infraestructura de HLA no equivale a evaluación detallada ni aprobación clínica. El software GPS se probó con simulador y WSS real; **GPS físico pendiente**. Mapas y aplicaciones consumidoras no se cuentan como implementados por existir contratos.

**NO APTA PARA CONTINUAR**
