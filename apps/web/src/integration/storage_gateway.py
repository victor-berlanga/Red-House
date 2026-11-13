"""Entrada de archivos para el dominio modular o su API independiente."""

from werkzeug.wrappers import Request, Response


def install(app):
    downstream = app.wsgi_app
    kernel = app.extensions.get("application_kernel")

    def gateway(environ, start_response):
        path = environ.get("PATH_INFO", "")
        if not path.startswith("/storage/v1/objects/"):
            return downstream(environ, start_response)
        if kernel is not None:
            return kernel.apps["documentos"].wsgi_app(environ, start_response)
        # El destino se toma solo de configuración privada, nunca del cliente.
        import requests

        target = app.config["SERVICE_URLS"]["documentos"].rstrip("/") + path
        req = Request(environ)
        if req.method not in ("GET", "PUT"):
            return Response(status=405)(environ, start_response)
        if req.method == "PUT" and req.content_length is None:
            return Response(status=411)(environ, start_response)
        if req.content_length is not None and req.content_length > 10 * 1024 * 1024:
            return Response(status=413)(environ, start_response)
        req.max_content_length = 10 * 1024 * 1024
        try:
            headers = {"Content-Type": req.content_type or "application/octet-stream"}
            with requests.Session() as session:
                session.trust_env = False
                response = session.request(
                    req.method,
                    target,
                    data=req.get_data(),
                    headers=headers,
                    timeout=(1, 15),
                    allow_redirects=False,
                )
            if (
                300 <= response.status_code < 400
                or len(response.content) > 10 * 1024 * 1024
            ):
                return Response(status=502)(environ, start_response)
            result = Response(
                response.content,
                status=response.status_code,
                content_type=response.headers.get(
                    "Content-Type", "application/octet-stream"
                ),
            )
            for header in (
                "Content-Disposition",
                "Cache-Control",
                "X-Content-Type-Options",
                "Referrer-Policy",
            ):
                if header in response.headers:
                    result.headers[header] = response.headers[header]
            return result(environ, start_response)
        except (requests.RequestException, OSError):
            return Response(status=503)(environ, start_response)

    app.wsgi_app = gateway
