#!/usr/bin/env bash
# Ejecutar como root EN LA VM; requiere IP fija y firewall TCP 80/443.
set -euo pipefail
cd /opt/redhouse
public_ip="${1:?Indica la IPv4 pública reservada para esta VM}"
compose=(docker compose -f compose.yaml -f .local/compose/gcs.compose.yaml -f .local/compose/public.compose.yaml)
install -d -m 755 /var/lib/redhouse-acme
python3 -m venv /opt/redhouse-certbot
/opt/redhouse-certbot/bin/pip install --disable-pip-version-check 'certbot>=5.4,<6'

# Primero servir únicamente el desafío HTTP. Las credenciales de aplicación
# nunca pasan por HTTP público; la redirección HTTPS existe desde el arranque.
if [[ ! -f /etc/letsencrypt/live/red-house-public/fullchain.pem ]]; then
  python3 deployment/gcp/configure_public.py --ip "$public_ip" --bootstrap
  "${compose[@]}" up -d --wait --no-deps gateway
  /opt/redhouse-certbot/bin/certbot certonly --non-interactive --agree-tos \
    --register-unsafely-without-email --preferred-profile shortlived \
    --webroot --webroot-path /var/lib/redhouse-acme --ip-address "$public_ip" \
    --cert-name red-house-public
fi
install -m 750 deployment/gcp/reload_certificate.sh /usr/local/sbin/redhouse-reload-certificate
/usr/local/sbin/redhouse-reload-certificate
python3 deployment/gcp/configure_public.py --ip "$public_ip"
# La imagen web reconoce HTTPS; las API publican Swagger con su prefijo.
"${compose[@]}" --parallel 1 build > /var/log/redhouse-public-build.log 2>&1
python3 deployment/start.py
# El archivo está montado por bind; recrear recoge también un inode sustituido.
"${compose[@]}" up -d --wait --no-deps --force-recreate gateway
install -d -m 755 /etc/letsencrypt/renewal-hooks/deploy
install -m 750 deployment/gcp/reload_certificate.sh /etc/letsencrypt/renewal-hooks/deploy/redhouse
install -m 644 deployment/gcp/redhouse-certbot.service deployment/gcp/redhouse-certbot.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now redhouse-certbot.timer
systemctl start redhouse-certbot.service
echo "Portal disponible en https://$public_ip"
