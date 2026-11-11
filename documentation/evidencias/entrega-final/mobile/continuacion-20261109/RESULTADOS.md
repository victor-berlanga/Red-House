# Continuación móvil — 09/11/2026

Estado: **incremento funcional; etapa 04 no aceptada integralmente**. Código compartido, Android y adaptadores iOS continúan el proyecto existente. No hubo despliegue, cambio productivo, escritura/borrado GCS ni compra de recursos.

## Entorno y alcance

macOS Intel 15.7.9, JDK 17, Kotlin 2.1.21, Compose Multiplatform 1.8.2, Gradle 8.11.1, Android API 35 x86_64. Servicios Flask independientes con PostgreSQL, Redis y MongoDB temporales; gateway HTTPS/WSS y CA efímera privada. Sin respuestas HTTP/WSS simuladas en recorridos reales. Cuentas, unidades, donantes y coordenadas sí son sintéticos.

La prueba Kotlin corre en JVM con Ktor/OkHttp real; **no equivale** a abrir cámara ni a dibujar el mapa en el emulador. Las pruebas de sesión/cola aisladas emplean MockEngine y se reportan aparte. El backend no usa GCS en este laboratorio.

## Pruebas ejecutadas

| Expediente | Resultado | Qué acredita |
|---|---|---|
| `backend.xml` | 3 aprobados iniciales | Registro propio ANDROID/IOS, aislamiento/revocación, QR y sesión móvil WSS real |
| `backend-regression.xml` | 19 aprobados / 1 fallo | Regresión de 20 casos únicos de rastreo/permisos/persistencia/recuperación |
| `wss-replicas-repeticion.xml` | 1 aprobado | Repetición del único fallo de arranque de réplicas; mismo test, sin ampliar timeout ni cambiar producto |
| `kotlin-real/` | 10 aprobados | 9 unitarios originales y un recorrido Kotlin real de transporte |
| `kotlin-donante/` | 1 aprobado | Agenda real: consentimiento, reserva, reprogramación, cancelación y acceso ajeno rechazado |
| `kotlin-final-intento/` | 11 aprobados / 1 fallo | 10 unitarios y transporte real aprobados; repetición donante chocó con datos existentes |
| `kotlin-donante-final/` | 1 aprobado | Repetición respeta sede única y expediente único por cuenta; agenda aprobada |
| `kotlin-final/` | 14 aprobados, 0 fallos, 0 omitidos | 12 unitarios de sesión/cola/contratos y 2 recorridos reales Kotlin actualizados; consulta también Geografía |
| `kotlin-entrega/` | **15 aprobados, 0 fallos, 0 omitidos** | 13 unitarios y 2 recorridos reales después de corregir cámara, donante y descarte GPS |
| `push-rotation-delivery.xml` | 3 aprobados | Rotación/reactivación propia en servicios/PG/Redis reales y compatibilidad JSON/XML de entrega; SMTP/push son receptores locales de prueba, no FCM/APNs |
| `shared-schema.json` | Aprobado | Migración aditiva 18, generación/restauración temporal y 116 tablas compartidas |

No se suman repeticiones como pruebas únicas adicionales. Los tres primeros casos están incluidos en la regresión posterior: total backend **20 casos únicos aprobados entre ejecución y repetición**, conservando el fallo inicial. El fallo WSS se produjo al esperar disponibilidad de una réplica bajo carga local; su log no emitió diagnóstico adicional. La repetición sin cambios pasó.

El primer recorrido Kotlin detectó interpretación incorrecta de `/auth/me`; se corrigió el cliente a la respuesta real. La repetición de agenda detectó primero sede duplicada y después el índice único de expediente por cuenta. Se corrigió el aislamiento/reutilización de fixtures, sin aflojar restricciones de servidor. Un intento de instrumentar trazas del test no compiló por un import Ktor ausente; corregido antes de su ejecución. Las trazas conservadas contienen únicamente método/ruta/código HTTP, nunca cuerpos, contraseñas o tokens.

La ampliación posterior de Alertas corrige dos carencias concretas: rotar/reactivar una suscripción conservando la unicidad por usuario/canal, y enviar `alert_id` al proveedor sin confundirlo con el ID de entrega. Sus tres pruebas nuevas pasaron en 79,17 s. No acreditan recepción FCM/APNs.

## Recorridos reales

