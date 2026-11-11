# Publicación de etapa 03 en la VM GCP existente

Fecha: **6 de noviembre de 2026, America/Monterrey**; artefactos con fecha UTC del 7.
Encargo posterior: «Puedes hacer que la versión de GCP esté también apta para la 04».
Autoriza actualizar la VM existente; mantiene la decisión anterior de dejar la
aceptación integrada pendiente de 06. No autoriza ensayar caídas sobre el entorno habitual.

## Alcance y versión

Portal: **https://34.18.186.116**. VM `red-house`, proyecto `sistemas-integracion-01`,
zona `me-central1-a`. Se encendió la VM existente, se respaldó y se publicó el árbol
aceptado localmente, sin reconstruir etapas 01/02 ni copiar bases/credenciales locales.
Imagen de aplicación: **`portal03-20261106`**; esquema SQL **17**. Los números propios
de los módulos (0.4.4/0.4.1) se conservan; el tag y los hashes identifican esta publicación.

El paquete incluye **3.895 archivos**, SHA-256
`73c165d7aa45ab1874fd652ebd876129291a3e53d7607431b5069b5dcfde078f`.
HEAD base `cbe3503b39a60b6b0a995f1284b2f5b1c3405cae`, **con cambios locales previos**;
no se atribuye el árbol completo a ese commit. No hubo cambios de producto en este
encargo. Los comprobadores y esta documentación se elaboraron después del paquete.

Los **90 casos históricos no se reejecutaron**. Siguen coincidiendo sus 1.234 fuentes
y 205 artefactos. Las cuatro pruebas locales del expediente de aceptación también
son antecedentes, no nuevas ejecuciones GCP. Véanse [integridad](historical-integrity.json),
[paquete](package.json) y [manifiesto publicado](source-manifest.json).

## Respaldo, migración y runtime comprobados

- Respaldo de PostgreSQL/MongoDB/Redis y restauración de verificación en contenedores
  separados; comparación de conteos/hashes, usuarios/permisos y TTL de Redis.
  El respaldo privado permanece en la VM; solo se publica [el informe](backup-report.json).
- Migración aditiva 16→17 con aplicaciones detenidas. Comparadas las columnas
  anteriores de **113 tablas**: **112 intactas**, única diferencia esperada en
  `schema_migration`. [Conservación de datos](data-preservation.json).
- **86 campos/archivos sensibles** coinciden con el respaldo de configuración;
  no se publican valores. [Conservación de configuración](configuration-preservation.json).
- **30 contenedores sanos**, dos réplicas por API; systemd y renovación TLS activos.
  Hashes del host coinciden para 3.895 archivos. Cotejo de fuentes dentro de **25
  contenedores de aplicación**, incluidos 1.193 archivos en web; catálogo HLA conservado.
- `BACKEND_MODE=monolith`, doce propietarios configurados; Nginx valida su
  configuración. PostgreSQL/MongoDB/Redis sin puertos publicados.
  [Runtime y hashes de imagen](runtime-final.json).

La pausa de mantenimiento para respaldo/migración **no es** el ensayo de continuidad
con mapa abierto de 06. No se cortó infraestructura para simular fallos. No se creó
VM, bucket, firewall ni cuenta de servicio. La VM queda encendida para utilizar el portal.

## Comprobación desde navegador

La comprobación dirigida de publicación conserva cada intento por separado. No es
una ejecución de la suite completa ni una nueva aceptación de los clientes móviles.

El [primer recorrido](browser-attempt1/browser.json) comprobó siete perfiles,
MFA en administrador/médico/coordinador, cookies Secure y TLS válido, 21 pantallas
de negocio y **50 instancias Highcharts** contrastadas con sus datos del servidor.
También comprobó 24 respuestas de salud HTTP 200, doce bloqueos públicos de rutas
internas con 404 y acceso anónimo a inventario con 401: **37 comprobaciones HTTP**.

La campaña ficticia creada en ese recorrido se reutilizó en todas las continuaciones;
no se repitió el alta. Su publicación privada persistió en versión 1. Las API JSON y
XML devolvieron el mismo identificador creado por el portal modular. Esta lectura
XML no acredita la aplicación de escritorio ni una nueva validación completa XSD.

Se creó un solo horario de cupo 1. Las [medidas responsive](layout/layout.json) y
capturas a [390](layout/390.png), [768](layout/768.png) y [1440](layout/1440.png)
confirman diseño estable sin desbordamiento horizontal. Revisión visual manual de
390/1440: etiquetas, fechas, cupo, acciones y paginación legibles. No se presenta como
una nueva auditoría axe o certificación completa de accesibilidad.

La [continuación final](browser-final3/browser.json) pasó: ocho comprobaciones
registradas, ocho visitas adicionales y cuatro rechazos HTTP 403 por URL (publicación
de campaña desde donante/institución ajena, política desde donante y mapa desde donante).
El logout web termina la sesión y `/panel` vuelve a redirigir al login.

Administrador registró un dispositivo **SIMULATOR** temporal mediante formulario;
coordinador lo asignó por formulario a un traslado ficticio existente de `transport1`,
sin cambiar su estado. El [mapa abierto](browser-final3/mapa-gateway.png) recibió
`authenticated`, `subscribed` y `tracking.status` por **WSS del gateway público real**.
Al revocar el dispositivo, recibió `tracking_closed` y mostró
[acceso terminado](browser-final3/mapa-permiso-terminado.png). El dispositivo quedó
revocado y conserva historia. Cero errores JavaScript observados en estos recorridos.

