SET LOCAL search_path=red_house,pg_catalog;
-- Un único propietario por tabla, sin duplicar instituciones, campañas ni archivos.
CREATE TABLE institution_presentations(
 id uuid PRIMARY KEY REFERENCES institution(institution_id), version integer NOT NULL DEFAULT 1,
 published boolean NOT NULL DEFAULT false, description text NOT NULL DEFAULT '',
 latitude double precision, longitude double precision, coordinate_source text,
 coordinate_recorded_at timestamptz, synthetic boolean NOT NULL DEFAULT true,
 CHECK ((latitude IS NULL) = (longitude IS NULL)),
 CHECK (latitude BETWEEN -90 AND 90), CHECK (longitude BETWEEN -180 AND 180)
);
CREATE TABLE portal_policies(
 id uuid PRIMARY KEY REFERENCES institution(institution_id), version integer NOT NULL DEFAULT 1,
 timezone text NOT NULL, tracking_interval_seconds integer NOT NULL,
 tracking_stale_seconds integer NOT NULL, reference text NOT NULL,
 CHECK (tracking_interval_seconds BETWEEN 1 AND 300),
 CHECK (tracking_stale_seconds BETWEEN 5 AND 3600),
 CHECK (tracking_stale_seconds >= tracking_interval_seconds)
);
CREATE TABLE campaign_publications(
 id uuid PRIMARY KEY REFERENCES campaign(campaign_id), tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 published boolean NOT NULL DEFAULT false, venue text NOT NULL,
 information text NOT NULL, version integer NOT NULL DEFAULT 1
);
ALTER TABLE document_metadata ADD COLUMN policy_version integer NOT NULL DEFAULT 1;
CREATE OR REPLACE VIEW access_transporte.tracking_devices AS
 SELECT d.id,d.tenant_id,d.user_id,d.source,d.token_hash,d.expires_at,d.active,d.version,
 u.active AS user_active,i.active AS institution_active,u.role AS user_role,d.label
 FROM devices d JOIN user_account u ON u.account_id=d.user_id JOIN institution i ON i.institution_id=d.tenant_id;
ALTER TABLE export_jobs ADD COLUMN context jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE export_jobs ADD COLUMN sealed_authorization text;
INSERT INTO schema_migration(version,description) VALUES(17,'Portal: publicación autorizada, georreferencias, política operativa y conservación documental');
