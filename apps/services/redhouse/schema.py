"""Migración 001 independiente. Ejecutar con propietario, nunca con credencial runtime."""

COMMON = """
CREATE TABLE IF NOT EXISTS schema_version(version integer PRIMARY KEY, installed_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE activity_events(id uuid PRIMARY KEY,tenant_id uuid NOT NULL,event jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE outbox(id uuid PRIMARY KEY,event_id uuid NOT NULL,target text NOT NULL,event jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),delivered_at timestamptz,attempts integer NOT NULL DEFAULT 0,
 next_attempt timestamptz NOT NULL DEFAULT now(),last_error text,UNIQUE(event_id,target));
CREATE INDEX outbox_pending ON outbox(next_attempt,created_at) WHERE delivered_at IS NULL;
CREATE TABLE inbox(event_id uuid PRIMARY KEY,fingerprint text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE idempotency(id uuid PRIMARY KEY,user_id uuid NOT NULL,key text NOT NULL,operation text NOT NULL,
 fingerprint text NOT NULL,result jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(user_id,key));
CREATE FUNCTION reject_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Immutable history'; END $$;
CREATE TRIGGER activity_immutable BEFORE UPDATE OR DELETE ON activity_events FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
"""
from collections.abc import Mapping
from pathlib import Path
from .config import SERVICES


def service_path(service):
    if service not in SERVICES:
        raise ValueError("Servicio desconocido")
    module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
    return Path(__file__).resolve().parents[1] / module


class ServiceSchemas(Mapping):
    """Carga únicamente la migración del propietario solicitado."""

    def __iter__(self):
        return iter(SERVICES)

    def __len__(self):
        return len(SERVICES)

    def __getitem__(self, service):
        return (service_path(service) / "migrations/001.sql").read_text()


SCHEMAS = ServiceSchemas()
