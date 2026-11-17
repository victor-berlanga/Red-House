# Android C: consulta del mismo resultado Qt desde web — 17/11/2026

Una ejecución Chrome sobre el monolito LOCAL existente aprobó la consulta de los registros del handoff Android C→Qt, sin repetir reserva, colecta, procesamiento, fraccionamiento, laboratorio, revisión o liberación. Runner y navegador terminaron con salida 0. La fuente del caso es Android; el nombre del donante sintético conserva «iOS» de su cuenta previa y no identifica la plataforma de esta ejecución.

## Resultado verificable

Operator1 del Hospital 1 consultó nueve vistas con HTTP 200: cita, donante, donación PROCESSED, recurso origen WITHDRAWN, linaje, los dos derivados, muestra RECEIVED y resultado AUTHORIZED. Se conservaron los mismos identificadores; eritrocitos AVAILABLE y plasma QUARANTINE. La interfaz mostró sus etiquetas traducidas y el resultado ABO autorizado documentalmente, sin convertirlo en aprobación clínica.

Operator2, de otra institución, recibió HTTP 403 al consultar el origen y no vio su folio. Cero errores JavaScript y cero POST de negocio. Los únicos POST fueron dos login y dos logout; cada cierre exigió HTTP 302 y regreso al login. Las dos familias propias quedaron revocadas en SQL y ausentes de Redis; cookies temporales retiradas. Los oráculos de negocio y las fuentes antes/después fueron idénticos.

El runtime conservado fue PID 93558, backend monolítico, proveedor LOCAL y esquema existente. Se verificaron UID, hash de argv, cwd y resolución del launcher relativo al archivo canónico, además del único listener. No se inició un portal alternativo, motor, worker ni fixture. TLS verificó la CA y el nombre del servidor antes de admitir únicamente ese SPKI en Chrome. No se usó una excepción general de certificados.

## Inspección de capturas reales

- [Cita Android consultada desde web](cita-android-consultada-web.png): inscripción conservada, campaña Android, sede y horarios legibles.
- [Donación procesada](procesamiento-escritorio-consultado-web.png): estado y pasos Recolectado/Procesado del mismo donante.
- [Linaje y derivados](derivados-escritorio-consultados-web.png): origen, plasma en cuarentena y eritrocitos disponibles.
- [Resultado ABO](laboratorio-escritorio-consultado-web.png): resultado autorizado documentalmente y aprobación clínica «No».

Las cuatro imágenes proceden de esta ejecución y fueron inspeccionadas. El detalle ABO conserva el código `REPORTED` y muestra el valor `O` bajo la etiqueta «Contacto»; no se atribuye una corrección ni aceptación completa de presentación. Los hashes de capturas, scripts ejecutados, recibos y snapshots privados constan en el [resumen saneado](resumen.json), sin publicar contraseñas, cookies ni factores.

## Alcance y pendientes

Cita y colecta se relacionan por el mismo donante; el modelo no conserva `donations.appointment_id` ni se acredita cierre automático de la cita, que permanece BOOKED. Esta lectura completa el tramo web del caso Android C conservado; no acredita por sí sola todos los criterios E2E-C del prompt 07. Último cupo, recordatorio Android, negativa de resultados al donante y accesibilidad mantienen su aceptación separada o pendiente. La [agenda y operaciones Android previas](../mobile/RESULTADOS.md) conservan sus fechas y artefactos; no se convierten en otra ejecución por este informe.

No hubo GCP, escrituras de negocio, nuevas cuentas, cambios de factor, capacidad medida ni operación de iPhone. El paquete preparado y el checkpoint de continuación permanecen privados. No se declara cierre de etapas 04–07.
