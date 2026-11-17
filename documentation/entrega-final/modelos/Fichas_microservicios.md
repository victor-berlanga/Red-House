# Fichas individuales de microservicios

Corte final: doce servicios independientes; esquema 21. Las versiones contractuales se leen de sus OpenAPI actuales. El catálogo documenta contratos, no ejecución ni aceptación de todas sus operaciones.

Cada servicio tiene API Flask/REST y worker supervisado, módulos de rutas/modelos, biblioteca común de autorización/contratos y persistencia propia mediante vistas limitadas. Puerto interno 8080; el gateway publica un puerto por propietario. Versiones exactas de dependencias en `requirements-verified.txt`; Docker usa Python 3.13 y las pruebas locales Python 3.12.

## Identidad y acceso

Identifica a cada persona y limita qué puede hacer y en qué institución.

**Justificación y proceso:** Un médico inicia sesión, recibe JWT y renovación; Inventario verifica su sesión y permisos antes de reservar.

**Integración declarada:** puede invocar contratos internos de auditoria; acepta llamadas firmadas de alertas, auditoria, donantes, inventario, priorizacion_geografia, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** Usuarios, instituciones, sesiones registradas y hashes scrypt en PostgreSQL. Redis conserva sesiones activas, permisos versionados, renovaciones y revocaciones.

