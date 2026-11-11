# Etapa 04 — incremento Android/iOS, 09/11/2026

Continúa el proyecto existente; etapas 01/02 y cambios anteriores conservados. **Sin cierre total de 04 ni aceptación integral iOS.** No se modificó producción, se descargó Simulator ni se escribió/borró en GCS.

## Implementación comprobable

- Transportista: contactos explícitamente operativos, origen/destino, ruta vinculada a la reserva con fuente/versión/fecha y selección de contraparte autorizada. Transporte reautoriza la tarea después de las consultas internas. Los contactos anteriores permanecen privados (`operational=false`); no se inventa geometría vial.
- Contratos aditivos JSON/XML/XSD/OpenAPI en sus propietarios, sin migración nueva de este incremento. Se conserva la ampliación IOS/registro seguro de dispositivos y migración 18 del incremento anterior, sin aplicarla a producción.
- Formularios compartidos: UUID, fechas con zona/orden y temperaturas finitas; identificadores de muestras/resultados visibles, campos permitidos explícitos y etiquetas accesibles. Ayuda de privacidad y acceso a permisos nativos. El cliente no incorpora reglas clínicas.
- iOS: Keychain, AVFoundation/cámara, CoreLocation, MapKit con accesibilidad nativa, APNs y BGAppRefresh compilados. Se corrigen importaciones CoreCrypto, colisión de módulo Swift (`RedHouseHost`), puente de avisos y permisos generados por XcodeGen. Cancelación de captura al entrar en segundo plano; datos protegidos bloqueados difieren sincronización.

## Pruebas ejecutadas

- **19 Kotlin/JVM aprobadas, cero errores/fallos/omisiones**, repetidas con la fuente final: 15 comunes (`shared-tests/`), 2 contratos y 2 recorridos reales (`real-tests/`). No son ejecuciones iOS.
- **6 casos únicos de backend aprobados**: cuatro en `backend-first.xml` y dos en `backend-context.xml`. Los dos fallos iniciales del arnés se conservan; se corrigieron el argumento `fmt` y el nombre de catálogo duplicado, sin contar reintentos como casos nuevos. Cubren JSON/XML/XSD, contactos privados excluidos, ruta vinculada, usuario ajeno/donante rechazados y endpoint interno protegido.
- **19 casos nativos Android únicos aprobados**, API 30 x86_64. La denegación GPS se repitió en el APK normal y se cuenta una sola vez. La cancelación QR aprobó en un archivo que también conserva el fallo inicial de fotografía; JPEG aprobó posteriormente por separado.

| Caso nativo | Casos únicos | Evidencia |
|---|---:|---|
| Formularios inválidos y recreación | 1 | [native-forms-recreation.txt](native-forms-recreation.txt) |
| Rotación real y letra 130 % | 1 | [native-rotation.txt](native-rotation.txt) |
| GPS inyectado, WSS y marcador | 1 | [native-gps-wss-map.txt](native-gps-wss-map.txt) |
| QR óptico y custodia completa | 1 | [native-custody-optical.txt](native-custody-optical.txt) |
| Programación y cancelación | 1 | [native-planning.txt](native-planning.txt) |
| Lectura térmica y completitud médica | 2 | [native-operational.txt](native-operational.txt) |
| Cancelación del lector QR | 1 | [native-camera-first.txt](native-camera-first.txt) |
| JPEG y limpieza de temporales | 1 | [native-photo-final.txt](native-photo-final.txt) |
| Cámara/GPS denegados, APK normal | 2 | [native-permissions-normal.txt](native-permissions-normal.txt) |
| Ubicación apagada, APK normal | 1 | [native-gps-off-normal.txt](native-gps-off-normal.txt) |
| Persistir antes de cerrar proceso | 1 | [native-persist.txt](native-persist.txt) |
| Recuperar sin duplicación | 1 | [native-recover.txt](native-recover.txt) |
| WorkManager sin interfaz activa | 1 | [native-worker.txt](native-worker.txt) |
| Consultas por tres perfiles | 3 | [native-profiles.txt](native-profiles.txt) |
| Donante reserva/cancela | 1 | [native-donor.txt](native-donor.txt) |

Custodia óptica: consulta contactos/ruta, rechazo de transferencia sin escaneo, tres lecturas ZXing desde fotogramas `virtualscene`, COLLECTED → IN_TRANSIT → DELIVERED → ACCEPTED, cuentas separadas de transportista/operador/coordinador y logout. **Sin inyectar el resultado del lector**. La tarea ya se había usado para GPS inyectado/WSS/mapa antes de cerrar custodia; no se presenta como medición física ni como carga GCS.

Operador: NaN deshabilita confirmación, lectura manual persistida y unidad permanece QUARANTINE. Médico: muestra identificada, completitud falsa, ABO faltante y perfil sintético sin habilitación clínica. La fixture térmica usa un intervalo arbitrario de ensayo, no una recomendación de conservación. Ambas pantallas se operaron con fuente 130 %. Un ensayo separado comprueba configuración horizontal/vertical real, restauración y consulta autorizada; no acredita TalkBack/VoiceOver.

Sincronización: mismo ID cifrado antes/después de cierre forzado, RECORDED real, reconsulta sin duplicación y WorkManager sin Activity visible. Wi-Fi/datos se deshabilitaron entre procesos y se restauraron; **no hubo envío durante ese intervalo**, por lo que ese tramo no acredita timeout de escritura. Los escenarios de respuesta perdida/renovación/concurrencia tienen pruebas comunes complementarias.

