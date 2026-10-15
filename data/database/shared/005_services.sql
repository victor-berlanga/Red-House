-- Ampliación del modelo compartido de main. Se aplica después de 001–004.
-- Las reglas clínicas heredadas conservan sus límites académicos.
ALTER TABLE parameter_version RENAME COLUMN is_demo TO is_illustrative;
ALTER TABLE blood_status_transition RENAME COLUMN is_demo TO is_illustrative;
ALTER TABLE parameter_version RENAME CONSTRAINT parameter_version_is_demo_check TO parameter_version_is_illustrative_check;
ALTER TABLE blood_status_transition RENAME CONSTRAINT blood_status_transition_is_demo_check TO blood_status_transition_is_illustrative_check;
UPDATE capability SET capability_name = 'Inventario sanguíneo ilustrativo'
WHERE capability_code = 'BLOOD_INVENTORY';

-- Se conservan cuentas y perfiles existentes; no se crean contraseñas.
ALTER TABLE user_account ADD COLUMN username varchar(180) UNIQUE;
ALTER TABLE donor ADD COLUMN account_id uuid UNIQUE REFERENCES user_account(account_id);
UPDATE role SET is_enabled = true WHERE role_code = 'DONOR';
CREATE TABLE site_schedule (
    schedule_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id uuid NOT NULL REFERENCES site,
    weekday smallint NOT NULL CHECK (weekday BETWEEN 1 AND 7),
    opens_at time NOT NULL, closes_at time NOT NULL CHECK (closes_at > opens_at),
    UNIQUE (site_id, weekday, opens_at)
);
CREATE TABLE campaign (
    campaign_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id uuid NOT NULL REFERENCES institution,
    title text NOT NULL, starts_at timestamptz NOT NULL,
    ends_at timestamptz NOT NULL CHECK (ends_at > starts_at),
    capacity integer NOT NULL CHECK (capacity > 0),
    current_status text NOT NULL DEFAULT 'OPEN' CHECK (current_status IN ('OPEN','CLOSED','CANCELLED')),
    version_no integer NOT NULL DEFAULT 1
);
CREATE TABLE appointment (
    appointment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id uuid NOT NULL REFERENCES donor,
    campaign_id uuid NOT NULL REFERENCES campaign,
    current_status text NOT NULL DEFAULT 'BOOKED' CHECK (current_status IN ('BOOKED','CANCELLED','ATTENDED')),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX appointment_active ON appointment(donor_id,campaign_id) WHERE current_status='BOOKED';
-- El aforo y las autorizaciones institucionales se validarán en transacción por el servicio.
CREATE TABLE blood_review (
    review_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id uuid NOT NULL REFERENCES blood_candidate,
    actor_id uuid NOT NULL REFERENCES user_account(account_id),
    decision text NOT NULL CHECK (decision IN ('FAVORABLE','REJECTED')),
    reason text NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (review_id,candidate_id)
);
ALTER TABLE blood_allocation ADD COLUMN review_id uuid REFERENCES blood_review;
ALTER TABLE blood_allocation ADD CONSTRAINT allocation_review_candidate_fk
    FOREIGN KEY (review_id,candidate_id) REFERENCES blood_review(review_id,candidate_id);
-- La columna es nullable para conservar asignaciones históricas de main.
-- La futura autorización exigirá dictamen explícito para nuevas asignaciones.
CREATE TABLE algorithm_run (
    run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id uuid NOT NULL REFERENCES institution,
    actor_id uuid REFERENCES user_account(account_id),
    operation text NOT NULL CHECK (operation IN ('RANKING','BALANCING')),
    algorithm_version text NOT NULL,
    blood_evaluation_id uuid REFERENCES candidate_evaluation(evaluation_id),
    organ_evaluation_id uuid REFERENCES organ_evaluation(evaluation_id),
    inputs jsonb NOT NULL, factors jsonb NOT NULL, result jsonb NOT NULL,
    elapsed_ms double precision NOT NULL CHECK (elapsed_ms >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (num_nonnulls(blood_evaluation_id,organ_evaluation_id) <= 1)
);
-- Un mismo registro de traslado puede corresponder a sangre o a órganos.
ALTER TABLE shipment ALTER COLUMN allocation_id DROP NOT NULL;
ALTER TABLE shipment ADD COLUMN organ_allocation_id uuid UNIQUE REFERENCES organ_allocation;
ALTER TABLE shipment ADD CONSTRAINT shipment_one_allocation CHECK (num_nonnulls(allocation_id,organ_allocation_id)=1);
CREATE TABLE transport_telemetry (
    telemetry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id uuid NOT NULL REFERENCES shipment,
    actor_id uuid NOT NULL REFERENCES user_account(account_id),
    latitude double precision NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude double precision NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    captured_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX telemetry_shipment_time ON transport_telemetry(shipment_id,captured_at);
CREATE TABLE stored_file (
    file_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id uuid NOT NULL REFERENCES shipment,
    owner_id uuid NOT NULL REFERENCES user_account(account_id),
    object_path text NOT NULL UNIQUE, mime_type text NOT NULL,
    size_bytes bigint NOT NULL CHECK (size_bytes BETWEEN 1 AND 10485760),
    sha256 varchar(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    current_status text NOT NULL DEFAULT 'PENDING' CHECK (current_status IN ('PENDING','READY','REJECTED')),
    generation text, created_at timestamptz NOT NULL DEFAULT now()
);
-- Los archivos binarios permanecen fuera de PostgreSQL.
ALTER TABLE custody_event ADD COLUMN previous_hash text;
ALTER TABLE custody_event ADD COLUMN event_hash text;
ALTER TABLE organ_custody_event ADD COLUMN previous_hash text;
ALTER TABLE organ_custody_event ADD COLUMN event_hash text;
ALTER TABLE audit_event ADD COLUMN source_service text;
ALTER TABLE audit_event ADD COLUMN metadata jsonb NOT NULL DEFAULT '{}';
CREATE TABLE notification (
    notification_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NOT NULL REFERENCES audit_event,
    institution_id uuid NOT NULL REFERENCES institution,
    target_role varchar(30) NOT NULL REFERENCES role(role_code),
    target_account_id uuid REFERENCES user_account(account_id),
    message_code text NOT NULL, entity_reference text NOT NULL,
    current_status text NOT NULL DEFAULT 'OPEN' CHECK (current_status IN ('OPEN','ACKNOWLEDGED')),
    acknowledged_by uuid REFERENCES user_account(account_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (event_id,institution_id,target_role),
    CHECK ((current_status='OPEN' AND acknowledged_by IS NULL) OR
           (current_status='ACKNOWLEDGED' AND acknowledged_by IS NOT NULL))
);
CREATE TABLE service_health_check (
    check_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    service text NOT NULL, state text NOT NULL, elapsed_ms double precision NOT NULL CHECK(elapsed_ms>=0),
    dependency text, last_error text, deployed_version text,
    checked_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX health_service_time ON service_health_check(service,checked_at DESC);
CREATE TABLE service_worker_health (
    service text PRIMARY KEY, checked_at timestamptz NOT NULL,
    last_success timestamptz, last_error text
);
-- Las claves incluyen el servicio: no colisionan los consumidores ni sus reintentos.
CREATE TABLE event_outbox (
    outbox_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NOT NULL REFERENCES audit_event,
    source_service text NOT NULL, target_service text NOT NULL,
    payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
    delivered_at timestamptz, attempts integer NOT NULL DEFAULT 0 CHECK(attempts>=0),
    next_attempt timestamptz NOT NULL DEFAULT now(), last_error text,
    UNIQUE(event_id,target_service)
);
CREATE INDEX outbox_pending ON event_outbox(next_attempt,created_at) WHERE delivered_at IS NULL;
CREATE TABLE event_inbox (
    service text NOT NULL, event_id uuid NOT NULL REFERENCES audit_event,
    fingerprint text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(service,event_id)
);
CREATE TABLE request_idempotency (
    service text NOT NULL, account_id uuid NOT NULL REFERENCES user_account,
    key text NOT NULL, operation text NOT NULL, fingerprint text NOT NULL,
    result jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(service,account_id,key)
);
CREATE TABLE cache_revision (
    name text PRIMARY KEY, revision bigint NOT NULL DEFAULT 0
);
INSERT INTO cache_revision(name) VALUES ('catalogues');
CREATE FUNCTION bump_read_cache() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    UPDATE red_house.cache_revision SET revision=revision+1 WHERE name='catalogues';
    RETURN NULL;
END; $$;
DO $$
DECLARE relation_name text;
BEGIN
    FOREACH relation_name IN ARRAY ARRAY['institution','site','contact','contact_method',
      'institution_contact','capability','institution_capability','storage_location','site_schedule'] LOOP
        EXECUTE format('CREATE TRIGGER catalogue_cache AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON %I FOR EACH STATEMENT EXECUTE FUNCTION bump_read_cache()', relation_name);
    END LOOP;
END; $$;
CREATE TABLE schema_migration (
    version integer PRIMARY KEY, description text NOT NULL,
    installed_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO schema_migration(version,description) VALUES
(1,'Esquema base de main'),(2,'Flujo regional'),(3,'Urgencia en solicitudes'),
(4,'Flujo de órganos'),(5,'Base compartida para microservicios');
CREATE TRIGGER blood_review_history BEFORE UPDATE OR DELETE ON blood_review FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER algorithm_run_history BEFORE UPDATE OR DELETE ON algorithm_run FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER telemetry_history BEFORE UPDATE OR DELETE ON transport_telemetry FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER health_check_history BEFORE UPDATE OR DELETE ON service_health_check FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
