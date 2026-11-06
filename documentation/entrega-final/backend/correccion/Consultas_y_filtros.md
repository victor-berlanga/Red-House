# Consultas, filtros y orden — corrección 0.4.1

Los parámetros siguientes proceden de los contratos OpenAPI regenerados. Cada propietario aplica su autorización institucional antes de contar o paginar. Las consultas no habilitan edición de historia.

En los listados comunes, `page` admite 1–100000 y `page_size` 1–100. `q` busca sin distinguir mayúsculas, escapa `%`/`_` y limita a 100 caracteres; donde no existe texto público apropiado busca UUID. `from_at` es inclusivo y `until_at` exclusivo; requieren zona horaria y se comparan como instantes UTC. `sort` admite `ID_ASC`, `DATE_ASC`, `DATE_DESC`; el UUID desempata fechas. La paginación es estable para una instantánea sin escrituras concurrentes; no promete aislamiento entre peticiones independientes.

`date_field` usa `created_at` salvo recursos (`created_at`, `expires_at`), traslados (`created_at`, `departure_at`) y lecturas de frío (`captured_at`, `received_at`). Los módulos generados por `install_reads` admiten los campos terminados en `_at`, `valid_from`, `valid_until`, `starts_at` y `ends_at` publicados por su DTO. UUID, booleanos y enumeraciones se validan mediante listas permitidas; parámetros desconocidos, duplicados, fechas sin zona, ventanas invertidas y límites inválidos se rechazan.

Auditoría conserva su contrato específico `from`/`to`, categorías, actor y correlación. La historia GPS usa cursor durable y watermark, sin sustituirse por paginación offset. Documentos exige sujeto autorizado para listar; los trabajos de reporte pertenecen exclusivamente a su creador.