**Ámbito SQL:** `access_identidad_acceso`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `accreditations` | `red_house.accreditations` |
| `activity_events` | `red_house.service_activity_events` |
| `cache_revision` | `red_house.cache_revision` |
| `catalogue` | `red_house.catalogue_entry` |
| `decisions` | `red_house.service_decisions` |
| `devices` | `red_house.devices` |
| `idempotency` | `red_house.service_idempotency` |
| `identity_deliveries` | `red_house.identity_deliveries` |
| `inbox` | `red_house.service_inbox` |
| `institution_presentations` | `red_house.institution_presentations` |
| `institutions` | `red_house.institution` |
| `outbox` | `red_house.service_outbox` |
| `portal_policies` | `red_house.portal_policies` |
| `recovery_tokens` | `red_house.recovery_tokens` |
| `schema_version` | `red_house.service_schema_version` |
| `security_contacts` | `red_house.security_contacts` |
| `security_factors` | `red_house.security_factors` |
| `sessions` | `red_house.web_session` |
| `shared_schema_version` | `red_house.schema_migration` |
| `users` | `red_house.user_account` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_identidad_acceso/Dockerfile), dos instancias `identidad-acceso-a/b`, gateway `http://127.0.0.1:6101` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_identidad_acceso/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_identidad_acceso/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| GET | `/api/v1/user-creation-receipt` | Consultar resultado de un alta propia | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/audit-assignees` | Coordinadores habilitados de la región para atención de hallazgos | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/audit-assignees/{identifier}` | Validar coordinador regional para un hallazgo | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/login` | Iniciar sesión independiente | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/refresh` | Rotar renovación; repetición revoca familia | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/logout` | Cerrar sesión y revocar familia | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/revoke` | Revocar familia con renovación opaca, incluso si venció el JWT de acceso | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/auth/me` | Consultar perfil y permisos vigentes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/institutions` | Instituciones de la región; sin datos clínicos | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/institutions` | Registrar institución de la región | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/institutions/{identifier}` | Detalle administrativo de institución regional | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/institutions/{identifier}` | Editar nombre institucional propio con versión y motivo | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/institutions/{identifier}/administrator` | Provisionar primer administrador de una institución creada por esta cuenta | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/users` | Crear cuenta institucional | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/users` | Cuentas propias o personal regional de traslado; nunca hashes ni sesiones | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/users/{identifier}` | Activar/desactivar cuenta; invalidar permisos antes del cambio | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/users/{identifier}/role` | user_role | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/institutions/{identifier}` | Referencia institucional autorizada | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/users/{identifier}` | Validar personal de traslado | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/appointment-site-labels` | Nombres de sedes propias para una página de horarios autorizados | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/institutions/{identifier}/operational-contacts` | Contactos explícitamente operativos; solo proyección de tarea por Transporte | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/appointment-sites` | appointment_sites | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/sites` | Consultar sites | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/sites` | Registrar sites | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/sites/{identifier}` | Detalle de sites | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/sites/{identifier}` | Editar o desactivar sites | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/contacts` | Consultar contacts | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/contacts` | Registrar contacts | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/contacts/{identifier}` | Detalle de contacts | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/contacts/{identifier}` | Editar o desactivar contacts | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/schedules` | Consultar schedules | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/schedules` | Registrar schedules | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/schedules/{identifier}` | Detalle de schedules | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/schedules/{identifier}` | Editar o desactivar schedules | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/capacities` | Consultar capacities | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/capacities` | Registrar capacities | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/capacities/{identifier}` | Detalle de capacities | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/capacities/{identifier}` | Editar o desactivar capacities | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/locations` | Consultar locations | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/locations` | Registrar locations | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/locations/{identifier}` | Detalle de locations | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/locations/{identifier}` | Editar o desactivar locations | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/responsibles` | Consultar responsibles | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/responsibles` | Registrar responsibles | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/responsibles/{identifier}` | Detalle de responsibles | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/responsibles/{identifier}` | Editar o desactivar responsibles | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/services` | Consultar services | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/catalogues/services` | Registrar services | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/catalogues/services/{identifier}` | Detalle de services | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/catalogues/services/{identifier}` | Editar o desactivar services | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/locations/{identifier}` | Validar ubicación y sede de la institución del usuario | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/mobile/devices` | Registrar teléfono propio, sin credencial de emisor autónomo | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/mobile/devices/{identifier}/revoke` | mobile_device_revoke | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/devices` | device_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/devices` | device_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/devices/{identifier}` | device_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/devices/{identifier}/credentials` | device_credentials | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/devices/{identifier}/revoke` | device_revoke | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/transport-users/{identifier}/operational-name` | Nombre operativo mínimo para una tarea autorizada por Transporte | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/custody-users/{identifier}` | custody_user | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/notification-users/{identifier}` | notification_user | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/mfa/enrollment` | mfa_enrollment | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/mfa/confirm` | mfa_confirm | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/reauthenticate` | obsolete_reauthentication | 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503, 410 |
| POST | `/api/v1/auth/reauthentication-proofs` | reauthenticate | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/contact` | security_contact | 202, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/contact/verify` | security_contact_verify | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/recovery` | recovery_request | 202, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/auth/recovery/complete` | recovery_complete | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/accreditations` | accreditations_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/accreditations` | accreditation_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/accreditations/{identifier}` | accreditations_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/public/institutions` | public_institutions | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/institutions/{identifier}/presentation` | institution_presentation | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/institutions/{identifier}/presentation` | institution_presentation_change | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/portal-policy` | portal_policy | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/portal-policy` | portal_policy_change | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Donantes

Gestiona registros preliminares, consentimiento, dictamen humano, donaciones, campañas y citas.

**Justificación y proceso:** Un donante se registra y agenda una cita. Un médico registra elegibilidad; después se documentan recolección y procesamiento.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria, identidad_acceso; acepta llamadas firmadas de inventario. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva expedientes y transacciones. Redis valida acceso y limita consumo. Outbox publica auditoría y avisos dirigidos al donante.

**Ámbito SQL:** `access_donantes`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `appointment_reminders` | `red_house.appointment_reminders` |
| `appointment_slots` | `red_house.appointment_slots` |
| `appointments` | `red_house.appointment` |
| `campaign_publications` | `red_house.campaign_publications` |
| `campaign_slots` | `red_house.campaign_slots` |
| `campaigns` | `red_house.campaign` |
| `consent_versions` | `red_house.consent_versions` |
| `decisions` | `red_house.service_decisions` |
| `donation_steps` | `red_house.donation_event` |
| `donations` | `red_house.donation` |
| `donor_reviews` | `red_house.donor_review` |
| `donors` | `red_house.donor` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_donantes/Dockerfile), dos instancias `donantes-a/b`, gateway `http://127.0.0.1:6102` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_donantes/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_donantes/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/donors` | Registro preliminar con consentimiento | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donors` | Expedientes autorizados | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donors/{identifier}` | Expediente y evaluaciones humanas | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/donors/{identifier}` | Corregir expediente sin dictámenes ni donaciones | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/donors/{identifier}/reviews` | Dictamen humano de elegibilidad | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/campaigns` | Crear campaña y capacidad de citas | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/campaigns` | Campañas institucionales vigentes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/appointments` | Reservar cita sin exceder capacidad | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/appointments` | Citas propias o institucionales | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/appointments/{identifier}/cancel` | Cancelar cita y liberar cupo | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/donations` | Registrar donación tras elegibilidad y confirmación humana | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donations` | Donaciones de la institución sin expediente personal | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/donations/{identifier}/steps` | Documentar procesamiento o rechazo; no infiere elegibilidad clínica | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/donations/{identifier}` | Referencia de procedencia; sin identidad ni estudios del donante | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donations/{identifier}` | Donación y pasos de procesamiento institucionales | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/donations/{identifier}` | Corregir fecha antes de procesamiento, conservando motivo | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/summary` | Indicadores agregados autorizados; no expone expedientes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/campaigns/{identifier}` | Detalle de campaña institucional | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/campaigns/{identifier}` | Editar campaña sin reducir cupos ya ocupados | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/donors/{identifier}/personal` | Actualizar el nombre mostrado del expediente propio sin cambiar datos clínicos | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/donors/{identifier}/withdraw` | Dar de baja: borrar sin historial o conservar como inactivo | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/appointments/agenda` | appointment_agenda | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/appointments/next` | next_appointment | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donations/{identifier}/history` | donation_history | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/campaign-slots` | campaign_slots_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/campaign-slots` | campaign_slot_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/campaign-slots/{identifier}` | campaign_slots_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/donors/{identifier}/consents` | consent_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/donors/{identifier}/consents` | consent_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/appointments/{identifier}/schedule` | appointment_schedule | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/appointments/{identifier}/commands` | appointment_command | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/decision-data` | donation_decision_data | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/public/campaigns` | public_campaigns | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/public/campaign-feed` | Campañas públicas paginadas, con búsqueda y fechas de inicio | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/campaigns/{identifier}/publication` | campaign_publication | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/campaigns/{identifier}/publication` | campaign_publish | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/portal-metrics` | portal_metrics | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Receptores y solicitudes

