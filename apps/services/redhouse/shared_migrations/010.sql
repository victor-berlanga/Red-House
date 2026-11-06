SET LOCAL search_path=red_house,pg_catalog;
CREATE TABLE alert_policies(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 message_code text NOT NULL, severity text NOT NULL, reminder_seconds integer NOT NULL CHECK(reminder_seconds>0),
 escalate_seconds integer NOT NULL CHECK(escalate_seconds>reminder_seconds), escalation_role text NOT NULL,
 author_id uuid NOT NULL REFERENCES user_account(account_id), source text NOT NULL,
 effective_at timestamptz NOT NULL, supersedes uuid UNIQUE REFERENCES alert_policies(id),
 active boolean NOT NULL DEFAULT true, version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(tenant_id,message_code,version));
CREATE TABLE alert_subscriptions(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id), user_id uuid NOT NULL REFERENCES user_account(account_id),
 role text NOT NULL, channel text NOT NULL CHECK(channel IN ('EMAIL','PUSH')), destination text NOT NULL,
 active boolean NOT NULL DEFAULT true, version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(user_id,channel));
CREATE TABLE alert_deliveries(id uuid PRIMARY KEY, alert_id uuid NOT NULL REFERENCES notification(notification_id),
 subscription_id uuid NOT NULL REFERENCES alert_subscriptions(id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 stage text NOT NULL CHECK(stage IN ('INITIAL','REMINDER','ESCALATED')), status text NOT NULL DEFAULT 'PENDING',
 attempts integer NOT NULL DEFAULT 0, next_attempt timestamptz NOT NULL DEFAULT now(), accepted_at timestamptz,
 last_error text, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(alert_id,subscription_id,stage));
CREATE TABLE alert_actions(id uuid PRIMARY KEY, alert_id uuid NOT NULL REFERENCES notification(notification_id),
 tenant_id uuid NOT NULL REFERENCES institution(institution_id), actor_id uuid REFERENCES user_account(account_id), action text NOT NULL,
 reason text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(alert_id,action));
ALTER TABLE stored_file ALTER COLUMN shipment_id DROP NOT NULL;
CREATE TABLE document_metadata(id uuid PRIMARY KEY REFERENCES stored_file(file_id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 category text NOT NULL, subject_kind text NOT NULL, subject_id uuid NOT NULL, version integer NOT NULL,
 supersedes uuid REFERENCES document_metadata(id), privacy text NOT NULL DEFAULT 'PRIVATE' CHECK(privacy='PRIVATE'),
 retention_until timestamptz, legal_hold boolean NOT NULL DEFAULT true, policy_reference text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE file_scans(id uuid PRIMARY KEY, file_id uuid NOT NULL REFERENCES stored_file(file_id), generation text NOT NULL, sha256 text NOT NULL,
 status text NOT NULL CHECK(status IN ('CLEAN','INFECTED','ERROR')), engine text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX file_scan_latest ON file_scans(file_id,created_at DESC);
CREATE TABLE export_jobs(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id), user_id uuid NOT NULL REFERENCES user_account(account_id),
 report text NOT NULL, format text NOT NULL CHECK(format IN ('CSV','PDF','XLSX')), status text NOT NULL DEFAULT 'PENDING',
 rows jsonb NOT NULL, file_id uuid REFERENCES stored_file(file_id), last_error text, attempts integer NOT NULL DEFAULT 0,
 created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE sync_commands(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id), user_id uuid NOT NULL REFERENCES user_account(account_id),
 shipment_id uuid NOT NULL REFERENCES shipment(shipment_id), device_id uuid NOT NULL REFERENCES devices(id),
 cursor bigint NOT NULL, expected_version integer NOT NULL, body jsonb NOT NULL, fingerprint text NOT NULL,
 result jsonb NOT NULL, captured_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(user_id,cursor));
CREATE TABLE external_mappings(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 system text NOT NULL, external_id text NOT NULL, resource_id uuid NOT NULL REFERENCES resource(resource_id),
 author_id uuid NOT NULL REFERENCES user_account(account_id), created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(tenant_id,system,external_id));
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['alert_policies','alert_actions','file_scans','sync_commands','external_mappings'] LOOP
  EXECUTE format('CREATE TRIGGER history_immutable BEFORE UPDATE OR DELETE ON red_house.%I FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()',t);
 END LOOP;
END $$;
INSERT INTO schema_migration(version,description) VALUES(10,'Entrega de alertas, documentos, exportaciones, sincronización e identificadores externos');
