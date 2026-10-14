# Mapa de bases de datos

Un servidor PostgreSQL local contiene once bases reales y persistentes. Cada microservicio accede únicamente a su base mediante su credencial de ejecución.

| Propietario | Base | Migraciones |
| --- | --- | --- |
| identidad_acceso | `rh_identidad_acceso` | [SQL](../../apps/services/ms_identidad_acceso/migrations/) |
| donantes | `rh_donantes` | [SQL](../../apps/services/ms_donantes/migrations/) |
| receptores | `rh_receptores` | [SQL](../../apps/services/ms_receptores/migrations/) |
| inventario | `rh_inventario` | [SQL](../../apps/services/ms_inventario/migrations/) |
| compatibilidad | `rh_compatibilidad` | [SQL](../../apps/services/ms_compatibilidad/migrations/) |
| priorizacion_geografia | `rh_priorizacion_geografia` | [SQL](../../apps/services/ms_priorizacion_geografia/migrations/) |
| transporte | `rh_transporte` | [SQL](../../apps/services/ms_transporte/migrations/) |
| custodia | `rh_custodia` | [SQL](../../apps/services/ms_custodia/migrations/) |
| alertas | `rh_alertas` | [SQL](../../apps/services/ms_alertas/migrations/) |
| auditoria | `rh_auditoria` | [SQL](../../apps/services/ms_auditoria/migrations/) |
| monitoreo | `rh_monitoreo` | [SQL](../../apps/services/servicio_monitoreo/migrations/) |

La infraestructura técnica común se define en [schema.py](../../apps/services/redhouse/schema.py) y [migrations.py](../../apps/services/redhouse/migrations.py). No hay un `schema.sql` central para el sistema actual.

El [esquema del primer parcial](../../documentation/historial/primer-parcial/database/schema.sql) se conserva únicamente como antecedente; no debe ejecutarse para instalar el sistema vigente.
