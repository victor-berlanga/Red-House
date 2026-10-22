# Auditoría y formularios publicados en GCP

Fecha local: **21 de octubre de 2026, America/Monterrey**. Destino: **https://34.18.186.116**, VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`. Actualización solicitada después de las [176 pruebas locales](../../auditoria-formularios/RESULTADOS.md).

## Resultado

Auditoría investigable, exportación filtrada, seguimiento de hallazgos y validación de formularios disponibles en el portal publicado. **27 contenedores saludables, once readiness HTTP 200 y 38 controles API aprobados**. Chrome completó cuatro grupos de recorridos, incluidos móvil y teclado, sin errores JavaScript.

| Criterio de aceptación | Evidencia comprobada |
| --- | --- |
| Actualizar sin perder datos | [Respaldo y despliegue](despliegue.json): PostgreSQL de 72 tablas y siete colecciones MongoDB restaurados con conteos/hashes idénticos; Redis restaurado con TTL vigente y permisos del portal conservados |
| Migrar de forma aditiva | Ensayo sobre la copia restaurada y aplicación global 6→7 / Auditoría 2→3; tres tablas nuevas; 70 tablas ajenas al control de versiones idénticas; segunda ejecución sin cambios |
| Publicar código correcto | Doce imágenes reconstruidas; 2.389 comprobaciones de archivos dentro de las 23 instancias de aplicación, con cero diferencias |
| Conservar el negocio y la auditoría anterior | [Comprobación final](final.json): 60 tablas idénticas después de las pruebas y 7.928 eventos previos con el mismo conteo y hash |
| Corregir los cuatro errores originales del formulario | [Chrome](navegador.json): HTTP 422 con campo y mensaje concreto para restricciones, antecedentes y consentimiento; valores y confirmación conservados |
| Investigar y exportar | Filtro de recurso, detalle y regreso al listado; [CSV](auditoria.csv) de una fila coincidente con el [total API](exportacion.json) |
| Segregar atención y verificación | Un hallazgo ficticio pasa por abierto, en atención, pendiente y cerrado; cuatro acciones, un vínculo, versión 4 y evidencia obligatoria |
| Mantener contratos y permisos | [38 controles API](api.json): consultas JSON/XML de once servicios; rechazos 401/403/404; errores seguros 422; avisos dirigidos a coordinador y auditor |
| Mantener la operación | [Estado final](final.json): 27 contenedores saludables, once readiness 200, `redhouse` y temporizador de renovación TLS activos |
| Acceso público sin túneles | [Red pública](red-publica.json): login y once readiness por HTTPS en 200, TLS verificado y redirección HTTP 308 |

## Respaldo y conservación

Respaldo privado en `/opt/redhouse/.local/compose/backups/20261021T215850Z`. Incluye PostgreSQL, roles, MongoDB, Redis y configuración; los tamaños y SHA-256 están en `despliegue.json`, sin publicar el contenido privado. Código anterior, imágenes etiquetadas y configuración adicional se conservaron en la VM. Los tres contenedores de restauración temporal y sus volúmenes se retiraron después del ensayo.

La restauración se hizo en contenedores aislados. La base pública recibió únicamente la migración aditiva; no se reemplazó con el respaldo ni con el esquema de instalación nueva. Permanecen 74 tablas de dominio y `web_runtime.session_revocations`, 75 en total. Credenciales y configuración de GCS/HTTPS se conservaron.

Después de las pruebas, las diferencias esperadas corresponden a versiones, sesiones, notificaciones y tablas técnicas de eventos, idempotencia, entrega y salud. Donantes, dictámenes, donaciones, citas, usuarios, catálogos, recursos, solicitudes, evaluaciones, traslados, custodia y archivos mantienen sus conteos/hashes. No se creó ningún donante durante esta verificación.

Se conserva el hallazgo ficticio `64a78c6b-7b39-447c-a12b-9d482835f1b7`, cerrado, vinculado a un evento académico existente. Su descripción identifica la comprobación técnica del despliegue; no representa una incidencia clínica. El rol operativo no tiene UPDATE/DELETE sobre vínculos o historial.

## Incidencia de publicación resuelta

El empaquetado temporal creó directorios de código con modo 0700. El usuario UID 10001 de Auditoría no pudo leer las migraciones y readiness bloqueó el arranque. Se corrigieron los directorios a 0755, se reconstruyeron las doce imágenes y se validó la lectura/hash con el usuario habitual dentro de todos los contenedores de aplicación. No se relajaron permisos de los secretos ni se modificó el contenido de negocio para resolverlo.

El mantenimiento registrado abarcó **21:58:50–23:37:06 UTC** del 21 de octubre (15:58:50–17:37:06 en Monterrey). El primer arranque fallido queda identificado en `despliegue.json`; el estado final se verificó después de la corrección. La clave SSH temporal de administración se retiró al terminar.

## Navegador y reproducción

[Errores en móvil](errores-movil.png) · [Errores del servidor](errores-servidor.png) · [Auditoría filtrada](auditoria-filtrada.png) · [Hallazgo cerrado](hallazgo-cerrado.png).

La comprobación de Chrome usa [verify_audit_forms.cjs](../../../../deployment/gcp/verify_audit_forms.cjs), con credenciales por stdin, sin registrarlas. Requiere Chrome y Playwright; su ejecución escribe un hallazgo ficticio nuevo y queda reservada para una verificación autorizada. El [verificador API](../../../../deployment/gcp/verify_audit_forms.py) se ejecuta dentro de la VM y toma `--finding`, `--resource` y `--output`. Sus POST de donantes son deliberadamente inválidos; cierra las sesiones que abre.

Esta publicación no repitió la suite local completa de 176 casos, pruebas de carga ni carga/descarga de objetos GCS. Sí comprobó readiness de almacenamiento y preservó los archivos y sus referencias existentes. No se certifica redundancia entre máquinas ni operación clínica. La evidencia de hallazgos sigue siendo texto/referencia; reasignación y adjuntos nuevos permanecen fuera de este incremento.
