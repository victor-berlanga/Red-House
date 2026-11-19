#!/bin/bash
# Quita el segundo factor del inicio de sesión en la VM (pedido de Víctor, 19/11/2026).
# No toca código ni imágenes: (1) MFA_REQUIRED_ROLES=[] en el JSON privado de identidad,
# (2) security_factors.active=false. Reversa: ./quitar_mfa.sh revertir
set -euo pipefail
cd /opt/redhouse
CFG=.local/compose/apps/identidad_acceso.json
BK=.local/compose/backups/sin-mfa-20261119
COMPOSE="docker compose --project-directory /opt/redhouse -f compose.yaml -f .local/compose/gcs.compose.yaml -f .local/compose/public.compose.yaml"
PSQL="docker exec -i redhouse-parcial2-postgres-1 psql -U rh_bootstrap -d red_house -v ON_ERROR_STOP=1 -qAt"

recrear() {
  for s in identidad-acceso-b identidad-acceso-a; do
    $COMPOSE up -d --wait --no-deps --no-build --force-recreate $s
  done
}

if [ "${1:-}" = "revertir" ]; then
  cp -p $BK/identidad_acceso.json.orig $CFG
  ids=$(paste -sd, $BK/factores_activos.txt | sed "s/[^,]\+/'&'/g")
  [ -n "$ids" ] && $PSQL -c "UPDATE red_house.security_factors SET active=true WHERE id IN ($ids)"
  recrear
  echo "revertido"; exit 0
fi

mkdir -p $BK
[ -f $BK/identidad_acceso.json.orig ] || cp -p $CFG $BK/identidad_acceso.json.orig
[ -s $BK/factores_activos.txt ] || $PSQL -c "SELECT id FROM red_house.security_factors WHERE active ORDER BY id" > $BK/factores_activos.txt
echo "--- factores activos antes: $(wc -l < $BK/factores_activos.txt)"
$PSQL -c "SELECT a.username FROM red_house.security_factors f JOIN red_house.user_account a ON a.account_id=f.id WHERE f.active ORDER BY 1"
echo "--- roles con MFA antes: $(python3 -c "import json;print(json.load(open('$CFG')).get('MFA_REQUIRED_ROLES','(no definido: por omisión ADMIN, MEDICAL, COORDINATOR)'))")"

python3 - <<EOF
import json
p="$CFG"; d=json.load(open(p))
d["MFA_REQUIRED_ROLES"]=[]
open(p,"w").write(json.dumps(d,indent=2)+"\n")
EOF
$PSQL -c "UPDATE red_house.security_factors SET active=false WHERE active"
echo "--- factores activos después: $($PSQL -c 'SELECT count(*) FROM red_house.security_factors WHERE active')"

recrear
echo "--- sanos: $(docker ps --format '{{.Status}}' | grep -c '(healthy)') de $(docker ps -q | wc -l)"
for c in $(docker ps --format '{{.Names}}' | grep identidad); do
  echo "$c roles=$(docker exec $c python -c 'import json;print(json.load(open("/run/secrets/config")).get("MFA_REQUIRED_ROLES"))')"
done
