"""Adaptador técnico GCS; las operaciones de evidencia pertenecen a Documentos."""

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
        if method == "GET" and blob.generation is None:
            raise ValueError("Verified object generation is required.")
        return blob.generate_signed_url(
            credentials=current_app.extensions.get("gcs_signing"),
            version="v4",
            expiration=timedelta(minutes=5),
            method=method,
            content_type=mime,
            headers={"x-goog-if-generation-match": "0"} if method == "PUT" else None,
            generation=str(blob.generation) if method == "GET" else None,
            response_disposition="attachment" if method == "GET" else None,
        )
    except Exception:  # noqa: BLE001 - SDK/auth boundary returns a sanitized dependency error
        raise APIError(
            "storage_unavailable", "No se pudo generar acceso temporal al archivo.", 503
        ) from None


# Los objetos locales usan un UUID y metadatos internos; jamás una ruta del cliente.
LOCAL_LIMIT = 10 * 1024 * 1024


def provider():
    value = current_app.config.get("STORAGE_PROVIDER") or (
        "gcs" if current_app.config.get("GCS_BUCKET") else "local"
    )
    if value not in ("local", "gcs"):
        raise APIError("storage_unconfigured", "Proveedor de archivos inválido.", 503)
    return value


def object_bucket(name=None):
    selected = name or provider()
    if selected == "gcs":
        return bucket()
    if selected == "local":
        return LocalBucket()
    raise APIError("storage_unconfigured", "Proveedor de archivos inválido.", 503)


def local_root():
    import os
    import stat
    from pathlib import Path

    root = current_app.config.get("STORAGE_LOCAL_ROOT", "")
    if not root or not Path(root).is_absolute():
        raise APIError(
            "storage_unconfigured", "Almacén local privado no configurado.", 503
        )
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        info = os.fstat(fd)
        if (
            info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) & 0o077
            or not stat.S_ISDIR(info.st_mode)
        ):
            os.close(fd)
            raise OSError("private directory permissions")
        return fd
    except OSError:
        raise APIError(
            "storage_unavailable", "Almacenamiento local inaccesible.", 503
        ) from None


def local_health():
    import os
    import secrets

    root = local_root()
    name = ".health-" + secrets.token_hex(24)
    try:
        disk = os.fstatvfs(root)
        if disk.f_bavail * disk.f_frsize < LOCAL_LIMIT:
            raise OSError("insufficient free space")
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=root,
        )
        try:
            os.write(fd, b"1")
            os.fsync(fd)
        finally:
            os.close(fd)
            os.unlink(name, dir_fd=root)
    except OSError:
        raise APIError(
            "storage_unavailable", "Almacenamiento local inaccesible.", 503
        ) from None
    finally:
        os.close(root)


class LocalBucket:
    def blob(self, path, generation=None):
        from uuid import UUID

        try:
            identifier = str(UUID(path.rsplit("/", 1)[-1]))
        except (ValueError, AttributeError):
            raise APIError(
                "storage_unavailable", "Identificador inválido.", 503
            ) from None
        return LocalBlob(identifier, generation)


