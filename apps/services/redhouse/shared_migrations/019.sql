-- Filas previas conservan su proveedor GCS; no se mueve ningún objeto.
ALTER TABLE red_house.stored_file ADD COLUMN storage_provider text NOT NULL DEFAULT 'gcs'
 CHECK (storage_provider IN ('gcs','local'));
ALTER TABLE red_house.export_jobs ADD COLUMN storage_provider text NOT NULL DEFAULT 'gcs' CHECK (storage_provider IN ('gcs','local'));
CREATE OR REPLACE VIEW access_documentos.files AS
 SELECT file_id AS id, shipment_id, owner_id, object_path, mime_type,
 size_bytes AS size, sha256, current_status AS status, generation, created_at, storage_provider
 FROM red_house.stored_file;
CREATE FUNCTION red_house.file_storage_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.storage_provider IS DISTINCT FROM OLD.storage_provider OR NEW.object_path IS DISTINCT FROM OLD.object_path THEN
  RAISE EXCEPTION 'stored file provider and path are immutable';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER file_storage_immutable BEFORE UPDATE ON red_house.stored_file
 FOR EACH ROW EXECUTE FUNCTION red_house.file_storage_immutable();
CREATE FUNCTION red_house.export_storage_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.storage_provider IS DISTINCT FROM OLD.storage_provider THEN
  RAISE EXCEPTION 'export provider is immutable once selected';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER export_storage_immutable BEFORE UPDATE ON red_house.export_jobs
 FOR EACH ROW EXECUTE FUNCTION red_house.export_storage_immutable();
INSERT INTO red_house.schema_migration(version,description) VALUES (19,'Proveedor inmutable por archivo; históricos GCS');
