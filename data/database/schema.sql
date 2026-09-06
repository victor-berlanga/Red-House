-- Red House · PostgreSQL 14+ · subconjunto académico del primer parcial.
-- Ejecutar UNA vez sobre una BD vacía, en una sola transacción.
-- Sin DROP, datos clínicos, contraseñas ni extensiones. Véase README.md.
CREATE SCHEMA red_house;
SET LOCAL search_path TO red_house, pg_catalog;

CREATE TABLE institution (
    institution_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_code varchar(30) NOT NULL UNIQUE,
    institution_name varchar(160) NOT NULL,
    institution_type varchar(40) NOT NULL CHECK (institution_type IN ('BLOOD_BANK', 'HOSPITAL', 'COORDINATION')),
    region_name varchar(80) NOT NULL,
    city varchar(100) NOT NULL,
    street varchar(200) NOT NULL,
    participation_status varchar(10) NOT NULL DEFAULT 'ACTIVE' CHECK (participation_status IN ('ACTIVE', 'INACTIVE')),
    version_no integer NOT NULL DEFAULT 1,
    registered_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE site (
    site_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id uuid NOT NULL REFERENCES institution,
    site_code varchar(30) NOT NULL,
    site_name varchar(120) NOT NULL,
    street varchar(200) NOT NULL,
    city varchar(100) NOT NULL,
    site_status varchar(10) NOT NULL DEFAULT 'ACTIVE' CHECK (site_status IN ('ACTIVE', 'INACTIVE')),
    version_no integer NOT NULL DEFAULT 1,
    UNIQUE (institution_id, site_code)
);
CREATE TABLE contact (
    contact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_name varchar(120) NOT NULL,
    contact_function varchar(80) NOT NULL
);
CREATE TABLE contact_method (
    contact_id uuid NOT NULL REFERENCES contact,
    method_kind varchar(10) NOT NULL CHECK (method_kind IN ('EMAIL', 'PHONE')),
    method_value varchar(180) NOT NULL,
    PRIMARY KEY (contact_id, method_kind)
);
CREATE TABLE institution_contact (
    institution_id uuid NOT NULL REFERENCES institution,
    contact_id uuid NOT NULL UNIQUE REFERENCES contact,
    PRIMARY KEY (institution_id, contact_id)
);
CREATE TABLE capability (
    capability_code varchar(40) PRIMARY KEY,
    capability_name varchar(100) NOT NULL
);
CREATE TABLE institution_capability (
    institution_id uuid NOT NULL REFERENCES institution,
    capability_code varchar(40) NOT NULL REFERENCES capability,
    PRIMARY KEY (institution_id, capability_code)
);
CREATE TABLE party (
    party_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    party_name varchar(120) NOT NULL
);
CREATE TABLE user_account (
    account_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    party_id uuid NOT NULL UNIQUE REFERENCES party,
    login_email varchar(180) NOT NULL UNIQUE CHECK (login_email = lower(login_email)),
    password_hash text NOT NULL,
    account_status varchar(10) NOT NULL DEFAULT 'ACTIVE' CHECK (account_status IN ('ACTIVE', 'INACTIVE')),
    version_no integer NOT NULL DEFAULT 1,
    registered_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE role (
    role_code varchar(30) PRIMARY KEY,
    role_name varchar(80) NOT NULL,
    is_enabled boolean NOT NULL
);
-- Una asignación vigente por cuenta en este incremento. Rol y ámbito forman
-- una misma asociación, nunca dos listas independientes de permisos y tenants.
CREATE TABLE account_role (
    account_id uuid PRIMARY KEY REFERENCES user_account,
    role_code varchar(30) NOT NULL REFERENCES role,
    institution_id uuid REFERENCES institution,
    region_name varchar(80),
    CHECK ((institution_id IS NOT NULL) <> (region_name IS NOT NULL)),
    CHECK (role_code <> 'OPERATOR' OR institution_id IS NOT NULL)
);
CREATE TABLE blood_component (
    component_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    component_code varchar(30) NOT NULL UNIQUE,
    component_name varchar(100) NOT NULL,
    region_name varchar(80) NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    version_no integer NOT NULL DEFAULT 1
);
CREATE TABLE storage_location (
    location_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id uuid NOT NULL REFERENCES site,
    location_code varchar(30) NOT NULL,
    location_description varchar(150) NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    version_no integer NOT NULL DEFAULT 1,
    UNIQUE (site_id, location_code)
);
CREATE TABLE parameter_version (
    parameter_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parameter_code varchar(40) NOT NULL CHECK (parameter_code = 'EXPIRY_WARNING_HOURS'),
    region_name varchar(80) NOT NULL,
    version_no integer NOT NULL,
    scalar_value integer NOT NULL CHECK (scalar_value BETWEEN 1 AND 720),
    measurement_unit varchar(10) NOT NULL DEFAULT 'HOURS' CHECK (measurement_unit = 'HOURS'),
    is_demo boolean NOT NULL DEFAULT true CHECK (is_demo),
    approved_by uuid REFERENCES user_account,
    valid_from timestamptz NOT NULL DEFAULT now(),
    UNIQUE (region_name, parameter_code, version_no)
);
CREATE TABLE resource (
    resource_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    traceability_code varchar(40) NOT NULL UNIQUE,
    resource_kind varchar(10) NOT NULL DEFAULT 'BLOOD' CHECK (resource_kind = 'BLOOD')
);
CREATE TABLE blood_unit (
    resource_id uuid PRIMARY KEY REFERENCES resource,
    component_id uuid NOT NULL REFERENCES blood_component,
    location_id uuid NOT NULL REFERENCES storage_location,
    collected_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL CHECK (expires_at > collected_at),
    current_status varchar(16) NOT NULL CHECK (current_status IN ('AVAILABLE', 'QUARANTINED', 'WITHDRAWN')),
    version_no integer NOT NULL DEFAULT 1,
    registered_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE blood_classification (
    resource_id uuid PRIMARY KEY REFERENCES blood_unit,
    recorded_group_code varchar(3) NOT NULL CHECK (recorded_group_code IN ('O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+')),
    source_reference varchar(120) NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE blood_status_transition (
    previous_status varchar(16) NOT NULL,
    new_status varchar(16) NOT NULL,
    is_demo boolean NOT NULL DEFAULT true CHECK (is_demo),
    PRIMARY KEY (previous_status, new_status),
    CHECK (previous_status IN ('AVAILABLE', 'QUARANTINED')),
    CHECK (new_status IN ('AVAILABLE', 'QUARANTINED', 'WITHDRAWN')),
    CHECK (previous_status <> new_status)
);
CREATE TABLE blood_movement (
    movement_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id uuid NOT NULL REFERENCES blood_unit,
    sequence integer NOT NULL,
    previous_status varchar(16),
    new_status varchar(16) NOT NULL,
    origin_location_id uuid REFERENCES storage_location,
    destination_location_id uuid NOT NULL REFERENCES storage_location,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    actor_id uuid NOT NULL REFERENCES user_account,
    reason varchar(240) NOT NULL,
    UNIQUE (resource_id, sequence)
);
CREATE TABLE audit_event (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id uuid REFERENCES user_account,
    institution_id uuid REFERENCES institution,
    region_name varchar(80),
    occurred_at timestamptz NOT NULL DEFAULT now(),
    action varchar(50) NOT NULL,
    entity_type varchar(40) NOT NULL,
    entity_reference varchar(80) NOT NULL,
    outcome varchar(12) NOT NULL CHECK (outcome IN ('SUCCESS', 'DENIED', 'FAILED')),
    correlation_id uuid NOT NULL,
    reason varchar(240) NOT NULL
);
CREATE TABLE audit_change (
    event_id uuid NOT NULL REFERENCES audit_event,
    field_name varchar(60) NOT NULL,
    previous_value varchar(240),
    new_value varchar(240),
    PRIMARY KEY (event_id, field_name)
);
CREATE TABLE web_session (
    session_id uuid PRIMARY KEY,
    account_id uuid NOT NULL REFERENCES user_account,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE login_attempt (
    attempt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    identity_hash char(64) NOT NULL,
    address_hash char(64) NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    was_successful boolean NOT NULL
);

CREATE INDEX site_institution_idx ON site (institution_id);
CREATE INDEX account_role_scope_idx ON account_role (institution_id);
CREATE INDEX storage_site_idx ON storage_location (site_id);
CREATE INDEX blood_unit_location_idx ON blood_unit (location_id);
CREATE INDEX blood_unit_component_idx ON blood_unit (component_id);
CREATE INDEX blood_unit_expiry_idx ON blood_unit (expires_at) WHERE current_status = 'AVAILABLE';
CREATE INDEX audit_scope_time_idx ON audit_event (institution_id, occurred_at DESC);
CREATE INDEX audit_region_time_idx ON audit_event (region_name, occurred_at DESC);
CREATE INDEX web_session_account_idx ON web_session (account_id);
CREATE INDEX login_identity_time_idx ON login_attempt (identity_hash, occurred_at DESC);
CREATE INDEX login_address_time_idx ON login_attempt (address_hash, occurred_at DESC);

-- Caducidad derivada al consultar: no se guarda un estado temporal obsoleto.
CREATE VIEW blood_inventory AS
SELECT r.resource_id, r.traceability_code, u.component_id, c.component_code,
       c.component_name, u.location_id, l.location_code, l.location_description,
       s.site_id, s.site_name, i.institution_id, i.institution_code, i.institution_name,
       i.region_name, b.recorded_group_code, b.source_reference,
       u.collected_at, u.expires_at, u.current_status, u.version_no, u.registered_at,
       CASE WHEN u.current_status = 'WITHDRAWN' THEN 'WITHDRAWN'
            WHEN u.expires_at <= now() THEN 'EXPIRED'
            WHEN u.current_status = 'AVAILABLE' AND (i.participation_status <> 'ACTIVE'
                 OR s.site_status <> 'ACTIVE' OR NOT l.is_active OR NOT c.is_active) THEN 'UNAVAILABLE'
            ELSE u.current_status END AS effective_status,
       (u.current_status = 'AVAILABLE' AND u.expires_at > now()
        AND i.participation_status = 'ACTIVE' AND s.site_status = 'ACTIVE'
        AND l.is_active AND c.is_active) AS is_available
FROM blood_unit u JOIN resource r USING (resource_id)
JOIN blood_component c USING (component_id)
JOIN storage_location l USING (location_id) JOIN site s USING (site_id)
JOIN institution i USING (institution_id)
JOIN blood_classification b USING (resource_id);

-- Evidencia solo anexable desde el rol de aplicación, incluso ante un error de código.
CREATE FUNCTION reject_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Historical records are append-only' USING ERRCODE = '23514';
END;
$$;
CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE ON audit_event
FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER audit_change_append_only BEFORE UPDATE OR DELETE ON audit_change
FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER movement_append_only BEFORE UPDATE OR DELETE ON blood_movement
FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TRIGGER parameter_append_only BEFORE UPDATE OR DELETE ON parameter_version
FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();

INSERT INTO role VALUES
('ADMIN', 'Administrador', true), ('OPERATOR', 'Operador de banco de sangre', true),
('AUDITOR', 'Auditor', true), ('MEDICAL', 'Personal médico autorizado', false),
('COORDINATOR', 'Coordinador regional', false), ('TRANSPORT', 'Personal de traslado', false),
('DONOR', 'Donante', false);
INSERT INTO capability VALUES
('BLOOD_INVENTORY', 'Inventario sanguíneo DEMO'),
('LABORATORY', 'Laboratorio declarado (sin operación clínica)'),
('COORDINATION', 'Coordinación institucional');
INSERT INTO blood_status_transition (previous_status, new_status) VALUES
('AVAILABLE', 'QUARANTINED'), ('AVAILABLE', 'WITHDRAWN'),
('QUARANTINED', 'AVAILABLE'), ('QUARANTINED', 'WITHDRAWN');
-- El parámetro regional se crea durante la carga DEMO o al guardar configuración.
