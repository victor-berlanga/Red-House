# Evidencia móvil — 09/11/2026

Incremento inicial, **no completa el prompt 04**. Fuentes previas del usuario preservadas. Sin despliegues, migraciones, escritura productiva, publicación ni prueba física.

Entorno: macOS Intel, JDK Oracle 17.0.12, Gradle 8.11.1, SDK Android 35 instalado en `/tmp/redhouse-sdk`. Descargas oficiales realizadas fuera de la restricción de red del sandbox. El usuario autorizó explícitamente aceptar la licencia Android SDK.

Intentos conservados: Gradle inicial no pudo cargar biblioteca nativa usando la ubicación predeterminada; se configuró `GRADLE_USER_HOME=/tmp/redhouse-gradle-home`. Primera instalación SDK omitió paquetes por no aceptar licencia; se reejecutó después de autorización del usuario. Wrapper generado correctamente.

`xcodebuild -version` falla: el directorio activo es CommandLineTools y requiere Xcode. `xcrun simctl list devices booted` falla porque no existe `simctl`. No hay compilación/arranque iOS, IPA ni firma física. No se presenta código Swift como plataforma verificada.

Los resultados finales de compilación/pruebas se añaden después de la ejecución, junto con XML y manifiesto de fuentes. Las pruebas unitarias utilizan MockEngine identificado; no acreditan cuatro servicios reales, persistencia backend, UI instrumentada ni GPS/cámara/push/mapa.

## Compilación y pruebas ejecutadas

- Primera compilación: `:composeApp:testDebugUnitTest :composeApp:assembleDebug`, aprobada en 6 min 7 s; siete pruebas unitarias.
- Verificación de fuentes finales de aplicación tras ajustes: aprobada en 1 min 6 s.
- Adición de pruebas de cola: misma selección aprobada en 26 s, **nueve casos únicos, cero fallos/errores/omitidos** (siete de sesión y dos de cola). Las repeticiones no se suman.
- `apksigner verify --verbose`: APK válido, firma v2 debug, un firmante. SHA-256 conservado en `apk.sha256`.
- `git diff --check`, análisis XML de Info.plist y enlaces locales de la guía: aprobados.

Las nueve pruebas usan `MockEngine` y almacenamiento en memoria identificado. Cubren HTTPS, ausencia de contraseña persistida, renovación concurrente única, respuesta perdida de renovación, logout offline, rechazo de HTML, navegación del donante, identidad de la cola y confirmación incompleta. **No acreditan Keystore/Keychain en hardware, backend real ni autorización efectiva de servidor.**

APK: `apps/mobile/composeApp/build/outputs/apk/debug/composeApp-debug.apk`, 10,8 MiB aproximadamente; requiere Android 8/API 26 o superior. Sin dispositivo físico conectado según `adb devices -l`. No hay APK de producción firmado ni IPA.

## Preparación de emulador

Se descargaron Android Emulator 37.2.13 y Google APIs API 35 x86_64 en `/tmp/redhouse-sdk`; AVD nuevo y aislado `RedHouseApi35`, puerto ADB 5580. Primer arranque falló por buscar `.ini` en un directorio distinto del creado por avdmanager; se corrigió `ANDROID_AVD_HOME=/tmp/redhouse-android-user/avd`. Primer intento de instalación ocurrió antes de iniciar PackageManager y falló con `Can't find service: package`; no se cuenta como instalación aprobada. El diagnóstico mostró descompresión inicial de paquetes del sistema, sin atribuir ese retraso al APK.

## Instalación y arranque Android comprobados

El segundo intento de instalación también fue prematuro: PackageManager existía, pero StorageManager aún no completaba su inicialización; produjo una excepción del sistema. Se conservó `install-during-boot.txt`. Tras comprobar `sys.boot_completed=1`, la instalación terminó con `Success`.

`am start -W -n org.redhouse.mobile/.MainActivity` devolvió `Status: ok`, `LaunchState: COLD`, 32.041 ms de arranque en este emulador Intel. No es una medición de rendimiento de hardware físico. Se confirmó proceso vivo PID 2262 y pantalla inicial Compose a 320×640. Jerarquía accesible: título Red House, gateway, usuario, contraseña, MFA, login y recuperación; sin WebView. Se conservan XML y comprobaciones estructuradas. El primer intento de copiar el dump desde `/sdcard` no encontró archivo; se recuperó directamente con `exec-out uiautomator dump /dev/tty`.

Durante el arranque del sistema hubo un error de Launcher/Quickstep ajeno al paquete; no se atribuye a Red House. No se introdujeron credenciales ni se conectó a producción. **Plataforma comprobada: Android API 35 x86_64, instalación y pantalla inicial.** No hay recorridos con sesión real, validación clínica, cámara/QR/GPS/push, mapa, sincronización ni accesibilidad integral. iOS permanece sin compilar/arrancar.

## Continuación funcional posterior — 09/11/2026

Este expediente conserva el incremento inicial. El estado vigente, nuevos recorridos reales, cambios de backend, pruebas nativas, APK actualizado y dependencias se documentan en [continuacion-20261109/RESULTADOS.md](continuacion-20261109/RESULTADOS.md). No se atribuyen los resultados iniciales a modificaciones posteriores.
