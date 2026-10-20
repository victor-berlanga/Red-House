# Fichas individuales de microservicios

Edición 0.3.0. Los contratos enlazados contienen campos, tipos, obligatoriedad, ejemplos JSON/XML, XSD, errores y paginación. El expediente HTTP distingue ejemplos de ejecuciones.

Cada servicio tiene API Flask/REST y worker supervisado, módulos de rutas/modelos, biblioteca común de autorización/contratos y persistencia propia mediante vistas limitadas. Puerto interno 8080; el gateway publica un puerto por propietario. Versiones exactas de dependencias en `requirements-verified.txt`; Docker usa Python 3.13 y las pruebas locales Python 3.12.

## Identidad y acceso

Identifica a cada persona y limita qué puede hacer y en qué institución.

**Justificación y proceso:** Un médico inicia sesión, recibe JWT y renovación; Inventario verifica su sesión y permisos antes de reservar.

**Integración declarada:** puede invocar contratos internos de auditoria; acepta llamadas firmadas de donantes, inventario, priorizacion_geografia, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** Usuarios, instituciones, sesiones registradas y hashes scrypt en PostgreSQL. Redis conserva sesiones activas, permisos versionados, renovaciones y revocaciones.

**Ámbito SQL:** `access_identidad_acceso`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `cache_revision` | `red_house.cache_revision` |
| `catalogue` | `red_house.catalogue_entry` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `institutions` | `red_house.institution` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `sessions` | `red_house.web_session` |
| `users` | `red_house.user_account` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_identidad_acceso/Dockerfile), dos instancias `identidad-acceso-a/b`, gateway `http://127.0.0.1:6101` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_identidad_acceso/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_identidad_acceso/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | Iniciar sesión independiente | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/refresh` | Rotar renovación; repetición revoca familia | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/logout` | Cerrar sesión y revocar familia | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/revoke` | Revocar familia con renovación opaca, incluso si venció el JWT de acceso | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/auth/me` | Consultar perfil y permisos vigentes | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/institutions` | Instituciones de la región; sin datos clínicos | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/institutions` | Registrar institución de la región | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/institutions/{identifier}` | Detalle administrativo de institución regional | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/institutions/{identifier}` | Editar nombre institucional propio con versión y motivo | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/institutions/{identifier}/administrator` | Provisionar primer administrador de una institución creada por esta cuenta | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/users` | Crear cuenta institucional | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/users` | Cuentas propias o personal regional de traslado; nunca hashes ni sesiones | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/users/{identifier}` | Activar/desactivar cuenta; invalidar permisos antes del cambio | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/institutions/{identifier}` | Referencia institucional autorizada | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/users/{identifier}` | Validar personal de traslado | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/sites` | Consultar sites | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/sites` | Registrar sites | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/sites/{identifier}` | Detalle de sites | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/sites/{identifier}` | Editar o desactivar sites | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/contacts` | Consultar contacts | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/contacts` | Registrar contacts | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/contacts/{identifier}` | Detalle de contacts | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/contacts/{identifier}` | Editar o desactivar contacts | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/schedules` | Consultar schedules | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/schedules` | Registrar schedules | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/schedules/{identifier}` | Detalle de schedules | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/schedules/{identifier}` | Editar o desactivar schedules | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/capacities` | Consultar capacities | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/capacities` | Registrar capacities | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/capacities/{identifier}` | Detalle de capacities | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/capacities/{identifier}` | Editar o desactivar capacities | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/locations` | Consultar locations | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/locations` | Registrar locations | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/locations/{identifier}` | Detalle de locations | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/locations/{identifier}` | Editar o desactivar locations | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/locations/{identifier}` | Validar ubicación y sede de la institución del usuario | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Donantes

Gestiona registros preliminares, consentimiento, dictamen humano, donaciones, campañas y citas.

**Justificación y proceso:** Un donante se registra y agenda una cita. Un médico registra elegibilidad; después se documentan recolección y procesamiento.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria, identidad_acceso; acepta llamadas firmadas de inventario. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva expedientes y transacciones. Redis valida acceso y limita consumo. Outbox publica auditoría y avisos dirigidos al donante.

**Ámbito SQL:** `access_donantes`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `appointments` | `red_house.appointment` |
| `campaigns` | `red_house.campaign` |
| `decisions` | `red_house.service_decisions` |
| `donation_steps` | `red_house.donation_event` |
| `donations` | `red_house.donation` |
| `donor_reviews` | `red_house.donor_review` |
| `donors` | `red_house.donor` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_donantes/Dockerfile), dos instancias `donantes-a/b`, gateway `http://127.0.0.1:6102` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_donantes/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_donantes/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/donors` | Registro preliminar con consentimiento | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donors` | Expedientes autorizados | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donors/{identifier}` | Expediente y evaluaciones humanas | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/donors/{identifier}` | Corregir expediente sin dictámenes ni donaciones | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/donors/{identifier}/reviews` | Dictamen humano de elegibilidad | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/campaigns` | Crear campaña y capacidad de citas | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/campaigns` | Campañas institucionales vigentes | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/appointments` | Reservar cita sin exceder capacidad | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/appointments` | Citas propias o institucionales | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/appointments/{identifier}/cancel` | Cancelar cita y liberar cupo | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/donations` | Registrar donación tras elegibilidad y confirmación humana | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donations` | Donaciones de la institución sin expediente personal | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/donations/{identifier}/steps` | Documentar procesamiento o rechazo; no infiere elegibilidad clínica | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/donations/{identifier}` | Referencia de procedencia; sin identidad ni estudios del donante | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donations/{identifier}` | Donación y pasos de procesamiento institucionales | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/donations/{identifier}` | Corregir fecha antes de procesamiento, conservando motivo | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/summary` | Indicadores agregados autorizados; no expone expedientes | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/campaigns/{identifier}` | Detalle de campaña institucional | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/campaigns/{identifier}` | Editar campaña sin reducir cupos ya ocupados | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Receptores y solicitudes

