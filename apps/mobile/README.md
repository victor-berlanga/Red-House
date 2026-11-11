# Red House móvil

Aplicación Kotlin Multiplatform / Compose Multiplatform en continuación de etapa 04. Los recorridos de transporte y donante ya se ejecutaron desde Kotlin contra microservicios reales aislados. La aceptación integral Android/iOS sigue pendiente; consulta la matriz para distinguir código, pruebas JVM, instrumentación y dependencias externas.

## Compilar Android

Requiere JDK 17, Android SDK Platform 35 y Build Tools 34.0.0. Configurar `sdk.dir` en `local.properties` (ignorado por Git) o `ANDROID_HOME`.

```sh
cd apps/mobile
./gradlew :composeApp:testDebugUnitTest :composeApp:assembleDebug
adb install -r composeApp/build/outputs/apk/debug/composeApp-debug.apk
```

El APK debug usa firma de desarrollo. No es una firma de distribución. Release se genera con `:composeApp:assembleRelease` y requiere firma externa; no se incluyen claves. Ambas variantes bloquean HTTP, conservan validación TLS y excluyen backups. En desarrollo use un gateway HTTPS con certificado confiable para el dispositivo. No desactive la verificación del certificado.

La compilación normal usa **https://34.18.186.116** por defecto en Android e iOS. El acceso solo pide credenciales; no muestra un campo de gateway. Los servicios mantienen sus prefijos `/services/...` y validación TLS. La VM debe estar encendida. Si una instalación anterior guardó otro gateway, se cancela su trabajo y se eliminan sesión/diario/observaciones locales antes de usar GCP; nunca se transfieren tokens o escrituras entre entornos.

Para otro despliegue autorizado, generar una compilación con `-PmobileGateway=https://servidor-autorizado`; no es una opción del usuario final. El campo editable se conserva exclusivamente en la compilación explícita del laboratorio `-PmobileLabDirectory=...`, para mantener reproducibles sus pruebas aisladas.

## Operación por perfil

- **Transportista:** abrir Traslados y tarea propia. Escanear el UUID de unidad por cámara; el servidor comprueba reserva/tarea. Consultar contactos y ruta de la tarea; elegir la contraparte autorizada del origen/destino, capturar sello y motivo, y confirmar recolección, inicio y entrega. Solo se muestran contactos activos marcados explícitamente como operativos. La ruta identifica la versión reservada y la vigente; advierte cambios sin inventar geometría vial. Volver a escanear antes de cada transferencia. La recepción corresponde al operador de destino y no constituye uso clínico final.
- **Ubicación:** autorizar la sesión de rastreo de la tarea, después capturar/publicar una fijación o activar envíos cada 15 segundos en primer plano. Cada punto conserva dispositivo, evento, secuencia, fuente y hora. Solo `PERSISTED_SQL` confirma el pendiente y lo elimina automáticamente. Si una lectura queda rechazada o incierta, el usuario puede descartarla explícitamente: se detiene la captura, no se afirma recepción remota y la custodia permanece intacta. Volver a autorizar ubicación permite capturar una lectura nueva. Al salir de tarea/primer plano/logout se detienen captura y socket. El backend limita la autorización del teléfono a una hora; renovarla exige otra acción explícita. La cartografía nativa usa OSM en Android y MapKit en iOS. La última observación, fuente, precisión y antigüedad se muestran por separado del estado de conexión. No se inventa una ruta vial ni una ETA medida.
- **Evidencia:** capturar con cámara, revisar preview y cargar/verificar. JPEG se reduce a 1600 píxeles y se vuelve a codificar para eliminar EXIF; se calcula SHA-256. Documentos autoriza la URL GCS; solo su verificación y análisis habilitan uso. Sin configuración real se informa dependencia no disponible. No hay éxito simulado.
- **Donante:** abrir Expediente, consentimiento y agenda. Registrar el expediente propio desde la identidad autenticada; indicar versión/referencia institucional del consentimiento, sin inventar requisitos. Consultar sedes, campañas y horarios; agendar, confirmar asistencia prevista, reprogramar o cancelar. Revisar estado comunicado e historial. La corrección de datos clínicos sigue reservada por el contrato al personal institucional.
- **Operador:** consultar inventario propio, movimientos y capturar lectura térmica manual con referencia del instrumento; el servidor evalúa perfil/equipo y restricciones. En tareas, preparar origen o aceptar recepción en destino tras escaneo. No libera médicamente unidades.
- **Coordinador:** disponibilidad regional y solicitudes institucionales agregadas, reservas autorizadas, tareas/mapa y programación sobre reserva existente. Las consultas de solicitudes individuales no se ofrecen a este perfil porque el contrato las restringe. Programar no equivale a asignar clínicamente.
- **Médico:** consulta institucional de solicitudes, cobertura, muestras, resultados y completitud versionada; no se habilitan dictámenes clínicos desde móvil.
- **Avisos:** bandeja y detalle reautorizados por Alertas. Activar push solicita permiso y registro del proveedor configurado; si falta, la bandeja continúa. No se ha comprobado recepción FCM/APNs.

