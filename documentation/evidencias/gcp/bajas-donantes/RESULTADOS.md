# Baja de donantes y salida sin aviso

Verificación del **21 de octubre de 2026** contra `https://34.18.186.116` y un entorno temporal aislado dentro de la misma VM. El usuario autorizó eliminar registros sin historia, conservar los relacionados mediante baja lógica y quitar el aviso del navegador al salir del formulario.

## Uso

1. Iniciar sesión con perfil **Médico**.
2. Abrir **Donantes** y pulsar el **icono de papelera** en el registro o en su detalle (etiqueta «Retirar donante»).
3. Revisar nombre y folio, indicar el motivo y confirmar la operación.

Sin dictámenes, donaciones, citas ni correcciones documentadas se borra la fila del donante. La auditoría de alta, accesos y baja se conserva. Con cualquiera de esos antecedentes, incluso una cita cancelada, se cambia el estado a `INACTIVE` y se conservan las relaciones. Las citas pendientes se cancelan y liberan su cupo.

Los inactivos desaparecen de los listados, selectores e indicadores activos. El detalle histórico sigue disponible bajo los permisos anteriores; ya no ofrece acciones de edición, dictamen, donación o baja. La API también impide nuevas operaciones sobre ese expediente. La cuenta de acceso y los recursos obtenidos de donaciones anteriores se conservan.

Volver, Cancelar y recargar ya no muestran el aviso nativo de cambios sin guardar. Las modificaciones pendientes se descartan. No se quitaron CSRF ni las confirmaciones de operaciones.

## Evidencia

| Criterio | Resultado | Evidencia |
| --- | --- | --- |
| Borrado físico sin historia y auditoría única al repetir | Aprobado | [JUnit: 27 pruebas](withdrawal-tests.xml) |
| Baja lógica con dictamen, donación, cita activa, cita cancelada o corrección | Aprobado; registros conservados y citas pendientes canceladas | [Pruebas automatizadas](../../../../apps/services/tests/test_donor_withdrawal.py) |
| Rechazo por rol, institución, versión, motivo o confirmación inválidos | Aprobado | [JUnit](withdrawal-tests.xml) |
| Cita simultánea a una baja | Sin huérfanos ni reservas activas del donante dado de baja | [JUnit](withdrawal-tests.xml) |
| JSON/XML y formularios CSRF en ambos modos del portal | Aprobado; monolito probado con las API detenidas | [JUnit](withdrawal-tests.xml) |
| Volver, Cancelar y recargar desde un formulario modificado | Cero diálogos; cambios sin guardar descartados | [Navegador](browser.json) |
| Baja desde el portal público, con y sin historia | Ambas completadas; detalle histórico sin acciones nuevas | [Navegador](browser.json), [captura](baja-con-historial.png) |
| Persistencia real y auditoría central en GCP | Cero filas para el borrado físico; una fila `INACTIVE` para la baja lógica; un evento de baja por registro | [Comprobación SQL](verification.json) |
| Conservar datos previos | Iguales por cantidad y hash: 70 donantes, 64 dictámenes, 60 donaciones y 118 citas | [Comprobación SQL](verification.json) |
| Despliegue y dependencias | 27 contenedores saludables; once readiness 200 | [Despliegue](release.json) |
| Código ejecutado | Hashes coincidentes en web y las dos réplicas de Donantes | [Comprobación de contenedores](verification.json) |

La ejecución final de las 27 pruebas terminó con cero fallos, errores u omisiones en **86,509 segundos**. El navegador ejecutó cinco controles, sin diálogos ni errores JavaScript. Los dos expedientes de esta comprobación se crearon específicamente para ella: uno se eliminó y el otro permanece inactivo con su dictamen y auditoría. No se dieron de baja registros preexistentes.

## Implementación y reproducción

