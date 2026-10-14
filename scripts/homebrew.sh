#!/usr/bin/env bash
# Se usa solo cuando falta una dependencia que requiere Homebrew.
redhouse_find_brew() {
    if [[ "$(uname -s)" != Darwin ]]; then
        printf 'Este auxiliar es exclusivo de macOS. En Ubuntu utiliza los paquetes de tu distribucion; consulta documentation/markdowns/Instalacion_y_operacion.md.\n' >&2
        return 1
    fi
    redhouse_brew="$(command -v brew || true)"
    if [[ -z "$redhouse_brew" ]]; then
        for redhouse_brew_path in /opt/homebrew/bin/brew /usr/local/bin/brew; do
            if [[ -x "$redhouse_brew_path" ]]; then redhouse_brew="$redhouse_brew_path"; break; fi
        done
    fi
    if [[ -z "$redhouse_brew" ]]; then
        printf 'Instalando Homebrew desde su instalador oficial (puede solicitar contraseña de macOS).\n'
        local redhouse_installer
        redhouse_installer="$(mktemp -t redhouse-brew.XXXXXX)"
        curl -fL --retry 2 --connect-timeout 20 https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$redhouse_installer"
        /bin/bash "$redhouse_installer"
        for redhouse_brew_path in /opt/homebrew/bin/brew /usr/local/bin/brew; do
            if [[ -x "$redhouse_brew_path" ]]; then redhouse_brew="$redhouse_brew_path"; break; fi
        done
        [[ -n "$redhouse_brew" ]] || { printf 'Homebrew no quedó instalado.\n' >&2; return 1; }
    fi
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    set -euo pipefail
    redhouse_find_brew
    exec "$redhouse_brew" install "$@"
fi