Administra expedientes de receptores y el ciclo de vida y cobertura de solicitudes.

**Justificación y proceso:** Una solicitud de una unidad retiene un cupo antes de que Inventario reserve el recurso. Dos peticiones concurrentes no pueden cubrir dos veces ese cupo.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria; acepta llamadas firmadas de compatibilidad, inventario. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva receptores, solicitudes y retenciones de capacidad; Redis valida sesión y permisos. Auditoría/alertas reciben eventos durables.

**Ámbito SQL:** `access_receptores`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `decisions` | `red_house.service_decisions` |
| `external_authorizations` | `red_house.external_authorizations` |
| `holds` | `red_house.request_hold` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `recipients` | `red_house.recipient` |
| `requests` | `red_house.blood_request` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_receptores/Dockerfile), dos instancias `receptores-a/b`, gateway `http://127.0.0.1:6103` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_receptores/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_receptores/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/recipients` | Expediente diferenciado de sangre u órgano | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/recipients` | Expedientes de la propia institución | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/recipients/{identifier}` | Consultar expediente clínico autorizado | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/recipients/{identifier}` | Corregir receptor antes de registrar solicitudes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/requests` | Solicitud humana de recursos | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/requests` | Solicitudes institucionales y cobertura | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/requests/{identifier}` | Solicitud y reservas pendientes/confirmadas | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/requests/{identifier}` | Editar solicitud abierta sin retenciones, invalidando evaluaciones anteriores | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/requests/{identifier}/cancel` | Cancelar únicamente sin reservas pendientes o físicas | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/requests/{identifier}` | Instantánea mínima para compatibilidad y reserva | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/holds` | Retener capacidad; serializar solicitud y receptor | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/holds/{identifier}` | Confirmar, liberar o recibir retención de forma idempotente | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/holds-by-operation/{identifier}` | Localizar retención tras perder una respuesta | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/events` | Recibir recepción o liberación sin duplicados | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/summary` | Indicadores agregados autorizados; no expone expedientes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/requests/{identifier}/external-authorizations` | external_authorization_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/requests/{identifier}/external-authorizations` | external_authorizations | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/decision-data` | request_decision_data | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/portal-metrics` | portal_metrics | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Inventario y reservas

Mantiene unidades de sangre y ofertas de órganos, su disponibilidad, reservas y ubicación institucional.

**Justificación y proceso:** El origen registra y libera un recurso; el destino lo reserva con evaluación y dictamen favorable; tras recepción queda registrado en la institución de destino.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria, compatibilidad, donantes, identidad_acceso, priorizacion_geografia, receptores; acepta llamadas firmadas de compatibilidad, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL es autoridad de recursos, movimientos y operaciones. Redis ofrece caché breve de disponibilidad y seguridad; una reserva siempre reconsulta PostgreSQL.

**Ámbito SQL:** `access_inventario`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `cache_revision` | `red_house.cache_revision` |
| `cold_equipment` | `red_house.cold_equipment` |
| `cold_profiles` | `red_house.cold_profiles` |
| `cold_readings` | `red_house.cold_readings` |
| `cold_reviews` | `red_house.cold_reviews` |
| `decisions` | `red_house.service_decisions` |
| `external_mappings` | `red_house.external_mappings` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `movements` | `red_house.blood_movement` |
| `operations` | `red_house.allocation_operation` |
| `outbox` | `red_house.service_outbox` |
| `reservations` | `red_house.blood_allocation` |
| `resource_controls` | `red_house.resource_controls` |
| `resource_destinations` | `red_house.resource_destinations` |
| `resource_lineage` | `red_house.resource_lineage` |
| `resource_reviews` | `red_house.resource_review` |
| `resources` | `red_house.resource` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_inventario/Dockerfile), dos instancias `inventario-a/b`, gateway `http://127.0.0.1:6104` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_inventario/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_inventario/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| GET | `/api/v1/operations/by-key/{command_key}` | Consultar el comando propio antes de reintentar una reserva incierta | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources` | Registrar unidad u oferta separada, inicialmente en cuarentena | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resources` | Inventario propio; coordinador recibe disponibilidad regional mínima | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/release` | Liberación humana documentada | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/availability` | Disponibilidad regional minimizada con caché autorizada | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/available-resources` | Fuente autoritativa de candidatos; omite caché | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/resources/{identifier}/laboratory-context` | resource_laboratory_context | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/reservations` | Reservar con retención de capacidad y seguimiento de operación | 202, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/reservations` | Reservas institucionales o regionales para coordinación | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/operations/{identifier}` | Consultar resultado tras pérdida de respuesta | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/operations/{identifier}/resume` | Reanudar confirmación o compensación pendiente | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/reservations/{identifier}` | Consultar asignación autorizada | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/reservations/{identifier}/cancel` | Liberar reserva antes de programar un traslado | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/reservations/{identifier}` | Datos mínimos para planear traslado | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/reservations/{identifier}/claim` | Vincular traslado durable antes de permitir recolección | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/events` | Aplicar hechos logísticos en orden y sin duplicación | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resources/{identifier}` | Recurso y movimientos; sin identidad del donante | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/resources/{identifier}` | Corregir unidad antes de liberación clínica | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/summary` | Indicadores agregados autorizados; no expone expedientes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/withdraw` | Baja lógica sin reservas ni traslado; conserva historial | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/label-issuances` | label_issue | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/reservations/{identifier}/logistics` | reservation_logistics | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/reservations/{identifier}/custody-check` | custody_check | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/cold/equipment` | cold_equipment_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/cold/equipment` | cold_equipment_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/cold/equipment/{identifier}` | cold_equipment_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/cold/profiles` | cold_profiles_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/cold/profiles` | cold_profile_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/cold/profiles/{identifier}` | cold_profiles_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resource-destinations` | resource_destinations_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resource-destinations/{identifier}` | resource_destinations_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/controls` | resource_controls_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resources/{identifier}/controls` | resource_controls_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/cold-readings` | cold_reading_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resources/{identifier}/cold-readings` | cold_readings_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/quality-review` | quality_review | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/destination` | resource_destination | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/resources/{identifier}/components` | resource_fractionate | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resources/{identifier}/lineage` | resource_lineage | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/external-mappings` | external_mappings_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/external-mappings/{identifier}` | external_mappings_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/interoperability/reconcile` | external_reconcile | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/interoperability/export/{identifier}` | external_export | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/analytics/inventory` | inventory_analytics | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/resources/{identifier}/trace` | resource_trace | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/decision-data` | inventory_decision_data | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/portal-metrics` | portal_metrics | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Compatibilidad

