"""Adaptadores reales; un 2xx del receptor o aceptación SMTP no implica lectura humana."""

from email.message import EmailMessage
import smtplib
import ssl
from urllib.parse import urlparse

import requests
from flask import current_app

from .errors import APIError


def email(recipient, subject, body, identifier):
    cfg = current_app.config
    host = cfg.get("SMTP_HOST")
    if not host:
        raise APIError("email_unconfigured", "SMTP no configurado.", 503)
    testing = cfg.get("SMTP_TEST_RECEIVER", False) and host in (
        "127.0.0.1",
        "localhost",
    )
    message = EmailMessage()
    message["From"] = cfg.get("SMTP_FROM", "redhouse@localhost")
    message["To"], message["Subject"] = recipient, subject
    message["Message-ID"] = f"<{identifier}@redhouse>"
    message.set_content(body)
    try:
        with smtplib.SMTP(host, int(cfg.get("SMTP_PORT", 587)), timeout=5) as client:
            if not testing:
                client.starttls(context=ssl.create_default_context())
            if cfg.get("SMTP_USERNAME"):
                client.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
            if client.send_message(message):
                raise RuntimeError("recipient_rejected")
    except Exception:
        raise APIError(
            "email_unavailable", "El receptor SMTP no aceptó la entrega.", 503
        ) from None


def push(recipient, code, identifier, *, alert_id=None):
    cfg = current_app.config
    url = cfg.get("PUSH_ADAPTER_URL", "")
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (
        cfg.get("PUSH_TEST_RECEIVER") and parsed.hostname in ("localhost", "127.0.0.1")
    ):
        raise APIError("push_unconfigured", "Adaptador push HTTPS no configurado.", 503)
    try:
        response = requests.post(
            url,
            json={
                "recipient": recipient,
                "message_code": code,
                "event_id": identifier,
                **({"alert_id": alert_id} if alert_id else {}),
            },
            headers={
                "Authorization": "Bearer " + cfg.get("PUSH_ADAPTER_TOKEN", ""),
                "Idempotency-Key": identifier,
            },
            timeout=(1, 4),
            allow_redirects=False,
        )
        if response.status_code not in (200, 201, 202, 204):
            raise ValueError()
    except (requests.RequestException, ValueError):
        raise APIError(
            "push_unavailable", "Adaptador push inaccesible o rechazó el mensaje.", 503
        ) from None
