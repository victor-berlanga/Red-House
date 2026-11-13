"""Trust forwarding metadata only from one explicitly configured network peer."""

import ipaddress
import socket

from werkzeug.middleware.proxy_fix import ProxyFix


def trusted_peer(config):
    address = config.get("TRUSTED_PROXY_ADDRESS", "")
    host = config.get("TRUSTED_PROXY_HOST", "")
    if address and host:
        raise ValueError("Configura dirección o nombre del proxy, no ambos.")
    if address:
        return str(ipaddress.ip_address(address))
    if not host:
        return None
    # Resolve the private gateway at startup; never trust an entire Docker subnet.
    addresses = {
        entry[4][0] for entry in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    }
    if len(addresses) != 1:
        raise ValueError("El proxy debe resolver a una única dirección privada.")
    return str(ipaddress.ip_address(addresses.pop()))


def waitress_proxy_options(config):
    peer = trusted_peer(config)
    if peer is None:
        return {"clear_untrusted_proxy_headers": True}
    return {
        "trusted_proxy": peer,
        "trusted_proxy_count": 1,
        "trusted_proxy_headers": {"x-forwarded-for", "x-forwarded-proto"},
        "clear_untrusted_proxy_headers": True,
    }


class TrustedProxy:
    """Gevent counterpart of Waitress's explicit single-peer proxy policy."""

    def __init__(self, app, peer):
        self.app = app
        self.peer = str(ipaddress.ip_address(peer))
        self.forwarded = ProxyFix(
            app, x_for=1, x_proto=1, x_host=0, x_port=0, x_prefix=0
        )

    def __call__(self, environ, start_response):
        environ = environ.copy()
        for key in (
            "HTTP_FORWARDED",
            "HTTP_X_FORWARDED_HOST",
            "HTTP_X_FORWARDED_PORT",
            "HTTP_X_FORWARDED_PREFIX",
            "HTTP_X_FORWARDED_BY",
        ):
            environ.pop(key, None)
        if environ.get("REMOTE_ADDR") == self.peer:
            return self.forwarded(environ, start_response)
        environ.pop("HTTP_X_FORWARDED_FOR", None)
        environ.pop("HTTP_X_FORWARDED_PROTO", None)
        return self.app(environ, start_response)