Genera candidatos explicables y conserva evaluaciones y dictámenes humanos.

**Justificación y proceso:** Para RBC se aplica el filtro ABO/RhD ya documentado. Para órgano se preselecciona mismo tipo y ABO idéntico, sin interpretar HLA.

**Integración declarada:** puede invocar contratos internos de auditoria, inventario, priorizacion_geografia, receptores; acepta llamadas firmadas de inventario, priorizacion_geografia. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva instantáneas, versiones, candidatos y revisión. Flask consulta propietarios por HTTP; Redis valida JWT y permisos.

**Ámbito SQL:** `access_compatibilidad`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `decisions` | `red_house.service_decisions` |
| `evaluations` | `red_house.candidate_evaluation` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `lab_actions` | `red_house.lab_actions` |
| `lab_profiles` | `red_house.lab_profiles` |
| `lab_results` | `red_house.lab_results` |
| `lab_samples` | `red_house.lab_samples` |
| `outbox` | `red_house.service_outbox` |
| `reviews` | `red_house.blood_review` |
| `rule_actions` | `red_house.rule_actions` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_compatibilidad/Dockerfile), dos instancias `compatibilidad-a/b`, gateway `http://127.0.0.1:6105` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_compatibilidad/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_compatibilidad/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/evaluations` | Preselección ilustrativa con datos y reglas versionados | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/evaluations` | Historial institucional de evaluaciones y versiones | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/evaluations/{identifier}` | Consultar evaluación, explicación y dictámenes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/evaluations/{identifier}/reproduce` | evaluation_reproduce | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/evaluations/{identifier}/reviews` | Registrar dictamen humano inmutable de un candidato | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/evaluations/{identifier}` | Instantánea y dictámenes para reservar o priorizar | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/samples/{identifier}/completeness` | sample_completeness | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/resources/{identifier}/history` | lab_history | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/profiles` | lab_profiles_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/laboratory/profiles` | lab_profile_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/profiles/{identifier}` | lab_profiles_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/samples` | lab_samples_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/laboratory/samples` | lab_sample_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/samples/{identifier}` | lab_samples_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/results` | lab_results_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/laboratory/results` | lab_result_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/results/{identifier}` | lab_results_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/laboratory/samples/{identifier}/receive` | lab_sample_receive | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/laboratory/results/{identifier}/review` | lab_result_review | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/laboratory/resources/{identifier}/check` | lab_resource_check | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/laboratory/resources/{identifier}/check` | lab_resource_completeness | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/profiles/{identifier}/governance` | rule_governance | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/laboratory/profiles/{identifier}/actions` | rule_transition | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/decision-data` | laboratory_decision_data | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/laboratory/reference-sources` | reference_sources | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/portal-metrics` | portal_metrics | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.4`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Priorización y geografía

Mantiene estimaciones de rutas, ranking operativo y propuestas de cobertura máxima.

**Justificación y proceso:** Si un paciente admite A o B y otro solo A, un recorrido voraz puede dejar uno sin propuesta. Un camino aumentante permite proponer B al flexible y A al restringido.

**Integración declarada:** puede invocar contratos internos de auditoria, compatibilidad, identidad_acceso; acepta llamadas firmadas de compatibilidad, inventario, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva rutas versionadas, factores, rankings y propuestas. Python ejecuta ordenamiento y matching bipartito Hopcroft–Karp. Redis aplica seguridad.

**Ámbito SQL:** `access_priorizacion_geografia`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `algorithm_runs` | `red_house.algorithm_runs` |
| `decision_runs` | `red_house.decision_runs` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `proposals` | `red_house.balance_proposal` |
| `rankings` | `red_house.ranking_run` |
| `regional_graphs` | `red_house.regional_graphs` |
| `routes` | `red_house.regional_route` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_priorizacion_geografia/Dockerfile), dos instancias `priorizacion-geografia-a/b`, gateway `http://127.0.0.1:6106` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_priorizacion_geografia/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_priorizacion_geografia/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/routes` | Registrar estimación logística con procedencia | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/routes` | Rutas autorizadas de la región | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| PATCH | `/api/v1/routes/{identifier}` | Actualizar ruta con control de versión | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/routes/{identifier}` | Consultar una ruta regional por identificador | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/routes/{identifier}` | Revalidar una ruta conocida | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/route-options` | Estimaciones regionales para filtrar candidatos | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/rankings` | Ranking operativo explicable y versionado, no decisión clínica | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/rankings` | Historial propio de rankings operativos | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/rankings/{identifier}` | Factores, explicación y resultados del ranking | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/allocation-proposals` | Matching máximo de candidatos con dictamen favorable; propuesta sin reservas | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/allocation-proposals` | Historial institucional de propuestas de cobertura, sin reservas automáticas | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/allocation-proposals/{identifier}` | Consultar propuesta, límites y versiones originales | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/algorithm-runs` | algorithm_runs_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/algorithm-runs` | algorithm_run | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/algorithm-runs/{identifier}` | algorithm_runs_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/regional-graph-sources` | regional_graph_sources | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/regional-graphs/from-reference` | regional_graph_import | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/regional-graphs` | regional_graphs_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/regional-graphs` | regional_graph_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/regional-graphs/{identifier}` | regional_graphs_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/decision-runs` | decision_runs_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/decision-runs` | decision_run_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/decision-runs/{identifier}` | decision_runs_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/decision-runs/{identifier}/reproduce` | decision_run_reproduce | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.4`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Transporte

