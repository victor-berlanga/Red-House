# Modelo físico PostgreSQL instalado

Base `red_house`, esquemas `red_house` y `web_runtime`, versión 20. Catálogo extraído en una transacción READ ONLY del laboratorio privado; no contiene filas de negocio ni credenciales. No acredita instalación GCP, validación clínica ni normalización lógica por sí solo.

117 tablas físicas y 226 índices. Las vistas `access_*` adaptan los contratos sin duplicar estas tablas. La correspondencia por propietario está en las fichas de servicios; una vista no constituye otra tabla física.

[Metadatos verificables](../../evidencias/entrega-final/modelos-20261114/postgresql-physical.json) · [SQL de instalación](../../../data/database/schema.sql) · [Diagrama editable](diagramas/postgresql-completo.mmd) · [SVG físico ampliable](diagramas/postgresql-completo.svg). La generación e inspección se identifican por separado en el registro editorial.

## red_house.account_role

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| account_id | uuid | NO | — |
| role_code | character varying(30) | NO | — |
| institution_id | uuid | YES | — |
| region_name | character varying(80) | YES | — |

Restricciones:

- `account_role_account_id_fkey`: `FOREIGN KEY (account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `account_role_check`: `CHECK ((institution_id IS NOT NULL) <> (region_name IS NOT NULL))`.
- `account_role_check1`: `CHECK (role_code::text <> 'OPERATOR'::text OR institution_id IS NOT NULL)`.
- `account_role_check2`: `CHECK ((role_code::text <> ALL (ARRAY['MEDICAL'::character varying::text, 'TRANSPORT'::character varying::text])) OR institution_id IS NOT NULL)`.
- `account_role_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `account_role_pkey`: `PRIMARY KEY (account_id)`.
- `account_role_role_code_fkey`: `FOREIGN KEY (role_code) REFERENCES red_house.role(role_code) DEFERRABLE`.

Índices:

- `account_role_pkey`: `CREATE UNIQUE INDEX account_role_pkey ON red_house.account_role USING btree (account_id)`.
- `account_role_scope_idx`: `CREATE INDEX account_role_scope_idx ON red_house.account_role USING btree (institution_id)`.

Disparadores no internos:


## red_house.accreditations

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| issuer | text | NO | — |
| category | text | NO | — |
| reference | text | NO | — |
| valid_from | timestamp with time zone | NO | — |
| valid_until | timestamp with time zone | NO | — |
| author_id | uuid | NO | — |
| supersedes | uuid | YES | — |
| version | integer | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `accreditations_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `accreditations_check`: `CHECK (valid_until > valid_from)`.
- `accreditations_pkey`: `PRIMARY KEY (id)`.
- `accreditations_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.accreditations(id)`.
- `accreditations_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `accreditations_pkey`: `CREATE UNIQUE INDEX accreditations_pkey ON red_house.accreditations USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.accreditations FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.alert_actions

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| alert_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| actor_id | uuid | YES | — |
| action | text | NO | — |
| reason | text | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `alert_actions_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id)`.
- `alert_actions_alert_id_action_key`: `UNIQUE (alert_id, action)`.
- `alert_actions_alert_id_fkey`: `FOREIGN KEY (alert_id) REFERENCES red_house.notification(notification_id)`.
- `alert_actions_pkey`: `PRIMARY KEY (id)`.
- `alert_actions_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `alert_actions_alert_id_action_key`: `CREATE UNIQUE INDEX alert_actions_alert_id_action_key ON red_house.alert_actions USING btree (alert_id, action)`.
- `alert_actions_pkey`: `CREATE UNIQUE INDEX alert_actions_pkey ON red_house.alert_actions USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.alert_actions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.alert_deliveries

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| alert_id | uuid | NO | — |
| subscription_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| stage | text | NO | — |
| status | text | NO | 'PENDING'::text |
| attempts | integer | NO | 0 |
| next_attempt | timestamp with time zone | NO | now() |
| accepted_at | timestamp with time zone | YES | — |
| last_error | text | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `alert_deliveries_alert_id_fkey`: `FOREIGN KEY (alert_id) REFERENCES red_house.notification(notification_id)`.
- `alert_deliveries_alert_id_subscription_id_stage_key`: `UNIQUE (alert_id, subscription_id, stage)`.
- `alert_deliveries_pkey`: `PRIMARY KEY (id)`.
- `alert_deliveries_stage_check`: `CHECK (stage = ANY (ARRAY['INITIAL'::text, 'REMINDER'::text, 'ESCALATED'::text]))`.
- `alert_deliveries_subscription_id_fkey`: `FOREIGN KEY (subscription_id) REFERENCES red_house.alert_subscriptions(id)`.
- `alert_deliveries_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `alert_deliveries_alert_id_subscription_id_stage_key`: `CREATE UNIQUE INDEX alert_deliveries_alert_id_subscription_id_stage_key ON red_house.alert_deliveries USING btree (alert_id, subscription_id, stage)`.
- `alert_deliveries_pkey`: `CREATE UNIQUE INDEX alert_deliveries_pkey ON red_house.alert_deliveries USING btree (id)`.

Disparadores no internos:


## red_house.alert_policies

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| message_code | text | NO | — |
| severity | text | NO | — |
| reminder_seconds | integer | NO | — |
| escalate_seconds | integer | NO | — |
| escalation_role | text | NO | — |
| author_id | uuid | NO | — |
| source | text | NO | — |
| effective_at | timestamp with time zone | NO | — |
| supersedes | uuid | YES | — |
| active | boolean | NO | true |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `alert_policies_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `alert_policies_check`: `CHECK (escalate_seconds > reminder_seconds)`.
- `alert_policies_pkey`: `PRIMARY KEY (id)`.
- `alert_policies_reminder_seconds_check`: `CHECK (reminder_seconds > 0)`.
- `alert_policies_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.alert_policies(id)`.
- `alert_policies_supersedes_key`: `UNIQUE (supersedes)`.
- `alert_policies_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.
- `alert_policies_tenant_id_message_code_version_key`: `UNIQUE (tenant_id, message_code, version)`.

Índices:

- `alert_policies_pkey`: `CREATE UNIQUE INDEX alert_policies_pkey ON red_house.alert_policies USING btree (id)`.
- `alert_policies_supersedes_key`: `CREATE UNIQUE INDEX alert_policies_supersedes_key ON red_house.alert_policies USING btree (supersedes)`.
- `alert_policies_tenant_id_message_code_version_key`: `CREATE UNIQUE INDEX alert_policies_tenant_id_message_code_version_key ON red_house.alert_policies USING btree (tenant_id, message_code, version)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.alert_policies FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.alert_subscriptions

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| user_id | uuid | NO | — |
| role | text | NO | — |
| channel | text | NO | — |
| destination | text | NO | — |
| active | boolean | NO | true |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `alert_subscriptions_channel_check`: `CHECK (channel = ANY (ARRAY['EMAIL'::text, 'PUSH'::text]))`.
- `alert_subscriptions_pkey`: `PRIMARY KEY (id)`.
- `alert_subscriptions_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.
- `alert_subscriptions_user_id_channel_key`: `UNIQUE (user_id, channel)`.
- `alert_subscriptions_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES red_house.user_account(account_id)`.

Índices:

- `alert_subscriptions_pkey`: `CREATE UNIQUE INDEX alert_subscriptions_pkey ON red_house.alert_subscriptions USING btree (id)`.
- `alert_subscriptions_user_id_channel_key`: `CREATE UNIQUE INDEX alert_subscriptions_user_id_channel_key ON red_house.alert_subscriptions USING btree (user_id, channel)`.

Disparadores no internos:


## red_house.algorithm_run

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

