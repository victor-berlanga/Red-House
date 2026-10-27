# Construir la aplicación Android con Kotlin y Jetpack Compose

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Construye una aplicación Android nativa completa en `apps/android/`, usando **Kotlin con Jetpack Compose**, decisión confirmada por el usuario. Debe funcionar con los microservicios reales y datos persistidos; no entregues una WebView del portal ni una demostración con respuestas fijas.

## Arquitectura y preparación

Inspecciona los contratos JSON, autenticación y funcionalidades de los prompts 01 y 02. Define una matriz pantalla/perfil/permiso/servicio/operación/capacidad del dispositivo. La aplicación consumirá al menos cuatro microservicios reales; demuestra, como mínimo, uso de Identidad, Donantes/citas, Transporte y Alertas, más Inventario/Custodia según las tareas.

Separa presentación Compose, estado/ViewModel, casos de uso de cliente, repositorios, cliente HTTP y persistencia local. El cliente controla navegación, captura y sincronización; no replica compatibilidad, prioridad, elegibilidad, reservas ni autorización del servidor.

Incluye Gradle Wrapper, versiones compatibles verificadas con documentación oficial, dependencias reproducibles, variantes de desarrollo/entrega, configuración de URL HTTPS sin secretos, icono y nombre Red House. Justifica minSdk/targetSdk y permisos según el entorno de entrega. No permitas HTTP ni omitas validación TLS en la compilación de entrega.

Si una capacidad backend falta, complétala en su propietario y actualiza JSON/XML, OpenAPI, pruebas y web modular cuando corresponda antes de conectar la pantalla. No supongas que un endpoint existe por su nombre.

## Sesión y protección de datos

- Inicio de sesión JSON, MFA cuando se requiera, consulta de perfil/permisos y registro del dispositivo. No uses cookies ni sesión del portal.
- Guarda credenciales mediante almacenamiento cifrado y claves protegidas por Android Keystore usando mecanismos vigentes. No guardes tokens en preferencias sin cifrar, logs, backups o código.
- Renovación rotativa coordinada: una sola renovación simultánea, tratamiento de reutilización/revocación y actualización atómica. Cierre revoca servidor cuando esté disponible, destruye credenciales locales y cancela tareas de esa identidad.
- Si no se puede confirmar revocación remota, informa el estado y utiliza el mecanismo seguro del backend sin conservar tokens indefinidamente en una cola genérica. Cambiar de usuario no recupera borradores ni notificaciones del anterior.
- Biometría puede desbloquear almacenamiento local, pero no sustituye permisos del servidor ni reautenticación exigida por una operación.
- Protege pantallas sensibles, portapapeles, notificaciones y previsualización de tareas según el dato. Excluye secretos/datos sensibles de copias automáticas y limita cachés y archivos temporales.
- Trata 401, 403, conflicto, validación, rate limit, dependencia caída y error de contrato con mensajes específicos. No vuelvas a intentar una escritura con clave nueva tras timeout.

## Funciones por perfil

### Donante

Registro preliminar con datos mínimos y consentimiento versionado; consulta/edición permitida de su expediente; estado de evaluación comunicado por personal autorizado; campañas con filtros de sede/fecha; disponibilidad de horarios/cupos; agendar, reprogramar y cancelar; recordatorios e historial propio. Muestra requisitos generales aprobados y contacto institucional, sin calcular aptitud o elegibilidad en el teléfono.

El registro de cuenta o vinculación del expediente debe verificar identidad mediante el flujo definido por Identidad; conocer un folio/UUID no permite apropiarse de otro donante. El donante no consulta receptores, HLA ajeno, inventario clínico detallado ni órdenes de transporte.

### Transportista

Lista y detalle de tareas asignadas, origen/destino/contactos operativos autorizados, ventanas y ruta con procedencia, recurso y estado, incidencias y condiciones. Escanea la unidad y verifica contra la tarea en el servidor antes de cada transferencia.

Registra recolección, inicio de traslado, observaciones, ubicación autorizada, fotografía y entrega. Respeta secuencia, responsable, versión y confirmación. Una entrega física capturada no equivale a recepción clínica aceptada. No autorices una unidad fuera de tarea ni acceso general a donantes/receptores.

### Operador de banco

Consulta mínima del inventario propio y tareas de recepción/transferencia; escaneo, verificación de identidad y estado, movimientos permitidos, lecturas térmicas manuales autorizadas, incidencias y aceptación dentro de sus facultades. No dictamen, asignación clínica ni liberación médica por este perfil.

### Coordinador regional

Vista operativa autorizada de solicitudes/traslados, disponibilidad agregada, alertas y tiempos. Permite asignación/programación cuando el contrato lo autorice y sea pertinente en móvil. No expongas expedientes clínicos completos para mostrar un mapa.

### Médico autorizado

Consulta de solicitudes asignadas, resultados pertinentes, completitud y estado de revisión. Las autorizaciones críticas permanecen en los flujos web/escritorio salvo que exista un flujo móvil expresamente aprobado y documentado. No habilites decisiones clínicas desde una notificación o una cola offline.

## Pantallas obligatorias