Administra expedientes de receptores y el ciclo de vida y cobertura de solicitudes.

**Justificación y proceso:** Una solicitud de una unidad retiene un cupo antes de que Inventario reserve el recurso. Dos peticiones concurrentes no pueden cubrir dos veces ese cupo.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria; acepta llamadas firmadas de compatibilidad, inventario. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva receptores, solicitudes y retenciones de capacidad; Redis valida sesión y permisos. Auditoría/alertas reciben eventos durables.

**Ámbito SQL:** `access_receptores`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `decisions` | `red_house.service_decisions` |
| `holds` | `red_house.request_hold` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `recipients` | `red_house.recipient` |
| `requests` | `red_house.blood_request` |
| `schema_version` | `red_house.service_schema_version` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_receptores/Dockerfile), dos instancias `receptores-a/b`, gateway `http://127.0.0.1:6103` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_receptores/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_receptores/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/recipients` | Expediente diferenciado de sangre u órgano | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/recipients` | Expedientes de la propia institución | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/recipients/{identifier}` | Consultar expediente clínico autorizado | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/recipients/{identifier}` | Corregir receptor antes de registrar solicitudes | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/requests` | Solicitud humana de recursos | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/requests` | Solicitudes institucionales y cobertura | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/requests/{identifier}` | Solicitud y reservas pendientes/confirmadas | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/requests/{identifier}` | Editar solicitud abierta sin retenciones, invalidando evaluaciones anteriores | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/requests/{identifier}/cancel` | Cancelar únicamente sin reservas pendientes o físicas | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/requests/{identifier}` | Instantánea mínima para compatibilidad y reserva | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/holds` | Retener capacidad; serializar solicitud y receptor | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/holds/{identifier}` | Confirmar, liberar o recibir retención de forma idempotente | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/holds-by-operation/{identifier}` | Localizar retención tras perder una respuesta | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/events` | Recibir recepción o liberación sin duplicados | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/summary` | Indicadores agregados autorizados; no expone expedientes | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Inventario y reservas

Mantiene unidades de sangre y ofertas de órganos, su disponibilidad, reservas y ubicación institucional.

**Justificación y proceso:** El origen registra y libera un recurso; el destino lo reserva con evaluación y dictamen favorable; tras recepción queda registrado en la institución de destino.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria, compatibilidad, donantes, identidad_acceso, priorizacion_geografia, receptores; acepta llamadas firmadas de compatibilidad, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL es autoridad de recursos, movimientos y operaciones. Redis ofrece caché breve de disponibilidad y seguridad; una reserva siempre reconsulta PostgreSQL.

**Ámbito SQL:** `access_inventario`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `cache_revision` | `red_house.cache_revision` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `movements` | `red_house.blood_movement` |
| `operations` | `red_house.allocation_operation` |
| `outbox` | `red_house.service_outbox` |
| `reservations` | `red_house.blood_allocation` |
| `resource_reviews` | `red_house.resource_review` |
| `resources` | `red_house.resource` |
| `schema_version` | `red_house.service_schema_version` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_inventario/Dockerfile), dos instancias `inventario-a/b`, gateway `http://127.0.0.1:6104` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_inventario/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_inventario/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/resources` | Registrar unidad u oferta separada, inicialmente en cuarentena | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resources` | Inventario propio; coordinador recibe disponibilidad regional mínima | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/release` | Liberación humana documentada | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/availability` | Disponibilidad regional minimizada con caché autorizada | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/available-resources` | Fuente autoritativa de candidatos; omite caché | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/reservations` | Reservar con retención de capacidad y seguimiento de operación | 202, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/reservations` | Reservas institucionales o regionales para coordinación | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/operations/{identifier}` | Consultar resultado tras pérdida de respuesta | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/operations/{identifier}/resume` | Reanudar confirmación o compensación pendiente | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/reservations/{identifier}` | Consultar asignación autorizada | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/reservations/{identifier}/cancel` | Liberar reserva antes de programar un traslado | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/reservations/{identifier}` | Datos mínimos para planear traslado | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/reservations/{identifier}/claim` | Vincular traslado durable antes de permitir recolección | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/events` | Aplicar hechos logísticos en orden y sin duplicación | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resources/{identifier}` | Recurso y movimientos; sin identidad del donante | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/resources/{identifier}` | Corregir unidad antes de liberación clínica | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/summary` | Indicadores agregados autorizados; no expone expedientes | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/withdraw` | Baja lógica sin reservas ni traslado; conserva historial | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Compatibilidad