## Persistencia, sesión y recuperación

`Session` coordina renovación y logout con mutex de proceso compartido entre interfaz y WorkManager, recarga el registro cifrado y rechaza cambio de identidad. `/auth/me` revalida al restaurar. La contraseña no se persiste. Android utiliza AES-GCM con clave Keystore y escritura atómica sin backup; iOS usa Keychain `WhenUnlockedThisDeviceOnly` y cubierta al salir de primer plano.

`ObservationQueue` está conectada a almacenamiento cifrado separado, UI, ciclo de vida y WorkManager con condición de red. Solo admite observaciones no clínicas: ámbito usuario/institución, versión base, ID estable, captura original, máximo 100 filas y vigencia de 24 horas. Guarda `SENDING` antes del envío; tras reiniciar consulta el resultado antes de reenviar el mismo ID. Hasta cinco intentos automáticos con espera progresiva; recuperación manual explícita y estados `RECORDED`, `CONFLICT`, `REJECTED`, `EXPIRED`, `UNCERTAIN`. iOS incorpora BGAppRefresh y reanudación en primer plano, todavía sin verificar ejecución.

Las transiciones de custodia y demás escrituras interactivas conservan clave y cuerpo inciertos en un diario cifrado; nunca entran al sincronizador automático. Recuperar repite exclusivamente la misma operación/idempotencia. El servidor sigue autorizando toda petición. Logout cancela trabajo y limpia registros, solicita revocación de dispositivo/suscripción/sesión e informa revocaciones no confirmadas.

No se usa WebView, XML de negocio, cookies del portal ni acceso cliente a almacenes. La validación JSON incluye envoltura, tipos usados por cada operación y validaciones de resultados críticos; no se acredita validación exhaustiva de todos los DTO/XSD desde móvil.

## Pruebas con servicios reales

El laboratorio monta las aplicaciones Flask reales por servicio detrás de un gateway HTTPS/WSS y usa PostgreSQL/Redis/MongoDB temporales. Este recorrido no acredita despliegue en procesos o contenedores separados. No requiere ni escribe GCS. Se ejecuta desde raíz:

```sh
REDHOUSE_TEST_MONGOD=/ruta/mongod apps/services/.venv/bin/python apps/mobile/tests/real_backend.py
```

Imprime solamente la ruta de un `lab.json` privado fuera del repositorio. No copie su contenido ni el APK de instrumentación a evidencias: contiene una contraseña sintética efímera.

```sh
REDHOUSE_MOBILE_LAB=/ruta/privada/lab.json ./apps/mobile/gradlew -p apps/mobile :composeApp:testDebugUnitTest
python3 apps/mobile/tests/prepare_android_lab.py /ruta/privada/lab.json
./apps/mobile/gradlew -p apps/mobile :composeApp:assembleDebug :composeApp:assembleDebugAndroidTest -PmobileLabDirectory=/ruta/privada/android
```

