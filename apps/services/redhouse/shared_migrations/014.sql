-- Additive laboratory metadata; existing values and histories remain unchanged.
ALTER TABLE red_house.lab_profiles ADD COLUMN purpose text NOT NULL DEFAULT 'Completitud académica, sin aplicación clínica';
ALTER TABLE red_house.lab_profiles ADD COLUMN rule_status text NOT NULL DEFAULT 'DRAFT' CHECK (rule_status IN ('DRAFT','IN_REVIEW','RETIRED'));
ALTER TABLE red_house.lab_profiles ADD COLUMN required_loci jsonb NOT NULL DEFAULT '[]';
ALTER TABLE red_house.lab_profiles ADD COLUMN clinical_enabled boolean NOT NULL DEFAULT false CHECK (NOT clinical_enabled);
ALTER TABLE red_house.lab_results ALTER COLUMN value DROP NOT NULL;
ALTER TABLE red_house.lab_results ADD COLUMN result_state text NOT NULL DEFAULT 'REPORTED' CHECK (result_state IN ('NOT_PERFORMED','PENDING','INDETERMINATE','REPORTED','CORRECTED'));
ALTER TABLE red_house.lab_results ADD COLUMN hla jsonb;
ALTER TABLE red_house.lab_results ADD COLUMN issued_at timestamptz;
ALTER TABLE red_house.lab_results ADD COLUMN document_id uuid REFERENCES red_house.stored_file(file_id);
CREATE TABLE red_house.algorithm_runs (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES red_house.institution(institution_id), author_id uuid NOT NULL REFERENCES red_house.user_account(account_id),
 algorithm_version text NOT NULL, source text NOT NULL, snapshot jsonb NOT NULL,
 result jsonb NOT NULL, fingerprint text NOT NULL, elapsed_ms double precision NOT NULL,
 synthetic boolean NOT NULL DEFAULT true CHECK(synthetic), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX algorithm_runs_tenant_time ON red_house.algorithm_runs(tenant_id, created_at DESC, id);
CREATE TRIGGER history_immutable BEFORE UPDATE OR DELETE ON red_house.algorithm_runs FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();
INSERT INTO red_house.schema_migration(version,description) VALUES(14,'HLA declarado y ejecuciones académicas reproducibles');
