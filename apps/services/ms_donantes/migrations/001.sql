CREATE TABLE donors(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,user_id uuid,folio text NOT NULL,display_name text NOT NULL,
 blood_group text NOT NULL,consent boolean NOT NULL CHECK(consent),status text NOT NULL DEFAULT 'PRELIMINARY',
 version integer NOT NULL DEFAULT 1,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(tenant_id,folio));
CREATE UNIQUE INDEX donor_account ON donors(user_id) WHERE user_id IS NOT NULL;
CREATE TABLE donor_reviews(id uuid PRIMARY KEY,donor_id uuid NOT NULL REFERENCES donors(id),decision text NOT NULL,
 reason text NOT NULL,actor_id uuid NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE donations(id uuid PRIMARY KEY,donor_id uuid NOT NULL REFERENCES donors(id),tenant_id uuid NOT NULL,
 kind text NOT NULL CHECK(kind IN ('BLOOD','ORGAN')),component text NOT NULL,blood_group text NOT NULL,
 collected_at timestamptz NOT NULL,status text NOT NULL DEFAULT 'COLLECTED',version integer NOT NULL DEFAULT 1,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE donation_steps(id uuid PRIMARY KEY,donation_id uuid NOT NULL REFERENCES donations(id),state text NOT NULL,
 actor_id uuid NOT NULL,reason text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE campaigns(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,title text NOT NULL,starts_at timestamptz NOT NULL,
 ends_at timestamptz NOT NULL,capacity integer NOT NULL CHECK(capacity>0),status text NOT NULL DEFAULT 'OPEN',CHECK(ends_at>starts_at));
CREATE TABLE appointments(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,donor_id uuid NOT NULL REFERENCES donors(id),
 campaign_id uuid NOT NULL REFERENCES campaigns(id),status text NOT NULL DEFAULT 'BOOKED',created_at timestamptz NOT NULL DEFAULT now());
CREATE UNIQUE INDEX active_appointment ON appointments(donor_id,campaign_id) WHERE status='BOOKED';
