-- Órganos: persistencia independiente del inventario sanguíneo. Sin datos ni cuentas nuevos.
CREATE TABLE organ_donor (
 donor_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), institution_id uuid NOT NULL REFERENCES institution,
 record_code varchar(30) NOT NULL UNIQUE, display_name varchar(120) NOT NULL,
 abo varchar(2) NOT NULL CHECK(abo IN ('O','A','B','AB')),
 donation_kind varchar(12) NOT NULL CHECK(donation_kind IN ('LIVING','DECEASED')),
 consent_reference varchar(240) NOT NULL, studies text NOT NULL, hla text NOT NULL,
 clinical_reference varchar(240) NOT NULL, reviewed_by uuid NOT NULL REFERENCES user_account(account_id),
 registered_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE organ_recipient (
 recipient_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), institution_id uuid NOT NULL REFERENCES institution,
 record_code varchar(30) NOT NULL UNIQUE, display_name varchar(120) NOT NULL,
 organ_type varchar(12) NOT NULL CHECK(organ_type IN ('KIDNEY','LIVER','HEART')),
 abo varchar(2) NOT NULL CHECK(abo IN ('O','A','B','AB')), studies text NOT NULL, hla text NOT NULL,
 urgency varchar(12) NOT NULL CHECK(urgency IN ('URGENT','PRIORITY','ROUTINE')),
 waiting_since timestamptz NOT NULL, clinical_reference varchar(240) NOT NULL,
 responsible_id uuid NOT NULL REFERENCES user_account(account_id),
 current_status varchar(12) NOT NULL DEFAULT 'ACTIVE' CHECK(current_status IN ('ACTIVE','INACTIVE','RESERVED','CLOSED')),
 version_no integer NOT NULL DEFAULT 1, registered_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE organ_offer (
 offer_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), donor_id uuid NOT NULL REFERENCES organ_donor,
 record_code varchar(30) NOT NULL UNIQUE,
 organ_type varchar(12) NOT NULL CHECK(organ_type IN ('KIDNEY','LIVER','HEART')),
 anatomical_description varchar(240) NOT NULL,
 recovered_at timestamptz NOT NULL, preservation_until timestamptz NOT NULL CHECK(preservation_until>recovered_at),
 preservation_reference varchar(240) NOT NULL, released_by uuid NOT NULL REFERENCES user_account(account_id),
 current_status varchar(12) NOT NULL DEFAULT 'AVAILABLE' CHECK(current_status IN ('AVAILABLE','RESERVED','IN_TRANSIT','RECEIVED','WITHDRAWN')),
 version_no integer NOT NULL DEFAULT 1, registered_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE organ_evaluation (
 evaluation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), offer_id uuid NOT NULL REFERENCES organ_offer,
 evaluated_by uuid NOT NULL REFERENCES user_account(account_id), algorithm_version varchar(40) NOT NULL,
 evaluated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE organ_candidate (
 candidate_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), evaluation_id uuid NOT NULL REFERENCES organ_evaluation,
 offer_id uuid NOT NULL REFERENCES organ_offer, recipient_id uuid NOT NULL REFERENCES organ_recipient,
 offer_version integer NOT NULL, recipient_version integer NOT NULL, route_version integer NOT NULL,
 rank_no integer NOT NULL CHECK(rank_no>0), algorithm_version varchar(40) NOT NULL,
 explanation text NOT NULL, distance_km integer NOT NULL, travel_minutes integer NOT NULL,
 evaluated_by uuid NOT NULL REFERENCES user_account(account_id), evaluated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(evaluation_id,recipient_id)
);
CREATE TABLE organ_review (
 review_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), candidate_id uuid NOT NULL REFERENCES organ_candidate,
 decision varchar(12) NOT NULL CHECK(decision IN ('FAVORABLE','REJECTED')),
 hla_assessment text NOT NULL, size_assessment text NOT NULL, crossmatch_reference varchar(240) NOT NULL,
 clinical_reference varchar(240) NOT NULL, reviewed_by uuid NOT NULL REFERENCES user_account(account_id),
 occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE organ_allocation (
 allocation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), candidate_id uuid NOT NULL REFERENCES organ_candidate,
 review_id uuid NOT NULL REFERENCES organ_review, offer_id uuid NOT NULL REFERENCES organ_offer,
 recipient_id uuid NOT NULL REFERENCES organ_recipient, authorized_by uuid NOT NULL REFERENCES user_account(account_id),
 authorization_reference varchar(240) NOT NULL,
 current_status varchar(12) NOT NULL DEFAULT 'RESERVED' CHECK(current_status IN ('RESERVED','SCHEDULED','PREPARED','COLLECTED','IN_TRANSIT','DELIVERED','ACCEPTED','CANCELLED')),
 transport_id uuid REFERENCES user_account(account_id), vehicle varchar(120), departure_at timestamptz, eta timestamptz,
 reserved_at timestamptz NOT NULL DEFAULT now(), received_at timestamptz, version_no integer NOT NULL DEFAULT 1,
 CHECK(eta IS NULL OR eta>departure_at)
);
CREATE UNIQUE INDEX organ_exclusive_offer ON organ_allocation(offer_id) WHERE current_status<>'CANCELLED';
CREATE UNIQUE INDEX organ_exclusive_recipient ON organ_allocation(recipient_id) WHERE current_status<>'CANCELLED';
CREATE TABLE organ_custody_event (
 event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), allocation_id uuid NOT NULL REFERENCES organ_allocation,
 status varchar(20) NOT NULL, actor_id uuid NOT NULL REFERENCES user_account(account_id),
 occurred_at timestamptz NOT NULL DEFAULT now(), location_description varchar(240) NOT NULL,
 observation text NOT NULL, evidence_reference varchar(240) NOT NULL
);
CREATE INDEX organ_candidates_offer ON organ_candidate(offer_id,evaluated_at);
CREATE INDEX organ_custody_allocation ON organ_custody_event(allocation_id,occurred_at);
CREATE TRIGGER organ_donor_history BEFORE UPDATE OR DELETE ON organ_donor FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER organ_candidate_history BEFORE UPDATE OR DELETE ON organ_candidate FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER organ_review_history BEFORE UPDATE OR DELETE ON organ_review FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER organ_custody_history BEFORE UPDATE OR DELETE ON organ_custody_event FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();

CREATE TRIGGER organ_evaluation_history BEFORE UPDATE OR DELETE ON organ_evaluation FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
