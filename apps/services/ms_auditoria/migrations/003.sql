CREATE TABLE audit_findings(
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, region_id uuid NOT NULL,
 description text NOT NULL CHECK(length(description) BETWEEN 6 AND 1000),
 priority text NOT NULL CHECK(priority IN ('LOW','MEDIUM','HIGH','CRITICAL')),
 assignee_id uuid NOT NULL, assignee_tenant_id uuid NOT NULL, assignee_name text NOT NULL,
 created_by uuid NOT NULL, resource_id uuid,
 evidence text CHECK(evidence IS NULL OR length(evidence) BETWEEN 6 AND 1000),
 status text NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN','IN_PROGRESS','PENDING_VERIFICATION','CLOSED')),
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX audit_findings_scope ON audit_findings(region_id,assignee_id,status,created_at);
CREATE TABLE audit_finding_links(
 id uuid PRIMARY KEY, finding_id uuid NOT NULL REFERENCES audit_findings(id),
 event_id uuid NOT NULL REFERENCES audit_events(id), UNIQUE(finding_id,event_id));
CREATE TABLE audit_finding_actions(
 id uuid PRIMARY KEY, finding_id uuid NOT NULL REFERENCES audit_findings(id),
 actor_id uuid NOT NULL, actor_name text NOT NULL, actor_role text NOT NULL,
 previous_status text, status text NOT NULL,
 reason text NOT NULL CHECK(length(reason) BETWEEN 6 AND 1000),
 corrective_action text CHECK(corrective_action IS NULL OR length(corrective_action) BETWEEN 6 AND 1000),
 evidence text CHECK(evidence IS NULL OR length(evidence) BETWEEN 6 AND 1000),
 correlation_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX audit_finding_actions_timeline ON audit_finding_actions(finding_id,created_at,id);
CREATE TRIGGER finding_links_immutable BEFORE UPDATE OR DELETE ON audit_finding_links FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER finding_actions_immutable BEFORE UPDATE OR DELETE ON audit_finding_actions FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
-- Disponible también en un paquete de Auditoría con esquema propio.
CREATE FUNCTION event_time(value text) RETURNS timestamptz
LANGUAGE plpgsql IMMUTABLE STRICT SET search_path=pg_catalog AS $$
BEGIN
 IF value !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*(Z|[+-][0-9]{2}:[0-9]{2})$' THEN RETURN NULL; END IF;
 RETURN value::timestamptz;
EXCEPTION WHEN invalid_datetime_format OR datetime_field_overflow THEN RETURN NULL;
END $$;
