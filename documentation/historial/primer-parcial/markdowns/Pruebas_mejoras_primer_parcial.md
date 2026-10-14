# Cómo probar las mejoras del primer parcial — 23 de septiembre de 2026

> **Actualización del 27 de septiembre de 2026:** órganos/HLA ya dispone de flujo independiente para riñón, hígado y corazón, con estudios e interpretación humana, preselección ilustrativa, reserva y custodia. Sustituye las menciones anteriores que lo dejaban pendiente. La migración 004 amplía el esquema a 46 tablas. El procedimiento, reglas y límites se documentan en `documentation/historial/primer-parcial/markdowns/Guia_del_flujo_de_organos.md`; las capturas reales están en `documentation/historial/primer-parcial/capturas/README.md`.


Este incremento mejora el monolito conforme a la retroalimentación; no inicia microservicios, clientes ni infraestructura del segundo parcial. Usar exclusivamente datos ficticios y cuentas autorizadas. Los nombres de perfil siguientes no implican crear nuevas credenciales.

## Preparación

Desde la raíz del repositorio:

```sh
cd apps/web
.venv/bin/python -m flask --app run:app migrate-db
PORT=5050 .venv/bin/python run.py
```

En Windows, usar `.venv\Scripts\python.exe` en lugar de `.venv/bin/python`; establecer `PORT` según la terminal utilizada. Detener previamente la instancia antigua si ocupa el mismo puerto. No ejecutar `init-db`, reinicializar ni volver a cargar datos para aplicar este incremento.

La migración 003 conserva la urgencia anterior del receptor en `legacy_urgency`, sin utilizarla ni completarla para altas nuevas. No cambia cuentas, contraseñas, folios ni cierres anteriores. Las solicitudes ya recibidas antes de actualizar conservan la opción explícita de completar su cierre; no se cierran masivamente.

## Recorrido corto de interfaz

1. **Coordinador:** entrar al panel regional. Debe existir un solo acceso al panel. Comprobar indicadores, alertas al inicio, gráfica con tabla visible, distribución completa por institución, cinco caducidades y últimos movimientos sin desplegables.
2. **Coordinador → Rutas:** crear o editar una estimación. Capturar origen/destino cuando corresponda, kilómetros y minutos. Ya no se solicita fuente/supuesto. El motivo se captura al confirmar; la procedencia manual, autor, fecha y versión quedan registrados. Fuentes previas se conservan en las rutas no modificadas y en la auditoría al actualizarlas.
3. **Médico → Donantes:** abrir un expediente con el ojo y con el lápiz. El ojo no permite guardar. Revisar estado, etapa actual, última evaluación, responsable, cronología y donaciones relacionadas, si existen. La edición histórica permanece protegida.
4. **Médico → Receptores:** el formulario de registro aparece directamente; Nuevo registro desplaza hasta él. No debe aparecer urgencia. Un folio nuevo `AB` debe rechazarse; uno como `REC-230923` debe aceptarse si no existe. Completar los campos obligatorios ficticios. Guardar vuelve a la tabla y muestra acceso al registro creado. Los folios antiguos cortos no se renombran.
5. Modificar un formulario sin guardar e intentar salir. Cancelar el aviso debe conservar la captura. En una tabla filtrada, abrir el lápiz y utilizar Volver para recuperar la URL de la consulta.
6. **Traslado:** el inicio debe llevar a sus traslados asignados y el menú no debe incluir Panel principal.
7. **Auditor:** abrir un evento de consulta. LIST se presenta como Consulta de listado y SUMMARY como Consulta de resumen/panel. El ojo explica su alcance, actor, fecha, motivo, resultado y cambios registrados, cuando existan. No muestra contenido clínico copiado a la bitácora.
8. Repetir consulta de solicitudes y candidatos con un ancho de 390 px. Los registros regionales se organizan como tarjetas, con folios legibles y Factores y límites visibles.

## Flujo de solicitud hasta cierre automático

Preparar un receptor activo, componente `RBC`, unidades disponibles con vigencia suficiente y ruta registrada desde el origen al destino. La compatibilidad es ilustrativa y exige revisión humana; no usar estos ejemplos como reglas clínicas.

1. **Médico de destino:** crear solicitud por **2 unidades/bolsas**, indicando urgencia y justificación. La cantidad es un entero, no litros; cero y más de cien deben rechazarse.
2. Buscar unidades potencialmente compatibles. Comprobar fecha de evaluación, institución, ABO/Rh, caducidad, distancia y tiempo. Consultar Factores y límites y Detalles del cálculo, visibles sin desplegarlos.
3. Autorizar y reservar una unidad con confirmación humana y referencia. Volver a la solicitud: debe quedar una unidad pendiente de reservar. La alternativa utilizada no debe seguir siendo seleccionable.
4. Reservar la segunda. La cobertura debe mostrar dos reservadas y cero pendientes; ya no se ofrece reservar más.
5. **Coordinador:** programar cada traslado con responsable activo del origen, vehículo, salida y ETA.
6. **Operador de origen:** preparar cada recurso.
7. **Transportista asignado:** registrar recolección, tránsito y entrega con observación, ubicación y referencia de evidencia.
8. **Operador o médico de destino:** aceptar la primera unidad y seleccionar una ubicación receptora activa. La solicitud sigue en atención, con una recibida.
9. Aceptar la segunda. La solicitud debe quedar **Cerrada**, automáticamente, con fecha y un único evento de cierre en historial/auditoría. La recepción no registra una transfusión.
10. **Auditor:** verificar la cadena de custodia y el cierre. Intentar repetir una operación con una versión anterior debe rechazarse.

## Cancelación y alternativas no disponibles

- Crear otra solicitud sin reservas. Usar Cancelar solicitud; comprobar mensaje, motivo obligatorio y botón específico. Volver a editar no debe cancelar. Confirmar deja Cancelada, conservando historial.
- Una solicitud con reserva no ofrece cancelación directa. El coordinador debe cancelar primero la reserva antes de recolección. No se permite cancelar silenciosamente una entrega aceptada.
- Sin ruta, la búsqueda explica que faltan estimaciones. Sin inventario disponible, lo indica. Un componente distinto de RBC no ofrece evaluación automática.
- Si cambian disponibilidad, ruta o caducidad después de evaluar, la reserva debe rechazarse y solicitar otra evaluación.

## Continuar sesión

1. Iniciar sesión y abrir un formulario. Capturar un borrador sin enviarlo.
2. Aproximadamente a los **10 minutos desde el ingreso o la última renovación**, aparece un aviso fijo, sin contador, cinco minutos antes del vencimiento. No depende de inactividad.
3. Elegir Continuar sesión: el diálogo se cierra, el borrador permanece y comienza otro periodo de 15 minutos. La credencial anterior queda revocada en el servidor.
4. Con otra pestaña del mismo navegador, comprobar que comparte la sesión renovada. No se transfieren borradores entre pestañas.
5. Elegir Cerrar sesión debe cerrar el acceso. Si se deja vencer sin responder, se redirige directamente al inicio de sesión, sin ventana de sesión terminada ni confirmación de salida por borradores. La interfaz no promete guardar en servidor un borrador no enviado.

## Alcance y evidencia

No se incorporaron volumen por bolsa, reglas clínicas nuevas, correcciones versionadas de expedientes ni órganos/HLA funcionales. Urgencia/antigüedad ordenan solicitudes; las unidades candidatas mantienen el orden logístico por caducidad, tiempo y distancia.

Los resultados de este incremento se resumen en `PROJECT_STATUS.md`. La guía regional conserva el recorrido por perfil con el nuevo cierre automático.