- `algorithm_run_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `algorithm_run_blood_evaluation_id_fkey`: `FOREIGN KEY (blood_evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE`.
- `algorithm_run_check`: `CHECK (num_nonnulls(blood_evaluation_id, organ_evaluation_id) <= 1)`.
- `algorithm_run_elapsed_ms_check`: `CHECK (elapsed_ms >= 0::double precision)`.
- `algorithm_run_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `algorithm_run_operation_check`: `CHECK (operation = ANY (ARRAY['RANKING'::text, 'BALANCING'::text]))`.
- `algorithm_run_organ_evaluation_id_fkey`: `FOREIGN KEY (organ_evaluation_id) REFERENCES red_house.organ_evaluation(evaluation_id) DEFERRABLE`.
- `algorithm_run_pkey`: `PRIMARY KEY (run_id)`.

Índices:

- `algorithm_run_pkey`: `CREATE UNIQUE INDEX algorithm_run_pkey ON red_house.algorithm_run USING btree (run_id)`.

Disparadores no internos:

- `algorithm_run_history`: `CREATE TRIGGER algorithm_run_history BEFORE DELETE OR UPDATE ON red_house.algorithm_run FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.algorithm_runs

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| author_id | uuid | NO | — |
| algorithm_version | text | NO | — |
| source | text | NO | — |
| snapshot | jsonb | NO | — |
| result | jsonb | NO | — |
| fingerprint | text | NO | — |
| elapsed_ms | double precision | NO | — |
| synthetic | boolean | NO | true |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `algorithm_runs_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `algorithm_runs_pkey`: `PRIMARY KEY (id)`.
- `algorithm_runs_synthetic_check`: `CHECK (synthetic)`.
- `algorithm_runs_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `algorithm_runs_pkey`: `CREATE UNIQUE INDEX algorithm_runs_pkey ON red_house.algorithm_runs USING btree (id)`.
- `algorithm_runs_tenant_time`: `CREATE INDEX algorithm_runs_tenant_time ON red_house.algorithm_runs USING btree (tenant_id, created_at DESC, id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.algorithm_runs FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.allocation_operation

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

Disparadores no internos:


## red_house.anomaly_actions

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| review_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| author_id | uuid | NO | — |
| state | text | NO | — |
| reason | text | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `anomaly_actions_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `anomaly_actions_pkey`: `PRIMARY KEY (id)`.
- `anomaly_actions_review_id_fkey`: `FOREIGN KEY (review_id) REFERENCES red_house.anomaly_reviews(id)`.
- `anomaly_actions_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `anomaly_actions_pkey`: `CREATE UNIQUE INDEX anomaly_actions_pkey ON red_house.anomaly_actions USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.anomaly_actions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.anomaly_reviews

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| region_id | uuid | NO | — |
| source | text | NO | — |
| source_run_id | uuid | NO | — |
| deduplication_key | text | NO | — |
| evidence | jsonb | NO | — |
| correlation_id | text | NO | — |
| responsible_id | uuid | NO | — |
| state | text | NO | 'OPEN'::text |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `anomaly_reviews_deduplication_key_key`: `UNIQUE (deduplication_key)`.
- `anomaly_reviews_pkey`: `PRIMARY KEY (id)`.
- `anomaly_reviews_responsible_id_fkey`: `FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id)`.
- `anomaly_reviews_state_check`: `CHECK (state = ANY (ARRAY['OPEN'::text, 'CONFIRMED'::text, 'DISMISSED'::text]))`.
- `anomaly_reviews_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `anomaly_reviews_deduplication_key_key`: `CREATE UNIQUE INDEX anomaly_reviews_deduplication_key_key ON red_house.anomaly_reviews USING btree (deduplication_key)`.
- `anomaly_reviews_pkey`: `CREATE UNIQUE INDEX anomaly_reviews_pkey ON red_house.anomaly_reviews USING btree (id)`.

Disparadores no internos:


## red_house.appointment

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| appointment_id | uuid | NO | — |
| donor_id | uuid | NO | — |
| campaign_id | uuid | NO | — |
| current_status | text | NO | 'BOOKED'::text |
| created_at | timestamp with time zone | NO | now() |
| tenant_id | uuid | NO | — |

Restricciones:

- `api_appointments_campaign_id_fkey`: `FOREIGN KEY (campaign_id) REFERENCES red_house.campaign(campaign_id) DEFERRABLE`.
- `api_appointments_donor_id_fkey`: `FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id) DEFERRABLE`.
- `appointment_pkey`: `PRIMARY KEY (appointment_id)`.
- `shared_appointments_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_active_appointment`: `CREATE UNIQUE INDEX api_active_appointment ON red_house.appointment USING btree (donor_id, campaign_id) WHERE (current_status = 'BOOKED'::text)`.
- `appointment_active`: `CREATE UNIQUE INDEX appointment_active ON red_house.appointment USING btree (donor_id, campaign_id) WHERE (current_status = 'BOOKED'::text)`.
- `appointment_pkey`: `CREATE UNIQUE INDEX appointment_pkey ON red_house.appointment USING btree (appointment_id)`.

Disparadores no internos:


## red_house.appointment_reminders

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| version | integer | NO | — |
| sent_at | timestamp with time zone | NO | now() |

Restricciones:

- `appointment_reminders_id_fkey`: `FOREIGN KEY (id) REFERENCES red_house.appointment(appointment_id)`.
- `appointment_reminders_pkey`: `PRIMARY KEY (id)`.

Índices:

- `appointment_reminders_pkey`: `CREATE UNIQUE INDEX appointment_reminders_pkey ON red_house.appointment_reminders USING btree (id)`.

Disparadores no internos:


## red_house.appointment_slots

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| slot_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| status | text | NO | 'BOOKED'::text |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `appointment_slots_id_fkey`: `FOREIGN KEY (id) REFERENCES red_house.appointment(appointment_id)`.
- `appointment_slots_pkey`: `PRIMARY KEY (id)`.
- `appointment_slots_slot_id_fkey`: `FOREIGN KEY (slot_id) REFERENCES red_house.campaign_slots(id)`.
- `appointment_slots_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `appointment_slots_pkey`: `CREATE UNIQUE INDEX appointment_slots_pkey ON red_house.appointment_slots USING btree (id)`.

Disparadores no internos:


## red_house.audit_change

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| event_id | uuid | NO | — |
| field_name | character varying(60) | NO | — |
| previous_value | character varying(240) | YES | — |
| new_value | character varying(240) | YES | — |

Restricciones:

- `audit_change_event_id_fkey`: `FOREIGN KEY (event_id) REFERENCES red_house.audit_event(event_id) DEFERRABLE`.
- `audit_change_pkey`: `PRIMARY KEY (event_id, field_name)`.

Índices:

- `audit_change_pkey`: `CREATE UNIQUE INDEX audit_change_pkey ON red_house.audit_change USING btree (event_id, field_name)`.

Disparadores no internos:

- `audit_change_append_only`: `CREATE TRIGGER audit_change_append_only BEFORE DELETE OR UPDATE ON red_house.audit_change FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.audit_event

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

- `audit_event_outcome_check`: `CHECK (outcome::text = ANY (ARRAY['SUCCESS'::character varying::text, 'DENIED'::character varying::text, 'FAILED'::character varying::text]))`.
- `audit_event_pkey`: `PRIMARY KEY (event_id)`.
- `shared_audit_events_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_audit_events_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_audit_search`: `CREATE INDEX api_audit_search ON red_house.audit_event USING btree (region_id, institution_id, occurred_at)`.
- `audit_action_search`: `CREATE INDEX audit_action_search ON red_house.audit_event USING btree (region_id, action, actor_id)`.
- `audit_correlation_search`: `CREATE INDEX audit_correlation_search ON red_house.audit_event USING btree (region_id, ((event ->> 'correlation_id'::text)))`.
- `audit_event_pkey`: `CREATE UNIQUE INDEX audit_event_pkey ON red_house.audit_event USING btree (event_id)`.
- `audit_execution_search`: `CREATE INDEX audit_execution_search ON red_house.audit_event USING btree (region_id, access_auditoria.event_time((event ->> 'occurred_at'::text)), event_id)`.
- `audit_region_time_idx`: `CREATE INDEX audit_region_time_idx ON red_house.audit_event USING btree (region_name, occurred_at DESC)`.
- `audit_resource_search`: `CREATE INDEX audit_resource_search ON red_house.audit_event USING btree (region_id, ((event ->> 'resource_id'::text)))`.
- `audit_scope_time_idx`: `CREATE INDEX audit_scope_time_idx ON red_house.audit_event USING btree (institution_id, occurred_at DESC)`.

Disparadores no internos:

- `audit_append_only`: `CREATE TRIGGER audit_append_only BEFORE DELETE OR UPDATE ON red_house.audit_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.audit_finding_actions

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| finding_id | uuid | NO | — |
| actor_id | uuid | NO | — |
| actor_name | text | NO | — |
| actor_role | text | NO | — |
| previous_status | text | YES | — |
| status | text | NO | — |
| reason | text | NO | — |
| corrective_action | text | YES | — |
| evidence | text | YES | — |
| correlation_id | uuid | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_audit_finding_actions_corrective_action_check`: `CHECK (corrective_action IS NULL OR length(corrective_action) >= 6 AND length(corrective_action) <= 1000)`.
- `api_audit_finding_actions_evidence_check`: `CHECK (evidence IS NULL OR length(evidence) >= 6 AND length(evidence) <= 1000)`.
- `api_audit_finding_actions_finding_id_fkey`: `FOREIGN KEY (finding_id) REFERENCES red_house.audit_findings(id) DEFERRABLE`.
- `api_audit_finding_actions_pkey`: `PRIMARY KEY (id)`.
- `api_audit_finding_actions_reason_check`: `CHECK (length(reason) >= 6 AND length(reason) <= 1000)`.
- `shared_audit_finding_actions_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `api_audit_finding_actions_pkey`: `CREATE UNIQUE INDEX api_audit_finding_actions_pkey ON red_house.audit_finding_actions USING btree (id)`.
- `api_audit_finding_actions_timeline`: `CREATE INDEX api_audit_finding_actions_timeline ON red_house.audit_finding_actions USING btree (finding_id, created_at, id)`.
- `audit_finding_actions_timeline`: `CREATE INDEX audit_finding_actions_timeline ON red_house.audit_finding_actions USING btree (finding_id, created_at, id)`.

Disparadores no internos:

- `api_immutable`: `CREATE TRIGGER api_immutable BEFORE DELETE OR UPDATE ON red_house.audit_finding_actions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.audit_finding_links

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| finding_id | uuid | NO | — |
| event_id | uuid | NO | — |

Restricciones:

- `api_audit_finding_links_event_id_fkey`: `FOREIGN KEY (event_id) REFERENCES red_house.audit_event(event_id) DEFERRABLE`.
- `api_audit_finding_links_finding_id_event_id_key`: `UNIQUE (finding_id, event_id)`.
- `api_audit_finding_links_finding_id_fkey`: `FOREIGN KEY (finding_id) REFERENCES red_house.audit_findings(id) DEFERRABLE`.
- `api_audit_finding_links_pkey`: `PRIMARY KEY (id)`.

Índices:

- `api_audit_finding_links_finding_id_event_id_key`: `CREATE UNIQUE INDEX api_audit_finding_links_finding_id_event_id_key ON red_house.audit_finding_links USING btree (finding_id, event_id)`.
- `api_audit_finding_links_pkey`: `CREATE UNIQUE INDEX api_audit_finding_links_pkey ON red_house.audit_finding_links USING btree (id)`.

Disparadores no internos:

- `api_immutable`: `CREATE TRIGGER api_immutable BEFORE DELETE OR UPDATE ON red_house.audit_finding_links FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.audit_findings

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| region_id | uuid | NO | — |
| description | text | NO | — |
| priority | text | NO | — |
| assignee_id | uuid | NO | — |
| assignee_tenant_id | uuid | NO | — |
| assignee_name | text | NO | — |
| created_by | uuid | NO | — |
| resource_id | uuid | YES | — |
| evidence | text | YES | — |
| status | text | NO | 'OPEN'::text |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_audit_findings_description_check`: `CHECK (length(description) >= 6 AND length(description) <= 1000)`.
- `api_audit_findings_evidence_check`: `CHECK (evidence IS NULL OR length(evidence) >= 6 AND length(evidence) <= 1000)`.
- `api_audit_findings_pkey`: `PRIMARY KEY (id)`.
- `api_audit_findings_priority_check`: `CHECK (priority = ANY (ARRAY['LOW'::text, 'MEDIUM'::text, 'HIGH'::text, 'CRITICAL'::text]))`.
- `api_audit_findings_status_check`: `CHECK (status = ANY (ARRAY['OPEN'::text, 'IN_PROGRESS'::text, 'PENDING_VERIFICATION'::text, 'CLOSED'::text]))`.
- `api_audit_findings_version_check`: `CHECK (version > 0)`.
- `shared_audit_findings_assignee_id`: `FOREIGN KEY (assignee_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_audit_findings_assignee_tenant_id`: `FOREIGN KEY (assignee_tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_audit_findings_created_by`: `FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_audit_findings_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_audit_findings_pkey`: `CREATE UNIQUE INDEX api_audit_findings_pkey ON red_house.audit_findings USING btree (id)`.
- `api_audit_findings_scope`: `CREATE INDEX api_audit_findings_scope ON red_house.audit_findings USING btree (region_id, assignee_id, status, created_at)`.
- `audit_findings_scope`: `CREATE INDEX audit_findings_scope ON red_house.audit_findings USING btree (region_id, assignee_id, status, created_at)`.

Disparadores no internos:


## red_house.balance_proposal

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

Disparadores no internos:


## red_house.blood_allocation

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
- `api_reservations_operation_id_fkey`: `FOREIGN KEY (operation_id) REFERENCES red_house.allocation_operation(id) DEFERRABLE`.
- `api_reservations_operation_id_key`: `UNIQUE (operation_id)`.
- `api_reservations_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.
- `blood_allocation_authorized_by_fkey`: `FOREIGN KEY (authorized_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `blood_allocation_candidate_id_fkey`: `FOREIGN KEY (candidate_id) REFERENCES red_house.blood_candidate(candidate_id) DEFERRABLE`.
- `blood_allocation_candidate_id_key`: `UNIQUE (candidate_id)`.
- `blood_allocation_pkey`: `PRIMARY KEY (allocation_id)`.
- `blood_allocation_review_id_fkey`: `FOREIGN KEY (review_id) REFERENCES red_house.blood_review(review_id) DEFERRABLE`.
- `shared_reservations_destination_id`: `FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_reservations_evaluation_id`: `FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE`.
- `shared_reservations_hold_id`: `FOREIGN KEY (hold_id) REFERENCES red_house.request_hold(id) DEFERRABLE`.
- `shared_reservations_origin_id`: `FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_reservations_recipient_id`: `FOREIGN KEY (recipient_id) REFERENCES red_house.recipient(recipient_id) DEFERRABLE`.
- `shared_reservations_request_id`: `FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE`.
- `shared_reservations_route_id`: `FOREIGN KEY (route_id) REFERENCES red_house.regional_route(route_id) DEFERRABLE`.

Índices:

- `allocation_request_idx`: `CREATE INDEX allocation_request_idx ON red_house.blood_allocation USING btree (request_id)`.
- `allocation_resource_exclusive`: `CREATE UNIQUE INDEX allocation_resource_exclusive ON red_house.blood_allocation USING btree (resource_id) WHERE (current_status <> 'CANCELLED'::text)`.
- `api_reservations_hold_id_key`: `CREATE UNIQUE INDEX api_reservations_hold_id_key ON red_house.blood_allocation USING btree (hold_id)`.
- `api_reservations_operation_id_key`: `CREATE UNIQUE INDEX api_reservations_operation_id_key ON red_house.blood_allocation USING btree (operation_id)`.
- `api_resource_reserved`: `CREATE UNIQUE INDEX api_resource_reserved ON red_house.blood_allocation USING btree (resource_id) WHERE (current_status <> 'CANCELLED'::text)`.
- `blood_allocation_candidate_id_key`: `CREATE UNIQUE INDEX blood_allocation_candidate_id_key ON red_house.blood_allocation USING btree (candidate_id)`.
- `blood_allocation_pkey`: `CREATE UNIQUE INDEX blood_allocation_pkey ON red_house.blood_allocation USING btree (allocation_id)`.

Disparadores no internos:


## red_house.blood_candidate

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

- `blood_candidate_evaluation_id_fkey`: `FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE`.
- `blood_candidate_evaluation_id_rank_no_key`: `UNIQUE (evaluation_id, rank_no)`.
- `blood_candidate_evaluation_id_resource_id_key`: `UNIQUE (evaluation_id, resource_id)`.
- `blood_candidate_pkey`: `PRIMARY KEY (candidate_id)`.
- `blood_candidate_rank_no_check`: `CHECK (rank_no > 0)`.
- `blood_candidate_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.blood_unit(resource_id) DEFERRABLE`.
- `blood_candidate_wait_minutes_check`: `CHECK (wait_minutes >= 0)`.

Índices:

- `blood_candidate_evaluation_id_rank_no_key`: `CREATE UNIQUE INDEX blood_candidate_evaluation_id_rank_no_key ON red_house.blood_candidate USING btree (evaluation_id, rank_no)`.
- `blood_candidate_evaluation_id_resource_id_key`: `CREATE UNIQUE INDEX blood_candidate_evaluation_id_resource_id_key ON red_house.blood_candidate USING btree (evaluation_id, resource_id)`.
- `blood_candidate_pkey`: `CREATE UNIQUE INDEX blood_candidate_pkey ON red_house.blood_candidate USING btree (candidate_id)`.

Disparadores no internos:

- `candidate_append_only`: `CREATE TRIGGER candidate_append_only BEFORE DELETE OR UPDATE ON red_house.blood_candidate FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.blood_classification

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| resource_id | uuid | NO | — |
| recorded_group_code | character varying(3) | NO | — |
| source_reference | character varying(120) | NO | — |
| recorded_at | timestamp with time zone | NO | now() |

Restricciones:

- `blood_classification_pkey`: `PRIMARY KEY (resource_id)`.
- `blood_classification_recorded_group_code_check`: `CHECK (recorded_group_code::text = ANY (ARRAY['O-'::character varying::text, 'O+'::character varying::text, 'A-'::character varying::text, 'A+'::character varying::text, 'B-'::character varying::text, 'B+'::character varying::text, 'AB-'::character varying::text, 'AB+'::character varying::text]))`.
- `blood_classification_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.blood_unit(resource_id) DEFERRABLE`.

Índices:

- `blood_classification_pkey`: `CREATE UNIQUE INDEX blood_classification_pkey ON red_house.blood_classification USING btree (resource_id)`.

Disparadores no internos:


## red_house.blood_component

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

Disparadores no internos:


## red_house.blood_movement

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

- `api_movements_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.
- `blood_movement_destination_location_id_fkey`: `FOREIGN KEY (destination_location_id) REFERENCES red_house.storage_location(location_id) DEFERRABLE`.
- `blood_movement_origin_location_id_fkey`: `FOREIGN KEY (origin_location_id) REFERENCES red_house.storage_location(location_id) DEFERRABLE`.
- `blood_movement_pkey`: `PRIMARY KEY (movement_id)`.
- `shared_movements_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `blood_movement_pkey`: `CREATE UNIQUE INDEX blood_movement_pkey ON red_house.blood_movement USING btree (movement_id)`.

Disparadores no internos:

- `movement_append_only`: `CREATE TRIGGER movement_append_only BEFORE DELETE OR UPDATE ON red_house.blood_movement FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.blood_request

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

- `api_requests_check`: `CHECK (kind <> 'ORGAN'::text OR quantity = 1)`.
- `api_requests_quantity_check`: `CHECK (quantity > 0)`.
- `api_requests_recipient_id_fkey`: `FOREIGN KEY (recipient_id) REFERENCES red_house.recipient(recipient_id) DEFERRABLE`.
- `api_requests_urgency_check`: `CHECK (priority_level >= 1 AND priority_level <= 3)`.
- `blood_request_component_id_fkey`: `FOREIGN KEY (component_id) REFERENCES red_house.blood_component(component_id) DEFERRABLE`.
- `blood_request_pkey`: `PRIMARY KEY (request_id)`.
- `blood_request_request_code_key`: `UNIQUE (request_code)`.
- `blood_request_responsible_id_fkey`: `FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `blood_request_urgency_check`: `CHECK (urgency::text = ANY (ARRAY['URGENT'::character varying::text, 'PRIORITY'::character varying::text, 'ROUTINE'::character varying::text]))`.
- `shared_requests_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_active_organ_request`: `CREATE UNIQUE INDEX api_active_organ_request ON red_house.blood_request USING btree (recipient_id) WHERE ((kind = 'ORGAN'::text) AND (current_status = ANY (ARRAY['OPEN'::text, 'IN_PROGRESS'::text])))`.
- `blood_request_pkey`: `CREATE UNIQUE INDEX blood_request_pkey ON red_house.blood_request USING btree (request_id)`.
- `blood_request_request_code_key`: `CREATE UNIQUE INDEX blood_request_request_code_key ON red_house.blood_request USING btree (request_code)`.
- `request_queue_idx`: `CREATE INDEX request_queue_idx ON red_house.blood_request USING btree (current_status, urgency, requested_at)`.
- `request_recipient_idx`: `CREATE INDEX request_recipient_idx ON red_house.blood_request USING btree (recipient_id)`.

Disparadores no internos:


## red_house.blood_review

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
| operation_scope | text | NO | 'LEGACY'::text |

Restricciones:

- `api_reviews_evaluation_id_fkey`: `FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE`.
- `api_reviews_evaluation_id_resource_id_key`: `UNIQUE (evaluation_id, resource_id)`.
- `blood_review_candidate_id_fkey`: `FOREIGN KEY (candidate_id) REFERENCES red_house.blood_candidate(candidate_id) DEFERRABLE`.
- `blood_review_operation_scope_check`: `CHECK (operation_scope = ANY (ARRAY['LEGACY'::text, 'ACADEMIC'::text, 'CLINICAL'::text]))`.
- `blood_review_pkey`: `PRIMARY KEY (review_id)`.
- `shared_reviews_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_reviews_resource_id`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.
- `shared_reviews_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_reviews_evaluation_id_resource_id_key`: `CREATE UNIQUE INDEX api_reviews_evaluation_id_resource_id_key ON red_house.blood_review USING btree (evaluation_id, resource_id)`.
- `blood_review_pkey`: `CREATE UNIQUE INDEX blood_review_pkey ON red_house.blood_review USING btree (review_id)`.

Disparadores no internos:

- `blood_review_history`: `CREATE TRIGGER blood_review_history BEFORE DELETE OR UPDATE ON red_house.blood_review FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.blood_status_transition

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| previous_status | character varying(16) | NO | — |
| new_status | character varying(16) | NO | — |
| is_illustrative | boolean | NO | true |

Restricciones:

- `blood_status_transition_check`: `CHECK (previous_status::text <> new_status::text)`.
- `blood_status_transition_is_illustrative_check`: `CHECK (is_illustrative)`.
- `blood_status_transition_new_status_check`: `CHECK (new_status::text = ANY (ARRAY['AVAILABLE'::character varying::text, 'QUARANTINED'::character varying::text, 'WITHDRAWN'::character varying::text]))`.
- `blood_status_transition_pkey`: `PRIMARY KEY (previous_status, new_status)`.
- `blood_status_transition_previous_status_check`: `CHECK (previous_status::text = ANY (ARRAY['AVAILABLE'::character varying::text, 'QUARANTINED'::character varying::text]))`.

Índices:

- `blood_status_transition_pkey`: `CREATE UNIQUE INDEX blood_status_transition_pkey ON red_house.blood_status_transition USING btree (previous_status, new_status)`.

Disparadores no internos:


## red_house.blood_unit

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

- `blood_unit_check`: `CHECK (expires_at > collected_at)`.
- `blood_unit_component_id_fkey`: `FOREIGN KEY (component_id) REFERENCES red_house.blood_component(component_id) DEFERRABLE`.
- `blood_unit_current_status_check`: `CHECK (current_status::text = ANY (ARRAY['AVAILABLE'::character varying::text, 'QUARANTINED'::character varying::text, 'WITHDRAWN'::character varying::text, 'RESERVED'::character varying::text, 'IN_TRANSIT'::character varying::text, 'DELIVERED'::character varying::text]))`.
- `blood_unit_location_id_fkey`: `FOREIGN KEY (location_id) REFERENCES red_house.storage_location(location_id) DEFERRABLE`.
- `blood_unit_pkey`: `PRIMARY KEY (resource_id)`.
- `blood_unit_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE`.

Índices:

- `blood_unit_component_idx`: `CREATE INDEX blood_unit_component_idx ON red_house.blood_unit USING btree (component_id)`.
- `blood_unit_expiry_idx`: `CREATE INDEX blood_unit_expiry_idx ON red_house.blood_unit USING btree (expires_at) WHERE ((current_status)::text = 'AVAILABLE'::text)`.
- `blood_unit_location_idx`: `CREATE INDEX blood_unit_location_idx ON red_house.blood_unit USING btree (location_id)`.
- `blood_unit_pkey`: `CREATE UNIQUE INDEX blood_unit_pkey ON red_house.blood_unit USING btree (resource_id)`.

Disparadores no internos:


## red_house.cache_revision

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| name | text | NO | — |
| revision | bigint | NO | 0 |

Restricciones:

- `cache_revision_pkey`: `PRIMARY KEY (name)`.

Índices:

- `cache_revision_pkey`: `CREATE UNIQUE INDEX cache_revision_pkey ON red_house.cache_revision USING btree (name)`.

Disparadores no internos:


## red_house.campaign

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

- `api_campaigns_capacity_check`: `CHECK (capacity > 0)`.
- `api_campaigns_check`: `CHECK (ends_at > starts_at)`.
- `campaign_pkey`: `PRIMARY KEY (campaign_id)`.
- `shared_campaigns_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `campaign_pkey`: `CREATE UNIQUE INDEX campaign_pkey ON red_house.campaign USING btree (campaign_id)`.

Disparadores no internos:


## red_house.campaign_publications

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| published | boolean | NO | false |
| venue | text | NO | — |
| information | text | NO | — |
| version | integer | NO | 1 |

Restricciones:

- `campaign_publications_id_fkey`: `FOREIGN KEY (id) REFERENCES red_house.campaign(campaign_id)`.
- `campaign_publications_pkey`: `PRIMARY KEY (id)`.
- `campaign_publications_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `campaign_publications_pkey`: `CREATE UNIQUE INDEX campaign_publications_pkey ON red_house.campaign_publications USING btree (id)`.

Disparadores no internos:


## red_house.campaign_slots

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| campaign_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| site_id | uuid | NO | — |
| starts_at | timestamp with time zone | NO | — |
| ends_at | timestamp with time zone | NO | — |
| capacity | integer | NO | — |
| active | boolean | NO | true |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `campaign_slots_campaign_id_fkey`: `FOREIGN KEY (campaign_id) REFERENCES red_house.campaign(campaign_id)`.
- `campaign_slots_capacity_check`: `CHECK (capacity > 0)`.
- `campaign_slots_check`: `CHECK (ends_at > starts_at)`.
- `campaign_slots_pkey`: `PRIMARY KEY (id)`.
- `campaign_slots_site_id_fkey`: `FOREIGN KEY (site_id) REFERENCES red_house.catalogue_entry(id)`.
- `campaign_slots_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `campaign_slots_pkey`: `CREATE UNIQUE INDEX campaign_slots_pkey ON red_house.campaign_slots USING btree (id)`.

Disparadores no internos:


## red_house.candidate_evaluation

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

- `candidate_evaluation_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `candidate_evaluation_pkey`: `PRIMARY KEY (evaluation_id)`.
- `shared_evaluations_request_id`: `FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE`.
- `shared_evaluations_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `candidate_evaluation_pkey`: `CREATE UNIQUE INDEX candidate_evaluation_pkey ON red_house.candidate_evaluation USING btree (evaluation_id)`.

Disparadores no internos:

- `evaluation_append_only`: `CREATE TRIGGER evaluation_append_only BEFORE DELETE OR UPDATE ON red_house.candidate_evaluation FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.capability

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| capability_code | character varying(40) | NO | — |
| capability_name | character varying(100) | NO | — |

Restricciones:

- `capability_pkey`: `PRIMARY KEY (capability_code)`.

Índices:

- `capability_pkey`: `CREATE UNIQUE INDEX capability_pkey ON red_house.capability USING btree (capability_code)`.

Disparadores no internos:

- `catalogue_cache`: `CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.capability FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.catalogue_entry

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

- `api_catalogue_kind_check`: `CHECK (kind = ANY (ARRAY['sites'::text, 'contacts'::text, 'schedules'::text, 'capacities'::text, 'locations'::text, 'responsibles'::text, 'services'::text]))`.
- `api_catalogue_parent_id_fkey`: `FOREIGN KEY (parent_id) REFERENCES red_house.catalogue_entry(id) DEFERRABLE`.
- `api_catalogue_pkey`: `PRIMARY KEY (id)`.
- `api_catalogue_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `api_catalogue_tenant_id_kind_name_key`: `UNIQUE (tenant_id, kind, name)`.

Índices:

- `api_catalogue_pkey`: `CREATE UNIQUE INDEX api_catalogue_pkey ON red_house.catalogue_entry USING btree (id)`.
- `api_catalogue_tenant`: `CREATE INDEX api_catalogue_tenant ON red_house.catalogue_entry USING btree (tenant_id, kind, name, id)`.
- `api_catalogue_tenant_id_kind_name_key`: `CREATE UNIQUE INDEX api_catalogue_tenant_id_kind_name_key ON red_house.catalogue_entry USING btree (tenant_id, kind, name)`.

Disparadores no internos:

- `api_catalogue_cache`: `CREATE TRIGGER api_catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.catalogue_entry FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.cold_equipment

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| label | text | NO | — |
| location | text | NO | — |
| calibration_reference | text | YES | — |
| active | boolean | NO | true |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `cold_equipment_pkey`: `PRIMARY KEY (id)`.
- `cold_equipment_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `cold_equipment_pkey`: `CREATE UNIQUE INDEX cold_equipment_pkey ON red_house.cold_equipment USING btree (id)`.

Disparadores no internos:


## red_house.cold_profiles

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| kind | text | NO | — |
| component | text | NO | — |
| minimum_c | double precision | NO | — |
| maximum_c | double precision | NO | — |
| max_gap_seconds | integer | NO | — |
| source | text | NO | — |
| synthetic | boolean | NO | — |
| version | integer | NO | — |
| author_id | uuid | NO | — |
| effective_at | timestamp with time zone | NO | — |
| supersedes | uuid | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `cold_profiles_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `cold_profiles_check`: `CHECK (maximum_c > minimum_c)`.
- `cold_profiles_kind_check`: `CHECK (kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text]))`.
- `cold_profiles_max_gap_seconds_check`: `CHECK (max_gap_seconds > 0)`.
- `cold_profiles_pkey`: `PRIMARY KEY (id)`.
- `cold_profiles_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.cold_profiles(id)`.
- `cold_profiles_supersedes_key`: `UNIQUE (supersedes)`.
- `cold_profiles_synthetic_check`: `CHECK (synthetic)`.
- `cold_profiles_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `cold_profiles_pkey`: `CREATE UNIQUE INDEX cold_profiles_pkey ON red_house.cold_profiles USING btree (id)`.
- `cold_profiles_supersedes_key`: `CREATE UNIQUE INDEX cold_profiles_supersedes_key ON red_house.cold_profiles USING btree (supersedes)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.cold_profiles FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.cold_readings

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| resource_id | uuid | NO | — |
| equipment_id | uuid | NO | — |
| profile_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| temperature_c | double precision | NO | — |
| captured_at | timestamp with time zone | NO | — |
| received_at | timestamp with time zone | NO | now() |
| source | text | NO | — |
| calibration_reference | text | YES | — |
| excursion | boolean | NO | — |
| gap | boolean | NO | — |
| author_id | uuid | NO | — |

Restricciones:

- `cold_readings_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `cold_readings_equipment_id_fkey`: `FOREIGN KEY (equipment_id) REFERENCES red_house.cold_equipment(id)`.
- `cold_readings_pkey`: `PRIMARY KEY (id)`.
- `cold_readings_profile_id_fkey`: `FOREIGN KEY (profile_id) REFERENCES red_house.cold_profiles(id)`.
- `cold_readings_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id)`.
- `cold_readings_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `cold_history`: `CREATE INDEX cold_history ON red_house.cold_readings USING btree (resource_id, captured_at DESC)`.
- `cold_readings_pkey`: `CREATE UNIQUE INDEX cold_readings_pkey ON red_house.cold_readings USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.cold_readings FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.cold_reviews

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| resource_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| author_id | uuid | NO | — |
| reason | text | NO | — |
| decision | text | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `cold_reviews_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `cold_reviews_pkey`: `PRIMARY KEY (id)`.
- `cold_reviews_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id)`.
- `cold_reviews_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `cold_reviews_pkey`: `CREATE UNIQUE INDEX cold_reviews_pkey ON red_house.cold_reviews USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.cold_reviews FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.consent_versions

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| donor_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| author_id | uuid | NO | — |
| version | integer | NO | — |
| policy_version | text | NO | — |
| reference | text | NO | — |
| effective_at | timestamp with time zone | NO | — |
| granted | boolean | NO | — |
| supersedes | uuid | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `consent_versions_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `consent_versions_donor_id_fkey`: `FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id)`.
- `consent_versions_donor_id_version_key`: `UNIQUE (donor_id, version)`.
- `consent_versions_pkey`: `PRIMARY KEY (id)`.
- `consent_versions_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.consent_versions(id)`.
- `consent_versions_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `consent_versions_donor_id_version_key`: `CREATE UNIQUE INDEX consent_versions_donor_id_version_key ON red_house.consent_versions USING btree (donor_id, version)`.
- `consent_versions_pkey`: `CREATE UNIQUE INDEX consent_versions_pkey ON red_house.consent_versions USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.consent_versions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.contact

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| contact_id | uuid | NO | gen_random_uuid() |
| contact_name | character varying(120) | NO | — |
| contact_function | character varying(80) | NO | — |

