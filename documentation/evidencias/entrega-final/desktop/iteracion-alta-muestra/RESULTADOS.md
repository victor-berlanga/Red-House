# Alta de muestra: preparación

La consola ofrece al operador y personal médico seleccionar una unidad y un perfil mediante consultas paginadas, introducir identificador y confirmar la fecha documentada en hora local. La solicitud se envía mediante XML/XSD y diario idempotente; el servidor conserva la validación de perfil, ámbito y vigencia. No se añaden reglas clínicas.

La selección y el formulario se revisaron con doble en `doble-final/muestra-doble.png`; UI y diario existentes pasaron 16/16. Una prueba específica adicional pasó 1/1 y comprueba con doble la misma clave tras respuesta perdida y el rechazo de una respuesta de otra unidad. El primer intento visual falló por inicialización de workers; se corrigió y su JUnit permanece en `doble-01`. Se retiraron solo espacios al final de líneas del traceback para mantener limpio el diff. No son consultas de laboratorio reales ni acreditan llavero nativo o MFA de esta operación.

El ensayo conjunto `ensayo-vertical` pasó 2/2 en 98,94 s; el caso de muestra registró desde Qt/XML una muestra para la unidad y perfil seleccionados, comprobó `REQUESTED` en PostgreSQL y la recibió hasta `RECEIVED` consultado por el cliente. Los eventos de alta y recepción se comprobaron en SQL. La captura real `ensayo-vertical/alta-muestra-qt.png` se inspeccionó; las huellas de las fuentes coinciden antes y después. El segundo caso corresponde a receptores y solicitudes, documentado en `../iteracion-receptores/RESULTADOS.md`.

La ejecución usó datos sintéticos, proxy Flask/TLS, servicios `TESTING`, Qt `offscreen` y proveedor de clave doble. No acredita colecta/derivados, operación clínica, MFA de esta acción ni recuperación de proceso/llavero real para esta muestra.
