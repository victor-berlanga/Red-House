CREATE TABLE resources(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,region_id uuid NOT NULL,folio text NOT NULL,
 current_institution_id uuid NOT NULL,donation_id uuid,
 kind text NOT NULL CHECK(kind IN ('BLOOD','ORGAN')),component text NOT NULL,blood_group text NOT NULL,
 expires_at timestamptz NOT NULL,status text NOT NULL DEFAULT 'QUARANTINE',version integer NOT NULL DEFAULT 1,
 created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(tenant_id,folio));
CREATE INDEX available_resources ON resources(region_id,kind,component,expires_at) WHERE status='AVAILABLE';
CREATE INDEX availability_page ON resources(region_id,expires_at,id) WHERE status='AVAILABLE';
CREATE TABLE resource_reviews(id uuid PRIMARY KEY,resource_id uuid NOT NULL REFERENCES resources(id),actor_id uuid NOT NULL,
 decision text NOT NULL,reason text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE operations(id uuid PRIMARY KEY,user_id uuid NOT NULL,tenant_id uuid NOT NULL,key text NOT NULL,
 fingerprint text NOT NULL,input jsonb NOT NULL,status text NOT NULL DEFAULT 'PENDING',hold_id uuid,
 error text,last_recovery_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(user_id,key));
CREATE TABLE reservations(id uuid PRIMARY KEY,operation_id uuid NOT NULL UNIQUE REFERENCES operations(id),
 resource_id uuid NOT NULL REFERENCES resources(id),request_id uuid NOT NULL,recipient_id uuid NOT NULL,
 origin_id uuid NOT NULL,destination_id uuid NOT NULL,region_id uuid NOT NULL,hold_id uuid NOT NULL UNIQUE,
 evaluation_id uuid NOT NULL,route_id uuid NOT NULL,route_version integer NOT NULL,status text NOT NULL DEFAULT 'PENDING',
 shipment_id uuid,shipment_sequence integer NOT NULL DEFAULT 0,created_at timestamptz NOT NULL DEFAULT now());
CREATE UNIQUE INDEX resource_reserved ON reservations(resource_id) WHERE status<>'CANCELLED';
CREATE TABLE movements(id uuid PRIMARY KEY,resource_id uuid NOT NULL REFERENCES resources(id),action text NOT NULL,
 actor_id uuid NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TRIGGER movements_immutable BEFORE UPDATE OR DELETE ON movements FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
