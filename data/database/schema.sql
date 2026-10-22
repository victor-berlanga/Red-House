-- Red House: base única compartida; PostgreSQL 14+.
-- Base: main 44eeaf90c445b4d9564c2f0ab2dd3167f0296418, esquema inicial y migraciones 002–004.
-- Generado con scripts/build_shared_schema.py, shared/005_services.sql y redhouse/shared_schema.py.
-- Instalación estructural en una base VACÍA. No migra datos de las once bases actuales.
-- Incluye catálogos, no cuentas, credenciales ni datos clínicos.
BEGIN;
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
-- Name: access_alertas; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_alertas;


--
-- Name: access_auditoria; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_auditoria;


--
-- Name: access_compatibilidad; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_compatibilidad;


--
-- Name: access_custodia; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_custodia;


--
-- Name: access_donantes; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_donantes;


--
-- Name: access_identidad_acceso; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_identidad_acceso;


--
-- Name: access_inventario; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_inventario;


--
-- Name: access_monitoreo; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_monitoreo;


--
-- Name: access_priorizacion_geografia; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_priorizacion_geografia;


--
-- Name: access_receptores; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_receptores;


--
-- Name: access_transporte; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA access_transporte;


--
-- Name: red_house; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA red_house;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_alertas; Owner: -
--

