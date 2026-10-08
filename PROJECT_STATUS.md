# Estado vigente de Red House

Actualizado: **8 de octubre de 2026**. Leer junto con [AGENTS.md](AGENTS.md). Este archivo distingue implementación comprobada y trabajo pendiente; no declara terminado el producto semestral. [Bitácora y estados anteriores](documentation/historial/ESTADO_HASTA_2026_10_07.md).

## Alcance y decisiones vigentes

- Web Flask/Jinja2 integrada por HTTP a diez microservicios y Monitoreo. Modo histórico `BACKEND_MODE=local` conservado de forma explícita, sin fallback ni doble escritura. Su base anterior no recibió cambios de negocio en este incremento.
- Servicios en `apps/services`: Identidad/Acceso, Donantes, Receptores/Solicitudes, Inventario, Compatibilidad, Priorización/Geografía, Transporte, Custodia, Alertas, Auditoría y Monitoreo.
- Stack vigente: Python/Flask, PostgreSQL, Redis, MongoDB, JWT, Swagger/OpenAPI, JSON/XML. Docker, móvil, escritorio y GCP siguen en fase posterior por instrucción expresa del usuario. No se añadieron frameworks, brokers ni proveedores de nube.
- Cada propietario conserva consultas, entradas, DTO de salida, migraciones y base propia. Biblioteca `redhouse` limitada a mecanismos técnicos; entregas con una copia fija de esa biblioteca y un solo dominio. API v1 compatible con cuerpos anteriores; cambios incompatibles futuros requieren versión y transición de consumidores.
- Sangre y órganos separados. Reglas RBC-DEMO/ORGAN-DEMO y matching operativo explicable; interpretación HLA y decisiones clínicas corresponden a personal autorizado. No presentar una recepción como transfusión o trasplante realizado.

## Incremento de revisión implementado

| Área | Criterio de aceptación y evidencia |
| --- | --- |
| Seguridad y consistencia | Caducidad bloquea avance/aceptación; versiones Redis recuperables después de rollback SQL; límites por actor; motivos inmutables y autorizados. `test_review_regressions.py` y suite de seguridad/flujos. |
| JSON/XML | Evidencia anidada opcional equivalente, XSD de entrada, XSD estructural de respuesta + validación semántica del DTO publicado. `test_review_unit.py`, pruebas de contratos. |
| Web | Rutas separadas, búsquedas paginadas, edición versionada, catálogos institucionales, primer administrador, estados coherentes, logout local y revocación remota diferida. Pruebas web y mantenimiento. |
| Aislamiento | Once paquetes ejecutables sin dominios vecinos; actualización de Donantes conserva otros diez servicios, sus workers y web. [Comprobación](apps/services/docs/evidence/review-independence.json). |
| Migraciones y operación | Respaldo previo; once restauraciones desechables, migración doble sin pérdida de registros; salud de worker/outbox/bucket. [Restauración](apps/services/docs/evidence/review-backup.json). |
| Organización | Migraciones y DTO propios, eliminación de DDL duplicado, estado vigente separado del histórico, TXT y contratos regenerados, Ruff y CI definida sin Docker. |

Detalles de cambios, restricciones de edición y correspondencia con la revisión: [matriz de revisión](apps/services/docs/REVISION_2026_10_08.md). Arquitectura: [decisiones](apps/services/docs/ARQUITECTURA.md). Resultados completos: [VALIDACION](apps/services/docs/VALIDACION.md).

## Pruebas verificadas de este corte

- Suite completa: **113 aprobadas**, cero fallos/errores/omisiones, 354.41 s. [JUnit](apps/services/docs/evidence/review-junit.xml). Una ejecución previa tuvo un 503 de notificaciones (112 aprobadas); no se reprodujo en las 19 pruebas web aisladas ni en la repetición completa. Se incorporó diagnóstico técnico sin credenciales; no se atribuye una causa no demostrada.
- Once paquetes por separado publican OpenAPI sin otros dominios instalados. Migración v1→actual repetible y datos preservados; respaldo de las once bases restaurado y actualizado en copias desechables.
- DEMO: once servicios y web disponibles; 18 cadenas verificadas, disponibilidad con HIT, límites normales de 180/minuto y ocho hashes/roles históricos conservados. [Informe](apps/services/docs/evidence/review-demo.json).
- Ajustes finales: **51 pruebas** de consultas/historial/web y **50 pruebas** de contratos/seguridad/paquetes aprobadas; son subconjuntos repetidos, no casos adicionales. Monolito histórico: **121 aprobadas y 8 omitidas**. Chrome: **33 páginas**, búsqueda HTTP y cero errores JavaScript/fallos estáticos/desbordamiento del documento. [Evidencias y duraciones](apps/services/docs/VALIDACION.md).
- CI disponible en `.github/workflows/services.yml`; no se ha ejecutado en GitHub. Linux/Windows nativos y GCS real no quedan certificados por pruebas locales de macOS ni por mocks.

