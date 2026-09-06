// Especificación lógica del ejercicio. No crea bases de datos ni genera SQL.
export const tables = [];
let domain = '';
const words = value => value ? value.trim().split(/\s+/) : [];
const typeOf = name => /_id$/.test(name) ? 'uuid'
  : /(^is_|^has_)/.test(name) ? 'boolean'
  : /(_at$|^valid_from$|^valid_until$|^starts_at$|^ends_at$)/.test(name) ? 'datetime'
  : /(_no$|^sequence$|^capacity$|^size_bytes$|^ranking_position$)/.test(name) ? 'int'
  : /(^latitude$|^longitude$|^quantity$|^distance_km$|^duration_minutes$|^factor_value$|^applied_weight$)/.test(name) ? 'decimal'
  : /(^birth_date$|_date$)/.test(name) ? 'date' : 'string';
function T(name, key, attributes, foreign = {}, unique = []) {
  const pk = words(key);
  const columns = [...new Set([...pk, ...words(attributes)])].map(name => ({name, type:typeOf(name)}));
  tables.push({name, domain, columns, keys:[pk, ...unique.map(words)], foreign:Object.entries(foreign).map(([column,target]) => ({columns:[column], target, targetColumns:[]}))});
}
const D = name => { domain = name; };

D('01 — Instituciones y sedes');
T('INSTITUTION','institution_id','institution_code institution_name institution_type region_name participation_status street street_number city postal_code latitude longitude registered_at',{},['institution_code']);
T('SITE','site_id','institution_id site_code site_name street street_number city postal_code latitude longitude site_status',{institution_id:'INSTITUTION'},['institution_id site_code']);
T('CONTACT','contact_id','contact_name contact_function');
T('CONTACT_METHOD','contact_method_id','contact_id method_kind method_value purpose',{contact_id:'CONTACT'});
T('INSTITUTION_CONTACT','institution_id contact_id','',{institution_id:'INSTITUTION',contact_id:'CONTACT'});
T('SITE_CONTACT','site_id contact_id','',{site_id:'SITE',contact_id:'CONTACT'});
T('SITE_SCHEDULE','schedule_id','site_id sequence day_code opens_at closes_at valid_from valid_until',{site_id:'SITE'},['site_id sequence']);
T('CAPABILITY','capability_id','capability_code capability_name resource_kind',{},['capability_code']);
T('INSTITUTION_CAPABILITY','institution_capability_id','institution_id capability_id valid_from valid_until',{institution_id:'INSTITUTION',capability_id:'CAPABILITY'});
T('SITE_CAPABILITY','site_capability_id','site_id capability_id valid_from valid_until',{site_id:'SITE',capability_id:'CAPABILITY'});
T('INSTITUTION_SETTING','setting_id','institution_id parameter_version_id scalar_value changed_at changed_by reason',{institution_id:'INSTITUTION',parameter_version_id:'PARAMETER_VERSION',changed_by:'PARTY'});
T('INSTITUTION_EVENT','event_id','institution_id sequence previous_status new_status occurred_at actor_id reason',{institution_id:'INSTITUTION',actor_id:'PARTY'},['institution_id sequence']);

D('02 — Identidad, permisos y ámbitos');
T('PARTY','party_id','party_name party_kind');
T('USER_ACCOUNT','account_id','account_reference party_id login_email password_hash account_status registered_at',{party_id:'PARTY'},['account_reference','login_email','party_id']);
T('ACCOUNT_CONTACT','account_id contact_id','',{account_id:'USER_ACCOUNT',contact_id:'CONTACT'});
T('ROLE','role_id','role_code role_name',{},['role_code']);
T('PERMISSION','permission_id','permission_code permission_name',{},['permission_code']);
T('ACCOUNT_ROLE','account_role_id','account_id role_id valid_from valid_until assigned_by',{account_id:'USER_ACCOUNT',role_id:'ROLE',assigned_by:'PARTY'});
T('ACCESS_SCOPE','scope_id','scope_kind');
T('INSTITUTION_SCOPE','scope_id','institution_id',{scope_id:'ACCESS_SCOPE',institution_id:'INSTITUTION'},['institution_id']);
T('SITE_SCOPE','scope_id','site_id',{scope_id:'ACCESS_SCOPE',site_id:'SITE'},['site_id']);
T('REGIONAL_SCOPE','scope_id','region_name',{scope_id:'ACCESS_SCOPE'},['region_name']);
T('ACCESS_GRANT','grant_id','account_role_id permission_id scope_id valid_from valid_until assigned_by',{account_role_id:'ACCOUNT_ROLE',permission_id:'PERMISSION',scope_id:'ACCESS_SCOPE',assigned_by:'PARTY'});
T('ACCOUNT_EVENT','event_id','account_id sequence affected_grant_id occurred_at actor_id reason',{account_id:'USER_ACCOUNT',affected_grant_id:'ACCESS_GRANT',actor_id:'PARTY'},['account_id sequence']);
T('NOTIFICATION_PREFERENCE','account_id channel_code purpose','is_enabled',{account_id:'USER_ACCOUNT'});
T('PROFESSIONAL_AUTHORIZATION','authorization_id','party_id institution_id credential_reference authorized_purpose valid_from valid_until document_id',{party_id:'PARTY',institution_id:'INSTITUTION',document_id:'DOCUMENT_RECORD'});

