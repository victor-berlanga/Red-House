# Edición personal del expediente de donante — CONT-05

## Decisión y límites

El campo personal autogestionable es `display_name`, el nombre mostrado en el expediente. Es el campo personal no clínico que el modelo vigente ya conserva. El titular puede actualizarlo en un expediente activo vinculado a su cuenta y de su institución, incluso si existe historia; esa actualización no altera los dictámenes ni cambia el estado de elegibilidad.

El donante no cambia por esta operación el folio, vínculo de cuenta, institución, grupo sanguíneo, antecedentes, restricciones, tipo de donación, consentimiento ni decisiones clínicas. El consentimiento conserva su flujo específico. Las correcciones del personal competente conservan el endpoint y las condiciones anteriores. No se agregan datos de contacto sin contrato ni se confunde este nombre con una comprobación de identidad de la persona.

## Contrato y persistencia

`PATCH /api/v1/donors/{id}/personal`, JWT de rol DONOR e `Idempotency-Key`. Entrada JSON/XML: `display_name` y `version`; se rechazan campos extra. La versión técnica procede de la lectura autorizada y la interfaz no pide escribirla. Respuesta mínima: `id`, `display_name`, `version`.

El propietario revalida sesión Redis, institución, titular y estado activo antes de operar, después de tomar el bloqueo de fila y antes de entregar el resultado guardado. Una versión distinta devuelve 409 y exige volver a consultar. Clave y cuerpo iguales recuperan el resultado sin repetir auditoría; la misma clave con cuerpo distinto devuelve 409. Dos ediciones con la misma versión tienen un solo ganador.

La transacción incrementa versión, conserva nombre anterior/nuevo en el historial privado del propietario y emite `DONOR_PERSONAL_UPDATED`. El evento de auditoría incluye campos modificados y versión, sin nombres personales. Los dictámenes, el estado clínico y el resto de datos permanecen intactos. Como en otros comandos, no se promete atomicidad distribuida entre una revocación Redis concurrente y el commit SQL.

## Interfaces y aceptación

Portal: el expediente propio y su listado ofrecen «Editar mi nombre». El formulario muestra un único campo personal y una indicación para solicitar correcciones clínicas a la institución. Conserva CSRF, clave idempotente, versión y retorno al expediente. El móvil debe ofrecer el mismo cambio desde el expediente propio, validar su respuesta y recargar el registro; su integración se realiza después de verificar el endpoint.

Criterios definidos antes del ensayo:

| Criterio | Comprobación |
| --- | --- |
| Edición propia y versiones | JSON y XML, lectura persistida, un incremento, revisión clínica anterior intacta. |
| Ámbito y campos | Rechazo de otro titular, otra institución, otro rol y campos protegidos; recibo inaccesible tras perder el vínculo. |
| Concurrencia y recuperación | Un ganador con dos claves/versiones iguales; mismo recibo tras respuesta repetida; cuerpo distinto rechazado. |
| Auditoría | Una decisión privada y un evento del propietario/proyección; nombres ausentes del evento minimizado. |
| Portal | CSRF y formulario reales; Chrome con cuenta sintética, teclado, guardado, recarga y capturas inspeccionadas. |
| Móvil | Recorrido Android/iPhone del artefacto vigente; no se extrapola desde HTTP ni desde el portal. |

Estado: seis casos API/formulario aprobados en una ejecución y Chrome final 1/1 aprobado por separado; capturas reales a 390/1280 px y expediente recargado inspeccionados. Se conservaron los fallos de preparación/selector y la captura transitoria. [Resultados, comandos y hashes](../../evidencias/entrega-final/edicion-personal-20261113/RESULTADOS.md). Falta integración nativa y publicación; no cierra CONT-05.
