# Cobertura: ensayo XML y antecedentes con dobles

El ensayo `ensayo-xml-real` pasó 1/1 en 65,50 s con servicios locales y cuentas sintéticas. El médico consultó la propuesta XML y abrió la evaluación mediante Qt; obtuvo 403 al consultar una unidad de otra institución. Coordinación consultó la misma propuesta, sin instantáneas clínicas, abrió desde Qt el detalle autorizado de la unidad y consultó una propuesta vacía. El folio y el estado del detalle coincidieron con Inventario. Cinco capturas reales se inspeccionaron; las huellas de las fuentes fueron idénticas antes y después. El fixture y sus motores cerraron.

La denegación se comprobó mediante el cliente XML; no se ejerció visualmente la presentación del 403 ni una caída de red. El ensayo no acredita decisión clínica, otros ámbitos ni Windows.

Después del ensayo real se ajustó solo la redacción del resumen a «Unidades propuestas … · requeridas …». Las capturas `resumen-ajustado/propuesta-doble.png` y `vacia-doble.png`, generadas sin servicios con datos dobles y `STYLE`, se inspeccionaron por separado. No corresponden a una repetición XML; las huellas del ensayo real permanecen intactas.

La ventana presenta cuántas unidades requeridas tienen una unidad propuesta, muestra la versión y fecha del cálculo, distingue que no hay reserva automática y permite seleccionar una pareja. Las etiquetas «Solicitud» y «Unidad propuesta» son referencias temporales de esta ventana, no folios ni identificadores clínicos. «Consultar unidad» solicita el detalle autorizado de Inventario; personal médico puede abrir la evaluación si la instantánea la identifica. Coordinación no recibe instantáneas clínicas y no muestra esa acción. Una propuesta sin resultados explica el siguiente paso.

La repetición Qt sin red pasó 3/3 en 5,95 s; cubre selección, visibilidad por rol, vacío y rechazo de identificadores inválidos con respuestas y llamadas dobles. La captura final `texto-final-fecha/cobertura-doble.png` usa `STYLE` y se inspeccionó visualmente. El primer intento dio 1/3 por un atributo omitido en el cliente doble al cerrar la ventana; su JUnit se conserva en este directorio. No acredita consulta XML ni persistencia reales, permisos reales, respuesta del servicio o recuperación de errores de red.

Queda pendiente verificar desde la GUI un error de servicio y su recuperación, además de otros ámbitos autorizados. Coordinación no recibe acceso a solicitudes clínicas.
