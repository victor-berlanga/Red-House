SET LOCAL search_path=red_house,pg_catalog;
CREATE FUNCTION protect_lab_result() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (to_jsonb(NEW)-'status') IS DISTINCT FROM (to_jsonb(OLD)-'status')
    OR OLD.status <> 'CAPTURED' OR NEW.status NOT IN ('AUTHORIZED','REJECTED') THEN
  RAISE EXCEPTION 'Resultado histórico inmutable; registrar corrección' USING ERRCODE='42501';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER lab_result_immutable BEFORE UPDATE ON lab_results FOR EACH ROW EXECUTE FUNCTION protect_lab_result();
CREATE TRIGGER lab_result_no_delete BEFORE DELETE ON lab_results FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
INSERT INTO schema_migration(version,description) VALUES(12,'Protección de valores históricos de laboratorio');
