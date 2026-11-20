-- Acceso por aplicación: cada sesión guarda la aplicación con la que inició (web, desktop, mobile).
-- Solo migración compartida (como 012-021): no hay migración por servicio posterior a schema.sql v6.
-- Aditiva: las filas previas quedan con client NULL; Identidad las rechaza (falla cerrada)
-- y apps/services/scripts/revocar_sesiones_sin_cliente.py las cierra al publicar.
ALTER TABLE red_house.web_session ADD COLUMN IF NOT EXISTS client text
 CHECK (client IS NULL OR client IN ('web','desktop','mobile'));
CREATE OR REPLACE VIEW access_identidad_acceso.sessions AS
 SELECT session_id AS id, account_id AS user_id, expires_at, revoked_at, client
 FROM red_house.web_session;
INSERT INTO red_house.schema_migration(version,description) VALUES (22,'Aplicación de origen por sesión (acceso por aplicación)');
