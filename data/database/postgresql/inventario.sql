-- Red House: inventario; base de referencia: rh_inventario.
-- Migraciones aplicadas: 1, 2, 3, 4, 5.
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
-- Name: bump_read_cache(); Type: FUNCTION; Schema: api; Owner: -
--

CREATE FUNCTION api.bump_read_cache() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
 UPDATE cache_revision SET revision=revision+1 WHERE name='inventory';
 RETURN NULL;
END; $$;


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
-- Name: cache_revision; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.cache_revision (
    name text NOT NULL,
    revision bigint DEFAULT 0 NOT NULL
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
-- Name: movements; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.movements (
    id uuid NOT NULL,
    resource_id uuid NOT NULL,
    action text NOT NULL,
    actor_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: operations; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.operations (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    key text NOT NULL,
    fingerprint text NOT NULL,
    input jsonb NOT NULL,
    status text DEFAULT 'PENDING'::text NOT NULL,
    hold_id uuid,
    error text,
    last_recovery_at timestamp with time zone,
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
-- Name: reservations; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.reservations (
    id uuid NOT NULL,
    operation_id uuid NOT NULL,
    resource_id uuid NOT NULL,
    request_id uuid NOT NULL,
    recipient_id uuid NOT NULL,
    origin_id uuid NOT NULL,
    destination_id uuid NOT NULL,
    region_id uuid NOT NULL,
    hold_id uuid NOT NULL,
    evaluation_id uuid NOT NULL,
    route_id uuid NOT NULL,
    route_version integer NOT NULL,
    status text DEFAULT 'PENDING'::text NOT NULL,
    shipment_id uuid,
    shipment_sequence integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: resource_reviews; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.resource_reviews (
    id uuid NOT NULL,
    resource_id uuid NOT NULL,
    actor_id uuid NOT NULL,
    decision text NOT NULL,
    reason text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: resources; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.resources (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    region_id uuid NOT NULL,
    folio text NOT NULL,
    current_institution_id uuid NOT NULL,
    donation_id uuid,
    kind text NOT NULL,
    component text NOT NULL,
    blood_group text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    status text DEFAULT 'QUARANTINE'::text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    location_id uuid,
    collected_at timestamp with time zone,
    CONSTRAINT resources_kind_check CHECK ((kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text])))
);


--
-- Name: schema_version; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.schema_version (
    version integer NOT NULL,
    installed_at timestamp with time zone DEFAULT now() NOT NULL
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
-- Name: cache_revision cache_revision_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.cache_revision
    ADD CONSTRAINT cache_revision_pkey PRIMARY KEY (name);


--
-- Name: decisions decisions_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.decisions
    ADD CONSTRAINT decisions_pkey PRIMARY KEY (id);


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
-- Name: movements movements_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.movements
    ADD CONSTRAINT movements_pkey PRIMARY KEY (id);


--
-- Name: operations operations_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.operations
    ADD CONSTRAINT operations_pkey PRIMARY KEY (id);


--
-- Name: operations operations_user_id_key_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.operations
    ADD CONSTRAINT operations_user_id_key_key UNIQUE (user_id, key);


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
-- Name: reservations reservations_hold_id_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.reservations
    ADD CONSTRAINT reservations_hold_id_key UNIQUE (hold_id);


--
-- Name: reservations reservations_operation_id_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.reservations
    ADD CONSTRAINT reservations_operation_id_key UNIQUE (operation_id);


--
-- Name: reservations reservations_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.reservations
    ADD CONSTRAINT reservations_pkey PRIMARY KEY (id);


--
-- Name: resource_reviews resource_reviews_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.resource_reviews
    ADD CONSTRAINT resource_reviews_pkey PRIMARY KEY (id);


--
-- Name: resources resources_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.resources
    ADD CONSTRAINT resources_pkey PRIMARY KEY (id);


--
-- Name: resources resources_tenant_id_folio_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.resources
    ADD CONSTRAINT resources_tenant_id_folio_key UNIQUE (tenant_id, folio);


--
-- Name: schema_version schema_version_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.schema_version
    ADD CONSTRAINT schema_version_pkey PRIMARY KEY (version);


--
-- Name: worker_health worker_health_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.worker_health
    ADD CONSTRAINT worker_health_pkey PRIMARY KEY (id);


--
-- Name: availability_page; Type: INDEX; Schema: api; Owner: -
--

CREATE INDEX availability_page ON api.resources USING btree (region_id, expires_at, id) WHERE (status = 'AVAILABLE'::text);


--
-- Name: available_resources; Type: INDEX; Schema: api; Owner: -
--

CREATE INDEX available_resources ON api.resources USING btree (region_id, kind, component, expires_at) WHERE (status = 'AVAILABLE'::text);


--
-- Name: decisions_resource; Type: INDEX; Schema: api; Owner: -
--

CREATE INDEX decisions_resource ON api.decisions USING btree (resource_id, created_at);


--
-- Name: outbox_pending; Type: INDEX; Schema: api; Owner: -
--

CREATE INDEX outbox_pending ON api.outbox USING btree (next_attempt, created_at) WHERE (delivered_at IS NULL);


--
-- Name: resource_reserved; Type: INDEX; Schema: api; Owner: -
--

CREATE UNIQUE INDEX resource_reserved ON api.reservations USING btree (resource_id) WHERE (status <> 'CANCELLED'::text);


--
-- Name: activity_events activity_immutable; Type: TRIGGER; Schema: api; Owner: -
--

CREATE TRIGGER activity_immutable BEFORE DELETE OR UPDATE ON api.activity_events FOR EACH ROW EXECUTE FUNCTION api.reject_history_mutation();


--
-- Name: decisions decisions_immutable; Type: TRIGGER; Schema: api; Owner: -
--

CREATE TRIGGER decisions_immutable BEFORE DELETE OR UPDATE ON api.decisions FOR EACH ROW EXECUTE FUNCTION api.reject_history_mutation();


--
-- Name: movements movements_immutable; Type: TRIGGER; Schema: api; Owner: -
--

CREATE TRIGGER movements_immutable BEFORE DELETE OR UPDATE ON api.movements FOR EACH ROW EXECUTE FUNCTION api.reject_history_mutation();


--
-- Name: resources resources_cache; Type: TRIGGER; Schema: api; Owner: -
--

CREATE TRIGGER resources_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON api.resources FOR EACH STATEMENT EXECUTE FUNCTION api.bump_read_cache();


--
-- Name: movements movements_resource_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.movements
    ADD CONSTRAINT movements_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES api.resources(id);


--
-- Name: reservations reservations_operation_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.reservations
    ADD CONSTRAINT reservations_operation_id_fkey FOREIGN KEY (operation_id) REFERENCES api.operations(id);


--
-- Name: reservations reservations_resource_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.reservations
    ADD CONSTRAINT reservations_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES api.resources(id);


--
-- Name: resource_reviews resource_reviews_resource_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.resource_reviews
    ADD CONSTRAINT resource_reviews_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES api.resources(id);


--
-- PostgreSQL database dump complete
--
