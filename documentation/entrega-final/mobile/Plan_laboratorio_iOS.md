# Plan pendiente: laboratorio iOS para capacidades físicas

**Estado: NO IMPLEMENTADO / NO VERIFICADO.** Preparación autorizada; no acredita cámara, QR, ubicación, conectividad ni aceptación integral de iOS. No se han ejecutado compilaciones, instalaciones ni pruebas físicas como parte de este plan.

La aplicación normal `org.redhouse.mobile` ya está firmada, instalada e inspeccionada en el iPhone 16 Pro. Debe conservarse su instalación y sesión donante. Existe además un artefacto normal más reciente todavía no instalado. Las pruebas de laboratorio se instalarán aparte; las actualizaciones normales ya autorizadas se gestionan por separado, conservando la sesión. El perfil de provisionamiento de `org.redhouse.mobile.lab` y su conexión física al laboratorio siguen pendientes de comprobar. Son verificaciones necesarias, no imposibilidades establecidas. No se presupone crear nuevas cuentas Apple, Firebase o APNs.

## Variante y almacenamiento

- Crear target/esquema `RedHouseLab`, únicamente Debug, con bundle exacto `org.redhouse.mobile.lab` y nombre visible «Red House Lab». El procedimiento de instalación debe rechazar otro bundle.
- Derivar el servicio Keychain del bundle validado contra los dos identificadores admitidos. Normal conserva exactamente `org.redhouse.mobile`; lab utiliza `org.redhouse.mobile.lab`. Conservar las cuentas `session`, `journal`, `observations` y `gateway`, sin copiar ni migrar credenciales entre aplicaciones.
- Mantener Documentos/Application Support dentro del contenedor propio. No incorporar grupos Keychain compartidos, App Groups ni rutas compartidas.
- Derivar coherentemente el identificador BGTask del bundle en registro, solicitud, cancelación y `BGTaskSchedulerPermittedIdentifiers`: normal conserva `org.redhouse.mobile.observations`; lab utiliza `org.redhouse.mobile.lab.observations`.
- Añadir una guarda de coherencia entre bundle, variante y gateway **antes de leer los almacenes o ejecutar `GatewayConfiguration.prepare`**. Ante incoherencia, abortar sin borrar datos. `prepare` conserva su protección actual: cambiar de gateway elimina sesión, diario y cola del entorno anterior.

## Aislamiento de compilación y procedencia

Actualmente `generateMobileEnvironment` declara `gateway` y `gcsBucket` como inputs, pero escribe en `composeApp/build/generated/mobileEnvironment`. El framework también utiliza una salida compartida bajo `composeApp/build/xcode-frameworks`. Declarar esos inputs ayuda a invalidar la tarea; por sí solo no acredita que dos variantes empaqueten el framework correcto.

- Separar directorios de salida y estado incremental de normal/lab, o utilizar una copia/worktree aislada con configuración explícita. Revisar también las rutas de búsqueda y copia del framework en Xcode.
- Declarar todos los nuevos inputs que afecten al resultado: variante, gateway, puerto/origen y configuración/huella de CA. Mantener los valores normales explícitos, excluir la CA del artefacto normal y de Release y conservar en ellos la configuración TLS estándar.
- Verificar posteriormente la secuencia normal → lab → normal, incluida una reconstrucción que pueda considerarse `UP-TO-DATE` o recuperar caché. Comprobar el contenido generado y empaquetado, no solo el estado comunicado por Gradle. El framework lab no debe reutilizarse en normal.
- Conservar un manifiesto por artefacto con variante, bundle, gateway/origen, huella de CA cuando aplique, revisión de fuentes y hashes del framework y paquete. La verificación previa a instalar debe comparar esos datos con el destino esperado.

## HTTPS/WSS local con confianza específica

El proyecto fija Ktor Darwin **2.3.13**. Su API `handleChallenge` permite evaluar desafíos de autenticación; la sesión de esa versión utiliza el mismo delegado para tareas HTTP y WebSocket. Esto respalda la viabilidad del diseño, pero no sustituye su compilación ni validación real.

