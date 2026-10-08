CREATE TABLE audit_events(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,region_id uuid NOT NULL,source text NOT NULL,
 action text NOT NULL,actor_id uuid,event jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX audit_search ON audit_events(region_id,tenant_id,created_at);
CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
