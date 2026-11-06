SET LOCAL search_path=red_house,pg_catalog;
CREATE OR REPLACE VIEW access_transporte.tracking_devices AS
 SELECT d.id,d.tenant_id,d.user_id,d.source,d.token_hash,d.expires_at,d.active,d.version,
 u.active AS user_active,i.active AS institution_active,u.role AS user_role
 FROM devices d JOIN user_account u ON u.account_id=d.user_id JOIN institution i ON i.institution_id=d.tenant_id;
ALTER TABLE catalogue_entry DROP CONSTRAINT api_catalogue_kind_check;
ALTER TABLE catalogue_entry ADD CONSTRAINT api_catalogue_kind_check CHECK(kind IN ('sites','contacts','schedules','capacities','locations','responsibles','services'));
CREATE TABLE external_authorizations(id uuid PRIMARY KEY, request_id uuid NOT NULL REFERENCES blood_request(request_id),
 tenant_id uuid NOT NULL REFERENCES institution(institution_id), authority text NOT NULL, reference text NOT NULL,
 valid_from timestamptz NOT NULL, valid_until timestamptz NOT NULL, effective_at timestamptz NOT NULL,
 author_id uuid NOT NULL REFERENCES user_account(account_id), version integer NOT NULL, supersedes uuid REFERENCES external_authorizations(id),
 decision text NOT NULL CHECK(decision IN ('RECORDED','WITHDRAWN')), created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(valid_until>valid_from), UNIQUE(request_id,version));
CREATE TRIGGER history_immutable BEFORE UPDATE OR DELETE ON external_authorizations FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();
CREATE TABLE appointment_reminders(id uuid PRIMARY KEY REFERENCES appointment(appointment_id), version integer NOT NULL, sent_at timestamptz NOT NULL DEFAULT now());
ALTER TABLE notification ADD COLUMN severity text NOT NULL DEFAULT 'INFO';
ALTER TABLE notification ADD COLUMN delivery_checked_at timestamptz;
-- Las vistas anteriores conservan columnas/contratos; campos nuevos se consultan con vistas específicas.
CREATE VIEW access_alertas.alert_severity AS SELECT notification_id AS id,severity,delivery_checked_at FROM notification;
INSERT INTO schema_migration(version,description) VALUES(11,'Autorizaciones externas versionadas, recordatorios y seguimiento de entrega');
