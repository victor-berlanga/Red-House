-- Additive provenance; previous specifications, results and runs stay immutable.
ALTER TABLE red_house.lab_profiles ADD COLUMN evidence_rules jsonb NOT NULL DEFAULT '[]';
ALTER TABLE red_house.lab_profiles ADD COLUMN reference_snapshot jsonb NOT NULL DEFAULT '[]';
ALTER TABLE red_house.lab_results ADD COLUMN catalogue_check jsonb;
ALTER TABLE red_house.regional_graphs ADD COLUMN provenance jsonb;
INSERT INTO red_house.schema_migration(version,description) VALUES(16,'Public source traceability, HLA membership snapshots and road provenance');