D('03 — Catálogos y reglas versionadas');
T('REFERENCE_CATALOG','catalog_id','catalog_reference catalog_name catalog_purpose',{},['catalog_reference']);
T('CATALOG_VERSION','catalog_version_id','catalog_id version_no catalog_status scope_id',{catalog_id:'REFERENCE_CATALOG',scope_id:'ACCESS_SCOPE'},['catalog_id version_no']);
T('CATALOG_ENTRY','entry_id','catalog_version_id entry_code entry_name entry_status',{catalog_version_id:'CATALOG_VERSION'},['catalog_version_id entry_code']);
T('CATALOG_ENTRY_VALUE','entry_id value_no','value_name scalar_value',{entry_id:'CATALOG_ENTRY'});
T('CATALOG_CHANGE','change_id','catalog_version_id occurred_at actor_id reason',{catalog_version_id:'CATALOG_VERSION',actor_id:'PARTY'});
T('CATALOG_CHANGED_ENTRY','change_id entry_id','',{change_id:'CATALOG_CHANGE',entry_id:'CATALOG_ENTRY'});
T('CATALOG_CHANGE_FIELD','change_id field_name','previous_value new_value',{change_id:'CATALOG_CHANGE'});
T('PARAMETER_VERSION','parameter_version_id','parameter_code version_no scalar_value measurement_unit scope_id is_demo source_reference approved_by valid_from valid_until',{scope_id:'ACCESS_SCOPE',approved_by:'PARTY'},['parameter_code version_no']);
T('CATALOG_PARAMETER','catalog_version_id parameter_version_id','',{catalog_version_id:'CATALOG_VERSION',parameter_version_id:'PARAMETER_VERSION'});
T('RULE_VERSION','rule_version_id','rule_reference version_no resource_kind application_process source_reference scope_id approved_by valid_from valid_until is_demo',{scope_id:'ACCESS_SCOPE',approved_by:'PARTY'},['rule_reference version_no']);

D('04 — Donantes y episodios de donación');
T('DONOR','donor_id','donor_reference full_name birth_date registration_status registered_at',{},['donor_reference']);
T('DONOR_CONTACT','donor_id contact_id','',{donor_id:'DONOR',contact_id:'CONTACT'});
T('DONOR_INSTITUTION','donor_id institution_id','local_record_reference',{donor_id:'DONOR',institution_id:'INSTITUTION'},['institution_id local_record_reference']);
T('DONOR_CONSENT','consent_id','donor_id purpose document_version_id granted_at withdrawn_at recorded_by',{donor_id:'DONOR',document_version_id:'DOCUMENT_VERSION',recorded_by:'PARTY'});
T('PRELIMINARY_EVALUATION','evaluation_id','donor_id occurred_at reviewer_id review_status review_note',{donor_id:'DONOR',reviewer_id:'PARTY'});
T('PRELIMINARY_ANSWER','evaluation_id question_code','scalar_answer',{evaluation_id:'PRELIMINARY_EVALUATION'});
T('ELIGIBILITY_DECISION','decision_id','donor_id donation_process rule_version_id reviewer_id decided_at decision reason document_id',{donor_id:'DONOR',rule_version_id:'RULE_VERSION',reviewer_id:'PARTY',document_id:'DOCUMENT_RECORD'});
T('BLOOD_DONATION','donation_id','donation_reference donor_id institution_id recorded_at responsible_party_id donation_status',{donor_id:'DONOR',institution_id:'INSTITUTION',responsible_party_id:'PARTY'},['donation_reference']);
T('BLOOD_DONATION_SAMPLE','donation_id sample_id','',{donation_id:'BLOOD_DONATION',sample_id:'SAMPLE'});
T('DONATION_INCIDENT','incident_id','donation_id occurred_at description outcome',{donation_id:'BLOOD_DONATION'});
T('ORGAN_DONATION_PROCESS','process_id','process_reference donor_id institution_id process_status',{donor_id:'DONOR',institution_id:'INSTITUTION'},['process_reference']);
T('ORGAN_PROCESS_AUTHORIZATION','process_authorization_id','process_id authorization_id decision decided_at reason document_id',{process_id:'ORGAN_DONATION_PROCESS',authorization_id:'PROFESSIONAL_AUTHORIZATION',document_id:'DOCUMENT_RECORD'});
T('ORGAN_PROCESS_EVENT','event_id','process_id sequence previous_status new_status occurred_at actor_id review_reference reason',{process_id:'ORGAN_DONATION_PROCESS',actor_id:'PARTY'},['process_id sequence']);
T('DONOR_EVENT','event_id','donor_id sequence occurred_at actor_id reason',{donor_id:'DONOR',actor_id:'PARTY'},['donor_id sequence']);

