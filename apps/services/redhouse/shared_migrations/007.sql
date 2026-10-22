SET LOCAL search_path=red_house,pg_catalog;
CREATE TABLE IF NOT EXISTS audit_findings(
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, region_id uuid NOT NULL,
 description text NOT NULL CHECK(length(description) BETWEEN 6 AND 1000),
 priority text NOT NULL CHECK(priority IN ('LOW','MEDIUM','HIGH','CRITICAL')),
 assignee_id uuid NOT NULL, assignee_tenant_id uuid NOT NULL, assignee_name text NOT NULL,
 created_by uuid NOT NULL, resource_id uuid,
 evidence text CHECK(evidence IS NULL OR length(evidence) BETWEEN 6 AND 1000),
 status text NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN','IN_PROGRESS','PENDING_VERIFICATION','CLOSED')),
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS audit_findings_scope ON audit_findings(region_id,assignee_id,status,created_at);
CREATE TABLE IF NOT EXISTS audit_finding_links(
 id uuid PRIMARY KEY, finding_id uuid NOT NULL REFERENCES audit_findings(id),
 event_id uuid NOT NULL REFERENCES red_house.audit_event(event_id), UNIQUE(finding_id,event_id));
CREATE TABLE IF NOT EXISTS audit_finding_actions(
 id uuid PRIMARY KEY, finding_id uuid NOT NULL REFERENCES audit_findings(id),
 actor_id uuid NOT NULL, actor_name text NOT NULL, actor_role text NOT NULL,
 previous_status text, status text NOT NULL,
 reason text NOT NULL CHECK(length(reason) BETWEEN 6 AND 1000),
 corrective_action text CHECK(corrective_action IS NULL OR length(corrective_action) BETWEEN 6 AND 1000),
 evidence text CHECK(evidence IS NULL OR length(evidence) BETWEEN 6 AND 1000),
 correlation_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS audit_finding_actions_timeline ON audit_finding_actions(finding_id,created_at,id);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='red_house.audit_finding_links'::regclass AND NOT tgisinternal) THEN
    CREATE TRIGGER finding_links_immutable BEFORE UPDATE OR DELETE ON red_house.audit_finding_links FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='red_house.audit_finding_actions'::regclass AND NOT tgisinternal) THEN
    CREATE TRIGGER finding_actions_immutable BEFORE UPDATE OR DELETE ON red_house.audit_finding_actions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();
  END IF;
END $$;
CREATE OR REPLACE VIEW access_auditoria.audit_findings AS SELECT * FROM red_house.audit_findings;
CREATE OR REPLACE VIEW access_auditoria.audit_finding_links AS SELECT * FROM red_house.audit_finding_links;
CREATE OR REPLACE VIEW access_auditoria.audit_finding_actions AS SELECT * FROM red_house.audit_finding_actions;
ALTER VIEW access_auditoria.audit_findings ALTER COLUMN status SET DEFAULT 'OPEN';
ALTER VIEW access_auditoria.audit_findings ALTER COLUMN version SET DEFAULT 1;
ALTER VIEW access_auditoria.audit_findings ALTER COLUMN created_at SET DEFAULT now();
ALTER VIEW access_auditoria.audit_findings ALTER COLUMN updated_at SET DEFAULT now();
ALTER VIEW access_auditoria.audit_finding_actions ALTER COLUMN created_at SET DEFAULT now();
-- Una fecha histórica no reconocida queda desconocida, nunca se sustituye por centralización.
CREATE OR REPLACE FUNCTION access_auditoria.event_time(value text) RETURNS timestamptz
LANGUAGE plpgsql IMMUTABLE STRICT SET search_path=pg_catalog AS $$
BEGIN
 IF value !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*(Z|[+-][0-9]{2}:[0-9]{2})$' THEN RETURN NULL; END IF;
 RETURN value::timestamptz;
EXCEPTION WHEN invalid_datetime_format OR datetime_field_overflow THEN RETURN NULL;
END $$;
REVOKE ALL ON FUNCTION access_auditoria.event_time(text) FROM PUBLIC;
CREATE INDEX IF NOT EXISTS audit_execution_search ON red_house.audit_event(region_id,access_auditoria.event_time(event->>'occurred_at'),event_id);
CREATE INDEX IF NOT EXISTS audit_action_search ON red_house.audit_event(region_id,action,actor_id);
CREATE INDEX IF NOT EXISTS audit_resource_search ON red_house.audit_event(region_id,(event->>'resource_id'));
CREATE INDEX IF NOT EXISTS audit_correlation_search ON red_house.audit_event(region_id,(event->>'correlation_id'));
INSERT INTO red_house.service_schema_version(service,version) VALUES('auditoria',3) ON CONFLICT DO NOTHING;
INSERT INTO red_house.schema_migration(version,description) VALUES(7,'Investigación de auditoría e historial de hallazgos');

DO $$ BEGIN
IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='shared_audit_findings_tenant_id' AND conrelid='red_house.audit_findings'::regclass) THEN ALTER TABLE red_house.audit_findings ADD CONSTRAINT shared_audit_findings_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE INITIALLY IMMEDIATE; END IF;
IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='shared_audit_findings_assignee_tenant_id' AND conrelid='red_house.audit_findings'::regclass) THEN ALTER TABLE red_house.audit_findings ADD CONSTRAINT shared_audit_findings_assignee_tenant_id FOREIGN KEY (assignee_tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE INITIALLY IMMEDIATE; END IF;
IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='shared_audit_findings_assignee_id' AND conrelid='red_house.audit_findings'::regclass) THEN ALTER TABLE red_house.audit_findings ADD CONSTRAINT shared_audit_findings_assignee_id FOREIGN KEY (assignee_id) REFERENCES red_house.user_account(account_id) DEFERRABLE INITIALLY IMMEDIATE; END IF;
IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='shared_audit_findings_created_by' AND conrelid='red_house.audit_findings'::regclass) THEN ALTER TABLE red_house.audit_findings ADD CONSTRAINT shared_audit_findings_created_by FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE INITIALLY IMMEDIATE; END IF;
IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='shared_audit_finding_actions_actor_id' AND conrelid='red_house.audit_finding_actions'::regclass) THEN ALTER TABLE red_house.audit_finding_actions ADD CONSTRAINT shared_audit_finding_actions_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE INITIALLY IMMEDIATE; END IF;
END $$;

DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='rh_auditoria') THEN
  GRANT SELECT,INSERT ON access_auditoria.audit_findings,access_auditoria.audit_finding_links,access_auditoria.audit_finding_actions TO rh_auditoria;
  REVOKE UPDATE,DELETE ON access_auditoria.audit_findings,access_auditoria.audit_finding_links,access_auditoria.audit_finding_actions FROM rh_auditoria;
  GRANT UPDATE ON access_auditoria.audit_findings TO rh_auditoria;
  GRANT EXECUTE ON FUNCTION access_auditoria.event_time(text) TO rh_auditoria;
 END IF;
END $$;