## Integración real

`real-services-summary.json` deriva de la ejecución Kotlin final y registra seis propietarios HTTPS: Identidad, Donantes, Inventario, Transporte, Priorización/Geografía y Alertas; además WSS JSON real con respuesta 101, publicación/ACK y distribución. PostgreSQL, Redis y MongoDB son reales y temporales. Se montan aplicaciones Flask reales detrás de un gateway aislado; **no se acredita despliegue de contenedores separados con este laboratorio**. Las respuestas simuladas unitarias no se cuentan como estos recorridos.

## Artefactos

- Android normal **0.3.0 (2)**: `.local/artifacts/mobile/RedHouse-0.3.0-debug.apk`, 14 369 997 bytes, SHA-256 `26c96cd77986997e1ea995f2e9bfa73d45eab24b85f5d3d08eab32fd8b3d121e`. Firma de desarrollo v2 válida, un firmante, minSdk 26/targetSdk 35. Instalado con ADB; MainActivity arrancó COLD en 7764 ms; controles de acceso y Activity activa comprobados. ZIP sin contraseña, `lab.json` ni CA del laboratorio (`apk.json`). Instrumentación retirada después; APK normal permanece instalado en el AVD apagado. Los recorridos de negocio usan la variante TLS privada del mismo código; esa variante y sus credenciales no son entrega.
- iOS **0.3.0 (2)**: `.local/artifacts/mobile/ios/RedHouse-0.3.0-ios-arm64-unsigned.zip`, 16 474 318 bytes, SHA-256 `81a9bce4d2e222b8c02a3c95b407f255554d0b6d07ce9454640d156626ca6207`. Contiene `.app` Mach-O arm64, mínimo iOS 15.0, SDK iPhoneOS 18.4, Xcode 16.3 (16E140). Kotlin/Native, Swift y enlace aprobados; `ios-artifact.json` verifica permisos, bibliotecas de sistema, **ausencia de firma y provisioning**. **No instalable en ese estado; no se ejecutó en iPhone ni Simulator.**
- `ios-compile-tests.txt`: pruebas compartidas compiladas para arm64; no ejecutadas en iOS. `source-sha256.json`: fuentes/configuración del incremento.

Xcode conserva una advertencia: omite extracción de metadatos porque el destino no depende de `AppIntents.framework`. El enlace terminó con `BUILD SUCCEEDED`; no se presenta como compilación sin advertencias.

## Fallos y recuperación conservados

- Imports CoreCrypto/accesibilidad, módulo Swift homónimo y setter StateFlow no escribible desde Swift: errores reales corregidos; diagnósticos filtrados `ios-first-compiler.txt`, `ios-first-swift.txt`, `ios-swift-flow.txt`.
- `actool` solicitó runtime Simulator incluso para dispositivo (`ios-asset-runtime.txt`). El destino copia iconos PNG con `CFBundleIcons/CFBundleIconFiles`; el catálogo queda como fuente. No se descargó runtime. Es configuración de desarrollo, no validación App Store. [Contrato Apple](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleiconfiles).
- ANR de System UI y capturas vacías durante carga del equipo. El arnés QR también exigía raíz Compose mientras ZXing mostraba su Activity; corregido con espera que permite ausencia temporal. `native-custody-optical.txt` conserva el recorrido completo aprobado tras esa corrección.
- Fotografía falló con virtualscene y durante arranque de cámara emulada. `camera-system-ui-anr.png` muestra el diálogo que cubría el disparador. Tras retirarlo y esperar al sistema, Camera2 devolvió JPEG, el adaptador normalizó y eliminó temporal: `native-photo-final.txt`, 33,918 s. QR y JPEG son ensayos de cámara emulada distintos; no lente física.
- ClamD real 127.0.0.1:13310 volvió a responder CLEAN/EICAR INFECTED (`clamd-final.json`); esto no acredita un ciclo GCS.

## Pendientes exactos

**Externos:** cuenta/Team/provisioning/firma Apple y acceso al iPhone; gateway HTTPS aislado accesible y confiable desde ese teléfono; proyecto/configuración FCM y proveedor APNs/entitlement; autorización del prefijo de ensayo y permisos de URL firmada en `red-house-evidencias-sistemas-integracion-01`. No se crearon recursos facturables ni proveedores. El SDK anterior no demuestra incompatibilidad de ejecución con el iPhone 16 Pro/iOS 27.0.1; firma, instalación, preparación del dispositivo y depuración se verifican por separado.

**Verificación técnica pendiente:** recorridos iOS reales, MFA/reautenticación desde interfaz, conflicto concurrente de cupo desde interfaz, lectores de pantalla, pruebas físicas de precisión/cámara/permisos/ahorro de batería y recuperación bajo suspensión del sistema. Se conservan como pendientes, no como capacidades aceptadas por existir código. Push real y ciclo documental GCS requieren además sus accesos autorizados.

[Guía y lista física iPhone](../../../../entrega-final/mobile/Prueba_fisica_iPhone.md), [matriz](../../../../entrega-final/mobile/Matriz.md), [dependencias](../../../../entrega-final/mobile/Dependencias_externas.md). Los expedientes anteriores permanecen en `../continuacion-20261109/`.
