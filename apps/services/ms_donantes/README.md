# Donantes

Gestiona registros preliminares, consentimiento, dictamen humano, donaciones, campañas y citas.

Puerto por defecto: `5102`.

Ejecutar desde `apps/services`: `python run.py donantes --config /ruta/privada/donantes.json`.

Swagger: `/docs`. Contratos estáticos y XSD: [contracts](contracts). Guía común: [README](../README.md).

Apuntes de presentación: [TXT](../../../stuff/presentacion/02-ms_donantes.txt).

## Baja de donantes

`POST /api/v1/donors/{identifier}/withdraw` requiere JWT de médico de la misma institución, `Idempotency-Key`, `version`, `human_confirmation: true` y un motivo de 6–1000 caracteres. Acepta JSON y XML; [ejemplo JSON](contracts/donor_withdraw.example.json), [XSD](contracts/donor_withdraw.xsd) y [respuesta](contracts/donor_withdraw.response.json).

- Sin dictámenes, donaciones, citas ni decisiones de corrección: borra la fila del donante y responde `mode: DELETED`.
- Con cualquiera de esos antecedentes, incluso una cita cancelada: conserva la fila con `status: INACTIVE`, incrementa su versión y responde `mode: INACTIVE`. Cancela las citas `BOOKED`, conservando sus filas y liberando el cupo.
- Ambas variantes registran el actor, fecha, motivo y tipo de baja en una decisión inmutable y emiten auditoría y notificación. Los eventos originales de alta y lectura no impiden eliminar una captura vacía; tampoco se borran.

El listado, los selectores y los indicadores omiten expedientes inactivos. El detalle sigue disponible para los perfiles que ya podían consultarlo, bajo el mismo ámbito institucional, y permite revisar el historial. Se rechazan nuevos dictámenes, donaciones, citas y ediciones sobre un donante inactivo. La baja no elimina su cuenta de acceso ni los recursos obtenidos de donaciones anteriores.

La comprobación y la baja usan una transacción y el mismo bloqueo de fila que las altas relacionadas. No se utiliza borrado en cascada. Las claves foráneas impiden eliminar referencias no previstas. Una versión obsoleta responde 409 y repetir la misma clave/cuerpo devuelve el resultado guardado.

No requiere cambiar el esquema: utiliza el campo de estado existente. Pruebas: `tests/test_donor_withdrawal.py`, con los motores aislados del entorno de pruebas; no ejecutar la suite contra datos de uso diario.
