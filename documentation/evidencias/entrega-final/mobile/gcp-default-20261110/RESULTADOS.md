# Cliente 0.3.1 con gateway GCP incorporado — 10/11/2026

La aplicación normal Android/iOS utiliza **https://34.18.186.116** sin pedir dirección al usuario. El despliegue real está [publicado y comprobado](../../../gcp/mobile04-20261110/RESULTADOS.md), tag `mobile04-20261110`, esquema 18. El servidor y la IP reservada ya existían; no se creó infraestructura.

## Cambio funcional y seguridad

- Configuración generada al compilar y compartida por Android/iOS. La pantalla normal muestra credenciales y MFA, sin campo gateway. Otro entorno autorizado requiere `-PmobileGateway=https://...` al compilar; el campo editable existe solamente con el opt-in explícito `mobileLabDirectory`.
- Si una instalación anterior conservaba otra dirección, cancela trabajo y elimina sesión, diario y observaciones de ese entorno antes de usar GCP. No envía credenciales ni reintenta escrituras entre servidores. WorkManager/BGAppRefresh rechazan una dirección persistida distinta de la incorporada.
- Las sesiones y observaciones del mismo servidor se conservan. TLS permanece verificado; no se añadieron excepciones de certificados ni HTTP.
- Versión 0.3.1 (3). Conserva `CADisableMinimumFrameDurationOnPhone=true` en iOS y la configuración local de firma; no se regeneró el proyecto sobre los ajustes del usuario.

## Android comprobado

`RedHouse-0.3.1-debug.apk` compilado, firma v2 válida, instalado y arrancado en AOSP API 30 x86_64. Arranque COLD: 1 781 ms. No es una medición general de rendimiento. Instrumentación retirada después; APK normal permanece instalado en el AVD apagado.

**19 pruebas Kotlin/JVM aprobadas y 2 omitidas explícitamente**: el laboratorio aislado no se inició en este encargo. Las dos nuevas verifican que cambiar de entorno borra credenciales/cola y que conservar el mismo servidor mantiene su estado. [JUnit](junit/), [compilación](android-build.txt).

**Una prueba nativa aprobada**, 6,536 s: instalación limpia, ausencia del campo gateway, controles de acceso, almacenamiento de la IP predeterminada y cuatro respuestas JSON HTTPS readiness desde Identidad, Transporte, Inventario y Donantes. Sin credenciales ni escrituras de negocio. [Instrumentación](native-gateway.txt). Esto no acredita login desde Android; login y permisos se comprobaron por separado en la VM. Los diecinueve recorridos nativos anteriores siguen siendo evidencia histórica, no una nueva ejecución completa.

Artefacto: `.local/artifacts/mobile/RedHouse-0.3.1-debug.apk`, SHA-256 `1ba932816d18af5b4fbaf255691c1047b10967077c1292e159cbad86a427c851`. [Metadatos](android-artifact.json). Sin `lab.json`, `gcp.json` ni CA del laboratorio en el ZIP.

## iOS

**Compilación arm64 aprobada**: Kotlin/Native, Swift y enlace final con Xcode 16.3/SDK iPhoneOS 18.4. El binario contiene la dirección predeterminada (cadena Kotlin/Native UTF-16); Info.plist confirma versión 0.3.1 (3) y `CADisableMinimumFrameDurationOnPhone=true`. [Log filtrado](ios-build.txt), [metadatos](ios-artifact.json).

Artefacto `.local/artifacts/mobile/ios/RedHouse-0.3.1-ios-arm64-unsigned.zip`, 16480500 bytes, SHA-256 `071c8143ca5382d52bac4ec0fe6b378600559e46cf9e279d41bc73529e41d3ef`. **Sin firma/provisioning: no instalable en ese estado, no ejecutado físicamente en este encargo.** El usuario debe recompilar e instalar desde su Xcode para recibir el cambio en el iPhone. No se descargó runtime Simulator. La compilación conserva una advertencia de extracción AppIntents omitida porque el destino no usa ese framework.

El verificador de empaquetado buscó inicialmente la dirección en UTF-8; la comprobación correcta de la cadena UTF-16 pasó sin cambiar la aplicación.

## Incidencias y límites

El primer intento Gradle falló porque el acceso DSL `java` ocultaba el paquete `java.net`; se añadió import explícito `URI`. Se conserva [el intento fallido](android-first-build.txt); la repetición terminó correctamente.

La revisión automática rechazó crear assets de prueba con una contraseña. No se ejecutó esa acción. La prueba nativa final no contiene credenciales; la verificación autenticada permanece dentro de la VM. No se eludió el rechazo.

No se probaron nuevos ciclos GCS, proveedores push ni recorridos físicos. Continúan los pendientes técnicos y externos de la [matriz](../../../../entrega-final/mobile/Matriz.md). No se declara cierre total de 04/06.
