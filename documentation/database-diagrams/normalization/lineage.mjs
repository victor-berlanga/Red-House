// Un destino por atributo de la 0FN; los destinos múltiples preservan subgrupos.
// La descripción humana y los esquemas completos se publican en Markdown.
export const lineage = {};
const L = (entity, rows) => {
  for (const line of rows.trim().split('\n')) {
    const [sources, targets, note = 'Descomposición en hechos atómicos.'] = line.split('|').map(x=>x.trim());
    for (const attribute of sources.split(' ')) lineage[`${entity}.${attribute}`] = {targets:targets.split(' '),note};
  }
};
L('INSTITUTION', `
institution_code | INSTITUTION.institution_code | Clave candidata regional propuesta.
institution_name | INSTITUTION.institution_name
institution_type | INSTITUTION.institution_type
region_name | INSTITUTION.region_name
participation_status | INSTITUTION.participation_status
main_address | INSTITUTION.street INSTITUTION.street_number INSTITUTION.city INSTITUTION.postal_code INSTITUTION.latitude INSTITUTION.longitude | Dirección descompuesta; precisión y campos autorizados pendientes del diseño físico.
contacts | CONTACT CONTACT_METHOD INSTITUTION_CONTACT
sites | SITE SITE_CONTACT SITE_SCHEDULE SITE_CAPABILITY
declared_capabilities | CAPABILITY INSTITUTION_CAPABILITY
administrative_settings | INSTITUTION_SETTING PARAMETER_VERSION
participation_history | INSTITUTION_EVENT
registered_at | INSTITUTION.registered_at
`);
L('USER_ACCOUNT', `
account_reference | USER_ACCOUNT.account_reference
display_name | PARTY.party_name USER_ACCOUNT.party_id | La identidad de actor se comparte sin duplicar el nombre en la cuenta.
login_email | USER_ACCOUNT.login_email
password_hash | USER_ACCOUNT.password_hash | Únicamente hash; no contraseñas ni tokens reutilizables.
account_status | USER_ACCOUNT.account_status
contact_details | ACCOUNT_CONTACT CONTACT CONTACT_METHOD
role_assignments | ACCOUNT_ROLE ROLE PERMISSION ACCESS_GRANT ACCESS_SCOPE INSTITUTION_SCOPE SITE_SCOPE REGIONAL_SCOPE | El permiso queda unido al rol y ámbito concretos; no hay producto cartesiano de autorizaciones.
account_changes | ACCOUNT_EVENT AUDIT_EVENT AUDIT_FIELD_CHANGE
notification_preferences | NOTIFICATION_PREFERENCE
registered_at | USER_ACCOUNT.registered_at
`);
L('REFERENCE_CATALOG', `
catalog_reference | REFERENCE_CATALOG.catalog_reference
catalog_name | REFERENCE_CATALOG.catalog_name
catalog_purpose | REFERENCE_CATALOG.catalog_purpose
catalog_version | CATALOG_VERSION.version_no | Identificador lógico de versión; no se exige que el rótulo original sea numérico.
catalog_status | CATALOG_VERSION.catalog_status
administrative_scope | CATALOG_VERSION.scope_id ACCESS_SCOPE
entries | CATALOG_ENTRY CATALOG_ENTRY_VALUE
parameter_definitions | CATALOG_PARAMETER PARAMETER_VERSION
change_history | CATALOG_CHANGE CATALOG_CHANGED_ENTRY CATALOG_CHANGE_FIELD
`);
L('DONOR', `
donor_reference | DONOR.donor_reference
registration_status | DONOR.registration_status
identity_details | DONOR.full_name DONOR.birth_date | Perfil mínimo propuesto; no se incorpora un identificador nacional obligatorio.
contact_methods | DONOR_CONTACT CONTACT CONTACT_METHOD
institution_details | DONOR_INSTITUTION INSTITUTION
consents | DONOR_CONSENT DOCUMENT_VERSION
preliminary_evaluations | PRELIMINARY_EVALUATION PRELIMINARY_ANSWER
eligibility_decisions | ELIGIBILITY_DECISION RULE_VERSION
blood_donation_history | BLOOD_DONATION BLOOD_DONATION_SAMPLE DONATION_INCIDENT BLOOD_UNIT
organ_donation_history | ORGAN_DONATION_PROCESS ORGAN_PROCESS_AUTHORIZATION ORGAN_PROCESS_EVENT ORGAN_AVAILABILITY
blood_studies organ_studies | STUDY_SUBJECT DONOR_SUBJECT CLINICAL_TEST TEST_SAMPLE TEST_REVISION BLOOD_OBSERVATION ORGAN_OBSERVATION HLA_CALL TEST_DOCUMENT | Conjuntos distintos por study_kind; no se convierten HLA ni resultados compuestos en listas de texto.
record_changes | DONOR_EVENT AUDIT_EVENT AUDIT_FIELD_CHANGE
registered_at | DONOR.registered_at
`);
L('CAMPAIGN', `
campaign_reference | CAMPAIGN.campaign_reference
campaign_name | CAMPAIGN.campaign_name
donation_process | CAMPAIGN.donation_process
publication_status | CAMPAIGN.publication_status
description | CAMPAIGN.description
organizing_institution | CAMPAIGN.institution_id INSTITUTION INSTITUTION_CONTACT
campaign_period | CAMPAIGN.starts_at CAMPAIGN.ends_at
available_slots | CAMPAIGN_SLOT SITE SLOT_CONDITION | Disponibilidad de cupo derivada de capacidad y citas activas; no es un segundo contador autoritativo.
published_conditions | CAMPAIGN_CONDITION
publication_changes | CAMPAIGN_EVENT AUDIT_FIELD_CHANGE
`);
L('APPOINTMENT', `
appointment_reference | APPOINTMENT.appointment_reference
current_status | APPOINTMENT.current_status
donor_details | APPOINTMENT.donor_id DONOR DONOR_CONTACT
institution_details | APPOINTMENT.site_id SITE INSTITUTION
campaign_details | APPOINTMENT_CAMPAIGN CAMPAIGN_SLOT CAMPAIGN | La fila asociativa puede faltar; no se inventa una campaña para una cita independiente.
scheduled_at | APPOINTMENT.scheduled_at
status_history | APPOINTMENT_STATUS_EVENT
schedule_changes | APPOINTMENT_RESCHEDULE
notice_history | APPOINTMENT_NOTICE ALERT_DELIVERY DELIVERY_ATTEMPT DELIVERY_RECEIPT
created_at | APPOINTMENT.created_at
`);
L('RECIPIENT', `
recipient_reference | RECIPIENT.recipient_reference
record_status | RECIPIENT.record_status
identity_details | RECIPIENT.full_name RECIPIENT.birth_date | No crea automáticamente cuenta ni vinculación con un donante de nombre parecido.
contact_methods | RECIPIENT_CONTACT CONTACT CONTACT_METHOD
care_institutions | CARE_EPISODE INSTITUTION
authorized_professionals | CARE_PROFESSIONAL PROFESSIONAL_AUTHORIZATION PARTY
consents | RECIPIENT_CONSENT DOCUMENT_VERSION
blood_needs | RECIPIENT_BLOOD_NEED
organ_waiting_processes | ORGAN_WAITING_PROCESS WAITING_EVENT
blood_studies organ_studies | STUDY_SUBJECT RECIPIENT_SUBJECT CLINICAL_TEST TEST_SAMPLE TEST_REVISION BLOOD_OBSERVATION ORGAN_OBSERVATION HLA_CALL TEST_DOCUMENT
care_history | CARE_EVENT AUDIT_EVENT AUDIT_FIELD_CHANGE
`);
L('BLOOD_UNIT', `
unit_reference | BLOOD_UNIT.unit_reference
traceability_code | RESOURCE.traceability_code
current_status | BLOOD_UNIT.current_status
institution_details | BLOOD_UNIT.location_id STORAGE_LOCATION SITE INSTITUTION | Se obtiene la institución custodiante desde la ubicación, sin copiarla en la unidad.
component_details | BLOOD_COMPONENT COMPONENT_ATTRIBUTE
donation_origin | BLOOD_UNIT.donation_id BLOOD_DONATION DONOR_INSTITUTION BLOOD_ORIGIN | La referencia interna puede faltar en el MVP; BLOOD_ORIGIN identifica un origen externo autorizado sin inventar un donante.
blood_classification | BLOOD_CLASSIFICATION TEST_REVISION
location_details | BLOOD_UNIT.location_id STORAGE_LOCATION
collected_at | BLOOD_UNIT.collected_at
expires_at | BLOOD_UNIT.expires_at | Fecha registrada; no se deriva mediante una regla clínica inventada.
expiry_parameter | BLOOD_UNIT.expiry_parameter_version_id PARAMETER_VERSION
test_results | STUDY_SUBJECT RESOURCE_SUBJECT CLINICAL_TEST TEST_SAMPLE SAMPLE TEST_REVISION BLOOD_OBSERVATION TEST_DOCUMENT
movement_history | BLOOD_MOVEMENT
label_prints | LABEL_PRINT DOCUMENT_TEMPLATE_VERSION
`);
L('ORGAN_AVAILABILITY', `
organ_reference | ORGAN_AVAILABILITY.organ_reference
traceability_code | RESOURCE.traceability_code
organ_type | ORGAN_AVAILABILITY.organ_type
availability_status | ORGAN_AVAILABILITY.availability_status
institution_details | ORGAN_AVAILABILITY.location_id STORAGE_LOCATION SITE INSTITUTION
donation_process_details | ORGAN_AVAILABILITY.process_id ORGAN_DONATION_PROCESS
location_details | ORGAN_AVAILABILITY.location_id STORAGE_LOCATION
viability_information | ORGAN_CURRENT_VIABILITY ORGAN_VIABILITY_RECORD | Referencia explícita al registro vigente, conservando los previos; sin condiciones médicas nuevas.
required_authorizations | ORGAN_AUTHORIZATION PROFESSIONAL_AUTHORIZATION
test_results | STUDY_SUBJECT RESOURCE_SUBJECT CLINICAL_TEST TEST_SAMPLE SAMPLE TEST_REVISION ORGAN_OBSERVATION HLA_CALL TEST_DOCUMENT
availability_history | ORGAN_EVENT
related_documents | ORGAN_DOCUMENT
last_updated_at | ORGAN_AVAILABILITY.last_updated_at
`);
L('RESOURCE_REQUEST', `
request_reference | RESOURCE_REQUEST.request_reference
resource_kind | RESOURCE_REQUEST.resource_kind
current_status | RESOURCE_REQUEST.current_status
recorded_urgency | RESOURCE_REQUEST.recorded_urgency
recipient_details | RESOURCE_REQUEST.recipient_id RECIPIENT
requesting_institution | RESOURCE_REQUEST.requesting_institution_id INSTITUTION INSTITUTION_CONTACT
requesting_professional | REQUEST_AUTHORSHIP PROFESSIONAL_AUTHORIZATION PARTY
blood_requirements | BLOOD_REQUIREMENT BLOOD_COMPONENT
organ_requirement | ORGAN_REQUIREMENT
supporting_studies | REQUEST_STUDY TEST_REVISION
urgency_history | REQUEST_URGENCY_EVENT
status_history | REQUEST_STATUS_EVENT
requested_at | RESOURCE_REQUEST.requested_at
`);
L('CANDIDATE_ASSESSMENT', `
assessment_reference | CANDIDATE_ASSESSMENT.assessment_reference
assessment_status | CANDIDATE_ASSESSMENT.assessment_status
resource_kind | CANDIDATE_ASSESSMENT.request_id RESOURCE_REQUEST.resource_kind | Tipo estable de la solicitud; la revisión conserva los valores evaluados en ASSESSMENT_INPUT.
request_details | CANDIDATE_ASSESSMENT.request_id ASSESSMENT_INPUT | El vínculo actual no sustituye la copia atómica inmutable de las entradas evaluadas.
requesting_user | CANDIDATE_ASSESSMENT.requesting_grant_id ACCESS_GRANT ACCOUNT_ROLE USER_ACCOUNT
applied_rules | ASSESSMENT_RULE RULE_VERSION
input_information | ASSESSMENT_INPUT
candidates | ASSESSMENT_CANDIDATE CANDIDATE_COMPATIBILITY CANDIDATE_FACTOR CANDIDATE_GEOGRAPHY CANDIDATE_ISSUE ASSESSMENT_INPUT
human_reviews | CANDIDATE_REVIEW REVIEW_EVIDENCE
missing_information | ASSESSMENT_ISSUE
generated_at | CANDIDATE_ASSESSMENT.generated_at
`);
L('ALLOCATION', `
allocation_reference | ALLOCATION.allocation_reference
operation_type | ALLOCATION.operation_type
allocation_status | ALLOCATION.allocation_status
resource_kind | ALLOCATION.resource_id RESOURCE.resource_kind
request_details | ALLOCATION.request_id RESOURCE_REQUEST RECIPIENT
selected_blood_unit selected_organ | ALLOCATION.resource_id RESOURCE BLOOD_UNIT ORGAN_AVAILABILITY | Un recurso y exactamente un subtipo; la selección no se representa con dos FK ambiguas.
assessment_details | ALLOCATION_ASSESSMENT ASSESSMENT_CANDIDATE CANDIDATE_ASSESSMENT
reservation_period | ALLOCATION.reservation_starts_at ALLOCATION.reservation_ends_at
human_authorizations | ALLOCATION_AUTHORIZATION ALLOCATION_EVIDENCE PROFESSIONAL_AUTHORIZATION
decision_history | ALLOCATION_EVENT
operation_attempts | ALLOCATION_OPERATION ALLOCATION_ATTEMPT SYNC_OPERATION
created_at | ALLOCATION.created_at
`);
L('TRANSFER_ORDER', `
transfer_reference | TRANSFER_ORDER.transfer_reference
transfer_status | TRANSFER_ORDER.transfer_status
allocation_details | TRANSFER_ORDER.allocation_id ALLOCATION
origin_details | TRANSFER_ORDER.origin_site_id SITE INSTITUTION TRANSFER_CONTACT
destination_details | TRANSFER_ORDER.destination_site_id SITE INSTITUTION TRANSFER_CONTACT
transfer_schedule | TRANSFER_ORDER.planned_collection_at TRANSFER_ORDER.planned_delivery_at TRANSFER_ORDER.collected_at TRANSFER_ORDER.delivered_at
staff_assignments | TRANSFER_STAFF PARTY
route_options | ROUTE_OPTION
selected_route | ROUTE_SELECTION ROUTE_OPTION | Selección vigente derivada del último evento de selección autorizado; se conserva su historia.
scan_checks | SCAN_CHECK
custody_events | CUSTODY_EVENT ALLOCATION RESOURCE | Recurso derivado de la asignación del traslado; no se cruza cada evento con todos los recursos.
incidents | TRANSFER_INCIDENT INCIDENT_ACTION
evidence_references | CUSTODY_EVIDENCE CAPTURE_AUTHORIZATION DOCUMENT_VERSION
synchronization_results | TRANSFER_SYNC SYNC_OPERATION SYNC_CONFLICT
created_at | TRANSFER_ORDER.created_at
`);
L('INVENTORY_ANALYSIS', `
analysis_reference | INVENTORY_ANALYSIS.analysis_reference
analysis_type | INVENTORY_ANALYSIS.analysis_type
analysis_status | INVENTORY_ANALYSIS.analysis_status
regional_scope | ANALYSIS_INSTITUTION INVENTORY_ANALYSIS.period_starts_at INVENTORY_ANALYSIS.period_ends_at
method_details | INVENTORY_ANALYSIS.method_version_id METHOD_VERSION
dataset_description | INVENTORY_ANALYSIS.source_reference INVENTORY_ANALYSIS.is_synthetic INVENTORY_ANALYSIS.period_starts_at INVENTORY_ANALYSIS.period_ends_at
resource_inputs | INVENTORY_INPUT
expiry_forecasts | EXPIRY_FORECAST
balancing_proposals | BALANCING_PROPOSAL BALANCING_FACTOR
human_reviews | ANALYSIS_REVIEW
generated_at | INVENTORY_ANALYSIS.generated_at
`);
L('ALERT', `
alert_reference | ALERT.alert_reference
alert_type | ALERT.alert_type
operational_priority | ALERT.operational_priority
alert_status | ALERT.alert_status
origin_details | ALERT.source_component ALERT.origin_record_type ALERT.origin_record_reference ALERT.origin_event_reference
trigger_details | ALERT.rule_version_id RULE_VERSION ALERT.trigger_decision_reference
recipients | ALERT_RECIPIENT ALERT_DELIVERY DELIVERY_ATTEMPT DELIVERY_RECEIPT
repeated_occurrences | ALERT_OCCURRENCE | Frecuencia derivada de las ocurrencias, sin mantener otro contador autoritativo.
attention_history | ALERT_ATTENTION
created_at | ALERT.created_at
`);
L('DOCUMENT_RECORD', `
document_reference | DOCUMENT_RECORD.document_reference
document_purpose | DOCUMENT_RECORD.document_purpose
document_status | DOCUMENT_RECORD.document_status
owner_details | DOCUMENT_RECORD.owner_party_id DOCUMENT_RECORD.owner_institution_id PARTY INSTITUTION
storage_metadata | DOCUMENT_CURRENT_VERSION DOCUMENT_VERSION | Puntero explícito a la versión vigente; cada versión conserva identidad del objeto, ruta, tipo, tamaño, hash y fecha; nunca el binario.
privacy_details | DOCUMENT_RECORD.privacy_classification DOCUMENT_RECORD.retention_policy_reference DOCUMENT_SCOPE
report_parameters | REPORT_DEFINITION REPORT_FILTER REPORT_SOURCE DOCUMENT_TEMPLATE_VERSION
related_records | DOCUMENT_RELATION
version_history | DOCUMENT_VERSION
access_history | DOCUMENT_ACCESS
recorded_at | DOCUMENT_RECORD.recorded_at
`);
L('AUDIT_EVENT', `
event_reference | AUDIT_EVENT.event_reference
correlation_reference | AUDIT_EVENT.correlation_reference
source_component | AUDIT_EVENT.source_component
action | AUDIT_EVENT.action
result | AUDIT_EVENT.result
actor_details | AUDIT_EVENT.actor_id PARTY AUDIT_EVENT.performed_role_code AUDIT_EVENT.performed_scope_reference | Rol y ámbito son los observados al ejecutar, no los permisos actuales del actor.
affected_records | AUDIT_RECORD
authorized_change_details | AUDIT_FIELD_CHANGE
related_events | AUDIT_RELATION
occurred_at | AUDIT_EVENT.occurred_at
`);
L('MOBILE_DEVICE', `
device_reference | MOBILE_DEVICE.device_reference
registration_status | MOBILE_DEVICE.registration_status
device_details | MOBILE_DEVICE.operating_system MOBILE_DEVICE.application_version
account_registrations | DEVICE_REGISTRATION ACCOUNT_ROLE ACCESS_SCOPE
granted_capabilities | DEVICE_CAPABILITY_GRANT
synchronized_operations | DEVICE_OPERATION SYNC_OPERATION
synchronization_conflicts | SYNC_CONFLICT
credential_cleanup_events | CREDENTIAL_CLEANUP
registered_at | MOBILE_DEVICE.registered_at
last_activity_at | MOBILE_DEVICE.last_activity_at
`);