Planea y sigue traslados, responsables, incidencias, ubicación autorizada y evidencias.

**Justificación y proceso:** Coordinación planea; origen prepara; traslado recoge y entrega; destino acepta. Cada paso genera eventos de custodia y auditoría.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria, custodia, documentos, identidad_acceso, inventario, priorizacion_geografia; acepta llamadas firmadas de custodia. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva órdenes, pasos y referencias de archivos. MongoDB recibe documentos y telemetría mediante outbox. Redis conserva sesión y referencia de ubicación reciente. GCS almacena archivos privados; el portal carga, verifica y descarga mediante firmas temporales.

**Ámbito SQL:** `access_transporte`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `decisions` | `red_house.service_decisions` |
| `files` | `red_house.stored_file` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `shipments` | `red_house.shipment` |
| `sync_commands` | `red_house.sync_commands` |
| `telemetry` | `red_house.transport_telemetry` |
| `tracking_assignments` | `red_house.tracking_assignments` |
| `tracking_devices` | `red_house.devices`, `red_house.institution`, `red_house.user_account` |
| `tracking_points` | `red_house.tracking_points` |
| `transitions` | `red_house.shipment_transition` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_transporte/Dockerfile), dos instancias `transporte-a/b`, gateway `http://127.0.0.1:6107` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_transporte/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_transporte/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/shipments` | Planear traslado y confirmar vínculo exclusivo con Inventario | 202, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments` | Traslados de la región, institución o responsable | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}` | Estado logístico y coordinación pendiente | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/transitions` | Registrar paso autorizado y evento de custodia durable | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/telemetry` | Ubicación solo del responsable durante traslado activo | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/telemetry` | Historial de ubicación con autorización por traslado | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/internal/v1/shipments/{identifier}/access` | Autorizar consulta de custodia por asignación logística | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/summary` | Indicadores agregados autorizados; no expone expedientes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/tracking` | Último paso documental con versión y referencia a PostgreSQL | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipment-statistics` | Agregación regional del último paso documental de cada traslado | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/tracking/devices` | tracking_devices_for_shipment | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/tracking/ticket` | tracking_ticket | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/tracking/metrics` | tracking_metrics | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/tracking/assignments` | tracking_assign | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/tracking/assignments` | tracking_assignments | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/tracking/assignments/{identifier}/revoke` | tracking_revoke | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/tracking/snapshot` | tracking_snapshot | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/tracking/history` | tracking_history | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/operational-handover` | Identidad operativa mínima del transportista de la tarea autorizada | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/operational-context` | Contactos operativos y ruta vinculada a la tarea autorizada; sin expediente clínico | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/scan` | shipment_scan | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/tracking/mobile-session` | mobile_tracking_start | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/tracking/mobile-session/stop` | mobile_tracking_stop | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/sync/shipments/{identifier}/changes` | sync_shipment_changes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/sync/commands` | sync_command | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/sync/commands/{identifier}` | sync_result | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/sync/changes` | sync_changes | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/shipments/{identifier}/files` | Preparar carga privada con URL firmada de cinco minutos | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/files` | Evidencias del traslado y estado persistente de validación | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/files/{identifier}/verify` | Verificar tamaño, MIME, firma de archivo y SHA-256 del objeto real | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/files/{identifier}/download` | Descargar evidencia verificada mediante acceso temporal privado | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/documents` | document_prepare | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/documents` | document_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/documents/{identifier}` | document_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/export-jobs` | export_create | 202, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/export-jobs` | export_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/export-jobs/{identifier}` | export_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/export-jobs/{identifier}/retry` | export_retry | 202, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/analytics/transport` | transport_analytics | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/decision-data` | transport_decision_data | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/portal-metrics` | portal_metrics | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Cadena de custodia

Conserva secuencia verificable de transferencias físicas y referencias de evidencia.

**Justificación y proceso:** Transporte produce PLANNED, PREPARED, COLLECTED, IN_TRANSIT, DELIVERED y ACCEPTED; Custodia los incorpora sin duplicarlos ni admitir huecos.

**Integración declarada:** puede invocar contratos internos de auditoria, transporte; acepta llamadas firmadas de transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL mantiene el registro autoritativo con secuencia e historial protegido. MongoDB recibe la proyección documental. SHA-256 enlaza eventos; Redis valida identidad y acceso.

**Ámbito SQL:** `access_custodia`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

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
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_custodia/Dockerfile), dos instancias `custodia-a/b`, gateway `http://127.0.0.1:6108` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_custodia/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_custodia/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/internal/v1/events` | Custodia secuencial, deduplicada e inmutable | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/chains/{identifier}` | Consultar cadena; hash detecta alteraciones, no certifica veracidad física | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Alertas

