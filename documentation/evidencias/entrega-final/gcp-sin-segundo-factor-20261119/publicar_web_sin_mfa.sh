#!/bin/bash
# Quita los campos de segundo factor del portal web (login y confirmación de identidad).
# Imagen derivada de la que corre, con dos COPY. Reversa: publicar_web.sh revertir
set -euo pipefail
cd /opt/redhouse
CTX=/tmp/webctx
TAG=redhouse-web:sin-segundo-factor-20261119-01
OVR=.local/compose/gcs.compose.yaml
BK=.local/compose/backups/web-sin-mfa-20261119
COMPOSE="docker compose --project-directory /opt/redhouse -f compose.yaml -f .local/compose/gcs.compose.yaml -f .local/compose/public.compose.yaml"
F1=apps/web/src/presentation/templates/login.html
F2=apps/web/src/integration/routes/common.py

if [ "${1:-}" = "revertir" ]; then
  cp -p $BK/gcs.compose.yaml.orig $OVR
  cp -p $BK/login.html.orig $F1; cp -p $BK/common.py.orig $F2
  $COMPOSE up -d --wait --no-deps --no-build web
  echo "revertido"; exit 0
fi

OLD_IMG=$(python3 -c 'import json;print(json.load(open("'$OVR'"))["services"]["web"]["image"])')
echo "imagen en uso: $OLD_IMG"
mkdir -p $BK
[ -f $BK/gcs.compose.yaml.orig ] || cp -p $OVR $BK/gcs.compose.yaml.orig
[ -f $BK/login.html.orig ] || cp -p $F1 $BK/login.html.orig
[ -f $BK/common.py.orig ] || cp -p $F2 $BK/common.py.orig

printf 'FROM %s\nCOPY --chown=0:0 --chmod=644 login.html /app/%s\nCOPY --chown=0:0 --chmod=644 common.py /app/%s\n' "$OLD_IMG" "$F1" "$F2" > $CTX/Dockerfile
DOCKER_BUILDKIT=1 docker build -q -t $TAG -f $CTX/Dockerfile $CTX
install -o 0 -g 0 -m 644 $CTX/login.html $F1
install -o 0 -g 0 -m 644 $CTX/common.py $F2

python3 - <<PY
import json
p="$OVR"; d=json.load(open(p)); d["services"]["web"]["image"]="$TAG"
open(p,"w").write(json.dumps(d,indent=2)+"\n")
PY
docker ps --format '{{.Names}} {{.ID}}' | sort > $BK/ps-antes.txt
$COMPOSE up -d --wait --no-deps --no-build web
docker ps --format '{{.Names}} {{.ID}}' | sort > $BK/ps-despues.txt
echo "--- contenedores cambiados:"; diff $BK/ps-antes.txt $BK/ps-despues.txt | grep '^[<>]' || true
echo "--- sanos: $(docker ps --format '{{.Status}}' | grep -c '(healthy)') de $(docker ps -q | wc -l)"
for f in $F1 $F2; do echo "$f $(docker exec redhouse-parcial2-web-1 sha256sum /app/$f | cut -d' ' -f1)"; done
docker image inspect $TAG --format 'imagen {{.Id}}'
