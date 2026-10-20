"""Adaptador técnico GCS; las operaciones de evidencia pertenecen a Transporte."""

import atexit
from datetime import timedelta
from threading import Lock

from flask import current_app

from .errors import APIError

_client_lock = Lock()


def bucket():
    if not current_app.config.get("GCS_BUCKET"):
        raise APIError(
            "storage_unconfigured",
            "Bucket privado y credenciales GCS pendientes de configuración.",
            503,
        )
    try:
        from google.cloud import storage

        with _client_lock:
            client = current_app.extensions.get("gcs_client")
            if client is None:
                import google.auth
                from google.auth.transport.requests import AuthorizedSession, Request

                class BoundedRequest(Request):
                    def __call__(self, *args, **kwargs):
                        kwargs["timeout"] = (1, 2)
                        return super().__call__(*args, **kwargs)

                credentials, project = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                auth_request = BoundedRequest()
                http = AuthorizedSession(
                    credentials,
                    auth_request=auth_request,
                    refresh_timeout=2,
                    max_refresh_attempts=0,
                )
                client = storage.Client(
                    project=current_app.config.get("GCS_PROJECT") or project,
                    credentials=credentials,
                    _http=http,
                )
                current_app.extensions["gcs_signing"] = bounded_signing(
                    credentials, auth_request
                )
                current_app.extensions["gcs_client"] = client
                atexit.register(client.close)
        return client.bucket(current_app.config["GCS_BUCKET"])
    except Exception:  # noqa: BLE001 - SDK/auth boundary returns a sanitized dependency error
        raise APIError(
            "storage_unavailable", "Almacenamiento de archivos inaccesible.", 503
        ) from None


def bounded_signing(credentials, auth_request):
    """Bound the IAM signing RPC; SDK default signing has unbounded HTTP waits."""
    from google.auth import impersonated_credentials
    from google.auth.compute_engine.credentials import Credentials as ComputeCredentials

    if isinstance(credentials, impersonated_credentials.Credentials):
        signing_source = credentials._source_credentials
        signing_email = credentials.signer_email
        delegates = credentials._delegates
    elif isinstance(credentials, ComputeCredentials):
        # Metadata credentials have no local private key. Resolve the attached
        # identity before signing and call IAM with its short-lived access token.
        credentials.refresh(auth_request)
        signing_source = credentials
        signing_email = credentials.service_account_email
        delegates = None
        if not signing_email or signing_email == "default":
            raise ValueError("Attached service account could not be resolved.")
    else:
        return credentials
    import base64

    from google.auth.credentials import Signing
    from google.auth.transport.requests import AuthorizedSession

    # google-auth 2.x itself signs with these source credentials. Keep the
    # impersonation chain, but replace its unbounded RPC with a single deadline.
    # A Compute Engine identity signs directly, without a downloaded key or ADC.
    session = AuthorizedSession(
        signing_source,
        auth_request=auth_request,
        refresh_timeout=2,
        max_refresh_attempts=0,
    )
    atexit.register(session.close)

    class RemoteSigning(Signing):
        @property
        def signer_email(self):
            return signing_email

        @property
        def signer(self):
            return self

        def sign(self, message):
            return self.sign_bytes(message)

        def sign_bytes(self, message):
            result = session.post(
                "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
                + self.signer_email
                + ":signBlob",
                json={
                    "payload": base64.b64encode(message).decode(),
                    "delegates": delegates,
                },
                timeout=(1, 2),
            )
            result.raise_for_status()
            return base64.b64decode(result.json()["signedBlob"])

    return RemoteSigning()


def signed_url(blob, method, mime=None):
    try:
        return blob.generate_signed_url(
            credentials=current_app.extensions.get("gcs_signing"),
            version="v4",
            expiration=timedelta(minutes=5),
            method=method,
            content_type=mime,
            headers={"x-goog-if-generation-match": "0"} if method == "PUT" else None,
        )
    except Exception:  # noqa: BLE001 - SDK/auth boundary returns a sanitized dependency error
        raise APIError(
            "storage_unavailable", "No se pudo generar acceso temporal al archivo.", 503
        ) from None
