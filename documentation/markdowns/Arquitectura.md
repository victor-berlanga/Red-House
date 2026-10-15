# Decisiones de arquitectura — servicios 0.2.0

Alcance inicial aprobado el 7 de octubre de 2026: diez servicios más monitoreo, desarrollados y probados antes de integrar clientes, Redis y MongoDB permitidos, Docker pospuesto. En el siguiente incremento autorizado se integró el portal Flask como consumidor HTTP; las API siguen siendo independientes de sus plantillas y sesiones. [Arquitectura y operación web](../../apps/web/README.md).

| Decisión | Implementación y efecto |
| --- | --- |
| Base compartida y permisos por servicio | Una base `red_house`, tablas comunes y claves foráneas entre módulos. Vistas `access_*` sin copias físicas; cada credencial conserva permisos limitados. |
| Compartir infraestructura, no reglas | `redhouse` contiene autenticación, codecs, contratos, persistencia y eventos; cada módulo contiene sus reglas y rutas. |
| Consistencia local fuerte | Transacción SQL de negocio, evento local y outbox. Restricciones únicas y bloqueos de fila. |
| Coordinación explícita | Retención en Receptores → reserva local en Inventario → confirmación. Resultado pendiente durable y compensación limitada. |
| Fallos parciales | Liveness separado de readiness; API con 503 seguro, reintentos de eventos, circuito por destinatario dentro del lote. |
| Custodia separada | Transporte es dueño de estados y hechos físicos; Custodia conserva su secuencia inmutable. MongoDB recibe proyecciones sin doble escritura directa. |
| Auditoría eventual | Registro local obligatorio transaccional, centralización deduplicada; fallar la centralización conserva pendientes. |
| Seguridad distribuida | RS256 solo firmado por Identidad; Redis activo/versionado; Ed25519 por servicio y JWT delegado en consultas interactivas. |
| Sangre y órganos | Tipo, componente, solicitudes y restricciones diferenciados; las reglas clínicas siguen siendo ilustrativas o humanas. |
| Caché orientativa | Datos autorizados por usuario/institución/región/rol/ruta/filtros; inventario/resumen 10 s, disponibilidad 15 s, catálogos 30 s. Generación SQL transaccional; reserva omite caché. |
| MongoDB justificado | Transporte: telemetría/documentos; Custodia: proyección de historia; Auditoría: eventos documentales; Monitoreo: sondeos persistidos primero en MongoDB para observar fallas de PostgreSQL. PostgreSQL conserva los compromisos transaccionales. |
| Contratos | API v1, JSON y XML, XSD de entrada y envoltura de salida, OpenAPI con esquemas, ejemplos y errores. |

## Reserva y fallos

1. Médico del destino solicita una reserva con evaluación y dictamen favorable.
2. Inventario registra una operación por usuario e Idempotency-Key. Las repeticiones con distinto cuerpo se rechazan.
3. Receptores bloquea solicitud y receptor; verifica versiones, estado y cantidad retenida/confirmada/recibida; registra un grant por operación.
4. Inventario bloquea operación y recurso; revalida estado, versión y viabilidad temporal con la ruta capturada, y registra reserva y evento en una sola transacción.
5. Confirma el grant por contrato; una respuesta perdida mantiene estado pendiente que puede consultarse y reanudarse.
6. Un conflicto local libera el grant; si la liberación no responde, queda ROLLBACK_PENDING. Una interrupción entre grant y commit puede compensarse después de 60 segundos, siempre que no exista reserva local.

Las operaciones sin grant ni reserva requieren reintento autorizado; no se deduce fracaso a partir de un timeout. Los tiempos de espera de las llamadas son conexión 1 s/lectura 3 s. El worker no almacena JWT de usuarios.

El ciclo de una ruta es independiente; Inventario revalida su versión antes de reservar y Transporte antes de planificar. No se promete congelación global de rutas ni simultaneidad ACID entre servicios. Cambios posteriores requieren revisión operativa; la aprobación clínica real y su protocolo institucional siguen pendientes.

## Traslado y recepción