Genera una bandeja de avisos por eventos y conserva su atención.

**Justificación y proceso:** Una reserva avisa a las instituciones implicadas; una cita o evaluación de donante puede avisar a su cuenta específica.

**Integración declarada:** puede invocar contratos internos de auditoria, identidad_acceso; acepta llamadas firmadas de auditoria, donantes, inventario, monitoreo, receptores, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva alertas, destinatarios y acuses. Redis valida sesión y permisos. Eventos se deduplican por identificador.

**Ámbito SQL:** `access_alertas`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `alert_actions` | `red_house.alert_actions` |
| `alert_deliveries` | `red_house.alert_deliveries` |
| `alert_policies` | `red_house.alert_policies` |
| `alert_severity` | `red_house.notification` |
| `alert_subscriptions` | `red_house.alert_subscriptions` |
| `alerts` | `red_house.notification` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_alertas/Dockerfile), dos instancias `alertas-a/b`, gateway `http://127.0.0.1:6109` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_alertas/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_alertas/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/internal/v1/events` | Generar alertas por evento con deduplicación y destinatarios explícitos | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/alerts` | Bandeja autorizada: institución, rol y usuario | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/alerts/{identifier}/acknowledge` | Acusar recibo sin modificar el hecho de origen | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/alert-policies` | alert_policies_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/alert-policies` | alert_policy_create | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/alert-policies/{identifier}` | alert_policies_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/alert-subscriptions` | Registrar, rotar o reactivar destino propio; una suscripción por cuenta y canal | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/alert-subscriptions` | alert_subscriptions | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/alert-subscriptions/{identifier}/revoke` | alert_subscription_revoke | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/alerts/{identifier}/close` | alert_close | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/alerts/{identifier}/deliveries` | alert_deliveries | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Auditoría

Recibe registros minimizados de accesos, cambios, evaluaciones y decisiones.

**Justificación y proceso:** El cambio y su evento se guardan juntos en el servicio de origen. Auditoría recibe después el evento con reintentos y deduplicación.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria, identidad_acceso; acepta llamadas firmadas de alertas, auditoria, compatibilidad, custodia, documentos, donantes, identidad_acceso, inventario, monitoreo, priorizacion_geografia, receptores, transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL mantiene registro inmutable bajo credenciales de aplicación. MongoDB proporciona proyección documental flexible. Redis controla sesión, perfil Auditor y región.

**Ámbito SQL:** `access_auditoria`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `anomaly_actions` | `red_house.anomaly_actions` |
| `anomaly_reviews` | `red_house.anomaly_reviews` |
| `audit_events` | `red_house.audit_event` |
| `audit_finding_actions` | `red_house.audit_finding_actions` |
| `audit_finding_links` | `red_house.audit_finding_links` |
| `audit_findings` | `red_house.audit_findings` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_auditoria/Dockerfile), dos instancias `auditoria-a/b`, gateway `http://127.0.0.1:6110` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_auditoria/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_auditoria/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| GET | `/api/v1/event-options` | Categorías, acciones, resultados y límite de exportación | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/events` | Recibir registro minimizado y conservarlo de forma inmutable | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/events` | Bitácora regional de solo lectura; sin credenciales ni contenido clínico | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/events/export` | Exportar hasta 5000 resultados con los mismos filtros y una instantánea consistente | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/events/{identifier}/related` | Secuencia regional relacionada por recursos o correlación; máximo 500 eventos y cuatro saltos | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/events/{identifier}` | Evento auditable y correlación | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/documentary-events` | Proyección documental MongoDB; puede estar pendiente de sincronización | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/findings` | Hallazgos regionales para auditor o asignados al responsable | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/findings` | Registrar hallazgo con eventos o recurso autorizado y coordinador responsable | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/findings/{identifier}` | Hallazgo, referencias e historial inmutable de atención | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/findings/{identifier}/actions` | Atención por responsable; cierre o devolución exclusivamente por auditor | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/anomaly-reviews` | anomaly_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/anomaly-reviews/{identifier}` | anomaly_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/anomaly-reviews/{identifier}/resolve` | anomaly_resolve | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Monitoreo

