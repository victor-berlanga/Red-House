CREATE TABLE evaluations(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,request_id uuid NOT NULL,request_version integer NOT NULL,
 recipient_version integer NOT NULL,kind text NOT NULL,algorithm_version text NOT NULL,snapshot jsonb NOT NULL,
 candidates jsonb NOT NULL,elapsed_ms double precision NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE reviews(id uuid PRIMARY KEY,evaluation_id uuid NOT NULL REFERENCES evaluations(id),resource_id uuid NOT NULL,
 tenant_id uuid NOT NULL,actor_id uuid NOT NULL,decision text NOT NULL,reason text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(evaluation_id,resource_id));
CREATE TRIGGER reviews_immutable BEFORE UPDATE OR DELETE ON reviews FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
