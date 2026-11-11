# Publicación móvil 04 y gateway predeterminado — 10/11/2026

Solicitud: desplegar las ampliaciones móviles en la VM existente y configurar su IP externa por defecto en la aplicación. Autoriza actualizar ese despliegue y su esquema; no incluye crear infraestructura, configurar proveedores push ni realizar ensayos de objetos GCS.

Destino: VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`, IP reservada `34.18.186.116`. La VM estaba `TERMINATED`; se inició para este encargo. La clave SSH habitual fue rechazada; se utiliza una clave temporal de OS Login con vencimiento de dos horas.

## Alcance preparado

Delta de 75 archivos de backend y contratos respecto de `portal03-20261106`. No incluye fuentes del monolito ni configuraciones privadas. Las imágenes que incorporan bibliotecas compartidas se reconstruyen, incluida web, conservando su código y configuración. La migración 18 amplía únicamente la restricción de fuente del dispositivo para admitir IOS y registra su versión.

## Criterios de comprobación

- Respaldo remoto y restauración de PostgreSQL/MongoDB/Redis verificados antes de instalar; sin sustituir datos remotos por locales.
- Comparación de las columnas históricas antes/después, con cambio esperado exclusivo en `schema_migration`.
- Configuración sensible conservada y fuentes del monolito sin cambios.
- Contenedores sanos, HTTPS con validación del certificado y API protegidas.
- Registro/revocación de teléfonos ANDROID/IOS, autorización por propietario, consultas y WSS real. Sin cambios de custodia ni publicación de posiciones.
- Aplicación con dirección incorporada, sin campo técnico en acceso normal; separación de sesiones y colas respecto de gateways anteriores.
- Compilación Android e iOS arm64; pruebas físicas y proveedores externos continúan separados.

## Resultado comprobado

**Publicado `mobile04-20261110`, esquema 18; VM encendida.**

- Respaldo PostgreSQL/MongoDB/Redis y restauración aislada aprobados. [Informe](backup-report.json); respaldos y configuración privados permanecen en la VM.
- Comparadas 116 tablas: 115 sin cambios, única diferencia esperada en `schema_migration`. Cero diferencias imprevistas. [Conservación](data-preservation.json).
- 86 campos/archivos sensibles conservados sin publicar valores. [Configuración](configuration-preservation.json).
- 30 contenedores sanos, hashes cotejados en 25 contenedores de aplicación y 75 archivos de delta. Las 153 fuentes archivadas de `apps/web/` permanecen idénticas. Nginx válido, systemd y temporizador TLS activos; bases sin puertos públicos. [Runtime](runtime-final.json).
- HTTPS público validado con TLS 1.3; certificado incluye IP `34.18.186.116`, vencimiento registrado 14/11/2026 15:14:33 UTC y renovación automática existente. Portal HTTP 200.
- **46 respuestas JSON comprobadas en el recorrido final**, incluidas 24 de salud para doce API; además doce rechazos 404 de rutas internas públicas. Login/me/logout de transportista, donante y operador; registro ANDROID/IOS, rechazo de propietario ajeno y revocación final. Consultas de inventario, campañas, avisos y contactos/ruta; donante rechazado en tarea operativa. [HTTP móvil](mobile-http.json).
- WSS JSON real: TLS, autenticación y heartbeat aprobados. Suscripción rechazada correctamente con `tracking_closed` porque la tarea consultada carecía de rastreo vigente. **No acredita recepción de nuevas posiciones ni recorrido de custodia**; no se alteró la tarea para forzar aceptación.
- Se registraron y revocaron cuatro dispositivos ficticios en total: dos en cada intento del comprobador. Ningún dispositivo de prueba queda activo; no se modificaron estados clínicos/custodia, proveedores push ni objetos GCS.
- Clave temporal OS Login retirada y copias locales eliminadas; claves previas conservadas. [Cierre](cleanup.json).

## Incidencias conservadas

SSH con la clave habitual devolvió `Permission denied`; la clave temporal con TTL permitió administrar la VM. Durante el arranque secuencial el gateway respondió 502 hasta que web quedó listo; el resultado final es 200.

El primer comprobador intentó `docker cp` al filesystem de solo lectura del contenedor. Se corrigió para ejecutar código por `python -c`, sin relajar el contenedor. Después, el uso de `WebSocket` como context manager falló: se sustituyó por `contextlib.closing`. [Primer recorrido](mobile-http-first.json) conserva las comprobaciones HTTP y las revocaciones antes de ese fallo; no se suma como otro conjunto de criterios aprobados.

La revisión automática rechazó crear un APK de prueba con contraseña incrustada. No se ejecutó esa acción ni se solicitó eludirla. La alternativa usa instrumentación sin credenciales para la interfaz/TLS Android; la autenticación permanece en el comprobador remoto con la configuración privada ya existente.

## Cliente y límites

[Cliente 0.3.1 y evidencias](../../entrega-final/mobile/gcp-default-20261110/RESULTADOS.md). El gateway normal viene incorporado; no se solicita a usuarios finales. Quedan pendientes los recorridos físicos iOS, los demás criterios de aceptación móvil, FCM/APNs y el ensayo GCS aislado autorizado. Este despliegue no cierra integralmente 04 ni sustituye los ensayos 06.

