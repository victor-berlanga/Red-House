-- Almacenamiento técnico del portal, separado de las 71 tablas del dominio.
-- Instalador/actualizador explícito; la aplicación no ejecuta DDL.
CREATE SCHEMA IF NOT EXISTS web_runtime AUTHORIZATION rh_shared_owner;
CREATE TABLE IF NOT EXISTS web_runtime.session_revocations (
    id text PRIMARY KEY CHECK (id ~ '^[0-9a-f]{64}$'),
    payload bytea,
    expires timestamptz NOT NULL,
    confirmed boolean NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS session_revocations_pending
    ON web_runtime.session_revocations(expires) WHERE NOT confirmed;
CREATE INDEX IF NOT EXISTS session_revocations_expiry
    ON web_runtime.session_revocations(expires);
REVOKE ALL ON SCHEMA web_runtime FROM PUBLIC;
REVOKE ALL ON web_runtime.session_revocations FROM PUBLIC;
