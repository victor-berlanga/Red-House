"""Genera la entrada HTTPS de GCE sin cambiar los puertos del Compose local."""

import argparse
import ipaddress
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def configure(directory, address, bootstrap=False):
    address = str(ipaddress.IPv4Address(address))
    directory = directory.resolve()
    services = json.loads((ROOT / "compose.yaml").read_text())["services"]
    names = [name[:-2] for name in services if name.endswith("-a")]
    blocks = [
        f"""
  server {{
    listen 8081;
    server_name {address};
    location /.well-known/acme-challenge/ {{ root /var/www/acme; }}
    location / {{ return 308 https://{address}$request_uri; }}
  }}
"""
    ]
    if not bootstrap:
        blocks.append(
            f"""
  upstream public_web {{
    zone public_web 64k;
    server web:8080 resolve;
    keepalive 8;
  }}
  server {{
    listen 8443 ssl;
    server_name {address};
    ssl_certificate /etc/nginx/tls/fullchain.pem;
    ssl_certificate_key /etc/nginx/tls/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:TLS:10m;
    ssl_session_timeout 1d;
    server_tokens off;
    if ($host != {address}) {{ return 444; }}
    add_header Strict-Transport-Security "max-age=31536000" always;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host {address};
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Host "";
    proxy_set_header X-Forwarded-Prefix "";
    proxy_set_header Forwarded "";
    proxy_connect_timeout 1s;
    proxy_read_timeout 15s;
    proxy_hide_header X-Backend;
    proxy_redirect off;
    location / {{
      client_max_body_size 11m;
      proxy_pass http://public_web;
    }}
    location /services/ {{ return 404; }}
"""
        )
        for name in names:
            upstream = name.replace("-", "_")
            prefix = "/services/" + name
            # Swagger genera enlaces absolutos a sus recursos: conservar el
            # prefijo solo para /docs; las rutas de negocio mantienen /api/v1.
            blocks.append(
                f"""
    location = {prefix} {{ return 308 {prefix}/docs/; }}
    location = {prefix}/ {{ return 308 {prefix}/docs/; }}
    location = {prefix}/internal {{ return 404; }}
    location ^~ {prefix}/internal/ {{ return 404; }}
    location = {prefix}/docs {{ return 308 {prefix}/docs/; }}
    location {prefix}/docs/ {{ proxy_pass http://{upstream}; }}
    location {prefix}/ {{ proxy_pass http://{upstream}/; }}
"""
            )
        blocks.append("  }\n")
    original = (ROOT / "deployment/nginx.conf").read_text().rstrip()
    assert original.endswith("}")
    (directory / "public.nginx.conf").write_text(
        original[:-1] + "".join(blocks) + "}\n"
    )
    tls = directory / "tls"
    tls.mkdir(mode=0o750, exist_ok=True)
    override = {
        "services": {
            "gateway": {
                "volumes": [
                    f"{directory}/public.nginx.conf:/etc/nginx/nginx.conf:ro",
                    f"{tls}:/etc/nginx/tls:ro",
                    "/var/lib/redhouse-acme:/var/www/acme:ro",
                ],
                "ports": ["0.0.0.0:80:8081", "0.0.0.0:443:8443"],
            }
        }
    }
    (directory / "public.compose.yaml").write_text(
        json.dumps(override, indent=2) + "\n"
    )
    if not bootstrap:
        path = directory / "web.json"
        config = json.loads(path.read_text())
        config.update(
            SESSION_COOKIE_SECURE=True,
            PRODUCTION=True,
            PREFERRED_URL_SCHEME="https",
            TRUSTED_HOSTS=[address, "127.0.0.1", "localhost"],
        )
        path.write_text(json.dumps(config, indent=2) + "\n")
        for name in names:
            path = directory / "apps" / (name.replace("-", "_") + ".json")
            config = json.loads(path.read_text())
            config["PUBLIC_API_PREFIX"] = "/services/" + name
            path.write_text(json.dumps(config, indent=2) + "\n")
        (directory / "public.json").write_text(
            json.dumps({"address": address, "origin": "https://" + address}) + "\n"
        )
    print("Entrada pública generada: " + ("ACME" if bootstrap else "HTTPS"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=ROOT / ".local/compose")
    parser.add_argument("--ip", required=True)
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()
    configure(args.directory, args.ip, args.bootstrap)
