# Android C — último cupo y recordatorio persistido, 17/11/2026

## Preparación y cierre del operador

El entorno académico LOCAL registró una campaña sintética de capacidad dos y un horario de capacidad uno. Al terminar el alta, el horario tenía un cupo libre y cero ocupados. El alta creó cero usuarios y envió cero solicitudes de reserva.

El ejecutor de preparación conserva **FAIL**. Registró `ValueError` en el logout y `RuntimeError` al verificar el cierre. La revisión del código identificó que el ejecutor omitió `Idempotency-Key`, cabecera que la ruta exige. La consulta posterior confirmó un solo evento LOGIN atribuible a la preparación y una única sesión nueva aún activa en PostgreSQL y Redis.

La revocación de esa sesión concreta con las credenciales del servicio de Identidad terminó **PASS**, con código 0. PostgreSQL registró la revocación y Redis confirmó la ausencia de la clave de sesión. Las demás sesiones del operador conservaron su estado. Esta intervención realizó cero peticiones HTTP y cero escrituras de negocio. La campaña y el horario quedaron disponibles para continuar el ensayo.

## Último cupo disputado

Dos cuentas intentaron reservar el único cupo del mismo horario. El rival obtuvo HTTP 201 y Android recibió 409 `slot_full`. La conciliación de negocio confirmó una sola cita `BOOKED`, un cupo ocupado, cero disponibles, idempotencia del ganador y ambos eventos concordantes en Auditoría SQL y MongoDB. El rival cerró sesión y se verificó el cierre de una familia en SQL y Redis. Los casos anteriores se conservaron.

El ejecutor conserva **FAIL temporal**. Las entradas WSGI quedaron separadas **1,157497 s**, por encima del umbral de 1 s del ensayo. El oráculo registró `business_passed_concurrency_failed` con `concurrency_accepted=false`. El punto del último cupo de Prompt 07, línea 76, pide que solo una cuenta obtenga confirmación y no fija un umbral de 1 s. Se observó ese desenlace y el rechazo en Android. Las pruebas generales de concurrencia conservan su alcance.

Dirección inspeccionó las capturas privadas 01, 04, 05 y 06. Revisó el historial de la cita anterior, el expediente con consentimiento, la confirmación del horario de las 18:08 y el rechazo «Este horario ya no tiene cupo. Elige otro horario.» con disponibilidad cero y «Agendar» deshabilitado.

## Segundo horario y reserva nativa

El operador creó un solo horario nuevo de capacidad uno en la misma campaña y sede. El setup pasó, cerró una familia SQL/Redis y conservó la reserva rival. El setup no envió solicitudes de reserva.

Android confirmó el horario de las **18:19** con un único toque. El primer POST recibió 401, la app renovó la sesión y el reenvío con la misma clave de idempotencia recibió 201. La consulta al propietario confirmó una sola cita `BOOKED`, con horario `BOOKED` versión 1, y la cita anterior intacta. Dirección inspeccionó la pantalla de confirmación de la app. El observador del primer intento conserva **FAIL** porque terminó tras leer el 401, antes de la renovación y el 201. Los recibos posteriores documentan el desenlace sin otro toque.

## Recordatorio persistido

El preflight encontró dos citas elegibles del caso. El worker real de Donantes se ejecutó una vez y terminó con salida 0. El oráculo de solo lectura aprobó para la cita Android de las 18:19 el recordatorio de la versión vigente, el aviso dirigido al donante, el aviso separado del operador y la concordancia de Auditoría SQL y MongoDB.

En Android apareció la tarjeta «Recordatorio de tu cita». El único toque en «Ver detalle» devolvió «Respuesta no válida del servicio». Dirección inspeccionó las capturas 01 y 02 del aviso y del error. El fallo de detalle queda abierto.

## Cierre de sesión y pendientes

Un único toque en «Cerrar sesión» revocó una familia nativa en PostgreSQL. La comprobación de solo lectura confirmó su ausencia en Redis y cero familias activas de la cuenta. Dirección inspeccionó la captura 03 de la pantalla de inicio de sesión vacía.

El reinicio y la reapertura de la app no se ejecutaron. Quedan pendientes «Ver detalle» y la traducción de las etiquetas `ELIGIBLE` e `INFO`. El registro persistido y la tarjeta de Android no acreditan entrega push del sistema operativo.

El [resumen verificable](resumen.json) reúne resultados y huellas de los recibos privados.

Huellas SHA-256 de los recibos privados

- Preparación original `d9b1bc7ce0d632fd9232eb1d28b35c882da341a5750ed865fce6809ac019c915`
- Revocación de la sesión `2d67e4fc0d086c769a9e145184025910480e3e3ed9c72d1cf878354c7455e65a`
