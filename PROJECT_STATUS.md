# Estado vigente de Red House

Actualizado: **8 de octubre de 2026**. Leer junto con [AGENTS.md](AGENTS.md). Este archivo distingue implementación comprobada y trabajo pendiente; no declara terminado el producto semestral. [Bitácora y estados anteriores](documentation/historial/ESTADO_HASTA_2026_10_07.md).

## Alcance y decisiones vigentes

- Web Flask/Jinja2 integrada por HTTP a diez microservicios y Monitoreo. Modo histórico `BACKEND_MODE=local` conservado de forma explícita, sin fallback ni doble escritura. Su base anterior no recibió cambios de negocio en este incremento.
- Servicios en `apps/services`: Identidad/Acceso, Donantes, Receptores/Solicitudes, Inventario, Compatibilidad, Priorización/Geografía, Transporte, Custodia, Alertas, Auditoría y Monitoreo.
- Stack vigente: Python/Flask, PostgreSQL, Redis, MongoDB, JWT, Swagger/OpenAPI, JSON/XML. Docker, móvil, escritorio y GCP siguen en fase posterior por instrucción expresa del usuario. No se añadieron frameworks, brokers ni proveedores de nube.
- Cada propietario conserva consultas, entradas, DTO de salida, migraciones y base propia. Biblioteca `redhouse` limitada a mecanismos técnicos; entregas con una copia fija de esa biblioteca y un solo dominio. API v1 compatible con cuerpos anteriores; cambios incompatibles futuros requieren versión y transición de consumidores.
- Sangre y órganos separados. Reglas RBC-DEMO/ORGAN-DEMO y matching operativo explicable; interpretación HLA y decisiones clínicas corresponden a personal autorizado. No presentar una recepción como transfusión o trasplante realizado.

## Corrección de controles y horario — 08/10/2026

- El botón **Filtrar** solo queda como alternativa si no se activa JavaScript; los listados sin filtros conservan su acción útil de actualizar. Se retiraron el pie «Red House · Red regional / Entorno de pruebas» y contadores visuales repetidos. El carácter de los datos continúa documentado.
- Paginación con **Anterior**, **Siguiente**, números separados y página actual; controles arriba y abajo, límites deshabilitados y conservación de filtros. Una página que dejó de existir muestra la última disponible.
- Horario junto al encabezado: seleccionar Monterrey/UTC guarda la preferencia con CSRF y actualiza fechas, fragmentos y modales sin navegación del documento. Las fechas de formularios abiertos se convierten conservando el instante; el resto del borrador permanece intacto. Ante error se conserva la presentación anterior y se ofrece reintentar. Sin JavaScript permanece el envío convencional.
- Evidencia: [14 pruebas HTTP](apps/services/docs/evidence/ui-controls-junit.xml), incluidas las vistas de siete perfiles, paginación, conversión/persistencia de horario y CSRF; [5 regresiones históricas](apps/services/docs/evidence/ui-controls-legacy.xml), todas aprobadas. [Navegador](apps/services/docs/evidence/ui-controls/report.json): navegación real, filtros, zona, borradores, 503, móvil y alternativa sin JavaScript. Detalles en [documentación UI](apps/services/docs/UI_UX_JINJA_2026_10_08.md#corrección-de-controles-tras-la-revisión-del-usuario).

## Incremento UI/UX y Jinja — 08/10/2026

- Implementado en `Microservicios`: ojo de consulta y lápiz de edición separados; acciones de estado explícitas, tablas compactas/adaptables, detalle por secciones y trazabilidad desplegable, panel con tareas por perfil. Nombres sin sufijo repetido; límites clínicos conservados. El pie de entorno se retiró en la corrección posterior solicitada por el usuario.
- Filtros GET con fragmentos Jinja, espera de 300 ms, cancelación de consultas anteriores, foco e historial; filtros/página conservados al volver desde edición. Actualización opcional cada 30 s en listados operativos, sin WebSockets. No se agregó Docker ni otro framework.
- Caché autorizada propiedad de Inventario (listado/resumen 10 s, disponibilidad 15 s) e Identidad (catálogos 30 s), con invalidación mediante revisión SQL en el mismo commit. Sesión/JWT/permisos se validan antes del HIT. Receptores expone `can_edit` opcional; el backend sigue comprobando reglas al guardar.
- Criterios, arquitectura, límites, comandos y capturas: [UI/UX y Jinja](apps/services/docs/UI_UX_JINJA_2026_10_08.md). [Chrome](apps/services/docs/evidence/ui/report.json): **36 páginas**, siete perfiles, filtros sin navegación del documento, modal de consulta, regreso desde edición, error/reintento, actualización periódica y móvil de 390 px; cero errores JavaScript/estáticos/desbordamientos.
- [Suite general](apps/services/docs/evidence/ui-cache-junit.xml): **117 aprobadas de 118** en 424.20 s. Único fallo: la prueba de migración esperaba versiones 1–3, pero se añadió correctamente la 4. Se actualizó la aserción y comprobó revisión inicial; [repetición focalizada](apps/services/docs/evidence/ui-final-targeted.xml): **9 aprobadas**, incluida esa migración, en 62.82 s. No quedan fallos de esa ejecución sin resolver; no se presenta como una única ejecución de 118 aprobadas.
- [Monolito histórico](apps/services/docs/evidence/ui-legacy-junit.xml): **121 aprobadas y 8 omitidas**, 305.03 s. El fixture de pruebas web utiliza ahora el timeout normal de 8 s, tras timeouts intermitentes con 2 s; la configuración productiva no cambió.
- Entorno existente `.local/demo` preservado: respaldos y migraciones aditivas en Inventario e Identidad; reinicio individual de esos servicios, Receptores y web. Once servicios y portal disponibles. No se borraron ni recargaron expedientes ni se modificó la base histórica de negocio del monolito.
- Rendimiento medido: 30 pares por endpoint, caché sin reducción de latencia demostrada en este volumen (Disponibilidad 108.795 vs 100.581 ms; resumen 87.782 vs 85.993 ms). Fragmento Jinja de 20 resultados: 17 837 vs 28 965 bytes, **38.4 % menos HTML**; no equivale a una mejora de tiempo de respuesta garantizada. [Mediciones](apps/services/docs/UI_UX_JINJA_2026_10_08.md#medición-local-y-límites-del-rendimiento).
- Pendiente de esta entrega: revisión visual del usuario. La consulta periódica y los TTL no equivalen a actualización instantánea; las mediciones locales no certifican escalabilidad. Los Word/PDF y la matriz Excel anteriores mantienen su corte histórico; los permisos de roles no se ampliaron.

## Incremento de revisión anterior

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
