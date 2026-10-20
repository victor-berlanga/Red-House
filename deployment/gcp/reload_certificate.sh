#!/usr/bin/env bash
# Hook de Certbot: instalar la clave para el usuario no privilegiado de Nginx.
set -euo pipefail
destination=/opt/redhouse/.local/compose/tls
lineage="${RENEWED_LINEAGE:-/etc/letsencrypt/live/red-house-public}"
install -d -m 750 -o root -g 101 "$destination"
for name in fullchain.pem privkey.pem; do
  install -m 640 -o root -g 101 "$lineage/$name" "$destination/$name.new"
  mv "$destination/$name.new" "$destination/$name"
done
docker exec redhouse-parcial2-gateway-1 nginx -t
docker exec redhouse-parcial2-gateway-1 nginx -s reload
