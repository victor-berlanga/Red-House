CREATE TABLE shipments(id uuid PRIMARY KEY,reservation_id uuid NOT NULL UNIQUE,origin_id uuid NOT NULL,destination_id uuid NOT NULL,
 region_id uuid NOT NULL,transport_user_id uuid NOT NULL,departure_at timestamptz NOT NULL,eta timestamptz NOT NULL,
 status text NOT NULL DEFAULT 'PLANNED',version integer NOT NULL DEFAULT 1,sequence integer NOT NULL DEFAULT 0,
 inventory_pending boolean NOT NULL DEFAULT true,expires_at timestamptz NOT NULL,CHECK(eta>departure_at),CHECK(eta<expires_at));
CREATE TABLE transitions(id uuid PRIMARY KEY,shipment_id uuid NOT NULL REFERENCES shipments(id),sequence integer NOT NULL,
 state text NOT NULL,actor_id uuid NOT NULL,reason text NOT NULL,evidence jsonb,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(shipment_id,sequence));
CREATE TRIGGER transitions_immutable BEFORE UPDATE OR DELETE ON transitions FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TABLE telemetry(id uuid PRIMARY KEY,shipment_id uuid NOT NULL REFERENCES shipments(id),actor_id uuid NOT NULL,
 latitude double precision NOT NULL,longitude double precision NOT NULL,captured_at timestamptz NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE files(id uuid PRIMARY KEY,shipment_id uuid NOT NULL REFERENCES shipments(id),owner_id uuid NOT NULL,
 object_path text NOT NULL UNIQUE,mime_type text NOT NULL,size integer NOT NULL CHECK(size BETWEEN 1 AND 10485760),
 sha256 text NOT NULL,status text NOT NULL DEFAULT 'PENDING',generation text,created_at timestamptz NOT NULL DEFAULT now());
