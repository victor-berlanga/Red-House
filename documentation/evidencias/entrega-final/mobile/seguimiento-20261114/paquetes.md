# Paquetes normales con recuperación de fotografía

Fuente: `d735668`. Compilación Gradle `:composeApp:assembleDebug :composeApp:compileKotlinIosArm64`; enlace iOS con Xcode `Debug`, SDK `iphoneos`, arquitectura `arm64` y firma del equipo existente. No se repitieron las pruebas funcionales previas.

- Android normal **debug**: `.local/artifacts/mobile/redhouse-android-normal-foto-d735668.apk`, SHA-256 `da74c62c1a729e05c0fd33b62a0c658e380c8ca33e5c1b8e6d2a822b3d381ac2`. Contiene Activity de prueba no exportada; no es paquete release.
- iOS normal: `.local/artifacts/mobile/ios-foto-d735668/Debug-iphoneos/RedHouse.app`, ejecutable SHA-256 `fcda77e799c7c3bb58175f45c393ac8c386353d050de4a7c4dc7d6a26be957ac`. `codesign --verify --deep --strict` pasó; bundle `org.redhouse.mobile`; perfil vence 17/11/2026 22:39 UTC.
- Ambos incorporan el origen normal de GCP, sin dirección ni CA del laboratorio. iOS no contiene excepciones ATS. Android declara permisos de cámara, ubicación, red y avisos, entre otros permisos de sistema; iOS declara cámara y ubicación en uso. La comprobación identifica declaraciones, no concesiones del usuario.
- `xcrun devicectl device install app` actualizó la app en iPhone 16 Pro y `device process launch` terminó correctamente. No se borraron datos ni se introdujeron credenciales. No se inspeccionó la continuidad de la sesión ni se ejecutaron operaciones de negocio.
- Logs privados de compilación, firma/instalación y arranque: `.local/artifacts/mobile/pausa-20261114/reanudacion-*.log`. Los resultados de fotografía y sus límites están en [RESULTADOS.md](../RESULTADOS.md).
