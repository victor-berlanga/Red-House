# Datos de demostración en GCP — 21 de octubre de 2026

Se amplió la base de la VM `red-house`, en **https://34.18.186.116**, con registros ficticios. Los datos anteriores se conservaron. La carga inicial utilizó las API existentes con JWT, permisos institucionales, validaciones, auditoría y notificaciones; sus consultas SQL administrativas solo comprobaron resultados. Posteriormente se retiraron las etiquetas repetitivas de los textos actuales por solicitud del usuario, mediante la corrección administrativa documentada al final.

## Resultado visible

| Información | Antes | Después |
| --- | ---: | ---: |
| Donantes | 0 | 68 |
| Dictámenes de donantes | 0 | 64 |
| Campañas | 0 | 60 |
| Citas | 0 | 118 |
| Donaciones | 0 | 60 |
| Recursos de inventario | 20 | 140 |
| Receptores | 18 | 138 |
| Solicitudes | 18 | 138 |
| Evaluaciones de compatibilidad | 18 | 78 |
| Rankings | 15 | 75 |
| Propuestas de asignación | 0 | 30 |
| Reservas y traslados | 18 de cada uno | 48 de cada uno |
| Archivos privados verificados | 3 | 33 |
| Puntos de seguimiento de traslados | 0 | 50 |
| Instituciones | 2 | 30 |
| Usuarios | 14 | 30 |
| Rutas | 1 | 32 |
| Entradas de catálogos | 0 | 300 |

Cada hospital original tiene **34 donantes, 30 campañas, 59 citas y 30 donaciones**. Se agregaron 30 recursos de sangre y 30 de órganos por hospital, con receptores y solicitudes relacionados. Los traslados cambian la institución actual de algunos recursos; los totales de inventario incluyen datos anteriores.

Los cinco catálogos —sedes, contactos, horarios, capacidades y ubicaciones— tienen 30 entradas por hospital. Los 28 hospitales adicionales sirven como instituciones de la red y destinos de rutas; la actividad detallada se concentra en los dos hospitales originales.

Los **30 traslados nuevos** quedaron distribuidos en 10 recibidos, 10 en tránsito, 5 recolectados y 5 planeados. Cada uno tiene un PNG ficticio pequeño en GCS, verificado por contenido, tamaño y hash. Las revisiones y confirmaciones son ejemplos académicos, sin validez clínica; se utilizaron las reglas existentes sin modificarlas.

## Cómo verlo en el portal

- Con `operator1` u `operator2`: Donantes, Campañas, Inscripciones, Donaciones e Inventario. Los listados tienen 20 filas por página; usar **Siguiente**.
- Con `medical1` o `medical2`: Receptores y Solicitudes; hay registros de sangre y órganos.
- Con `coordinator1` o `coordinator2`: Rutas, Traslados y custodia.
- Con `donor1` o `donor2`: un expediente propio y 30 citas por cuenta, además de las 30 campañas de su institución. El aislamiento por usuario es intencional.
- Con `admin1` o `admin2`: los cinco catálogos de su institución.

Las credenciales originales permanecen vigentes. Las 16 cuentas adicionales de donante son ahora `donor_1_01` a `donor_1_08` y `donor_2_01` a `donor_2_08`, con la contraseña del entorno de demostración conservada en el registro privado de la VM. El cambio de nombre no cambió sus contraseñas. No se publican contraseñas en estos archivos.

[Captura de donantes](donantes.png) · [Captura de campañas](campanas.png).

## Alcance del mínimo de 30

**38 de las 72 tablas físicas contienen al menos 30 filas**, incluidas todas las tablas operativas de negocio utilizadas por los contratos actuales. Las otras 34 son 27 tablas heredadas sin uso actual y 7 catálogos cerrados o tablas técnicas. No se crearon perfiles, versiones de esquema, intentos fallidos ni revocaciones ficticias para alcanzar una cuota.

Por ejemplo, `role` conserva sus siete perfiles y `service_worker_health` un registro por propietario de servicio. Los catálogos de la interfaz usan `catalogue_entry`; no escriben en las antiguas `site` o `storage_location`. El inventario actual usa `resource`, sin duplicarlo en `blood_unit` ni `organ_offer`.

[Conteo y explicación de las 72 tablas](TABLAS.md) · [Correspondencia del esquema vigente](../../../markdowns/Esquema_compartido.md).

## Comprobaciones realizadas

| Comprobación | Resultado |
| --- | --- |
| Carga autenticada y reanudable | 1 755 operaciones de negocio completadas |
| Cantidades por tabla y por institución | [counts.json](counts.json), todos los mínimos operativos aprobados |
| Navegador público | [browser.json](browser.json): 34 páginas, cuatro perfiles por hospital, totales y paginación correctos, cero errores JavaScript o solicitudes a localhost |
| Custodia y MongoDB | [integrity.json](integrity.json): los 30 traslados nuevos coinciden en estado y secuencia; hashes de las 30 cadenas comprobados |
| Archivos | 30 nuevos verificados; descarga de una muestra de sangre y otra de órganos con hash correcto y acceso anónimo rechazado |
| Integridad referencial | 139 claves foráneas presentes; cero restricciones sin validar |
| Entregas asíncronas | Cero entregas pendientes con más de 30 segundos al comprobar |
| Disponibilidad | 27 contenedores saludables y once readiness HTTP 200 |
| Repetición de la carga | [idempotence.json](idempotence.json): 64 tablas comparadas sin cambios de cantidad; continúan las mismas 1 755 operaciones, sin duplicados |