La orden se guarda pendiente y se vincula exclusivamente a la reserva antes de permitir pasos físicos. Mientras no se confirme ese vínculo no se puede recolectar. Una reserva con orden vinculada solo puede cancelarse mediante Transporte, antes de recolección. Cada paso conserva su actor, razón, secuencia y evento local durable.

Los consumidores aplican eventos con inbox deduplicado. Inventario exige secuencia; recepción cambia el recurso a RECEIVED y su institución actual a destino, y emite el evento que confirma recepción del grant. Receptores cierra únicamente cuando toda la cantidad se recibió. La disponibilidad nunca reaparece por un fallo de custodia o notificación.

Una entrega física tardía puede registrarse como DELIVERED o incidencia. La aceptación ACCEPTED y el cierre de la solicitud se bloquean si el recurso ya caducó; no se inventa un plazo clínico nuevo. La recepción no equivale a liberación clínica. Los procesos de cuarentena posterior, transfusión y trasplante están fuera de este incremento y necesitan definición normativa.

## Límites técnicos

- El portal integrado utiliza datos nuevos en las bases de sus propietarios; la antigua base se conserva como referencia y no recibe doble escritura. Ocho cuentas y sus hashes se conservaron durante el provisionamiento inicial. Ese procedimiento histórico no forma parte del instalador actual.
- Los permisos regionales se restringen por `region_id`; expedientes clínicos por institución, y logística por asignación.
- Un hash encadenado detecta alteraciones del registro bajo el modelo de confianza; no certifica verdad física ni evita intervención de un administrador de infraestructura.
- SQL y MongoDB no contienen binarios. GCS tiene adaptador opcional, sin evidencia de operación en nube.
- No hay broker adicional ni dependencias AWS/Azure: el outbox se entrega mediante HTTP y workers locales.
- La instancia física compartida facilita pruebas, pero detener PostgreSQL afecta todas esas bases. El despliegue independiente de procesos no implica alta disponibilidad de infraestructura.

## Fuentes técnicas

