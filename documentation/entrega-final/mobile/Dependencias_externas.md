# Dependencias externas de etapa 04 — 09/11/2026

Se inspeccionaron `/Applications`, `~/Applications`, `xcode-select`, `xcrun`, configuración móvil y nombres de archivos locales. No se imprimieron secretos. No se crearon recursos GCP ni se cambió producción.


## Preparación local posterior — 09/11/2026

Por solicitud del usuario se preparan las dependencias locales. Las inspecciones de ausencia que siguen describen el estado anterior, no el resultado de esta preparación.

- XcodeGen **2.46.0** instalado con Homebrew; `xcodegen --version` y lectura de `iosApp/project.yml` comprobados.
- ClamAV **1.5.4** preparado en `.local/tools/clamav-1.5.4/`, con enlace `/usr/local/clamav` aprobado mediante diálogo de administrador. Se conserva configuración propia en `.local/runtime/clamav/`; no se modificó producción ni se habilitó un servicio de arranque automático.
- El instalador se obtuvo del sitio oficial. La primera consulta `pkgutil` dentro del sandbox indicó firma inválida; la repetición fuera del sandbox confirmó certificado Cisco `DE8Y96K9QP`, timestamp del 07/08/2026 y notarización Apple de confianza. Antes de ejecutar también se comprobó la firma PGP separada contra la clave publicada por Cisco/Talos, fingerprint `5BADCA2665EF59DCF8A23D8B707F0DB480836771`, con resultado válido. No se desactivó Gatekeeper ni se modificaron los binarios. El intento Homebrew de ClamAV se interrumpió para evitar compilar LLVM/Rust y sus dependencias en Intel.
- FreshClam descargó y verificó `daily` 28178, `main` 63 y `bytecode` 339. ClamD real está preparado para **127.0.0.1:13310**, sin exposición pública. Prueba con `redhouse.malware.scan`: contenido inocuo `CLEAN`, muestra estándar EICAR `INFECTED`. Esto acredita el motor local, no el ciclo documental móvil ni GCS.
- Para el laboratorio usar `CLAMD_HOST=127.0.0.1` y `CLAMD_PORT=13310` en la configuración efectiva de sus propietarios. Actualizar firmas con `.local/tools/clamav-1.5.4/update.sh`; iniciar cuando no esté activo con `.local/tools/clamav-1.5.4/start.sh`. Comprobación: `PYTHONPATH=apps/services apps/services/.venv/bin/python .local/tools/clamav-1.5.4/check.py`. Los procesos del sandbox pueden necesitar autorización de red local. ClamD ya está activo al terminar la comprobación; no iniciar una segunda instancia sobre el mismo puerto.
- El usuario proporcionó `/Users/victorberlanga/Downloads/Xcode_16.3.xip`; se extrajo correctamente en `/Applications/Xcode.app`. `codesign --verify --strict` fuera del sandbox terminó con código 0 (firma válida y requisito designado satisfecho). El usuario autorizó aceptar la licencia; Developer directory seleccionado y `xcodebuild -runFirstLaunch` aprobado. `xcodebuild -version`: 16.3, build 16E140; SDK iPhoneOS 18.4 comprobado. Gatekeeper aceptó Xcode como `Apple System`. No se descargará runtime Simulator por ahora: el usuario prefiere probar con teléfono físico.
- Dispositivo declarado por el usuario: **iPhone 16 Pro, iOS 27.0.1**. Se distinguen compilación con SDK 18.4, firma, instalación, ejecución y depuración. El SDK anterior no demuestra por sí solo incompatibilidad de ejecución. La compatibilidad de conexión/preparación del dispositivo con Xcode se verificará cuando exista acceso físico. No se descargará runtime Simulator por instrucción vigente.
- Firebase/APNs y permisos de ensayo GCS siguen pendientes. No se creó proyecto ni se habilitó facturación, no se escribió en el bucket y no se configuraron credenciales push. Evidencia local de preparación: `.local/dependency-preparation-20261109/verification.json`.

