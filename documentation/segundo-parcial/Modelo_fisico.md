# Modelo físico PostgreSQL instalado

Base `red_house`, esquema `red_house`. Metadatos exportados de la instancia Docker aislada. No contiene filas de negocio ni credenciales.

71 tablas físicas y 145 índices. Las vistas `access_*` adaptan los contratos sin duplicar estas tablas. Algunas tablas conservadas de main no son escritas por los servicios actuales; consultar la correspondencia en `Esquema_compartido.md`.

[Metadatos verificables](../evidencias/segundo-parcial/postgresql-physical.json) · [SQL de instalación](../../data/database/schema.sql) · [Diagrama físico completo, ampliable](diagramas/postgresql-completo.svg)

## account_role

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| account_id | uuid | NO | — |
| role_code | character varying(30) | NO | — |
| institution_id | uuid | YES | — |
| region_name | character varying(80) | YES | — |

Restricciones:

- `account_role_check`: `CHECK (((institution_id IS NOT NULL) <> (region_name IS NOT NULL)))`.
- `account_role_check1`: `CHECK ((((role_code)::text <> 'OPERATOR'::text) OR (institution_id IS NOT NULL)))`.
- `account_role_check2`: `CHECK ((((role_code)::text <> ALL (ARRAY[('MEDICAL'::character varying)::text, ('TRANSPORT'::character varying)::text])) OR (institution_id IS NOT NULL)))`.
- `account_role_pkey`: `PRIMARY KEY (account_id)`.
- `account_role_account_id_fkey`: `FOREIGN KEY (account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `account_role_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `account_role_role_code_fkey`: `FOREIGN KEY (role_code) REFERENCES red_house.role(role_code) DEFERRABLE`.

Índices:

- `account_role_pkey`: `CREATE UNIQUE INDEX account_role_pkey ON red_house.account_role USING btree (account_id)`.
- `account_role_scope_idx`: `CREATE INDEX account_role_scope_idx ON red_house.account_role USING btree (institution_id)`.

