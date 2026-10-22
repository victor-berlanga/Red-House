# Investigación de auditoría, hallazgos y validación de formularios

Incremento del 21 de octubre de 2026. [Resultados locales y reproducción](../evidencias/auditoria-formularios/RESULTADOS.md). [Publicación y verificación en GCP](../evidencias/gcp/auditoria-formularios/RESULTADOS.md). [Estado del proyecto](../../PROJECT_STATUS.md).

## Investigación de operaciones

La bitácora muestra acción descriptiva, responsable, institución afectada, recurso o folio, ejecución y resultado. La fecha de centralización permanece en el detalle. Una fecha histórica ausente o inválida se muestra como desconocida; no se reemplaza por la recepción.

Las categorías iniciales son operaciones de negocio, decisiones/autorizaciones e incidentes de seguridad. Sesiones y consultas se conservan y pueden activarse. Los eventos técnicos tienen un control y un acceso separado. Un código desconocido se identifica expresamente. «Registrado» significa que existe el evento, no que una decisión clínica haya sido correcta. La clasificación está en `redhouse/audit_catalog.py`.

Filtros combinables: desde/hasta (instantes inclusivos), categorías, acción, responsable (cuenta registrada o ID), institución afectada, recurso/folio, resultado y correlación. El portal interpreta las fechas en la zona horaria seleccionada y envía instantes con desplazamiento. Los filtros se conservan en paginación, exportación y regreso desde el detalle. La región procede de la identidad autenticada; no se acepta una región elegida por el cliente.

Los eventos nuevos conservan una instantánea minimizada de cuenta, rol e ID institucional del responsable, folio disponible, motivo validado, nombres de campos corregidos y determinados cambios operativos. No se copian expedientes ni valores clínicos modificados. El nombre de la institución afectada procede del catálogo actual; el detalle distingue la referencia institucional histórica. Los eventos anteriores no se reescriben ni se completan con el perfil actual de la persona.

La secuencia relacionada utiliza referencias registradas y correlación. Ordena por ejecución y desempata por centralización/ID. Su límite es **500 eventos y cuatro niveles de relación**, indicado al alcanzarlo. No deduce vínculos clínicos ausentes. Los accesos generan `READ`, oculto inicialmente; recibir o proyectar un evento no genera otra lectura.

## Contratos y exportación

Las rutas públicas siguen en `/api/v1`, con JWT, sesión/permisos Redis y autorización por recurso. Admiten JSON/XML; XSD y esquemas de respuesta están en `ms_auditoria/contracts` y Swagger.

| Operación | Ruta después de `/api/v1` |
| --- | --- |
| Opciones y límites | `GET /event-options` |
| Listado y contador | `GET /events` |
| Todos los resultados filtrados | `GET /events/export` |
| Detalle y secuencia | `GET /events/{id}`, `GET /events/{id}/related` |
| Listar o registrar hallazgos | `GET /findings`, `POST /findings` |
| Detalle e historial | `GET /findings/{id}` |
| Registrar atención/verificación | `POST /findings/{id}/actions` |
| Coordinadores asignables | Identidad: `GET /audit-assignees` |

`categories` admite códigos separados por coma (`BUSINESS,DECISION,SECURITY,SESSION,READ,TECHNICAL`), `ALL` o `NONE`. Omitirlo conserva las tres categorías iniciales. Otros parámetros: `from`, `to`, `action`, `actor`, `institution_id`, `resource`, `result`, `correlation_id`, `q`. Las fechas requieren zona horaria. `page_size` llega hasta 100; el portal usa 20.

Listado, contador y exportación comparten filtros. Cada respuesta obtiene filas y total en una transacción de lectura con instantánea consistente. **Exportar página** descarga la página visible. **Exportar resultados filtrados** permite hasta **5.000 eventos**; al superar el límite responde 422 y pide reducir filtros, sin entregar un archivo truncado. Solicitudes hechas en momentos distintos pueden incluir nuevas operaciones centralizadas entre ellas. El CSV usa UTF-8 y neutraliza fórmulas, incluidas las precedidas por espacios.

## Hallazgos y permisos

Un hallazgo contiene descripción de 6–1000 caracteres, prioridad, responsable activo, evidencia o referencia documental y al menos un evento o recurso de la bitácora autorizada. Admite hasta 20 eventos. Las prioridades baja, media, alta y crítica sirven para seguimiento; no representan urgencia clínica. El responsable es un coordinador activo de la misma región.

| Perfil | Estado inicial | Operación | Estado resultante |
| --- | --- | --- | --- |
| Auditor regional | — | Registrar | Abierto |
| Coordinador asignado | Abierto | Iniciar con plan/acción | En atención |
| Coordinador asignado | En atención | Registrar avance | En atención |
| Coordinador asignado | En atención | Enviar acción y evidencia | Pendiente de verificación |
| Auditor regional | Pendiente de verificación | Devolver con motivo | En atención |
| Auditor regional | Pendiente de verificación | Verificar con evidencia y motivo | Cerrado |

Cada transición requiere motivo de 6–1000 caracteres, confirmación humana, versión vigente e idempotencia. La evidencia es obligatoria al solicitar verificación y al cerrar. El coordinador solo consulta y atiende lo asignado a su cuenta; el auditor consulta su región. Otros perfiles no acceden. Recibir un hallazgo no concede al coordinador acceso a eventos originales.

