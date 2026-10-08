CREATE TABLE checks(id uuid PRIMARY KEY,service text NOT NULL,state text NOT NULL,elapsed_ms double precision NOT NULL,
 dependency text,last_error text,version text,created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX checks_latest ON checks(service,created_at DESC);
