SET LOCAL search_path=red_house,pg_catalog;
CREATE TABLE devices(
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES institution(institution_id),
 user_id uuid NOT NULL REFERENCES user_account(account_id), source text NOT NULL
 CHECK(source IN ('SIMULATOR','GPS_BRIDGE','ANDROID')),
 label text NOT NULL, token_hash text NOT NULL, expires_at timestamptz NOT NULL,
 active boolean NOT NULL DEFAULT true, version integer NOT NULL DEFAULT 1,
 created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE tracking_assignments(
 id uuid PRIMARY KEY, shipment_id uuid NOT NULL REFERENCES shipment(shipment_id),
 device_id uuid NOT NULL REFERENCES devices(id), responsible_id uuid NOT NULL REFERENCES user_account(account_id),
 starts_at timestamptz NOT NULL, ends_at timestamptz NOT NULL CHECK(ends_at>starts_at),
 active boolean NOT NULL DEFAULT true, version integer NOT NULL DEFAULT 1,
 actor_id uuid NOT NULL REFERENCES user_account(account_id), created_at timestamptz NOT NULL DEFAULT now());
CREATE UNIQUE INDEX tracking_device_active ON tracking_assignments(device_id) WHERE active;
CREATE TABLE tracking_points(
 id uuid PRIMARY KEY, shipment_id uuid NOT NULL REFERENCES shipment(shipment_id),
 assignment_id uuid NOT NULL REFERENCES tracking_assignments(id), device_id uuid NOT NULL REFERENCES devices(id),
 cursor bigint NOT NULL CHECK(cursor>0), sequence bigint NOT NULL CHECK(sequence>=0),
 captured_at timestamptz NOT NULL, received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 fingerprint text NOT NULL, position jsonb NOT NULL,
 UNIQUE(shipment_id,cursor), UNIQUE(assignment_id,sequence));
CREATE INDEX tracking_capture ON tracking_points(shipment_id,captured_at DESC,cursor DESC);
CREATE TRIGGER tracking_history_immutable BEFORE UPDATE OR DELETE ON tracking_points
 FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE VIEW access_identidad_acceso.devices AS SELECT * FROM devices;
CREATE VIEW access_transporte.tracking_devices AS SELECT d.id,d.tenant_id,d.user_id,d.source,d.token_hash,
 d.expires_at,d.active,d.version,u.active AS user_active,i.active AS institution_active
 FROM devices d JOIN user_account u ON u.account_id=d.user_id JOIN institution i ON i.institution_id=d.tenant_id;
CREATE VIEW access_transporte.tracking_assignments AS SELECT * FROM tracking_assignments;
CREATE VIEW access_transporte.tracking_points AS SELECT * FROM tracking_points;
-- Defaults on views are explicit, as in the existing shared access schemas.
ALTER VIEW access_identidad_acceso.devices ALTER COLUMN active SET DEFAULT true;
ALTER VIEW access_identidad_acceso.devices ALTER COLUMN version SET DEFAULT 1;
ALTER VIEW access_identidad_acceso.devices ALTER COLUMN created_at SET DEFAULT now();
ALTER VIEW access_transporte.tracking_assignments ALTER COLUMN active SET DEFAULT true;
ALTER VIEW access_transporte.tracking_assignments ALTER COLUMN version SET DEFAULT 1;
ALTER VIEW access_transporte.tracking_assignments ALTER COLUMN created_at SET DEFAULT now();
ALTER VIEW access_transporte.tracking_points ALTER COLUMN received_at SET DEFAULT clock_timestamp();
INSERT INTO schema_migration(version,description) VALUES(8,'Identidades de dispositivo y rastreo durable con cursor');