Genera candidatos explicables y conserva evaluaciones y dictámenes humanos.

**Justificación y proceso:** Para RBC se aplica el filtro ABO/RhD ya documentado. Para órgano se preselecciona mismo tipo y ABO idéntico, sin interpretar HLA.

**Integración declarada:** puede invocar contratos internos de auditoria, inventario, priorizacion_geografia, receptores; acepta llamadas firmadas de inventario, priorizacion_geografia. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva instantáneas, versiones, candidatos y revisión. Flask consulta propietarios por HTTP; Redis valida JWT y permisos.

**Ámbito SQL:** `access_compatibilidad`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `decisions` | `red_house.service_decisions` |
| `evaluations` | `red_house.candidate_evaluation` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `reviews` | `red_house.blood_review` |
| `schema_version` | `red_house.service_schema_version` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_compatibilidad/Dockerfile), dos instancias `compatibilidad-a/b`, gateway `http://127.0.0.1:6105` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_compatibilidad/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_compatibilidad/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/evaluations` | Preselección ilustrativa con datos y reglas versionados | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/evaluations` | Historial institucional de evaluaciones y versiones | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/evaluations/{identifier}` | Consultar evaluación, explicación y dictámenes | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/evaluations/{identifier}/reviews` | Registrar dictamen humano inmutable de un candidato | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/evaluations/{identifier}` | Instantánea y dictámenes para reservar o priorizar | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Priorización y geografía

Mantiene estimaciones de rutas, ranking operativo y propuestas de cobertura máxima.

**Justificación y proceso:** Si un paciente admite A o B y otro solo A, un recorrido voraz puede dejar uno sin propuesta. Un camino aumentante permite proponer B al flexible y A al restringido.

**Integración declarada:** puede invocar contratos internos de auditoria, compatibilidad, identidad_acceso; acepta llamadas firmadas de compatibilidad, inventario, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva rutas versionadas, factores, rankings y propuestas. Python ejecuta ordenamiento y matching bipartito Hopcroft–Karp. Redis aplica seguridad.

**Ámbito SQL:** `access_priorizacion_geografia`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `proposals` | `red_house.balance_proposal` |
| `rankings` | `red_house.ranking_run` |
| `routes` | `red_house.regional_route` |
| `schema_version` | `red_house.service_schema_version` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_priorizacion_geografia/Dockerfile), dos instancias `priorizacion-geografia-a/b`, gateway `http://127.0.0.1:6106` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_priorizacion_geografia/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_priorizacion_geografia/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/routes` | Registrar estimación logística con procedencia | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/routes` | Rutas autorizadas de la región | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/routes/{identifier}` | Actualizar ruta con control de versión | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/routes/{identifier}` | Consultar una ruta regional por identificador | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/routes/{identifier}` | Revalidar una ruta conocida | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/route-options` | Estimaciones regionales para filtrar candidatos | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/rankings` | Ranking operativo explicable y versionado, no decisión clínica | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/rankings` | Historial propio de rankings operativos | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/rankings/{identifier}` | Factores, explicación y resultados del ranking | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/allocation-proposals` | Matching máximo de candidatos con dictamen favorable; propuesta sin reservas | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/allocation-proposals` | Historial institucional de propuestas de cobertura, sin reservas automáticas | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/allocation-proposals/{identifier}` | Consultar propuesta, límites y versiones originales | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Transporte

