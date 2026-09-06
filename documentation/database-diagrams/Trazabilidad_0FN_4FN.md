# Trazabilidad del modelo 0FN a 4FN

> Estado: normalización lógica desarrollada para el ejercicio académico, bajo las dependencias y decisiones declaradas. No es una base instalada, un modelo físico aprobado ni una validación clínica.

Origen inalterado: [Modelo_0FN.md](./Modelo_0FN.md). Resultado: [Modelo_4FN.md](./Modelo_4FN.md).

Cada una de las 208 filas siguientes corresponde a un atributo de las 18 estructuras originales. Cuando el origen es una lista u objeto, se indican sus relaciones hijas; sus subcampos están definidos en los diagramas completos. Los identificadores y columnas añadidos para distinguir elementos, versiones y sucesos son decisiones de atomización, no requisitos clínicos nuevos.

Las fronteras de MongoDB, Redis y archivos se mantienen documentadas en la 4FN. Una referencia histórica no se elimina como si fuera una redundancia actual. Las derivaciones —institución desde sede, tipo desde recurso, frecuencia desde ocurrencias y cupo desde citas— se señalan para distinguir información reconstruible de un dato descartado.

| Atributo 0FN | Destino lógico 4FN | Transformación o conservación |
| --- | --- | --- |
| `INSTITUTION.institution_code` | `INSTITUTION.institution_code` | Clave candidata regional propuesta. |
| `INSTITUTION.institution_name` | `INSTITUTION.institution_name` | Descomposición en hechos atómicos. |
| `INSTITUTION.institution_type` | `INSTITUTION.institution_type` | Descomposición en hechos atómicos. |
| `INSTITUTION.region_name` | `INSTITUTION.region_name` | Descomposición en hechos atómicos. |
| `INSTITUTION.participation_status` | `INSTITUTION.participation_status` | Descomposición en hechos atómicos. |
| `INSTITUTION.main_address` | `INSTITUTION.street`, `INSTITUTION.street_number`, `INSTITUTION.city`, `INSTITUTION.postal_code`, `INSTITUTION.latitude`, `INSTITUTION.longitude` | Dirección descompuesta; precisión y campos autorizados pendientes del diseño físico. |
| `INSTITUTION.contacts` | `CONTACT`, `CONTACT_METHOD`, `INSTITUTION_CONTACT` | Descomposición en hechos atómicos. |
| `INSTITUTION.sites` | `SITE`, `SITE_CONTACT`, `SITE_SCHEDULE`, `SITE_CAPABILITY` | Descomposición en hechos atómicos. |
| `INSTITUTION.declared_capabilities` | `CAPABILITY`, `INSTITUTION_CAPABILITY` | Descomposición en hechos atómicos. |
| `INSTITUTION.administrative_settings` | `INSTITUTION_SETTING`, `PARAMETER_VERSION` | Descomposición en hechos atómicos. |
| `INSTITUTION.participation_history` | `INSTITUTION_EVENT` | Descomposición en hechos atómicos. |
| `INSTITUTION.registered_at` | `INSTITUTION.registered_at` | Descomposición en hechos atómicos. |
| `USER_ACCOUNT.account_reference` | `USER_ACCOUNT.account_reference` | Descomposición en hechos atómicos. |
| `USER_ACCOUNT.display_name` | `PARTY.party_name`, `USER_ACCOUNT.party_id` | La identidad de actor se comparte sin duplicar el nombre en la cuenta. |
| `USER_ACCOUNT.login_email` | `USER_ACCOUNT.login_email` | Descomposición en hechos atómicos. |
| `USER_ACCOUNT.password_hash` | `USER_ACCOUNT.password_hash` | Únicamente hash; no contraseñas ni tokens reutilizables. |
| `USER_ACCOUNT.account_status` | `USER_ACCOUNT.account_status` | Descomposición en hechos atómicos. |
| `USER_ACCOUNT.contact_details` | `ACCOUNT_CONTACT`, `CONTACT`, `CONTACT_METHOD` | Descomposición en hechos atómicos. |
| `USER_ACCOUNT.role_assignments` | `ACCOUNT_ROLE`, `ROLE`, `PERMISSION`, `ACCESS_GRANT`, `ACCESS_SCOPE`, `INSTITUTION_SCOPE`, `SITE_SCOPE`, `REGIONAL_SCOPE` | El permiso queda unido al rol y ámbito concretos; no hay producto cartesiano de autorizaciones. |
| `USER_ACCOUNT.account_changes` | `ACCOUNT_EVENT`, `AUDIT_EVENT`, `AUDIT_FIELD_CHANGE` | Descomposición en hechos atómicos. |
| `USER_ACCOUNT.notification_preferences` | `NOTIFICATION_PREFERENCE` | Descomposición en hechos atómicos. |
| `USER_ACCOUNT.registered_at` | `USER_ACCOUNT.registered_at` | Descomposición en hechos atómicos. |
| `REFERENCE_CATALOG.catalog_reference` | `REFERENCE_CATALOG.catalog_reference` | Descomposición en hechos atómicos. |
| `REFERENCE_CATALOG.catalog_name` | `REFERENCE_CATALOG.catalog_name` | Descomposición en hechos atómicos. |
| `REFERENCE_CATALOG.catalog_purpose` | `REFERENCE_CATALOG.catalog_purpose` | Descomposición en hechos atómicos. |
| `REFERENCE_CATALOG.catalog_version` | `CATALOG_VERSION.version_no` | Identificador lógico de versión; no se exige que el rótulo original sea numérico. |
| `REFERENCE_CATALOG.catalog_status` | `CATALOG_VERSION.catalog_status` | Descomposición en hechos atómicos. |
| `REFERENCE_CATALOG.administrative_scope` | `CATALOG_VERSION.scope_id`, `ACCESS_SCOPE` | Descomposición en hechos atómicos. |
| `REFERENCE_CATALOG.entries` | `CATALOG_ENTRY`, `CATALOG_ENTRY_VALUE` | Descomposición en hechos atómicos. |
| `REFERENCE_CATALOG.parameter_definitions` | `CATALOG_PARAMETER`, `PARAMETER_VERSION` | Descomposición en hechos atómicos. |
| `REFERENCE_CATALOG.change_history` | `CATALOG_CHANGE`, `CATALOG_CHANGED_ENTRY`, `CATALOG_CHANGE_FIELD` | Descomposición en hechos atómicos. |
| `DONOR.donor_reference` | `DONOR.donor_reference` | Descomposición en hechos atómicos. |
| `DONOR.registration_status` | `DONOR.registration_status` | Descomposición en hechos atómicos. |
| `DONOR.identity_details` | `DONOR.full_name`, `DONOR.birth_date` | Perfil mínimo propuesto; no se incorpora un identificador nacional obligatorio. |
| `DONOR.contact_methods` | `DONOR_CONTACT`, `CONTACT`, `CONTACT_METHOD` | Descomposición en hechos atómicos. |
| `DONOR.institution_details` | `DONOR_INSTITUTION`, `INSTITUTION` | Descomposición en hechos atómicos. |
| `DONOR.consents` | `DONOR_CONSENT`, `DOCUMENT_VERSION` | Descomposición en hechos atómicos. |
| `DONOR.preliminary_evaluations` | `PRELIMINARY_EVALUATION`, `PRELIMINARY_ANSWER` | Descomposición en hechos atómicos. |
| `DONOR.eligibility_decisions` | `ELIGIBILITY_DECISION`, `RULE_VERSION` | Descomposición en hechos atómicos. |
| `DONOR.blood_donation_history` | `BLOOD_DONATION`, `BLOOD_DONATION_SAMPLE`, `DONATION_INCIDENT`, `BLOOD_UNIT` | Descomposición en hechos atómicos. |
| `DONOR.organ_donation_history` | `ORGAN_DONATION_PROCESS`, `ORGAN_PROCESS_AUTHORIZATION`, `ORGAN_PROCESS_EVENT`, `ORGAN_AVAILABILITY` | Descomposición en hechos atómicos. |
| `DONOR.blood_studies` | `STUDY_SUBJECT`, `DONOR_SUBJECT`, `CLINICAL_TEST`, `TEST_SAMPLE`, `TEST_REVISION`, `BLOOD_OBSERVATION`, `ORGAN_OBSERVATION`, `HLA_CALL`, `TEST_DOCUMENT` | Conjuntos distintos por study_kind; no se convierten HLA ni resultados compuestos en listas de texto. |
| `DONOR.organ_studies` | `STUDY_SUBJECT`, `DONOR_SUBJECT`, `CLINICAL_TEST`, `TEST_SAMPLE`, `TEST_REVISION`, `BLOOD_OBSERVATION`, `ORGAN_OBSERVATION`, `HLA_CALL`, `TEST_DOCUMENT` | Conjuntos distintos por study_kind; no se convierten HLA ni resultados compuestos en listas de texto. |
| `DONOR.record_changes` | `DONOR_EVENT`, `AUDIT_EVENT`, `AUDIT_FIELD_CHANGE` | Descomposición en hechos atómicos. |
| `DONOR.registered_at` | `DONOR.registered_at` | Descomposición en hechos atómicos. |
| `CAMPAIGN.campaign_reference` | `CAMPAIGN.campaign_reference` | Descomposición en hechos atómicos. |
| `CAMPAIGN.campaign_name` | `CAMPAIGN.campaign_name` | Descomposición en hechos atómicos. |
| `CAMPAIGN.donation_process` | `CAMPAIGN.donation_process` | Descomposición en hechos atómicos. |
| `CAMPAIGN.publication_status` | `CAMPAIGN.publication_status` | Descomposición en hechos atómicos. |
| `CAMPAIGN.description` | `CAMPAIGN.description` | Descomposición en hechos atómicos. |
| `CAMPAIGN.organizing_institution` | `CAMPAIGN.institution_id`, `INSTITUTION`, `INSTITUTION_CONTACT` | Descomposición en hechos atómicos. |
| `CAMPAIGN.campaign_period` | `CAMPAIGN.starts_at`, `CAMPAIGN.ends_at` | Descomposición en hechos atómicos. |
| `CAMPAIGN.available_slots` | `CAMPAIGN_SLOT`, `SITE`, `SLOT_CONDITION` | Disponibilidad de cupo derivada de capacidad y citas activas; no es un segundo contador autoritativo. |
| `CAMPAIGN.published_conditions` | `CAMPAIGN_CONDITION` | Descomposición en hechos atómicos. |
| `CAMPAIGN.publication_changes` | `CAMPAIGN_EVENT`, `AUDIT_FIELD_CHANGE` | Descomposición en hechos atómicos. |
| `APPOINTMENT.appointment_reference` | `APPOINTMENT.appointment_reference` | Descomposición en hechos atómicos. |
| `APPOINTMENT.current_status` | `APPOINTMENT.current_status` | Descomposición en hechos atómicos. |
| `APPOINTMENT.donor_details` | `APPOINTMENT.donor_id`, `DONOR`, `DONOR_CONTACT` | Descomposición en hechos atómicos. |
| `APPOINTMENT.institution_details` | `APPOINTMENT.site_id`, `SITE`, `INSTITUTION` | Descomposición en hechos atómicos. |
| `APPOINTMENT.campaign_details` | `APPOINTMENT_CAMPAIGN`, `CAMPAIGN_SLOT`, `CAMPAIGN` | La fila asociativa puede faltar; no se inventa una campaña para una cita independiente. |
| `APPOINTMENT.scheduled_at` | `APPOINTMENT.scheduled_at` | Descomposición en hechos atómicos. |
| `APPOINTMENT.status_history` | `APPOINTMENT_STATUS_EVENT` | Descomposición en hechos atómicos. |
| `APPOINTMENT.schedule_changes` | `APPOINTMENT_RESCHEDULE` | Descomposición en hechos atómicos. |
| `APPOINTMENT.notice_history` | `APPOINTMENT_NOTICE`, `ALERT_DELIVERY`, `DELIVERY_ATTEMPT`, `DELIVERY_RECEIPT` | Descomposición en hechos atómicos. |
| `APPOINTMENT.created_at` | `APPOINTMENT.created_at` | Descomposición en hechos atómicos. |
| `RECIPIENT.recipient_reference` | `RECIPIENT.recipient_reference` | Descomposición en hechos atómicos. |
| `RECIPIENT.record_status` | `RECIPIENT.record_status` | Descomposición en hechos atómicos. |
| `RECIPIENT.identity_details` | `RECIPIENT.full_name`, `RECIPIENT.birth_date` | No crea automáticamente cuenta ni vinculación con un donante de nombre parecido. |
| `RECIPIENT.contact_methods` | `RECIPIENT_CONTACT`, `CONTACT`, `CONTACT_METHOD` | Descomposición en hechos atómicos. |
| `RECIPIENT.care_institutions` | `CARE_EPISODE`, `INSTITUTION` | Descomposición en hechos atómicos. |
| `RECIPIENT.authorized_professionals` | `CARE_PROFESSIONAL`, `PROFESSIONAL_AUTHORIZATION`, `PARTY` | Descomposición en hechos atómicos. |
| `RECIPIENT.consents` | `RECIPIENT_CONSENT`, `DOCUMENT_VERSION` | Descomposición en hechos atómicos. |
| `RECIPIENT.blood_needs` | `RECIPIENT_BLOOD_NEED` | Descomposición en hechos atómicos. |
| `RECIPIENT.organ_waiting_processes` | `ORGAN_WAITING_PROCESS`, `WAITING_EVENT` | Descomposición en hechos atómicos. |
| `RECIPIENT.blood_studies` | `STUDY_SUBJECT`, `RECIPIENT_SUBJECT`, `CLINICAL_TEST`, `TEST_SAMPLE`, `TEST_REVISION`, `BLOOD_OBSERVATION`, `ORGAN_OBSERVATION`, `HLA_CALL`, `TEST_DOCUMENT` | Descomposición en hechos atómicos. |
| `RECIPIENT.organ_studies` | `STUDY_SUBJECT`, `RECIPIENT_SUBJECT`, `CLINICAL_TEST`, `TEST_SAMPLE`, `TEST_REVISION`, `BLOOD_OBSERVATION`, `ORGAN_OBSERVATION`, `HLA_CALL`, `TEST_DOCUMENT` | Descomposición en hechos atómicos. |
| `RECIPIENT.care_history` | `CARE_EVENT`, `AUDIT_EVENT`, `AUDIT_FIELD_CHANGE` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.unit_reference` | `BLOOD_UNIT.unit_reference` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.traceability_code` | `RESOURCE.traceability_code` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.current_status` | `BLOOD_UNIT.current_status` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.institution_details` | `BLOOD_UNIT.location_id`, `STORAGE_LOCATION`, `SITE`, `INSTITUTION` | Se obtiene la institución custodiante desde la ubicación, sin copiarla en la unidad. |
| `BLOOD_UNIT.component_details` | `BLOOD_COMPONENT`, `COMPONENT_ATTRIBUTE` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.donation_origin` | `BLOOD_UNIT.donation_id`, `BLOOD_DONATION`, `DONOR_INSTITUTION`, `BLOOD_ORIGIN` | La referencia interna puede faltar en el MVP; BLOOD_ORIGIN identifica un origen externo autorizado sin inventar un donante. |
| `BLOOD_UNIT.blood_classification` | `BLOOD_CLASSIFICATION`, `TEST_REVISION` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.location_details` | `BLOOD_UNIT.location_id`, `STORAGE_LOCATION` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.collected_at` | `BLOOD_UNIT.collected_at` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.expires_at` | `BLOOD_UNIT.expires_at` | Fecha registrada; no se deriva mediante una regla clínica inventada. |
| `BLOOD_UNIT.expiry_parameter` | `BLOOD_UNIT.expiry_parameter_version_id`, `PARAMETER_VERSION` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.test_results` | `STUDY_SUBJECT`, `RESOURCE_SUBJECT`, `CLINICAL_TEST`, `TEST_SAMPLE`, `SAMPLE`, `TEST_REVISION`, `BLOOD_OBSERVATION`, `TEST_DOCUMENT` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.movement_history` | `BLOOD_MOVEMENT` | Descomposición en hechos atómicos. |
| `BLOOD_UNIT.label_prints` | `LABEL_PRINT`, `DOCUMENT_TEMPLATE_VERSION` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.organ_reference` | `ORGAN_AVAILABILITY.organ_reference` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.traceability_code` | `RESOURCE.traceability_code` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.organ_type` | `ORGAN_AVAILABILITY.organ_type` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.availability_status` | `ORGAN_AVAILABILITY.availability_status` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.institution_details` | `ORGAN_AVAILABILITY.location_id`, `STORAGE_LOCATION`, `SITE`, `INSTITUTION` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.donation_process_details` | `ORGAN_AVAILABILITY.process_id`, `ORGAN_DONATION_PROCESS` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.location_details` | `ORGAN_AVAILABILITY.location_id`, `STORAGE_LOCATION` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.viability_information` | `ORGAN_CURRENT_VIABILITY`, `ORGAN_VIABILITY_RECORD` | Referencia explícita al registro vigente, conservando los previos; sin condiciones médicas nuevas. |
| `ORGAN_AVAILABILITY.required_authorizations` | `ORGAN_AUTHORIZATION`, `PROFESSIONAL_AUTHORIZATION` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.test_results` | `STUDY_SUBJECT`, `RESOURCE_SUBJECT`, `CLINICAL_TEST`, `TEST_SAMPLE`, `SAMPLE`, `TEST_REVISION`, `ORGAN_OBSERVATION`, `HLA_CALL`, `TEST_DOCUMENT` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.availability_history` | `ORGAN_EVENT` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.related_documents` | `ORGAN_DOCUMENT` | Descomposición en hechos atómicos. |
| `ORGAN_AVAILABILITY.last_updated_at` | `ORGAN_AVAILABILITY.last_updated_at` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.request_reference` | `RESOURCE_REQUEST.request_reference` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.resource_kind` | `RESOURCE_REQUEST.resource_kind` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.current_status` | `RESOURCE_REQUEST.current_status` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.recorded_urgency` | `RESOURCE_REQUEST.recorded_urgency` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.recipient_details` | `RESOURCE_REQUEST.recipient_id`, `RECIPIENT` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.requesting_institution` | `RESOURCE_REQUEST.requesting_institution_id`, `INSTITUTION`, `INSTITUTION_CONTACT` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.requesting_professional` | `REQUEST_AUTHORSHIP`, `PROFESSIONAL_AUTHORIZATION`, `PARTY` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.blood_requirements` | `BLOOD_REQUIREMENT`, `BLOOD_COMPONENT` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.organ_requirement` | `ORGAN_REQUIREMENT` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.supporting_studies` | `REQUEST_STUDY`, `TEST_REVISION` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.urgency_history` | `REQUEST_URGENCY_EVENT` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.status_history` | `REQUEST_STATUS_EVENT` | Descomposición en hechos atómicos. |
| `RESOURCE_REQUEST.requested_at` | `RESOURCE_REQUEST.requested_at` | Descomposición en hechos atómicos. |
| `CANDIDATE_ASSESSMENT.assessment_reference` | `CANDIDATE_ASSESSMENT.assessment_reference` | Descomposición en hechos atómicos. |
| `CANDIDATE_ASSESSMENT.assessment_status` | `CANDIDATE_ASSESSMENT.assessment_status` | Descomposición en hechos atómicos. |
| `CANDIDATE_ASSESSMENT.resource_kind` | `CANDIDATE_ASSESSMENT.request_id`, `RESOURCE_REQUEST.resource_kind` | Tipo estable de la solicitud; la revisión conserva los valores evaluados en ASSESSMENT_INPUT. |
| `CANDIDATE_ASSESSMENT.request_details` | `CANDIDATE_ASSESSMENT.request_id`, `ASSESSMENT_INPUT` | El vínculo actual no sustituye la copia atómica inmutable de las entradas evaluadas. |
| `CANDIDATE_ASSESSMENT.requesting_user` | `CANDIDATE_ASSESSMENT.requesting_grant_id`, `ACCESS_GRANT`, `ACCOUNT_ROLE`, `USER_ACCOUNT` | Descomposición en hechos atómicos. |
| `CANDIDATE_ASSESSMENT.applied_rules` | `ASSESSMENT_RULE`, `RULE_VERSION` | Descomposición en hechos atómicos. |
| `CANDIDATE_ASSESSMENT.input_information` | `ASSESSMENT_INPUT` | Descomposición en hechos atómicos. |
| `CANDIDATE_ASSESSMENT.candidates` | `ASSESSMENT_CANDIDATE`, `CANDIDATE_COMPATIBILITY`, `CANDIDATE_FACTOR`, `CANDIDATE_GEOGRAPHY`, `CANDIDATE_ISSUE`, `ASSESSMENT_INPUT` | Descomposición en hechos atómicos. |
| `CANDIDATE_ASSESSMENT.human_reviews` | `CANDIDATE_REVIEW`, `REVIEW_EVIDENCE` | Descomposición en hechos atómicos. |
| `CANDIDATE_ASSESSMENT.missing_information` | `ASSESSMENT_ISSUE` | Descomposición en hechos atómicos. |
| `CANDIDATE_ASSESSMENT.generated_at` | `CANDIDATE_ASSESSMENT.generated_at` | Descomposición en hechos atómicos. |
| `ALLOCATION.allocation_reference` | `ALLOCATION.allocation_reference` | Descomposición en hechos atómicos. |
| `ALLOCATION.operation_type` | `ALLOCATION.operation_type` | Descomposición en hechos atómicos. |
| `ALLOCATION.allocation_status` | `ALLOCATION.allocation_status` | Descomposición en hechos atómicos. |
| `ALLOCATION.resource_kind` | `ALLOCATION.resource_id`, `RESOURCE.resource_kind` | Descomposición en hechos atómicos. |
| `ALLOCATION.request_details` | `ALLOCATION.request_id`, `RESOURCE_REQUEST`, `RECIPIENT` | Descomposición en hechos atómicos. |
| `ALLOCATION.selected_blood_unit` | `ALLOCATION.resource_id`, `RESOURCE`, `BLOOD_UNIT`, `ORGAN_AVAILABILITY` | Un recurso y exactamente un subtipo; la selección no se representa con dos FK ambiguas. |
| `ALLOCATION.selected_organ` | `ALLOCATION.resource_id`, `RESOURCE`, `BLOOD_UNIT`, `ORGAN_AVAILABILITY` | Un recurso y exactamente un subtipo; la selección no se representa con dos FK ambiguas. |
| `ALLOCATION.assessment_details` | `ALLOCATION_ASSESSMENT`, `ASSESSMENT_CANDIDATE`, `CANDIDATE_ASSESSMENT` | Descomposición en hechos atómicos. |
| `ALLOCATION.reservation_period` | `ALLOCATION.reservation_starts_at`, `ALLOCATION.reservation_ends_at` | Descomposición en hechos atómicos. |
| `ALLOCATION.human_authorizations` | `ALLOCATION_AUTHORIZATION`, `ALLOCATION_EVIDENCE`, `PROFESSIONAL_AUTHORIZATION` | Descomposición en hechos atómicos. |
| `ALLOCATION.decision_history` | `ALLOCATION_EVENT` | Descomposición en hechos atómicos. |
| `ALLOCATION.operation_attempts` | `ALLOCATION_OPERATION`, `ALLOCATION_ATTEMPT`, `SYNC_OPERATION` | Descomposición en hechos atómicos. |
| `ALLOCATION.created_at` | `ALLOCATION.created_at` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.transfer_reference` | `TRANSFER_ORDER.transfer_reference` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.transfer_status` | `TRANSFER_ORDER.transfer_status` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.allocation_details` | `TRANSFER_ORDER.allocation_id`, `ALLOCATION` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.origin_details` | `TRANSFER_ORDER.origin_site_id`, `SITE`, `INSTITUTION`, `TRANSFER_CONTACT` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.destination_details` | `TRANSFER_ORDER.destination_site_id`, `SITE`, `INSTITUTION`, `TRANSFER_CONTACT` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.transfer_schedule` | `TRANSFER_ORDER.planned_collection_at`, `TRANSFER_ORDER.planned_delivery_at`, `TRANSFER_ORDER.collected_at`, `TRANSFER_ORDER.delivered_at` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.staff_assignments` | `TRANSFER_STAFF`, `PARTY` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.route_options` | `ROUTE_OPTION` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.selected_route` | `ROUTE_SELECTION`, `ROUTE_OPTION` | Selección vigente derivada del último evento de selección autorizado; se conserva su historia. |
| `TRANSFER_ORDER.scan_checks` | `SCAN_CHECK` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.custody_events` | `CUSTODY_EVENT`, `ALLOCATION`, `RESOURCE` | Recurso derivado de la asignación del traslado; no se cruza cada evento con todos los recursos. |
| `TRANSFER_ORDER.incidents` | `TRANSFER_INCIDENT`, `INCIDENT_ACTION` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.evidence_references` | `CUSTODY_EVIDENCE`, `CAPTURE_AUTHORIZATION`, `DOCUMENT_VERSION` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.synchronization_results` | `TRANSFER_SYNC`, `SYNC_OPERATION`, `SYNC_CONFLICT` | Descomposición en hechos atómicos. |
| `TRANSFER_ORDER.created_at` | `TRANSFER_ORDER.created_at` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.analysis_reference` | `INVENTORY_ANALYSIS.analysis_reference` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.analysis_type` | `INVENTORY_ANALYSIS.analysis_type` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.analysis_status` | `INVENTORY_ANALYSIS.analysis_status` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.regional_scope` | `ANALYSIS_INSTITUTION`, `INVENTORY_ANALYSIS.period_starts_at`, `INVENTORY_ANALYSIS.period_ends_at` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.method_details` | `INVENTORY_ANALYSIS.method_version_id`, `METHOD_VERSION` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.dataset_description` | `INVENTORY_ANALYSIS.source_reference`, `INVENTORY_ANALYSIS.is_synthetic`, `INVENTORY_ANALYSIS.period_starts_at`, `INVENTORY_ANALYSIS.period_ends_at` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.resource_inputs` | `INVENTORY_INPUT` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.expiry_forecasts` | `EXPIRY_FORECAST` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.balancing_proposals` | `BALANCING_PROPOSAL`, `BALANCING_FACTOR` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.human_reviews` | `ANALYSIS_REVIEW` | Descomposición en hechos atómicos. |
| `INVENTORY_ANALYSIS.generated_at` | `INVENTORY_ANALYSIS.generated_at` | Descomposición en hechos atómicos. |
| `ALERT.alert_reference` | `ALERT.alert_reference` | Descomposición en hechos atómicos. |
| `ALERT.alert_type` | `ALERT.alert_type` | Descomposición en hechos atómicos. |
| `ALERT.operational_priority` | `ALERT.operational_priority` | Descomposición en hechos atómicos. |
| `ALERT.alert_status` | `ALERT.alert_status` | Descomposición en hechos atómicos. |
| `ALERT.origin_details` | `ALERT.source_component`, `ALERT.origin_record_type`, `ALERT.origin_record_reference`, `ALERT.origin_event_reference` | Descomposición en hechos atómicos. |
| `ALERT.trigger_details` | `ALERT.rule_version_id`, `RULE_VERSION`, `ALERT.trigger_decision_reference` | Descomposición en hechos atómicos. |
| `ALERT.recipients` | `ALERT_RECIPIENT`, `ALERT_DELIVERY`, `DELIVERY_ATTEMPT`, `DELIVERY_RECEIPT` | Descomposición en hechos atómicos. |
| `ALERT.repeated_occurrences` | `ALERT_OCCURRENCE` | Frecuencia derivada de las ocurrencias, sin mantener otro contador autoritativo. |
| `ALERT.attention_history` | `ALERT_ATTENTION` | Descomposición en hechos atómicos. |
| `ALERT.created_at` | `ALERT.created_at` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.document_reference` | `DOCUMENT_RECORD.document_reference` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.document_purpose` | `DOCUMENT_RECORD.document_purpose` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.document_status` | `DOCUMENT_RECORD.document_status` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.owner_details` | `DOCUMENT_RECORD.owner_party_id`, `DOCUMENT_RECORD.owner_institution_id`, `PARTY`, `INSTITUTION` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.storage_metadata` | `DOCUMENT_CURRENT_VERSION`, `DOCUMENT_VERSION` | Puntero explícito a la versión vigente; cada versión conserva identidad del objeto, ruta, tipo, tamaño, hash y fecha; nunca el binario. |
| `DOCUMENT_RECORD.privacy_details` | `DOCUMENT_RECORD.privacy_classification`, `DOCUMENT_RECORD.retention_policy_reference`, `DOCUMENT_SCOPE` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.report_parameters` | `REPORT_DEFINITION`, `REPORT_FILTER`, `REPORT_SOURCE`, `DOCUMENT_TEMPLATE_VERSION` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.related_records` | `DOCUMENT_RELATION` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.version_history` | `DOCUMENT_VERSION` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.access_history` | `DOCUMENT_ACCESS` | Descomposición en hechos atómicos. |
| `DOCUMENT_RECORD.recorded_at` | `DOCUMENT_RECORD.recorded_at` | Descomposición en hechos atómicos. |
| `AUDIT_EVENT.event_reference` | `AUDIT_EVENT.event_reference` | Descomposición en hechos atómicos. |
| `AUDIT_EVENT.correlation_reference` | `AUDIT_EVENT.correlation_reference` | Descomposición en hechos atómicos. |
| `AUDIT_EVENT.source_component` | `AUDIT_EVENT.source_component` | Descomposición en hechos atómicos. |
| `AUDIT_EVENT.action` | `AUDIT_EVENT.action` | Descomposición en hechos atómicos. |
| `AUDIT_EVENT.result` | `AUDIT_EVENT.result` | Descomposición en hechos atómicos. |
| `AUDIT_EVENT.actor_details` | `AUDIT_EVENT.actor_id`, `PARTY`, `AUDIT_EVENT.performed_role_code`, `AUDIT_EVENT.performed_scope_reference` | Rol y ámbito son los observados al ejecutar, no los permisos actuales del actor. |
| `AUDIT_EVENT.affected_records` | `AUDIT_RECORD` | Descomposición en hechos atómicos. |
| `AUDIT_EVENT.authorized_change_details` | `AUDIT_FIELD_CHANGE` | Descomposición en hechos atómicos. |
| `AUDIT_EVENT.related_events` | `AUDIT_RELATION` | Descomposición en hechos atómicos. |
| `AUDIT_EVENT.occurred_at` | `AUDIT_EVENT.occurred_at` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.device_reference` | `MOBILE_DEVICE.device_reference` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.registration_status` | `MOBILE_DEVICE.registration_status` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.device_details` | `MOBILE_DEVICE.operating_system`, `MOBILE_DEVICE.application_version` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.account_registrations` | `DEVICE_REGISTRATION`, `ACCOUNT_ROLE`, `ACCESS_SCOPE` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.granted_capabilities` | `DEVICE_CAPABILITY_GRANT` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.synchronized_operations` | `DEVICE_OPERATION`, `SYNC_OPERATION` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.synchronization_conflicts` | `SYNC_CONFLICT` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.credential_cleanup_events` | `CREDENTIAL_CLEANUP` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.registered_at` | `MOBILE_DEVICE.registered_at` | Descomposición en hechos atómicos. |
| `MOBILE_DEVICE.last_activity_at` | `MOBILE_DEVICE.last_activity_at` | Descomposición en hechos atómicos. |

## Especificación y comprobación

[model.mjs](./normalization/model.mjs) declara los esquemas de las cuatro etapas y sus claves/DF; [lineage.mjs](./normalization/lineage.mjs) declara esta correspondencia. [render.mjs](./normalization/render.mjs) calcula los documentos sin escribir archivos. [validate.mjs](./normalization/validate.mjs) comprueba que no falte un atributo inicial, que todos los destinos existan y que cada tabla final provenga de al menos un grupo de la 0FN. Es una comprobación estructural, no una aprobación de todos los subcampos clínicos posibles.