Consulta salud y conserva disponibilidad, latencia, versión y dependencia que falla.

**Justificación y proceso:** Con Redis detenido, el proceso sigue vivo, readiness se degrada y las operaciones protegidas fallan de forma cerrada.

**Integración declarada:** puede invocar contratos internos de alertas, auditoria; no ofrece contratos internos firmados. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** HTTP requests consulta /health/ready; MongoDB guarda primero cada sondeo y PostgreSQL conserva las verificaciones. El estado puede consultarse desde MongoDB si PostgreSQL falla. Redis protege las consultas. El worker sondea cada 30 segundos.

**Ámbito SQL:** `access_monitoreo`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `checks` | `red_house.service_health_check` |
| `decisions` | `red_house.service_decisions` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/servicio_monitoreo/Dockerfile), dos instancias `monitoreo-a/b`, gateway `http://127.0.0.1:6111` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/servicio_monitoreo/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/servicio_monitoreo/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| GET | `/api/v1/status/percentiles` | status_percentiles | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/status` | Estado, promedio, último error, versión e historial resumido | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/checks` | Historial persistente de verificaciones | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

## Documentos y reportes

Gestiona archivos privados y exportaciones minimizadas.

**Justificación y proceso:** Prepara, verifica y entrega URL temporal. El worker genera PDF, CSV o XLSX con ruta determinista.