D('05 — Campañas y citas');
T('CAMPAIGN','campaign_id','campaign_reference institution_id campaign_name donation_process publication_status description starts_at ends_at',{institution_id:'INSTITUTION'},['campaign_reference']);
T('CAMPAIGN_SLOT','slot_id','campaign_id site_id starts_at ends_at capacity slot_status',{campaign_id:'CAMPAIGN',site_id:'SITE'});
T('CAMPAIGN_CONDITION','condition_id','campaign_id condition_text source_reference version_no',{campaign_id:'CAMPAIGN'});
T('SLOT_CONDITION','slot_id condition_id','',{slot_id:'CAMPAIGN_SLOT',condition_id:'CAMPAIGN_CONDITION'});
T('CAMPAIGN_EVENT','event_id','campaign_id sequence occurred_at actor_id previous_status new_status reason',{campaign_id:'CAMPAIGN',actor_id:'PARTY'},['campaign_id sequence']);
T('APPOINTMENT','appointment_id','appointment_reference donor_id site_id scheduled_at current_status created_at',{donor_id:'DONOR',site_id:'SITE'},['appointment_reference']);
T('APPOINTMENT_CAMPAIGN','appointment_id','slot_id',{appointment_id:'APPOINTMENT',slot_id:'CAMPAIGN_SLOT'});
T('APPOINTMENT_STATUS_EVENT','event_id','appointment_id sequence previous_status new_status changed_at changed_by reason',{appointment_id:'APPOINTMENT',changed_by:'PARTY'},['appointment_id sequence']);
T('APPOINTMENT_RESCHEDULE','reschedule_id','appointment_id previous_slot_id new_slot_id previous_scheduled_at new_scheduled_at confirmed_at confirmed_by reason',{appointment_id:'APPOINTMENT',previous_slot_id:'CAMPAIGN_SLOT',new_slot_id:'CAMPAIGN_SLOT',confirmed_by:'PARTY'});
T('APPOINTMENT_NOTICE','appointment_id delivery_id','',{appointment_id:'APPOINTMENT',delivery_id:'ALERT_DELIVERY'});

D('06 — Receptores y necesidades');
T('RECIPIENT','recipient_id','recipient_reference full_name birth_date record_status',{},['recipient_reference']);
T('RECIPIENT_CONTACT','recipient_id contact_id','',{recipient_id:'RECIPIENT',contact_id:'CONTACT'});
T('CARE_EPISODE','care_id','recipient_id institution_id local_record_reference starts_at ends_at',{recipient_id:'RECIPIENT',institution_id:'INSTITUTION'});
T('CARE_PROFESSIONAL','care_id authorization_id','responsibility valid_from valid_until',{care_id:'CARE_EPISODE',authorization_id:'PROFESSIONAL_AUTHORIZATION'});
T('RECIPIENT_CONSENT','consent_id','recipient_id purpose document_version_id granted_at withdrawn_at recorded_by',{recipient_id:'RECIPIENT',document_version_id:'DOCUMENT_VERSION',recorded_by:'PARTY'});
T('RECIPIENT_BLOOD_NEED','need_id','recipient_id component_id quantity measurement_unit authorized_context',{recipient_id:'RECIPIENT',component_id:'BLOOD_COMPONENT'});
T('ORGAN_WAITING_PROCESS','waiting_id','recipient_id organ_type started_at current_status authorized_context',{recipient_id:'RECIPIENT'});
T('WAITING_EVENT','event_id','waiting_id sequence previous_status new_status occurred_at actor_id reason',{waiting_id:'ORGAN_WAITING_PROCESS',actor_id:'PARTY'},['waiting_id sequence']);
T('CARE_EVENT','event_id','recipient_id sequence occurred_at actor_id reason',{recipient_id:'RECIPIENT',actor_id:'PARTY'},['recipient_id sequence']);

D('07 — Estudios, muestras y resultados');
T('STUDY_SUBJECT','subject_id','subject_kind');
T('DONOR_SUBJECT','subject_id','donor_id',{subject_id:'STUDY_SUBJECT',donor_id:'DONOR'},['donor_id']);
T('RECIPIENT_SUBJECT','subject_id','recipient_id',{subject_id:'STUDY_SUBJECT',recipient_id:'RECIPIENT'},['recipient_id']);
T('RESOURCE_SUBJECT','subject_id','resource_id',{subject_id:'STUDY_SUBJECT',resource_id:'RESOURCE'},['resource_id']);
T('SAMPLE','sample_id','institution_id sample_reference collected_at',{institution_id:'INSTITUTION'},['institution_id sample_reference']);
T('CLINICAL_TEST','test_id','test_reference subject_id study_kind test_type source_institution_id',{subject_id:'STUDY_SUBJECT',source_institution_id:'INSTITUTION'},['source_institution_id test_reference']);
T('TEST_SAMPLE','test_id sample_id','',{test_id:'CLINICAL_TEST',sample_id:'SAMPLE'});
T('TEST_REVISION','revision_id','test_id revision_no source_reference recorded_at responsible_party_id review_status corrects_revision_id',{test_id:'CLINICAL_TEST',responsible_party_id:'PARTY',corrects_revision_id:'TEST_REVISION'},['test_id revision_no']);
T('BLOOD_OBSERVATION','revision_id observation_no','observation_code scalar_result measurement_unit',{revision_id:'TEST_REVISION'});
T('ORGAN_OBSERVATION','revision_id observation_no','observation_code scalar_result measurement_unit',{revision_id:'TEST_REVISION'});
T('HLA_CALL','revision_id locus_code call_no','allele_code method_reference',{revision_id:'TEST_REVISION'});
T('TEST_DOCUMENT','revision_id document_version_id','purpose',{revision_id:'TEST_REVISION',document_version_id:'DOCUMENT_VERSION'});