El opt-in confía únicamente en la CA efímera para `10.0.2.2`, solo en debug. La compilación normal y release no la incluyen. `RealServicesTest` se omite explícitamente si no hay laboratorio; una omisión nunca acredita integración. Para repetir transporte sobre un caso fresco, ejecutar `tests/seed_transport.py /ruta/privada/lab.json`. Los servicios siguen siendo reales; los pacientes, unidades y coordenadas son sintéticos.

Instrumentación comprobada en AOSP API 30 x86_64: instalar ambos APK únicamente en emulador privado. Ejecutar cada clase por separado con `adb shell am instrument -w -e class org.redhouse.mobile.NombreTest org.redhouse.mobile.test/androidx.test.runner.AndroidJUnitRunner`. Limpiar datos de la aplicación entre recorridos independientes; `PermissionDenialTest` requiere permiso inicialmente denegado. `CameraPermissionTest` abre cámara/QR y captura JPEG; no demuestra decodificación óptica.

`DeviceJourneyTest` requiere inyectar `adb emu geo fix -100.3161 25.6866` repetidamente durante la captura. Comprueba publicación WSS real y marcador nativo; la posición aparece como simulada, no GPS físico. `ProfileQueriesTest` comprueba consultas por operador, coordinador y médico; `DonorJourneyTest` reserva y cancela desde Compose.

La recuperación de proceso requiere este orden, sin limpiar datos entre fases:

```sh
adb shell am instrument -w -e class 'org.redhouse.mobile.ProcessRecoveryTest#persistBeforeProcessDeath' org.redhouse.mobile.test/androidx.test.runner.AndroidJUnitRunner
adb shell am force-stop org.redhouse.mobile
adb shell am instrument -w -e class 'org.redhouse.mobile.ProcessRecoveryTest#recoverAfterProcessDeath' org.redhouse.mobile.test/androidx.test.runner.AndroidJUnitRunner
adb shell am instrument -w -e class 'org.redhouse.mobile.ProcessRecoveryTest#workManagerSynchronizesWithoutForegroundUi' org.redhouse.mobile.test/androidx.test.runner.AndroidJUnitRunner
```

La última prueba usa el scheduler real con requisito de red y espera confirmación remota; no llama directamente al método de sincronización. No ejecutar las tres fases juntas con un orden JUnit implícito.

## iOS

Se incluyen los destinos `iosX64`, `iosArm64` e `iosSimulatorArm64`, framework estático `RedHouse`, host UIKit Swift, `Info.plist` y definición `iosApp/project.yml` para XcodeGen. No se utiliza WebView.

En un Mac con Xcode completo compatible, generar el proyecto con XcodeGen y abrirlo:

```sh
cd apps/mobile/iosApp
xcodegen generate
open RedHouse.xcodeproj
```

El paso de construcción ejecuta `:composeApp:embedAndSignAppleFrameworkForXcode`. Mínimo iOS 15. Proyecto generado con XcodeGen 2.46.0 y Xcode 16.3 (16E140), SDK iPhoneOS 18.4. No se descargó runtime Simulator por instrucción vigente. Los resultados de compilación y artefactos constan en el expediente de este incremento. La cuenta Apple, provisioning y firma física no se han comprobado; no se entrega IPA ni se publica en tiendas.

## Versiones y fuentes

Base reproducible inicial: Kotlin 2.1.21, Compose Multiplatform 1.8.2, Gradle 8.11.1, AGP 8.7.2, Ktor 2.3.13, coroutines 1.10.2, serialization 1.8.1, datetime 0.6.2, Activity Compose 1.10.1. Gradle Wrapper incluye checksum oficial. Son versiones fijadas, no una afirmación de ser las más recientes. El mínimo Android 26 reduce la superficie heredada para este prototipo; target/compile 35 corresponden al SDK seleccionado para compilación local, no a una certificación de requisitos actuales de tienda.

Fuentes oficiales consultadas el 09/11/2026:

