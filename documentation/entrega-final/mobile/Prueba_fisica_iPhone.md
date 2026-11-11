# Instalación y pruebas físicas iOS

Dispositivo declarado por el usuario: iPhone 16 Pro, iOS 27.0.1. La compilación usa Xcode 16.3/SDK iPhoneOS 18.4 y destino mínimo iOS 15. Un SDK anterior no establece por sí solo incompatibilidad de ejecución. Firma, instalación, ejecución y soporte del depurador son comprobaciones distintas; ninguna se acredita sin el teléfono y sus resultados.

## Preparación y firma

1. Abrir `apps/mobile/iosApp/RedHouse.xcodeproj`, generado con `xcodegen generate --spec project.yml`. Configurar JDK 17, `ANDROID_HOME` y Gradle según el manual; el framework compartido se compila en la fase Gradle de Xcode.
2. En **Xcode > Settings > Accounts**, añadir la cuenta Apple localmente. No enviar contraseña, certificados privados ni claves al chat. En el target **RedHouse > Signing & Capabilities**, elegir un Team autorizado, habilitar **Automatically manage signing** y comprobar el bundle ID `org.redhouse.mobile`. Si ese identificador pertenece a otra cuenta, el titular debe autorizarlo o definir un identificador propio y actualizar coherentemente registro push y provisioning.
3. Conectar el iPhone, desbloquear y aceptar **Trust**. En el teléfono, activar **Settings > Privacy & Security > Developer Mode**, reiniciar y confirmar. Registrar el dispositivo en el Team cuando Xcode lo solicite. La cuenta/Team determina capacidades y vigencia del perfil; no se promete APNs con un perfil gratuito.
4. Seleccionar el teléfono y compilar/instalar. Si Xcode 16.3 no puede preparar el dispositivo iOS 27, conservar el error exacto: no atribuirlo automáticamente a incompatibilidad del binario. Una alternativa es firmar/exportar para el dispositivo registrado y utilizar Apple Configurator con herramientas compatibles. El `.app` sin firma entregado solo acredita compilación: **no es instalable**, no es un IPA firmado ni incluye provisioning.
5. Si se necesita depurar y las herramientas instaladas no soportan ese sistema, usar un Mac/Xcode con soporte documentado para ese dispositivo. No descargar runtimes ni cambiar herramientas automáticamente durante este encargo.
6. Para push, después de disponer del Team/proveedor autorizado, añadir **Push Notifications** al target y generar el entitlement `aps-environment` y perfil correspondientes. Configurar el proveedor para el token `apns:<hex>` y mensajes con `alert_id` opaco. Un callback de registro no acredita recepción.

Fuentes oficiales consultadas: [ejecutar en dispositivos](https://developer.apple.com/documentation/Xcode/running-your-app-on-simulated-or-physical-devices), [Developer Mode](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device), [distribución a dispositivos registrados](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices). Las opciones concretas de interfaz pueden variar entre versiones de Xcode.

## Entorno del recorrido

La compilación normal usa `https://34.18.186.116`, con la VM encendida y certificado confiable. Para ensayos que requieran aislamiento, preparar otra compilación con `-PmobileGateway=https://servidor-autorizado`, accesible desde el iPhone, y cuentas sintéticas independientes de un único rol. `127.0.0.1` y `10.0.2.2` del laboratorio Android no son direcciones utilizables desde ese teléfono. No desactivar TLS ni probar escrituras en producción. Preparar una tarea nueva, unidad con QR UUID, operadores de origen/destino, ruta de reserva y contactos marcados explícitamente como operativos por Identidad. Proporcionar configuración/credenciales por un canal privado, nunca en evidencias.

La fotografía puede capturarse y revisarse sin bucket. Carga, análisis y descarga solo se prueban cuando exista autorización específica del aislamiento GCS. ClamD local validado no acredita ese ciclo por sí solo.

## Lista de aceptación física

Todos los casos siguientes permanecen **PENDIENTES DEL USUARIO**, aunque exista código o compilación. Registrar versión/SHA del artefacto, modelo/OS, caso, resultado observado y un identificador de correlación no sensible. No compartir tokens, fotos clínicas, contraseñas ni expedientes reales.

| Caso | Resultado esperado |
|---|---|
| Instalar y abrir | Firma/perfil aceptados; pantalla Compose; gateway HTTPS preconfigurado; sin WebView |
| Login, MFA requerido y logout | Rol único del servidor, menú correspondiente; credenciales fuera de preferencias; cierre impide recuperar sesión anterior |
| Donante | Expediente propio, consentimiento institucional, horarios reales; reserva, cambio y cancelación persisten; datos ajenos rechazados |
| QR óptico | Cámara lee UUID de etiqueta; desconocido/otra tarea se rechaza; cancelación vuelve sin transferir |
| Custodia | PREPARED → COLLECTED → IN_TRANSIT → DELIVERED; escaneo/versiones/contraparte en cada transferencia; operador destino acepta; coordinador consulta resultado |
| Contactos y ruta | Solo contacto operativo publicado; ruta de reserva con fuente/versión; cambios advertidos sin inventar itinerario vial |
| Cámara | Denegar, autorizar, cancelar, girar; preview correcta, JPEG normalizado y sin EXIF de ubicación; sin acceso general a galería |
| GPS | Denegado/aproximado/desactivado: error claro o precisión real; permitido: fuente IOS, hora y calidad; envío solo durante tarea autorizada |
| WSS y mapa | Publicación JSON y ACK PERSISTED_SQL; marcador cambia por evento; desconexión indica última observación, sin falsear frescura |
| Ciclo de vida | Ir a inicio, bloquear, volver y rotar; no prometer captura continua; cubierta de privacidad; se recupera estado central |
| Sincronización | Observación cifrada, proceso terminado y red cortada; mismo ID al recuperar; sin duplicación; conflicto visible; no envía bajo otra cuenta |
| Operador | Inventario propio, lectura térmica autorizada, verificación y recepción; sin liberación médica |
| Coordinador | Agregados, programación de reserva autorizada y cancelación previa a recolección; sin expedientes clínicos completos |
| Médico | Solicitudes/resultados/completitud propios; sin decisiones clínicas desde notificaciones/cola |
| Accesibilidad | VoiceOver anuncia etiquetas y estado; Dynamic Type permite leer y operar; controles alcanzables en ambas orientaciones |
| Push, condicionado a proveedor | Denegación mantiene bandeja; recepción y deep link reautorizado; recurso ajeno rechazado; logout y rotación sin contenido sensible |
| GCS, condicionado a autorización | Preparación JSON, PUT firmado, hash, ClamD, estado confirmado y acceso privado; fallos recuperables sin afirmar éxito |

No marcar una fila aprobada por observar solo un botón, recibir HTTP 2xx del proveedor push o instalar el binario. Conservar los fallos y repetir después de corregirlos.