El diseño de datos y consistencia se contrastó con [Microsoft: data considerations](https://learn.microsoft.com/en-us/azure/architecture/microservices/design/data-considerations), el registro de publicación con [AWS: transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) y la coordinación con [Microsoft: saga](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga). Estas fuentes describen patrones; no implican usar esos proveedores.

Referencias de implementación: [Flask](https://flask.palletsprojects.com/en/stable/api/), [PyJWT](https://pyjwt.readthedocs.io/en/stable/api.html), [Psycopg](https://www.psycopg.org/psycopg3/docs/basic/transactions.html), [Redis](https://redis.io/docs/latest/develop/clients/redis-py/), [PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/), [lxml](https://lxml.de/validation.html) y [OpenAPI/Swagger](https://swagger.io/docs/specification/v3_0/describing-request-body/describing-request-body/).

## Independencia de las entregas (8 de octubre)

Cada propietario mantiene `routes.py`, `queries.py`, sus modelos de entrada, `outputs.json` y `migrations/`. Las consultas de negocio y las definiciones de tablas no viven en una biblioteca central. `redhouse` contiene mecanismos técnicos comunes, sin importar dominios vecinos. Identidad es propietario de sedes, contactos, horarios, capacidades y ubicaciones; Inventario conserva referencias y las valida mediante HTTP.

`scripts/package_service.py` construye una carpeta que contiene un único dominio y una copia de las utilidades compartidas, con manifiesto SHA-256. La copia queda fijada en esa entrega: modificar el código compartido del repositorio no cambia una entrega instalada. Los once paquetes se cargan y publican OpenAPI en pruebas sin disponer de otros módulos de dominio.

Las migraciones son aditivas, numeradas, transaccionales y protegidas mediante bloqueo por base. Se aplican explícitamente con el propietario, después de un respaldo, antes de iniciar la nueva versión. Las credenciales HTTP no migran esquemas. `local.py restart-service` cambia únicamente API y worker del servicio seleccionado. La API conserva `/api/v1`, admite los cuerpos anteriores y agrega campos opcionales; una ruptura futura requiere otra versión y un periodo de convivencia. No retirar columnas mientras exista un consumidor anterior.

Independencia no significa ausencia de dependencias: una reserva necesita Inventario, Receptores y Compatibilidad, y la autenticación necesita Identidad/Redis. Al detener un propietario, sus operaciones pueden responder 503; otros procesos y operaciones sin esa dependencia continúan. Una actualización arbitraria que rompa contratos no puede garantizar continuidad. La base física PostgreSQL y Redis compartidos siguen siendo puntos de fallo comunes en el entorno.

## Clientes, conexiones y estado operacional

La web separa rutas por proceso, formularios de mantenimiento y selectores paginados. No comparte modelos de dominio con las API. HTTP reutiliza conexiones por hilo; Redis reutiliza su pool y MongoDB un cliente por aplicación. PostgreSQL conserva transacciones y conexiones cortas; no se agregó un intermediario de infraestructura.

La renovación web toma una concesión por sesión y libera el bloqueo SQLite antes de llamar a Identidad. Logout elimina la sesión local inmediatamente, conserva únicamente una revocación cifrada pendiente y un worker reintenta hasta completarla o expirar. Este SQLite es almacenamiento técnico de credenciales de la web, no una base del dominio ni una autoridad alternativa a Redis.

Los límites se separan por servicio/usuario/institución, por servicio emisor interno y por IP anónima. Un fallo SQL después de publicar la versión de permisos en Redis puede repararse desde la versión SQL autoritativa, bajo bloqueo de usuario. Los motivos de decisiones se guardan en historial local inmutable con acceso del propietario; los eventos centrales permanecen minimizados.

Readiness comprueba migraciones requeridas, dependencias, latido del worker y antigüedad del outbox. Monitoreo marca verificaciones antiguas y resume las últimas 24 horas. Un bucket configurado debe responder; no se presenta como disponible por existir una cadena de configuración. GCS real continúa pendiente.

XML v1 conserva su formato: `response.xsd` valida la estructura y `redhouse.xml_response.validate_response` valida tipos y el DTO publicado por operación. Ambos pasos son necesarios. La biblioteca `jsonschema`, que ya se usaba en pruebas, pasa a ejecución para esta validación; no se incorporó otro framework, broker ni proveedor.

## Interfaz Jinja y caché de lecturas (08/10/2026)

El navegador solicita fragmentos HTML al portal con `X-Filter-Fragment: 1` y `X-Detail-Modal: 1`. La web mantiene autorización, escape Jinja y consumo HTTP de las API; no consulta Redis ni las bases de los servicios directamente. JavaScript mejora los GET: 300 ms de espera al escribir, cancelación de peticiones anteriores, historial del navegador, foco conservado y consulta opcional cada 30 s. No se añadieron WebSockets ni un framework de interfaz.

`redhouse/cache.py` es un mecanismo técnico compartido en código; cada servicio publica su propia copia y controla su namespace y tablas. Inventario e Identidad incorporan su migración `004.sql`, una fila de revisión y triggers de sentencia en `resources`/`catalogue`. La revisión cambia en el mismo commit que los datos. Un rollback no la cambia y una consulta antigua en vuelo solo puede llenar una generación anterior. Las revisiones se leen desde PostgreSQL incluso en HIT: una caída de esa base no se oculta con datos almacenados. Los TTL limitan el envejecimiento por paso del tiempo (p. ej., caducidad); las operaciones críticas vuelven a comprobar datos y estados en su propietario.

Esta invalidación por servicio es conservadora: un cambio invalida todas sus consultas del namespace. Evita dependencias de invalidación entre dominios, a costa de más fallos de caché con muchas escrituras. El HTML, los formularios y las decisiones no se cachean. Para actualizar una instalación existente, respaldar y migrar Inventario e Identidad mediante `scripts/upgrade.py` antes de reiniciar sus procesos. Receptores añade `can_edit` opcional a listados y detalles sin cambiar los cuerpos de escritura ni `/api/v1`.

Desde el 15 de octubre, [el esquema compartido](Esquema_compartido.md) sustituye la separación de bases. La coordinación HTTP descrita se conserva; no se afirma atomicidad global de una secuencia HTTP.
