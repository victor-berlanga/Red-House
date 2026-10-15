-- Red House: transporte; base de referencia: rh_transporte.
-- Migraciones aplicadas: 1, 2.
-- Generado por scripts/export_schemas.py; no editar manualmente.
-- Solo estructura; sin registros, roles, permisos ni marcas de migración.
-- Para consulta/restauración estructural en una base vacía, no para actualizar el entorno.

--
-- PostgreSQL database dump
--



SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: api; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA api;


--
-- Name: reject_history_mutation(); Type: FUNCTION; Schema: api; Owner: -
--

CREATE FUNCTION api.reject_history_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN RAISE EXCEPTION 'Immutable history'; END $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: activity_events; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.activity_events (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    event jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: decisions; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.decisions (
    id uuid NOT NULL,
    resource_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    actor_id uuid NOT NULL,
    action text NOT NULL,
    reason text NOT NULL,
    changes jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: files; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.files (
    id uuid NOT NULL,
    shipment_id uuid NOT NULL,
    owner_id uuid NOT NULL,
    object_path text NOT NULL,
    mime_type text NOT NULL,
    size integer NOT NULL,
    sha256 text NOT NULL,
    status text DEFAULT 'PENDING'::text NOT NULL,
    generation text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT files_size_check CHECK (((size >= 1) AND (size <= 10485760)))
);


--
-- Name: idempotency; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.idempotency (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    key text NOT NULL,
    operation text NOT NULL,
    fingerprint text NOT NULL,
    result jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: inbox; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.inbox (
    event_id uuid NOT NULL,
    fingerprint text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: outbox; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.outbox (
    id uuid NOT NULL,
    event_id uuid NOT NULL,
    target text NOT NULL,
    event jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    delivered_at timestamp with time zone,
    attempts integer DEFAULT 0 NOT NULL,
    next_attempt timestamp with time zone DEFAULT now() NOT NULL,
    last_error text
);


--
-- Name: schema_version; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.schema_version (
    version integer NOT NULL,
    installed_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: shipments; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.shipments (
    id uuid NOT NULL,
    reservation_id uuid NOT NULL,
    origin_id uuid NOT NULL,
    destination_id uuid NOT NULL,
    region_id uuid NOT NULL,
    transport_user_id uuid NOT NULL,
    departure_at timestamp with time zone NOT NULL,
    eta timestamp with time zone NOT NULL,
    status text DEFAULT 'PLANNED'::text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    sequence integer DEFAULT 0 NOT NULL,
    inventory_pending boolean DEFAULT true NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    CONSTRAINT shipments_check CHECK ((eta > departure_at)),
    CONSTRAINT shipments_check1 CHECK ((eta < expires_at))
);


--
-- Name: telemetry; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.telemetry (
    id uuid NOT NULL,
    shipment_id uuid NOT NULL,
    actor_id uuid NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    captured_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: transitions; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.transitions (
    id uuid NOT NULL,
    shipment_id uuid NOT NULL,
    sequence integer NOT NULL,
    state text NOT NULL,
    actor_id uuid NOT NULL,
    reason text NOT NULL,
    evidence jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: worker_health; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.worker_health (
    id integer NOT NULL,
    checked_at timestamp with time zone NOT NULL,
    last_success timestamp with time zone,
    last_error text,
    CONSTRAINT worker_health_id_check CHECK ((id = 1))
);


--
-- Name: activity_events activity_events_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.activity_events
    ADD CONSTRAINT activity_events_pkey PRIMARY KEY (id);


--
-- Name: decisions decisions_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.decisions
    ADD CONSTRAINT decisions_pkey PRIMARY KEY (id);


--
-- Name: files files_object_path_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.files
    ADD CONSTRAINT files_object_path_key UNIQUE (object_path);


--
-- Name: files files_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);


--
-- Name: idempotency idempotency_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.idempotency
    ADD CONSTRAINT idempotency_pkey PRIMARY KEY (id);


--
-- Name: idempotency idempotency_user_id_key_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.idempotency
    ADD CONSTRAINT idempotency_user_id_key_key UNIQUE (user_id, key);


--
-- Name: inbox inbox_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.inbox
    ADD CONSTRAINT inbox_pkey PRIMARY KEY (event_id);


--
-- Name: outbox outbox_event_id_target_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.outbox
    ADD CONSTRAINT outbox_event_id_target_key UNIQUE (event_id, target);


--
-- Name: outbox outbox_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.outbox
    ADD CONSTRAINT outbox_pkey PRIMARY KEY (id);


--
-- Name: schema_version schema_version_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.schema_version
    ADD CONSTRAINT schema_version_pkey PRIMARY KEY (version);


--
-- Name: shipments shipments_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.shipments
    ADD CONSTRAINT shipments_pkey PRIMARY KEY (id);


--
-- Name: shipments shipments_reservation_id_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.shipments
    ADD CONSTRAINT shipments_reservation_id_key UNIQUE (reservation_id);


--
-- Name: telemetry telemetry_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.telemetry
    ADD CONSTRAINT telemetry_pkey PRIMARY KEY (id);


--
-- Name: transitions transitions_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.transitions
    ADD CONSTRAINT transitions_pkey PRIMARY KEY (id);


--
-- Name: transitions transitions_shipment_id_sequence_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.transitions
    ADD CONSTRAINT transitions_shipment_id_sequence_key UNIQUE (shipment_id, sequence);


--
-- Name: worker_health worker_health_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.worker_health
    ADD CONSTRAINT worker_health_pkey PRIMARY KEY (id);


--
-- Name: decisions_resource; Type: INDEX; Schema: api; Owner: -
--

CREATE INDEX decisions_resource ON api.decisions USING btree (resource_id, created_at);


--
-- Name: outbox_pending; Type: INDEX; Schema: api; Owner: -
--

CREATE INDEX outbox_pending ON api.outbox USING btree (next_attempt, created_at) WHERE (delivered_at IS NULL);


--
-- Name: activity_events activity_immutable; Type: TRIGGER; Schema: api; Owner: -
--

CREATE TRIGGER activity_immutable BEFORE DELETE OR UPDATE ON api.activity_events FOR EACH ROW EXECUTE FUNCTION api.reject_history_mutation();


--
-- Name: decisions decisions_immutable; Type: TRIGGER; Schema: api; Owner: -
--

CREATE TRIGGER decisions_immutable BEFORE DELETE OR UPDATE ON api.decisions FOR EACH ROW EXECUTE FUNCTION api.reject_history_mutation();


--
-- Name: transitions transitions_immutable; Type: TRIGGER; Schema: api; Owner: -
--

CREATE TRIGGER transitions_immutable BEFORE DELETE OR UPDATE ON api.transitions FOR EACH ROW EXECUTE FUNCTION api.reject_history_mutation();


--
-- Name: files files_shipment_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.files
    ADD CONSTRAINT files_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES api.shipments(id);


--
-- Name: telemetry telemetry_shipment_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.telemetry
    ADD CONSTRAINT telemetry_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES api.shipments(id);


--
-- Name: transitions transitions_shipment_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.transitions
    ADD CONSTRAINT transitions_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES api.shipments(id);


--
-- PostgreSQL database dump complete
--