Transportista: login/restauración, registro propio, autorización temporal, QR ajeno 409 y correcto, WSS autenticado/suscripción/publicación, `PERSISTED_SQL`, actualización del estado recibido, observación durable reconstruida y confirmada. Transiciones `PREPARED → COLLECTED → IN_TRANSIT → DELIVERED`; operador destino verifica y acepta. Coordinador consulta `ACCEPTED`; Inventario y Alertas se consultan por sus contratos; donante consulta campañas y no accede al traslado. Al menos cinco microservicios consumidos directamente por JSON, además de coordinación interna Custodia/Auditoría.

Donante: login, expediente vinculado a identidad, consentimiento versionado, campaña/horarios reales, reserva/cambio/cancelación. Donante ajeno no lee expediente, y DONOR no consulta inventario. La repetición usa el expediente autorizado existente, porque el esquema compartido permite uno por cuenta.

Los ensayos backend cubren WSS JSON/XML, fuentes IOS/ANDROID/SIMULATOR/GPS_BRIDGE, deduplicación y secuencia, permisos/revocación, almacenamiento y recuperación, réplicas y dependencias interrumpidas en entornos temporales. La migración y contratos XML no convierten el móvil en consumidor XML.

## Android nativo

Se generaron e instalaron APK principal y APK de instrumentación del laboratorio. Los tres primeros intentos de instrumentación devolvieron `Process crashed`, sin casos completados; hubo ANR de componentes Android y un arranque manual de actividad agotó 91503 ms. No se presentan como pruebas aprobadas ni se atribuye una causa única sin evidencia. Se ensayó GPU host sin Vulkan; posteriormente se restableció únicamente el AVD sintético para descartar estado local corrupto. Un intento prematuro de instalación, antes de completar boot, recibió NPE del PackageManager; no se atribuye al código móvil. Se instaló después imagen AOSP API 30 rev. 11 x86_64 y creó un AVD independiente de 360×720, donde sí arrancaron las pruebas.

La compilación privada de laboratorio agrega CA restringida a `10.0.2.2` solo en debug. Su APK de tests contiene una contraseña sintética: **no se distribuye ni se archiva aquí**. El artefacto normal se recompiló sin esa propiedad: `.local/artifacts/mobile/RedHouse-0.2.0-debug.apk`, 14288077 bytes, SHA-256 `cfd986c632b27b631da7c90ddaf1f7ab9e79428ca98f05d2914a361c71aef324`. Firma verificada en `apk-signature.txt`; `apk.json` comprueba ausencia de assets y CA efímera. `android-build.txt` conserva compilación y prueba final. Instalación final aprobada. `android-normal-ui.json` comprueba los cinco elementos de acceso desde UI Automator sobre este APK normal; `android-normal-qr.txt` confirma lector/cancelación. Los arranques `am start -W` agotaron su plazo de aproximadamente 11 s y un primer dump no encontró raíz; se conservan los intentos. La pantalla se comprobó posteriormente sin cambiar código ni APK. No se acredita un objetivo de rendimiento de arranque.

### Instrumentación aprobada en API 30

11 casos nativos únicos aprobados en ejecuciones por fases y distintos incrementos (no una suite monolítica sobre un único APK). El APK normal final repite arranque y lector QR; los recorridos HTTPS/WSS usan la compilación privada de laboratorio:

| Evidencia | Casos / resultado |
|---|---|
| `android-permission-denied.txt` | 1: denegación de ubicación devuelve error sin coordenada |
| `android-camera-final.txt` | 1: Camera2 produce JPEG normalizado y borra temporal |
| `android-normal-qr.txt` | 1: lector abre/cancela cámara sobre el APK normal final; no decodificación óptica |
| `android-process-persist.txt`, `android-process-recover.txt` | 2: proceso separado por `am force-stop`, Keystore conserva ID, Transporte confirma y reconsulta sin duplicar |
| `android-workmanager.txt` | 1: scheduler real sincroniza sin UI activa; `SUCCEEDED`, ID estable y `RECORDED` remoto |
| `android-journey-final.txt` | 1: Compose, captura LocationManager inyectada, WSS real, marcador MapView y privacidad/logout |
| `android-profiles.txt` | 3: consultas reales por operador, coordinador y médico, con menú restringido |
| `android-donor-final.txt` | 1: reserva/cancelación real desde Compose y limpieza de sesión, 70,08 s |

