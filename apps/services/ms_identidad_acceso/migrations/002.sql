ALTER TABLE institutions ADD COLUMN created_by uuid REFERENCES users(id);
ALTER TABLE institutions ADD COLUMN version integer NOT NULL DEFAULT 1;
CREATE TABLE catalogue(id uuid PRIMARY KEY,tenant_id uuid NOT NULL REFERENCES institutions(id),
 kind text NOT NULL CHECK(kind IN ('sites','contacts','schedules','capacities','locations')),
 name text NOT NULL,parent_id uuid REFERENCES catalogue(id),details jsonb NOT NULL,
 active boolean NOT NULL DEFAULT true,version integer NOT NULL DEFAULT 1,
 created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(tenant_id,kind,name));
CREATE INDEX catalogue_tenant ON catalogue(tenant_id,kind,name,id);
