#!/usr/bin/env bash
# Configuración comprobada de maquina01 el 20 de octubre de 2026.
# Crea otra VM; no modifica maquina01 ni instala datos por sí mismo.
set -euo pipefail
redhouse_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
redhouse_project="${REDHOUSE_GCP_PROJECT:-sistemas-integracion-01}"
redhouse_instance="${REDHOUSE_GCP_INSTANCE:-red-house}"
redhouse_zone="${REDHOUSE_GCP_ZONE:-me-central1-a}"
redhouse_identity="red-house-archivos@${redhouse_project}.iam.gserviceaccount.com"

# Firma remota limitada a esta cuenta de servicio; no crea claves privadas.
gcloud iam service-accounts add-iam-policy-binding "$redhouse_identity" \
    --project="$redhouse_project" \
    --member="serviceAccount:$redhouse_identity" \
    --role=roles/iam.serviceAccountTokenCreator \
    --condition=None --quiet --format='value(etag)'

gcloud compute instances create "$redhouse_instance" \
    --project="$redhouse_project" --zone="$redhouse_zone" \
    --machine-type=e2-standard-2 \
    --image=centos-stream-10-v20260609 --image-project=centos-cloud \
    --boot-disk-size=20GB --boot-disk-type=pd-standard \
    --network=default --subnet=default --network-tier=PREMIUM \
    --maintenance-policy=MIGRATE --provisioning-model=STANDARD \
    --service-account="$redhouse_identity" --scopes=cloud-platform \
    --metadata=enable-oslogin=TRUE \
    --metadata-from-file="startup-script=$redhouse_script_dir/startup.sh" \
    --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring \
    --labels=app=red-house,environment=academic \
    --quiet --format='table(name,zone.basename(),machineType.basename(),status)'