No se publicó ninguna posición nueva: la captura muestra correctamente **sin datos**
y coordenadas institucionales pendientes. No acredita GPS físico, latencia captura–mapa,
replay de nuevas posiciones ni recuperación de una caída total. La cartografía OSM
real y su atribución sí se observaron; no se inventaron anclas institucionales.

La [corroboración SQL posterior](persistence.json) pasó: una campaña, publicación
privada versión 1, un horario, un dispositivo revocado y una asignación. La campaña
de prueba queda sin publicación pública; los registros conservan su trazabilidad.

## Incidencias de comprobación conservadas

1. El primer cotejo de runtime se lanzó durante el arranque secuencial; se añadió
   espera explícita a `systemd=active`. Otro intento suponía que `DOMAIN_CONFIGS`
   era un diccionario: la configuración válida de Compose es un directorio. Se
   corrigió el comprobador y el cotejo final pasó; el producto no cambió.
2. `browser-attempt1` se detuvo tras crear la campaña: buscaba el título dentro de
   un enlace y suponía un filtro `q` que esa vista no declara. La continuación
   localizó el registro exacto mediante la API autorizada y abrió su detalle web.
3. [Primera continuación](browser-resume/browser.json): el lector de prueba XML
   esperaba etiquetas `id`; el contrato usa `field name="id"`. Se corrigió el lector.
4. [Segunda continuación](browser-final/browser.json): logout de API devolvió 400
   porque el comprobador omitía `Idempotency-Key`. Se añadió el encabezado exigido.
5. [Tercera continuación](browser-final2/browser.json): lectura del ancho justo
   durante la transición de la barra lateral (441 frente a 390). La prueba dirigida
   conservó ambas mediciones: tras 600 ms, 390/390, 768/768 y 1440/1440. Se corrigió
   la sincronización del comprobador; no se cambió CSS ni se eliminó la aserción.
6. La revisión automática rechazó una descarga mediante comodín de todos los logs
   remotos por posible exposición de secretos. No se repitió ni se intentó eludirla.
   Se conservan los informes sanitizados de lista explícita y los errores observados;
   los logs brutos siguen privados en la VM. No queda autorización de logs pendiente
   para utilizar el portal.

Los intentos fallidos no se ocultan ni se suman como casos nuevos aprobados.

El [consolidado](consolidado.json) identifica intentos, fechas y resultados sin sumar
repeticiones. Procedimientos conservados: [publicación por fases](procedimiento/deploy.py),
[cotejo remoto](procedimiento/verify_remote.py), [Chrome](procedimiento/verify_browser.cjs),
[responsive dirigido](procedimiento/verify_layout.cjs) y [SQL](procedimiento/verify_records.py).
Son procedimientos de este despliegue fechado, con UUID ficticios identificados;
no son un instalador nuevo ni deben ejecutarse sobre otra base sin preparar su ensayo.
Las credenciales se reciben por entrada privada; no están en los artefactos.

Se utilizó una clave SSH temporal con TTL de dos horas para OS Login; se retiró del
perfil al terminar (comando exitoso) y se eliminaron las copias locales de esa clave.
Las claves previas del usuario se conservaron. [Cierre](cierre.json) y
[hashes de los artefactos](artefactos-sha256.json).

## Siete criterios y aceptación integrada

| Criterio | Estado | Pendiente de cierre |
|---|---|---|
| WEB-12 | PARCIAL | Estudio privado de laboratorio en Chrome con objeto/generación exactos y GCS/ClamAV reales: I06-01/02/04/05. |
| WEB-15 | PARCIAL | Evidencia documental del traslado con análisis y descarga reales, incluida orden ajena: I06-01/02/05. |
| WEB-19 | PARCIAL | Ciclo general, versiones, retención/hold efectivos, EICAR y fallos reales de almacenamiento/motor: I06-01 a I06-05. |
| WEB-21 | PARCIAL | Generación/descarga de PDF/CSV/XLSX por GCS, y revocación entre creación y descarga: I06-06. |
| WEB-24 | PARCIAL | Fallos y recuperación controlados de GCS/ClamAV/rastreo con negocio web simultáneo: I06-05/07/08. |
| TRACK-09 | PARCIAL | Caída total de réplicas por gateway real, recuperación con cursor y permisos vigentes, y escritura web durante la caída: I06-07/08. |
| TRACK-10 | PARCIAL | Expediente integrado completo y correlación de las pruebas pendientes: I06-09. Captura física móvil: 04/07. |

Responsables, prerrequisitos y prueba exacta permanecen en
[Aceptación integrada 06](../../../entrega-final/portal/Aceptacion_integrada_06.md):
Infraestructura/Seguridad 06, QA 03 y propietarios Documentos/Transporte/Identidad de
Equipo 01. Falta identificar y autorizar un entorno aislado para cortes y objetos de
prueba. Esta publicación en la VM habitual no concede esa autorización.

ClamAV sano y Documentos ready **no prueban** carga, EICAR, análisis ni descarga
privada del objeto exacto. No se ejecutó ninguno de esos ciclos GCS en este encargo,
ni se permitió una descarga sin análisis o autorización. Se mantienen **27 criterios
APROBADOS y 7 PARCIALES**; no se declara aceptación integral.

La base técnica quedó publicada y comprobada de forma dirigida en GCP. Se puede
continuar el cliente móvil contra las API HTTPS existentes. La aceptación integrada
continúa pendiente de los ensayos 06 identificados arriba.

**Veredicto: APTA LOCALMENTE PARA CONTINUAR A 04.**