Historial y vínculos son inmutables mediante permisos y triggers PostgreSQL. La atención no modifica eventos originales, inventario, evaluaciones ni decisiones clínicas. Se emiten avisos dirigidos al coordinador y, al solicitar verificación, al auditor creador. Cerrado es final en este incremento. No hay reasignación ni adjuntos nuevos para hallazgos: la evidencia es texto o referencia documental, cuya autenticidad se comprueba mediante revisión humana. Las evidencias de traslado mantienen su flujo GCS.

## Formularios y errores

Los modelos del servidor siguen siendo la autoridad. `validation.py` y `codec.py` producen detalles seguros con `field`, `code`, `message` y límites numéricos cuando aplican. Se conservan el envoltorio de error, sus campos existentes y XML v1; la ampliación es aditiva. No se devuelven valores recibidos, credenciales, excepciones ni contexto interno de Pydantic.

El portal transporta esos detalles y los asocia con etiquetas visibles. Los campos muestran ayuda permanente, obligatoriedad y límites HTML. Después de enviar, el resumen recibe foco y ofrece enlaces con teclado. Los campos afectados tienen texto, borde, `aria-invalid` y `aria-describedby`. JavaScript coordina una sola presentación con las restricciones nativas; el servidor también valida sin JavaScript.

Se conservan valores, selecciones paginadas/múltiples, confirmaciones e idempotencia tras el rechazo. Las contraseñas no se rellenan de nuevo. Un archivo debe seleccionarse nuevamente, con aviso explícito. Una carga corregida usa una clave derivada del contenido y de la clave del formulario; repetir el mismo contenido conserva idempotencia. Una carga sin confirmar permite verificar la evidencia pendiente.

| Dato | Regla conservada |
| --- | --- |
| Restricciones, antecedentes, requerimientos, estudios y motivos | 6–1000 caracteres; se respetan opcionales |
| Folio | 6–30 caracteres ASCII: letras, dígitos, `_`, `-`; sin espacios ni acentos |
| Nombres y textos breves | Hasta 200 caracteres |
| Campaña | Cupo 1–10000; fin posterior al inicio y al momento actual |
| Edición de campaña | Versión desactualizada y cupo inferior a citas reservadas son conflictos distintos; se informa el mínimo disponible |
| Solicitud | Cantidad 1–100; urgencia capturada 1–3, sin añadir interpretaciones clínicas |
| Ruta | 0–20000 km; 0–10080 minutos enteros; fuente 6–1000 caracteres |
| Ubicación | Latitud −90…90; longitud −180…180; periodo y perfil autorizados |
| Cuenta y contraseña | Cuenta 3–80; contraseña nueva 12–128 |
| Capacidad de catálogo | 0–100000 |
| Consentimiento | Referencia y fecha juntas; fecha no futura |
| Inventario y traslado | Errores separados de componente, caducidad, recolección, salida, llegada y duración |
| Evidencia de traslado | JPEG/PNG/PDF hasta 10 MiB; validación de contenido conservada con causa y corrección específicas |

El portal trata espacios sin contenido en opcionales como ausencia. La API conserva su contrato estricto: el consumidor envía `null` u omite el opcional, en vez de enviar una cadena en blanco. Los rechazos de permisos, estados concurrentes y dependencias no se presentan como errores de longitud. La autenticación no revela si una cuenta existe.

Los límites se generan como archivo estático, para no requerir API disponibles al pintar ayuda:

```sh
apps/services/.venv/bin/python scripts/export_form_constraints.py
apps/services/.venv/bin/python scripts/export_form_constraints.py --check
apps/services/.venv/bin/python apps/services/scripts/document.py --contracts-only
```

## Actualización conservando datos

El esquema global pasa de **6 a 7** y Auditoría de **2 a 3**. Se agregan `audit_findings`, `audit_finding_links`, `audit_finding_actions`, vistas, permisos, triggers e índices. El dominio queda en **74 tablas**; con `web_runtime.session_revocations`, son **75**. No se actualizan filas históricas. `data/database/schema.sql` sirve para bases nuevas; no reemplaza una instalación existente.

En una instalación local, con aplicaciones detenidas durante el mantenimiento:

```sh
apps/services/.venv/bin/python apps/services/scripts/upgrade.py --directory /ruta/privada/del/entorno
```

Valida versión, genera respaldo PostgreSQL privado y aplica el incremento en una transacción. Repetirlo verifica la versión sin repetir la migración.

En Docker, conservar configuración privada, detener aplicaciones durante la actualización y mantener PostgreSQL disponible:

```sh
python3 deployment/migrate_audit.py --directory /ruta/privada/de/compose
```

Exige marcador de instalación, respalda base y roles y aplica la misma migración bajo el propietario del esquema. Después deben reconstruirse portal y servicios que incluyen la biblioteca compartida, arrancar según la [guía de despliegue](../../deployment/README.md) y comprobar salud, login, bitácora, exportación y hallazgos. Bootstrap rechaza una base anterior sin migrar; no la reinicializa ni rota secretos para resolver la incompatibilidad.

Se conservan ambos modos del portal, paquetes independientes, JWT, Redis, CSRF y contratos versionados. La herramienta Docker es un procedimiento de operación: consultar la evidencia para distinguir pruebas locales de una actualización aplicada en GCP.
