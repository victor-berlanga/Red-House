import os
from pathlib import Path

from dotenv import load_dotenv

APP_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = APP_ROOT.parents[1]


def settings():
    load_dotenv(APP_ROOT / ".env", override=False)
    production = os.getenv("APP_ENV", "production") != "development"
    return {
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql://localhost/red_house"),
        "PRODUCTION": production,
        "SESSION_COOKIE_NAME": "red_house_csrf",
        "SESSION_COOKIE_SECURE": production,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "JWT_COOKIE_NAME": "red_house_access",
        "JWT_LIFETIME_SECONDS": 900,
        "MAX_CONTENT_LENGTH": 64 * 1024,
        "MAX_FORM_PARTS": 80,
        "WTF_CSRF_TIME_LIMIT": 3600,
        "HIGHCHARTS_ENABLED": os.getenv("HIGHCHARTS_ENABLED", "true").lower() == "true",
        "SCHEMA_PATH": REPO_ROOT / "data" / "database" / "schema.sql",
    }
