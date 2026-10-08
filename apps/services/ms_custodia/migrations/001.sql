CREATE TABLE chains(id uuid PRIMARY KEY,region_id uuid NOT NULL,origin_id uuid NOT NULL,destination_id uuid NOT NULL,last_sequence integer NOT NULL DEFAULT 0,last_hash text NOT NULL DEFAULT '');
CREATE TABLE custody_events(id uuid PRIMARY KEY,shipment_id uuid NOT NULL REFERENCES chains(id),sequence integer NOT NULL,
 event jsonb NOT NULL,previous_hash text NOT NULL,hash text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(shipment_id,sequence));
CREATE TRIGGER custody_immutable BEFORE UPDATE OR DELETE ON custody_events FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