- Incluir únicamente el certificado **público** DER de la CA local en lab. La clave privada permanece fuera del paquete y del repositorio.
- Habilitar el handler solo en la compilación lab y con bundle exacto `.lab`. Normal y Release no deben incluir la CA ni registrar el callback alternativo.
- Aplicarlo únicamente a `NSURLAuthenticationMethodServerTrust`, para HTTPS/WSS del host y puerto exactos configurados. Comprobar también el origen de la tarea; rechazar incoherencias y conservar la restricción de origen del cliente API.
- Evaluar la cadena hasta la CA anclada, con anclas exclusivas, política SSL de servidor y hostname exacto. Exigir SAN correspondiente al host o IP, vigencia y validación criptográfica; mantener los requisitos TLS. Aceptar la credencial solo tras evaluación satisfactoria. Ante error o recurso ausente, cancelar.
- No aceptar otros desafíos mediante el handler de laboratorio. No ampliar la confianza para otros destinos: cualquier acceso permitido a ellos conserva evaluación estándar. No desactivar validación, usar excepciones generales ATS ni importar la CA al almacén global.
- Servir certificado y cadena completos mediante HTTPS local. El iPhone necesita una dirección alcanzable del Mac; `127.0.0.1` en el teléfono no identifica al Mac. Verificar permiso de red local, resolución/dirección y firewall, sin publicar las bases de datos.

Fuentes oficiales: [configuración Darwin 2.3.13](https://raw.githubusercontent.com/ktorio/ktor/2.3.13/ktor-client/ktor-client-darwin/darwin/src/io/ktor/client/engine/darwin/DarwinClientEngineConfig.kt), [sesión HTTP/WSS 2.3.13](https://raw.githubusercontent.com/ktorio/ktor/2.3.13/ktor-client/ktor-client-darwin/darwin/src/io/ktor/client/engine/darwin/internal/DarwinSession.kt), [delegado 2.3.13](https://raw.githubusercontent.com/ktorio/ktor/2.3.13/ktor-client/ktor-client-darwin/darwin/src/io/ktor/client/engine/darwin/KtorNSURLSessionDelegate.kt). Apple documenta [política SSL y hostname](https://developer.apple.com/documentation/security/secpolicycreatessl(_:_:)), [anclas exclusivas](https://developer.apple.com/documentation/security/sectrustsetanchorcertificatesonly(_:_:)) y [evaluación de confianza](https://developer.apple.com/documentation/security/sectrustevaluatewitherror(_:_:)).

## Verificación pendiente y aceptación

1. Preparar variante, guardas, certificados, configuración local y pruebas con datos sintéticos. No requieren nuevas cuentas. Después comprobar firma y perfil `.lab`: equipo autorizado, identificador, dispositivo, vigencia y entitlements compatibles. La firma normal existente no acredita ese perfil.
2. Comprobar aislamiento usando valores sintéticos en los namespaces, sin leer ni copiar tokens reales. Confirmar que un artefacto incoherente aborta antes de `prepare` y que normal permanece intacto.
3. Probar HTTPS y WSS válidos. Probar rechazo de CA distinta, SAN/hostname incorrecto, certificado vencido, host/puerto no permitido, CA ausente y desafíos no admitidos. Confirmar que normal conserva su evaluación TLS y rechaza la CA privada.
4. Instalar exclusivamente `.lab` tras verificar manifiesto, firma y bundle. La persona concede los permisos de cámara, ubicación y red local que correspondan. No resetear permisos globales ni cerrar la sesión normal.
5. Leer un QR físico mediante AVCapture y correlacionar la validación con el backend sintético. Obtener ubicación mediante CoreLocation con timestamp, precisión y señal `simulated`; documentar dispositivo y procedimiento. `simulated=false` por sí solo no demuestra origen físico. Si se prueba foto, capturarla con la cámara real.
6. Verificar cancelación, permisos denegados y limpieza al abandonar la captura. Conservar evidencia sin secretos y con ubicación/fotografía únicamente autorizadas. No usar mocks, GPX ni inyección para declarar capacidades físicas aprobadas.

Los comandos concretos se incorporarán después de implementar y verificar la variante. La aceptación dependerá de resultados reproducibles; este plan no promete éxito de firma, red o sensores.