Planea y sigue traslados, responsables, incidencias, ubicación autorizada y evidencias.

**Justificación y proceso:** Coordinación planea; origen prepara; traslado recoge y entrega; destino acepta. Cada paso genera eventos de custodia y auditoría.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria, custodia, identidad_acceso, inventario, priorizacion_geografia; acepta llamadas firmadas de custodia. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva órdenes, pasos y referencias de archivos. MongoDB recibe documentos y telemetría mediante outbox. Redis conserva sesión y referencia de ubicación reciente. GCS almacena archivos privados; el portal carga, verifica y descarga mediante firmas temporales.

**Ámbito SQL:** `access_transporte`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `decisions` | `red_house.service_decisions` |
| `files` | `red_house.stored_file` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `shipments` | `red_house.shipment` |
| `telemetry` | `red_house.transport_telemetry` |
| `transitions` | `red_house.shipment_transition` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_transporte/Dockerfile), dos instancias `transporte-a/b`, gateway `http://127.0.0.1:6107` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_transporte/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_transporte/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/shipments` | Planear traslado y confirmar vínculo exclusivo con Inventario | 202, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments` | Traslados de la región, institución o responsable | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}` | Estado logístico y coordinación pendiente | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/transitions` | Registrar paso autorizado y evento de custodia durable | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/telemetry` | Ubicación solo del responsable durante traslado activo | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/telemetry` | Historial de ubicación con autorización por traslado | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/shipments/{identifier}/access` | Autorizar consulta de custodia por asignación logística | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/files` | Preparar carga privada con URL firmada de cinco minutos | 201, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/files` | Evidencias del traslado y estado persistente de validación | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/files/{identifier}/verify` | Verificar tamaño, MIME, firma de archivo y SHA-256 del objeto real | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/files/{identifier}/download` | Descargar evidencia verificada mediante acceso temporal privado | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/summary` | Indicadores agregados autorizados; no expone expedientes | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/tracking` | Último paso documental con versión y referencia a PostgreSQL | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipment-statistics` | Agregación regional del último paso documental de cada traslado | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Cadena de custodia

Conserva secuencia verificable de transferencias físicas y referencias de evidencia.

**Justificación y proceso:** Transporte produce PLANNED, PREPARED, COLLECTED, IN_TRANSIT, DELIVERED y ACCEPTED; Custodia los incorpora sin duplicarlos ni admitir huecos.

