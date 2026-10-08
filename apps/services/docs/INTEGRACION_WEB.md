# Integración de la web

El portal es un consumidor HTTP de los servicios: [operación, arquitectura y demostración](../../web-monolito01/INTEGRACION.md). Los servicios siguen ejecutándose sin depender de plantillas, sesiones internas ni conexiones de la web.

Se incorporaron contratos de consulta para indicadores autorizados, usuarios minimizados, detalle de recursos y procesamiento, historial de evaluaciones, rankings, propuestas y reservas. Cada contrato consulta únicamente la base de su propietario. Los filtros documentados se parametrizan, limitan búsqueda y validan enums/UUID; el total refleja el conjunto filtrado. Las proyecciones regionales de coordinación omiten identidad clínica. Los indicadores de solicitudes del coordinador son institucionales: no se reconstruyen relaciones mediante SQL contra otros servicios.

La web consume disponibilidad regional con caché Redis y revisa las operaciones pendientes antes de planificar. API v1, JWT, versiones, idempotencia, JSON/XML y seguridad de las llamadas internas mantienen los contratos anteriores. Los DTO nuevos se incluyen en OpenAPI y en los esquemas equivalentes de salida. No existe comunicación SQL directa web → bases de negocio, ni una doble escritura al monolito antiguo.

`scripts/seed_nuevo_leon.py` provisiona seis instituciones y crea la demostración por API, con perfiles reales. Su SQL se limita al provisionamiento explícito de identidades en un entorno nuevo; la lectura opcional de cuentas antiguas es de solo lectura. Restablecer límites con `restore` y reiniciar después de una carga. `scripts/integrated.py` gestiona web y entorno propio conjuntamente; `scripts/local.py` continúa disponible para operar solo servicios.