## algorithm_run

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| run_id | uuid | NO | gen_random_uuid() |
| institution_id | uuid | NO | — |
| actor_id | uuid | YES | — |
| operation | text | NO | — |
| algorithm_version | text | NO | — |
| blood_evaluation_id | uuid | YES | — |
| organ_evaluation_id | uuid | YES | — |
| inputs | jsonb | NO | — |
| factors | jsonb | NO | — |
| result | jsonb | NO | — |
| elapsed_ms | double precision | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `algorithm_run_check`: `CHECK ((num_nonnulls(blood_evaluation_id, organ_evaluation_id) <= 1))`.
- `algorithm_run_elapsed_ms_check`: `CHECK ((elapsed_ms >= (0)::double precision))`.
- `algorithm_run_operation_check`: `CHECK ((operation = ANY (ARRAY['RANKING'::text, 'BALANCING'::text])))`.
- `algorithm_run_pkey`: `PRIMARY KEY (run_id)`.
- `algorithm_run_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `algorithm_run_blood_evaluation_id_fkey`: `FOREIGN KEY (blood_evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE`.
- `algorithm_run_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `algorithm_run_organ_evaluation_id_fkey`: `FOREIGN KEY (organ_evaluation_id) REFERENCES red_house.organ_evaluation(evaluation_id) DEFERRABLE`.

Índices:

- `algorithm_run_pkey`: `CREATE UNIQUE INDEX algorithm_run_pkey ON red_house.algorithm_run USING btree (run_id)`.

## allocation_operation

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| user_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| key | text | NO | — |
| fingerprint | text | NO | — |
| input | jsonb | NO | — |
| status | text | NO | 'PENDING'::text |
| hold_id | uuid | YES | — |
| error | text | YES | — |
| last_recovery_at | timestamp with time zone | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_operations_pkey`: `PRIMARY KEY (id)`.
- `api_operations_user_id_key_key`: `UNIQUE (user_id, key)`.
- `shared_operations_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_operations_user_id`: `FOREIGN KEY (user_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `api_operations_pkey`: `CREATE UNIQUE INDEX api_operations_pkey ON red_house.allocation_operation USING btree (id)`.
- `api_operations_user_id_key_key`: `CREATE UNIQUE INDEX api_operations_user_id_key_key ON red_house.allocation_operation USING btree (user_id, key)`.

## appointment

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| appointment_id | uuid | NO | — |
| donor_id | uuid | NO | — |
| campaign_id | uuid | NO | — |
| current_status | text | NO | 'BOOKED'::text |
| created_at | timestamp with time zone | NO | now() |
| tenant_id | uuid | NO | — |

Restricciones:

- `appointment_pkey`: `PRIMARY KEY (appointment_id)`.
- `api_appointments_campaign_id_fkey`: `FOREIGN KEY (campaign_id) REFERENCES red_house.campaign(campaign_id) DEFERRABLE`.
- `api_appointments_donor_id_fkey`: `FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id) DEFERRABLE`.
- `shared_appointments_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `appointment_pkey`: `CREATE UNIQUE INDEX appointment_pkey ON red_house.appointment USING btree (appointment_id)`.
- `api_active_appointment`: `CREATE UNIQUE INDEX api_active_appointment ON red_house.appointment USING btree (donor_id, campaign_id) WHERE (current_status = 'BOOKED'::text)`.
- `appointment_active`: `CREATE UNIQUE INDEX appointment_active ON red_house.appointment USING btree (donor_id, campaign_id) WHERE (current_status = 'BOOKED'::text)`.

## audit_change

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| event_id | uuid | NO | — |
| field_name | character varying(60) | NO | — |
| previous_value | character varying(240) | YES | — |
| new_value | character varying(240) | YES | — |

Restricciones:

- `audit_change_pkey`: `PRIMARY KEY (event_id, field_name)`.
- `audit_change_event_id_fkey`: `FOREIGN KEY (event_id) REFERENCES red_house.audit_event(event_id) DEFERRABLE`.

Índices:

- `audit_change_pkey`: `CREATE UNIQUE INDEX audit_change_pkey ON red_house.audit_change USING btree (event_id, field_name)`.

## audit_event

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| event_id | uuid | NO | — |
| actor_id | uuid | YES | — |
| institution_id | uuid | NO | — |
| region_name | character varying(80) | YES | — |
| occurred_at | timestamp with time zone | NO | now() |
| action | text | NO | — |
| entity_type | character varying(40) | YES | — |
| entity_reference | character varying(80) | YES | — |
| outcome | character varying(12) | YES | — |
| correlation_id | uuid | YES | — |
| reason | character varying(240) | YES | — |
| source_service | text | NO | — |
| metadata | jsonb | YES | '{}'::jsonb |
| region_id | uuid | NO | — |
| event | jsonb | NO | — |

Restricciones:

- `audit_event_outcome_check`: `CHECK (((outcome)::text = ANY (ARRAY[('SUCCESS'::character varying)::text, ('DENIED'::character varying)::text, ('FAILED'::character varying)::text])))`.
- `audit_event_pkey`: `PRIMARY KEY (event_id)`.
- `shared_audit_events_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_audit_events_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `audit_event_pkey`: `CREATE UNIQUE INDEX audit_event_pkey ON red_house.audit_event USING btree (event_id)`.
- `api_audit_search`: `CREATE INDEX api_audit_search ON red_house.audit_event USING btree (region_id, institution_id, occurred_at)`.
- `audit_region_time_idx`: `CREATE INDEX audit_region_time_idx ON red_house.audit_event USING btree (region_name, occurred_at DESC)`.
- `audit_scope_time_idx`: `CREATE INDEX audit_scope_time_idx ON red_house.audit_event USING btree (institution_id, occurred_at DESC)`.

## balance_proposal

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| algorithm_version | text | NO | — |
| snapshots | jsonb | NO | — |
| result | jsonb | NO | — |
| elapsed_ms | double precision | NO | — |
| slot_count | integer | NO | — |
| matched_count | integer | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_proposals_pkey`: `PRIMARY KEY (id)`.
- `shared_proposals_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_proposals_pkey`: `CREATE UNIQUE INDEX api_proposals_pkey ON red_house.balance_proposal USING btree (id)`.

## blood_allocation

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| allocation_id | uuid | NO | — |
| request_id | uuid | NO | — |
| candidate_id | uuid | YES | — |
| resource_id | uuid | NO | — |
| origin_id | uuid | NO | — |
| destination_id | uuid | NO | — |
| authorized_by | uuid | YES | — |
| authorization_reason | character varying(240) | YES | — |
| current_status | text | NO | 'PENDING'::text |
| reserved_at | timestamp with time zone | NO | now() |
| received_at | timestamp with time zone | YES | — |
| version_no | integer | YES | 1 |
| review_id | uuid | YES | — |
| operation_id | uuid | NO | — |
| recipient_id | uuid | NO | — |
| region_id | uuid | NO | — |
| hold_id | uuid | NO | — |
| evaluation_id | uuid | NO | — |
| route_id | uuid | NO | — |
| route_version | integer | NO | — |
| shipment_id | uuid | YES | — |
| shipment_sequence | integer | NO | 0 |

Restricciones:

- `api_reservations_hold_id_key`: `UNIQUE (hold_id)`.
- `api_reservations_operation_id_key`: `UNIQUE (operation_id)`.
- `blood_allocation_candidate_id_key`: `UNIQUE (candidate_id)`.
- `blood_allocation_pkey`: `PRIMARY KEY (allocation_id)`.
- `api_reservations_operation_id_fkey`: `FOREIGN KEY (operation_id) REFERENCES red_house.allocation_operation(id) DEFERRABLE`.
- `api_reservations_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.
- `blood_allocation_authorized_by_fkey`: `FOREIGN KEY (authorized_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `blood_allocation_candidate_id_fkey`: `FOREIGN KEY (candidate_id) REFERENCES red_house.blood_candidate(candidate_id) DEFERRABLE`.
- `blood_allocation_review_id_fkey`: `FOREIGN KEY (review_id) REFERENCES red_house.blood_review(review_id) DEFERRABLE`.
- `shared_reservations_destination_id`: `FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_reservations_evaluation_id`: `FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE`.
- `shared_reservations_hold_id`: `FOREIGN KEY (hold_id) REFERENCES red_house.request_hold(id) DEFERRABLE`.
- `shared_reservations_origin_id`: `FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_reservations_recipient_id`: `FOREIGN KEY (recipient_id) REFERENCES red_house.recipient(recipient_id) DEFERRABLE`.
- `shared_reservations_request_id`: `FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE`.
- `shared_reservations_route_id`: `FOREIGN KEY (route_id) REFERENCES red_house.regional_route(route_id) DEFERRABLE`.

Índices:

- `api_reservations_hold_id_key`: `CREATE UNIQUE INDEX api_reservations_hold_id_key ON red_house.blood_allocation USING btree (hold_id)`.
- `api_reservations_operation_id_key`: `CREATE UNIQUE INDEX api_reservations_operation_id_key ON red_house.blood_allocation USING btree (operation_id)`.
- `blood_allocation_candidate_id_key`: `CREATE UNIQUE INDEX blood_allocation_candidate_id_key ON red_house.blood_allocation USING btree (candidate_id)`.
- `blood_allocation_pkey`: `CREATE UNIQUE INDEX blood_allocation_pkey ON red_house.blood_allocation USING btree (allocation_id)`.
- `allocation_request_idx`: `CREATE INDEX allocation_request_idx ON red_house.blood_allocation USING btree (request_id)`.
- `allocation_resource_exclusive`: `CREATE UNIQUE INDEX allocation_resource_exclusive ON red_house.blood_allocation USING btree (resource_id) WHERE (current_status <> 'CANCELLED'::text)`.
- `api_resource_reserved`: `CREATE UNIQUE INDEX api_resource_reserved ON red_house.blood_allocation USING btree (resource_id) WHERE (current_status <> 'CANCELLED'::text)`.

## blood_candidate

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| candidate_id | uuid | NO | gen_random_uuid() |
| evaluation_id | uuid | NO | — |
| resource_id | uuid | NO | — |
| rank_no | integer | NO | — |
| unit_version | integer | NO | — |
| donor_group | character varying(3) | NO | — |
| recipient_group | character varying(3) | NO | — |
| urgency | character varying(20) | NO | — |
| wait_minutes | integer | NO | — |
| distance_km | integer | NO | — |
| travel_minutes | integer | NO | — |
| route_version | integer | NO | — |
| expires_at | timestamp with time zone | NO | — |
| explanation | character varying(1000) | NO | — |

Restricciones:

- `blood_candidate_rank_no_check`: `CHECK ((rank_no > 0))`.
- `blood_candidate_wait_minutes_check`: `CHECK ((wait_minutes >= 0))`.
- `blood_candidate_evaluation_id_rank_no_key`: `UNIQUE (evaluation_id, rank_no)`.
- `blood_candidate_evaluation_id_resource_id_key`: `UNIQUE (evaluation_id, resource_id)`.
- `blood_candidate_pkey`: `PRIMARY KEY (candidate_id)`.
- `blood_candidate_evaluation_id_fkey`: `FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE`.
- `blood_candidate_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.blood_unit(resource_id) DEFERRABLE`.

Índices:

- `blood_candidate_evaluation_id_rank_no_key`: `CREATE UNIQUE INDEX blood_candidate_evaluation_id_rank_no_key ON red_house.blood_candidate USING btree (evaluation_id, rank_no)`.
- `blood_candidate_evaluation_id_resource_id_key`: `CREATE UNIQUE INDEX blood_candidate_evaluation_id_resource_id_key ON red_house.blood_candidate USING btree (evaluation_id, resource_id)`.
- `blood_candidate_pkey`: `CREATE UNIQUE INDEX blood_candidate_pkey ON red_house.blood_candidate USING btree (candidate_id)`.

## blood_classification

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| resource_id | uuid | NO | — |
| recorded_group_code | character varying(3) | NO | — |
| source_reference | character varying(120) | NO | — |
| recorded_at | timestamp with time zone | NO | now() |

Restricciones:

- `blood_classification_recorded_group_code_check`: `CHECK (((recorded_group_code)::text = ANY (ARRAY[('O-'::character varying)::text, ('O+'::character varying)::text, ('A-'::character varying)::text, ('A+'::character varying)::text, ('B-'::character varying)::text, ('B+'::character varying)::text, ('AB-'::character varying)::text, ('AB+'::character varying)::text])))`.
- `blood_classification_pkey`: `PRIMARY KEY (resource_id)`.
- `blood_classification_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.blood_unit(resource_id) DEFERRABLE`.

Índices:

- `blood_classification_pkey`: `CREATE UNIQUE INDEX blood_classification_pkey ON red_house.blood_classification USING btree (resource_id)`.

## blood_component

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| component_id | uuid | NO | gen_random_uuid() |
| component_code | character varying(30) | NO | — |
| component_name | character varying(100) | NO | — |
| region_name | character varying(80) | NO | — |
| is_active | boolean | NO | true |
| version_no | integer | NO | 1 |

Restricciones:

- `blood_component_component_code_key`: `UNIQUE (component_code)`.
- `blood_component_pkey`: `PRIMARY KEY (component_id)`.

Índices:

- `blood_component_component_code_key`: `CREATE UNIQUE INDEX blood_component_component_code_key ON red_house.blood_component USING btree (component_code)`.
- `blood_component_pkey`: `CREATE UNIQUE INDEX blood_component_pkey ON red_house.blood_component USING btree (component_id)`.

## blood_movement

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| movement_id | uuid | NO | — |
| resource_id | uuid | NO | — |
| sequence | integer | YES | — |
| previous_status | character varying(16) | YES | — |
| new_status | character varying(16) | YES | — |
| origin_location_id | uuid | YES | — |
| destination_location_id | uuid | YES | — |
| occurred_at | timestamp with time zone | NO | now() |
| actor_id | uuid | NO | — |
| reason | character varying(240) | YES | — |
| action | text | NO | — |

Restricciones:

- `blood_movement_pkey`: `PRIMARY KEY (movement_id)`.
- `api_movements_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.
- `blood_movement_destination_location_id_fkey`: `FOREIGN KEY (destination_location_id) REFERENCES red_house.storage_location(location_id) DEFERRABLE`.
- `blood_movement_origin_location_id_fkey`: `FOREIGN KEY (origin_location_id) REFERENCES red_house.storage_location(location_id) DEFERRABLE`.
- `shared_movements_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `blood_movement_pkey`: `CREATE UNIQUE INDEX blood_movement_pkey ON red_house.blood_movement USING btree (movement_id)`.

## blood_request

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| request_id | uuid | NO | — |
| request_code | character varying(30) | YES | — |
| recipient_id | uuid | NO | — |
| component_id | uuid | YES | — |
| quantity | integer | NO | — |
| urgency | character varying(20) | YES | — |
| justification | character varying(1000) | YES | — |
| current_status | text | NO | 'OPEN'::text |
| responsible_id | uuid | YES | — |
| requested_at | timestamp with time zone | NO | now() |
| closed_at | timestamp with time zone | YES | — |
| version_no | integer | NO | 1 |
| tenant_id | uuid | NO | — |
| kind | text | NO | — |
| component | text | NO | — |
| priority_level | integer | NO | — |

Restricciones:

- `api_requests_check`: `CHECK (((kind <> 'ORGAN'::text) OR (quantity = 1)))`.
- `api_requests_quantity_check`: `CHECK ((quantity > 0))`.
- `api_requests_urgency_check`: `CHECK (((priority_level >= 1) AND (priority_level <= 3)))`.
- `blood_request_urgency_check`: `CHECK (((urgency)::text = ANY (ARRAY[('URGENT'::character varying)::text, ('PRIORITY'::character varying)::text, ('ROUTINE'::character varying)::text])))`.
- `blood_request_pkey`: `PRIMARY KEY (request_id)`.
- `blood_request_request_code_key`: `UNIQUE (request_code)`.
- `api_requests_recipient_id_fkey`: `FOREIGN KEY (recipient_id) REFERENCES red_house.recipient(recipient_id) DEFERRABLE`.
- `blood_request_component_id_fkey`: `FOREIGN KEY (component_id) REFERENCES red_house.blood_component(component_id) DEFERRABLE`.
- `blood_request_responsible_id_fkey`: `FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_requests_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `blood_request_pkey`: `CREATE UNIQUE INDEX blood_request_pkey ON red_house.blood_request USING btree (request_id)`.
- `blood_request_request_code_key`: `CREATE UNIQUE INDEX blood_request_request_code_key ON red_house.blood_request USING btree (request_code)`.
- `api_active_organ_request`: `CREATE UNIQUE INDEX api_active_organ_request ON red_house.blood_request USING btree (recipient_id) WHERE ((kind = 'ORGAN'::text) AND (current_status = ANY (ARRAY['OPEN'::text, 'IN_PROGRESS'::text])))`.
- `request_queue_idx`: `CREATE INDEX request_queue_idx ON red_house.blood_request USING btree (current_status, urgency, requested_at)`.
- `request_recipient_idx`: `CREATE INDEX request_recipient_idx ON red_house.blood_request USING btree (recipient_id)`.

## blood_review

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| review_id | uuid | NO | — |
| candidate_id | uuid | YES | — |
| actor_id | uuid | NO | — |
| decision | text | NO | — |
| reason | text | NO | — |
| occurred_at | timestamp with time zone | NO | now() |
| evaluation_id | uuid | NO | — |
| resource_id | uuid | NO | — |
| tenant_id | uuid | NO | — |

Restricciones:

- `api_reviews_evaluation_id_resource_id_key`: `UNIQUE (evaluation_id, resource_id)`.
- `blood_review_pkey`: `PRIMARY KEY (review_id)`.
- `api_reviews_evaluation_id_fkey`: `FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE`.
- `blood_review_candidate_id_fkey`: `FOREIGN KEY (candidate_id) REFERENCES red_house.blood_candidate(candidate_id) DEFERRABLE`.
- `shared_reviews_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_reviews_resource_id`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.
- `shared_reviews_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_reviews_evaluation_id_resource_id_key`: `CREATE UNIQUE INDEX api_reviews_evaluation_id_resource_id_key ON red_house.blood_review USING btree (evaluation_id, resource_id)`.
- `blood_review_pkey`: `CREATE UNIQUE INDEX blood_review_pkey ON red_house.blood_review USING btree (review_id)`.

## blood_status_transition

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| previous_status | character varying(16) | NO | — |
| new_status | character varying(16) | NO | — |
| is_illustrative | boolean | NO | true |

Restricciones:

- `blood_status_transition_check`: `CHECK (((previous_status)::text <> (new_status)::text))`.
- `blood_status_transition_is_illustrative_check`: `CHECK (is_illustrative)`.
- `blood_status_transition_new_status_check`: `CHECK (((new_status)::text = ANY (ARRAY[('AVAILABLE'::character varying)::text, ('QUARANTINED'::character varying)::text, ('WITHDRAWN'::character varying)::text])))`.
- `blood_status_transition_previous_status_check`: `CHECK (((previous_status)::text = ANY (ARRAY[('AVAILABLE'::character varying)::text, ('QUARANTINED'::character varying)::text])))`.
- `blood_status_transition_pkey`: `PRIMARY KEY (previous_status, new_status)`.

Índices:

- `blood_status_transition_pkey`: `CREATE UNIQUE INDEX blood_status_transition_pkey ON red_house.blood_status_transition USING btree (previous_status, new_status)`.

## blood_unit

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| resource_id | uuid | NO | — |
| component_id | uuid | NO | — |
| location_id | uuid | NO | — |
| collected_at | timestamp with time zone | NO | — |
| expires_at | timestamp with time zone | NO | — |
| current_status | character varying(16) | NO | — |
| version_no | integer | NO | 1 |
| registered_at | timestamp with time zone | NO | now() |

Restricciones:

- `blood_unit_current_status_check`: `CHECK (((current_status)::text = ANY (ARRAY[('AVAILABLE'::character varying)::text, ('QUARANTINED'::character varying)::text, ('WITHDRAWN'::character varying)::text, ('RESERVED'::character varying)::text, ('IN_TRANSIT'::character varying)::text, ('DELIVERED'::character varying)::text])))`.
- `blood_unit_check`: `CHECK ((expires_at > collected_at))`.
- `blood_unit_pkey`: `PRIMARY KEY (resource_id)`.
- `blood_unit_component_id_fkey`: `FOREIGN KEY (component_id) REFERENCES red_house.blood_component(component_id) DEFERRABLE`.
- `blood_unit_location_id_fkey`: `FOREIGN KEY (location_id) REFERENCES red_house.storage_location(location_id) DEFERRABLE`.
- `blood_unit_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.

Índices:

- `blood_unit_pkey`: `CREATE UNIQUE INDEX blood_unit_pkey ON red_house.blood_unit USING btree (resource_id)`.
- `blood_unit_component_idx`: `CREATE INDEX blood_unit_component_idx ON red_house.blood_unit USING btree (component_id)`.
- `blood_unit_expiry_idx`: `CREATE INDEX blood_unit_expiry_idx ON red_house.blood_unit USING btree (expires_at) WHERE ((current_status)::text = 'AVAILABLE'::text)`.
- `blood_unit_location_idx`: `CREATE INDEX blood_unit_location_idx ON red_house.blood_unit USING btree (location_id)`.

## cache_revision

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| name | text | NO | — |
| revision | bigint | NO | 0 |

Restricciones:

- `cache_revision_pkey`: `PRIMARY KEY (name)`.

Índices:

- `cache_revision_pkey`: `CREATE UNIQUE INDEX cache_revision_pkey ON red_house.cache_revision USING btree (name)`.

## campaign

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| campaign_id | uuid | NO | — |
| institution_id | uuid | NO | — |
| title | text | NO | — |
| starts_at | timestamp with time zone | NO | — |
| ends_at | timestamp with time zone | NO | — |
| capacity | integer | NO | — |
| current_status | text | NO | 'OPEN'::text |
| version_no | integer | NO | 1 |

Restricciones:

- `api_campaigns_capacity_check`: `CHECK ((capacity > 0))`.
- `api_campaigns_check`: `CHECK ((ends_at > starts_at))`.
- `campaign_pkey`: `PRIMARY KEY (campaign_id)`.
- `shared_campaigns_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `campaign_pkey`: `CREATE UNIQUE INDEX campaign_pkey ON red_house.campaign USING btree (campaign_id)`.

## candidate_evaluation

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| evaluation_id | uuid | NO | — |
| request_id | uuid | NO | — |
| algorithm_version | text | NO | — |
| request_version | integer | NO | — |
| recipient_version | integer | NO | — |
| actor_id | uuid | YES | — |
| occurred_at | timestamp with time zone | NO | now() |
| elapsed_ms | double precision | NO | — |
| tenant_id | uuid | NO | — |
| kind | text | NO | — |
| snapshot | jsonb | NO | — |
| candidates | jsonb | NO | — |

Restricciones:

- `candidate_evaluation_pkey`: `PRIMARY KEY (evaluation_id)`.
- `candidate_evaluation_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_evaluations_request_id`: `FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE`.
- `shared_evaluations_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `candidate_evaluation_pkey`: `CREATE UNIQUE INDEX candidate_evaluation_pkey ON red_house.candidate_evaluation USING btree (evaluation_id)`.

## capability

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| capability_code | character varying(40) | NO | — |
| capability_name | character varying(100) | NO | — |

Restricciones:

- `capability_pkey`: `PRIMARY KEY (capability_code)`.

Índices:

- `capability_pkey`: `CREATE UNIQUE INDEX capability_pkey ON red_house.capability USING btree (capability_code)`.

## catalogue_entry

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| kind | text | NO | — |
| name | text | NO | — |
| parent_id | uuid | YES | — |
| details | jsonb | NO | — |
| active | boolean | NO | true |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_catalogue_kind_check`: `CHECK ((kind = ANY (ARRAY['sites'::text, 'contacts'::text, 'schedules'::text, 'capacities'::text, 'locations'::text])))`.
- `api_catalogue_pkey`: `PRIMARY KEY (id)`.
- `api_catalogue_tenant_id_kind_name_key`: `UNIQUE (tenant_id, kind, name)`.
- `api_catalogue_parent_id_fkey`: `FOREIGN KEY (parent_id) REFERENCES red_house.catalogue_entry(id) DEFERRABLE`.
- `api_catalogue_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_catalogue_pkey`: `CREATE UNIQUE INDEX api_catalogue_pkey ON red_house.catalogue_entry USING btree (id)`.
- `api_catalogue_tenant_id_kind_name_key`: `CREATE UNIQUE INDEX api_catalogue_tenant_id_kind_name_key ON red_house.catalogue_entry USING btree (tenant_id, kind, name)`.
- `api_catalogue_tenant`: `CREATE INDEX api_catalogue_tenant ON red_house.catalogue_entry USING btree (tenant_id, kind, name, id)`.

## contact

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| contact_id | uuid | NO | gen_random_uuid() |
| contact_name | character varying(120) | NO | — |
| contact_function | character varying(80) | NO | — |

Restricciones:

- `contact_pkey`: `PRIMARY KEY (contact_id)`.

Índices:

- `contact_pkey`: `CREATE UNIQUE INDEX contact_pkey ON red_house.contact USING btree (contact_id)`.

## contact_method

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| contact_id | uuid | NO | — |
| method_kind | character varying(10) | NO | — |
| method_value | character varying(180) | NO | — |

Restricciones:

- `contact_method_method_kind_check`: `CHECK (((method_kind)::text = ANY (ARRAY[('EMAIL'::character varying)::text, ('PHONE'::character varying)::text])))`.
- `contact_method_pkey`: `PRIMARY KEY (contact_id, method_kind)`.
- `contact_method_contact_id_fkey`: `FOREIGN KEY (contact_id) REFERENCES red_house.contact(contact_id) DEFERRABLE`.

Índices:

- `contact_method_pkey`: `CREATE UNIQUE INDEX contact_method_pkey ON red_house.contact_method USING btree (contact_id, method_kind)`.

## custody_chain

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| region_id | uuid | NO | — |
| origin_id | uuid | NO | — |
| destination_id | uuid | NO | — |
| last_sequence | integer | NO | 0 |
| last_hash | text | NO | ''::text |

Restricciones:

- `api_chains_pkey`: `PRIMARY KEY (id)`.
- `shared_chains_destination_id`: `FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_chains_id`: `FOREIGN KEY (id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE`.
- `shared_chains_origin_id`: `FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_chains_pkey`: `CREATE UNIQUE INDEX api_chains_pkey ON red_house.custody_chain USING btree (id)`.

## custody_event

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| event_id | uuid | NO | — |
| shipment_id | uuid | NO | — |
| sequence | integer | NO | — |
| status | character varying(20) | YES | — |
| actor_id | uuid | YES | — |
| occurred_at | timestamp with time zone | NO | now() |
| location_description | character varying(240) | YES | — |
| observation | character varying(1000) | YES | — |
| evidence_reference | character varying(240) | YES | — |
| previous_hash | text | NO | — |
| event_hash | text | NO | — |
| event | jsonb | NO | — |

Restricciones:

- `api_custody_events_shipment_id_sequence_key`: `UNIQUE (shipment_id, sequence)`.
- `custody_event_pkey`: `PRIMARY KEY (event_id)`.
- `api_custody_events_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.custody_chain(id) DEFERRABLE`.
- `custody_event_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `api_custody_events_shipment_id_sequence_key`: `CREATE UNIQUE INDEX api_custody_events_shipment_id_sequence_key ON red_house.custody_event USING btree (shipment_id, sequence)`.
- `custody_event_pkey`: `CREATE UNIQUE INDEX custody_event_pkey ON red_house.custody_event USING btree (event_id)`.

## donation

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| donation_id | uuid | NO | — |
| donor_id | uuid | NO | — |
| review_id | uuid | YES | — |
| donation_code | character varying(30) | YES | — |
| current_status | text | NO | 'COLLECTED'::text |
| collected_at | timestamp with time zone | NO | — |
| processed_at | timestamp with time zone | YES | — |
| created_by | uuid | YES | — |
| registered_at | timestamp with time zone | NO | now() |
| version_no | integer | NO | 1 |
| tenant_id | uuid | NO | — |
| kind | text | NO | — |
| component | text | NO | — |
| blood_group | text | NO | — |

Restricciones:

- `api_donations_kind_check`: `CHECK ((kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text])))`.
- `donation_donation_code_key`: `UNIQUE (donation_code)`.
- `donation_pkey`: `PRIMARY KEY (donation_id)`.
- `api_donations_donor_id_fkey`: `FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id) DEFERRABLE`.
- `donation_created_by_fkey`: `FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `donation_review_id_fkey`: `FOREIGN KEY (review_id) REFERENCES red_house.donor_review(review_id) DEFERRABLE`.
- `shared_donations_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `donation_donation_code_key`: `CREATE UNIQUE INDEX donation_donation_code_key ON red_house.donation USING btree (donation_code)`.
- `donation_pkey`: `CREATE UNIQUE INDEX donation_pkey ON red_house.donation USING btree (donation_id)`.

## donation_event

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| event_id | uuid | NO | — |
| donation_id | uuid | NO | — |
| status | text | NO | — |
| actor_id | uuid | NO | — |
| occurred_at | timestamp with time zone | NO | now() |
| observation | text | NO | — |

Restricciones:

- `donation_event_pkey`: `PRIMARY KEY (event_id)`.
- `api_donation_steps_donation_id_fkey`: `FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id) DEFERRABLE`.
- `shared_donation_steps_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `donation_event_pkey`: `CREATE UNIQUE INDEX donation_event_pkey ON red_house.donation_event USING btree (event_id)`.