D('08 — Recursos sanguíneos y órganos');
T('RESOURCE','resource_id','traceability_code resource_kind',{},['traceability_code']);
T('BLOOD_COMPONENT','component_id','component_code component_name',{},['component_code']);
T('COMPONENT_ATTRIBUTE','component_id attribute_name','scalar_value',{component_id:'BLOOD_COMPONENT'});
T('STORAGE_LOCATION','location_id','site_id location_code location_description',{site_id:'SITE'},['site_id location_code']);
T('BLOOD_UNIT','resource_id','unit_reference donation_id component_id location_id collected_at expires_at expiry_parameter_version_id current_status',{resource_id:'RESOURCE',donation_id:'BLOOD_DONATION',component_id:'BLOOD_COMPONENT',location_id:'STORAGE_LOCATION',expiry_parameter_version_id:'PARAMETER_VERSION'},['unit_reference']);
T('BLOOD_ORIGIN','resource_id','source_institution_id source_reference',{resource_id:'BLOOD_UNIT',source_institution_id:'INSTITUTION'});
T('BLOOD_CLASSIFICATION','resource_id','recorded_group_code source_reference recorded_at revision_id',{resource_id:'BLOOD_UNIT',revision_id:'TEST_REVISION'});
T('BLOOD_MOVEMENT','movement_id','resource_id sequence previous_status new_status origin_location_id destination_location_id occurred_at actor_id reason',{resource_id:'BLOOD_UNIT',origin_location_id:'STORAGE_LOCATION',destination_location_id:'STORAGE_LOCATION',actor_id:'PARTY'},['resource_id sequence']);
T('DOCUMENT_TEMPLATE_VERSION','template_version_id','template_reference version_no template_purpose document_id',{document_id:'DOCUMENT_RECORD'},['template_reference version_no']);
T('LABEL_PRINT','print_id','resource_id template_version_id printed_at printed_by destination result reprint_reason',{resource_id:'BLOOD_UNIT',template_version_id:'DOCUMENT_TEMPLATE_VERSION',printed_by:'PARTY'});
T('ORGAN_AVAILABILITY','resource_id','organ_reference process_id organ_type location_id availability_status last_updated_at',{resource_id:'RESOURCE',process_id:'ORGAN_DONATION_PROCESS',location_id:'STORAGE_LOCATION'},['organ_reference']);
T('ORGAN_VIABILITY_RECORD','viability_id','resource_id recorded_condition source_reference recorded_at responsible_party_id',{resource_id:'ORGAN_AVAILABILITY',responsible_party_id:'PARTY'});
T('ORGAN_CURRENT_VIABILITY','resource_id','viability_id',{resource_id:'ORGAN_AVAILABILITY',viability_id:'ORGAN_VIABILITY_RECORD'},['viability_id']);
T('ORGAN_AUTHORIZATION','organ_authorization_id','resource_id authorization_id decision decided_at document_id reason',{resource_id:'ORGAN_AVAILABILITY',authorization_id:'PROFESSIONAL_AUTHORIZATION',document_id:'DOCUMENT_RECORD'});
T('ORGAN_EVENT','event_id','resource_id sequence previous_status new_status occurred_at actor_id reason',{resource_id:'ORGAN_AVAILABILITY',actor_id:'PARTY'},['resource_id sequence']);
T('ORGAN_DOCUMENT','resource_id document_id','purpose',{resource_id:'ORGAN_AVAILABILITY',document_id:'DOCUMENT_RECORD'});

D('09 — Solicitudes');
T('RESOURCE_REQUEST','request_id','request_reference recipient_id requesting_institution_id resource_kind current_status recorded_urgency requested_at',{recipient_id:'RECIPIENT',requesting_institution_id:'INSTITUTION'},['request_reference']);
T('REQUEST_AUTHORSHIP','request_id','authorization_id',{request_id:'RESOURCE_REQUEST',authorization_id:'PROFESSIONAL_AUTHORIZATION'});
T('BLOOD_REQUIREMENT','requirement_id','request_id line_no component_id quantity measurement_unit authorized_context',{request_id:'RESOURCE_REQUEST',component_id:'BLOOD_COMPONENT'},['request_id line_no']);
T('ORGAN_REQUIREMENT','request_id','organ_type authorized_context',{request_id:'RESOURCE_REQUEST'});
T('REQUEST_STUDY','request_id revision_id','purpose',{request_id:'RESOURCE_REQUEST',revision_id:'TEST_REVISION'});
T('REQUEST_URGENCY_EVENT','event_id','request_id sequence previous_urgency new_urgency changed_at authorization_id reason',{request_id:'RESOURCE_REQUEST',authorization_id:'PROFESSIONAL_AUTHORIZATION'},['request_id sequence']);
T('REQUEST_STATUS_EVENT','event_id','request_id sequence previous_status new_status changed_at actor_id reason',{request_id:'RESOURCE_REQUEST',actor_id:'PARTY'},['request_id sequence']);