| Servicio / ruta GET | Parámetros de consulta publicados |
| --- | --- |
| `ms_alertas` · `/api/v1/alert-policies` | `page`, `page_size`, `q`, `severity`, `escalation_role`, `active`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_alertas` · `/api/v1/alert-subscriptions` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_alertas` · `/api/v1/alerts` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_alertas` · `/api/v1/alerts/{identifier}/deliveries` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_auditoria` · `/api/v1/documentary-events` | `page`, `page_size` |
| `ms_auditoria` · `/api/v1/events` | `page`, `page_size`, `from`, `to`, `categories`, `action`, `actor`, `institution_id`, `resource`, `result`, `correlation_id`, `q` |
| `ms_auditoria` · `/api/v1/findings` | `page`, `page_size`, `status`, `priority`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_compatibilidad` · `/api/v1/evaluations` | `page`, `page_size`, `request_id`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_compatibilidad` · `/api/v1/laboratory/profiles` | `page`, `page_size`, `q`, `kind`, `synthetic`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_compatibilidad` · `/api/v1/laboratory/results` | `page`, `page_size`, `sample_id`, `status`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_compatibilidad` · `/api/v1/laboratory/samples` | `page`, `page_size`, `q`, `status`, `resource_id`, `recipient_id`, `donation_id`, `profile_id`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_documentos` · `/api/v1/documents` | `page`, `page_size`, `subject_kind`, `subject_id`, `category`, `legal_hold`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_documentos` · `/api/v1/export-jobs` | `page`, `page_size`, `q`, `report`, `format`, `status`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_documentos` · `/api/v1/shipments/{identifier}/files` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_donantes` · `/api/v1/appointments` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_donantes` · `/api/v1/campaign-slots` | `page`, `page_size`, `campaign_id`, `q`, `site_id`, `active`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_donantes` · `/api/v1/campaigns` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_donantes` · `/api/v1/donations` | `page`, `page_size`, `q`, `kind`, `status`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_donantes` · `/api/v1/donors` | `page`, `page_size`, `q`, `status`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_donantes` · `/api/v1/donors/{identifier}/consents` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_identidad_acceso` · `/api/v1/accreditations` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_identidad_acceso` · `/api/v1/audit-assignees` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_identidad_acceso` · `/api/v1/catalogues/capacities` | `page`, `page_size`, `q`, `active` |
| `ms_identidad_acceso` · `/api/v1/catalogues/contacts` | `page`, `page_size`, `q`, `active` |
| `ms_identidad_acceso` · `/api/v1/catalogues/locations` | `page`, `page_size`, `q`, `active` |
| `ms_identidad_acceso` · `/api/v1/catalogues/responsibles` | `page`, `page_size`, `q`, `active` |
| `ms_identidad_acceso` · `/api/v1/catalogues/schedules` | `page`, `page_size`, `q`, `active` |
| `ms_identidad_acceso` · `/api/v1/catalogues/services` | `page`, `page_size`, `q`, `active` |
| `ms_identidad_acceso` · `/api/v1/catalogues/sites` | `page`, `page_size`, `q`, `active` |
| `ms_identidad_acceso` · `/api/v1/devices` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_identidad_acceso` · `/api/v1/institutions` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_identidad_acceso` · `/api/v1/users` | `page`, `page_size`, `q`, `role`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_inventario` · `/api/v1/availability` | `page`, `page_size` |
| `ms_inventario` · `/api/v1/cold/equipment` | `page`, `page_size`, `q`, `active`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_inventario` · `/api/v1/cold/profiles` | `page`, `page_size`, `q`, `kind`, `synthetic`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_inventario` · `/api/v1/external-mappings` | `page`, `page_size`, `q`, `external_id`, `resource_id`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_inventario` · `/api/v1/reservations` | `page`, `page_size`, `status`, `request_id`, `q`, `unplanned`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_inventario` · `/api/v1/resource-destinations` | `page`, `page_size`, `resource_id`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_inventario` · `/api/v1/resources` | `page`, `page_size`, `q`, `kind`, `status`, `blood_group`, `component`, `current_institution_id`, `expiry`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_inventario` · `/api/v1/resources/{identifier}/cold-readings` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_priorizacion_geografia` · `/api/v1/allocation-proposals` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_priorizacion_geografia` · `/api/v1/rankings` | `page`, `page_size`, `evaluation_id`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_priorizacion_geografia` · `/api/v1/routes` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_receptores` · `/api/v1/recipients` | `page`, `page_size`, `q`, `kind`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_receptores` · `/api/v1/requests` | `page`, `page_size`, `kind`, `status`, `from_at`, `until_at`, `date_field`, `sort`, `q` |
| `ms_receptores` · `/api/v1/requests/{identifier}/external-authorizations` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_transporte` · `/api/v1/documents` | `page`, `page_size`, `subject_kind`, `subject_id`, `category`, `legal_hold`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_transporte` · `/api/v1/export-jobs` | `page`, `page_size`, `q`, `report`, `format`, `status`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_transporte` · `/api/v1/shipments` | `page`, `page_size`, `from_at`, `until_at`, `date_field`, `sort`, `status`, `q` |
| `ms_transporte` · `/api/v1/shipments/{identifier}/files` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_transporte` · `/api/v1/shipments/{identifier}/telemetry` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_transporte` · `/api/v1/shipments/{identifier}/tracking/assignments` | `page`, `page_size`, `q`, `from_at`, `until_at`, `date_field`, `sort` |
| `ms_transporte` · `/api/v1/shipments/{identifier}/tracking/history` | `cursor`, `through`, `limit` |
| `ms_transporte` · `/api/v1/shipments/{identifier}/tracking/snapshot` | `cursor` |
| `ms_transporte` · `/api/v1/sync/changes` | `cursor` |
| `ms_transporte` · `/api/v1/sync/shipments/{identifier}/changes` | `cursor` |
| `servicio_monitoreo` · `/api/v1/checks` | `page`, `page_size` |

Pruebas: `test_extension_search_time_sort_and_tenant`, `test_report_window_applies_before_limit`, `test_all_report_families_formats_private_jobs_and_retries`, `test_normalized_http_wss_and_durable_history`, más contratos y regresión de cada propietario. El resultado de ejecución se registra en la matriz de cierre; esta tabla describe el contrato, no acredita por sí sola su aceptación.
