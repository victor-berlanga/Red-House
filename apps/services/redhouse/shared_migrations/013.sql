-- Extracción de Documentos sin copiar archivos, referencias ni historia.
CREATE SCHEMA IF NOT EXISTS access_documentos;
DO $$
DECLARE target_table text; definition text; item record;
BEGIN
  FOREACH target_table IN ARRAY ARRAY['schema_version','activity_events','outbox','inbox','idempotency','decisions','worker_health'] LOOP
    IF to_regclass('access_documentos.' || target_table) IS NULL THEN
      SELECT pg_get_viewdef(to_regclass('access_transporte.' || target_table), true) INTO definition;
      definition := replace(definition, '''transporte''', '''documentos''');
      EXECUTE format('CREATE VIEW access_documentos.%I AS %s', target_table, definition);
      EXECUTE format('ALTER VIEW access_documentos.%I SET (check_option=local)', target_table);
      SELECT pg_get_functiondef(to_regprocedure('access_transporte.insert_' || target_table || '()')) INTO definition;
      definition := replace(replace(definition, 'access_transporte.', 'access_documentos.'), '''transporte''', '''documentos''');
      EXECUTE definition;
      EXECUTE format('CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_documentos.%I FOR EACH ROW EXECUTE FUNCTION access_documentos.insert_%s()', target_table, target_table);
      FOR item IN SELECT column_name,column_default FROM information_schema.columns WHERE table_schema='access_transporte' AND columns.table_name=target_table AND column_default IS NOT NULL LOOP
        EXECUTE format('ALTER VIEW access_documentos.%I ALTER COLUMN %I SET DEFAULT %s', target_table,item.column_name,item.column_default);
      END LOOP;
    END IF;
  END LOOP;
  SELECT pg_get_viewdef('access_transporte.files'::regclass, true) INTO definition;
  EXECUTE 'CREATE OR REPLACE VIEW access_documentos.files AS ' || definition;
  FOR item IN SELECT column_name,column_default FROM information_schema.columns WHERE table_schema='access_transporte' AND columns.table_name='files' AND column_default IS NOT NULL LOOP
    EXECUTE format('ALTER VIEW access_documentos.files ALTER COLUMN %I SET DEFAULT %s',item.column_name,item.column_default);
  END LOOP;
END $$;
INSERT INTO red_house.service_schema_version(service,version) VALUES('documentos',1),('documentos',2) ON CONFLICT DO NOTHING;

-- Se mueve la clave de idempotencia, no se repite la operación ni se cambia su resultado.
UPDATE red_house.service_idempotency SET service='documentos'
WHERE service='transporte' AND (operation LIKE 'file_%' OR operation LIKE 'document_%' OR operation LIKE 'export_%');
-- Las colas y eventos anteriores conservan su fuente Transporte y su worker los drena.
ALTER TABLE red_house.export_jobs ADD COLUMN region_id uuid;
UPDATE red_house.export_jobs job SET region_id=(
  SELECT (event->>'region_id')::uuid FROM red_house.service_activity_events
  WHERE service='transporte' AND event->>'action'='EXPORT_REQUESTED'
  AND event->>'resource_id'=job.id::text ORDER BY created_at LIMIT 1
);
INSERT INTO red_house.schema_migration(version,description) VALUES(13,'Propietario Documentos y Reportes; referencias e idempotencia conservadas');