## Matriz documental de roles y cambios web

- [Excel de roles y permisos](documentation/excel/Matriz_Roles_Permisos_Red_House.xlsx), corte 08/10/2026: siete perfiles, 107 contratos públicos de API, condiciones por institución/estado, navegación y 20 cambios del portal. Describe el modo integrado; distingue permisos de API, disponibilidad en la web y funcionalidades pendientes.
- Criterio y evidencia: archivo XLSX reabierto y validado, siete hojas con filtros y paneles inmovilizados; permisos contrastados con contratos y condiciones del código, enlaces a fuentes comprobados. Las transiciones de traslado se desglosan por estado; ningún rol recibe borrado físico de negocio. Revisión documental sin nuevas pruebas de autenticación ni cambios al código, datos o procesos.

## Entorno actual

Portal: http://127.0.0.1:5050. [URLs Swagger y operación](apps/services/docs/ENTORNO_LOCAL_ACTUAL.md).

Datos y credenciales en **`.local/demo`** (privado, ignorado por Git), trasladados con procesos detenidos desde `/private/tmp/red-house-integrated-20261007`, cuyo contenido se conserva como respaldo. No iniciar ambos directorios a la vez: comparten puertos y representan copias de la misma DEMO. El `.env` web apunta al nuevo `web-client.json`; no contiene credenciales versionadas.

DEMO Nuevo León: seis instituciones, 108 donantes, 36 donaciones, 12 campañas, 36 citas, 72 receptores/solicitudes, 252 recursos y 18 traslados. Se añadieron por API 54 registros administrativos ficticios de sedes, contactos, horarios, capacidad declarada y ubicaciones. [Carga de catálogos](apps/services/docs/evidence/review-catalogues.json). No se reescribieron estados clínicos ni expedientes existentes.

Desde la raíz:

```sh
apps/services/.venv/bin/python apps/services/scripts/integrated.py start --directory .local/demo
apps/services/.venv/bin/python apps/services/scripts/integrated.py status --directory .local/demo
apps/services/.venv/bin/python apps/services/scripts/integrated.py stop --directory .local/demo
apps/services/.venv/bin/python apps/services/scripts/local.py restart-service --directory .local/demo --service donantes
apps/services/.venv/bin/python apps/services/scripts/integrated.py restart-web --directory .local/demo
```

La independencia de procesos permite actualizar servicios individuales. Una operación que dependa del servicio detenido puede devolver 503; no se garantiza continuidad ante contratos rotos ni caída de PostgreSQL/Redis compartidos. La DEMO no constituye alta disponibilidad.

## Pendientes explícitos

- Reglas clínicas/normativas validadas, HLA clínico, elegibilidad y prioridad oficial; aprobación institucional y políticas de retención.
- Agenda clínica por sede/horario, restablecimiento de contraseña y administración institucional definitiva, email/push.
- GCS con bucket real, archivos grandes, firma/descarga y pruebas de caída en nube.
- Android, escritorio XML, Docker, GCP, HTTPS y operación productiva; no seleccionar tecnologías cliente sin decisión registrada.
- Estrés/saturación y escalabilidad institucional, redundancia, recuperación productiva y ejecución remota de CI. Mediciones breves locales no sustituyen esos resultados.
- Actualizar Word/PDF semestral cuando se consolide el siguiente entregable: esos archivos y capturas antiguas conservan su fecha histórica; no representan automáticamente los servicios 0.2.0.

## Regla de mantenimiento

Tras cambios materiales, actualizar este estado, criterios de aceptación, evidencia, decisiones y pendientes. No confundir un contrato documentado con funcionalidad probada. Mantener secretos y datos operativos fuera de Git.

## Entrega en Git

- Rama de entrega `Microservicios`, creada desde `main` (`44eeaf9`). El usuario autorizó guardar el trabajo actual y publicar esta rama en GitHub; no se integra a `main` ni se despliega la aplicación.
- Revisión previa al commit: `.local`, entornos virtuales y `.env` reales excluidos; ejemplos con marcadores sin credenciales operativas. Ruff sin errores y formato verificado en 132 archivos. Las pruebas funcionales conservan la evidencia del corte anterior; no se repitieron por esta operación de Git.