Restricciones:

- `contact_pkey`: `PRIMARY KEY (contact_id)`.

Índices:

- `contact_pkey`: `CREATE UNIQUE INDEX contact_pkey ON red_house.contact USING btree (contact_id)`.

Disparadores no internos:

- `catalogue_cache`: `CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.contact FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.contact_method

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| contact_id | uuid | NO | — |
| method_kind | character varying(10) | NO | — |
| method_value | character varying(180) | NO | — |

Restricciones:

- `contact_method_contact_id_fkey`: `FOREIGN KEY (contact_id) REFERENCES red_house.contact(contact_id) DEFERRABLE`.
- `contact_method_method_kind_check`: `CHECK (method_kind::text = ANY (ARRAY['EMAIL'::character varying::text, 'PHONE'::character varying::text]))`.
- `contact_method_pkey`: `PRIMARY KEY (contact_id, method_kind)`.

Índices:

- `contact_method_pkey`: `CREATE UNIQUE INDEX contact_method_pkey ON red_house.contact_method USING btree (contact_id, method_kind)`.

Disparadores no internos:

- `catalogue_cache`: `CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.contact_method FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.custody_chain

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

Disparadores no internos:


## red_house.custody_event

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

- `api_custody_events_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.custody_chain(id) DEFERRABLE`.
- `api_custody_events_shipment_id_sequence_key`: `UNIQUE (shipment_id, sequence)`.
- `custody_event_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `custody_event_pkey`: `PRIMARY KEY (event_id)`.

Índices:

- `api_custody_events_shipment_id_sequence_key`: `CREATE UNIQUE INDEX api_custody_events_shipment_id_sequence_key ON red_house.custody_event USING btree (shipment_id, sequence)`.
- `custody_event_pkey`: `CREATE UNIQUE INDEX custody_event_pkey ON red_house.custody_event USING btree (event_id)`.

Disparadores no internos:

- `custody_append_only`: `CREATE TRIGGER custody_append_only BEFORE DELETE OR UPDATE ON red_house.custody_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.decision_runs

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| author_id | uuid | NO | — |
| algorithm_version | text | NO | — |
| source | text | NO | — |
| snapshot | jsonb | NO | — |
| result | jsonb | NO | — |
| fingerprint | text | NO | — |
| elapsed_ms | double precision | NO | — |
| synthetic | boolean | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `decision_runs_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `decision_runs_pkey`: `PRIMARY KEY (id)`.
- `decision_runs_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `decision_runs_pkey`: `CREATE UNIQUE INDEX decision_runs_pkey ON red_house.decision_runs USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.decision_runs FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.devices

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| user_id | uuid | NO | — |
| source | text | NO | — |
| label | text | NO | — |
| token_hash | text | NO | — |
| expires_at | timestamp with time zone | NO | — |
| active | boolean | NO | true |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `devices_pkey`: `PRIMARY KEY (id)`.
- `devices_source_check`: `CHECK (source = ANY (ARRAY['SIMULATOR'::text, 'GPS_BRIDGE'::text, 'ANDROID'::text, 'IOS'::text]))`.
- `devices_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.
- `devices_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES red_house.user_account(account_id)`.

