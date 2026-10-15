# Diseño y modelos de datos

Los modelos [0FN](Modelo_0FN.md), [1FN](Modelo_1FN.md), [2FN](Modelo_2FN.md), [3FN](Modelo_3FN.md), [4FN](Modelo_4FN.md) y su [trazabilidad](Trazabilidad_0FN_4FN.md) forman parte del diseño lógico académico del semestre. Se conservan aquí por su valor para el modelado y la justificación de dependencias; no son un esquema físico instalado ni una validación clínica.

`normalization/` contiene las fuentes, el generador y el validador de ese ejercicio. Desde la raíz:

```sh
node documentation/database-diagrams/normalization/validate.mjs
```

La implementación nueva utiliza una base compartida con permisos por servicio. El [mapa de bases y migraciones](../../data/database/README.md) identifica el [esquema físico SQL compartido](../../data/database/schema.sql) y su generador. La [distribución de almacenamiento](../markdowns/Datos_y_persistencia.md) explica PostgreSQL, MongoDB, Redis y las sesiones técnicas. Los diagramas físicos por servicio siguen pendientes: las 169 relaciones del diseño lógico no deben interpretarse como tablas desplegadas.

El [esquema SQL del monolito](../historial/primer-parcial/database/README.md) sí pertenece a una implementación retirada y permanece en el historial.

La arquitectura objetivo aprobada el 15 de octubre usa una [base compartida basada en main](../markdowns/Esquema_compartido.md), cuyo [SQL consolidado](../../data/database/schema.sql) está preparado. La adaptación ejecutable usa vistas por servicio sobre tablas comunes; el estado de migración del entorno está en PROJECT_STATUS.md. Los modelos académicos 0FN–4FN tampoco sustituyen este nuevo esquema físico.