CREATE FUNCTION access_alertas.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('alertas',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_alertas; Owner: -
--

CREATE FUNCTION access_alertas.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('alertas',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_alertas; Owner: -
--

CREATE FUNCTION access_alertas.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('alertas',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_alertas; Owner: -
--

CREATE FUNCTION access_alertas.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('alertas',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_alertas; Owner: -
--

CREATE FUNCTION access_alertas.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('alertas',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_alertas; Owner: -
--

CREATE FUNCTION access_alertas.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('alertas',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_alertas; Owner: -
--

CREATE FUNCTION access_alertas.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('alertas',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: event_time(text); Type: FUNCTION; Schema: access_auditoria; Owner: -
--

CREATE FUNCTION access_auditoria.event_time(value text) RETURNS timestamp with time zone
    LANGUAGE plpgsql IMMUTABLE STRICT
    SET search_path TO 'pg_catalog'
    AS $_$
BEGIN
 IF value !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*(Z|[+-][0-9]{2}:[0-9]{2})$' THEN RETURN NULL; END IF;
 RETURN value::timestamptz;
EXCEPTION WHEN invalid_datetime_format OR datetime_field_overflow THEN RETURN NULL;
END $_$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_auditoria; Owner: -
--

CREATE FUNCTION access_auditoria.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('auditoria',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_auditoria; Owner: -
--

CREATE FUNCTION access_auditoria.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('auditoria',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_auditoria; Owner: -
--

CREATE FUNCTION access_auditoria.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('auditoria',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_auditoria; Owner: -
--

CREATE FUNCTION access_auditoria.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('auditoria',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_auditoria; Owner: -
--

CREATE FUNCTION access_auditoria.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('auditoria',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_auditoria; Owner: -
--

CREATE FUNCTION access_auditoria.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('auditoria',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_auditoria; Owner: -
--

CREATE FUNCTION access_auditoria.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('auditoria',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_compatibilidad; Owner: -
--

CREATE FUNCTION access_compatibilidad.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('compatibilidad',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_compatibilidad; Owner: -
--

CREATE FUNCTION access_compatibilidad.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('compatibilidad',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_compatibilidad; Owner: -
--

CREATE FUNCTION access_compatibilidad.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('compatibilidad',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_compatibilidad; Owner: -
--

CREATE FUNCTION access_compatibilidad.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('compatibilidad',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_compatibilidad; Owner: -
--

CREATE FUNCTION access_compatibilidad.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('compatibilidad',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_compatibilidad; Owner: -
--

CREATE FUNCTION access_compatibilidad.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('compatibilidad',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_compatibilidad; Owner: -
--

CREATE FUNCTION access_compatibilidad.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('compatibilidad',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_custodia; Owner: -
--

CREATE FUNCTION access_custodia.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('custodia',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_custodia; Owner: -
--

CREATE FUNCTION access_custodia.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('custodia',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_custodia; Owner: -
--

CREATE FUNCTION access_custodia.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('custodia',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_custodia; Owner: -
--

CREATE FUNCTION access_custodia.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('custodia',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_custodia; Owner: -
--

CREATE FUNCTION access_custodia.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('custodia',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_custodia; Owner: -
--

CREATE FUNCTION access_custodia.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('custodia',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_custodia; Owner: -
--

CREATE FUNCTION access_custodia.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('custodia',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_donantes; Owner: -
--

CREATE FUNCTION access_donantes.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('donantes',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_donantes; Owner: -
--

CREATE FUNCTION access_donantes.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('donantes',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_donantes; Owner: -
--

CREATE FUNCTION access_donantes.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('donantes',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_donantes; Owner: -
--

CREATE FUNCTION access_donantes.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('donantes',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_donantes; Owner: -
--

CREATE FUNCTION access_donantes.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('donantes',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_donantes; Owner: -
--

CREATE FUNCTION access_donantes.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('donantes',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_donantes; Owner: -
--

CREATE FUNCTION access_donantes.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('donantes',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_identidad_acceso; Owner: -
--

CREATE FUNCTION access_identidad_acceso.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('identidad_acceso',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_identidad_acceso; Owner: -
--

CREATE FUNCTION access_identidad_acceso.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('identidad_acceso',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_identidad_acceso; Owner: -
--

CREATE FUNCTION access_identidad_acceso.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('identidad_acceso',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_identidad_acceso; Owner: -
--

CREATE FUNCTION access_identidad_acceso.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('identidad_acceso',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_identidad_acceso; Owner: -
--

CREATE FUNCTION access_identidad_acceso.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('identidad_acceso',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_identidad_acceso; Owner: -
--

CREATE FUNCTION access_identidad_acceso.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('identidad_acceso',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_identidad_acceso; Owner: -
--

CREATE FUNCTION access_identidad_acceso.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('identidad_acceso',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_inventario; Owner: -
--

CREATE FUNCTION access_inventario.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('inventario',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_inventario; Owner: -
--

CREATE FUNCTION access_inventario.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('inventario',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_inventario; Owner: -
--

CREATE FUNCTION access_inventario.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('inventario',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_inventario; Owner: -
--

CREATE FUNCTION access_inventario.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('inventario',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_inventario; Owner: -
--

CREATE FUNCTION access_inventario.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('inventario',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_inventario; Owner: -
--

CREATE FUNCTION access_inventario.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('inventario',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_inventario; Owner: -
--

CREATE FUNCTION access_inventario.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('inventario',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_monitoreo; Owner: -
--

CREATE FUNCTION access_monitoreo.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('monitoreo',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_monitoreo; Owner: -
--

CREATE FUNCTION access_monitoreo.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('monitoreo',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_monitoreo; Owner: -
--

CREATE FUNCTION access_monitoreo.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('monitoreo',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_monitoreo; Owner: -
--

CREATE FUNCTION access_monitoreo.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('monitoreo',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_monitoreo; Owner: -
--

CREATE FUNCTION access_monitoreo.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('monitoreo',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_monitoreo; Owner: -
--

CREATE FUNCTION access_monitoreo.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('monitoreo',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_monitoreo; Owner: -
--

CREATE FUNCTION access_monitoreo.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('monitoreo',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_priorizacion_geografia; Owner: -
--

CREATE FUNCTION access_priorizacion_geografia.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('priorizacion_geografia',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_priorizacion_geografia; Owner: -
--

CREATE FUNCTION access_priorizacion_geografia.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('priorizacion_geografia',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_priorizacion_geografia; Owner: -
--

CREATE FUNCTION access_priorizacion_geografia.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('priorizacion_geografia',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_priorizacion_geografia; Owner: -
--

CREATE FUNCTION access_priorizacion_geografia.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('priorizacion_geografia',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_priorizacion_geografia; Owner: -
--

CREATE FUNCTION access_priorizacion_geografia.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('priorizacion_geografia',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_priorizacion_geografia; Owner: -
--

CREATE FUNCTION access_priorizacion_geografia.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('priorizacion_geografia',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_priorizacion_geografia; Owner: -
--

CREATE FUNCTION access_priorizacion_geografia.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('priorizacion_geografia',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_receptores; Owner: -
--

CREATE FUNCTION access_receptores.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('receptores',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_receptores; Owner: -
--

CREATE FUNCTION access_receptores.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('receptores',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_receptores; Owner: -
--

CREATE FUNCTION access_receptores.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('receptores',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_receptores; Owner: -
--

CREATE FUNCTION access_receptores.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('receptores',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_receptores; Owner: -
--

CREATE FUNCTION access_receptores.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('receptores',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_receptores; Owner: -
--

CREATE FUNCTION access_receptores.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('receptores',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_receptores; Owner: -
--

CREATE FUNCTION access_receptores.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('receptores',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_activity_events(); Type: FUNCTION; Schema: access_transporte; Owner: -
--

CREATE FUNCTION access_transporte.insert_activity_events() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_activity_events"(service,"id", "tenant_id", "event", "created_at") VALUES ('transporte',NEW."id", NEW."tenant_id", NEW."event", NEW."created_at") RETURNING "id", "tenant_id", "event", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_decisions(); Type: FUNCTION; Schema: access_transporte; Owner: -
--

CREATE FUNCTION access_transporte.insert_decisions() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_decisions"(service,"id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at") VALUES ('transporte',NEW."id", NEW."resource_id", NEW."tenant_id", NEW."actor_id", NEW."action", NEW."reason", NEW."changes", NEW."created_at") RETURNING "id", "resource_id", "tenant_id", "actor_id", "action", "reason", "changes", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_idempotency(); Type: FUNCTION; Schema: access_transporte; Owner: -
--

CREATE FUNCTION access_transporte.insert_idempotency() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_idempotency"(service,"id", "user_id", "key", "operation", "fingerprint", "result", "created_at") VALUES ('transporte',NEW."id", NEW."user_id", NEW."key", NEW."operation", NEW."fingerprint", NEW."result", NEW."created_at") RETURNING "id", "user_id", "key", "operation", "fingerprint", "result", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_inbox(); Type: FUNCTION; Schema: access_transporte; Owner: -
--

CREATE FUNCTION access_transporte.insert_inbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_inbox"(service,"event_id", "fingerprint", "created_at") VALUES ('transporte',NEW."event_id", NEW."fingerprint", NEW."created_at") RETURNING "event_id", "fingerprint", "created_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_outbox(); Type: FUNCTION; Schema: access_transporte; Owner: -
--

CREATE FUNCTION access_transporte.insert_outbox() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_outbox"(service,"id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error") VALUES ('transporte',NEW."id", NEW."event_id", NEW."target", NEW."event", NEW."created_at", NEW."delivered_at", NEW."attempts", NEW."next_attempt", NEW."last_error") RETURNING "id", "event_id", "target", "event", "created_at", "delivered_at", "attempts", "next_attempt", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_schema_version(); Type: FUNCTION; Schema: access_transporte; Owner: -
--

CREATE FUNCTION access_transporte.insert_schema_version() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_schema_version"(service,"version", "installed_at") VALUES ('transporte',NEW."version", NEW."installed_at") RETURNING "version", "installed_at" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: insert_worker_health(); Type: FUNCTION; Schema: access_transporte; Owner: -
--

CREATE FUNCTION access_transporte.insert_worker_health() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
                  DECLARE stored record; BEGIN
                    INSERT INTO red_house."service_worker_health"(service,"id", "checked_at", "last_success", "last_error") VALUES ('transporte',NEW."id", NEW."checked_at", NEW."last_success", NEW."last_error") RETURNING "id", "checked_at", "last_success", "last_error" INTO stored;
                    NEW:=stored; RETURN NEW;
                  END $$;


--
-- Name: bump_inventory_cache(); Type: FUNCTION; Schema: red_house; Owner: -
--

CREATE FUNCTION red_house.bump_inventory_cache() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
        BEGIN UPDATE red_house.cache_revision SET revision=revision+1 WHERE name='inventory'; RETURN NULL; END $$;


--
-- Name: bump_read_cache(); Type: FUNCTION; Schema: red_house; Owner: -
--

CREATE FUNCTION red_house.bump_read_cache() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
BEGIN
    UPDATE red_house.cache_revision SET revision=revision+1 WHERE name='catalogues';
    RETURN NULL;
END; $$;


--
-- Name: reject_history_mutation(); Type: FUNCTION; Schema: red_house; Owner: -
--

CREATE FUNCTION red_house.reject_history_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'Historical records are append-only' USING ERRCODE = '23514';
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: service_activity_events; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.service_activity_events (
    service text NOT NULL,
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    event jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: activity_events; Type: VIEW; Schema: access_alertas; Owner: -
--

CREATE VIEW access_alertas.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'alertas'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: notification; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.notification (
    notification_id uuid NOT NULL,
    event_id uuid NOT NULL,
    institution_id uuid NOT NULL,
    target_role text NOT NULL,
    target_account_id uuid,
    message_code text NOT NULL,
    entity_reference text NOT NULL,
    current_status text DEFAULT 'OPEN'::text NOT NULL,
    acknowledged_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    region_id uuid NOT NULL
);


--
-- Name: alerts; Type: VIEW; Schema: access_alertas; Owner: -
--

CREATE VIEW access_alertas.alerts AS
 SELECT notification.notification_id AS id,
    notification.event_id,
    notification.institution_id AS tenant_id,
    notification.region_id,
    notification.target_role,
    notification.target_account_id AS target_user_id,
    notification.message_code,
    notification.entity_reference AS resource_id,
    notification.current_status AS status,
    notification.acknowledged_by,
    notification.created_at
   FROM red_house.notification;


--
-- Name: service_decisions; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.service_decisions (
    service text NOT NULL,
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
-- Name: decisions; Type: VIEW; Schema: access_alertas; Owner: -
--

CREATE VIEW access_alertas.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'alertas'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: service_idempotency; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.service_idempotency (
    service text NOT NULL,
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    key text NOT NULL,
    operation text NOT NULL,
    fingerprint text NOT NULL,
    result jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: idempotency; Type: VIEW; Schema: access_alertas; Owner: -
--

CREATE VIEW access_alertas.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'alertas'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: service_inbox; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.service_inbox (
    service text NOT NULL,
    event_id uuid NOT NULL,
    fingerprint text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: inbox; Type: VIEW; Schema: access_alertas; Owner: -
--

CREATE VIEW access_alertas.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'alertas'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: service_outbox; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.service_outbox (
    service text NOT NULL,
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
-- Name: outbox; Type: VIEW; Schema: access_alertas; Owner: -
--

CREATE VIEW access_alertas.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'alertas'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: service_schema_version; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.service_schema_version (
    service text NOT NULL,
    version integer NOT NULL,
    installed_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: schema_version; Type: VIEW; Schema: access_alertas; Owner: -
--

CREATE VIEW access_alertas.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'alertas'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: service_worker_health; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.service_worker_health (
    service text NOT NULL,
    id integer NOT NULL,
    checked_at timestamp with time zone NOT NULL,
    last_success timestamp with time zone,
    last_error text,
    CONSTRAINT service_worker_health_id_check CHECK ((id = 1))
);


--
-- Name: worker_health; Type: VIEW; Schema: access_alertas; Owner: -
--

CREATE VIEW access_alertas.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'alertas'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'auditoria'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: audit_event; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.audit_event (
    event_id uuid NOT NULL,
    actor_id uuid,
    institution_id uuid NOT NULL,
    region_name character varying(80),
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    action text NOT NULL,
    entity_type character varying(40),
    entity_reference character varying(80),
    outcome character varying(12),
    correlation_id uuid,
    reason character varying(240),
    source_service text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    region_id uuid NOT NULL,
    event jsonb NOT NULL,
    CONSTRAINT audit_event_outcome_check CHECK (((outcome)::text = ANY (ARRAY[('SUCCESS'::character varying)::text, ('DENIED'::character varying)::text, ('FAILED'::character varying)::text])))
);


--
-- Name: audit_events; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.audit_events AS
 SELECT audit_event.event_id AS id,
    audit_event.institution_id AS tenant_id,
    audit_event.region_id,
    audit_event.source_service AS source,
    audit_event.action,
    audit_event.actor_id,
    audit_event.event,
    audit_event.occurred_at AS created_at
   FROM red_house.audit_event;


--
-- Name: audit_finding_actions; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.audit_finding_actions (
    id uuid NOT NULL,
    finding_id uuid NOT NULL,
    actor_id uuid NOT NULL,
    actor_name text NOT NULL,
    actor_role text NOT NULL,
    previous_status text,
    status text NOT NULL,
    reason text NOT NULL,
    corrective_action text,
    evidence text,
    correlation_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT api_audit_finding_actions_corrective_action_check CHECK (((corrective_action IS NULL) OR ((length(corrective_action) >= 6) AND (length(corrective_action) <= 1000)))),
    CONSTRAINT api_audit_finding_actions_evidence_check CHECK (((evidence IS NULL) OR ((length(evidence) >= 6) AND (length(evidence) <= 1000)))),
    CONSTRAINT api_audit_finding_actions_reason_check CHECK (((length(reason) >= 6) AND (length(reason) <= 1000)))
);


--
-- Name: audit_finding_actions; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.audit_finding_actions AS
 SELECT audit_finding_actions.id,
    audit_finding_actions.finding_id,
    audit_finding_actions.actor_id,
    audit_finding_actions.actor_name,
    audit_finding_actions.actor_role,
    audit_finding_actions.previous_status,
    audit_finding_actions.status,
    audit_finding_actions.reason,
    audit_finding_actions.corrective_action,
    audit_finding_actions.evidence,
    audit_finding_actions.correlation_id,
    audit_finding_actions.created_at
   FROM red_house.audit_finding_actions;


--
-- Name: audit_finding_links; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.audit_finding_links (
    id uuid NOT NULL,
    finding_id uuid NOT NULL,
    event_id uuid NOT NULL
);


--
-- Name: audit_finding_links; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.audit_finding_links AS
 SELECT audit_finding_links.id,
    audit_finding_links.finding_id,
    audit_finding_links.event_id
   FROM red_house.audit_finding_links;


--
-- Name: audit_findings; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.audit_findings (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    region_id uuid NOT NULL,
    description text NOT NULL,
    priority text NOT NULL,
    assignee_id uuid NOT NULL,
    assignee_tenant_id uuid NOT NULL,
    assignee_name text NOT NULL,
    created_by uuid NOT NULL,
    resource_id uuid,
    evidence text,
    status text DEFAULT 'OPEN'::text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT api_audit_findings_description_check CHECK (((length(description) >= 6) AND (length(description) <= 1000))),
    CONSTRAINT api_audit_findings_evidence_check CHECK (((evidence IS NULL) OR ((length(evidence) >= 6) AND (length(evidence) <= 1000)))),
    CONSTRAINT api_audit_findings_priority_check CHECK ((priority = ANY (ARRAY['LOW'::text, 'MEDIUM'::text, 'HIGH'::text, 'CRITICAL'::text]))),
    CONSTRAINT api_audit_findings_status_check CHECK ((status = ANY (ARRAY['OPEN'::text, 'IN_PROGRESS'::text, 'PENDING_VERIFICATION'::text, 'CLOSED'::text]))),
    CONSTRAINT api_audit_findings_version_check CHECK ((version > 0))
);


--
-- Name: audit_findings; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.audit_findings AS
 SELECT audit_findings.id,
    audit_findings.tenant_id,
    audit_findings.region_id,
    audit_findings.description,
    audit_findings.priority,
    audit_findings.assignee_id,
    audit_findings.assignee_tenant_id,
    audit_findings.assignee_name,
    audit_findings.created_by,
    audit_findings.resource_id,
    audit_findings.evidence,
    audit_findings.status,
    audit_findings.version,
    audit_findings.created_at,
    audit_findings.updated_at
   FROM red_house.audit_findings;


--
-- Name: decisions; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'auditoria'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: idempotency; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'auditoria'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'auditoria'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: outbox; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'auditoria'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: schema_version; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'auditoria'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: worker_health; Type: VIEW; Schema: access_auditoria; Owner: -
--

CREATE VIEW access_auditoria.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'auditoria'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_compatibilidad; Owner: -
--

CREATE VIEW access_compatibilidad.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'compatibilidad'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: decisions; Type: VIEW; Schema: access_compatibilidad; Owner: -
--

CREATE VIEW access_compatibilidad.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'compatibilidad'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: candidate_evaluation; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.candidate_evaluation (
    evaluation_id uuid NOT NULL,
    request_id uuid NOT NULL,
    algorithm_version text NOT NULL,
    request_version integer NOT NULL,
    recipient_version integer NOT NULL,
    actor_id uuid,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    elapsed_ms double precision NOT NULL,
    tenant_id uuid NOT NULL,
    kind text NOT NULL,
    snapshot jsonb NOT NULL,
    candidates jsonb NOT NULL
);


--
-- Name: evaluations; Type: VIEW; Schema: access_compatibilidad; Owner: -
--

CREATE VIEW access_compatibilidad.evaluations AS
 SELECT candidate_evaluation.evaluation_id AS id,
    candidate_evaluation.tenant_id,
    candidate_evaluation.request_id,
    candidate_evaluation.request_version,
    candidate_evaluation.recipient_version,
    candidate_evaluation.kind,
    candidate_evaluation.algorithm_version,
    candidate_evaluation.snapshot,
    candidate_evaluation.candidates,
    candidate_evaluation.elapsed_ms,
    candidate_evaluation.occurred_at AS created_at
   FROM red_house.candidate_evaluation;


--
-- Name: idempotency; Type: VIEW; Schema: access_compatibilidad; Owner: -
--

CREATE VIEW access_compatibilidad.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'compatibilidad'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_compatibilidad; Owner: -
--

CREATE VIEW access_compatibilidad.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'compatibilidad'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: outbox; Type: VIEW; Schema: access_compatibilidad; Owner: -
--

CREATE VIEW access_compatibilidad.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'compatibilidad'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: blood_review; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.blood_review (
    review_id uuid NOT NULL,
    candidate_id uuid,
    actor_id uuid NOT NULL,
    decision text NOT NULL,
    reason text NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    evaluation_id uuid NOT NULL,
    resource_id uuid NOT NULL,
    tenant_id uuid NOT NULL
);


--
-- Name: reviews; Type: VIEW; Schema: access_compatibilidad; Owner: -
--

CREATE VIEW access_compatibilidad.reviews AS
 SELECT blood_review.review_id AS id,
    blood_review.evaluation_id,
    blood_review.resource_id,
    blood_review.tenant_id,
    blood_review.actor_id,
    blood_review.decision,
    blood_review.reason,
    blood_review.occurred_at AS created_at
   FROM red_house.blood_review;


--
-- Name: schema_version; Type: VIEW; Schema: access_compatibilidad; Owner: -
--

CREATE VIEW access_compatibilidad.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'compatibilidad'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: worker_health; Type: VIEW; Schema: access_compatibilidad; Owner: -
--

CREATE VIEW access_compatibilidad.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'compatibilidad'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_custodia; Owner: -
--

CREATE VIEW access_custodia.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'custodia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: custody_chain; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.custody_chain (
    id uuid NOT NULL,
    region_id uuid NOT NULL,
    origin_id uuid NOT NULL,
    destination_id uuid NOT NULL,
    last_sequence integer DEFAULT 0 NOT NULL,
    last_hash text DEFAULT ''::text NOT NULL
);


--
-- Name: chains; Type: VIEW; Schema: access_custodia; Owner: -
--

CREATE VIEW access_custodia.chains AS
 SELECT custody_chain.id,
    custody_chain.region_id,
    custody_chain.origin_id,
    custody_chain.destination_id,
    custody_chain.last_sequence,
    custody_chain.last_hash
   FROM red_house.custody_chain;


--
-- Name: custody_event; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.custody_event (
    event_id uuid NOT NULL,
    shipment_id uuid NOT NULL,
    sequence integer NOT NULL,
    status character varying(20),
    actor_id uuid,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    location_description character varying(240),
    observation character varying(1000),
    evidence_reference character varying(240),
    previous_hash text NOT NULL,
    event_hash text NOT NULL,
    event jsonb NOT NULL
);


--
-- Name: custody_events; Type: VIEW; Schema: access_custodia; Owner: -
--

CREATE VIEW access_custodia.custody_events AS
 SELECT custody_event.event_id AS id,
    custody_event.shipment_id,
    custody_event.sequence,
    custody_event.event,
    custody_event.previous_hash,
    custody_event.event_hash AS hash,
    custody_event.occurred_at AS created_at
   FROM red_house.custody_event;


--
-- Name: decisions; Type: VIEW; Schema: access_custodia; Owner: -
--

CREATE VIEW access_custodia.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'custodia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: idempotency; Type: VIEW; Schema: access_custodia; Owner: -
--

CREATE VIEW access_custodia.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'custodia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_custodia; Owner: -
--

CREATE VIEW access_custodia.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'custodia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: outbox; Type: VIEW; Schema: access_custodia; Owner: -
--

CREATE VIEW access_custodia.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'custodia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: schema_version; Type: VIEW; Schema: access_custodia; Owner: -
--

CREATE VIEW access_custodia.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'custodia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: worker_health; Type: VIEW; Schema: access_custodia; Owner: -
--

CREATE VIEW access_custodia.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'custodia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'donantes'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: appointment; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.appointment (
    appointment_id uuid NOT NULL,
    donor_id uuid NOT NULL,
    campaign_id uuid NOT NULL,
    current_status text DEFAULT 'BOOKED'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    tenant_id uuid NOT NULL
);


--
-- Name: appointments; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.appointments AS
 SELECT appointment.appointment_id AS id,
    appointment.tenant_id,
    appointment.donor_id,
    appointment.campaign_id,
    appointment.current_status AS status,
    appointment.created_at
   FROM red_house.appointment;


--
-- Name: campaign; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.campaign (
    campaign_id uuid NOT NULL,
    institution_id uuid NOT NULL,
    title text NOT NULL,
    starts_at timestamp with time zone NOT NULL,
    ends_at timestamp with time zone NOT NULL,
    capacity integer NOT NULL,
    current_status text DEFAULT 'OPEN'::text NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    CONSTRAINT api_campaigns_capacity_check CHECK ((capacity > 0)),
    CONSTRAINT api_campaigns_check CHECK ((ends_at > starts_at))
);


--
-- Name: campaigns; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.campaigns AS
 SELECT campaign.campaign_id AS id,
    campaign.institution_id AS tenant_id,
    campaign.title,
    campaign.starts_at,
    campaign.ends_at,
    campaign.capacity,
    campaign.current_status AS status,
    campaign.version_no AS version
   FROM red_house.campaign;


--
-- Name: decisions; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'donantes'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: donation_event; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.donation_event (
    event_id uuid NOT NULL,
    donation_id uuid NOT NULL,
    status text NOT NULL,
    actor_id uuid NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    observation text NOT NULL
);


--
-- Name: donation_steps; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.donation_steps AS
 SELECT donation_event.event_id AS id,
    donation_event.donation_id,
    donation_event.status AS state,
    donation_event.actor_id,
    donation_event.observation AS reason,
    donation_event.occurred_at AS created_at
   FROM red_house.donation_event;


--
-- Name: donation; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.donation (
    donation_id uuid NOT NULL,
    donor_id uuid NOT NULL,
    review_id uuid,
    donation_code character varying(30),
    current_status text DEFAULT 'COLLECTED'::text NOT NULL,
    collected_at timestamp with time zone NOT NULL,
    processed_at timestamp with time zone,
    created_by uuid,
    registered_at timestamp with time zone DEFAULT now() NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    tenant_id uuid NOT NULL,
    kind text NOT NULL,
    component text NOT NULL,
    blood_group text NOT NULL,
    CONSTRAINT api_donations_kind_check CHECK ((kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text])))
);


--
-- Name: donations; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.donations AS
 SELECT donation.donation_id AS id,
    donation.donor_id,
    donation.tenant_id,
    donation.kind,
    donation.component,
    donation.blood_group,
    donation.collected_at,
    donation.current_status AS status,
    donation.version_no AS version,
    donation.registered_at AS created_at
   FROM red_house.donation;


--
-- Name: donor_review; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.donor_review (
    review_id uuid NOT NULL,
    donor_id uuid NOT NULL,
    decision text NOT NULL,
    reason text NOT NULL,
    actor_id uuid NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: donor_reviews; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.donor_reviews AS
 SELECT donor_review.review_id AS id,
    donor_review.donor_id,
    donor_review.decision,
    donor_review.reason,
    donor_review.actor_id,
    donor_review.occurred_at AS created_at
   FROM red_house.donor_review;


--
-- Name: donor; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.donor (
    donor_id uuid NOT NULL,
    institution_id uuid NOT NULL,
    record_code text NOT NULL,
    display_name text NOT NULL,
    blood_group text NOT NULL,
    donation_kind text,
    background text,
    restrictions text,
    consent_reference text,
    consent_at text,
    current_status text DEFAULT 'PRELIMINARY'::text NOT NULL,
    created_by uuid,
    registered_at timestamp with time zone DEFAULT now() NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    account_id uuid,
    consent boolean NOT NULL,
    CONSTRAINT api_donors_consent_check CHECK (consent),
    CONSTRAINT api_donors_donation_kind_check CHECK ((donation_kind = ANY (ARRAY['VOLUNTARY'::text, 'REPLACEMENT'::text])))
);


--
-- Name: donors; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.donors AS
 SELECT donor.donor_id AS id,
    donor.institution_id AS tenant_id,
    donor.account_id AS user_id,
    donor.record_code AS folio,
    donor.display_name,
    donor.blood_group,
    donor.consent,
    donor.current_status AS status,
    donor.version_no AS version,
    donor.registered_at AS created_at,
    donor.restrictions,
    donor.background,
    donor.donation_kind,
    donor.consent_reference,
    donor.consent_at
   FROM red_house.donor;


--
-- Name: idempotency; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'donantes'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'donantes'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: outbox; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'donantes'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: schema_version; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'donantes'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: worker_health; Type: VIEW; Schema: access_donantes; Owner: -
--

CREATE VIEW access_donantes.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'donantes'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'identidad_acceso'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: cache_revision; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.cache_revision (
    name text NOT NULL,
    revision bigint DEFAULT 0 NOT NULL
);


--
-- Name: cache_revision; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.cache_revision AS
 SELECT cache_revision.name,
    cache_revision.revision
   FROM red_house.cache_revision
  WHERE (cache_revision.name = 'catalogues'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: catalogue_entry; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.catalogue_entry (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    kind text NOT NULL,
    name text NOT NULL,
    parent_id uuid,
    details jsonb NOT NULL,
    active boolean DEFAULT true NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT api_catalogue_kind_check CHECK ((kind = ANY (ARRAY['sites'::text, 'contacts'::text, 'schedules'::text, 'capacities'::text, 'locations'::text])))
);


--
-- Name: catalogue; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.catalogue AS
 SELECT catalogue_entry.id,
    catalogue_entry.tenant_id,
    catalogue_entry.kind,
    catalogue_entry.name,
    catalogue_entry.parent_id,
    catalogue_entry.details,
    catalogue_entry.active,
    catalogue_entry.version,
    catalogue_entry.created_at
   FROM red_house.catalogue_entry;


--
-- Name: decisions; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'identidad_acceso'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: idempotency; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'identidad_acceso'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'identidad_acceso'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: institution; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.institution (
    institution_id uuid NOT NULL,
    institution_code character varying(30),
    institution_name text NOT NULL,
    institution_type character varying(40),
    region_name character varying(80),
    city character varying(100),
    street character varying(200),
    participation_status character varying(10) DEFAULT 'ACTIVE'::character varying,
    version_no integer DEFAULT 1 NOT NULL,
    registered_at timestamp with time zone DEFAULT now(),
    operating_hours character varying(240) DEFAULT ''::character varying,
    region_id uuid NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_by uuid,
    CONSTRAINT institution_institution_type_check CHECK (((institution_type)::text = ANY (ARRAY[('BLOOD_BANK'::character varying)::text, ('HOSPITAL'::character varying)::text, ('COORDINATION'::character varying)::text, ('TRANSPLANT_CENTER'::character varying)::text]))),
    CONSTRAINT institution_participation_status_check CHECK (((participation_status)::text = ANY (ARRAY[('ACTIVE'::character varying)::text, ('INACTIVE'::character varying)::text])))
);


--
-- Name: institutions; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.institutions AS
 SELECT institution.institution_id AS id,
    institution.institution_name AS name,
    institution.region_id,
    institution.active,
    institution.created_by,
    institution.version_no AS version
   FROM red_house.institution;


--
-- Name: outbox; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'identidad_acceso'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: schema_version; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'identidad_acceso'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: web_session; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.web_session (
    session_id uuid NOT NULL,
    account_id uuid NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: sessions; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.sessions AS
 SELECT web_session.session_id AS id,
    web_session.account_id AS user_id,
    web_session.expires_at,
    web_session.revoked_at
   FROM red_house.web_session;


--
-- Name: user_account; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.user_account (
    account_id uuid NOT NULL,
    party_id uuid,
    login_email character varying(180),
    password_hash text NOT NULL,
    account_status character varying(10) DEFAULT 'ACTIVE'::character varying,
    version_no integer DEFAULT 1 NOT NULL,
    registered_at timestamp with time zone DEFAULT now(),
    username text NOT NULL,
    tenant_id uuid NOT NULL,
    role text NOT NULL,
    active boolean DEFAULT true NOT NULL,
    CONSTRAINT api_users_role_check CHECK ((role = ANY (ARRAY['ADMIN'::text, 'OPERATOR'::text, 'MEDICAL'::text, 'COORDINATOR'::text, 'TRANSPORT'::text, 'AUDITOR'::text, 'DONOR'::text]))),
    CONSTRAINT user_account_account_status_check CHECK (((account_status)::text = ANY (ARRAY[('ACTIVE'::character varying)::text, ('INACTIVE'::character varying)::text]))),
    CONSTRAINT user_account_login_email_check CHECK (((login_email)::text = lower((login_email)::text)))
);


--
-- Name: users; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.users AS
 SELECT user_account.account_id AS id,
    user_account.tenant_id,
    user_account.username,
    user_account.password_hash,
    user_account.role,
    user_account.active,
    user_account.version_no AS version
   FROM red_house.user_account;


--
-- Name: worker_health; Type: VIEW; Schema: access_identidad_acceso; Owner: -
--

CREATE VIEW access_identidad_acceso.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'identidad_acceso'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'inventario'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: cache_revision; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.cache_revision AS
 SELECT cache_revision.name,
    cache_revision.revision
   FROM red_house.cache_revision
  WHERE (cache_revision.name = 'inventory'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: decisions; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'inventario'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: idempotency; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'inventario'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'inventario'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: blood_movement; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.blood_movement (
    movement_id uuid NOT NULL,
    resource_id uuid NOT NULL,
    sequence integer,
    previous_status character varying(16),
    new_status character varying(16),
    origin_location_id uuid,
    destination_location_id uuid,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    actor_id uuid NOT NULL,
    reason character varying(240),
    action text NOT NULL
);


--
-- Name: movements; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.movements AS
 SELECT blood_movement.movement_id AS id,
    blood_movement.resource_id,
    blood_movement.action,
    blood_movement.actor_id,
    blood_movement.occurred_at AS created_at
   FROM red_house.blood_movement;


--
-- Name: allocation_operation; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.allocation_operation (
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
-- Name: operations; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.operations AS
 SELECT allocation_operation.id,
    allocation_operation.user_id,
    allocation_operation.tenant_id,
    allocation_operation.key,
    allocation_operation.fingerprint,
    allocation_operation.input,
    allocation_operation.status,
    allocation_operation.hold_id,
    allocation_operation.error,
    allocation_operation.last_recovery_at,
    allocation_operation.created_at
   FROM red_house.allocation_operation;


--
-- Name: outbox; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'inventario'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: blood_allocation; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.blood_allocation (
    allocation_id uuid NOT NULL,
    request_id uuid NOT NULL,
    candidate_id uuid,
    resource_id uuid NOT NULL,
    origin_id uuid NOT NULL,
    destination_id uuid NOT NULL,
    authorized_by uuid,
    authorization_reason character varying(240),
    current_status text DEFAULT 'PENDING'::text NOT NULL,
    reserved_at timestamp with time zone DEFAULT now() NOT NULL,
    received_at timestamp with time zone,
    version_no integer DEFAULT 1,
    review_id uuid,
    operation_id uuid NOT NULL,
    recipient_id uuid NOT NULL,
    region_id uuid NOT NULL,
    hold_id uuid NOT NULL,
    evaluation_id uuid NOT NULL,
    route_id uuid NOT NULL,
    route_version integer NOT NULL,
    shipment_id uuid,
    shipment_sequence integer DEFAULT 0 NOT NULL
);


--
-- Name: reservations; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.reservations AS
 SELECT blood_allocation.allocation_id AS id,
    blood_allocation.operation_id,
    blood_allocation.resource_id,
    blood_allocation.request_id,
    blood_allocation.recipient_id,
    blood_allocation.origin_id,
    blood_allocation.destination_id,
    blood_allocation.region_id,
    blood_allocation.hold_id,
    blood_allocation.evaluation_id,
    blood_allocation.route_id,
    blood_allocation.route_version,
    blood_allocation.current_status AS status,
    blood_allocation.shipment_id,
    blood_allocation.shipment_sequence,
    blood_allocation.reserved_at AS created_at
   FROM red_house.blood_allocation;


--
-- Name: resource_review; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.resource_review (
    id uuid NOT NULL,
    resource_id uuid NOT NULL,
    actor_id uuid NOT NULL,
    decision text NOT NULL,
    reason text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: resource_reviews; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.resource_reviews AS
 SELECT resource_review.id,
    resource_review.resource_id,
    resource_review.actor_id,
    resource_review.decision,
    resource_review.reason,
    resource_review.created_at
   FROM red_house.resource_review;


--
-- Name: resource; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.resource (
    resource_id uuid NOT NULL,
    traceability_code character varying(40),
    resource_kind text NOT NULL,
    tenant_id uuid NOT NULL,
    region_id uuid NOT NULL,
    folio text NOT NULL,
    current_institution_id uuid NOT NULL,
    donation_id uuid,
    component text NOT NULL,
    blood_group text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    status text DEFAULT 'QUARANTINE'::text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    location_id uuid,
    collected_at timestamp with time zone,
    CONSTRAINT api_resources_kind_check CHECK ((resource_kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text])))
);


--
-- Name: resources; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.resources AS
 SELECT resource.resource_id AS id,
    resource.tenant_id,
    resource.region_id,
    resource.folio,
    resource.current_institution_id,
    resource.donation_id,
    resource.resource_kind AS kind,
    resource.component,
    resource.blood_group,
    resource.expires_at,
    resource.status,
    resource.version,
    resource.created_at,
    resource.location_id,
    resource.collected_at
   FROM red_house.resource;


--
-- Name: schema_version; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'inventario'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: worker_health; Type: VIEW; Schema: access_inventario; Owner: -
--

CREATE VIEW access_inventario.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'inventario'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_monitoreo; Owner: -
--

CREATE VIEW access_monitoreo.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'monitoreo'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: service_health_check; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.service_health_check (
    check_id uuid NOT NULL,
    service text NOT NULL,
    state text NOT NULL,
    elapsed_ms double precision NOT NULL,
    dependency text,
    last_error text,
    deployed_version text,
    checked_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: checks; Type: VIEW; Schema: access_monitoreo; Owner: -
--

CREATE VIEW access_monitoreo.checks AS
 SELECT service_health_check.check_id AS id,
    service_health_check.service,
    service_health_check.state,
    service_health_check.elapsed_ms,
    service_health_check.dependency,
    service_health_check.last_error,
    service_health_check.deployed_version AS version,
    service_health_check.checked_at AS created_at
   FROM red_house.service_health_check;


--
-- Name: decisions; Type: VIEW; Schema: access_monitoreo; Owner: -
--

CREATE VIEW access_monitoreo.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'monitoreo'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: idempotency; Type: VIEW; Schema: access_monitoreo; Owner: -
--

CREATE VIEW access_monitoreo.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'monitoreo'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_monitoreo; Owner: -
--

CREATE VIEW access_monitoreo.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'monitoreo'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: outbox; Type: VIEW; Schema: access_monitoreo; Owner: -
--

CREATE VIEW access_monitoreo.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'monitoreo'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: schema_version; Type: VIEW; Schema: access_monitoreo; Owner: -
--

CREATE VIEW access_monitoreo.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'monitoreo'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: worker_health; Type: VIEW; Schema: access_monitoreo; Owner: -
--

CREATE VIEW access_monitoreo.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'monitoreo'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'priorizacion_geografia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: decisions; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'priorizacion_geografia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: idempotency; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'priorizacion_geografia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'priorizacion_geografia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: outbox; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'priorizacion_geografia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: balance_proposal; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.balance_proposal (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    algorithm_version text NOT NULL,
    snapshots jsonb NOT NULL,
    result jsonb NOT NULL,
    elapsed_ms double precision NOT NULL,
    slot_count integer NOT NULL,
    matched_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: proposals; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.proposals AS
 SELECT balance_proposal.id,
    balance_proposal.tenant_id,
    balance_proposal.algorithm_version,
    balance_proposal.snapshots,
    balance_proposal.result,
    balance_proposal.elapsed_ms,
    balance_proposal.slot_count,
    balance_proposal.matched_count,
    balance_proposal.created_at
   FROM red_house.balance_proposal;


--
-- Name: ranking_run; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.ranking_run (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    evaluation_id uuid NOT NULL,
    algorithm_version text NOT NULL,
    factors jsonb NOT NULL,
    result jsonb NOT NULL,
    elapsed_ms double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: rankings; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.rankings AS
 SELECT ranking_run.id,
    ranking_run.tenant_id,
    ranking_run.evaluation_id,
    ranking_run.algorithm_version,
    ranking_run.factors,
    ranking_run.result,
    ranking_run.elapsed_ms,
    ranking_run.created_at
   FROM red_house.ranking_run;


--
-- Name: regional_route; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.regional_route (
    route_id uuid NOT NULL,
    origin_id uuid NOT NULL,
    destination_id uuid NOT NULL,
    distance_km double precision NOT NULL,
    travel_minutes integer NOT NULL,
    source_reference text NOT NULL,
    recorded_by uuid,
    recorded_at timestamp with time zone DEFAULT now() NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    region_id uuid NOT NULL,
    CONSTRAINT api_routes_distance_km_check CHECK ((distance_km >= (0)::double precision)),
    CONSTRAINT api_routes_travel_minutes_check CHECK ((travel_minutes >= 0))
);


--
-- Name: routes; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.routes AS
 SELECT regional_route.route_id AS id,
    regional_route.origin_id,
    regional_route.destination_id,
    regional_route.region_id,
    regional_route.distance_km,
    regional_route.travel_minutes,
    regional_route.source_reference AS source,
    regional_route.version_no AS version,
    regional_route.recorded_at AS updated_at
   FROM red_house.regional_route;


--
-- Name: schema_version; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'priorizacion_geografia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: worker_health; Type: VIEW; Schema: access_priorizacion_geografia; Owner: -
--

CREATE VIEW access_priorizacion_geografia.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'priorizacion_geografia'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'receptores'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: decisions; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'receptores'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: request_hold; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.request_hold (
    id uuid NOT NULL,
    request_id uuid NOT NULL,
    recipient_id uuid NOT NULL,
    operation_id uuid NOT NULL,
    resource_id uuid NOT NULL,
    kind text NOT NULL,
    request_version integer NOT NULL,
    region_id uuid NOT NULL,
    status text DEFAULT 'HELD'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: holds; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.holds AS
 SELECT request_hold.id,
    request_hold.request_id,
    request_hold.recipient_id,
    request_hold.operation_id,
    request_hold.resource_id,
    request_hold.kind,
    request_hold.request_version,
    request_hold.region_id,
    request_hold.status,
    request_hold.created_at
   FROM red_house.request_hold;


--
-- Name: idempotency; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'receptores'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'receptores'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: outbox; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'receptores'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: recipient; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.recipient (
    recipient_id uuid NOT NULL,
    institution_id uuid NOT NULL,
    record_code text NOT NULL,
    display_name text NOT NULL,
    blood_group text NOT NULL,
    requirement text,
    legacy_urgency character varying(20),
    studies text NOT NULL,
    restrictions text,
    current_status text DEFAULT 'ACTIVE'::text NOT NULL,
    responsible_id uuid,
    registered_at timestamp with time zone DEFAULT now(),
    version_no integer DEFAULT 1 NOT NULL,
    kind text NOT NULL,
    organ_type text,
    CONSTRAINT api_recipients_check CHECK ((((kind = 'BLOOD'::text) AND (organ_type IS NULL)) OR ((kind = 'ORGAN'::text) AND (organ_type = ANY (ARRAY['KIDNEY'::text, 'LIVER'::text, 'HEART'::text]))))),
    CONSTRAINT api_recipients_kind_check CHECK ((kind = ANY (ARRAY['BLOOD'::text, 'ORGAN'::text]))),
    CONSTRAINT recipient_urgency_check CHECK (((legacy_urgency)::text = ANY (ARRAY[('URGENT'::character varying)::text, ('PRIORITY'::character varying)::text, ('ROUTINE'::character varying)::text])))
);


--
-- Name: COLUMN recipient.legacy_urgency; Type: COMMENT; Schema: red_house; Owner: -
--

COMMENT ON COLUMN red_house.recipient.legacy_urgency IS 'Dato histórico previo al 23-09-2026; urgencia operativa en blood_request.';


--
-- Name: recipients; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.recipients AS
 SELECT recipient.recipient_id AS id,
    recipient.institution_id AS tenant_id,
    recipient.record_code AS folio,
    recipient.display_name,
    recipient.kind,
    recipient.blood_group,
    recipient.organ_type,
    recipient.studies,
    recipient.current_status AS status,
    recipient.version_no AS version,
    recipient.restrictions,
    recipient.requirement
   FROM red_house.recipient;


--
-- Name: blood_request; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.blood_request (
    request_id uuid NOT NULL,
    request_code character varying(30),
    recipient_id uuid NOT NULL,
    component_id uuid,
    quantity integer NOT NULL,
    urgency character varying(20),
    justification character varying(1000),
    current_status text DEFAULT 'OPEN'::text NOT NULL,
    responsible_id uuid,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    closed_at timestamp with time zone,
    version_no integer DEFAULT 1 NOT NULL,
    tenant_id uuid NOT NULL,
    kind text NOT NULL,
    component text NOT NULL,
    priority_level integer NOT NULL,
    CONSTRAINT api_requests_check CHECK (((kind <> 'ORGAN'::text) OR (quantity = 1))),
    CONSTRAINT api_requests_quantity_check CHECK ((quantity > 0)),
    CONSTRAINT api_requests_urgency_check CHECK (((priority_level >= 1) AND (priority_level <= 3))),
    CONSTRAINT blood_request_urgency_check CHECK (((urgency)::text = ANY (ARRAY[('URGENT'::character varying)::text, ('PRIORITY'::character varying)::text, ('ROUTINE'::character varying)::text])))
);


--
-- Name: requests; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.requests AS
 SELECT blood_request.request_id AS id,
    blood_request.tenant_id,
    blood_request.recipient_id,
    blood_request.kind,
    blood_request.component,
    blood_request.quantity,
    blood_request.priority_level AS urgency,
    blood_request.current_status AS status,
    blood_request.version_no AS version,
    blood_request.requested_at AS created_at
   FROM red_house.blood_request;


--
-- Name: schema_version; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'receptores'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: worker_health; Type: VIEW; Schema: access_receptores; Owner: -
--

CREATE VIEW access_receptores.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'receptores'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: activity_events; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.activity_events AS
 SELECT service_activity_events.id,
    service_activity_events.tenant_id,
    service_activity_events.event,
    service_activity_events.created_at
   FROM red_house.service_activity_events
  WHERE (service_activity_events.service = 'transporte'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: decisions; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.decisions AS
 SELECT service_decisions.id,
    service_decisions.resource_id,
    service_decisions.tenant_id,
    service_decisions.actor_id,
    service_decisions.action,
    service_decisions.reason,
    service_decisions.changes,
    service_decisions.created_at
   FROM red_house.service_decisions
  WHERE (service_decisions.service = 'transporte'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: stored_file; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.stored_file (
    file_id uuid NOT NULL,
    shipment_id uuid NOT NULL,
    owner_id uuid NOT NULL,
    object_path text NOT NULL,
    mime_type text NOT NULL,
    size_bytes integer NOT NULL,
    sha256 text NOT NULL,
    current_status text DEFAULT 'PENDING'::text NOT NULL,
    generation text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT api_files_size_check CHECK (((size_bytes >= 1) AND (size_bytes <= 10485760)))
);


--
-- Name: files; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.files AS
 SELECT stored_file.file_id AS id,
    stored_file.shipment_id,
    stored_file.owner_id,
    stored_file.object_path,
    stored_file.mime_type,
    stored_file.size_bytes AS size,
    stored_file.sha256,
    stored_file.current_status AS status,
    stored_file.generation,
    stored_file.created_at
   FROM red_house.stored_file;


--
-- Name: idempotency; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.idempotency AS
 SELECT service_idempotency.id,
    service_idempotency.user_id,
    service_idempotency.key,
    service_idempotency.operation,
    service_idempotency.fingerprint,
    service_idempotency.result,
    service_idempotency.created_at
   FROM red_house.service_idempotency
  WHERE (service_idempotency.service = 'transporte'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: inbox; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.inbox AS
 SELECT service_inbox.event_id,
    service_inbox.fingerprint,
    service_inbox.created_at
   FROM red_house.service_inbox
  WHERE (service_inbox.service = 'transporte'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: outbox; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.outbox AS
 SELECT service_outbox.id,
    service_outbox.event_id,
    service_outbox.target,
    service_outbox.event,
    service_outbox.created_at,
    service_outbox.delivered_at,
    service_outbox.attempts,
    service_outbox.next_attempt,
    service_outbox.last_error
   FROM red_house.service_outbox
  WHERE (service_outbox.service = 'transporte'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: schema_version; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.schema_version AS
 SELECT service_schema_version.version,
    service_schema_version.installed_at
   FROM red_house.service_schema_version
  WHERE (service_schema_version.service = 'transporte'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: shipment; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.shipment (
    shipment_id uuid NOT NULL,
    allocation_id uuid NOT NULL,
    transport_id uuid NOT NULL,
    vehicle character varying(120),
    departure_at timestamp with time zone NOT NULL,
    eta timestamp with time zone NOT NULL,
    current_status text DEFAULT 'PLANNED'::text NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    organ_allocation_id uuid,
    origin_id uuid NOT NULL,
    destination_id uuid NOT NULL,
    region_id uuid NOT NULL,
    sequence integer DEFAULT 0 NOT NULL,
    inventory_pending boolean DEFAULT true NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    CONSTRAINT api_shipments_check CHECK ((eta > departure_at)),
    CONSTRAINT api_shipments_check1 CHECK ((eta < expires_at))
);


--
-- Name: shipments; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.shipments AS
 SELECT shipment.shipment_id AS id,
    shipment.allocation_id AS reservation_id,
    shipment.origin_id,
    shipment.destination_id,
    shipment.region_id,
    shipment.transport_id AS transport_user_id,
    shipment.departure_at,
    shipment.eta,
    shipment.current_status AS status,
    shipment.version_no AS version,
    shipment.sequence,
    shipment.inventory_pending,
    shipment.expires_at
   FROM red_house.shipment;


--
-- Name: transport_telemetry; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.transport_telemetry (
    telemetry_id uuid NOT NULL,
    shipment_id uuid NOT NULL,
    actor_id uuid NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    captured_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: telemetry; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.telemetry AS
 SELECT transport_telemetry.telemetry_id AS id,
    transport_telemetry.shipment_id,
    transport_telemetry.actor_id,
    transport_telemetry.latitude,
    transport_telemetry.longitude,
    transport_telemetry.captured_at,
    transport_telemetry.created_at
   FROM red_house.transport_telemetry;


--
-- Name: shipment_transition; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.shipment_transition (
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
-- Name: transitions; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.transitions AS
 SELECT shipment_transition.id,
    shipment_transition.shipment_id,
    shipment_transition.sequence,
    shipment_transition.state,
    shipment_transition.actor_id,
    shipment_transition.reason,
    shipment_transition.evidence,
    shipment_transition.created_at
   FROM red_house.shipment_transition;


--
-- Name: worker_health; Type: VIEW; Schema: access_transporte; Owner: -
--

CREATE VIEW access_transporte.worker_health AS
 SELECT service_worker_health.id,
    service_worker_health.checked_at,
    service_worker_health.last_success,
    service_worker_health.last_error
   FROM red_house.service_worker_health
  WHERE (service_worker_health.service = 'transporte'::text)
  WITH LOCAL CHECK OPTION;


--
-- Name: account_role; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.account_role (
    account_id uuid NOT NULL,
    role_code character varying(30) NOT NULL,
    institution_id uuid,
    region_name character varying(80),
    CONSTRAINT account_role_check CHECK (((institution_id IS NOT NULL) <> (region_name IS NOT NULL))),
    CONSTRAINT account_role_check1 CHECK ((((role_code)::text <> 'OPERATOR'::text) OR (institution_id IS NOT NULL))),
    CONSTRAINT account_role_check2 CHECK ((((role_code)::text <> ALL (ARRAY[('MEDICAL'::character varying)::text, ('TRANSPORT'::character varying)::text])) OR (institution_id IS NOT NULL)))
);


--
-- Name: algorithm_run; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.algorithm_run (
    run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    institution_id uuid NOT NULL,
    actor_id uuid,
    operation text NOT NULL,
    algorithm_version text NOT NULL,
    blood_evaluation_id uuid,
    organ_evaluation_id uuid,
    inputs jsonb NOT NULL,
    factors jsonb NOT NULL,
    result jsonb NOT NULL,
    elapsed_ms double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT algorithm_run_check CHECK ((num_nonnulls(blood_evaluation_id, organ_evaluation_id) <= 1)),
    CONSTRAINT algorithm_run_elapsed_ms_check CHECK ((elapsed_ms >= (0)::double precision)),
    CONSTRAINT algorithm_run_operation_check CHECK ((operation = ANY (ARRAY['RANKING'::text, 'BALANCING'::text])))
);


--
-- Name: audit_change; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.audit_change (
    event_id uuid NOT NULL,
    field_name character varying(60) NOT NULL,
    previous_value character varying(240),
    new_value character varying(240)
);


--
-- Name: blood_candidate; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.blood_candidate (
    candidate_id uuid DEFAULT gen_random_uuid() NOT NULL,
    evaluation_id uuid NOT NULL,
    resource_id uuid NOT NULL,
    rank_no integer NOT NULL,
    unit_version integer NOT NULL,
    donor_group character varying(3) NOT NULL,
    recipient_group character varying(3) NOT NULL,
    urgency character varying(20) NOT NULL,
    wait_minutes integer NOT NULL,
    distance_km integer NOT NULL,
    travel_minutes integer NOT NULL,
    route_version integer NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    explanation character varying(1000) NOT NULL,
    CONSTRAINT blood_candidate_rank_no_check CHECK ((rank_no > 0)),
    CONSTRAINT blood_candidate_wait_minutes_check CHECK ((wait_minutes >= 0))
);


--
-- Name: blood_classification; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.blood_classification (
    resource_id uuid NOT NULL,
    recorded_group_code character varying(3) NOT NULL,
    source_reference character varying(120) NOT NULL,
    recorded_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT blood_classification_recorded_group_code_check CHECK (((recorded_group_code)::text = ANY (ARRAY[('O-'::character varying)::text, ('O+'::character varying)::text, ('A-'::character varying)::text, ('A+'::character varying)::text, ('B-'::character varying)::text, ('B+'::character varying)::text, ('AB-'::character varying)::text, ('AB+'::character varying)::text])))
);


--
-- Name: blood_component; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.blood_component (
    component_id uuid DEFAULT gen_random_uuid() NOT NULL,
    component_code character varying(30) NOT NULL,
    component_name character varying(100) NOT NULL,
    region_name character varying(80) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    version_no integer DEFAULT 1 NOT NULL
);


--
-- Name: blood_status_transition; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.blood_status_transition (
    previous_status character varying(16) NOT NULL,
    new_status character varying(16) NOT NULL,
    is_illustrative boolean DEFAULT true NOT NULL,
    CONSTRAINT blood_status_transition_check CHECK (((previous_status)::text <> (new_status)::text)),
    CONSTRAINT blood_status_transition_is_illustrative_check CHECK (is_illustrative),
    CONSTRAINT blood_status_transition_new_status_check CHECK (((new_status)::text = ANY (ARRAY[('AVAILABLE'::character varying)::text, ('QUARANTINED'::character varying)::text, ('WITHDRAWN'::character varying)::text]))),
    CONSTRAINT blood_status_transition_previous_status_check CHECK (((previous_status)::text = ANY (ARRAY[('AVAILABLE'::character varying)::text, ('QUARANTINED'::character varying)::text])))
);


--
-- Name: blood_unit; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.blood_unit (
    resource_id uuid NOT NULL,
    component_id uuid NOT NULL,
    location_id uuid NOT NULL,
    collected_at timestamp with time zone NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    current_status character varying(16) NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    registered_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT blood_unit_check CHECK ((expires_at > collected_at)),
    CONSTRAINT blood_unit_current_status_check CHECK (((current_status)::text = ANY (ARRAY[('AVAILABLE'::character varying)::text, ('QUARANTINED'::character varying)::text, ('WITHDRAWN'::character varying)::text, ('RESERVED'::character varying)::text, ('IN_TRANSIT'::character varying)::text, ('DELIVERED'::character varying)::text])))
);


--
-- Name: capability; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.capability (
    capability_code character varying(40) NOT NULL,
    capability_name character varying(100) NOT NULL
);


--
-- Name: contact; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.contact (
    contact_id uuid DEFAULT gen_random_uuid() NOT NULL,
    contact_name character varying(120) NOT NULL,
    contact_function character varying(80) NOT NULL
);


--
-- Name: contact_method; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.contact_method (
    contact_id uuid NOT NULL,
    method_kind character varying(10) NOT NULL,
    method_value character varying(180) NOT NULL,
    CONSTRAINT contact_method_method_kind_check CHECK (((method_kind)::text = ANY (ARRAY[('EMAIL'::character varying)::text, ('PHONE'::character varying)::text])))
);


--
-- Name: donation_unit; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.donation_unit (
    resource_id uuid NOT NULL,
    donation_id uuid NOT NULL,
    released_by uuid NOT NULL,
    release_reference character varying(240) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: institution_capability; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.institution_capability (
    institution_id uuid NOT NULL,
    capability_code character varying(40) NOT NULL
);


--
-- Name: institution_contact; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.institution_contact (
    institution_id uuid NOT NULL,
    contact_id uuid NOT NULL
);


--
-- Name: login_attempt; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.login_attempt (
    attempt_id bigint NOT NULL,
    identity_hash character(64) NOT NULL,
    address_hash character(64) NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    was_successful boolean NOT NULL
);


--
-- Name: login_attempt_attempt_id_seq; Type: SEQUENCE; Schema: red_house; Owner: -
--

ALTER TABLE red_house.login_attempt ALTER COLUMN attempt_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME red_house.login_attempt_attempt_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: organ_allocation; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.organ_allocation (
    allocation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    candidate_id uuid NOT NULL,
    review_id uuid NOT NULL,
    offer_id uuid NOT NULL,
    recipient_id uuid NOT NULL,
    authorized_by uuid NOT NULL,
    authorization_reference character varying(240) NOT NULL,
    current_status character varying(12) DEFAULT 'RESERVED'::character varying NOT NULL,
    transport_id uuid,
    vehicle character varying(120),
    departure_at timestamp with time zone,
    eta timestamp with time zone,
    reserved_at timestamp with time zone DEFAULT now() NOT NULL,
    received_at timestamp with time zone,
    version_no integer DEFAULT 1 NOT NULL,
    CONSTRAINT organ_allocation_check CHECK (((eta IS NULL) OR (eta > departure_at))),
    CONSTRAINT organ_allocation_current_status_check CHECK (((current_status)::text = ANY (ARRAY[('RESERVED'::character varying)::text, ('SCHEDULED'::character varying)::text, ('PREPARED'::character varying)::text, ('COLLECTED'::character varying)::text, ('IN_TRANSIT'::character varying)::text, ('DELIVERED'::character varying)::text, ('ACCEPTED'::character varying)::text, ('CANCELLED'::character varying)::text])))
);


--
-- Name: organ_candidate; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.organ_candidate (
    candidate_id uuid DEFAULT gen_random_uuid() NOT NULL,
    evaluation_id uuid NOT NULL,
    offer_id uuid NOT NULL,
    recipient_id uuid NOT NULL,
    offer_version integer NOT NULL,
    recipient_version integer NOT NULL,
    route_version integer NOT NULL,
    rank_no integer NOT NULL,
    algorithm_version character varying(40) NOT NULL,
    explanation text NOT NULL,
    distance_km integer NOT NULL,
    travel_minutes integer NOT NULL,
    evaluated_by uuid NOT NULL,
    evaluated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT organ_candidate_rank_no_check CHECK ((rank_no > 0))
);


--
-- Name: organ_custody_event; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.organ_custody_event (
    event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    allocation_id uuid NOT NULL,
    status character varying(20) NOT NULL,
    actor_id uuid NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    location_description character varying(240) NOT NULL,
    observation text NOT NULL,
    evidence_reference character varying(240) NOT NULL,
    previous_hash text,
    event_hash text
);


--
-- Name: organ_donor; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.organ_donor (
    donor_id uuid DEFAULT gen_random_uuid() NOT NULL,
    institution_id uuid NOT NULL,
    record_code character varying(30) NOT NULL,
    display_name character varying(120) NOT NULL,
    abo character varying(2) NOT NULL,
    donation_kind character varying(12) NOT NULL,
    consent_reference character varying(240) NOT NULL,
    studies text NOT NULL,
    hla text NOT NULL,
    clinical_reference character varying(240) NOT NULL,
    reviewed_by uuid NOT NULL,
    registered_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT organ_donor_abo_check CHECK (((abo)::text = ANY (ARRAY[('O'::character varying)::text, ('A'::character varying)::text, ('B'::character varying)::text, ('AB'::character varying)::text]))),
    CONSTRAINT organ_donor_donation_kind_check CHECK (((donation_kind)::text = ANY (ARRAY[('LIVING'::character varying)::text, ('DECEASED'::character varying)::text])))
);


--
-- Name: organ_evaluation; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.organ_evaluation (
    evaluation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    offer_id uuid NOT NULL,
    evaluated_by uuid NOT NULL,
    algorithm_version character varying(40) NOT NULL,
    evaluated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: organ_offer; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.organ_offer (
    offer_id uuid DEFAULT gen_random_uuid() NOT NULL,
    donor_id uuid NOT NULL,
    record_code character varying(30) NOT NULL,
    organ_type character varying(12) NOT NULL,
    anatomical_description character varying(240) NOT NULL,
    recovered_at timestamp with time zone NOT NULL,
    preservation_until timestamp with time zone NOT NULL,
    preservation_reference character varying(240) NOT NULL,
    released_by uuid NOT NULL,
    current_status character varying(12) DEFAULT 'AVAILABLE'::character varying NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    registered_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT organ_offer_check CHECK ((preservation_until > recovered_at)),
    CONSTRAINT organ_offer_current_status_check CHECK (((current_status)::text = ANY (ARRAY[('AVAILABLE'::character varying)::text, ('RESERVED'::character varying)::text, ('IN_TRANSIT'::character varying)::text, ('RECEIVED'::character varying)::text, ('WITHDRAWN'::character varying)::text]))),
    CONSTRAINT organ_offer_organ_type_check CHECK (((organ_type)::text = ANY (ARRAY[('KIDNEY'::character varying)::text, ('LIVER'::character varying)::text, ('HEART'::character varying)::text])))
);


--
-- Name: organ_recipient; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.organ_recipient (
    recipient_id uuid DEFAULT gen_random_uuid() NOT NULL,
    institution_id uuid NOT NULL,
    record_code character varying(30) NOT NULL,
    display_name character varying(120) NOT NULL,
    organ_type character varying(12) NOT NULL,
    abo character varying(2) NOT NULL,
    studies text NOT NULL,
    hla text NOT NULL,
    urgency character varying(12) NOT NULL,
    waiting_since timestamp with time zone NOT NULL,
    clinical_reference character varying(240) NOT NULL,
    responsible_id uuid NOT NULL,
    current_status character varying(12) DEFAULT 'ACTIVE'::character varying NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    registered_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT organ_recipient_abo_check CHECK (((abo)::text = ANY (ARRAY[('O'::character varying)::text, ('A'::character varying)::text, ('B'::character varying)::text, ('AB'::character varying)::text]))),
    CONSTRAINT organ_recipient_current_status_check CHECK (((current_status)::text = ANY (ARRAY[('ACTIVE'::character varying)::text, ('INACTIVE'::character varying)::text, ('RESERVED'::character varying)::text, ('CLOSED'::character varying)::text]))),
    CONSTRAINT organ_recipient_organ_type_check CHECK (((organ_type)::text = ANY (ARRAY[('KIDNEY'::character varying)::text, ('LIVER'::character varying)::text, ('HEART'::character varying)::text]))),
    CONSTRAINT organ_recipient_urgency_check CHECK (((urgency)::text = ANY (ARRAY[('URGENT'::character varying)::text, ('PRIORITY'::character varying)::text, ('ROUTINE'::character varying)::text])))
);


--
-- Name: organ_review; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.organ_review (
    review_id uuid DEFAULT gen_random_uuid() NOT NULL,
    candidate_id uuid NOT NULL,
    decision character varying(12) NOT NULL,
    hla_assessment text NOT NULL,
    size_assessment text NOT NULL,
    crossmatch_reference character varying(240) NOT NULL,
    clinical_reference character varying(240) NOT NULL,
    reviewed_by uuid NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT organ_review_decision_check CHECK (((decision)::text = ANY (ARRAY[('FAVORABLE'::character varying)::text, ('REJECTED'::character varying)::text])))
);


--
-- Name: parameter_version; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.parameter_version (
    parameter_version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    parameter_code character varying(40) NOT NULL,
    region_name character varying(80) NOT NULL,
    version_no integer NOT NULL,
    scalar_value integer NOT NULL,
    measurement_unit character varying(10) DEFAULT 'HOURS'::character varying NOT NULL,
    is_illustrative boolean DEFAULT true NOT NULL,
    approved_by uuid,
    valid_from timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT parameter_version_is_illustrative_check CHECK (is_illustrative),
    CONSTRAINT parameter_version_measurement_unit_check CHECK (((measurement_unit)::text = 'HOURS'::text)),
    CONSTRAINT parameter_version_parameter_code_check CHECK (((parameter_code)::text = 'EXPIRY_WARNING_HOURS'::text)),
    CONSTRAINT parameter_version_scalar_value_check CHECK (((scalar_value >= 1) AND (scalar_value <= 720)))
);


--
-- Name: party; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.party (
    party_id uuid DEFAULT gen_random_uuid() NOT NULL,
    party_name character varying(120) NOT NULL
);


--
-- Name: request_event; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.request_event (
    event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    request_id uuid NOT NULL,
    action character varying(30) NOT NULL,
    actor_id uuid NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    observation character varying(240) NOT NULL
);


--
-- Name: role; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.role (
    role_code character varying(30) NOT NULL,
    role_name character varying(80) NOT NULL,
    is_enabled boolean NOT NULL
);


--
-- Name: schema_migration; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.schema_migration (
    version integer NOT NULL,
    description text NOT NULL,
    installed_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: site; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.site (
    site_id uuid DEFAULT gen_random_uuid() NOT NULL,
    institution_id uuid NOT NULL,
    site_code character varying(30) NOT NULL,
    site_name character varying(120) NOT NULL,
    street character varying(200) NOT NULL,
    city character varying(100) NOT NULL,
    site_status character varying(10) DEFAULT 'ACTIVE'::character varying NOT NULL,
    version_no integer DEFAULT 1 NOT NULL,
    CONSTRAINT site_site_status_check CHECK (((site_status)::text = ANY (ARRAY[('ACTIVE'::character varying)::text, ('INACTIVE'::character varying)::text])))
);


--
-- Name: site_schedule; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.site_schedule (
    schedule_id uuid DEFAULT gen_random_uuid() NOT NULL,
    site_id uuid NOT NULL,
    weekday smallint NOT NULL,
    opens_at time without time zone NOT NULL,
    closes_at time without time zone NOT NULL,
    CONSTRAINT site_schedule_check CHECK ((closes_at > opens_at)),
    CONSTRAINT site_schedule_weekday_check CHECK (((weekday >= 1) AND (weekday <= 7)))
);


--
-- Name: storage_location; Type: TABLE; Schema: red_house; Owner: -
--

CREATE TABLE red_house.storage_location (
    location_id uuid DEFAULT gen_random_uuid() NOT NULL,
    site_id uuid NOT NULL,
    location_code character varying(30) NOT NULL,
    location_description character varying(150) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    version_no integer DEFAULT 1 NOT NULL
);


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: alerts status; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.alerts ALTER COLUMN status SET DEFAULT 'OPEN'::text;


--
-- Name: alerts created_at; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.alerts ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_alertas; Owner: -
--

ALTER TABLE ONLY access_alertas.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: audit_events created_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.audit_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: audit_finding_actions created_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.audit_finding_actions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: audit_findings status; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.audit_findings ALTER COLUMN status SET DEFAULT 'OPEN'::text;


--
-- Name: audit_findings version; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.audit_findings ALTER COLUMN version SET DEFAULT 1;


--
-- Name: audit_findings created_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.audit_findings ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: audit_findings updated_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.audit_findings ALTER COLUMN updated_at SET DEFAULT now();


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_auditoria; Owner: -
--

ALTER TABLE ONLY access_auditoria.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: evaluations created_at; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.evaluations ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: reviews created_at; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.reviews ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_compatibilidad; Owner: -
--

ALTER TABLE ONLY access_compatibilidad.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: chains last_sequence; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.chains ALTER COLUMN last_sequence SET DEFAULT 0;


--
-- Name: chains last_hash; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.chains ALTER COLUMN last_hash SET DEFAULT ''::text;


--
-- Name: custody_events created_at; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.custody_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_custodia; Owner: -
--

ALTER TABLE ONLY access_custodia.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: appointments status; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.appointments ALTER COLUMN status SET DEFAULT 'BOOKED'::text;


--
-- Name: appointments created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.appointments ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: campaigns status; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.campaigns ALTER COLUMN status SET DEFAULT 'OPEN'::text;


--
-- Name: campaigns version; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.campaigns ALTER COLUMN version SET DEFAULT 1;


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: donation_steps created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.donation_steps ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: donations status; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.donations ALTER COLUMN status SET DEFAULT 'COLLECTED'::text;


--
-- Name: donations version; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.donations ALTER COLUMN version SET DEFAULT 1;


--
-- Name: donations created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.donations ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: donor_reviews created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.donor_reviews ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: donors status; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.donors ALTER COLUMN status SET DEFAULT 'PRELIMINARY'::text;


--
-- Name: donors version; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.donors ALTER COLUMN version SET DEFAULT 1;


--
-- Name: donors created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.donors ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_donantes; Owner: -
--

ALTER TABLE ONLY access_donantes.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: cache_revision revision; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.cache_revision ALTER COLUMN revision SET DEFAULT 0;


--
-- Name: catalogue active; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.catalogue ALTER COLUMN active SET DEFAULT true;


--
-- Name: catalogue version; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.catalogue ALTER COLUMN version SET DEFAULT 1;


--
-- Name: catalogue created_at; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.catalogue ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: institutions active; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.institutions ALTER COLUMN active SET DEFAULT true;


--
-- Name: institutions version; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.institutions ALTER COLUMN version SET DEFAULT 1;


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: users active; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.users ALTER COLUMN active SET DEFAULT true;


--
-- Name: users version; Type: DEFAULT; Schema: access_identidad_acceso; Owner: -
--

ALTER TABLE ONLY access_identidad_acceso.users ALTER COLUMN version SET DEFAULT 1;


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: cache_revision revision; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.cache_revision ALTER COLUMN revision SET DEFAULT 0;


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: movements created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.movements ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: operations status; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.operations ALTER COLUMN status SET DEFAULT 'PENDING'::text;


--
-- Name: operations created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.operations ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: reservations status; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.reservations ALTER COLUMN status SET DEFAULT 'PENDING'::text;


--
-- Name: reservations shipment_sequence; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.reservations ALTER COLUMN shipment_sequence SET DEFAULT 0;


--
-- Name: reservations created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.reservations ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: resource_reviews created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.resource_reviews ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: resources status; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.resources ALTER COLUMN status SET DEFAULT 'QUARANTINE'::text;


--
-- Name: resources version; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.resources ALTER COLUMN version SET DEFAULT 1;


--
-- Name: resources created_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.resources ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_inventario; Owner: -
--

ALTER TABLE ONLY access_inventario.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: checks created_at; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.checks ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_monitoreo; Owner: -
--

ALTER TABLE ONLY access_monitoreo.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: proposals created_at; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.proposals ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: rankings created_at; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.rankings ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: routes version; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.routes ALTER COLUMN version SET DEFAULT 1;


--
-- Name: routes updated_at; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.routes ALTER COLUMN updated_at SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_priorizacion_geografia; Owner: -
--

ALTER TABLE ONLY access_priorizacion_geografia.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: holds status; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.holds ALTER COLUMN status SET DEFAULT 'HELD'::text;


--
-- Name: holds created_at; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.holds ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: recipients status; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.recipients ALTER COLUMN status SET DEFAULT 'ACTIVE'::text;


--
-- Name: recipients version; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.recipients ALTER COLUMN version SET DEFAULT 1;


--
-- Name: requests status; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.requests ALTER COLUMN status SET DEFAULT 'OPEN'::text;


--
-- Name: requests version; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.requests ALTER COLUMN version SET DEFAULT 1;


--
-- Name: requests created_at; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.requests ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_receptores; Owner: -
--

ALTER TABLE ONLY access_receptores.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: activity_events created_at; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.activity_events ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: decisions changes; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.decisions ALTER COLUMN changes SET DEFAULT '{}'::jsonb;


--
-- Name: decisions created_at; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.decisions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: files status; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.files ALTER COLUMN status SET DEFAULT 'PENDING'::text;


--
-- Name: files created_at; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.files ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: idempotency created_at; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.idempotency ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: inbox created_at; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.inbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox created_at; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.outbox ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: outbox attempts; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.outbox ALTER COLUMN attempts SET DEFAULT 0;


--
-- Name: outbox next_attempt; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.outbox ALTER COLUMN next_attempt SET DEFAULT now();


--
-- Name: schema_version installed_at; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.schema_version ALTER COLUMN installed_at SET DEFAULT now();


--
-- Name: shipments status; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.shipments ALTER COLUMN status SET DEFAULT 'PLANNED'::text;


--
-- Name: shipments version; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.shipments ALTER COLUMN version SET DEFAULT 1;


--
-- Name: shipments sequence; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.shipments ALTER COLUMN sequence SET DEFAULT 0;


--
-- Name: shipments inventory_pending; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.shipments ALTER COLUMN inventory_pending SET DEFAULT true;


--
-- Name: telemetry created_at; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.telemetry ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: transitions created_at; Type: DEFAULT; Schema: access_transporte; Owner: -
--

ALTER TABLE ONLY access_transporte.transitions ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: account_role account_role_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.account_role
    ADD CONSTRAINT account_role_pkey PRIMARY KEY (account_id);


--
-- Name: algorithm_run algorithm_run_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.algorithm_run
    ADD CONSTRAINT algorithm_run_pkey PRIMARY KEY (run_id);


--
-- Name: notification api_alerts_event_id_tenant_id_target_role_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.notification
    ADD CONSTRAINT api_alerts_event_id_tenant_id_target_role_key UNIQUE (event_id, institution_id, target_role);


--
-- Name: audit_finding_actions api_audit_finding_actions_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_finding_actions
    ADD CONSTRAINT api_audit_finding_actions_pkey PRIMARY KEY (id);


--
-- Name: audit_finding_links api_audit_finding_links_finding_id_event_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_finding_links
    ADD CONSTRAINT api_audit_finding_links_finding_id_event_id_key UNIQUE (finding_id, event_id);


--
-- Name: audit_finding_links api_audit_finding_links_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_finding_links
    ADD CONSTRAINT api_audit_finding_links_pkey PRIMARY KEY (id);


--
-- Name: audit_findings api_audit_findings_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_findings
    ADD CONSTRAINT api_audit_findings_pkey PRIMARY KEY (id);


--
-- Name: catalogue_entry api_catalogue_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.catalogue_entry
    ADD CONSTRAINT api_catalogue_pkey PRIMARY KEY (id);


--
-- Name: catalogue_entry api_catalogue_tenant_id_kind_name_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.catalogue_entry
    ADD CONSTRAINT api_catalogue_tenant_id_kind_name_key UNIQUE (tenant_id, kind, name);


--
-- Name: custody_chain api_chains_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.custody_chain
    ADD CONSTRAINT api_chains_pkey PRIMARY KEY (id);


--
-- Name: custody_event api_custody_events_shipment_id_sequence_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.custody_event
    ADD CONSTRAINT api_custody_events_shipment_id_sequence_key UNIQUE (shipment_id, sequence);


--
-- Name: donor api_donors_tenant_id_folio_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donor
    ADD CONSTRAINT api_donors_tenant_id_folio_key UNIQUE (institution_id, record_code);


--
-- Name: stored_file api_files_object_path_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.stored_file
    ADD CONSTRAINT api_files_object_path_key UNIQUE (object_path);


--
-- Name: request_hold api_holds_operation_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.request_hold
    ADD CONSTRAINT api_holds_operation_id_key UNIQUE (operation_id);


--
-- Name: request_hold api_holds_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.request_hold
    ADD CONSTRAINT api_holds_pkey PRIMARY KEY (id);


--
-- Name: allocation_operation api_operations_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.allocation_operation
    ADD CONSTRAINT api_operations_pkey PRIMARY KEY (id);


--
-- Name: allocation_operation api_operations_user_id_key_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.allocation_operation
    ADD CONSTRAINT api_operations_user_id_key_key UNIQUE (user_id, key);


--
-- Name: balance_proposal api_proposals_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.balance_proposal
    ADD CONSTRAINT api_proposals_pkey PRIMARY KEY (id);


--
-- Name: ranking_run api_rankings_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.ranking_run
    ADD CONSTRAINT api_rankings_pkey PRIMARY KEY (id);


--
-- Name: recipient api_recipients_tenant_id_folio_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.recipient
    ADD CONSTRAINT api_recipients_tenant_id_folio_key UNIQUE (institution_id, record_code);


--
-- Name: blood_allocation api_reservations_hold_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT api_reservations_hold_id_key UNIQUE (hold_id);


--
-- Name: blood_allocation api_reservations_operation_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT api_reservations_operation_id_key UNIQUE (operation_id);


--
-- Name: resource_review api_resource_reviews_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.resource_review
    ADD CONSTRAINT api_resource_reviews_pkey PRIMARY KEY (id);


--
-- Name: resource api_resources_tenant_id_folio_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.resource
    ADD CONSTRAINT api_resources_tenant_id_folio_key UNIQUE (tenant_id, folio);


--
-- Name: blood_review api_reviews_evaluation_id_resource_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_review
    ADD CONSTRAINT api_reviews_evaluation_id_resource_id_key UNIQUE (evaluation_id, resource_id);


--
-- Name: regional_route api_routes_origin_id_destination_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.regional_route
    ADD CONSTRAINT api_routes_origin_id_destination_id_key UNIQUE (origin_id, destination_id);


--
-- Name: shipment api_shipments_reservation_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment
    ADD CONSTRAINT api_shipments_reservation_id_key UNIQUE (allocation_id);


--
-- Name: shipment_transition api_transitions_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment_transition
    ADD CONSTRAINT api_transitions_pkey PRIMARY KEY (id);


--
-- Name: shipment_transition api_transitions_shipment_id_sequence_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment_transition
    ADD CONSTRAINT api_transitions_shipment_id_sequence_key UNIQUE (shipment_id, sequence);


--
-- Name: user_account api_users_username_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.user_account
    ADD CONSTRAINT api_users_username_key UNIQUE (username);


--
-- Name: appointment appointment_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.appointment
    ADD CONSTRAINT appointment_pkey PRIMARY KEY (appointment_id);


--
-- Name: audit_change audit_change_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_change
    ADD CONSTRAINT audit_change_pkey PRIMARY KEY (event_id, field_name);


--
-- Name: audit_event audit_event_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_event
    ADD CONSTRAINT audit_event_pkey PRIMARY KEY (event_id);


--
-- Name: blood_allocation blood_allocation_candidate_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT blood_allocation_candidate_id_key UNIQUE (candidate_id);


--
-- Name: blood_allocation blood_allocation_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT blood_allocation_pkey PRIMARY KEY (allocation_id);


--
-- Name: blood_candidate blood_candidate_evaluation_id_rank_no_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_candidate
    ADD CONSTRAINT blood_candidate_evaluation_id_rank_no_key UNIQUE (evaluation_id, rank_no);


--
-- Name: blood_candidate blood_candidate_evaluation_id_resource_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_candidate
    ADD CONSTRAINT blood_candidate_evaluation_id_resource_id_key UNIQUE (evaluation_id, resource_id);


--
-- Name: blood_candidate blood_candidate_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_candidate
    ADD CONSTRAINT blood_candidate_pkey PRIMARY KEY (candidate_id);


--
-- Name: blood_classification blood_classification_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_classification
    ADD CONSTRAINT blood_classification_pkey PRIMARY KEY (resource_id);


--
-- Name: blood_component blood_component_component_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_component
    ADD CONSTRAINT blood_component_component_code_key UNIQUE (component_code);


--
-- Name: blood_component blood_component_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_component
    ADD CONSTRAINT blood_component_pkey PRIMARY KEY (component_id);


--
-- Name: blood_movement blood_movement_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_movement
    ADD CONSTRAINT blood_movement_pkey PRIMARY KEY (movement_id);


--
-- Name: blood_request blood_request_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_request
    ADD CONSTRAINT blood_request_pkey PRIMARY KEY (request_id);


--
-- Name: blood_request blood_request_request_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_request
    ADD CONSTRAINT blood_request_request_code_key UNIQUE (request_code);


--
-- Name: blood_review blood_review_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_review
    ADD CONSTRAINT blood_review_pkey PRIMARY KEY (review_id);


--
-- Name: blood_status_transition blood_status_transition_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_status_transition
    ADD CONSTRAINT blood_status_transition_pkey PRIMARY KEY (previous_status, new_status);


--
-- Name: blood_unit blood_unit_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_unit
    ADD CONSTRAINT blood_unit_pkey PRIMARY KEY (resource_id);


--
-- Name: cache_revision cache_revision_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.cache_revision
    ADD CONSTRAINT cache_revision_pkey PRIMARY KEY (name);


--
-- Name: campaign campaign_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.campaign
    ADD CONSTRAINT campaign_pkey PRIMARY KEY (campaign_id);


--
-- Name: candidate_evaluation candidate_evaluation_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.candidate_evaluation
    ADD CONSTRAINT candidate_evaluation_pkey PRIMARY KEY (evaluation_id);


--
-- Name: capability capability_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.capability
    ADD CONSTRAINT capability_pkey PRIMARY KEY (capability_code);


--
-- Name: contact_method contact_method_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.contact_method
    ADD CONSTRAINT contact_method_pkey PRIMARY KEY (contact_id, method_kind);


--
-- Name: contact contact_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.contact
    ADD CONSTRAINT contact_pkey PRIMARY KEY (contact_id);


--
-- Name: custody_event custody_event_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.custody_event
    ADD CONSTRAINT custody_event_pkey PRIMARY KEY (event_id);


--
-- Name: donation donation_donation_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation
    ADD CONSTRAINT donation_donation_code_key UNIQUE (donation_code);


--
-- Name: donation_event donation_event_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation_event
    ADD CONSTRAINT donation_event_pkey PRIMARY KEY (event_id);


--
-- Name: donation donation_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation
    ADD CONSTRAINT donation_pkey PRIMARY KEY (donation_id);


--
-- Name: donation_unit donation_unit_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation_unit
    ADD CONSTRAINT donation_unit_pkey PRIMARY KEY (resource_id);


--
-- Name: donor donor_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donor
    ADD CONSTRAINT donor_pkey PRIMARY KEY (donor_id);


--
-- Name: donor_review donor_review_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donor_review
    ADD CONSTRAINT donor_review_pkey PRIMARY KEY (review_id);


--
-- Name: institution_capability institution_capability_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution_capability
    ADD CONSTRAINT institution_capability_pkey PRIMARY KEY (institution_id, capability_code);


--
-- Name: institution_contact institution_contact_contact_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution_contact
    ADD CONSTRAINT institution_contact_contact_id_key UNIQUE (contact_id);


--
-- Name: institution_contact institution_contact_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution_contact
    ADD CONSTRAINT institution_contact_pkey PRIMARY KEY (institution_id, contact_id);


--
-- Name: institution institution_institution_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution
    ADD CONSTRAINT institution_institution_code_key UNIQUE (institution_code);


--
-- Name: institution institution_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution
    ADD CONSTRAINT institution_pkey PRIMARY KEY (institution_id);


--
-- Name: login_attempt login_attempt_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.login_attempt
    ADD CONSTRAINT login_attempt_pkey PRIMARY KEY (attempt_id);


--
-- Name: notification notification_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.notification
    ADD CONSTRAINT notification_pkey PRIMARY KEY (notification_id);


--
-- Name: organ_allocation organ_allocation_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_allocation
    ADD CONSTRAINT organ_allocation_pkey PRIMARY KEY (allocation_id);


--
-- Name: organ_candidate organ_candidate_evaluation_id_recipient_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_candidate
    ADD CONSTRAINT organ_candidate_evaluation_id_recipient_id_key UNIQUE (evaluation_id, recipient_id);


--
-- Name: organ_candidate organ_candidate_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_candidate
    ADD CONSTRAINT organ_candidate_pkey PRIMARY KEY (candidate_id);


--
-- Name: organ_custody_event organ_custody_event_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_custody_event
    ADD CONSTRAINT organ_custody_event_pkey PRIMARY KEY (event_id);


--
-- Name: organ_donor organ_donor_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_donor
    ADD CONSTRAINT organ_donor_pkey PRIMARY KEY (donor_id);


--
-- Name: organ_donor organ_donor_record_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_donor
    ADD CONSTRAINT organ_donor_record_code_key UNIQUE (record_code);


--
-- Name: organ_evaluation organ_evaluation_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_evaluation
    ADD CONSTRAINT organ_evaluation_pkey PRIMARY KEY (evaluation_id);


--
-- Name: organ_offer organ_offer_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_offer
    ADD CONSTRAINT organ_offer_pkey PRIMARY KEY (offer_id);


--
-- Name: organ_offer organ_offer_record_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_offer
    ADD CONSTRAINT organ_offer_record_code_key UNIQUE (record_code);


--
-- Name: organ_recipient organ_recipient_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_recipient
    ADD CONSTRAINT organ_recipient_pkey PRIMARY KEY (recipient_id);


--
-- Name: organ_recipient organ_recipient_record_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_recipient
    ADD CONSTRAINT organ_recipient_record_code_key UNIQUE (record_code);


--
-- Name: organ_review organ_review_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_review
    ADD CONSTRAINT organ_review_pkey PRIMARY KEY (review_id);


--
-- Name: parameter_version parameter_version_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.parameter_version
    ADD CONSTRAINT parameter_version_pkey PRIMARY KEY (parameter_version_id);


--
-- Name: parameter_version parameter_version_region_name_parameter_code_version_no_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.parameter_version
    ADD CONSTRAINT parameter_version_region_name_parameter_code_version_no_key UNIQUE (region_name, parameter_code, version_no);


--
-- Name: party party_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.party
    ADD CONSTRAINT party_pkey PRIMARY KEY (party_id);


--
-- Name: recipient recipient_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.recipient
    ADD CONSTRAINT recipient_pkey PRIMARY KEY (recipient_id);


--
-- Name: regional_route regional_route_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.regional_route
    ADD CONSTRAINT regional_route_pkey PRIMARY KEY (route_id);


--
-- Name: request_event request_event_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.request_event
    ADD CONSTRAINT request_event_pkey PRIMARY KEY (event_id);


--
-- Name: resource resource_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.resource
    ADD CONSTRAINT resource_pkey PRIMARY KEY (resource_id);


--
-- Name: resource resource_traceability_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.resource
    ADD CONSTRAINT resource_traceability_code_key UNIQUE (traceability_code);


--
-- Name: role role_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.role
    ADD CONSTRAINT role_pkey PRIMARY KEY (role_code);


--
-- Name: schema_migration schema_migration_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.schema_migration
    ADD CONSTRAINT schema_migration_pkey PRIMARY KEY (version);


--
-- Name: service_activity_events service_activity_events_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_activity_events
    ADD CONSTRAINT service_activity_events_pkey PRIMARY KEY (service, id);


--
-- Name: service_decisions service_decisions_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_decisions
    ADD CONSTRAINT service_decisions_pkey PRIMARY KEY (service, id);


--
-- Name: service_health_check service_health_check_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_health_check
    ADD CONSTRAINT service_health_check_pkey PRIMARY KEY (check_id);


--
-- Name: service_idempotency service_idempotency_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_idempotency
    ADD CONSTRAINT service_idempotency_pkey PRIMARY KEY (service, id);


--
-- Name: service_idempotency service_idempotency_service_user_id_key_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_idempotency
    ADD CONSTRAINT service_idempotency_service_user_id_key_key UNIQUE (service, user_id, key);


--
-- Name: service_inbox service_inbox_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_inbox
    ADD CONSTRAINT service_inbox_pkey PRIMARY KEY (service, event_id);


--
-- Name: service_outbox service_outbox_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_outbox
    ADD CONSTRAINT service_outbox_pkey PRIMARY KEY (service, id);


--
-- Name: service_outbox service_outbox_service_event_id_target_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_outbox
    ADD CONSTRAINT service_outbox_service_event_id_target_key UNIQUE (service, event_id, target);


--
-- Name: service_schema_version service_schema_version_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_schema_version
    ADD CONSTRAINT service_schema_version_pkey PRIMARY KEY (service, version);


--
-- Name: service_worker_health service_worker_health_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.service_worker_health
    ADD CONSTRAINT service_worker_health_pkey PRIMARY KEY (service, id);


--
-- Name: shipment shipment_organ_allocation_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment
    ADD CONSTRAINT shipment_organ_allocation_id_key UNIQUE (organ_allocation_id);


--
-- Name: shipment shipment_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment
    ADD CONSTRAINT shipment_pkey PRIMARY KEY (shipment_id);


--
-- Name: site site_institution_id_site_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.site
    ADD CONSTRAINT site_institution_id_site_code_key UNIQUE (institution_id, site_code);


--
-- Name: site site_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.site
    ADD CONSTRAINT site_pkey PRIMARY KEY (site_id);


--
-- Name: site_schedule site_schedule_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.site_schedule
    ADD CONSTRAINT site_schedule_pkey PRIMARY KEY (schedule_id);


--
-- Name: site_schedule site_schedule_site_id_weekday_opens_at_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.site_schedule
    ADD CONSTRAINT site_schedule_site_id_weekday_opens_at_key UNIQUE (site_id, weekday, opens_at);


--
-- Name: storage_location storage_location_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.storage_location
    ADD CONSTRAINT storage_location_pkey PRIMARY KEY (location_id);


--
-- Name: storage_location storage_location_site_id_location_code_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.storage_location
    ADD CONSTRAINT storage_location_site_id_location_code_key UNIQUE (site_id, location_code);


--
-- Name: stored_file stored_file_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.stored_file
    ADD CONSTRAINT stored_file_pkey PRIMARY KEY (file_id);


--
-- Name: transport_telemetry transport_telemetry_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.transport_telemetry
    ADD CONSTRAINT transport_telemetry_pkey PRIMARY KEY (telemetry_id);


--
-- Name: user_account user_account_login_email_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.user_account
    ADD CONSTRAINT user_account_login_email_key UNIQUE (login_email);


--
-- Name: user_account user_account_party_id_key; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.user_account
    ADD CONSTRAINT user_account_party_id_key UNIQUE (party_id);


--
-- Name: user_account user_account_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.user_account
    ADD CONSTRAINT user_account_pkey PRIMARY KEY (account_id);


--
-- Name: web_session web_session_pkey; Type: CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.web_session
    ADD CONSTRAINT web_session_pkey PRIMARY KEY (session_id);


--
-- Name: account_role_scope_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX account_role_scope_idx ON red_house.account_role USING btree (institution_id);


--
-- Name: allocation_request_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX allocation_request_idx ON red_house.blood_allocation USING btree (request_id);


--
-- Name: allocation_resource_exclusive; Type: INDEX; Schema: red_house; Owner: -
--

CREATE UNIQUE INDEX allocation_resource_exclusive ON red_house.blood_allocation USING btree (resource_id) WHERE (current_status <> 'CANCELLED'::text);


--
-- Name: api_active_appointment; Type: INDEX; Schema: red_house; Owner: -
--

CREATE UNIQUE INDEX api_active_appointment ON red_house.appointment USING btree (donor_id, campaign_id) WHERE (current_status = 'BOOKED'::text);


--
-- Name: api_active_organ_request; Type: INDEX; Schema: red_house; Owner: -
--

CREATE UNIQUE INDEX api_active_organ_request ON red_house.blood_request USING btree (recipient_id) WHERE ((kind = 'ORGAN'::text) AND (current_status = ANY (ARRAY['OPEN'::text, 'IN_PROGRESS'::text])));


--
-- Name: api_audit_finding_actions_timeline; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX api_audit_finding_actions_timeline ON red_house.audit_finding_actions USING btree (finding_id, created_at, id);


--
-- Name: api_audit_findings_scope; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX api_audit_findings_scope ON red_house.audit_findings USING btree (region_id, assignee_id, status, created_at);


--
-- Name: api_audit_search; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX api_audit_search ON red_house.audit_event USING btree (region_id, institution_id, occurred_at);


--
-- Name: api_availability_page; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX api_availability_page ON red_house.resource USING btree (region_id, expires_at, resource_id) WHERE (status = 'AVAILABLE'::text);


--
-- Name: api_available_resources; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX api_available_resources ON red_house.resource USING btree (region_id, resource_kind, component, expires_at) WHERE (status = 'AVAILABLE'::text);


--
-- Name: api_catalogue_tenant; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX api_catalogue_tenant ON red_house.catalogue_entry USING btree (tenant_id, kind, name, id);


--
-- Name: api_checks_latest; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX api_checks_latest ON red_house.service_health_check USING btree (service, checked_at DESC);


--
-- Name: api_donor_account; Type: INDEX; Schema: red_house; Owner: -
--

CREATE UNIQUE INDEX api_donor_account ON red_house.donor USING btree (account_id) WHERE (account_id IS NOT NULL);


--
-- Name: api_organ_patient_reserved; Type: INDEX; Schema: red_house; Owner: -
--

CREATE UNIQUE INDEX api_organ_patient_reserved ON red_house.request_hold USING btree (recipient_id) WHERE ((kind = 'ORGAN'::text) AND (status = ANY (ARRAY['HELD'::text, 'CONFIRMED'::text, 'RECEIVED'::text])));


--
-- Name: api_resource_reserved; Type: INDEX; Schema: red_house; Owner: -
--

CREATE UNIQUE INDEX api_resource_reserved ON red_house.blood_allocation USING btree (resource_id) WHERE (current_status <> 'CANCELLED'::text);


--
-- Name: appointment_active; Type: INDEX; Schema: red_house; Owner: -
--

CREATE UNIQUE INDEX appointment_active ON red_house.appointment USING btree (donor_id, campaign_id) WHERE (current_status = 'BOOKED'::text);


--
-- Name: audit_action_search; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX audit_action_search ON red_house.audit_event USING btree (region_id, action, actor_id);


--
-- Name: audit_correlation_search; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX audit_correlation_search ON red_house.audit_event USING btree (region_id, ((event ->> 'correlation_id'::text)));


--
-- Name: audit_execution_search; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX audit_execution_search ON red_house.audit_event USING btree (region_id, access_auditoria.event_time((event ->> 'occurred_at'::text)), event_id);


--
-- Name: audit_finding_actions_timeline; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX audit_finding_actions_timeline ON red_house.audit_finding_actions USING btree (finding_id, created_at, id);


--
-- Name: audit_findings_scope; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX audit_findings_scope ON red_house.audit_findings USING btree (region_id, assignee_id, status, created_at);


--
-- Name: audit_region_time_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX audit_region_time_idx ON red_house.audit_event USING btree (region_name, occurred_at DESC);


--
-- Name: audit_resource_search; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX audit_resource_search ON red_house.audit_event USING btree (region_id, ((event ->> 'resource_id'::text)));


--
-- Name: audit_scope_time_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX audit_scope_time_idx ON red_house.audit_event USING btree (institution_id, occurred_at DESC);


--
-- Name: blood_unit_component_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX blood_unit_component_idx ON red_house.blood_unit USING btree (component_id);


--
-- Name: blood_unit_expiry_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX blood_unit_expiry_idx ON red_house.blood_unit USING btree (expires_at) WHERE ((current_status)::text = 'AVAILABLE'::text);


--
-- Name: blood_unit_location_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX blood_unit_location_idx ON red_house.blood_unit USING btree (location_id);


--
-- Name: donor_institution_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX donor_institution_idx ON red_house.donor USING btree (institution_id);


--
-- Name: health_service_time; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX health_service_time ON red_house.service_health_check USING btree (service, checked_at DESC);


--
-- Name: login_address_time_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX login_address_time_idx ON red_house.login_attempt USING btree (address_hash, occurred_at DESC);


--
-- Name: login_identity_time_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX login_identity_time_idx ON red_house.login_attempt USING btree (identity_hash, occurred_at DESC);


--
-- Name: organ_candidates_offer; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX organ_candidates_offer ON red_house.organ_candidate USING btree (offer_id, evaluated_at);


--
-- Name: organ_custody_allocation; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX organ_custody_allocation ON red_house.organ_custody_event USING btree (allocation_id, occurred_at);


--
-- Name: organ_exclusive_offer; Type: INDEX; Schema: red_house; Owner: -
--

CREATE UNIQUE INDEX organ_exclusive_offer ON red_house.organ_allocation USING btree (offer_id) WHERE ((current_status)::text <> 'CANCELLED'::text);


--
-- Name: organ_exclusive_recipient; Type: INDEX; Schema: red_house; Owner: -
--

CREATE UNIQUE INDEX organ_exclusive_recipient ON red_house.organ_allocation USING btree (recipient_id) WHERE ((current_status)::text <> 'CANCELLED'::text);


--
-- Name: recipient_institution_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX recipient_institution_idx ON red_house.recipient USING btree (institution_id);


--
-- Name: request_queue_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX request_queue_idx ON red_house.blood_request USING btree (current_status, urgency, requested_at);


--
-- Name: request_recipient_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX request_recipient_idx ON red_house.blood_request USING btree (recipient_id);


--
-- Name: shared_outbox_pending; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX shared_outbox_pending ON red_house.service_outbox USING btree (service, next_attempt, created_at) WHERE (delivered_at IS NULL);


--
-- Name: shipment_transport_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX shipment_transport_idx ON red_house.shipment USING btree (transport_id);


--
-- Name: site_institution_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX site_institution_idx ON red_house.site USING btree (institution_id);


--
-- Name: storage_site_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX storage_site_idx ON red_house.storage_location USING btree (site_id);


--
-- Name: telemetry_shipment_time; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX telemetry_shipment_time ON red_house.transport_telemetry USING btree (shipment_id, captured_at);


--
-- Name: web_session_account_idx; Type: INDEX; Schema: red_house; Owner: -
--

CREATE INDEX web_session_account_idx ON red_house.web_session USING btree (account_id);


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_alertas; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_alertas.activity_events FOR EACH ROW EXECUTE FUNCTION access_alertas.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_alertas; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_alertas.decisions FOR EACH ROW EXECUTE FUNCTION access_alertas.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_alertas; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_alertas.idempotency FOR EACH ROW EXECUTE FUNCTION access_alertas.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_alertas; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_alertas.inbox FOR EACH ROW EXECUTE FUNCTION access_alertas.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_alertas; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_alertas.outbox FOR EACH ROW EXECUTE FUNCTION access_alertas.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_alertas; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_alertas.schema_version FOR EACH ROW EXECUTE FUNCTION access_alertas.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_alertas; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_alertas.worker_health FOR EACH ROW EXECUTE FUNCTION access_alertas.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_auditoria; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_auditoria.activity_events FOR EACH ROW EXECUTE FUNCTION access_auditoria.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_auditoria; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_auditoria.decisions FOR EACH ROW EXECUTE FUNCTION access_auditoria.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_auditoria; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_auditoria.idempotency FOR EACH ROW EXECUTE FUNCTION access_auditoria.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_auditoria; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_auditoria.inbox FOR EACH ROW EXECUTE FUNCTION access_auditoria.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_auditoria; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_auditoria.outbox FOR EACH ROW EXECUTE FUNCTION access_auditoria.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_auditoria; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_auditoria.schema_version FOR EACH ROW EXECUTE FUNCTION access_auditoria.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_auditoria; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_auditoria.worker_health FOR EACH ROW EXECUTE FUNCTION access_auditoria.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_compatibilidad; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_compatibilidad.activity_events FOR EACH ROW EXECUTE FUNCTION access_compatibilidad.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_compatibilidad; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_compatibilidad.decisions FOR EACH ROW EXECUTE FUNCTION access_compatibilidad.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_compatibilidad; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_compatibilidad.idempotency FOR EACH ROW EXECUTE FUNCTION access_compatibilidad.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_compatibilidad; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_compatibilidad.inbox FOR EACH ROW EXECUTE FUNCTION access_compatibilidad.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_compatibilidad; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_compatibilidad.outbox FOR EACH ROW EXECUTE FUNCTION access_compatibilidad.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_compatibilidad; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_compatibilidad.schema_version FOR EACH ROW EXECUTE FUNCTION access_compatibilidad.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_compatibilidad; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_compatibilidad.worker_health FOR EACH ROW EXECUTE FUNCTION access_compatibilidad.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_custodia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_custodia.activity_events FOR EACH ROW EXECUTE FUNCTION access_custodia.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_custodia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_custodia.decisions FOR EACH ROW EXECUTE FUNCTION access_custodia.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_custodia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_custodia.idempotency FOR EACH ROW EXECUTE FUNCTION access_custodia.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_custodia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_custodia.inbox FOR EACH ROW EXECUTE FUNCTION access_custodia.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_custodia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_custodia.outbox FOR EACH ROW EXECUTE FUNCTION access_custodia.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_custodia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_custodia.schema_version FOR EACH ROW EXECUTE FUNCTION access_custodia.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_custodia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_custodia.worker_health FOR EACH ROW EXECUTE FUNCTION access_custodia.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_donantes; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_donantes.activity_events FOR EACH ROW EXECUTE FUNCTION access_donantes.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_donantes; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_donantes.decisions FOR EACH ROW EXECUTE FUNCTION access_donantes.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_donantes; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_donantes.idempotency FOR EACH ROW EXECUTE FUNCTION access_donantes.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_donantes; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_donantes.inbox FOR EACH ROW EXECUTE FUNCTION access_donantes.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_donantes; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_donantes.outbox FOR EACH ROW EXECUTE FUNCTION access_donantes.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_donantes; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_donantes.schema_version FOR EACH ROW EXECUTE FUNCTION access_donantes.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_donantes; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_donantes.worker_health FOR EACH ROW EXECUTE FUNCTION access_donantes.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_identidad_acceso; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_identidad_acceso.activity_events FOR EACH ROW EXECUTE FUNCTION access_identidad_acceso.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_identidad_acceso; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_identidad_acceso.decisions FOR EACH ROW EXECUTE FUNCTION access_identidad_acceso.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_identidad_acceso; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_identidad_acceso.idempotency FOR EACH ROW EXECUTE FUNCTION access_identidad_acceso.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_identidad_acceso; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_identidad_acceso.inbox FOR EACH ROW EXECUTE FUNCTION access_identidad_acceso.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_identidad_acceso; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_identidad_acceso.outbox FOR EACH ROW EXECUTE FUNCTION access_identidad_acceso.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_identidad_acceso; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_identidad_acceso.schema_version FOR EACH ROW EXECUTE FUNCTION access_identidad_acceso.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_identidad_acceso; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_identidad_acceso.worker_health FOR EACH ROW EXECUTE FUNCTION access_identidad_acceso.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_inventario; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_inventario.activity_events FOR EACH ROW EXECUTE FUNCTION access_inventario.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_inventario; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_inventario.decisions FOR EACH ROW EXECUTE FUNCTION access_inventario.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_inventario; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_inventario.idempotency FOR EACH ROW EXECUTE FUNCTION access_inventario.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_inventario; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_inventario.inbox FOR EACH ROW EXECUTE FUNCTION access_inventario.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_inventario; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_inventario.outbox FOR EACH ROW EXECUTE FUNCTION access_inventario.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_inventario; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_inventario.schema_version FOR EACH ROW EXECUTE FUNCTION access_inventario.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_inventario; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_inventario.worker_health FOR EACH ROW EXECUTE FUNCTION access_inventario.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_monitoreo; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_monitoreo.activity_events FOR EACH ROW EXECUTE FUNCTION access_monitoreo.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_monitoreo; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_monitoreo.decisions FOR EACH ROW EXECUTE FUNCTION access_monitoreo.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_monitoreo; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_monitoreo.idempotency FOR EACH ROW EXECUTE FUNCTION access_monitoreo.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_monitoreo; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_monitoreo.inbox FOR EACH ROW EXECUTE FUNCTION access_monitoreo.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_monitoreo; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_monitoreo.outbox FOR EACH ROW EXECUTE FUNCTION access_monitoreo.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_monitoreo; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_monitoreo.schema_version FOR EACH ROW EXECUTE FUNCTION access_monitoreo.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_monitoreo; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_monitoreo.worker_health FOR EACH ROW EXECUTE FUNCTION access_monitoreo.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_priorizacion_geografia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_priorizacion_geografia.activity_events FOR EACH ROW EXECUTE FUNCTION access_priorizacion_geografia.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_priorizacion_geografia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_priorizacion_geografia.decisions FOR EACH ROW EXECUTE FUNCTION access_priorizacion_geografia.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_priorizacion_geografia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_priorizacion_geografia.idempotency FOR EACH ROW EXECUTE FUNCTION access_priorizacion_geografia.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_priorizacion_geografia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_priorizacion_geografia.inbox FOR EACH ROW EXECUTE FUNCTION access_priorizacion_geografia.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_priorizacion_geografia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_priorizacion_geografia.outbox FOR EACH ROW EXECUTE FUNCTION access_priorizacion_geografia.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_priorizacion_geografia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_priorizacion_geografia.schema_version FOR EACH ROW EXECUTE FUNCTION access_priorizacion_geografia.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_priorizacion_geografia; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_priorizacion_geografia.worker_health FOR EACH ROW EXECUTE FUNCTION access_priorizacion_geografia.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_receptores; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_receptores.activity_events FOR EACH ROW EXECUTE FUNCTION access_receptores.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_receptores; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_receptores.decisions FOR EACH ROW EXECUTE FUNCTION access_receptores.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_receptores; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_receptores.idempotency FOR EACH ROW EXECUTE FUNCTION access_receptores.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_receptores; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_receptores.inbox FOR EACH ROW EXECUTE FUNCTION access_receptores.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_receptores; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_receptores.outbox FOR EACH ROW EXECUTE FUNCTION access_receptores.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_receptores; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_receptores.schema_version FOR EACH ROW EXECUTE FUNCTION access_receptores.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_receptores; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_receptores.worker_health FOR EACH ROW EXECUTE FUNCTION access_receptores.insert_worker_health();


--
-- Name: activity_events scoped_insert; Type: TRIGGER; Schema: access_transporte; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_transporte.activity_events FOR EACH ROW EXECUTE FUNCTION access_transporte.insert_activity_events();


--
-- Name: decisions scoped_insert; Type: TRIGGER; Schema: access_transporte; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_transporte.decisions FOR EACH ROW EXECUTE FUNCTION access_transporte.insert_decisions();


--
-- Name: idempotency scoped_insert; Type: TRIGGER; Schema: access_transporte; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_transporte.idempotency FOR EACH ROW EXECUTE FUNCTION access_transporte.insert_idempotency();


--
-- Name: inbox scoped_insert; Type: TRIGGER; Schema: access_transporte; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_transporte.inbox FOR EACH ROW EXECUTE FUNCTION access_transporte.insert_inbox();


--
-- Name: outbox scoped_insert; Type: TRIGGER; Schema: access_transporte; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_transporte.outbox FOR EACH ROW EXECUTE FUNCTION access_transporte.insert_outbox();


--
-- Name: schema_version scoped_insert; Type: TRIGGER; Schema: access_transporte; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_transporte.schema_version FOR EACH ROW EXECUTE FUNCTION access_transporte.insert_schema_version();


--
-- Name: worker_health scoped_insert; Type: TRIGGER; Schema: access_transporte; Owner: -
--

CREATE TRIGGER scoped_insert INSTEAD OF INSERT ON access_transporte.worker_health FOR EACH ROW EXECUTE FUNCTION access_transporte.insert_worker_health();


--
-- Name: algorithm_run algorithm_run_history; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER algorithm_run_history BEFORE DELETE OR UPDATE ON red_house.algorithm_run FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: catalogue_entry api_catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER api_catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.catalogue_entry FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: audit_finding_actions api_immutable; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER api_immutable BEFORE DELETE OR UPDATE ON red_house.audit_finding_actions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: audit_finding_links api_immutable; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER api_immutable BEFORE DELETE OR UPDATE ON red_house.audit_finding_links FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: shipment_transition api_immutable; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER api_immutable BEFORE DELETE OR UPDATE ON red_house.shipment_transition FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: resource api_inventory_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER api_inventory_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.resource FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_inventory_cache();


--
-- Name: audit_event audit_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER audit_append_only BEFORE DELETE OR UPDATE ON red_house.audit_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: audit_change audit_change_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER audit_change_append_only BEFORE DELETE OR UPDATE ON red_house.audit_change FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: blood_review blood_review_history; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER blood_review_history BEFORE DELETE OR UPDATE ON red_house.blood_review FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: blood_candidate candidate_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER candidate_append_only BEFORE DELETE OR UPDATE ON red_house.blood_candidate FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: capability catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.capability FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: contact catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.contact FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: contact_method catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.contact_method FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: institution catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.institution FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: institution_capability catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.institution_capability FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: institution_contact catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.institution_contact FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: site catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.site FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: site_schedule catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.site_schedule FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: storage_location catalogue_cache; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER catalogue_cache AFTER INSERT OR DELETE OR UPDATE OR TRUNCATE ON red_house.storage_location FOR EACH STATEMENT EXECUTE FUNCTION red_house.bump_read_cache();


--
-- Name: custody_event custody_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER custody_append_only BEFORE DELETE OR UPDATE ON red_house.custody_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: donation_event donation_event_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER donation_event_append_only BEFORE DELETE OR UPDATE ON red_house.donation_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: donation_unit donation_unit_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER donation_unit_append_only BEFORE DELETE OR UPDATE ON red_house.donation_unit FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: donor_review donor_review_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER donor_review_append_only BEFORE DELETE OR UPDATE ON red_house.donor_review FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: candidate_evaluation evaluation_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER evaluation_append_only BEFORE DELETE OR UPDATE ON red_house.candidate_evaluation FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: service_health_check health_check_history; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER health_check_history BEFORE DELETE OR UPDATE ON red_house.service_health_check FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: service_activity_events immutable; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER immutable BEFORE DELETE OR UPDATE ON red_house.service_activity_events FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: service_decisions immutable; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER immutable BEFORE DELETE OR UPDATE ON red_house.service_decisions FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: blood_movement movement_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER movement_append_only BEFORE DELETE OR UPDATE ON red_house.blood_movement FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: organ_candidate organ_candidate_history; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER organ_candidate_history BEFORE DELETE OR UPDATE ON red_house.organ_candidate FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: organ_custody_event organ_custody_history; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER organ_custody_history BEFORE DELETE OR UPDATE ON red_house.organ_custody_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: organ_donor organ_donor_history; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER organ_donor_history BEFORE DELETE OR UPDATE ON red_house.organ_donor FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: organ_evaluation organ_evaluation_history; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER organ_evaluation_history BEFORE DELETE OR UPDATE ON red_house.organ_evaluation FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: organ_review organ_review_history; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER organ_review_history BEFORE DELETE OR UPDATE ON red_house.organ_review FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: parameter_version parameter_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER parameter_append_only BEFORE DELETE OR UPDATE ON red_house.parameter_version FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: request_event request_event_append_only; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER request_event_append_only BEFORE DELETE OR UPDATE ON red_house.request_event FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: transport_telemetry telemetry_history; Type: TRIGGER; Schema: red_house; Owner: -
--

CREATE TRIGGER telemetry_history BEFORE DELETE OR UPDATE ON red_house.transport_telemetry FOR EACH ROW EXECUTE FUNCTION red_house.reject_history_mutation();


--
-- Name: account_role account_role_account_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.account_role
    ADD CONSTRAINT account_role_account_id_fkey FOREIGN KEY (account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: account_role account_role_institution_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.account_role
    ADD CONSTRAINT account_role_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: account_role account_role_role_code_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.account_role
    ADD CONSTRAINT account_role_role_code_fkey FOREIGN KEY (role_code) REFERENCES red_house.role(role_code) DEFERRABLE;


--
-- Name: algorithm_run algorithm_run_actor_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.algorithm_run
    ADD CONSTRAINT algorithm_run_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: algorithm_run algorithm_run_blood_evaluation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.algorithm_run
    ADD CONSTRAINT algorithm_run_blood_evaluation_id_fkey FOREIGN KEY (blood_evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE;


--
-- Name: algorithm_run algorithm_run_institution_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.algorithm_run
    ADD CONSTRAINT algorithm_run_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: algorithm_run algorithm_run_organ_evaluation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.algorithm_run
    ADD CONSTRAINT algorithm_run_organ_evaluation_id_fkey FOREIGN KEY (organ_evaluation_id) REFERENCES red_house.organ_evaluation(evaluation_id) DEFERRABLE;


--
-- Name: appointment api_appointments_campaign_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.appointment
    ADD CONSTRAINT api_appointments_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES red_house.campaign(campaign_id) DEFERRABLE;


--
-- Name: appointment api_appointments_donor_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.appointment
    ADD CONSTRAINT api_appointments_donor_id_fkey FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id) DEFERRABLE;


--
-- Name: audit_finding_actions api_audit_finding_actions_finding_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_finding_actions
    ADD CONSTRAINT api_audit_finding_actions_finding_id_fkey FOREIGN KEY (finding_id) REFERENCES red_house.audit_findings(id) DEFERRABLE;


--
-- Name: audit_finding_links api_audit_finding_links_event_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_finding_links
    ADD CONSTRAINT api_audit_finding_links_event_id_fkey FOREIGN KEY (event_id) REFERENCES red_house.audit_event(event_id) DEFERRABLE;


--
-- Name: audit_finding_links api_audit_finding_links_finding_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_finding_links
    ADD CONSTRAINT api_audit_finding_links_finding_id_fkey FOREIGN KEY (finding_id) REFERENCES red_house.audit_findings(id) DEFERRABLE;


--
-- Name: catalogue_entry api_catalogue_parent_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.catalogue_entry
    ADD CONSTRAINT api_catalogue_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES red_house.catalogue_entry(id) DEFERRABLE;


--
-- Name: catalogue_entry api_catalogue_tenant_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.catalogue_entry
    ADD CONSTRAINT api_catalogue_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: custody_event api_custody_events_shipment_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.custody_event
    ADD CONSTRAINT api_custody_events_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES red_house.custody_chain(id) DEFERRABLE;


--
-- Name: donation_event api_donation_steps_donation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation_event
    ADD CONSTRAINT api_donation_steps_donation_id_fkey FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id) DEFERRABLE;


--
-- Name: donation api_donations_donor_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation
    ADD CONSTRAINT api_donations_donor_id_fkey FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id) DEFERRABLE;


--
-- Name: donor_review api_donor_reviews_donor_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donor_review
    ADD CONSTRAINT api_donor_reviews_donor_id_fkey FOREIGN KEY (donor_id) REFERENCES red_house.donor(donor_id) DEFERRABLE;


--
-- Name: stored_file api_files_shipment_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.stored_file
    ADD CONSTRAINT api_files_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE;


--
-- Name: request_hold api_holds_recipient_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.request_hold
    ADD CONSTRAINT api_holds_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES red_house.recipient(recipient_id) DEFERRABLE;


--
-- Name: request_hold api_holds_request_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.request_hold
    ADD CONSTRAINT api_holds_request_id_fkey FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE;


--
-- Name: institution api_institutions_created_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution
    ADD CONSTRAINT api_institutions_created_by_fkey FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: blood_movement api_movements_resource_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_movement
    ADD CONSTRAINT api_movements_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE;


--
-- Name: blood_request api_requests_recipient_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_request
    ADD CONSTRAINT api_requests_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES red_house.recipient(recipient_id) DEFERRABLE;


--
-- Name: blood_allocation api_reservations_operation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT api_reservations_operation_id_fkey FOREIGN KEY (operation_id) REFERENCES red_house.allocation_operation(id) DEFERRABLE;


--
-- Name: blood_allocation api_reservations_resource_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT api_reservations_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE;


--
-- Name: resource_review api_resource_reviews_resource_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.resource_review
    ADD CONSTRAINT api_resource_reviews_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE;


--
-- Name: blood_review api_reviews_evaluation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_review
    ADD CONSTRAINT api_reviews_evaluation_id_fkey FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE;


--
-- Name: web_session api_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.web_session
    ADD CONSTRAINT api_sessions_user_id_fkey FOREIGN KEY (account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: transport_telemetry api_telemetry_shipment_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.transport_telemetry
    ADD CONSTRAINT api_telemetry_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE;


--
-- Name: shipment_transition api_transitions_shipment_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment_transition
    ADD CONSTRAINT api_transitions_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE;


--
-- Name: user_account api_users_tenant_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.user_account
    ADD CONSTRAINT api_users_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: audit_change audit_change_event_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_change
    ADD CONSTRAINT audit_change_event_id_fkey FOREIGN KEY (event_id) REFERENCES red_house.audit_event(event_id) DEFERRABLE;


--
-- Name: blood_allocation blood_allocation_authorized_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT blood_allocation_authorized_by_fkey FOREIGN KEY (authorized_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: blood_allocation blood_allocation_candidate_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT blood_allocation_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES red_house.blood_candidate(candidate_id) DEFERRABLE;


--
-- Name: blood_allocation blood_allocation_review_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT blood_allocation_review_id_fkey FOREIGN KEY (review_id) REFERENCES red_house.blood_review(review_id) DEFERRABLE;


--
-- Name: blood_candidate blood_candidate_evaluation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_candidate
    ADD CONSTRAINT blood_candidate_evaluation_id_fkey FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE;


--
-- Name: blood_candidate blood_candidate_resource_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_candidate
    ADD CONSTRAINT blood_candidate_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES red_house.blood_unit(resource_id) DEFERRABLE;


--
-- Name: blood_classification blood_classification_resource_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_classification
    ADD CONSTRAINT blood_classification_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES red_house.blood_unit(resource_id) DEFERRABLE;


--
-- Name: blood_movement blood_movement_destination_location_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_movement
    ADD CONSTRAINT blood_movement_destination_location_id_fkey FOREIGN KEY (destination_location_id) REFERENCES red_house.storage_location(location_id) DEFERRABLE;


--
-- Name: blood_movement blood_movement_origin_location_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_movement
    ADD CONSTRAINT blood_movement_origin_location_id_fkey FOREIGN KEY (origin_location_id) REFERENCES red_house.storage_location(location_id) DEFERRABLE;


--
-- Name: blood_request blood_request_component_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_request
    ADD CONSTRAINT blood_request_component_id_fkey FOREIGN KEY (component_id) REFERENCES red_house.blood_component(component_id) DEFERRABLE;


--
-- Name: blood_request blood_request_responsible_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_request
    ADD CONSTRAINT blood_request_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: blood_review blood_review_candidate_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_review
    ADD CONSTRAINT blood_review_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES red_house.blood_candidate(candidate_id) DEFERRABLE;


--
-- Name: blood_unit blood_unit_component_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_unit
    ADD CONSTRAINT blood_unit_component_id_fkey FOREIGN KEY (component_id) REFERENCES red_house.blood_component(component_id) DEFERRABLE;


--
-- Name: blood_unit blood_unit_location_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_unit
    ADD CONSTRAINT blood_unit_location_id_fkey FOREIGN KEY (location_id) REFERENCES red_house.storage_location(location_id) DEFERRABLE;


--
-- Name: blood_unit blood_unit_resource_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_unit
    ADD CONSTRAINT blood_unit_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE;


--
-- Name: candidate_evaluation candidate_evaluation_actor_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.candidate_evaluation
    ADD CONSTRAINT candidate_evaluation_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: contact_method contact_method_contact_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.contact_method
    ADD CONSTRAINT contact_method_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES red_house.contact(contact_id) DEFERRABLE;


--
-- Name: custody_event custody_event_actor_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.custody_event
    ADD CONSTRAINT custody_event_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: donation donation_created_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation
    ADD CONSTRAINT donation_created_by_fkey FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: donation donation_review_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation
    ADD CONSTRAINT donation_review_id_fkey FOREIGN KEY (review_id) REFERENCES red_house.donor_review(review_id) DEFERRABLE;


--
-- Name: donation_unit donation_unit_donation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation_unit
    ADD CONSTRAINT donation_unit_donation_id_fkey FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id) DEFERRABLE;


--
-- Name: donation_unit donation_unit_released_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation_unit
    ADD CONSTRAINT donation_unit_released_by_fkey FOREIGN KEY (released_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: donation_unit donation_unit_resource_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation_unit
    ADD CONSTRAINT donation_unit_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES red_house.blood_unit(resource_id) DEFERRABLE;


--
-- Name: donor donor_created_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donor
    ADD CONSTRAINT donor_created_by_fkey FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: institution_capability institution_capability_capability_code_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution_capability
    ADD CONSTRAINT institution_capability_capability_code_fkey FOREIGN KEY (capability_code) REFERENCES red_house.capability(capability_code) DEFERRABLE;


--
-- Name: institution_capability institution_capability_institution_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution_capability
    ADD CONSTRAINT institution_capability_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: institution_contact institution_contact_contact_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution_contact
    ADD CONSTRAINT institution_contact_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES red_house.contact(contact_id) DEFERRABLE;


--
-- Name: institution_contact institution_contact_institution_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.institution_contact
    ADD CONSTRAINT institution_contact_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: organ_allocation organ_allocation_authorized_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_allocation
    ADD CONSTRAINT organ_allocation_authorized_by_fkey FOREIGN KEY (authorized_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: organ_allocation organ_allocation_candidate_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_allocation
    ADD CONSTRAINT organ_allocation_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES red_house.organ_candidate(candidate_id) DEFERRABLE;


--
-- Name: organ_allocation organ_allocation_offer_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_allocation
    ADD CONSTRAINT organ_allocation_offer_id_fkey FOREIGN KEY (offer_id) REFERENCES red_house.organ_offer(offer_id) DEFERRABLE;


--
-- Name: organ_allocation organ_allocation_recipient_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_allocation
    ADD CONSTRAINT organ_allocation_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES red_house.organ_recipient(recipient_id) DEFERRABLE;


--
-- Name: organ_allocation organ_allocation_review_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_allocation
    ADD CONSTRAINT organ_allocation_review_id_fkey FOREIGN KEY (review_id) REFERENCES red_house.organ_review(review_id) DEFERRABLE;


--
-- Name: organ_allocation organ_allocation_transport_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_allocation
    ADD CONSTRAINT organ_allocation_transport_id_fkey FOREIGN KEY (transport_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: organ_candidate organ_candidate_evaluated_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_candidate
    ADD CONSTRAINT organ_candidate_evaluated_by_fkey FOREIGN KEY (evaluated_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: organ_candidate organ_candidate_evaluation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_candidate
    ADD CONSTRAINT organ_candidate_evaluation_id_fkey FOREIGN KEY (evaluation_id) REFERENCES red_house.organ_evaluation(evaluation_id) DEFERRABLE;


--
-- Name: organ_candidate organ_candidate_offer_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_candidate
    ADD CONSTRAINT organ_candidate_offer_id_fkey FOREIGN KEY (offer_id) REFERENCES red_house.organ_offer(offer_id) DEFERRABLE;


--
-- Name: organ_candidate organ_candidate_recipient_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_candidate
    ADD CONSTRAINT organ_candidate_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES red_house.organ_recipient(recipient_id) DEFERRABLE;


--
-- Name: organ_custody_event organ_custody_event_actor_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_custody_event
    ADD CONSTRAINT organ_custody_event_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: organ_custody_event organ_custody_event_allocation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_custody_event
    ADD CONSTRAINT organ_custody_event_allocation_id_fkey FOREIGN KEY (allocation_id) REFERENCES red_house.organ_allocation(allocation_id) DEFERRABLE;


--
-- Name: organ_donor organ_donor_institution_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_donor
    ADD CONSTRAINT organ_donor_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: organ_donor organ_donor_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_donor
    ADD CONSTRAINT organ_donor_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: organ_evaluation organ_evaluation_evaluated_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_evaluation
    ADD CONSTRAINT organ_evaluation_evaluated_by_fkey FOREIGN KEY (evaluated_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: organ_evaluation organ_evaluation_offer_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_evaluation
    ADD CONSTRAINT organ_evaluation_offer_id_fkey FOREIGN KEY (offer_id) REFERENCES red_house.organ_offer(offer_id) DEFERRABLE;


--
-- Name: organ_offer organ_offer_donor_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_offer
    ADD CONSTRAINT organ_offer_donor_id_fkey FOREIGN KEY (donor_id) REFERENCES red_house.organ_donor(donor_id) DEFERRABLE;


--
-- Name: organ_offer organ_offer_released_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_offer
    ADD CONSTRAINT organ_offer_released_by_fkey FOREIGN KEY (released_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: organ_recipient organ_recipient_institution_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_recipient
    ADD CONSTRAINT organ_recipient_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: organ_recipient organ_recipient_responsible_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_recipient
    ADD CONSTRAINT organ_recipient_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: organ_review organ_review_candidate_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_review
    ADD CONSTRAINT organ_review_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES red_house.organ_candidate(candidate_id) DEFERRABLE;


--
-- Name: organ_review organ_review_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.organ_review
    ADD CONSTRAINT organ_review_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: parameter_version parameter_version_approved_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.parameter_version
    ADD CONSTRAINT parameter_version_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: recipient recipient_responsible_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.recipient
    ADD CONSTRAINT recipient_responsible_id_fkey FOREIGN KEY (responsible_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: regional_route regional_route_recorded_by_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.regional_route
    ADD CONSTRAINT regional_route_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: request_event request_event_actor_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.request_event
    ADD CONSTRAINT request_event_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: request_event request_event_request_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.request_event
    ADD CONSTRAINT request_event_request_id_fkey FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE;


--
-- Name: notification shared_alerts_acknowledged_by; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.notification
    ADD CONSTRAINT shared_alerts_acknowledged_by FOREIGN KEY (acknowledged_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: notification shared_alerts_target_user_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.notification
    ADD CONSTRAINT shared_alerts_target_user_id FOREIGN KEY (target_account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: notification shared_alerts_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.notification
    ADD CONSTRAINT shared_alerts_tenant_id FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: appointment shared_appointments_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.appointment
    ADD CONSTRAINT shared_appointments_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: audit_event shared_audit_events_actor_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_event
    ADD CONSTRAINT shared_audit_events_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: audit_event shared_audit_events_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_event
    ADD CONSTRAINT shared_audit_events_tenant_id FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: audit_finding_actions shared_audit_finding_actions_actor_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_finding_actions
    ADD CONSTRAINT shared_audit_finding_actions_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: audit_findings shared_audit_findings_assignee_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_findings
    ADD CONSTRAINT shared_audit_findings_assignee_id FOREIGN KEY (assignee_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: audit_findings shared_audit_findings_assignee_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_findings
    ADD CONSTRAINT shared_audit_findings_assignee_tenant_id FOREIGN KEY (assignee_tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: audit_findings shared_audit_findings_created_by; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_findings
    ADD CONSTRAINT shared_audit_findings_created_by FOREIGN KEY (created_by) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: audit_findings shared_audit_findings_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.audit_findings
    ADD CONSTRAINT shared_audit_findings_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: campaign shared_campaigns_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.campaign
    ADD CONSTRAINT shared_campaigns_tenant_id FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: custody_chain shared_chains_destination_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.custody_chain
    ADD CONSTRAINT shared_chains_destination_id FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: custody_chain shared_chains_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.custody_chain
    ADD CONSTRAINT shared_chains_id FOREIGN KEY (id) REFERENCES red_house.shipment(shipment_id) DEFERRABLE;


--
-- Name: custody_chain shared_chains_origin_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.custody_chain
    ADD CONSTRAINT shared_chains_origin_id FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: donation_event shared_donation_steps_actor_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation_event
    ADD CONSTRAINT shared_donation_steps_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: donation shared_donations_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donation
    ADD CONSTRAINT shared_donations_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: donor_review shared_donor_reviews_actor_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donor_review
    ADD CONSTRAINT shared_donor_reviews_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: donor shared_donors_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donor
    ADD CONSTRAINT shared_donors_tenant_id FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: donor shared_donors_user_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.donor
    ADD CONSTRAINT shared_donors_user_id FOREIGN KEY (account_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: candidate_evaluation shared_evaluations_request_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.candidate_evaluation
    ADD CONSTRAINT shared_evaluations_request_id FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE;


--
-- Name: candidate_evaluation shared_evaluations_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.candidate_evaluation
    ADD CONSTRAINT shared_evaluations_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: stored_file shared_files_owner_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.stored_file
    ADD CONSTRAINT shared_files_owner_id FOREIGN KEY (owner_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: request_hold shared_holds_resource_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.request_hold
    ADD CONSTRAINT shared_holds_resource_id FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE;


--
-- Name: blood_movement shared_movements_actor_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_movement
    ADD CONSTRAINT shared_movements_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: allocation_operation shared_operations_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.allocation_operation
    ADD CONSTRAINT shared_operations_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: allocation_operation shared_operations_user_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.allocation_operation
    ADD CONSTRAINT shared_operations_user_id FOREIGN KEY (user_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: balance_proposal shared_proposals_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.balance_proposal
    ADD CONSTRAINT shared_proposals_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: ranking_run shared_rankings_evaluation_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.ranking_run
    ADD CONSTRAINT shared_rankings_evaluation_id FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE;


--
-- Name: ranking_run shared_rankings_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.ranking_run
    ADD CONSTRAINT shared_rankings_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: recipient shared_recipients_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.recipient
    ADD CONSTRAINT shared_recipients_tenant_id FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: blood_request shared_requests_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_request
    ADD CONSTRAINT shared_requests_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: blood_allocation shared_reservations_destination_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT shared_reservations_destination_id FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: blood_allocation shared_reservations_evaluation_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT shared_reservations_evaluation_id FOREIGN KEY (evaluation_id) REFERENCES red_house.candidate_evaluation(evaluation_id) DEFERRABLE;


--
-- Name: blood_allocation shared_reservations_hold_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT shared_reservations_hold_id FOREIGN KEY (hold_id) REFERENCES red_house.request_hold(id) DEFERRABLE;


--
-- Name: blood_allocation shared_reservations_origin_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT shared_reservations_origin_id FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: blood_allocation shared_reservations_recipient_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT shared_reservations_recipient_id FOREIGN KEY (recipient_id) REFERENCES red_house.recipient(recipient_id) DEFERRABLE;


--
-- Name: blood_allocation shared_reservations_request_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT shared_reservations_request_id FOREIGN KEY (request_id) REFERENCES red_house.blood_request(request_id) DEFERRABLE;


--
-- Name: blood_allocation shared_reservations_route_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_allocation
    ADD CONSTRAINT shared_reservations_route_id FOREIGN KEY (route_id) REFERENCES red_house.regional_route(route_id) DEFERRABLE;


--
-- Name: resource_review shared_resource_reviews_actor_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.resource_review
    ADD CONSTRAINT shared_resource_reviews_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: resource shared_resources_current_institution_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.resource
    ADD CONSTRAINT shared_resources_current_institution_id FOREIGN KEY (current_institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: resource shared_resources_donation_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.resource
    ADD CONSTRAINT shared_resources_donation_id FOREIGN KEY (donation_id) REFERENCES red_house.donation(donation_id) DEFERRABLE;


--
-- Name: resource shared_resources_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.resource
    ADD CONSTRAINT shared_resources_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: blood_review shared_reviews_actor_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_review
    ADD CONSTRAINT shared_reviews_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: blood_review shared_reviews_resource_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_review
    ADD CONSTRAINT shared_reviews_resource_id FOREIGN KEY (resource_id) REFERENCES red_house.resource(resource_id) DEFERRABLE;


--
-- Name: blood_review shared_reviews_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.blood_review
    ADD CONSTRAINT shared_reviews_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: regional_route shared_routes_destination_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.regional_route
    ADD CONSTRAINT shared_routes_destination_id FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: regional_route shared_routes_origin_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.regional_route
    ADD CONSTRAINT shared_routes_origin_id FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: shipment shared_shipments_destination_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment
    ADD CONSTRAINT shared_shipments_destination_id FOREIGN KEY (destination_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: shipment shared_shipments_origin_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment
    ADD CONSTRAINT shared_shipments_origin_id FOREIGN KEY (origin_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: shipment shared_shipments_reservation_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment
    ADD CONSTRAINT shared_shipments_reservation_id FOREIGN KEY (allocation_id) REFERENCES red_house.blood_allocation(allocation_id) DEFERRABLE;


--
-- Name: shipment shared_shipments_transport_user_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment
    ADD CONSTRAINT shared_shipments_transport_user_id FOREIGN KEY (transport_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: transport_telemetry shared_telemetry_actor_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.transport_telemetry
    ADD CONSTRAINT shared_telemetry_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: shipment_transition shared_transitions_actor_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment_transition
    ADD CONSTRAINT shared_transitions_actor_id FOREIGN KEY (actor_id) REFERENCES red_house.user_account(account_id) DEFERRABLE;


--
-- Name: user_account shared_users_tenant_id; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.user_account
    ADD CONSTRAINT shared_users_tenant_id FOREIGN KEY (tenant_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: shipment shipment_organ_allocation_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.shipment
    ADD CONSTRAINT shipment_organ_allocation_id_fkey FOREIGN KEY (organ_allocation_id) REFERENCES red_house.organ_allocation(allocation_id) DEFERRABLE;


--
-- Name: site site_institution_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.site
    ADD CONSTRAINT site_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES red_house.institution(institution_id) DEFERRABLE;


--
-- Name: site_schedule site_schedule_site_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.site_schedule
    ADD CONSTRAINT site_schedule_site_id_fkey FOREIGN KEY (site_id) REFERENCES red_house.site(site_id) DEFERRABLE;


--
-- Name: storage_location storage_location_site_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.storage_location
    ADD CONSTRAINT storage_location_site_id_fkey FOREIGN KEY (site_id) REFERENCES red_house.site(site_id) DEFERRABLE;


--
-- Name: user_account user_account_party_id_fkey; Type: FK CONSTRAINT; Schema: red_house; Owner: -
--

ALTER TABLE ONLY red_house.user_account
    ADD CONSTRAINT user_account_party_id_fkey FOREIGN KEY (party_id) REFERENCES red_house.party(party_id) DEFERRABLE;


--
-- PostgreSQL database dump complete
--

INSERT INTO red_house."role" ("role_code","role_name","is_enabled") VALUES ('ADMIN','Administrador',true);
INSERT INTO red_house."role" ("role_code","role_name","is_enabled") VALUES ('AUDITOR','Auditor',true);
INSERT INTO red_house."role" ("role_code","role_name","is_enabled") VALUES ('COORDINATOR','Coordinador regional',true);
INSERT INTO red_house."role" ("role_code","role_name","is_enabled") VALUES ('DONOR','Donante',true);
INSERT INTO red_house."role" ("role_code","role_name","is_enabled") VALUES ('MEDICAL','Personal médico autorizado',true);
INSERT INTO red_house."role" ("role_code","role_name","is_enabled") VALUES ('OPERATOR','Operador de banco de sangre',true);
INSERT INTO red_house."role" ("role_code","role_name","is_enabled") VALUES ('TRANSPORT','Personal de traslado',true);
INSERT INTO red_house."capability" ("capability_code","capability_name") VALUES ('BLOOD_INVENTORY','Inventario sanguíneo ilustrativo');
INSERT INTO red_house."capability" ("capability_code","capability_name") VALUES ('COORDINATION','Coordinación institucional');
INSERT INTO red_house."capability" ("capability_code","capability_name") VALUES ('LABORATORY','Laboratorio declarado (sin operación clínica)');
INSERT INTO red_house."blood_status_transition" ("previous_status","new_status","is_illustrative") VALUES ('AVAILABLE','QUARANTINED',true);
INSERT INTO red_house."blood_status_transition" ("previous_status","new_status","is_illustrative") VALUES ('AVAILABLE','WITHDRAWN',true);
INSERT INTO red_house."blood_status_transition" ("previous_status","new_status","is_illustrative") VALUES ('QUARANTINED','AVAILABLE',true);
INSERT INTO red_house."blood_status_transition" ("previous_status","new_status","is_illustrative") VALUES ('QUARANTINED','WITHDRAWN',true);
INSERT INTO red_house."cache_revision" ("name","revision") VALUES ('catalogues',0);
INSERT INTO red_house."cache_revision" ("name","revision") VALUES ('inventory',0);
INSERT INTO red_house."schema_migration" ("version","description") VALUES (1,'Esquema base de main');
INSERT INTO red_house."schema_migration" ("version","description") VALUES (2,'Flujo regional');
INSERT INTO red_house."schema_migration" ("version","description") VALUES (3,'Urgencia en solicitudes');
INSERT INTO red_house."schema_migration" ("version","description") VALUES (4,'Flujo de órganos');
INSERT INTO red_house."schema_migration" ("version","description") VALUES (5,'Base compartida para microservicios');
INSERT INTO red_house."schema_migration" ("version","description") VALUES (6,'Adaptación ejecutable de servicios y relaciones compartidas');
INSERT INTO red_house."schema_migration" ("version","description") VALUES (7,'Investigación de auditoría e historial de hallazgos');
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('alertas',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('alertas',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('auditoria',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('auditoria',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('auditoria',3);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('compatibilidad',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('compatibilidad',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('custodia',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('custodia',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('donantes',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('donantes',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('donantes',3);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('donantes',4);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('identidad_acceso',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('identidad_acceso',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('identidad_acceso',4);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('identidad_acceso',5);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('identidad_acceso',6);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('inventario',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('inventario',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('inventario',3);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('inventario',4);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('inventario',5);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('monitoreo',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('monitoreo',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('priorizacion_geografia',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('priorizacion_geografia',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('priorizacion_geografia',3);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('receptores',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('receptores',2);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('receptores',3);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('receptores',4);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('transporte',1);
INSERT INTO red_house."service_schema_version" ("service","version") VALUES ('transporte',2);
COMMIT;