Índices:

- `devices_pkey`: `CREATE UNIQUE INDEX devices_pkey ON red_house.devices USING btree (id)`.

Disparadores no internos:


## red_house.document_metadata

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| category | text | NO | — |
| subject_kind | text | NO | — |
| subject_id | uuid | NO | — |
| version | integer | NO | — |
| supersedes | uuid | YES | — |
| privacy | text | NO | 'PRIVATE'::text |
| retention_until | timestamp with time zone | YES | — |
| legal_hold | boolean | NO | true |
| policy_reference | text | NO | — |
| created_at | timestamp with time zone | NO | now() |
| policy_version | integer | NO | 1 |

Restricciones:

- `document_metadata_id_fkey`: `FOREIGN KEY (id) REFERENCES red_house.stored_file(file_id)`.
- `document_metadata_pkey`: `PRIMARY KEY (id)`.
- `document_metadata_privacy_check`: `CHECK (privacy = 'PRIVATE'::text)`.
- `document_metadata_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.document_metadata(id)`.
- `document_metadata_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `document_metadata_pkey`: `CREATE UNIQUE INDEX document_metadata_pkey ON red_house.document_metadata USING btree (id)`.

Disparadores no internos:


## red_house.donation

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

- `api_donations_donor_id_fkey`: `FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id) DEFERRABLE`.
- `api_donations_kind_check`: `CHECK (kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text]))`.
- `donation_created_by_fkey`: `FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `donation_donation_code_key`: `UNIQUE (donation_code)`.
- `donation_pkey`: `PRIMARY KEY (donation_id)`.
- `donation_review_id_fkey`: `FOREIGN KEY (review_id) REFERENCES red_house.donor_review(review_id) DEFERRABLE`.
- `shared_donations_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `donation_donation_code_key`: `CREATE UNIQUE INDEX donation_donation_code_key ON red_house.donation USING btree (donation_code)`.
- `donation_pkey`: `CREATE UNIQUE INDEX donation_pkey ON red_house.donation USING btree (donation_id)`.

Disparadores no internos:


## red_house.donation_event

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| event_id | uuid | NO | — |
| donation_id | uuid | NO | — |
| status | text | NO | — |
| actor_id | uuid | NO | — |
| occurred_at | timestamp with time zone | NO | now() |
| observation | text | NO | — |

Restricciones:

- `api_donation_steps_donation_id_fkey`: `FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id) DEFERRABLE`.
- `donation_event_pkey`: `PRIMARY KEY (event_id)`.
- `shared_donation_steps_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `donation_event_pkey`: `CREATE UNIQUE INDEX donation_event_pkey ON red_house.donation_event USING btree (event_id)`.

Disparadores no internos:

- `donation_event_append_only`: `CREATE TRIGGER donation_event_append_only BEFORE DELETE OR UPDATE ON red_house.donation_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.donation_unit

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| resource_id | uuid | NO | — |
| donation_id | uuid | NO | — |
| released_by | uuid | NO | — |
| release_reference | character varying(240) | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `donation_unit_donation_id_fkey`: `FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id) DEFERRABLE`.
- `donation_unit_pkey`: `PRIMARY KEY (resource_id)`.
- `donation_unit_released_by_fkey`: `FOREIGN KEY (released_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `donation_unit_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.blood_unit(resource_id) DEFERRABLE`.

Índices:

- `donation_unit_pkey`: `CREATE UNIQUE INDEX donation_unit_pkey ON red_house.donation_unit USING btree (resource_id)`.

Disparadores no internos:

- `donation_unit_append_only`: `CREATE TRIGGER donation_unit_append_only BEFORE DELETE OR UPDATE ON red_house.donation_unit FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.donor

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
- `api_donors_donation_kind_check`: `CHECK (donation_kind = ANY (ARRAY['VOLUNTARY'::text, 'REPLACEMENT'::text]))`.
- `api_donors_tenant_id_folio_key`: `UNIQUE (institution_id, record_code)`.
- `donor_created_by_fkey`: `FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `donor_pkey`: `PRIMARY KEY (donor_id)`.
- `shared_donors_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_donors_user_id`: `FOREIGN KEY (account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `api_donor_account`: `CREATE UNIQUE INDEX api_donor_account ON red_house.donor USING btree (account_id) WHERE (account_id IS NOT NULL)`.
- `api_donors_tenant_id_folio_key`: `CREATE UNIQUE INDEX api_donors_tenant_id_folio_key ON red_house.donor USING btree (institution_id, record_code)`.
- `donor_institution_idx`: `CREATE INDEX donor_institution_idx ON red_house.donor USING btree (institution_id)`.
- `donor_pkey`: `CREATE UNIQUE INDEX donor_pkey ON red_house.donor USING btree (donor_id)`.

Disparadores no internos:


## red_house.donor_review

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| review_id | uuid | NO | — |
| donor_id | uuid | NO | — |
| decision | text | NO | — |
| reason | text | NO | — |
| actor_id | uuid | NO | — |
| occurred_at | timestamp with time zone | NO | now() |

Restricciones:

- `api_donor_reviews_donor_id_fkey`: `FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id) DEFERRABLE`.
- `donor_review_pkey`: `PRIMARY KEY (review_id)`.
- `shared_donor_reviews_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `donor_review_pkey`: `CREATE UNIQUE INDEX donor_review_pkey ON red_house.donor_review USING btree (review_id)`.

Disparadores no internos:

- `donor_review_append_only`: `CREATE TRIGGER donor_review_append_only BEFORE DELETE OR UPDATE ON red_house.donor_review FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.export_jobs

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| user_id | uuid | NO | — |
| report | text | NO | — |
| format | text | NO | — |
| status | text | NO | 'PENDING'::text |
| rows | jsonb | NO | — |
| file_id | uuid | YES | — |
| last_error | text | YES | — |
| attempts | integer | NO | 0 |
| created_at | timestamp with time zone | NO | now() |
| region_id | uuid | YES | — |
| context | jsonb | NO | '{}'::jsonb |
| sealed_authorization | text | YES | — |
| storage_provider | text | NO | 'gcs'::text |

Restricciones:

- `export_jobs_file_id_fkey`: `FOREIGN KEY (file_id) REFERENCES red_house.stored_file(file_id)`.
- `export_jobs_format_check`: `CHECK (format = ANY (ARRAY['CSV'::text, 'PDF'::text, 'XLSX'::text]))`.
- `export_jobs_pkey`: `PRIMARY KEY (id)`.
- `export_jobs_storage_provider_check`: `CHECK (storage_provider = ANY (ARRAY['gcs'::text, 'local'::text]))`.
- `export_jobs_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.
- `export_jobs_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES red_house.user_account(account_id)`.

Índices:

- `export_jobs_pkey`: `CREATE UNIQUE INDEX export_jobs_pkey ON red_house.export_jobs USING btree (id)`.

Disparadores no internos:

- `export_storage_immutable`: `CREATE TRIGGER export_storage_immutable BEFORE UPDATE ON red_house.export_jobs FOR EACH ROW EXECUTE FUNCTION red_house.export_storage_immutable()`.

