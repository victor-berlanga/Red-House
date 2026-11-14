# Receptores y solicitudes: preparación

La consola permite al personal médico registrar y corregir receptores, editar o cancelar solicitudes con versión y confirmación. El servicio propietario conserva la decisión de permitir la corrección y los controles de retenciones; la interfaz no establece criterios clínicos. Operadores pueden consultar el listado limitado, no modificarlo.

Las capturas `doble-corregido` se inspeccionaron con datos dobles. Una serie UI previa pasó 3/3; la serie combinada UI/diario pasó 17/17, y las pruebas específicas de PATCH con misma clave y conflicto incierto pasaron 2/2. Son pruebas sin servicios y no acreditan persistencia, autorización real ni conflictos concurrentes. La fila de órgano se ocultó después para sangre y se limpia al cambiar tipo; el motivo de cancelación se amplió y las capturas corregidas se inspeccionaron.

En el ensayo conjunto `../iteracion-alta-muestra/ensayo-vertical` pasaron 2/2 en 98,94 s. El caso de receptor usó Qt/XML con médico: alta y corrección del expediente, creación de solicitud por cliente XML, edición y cancelación desde GUI. El operador recibió 403 al intentar registrar un receptor; PostgreSQL confirmó solicitud CANCELLED, versión 3 y cantidad 2, y se comprobaron eventos de las cuatro operaciones en SQL. Las cuatro capturas reales se inspeccionaron. No se modificaron backend ni contratos propietarios.

El fixture usó proxy Flask/TLS, servicios `TESTING`, Qt `offscreen` y clave de diario doble. No se probaron en este ensayo conflicto concurrente real, edición de órgano, expiración de sesión ni recuperación tras terminar proceso. La creación de solicitud se hizo por cliente XML, no mediante su formulario en este caso.