D('10 — Evaluaciones reproducibles');
T('CANDIDATE_ASSESSMENT','assessment_id','assessment_reference request_id requesting_grant_id assessment_status generated_at',{request_id:'RESOURCE_REQUEST',requesting_grant_id:'ACCESS_GRANT'},['assessment_reference']);
T('ASSESSMENT_RULE','assessment_id rule_version_id','',{assessment_id:'CANDIDATE_ASSESSMENT',rule_version_id:'RULE_VERSION'});
T('ASSESSMENT_INPUT','input_id','assessment_id input_no input_name scalar_value measurement_unit source_record_type source_record_reference source_version captured_at',{assessment_id:'CANDIDATE_ASSESSMENT'},['assessment_id input_no']);
T('ASSESSMENT_ISSUE','issue_id','assessment_id issue_no field_name issue_kind explanation',{assessment_id:'CANDIDATE_ASSESSMENT'},['assessment_id issue_no']);
T('ASSESSMENT_CANDIDATE','candidate_id','assessment_id candidate_no resource_id ranking_position explanation',{assessment_id:'CANDIDATE_ASSESSMENT',resource_id:'RESOURCE'},['assessment_id candidate_no','assessment_id resource_id']);
T('CANDIDATE_COMPATIBILITY','candidate_id criterion_code','scalar_result source_revision_id explanation',{candidate_id:'ASSESSMENT_CANDIDATE',source_revision_id:'TEST_REVISION'});
T('CANDIDATE_FACTOR','candidate_id factor_name','factor_value measurement_unit applied_weight source_reference rule_version_id',{candidate_id:'ASSESSMENT_CANDIDATE',rule_version_id:'RULE_VERSION'});
T('CANDIDATE_GEOGRAPHY','candidate_id','origin_site_id destination_site_id distance_km duration_minutes source_reference calculated_at limitations',{candidate_id:'ASSESSMENT_CANDIDATE',origin_site_id:'SITE',destination_site_id:'SITE'});
T('CANDIDATE_ISSUE','candidate_id issue_no','field_name explanation',{candidate_id:'ASSESSMENT_CANDIDATE'});
T('CANDIDATE_REVIEW','review_id','candidate_id authorization_id decision reason reviewed_at',{candidate_id:'ASSESSMENT_CANDIDATE',authorization_id:'PROFESSIONAL_AUTHORIZATION'});
T('REVIEW_EVIDENCE','review_id document_version_id','',{review_id:'CANDIDATE_REVIEW',document_version_id:'DOCUMENT_VERSION'});

D('11 — Reserva y asignación humana');
T('ALLOCATION','allocation_id','allocation_reference request_id resource_id operation_type allocation_status reservation_starts_at reservation_ends_at created_at',{request_id:'RESOURCE_REQUEST',resource_id:'RESOURCE'},['allocation_reference']);
T('ALLOCATION_ASSESSMENT','allocation_id','candidate_id',{allocation_id:'ALLOCATION',candidate_id:'ASSESSMENT_CANDIDATE'});
T('ALLOCATION_AUTHORIZATION','allocation_authorization_id','allocation_id authorization_id decision decided_at reason',{allocation_id:'ALLOCATION',authorization_id:'PROFESSIONAL_AUTHORIZATION'});
T('ALLOCATION_EVIDENCE','allocation_authorization_id document_version_id','',{allocation_authorization_id:'ALLOCATION_AUTHORIZATION',document_version_id:'DOCUMENT_VERSION'});
T('ALLOCATION_EVENT','event_id','allocation_id sequence previous_status new_status occurred_at actor_id reason',{allocation_id:'ALLOCATION',actor_id:'PARTY'},['allocation_id sequence']);
T('ALLOCATION_OPERATION','operation_id','allocation_id',{operation_id:'SYNC_OPERATION',allocation_id:'ALLOCATION'});
T('ALLOCATION_ATTEMPT','attempt_id','operation_id attempt_no attempted_at attempt_result',{operation_id:'ALLOCATION_OPERATION'},['operation_id attempt_no']);

D('12 — Traslado y cadena de custodia');
T('TRANSFER_ORDER','transfer_id','transfer_reference allocation_id origin_site_id destination_site_id transfer_status planned_collection_at planned_delivery_at collected_at delivered_at created_at',{allocation_id:'ALLOCATION',origin_site_id:'SITE',destination_site_id:'SITE'},['transfer_reference']);
T('TRANSFER_STAFF','assignment_id','transfer_id party_id responsibility valid_from valid_until',{transfer_id:'TRANSFER_ORDER',party_id:'PARTY'});
T('ROUTE_OPTION','route_id','transfer_id option_no origin_latitude origin_longitude destination_latitude destination_longitude distance_km duration_minutes source_reference calculated_at limitations',{transfer_id:'TRANSFER_ORDER'},['transfer_id option_no']);
T('ROUTE_SELECTION','selection_id','route_id selected_at selected_by reason',{route_id:'ROUTE_OPTION',selected_by:'PARTY'});
T('SCAN_CHECK','scan_id','transfer_id expected_event scanned_code actor_id occurred_at result',{transfer_id:'TRANSFER_ORDER',actor_id:'PARTY'});
T('CUSTODY_EVENT','event_id','transfer_id sequence operation_id event_type occurred_at previous_custodian_id new_custodian_id recorded_by condition_report latitude longitude corrects_event_id',{transfer_id:'TRANSFER_ORDER',operation_id:'SYNC_OPERATION',previous_custodian_id:'PARTY',new_custodian_id:'PARTY',recorded_by:'PARTY',corrects_event_id:'CUSTODY_EVENT'},['transfer_id sequence','operation_id']);
T('CAPTURE_AUTHORIZATION','capture_authorization_id','transfer_id party_id purpose valid_from valid_until authorized_by',{transfer_id:'TRANSFER_ORDER',party_id:'PARTY',authorized_by:'PARTY'});
T('CUSTODY_EVIDENCE','event_id document_version_id','capture_authorization_id captured_at',{event_id:'CUSTODY_EVENT',document_version_id:'DOCUMENT_VERSION',capture_authorization_id:'CAPTURE_AUTHORIZATION'});
T('TRANSFER_INCIDENT','incident_id','transfer_id occurred_at description outcome',{transfer_id:'TRANSFER_ORDER'});
T('INCIDENT_ACTION','action_id','incident_id actor_id acted_at action_note result',{incident_id:'TRANSFER_INCIDENT',actor_id:'PARTY'});
T('TRANSFER_SYNC','operation_id','transfer_id',{transfer_id:'TRANSFER_ORDER',operation_id:'SYNC_OPERATION'});
T('TRANSFER_CONTACT','transfer_id contact_id contact_purpose','',{transfer_id:'TRANSFER_ORDER',contact_id:'CONTACT'});

D('13 — Pronóstico y balanceo');
T('METHOD_VERSION','method_version_id','method_reference version_no purpose limitations',{},['method_reference version_no']);
T('INVENTORY_ANALYSIS','analysis_id','analysis_reference analysis_type analysis_status method_version_id period_starts_at period_ends_at source_reference is_synthetic generated_at',{method_version_id:'METHOD_VERSION'},['analysis_reference']);
T('ANALYSIS_INSTITUTION','analysis_id institution_id','',{analysis_id:'INVENTORY_ANALYSIS',institution_id:'INSTITUTION'});
T('INVENTORY_INPUT','input_id','analysis_id input_no resource_id recorded_availability recorded_demand captured_at source_reference',{analysis_id:'INVENTORY_ANALYSIS',resource_id:'RESOURCE'},['analysis_id input_no']);
T('EXPIRY_FORECAST','forecast_id','input_id forecast_horizon predicted_value explanation',{input_id:'INVENTORY_INPUT'});
T('BALANCING_PROPOSAL','proposal_id','analysis_id resource_id origin_site_id destination_site_id explanation',{analysis_id:'INVENTORY_ANALYSIS',resource_id:'RESOURCE',origin_site_id:'SITE',destination_site_id:'SITE'});
T('BALANCING_FACTOR','proposal_id factor_name','factor_value measurement_unit applied_weight source_reference',{proposal_id:'BALANCING_PROPOSAL'});
T('ANALYSIS_REVIEW','review_id','analysis_id reviewer_id decision reviewed_at reason',{analysis_id:'INVENTORY_ANALYSIS',reviewer_id:'PARTY'});

D('14 — Alertas y entregas');
T('ALERT','alert_id','alert_reference alert_type operational_priority alert_status source_component origin_record_type origin_record_reference origin_event_reference rule_version_id trigger_decision_reference created_at',{rule_version_id:'RULE_VERSION'},['alert_reference']);
T('ALERT_RECIPIENT','recipient_id','alert_id party_id scope_id attention_state',{alert_id:'ALERT',party_id:'PARTY',scope_id:'ACCESS_SCOPE'},['alert_id party_id scope_id']);
T('ALERT_DELIVERY','delivery_id','recipient_id channel_code destination_snapshot',{recipient_id:'ALERT_RECIPIENT'},['recipient_id channel_code destination_snapshot']);
T('DELIVERY_ATTEMPT','attempt_id','delivery_id attempt_no attempted_at result',{delivery_id:'ALERT_DELIVERY'},['delivery_id attempt_no']);
T('DELIVERY_RECEIPT','receipt_id','attempt_id received_at receipt_result',{attempt_id:'DELIVERY_ATTEMPT'});
T('ALERT_OCCURRENCE','occurrence_id','alert_id related_event_reference occurred_at',{alert_id:'ALERT'});
T('ALERT_ATTENTION','attention_id','recipient_id actor_id acted_at action result',{recipient_id:'ALERT_RECIPIENT',actor_id:'PARTY'});