## red_house.external_authorizations

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| request_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| authority | text | NO | — |
| reference | text | NO | — |
| valid_from | timestamp with time zone | NO | — |
| valid_until | timestamp with time zone | NO | — |
| effective_at | timestamp with time zone | NO | — |
| author_id | uuid | NO | — |
| version | integer | NO | — |
| supersedes | uuid | YES | — |
| decision | text | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `external_authorizations_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `external_authorizations_check`: `CHECK (valid_until > valid_from)`.
- `external_authorizations_decision_check`: `CHECK (decision = ANY (ARRAY['RECORDED'::text, 'WITHDRAWN'::text]))`.
- `external_authorizations_pkey`: `PRIMARY KEY (id)`.
- `external_authorizations_request_id_fkey`: `FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id)`.
- `external_authorizations_request_id_version_key`: `UNIQUE (request_id, version)`.
- `external_authorizations_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.external_authorizations(id)`.
- `external_authorizations_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `external_authorizations_pkey`: `CREATE UNIQUE INDEX external_authorizations_pkey ON red_house.external_authorizations USING btree (id)`.
- `external_authorizations_request_id_version_key`: `CREATE UNIQUE INDEX external_authorizations_request_id_version_key ON red_house.external_authorizations USING btree (request_id, version)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.external_authorizations FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.external_mappings

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| system | text | NO | — |
| external_id | text | NO | — |
| resource_id | uuid | NO | — |
| author_id | uuid | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `external_mappings_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `external_mappings_pkey`: `PRIMARY KEY (id)`.
- `external_mappings_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id)`.
- `external_mappings_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.
- `external_mappings_tenant_id_system_external_id_key`: `UNIQUE (tenant_id, system, external_id)`.

Índices:

- `external_mappings_pkey`: `CREATE UNIQUE INDEX external_mappings_pkey ON red_house.external_mappings USING btree (id)`.
- `external_mappings_tenant_id_system_external_id_key`: `CREATE UNIQUE INDEX external_mappings_tenant_id_system_external_id_key ON red_house.external_mappings USING btree (tenant_id, system, external_id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.external_mappings FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.file_scans

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| file_id | uuid | NO | — |
| generation | text | NO | — |
| sha256 | text | NO | — |
| status | text | NO | — |
| engine | text | NO | — |
| created_at | timestamp with time zone | NO | now() |
| engine_version | text | YES | — |
| signature_version | text | YES | — |
| signature_at | timestamp with time zone | YES | — |
| signature_max_age_seconds | integer | YES | — |

Restricciones:

- `file_scans_file_id_fkey`: `FOREIGN KEY (file_id) REFERENCES red_house.stored_file(file_id)`.
- `file_scans_pkey`: `PRIMARY KEY (id)`.
- `file_scans_status_check`: `CHECK (status = ANY (ARRAY['CLEAN'::text, 'INFECTED'::text, 'ERROR'::text]))`.

Índices:

- `file_scan_latest`: `CREATE INDEX file_scan_latest ON red_house.file_scans USING btree (file_id, created_at DESC)`.
- `file_scans_pkey`: `CREATE UNIQUE INDEX file_scans_pkey ON red_house.file_scans USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.file_scans FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.identity_deliveries

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| recipient | text | NO | — |
| payload_ciphertext | text | NO | — |
| status | text | NO | 'PENDING'::text |
| attempts | integer | NO | 0 |
| next_attempt | timestamp with time zone | NO | now() |
| delivered_at | timestamp with time zone | YES | — |
| last_error | text | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `identity_deliveries_pkey`: `PRIMARY KEY (id)`.

Índices:

- `identity_deliveries_pkey`: `CREATE UNIQUE INDEX identity_deliveries_pkey ON red_house.identity_deliveries USING btree (id)`.

Disparadores no internos:


## red_house.institution

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

- `api_institutions_created_by_fkey`: `FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `institution_institution_code_key`: `UNIQUE (institution_code)`.
- `institution_institution_type_check`: `CHECK (institution_type::text = ANY (ARRAY['BLOOD_BANK'::character varying::text, 'HOSPITAL'::character varying::text, 'COORDINATION'::character varying::text, 'TRANSPLANT_CENTER'::character varying::text]))`.
- `institution_participation_status_check`: `CHECK (participation_status::text = ANY (ARRAY['ACTIVE'::character varying::text, 'INACTIVE'::character varying::text]))`.
- `institution_pkey`: `PRIMARY KEY (institution_id)`.

Índices:

- `institution_institution_code_key`: `CREATE UNIQUE INDEX institution_institution_code_key ON red_house.institution USING btree (institution_code)`.
- `institution_pkey`: `CREATE UNIQUE INDEX institution_pkey ON red_house.institution USING btree (institution_id)`.

Disparadores no internos:

- `catalogue_cache`: `CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.institution FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.institution_capability

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| institution_id | uuid | NO | — |
| capability_code | character varying(40) | NO | — |

Restricciones:

- `institution_capability_capability_code_fkey`: `FOREIGN KEY (capability_code) REFERENCES red_house.capability(capability_code) DEFERRABLE`.
- `institution_capability_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `institution_capability_pkey`: `PRIMARY KEY (institution_id, capability_code)`.

Índices:

- `institution_capability_pkey`: `CREATE UNIQUE INDEX institution_capability_pkey ON red_house.institution_capability USING btree (institution_id, capability_code)`.

Disparadores no internos:

- `catalogue_cache`: `CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.institution_capability FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.institution_contact

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| institution_id | uuid | NO | — |
| contact_id | uuid | NO | — |

Restricciones:

- `institution_contact_contact_id_fkey`: `FOREIGN KEY (contact_id) REFERENCES red_house.contact(contact_id) DEFERRABLE`.
- `institution_contact_contact_id_key`: `UNIQUE (contact_id)`.
- `institution_contact_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `institution_contact_pkey`: `PRIMARY KEY (institution_id, contact_id)`.

Índices:

- `institution_contact_contact_id_key`: `CREATE UNIQUE INDEX institution_contact_contact_id_key ON red_house.institution_contact USING btree (contact_id)`.
- `institution_contact_pkey`: `CREATE UNIQUE INDEX institution_contact_pkey ON red_house.institution_contact USING btree (institution_id, contact_id)`.

Disparadores no internos:

- `catalogue_cache`: `CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.institution_contact FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.institution_presentations

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| version | integer | NO | 1 |
| published | boolean | NO | false |
| description | text | NO | ''::text |
| latitude | double precision | YES | — |
| longitude | double precision | YES | — |
| coordinate_source | text | YES | — |
| coordinate_recorded_at | timestamp with time zone | YES | — |
| synthetic | boolean | NO | true |

Restricciones:

- `institution_presentations_check`: `CHECK ((latitude IS NULL) = (longitude IS NULL))`.
- `institution_presentations_id_fkey`: `FOREIGN KEY (id) REFERENCES red_house.institution(institution_id)`.
- `institution_presentations_latitude_check`: `CHECK (latitude >= '-90'::integer::double precision AND latitude <= 90::double precision)`.
- `institution_presentations_longitude_check`: `CHECK (longitude >= '-180'::integer::double precision AND longitude <= 180::double precision)`.
- `institution_presentations_pkey`: `PRIMARY KEY (id)`.

Índices:

- `institution_presentations_pkey`: `CREATE UNIQUE INDEX institution_presentations_pkey ON red_house.institution_presentations USING btree (id)`.

Disparadores no internos:


## red_house.lab_actions

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| result_id | uuid | NO | — |
| author_id | uuid | NO | — |
| decision | text | NO | — |
| reason | text | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `lab_actions_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `lab_actions_pkey`: `PRIMARY KEY (id)`.
- `lab_actions_result_id_fkey`: `FOREIGN KEY (result_id) REFERENCES red_house.lab_results(id)`.

Índices:

- `lab_actions_pkey`: `CREATE UNIQUE INDEX lab_actions_pkey ON red_house.lab_actions USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.lab_actions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.lab_profiles

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| name | text | NO | — |
| kind | text | NO | — |
| component | text | NO | — |
| version | integer | NO | — |
| required_tests | jsonb | NO | — |
| source | text | NO | — |
| synthetic | boolean | NO | — |
| author_id | uuid | NO | — |
| effective_at | timestamp with time zone | NO | — |
| supersedes | uuid | YES | — |
| created_at | timestamp with time zone | NO | now() |
| purpose | text | NO | 'Completitud académica, sin aplicación clínica'::text |
| rule_status | text | NO | 'DRAFT'::text |
| required_loci | jsonb | NO | '[]'::jsonb |
| clinical_enabled | boolean | NO | false |
| valid_until | timestamp with time zone | YES | — |
| policy | jsonb | NO | '{"version": "COMPLETENESS-2.0", "contradictions": "REVIEW", "max_age_seconds": null, "require_document": false}'::jsonb |
| evidence_rules | jsonb | NO | '[]'::jsonb |
| reference_snapshot | jsonb | NO | '[]'::jsonb |

Restricciones:

- `lab_profiles_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `lab_profiles_clinical_enabled_check`: `CHECK (NOT clinical_enabled)`.
- `lab_profiles_kind_check`: `CHECK (kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text]))`.
- `lab_profiles_pkey`: `PRIMARY KEY (id)`.
- `lab_profiles_required_tests_check`: `CHECK (jsonb_typeof(required_tests) = 'array'::text)`.
- `lab_profiles_rule_status_check`: `CHECK (rule_status = ANY (ARRAY['DRAFT'::text, 'IN_REVIEW'::text, 'RETIRED'::text]))`.
- `lab_profiles_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.lab_profiles(id)`.
- `lab_profiles_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.
- `profile_interval`: `CHECK (valid_until IS NULL OR valid_until > effective_at)`.

Índices:

- `lab_profiles_pkey`: `CREATE UNIQUE INDEX lab_profiles_pkey ON red_house.lab_profiles USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.lab_profiles FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.lab_results

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| sample_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| test_code | text | NO | — |
| value | text | YES | — |
| unit | text | YES | — |
| method | text | NO | — |
| laboratory | text | NO | — |
| reference | text | NO | — |
| measured_at | timestamp with time zone | NO | — |
| author_id | uuid | NO | — |
| version | integer | NO | — |
| supersedes | uuid | YES | — |
| status | text | NO | 'CAPTURED'::text |
| created_at | timestamp with time zone | NO | now() |
| result_state | text | NO | 'REPORTED'::text |
| hla | jsonb | YES | — |
| issued_at | timestamp with time zone | YES | — |
| document_id | uuid | YES | — |
| crossmatch | jsonb | YES | — |
| document_snapshot | jsonb | YES | — |
| catalogue_check | jsonb | YES | — |

Restricciones:

- `lab_results_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `lab_results_document_id_fkey`: `FOREIGN KEY (document_id) REFERENCES red_house.stored_file(file_id)`.
- `lab_results_pkey`: `PRIMARY KEY (id)`.
- `lab_results_result_state_check`: `CHECK (result_state = ANY (ARRAY['NOT_PERFORMED'::text, 'PENDING'::text, 'INDETERMINATE'::text, 'REPORTED'::text, 'CORRECTED'::text]))`.
- `lab_results_sample_id_fkey`: `FOREIGN KEY (sample_id) REFERENCES red_house.lab_samples(id)`.
- `lab_results_sample_id_test_code_version_key`: `UNIQUE (sample_id, test_code, version)`.
- `lab_results_status_check`: `CHECK (status = ANY (ARRAY['CAPTURED'::text, 'AUTHORIZED'::text, 'REJECTED'::text]))`.
- `lab_results_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.lab_results(id)`.
- `lab_results_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `lab_results_pkey`: `CREATE UNIQUE INDEX lab_results_pkey ON red_house.lab_results USING btree (id)`.
- `lab_results_sample_id_test_code_version_key`: `CREATE UNIQUE INDEX lab_results_sample_id_test_code_version_key ON red_house.lab_results USING btree (sample_id, test_code, version)`.

Disparadores no internos:

- `lab_result_immutable`: `CREATE TRIGGER lab_result_immutable BEFORE UPDATE ON red_house.lab_results FOR EACH ROW EXECUTE FUNCTION red_house.protect_lab_result()`.
- `lab_result_no_delete`: `CREATE TRIGGER lab_result_no_delete BEFORE DELETE ON red_house.lab_results FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.lab_samples

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| resource_id | uuid | YES | — |
| recipient_id | uuid | YES | — |
| donation_id | uuid | YES | — |
| profile_id | uuid | NO | — |
| identifier | text | NO | — |
| collected_at | timestamp with time zone | NO | — |
| received_at | timestamp with time zone | YES | — |
| status | text | NO | 'REQUESTED'::text |
| version | integer | NO | 1 |
| author_id | uuid | NO | — |
| created_at | timestamp with time zone | NO | now() |
| request_id | uuid | YES | — |

Restricciones:

- `lab_samples_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `lab_samples_check`: `CHECK (num_nonnulls(resource_id, recipient_id, donation_id) = 1)`.
- `lab_samples_donation_id_fkey`: `FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id)`.
- `lab_samples_pkey`: `PRIMARY KEY (id)`.
- `lab_samples_profile_id_fkey`: `FOREIGN KEY (profile_id) REFERENCES red_house.lab_profiles(id)`.
- `lab_samples_recipient_id_fkey`: `FOREIGN KEY (recipient_id) REFERENCES red_house.recipient(recipient_id)`.
- `lab_samples_request_id_fkey`: `FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id)`.
- `lab_samples_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id)`.
- `lab_samples_status_check`: `CHECK (status = ANY (ARRAY['REQUESTED'::text, 'RECEIVED'::text, 'REJECTED'::text]))`.
- `lab_samples_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.
- `lab_samples_tenant_id_identifier_key`: `UNIQUE (tenant_id, identifier)`.

Índices:

- `lab_samples_pkey`: `CREATE UNIQUE INDEX lab_samples_pkey ON red_house.lab_samples USING btree (id)`.
- `lab_samples_tenant_id_identifier_key`: `CREATE UNIQUE INDEX lab_samples_tenant_id_identifier_key ON red_house.lab_samples USING btree (tenant_id, identifier)`.

Disparadores no internos:


## red_house.login_attempt

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

- `login_address_time_idx`: `CREATE INDEX login_address_time_idx ON red_house.login_attempt USING btree (address_hash, occurred_at DESC)`.
- `login_attempt_pkey`: `CREATE UNIQUE INDEX login_attempt_pkey ON red_house.login_attempt USING btree (attempt_id)`.
- `login_identity_time_idx`: `CREATE INDEX login_identity_time_idx ON red_house.login_attempt USING btree (identity_hash, occurred_at DESC)`.

Disparadores no internos:


## red_house.notification

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
| severity | text | NO | 'INFO'::text |
| delivery_checked_at | timestamp with time zone | YES | — |

Restricciones:

- `api_alerts_event_id_tenant_id_target_role_key`: `UNIQUE (event_id, institution_id, target_role)`.
- `notification_pkey`: `PRIMARY KEY (notification_id)`.
- `shared_alerts_acknowledged_by`: `FOREIGN KEY (acknowledged_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_alerts_target_user_id`: `FOREIGN KEY (target_account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_alerts_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_alerts_event_id_tenant_id_target_role_key`: `CREATE UNIQUE INDEX api_alerts_event_id_tenant_id_target_role_key ON red_house.notification USING btree (event_id, institution_id, target_role)`.
- `notification_pkey`: `CREATE UNIQUE INDEX notification_pkey ON red_house.notification USING btree (notification_id)`.

Disparadores no internos:


## red_house.organ_allocation

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

- `organ_allocation_authorized_by_fkey`: `FOREIGN KEY (authorized_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `organ_allocation_candidate_id_fkey`: `FOREIGN KEY (candidate_id) REFERENCES red_house.organ_candidate(candidate_id) DEFERRABLE`.
- `organ_allocation_check`: `CHECK (eta IS NULL OR eta > departure_at)`.
- `organ_allocation_current_status_check`: `CHECK (current_status::text = ANY (ARRAY['RESERVED'::character varying::text, 'SCHEDULED'::character varying::text, 'PREPARED'::character varying::text, 'COLLECTED'::character varying::text, 'IN_TRANSIT'::character varying::text, 'DELIVERED'::character varying::text, 'ACCEPTED'::character varying::text, 'CANCELLED'::character varying::text]))`.
- `organ_allocation_offer_id_fkey`: `FOREIGN KEY (offer_id) REFERENCES red_house.organ_offer(offer_id) DEFERRABLE`.
- `organ_allocation_pkey`: `PRIMARY KEY (allocation_id)`.
- `organ_allocation_recipient_id_fkey`: `FOREIGN KEY (recipient_id) REFERENCES red_house.organ_recipient(recipient_id) DEFERRABLE`.
- `organ_allocation_review_id_fkey`: `FOREIGN KEY (review_id) REFERENCES red_house.organ_review(review_id) DEFERRABLE`.
- `organ_allocation_transport_id_fkey`: `FOREIGN KEY (transport_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `organ_allocation_pkey`: `CREATE UNIQUE INDEX organ_allocation_pkey ON red_house.organ_allocation USING btree (allocation_id)`.
- `organ_exclusive_offer`: `CREATE UNIQUE INDEX organ_exclusive_offer ON red_house.organ_allocation USING btree (offer_id) WHERE ((current_status)::text <> 'CANCELLED'::text)`.
- `organ_exclusive_recipient`: `CREATE UNIQUE INDEX organ_exclusive_recipient ON red_house.organ_allocation USING btree (recipient_id) WHERE ((current_status)::text <> 'CANCELLED'::text)`.

Disparadores no internos:


## red_house.organ_candidate

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

- `organ_candidate_evaluated_by_fkey`: `FOREIGN KEY (evaluated_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `organ_candidate_evaluation_id_fkey`: `FOREIGN KEY (evaluation_id) REFERENCES red_house.organ_evaluation(evaluation_id) DEFERRABLE`.
- `organ_candidate_evaluation_id_recipient_id_key`: `UNIQUE (evaluation_id, recipient_id)`.
- `organ_candidate_offer_id_fkey`: `FOREIGN KEY (offer_id) REFERENCES red_house.organ_offer(offer_id) DEFERRABLE`.
- `organ_candidate_pkey`: `PRIMARY KEY (candidate_id)`.
- `organ_candidate_rank_no_check`: `CHECK (rank_no > 0)`.
- `organ_candidate_recipient_id_fkey`: `FOREIGN KEY (recipient_id) REFERENCES red_house.organ_recipient(recipient_id) DEFERRABLE`.

Índices:

- `organ_candidate_evaluation_id_recipient_id_key`: `CREATE UNIQUE INDEX organ_candidate_evaluation_id_recipient_id_key ON red_house.organ_candidate USING btree (evaluation_id, recipient_id)`.
- `organ_candidate_pkey`: `CREATE UNIQUE INDEX organ_candidate_pkey ON red_house.organ_candidate USING btree (candidate_id)`.
- `organ_candidates_offer`: `CREATE INDEX organ_candidates_offer ON red_house.organ_candidate USING btree (offer_id, evaluated_at)`.

Disparadores no internos:

- `organ_candidate_history`: `CREATE TRIGGER organ_candidate_history BEFORE DELETE OR UPDATE ON red_house.organ_candidate FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.organ_custody_event

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

- `organ_custody_event_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `organ_custody_event_allocation_id_fkey`: `FOREIGN KEY (allocation_id) REFERENCES red_house.organ_allocation(allocation_id) DEFERRABLE`.
- `organ_custody_event_pkey`: `PRIMARY KEY (event_id)`.

Índices:

- `organ_custody_allocation`: `CREATE INDEX organ_custody_allocation ON red_house.organ_custody_event USING btree (allocation_id, occurred_at)`.
- `organ_custody_event_pkey`: `CREATE UNIQUE INDEX organ_custody_event_pkey ON red_house.organ_custody_event USING btree (event_id)`.

Disparadores no internos:

- `organ_custody_history`: `CREATE TRIGGER organ_custody_history BEFORE DELETE OR UPDATE ON red_house.organ_custody_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.organ_donor

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

- `organ_donor_abo_check`: `CHECK (abo::text = ANY (ARRAY['O'::character varying::text, 'A'::character varying::text, 'B'::character varying::text, 'AB'::character varying::text]))`.
- `organ_donor_donation_kind_check`: `CHECK (donation_kind::text = ANY (ARRAY['LIVING'::character varying::text, 'DECEASED'::character varying::text]))`.
- `organ_donor_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `organ_donor_pkey`: `PRIMARY KEY (donor_id)`.
- `organ_donor_record_code_key`: `UNIQUE (record_code)`.
- `organ_donor_reviewed_by_fkey`: `FOREIGN KEY (reviewed_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `organ_donor_pkey`: `CREATE UNIQUE INDEX organ_donor_pkey ON red_house.organ_donor USING btree (donor_id)`.
- `organ_donor_record_code_key`: `CREATE UNIQUE INDEX organ_donor_record_code_key ON red_house.organ_donor USING btree (record_code)`.

Disparadores no internos:

- `organ_donor_history`: `CREATE TRIGGER organ_donor_history BEFORE DELETE OR UPDATE ON red_house.organ_donor FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.organ_evaluation

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| evaluation_id | uuid | NO | gen_random_uuid() |
| offer_id | uuid | NO | — |
| evaluated_by | uuid | NO | — |
| algorithm_version | character varying(40) | NO | — |
| evaluated_at | timestamp with time zone | NO | now() |

Restricciones:

- `organ_evaluation_evaluated_by_fkey`: `FOREIGN KEY (evaluated_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `organ_evaluation_offer_id_fkey`: `FOREIGN KEY (offer_id) REFERENCES red_house.organ_offer(offer_id) DEFERRABLE`.
- `organ_evaluation_pkey`: `PRIMARY KEY (evaluation_id)`.

Índices:

- `organ_evaluation_pkey`: `CREATE UNIQUE INDEX organ_evaluation_pkey ON red_house.organ_evaluation USING btree (evaluation_id)`.

Disparadores no internos:

- `organ_evaluation_history`: `CREATE TRIGGER organ_evaluation_history BEFORE DELETE OR UPDATE ON red_house.organ_evaluation FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.organ_offer

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

- `organ_offer_check`: `CHECK (preservation_until > recovered_at)`.
- `organ_offer_current_status_check`: `CHECK (current_status::text = ANY (ARRAY['AVAILABLE'::character varying::text, 'RESERVED'::character varying::text, 'IN_TRANSIT'::character varying::text, 'RECEIVED'::character varying::text, 'WITHDRAWN'::character varying::text]))`.
- `organ_offer_donor_id_fkey`: `FOREIGN KEY (donor_id) REFERENCES red_house.organ_donor(donor_id) DEFERRABLE`.
- `organ_offer_organ_type_check`: `CHECK (organ_type::text = ANY (ARRAY['KIDNEY'::character varying::text, 'LIVER'::character varying::text, 'HEART'::character varying::text]))`.
- `organ_offer_pkey`: `PRIMARY KEY (offer_id)`.
- `organ_offer_record_code_key`: `UNIQUE (record_code)`.
- `organ_offer_released_by_fkey`: `FOREIGN KEY (released_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `organ_offer_pkey`: `CREATE UNIQUE INDEX organ_offer_pkey ON red_house.organ_offer USING btree (offer_id)`.
- `organ_offer_record_code_key`: `CREATE UNIQUE INDEX organ_offer_record_code_key ON red_house.organ_offer USING btree (record_code)`.

Disparadores no internos:


## red_house.organ_recipient

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

- `organ_recipient_abo_check`: `CHECK (abo::text = ANY (ARRAY['O'::character varying::text, 'A'::character varying::text, 'B'::character varying::text, 'AB'::character varying::text]))`.
- `organ_recipient_current_status_check`: `CHECK (current_status::text = ANY (ARRAY['ACTIVE'::character varying::text, 'INACTIVE'::character varying::text, 'RESERVED'::character varying::text, 'CLOSED'::character varying::text]))`.
- `organ_recipient_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `organ_recipient_organ_type_check`: `CHECK (organ_type::text = ANY (ARRAY['KIDNEY'::character varying::text, 'LIVER'::character varying::text, 'HEART'::character varying::text]))`.
- `organ_recipient_pkey`: `PRIMARY KEY (recipient_id)`.
- `organ_recipient_record_code_key`: `UNIQUE (record_code)`.
- `organ_recipient_responsible_id_fkey`: `FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `organ_recipient_urgency_check`: `CHECK (urgency::text = ANY (ARRAY['URGENT'::character varying::text, 'PRIORITY'::character varying::text, 'ROUTINE'::character varying::text]))`.

Índices:

- `organ_recipient_pkey`: `CREATE UNIQUE INDEX organ_recipient_pkey ON red_house.organ_recipient USING btree (recipient_id)`.
- `organ_recipient_record_code_key`: `CREATE UNIQUE INDEX organ_recipient_record_code_key ON red_house.organ_recipient USING btree (record_code)`.

Disparadores no internos:


## red_house.organ_review

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

- `organ_review_candidate_id_fkey`: `FOREIGN KEY (candidate_id) REFERENCES red_house.organ_candidate(candidate_id) DEFERRABLE`.
- `organ_review_decision_check`: `CHECK (decision::text = ANY (ARRAY['FAVORABLE'::character varying::text, 'REJECTED'::character varying::text]))`.
- `organ_review_pkey`: `PRIMARY KEY (review_id)`.
- `organ_review_reviewed_by_fkey`: `FOREIGN KEY (reviewed_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `organ_review_pkey`: `CREATE UNIQUE INDEX organ_review_pkey ON red_house.organ_review USING btree (review_id)`.

Disparadores no internos:

- `organ_review_history`: `CREATE TRIGGER organ_review_history BEFORE DELETE OR UPDATE ON red_house.organ_review FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.parameter_version

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

- `parameter_version_approved_by_fkey`: `FOREIGN KEY (approved_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `parameter_version_is_illustrative_check`: `CHECK (is_illustrative)`.
- `parameter_version_measurement_unit_check`: `CHECK (measurement_unit::text = 'HOURS'::text)`.
- `parameter_version_parameter_code_check`: `CHECK (parameter_code::text = 'EXPIRY_WARNING_HOURS'::text)`.
- `parameter_version_pkey`: `PRIMARY KEY (parameter_version_id)`.
- `parameter_version_region_name_parameter_code_version_no_key`: `UNIQUE (region_name, parameter_code, version_no)`.
- `parameter_version_scalar_value_check`: `CHECK (scalar_value >= 1 AND scalar_value <= 720)`.

Índices:

- `parameter_version_pkey`: `CREATE UNIQUE INDEX parameter_version_pkey ON red_house.parameter_version USING btree (parameter_version_id)`.
- `parameter_version_region_name_parameter_code_version_no_key`: `CREATE UNIQUE INDEX parameter_version_region_name_parameter_code_version_no_key ON red_house.parameter_version USING btree (region_name, parameter_code, version_no)`.

Disparadores no internos:

- `parameter_append_only`: `CREATE TRIGGER parameter_append_only BEFORE DELETE OR UPDATE ON red_house.parameter_version FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.party

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| party_id | uuid | NO | gen_random_uuid() |
| party_name | character varying(120) | NO | — |

Restricciones:

- `party_pkey`: `PRIMARY KEY (party_id)`.

Índices:

- `party_pkey`: `CREATE UNIQUE INDEX party_pkey ON red_house.party USING btree (party_id)`.

Disparadores no internos:


## red_house.portal_policies

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| version | integer | NO | 1 |
| timezone | text | NO | — |
| tracking_interval_seconds | integer | NO | — |
| tracking_stale_seconds | integer | NO | — |
| reference | text | NO | — |

Restricciones:

- `portal_policies_check`: `CHECK (tracking_stale_seconds >= tracking_interval_seconds)`.
- `portal_policies_id_fkey`: `FOREIGN KEY (id) REFERENCES red_house.institution(institution_id)`.
- `portal_policies_pkey`: `PRIMARY KEY (id)`.
- `portal_policies_tracking_interval_seconds_check`: `CHECK (tracking_interval_seconds >= 1 AND tracking_interval_seconds <= 300)`.
- `portal_policies_tracking_stale_seconds_check`: `CHECK (tracking_stale_seconds >= 5 AND tracking_stale_seconds <= 3600)`.

Índices:

- `portal_policies_pkey`: `CREATE UNIQUE INDEX portal_policies_pkey ON red_house.portal_policies USING btree (id)`.

Disparadores no internos:


## red_house.ranking_run

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

Disparadores no internos:


## red_house.recipient

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

- `api_recipients_check`: `CHECK (kind = 'BLOOD'::text AND organ_type IS NULL OR kind = 'ORGAN'::text AND (organ_type = ANY (ARRAY['KIDNEY'::text, 'LIVER'::text, 'HEART'::text])))`.
- `api_recipients_kind_check`: `CHECK (kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text]))`.
- `api_recipients_tenant_id_folio_key`: `UNIQUE (institution_id, record_code)`.
- `recipient_pkey`: `PRIMARY KEY (recipient_id)`.
- `recipient_responsible_id_fkey`: `FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `recipient_urgency_check`: `CHECK (legacy_urgency::text = ANY (ARRAY['URGENT'::character varying::text, 'PRIORITY'::character varying::text, 'ROUTINE'::character varying::text]))`.
- `shared_recipients_tenant_id`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_recipients_tenant_id_folio_key`: `CREATE UNIQUE INDEX api_recipients_tenant_id_folio_key ON red_house.recipient USING btree (institution_id, record_code)`.
- `recipient_institution_idx`: `CREATE INDEX recipient_institution_idx ON red_house.recipient USING btree (institution_id)`.
- `recipient_pkey`: `CREATE UNIQUE INDEX recipient_pkey ON red_house.recipient USING btree (recipient_id)`.

Disparadores no internos:


## red_house.recovery_tokens

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| user_id | uuid | NO | — |
| token_hash | text | NO | — |
| expires_at | timestamp with time zone | NO | — |
| used_at | timestamp with time zone | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `recovery_tokens_pkey`: `PRIMARY KEY (id)`.
- `recovery_tokens_token_hash_key`: `UNIQUE (token_hash)`.
- `recovery_tokens_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES red_house.user_account(account_id)`.

Índices:

- `recovery_tokens_pkey`: `CREATE UNIQUE INDEX recovery_tokens_pkey ON red_house.recovery_tokens USING btree (id)`.
- `recovery_tokens_token_hash_key`: `CREATE UNIQUE INDEX recovery_tokens_token_hash_key ON red_house.recovery_tokens USING btree (token_hash)`.

Disparadores no internos:


## red_house.regional_graphs

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| author_id | uuid | NO | — |
| name | text | NO | — |
| version | integer | NO | — |
| supersedes | uuid | YES | — |
| source | text | NO | — |
| observed_at | timestamp with time zone | NO | — |
| valid_until | timestamp with time zone | NO | — |
| synthetic | boolean | NO | — |
| region | text | NO | — |
| quality | text | NO | — |
| nodes | jsonb | NO | — |
| edges | jsonb | NO | — |
| created_at | timestamp with time zone | NO | now() |
| provenance | jsonb | YES | — |

Restricciones:

- `regional_graphs_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `regional_graphs_check`: `CHECK (valid_until > observed_at)`.
- `regional_graphs_pkey`: `PRIMARY KEY (id)`.
- `regional_graphs_region_check`: `CHECK (region = 'Nuevo León'::text)`.
- `regional_graphs_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.regional_graphs(id)`.
- `regional_graphs_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `regional_graphs_pkey`: `CREATE UNIQUE INDEX regional_graphs_pkey ON red_house.regional_graphs USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.regional_graphs FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.regional_route

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

- `api_routes_distance_km_check`: `CHECK (distance_km >= 0::double precision)`.
- `api_routes_origin_id_destination_id_key`: `UNIQUE (origin_id, destination_id)`.
- `api_routes_travel_minutes_check`: `CHECK (travel_minutes >= 0)`.
- `regional_route_pkey`: `PRIMARY KEY (route_id)`.
- `regional_route_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shared_routes_destination_id`: `FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_routes_origin_id`: `FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_routes_origin_id_destination_id_key`: `CREATE UNIQUE INDEX api_routes_origin_id_destination_id_key ON red_house.regional_route USING btree (origin_id, destination_id)`.
- `regional_route_pkey`: `CREATE UNIQUE INDEX regional_route_pkey ON red_house.regional_route USING btree (route_id)`.

Disparadores no internos:


## red_house.request_event

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| event_id | uuid | NO | gen_random_uuid() |
| request_id | uuid | NO | — |
| action | character varying(30) | NO | — |
| actor_id | uuid | NO | — |
| occurred_at | timestamp with time zone | NO | now() |
| observation | character varying(240) | NO | — |

Restricciones:

- `request_event_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `request_event_pkey`: `PRIMARY KEY (event_id)`.
- `request_event_request_id_fkey`: `FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE`.

Índices:

- `request_event_pkey`: `CREATE UNIQUE INDEX request_event_pkey ON red_house.request_event USING btree (event_id)`.

Disparadores no internos:

- `request_event_append_only`: `CREATE TRIGGER request_event_append_only BEFORE DELETE OR UPDATE ON red_house.request_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.request_hold

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

Disparadores no internos:


## red_house.resource

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

- `api_resources_kind_check`: `CHECK (resource_kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text]))`.
- `api_resources_tenant_id_folio_key`: `UNIQUE (tenant_id, folio)`.
- `resource_pkey`: `PRIMARY KEY (resource_id)`.
- `resource_traceability_code_key`: `UNIQUE (traceability_code)`.
- `shared_resources_current_institution_id`: `FOREIGN KEY (current_institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_resources_donation_id`: `FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id) DEFERRABLE`.
- `shared_resources_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.

Índices:

- `api_availability_page`: `CREATE INDEX api_availability_page ON red_house.resource USING btree (region_id, expires_at, resource_id) WHERE (status = 'AVAILABLE'::text)`.
- `api_available_resources`: `CREATE INDEX api_available_resources ON red_house.resource USING btree (region_id, resource_kind, component, expires_at) WHERE (status = 'AVAILABLE'::text)`.
- `api_resources_tenant_id_folio_key`: `CREATE UNIQUE INDEX api_resources_tenant_id_folio_key ON red_house.resource USING btree (tenant_id, folio)`.
- `resource_pkey`: `CREATE UNIQUE INDEX resource_pkey ON red_house.resource USING btree (resource_id)`.
- `resource_traceability_code_key`: `CREATE UNIQUE INDEX resource_traceability_code_key ON red_house.resource USING btree (traceability_code)`.

Disparadores no internos:

- `api_inventory_cache`: `CREATE TRIGGER api_inventory_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.resource FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_inventory_cache()`.

## red_house.resource_controls

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| lab_profile_id | uuid | YES | — |
| cold_equipment_id | uuid | YES | — |
| cold_profile_id | uuid | YES | — |
| blocked | boolean | NO | false |
| version | integer | NO | 1 |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `resource_controls_cold_equipment_id_fkey`: `FOREIGN KEY (cold_equipment_id) REFERENCES red_house.cold_equipment(id)`.
- `resource_controls_cold_profile_id_fkey`: `FOREIGN KEY (cold_profile_id) REFERENCES red_house.cold_profiles(id)`.
- `resource_controls_id_fkey`: `FOREIGN KEY (id) REFERENCES red_house.resource(resource_id)`.
- `resource_controls_lab_profile_id_fkey`: `FOREIGN KEY (lab_profile_id) REFERENCES red_house.lab_profiles(id)`.
- `resource_controls_pkey`: `PRIMARY KEY (id)`.

Índices:

- `resource_controls_pkey`: `CREATE UNIQUE INDEX resource_controls_pkey ON red_house.resource_controls USING btree (id)`.

Disparadores no internos:


## red_house.resource_destinations

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| resource_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| destination | text | NO | — |
| reference | text | NO | — |
| occurred_at | timestamp with time zone | NO | — |
| reason | text | NO | — |
| author_id | uuid | NO | — |
| version | integer | NO | — |
| supersedes | uuid | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `resource_destinations_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `resource_destinations_destination_check`: `CHECK (destination = ANY (ARRAY['TRANSFUSED'::text, 'TRANSPLANTED'::text, 'DISCARDED'::text, 'RETURNED'::text, 'RESEARCH'::text]))`.
- `resource_destinations_pkey`: `PRIMARY KEY (id)`.
- `resource_destinations_resource_id_fkey`: `FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id)`.
- `resource_destinations_resource_id_version_key`: `UNIQUE (resource_id, version)`.
- `resource_destinations_supersedes_fkey`: `FOREIGN KEY (supersedes) REFERENCES red_house.resource_destinations(id)`.
- `resource_destinations_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `resource_destinations_pkey`: `CREATE UNIQUE INDEX resource_destinations_pkey ON red_house.resource_destinations USING btree (id)`.
- `resource_destinations_resource_id_version_key`: `CREATE UNIQUE INDEX resource_destinations_resource_id_version_key ON red_house.resource_destinations USING btree (resource_id, version)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.resource_destinations FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.resource_lineage

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| parent_id | uuid | NO | — |
| child_id | uuid | NO | — |
| donation_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| author_id | uuid | NO | — |
| reason | text | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `resource_lineage_author_id_fkey`: `FOREIGN KEY (author_id) REFERENCES red_house.user_account(account_id)`.
- `resource_lineage_check`: `CHECK (parent_id <> child_id)`.
- `resource_lineage_child_id_fkey`: `FOREIGN KEY (child_id) REFERENCES red_house.resource(resource_id)`.
- `resource_lineage_child_id_key`: `UNIQUE (child_id)`.
- `resource_lineage_donation_id_fkey`: `FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id)`.
- `resource_lineage_parent_id_fkey`: `FOREIGN KEY (parent_id) REFERENCES red_house.resource(resource_id)`.
- `resource_lineage_pkey`: `PRIMARY KEY (id)`.
- `resource_lineage_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `resource_lineage_child_id_key`: `CREATE UNIQUE INDEX resource_lineage_child_id_key ON red_house.resource_lineage USING btree (child_id)`.
- `resource_lineage_pkey`: `CREATE UNIQUE INDEX resource_lineage_pkey ON red_house.resource_lineage USING btree (id)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.resource_lineage FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.resource_review

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

Disparadores no internos:


## red_house.role

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| role_code | character varying(30) | NO | — |
| role_name | character varying(80) | NO | — |
| is_enabled | boolean | NO | — |

Restricciones:

- `role_pkey`: `PRIMARY KEY (role_code)`.

Índices:

- `role_pkey`: `CREATE UNIQUE INDEX role_pkey ON red_house.role USING btree (role_code)`.

Disparadores no internos:


## red_house.rule_actions

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| profile_id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| actor_id | uuid | NO | — |
| sequence | integer | NO | — |
| state | text | NO | — |
| reason | text | NO | — |
| competency_reference | text | YES | — |
| evidence | jsonb | YES | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `rule_actions_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id)`.
- `rule_actions_pkey`: `PRIMARY KEY (id)`.
- `rule_actions_profile_id_fkey`: `FOREIGN KEY (profile_id) REFERENCES red_house.lab_profiles(id)`.
- `rule_actions_profile_id_sequence_key`: `UNIQUE (profile_id, sequence)`.
- `rule_actions_state_check`: `CHECK (state = ANY (ARRAY['IN_REVIEW'::text, 'APPROVED'::text, 'RETIRED'::text]))`.
- `rule_actions_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `rule_actions_pkey`: `CREATE UNIQUE INDEX rule_actions_pkey ON red_house.rule_actions USING btree (id)`.
- `rule_actions_profile_id_sequence_key`: `CREATE UNIQUE INDEX rule_actions_profile_id_sequence_key ON red_house.rule_actions USING btree (profile_id, sequence)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.rule_actions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.schema_migration

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| version | integer | NO | — |
| description | text | NO | — |
| installed_at | timestamp with time zone | NO | now() |

Restricciones:

- `schema_migration_pkey`: `PRIMARY KEY (version)`.

Índices:

- `schema_migration_pkey`: `CREATE UNIQUE INDEX schema_migration_pkey ON red_house.schema_migration USING btree (version)`.

Disparadores no internos:


## red_house.security_contacts

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| email | text | NO | — |
| verified | boolean | NO | false |
| verification_hash | text | NO | — |
| expires_at | timestamp with time zone | NO | — |
| version | integer | NO | 1 |

Restricciones:

- `security_contacts_id_fkey`: `FOREIGN KEY (id) REFERENCES red_house.user_account(account_id)`.
- `security_contacts_pkey`: `PRIMARY KEY (id)`.
- `security_contacts_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `security_contacts_pkey`: `CREATE UNIQUE INDEX security_contacts_pkey ON red_house.security_contacts USING btree (id)`.

Disparadores no internos:


## red_house.security_factors

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| secret_ciphertext | text | NO | — |
| last_counter | bigint | NO | '-1'::integer |
| active | boolean | NO | true |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `security_factors_id_fkey`: `FOREIGN KEY (id) REFERENCES red_house.user_account(account_id)`.
- `security_factors_pkey`: `PRIMARY KEY (id)`.
- `security_factors_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.

Índices:

- `security_factors_pkey`: `CREATE UNIQUE INDEX security_factors_pkey ON red_house.security_factors USING btree (id)`.

Disparadores no internos:


## red_house.service_activity_events

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

Disparadores no internos:

- `immutable`: `CREATE TRIGGER immutable BEFORE DELETE OR UPDATE ON red_house.service_activity_events FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.service_decisions

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

Disparadores no internos:

- `immutable`: `CREATE TRIGGER immutable BEFORE DELETE OR UPDATE ON red_house.service_decisions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.service_health_check

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

- `api_checks_latest`: `CREATE INDEX api_checks_latest ON red_house.service_health_check USING btree (service, checked_at DESC)`.
- `health_service_time`: `CREATE INDEX health_service_time ON red_house.service_health_check USING btree (service, checked_at DESC)`.
- `service_health_check_pkey`: `CREATE UNIQUE INDEX service_health_check_pkey ON red_house.service_health_check USING btree (check_id)`.

Disparadores no internos:

- `health_check_history`: `CREATE TRIGGER health_check_history BEFORE DELETE OR UPDATE ON red_house.service_health_check FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.service_idempotency

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

Disparadores no internos:


## red_house.service_inbox

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

Disparadores no internos:


## red_house.service_outbox

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

Disparadores no internos:


## red_house.service_schema_version

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| service | text | NO | — |
| version | integer | NO | — |
| installed_at | timestamp with time zone | NO | now() |

Restricciones:

- `service_schema_version_pkey`: `PRIMARY KEY (service, version)`.

Índices:

- `service_schema_version_pkey`: `CREATE UNIQUE INDEX service_schema_version_pkey ON red_house.service_schema_version USING btree (service, version)`.

Disparadores no internos:


## red_house.service_worker_health

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| service | text | NO | — |
| id | integer | NO | — |
| checked_at | timestamp with time zone | NO | — |
| last_success | timestamp with time zone | YES | — |
| last_error | text | YES | — |

Restricciones:

- `service_worker_health_id_check`: `CHECK (id = 1)`.
- `service_worker_health_pkey`: `PRIMARY KEY (service, id)`.

Índices:

- `service_worker_health_pkey`: `CREATE UNIQUE INDEX service_worker_health_pkey ON red_house.service_worker_health USING btree (service, id)`.

Disparadores no internos:


## red_house.shipment

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

- `api_shipments_check`: `CHECK (eta > departure_at)`.
- `api_shipments_check1`: `CHECK (eta < expires_at)`.
- `api_shipments_reservation_id_key`: `UNIQUE (allocation_id)`.
- `shared_shipments_destination_id`: `FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_shipments_origin_id`: `FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `shared_shipments_reservation_id`: `FOREIGN KEY (allocation_id) REFERENCES red_house.blood_allocation(allocation_id) DEFERRABLE`.
- `shared_shipments_transport_user_id`: `FOREIGN KEY (transport_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `shipment_organ_allocation_id_fkey`: `FOREIGN KEY (organ_allocation_id) REFERENCES red_house.organ_allocation(allocation_id) DEFERRABLE`.
- `shipment_organ_allocation_id_key`: `UNIQUE (organ_allocation_id)`.
- `shipment_pkey`: `PRIMARY KEY (shipment_id)`.

Índices:

- `api_shipments_reservation_id_key`: `CREATE UNIQUE INDEX api_shipments_reservation_id_key ON red_house.shipment USING btree (allocation_id)`.
- `shipment_organ_allocation_id_key`: `CREATE UNIQUE INDEX shipment_organ_allocation_id_key ON red_house.shipment USING btree (organ_allocation_id)`.
- `shipment_pkey`: `CREATE UNIQUE INDEX shipment_pkey ON red_house.shipment USING btree (shipment_id)`.
- `shipment_transport_idx`: `CREATE INDEX shipment_transport_idx ON red_house.shipment USING btree (transport_id)`.

Disparadores no internos:


## red_house.shipment_transition

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
- `api_transitions_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE`.
- `api_transitions_shipment_id_sequence_key`: `UNIQUE (shipment_id, sequence)`.
- `shared_transitions_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.

Índices:

- `api_transitions_pkey`: `CREATE UNIQUE INDEX api_transitions_pkey ON red_house.shipment_transition USING btree (id)`.
- `api_transitions_shipment_id_sequence_key`: `CREATE UNIQUE INDEX api_transitions_shipment_id_sequence_key ON red_house.shipment_transition USING btree (shipment_id, sequence)`.

Disparadores no internos:

- `api_immutable`: `CREATE TRIGGER api_immutable BEFORE DELETE OR UPDATE ON red_house.shipment_transition FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.site

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

- `site_institution_id_fkey`: `FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `site_institution_id_site_code_key`: `UNIQUE (institution_id, site_code)`.
- `site_pkey`: `PRIMARY KEY (site_id)`.
- `site_site_status_check`: `CHECK (site_status::text = ANY (ARRAY['ACTIVE'::character varying::text, 'INACTIVE'::character varying::text]))`.

Índices:

- `site_institution_id_site_code_key`: `CREATE UNIQUE INDEX site_institution_id_site_code_key ON red_house.site USING btree (institution_id, site_code)`.
- `site_institution_idx`: `CREATE INDEX site_institution_idx ON red_house.site USING btree (institution_id)`.
- `site_pkey`: `CREATE UNIQUE INDEX site_pkey ON red_house.site USING btree (site_id)`.

Disparadores no internos:

- `catalogue_cache`: `CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.site FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.site_schedule

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| schedule_id | uuid | NO | gen_random_uuid() |
| site_id | uuid | NO | — |
| weekday | smallint | NO | — |
| opens_at | time without time zone | NO | — |
| closes_at | time without time zone | NO | — |

Restricciones:

- `site_schedule_check`: `CHECK (closes_at > opens_at)`.
- `site_schedule_pkey`: `PRIMARY KEY (schedule_id)`.
- `site_schedule_site_id_fkey`: `FOREIGN KEY (site_id) REFERENCES red_house.site(site_id) DEFERRABLE`.
- `site_schedule_site_id_weekday_opens_at_key`: `UNIQUE (site_id, weekday, opens_at)`.
- `site_schedule_weekday_check`: `CHECK (weekday >= 1 AND weekday <= 7)`.

Índices:

- `site_schedule_pkey`: `CREATE UNIQUE INDEX site_schedule_pkey ON red_house.site_schedule USING btree (schedule_id)`.
- `site_schedule_site_id_weekday_opens_at_key`: `CREATE UNIQUE INDEX site_schedule_site_id_weekday_opens_at_key ON red_house.site_schedule USING btree (site_id, weekday, opens_at)`.

Disparadores no internos:

- `catalogue_cache`: `CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.site_schedule FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.storage_location

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
- `storage_location_site_id_fkey`: `FOREIGN KEY (site_id) REFERENCES red_house.site(site_id) DEFERRABLE`.
- `storage_location_site_id_location_code_key`: `UNIQUE (site_id, location_code)`.

Índices:

- `storage_location_pkey`: `CREATE UNIQUE INDEX storage_location_pkey ON red_house.storage_location USING btree (location_id)`.
- `storage_location_site_id_location_code_key`: `CREATE UNIQUE INDEX storage_location_site_id_location_code_key ON red_house.storage_location USING btree (site_id, location_code)`.
- `storage_site_idx`: `CREATE INDEX storage_site_idx ON red_house.storage_location USING btree (site_id)`.

Disparadores no internos:

- `catalogue_cache`: `CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.storage_location FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache()`.

## red_house.stored_file

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| file_id | uuid | NO | — |
| shipment_id | uuid | YES | — |
| owner_id | uuid | NO | — |
| object_path | text | NO | — |
| mime_type | text | NO | — |
| size_bytes | integer | NO | — |
| sha256 | text | NO | — |
| current_status | text | NO | 'PENDING'::text |
| generation | text | YES | — |
| created_at | timestamp with time zone | NO | now() |
| storage_provider | text | NO | 'gcs'::text |

Restricciones:

- `api_files_object_path_key`: `UNIQUE (object_path)`.
- `api_files_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE`.
- `api_files_size_check`: `CHECK (size_bytes >= 1 AND size_bytes <= 10485760)`.
- `shared_files_owner_id`: `FOREIGN KEY (owner_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `stored_file_pkey`: `PRIMARY KEY (file_id)`.
- `stored_file_storage_provider_check`: `CHECK (storage_provider = ANY (ARRAY['gcs'::text, 'local'::text]))`.

Índices:

- `api_files_object_path_key`: `CREATE UNIQUE INDEX api_files_object_path_key ON red_house.stored_file USING btree (object_path)`.
- `stored_file_pkey`: `CREATE UNIQUE INDEX stored_file_pkey ON red_house.stored_file USING btree (file_id)`.

Disparadores no internos:

- `file_storage_immutable`: `CREATE TRIGGER file_storage_immutable BEFORE UPDATE ON red_house.stored_file FOR EACH ROW EXECUTE FUNCTION red_house.file_storage_immutable()`.

## red_house.sync_commands

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| tenant_id | uuid | NO | — |
| user_id | uuid | NO | — |
| shipment_id | uuid | NO | — |
| device_id | uuid | NO | — |
| cursor | bigint | NO | — |
| expected_version | integer | NO | — |
| body | jsonb | NO | — |
| fingerprint | text | NO | — |
| result | jsonb | NO | — |
| captured_at | timestamp with time zone | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `sync_commands_device_id_fkey`: `FOREIGN KEY (device_id) REFERENCES red_house.devices(id)`.
- `sync_commands_pkey`: `PRIMARY KEY (id)`.
- `sync_commands_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id)`.
- `sync_commands_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id)`.
- `sync_commands_user_id_cursor_key`: `UNIQUE (user_id, cursor)`.
- `sync_commands_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES red_house.user_account(account_id)`.

Índices:

- `sync_commands_pkey`: `CREATE UNIQUE INDEX sync_commands_pkey ON red_house.sync_commands USING btree (id)`.
- `sync_commands_user_id_cursor_key`: `CREATE UNIQUE INDEX sync_commands_user_id_cursor_key ON red_house.sync_commands USING btree (user_id, cursor)`.

Disparadores no internos:

- `history_immutable`: `CREATE TRIGGER history_immutable BEFORE DELETE OR UPDATE ON red_house.sync_commands FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.tracking_assignments

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| shipment_id | uuid | NO | — |
| device_id | uuid | NO | — |
| responsible_id | uuid | NO | — |
| starts_at | timestamp with time zone | NO | — |
| ends_at | timestamp with time zone | NO | — |
| active | boolean | NO | true |
| version | integer | NO | 1 |
| actor_id | uuid | NO | — |
| created_at | timestamp with time zone | NO | now() |

Restricciones:

- `tracking_assignments_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id)`.
- `tracking_assignments_check`: `CHECK (ends_at > starts_at)`.
- `tracking_assignments_device_id_fkey`: `FOREIGN KEY (device_id) REFERENCES red_house.devices(id)`.
- `tracking_assignments_pkey`: `PRIMARY KEY (id)`.
- `tracking_assignments_responsible_id_fkey`: `FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id)`.
- `tracking_assignments_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id)`.

Índices:

- `tracking_assignments_pkey`: `CREATE UNIQUE INDEX tracking_assignments_pkey ON red_house.tracking_assignments USING btree (id)`.
- `tracking_device_active`: `CREATE UNIQUE INDEX tracking_device_active ON red_house.tracking_assignments USING btree (device_id) WHERE active`.

Disparadores no internos:


## red_house.tracking_points

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | uuid | NO | — |
| shipment_id | uuid | NO | — |
| assignment_id | uuid | NO | — |
| device_id | uuid | NO | — |
| cursor | bigint | NO | — |
| sequence | bigint | NO | — |
| captured_at | timestamp with time zone | NO | — |
| received_at | timestamp with time zone | NO | clock_timestamp() |
| fingerprint | text | NO | — |
| position | jsonb | NO | — |

Restricciones:

- `tracking_points_assignment_id_fkey`: `FOREIGN KEY (assignment_id) REFERENCES red_house.tracking_assignments(id)`.
- `tracking_points_assignment_id_sequence_key`: `UNIQUE (assignment_id, sequence)`.
- `tracking_points_cursor_check`: `CHECK (cursor > 0)`.
- `tracking_points_device_id_fkey`: `FOREIGN KEY (device_id) REFERENCES red_house.devices(id)`.
- `tracking_points_pkey`: `PRIMARY KEY (id)`.
- `tracking_points_sequence_check`: `CHECK (sequence >= 0)`.
- `tracking_points_shipment_id_cursor_key`: `UNIQUE (shipment_id, cursor)`.
- `tracking_points_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id)`.

Índices:

- `tracking_capture`: `CREATE INDEX tracking_capture ON red_house.tracking_points USING btree (shipment_id, captured_at DESC, cursor DESC)`.
- `tracking_points_assignment_id_sequence_key`: `CREATE UNIQUE INDEX tracking_points_assignment_id_sequence_key ON red_house.tracking_points USING btree (assignment_id, sequence)`.
- `tracking_points_pkey`: `CREATE UNIQUE INDEX tracking_points_pkey ON red_house.tracking_points USING btree (id)`.
- `tracking_points_shipment_id_cursor_key`: `CREATE UNIQUE INDEX tracking_points_shipment_id_cursor_key ON red_house.tracking_points USING btree (shipment_id, cursor)`.

Disparadores no internos:

- `tracking_history_immutable`: `CREATE TRIGGER tracking_history_immutable BEFORE DELETE OR UPDATE ON red_house.tracking_points FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.transport_telemetry

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

- `api_telemetry_shipment_id_fkey`: `FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE`.
- `shared_telemetry_actor_id`: `FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `transport_telemetry_pkey`: `PRIMARY KEY (telemetry_id)`.

Índices:

- `telemetry_shipment_time`: `CREATE INDEX telemetry_shipment_time ON red_house.transport_telemetry USING btree (shipment_id, captured_at)`.
- `transport_telemetry_pkey`: `CREATE UNIQUE INDEX transport_telemetry_pkey ON red_house.transport_telemetry USING btree (telemetry_id)`.

Disparadores no internos:

- `telemetry_history`: `CREATE TRIGGER telemetry_history BEFORE DELETE OR UPDATE ON red_house.transport_telemetry FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()`.

## red_house.user_account

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

- `api_users_role_check`: `CHECK (role = ANY (ARRAY['ADMIN'::text, 'OPERATOR'::text, 'MEDICAL'::text, 'COORDINATOR'::text, 'TRANSPORT'::text, 'AUDITOR'::text, 'DONOR'::text]))`.
- `api_users_tenant_id_fkey`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `api_users_username_key`: `UNIQUE (username)`.
- `shared_users_tenant_id`: `FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE`.
- `user_account_account_status_check`: `CHECK (account_status::text = ANY (ARRAY['ACTIVE'::character varying::text, 'INACTIVE'::character varying::text]))`.
- `user_account_login_email_check`: `CHECK (login_email::text = lower(login_email::text))`.
- `user_account_login_email_key`: `UNIQUE (login_email)`.
- `user_account_party_id_fkey`: `FOREIGN KEY (party_id) REFERENCES red_house.party(party_id) DEFERRABLE`.
- `user_account_party_id_key`: `UNIQUE (party_id)`.
- `user_account_pkey`: `PRIMARY KEY (account_id)`.

Índices:

- `api_users_username_key`: `CREATE UNIQUE INDEX api_users_username_key ON red_house.user_account USING btree (username)`.
- `user_account_login_email_key`: `CREATE UNIQUE INDEX user_account_login_email_key ON red_house.user_account USING btree (login_email)`.
- `user_account_party_id_key`: `CREATE UNIQUE INDEX user_account_party_id_key ON red_house.user_account USING btree (party_id)`.
- `user_account_pkey`: `CREATE UNIQUE INDEX user_account_pkey ON red_house.user_account USING btree (account_id)`.

Disparadores no internos:


## red_house.web_session

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| session_id | uuid | NO | — |
| account_id | uuid | NO | — |
| expires_at | timestamp with time zone | NO | — |
| revoked_at | timestamp with time zone | YES | — |
| created_at | timestamp with time zone | YES | now() |

Restricciones:

- `api_sessions_user_id_fkey`: `FOREIGN KEY (account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE`.
- `web_session_pkey`: `PRIMARY KEY (session_id)`.

Índices:

- `web_session_account_idx`: `CREATE INDEX web_session_account_idx ON red_house.web_session USING btree (account_id)`.
- `web_session_pkey`: `CREATE UNIQUE INDEX web_session_pkey ON red_house.web_session USING btree (session_id)`.

Disparadores no internos:


## web_runtime.session_revocations

| Columna | Tipo físico | NULL | Predeterminado |
| --- | --- | --- | --- |
| id | text | NO | — |
| payload | bytea | YES | — |
| expires | timestamp with time zone | NO | — |
| confirmed | boolean | NO | false |

Restricciones:

- `session_revocations_id_check`: `CHECK (id ~ '^[0-9a-f]{64}$'::text)`.
- `session_revocations_pkey`: `PRIMARY KEY (id)`.

Índices:

- `session_revocations_expiry`: `CREATE INDEX session_revocations_expiry ON web_runtime.session_revocations USING btree (expires)`.
- `session_revocations_pending`: `CREATE INDEX session_revocations_pending ON web_runtime.session_revocations USING btree (expires) WHERE (NOT confirmed)`.
- `session_revocations_pkey`: `CREATE UNIQUE INDEX session_revocations_pkey ON web_runtime.session_revocations USING btree (id)`.

Disparadores no internos:


