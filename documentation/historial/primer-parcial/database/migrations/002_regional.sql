-- Ampliación académica; se aplica una vez mediante migrate-db, en transacción.
ALTER TABLE institution DROP CONSTRAINT institution_institution_type_check;
ALTER TABLE institution ADD CHECK (institution_type IN ('BLOOD_BANK','HOSPITAL','COORDINATION','TRANSPLANT_CENTER'));
ALTER TABLE institution ADD COLUMN operating_hours varchar(240) NOT NULL DEFAULT '';
UPDATE role SET is_enabled = true WHERE role_code IN ('MEDICAL','COORDINATOR','TRANSPORT');
ALTER TABLE account_role ADD CHECK (role_code NOT IN ('MEDICAL','TRANSPORT') OR institution_id IS NOT NULL);
ALTER TABLE blood_unit DROP CONSTRAINT blood_unit_current_status_check;
ALTER TABLE blood_unit ADD CHECK (current_status IN ('AVAILABLE','QUARANTINED','WITHDRAWN','RESERVED','IN_TRANSIT','DELIVERED'));

CREATE TABLE donor (
    donor_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id uuid NOT NULL REFERENCES institution,
    record_code varchar(30) NOT NULL UNIQUE,
    display_name varchar(120) NOT NULL,
    blood_group varchar(3) NOT NULL CHECK (blood_group IN ('O-','O+','A-','A+','B-','B+','AB-','AB+')),
    donation_kind varchar(30) NOT NULL CHECK (donation_kind IN ('VOLUNTARY','REPLACEMENT')),
    background varchar(1000) NOT NULL,
    restrictions varchar(1000) NOT NULL,
    consent_reference varchar(240) NOT NULL,
    consent_at timestamptz NOT NULL,
    current_status varchar(20) NOT NULL DEFAULT 'PENDING' CHECK (current_status IN ('PENDING','ELIGIBLE','DEFERRED')),
    created_by uuid NOT NULL REFERENCES user_account,
    registered_at timestamptz NOT NULL DEFAULT now(),
    version_no integer NOT NULL DEFAULT 1
);
CREATE TABLE donor_review (
    review_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id uuid NOT NULL REFERENCES donor,
    decision varchar(20) NOT NULL CHECK (decision IN ('ELIGIBLE','DEFERRED')),
    reason varchar(1000) NOT NULL,
    actor_id uuid NOT NULL REFERENCES user_account,
    occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE donation (
    donation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id uuid NOT NULL REFERENCES donor,
    review_id uuid NOT NULL REFERENCES donor_review,
    donation_code varchar(30) NOT NULL UNIQUE,
    current_status varchar(20) NOT NULL DEFAULT 'REGISTERED' CHECK (current_status IN ('REGISTERED','COLLECTED','PROCESSED','CANCELLED')),
    collected_at timestamptz,
    processed_at timestamptz,
    created_by uuid NOT NULL REFERENCES user_account,
    registered_at timestamptz NOT NULL DEFAULT now(),
    version_no integer NOT NULL DEFAULT 1
);
CREATE TABLE donation_event (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    donation_id uuid NOT NULL REFERENCES donation,
    status varchar(20) NOT NULL,
    actor_id uuid NOT NULL REFERENCES user_account,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    observation varchar(1000) NOT NULL
);
CREATE TABLE donation_unit (
    resource_id uuid PRIMARY KEY REFERENCES blood_unit,
    donation_id uuid NOT NULL REFERENCES donation,
    released_by uuid NOT NULL REFERENCES user_account,
    release_reference varchar(240) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE recipient (
    recipient_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id uuid NOT NULL REFERENCES institution,
    record_code varchar(30) NOT NULL UNIQUE,
    display_name varchar(120) NOT NULL,
    blood_group varchar(3) NOT NULL CHECK (blood_group IN ('O-','O+','A-','A+','B-','B+','AB-','AB+')),
    requirement varchar(1000) NOT NULL,
    urgency varchar(20) NOT NULL DEFAULT 'ROUTINE' CHECK (urgency IN ('URGENT','PRIORITY','ROUTINE')),
    studies varchar(1000) NOT NULL,
    restrictions varchar(1000) NOT NULL,
    current_status varchar(20) NOT NULL DEFAULT 'ACTIVE' CHECK (current_status IN ('ACTIVE','INACTIVE')),
    responsible_id uuid NOT NULL REFERENCES user_account,
    registered_at timestamptz NOT NULL DEFAULT now(),
    version_no integer NOT NULL DEFAULT 1
);
CREATE TABLE blood_request (
    request_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    request_code varchar(30) NOT NULL UNIQUE,
    recipient_id uuid NOT NULL REFERENCES recipient,
    component_id uuid NOT NULL REFERENCES blood_component,
    quantity integer NOT NULL CHECK (quantity BETWEEN 1 AND 100),
    urgency varchar(20) NOT NULL CHECK (urgency IN ('URGENT','PRIORITY','ROUTINE')),
    justification varchar(1000) NOT NULL,
    current_status varchar(20) NOT NULL DEFAULT 'OPEN' CHECK (current_status IN ('OPEN','IN_PROGRESS','CLOSED','CANCELLED')),
    responsible_id uuid NOT NULL REFERENCES user_account,
    requested_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz,
    version_no integer NOT NULL DEFAULT 1
);
CREATE TABLE request_event (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id uuid NOT NULL REFERENCES blood_request,
    action varchar(30) NOT NULL,
    actor_id uuid NOT NULL REFERENCES user_account,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    observation varchar(240) NOT NULL
);
CREATE TABLE regional_route (
    route_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_id uuid NOT NULL REFERENCES institution,
    destination_id uuid NOT NULL REFERENCES institution,
    distance_km integer NOT NULL CHECK (distance_km BETWEEN 0 AND 5000),
    travel_minutes integer NOT NULL CHECK (travel_minutes BETWEEN 1 AND 10080),
    source_reference varchar(240) NOT NULL,
    recorded_by uuid NOT NULL REFERENCES user_account,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    version_no integer NOT NULL DEFAULT 1,
    UNIQUE (origin_id,destination_id)
);
CREATE TABLE candidate_evaluation (
    evaluation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id uuid NOT NULL REFERENCES blood_request,
    algorithm_version varchar(60) NOT NULL,
    request_version integer NOT NULL,
    recipient_version integer NOT NULL,
    actor_id uuid NOT NULL REFERENCES user_account,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    elapsed_ms numeric NOT NULL CHECK (elapsed_ms >= 0)
);
CREATE TABLE blood_candidate (
    candidate_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id uuid NOT NULL REFERENCES candidate_evaluation,
    resource_id uuid NOT NULL REFERENCES blood_unit,
    rank_no integer NOT NULL CHECK (rank_no > 0),
    unit_version integer NOT NULL,
    donor_group varchar(3) NOT NULL,
    recipient_group varchar(3) NOT NULL,
    urgency varchar(20) NOT NULL,
    wait_minutes integer NOT NULL CHECK (wait_minutes >= 0),
    distance_km integer NOT NULL,
    travel_minutes integer NOT NULL,
    route_version integer NOT NULL,
    expires_at timestamptz NOT NULL,
    explanation varchar(1000) NOT NULL,
    UNIQUE (evaluation_id,resource_id),
    UNIQUE (evaluation_id,rank_no)
);
CREATE TABLE blood_allocation (
    allocation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id uuid NOT NULL REFERENCES blood_request,
    candidate_id uuid NOT NULL UNIQUE REFERENCES blood_candidate,
    resource_id uuid NOT NULL REFERENCES blood_unit,
    origin_id uuid NOT NULL REFERENCES institution,
    destination_id uuid NOT NULL REFERENCES institution,
    authorized_by uuid NOT NULL REFERENCES user_account,
    authorization_reason varchar(240) NOT NULL,
    current_status varchar(20) NOT NULL DEFAULT 'RESERVED' CHECK (current_status IN ('RESERVED','ASSIGNED','IN_TRANSIT','RECEIVED','CANCELLED')),
    reserved_at timestamptz NOT NULL DEFAULT now(),
    received_at timestamptz,
    version_no integer NOT NULL DEFAULT 1
);
-- Una unidad entregada tampoco vuelve a asignarse. Cancelar conserva el registro.
CREATE UNIQUE INDEX allocation_resource_exclusive ON blood_allocation(resource_id) WHERE current_status <> 'CANCELLED';
CREATE TABLE shipment (
    shipment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    allocation_id uuid NOT NULL UNIQUE REFERENCES blood_allocation,
    transport_id uuid NOT NULL REFERENCES user_account,
    vehicle varchar(120) NOT NULL,
    departure_at timestamptz NOT NULL,
    eta timestamptz NOT NULL CHECK (eta > departure_at),
    current_status varchar(20) NOT NULL DEFAULT 'SCHEDULED' CHECK (current_status IN ('SCHEDULED','PREPARED','COLLECTED','IN_TRANSIT','DELIVERED','ACCEPTED','CANCELLED')),
    version_no integer NOT NULL DEFAULT 1
);
CREATE TABLE custody_event (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id uuid NOT NULL REFERENCES shipment,
    sequence integer NOT NULL,
    status varchar(20) NOT NULL,
    actor_id uuid NOT NULL REFERENCES user_account,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    location_description varchar(240) NOT NULL,
    observation varchar(1000) NOT NULL,
    evidence_reference varchar(240) NOT NULL,
    UNIQUE (shipment_id,sequence)
);
CREATE INDEX donor_institution_idx ON donor(institution_id);
CREATE INDEX recipient_institution_idx ON recipient(institution_id);
CREATE INDEX request_recipient_idx ON blood_request(recipient_id);
CREATE INDEX request_queue_idx ON blood_request(current_status,urgency,requested_at);
CREATE INDEX allocation_request_idx ON blood_allocation(request_id);
CREATE INDEX shipment_transport_idx ON shipment(transport_id);
CREATE TRIGGER donor_review_append_only BEFORE UPDATE OR DELETE ON donor_review FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER donation_event_append_only BEFORE UPDATE OR DELETE ON donation_event FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER donation_unit_append_only BEFORE UPDATE OR DELETE ON donation_unit FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER request_event_append_only BEFORE UPDATE OR DELETE ON request_event FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER evaluation_append_only BEFORE UPDATE OR DELETE ON candidate_evaluation FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER candidate_append_only BEFORE UPDATE OR DELETE ON blood_candidate FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER custody_append_only BEFORE UPDATE OR DELETE ON custody_event FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
