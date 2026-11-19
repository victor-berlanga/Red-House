#!/bin/bash
# Publica a4af39c (redhouse/audit_catalog.py) solo en auditoria-a/b.
set -euo pipefail
cd /opt/redhouse
NEW=/tmp/audit_catalog.py
TAG=redhouse/auditoria:audit-catalog-20261118-01
OVR=.local/compose/gcs.compose.yaml
BK=.local/compose/backups/audit-catalog-20261118
COMPOSE="docker compose --project-directory /opt/redhouse -f compose.yaml -f .local/compose/gcs.compose.yaml -f .local/compose/public.compose.yaml"
OLD_IMG=$(python3 -c 'import json;print(json.load(open("'$OVR'"))["services"]["auditoria-a"]["image"])')
echo "imagen en uso: $OLD_IMG"
echo "sha nuevo: $(sha256sum $NEW | cut -d' ' -f1)"

# Respaldo
mkdir -p $BK
cp -p $OVR $BK/gcs.compose.yaml.orig
cp -p apps/services/redhouse/audit_catalog.py $BK/audit_catalog.py.orig

# Ruta, dueño y modo dentro de la imagen
INNER=$(docker run --rm --entrypoint sh "$OLD_IMG" -c 'python -c "import redhouse.audit_catalog as m;print(m.__file__)"')
META=$(docker run --rm --entrypoint sh "$OLD_IMG" -c "stat -c '%u:%g %a' $INNER")
echo "dentro: $INNER ($META)"
OWN=${META% *}; MODE=${META#* }

# Imagen derivada con un solo COPY
CTX=$(mktemp -d); cp $NEW $CTX/audit_catalog.py
printf 'FROM %s\nCOPY --chown=%s --chmod=%s audit_catalog.py %s\n' "$OLD_IMG" "$OWN" "$MODE" "$INNER" > $CTX/Dockerfile
DOCKER_BUILDKIT=1 docker build -q -t $TAG $CTX
rm -rf $CTX

# Fuente en /opt/redhouse con dueño y modo del original
install -o "$(stat -c %u apps/services/redhouse/audit_catalog.py)" -g "$(stat -c %g apps/services/redhouse/audit_catalog.py)" -m "$(stat -c %a apps/services/redhouse/audit_catalog.py)" $NEW apps/services/redhouse/audit_catalog.py

# Override: solo auditoria-a/b
python3 - <<EOF
import json
p="$OVR"; d=json.load(open(p))
for s in ("auditoria-a","auditoria-b"): d["services"][s]["image"]="$TAG"
open(p,"w").write(json.dumps(d,indent=2)+"\n")
EOF

docker ps --format '{{.Names}} {{.ID}}' | sort > $BK/ps-antes.txt
for s in auditoria-b auditoria-a; do $COMPOSE up -d --wait --no-deps --no-build $s; done
docker ps --format '{{.Names}} {{.ID}}' | sort > $BK/ps-despues.txt
echo "--- contenedores cambiados:"; diff $BK/ps-antes.txt $BK/ps-despues.txt | grep '^[<>]' || true
echo "--- sanos: $(docker ps --format '{{.Status}}' | grep -c '(healthy)') de $(docker ps -q | wc -l)"
for c in $(docker ps --format '{{.Names}}' | grep auditoria); do
  echo "$c $(docker exec $c sha256sum $INNER | cut -d' ' -f1) $(docker inspect -f '{{.Config.Image}}' $c)"
  docker exec $c python -c 'from redhouse.audit_catalog import describe as d
for e in ["ALERT_SUBSCRIPTION_ROTATED","LABEL_ISSUANCE_AUTHORIZED","OPERATIONAL_CONTACTS_READ","SHIPMENT_OPERATIONAL_CONTEXT_READ","SHIPMENT_OPERATIONAL_HANDOVER_READ","SHIPMENT_RESOURCE_IDENTIFIER_VERIFIED","TRACKING_UNASSIGNED"]: print("  ",e,d(e))'
done
docker image inspect $TAG --format 'imagen {{.Id}}'
