# Guía de demostración del flujo regional

> Versión de interfaz: 14 de septiembre de 2026. Datos ficticios. Monolito local previo a microservicios.

Las etiquetas de las pantallas usan lenguaje operativo (Nombre, Folio, Antecedentes y Vehículo). Esta redacción no cambia el alcance académico ni autoriza datos reales o decisiones médicas automáticas. El aviso de compatibilidad demostrativa y la autorización médica permanecen junto a la evaluación y reserva.

## Preparación

Iniciar desde `apps/web-monolito01` con `python3 run.py` y abrir `http://127.0.0.1:5050`. La actualización local ya conserva la base anterior y sus credenciales. En otra instalación anterior aplicar primero la migración documentada en el README, con respaldo; no reinicializar la base.

Las cuentas iniciales siguen siendo `admin@red-house.test`, `operador@red-house.test`, `operador.valle@red-house.test` y `auditor@red-house.test`, con sus contraseñas existentes. La migración habilita perfiles, pero no crea cuentas ni contraseñas automáticamente.

Desde Administración → Usuarios, crear las siguientes cuentas de demostración con contraseñas elegidas por el Administrador. Los correos son ejemplos de nombres disponibles, no cuentas preinstaladas:

| Cuenta sugerida | Perfil | Ámbito |
| --- | --- | --- |
| medico@red-house.test | Personal médico autorizado | Banco Regional Norte DEMO |
| medico.valle@red-house.test | Personal médico autorizado | Hospital del Valle DEMO |
| coordinador@red-house.test | Coordinador regional | Regional DEMO-NORTE |
| traslado@red-house.test | Personal de traslado | Banco Regional Norte DEMO |

El Operador y Médico no pueden ampliar su ámbito a otras instituciones. El personal de traslado solo verá las órdenes asignadas a su cuenta.

## Formularios y horarios

Al guardar, el botón indica actividad y bloquea envíos repetidos. Si el servidor rechaza un dato, el formulario conserva la captura y muestra el motivo. Ante un conflicto de versión, revisar los cambios mediante «Recargar datos actuales» antes de volver a intentar; no se actualiza automáticamente la versión del expediente.

Los expedientes con donaciones o solicitudes se muestran como consulta para proteger su historia. Cada detalle incluye seguimiento, siguiente paso y responsable. La selección de donantes para una donación muestra únicamente revisiones favorables vigentes registradas; esto no sustituye una evaluación médica.

Al pie del portal se elige UTC o Monterrey. UTC sigue siendo el valor inicial y el formato de persistencia. Las etiquetas muestran la zona de captura y consulta; auditoría y tendencias usan sus días locales. Cambiar horario recarga la página y solicita confirmación si hay datos pendientes. Antecedentes, estudios y observaciones admiten varias líneas.

## Búsquedas y filtros

Los listados con buscador se actualizan al dejar de escribir durante 300 ms. Las listas desplegables y fechas actualizan los resultados al cambiar. No es necesario pulsar Buscar o Filtrar; «Limpiar» elimina los criterios. La paginación respeta los filtros y un cambio de criterio vuelve a la primera página. Solicitudes ofrece estado y urgencia; Donaciones ofrece estado; Traslados permite buscar por recurso, solicitud o institución y filtrar asignación/etapa. Los indicadores del panel abren los listados con los criterios correspondientes.

En Donantes y Receptores puedes filtrar sin perder lo que hayas escrito en el formulario de registro. Si aparece un error de consulta, se conservan los resultados anteriores y puedes pulsar Reintentar. Los controles de registro y autorización siguen requiriendo confirmación explícita.

## 1. Donante, consentimiento y revisión

Con el Operador Norte, entrar a Donantes y registrar un expediente ficticio: folio único, nombre ficticio, institución, ABO/Rh O−, tipo de donación, antecedentes, restricciones y referencia/fecha de consentimiento en la zona indicada. Usar una fecha no futura. El registro inicia pendiente.

Con el Médico Norte, abrir el expediente y usar «Registrar evaluación del donante». Capturar la decisión del ejercicio, su fundamento y la confirmación humana. La aplicación no calcula elegibilidad. Una donación no puede registrarse mientras el estado no sea favorable.

## 2. Donación, recolección y procesamiento

Con el Operador Norte, abrir Donaciones y procesamiento. Registrar un folio y seleccionar el expediente revisado. En el detalle, registrar primero recolección y después procesamiento, cada uno con observación o referencia del procedimiento ficticio. Las fechas se fijan en el servidor y no se puede saltar una etapa.

