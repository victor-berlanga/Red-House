# Referencia, etiquetas e inventario de órganos — 16/11/2026

**Dos relecturas Chrome aprobadas sobre LOCAL run04, después de integrar las cinco fuentes candidatas.** La constancia existente conservó su referencia original en listado y CSV; estado «Documentada» y botón «Documentar constancia» inspeccionados. El mismo recurso E2E-B mostró las seis etiquetas traducidas y el menú Órganos y HLA activo tanto en detalle como en destino. No se repitió ninguna operación de negocio.

El defecto inicial era una colisión del campo de presentación `reference`: el listado lo reemplazaba por un código REG aunque el propietario había guardado la referencia correcta. La corrección conserva el campo existente mediante `setdefault`; las filas que carecen del campo mantienen su fallback. No es anonimización. El texto de estado usa los mapas existentes compartidos por HTML y CSV humano; estructura, columnas y contratos API permanecen intactos. Los códigos de evento desconocidos conservan su fallback visible.

## Pruebas y continuación

Las [cuatro pruebas puras existentes](junit-reference-4.xml) aprobaron en 0,882 s: referencia/listado con escape HTML, CSV y fallbacks, protección contra fórmulas y etiqueta de acción sin cambiar la de solicitudes. No se repitieron. [Su corte](unit-source-binding.json) corresponde al candidato de referencia anterior a las etiquetas posteriores; se sustituyó la API por filas sintéticas autorizadas y la navegación por una envoltura mínima, con tabla/macros/exportación reales. No acredita sesión ni persistencia real. El primer JUnit de cuatro pruebas también se conserva privadamente; no se suman ambos como ocho casos.

El [fallo real original](original-failure.json) de `web-authorization-02` permanece FAIL después de una única constancia persistida. Las relecturas usan su comando/UUID anteriores y solo GET de negocio; login, MFA y logout son técnicos. No se repitió el POST ni se sustituyó retrospectivamente el fallo por éxito.

- [Constancia read03](constancia/receipt.json): exit 0, listado/CSV 200, referencia, fechas UTC y evento único correlacionados. La captura muestra «Documentada» y «Documentar constancia»; el CSV privado también contiene Documentada, sin RECORDED. Duración entre marcas del recibo: 22,999 s.
- [Consulta E2E-B web02](e2eb/receipt.json): exit 0, unidad Retirada, destino Descartado, traslado Aceptado y solicitud Cerrada/cobertura Recibido. Duración entre marcas: 23,467 s. En historial se inspeccionaron Registro inicial, Liberación, Reserva confirmada, Recolección confirmada, Recepción aceptada y Controles de conservación vinculados; Órganos y HLA activo en destino.

Cada runner cerró su única familia propia en SQL y Redis antes de iniciar el siguiente. Cero errores JavaScript, ningún POST de negocio y archivos temporales de cookies retirados. Los [cinco hashes anteriores](sources-before.json) y [posteriores](sources-after.json) coinciden con el lote candidato. Los originales privados conservan sesiones/correlaciones; esta evidencia no publica tokens, factores, cookies ni URLs firmadas.

## Inspección y límites

[Informe visual](visual-review.json), realizado sobre las capturas reales sin otra ejecución: [constancia](constancia/01-constancia-listado-corregido.png), [recurso](e2eb/01-recurso.png), [destino](e2eb/02-destino.png), [traslado](e2eb/03-traslado.png), [solicitud](e2eb/04-solicitud.png). Dirección confirmó además recurso y destino. Los campos revisados son legibles, sin recorte relevante. Permanece un UUID completo en el historial de evaluaciones de solicitud, fuera de este ajuste de etiquetas.

El [cierre de run04](fixture-closure.json) confirmó procesos propios cerrados, configuración/originales y fuentes conservados; datos y objetos permanecen disponibles. No se arrancó otro fixture para las relecturas. Esto no acredita nueva autorización clínica, política de retención, ejecución GCP ni cierre de etapas 06/07. Al preparar estas relecturas, el gate permanecía cerrado por los cuatro casos dirigidos; estos dos recibos no los sustituyeron. El [resultado posterior 4/4](../portal-i06-08-local-20261116/RESULTADOS.md) completó después el gate local con las mismas cinco huellas. Esto habilita revisión de publicación, no acredita su ejecución GCP.
