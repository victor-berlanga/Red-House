-- Ampliación compatible de fuente móvil. No modifica filas ni historiales previos.
ALTER TABLE red_house.devices DROP CONSTRAINT devices_source_check;
ALTER TABLE red_house.devices ADD CONSTRAINT devices_source_check
 CHECK (source IN ('SIMULATOR','GPS_BRIDGE','ANDROID','IOS'));
INSERT INTO red_house.schema_migration(version,description) VALUES (18,'Fuente IOS y registro móvil propio compatible');