- [Compatibilidad Kotlin, Gradle, AGP y Xcode](https://kotlinlang.org/docs/multiplatform/multiplatform-compatibility-guide.html): combinación 2.1.21/8.11.1/8.7.2, referencia Xcode 16.3.
- [Compose 1.8.2](https://www.jetbrains.com.cn/en-us/help/kotlin-multiplatform-dev/whats-new-compose-180.html).
- [Android SDK](https://developer.android.com/tools/releases/platforms).
- [Android Keystore](https://developer.android.com/privacy-and-security/keystore).
- [Apple Keychain](https://developer.apple.com/documentation/security/keychain-services).

La compilación no acredita ejecución física, firma ni aceptación integral de iOS. Consulte [matriz y pendientes](../../documentation/entrega-final/mobile/Matriz.md) y [evidencias](../../documentation/evidencias/entrega-final/mobile/android-ios-20261109/RESULTADOS.md).

## Dependencias nativas añadidas

JourneyApps ZXing 4.3.0, osmdroid 6.1.20, ExifInterface 1.3.7, WorkManager 2.10.1 y Firebase Messaging 24.1.2. osmdroid está archivado: se mantiene fijado para este incremento, con atribución OSM, agente identificable y caché extendida siete días; no hay descarga masiva. Revisar su sustitución antes de distribución mantenida.

Fuentes: [ZXing Android](https://github.com/journeyapps/zxing-android-embedded), [política de teselas OSM](https://operations.osmfoundation.org/policies/tiles/), [interop UIKit](https://kotlinlang.org/docs/multiplatform/compose-uikit-integration.html), [FCM Android](https://firebase.google.com/docs/cloud-messaging/android/get-started), [registro APNs](https://developer.apple.com/documentation/usernotifications/registering-your-app-with-apns).

[Dependencias exactas](../../documentation/entrega-final/mobile/Dependencias_externas.md). [Propuesta GCS sin ejecutar](../../documentation/entrega-final/mobile/Aislamiento_GCS_propuesto.md).

## Compilación iOS física sin firma

```sh
cd apps/mobile/iosApp
xcodegen generate --spec project.yml
xcodebuild -project RedHouse.xcodeproj -target RedHouse -configuration Debug \
  -sdk iphoneos -arch arm64 SYMROOT=/tmp/redhouse-ios-products \
  OBJROOT=/tmp/redhouse-ios-objects CLANG_MODULE_CACHE_PATH=/tmp/redhouse-ios-module-cache \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO build
```

El destino directo `-target` permite compilar `iphoneos` aunque la resolución de `-destination generic/platform=iOS` del Xcode instalado exija una plataforma no registrada. No descarga Simulator. El `.app` sin firma **no es instalable**. La versión 0.3.0 conserva las declaraciones de cámara, ubicación y BGAppRefresh en `project.yml`, que genera el Info.plist. La guía [Prueba física iPhone](../../documentation/entrega-final/mobile/Prueba_fisica_iPhone.md) describe firma, instalación y resultados esperados pendientes del usuario.

Para compilar también las pruebas compartidas destinadas al dispositivo, ejecutar `./gradlew :composeApp:compileTestKotlinIosArm64` desde `apps/mobile`. Compilar pruebas no equivale a ejecutarlas en iOS. Las pruebas comunes se ejecutan en Android/JVM con `:composeApp:testDebugUnitTest`.

## Nuevos casos nativos

`CustodyJourneyTest` exige una tarea PREPARED fresca y un QR óptico del `resource_id` sintético frente a la cámara. En emulador usar cámara trasera `virtualscene` y un póster PNG generado con ese ID. No inyecta el resultado del lector ni sustituye el servidor: confirma recolección, tránsito, entrega, aceptación por operador y consulta del coordinador. No acredita evidencia GCS ni GPS físico.

`FormAndRecreationTest` rechaza entradas inválidas de programación antes de confirmar y recrea la Activity. Comprueba restauración cifrada, `/auth/me`, navegación del mismo rol y consulta real. Los resultados ejecutados, fallos y reintentos se registran en [el expediente](../../documentation/evidencias/entrega-final/mobile/android-ios-20261109/RESULTADOS.md).

Póster QR reproducible (solo datos sintéticos del laboratorio):

```sh
python3 apps/mobile/tests/generate_qr.py /ruta/privada/lab.json /tmp/redhouse-qr.png
adb emu virtualscene-image wall /tmp/redhouse-qr.png
```

Arrancar el AVD con cámara trasera `virtualscene` y un renderizador soportado por la versión instalada del emulador. `aim_virtual_camera.py` puede orientar la cámara mediante gRPC local autenticado; requiere `grpcio==1.68.1` en un entorno de pruebas externo. Lee el token del archivo INI de descubrimiento del emulador sin imprimirlo. Ese control mueve la cámara virtual; no sustituye frames, callbacks ZXing ni respuestas del backend. Registrar por separado ANR/arranque fallido y recorridos aprobados. No ejecutar pruebas gráficas mientras el host está saturado por compilaciones.

MapKit habilita accesibilidad nativa en `UIKitInteropProperties` y conserva la última coordenada como texto Compose. La verificación VoiceOver sigue pendiente de dispositivo; véase la [guía oficial de interoperabilidad](https://kotlinlang.org/docs/multiplatform/compose-ios-migration.html).

El catálogo de iconos se conserva como fuente, pero este destino copia PNG desde `iosApp/Icons` y declara `CFBundleIcons/CFBundleIconFiles`. El `actool` de la instalación sin runtimes falló al compilar el catálogo incluso para `iphoneos`; los recursos PNG permiten construir sin descargar Simulator. Es una configuración de desarrollo para pruebas físicas, no una validación App Store. [Referencia Apple de CFBundleIconFiles](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleiconfiles).

El módulo Swift anfitrión se llama `RedHouseHost`; el framework Kotlin mantiene `RedHouse`. Evita que `import RedHouse` se resuelva al propio ejecutable. El callback APNs entrega la referencia a `NoticeLink.receive`, porque el setter de `MutableStateFlow.value` no se exporta como propiedad escribible a Swift.

La decodificación óptica y custodia completa aprobaron en API 30 con `-gpu host -camera-back virtualscene`. Para el escenario Toren1BD del emulador 37.2.13: cargar el póster `wall` y orientar con `aim_virtual_camera.py ... --position -2.307 0.9 2.718 --rotation 11 -150 0`. Bloquear la rotación de pantalla del emulador durante ese ensayo evita que la orientación física de cámara cambie el tamaño de la interfaz. Esto no inyecta el resultado de ZXing. La espera de Compose admite ausencia temporal de raíz mientras se muestra la Activity del lector.

`seed_transport.py /ruta/privada/lab.json --planning-only` prepara una reserva sintética adicional sin cambiar la tarea del ensayo QR. Regenerar assets privados con `prepare_android_lab.py` y reconstruir instrumentación antes de ejecutar `PlanningJourneyTest`: programación, cancelación previa a recolección y reconsulta tras recreación contra servicios reales.

`seed_operational.py /ruta/privada/lab.json` crea por JSON una unidad en cuarentena, equipo/perfiles sintéticos y una muestra incompleta para `OperationalJourneyTest`. El intervalo térmico arbitrario de esa fixture no se aplica como regla clínica. Regenerar assets privados y APK de instrumentación antes del ensayo; no liberar la unidad ni aprobar clínicamente el perfil sintético.

Resultado del incremento: 19 casos Kotlin/JVM y 19 casos nativos Android únicos aprobados; seis casos de servidor para ampliaciones/seguridad. El APK normal 0.3.0 se instala y abre en API 30. iOS compila arm64 sin firma; no se ejecutó en iPhone/Simulator. Artefactos, hashes, fallos y plataformas exactas en [RESULTADOS del incremento](../../documentation/evidencias/entrega-final/mobile/android-ios-20261109/RESULTADOS.md).

`FormAndRecreationTest#rotationRestoresAuthorizedSessionWithLargeText` se ejecuta con `adb shell settings put system font_scale 1.3`; comprueba orientación mediante Configuration, reautorización y consulta real en horizontal/vertical. Restaurar `font_scale 1.0` al terminar. `PermissionDenialTest` requiere `pm clear` antes de su clase; `LocationDisabledTest` debe ejecutarse por separado tras otro `pm clear`, pues concede permisos y apaga/restaura el interruptor real. Estas clases de permiso funcionan también sobre el APK normal sin assets de laboratorio.