1. Login/MFA, recuperación de acceso y cierre de sesión.
2. Inicio con nombre, rol, institución, tareas, alertas, conectividad y pendientes.
3. Perfil/expediente propio y consentimiento para donante.
4. Campañas, detalle, agenda, confirmación, cambio/cancelación e historial de citas.
5. Escaneo QR/código de barras y verificación de recurso/tarea/estado/origen/destino.
6. Lista/detalle de traslados, mapa, ruta, ubicación y antigüedad, secuencia y acciones permitidas.
7. Captura de incidencia, lectura autorizada, cámara/evidencia, revisión previa y estado de carga/análisis.
8. Bandeja de avisos y detalle autorizado, sin datos clínicos sensibles en el push.
9. Centro de sincronización con pendientes, enviando, confirmadas, rechazadas, conflicto y acción de recuperación.
10. Ajustes mínimos de privacidad/permisos, dispositivo y ayuda operativa sin exponer secretos.

## Capacidades del dispositivo

Implementa **QR/código de barras, cámara, GPS y notificaciones push**. No basta con botones que abran diálogos simulados.

- Escaneo por cámara y pruebas con códigos reales que no contengan identidad clínica ni autorizaciones; el identificador se verifica en servidor. Código desconocido, duplicado o de otro traslado produce rechazo seguro.
- Cámara con permisos mínimos, orientación/tamaño controlados, vista previa y eliminación de temporales. No accedas a toda la galería si la tarea no lo requiere. Carga con hash y estado confirmado por backend; metadatos de ubicación solo cuando se autoricen.
- GPS solo durante tarea/periodo autorizado, con consentimiento y controles del sistema. Gestiona permiso denegado, ubicación aproximada, GPS apagado y captura antigua. Si se necesita seguimiento en segundo plano, usa el mecanismo Android vigente con indicador visible y justificación; detén seguimiento al terminar o cerrar sesión.
- Push mediante proveedor configurado, por ejemplo FCM si se dispone del proyecto autorizado, registro/rotación/revocación de token y autorización del deep link al abrir. Una notificación contiene referencia opaca y texto mínimo. Bandeja interna funciona aunque el usuario deniegue push.
- Mapa real con proveedor autorizado o alternativa documentada; informa ausencia de red/cartografía. No inventes una ruta ni sustituyas tiempo estimado por medición actual.

## GPS externo y seguimiento por WebSockets

Implementa la [especificación de rastreo GPS y mapa de Nuevo León](09_rastreo_gps_websockets.md). El GPS físico se incorporará después: no asumas marca ni protocolo y prepara un adaptador/puente compatible con Transporte. El GPS Android es otra fuente autorizable, no una sustitución oculta del equipo externo. Identifica la fuente por tarea y usa contratos JSON sobre **WSS** para publicar/consultar el seguimiento permitido, con autenticación, revocación, reconexión y recuperación sin duplicados.

Muestra mapa interactivo actual de Nuevo León y última posición con hora/antigüedad/calidad, diferenciando simulador, teléfono y futuro hardware. Prueba actualización real del mapa por socket y fallos de señal/red. Detén la captura del teléfono al finalizar/logout según política; para el equipo externo aplica el cierre de autorización del backend, sin prometer que logout apaga un GPS autónomo. Las lecturas offline recuperadas no se presentan como ubicación actual ni confirman custodia.

## Offline y sincronización

Implementa almacenamiento local cifrado para la mínima información y borradores permitidos, separado por identidad e institución, con expiración y limpieza. No persistir contraseñas ni datos clínicos extensos para facilitar caché.

Cada comando conserva ID/idempotencia estable, usuario, institución, tipo permitido, recurso, versión base, instante de captura y estado. El servidor agrega hora de recepción y revalida permisos, vigencia y secuencia. Define contrato para consultar resultado después de respuesta perdida, reintentos acotados con espera progresiva y conflictos visibles.

Utiliza trabajo persistente compatible con Android para reintentos permitidos. Prueba cierre/reinicio del proceso, red intermitente, expiración de sesión, cambio de cuenta y revocación del dispositivo. Una tarea pendiente no se envía bajo otra identidad.

Se pueden guardar borradores, observaciones y evidencia pendiente cuando la política lo permita. Las transferencias físicas capturadas offline permanecen pendientes de verificación; no finalizan custodia, no consumen una reserva ni crean aprobación. No ordenes automáticamente eventos contradictorios ni resuelvas conflictos críticos con último escritor. Muestra antigüedad de datos offline y evita acciones que exigen estado central vigente.

## Pruebas y criterios de aceptación

Incluye pruebas unitarias relevantes, contratos JSON, repositorios/sincronización, instrumentación Compose y recorridos contra backend real aislado. Verifica accesibilidad, tamaños de pantalla, rotación, recreación del proceso, cancelación de permisos y ausencia de secretos en logs/almacenamiento inspeccionable.

Demuestra en emulador Android: donante agenda y cancela una cita; transportista recoge y entrega su tarea con QR, ubicación y evidencia; operador confirma recepción; coordinador consulta resultado. Comprueba que datos creados desde móvil aparecen coherentemente en web y escritorio autorizado y que un cambio de institución es rechazado.

Prueba reserva/cupo en conflicto, doble toque, timeout tras escritura, desconexión/reconexión sin duplicación, token revocado y push que intenta abrir recurso ajeno. Comprueba uso JSON de al menos cuatro servicios y ningún acceso a bases/Redis/XML de negocio.

Entrega proyecto compilable, APK instalable de demostración, procedimiento para compilación de entrega con claves fuera del repositorio, instrucciones de Android Studio/SDK, configuración y manual por perfil. Conserva evidencia real de cámara/QR/GPS/push; las capacidades verificadas únicamente en emulador se identifican y las pendientes de dispositivo físico no se presentan como probadas. No publiques en tienda ni distribuyas claves de firma sin autorización vigente. Actualiza `PROJECT_STATUS.md`.