**Integración declarada:** puede invocar contratos internos de auditoria, transporte; acepta llamadas firmadas de transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL mantiene el registro autoritativo con secuencia e historial protegido. MongoDB recibe la proyección documental. SHA-256 enlaza eventos; Redis valida identidad y acceso.

**Ámbito SQL:** `access_custodia`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `chains` | `red_house.custody_chain` |
| `custody_events` | `red_house.custody_event` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_custodia/Dockerfile), dos instancias `custodia-a/b`, gateway `http://127.0.0.1:6108` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_custodia/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_custodia/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/internal/v1/events` | Custodia secuencial, deduplicada e inmutable | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/chains/{identifier}` | Consultar cadena; hash detecta alteraciones, no certifica veracidad física | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Alertas

Genera una bandeja de avisos por eventos y conserva su atención.

**Justificación y proceso:** Una reserva avisa a las instituciones implicadas; una cita o evaluación de donante puede avisar a su cuenta específica.

**Integración declarada:** puede invocar contratos internos de auditoria; acepta llamadas firmadas de donantes, inventario, monitoreo, receptores, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva alertas, destinatarios y acuses. Redis valida sesión y permisos. Eventos se deduplican por identificador.

**Ámbito SQL:** `access_alertas`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `alerts` | `red_house.notification` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_alertas/Dockerfile), dos instancias `alertas-a/b`, gateway `http://127.0.0.1:6109` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_alertas/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_alertas/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/internal/v1/events` | Generar alertas por evento con deduplicación y destinatarios explícitos | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/alerts` | Bandeja autorizada: institución, rol y usuario | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/alerts/{identifier}/acknowledge` | Acusar recibo sin modificar el hecho de origen | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Auditoría

Recibe registros minimizados de accesos, cambios, evaluaciones y decisiones.

**Justificación y proceso:** El cambio y su evento se guardan juntos en el servicio de origen. Auditoría recibe después el evento con reintentos y deduplicación.

**Integración declarada:** puede invocar contratos internos de auditoria; acepta llamadas firmadas de alertas, auditoria, compatibilidad, custodia, donantes, identidad_acceso, inventario, monitoreo, priorizacion_geografia, receptores, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL mantiene registro inmutable bajo credenciales de aplicación. MongoDB proporciona proyección documental flexible. Redis controla sesión, perfil Auditor y región.

**Ámbito SQL:** `access_auditoria`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `audit_events` | `red_house.audit_event` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/ms_auditoria/Dockerfile), dos instancias `auditoria-a/b`, gateway `http://127.0.0.1:6110` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/ms_auditoria/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/ms_auditoria/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/internal/v1/events` | Recibir registro minimizado y conservarlo de forma inmutable | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/events` | Bitácora regional de solo lectura; sin credenciales ni contenido clínico | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/events/{identifier}` | Evento auditable y correlación | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/documentary-events` | Proyección documental MongoDB; puede estar pendiente de sincronización | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Monitoreo

Consulta salud y conserva disponibilidad, latencia, versión y dependencia que falla.

**Justificación y proceso:** Con Redis detenido, el proceso sigue vivo, readiness se degrada y las operaciones protegidas fallan de forma cerrada.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria; no ofrece contratos internos firmados. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** HTTP requests consulta /health/ready; MongoDB guarda primero cada sondeo y PostgreSQL conserva las verificaciones. El estado puede consultarse desde MongoDB si PostgreSQL falla. Redis protege las consultas. El worker sondea cada 30 segundos.

**Ámbito SQL:** `access_monitoreo`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `checks` | `red_house.service_health_check` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../apps/services/servicio_monitoreo/Dockerfile), dos instancias `monitoreo-a/b`, gateway `http://127.0.0.1:6111` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../apps/services/servicio_monitoreo/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/servicio_monitoreo/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| GET | `/api/v1/status` | Estado, promedio, último error, versión e historial resumido | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/checks` | Historial persistente de verificaciones | 200, 400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503 |

**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

