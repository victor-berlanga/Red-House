# Conteo de las 72 tablas físicas

Corte: `2026-10-21T14:35:12.186757+00:00`. Origen: [counts.json](counts.json). Los conteos de auditoría, sesiones y monitoreo siguen cambiando con el uso.

**38 tablas con al menos 30 filas; 34 excepciones justificadas.** Las tablas vacías pertenecen al modelo heredado conservado en el esquema. La aplicación utiliza sus tablas operativas y las vistas `access_*`; llenar las antiguas no agregaría registros a las pantallas.

| Tabla | Antes | Después | Resultado o motivo de excepción |
| --- | ---: | ---: | --- |
| `account_role` | 0 | 0 | Modelo heredado; el perfil actual se registra en user_account. |
| `algorithm_run` | 0 | 0 | Modelo heredado; las ejecuciones actuales usan candidate_evaluation, ranking_run y balance_proposal. |
| `allocation_operation` | 18 | 48 | Mínimo de 30 alcanzado. |
| `appointment` | 0 | 118 | Mínimo de 30 alcanzado. |
| `audit_change` | 0 | 0 | Modelo heredado; la auditoría actual usa audit_event y service_activity_events. |
| `audit_event` | 2444 | 5896 | Mínimo de 30 alcanzado. |
| `balance_proposal` | 0 | 30 | Mínimo de 30 alcanzado. |
| `blood_allocation` | 18 | 48 | Mínimo de 30 alcanzado. |
| `blood_candidate` | 0 | 0 | Modelo heredado; los candidatos se conservan dentro de candidate_evaluation. |
| `blood_classification` | 0 | 0 | Catálogo heredado ajeno al contrato operativo actual. |
| `blood_component` | 0 | 0 | Catálogo heredado ajeno al contrato operativo actual. |
| `blood_movement` | 86 | 391 | Mínimo de 30 alcanzado. |
| `blood_request` | 18 | 138 | Mínimo de 30 alcanzado. |
| `blood_review` | 18 | 78 | Mínimo de 30 alcanzado. |
| `blood_status_transition` | 4 | 4 | Cuatro transiciones declaradas; no se inventan estados. |
| `blood_unit` | 0 | 0 | Inventario actual en resource; no hay doble escritura. |
| `cache_revision` | 2 | 2 | Dos revisiones técnicas: catálogos e inventario. |
| `campaign` | 0 | 60 | Mínimo de 30 alcanzado. |
| `candidate_evaluation` | 18 | 78 | Mínimo de 30 alcanzado. |
| `capability` | 3 | 3 | Catálogo heredado cerrado; conserva sus tres capacidades. |
| `catalogue_entry` | 0 | 300 | Mínimo de 30 alcanzado. |
| `contact` | 0 | 0 | Catálogo actual en catalogue_entry, categoría contacts. |
| `contact_method` | 0 | 0 | Modelo de contactos heredado; la interfaz usa catalogue_entry. |
| `custody_chain` | 18 | 48 | Mínimo de 30 alcanzado. |
| `custody_event` | 93 | 213 | Mínimo de 30 alcanzado. |
| `donation` | 0 | 60 | Mínimo de 30 alcanzado. |
| `donation_event` | 0 | 120 | Mínimo de 30 alcanzado. |
| `donation_unit` | 0 | 0 | Relación vigente mediante resource.donation_id. |
| `donor` | 0 | 68 | Mínimo de 30 alcanzado. |
| `donor_review` | 0 | 64 | Mínimo de 30 alcanzado. |
| `institution` | 2 | 30 | Mínimo de 30 alcanzado. |
| `institution_capability` | 0 | 0 | Capacidades actuales en catalogue_entry, categoría capacities. |
| `institution_contact` | 0 | 0 | Contactos actuales en catalogue_entry, categoría contacts. |
| `login_attempt` | 0 | 0 | Tabla heredada sin escrituras del contrato vigente; no se provocan fallos para llenarla. |
| `notification` | 270 | 986 | Mínimo de 30 alcanzado. |
| `organ_allocation` | 0 | 0 | Asignaciones actuales en blood_allocation, vinculadas a recursos de tipo ORGAN. |
| `organ_candidate` | 0 | 0 | Candidatos actuales dentro de candidate_evaluation para solicitudes de órganos. |
| `organ_custody_event` | 0 | 0 | Custodia actual de ambos tipos en custody_event. |
| `organ_donor` | 0 | 0 | Tabla del modelo histórico; no utilizada por las API actuales. |
| `organ_evaluation` | 0 | 0 | Evaluaciones actuales en candidate_evaluation con distinción de tipo. |
| `organ_offer` | 0 | 0 | Inventario de órganos actual en resource, tipo ORGAN. |
| `organ_recipient` | 0 | 0 | Receptores actuales en recipient, tipo ORGAN. |
| `organ_review` | 0 | 0 | Revisiones actuales en blood_review, vinculadas a evaluaciones de órganos. |
| `parameter_version` | 0 | 0 | No se crean versiones de reglas clínicas sin validación. |
| `party` | 0 | 0 | Modelo histórico de personas; las API actuales usan donor, recipient y user_account. |
| `ranking_run` | 15 | 75 | Mínimo de 30 alcanzado. |
| `recipient` | 18 | 138 | Mínimo de 30 alcanzado. |
| `regional_route` | 1 | 32 | Mínimo de 30 alcanzado. |
| `request_event` | 0 | 0 | Historial heredado; las operaciones actuales emiten eventos de auditoría. |
| `request_hold` | 18 | 48 | Mínimo de 30 alcanzado. |
| `resource` | 20 | 140 | Mínimo de 30 alcanzado. |
| `resource_review` | 18 | 138 | Mínimo de 30 alcanzado. |
| `role` | 7 | 7 | Siete perfiles autorizados; no se crean roles adicionales. |
| `schema_migration` | 6 | 6 | Historial real de seis migraciones; no son datos de demostración. |
| `service_activity_events` | 2444 | 5896 | Mínimo de 30 alcanzado. |
| `service_decisions` | 18 | 48 | Mínimo de 30 alcanzado. |
| `service_health_check` | 10511 | 12062 | Mínimo de 30 alcanzado. |
| `service_idempotency` | 225 | 1987 | Mínimo de 30 alcanzado. |
| `service_inbox` | 2804 | 6978 | Mínimo de 30 alcanzado. |
| `service_outbox` | 5436 | 13352 | Mínimo de 30 alcanzado. |
| `service_schema_version` | 33 | 33 | Mínimo de 30 alcanzado. |
| `service_worker_health` | 11 | 11 | Un registro por servicio: once propietarios. |
| `shipment` | 18 | 48 | Mínimo de 30 alcanzado. |
| `shipment_transition` | 75 | 165 | Mínimo de 30 alcanzado. |
| `site` | 0 | 0 | Sedes actuales en catalogue_entry, categoría sites. |
| `site_schedule` | 0 | 0 | Horarios actuales en catalogue_entry, categoría schedules. |
| `storage_location` | 0 | 0 | Ubicaciones actuales en catalogue_entry, categoría locations. |
| `stored_file` | 3 | 33 | Mínimo de 30 alcanzado. |
| `transport_telemetry` | 0 | 50 | Mínimo de 30 alcanzado. |
| `user_account` | 14 | 30 | Mínimo de 30 alcanzado. |
| `web_session` | 278 | 327 | Mínimo de 30 alcanzado. |
| `web_runtime.session_revocations` | 16 | 26 | Marcas técnicas de cierre con ciclo de vida propio; no se fabrican. |

Los nombres sin prefijo pertenecen a `red_house`. No se contabilizan vistas como tablas ni se crean filas en las tablas técnicas para alcanzar una cuota. [Resultados y comprobaciones](RESULTADOS.md).