## donation_unit

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| resource_id | uuid | NO | — |
| donation_id | uuid | NO | — |
| released_by | uuid | NO | — |
| release_reference | character varying(240) | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `donation_unit_pkey`: `PRIMARY KEY (resource_id)`.
- `donation_unit_donation_id_fkey`: `FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id) DEFERRABLE`.
- `donation_unit_released_by_fkey`: `FOREIGN KEY (released_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `donation_unit_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.blood_unit(resource_id) DEFERRABLE`.

Índices:

- `donation_unit_pkey`: `CREATE UNIQUE INDEX donation_unit_pkey ON red_house.donation_unit USING btree (resource_id)`.

## donor

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| donor_id | uuid | NO | — |
| institution_id | uuid | NO | — |
| record_code | text | NO | — |
| display_name | text | NO | — |
| blood_group | text | NO | — |
| donation_kind | text | YES | — |
| background | text | YES | — |
| restrictions | text | YES | — |
| consent_reference | text | YES | — |
| consent_at | text | YES | — |
| current_status | text | NO | 'PRELIMINARY'::text |
| created_by | uuid | YES | — |
| registered_at | timestamp with time zone | NO | now() |
| version_no | integer | NO | 1 |
| account_id | uuid | YES | — |
| consent | boolean | NO | — |

Restricciones:

- `api_donors_consent_check`: `CHECK (consent)`.
- `api_donors_donation_kind_check`: `CHECK ((donation_kind = ANY (ARRAY['VOLUNTARY'::text, 'REPLACEMENT'::text])))`.
- `api_donors_tenant_id_folio_key`: `UNIQUE (institution_id, record_code)`.
- `donor_pkey`: `PRIMARY KEY (donor_id)`.
- `donor_created_by_fkey`: `FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_donors_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_donors_user_id`: `FOREIGN KEY (account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `api_donors_tenant_id_folio_key`: `CREATE UNIQUE INDEX api_donors_tenant_id_folio_key ON red_house.donor USING btree (institution_id, record_code)`.
- `donor_pkey`: `CREATE UNIQUE INDEX donor_pkey ON red_house.donor USING btree (donor_id)`.
- `api_donor_account`: `CREATE UNIQUE INDEX api_donor_account ON red_house.donor USING btree (account_id) WHERE (account_id IS NOT NULL)`.
- `donor_institution_idx`: `CREATE INDEX donor_institution_idx ON red_house.donor USING btree (institution_id)`.

## donor_review

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| review_id | uuid | NO | — |
| donor_id | uuid | NO | — |
| decision | text | NO | — |
| reason | text | NO | — |
| actor_id | uuid | NO | — |
| occurred_at | timestamp with time zone | NO | now() |

Restricciones:

- `donor_review_pkey`: `PRIMARY KEY (review_id)`.
- `api_donor_reviews_donor_id_fkey`: `FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id) DEFERRABLE`.
- `shared_donor_reviews_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `donor_review_pkey`: `CREATE UNIQUE INDEX donor_review_pkey ON red_house.donor_review USING btree (review_id)`.

## institution

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| institution_id | uuid | NO | — |
| institution_code | character varying(30) | YES | — |
| institution_name | text | NO | — |
| institution_type | character varying(40) | YES | — |
| region_name | character varying(80) | YES | — |
| city | character varying(100) | YES | — |
| street | character varying(200) | YES | — |
| participation_status | character varying(10) | YES | 'ACTIVE'::character varying |
| version_no | integer | NO | 1 |
| registered_at | timestamp with time zone | YES | now() |
| operating_hours | character varying(240) | YES | ''::character varying |
| region_id | uuid | NO | — |
| active | boolean | NO | true |
| created_by | uuid | YES | — |

Restricciones:

- `institution_institution_type_check`: `CHECK (((institution_type)::text = ANY (ARRAY[('BLOOD_BANK'::character varying)::text, ('HOSPITAL'::character varying)::text, ('COORDINATION'::character varying)::text, ('TRANSPLANT_CENTER'::character varying)::text])))`.
- `institution_participation_status_check`: `CHECK (((participation_status)::text = ANY (ARRAY[('ACTIVE'::character varying)::text, ('INACTIVE'::character varying)::text])))`.
- `institution_institution_code_key`: `UNIQUE (institution_code)`.
- `institution_pkey`: `PRIMARY KEY (institution_id)`.
- `api_institutions_created_by_fkey`: `FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `institution_institution_code_key`: `CREATE UNIQUE INDEX institution_institution_code_key ON red_house.institution USING btree (institution_code)`.
- `institution_pkey`: `CREATE UNIQUE INDEX institution_pkey ON red_house.institution USING btree (institution_id)`.

## institution_capability

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| institution_id | uuid | NO | — |
| capability_code | character varying(40) | NO | — |

Restricciones:

- `institution_capability_pkey`: `PRIMARY KEY (institution_id, capability_code)`.
- `institution_capability_capability_code_fkey`: `FOREIGN KEY (capability_code) REFERENCES red_house.capability(capability_code) DEFERRABLE`.
- `institution_capability_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `institution_capability_pkey`: `CREATE UNIQUE INDEX institution_capability_pkey ON red_house.institution_capability USING btree (institution_id, capability_code)`.

## institution_contact

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| institution_id | uuid | NO | — |
| contact_id | uuid | NO | — |

Restricciones:

- `institution_contact_contact_id_key`: `UNIQUE (contact_id)`.
- `institution_contact_pkey`: `PRIMARY KEY (institution_id, contact_id)`.
- `institution_contact_contact_id_fkey`: `FOREIGN KEY (contact_id) REFERENCES red_house.contact(contact_id) DEFERRABLE`.
- `institution_contact_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `institution_contact_contact_id_key`: `CREATE UNIQUE INDEX institution_contact_contact_id_key ON red_house.institution_contact USING btree (contact_id)`.
- `institution_contact_pkey`: `CREATE UNIQUE INDEX institution_contact_pkey ON red_house.institution_contact USING btree (institution_id, contact_id)`.

## login_attempt

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| attempt_id | bigint | NO | — |
| identity_hash | character(64) | NO | — |
| address_hash | character(64) | NO | — |
| occurred_at | timestamp with time zone | NO | now() |
| was_successful | boolean | NO | — |

Restricciones:

- `login_attempt_pkey`: `PRIMARY KEY (attempt_id)`.

Índices:

- `login_attempt_pkey`: `CREATE UNIQUE INDEX login_attempt_pkey ON red_house.login_attempt USING btree (attempt_id)`.
- `login_address_time_idx`: `CREATE INDEX login_address_time_idx ON red_house.login_attempt USING btree (address_hash, occurred_at DESC)`.
- `login_identity_time_idx`: `CREATE INDEX login_identity_time_idx ON red_house.login_attempt USING btree (identity_hash, occurred_at DESC)`.

## notification

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| notification_id | uuid | NO | — |
| event_id | uuid | NO | — |
| institution_id | uuid | NO | — |
| target_role | text | NO | — |
| target_account_id | uuid | YES | — |
| message_code | text | NO | — |
| entity_reference | text | NO | — |
| current_status | text | NO | 'OPEN'::text |
| acknowledged_by | uuid | YES | — |
| created_at | timestamp with time zone | NO | now() |
| region_id | uuid | NO | — |

Restricciones:

- `api_alerts_event_id_tenant_id_target_role_key`: `UNIQUE (event_id, institution_id, target_role)`.
- `notification_pkey`: `PRIMARY KEY (notification_id)`.
- `shared_alerts_acknowledged_by`: `FOREIGN KEY (acknowledged_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_alerts_target_user_id`: `FOREIGN KEY (target_account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_alerts_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_alerts_event_id_tenant_id_target_role_key`: `CREATE UNIQUE INDEX api_alerts_event_id_tenant_id_target_role_key ON red_house.notification USING btree (event_id, institution_id, target_role)`.
- `notification_pkey`: `CREATE UNIQUE INDEX notification_pkey ON red_house.notification USING btree (notification_id)`.

## organ_allocation

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| allocation_id | uuid | NO | gen_random_uuid() |
| candidate_id | uuid | NO | — |
| review_id | uuid | NO | — |
| offer_id | uuid | NO | — |
| recipient_id | uuid | NO | — |
| authorized_by | uuid | NO | — |
| authorization_reference | character varying(240) | NO | — |
| current_status | character varying(12) | NO | 'RESERVED'::character varying |
| transport_id | uuid | YES | — |
| vehicle | character varying(120) | YES | — |
| departure_at | timestamp with time zone | YES | — |
| eta | timestamp with time zone | YES | — |
| reserved_at | timestamp with time zone | NO | now() |
| received_at | timestamp with time zone | YES | — |
| version_no | integer | NO | 1 |

Restricciones:

- `organ_allocation_check`: `CHECK (((eta IS NULL) OR (eta > departure_at)))`.
- `organ_allocation_current_status_check`: `CHECK (((current_status)::text = ANY (ARRAY[('RESERVED'::character varying)::text, ('SCHEDULED'::character varying)::text, ('PREPARED'::character varying)::text, ('COLLECTED'::character varying)::text, ('IN_TRANSIT'::character varying)::text, ('DELIVERED'::character varying)::text, ('ACCEPTED'::character varying)::text, ('CANCELLED'::character varying)::text])))`.
- `organ_allocation_pkey`: `PRIMARY KEY (allocation_id)`.
- `organ_allocation_authorized_by_fkey`: `FOREIGN KEY (authorized_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `organ_allocation_candidate_id_fkey`: `FOREIGN KEY (candidate_id) REFERENCES red_house.organ_candidate(candidate_id) DEFERRABLE`.
- `organ_allocation_offer_id_fkey`: `FOREIGN KEY (offer_id) REFERENCES red_house.organ_offer(offer_id) DEFERRABLE`.
- `organ_allocation_recipient_id_fkey`: `FOREIGN KEY (recipient_id) REFERENCES red_house.organ_recipient(recipient_id) DEFERRABLE`.
- `organ_allocation_review_id_fkey`: `FOREIGN KEY (review_id) REFERENCES red_house.organ_review(review_id) DEFERRABLE`.
- `organ_allocation_transport_id_fkey`: `FOREIGN KEY (transport_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `organ_allocation_pkey`: `CREATE UNIQUE INDEX organ_allocation_pkey ON red_house.organ_allocation USING btree (allocation_id)`.
- `organ_exclusive_offer`: `CREATE UNIQUE INDEX organ_exclusive_offer ON red_house.organ_allocation USING btree (offer_id) WHERE ((current_status)::text <> 'CANCELLED'::text)`.
- `organ_exclusive_recipient`: `CREATE UNIQUE INDEX organ_exclusive_recipient ON red_house.organ_allocation USING btree (recipient_id) WHERE ((current_status)::text <> 'CANCELLED'::text)`.

## organ_candidate

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| candidate_id | uuid | NO | gen_random_uuid() |
| evaluation_id | uuid | NO | — |
| offer_id | uuid | NO | — |
| recipient_id | uuid | NO | — |
| offer_version | integer | NO | — |
| recipient_version | integer | NO | — |
| route_version | integer | NO | — |
| rank_no | integer | NO | — |
| algorithm_version | character varying(40) | NO | — |
| explanation | text | NO | — |
| distance_km | integer | NO | — |
| travel_minutes | integer | NO | — |
| evaluated_by | uuid | NO | — |
| evaluated_at | timestamp with time zone | NO | now() |

Restricciones:

- `organ_candidate_rank_no_check`: `CHECK ((rank_no > 0))`.
- `organ_candidate_evaluation_id_recipient_id_key`: `UNIQUE (evaluation_id, recipient_id)`.
- `organ_candidate_pkey`: `PRIMARY KEY (candidate_id)`.
- `organ_candidate_evaluated_by_fkey`: `FOREIGN KEY (evaluated_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `organ_candidate_evaluation_id_fkey`: `FOREIGN KEY (evaluation_id) REFERENCES red_house.organ_evaluation(evaluation_id) DEFERRABLE`.
- `organ_candidate_offer_id_fkey`: `FOREIGN KEY (offer_id) REFERENCES red_house.organ_offer(offer_id) DEFERRABLE`.
- `organ_candidate_recipient_id_fkey`: `FOREIGN KEY (recipient_id) REFERENCES red_house.organ_recipient(recipient_id) DEFERRABLE`.

Índices:

- `organ_candidate_evaluation_id_recipient_id_key`: `CREATE UNIQUE INDEX organ_candidate_evaluation_id_recipient_id_key ON red_house.organ_candidate USING btree (evaluation_id, recipient_id)`.
- `organ_candidate_pkey`: `CREATE UNIQUE INDEX organ_candidate_pkey ON red_house.organ_candidate USING btree (candidate_id)`.
- `organ_candidates_offer`: `CREATE INDEX organ_candidates_offer ON red_house.organ_candidate USING btree (offer_id, evaluated_at)`.

## organ_custody_event

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| event_id | uuid | NO | gen_random_uuid() |
| allocation_id | uuid | NO | — |
| status | character varying(20) | NO | — |
| actor_id | uuid | NO | — |
| occurred_at | timestamp with time zone | NO | now() |
| location_description | character varying(240) | NO | — |
| observation | text | NO | — |
| evidence_reference | character varying(240) | NO | — |
| previous_hash | text | YES | — |
| event_hash | text | YES | — |

Restricciones:

- `organ_custody_event_pkey`: `PRIMARY KEY (event_id)`.
- `organ_custody_event_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `organ_custody_event_allocation_id_fkey`: `FOREIGN KEY (allocation_id) REFERENCES red_house.organ_allocation(allocation_id) DEFERRABLE`.

Índices:

- `organ_custody_event_pkey`: `CREATE UNIQUE INDEX organ_custody_event_pkey ON red_house.organ_custody_event USING btree (event_id)`.
- `organ_custody_allocation`: `CREATE INDEX organ_custody_allocation ON red_house.organ_custody_event USING btree (allocation_id, occurred_at)`.

## organ_donor

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| donor_id | uuid | NO | gen_random_uuid() |
| institution_id | uuid | NO | — |
| record_code | character varying(30) | NO | — |
| display_name | character varying(120) | NO | — |
| abo | character varying(2) | NO | — |
| donation_kind | character varying(12) | NO | — |
| consent_reference | character varying(240) | NO | — |
| studies | text | NO | — |
| hla | text | NO | — |
| clinical_reference | character varying(240) | NO | — |
| reviewed_by | uuid | NO | — |
| registered_at | timestamp with time zone | NO | now() |

Restricciones:

- `organ_donor_abo_check`: `CHECK (((abo)::text = ANY (ARRAY[('O'::character varying)::text, ('A'::character varying)::text, ('B'::character varying)::text, ('AB'::character varying)::text])))`.
- `organ_donor_donation_kind_check`: `CHECK (((donation_kind)::text = ANY (ARRAY[('LIVING'::character varying)::text, ('DECEASED'::character varying)::text])))`.
- `organ_donor_pkey`: `PRIMARY KEY (donor_id)`.
- `organ_donor_record_code_key`: `UNIQUE (record_code)`.
- `organ_donor_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `organ_donor_reviewed_by_fkey`: `FOREIGN KEY (reviewed_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `organ_donor_pkey`: `CREATE UNIQUE INDEX organ_donor_pkey ON red_house.organ_donor USING btree (donor_id)`.
- `organ_donor_record_code_key`: `CREATE UNIQUE INDEX organ_donor_record_code_key ON red_house.organ_donor USING btree (record_code)`.

## organ_evaluation

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| evaluation_id | uuid | NO | gen_random_uuid() |
| offer_id | uuid | NO | — |
| evaluated_by | uuid | NO | — |
| algorithm_version | character varying(40) | NO | — |
| evaluated_at | timestamp with time zone | NO | now() |

Restricciones:

- `organ_evaluation_pkey`: `PRIMARY KEY (evaluation_id)`.
- `organ_evaluation_evaluated_by_fkey`: `FOREIGN KEY (evaluated_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `organ_evaluation_offer_id_fkey`: `FOREIGN KEY (offer_id) REFERENCES red_house.organ_offer(offer_id) DEFERRABLE`.

Índices:

- `organ_evaluation_pkey`: `CREATE UNIQUE INDEX organ_evaluation_pkey ON red_house.organ_evaluation USING btree (evaluation_id)`.

## organ_offer

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| offer_id | uuid | NO | gen_random_uuid() |
| donor_id | uuid | NO | — |
| record_code | character varying(30) | NO | — |
| organ_type | character varying(12) | NO | — |
| anatomical_description | character varying(240) | NO | — |
| recovered_at | timestamp with time zone | NO | — |
| preservation_until | timestamp with time zone | NO | — |
| preservation_reference | character varying(240) | NO | — |
| released_by | uuid | NO | — |
| current_status | character varying(12) | NO | 'AVAILABLE'::character varying |
| version_no | integer | NO | 1 |
| registered_at | timestamp with time zone | NO | now() |

Restricciones:

- `organ_offer_check`: `CHECK ((preservation_until > recovered_at))`.
- `organ_offer_current_status_check`: `CHECK (((current_status)::text = ANY (ARRAY[('AVAILABLE'::character varying)::text, ('RESERVED'::character varying)::text, ('IN_TRANSIT'::character varying)::text, ('RECEIVED'::character varying)::text, ('WITHDRAWN'::character varying)::text])))`.
- `organ_offer_organ_type_check`: `CHECK (((organ_type)::text = ANY (ARRAY[('KIDNEY'::character varying)::text, ('LIVER'::character varying)::text, ('HEART'::character varying)::text])))`.
- `organ_offer_pkey`: `PRIMARY KEY (offer_id)`.
- `organ_offer_record_code_key`: `UNIQUE (record_code)`.
- `organ_offer_donor_id_fkey`: `FOREIGN KEY (donor_id) REFERENCES red_house.organ_donor(donor_id) DEFERRABLE`.
- `organ_offer_released_by_fkey`: `FOREIGN KEY (released_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `organ_offer_pkey`: `CREATE UNIQUE INDEX organ_offer_pkey ON red_house.organ_offer USING btree (offer_id)`.
- `organ_offer_record_code_key`: `CREATE UNIQUE INDEX organ_offer_record_code_key ON red_house.organ_offer USING btree (record_code)`.

## organ_recipient

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| recipient_id | uuid | NO | gen_random_uuid() |
| institution_id | uuid | NO | — |
| record_code | character varying(30) | NO | — |
| display_name | character varying(120) | NO | — |
| organ_type | character varying(12) | NO | — |
| abo | character varying(2) | NO | — |
| studies | text | NO | — |
| hla | text | NO | — |
| urgency | character varying(12) | NO | — |
| waiting_since | timestamp with time zone | NO | — |
| clinical_reference | character varying(240) | NO | — |
| responsible_id | uuid | NO | — |
| current_status | character varying(12) | NO | 'ACTIVE'::character varying |
| version_no | integer | NO | 1 |
| registered_at | timestamp with time zone | NO | now() |

Restricciones:

- `organ_recipient_organ_type_check`: `CHECK (((organ_type)::text = ANY (ARRAY[('KIDNEY'::character varying)::text, ('LIVER'::character varying)::text, ('HEART'::character varying)::text])))`.
- `organ_recipient_abo_check`: `CHECK (((abo)::text = ANY (ARRAY[('O'::character varying)::text, ('A'::character varying)::text, ('B'::character varying)::text, ('AB'::character varying)::text])))`.
- `organ_recipient_current_status_check`: `CHECK (((current_status)::text = ANY (ARRAY[('ACTIVE'::character varying)::text, ('INACTIVE'::character varying)::text, ('RESERVED'::character varying)::text, ('CLOSED'::character varying)::text])))`.
- `organ_recipient_urgency_check`: `CHECK (((urgency)::text = ANY (ARRAY[('URGENT'::character varying)::text, ('PRIORITY'::character varying)::text, ('ROUTINE'::character varying)::text])))`.
- `organ_recipient_pkey`: `PRIMARY KEY (recipient_id)`.
- `organ_recipient_record_code_key`: `UNIQUE (record_code)`.
- `organ_recipient_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `organ_recipient_responsible_id_fkey`: `FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `organ_recipient_pkey`: `CREATE UNIQUE INDEX organ_recipient_pkey ON red_house.organ_recipient USING btree (recipient_id)`.
- `organ_recipient_record_code_key`: `CREATE UNIQUE INDEX organ_recipient_record_code_key ON red_house.organ_recipient USING btree (record_code)`.

## organ_review

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| review_id | uuid | NO | gen_random_uuid() |
| candidate_id | uuid | NO | — |
| decision | character varying(12) | NO | — |
| hla_assessment | text | NO | — |
| size_assessment | text | NO | — |
| crossmatch_reference | character varying(240) | NO | — |
| clinical_reference | character varying(240) | NO | — |
| reviewed_by | uuid | NO | — |
| occurred_at | timestamp with time zone | NO | now() |

Restricciones:

- `organ_review_decision_check`: `CHECK (((decision)::text = ANY (ARRAY[('FAVORABLE'::character varying)::text, ('REJECTED'::character varying)::text])))`.
- `organ_review_pkey`: `PRIMARY KEY (review_id)`.
- `organ_review_candidate_id_fkey`: `FOREIGN KEY (candidate_id) REFERENCES red_house.organ_candidate(candidate_id) DEFERRABLE`.
- `organ_review_reviewed_by_fkey`: `FOREIGN KEY (reviewed_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `organ_review_pkey`: `CREATE UNIQUE INDEX organ_review_pkey ON red_house.organ_review USING btree (review_id)`.

## parameter_version

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| parameter_version_id | uuid | NO | gen_random_uuid() |
| parameter_code | character varying(40) | NO | — |
| region_name | character varying(80) | NO | — |
| version_no | integer | NO | — |
| scalar_value | integer | NO | — |
| measurement_unit | character varying(10) | NO | 'HOURS'::character varying |
| is_illustrative | boolean | NO | true |
| approved_by | uuid | YES | — |
| valid_from | timestamp with time zone | NO | now() |

Restricciones:

- `parameter_version_is_illustrative_check`: `CHECK (is_illustrative)`.
- `parameter_version_measurement_unit_check`: `CHECK (((measurement_unit)::text = 'HOURS'::text))`.
- `parameter_version_parameter_code_check`: `CHECK (((parameter_code)::text = 'EXPIRY_WARNING_HOURS'::text))`.
- `parameter_version_scalar_value_check`: `CHECK (((scalar_value >= 1) AND (scalar_value <= 720)))`.
- `parameter_version_pkey`: `PRIMARY KEY (parameter_version_id)`.
- `parameter_version_region_name_parameter_code_version_no_key`: `UNIQUE (region_name, parameter_code, version_no)`.
- `parameter_version_approved_by_fkey`: `FOREIGN KEY (approved_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `parameter_version_pkey`: `CREATE UNIQUE INDEX parameter_version_pkey ON red_house.parameter_version USING btree (parameter_version_id)`.
- `parameter_version_region_name_parameter_code_version_no_key`: `CREATE UNIQUE INDEX parameter_version_region_name_parameter_code_version_no_key ON red_house.parameter_version USING btree (region_name, parameter_code, version_no)`.

## party

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| party_id | uuid | NO | gen_random_uuid() |
| party_name | character varying(120) | NO | — |

Restricciones:

- `party_pkey`: `PRIMARY KEY (party_id)`.

Índices:

- `party_pkey`: `CREATE UNIQUE INDEX party_pkey ON red_house.party USING btree (party_id)`.

## ranking_run

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| evaluation_id | uuid | NO | — |
| algorithm_version | text | NO | — |
| factors | jsonb | NO | — |
| result | jsonb | NO | — |
| elapsed_ms | double precision | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_rankings_pkey`: `PRIMARY KEY (id)`.
- `shared_rankings_evaluation_id`: `FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE`.
- `shared_rankings_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_rankings_pkey`: `CREATE UNIQUE INDEX api_rankings_pkey ON red_house.ranking_run USING btree (id)`.

## recipient

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| recipient_id | uuid | NO | — |
| institution_id | uuid | NO | — |
| record_code | text | NO | — |
| display_name | text | NO | — |
| blood_group | text | NO | — |
| requirement | text | YES | — |
| legacy_urgency | character varying(20) | YES | — |
| studies | text | NO | — |
| restrictions | text | YES | — |
| current_status | text | NO | 'ACTIVE'::text |
| responsible_id | uuid | YES | — |
| registered_at | timestamp with time zone | YES | now() |
| version_no | integer | NO | 1 |
| kind | text | NO | — |
| organ_type | text | YES | — |

Restricciones:

- `api_recipients_check`: `CHECK ((((kind = 'BLOOD'::text) AND (organ_type IS NULL)) OR ((kind = 'ORGAN'::text) AND (organ_type = ANY (ARRAY['KIDNEY'::text, 'LIVER'::text, 'HEART'::text])))))`.
- `api_recipients_kind_check`: `CHECK ((kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text])))`.
- `recipient_urgency_check`: `CHECK (((legacy_urgency)::text = ANY (ARRAY[('URGENT'::character varying)::text, ('PRIORITY'::character varying)::text, ('ROUTINE'::character varying)::text])))`.
- `api_recipients_tenant_id_folio_key`: `UNIQUE (institution_id, record_code)`.
- `recipient_pkey`: `PRIMARY KEY (recipient_id)`.
- `recipient_responsible_id_fkey`: `FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_recipients_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_recipients_tenant_id_folio_key`: `CREATE UNIQUE INDEX api_recipients_tenant_id_folio_key ON red_house.recipient USING btree (institution_id, record_code)`.
- `recipient_pkey`: `CREATE UNIQUE INDEX recipient_pkey ON red_house.recipient USING btree (recipient_id)`.
- `recipient_institution_idx`: `CREATE INDEX recipient_institution_idx ON red_house.recipient USING btree (institution_id)`.

## regional_route

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| route_id | uuid | NO | — |
| origin_id | uuid | NO | — |
| destination_id | uuid | NO | — |
| distance_km | double precision | NO | — |
| travel_minutes | integer | NO | — |
| source_reference | text | NO | — |
| recorded_by | uuid | YES | — |
| recorded_at | timestamp with time zone | NO | now() |
| version_no | integer | NO | 1 |
| region_id | uuid | NO | — |

Restricciones:

- `api_routes_distance_km_check`: `CHECK ((distance_km >= (0)::double precision))`.
- `api_routes_travel_minutes_check`: `CHECK ((travel_minutes >= 0))`.
- `api_routes_origin_id_destination_id_key`: `UNIQUE (origin_id, destination_id)`.
- `regional_route_pkey`: `PRIMARY KEY (route_id)`.
- `regional_route_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_routes_destination_id`: `FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_routes_origin_id`: `FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_routes_origin_id_destination_id_key`: `CREATE UNIQUE INDEX api_routes_origin_id_destination_id_key ON red_house.regional_route USING btree (origin_id, destination_id)`.
- `regional_route_pkey`: `CREATE UNIQUE INDEX regional_route_pkey ON red_house.regional_route USING btree (route_id)`.

## request_event

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| event_id | uuid | NO | gen_random_uuid() |
| request_id | uuid | NO | — |
| action | character varying(30) | NO | — |
| actor_id | uuid | NO | — |
| occurred_at | timestamp with time zone | NO | now() |
| observation | character varying(240) | NO | — |

Restricciones:

- `request_event_pkey`: `PRIMARY KEY (event_id)`.
- `request_event_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `request_event_request_id_fkey`: `FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE`.

Índices:

- `request_event_pkey`: `CREATE UNIQUE INDEX request_event_pkey ON red_house.request_event USING btree (event_id)`.

## request_hold

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| request_id | uuid | NO | — |
| recipient_id | uuid | NO | — |
| operation_id | uuid | NO | — |
| resource_id | uuid | NO | — |
| kind | text | NO | — |
| request_version | integer | NO | — |
| region_id | uuid | NO | — |
| status | text | NO | 'HELD'::text |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_holds_operation_id_key`: `UNIQUE (operation_id)`.
- `api_holds_pkey`: `PRIMARY KEY (id)`.
- `api_holds_recipient_id_fkey`: `FOREIGN KEY (recipient_id) REFERENCES red_house.recipient(recipient_id) DEFERRABLE`.
- `api_holds_request_id_fkey`: `FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE`.
- `shared_holds_resource_id`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.

Índices:

- `api_holds_operation_id_key`: `CREATE UNIQUE INDEX api_holds_operation_id_key ON red_house.request_hold USING btree (operation_id)`.
- `api_holds_pkey`: `CREATE UNIQUE INDEX api_holds_pkey ON red_house.request_hold USING btree (id)`.
- `api_organ_patient_reserved`: `CREATE UNIQUE INDEX api_organ_patient_reserved ON red_house.request_hold USING btree (recipient_id) WHERE ((kind = 'ORGAN'::text) AND (status = ANY (ARRAY['HELD'::text, 'CONFIRMED'::text, 'RECEIVED'::text])))`.

## resource

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| resource_id | uuid | NO | — |
| traceability_code | character varying(40) | YES | — |
| resource_kind | text | NO | — |
| tenant_id | uuid | NO | — |
| region_id | uuid | NO | — |
| folio | text | NO | — |
| current_institution_id | uuid | NO | — |
| donation_id | uuid | YES | — |
| component | text | NO | — |
| blood_group | text | NO | — |
| expires_at | timestamp with time zone | NO | — |
| status | text | NO | 'QUARANTINE'::text |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |
| location_id | uuid | YES | — |
| collected_at | timestamp with time zone | YES | — |

Restricciones:

- `api_resources_kind_check`: `CHECK ((resource_kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text])))`.
- `api_resources_tenant_id_folio_key`: `UNIQUE (tenant_id, folio)`.
- `resource_pkey`: `PRIMARY KEY (resource_id)`.
- `resource_traceability_code_key`: `UNIQUE (traceability_code)`.
- `shared_resources_current_institution_id`: `FOREIGN KEY (current_institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_resources_donation_id`: `FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id) DEFERRABLE`.
- `shared_resources_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_resources_tenant_id_folio_key`: `CREATE UNIQUE INDEX api_resources_tenant_id_folio_key ON red_house.resource USING btree (tenant_id, folio)`.
- `resource_pkey`: `CREATE UNIQUE INDEX resource_pkey ON red_house.resource USING btree (resource_id)`.
- `resource_traceability_code_key`: `CREATE UNIQUE INDEX resource_traceability_code_key ON red_house.resource USING btree (traceability_code)`.
- `api_availability_page`: `CREATE INDEX api_availability_page ON red_house.resource USING btree (region_id, expires_at, resource_id) WHERE (status = 'AVAILABLE'::text)`.
- `api_available_resources`: `CREATE INDEX api_available_resources ON red_house.resource USING btree (region_id, resource_kind, component, expires_at) WHERE (status = 'AVAILABLE'::text)`.

## resource_review

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| resource_id | uuid | NO | — |
| actor_id | uuid | NO | — |
| decision | text | NO | — |
| reason | text | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_resource_reviews_pkey`: `PRIMARY KEY (id)`.
- `api_resource_reviews_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.
- `shared_resource_reviews_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `api_resource_reviews_pkey`: `CREATE UNIQUE INDEX api_resource_reviews_pkey ON red_house.resource_review USING btree (id)`.

## role

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| role_code | character varying(30) | NO | — |
| role_name | character varying(80) | NO | — |
| is_enabled | boolean | NO | — |

Restricciones:

- `role_pkey`: `PRIMARY KEY (role_code)`.

Índices:

- `role_pkey`: `CREATE UNIQUE INDEX role_pkey ON red_house.role USING btree (role_code)`.

## schema_migration

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| version | integer | NO | — |
| description | text | NO | — |
| installed_at | timestamp with time zone | NO | now() |

Restricciones:

- `schema_migration_pkey`: `PRIMARY KEY (version)`.

Índices:

- `schema_migration_pkey`: `CREATE UNIQUE INDEX schema_migration_pkey ON red_house.schema_migration USING btree (version)`.

## service_activity_events

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| service | text | NO | — |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| event | jsonb | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `service_activity_events_pkey`: `PRIMARY KEY (service, id)`.

Índices:

- `service_activity_events_pkey`: `CREATE UNIQUE INDEX service_activity_events_pkey ON red_house.service_activity_events USING btree (service, id)`.

## service_decisions

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| service | text | NO | — |
| id | uuid | NO | — |
| resource_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| actor_id | uuid | NO | — |
| action | text | NO | — |
| reason | text | NO | — |
| changes | jsonb | NO | '{}'::jsonb |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `service_decisions_pkey`: `PRIMARY KEY (service, id)`.

Índices:

- `service_decisions_pkey`: `CREATE UNIQUE INDEX service_decisions_pkey ON red_house.service_decisions USING btree (service, id)`.

## service_health_check

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| check_id | uuid | NO | — |
| service | text | NO | — |
| state | text | NO | — |
| elapsed_ms | double precision | NO | — |
| dependency | text | YES | — |
| last_error | text | YES | — |
| deployed_version | text | YES | — |
| checked_at | timestamp with time zone | NO | now() |

Restricciones:

- `service_health_check_pkey`: `PRIMARY KEY (check_id)`.

Índices:

- `service_health_check_pkey`: `CREATE UNIQUE INDEX service_health_check_pkey ON red_house.service_health_check USING btree (check_id)`.
- `api_checks_latest`: `CREATE INDEX api_checks_latest ON red_house.service_health_check USING btree (service, checked_at DESC)`.
- `health_service_time`: `CREATE INDEX health_service_time ON red_house.service_health_check USING btree (service, checked_at DESC)`.

## service_idempotency

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| service | text | NO | — |
| id | uuid | NO | — |
| user_id | uuid | NO | — |
| key | text | NO | — |
| operation | text | NO | — |
| fingerprint | text | NO | — |
| result | jsonb | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `service_idempotency_pkey`: `PRIMARY KEY (service, id)`.
- `service_idempotency_service_user_id_key_key`: `UNIQUE (service, user_id, key)`.

Índices:

- `service_idempotency_pkey`: `CREATE UNIQUE INDEX service_idempotency_pkey ON red_house.service_idempotency USING btree (service, id)`.
- `service_idempotency_service_user_id_key_key`: `CREATE UNIQUE INDEX service_idempotency_service_user_id_key_key ON red_house.service_idempotency USING btree (service, user_id, key)`.

## service_inbox

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| service | text | NO | — |
| event_id | uuid | NO | — |
| fingerprint | text | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `service_inbox_pkey`: `PRIMARY KEY (service, event_id)`.

Índices:

- `service_inbox_pkey`: `CREATE UNIQUE INDEX service_inbox_pkey ON red_house.service_inbox USING btree (service, event_id)`.

## service_outbox

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| service | text | NO | — |
| id | uuid | NO | — |
| event_id | uuid | NO | — |
| target | text | NO | — |
| event | jsonb | NO | — |
| created_at | timestamp with time zone | NO | now() |
| delivered_at | timestamp with time zone | YES | — |
| attempts | integer | NO | 0 |
| next_attempt | timestamp with time zone | NO | now() |
| last_error | text | YES | — |

Restricciones:

- `service_outbox_pkey`: `PRIMARY KEY (service, id)`.
- `service_outbox_service_event_id_target_key`: `UNIQUE (service, event_id, target)`.

Índices:

- `service_outbox_pkey`: `CREATE UNIQUE INDEX service_outbox_pkey ON red_house.service_outbox USING btree (service, id)`.
- `service_outbox_service_event_id_target_key`: `CREATE UNIQUE INDEX service_outbox_service_event_id_target_key ON red_house.service_outbox USING btree (service, event_id, target)`.
- `shared_outbox_pending`: `CREATE INDEX shared_outbox_pending ON red_house.service_outbox USING btree (service, next_attempt, created_at) WHERE (delivered_at IS NULL)`.

## service_schema_version

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| service | text | NO | — |
| version | integer | NO | — |
| installed_at | timestamp with time zone | NO | now() |

Restricciones:

- `service_schema_version_pkey`: `PRIMARY KEY (service, version)`.

Índices:

- `service_schema_version_pkey`: `CREATE UNIQUE INDEX service_schema_version_pkey ON red_house.service_schema_version USING btree (service, version)`.

## service_worker_health

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| service | text | NO | — |
| id | integer | NO | — |
| checked_at | timestamp with time zone | NO | — |
| last_success | timestamp with time zone | YES | — |
| last_error | text | YES | — |

Restricciones:

- `service_worker_health_id_check`: `CHECK ((id = 1))`.
- `service_worker_health_pkey`: `PRIMARY KEY (service, id)`.

Índices:

- `service_worker_health_pkey`: `CREATE UNIQUE INDEX service_worker_health_pkey ON red_house.service_worker_health USING btree (service, id)`.

## shipment

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| shipment_id | uuid | NO | — |
| allocation_id | uuid | NO | — |
| transport_id | uuid | NO | — |
| vehicle | character varying(120) | YES | — |
| departure_at | timestamp with time zone | NO | — |
| eta | timestamp with time zone | NO | — |
| current_status | text | NO | 'PLANNED'::text |
| version_no | integer | NO | 1 |
| organ_allocation_id | uuid | YES | — |
| origin_id | uuid | NO | — |
| destination_id | uuid | NO | — |
| region_id | uuid | NO | — |
| sequence | integer | NO | 0 |
| inventory_pending | boolean | NO | true |
| expires_at | timestamp with time zone | NO | — |

Restricciones:

- `api_shipments_check`: `CHECK ((eta > departure_at))`.
- `api_shipments_check1`: `CHECK ((eta < expires_at))`.
- `api_shipments_reservation_id_key`: `UNIQUE (allocation_id)`.
- `shipment_organ_allocation_id_key`: `UNIQUE (organ_allocation_id)`.
- `shipment_pkey`: `PRIMARY KEY (shipment_id)`.
- `shared_shipments_destination_id`: `FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_shipments_origin_id`: `FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_shipments_reservation_id`: `FOREIGN KEY (allocation_id) REFERENCES red_house.blood_allocation(allocation_id) DEFERRABLE`.
- `shared_shipments_transport_user_id`: `FOREIGN KEY (transport_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shipment_organ_allocation_id_fkey`: `FOREIGN KEY (organ_allocation_id) REFERENCES red_house.organ_allocation(allocation_id) DEFERRABLE`.

Índices:

- `api_shipments_reservation_id_key`: `CREATE UNIQUE INDEX api_shipments_reservation_id_key ON red_house.shipment USING btree (allocation_id)`.
- `shipment_organ_allocation_id_key`: `CREATE UNIQUE INDEX shipment_organ_allocation_id_key ON red_house.shipment USING btree (organ_allocation_id)`.
- `shipment_pkey`: `CREATE UNIQUE INDEX shipment_pkey ON red_house.shipment USING btree (shipment_id)`.
- `shipment_transport_idx`: `CREATE INDEX shipment_transport_idx ON red_house.shipment USING btree (transport_id)`.

## shipment_transition

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| shipment_id | uuid | NO | — |
| sequence | integer | NO | — |
| state | text | NO | — |
| actor_id | uuid | NO | — |
| reason | text | NO | — |
| evidence | jsonb | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_transitions_pkey`: `PRIMARY KEY (id)`.
- `api_transitions_shipment_id_sequence_key`: `UNIQUE (shipment_id, sequence)`.
- `api_transitions_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE`.
- `shared_transitions_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `api_transitions_pkey`: `CREATE UNIQUE INDEX api_transitions_pkey ON red_house.shipment_transition USING btree (id)`.
- `api_transitions_shipment_id_sequence_key`: `CREATE UNIQUE INDEX api_transitions_shipment_id_sequence_key ON red_house.shipment_transition USING btree (shipment_id, sequence)`.

## site

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| site_id | uuid | NO | gen_random_uuid() |
| institution_id | uuid | NO | — |
| site_code | character varying(30) | NO | — |
| site_name | character varying(120) | NO | — |
| street | character varying(200) | NO | — |
| city | character varying(100) | NO | — |
| site_status | character varying(10) | NO | 'ACTIVE'::character varying |
| version_no | integer | NO | 1 |

Restricciones:

- `site_site_status_check`: `CHECK (((site_status)::text = ANY (ARRAY[('ACTIVE'::character varying)::text, ('INACTIVE'::character varying)::text])))`.
- `site_institution_id_site_code_key`: `UNIQUE (institution_id, site_code)`.
- `site_pkey`: `PRIMARY KEY (site_id)`.
- `site_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `site_institution_id_site_code_key`: `CREATE UNIQUE INDEX site_institution_id_site_code_key ON red_house.site USING btree (institution_id, site_code)`.
- `site_pkey`: `CREATE UNIQUE INDEX site_pkey ON red_house.site USING btree (site_id)`.
- `site_institution_idx`: `CREATE INDEX site_institution_idx ON red_house.site USING btree (institution_id)`.

## site_schedule

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| schedule_id | uuid | NO | gen_random_uuid() |
| site_id | uuid | NO | — |
| weekday | smallint | NO | — |
| opens_at | time without time zone | NO | — |
| closes_at | time without time zone | NO | — |

Restricciones:

- `site_schedule_check`: `CHECK ((closes_at > opens_at))`.
- `site_schedule_weekday_check`: `CHECK (((weekday >= 1) AND (weekday <= 7)))`.
- `site_schedule_pkey`: `PRIMARY KEY (schedule_id)`.
- `site_schedule_site_id_weekday_opens_at_key`: `UNIQUE (site_id, weekday, opens_at)`.
- `site_schedule_site_id_fkey`: `FOREIGN KEY (site_id) REFERENCES red_house.site(site_id) DEFERRABLE`.

Índices:

- `site_schedule_pkey`: `CREATE UNIQUE INDEX site_schedule_pkey ON red_house.site_schedule USING btree (schedule_id)`.
- `site_schedule_site_id_weekday_opens_at_key`: `CREATE UNIQUE INDEX site_schedule_site_id_weekday_opens_at_key ON red_house.site_schedule USING btree (site_id, weekday, opens_at)`.

## storage_location

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| location_id | uuid | NO | gen_random_uuid() |
| site_id | uuid | NO | — |
| location_code | character varying(30) | NO | — |
| location_description | character varying(150) | NO | — |
| is_active | boolean | NO | true |
| version_no | integer | NO | 1 |

Restricciones:

- `storage_location_pkey`: `PRIMARY KEY (location_id)`.
- `storage_location_site_id_location_code_key`: `UNIQUE (site_id, location_code)`.
- `storage_location_site_id_fkey`: `FOREIGN KEY (site_id) REFERENCES red_house.site(site_id) DEFERRABLE`.

Índices:

- `storage_location_pkey`: `CREATE UNIQUE INDEX storage_location_pkey ON red_house.storage_location USING btree (location_id)`.
- `storage_location_site_id_location_code_key`: `CREATE UNIQUE INDEX storage_location_site_id_location_code_key ON red_house.storage_location USING btree (site_id, location_code)`.
- `storage_site_idx`: `CREATE INDEX storage_site_idx ON red_house.storage_location USING btree (site_id)`.

## stored_file

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| file_id | uuid | NO | — |
| shipment_id | uuid | NO | — |
| owner_id | uuid | NO | — |
| object_path | text | NO | — |
| mime_type | text | NO | — |
| size_bytes | integer | NO | — |
| sha256 | text | NO | — |
| current_status | text | NO | 'PENDING'::text |
| generation | text | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_files_object_path_key`: `UNIQUE (object_path)`.
- `api_files_size_check`: `CHECK (((size_bytes >= 1) AND (size_bytes <= 10485760)))`.
- `stored_file_pkey`: `PRIMARY KEY (file_id)`.
- `api_files_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE`.
- `shared_files_owner_id`: `FOREIGN KEY (owner_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `api_files_object_path_key`: `CREATE UNIQUE INDEX api_files_object_path_key ON red_house.stored_file USING btree (object_path)`.
- `stored_file_pkey`: `CREATE UNIQUE INDEX stored_file_pkey ON red_house.stored_file USING btree (file_id)`.

## transport_telemetry

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| telemetry_id | uuid | NO | — |
| shipment_id | uuid | NO | — |
| actor_id | uuid | NO | — |
| latitude | double precision | NO | — |
| longitude | double precision | NO | — |
| captured_at | timestamp with time zone | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `transport_telemetry_pkey`: `PRIMARY KEY (telemetry_id)`.
- `api_telemetry_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE`.
- `shared_telemetry_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `transport_telemetry_pkey`: `CREATE UNIQUE INDEX transport_telemetry_pkey ON red_house.transport_telemetry USING btree (telemetry_id)`.
- `telemetry_shipment_time`: `CREATE INDEX telemetry_shipment_time ON red_house.transport_telemetry USING btree (shipment_id, captured_at)`.

## user_account

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| account_id | uuid | NO | — |
| party_id | uuid | YES | — |
| login_email | character varying(180) | YES | — |
| password_hash | text | NO | — |
| account_status | character varying(10) | YES | 'ACTIVE'::character varying |
| version_no | integer | NO | 1 |
| registered_at | timestamp with time zone | YES | now() |
| username | text | NO | — |
| tenant_id | uuid | NO | — |
| role | text | NO | — |
| active | boolean | NO | true |

Restricciones:

- `api_users_role_check`: `CHECK ((role = ANY (ARRAY['ADMIN'::text, 'OPERATOR'::text, 'MEDICAL'::text, 'COORDINATOR'::text, 'TRANSPORT'::text, 'AUDITOR'::text, 'DONOR'::text])))`.
- `user_account_account_status_check`: `CHECK (((account_status)::text = ANY (ARRAY[('ACTIVE'::character varying)::text, ('INACTIVE'::character varying)::text])))`.
- `user_account_login_email_check`: `CHECK (((login_email)::text = lower((login_email)::text)))`.
- `api_users_username_key`: `UNIQUE (username)`.
- `user_account_login_email_key`: `UNIQUE (login_email)`.
- `user_account_party_id_key`: `UNIQUE (party_id)`.
- `user_account_pkey`: `PRIMARY KEY (account_id)`.
- `api_users_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_users_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `user_account_party_id_fkey`: `FOREIGN KEY (party_id) REFERENCES red_house.party(party_id) DEFERRABLE`.

Índices:

- `api_users_username_key`: `CREATE UNIQUE INDEX api_users_username_key ON red_house.user_account USING btree (username)`.
- `user_account_login_email_key`: `CREATE UNIQUE INDEX user_account_login_email_key ON red_house.user_account USING btree (login_email)`.
- `user_account_party_id_key`: `CREATE UNIQUE INDEX user_account_party_id_key ON red_house.user_account USING btree (party_id)`.
- `user_account_pkey`: `CREATE UNIQUE INDEX user_account_pkey ON red_house.user_account USING btree (account_id)`.

## web_session

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| session_id | uuid | NO | — |
| account_id | uuid | NO | — |
| expires_at | timestamp with time zone | NO | — |
| revoked_at | timestamp with time zone | YES | — |
| created_at | timestamp with time zone | YES | now() |

Restricciones:

- `web_session_pkey`: `PRIMARY KEY (session_id)`.
- `api_sessions_user_id_fkey`: `FOREIGN KEY (account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `web_session_pkey`: `CREATE UNIQUE INDEX web_session_pkey ON red_house.web_session USING btree (session_id)`.
- `web_session_account_idx`: `CREATE INDEX web_session_account_idx ON red_house.web_session USING btree (account_id)`.

## Almacenamiento técnico del portal: web_runtime.session_revocations

Además de las 71 tablas anteriores, el portal utiliza una tabla técnica en el esquema `web_runtime` de la misma base PostgreSQL. El instalador aplica [web_sessions.sql](../../data/database/web_sessions.sql) con permisos exclusivos para `rh_web_sessions`; los servicios de dominio no tienen acceso. Total instalado tras esta actualización: 72 tablas entre ambos esquemas.

| Columna | Tipo | Regla |
| --- | --- | --- |
| id | text | PK; SHA-256 de la cookie opaca, 64 caracteres hexadecimales |
| payload | bytea, admite NULL | Credenciales cifradas pendientes de revocar; se elimina al confirmar |
| expires | timestamptz | NOT NULL; marca de cierre conservada hasta 24 horas |
| confirmed | boolean | NOT NULL, false inicial; true después de confirmar revocación |

Índices: clave primaria sobre `id`; `session_revocations_pending` sobre `expires` para filas sin confirmar; `session_revocations_expiry` para limpiar vencidas. Sin claves foráneas al dominio: identifica la sesión técnica del navegador, no un expediente clínico. El worker reintenta cierres pendientes; una marca confirmada impide reactivar la cookie desde una copia antigua de Redis. El respaldo PostgreSQL incluye este esquema.

Las sesiones activas y concesiones de renovación residen en Redis con TTL. La credencial Redis del portal solo accede al prefijo `web:*`; la credencial SQL solo accede a esta tabla.

