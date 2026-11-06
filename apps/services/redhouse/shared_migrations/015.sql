-- Immutable specifications and append-only approvals. No historic decision is rewritten.
ALTER TABLE red_house.lab_profiles DROP CONSTRAINT lab_profiles_synthetic_check;
ALTER TABLE red_house.lab_profiles ADD COLUMN valid_until timestamptz;
ALTER TABLE red_house.lab_profiles ADD COLUMN policy jsonb NOT NULL DEFAULT '{"version":"COMPLETENESS-2.0","max_age_seconds":null,"contradictions":"REVIEW","require_document":false}';
ALTER TABLE red_house.lab_profiles ADD CONSTRAINT profile_interval CHECK(valid_until IS NULL OR valid_until>effective_at);
CREATE TABLE red_house.rule_actions (
 id uuid PRIMARY KEY, profile_id uuid NOT NULL REFERENCES red_house.lab_profiles(id),
 tenant_id uuid NOT NULL REFERENCES red_house.institution(institution_id),
 actor_id uuid NOT NULL REFERENCES red_house.user_account(account_id),
 sequence integer NOT NULL, state text NOT NULL CHECK(state IN ('IN_REVIEW','APPROVED','RETIRED')),
 reason text NOT NULL, competency_reference text, evidence jsonb,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(profile_id,sequence)
);
CREATE TRIGGER history_immutable BEFORE UPDATE OR DELETE ON red_house.rule_actions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();
ALTER TABLE red_house.lab_samples ADD COLUMN request_id uuid REFERENCES red_house.blood_request(request_id);
ALTER TABLE red_house.lab_results ADD COLUMN crossmatch jsonb;
ALTER TABLE red_house.lab_results ADD COLUMN document_snapshot jsonb;
CREATE TABLE red_house.regional_graphs (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES red_house.institution(institution_id),
 author_id uuid NOT NULL REFERENCES red_house.user_account(account_id),
 name text NOT NULL, version integer NOT NULL, supersedes uuid REFERENCES red_house.regional_graphs(id),
 source text NOT NULL, observed_at timestamptz NOT NULL, valid_until timestamptz NOT NULL,
 synthetic boolean NOT NULL, region text NOT NULL CHECK(region='Nuevo León'), quality text NOT NULL,
 nodes jsonb NOT NULL, edges jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), CHECK(valid_until>observed_at)
);
CREATE TRIGGER history_immutable BEFORE UPDATE OR DELETE ON red_house.regional_graphs FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();
CREATE TABLE red_house.decision_runs (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES red_house.institution(institution_id),
 author_id uuid NOT NULL REFERENCES red_house.user_account(account_id), algorithm_version text NOT NULL,
 source text NOT NULL, snapshot jsonb NOT NULL, result jsonb NOT NULL, fingerprint text NOT NULL,
 elapsed_ms double precision NOT NULL, synthetic boolean NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER history_immutable BEFORE UPDATE OR DELETE ON red_house.decision_runs FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();
CREATE TABLE red_house.anomaly_reviews (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES red_house.institution(institution_id), region_id uuid NOT NULL,
 source text NOT NULL, source_run_id uuid NOT NULL, deduplication_key text NOT NULL UNIQUE,
 evidence jsonb NOT NULL, correlation_id text NOT NULL, responsible_id uuid NOT NULL REFERENCES red_house.user_account(account_id),
 state text NOT NULL DEFAULT 'OPEN' CHECK(state IN ('OPEN','CONFIRMED','DISMISSED')),
 version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE red_house.anomaly_actions (
 id uuid PRIMARY KEY, review_id uuid NOT NULL REFERENCES red_house.anomaly_reviews(id), tenant_id uuid NOT NULL REFERENCES red_house.institution(institution_id),
 author_id uuid NOT NULL REFERENCES red_house.user_account(account_id), state text NOT NULL, reason text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER history_immutable BEFORE UPDATE OR DELETE ON red_house.anomaly_actions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();
ALTER TABLE red_house.blood_review ADD COLUMN operation_scope text NOT NULL DEFAULT 'LEGACY' CHECK(operation_scope IN ('LEGACY','ACADEMIC','CLINICAL'));
CREATE OR REPLACE VIEW access_compatibilidad.reviews AS SELECT review_id AS id,evaluation_id,resource_id,tenant_id,actor_id,decision,reason,occurred_at AS created_at,operation_scope FROM red_house.blood_review;
INSERT INTO red_house.schema_migration(version,description) VALUES(15,'Reglas verificables, asociaciones, ejecuciones autoritativas y revisión de anomalías');