D('15 — Documentos y reportes');
T('DOCUMENT_RECORD','document_id','document_reference document_purpose document_status owner_party_id owner_institution_id privacy_classification retention_policy_reference recorded_at',{owner_party_id:'PARTY',owner_institution_id:'INSTITUTION'},['document_reference']);
T('DOCUMENT_VERSION','document_version_id','document_id version_no object_identifier object_path media_type size_bytes content_hash created_at author_id reason',{document_id:'DOCUMENT_RECORD',author_id:'PARTY'},['document_id version_no','object_identifier']);
T('DOCUMENT_CURRENT_VERSION','document_id','document_version_id',{document_id:'DOCUMENT_RECORD',document_version_id:'DOCUMENT_VERSION'},['document_version_id']);
T('DOCUMENT_SCOPE','document_id scope_id','',{document_id:'DOCUMENT_RECORD',scope_id:'ACCESS_SCOPE'});
T('DOCUMENT_RELATION','document_id record_type record_reference relation_kind','',{document_id:'DOCUMENT_RECORD'});
T('DOCUMENT_ACCESS','access_id','document_version_id actor_id purpose accessed_at result',{document_version_id:'DOCUMENT_VERSION',actor_id:'PARTY'});
T('REPORT_DEFINITION','document_id','template_version_id period_starts_at period_ends_at requested_by',{document_id:'DOCUMENT_RECORD',template_version_id:'DOCUMENT_TEMPLATE_VERSION',requested_by:'PARTY'});
T('REPORT_FILTER','document_id filter_name value_no','scalar_value',{document_id:'REPORT_DEFINITION'});
T('REPORT_SOURCE','document_id source_no','source_reference source_version',{document_id:'REPORT_DEFINITION'});

D('16 — Auditoría y cambios mínimos');
T('AUDIT_EVENT','event_id','event_reference correlation_reference source_component actor_id performed_role_code performed_scope_reference action result occurred_at',{actor_id:'PARTY'},['event_reference']);
T('AUDIT_RECORD','event_id record_no','record_type record_reference permitted_context',{event_id:'AUDIT_EVENT'});
T('AUDIT_FIELD_CHANGE','event_id record_no field_name','permitted_previous_value permitted_new_value redaction_state',{event_id:'AUDIT_EVENT'});
T('AUDIT_RELATION','event_id related_event_id relation_kind','',{event_id:'AUDIT_EVENT',related_event_id:'AUDIT_EVENT'});

D('17 — Dispositivos y sincronización');
T('MOBILE_DEVICE','device_id','device_reference registration_status operating_system application_version registered_at last_activity_at',{},['device_reference']);
T('DEVICE_REGISTRATION','registration_id','device_id account_role_id scope_id registered_at revoked_at',{device_id:'MOBILE_DEVICE',account_role_id:'ACCOUNT_ROLE',scope_id:'ACCESS_SCOPE'});
T('DEVICE_CAPABILITY_GRANT','capability_grant_id','registration_id capability_code purpose valid_from valid_until',{registration_id:'DEVICE_REGISTRATION'});
T('SYNC_OPERATION','operation_id','operation_reference operation_type target_record_type target_record_reference submitted_at result confirmation_reference',{},['operation_reference']);
T('DEVICE_OPERATION','registration_id operation_id','',{registration_id:'DEVICE_REGISTRATION',operation_id:'SYNC_OPERATION'});
T('SYNC_CONFLICT','conflict_id','operation_id reason detected_at resolved_at resolution resolved_by',{operation_id:'SYNC_OPERATION',resolved_by:'PARTY'});
T('CREDENTIAL_CLEANUP','cleanup_id','registration_id cleaned_at local_removal_result',{registration_id:'DEVICE_REGISTRATION'});

// Correcciones de tipos descriptivos: no son tipos físicos ni longitudes SQL.
for (const table of tables) for (const c of table.columns) {
  if (/latitude|longitude|_weight$/.test(c.name)) c.type = 'decimal';
  if (/^changed_by$|^assigned_by$|^approved_by$|^recorded_by$|^printed_by$|^confirmed_by$|^selected_by$|^authorized_by$|^requested_by$|^resolved_by$/.test(c.name)) c.type = 'uuid';
  if (/^opens_at$|^closes_at$/.test(c.name)) c.type = 'time';
  if (c.name === 'version_no') c.type = 'string';
}
export const optionalForeign = new Set([
  'BLOOD_UNIT.donation_id', 'BLOOD_UNIT.expiry_parameter_version_id',
  'ACCOUNT_EVENT.affected_grant_id', 'PROFESSIONAL_AUTHORIZATION.document_id',
  'PARAMETER_VERSION.approved_by', 'RULE_VERSION.approved_by',
  'ELIGIBILITY_DECISION.rule_version_id', 'ELIGIBILITY_DECISION.document_id',
  'APPOINTMENT_RESCHEDULE.previous_slot_id', 'APPOINTMENT_RESCHEDULE.new_slot_id',
  'APPOINTMENT_RESCHEDULE.confirmed_by', 'TEST_REVISION.corrects_revision_id',
  'BLOOD_CLASSIFICATION.revision_id', 'CANDIDATE_COMPATIBILITY.source_revision_id',
  'CUSTODY_EVENT.previous_custodian_id', 'CUSTODY_EVENT.corrects_event_id',
  'ALERT.rule_version_id', 'SYNC_CONFLICT.resolved_by',
]);
for (const t of tables) for (const f of t.foreign) f.optional = optionalForeign.has(`${t.name}.${f.columns[0]}`);
// La FK compuesta preserva qué registro concreto fue cambiado dentro del evento.
tables.find(t => t.name === 'AUDIT_FIELD_CHANGE').foreign = [{columns:['event_id','record_no'], target:'AUDIT_RECORD',targetColumns:['event_id','record_no']}];

