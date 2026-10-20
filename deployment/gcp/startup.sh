#!/usr/bin/env bash
# Preparación de CentOS Stream 10 para la VM dedicada de Red House.
set -euo pipefail
exec > >(tee -a /var/log/redhouse-host-setup.log) 2>&1

if [[ -f /var/lib/redhouse-host-ready ]]; then
    systemctl start docker
    exit 0
fi

dnf -y install dnf-plugins-core ca-certificates python3 tar gzip
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
install -d -m 0755 /etc/docker
if [[ ! -e /etc/docker/daemon.json ]]; then
    cat > /etc/docker/daemon.json <<'JSON'
{"log-driver":"local","log-opts":{"max-size":"10m","max-file":"3"}}
JSON
fi
systemctl enable --now docker
install -d -m 0700 /opt/redhouse
docker version --format '{{.Server.Version}}'
docker compose version
dnf clean all
touch /var/lib/redhouse-host-ready
