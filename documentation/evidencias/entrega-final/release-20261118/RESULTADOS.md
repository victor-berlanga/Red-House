# Release público `entrega-final-v1` — 18/11/2026

**Release:** https://github.com/victor-berlanga/Red-House/releases/tag/entrega-final-v1 (público, no borrador). Apunta al commit `1fcedaa` de `entrega-final`.

## Archivos publicados

| Archivo | Tamaño | Origen |
|---|---|---|
| `RedHouse-android-debug.apk` | 14,632,960 B | `./gradlew :composeApp:assembleDebug` en esta Mac, 18/11 12:36; sin cambios en `apps/mobile` después. Apunta a `https://34.18.186.116` |
| `RedHouse-windows-x64.zip` | 64,841,416 B | CI [44421598448](https://github.com/victor-berlanga/Red-House/actions/runs/44421598448), `windows-2025` |
| `RedHouse-macos-arm64.tar.gz` | 51,845,872 B | mismo CI, `macos-15` (arm64) |
| `RedHouse-macos-x64.tar.gz` | 55,997,232 B | mismo CI, `macos-15-intel` |
| `RedHouse-linux-x64.tar.gz` | 101,861,804 B | mismo CI, `ubuntu-24.04` |
| `SHA256SUMS.txt` | 462 B | hashes de los cinco archivos ([copia](SHA256SUMS.txt)) |

## Qué se comprobó

- [HECHO] En cada sistema el CI de escritorio corrió 286 pruebas, con 0 fallas y 0 errores (`unit.xml`). También arrancó el ejecutable empaquetado sin pantalla y cargó el XSD de login: `{"ok": true, "window": true}`. Ver `package-smoke-*.json` y `build-*.json`; los cuatro registran el commit `1fcedaa`.
- [HECHO] Los paquetes no incluyen `.env`, `state.json`, `checkpoint` ni llaves privadas. Lo único que coincidió con la búsqueda son archivos de bibliotecas: `certifi/cacert.pem` y los backends de `keyring`.
- [HECHO] `SHA256SUMS.txt` se descarga sin sesión (HTTP 200).

## Límites

- El APK es de depuración y lleva la llave de desarrollo. Los paquetes de escritorio no están firmados ni notarizados.
- Fuera del CI, solo se recorrió a mano el paquete de macOS Intel ([paquete 02](../desktop/paquete-macos-20261117-02/RESULTADOS.md)). Windows 11 sigue sin aceptación manual ([INC-423](../../../entrega-final/Registro_incidencias.md#inc-423)).
- Las apps solo funcionan con la VM de GCP encendida.
