CREATE TABLE routes(id uuid PRIMARY KEY,origin_id uuid NOT NULL,destination_id uuid NOT NULL,region_id uuid NOT NULL,
 distance_km double precision NOT NULL CHECK(distance_km>=0),travel_minutes integer NOT NULL CHECK(travel_minutes>=0),
 source text NOT NULL,version integer NOT NULL DEFAULT 1,updated_at timestamptz NOT NULL DEFAULT now(),UNIQUE(origin_id,destination_id));
CREATE TABLE rankings(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,evaluation_id uuid NOT NULL,algorithm_version text NOT NULL,
 factors jsonb NOT NULL,result jsonb NOT NULL,elapsed_ms double precision NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE proposals(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,algorithm_version text NOT NULL,snapshots jsonb NOT NULL,
 result jsonb NOT NULL,elapsed_ms double precision NOT NULL,slot_count integer NOT NULL,matched_count integer NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