class LocalBlob:
    def __init__(self, identifier, generation=None):
        self.identifier = identifier
        self.expected_generation = str(generation) if generation is not None else None
        self.generation = None
        self.size = None
        self.content_type = None

    def _read(self):
        import json
        import os
        import stat

        from google.api_core.exceptions import NotFound

        root = local_root()
        try:
            try:
                fd = os.open(
                    self.identifier,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                    dir_fd=root,
                )
            except FileNotFoundError:
                raise NotFound("object missing") from None
            with os.fdopen(fd, "rb") as handle:
                info = os.fstat(handle.fileno())
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) & 0o077
                    or info.st_size > LOCAL_LIMIT + 4096
                ):
                    raise ValueError("invalid local object")
                header = handle.readline(4097)
                if len(header) > 4096 or not header.endswith(b"\n"):
                    raise ValueError("invalid local object")
                metadata = json.loads(header)
                content = handle.read(LOCAL_LIMIT + 1)
                if len(content) > LOCAL_LIMIT or len(content) != metadata["size"]:
                    raise ValueError("invalid local object size")
                self.generation = int(metadata["generation"])
                self.size = len(content)
                self.content_type = metadata["mime"]
                if (
                    self.expected_generation
                    and str(self.generation) != self.expected_generation
                ):
                    raise ValueError("local object generation changed")
                return content
        except (OSError, ValueError, KeyError, TypeError, UnicodeError):
            raise APIError(
                "storage_unavailable", "No se pudo leer el objeto privado.", 503
            ) from None
        finally:
            os.close(root)

    def reload(self, **kwargs):
        self._read()

    def download_as_bytes(self, if_generation_match=None, **kwargs):
        content = self._read()
        if if_generation_match is not None and str(self.generation) != str(
            if_generation_match
        ):
            raise APIError(
                "storage_unavailable", "Generación de archivo inválida.", 503
            )
        return content

    def upload_from_string(
        self, content, content_type, if_generation_match=0, **kwargs
    ):
        import json
        import os
        import secrets

        from google.api_core.exceptions import PreconditionFailed

        if if_generation_match != 0 or len(content) > LOCAL_LIMIT:
            raise ValueError("invalid local upload")
        root = local_root()
        temporary = "." + secrets.token_hex(24)
        generation = secrets.randbits(120) + 1
        try:
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=root,
            )
            try:
                with os.fdopen(fd, "wb") as handle:
                    header = (
                        json.dumps(
                            {
                                "generation": str(generation),
                                "mime": content_type,
                                "size": len(content),
                            },
                            separators=(",", ":"),
                        ).encode()
                        + b"\n"
                    )
                    handle.write(header)
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                try:
                    os.link(
                        temporary,
                        self.identifier,
                        src_dir_fd=root,
                        dst_dir_fd=root,
                        follow_symlinks=False,
                    )
                except FileExistsError:
                    raise PreconditionFailed("object exists") from None
                os.fsync(root)
            finally:
                os.unlink(temporary, dir_fd=root)
            self.generation, self.size, self.content_type = (
                generation,
                len(content),
                content_type,
            )
        except OSError:
            raise APIError(
                "storage_unavailable", "No se pudo guardar el objeto privado.", 503
            ) from None
        finally:
            os.close(root)


def access_url(row, method):
    if row["storage_provider"] == "gcs":
        blob = bucket().blob(
            row["object_path"],
            generation=int(row["generation"]) if method == "GET" else None,
        )
        return signed_url(blob, method, row["mime_type"] if method == "PUT" else None)
    import base64
    import hashlib
    import json
    from urllib.parse import urlsplit

    from cryptography.fernet import Fernet
    from flask import request

    base = current_app.config.get("STORAGE_PUBLIC_BASE_URL", "").rstrip("/")
    parsed = urlsplit(base)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise APIError(
            "storage_unconfigured", "Origen HTTPS del almacén no configurado.", 503
        )
    key = current_app.config.get("SERVICE_PRIVATE_KEY")
    if not key:
        raise APIError("storage_unconfigured", "Firma del almacén no configurada.", 503)
    cipher = Fernet(
        base64.urlsafe_b64encode(
            hashlib.sha256(("private-storage-v1:" + key).encode()).digest()
        )
    )
    token = cipher.encrypt(
        json.dumps(
            {
                "id": str(row["id"]),
                "method": method,
                "generation": row.get("generation"),
                "authorization": request.headers.get("Authorization", ""),
            },
            separators=(",", ":"),
        ).encode()
    ).decode()
    prefix = current_app.config.get("STORAGE_OBJECT_PREFIX", "/storage/v1/objects/")
    if prefix not in ("/storage/v1/objects/", "/portal-storage/v1/objects/"):
        raise APIError("storage_unconfigured", "Ruta del almacén no configurada.", 503)
    return base + prefix + token


def upload_headers(row):
    headers = {"Content-Type": row["mime_type"]}
    if row["storage_provider"] == "gcs":
        headers["x-goog-if-generation-match"] = "0"
    return headers