// Redundancias presentes después de extraer las listas de 0FN.
// Se eliminan por las DF explícitas, no por el nombre de la tabla ni por añadir un UUID.
export const partialSteps = [
  {table:'SITE', determinant:['institution_id'], target:'INSTITUTION', mappings:{institution_name:'institution_name',institution_type:'institution_type'}},
  {table:'CATALOG_VERSION', determinant:['catalog_id'], target:'REFERENCE_CATALOG', mappings:{catalog_name:'catalog_name',catalog_purpose:'catalog_purpose'}},
  {table:'APPOINTMENT_STATUS_EVENT', determinant:['appointment_id'], target:'APPOINTMENT', mappings:{appointment_reference:'appointment_reference',scheduled_at:'scheduled_at'}},
  {table:'CATALOG_ENTRY', determinant:['catalog_version_id'], target:'CATALOG_VERSION', mappings:{catalog_version_no:'version_no',catalog_status:'catalog_status'}},
  {table:'BLOOD_REQUIREMENT', determinant:['request_id'], target:'RESOURCE_REQUEST', mappings:{request_reference:'request_reference',requested_at:'requested_at'}},
  {table:'ASSESSMENT_CANDIDATE', determinant:['assessment_id'], target:'CANDIDATE_ASSESSMENT', mappings:{assessment_status:'assessment_status',generated_at:'generated_at'}},
  {table:'DELIVERY_ATTEMPT', determinant:['delivery_id'], target:'ALERT_DELIVERY', mappings:{channel_code:'channel_code',destination_snapshot:'destination_snapshot'}},
  {table:'DOCUMENT_VERSION', determinant:['document_id'], target:'DOCUMENT_RECORD', mappings:{document_purpose:'document_purpose',document_status:'document_status'}},
];
export const transitiveSteps = [
  {table:'ACCOUNT_ROLE', determinant:['role_id'], target:'ROLE', mappings:{role_name:'role_name',role_code:'role_code'}},
  {table:'BLOOD_UNIT', determinant:['component_id'], target:'BLOOD_COMPONENT', mappings:{component_name:'component_name',component_code:'component_code'}},
  {table:'RESOURCE_REQUEST', determinant:['recipient_id'], target:'RECIPIENT', mappings:{recipient_reference:'recipient_reference',recipient_full_name:'full_name'}},
  {table:'TRANSFER_ORDER', determinant:['origin_site_id'], target:'SITE', mappings:{origin_site_name:'site_name'}},
];

export function schemaAt(stage) {
  const result = structuredClone(tables);
  for (const t of result) {
    t.dependencies = t.keys.map(key => ({left:key, right:t.columns.map(c=>c.name).filter(c=>!key.includes(c)), kind:'key'}));
  }
  const extras = [...(stage <= 2 ? transitiveSteps : []), ...(stage === 1 ? partialSteps : [])];
  for (const step of extras) {
    const t = result.find(t=>t.name===step.table);
    const parent = result.find(t=>t.name===step.target);
    for (const [column, original] of Object.entries(step.mappings)) {
      const type = parent.columns.find(c=>c.name===original)?.type;
      if (!type) throw new Error(`Unknown mapped column ${step.target}.${original}`);
      t.columns.push({name:column,type});
      for (const dependency of t.dependencies.filter(d=>d.kind==='key')) dependency.right.push(column);
    }
    t.dependencies.push({left:step.determinant,right:Object.keys(step.mappings),kind:'redundancy'});
    // Una referencia alternativa copiada conserva su DF inversa. Por ejemplo,
    // appointment_reference -> appointment_id también rige en la fila aplanada.
    const localNames = Object.fromEntries(Object.entries(step.mappings).map(([local,remote])=>[remote,local]));
    parent.keys[0].forEach((column,i)=>{localNames[column]=step.determinant[i];});
    for (const key of parent.keys) if (key.every(c=>localNames[c])) {
      const left=key.map(c=>localNames[c]);
      const right=Object.values(localNames).filter(c=>!left.includes(c));
      if (right.length && !left.every(c=>step.determinant.includes(c))) t.dependencies.push({left,right,kind:'copied_candidate_key'});
    }
  }
  // Claves alternativas inducidas por esas referencias copiadas. Se derivan de
  // las DF, en vez de declararlas únicas solo para pasar una comprobación.
  const closure=(key,dependencies)=>{
    const known=new Set(key);
    let changed=true;
    while(changed) {
      changed=false;
      for(const d of dependencies) if(d.left.every(c=>known.has(c))) for(const c of d.right) if(!known.has(c)) {known.add(c);changed=true;}
    }
    return known;
  };
  for(const t of result) {
    let changed=true;
    while(changed) {
      changed=false;
      for(const d of t.dependencies.filter(d=>d.kind==='copied_candidate_key')) for(const k of [...t.keys]) {
        const replace=k.filter(c=>d.right.includes(c));
        if(!replace.length) continue;
        const candidate=[...new Set([...k.filter(c=>!replace.includes(c)),...d.left])];
        if(t.keys.some(key=>key.length===candidate.length&&key.every(c=>candidate.includes(c)))) continue;
        if(closure(candidate,t.dependencies).size!==t.columns.length) continue;
        if(candidate.some(c=>closure(candidate.filter(a=>a!==c),t.dependencies).size===t.columns.length)) continue;
        t.keys.push(candidate);
        changed=true;
      }
    }
  }
  return result;
}