Se conservan fallos previos de cámara (carrera del temporal y disponibilidad del shutter), espera del registro de dispositivo y flujo donante. La cámara ahora elimina el temporal antes del callback. Donante separa diálogo, usa claves estables en listas y bloquea acciones durante carga inicial. Tras esos cambios pasó el recorrido; no se atribuye una causa única a la excepción previa de `SlotWriter`.

Las pruebas de cámara usan imagen generada por el emulador; no hardware físico. Abrir ZXing no demuestra decodificación óptica. Las consultas de otros perfiles no acreditan todos sus formularios. El flujo Kotlin completo de custodia y el recorrido nativo GPS/WSS/mapa tienen alcances distintos.

## Plataformas y accesos externos

`ios-sdk-ausente.txt`: solo CommandLineTools; no SDK iphonesimulator ni simctl. El intento Gradle iOS fue detenido por contención de recursos y no acredita compilación. Swift/MapKit/CoreLocation/APNs/Keychain/BGAppRefresh están en fuente, pendientes de compilar con Xcode completo. Sin firma física ni IPA.

`gcs-metadatos-solo-lectura.json`: bucket existente con acceso uniforme y prevención de acceso público. Metadatos no prueban permisos de firma, carga, ClamAV o descarga. [Propuesta de aislamiento sin ejecutar](../../../../entrega-final/mobile/Aislamiento_GCS_propuesto.md).

No se encontró configuración FCM/APNs autorizada. Proveedor HTTP de Alertas debe configurarse y demostrar recepción real en dispositivo; bandeja interna funciona por JSON. [Dependencias precisas](../../../../entrega-final/mobile/Dependencias_externas.md).

## Reproducción

Desde raíz, preparar venv de servicios y dependencias locales según sus manuales:

```sh
REDHOUSE_TEST_MONGOD=/ruta/mongod apps/services/.venv/bin/python -m pytest apps/services/tests/test_mobile_transport.py apps/services/tests/test_final_tracking.py --junitxml=/ruta/privada/backend.xml
REDHOUSE_TEST_MONGOD=/ruta/mongod apps/services/.venv/bin/python apps/mobile/tests/real_backend.py
```

La segunda orden imprime ruta privada del laboratorio. En otra terminal:

```sh
REDHOUSE_MOBILE_LAB=/ruta/privada/lab.json ./apps/mobile/gradlew -p apps/mobile :composeApp:testDebugUnitTest
python3 apps/mobile/tests/prepare_android_lab.py /ruta/privada/lab.json
./apps/mobile/gradlew -p apps/mobile :composeApp:assembleDebug :composeApp:assembleDebugAndroidTest -PmobileLabDirectory=/ruta/privada/android
```

Para repetir transporte crear caso nuevo con `apps/mobile/tests/seed_transport.py /ruta/privada/lab.json` y volver a preparar assets. Instalar ambos APK privados; ejecutar AndroidJUnitRunner. `PermissionDenialTest` requiere permisos limpios; `DeviceJourneyTest` requiere inyección `adb emu geo fix -100.3161 25.6866` durante la captura. Las coordenadas inyectadas deben conservar `simulated=true`.

## Criterios aún abiertos

Recorridos nativos completos de custodia y formularios restantes; decodificación óptica QR; revocación/ubicación aproximada y red intermitente nativas; accesibilidad/rotación/pantalla bloqueada; contactos operativos detallados y ruta confirmada con procedencia. El diario WSS incorpora descarte explícito de una lectura sin confirmar: detiene captura, conserva otras tareas/custodia y nunca fabrica un ACK. Su prueba unitaria no sustituye un recorrido nativo de rechazo y recuperación. Los campos compartidos añadidos están conectados, pero no todos tienen recorrido instrumentado aprobado. Validación JSON crítica implementada; DTO exhaustivo y separación completa de estado/ViewModel aún requieren revisión.

Estos pendientes técnicos son distintos de Xcode/firma, proveedor push y autorización GCS/ClamD. Ninguna dependencia externa convierte las pruebas pendientes en aprobadas.

## Integridad del expediente

`source-manifest.json` identifica las fuentes móviles y los propietarios backend relevantes. `evidence-manifest.json` contiene hashes de los archivos de este expediente, salvo él mismo. El manifiesto no convierte fuentes no ejecutadas en capacidades aprobadas. Se comprobó ausencia de contraseña efímera y JWT en los archivos archivados. No se distribuyen APK de instrumentación, claves ni CA privadas.