MongoDB conservaba 48 proyecciones de traslado, 263 eventos de Transporte, 213 de Custodia, 5 860 de Auditoría y 12 159 de Monitoreo al verificar. Los eventos, sesiones y sondeos continúan aumentando con el uso; los JSON registran el momento concreto de cada comprobación. Redis participó en las sesiones, permisos y controles normales de las API; no se rellenaron claves temporales para simular una base permanente.

La primera ejecución se interrumpió por una conexión HTTP de autenticación. Se ajustó únicamente el cliente de carga para reconectar y autenticar nuevamente cuando una respuesta de renovación es incierta. Se reanudó desde el checkpoint; no se cambiaron los servicios ni sus límites. Una repetición completa posterior confirmó que no se duplican registros de negocio.

## Respaldo y reproducción

Antes de escribir se exportaron PostgreSQL y MongoDB a `/opt/redhouse/.local/compose/demo-20261021/backup-before/`, con manifiesto y hashes. El archivo PostgreSQL pudo listar su contenido con `pg_restore --list`. Son respaldos en línea; no se afirma una instantánea simultánea de ambos motores ni una restauración ensayada en esta carga. Redis no se respaldó durante este incremento.

La [guía de GCP](../../../../deployment/gcp/README.md#datos-para-la-demostración) explica cómo reanudar el mismo conjunto con [`populate_demo.py`](../../../../deployment/gcp/populate_demo.py) y conservar el checkpoint. [`verify_demo.cjs`](../../../../deployment/gcp/verify_demo.cjs) reproduce las comprobaciones del portal desde un navegador cliente. La carga y las bases se ejecutaron exclusivamente en GCP; no se iniciaron servidores ni bases locales.

Los registros tienen fechas de campaña y caducidad propias de esta demostración. Al pasar el tiempo, la aplicación puede ocultar campañas concluidas o excluir recursos caducados. Repetir la carga no cambia esas fechas. No se certifica operación clínica ni se reemplaza la evidencia de pruebas de otras entregas.

## Normalización posterior de etiquetas

El usuario solicitó retirar `DEMO` de los datos agregados. Se corrigieron **743 registros de ocho tablas**: nombres y folios de donantes/receptores, folios de inventario, títulos de campañas, nombres y textos de catálogos, instituciones, cuentas nuevas y fuentes descriptivas de rutas. También se retiraron las frases de presentación repetidas de los campos actuales del conjunto. Ejemplos: `Ana Sofía Treviño`, `Campaña H1 01 · Jornada solidaria` y folios `RH26-D-H1-001`. Los correos de contacto conservan el dominio reservado `.example`.

La corrección se limitó a los IDs del checkpoint original. Las APIs no permiten modificar expedientes con historia ni cambiar nombres de usuario; por ello se utilizó [`normalize_labels.py`](../../../../deployment/gcp/normalize_labels.py), una tarea administrativa con columnas de texto permitidas explícitamente. Antes se generó `/opt/redhouse/.local/compose/labels-20261021/before.dump` y se comprobó su listado. La transacción verificó cada fila antes y después, conservó los demás campos mediante hashes e incorporó nuevos eventos de auditoría. Los triggers existentes invalidaron las cachés de catálogos e inventario.

[labels.json](labels.json) registra las cantidades iguales antes/después, los 743 cambios y cero cambios pendientes en una segunda revisión. UUID, contraseñas, relaciones, versiones operativas, cantidades, fechas, grupos sanguíneos y estados permanecen iguales. Las versiones operativas se conservaron porque la limpieza de etiquetas no altera los criterios de las evaluaciones existentes. No se desactivaron restricciones ni se cambiaron las reglas de edición de las APIs.

Los eventos, dictámenes, instantáneas de evaluaciones, respuestas históricas de idempotencia y el checkpoint conservan su contenido original; pueden mostrar nombres anteriores dentro de ese contexto histórico. Las cadenas de custodia no se recalcularon. Una comprobación posterior confirmó las 30 cadenas y proyecciones de traslado, 27 contenedores saludables y once readiness 200. El generador usa los nombres actuales para nuevas entradas; conservar el checkpoint evita recrear las existentes.

Verificación posterior: [13 controles API](labels-api.json), incluidos accesos con cuentas renombradas y expedientes propios; [34 páginas del portal](browser.json), con totales y paginación conservados, sin etiquetas anteriores en los listados y cero errores JavaScript. Las capturas de donantes y campañas muestran los textos actuales. [Integridad posterior](labels-integrity.json): cadenas, seguimiento MongoDB, archivos y disponibilidad correctos. Los resultados anteriores de esta página conservan la fecha de la carga inicial.