Fuentes oficiales: [descargas ClamAV](https://www.clamav.net/downloads), [configuración ClamAV](https://docs.clamav.net/manual/Usage/Configuration.html), [requisitos de Xcode](https://developer.apple.com/xcode/system-requirements), [notas Xcode 27](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes). Consultadas el 09/11/2026.

## Gateway disponible — 10/11/2026

La VM existente quedó encendida con `mobile04-20261110` y esquema 18. HTTPS de `https://34.18.186.116` valida con certificado para esa IP; Android/iOS 0.3.1 lo incorporan sin pedir configuración al usuario. No falta un gateway común para iniciar sesión. Un entorno aislado adicional sigue siendo requisito para los ensayos de caídas o GCS que aún no están autorizados. [Resultados del despliegue](../../evidencias/gcp/mobile04-20261110/RESULTADOS.md).

## Apple: dependencias vigentes

- Xcode **16.3 (16E140)** en `/Applications/Xcode.app`, Developer directory seleccionado, licencia y configuración inicial completadas. SDK iPhoneOS **18.4** y XcodeGen **2.46.0** disponibles. Las ausencias documentadas en el expediente anterior son históricas.
- El proyecto se genera con `cd apps/mobile/iosApp && xcodegen generate --spec project.yml`. Los permisos y el identificador `org.redhouse.mobile.observations` se conservan en `project.yml`; regenerar no debe borrar las declaraciones del Info.plist.
- No hay runtime Simulator instalado; no se descargó. La compilación `iphoneos`/`arm64` Kotlin/Swift/enlace aprobó; también compilaron las pruebas comunes para arm64. La `.app` sin firma no acredita instalación ni arranque. Evidencia y hashes en `android-ios-20261109/ios-artifact.json`.
- Falta seleccionar una cuenta local en **Xcode > Settings > Accounts**, seleccionar **Target RedHouse > Signing & Capabilities > Team** y habilitar la firma automática para un bundle ID autorizado. El usuario configura la cuenta en Xcode, nunca comparte contraseña, certificados ni claves en el chat. Conectar el iPhone, confiar en el Mac y habilitar Developer Mode. Si la cuenta requiere registro del dispositivo, incorporarlo al perfil de desarrollo. No se ejecutó aprovisionamiento remoto.
- APNs requiere además App ID habilitado para Push Notifications, perfil compatible y entitlement `aps-environment`; no se añade ese entitlement a una compilación sin proveedor/firma preparados.
- [Procedimiento de instalación y pruebas físicas](Prueba_fisica_iPhone.md). Todas las comprobaciones del iPhone continúan pendientes de evidencia del usuario. El expediente `android-ios-20261109` registra por separado generación, compilación, bibliotecas enlazadas y verificaciones de artefacto.

## Push

No se identificaron `google-services.json`, `GoogleService-Info.plist`, archivos FCM/APNs ni proyecto proveedor autorizado en las rutas inspeccionadas. Se incluyeron adaptadores nativos; su código no demuestra recepción.

Android: proporcionar recursos públicos Firebase de la aplicación autorizada (`google_app_id`, `gcm_defaultSenderId`, `google_api_key`, `project_id`) mediante directorio externo `-PfirebaseResources=/ruta/res`. El paquete debe ser `org.redhouse.mobile`. No introducir credenciales de servidor en esos recursos. Se usa Firebase Messaging 24.1.2, inicialización automática desactivada hasta consentimiento, permiso POST_NOTIFICATIONS y mensajes **data-only** con `alert_id` opaco. No enviar payload `notification` con texto sensible: Android puede mostrarlo sin pasar por el filtrado del cliente.

iOS: registro APNs nativo, autorización del sistema y callback del token. El destino se identifica como `apns:<hex>`. Hace falta firma/entitlement y proveedor que procese ese destino.

Backend Alertas conserva su adaptador HTTP `PUSH_ADAPTER_URL`/`PUSH_ADAPTER_TOKEN`: configurar un proveedor HTTPS autorizado que entregue por FCM/APNs y transforme el evento opaco al `alert_id` autorizado. Ese servicio proveedor aún no existe configurado. El sobre saliente conserva `event_id` como ID de entrega/idempotencia y agrega `alert_id` como referencia opaca para el deep link; nunca debe abrirse una entrega como si fuera una alerta. Un 2xx del adaptador no se presenta como recepción física. El cliente valida el recurso por JSON al abrirlo; una notificación nunca ejecuta acciones clínicas.

El contrato existente admite un destino por cuenta/canal: el registro rota o reactiva la misma suscripción bajo bloqueo y conserva auditoría, sin crear duplicados. Otro teléfono de la misma cuenta reemplaza ese destino; no se promete entrega multidispositivo.

Rotación: Android conserva token cifrado y actualiza el registro al volver a primer plano; no promete rotación inmediata con la aplicación cerrada. Logout elimina token del proveedor/local y solicita revocación de suscripción antes de destruir sesión. Si no hay red, la revocación remota puede quedar sin confirmar; el acceso a contenido siempre requiere sesión válida.

## Evidencia GCS

Bucket existente comprobado solo por metadatos. Ver `Aislamiento_GCS_propuesto.md`: falta autorización para escribir/borrar en el prefijo aislado, comprobar permisos de firma de URLs y ejecutar el ciclo autorizado. ClamD real ya está disponible y volvió a verificarse con contenido limpio y EICAR en este incremento. No se sustituye el análisis por mocks. La captura/preview, SHA-256, preparación JSON y PUT firmado están implementados; la carga completa aún requiere prueba autorizada.

## Dispositivos

Android se comprobó en emulador AOSP API 30 x86_64. Los intentos API 35 sufrieron fallos/ANR y no acreditan recorridos. Las posiciones inyectadas se etiquetan `ANDROID` + `simulated=true`; no son GPS físico. No se ha conectado un teléfono Android/iPhone físico. El puente externo `GPS_BRIDGE` existente permanece separado y no exige comprar hardware.
