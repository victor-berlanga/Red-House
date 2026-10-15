-- Red House: donantes; base de referencia: rh_donantes.
-- Migraciones aplicadas: 1, 2, 3, 4.
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
-- Name: appointments; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.appointments (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    donor_id uuid NOT NULL,
    campaign_id uuid NOT NULL,
    status text DEFAULT 'BOOKED'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: campaigns; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.campaigns (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    title text NOT NULL,
    starts_at timestamp with time zone NOT NULL,
    ends_at timestamp with time zone NOT NULL,
    capacity integer NOT NULL,
    status text DEFAULT 'OPEN'::text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    CONSTRAINT campaigns_capacity_check CHECK ((capacity > 0)),
    CONSTRAINT campaigns_check CHECK ((ends_at > starts_at))
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
-- Name: donation_steps; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.donation_steps (
    id uuid NOT NULL,
    donation_id uuid NOT NULL,
    state text NOT NULL,
    actor_id uuid NOT NULL,
    reason text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: donations; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.donations (
    id uuid NOT NULL,
    donor_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    kind text NOT NULL,
    component text NOT NULL,
    blood_group text NOT NULL,
    collected_at timestamp with time zone NOT NULL,
    status text DEFAULT 'COLLECTED'::text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT donations_kind_check CHECK ((kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text])))
);


--
-- Name: donor_reviews; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.donor_reviews (
    id uuid NOT NULL,
    donor_id uuid NOT NULL,
    decision text NOT NULL,
    reason text NOT NULL,
    actor_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: donors; Type: TABLE; Schema: api; Owner: -
--

CREATE TABLE api.donors (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    user_id uuid,
    folio text NOT NULL,
    display_name text NOT NULL,
    blood_group text NOT NULL,
    consent boolean NOT NULL,
    status text DEFAULT 'PRELIMINARY'::text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    restrictions text,
    background text,
    donation_kind text,
    consent_reference text,
    consent_at text,
    CONSTRAINT donors_consent_check CHECK (consent),
    CONSTRAINT donors_donation_kind_check CHECK ((donation_kind = ANY (ARRAY['VOLUNTARY'::text, 'REPLACEMENT'::text])))
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
-- Name: appointments appointments_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.appointments
    ADD CONSTRAINT appointments_pkey PRIMARY KEY (id);


--
-- Name: campaigns campaigns_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.campaigns
    ADD CONSTRAINT campaigns_pkey PRIMARY KEY (id);


--
-- Name: decisions decisions_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.decisions
    ADD CONSTRAINT decisions_pkey PRIMARY KEY (id);


--
-- Name: donation_steps donation_steps_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.donation_steps
    ADD CONSTRAINT donation_steps_pkey PRIMARY KEY (id);


--
-- Name: donations donations_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.donations
    ADD CONSTRAINT donations_pkey PRIMARY KEY (id);


--
-- Name: donor_reviews donor_reviews_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.donor_reviews
    ADD CONSTRAINT donor_reviews_pkey PRIMARY KEY (id);


--
-- Name: donors donors_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.donors
    ADD CONSTRAINT donors_pkey PRIMARY KEY (id);


--
-- Name: donors donors_tenant_id_folio_key; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.donors
    ADD CONSTRAINT donors_tenant_id_folio_key UNIQUE (tenant_id, folio);


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
-- Name: worker_health worker_health_pkey; Type: CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.worker_health
    ADD CONSTRAINT worker_health_pkey PRIMARY KEY (id);


--
-- Name: active_appointment; Type: INDEX; Schema: api; Owner: -
--

CREATE UNIQUE INDEX active_appointment ON api.appointments USING btree (donor_id, campaign_id) WHERE (status = 'BOOKED'::text);


--
-- Name: decisions_resource; Type: INDEX; Schema: api; Owner: -
--

CREATE INDEX decisions_resource ON api.decisions USING btree (resource_id, created_at);


--
-- Name: donor_account; Type: INDEX; Schema: api; Owner: -
--

CREATE UNIQUE INDEX donor_account ON api.donors USING btree (user_id) WHERE (user_id IS NOT NULL);


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
-- Name: appointments appointments_campaign_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.appointments
    ADD CONSTRAINT appointments_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES api.campaigns(id);


--
-- Name: appointments appointments_donor_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.appointments
    ADD CONSTRAINT appointments_donor_id_fkey FOREIGN KEY (donor_id) REFERENCES api.donors(id);


--
-- Name: donation_steps donation_steps_donation_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.donation_steps
    ADD CONSTRAINT donation_steps_donation_id_fkey FOREIGN KEY (donation_id) REFERENCES api.donations(id);


--
-- Name: donations donations_donor_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.donations
    ADD CONSTRAINT donations_donor_id_fkey FOREIGN KEY (donor_id) REFERENCES api.donors(id);


--
-- Name: donor_reviews donor_reviews_donor_id_fkey; Type: FK CONSTRAINT; Schema: api; Owner: -
--

ALTER TABLE ONLY api.donor_reviews
    ADD CONSTRAINT donor_reviews_donor_id_fkey FOREIGN KEY (donor_id) REFERENCES api.donors(id);


--
-- PostgreSQL database dump complete
--
