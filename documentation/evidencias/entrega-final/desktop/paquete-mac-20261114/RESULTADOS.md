# Paquete macOS x86_64: reconstrucción local

Se construyó `/private/tmp/redhouse-desktop-final-20261113/dist/RedHouse.app` (136 MiB) con Python 3.12.6 y PyInstaller 6.22.0. El ejecutable tiene SHA-256 `f61b4f1dad3e69c9dc53135ab93d27b8ed1bd4e6242f5c65947e42000378fad1`. `smoke.json` confirma arranque sin sesión ni red y carga de XSD/operación; `contracts.json` registra 34 contratos idénticos al código fuente. Esta huella corresponde al ejecutable, no a todos los archivos del bundle.

El primer intento falló antes de recopilar datos: con `--specpath` externo, PyInstaller resolvió la ruta relativa de contratos desde ese directorio. La repetición usó `$PWD/redhouse_desktop/contracts` y completó la construcción. Logs privados locales: `/private/tmp/redhouse-desktop-final-20261113/evidence/build.log` y `build-repeticion.log`. El bundle previo permaneció intacto.

El primer intento de inspección no identificó la ventana. Después, la dirección copió el bundle a `.local/artifacts/desktop/RedHouse-macOS-20261114.app`, lo abrió y revisó visualmente el acceso: marca, etiquetas, foco y botón completos, sin dirección técnica visible. Captura privada `/private/tmp/redhouse-desktop-final-visible.png`; no se introdujeron credenciales ni se inició sesión. El proceso terminó. El mensaje de error de configuración solo cambió su texto y no se capturó. No se probaron notarización, Windows ni servicios desde el ejecutable empaquetado; los ensayos XML previos conservan su alcance y no se repitieron.

La copia persistente pasó `--smoke-report`. Distribución local: `.local/artifacts/desktop/RedHouse-macOS-20261114.zip`, SHA-256 `cdaa4efa73534629619707b145cd46fe51ce47b5ecb9adf3c992dc192136c60c`. Esta huella sí identifica el ZIP completo. Se conservó el paquete anterior.