**Integración declarada:** puede invocar contratos internos de auditoria; acepta llamadas firmadas de transporte. Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.

**Persistencia y relaciones:** PostgreSQL conserva metadatos y trabajos; GCS objetos privados; ClamAV valida cada generación. Redis valida permisos.

**Ámbito SQL:** `access_documentos`. La correspondencia siguiente procede del catálogo capturado. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).

| Vista autorizada | Tabla física compartida |
| --- | --- |
| `activity_events` | `red_house.service_activity_events` |
| `decisions` | `red_house.service_decisions` |
| `document_metadata` | `red_house.document_metadata` |
| `export_jobs` | `red_house.export_jobs` |
| `file_scans` | `red_house.file_scans` |
| `files` | `red_house.stored_file` |
| `idempotency` | `red_house.service_idempotency` |
| `inbox` | `red_house.service_inbox` |
| `outbox` | `red_house.service_outbox` |
| `schema_version` | `red_house.service_schema_version` |
| `shared_schema_version` | `red_house.schema_migration` |
| `worker_health` | `red_house.service_worker_health` |

**Despliegue:** [Dockerfile](../../../apps/services/ms_documentos/Dockerfile), dos instancias `documentos-a/b`, gateway `http://127.0.0.1:6112` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Documentos añade configuración LOCAL/GCS y antivirus; los cuatro propietarios documentales añaden MongoDB.

**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.

**Contratos:** [OpenAPI completo](../../../apps/services/ms_documentos/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../../apps/services/ms_documentos/contracts/) · [Ejecuciones HTTP](../../evidencias/segundo-parcial/http/index.html).

| Método | Ruta | Objetivo | Códigos declarados |
| --- | --- | --- | --- |
| POST | `/api/v1/shipments/{identifier}/files` | Preparar carga privada con URL firmada de cinco minutos | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/shipments/{identifier}/files` | Evidencias del traslado y estado persistente de validación | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/files/{identifier}/verify` | Verificar tamaño, MIME, firma de archivo y SHA-256 del objeto real | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/files/{identifier}/download` | Descargar evidencia verificada mediante acceso temporal privado | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/documents/{identifier}/status` | document_status | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/documents/{identifier}/conservation` | document_conservation | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/internal/v1/files/{identifier}/transport-check` | file_transport_check | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/documents` | document_prepare | 201, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/documents` | document_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/documents/{identifier}/verified` | document_verified | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/documents/{identifier}` | document_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/export-jobs` | export_create | 202, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/export-jobs` | export_list | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| GET | `/api/v1/export-jobs/{identifier}` | export_detail | 200, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |
| POST | `/api/v1/export-jobs/{identifier}/retry` | export_retry | 202, 400, 401, 403, 404, 406, 409, 412, 413, 415, 422, 429, 500, 503 |

**Corte final de esta ficha:** versión OpenAPI `0.4.1`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.


**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.

**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.

