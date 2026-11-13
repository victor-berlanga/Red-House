-- Los análisis históricos no adquieren una identidad de motor inventada.
ALTER TABLE red_house.file_scans ADD COLUMN engine_version text;
ALTER TABLE red_house.file_scans ADD COLUMN signature_version text;
ALTER TABLE red_house.file_scans ADD COLUMN signature_at timestamptz;
ALTER TABLE red_house.file_scans ADD COLUMN signature_max_age_seconds integer;
INSERT INTO red_house.schema_migration(version,description)
 VALUES (20,'Identidad y vigencia observadas de ClamD en análisis nuevos');