La baja usa `POST /api/v1/donors/{identifier}/withdraw`, disponible también en Swagger. [Contrato y reglas del servicio](../../../../apps/services/ms_donantes/README.md#baja-de-donantes). Utiliza el estado existente, una transacción, bloqueo de la fila del donante, versión e idempotencia. No hay migración, borrado en cascada ni nuevos motores o bibliotecas de aplicación.

La suite está en `apps/services/tests/test_donor_withdrawal.py`; utiliza el fixture aislado común. En GCP se ejecutó con PostgreSQL, Redis y MongoDB temporales, sin puertos publicados, adaptando únicamente la preparación del fixture a esos contenedores. Se incluyeron además ocho casos existentes de mantenimiento, donación, citas, integración web y contratos. No se conectaron esas pruebas a los almacenes de la aplicación pública.

La comprobación de navegador es [verify_donor_withdrawal.cjs](../../../../deployment/gcp/verify_donor_withdrawal.cjs). Requiere Chrome/Playwright y las credenciales privadas ya existentes; se ejecuta como cliente HTTPS y termina el navegador y sus sesiones. Desde la raíz del repositorio, con el entorno de navegador preparado:

```sh
NODE_PATH=.local/gcp-public/browser/node_modules node deployment/gcp/verify_donor_withdrawal.cjs
```

Este comando crea y da de baja dos expedientes nuevos en GCP cada vez que se ejecuta. El que tiene historial permanece inactivo. No es un comando de arranque.

Se construyeron las imágenes en la VM y se actualizaron únicamente `donantes-a`, `donantes-b` y `web`, conservando los archivos privados de Compose y recargando Nginx. El resto de los componentes permaneció encendido. Respaldo previo: `/opt/redhouse/.local/donor-withdrawal-20261021/backup/before.dump`, 5 249 286 bytes, SHA-256 `ec29461a019f8f713c7e5a54144aaa68ae4bfbb27593bb2620db7cb737155807`. Se validó su listado; no se ensayó una nueva restauración. La misma carpeta conserva una copia del código. Docker conserva las imágenes anteriores con la etiqueta `before-withdrawal-20261021` para recuperación administrativa.

## Incidencias y límites

Dos preparaciones del entorno aislado se detuvieron antes de ejecutar los casos: un montaje impedía guardar las ACL de Redis y una clave del adaptador confundía la contraseña del motor con la de las cuentas de prueba. Se corrigieron y se recreó únicamente el entorno temporal. La primera ejecución funcional obtuvo 25 aprobadas y dos fallos de aserción: se buscaba el texto «Dar de baja» en toda la página y coincidía con el mensaje de éxito. La comprobación se corrigió para buscar enlaces de baja; la ejecución final de 27 casos pasó completa.

La primera cuenta de contenedores por etiqueta de Compose incluyó el MongoDB de prueba porque su imagen heredaba esa etiqueta. Los componentes reales estaban saludables. Tras retirar los cuatro contenedores temporales, sus volúmenes y su red, la cuenta final confirmó 27 saludables.

No se probó Safari directamente: Chrome comprobó la navegación y se retiró el manejador `beforeunload` que originaba el aviso. No se implementó reactivación de expedientes ni se cambió la lógica clínica. Las reglas de conservación normativas y la operación clínica/productiva continúan fuera de esta validación.

## Ajuste posterior de presentación

El 21 de octubre, después de la verificación funcional anterior, el usuario pidió sustituir «Dar de baja» por una papelera y eliminar las explicaciones de implementación del portal habitual. El listado y el detalle usan el icono con nombre accesible «Retirar donante» y ayuda al pasar el cursor. La confirmación conserva nombre, folio, motivo y autorización, con este aviso: «Dejará de aparecer en la lista de donantes. Sus citas pendientes se cancelarán».

Se ajustaron también los textos del expediente inactivo, seguimiento de reservas, propuestas, historial de traslados, archivos y errores de consulta/carga. Los bloques de versiones, hashes, identificadores técnicos y claves internas del historial se muestran únicamente en las vistas autorizadas de administración y auditoría. Los perfiles operativos conservan estados, fechas, motivos, responsables, antecedentes y advertencias clínicas. Se mantiene la evidencia técnica en las API y sus documentos.

| Criterio | Evidencia |
| --- | --- |
| Papelera en listado y detalle, ayuda y uso con teclado | [Revisión Chrome](portal-copy-browser.json), [detalle](donante-papelera.png) |
| Confirmación breve, motivo y cancelación sin ventana nativa | [Captura](confirmacion-usuario.png) |
| Expediente inactivo, propuestas, evidencias y diagnóstico según perfil | [Diez controles aprobados](portal-copy-browser.json) |
| Solo el portal actualizado; 27 contenedores saludables y once readiness 200 | [Despliegue y hashes](portal-copy-release.json) |
| Datos conservados durante el despliegue | Mismos conteos y hashes: 71 donantes, 65 dictámenes, 60 donaciones y 118 citas en [el informe](portal-copy-release.json) |

Chrome consultó **27 páginas** con siete cuentas de seis perfiles: médicos de ambos hospitales, operador, coordinador, administrador, auditor y donante. Terminó con cero errores JavaScript, cero diálogos y cero formularios de negocio enviados. Las consultas y los inicios/cierres de sesión conservan su auditoría habitual. Se validó la sintaxis de 16 plantillas y 18 módulos Python, Ruff y los scripts JavaScript; las capturas se revisaron visualmente. La suite funcional anterior de 27 casos no se repitió para este ajuste de presentación. Los casos existentes que buscaban el texto anterior quedaron adaptados al enlace con icono y al nuevo aviso.

Reproducción desde un equipo cliente con las dependencias de navegador y credenciales privadas existentes:

```sh
NODE_PATH=.local/gcp-public/browser/node_modules node deployment/gcp/verify_portal_copy.cjs
```

El [script](../../../../deployment/gcp/verify_portal_copy.cjs) consulta los datos existentes, incluido el expediente inactivo creado por la verificación anterior. No crea ni retira donantes. No inicia servidores locales. La comprobación de evaluación de candidatos se ejecuta solo si la solicitud seleccionada dispone de una evaluación; no se ejecutó esa rama en esta revisión. Los mensajes de fallo se revisaron en código, sin provocar caídas del sistema público.

Se reconstruyó únicamente `web`, conservando los archivos privados de Compose y recargando Nginx. Las fuentes anteriores y el manifiesto están en `/opt/redhouse/.local/ui-copy-20261021/`; Docker conserva `redhouse/web:before-ui-copy-20261021`. No hubo migraciones, cambios de reglas de negocio ni nuevas dependencias. Esta revisión tampoco incluye Safari.
