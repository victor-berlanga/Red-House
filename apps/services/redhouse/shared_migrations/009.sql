SET LOCAL search_path=red_house,pg_catalog;
CREATE TABLE security_factors(id uuid PRIMARY KEY REFERENCES user_account(account_id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 secret_ciphertext text NOT NULL, last_counter bigint NOT NULL DEFAULT -1, active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE security_contacts(id uuid PRIMARY KEY REFERENCES user_account(account_id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 email text NOT NULL, verified boolean NOT NULL DEFAULT false, verification_hash text NOT NULL, expires_at timestamptz NOT NULL, version integer NOT NULL DEFAULT 1);
CREATE TABLE recovery_tokens(id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES user_account(account_id), token_hash text NOT NULL UNIQUE,
 expires_at timestamptz NOT NULL, used_at timestamptz, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE identity_deliveries(id uuid PRIMARY KEY, recipient text NOT NULL, payload_ciphertext text NOT NULL,
 status text NOT NULL DEFAULT 'PENDING', attempts integer NOT NULL DEFAULT 0, next_attempt timestamptz NOT NULL DEFAULT now(),
 delivered_at timestamptz, last_error text, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE accreditations(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 issuer text NOT NULL, category text NOT NULL, reference text NOT NULL, valid_from timestamptz NOT NULL, valid_until timestamptz NOT NULL,
 author_id uuid NOT NULL REFERENCES user_account(account_id), supersedes uuid REFERENCES accreditations(id), version integer NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), CHECK(valid_until>valid_from));
CREATE TABLE consent_versions(id uuid PRIMARY KEY, donor_id uuid NOT NULL REFERENCES donor(donor_id),
 tenant_id uuid NOT NULL REFERENCES institution(institution_id), author_id uuid NOT NULL REFERENCES user_account(account_id),
 version integer NOT NULL, policy_version text NOT NULL, reference text NOT NULL, effective_at timestamptz NOT NULL,
 granted boolean NOT NULL, supersedes uuid REFERENCES consent_versions(id), created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(donor_id,version));
CREATE TABLE campaign_slots(id uuid PRIMARY KEY, campaign_id uuid NOT NULL REFERENCES campaign(campaign_id),
 tenant_id uuid NOT NULL REFERENCES institution(institution_id), site_id uuid NOT NULL REFERENCES catalogue_entry(id),
 starts_at timestamptz NOT NULL, ends_at timestamptz NOT NULL, capacity integer NOT NULL CHECK(capacity>0),
 active boolean NOT NULL DEFAULT true, version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(), CHECK(ends_at>starts_at));
CREATE TABLE appointment_slots(id uuid PRIMARY KEY REFERENCES appointment(appointment_id), slot_id uuid NOT NULL REFERENCES campaign_slots(id),
 tenant_id uuid NOT NULL REFERENCES institution(institution_id), status text NOT NULL DEFAULT 'BOOKED', version integer NOT NULL DEFAULT 1,
 created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE lab_profiles(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 name text NOT NULL, kind text NOT NULL CHECK(kind IN ('BLOOD','ORGAN')), component text NOT NULL, version integer NOT NULL,
 required_tests jsonb NOT NULL CHECK(jsonb_typeof(required_tests)='array'), source text NOT NULL,
 synthetic boolean NOT NULL CHECK(synthetic), author_id uuid NOT NULL REFERENCES user_account(account_id),
 effective_at timestamptz NOT NULL, supersedes uuid REFERENCES lab_profiles(id), created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE lab_samples(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 resource_id uuid REFERENCES resource(resource_id), recipient_id uuid REFERENCES recipient(recipient_id), donation_id uuid REFERENCES donation(donation_id),
 profile_id uuid NOT NULL REFERENCES lab_profiles(id), identifier text NOT NULL, collected_at timestamptz NOT NULL,
 received_at timestamptz, status text NOT NULL DEFAULT 'REQUESTED' CHECK(status IN ('REQUESTED','RECEIVED','REJECTED')),
 version integer NOT NULL DEFAULT 1, author_id uuid NOT NULL REFERENCES user_account(account_id), created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(num_nonnulls(resource_id,recipient_id,donation_id)=1), UNIQUE(tenant_id,identifier));
CREATE TABLE lab_results(id uuid PRIMARY KEY, sample_id uuid NOT NULL REFERENCES lab_samples(id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 test_code text NOT NULL, value text NOT NULL, unit text, method text NOT NULL, laboratory text NOT NULL, reference text NOT NULL,
 measured_at timestamptz NOT NULL, author_id uuid NOT NULL REFERENCES user_account(account_id),
 version integer NOT NULL, supersedes uuid REFERENCES lab_results(id), status text NOT NULL DEFAULT 'CAPTURED'
 CHECK(status IN ('CAPTURED','AUTHORIZED','REJECTED')), created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(sample_id,test_code,version));
CREATE TABLE lab_actions(id uuid PRIMARY KEY, result_id uuid NOT NULL REFERENCES lab_results(id), author_id uuid NOT NULL REFERENCES user_account(account_id),
 decision text NOT NULL, reason text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE resource_lineage(id uuid PRIMARY KEY, parent_id uuid NOT NULL REFERENCES resource(resource_id), child_id uuid NOT NULL UNIQUE REFERENCES resource(resource_id),
 donation_id uuid NOT NULL REFERENCES donation(donation_id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 author_id uuid NOT NULL REFERENCES user_account(account_id), reason text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), CHECK(parent_id<>child_id));
CREATE TABLE resource_controls(id uuid PRIMARY KEY REFERENCES resource(resource_id), lab_profile_id uuid REFERENCES lab_profiles(id),
 cold_equipment_id uuid, cold_profile_id uuid, blocked boolean NOT NULL DEFAULT false, version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE cold_equipment(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id), label text NOT NULL,
 location text NOT NULL, calibration_reference text, active boolean NOT NULL DEFAULT true, version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE cold_profiles(id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 kind text NOT NULL CHECK(kind IN ('BLOOD','ORGAN')), component text NOT NULL, minimum_c double precision NOT NULL,
 maximum_c double precision NOT NULL, max_gap_seconds integer NOT NULL CHECK(max_gap_seconds>0), source text NOT NULL,
 synthetic boolean NOT NULL CHECK(synthetic), version integer NOT NULL, author_id uuid NOT NULL REFERENCES user_account(account_id),
 effective_at timestamptz NOT NULL, supersedes uuid UNIQUE REFERENCES cold_profiles(id),
 created_at timestamptz NOT NULL DEFAULT now(), CHECK(maximum_c>minimum_c));
ALTER TABLE resource_controls ADD FOREIGN KEY(cold_equipment_id) REFERENCES cold_equipment(id);
ALTER TABLE resource_controls ADD FOREIGN KEY(cold_profile_id) REFERENCES cold_profiles(id);
CREATE TABLE cold_readings(id uuid PRIMARY KEY, resource_id uuid NOT NULL REFERENCES resource(resource_id), equipment_id uuid NOT NULL REFERENCES cold_equipment(id),
 profile_id uuid NOT NULL REFERENCES cold_profiles(id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 temperature_c double precision NOT NULL, captured_at timestamptz NOT NULL, received_at timestamptz NOT NULL DEFAULT now(),
 source text NOT NULL, calibration_reference text, excursion boolean NOT NULL, gap boolean NOT NULL,
 author_id uuid NOT NULL REFERENCES user_account(account_id));
CREATE INDEX cold_history ON cold_readings(resource_id,captured_at DESC);
CREATE TABLE cold_reviews(id uuid PRIMARY KEY, resource_id uuid NOT NULL REFERENCES resource(resource_id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 author_id uuid NOT NULL REFERENCES user_account(account_id), reason text NOT NULL, decision text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE resource_destinations(id uuid PRIMARY KEY, resource_id uuid NOT NULL REFERENCES resource(resource_id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 destination text NOT NULL CHECK(destination IN ('TRANSFUSED','TRANSPLANTED','DISCARDED','RETURNED','RESEARCH')),
 reference text NOT NULL, occurred_at timestamptz NOT NULL, reason text NOT NULL, author_id uuid NOT NULL REFERENCES user_account(account_id),
 version integer NOT NULL, supersedes uuid REFERENCES resource_destinations(id), created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(resource_id,version));
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['accreditations','consent_versions','lab_profiles','lab_actions','resource_lineage','cold_profiles','cold_readings','cold_reviews','resource_destinations'] LOOP
  EXECUTE format('CREATE TRIGGER history_immutable BEFORE UPDATE OR DELETE ON red_house.%I FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation()',t);
 END LOOP;
END $$;
INSERT INTO schema_migration(version,description) VALUES(9,'Consentimiento, agenda, laboratorio, linaje, frío, destino e identidad reforzada');
