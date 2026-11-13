import json
import os
from pathlib import Path

from dotenv import dotenv_values


SERVICES = {
    "identidad_acceso": 5101,
    "donantes": 5102,
    "receptores": 5103,
    "inventario": 5104,
    "compatibilidad": 5105,
    "priorizacion_geografia": 5106,
    "transporte": 5107,
    "custodia": 5108,
    "alertas": 5109,
    "auditoria": 5110,
    "monitoreo": 5111,
    "documentos": 5112,
}
MONGO_SERVICES = {"transporte", "custodia", "auditoria", "monitoreo"}


def settings(service, overrides=None):
    env_path = os.environ.get("REDHOUSE_ENV")
    env = dict(dotenv_values(env_path)) if env_path else {}
    env.update(os.environ)
    cfg = {
        "SERVICE": service,
        "PORT": SERVICES[service],
        "VERSION": "0.4.4",
        "DATABASE_URL": env.get(f"{service.upper()}_DATABASE_URL", ""),
        "REDIS_URL": env.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
        "REDIS_PREFIX": env.get("REDIS_PREFIX", "redhouse-ms:"),
        "MONGODB_URL": env.get(f"{service.upper()}_MONGODB_URL", ""),
        "MONGODB_DATABASE": f"rh_{service}",
        "JWT_PUBLIC_KEY": env.get("JWT_PUBLIC_KEY", "").replace("\\n", "\n"),
        "JWT_PRIVATE_KEY": env.get("JWT_PRIVATE_KEY", "").replace("\\n", "\n"),
        "JWT_ISSUER": "red-house-services",
        "JWT_AUDIENCE": "red-house-api-v1",
        "ACCESS_TTL": 900,
        "REFRESH_TTL": 86400,
        "RATE_LIMIT": 180,
        "INTERNAL_RATE_LIMIT": 1800,
        "SERVICE_PRIVATE_KEY": env.get(
            f"{service.upper()}_SERVICE_PRIVATE_KEY", ""
        ).replace("\\n", "\n"),
        "SERVICE_PUBLIC_KEYS": json.loads(env.get("SERVICE_PUBLIC_KEYS", "{}")),
        "SERVICE_URLS": json.loads(env.get("SERVICE_URLS", "{}")),
        "MAX_CONTENT_LENGTH": 262144,
        "CACHE_TTL": 15,
        "STORAGE_ENABLED": False,
        "HLA_REFERENCE_DIR": env.get("HLA_REFERENCE_DIR", str(Path(__file__).resolve().parents[3] / ".local/reference-data/hla")),
        "TESTING": False,
        "GCS_BUCKET": env.get("GCS_BUCKET", ""),
        "TRUSTED_PROXY_ADDRESS": env.get("TRUSTED_PROXY_ADDRESS", ""),
        "TRUSTED_PROXY_HOST": env.get("TRUSTED_PROXY_HOST", ""),
    }
    cfg.update(overrides or {})
    # Las suites heredadas explicitan TESTING; la instalación operativa arranca
    # reforzada. El despliegue debe preparar enrolamiento y clientes antes de activar.
    defaults = [] if cfg["TESTING"] else ["ADMIN", "MEDICAL", "COORDINATOR"]
    cfg.setdefault(
        "MFA_REQUIRED_ROLES",
        json.loads(env.get("MFA_REQUIRED_ROLES", json.dumps(defaults))),
    )
    critical = (
        []
        if cfg["TESTING"]
        else [
            "resource_release",
            "lab_result_review",
            "evaluation_review",
            "rule_transition",
            "anomaly_resolve",
            "reservation_create",
            "resource_destination",
        ]
    )
    cfg.setdefault(
        "REAUTH_REQUIRED_OPERATIONS",
        json.loads(env.get("REAUTH_REQUIRED_OPERATIONS", json.dumps(critical))),
    )
    cfg.setdefault(
        "REQUIRE_ORGAN_AUTHORIZATION",
        env.get(
            "REQUIRE_ORGAN_AUTHORIZATION", "false" if cfg["TESTING"] else "true"
        ).lower()
        == "true",
    )
    cfg.setdefault(
        "REQUIRE_LAB_PROFILE",
        env.get("REQUIRE_LAB_PROFILE", "false" if cfg["TESTING"] else "true").lower()
        == "true",
    )
    cfg.setdefault("OPERATION_SCOPE", env.get("OPERATION_SCOPE", "ACADEMIC" if cfg["TESTING"] else "CLINICAL"))
    cfg.setdefault("CLINICAL_APPROVERS", json.loads(env.get("CLINICAL_APPROVERS", "{}")))
    for name in (
        "SMTP_HOST",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM",
        "PUSH_ADAPTER_URL",
        "PUSH_ADAPTER_TOKEN",
        "CLAMD_HOST",
    ):
        cfg.setdefault(name, env.get(name, ""))
    for name, default in (("SMTP_PORT", 587), ("CLAMD_PORT", 3310)):
        cfg.setdefault(name, int(env.get(name, default)))
    if not cfg["DATABASE_URL"] or not cfg["JWT_PUBLIC_KEY"]:
        raise ValueError(
            "Configura DATABASE_URL del servicio y JWT_PUBLIC_KEY; consulta .env.example."
        )
    if service == "identidad_acceso" and not cfg["JWT_PRIVATE_KEY"]:
        raise ValueError("Identidad necesita JWT_PRIVATE_KEY.")
    # Los procesos de dominio no conservan la clave de firma de identidad.
    if service != "identidad_acceso":
        cfg.pop("JWT_PRIVATE_KEY", None)
    return cfg