Con el Médico Norte, abrir la donación procesada. En «Liberar unidad / componente», seleccionar Concentrado eritrocitario DEMO, una ubicación del origen, un folio único y una fecha futura de caducidad capturada. Registrar la referencia de pruebas/liberación y confirmar la decisión humana. Para una solicitud de dos unidades se deben liberar dos unidades con folios distintos.

El detalle de cada unidad permite seguir el vínculo a la donación. Las 36 unidades históricas del inventario inicial se conservan con una indicación de que no se les reconstruyó un expediente retrospectivo.

## 3. Receptor y solicitud de otra institución

Con el Médico Valle, registrar un receptor ficticio O−, requerimiento, urgencia registrada, estudios, restricciones y estado activo. Después crear una solicitud con folio, receptor, concentrado eritrocitario, cantidad 1, urgencia y justificación ficticia. La justificación y el expediente no se muestran al Coordinador ni al Auditor.

## 4. Ruta y candidatos regionales

Con el Coordinador, registrar una ruta dirigida de Banco Regional Norte a Hospital del Valle. Para el ejercicio puede usarse 30 km y 45 minutos, identificando expresamente «Supuesto académico, no ruta real». Las distancias no se infieren de la ciudad ni de la dirección. Registrar también la dirección inversa o una ruta interna si se necesitan esos casos.

Abrir la solicitud y pulsar «Evaluar ABO/Rh y ordenar alternativas». El resultado conserva candidatos, grupo, distancia, estimación, caducidad, explicación y versión RBC-DEMO-1.0. Una unidad sin ruta o sin vigencia suficiente no se propone. Plasma, plaquetas y órganos no utilizan este motor.

## 5. Autorización y reserva

Con el Médico Valle, abrir la solicitud evaluada. Seleccionar la unidad derivada de la donación, registrar la referencia de autorización y confirmar la revisión humana. La operación reserva una unidad por confirmación, conserva la evaluación y reduce su disponibilidad. Si la solicitud pide dos, autorizar dos alternativas, recargando la versión de la solicitud entre operaciones.

Una reserva simultánea, una unidad modificada, una ruta actualizada, caducidad o cantidad ya cubierta producen rechazo sin reserva parcial. Repetir la evaluación cuando hayan cambiado los datos.

## 6. Asignación y traslado

Con el Coordinador, abrir la reserva y programar el traslado: personal del origen, vehículo ficticio, salida prevista y ETA en la zona indicada. La ETA debe ser posterior a la salida, respetar la estimación de ruta y quedar antes de la caducidad capturada.

Con el Operador Norte, registrar preparación. Con el Transportista asignado, registrar recolección, tránsito y entrega en ese orden. Cada evento requiere ubicación declarada, observación sin datos clínicos y referencia de evidencia/acta ficticia.

Las evidencias actuales son referencias documentales inmutables; no se suben archivos. Una incidencia registra lo sucedido sin avanzar estado. La cancelación ordinaria solo se permite antes de recolección y conserva el historial. Devoluciones después de recolección requieren un proceso posterior; no se simulan como una cancelación silenciosa.

## 7. Recepción y cierre

Con el Operador o Médico Valle, abrir el traslado entregado, registrar aceptación y seleccionar una ubicación activa del destino. Una unidad caducada no puede aceptarse para cerrar la solicitud como atendida: se debe registrar la incidencia.

Con el Médico Valle, cerrar la solicitud después de recibir la cantidad completa. Una unidad recibida para esa solicitud no vuelve a aparecer como disponible. La recepción logística y el cierre no registran una transfusión.

## 8. Panel y auditoría

Con el Coordinador, consultar Panel regional: unidades disponibles y próximas a caducar, solicitudes activas/urgentes, recursos reservados, traslados activos, respuesta media e instituciones. La lista institucional, distribución, demanda observada, movimientos y tendencias proceden de datos persistidos. Las oportunidades de transferencia son coincidencias demostrativas con solicitudes existentes; no constituyen un pronóstico.

Con el Auditor, consultar el panel, las asignaciones/custodia y la bitácora. Comprobar quién autorizó, reservó, preparó, transportó, entregó y recibió, sin acceder al expediente clínico ni modificar la evidencia.

## Evidencia reproducible

`tests/regional_browser.cjs` realiza este recorrido mediante formularios de navegador. `tests/test_regional.py` prueba integración, permisos, concurrencia, versiones, caducidad, custodia y rollback. `tests/test_migration.py` verifica actualización desde el esquema anterior y rollback de una migración incompatible. Consultar `documentation/evidence/ampliacion-monolito/Tests.xml` y las capturas asociadas.
