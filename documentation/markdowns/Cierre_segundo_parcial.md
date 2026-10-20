# Matriz de ejecución del segundo parcial

Inicio: 15/10/2026. Entrega: 22/10/2026. Fuente: enunciado externo y
`stuff/prompts/completar_segundo_parcial.md`. El árbol inicial estaba limpio.
Las pruebas del 14 y 15 de octubre son antecedentes, no resultados de este cambio.

| Requisito | Estado inicial comprobado | Cambio entregado | Dependencias | Criterio y evidencia final |
| --- | --- | --- | --- | --- |
| Continuidad web | Portal exclusivamente HTTP | Backend modular propio, reglas versionadas y workers autónomos | PostgreSQL compartido, Redis y módulos autorizados | **Aprobado**: sangre y órganos con las 22 API detenidas; [Docker final](../evidencias/segundo-parcial/docker-release/docker-results.json); donación/procesamiento en la regresión |
| Disponibilidad JSON/XML | Una instancia por API | Dos instancias de los once propietarios, incluida Identidad, más workers y DNS | Gateway y contratos compatibles | **Aprobado**: once réplicas A detenidas, flujo de órganos y consultas JSON/XML; actualización real de Inventario, 100 consultas 200 y altas persistidas |
| PostgreSQL compartido | Base `red_house` ya migrada | Se conservan 71 tablas, permisos por servicio y vistas `access_*` | Esquema versión 6 y credenciales separadas | **Aprobado**: regresión, catálogo físico de 145 índices y restauración completa; entorno habitual conservado |
| Docker | Sin Dockerfile/Compose en el inicio del incremento | Imágenes por propietario/web, redes, secretos, supervisión y volúmenes | Docker Compose y acceso a registro de imágenes | **Aprobado**: 27 contenedores saludables, continuidad, actualización y reinicio; [clon limpio](../evidencias/segundo-parcial/clean-clone.json) con ocho etapas, negocio real y bootstrap repetido |
| MongoDB | Eventos inmutables y pipelines de Monitoreo existentes | Proyección mutable de seguimiento, índices y reconstrucción | Roles documentales limitados y eventos SQL relacionados | **Aprobado**: versión, duplicados, desorden, reconstrucción, filtrado, pipelines e índice `IXSCAN`; [resultado](../evidencias/segundo-parcial/mongo-projection.json) |
| Redis | Sesiones, permisos y caché existentes | Participación común de monolito y réplicas, TTL y revocación conservados | ACL y claves por prefijo | **Aprobado**: login/rotación/revocación, límites, nonce, caché y rechazo durante caída en regresión; evidencia SQL/Redis por endpoint |
| GCS | Adaptador sin bucket ni interfaz completa | Flujo web privado, validación, estados y descarga firmada | Recursos/IAM autorizados y ADC impersonada | **Aprobado**: carga/descarga/hash, permiso público denegado, inválido, ausente, expirado y recuperación; [GCS real](../evidencias/segundo-parcial/gcs-real.json), navegador |
| Web y seguridad | Procesos existentes y resultados históricos | Integración autónoma, gestión de archivos y configuración privada corregida | Roles institucionales, JWT y Redis | **Aprobado**: 182 pruebas finales y 20 páginas de siete perfiles; Highcharts con datos comprobados, filtros/paginación y ancho 390 |
| JSON/XML/XSD e internas | Contratos versionados existentes | Contratos actualizados, ejemplos correctos/error, archivo/proyección y evidencia real | Validadores, firmas Ed25519 y JWT delegado | **Aprobado**: regresión, consultas Docker y [expediente HTTP](../evidencias/segundo-parcial/http/index.html); Swagger ejecutado |
| Evidencia por endpoint | Ejemplos sin expediente exhaustivo | Inventario dinámico, registros redactados, persistencia y capturas | Pruebas finales y visor local | **Aprobado**: 284/284 éxitos HTTP y capturas; 240 con error real; 44 GET de documentación fija con no aplicabilidad justificada; [cobertura](../evidencias/segundo-parcial/http/coverage.json) |
| Fallos y recuperación | Pruebas históricas | Nuevas comprobaciones de dependencias, instancia, monolito y actualización | Entornos aislados | **Aprobado**: nueve controles Docker y una prueba complementaria de salud para los once propietarios; incidentes conservados |
| Respaldo | Procedimiento sin ensayo integral de este despliegue | Exportación coordinada y restauración en tres contenedores nuevos | Aplicaciones pausadas, secretos privados y volúmenes nuevos | **Aprobado**: 71 tablas/15 122 filas SQL, 7 632 documentos MongoDB, usuarios/roles por hash y clave Redis con TTL; [comparación](../evidencias/segundo-parcial/backup-restore.json) |
| Documento técnico | Guías dispersas y revisión histórica | Informe, once fichas, diagramas, catálogo físico y trazabilidad | Código y resultados fechados | **Entregado**: [informe Word](../docx/Reporte_tecnico_segundo_parcial.docx) / [PDF](../pdf/Reporte_tecnico_segundo_parcial.pdf), [modelo físico](../segundo-parcial/Modelo_fisico.md), once fichas y figuras actuales |
| Presentación | Apuntes individuales | [Guion presencial y de video](../../stuff/presentacion/Guion_segundo_parcial.md), reparto por responsabilidad y demo reproducible | Participación y publicación reales del equipo | **Material preparado; requisito externo pendiente**: ensayo, presentación, grabación, publicación y enlace de YouTube |

## Decisión de continuidad

El monolito ejecuta dentro de su proceso los módulos de aplicación distribuidos
también en las imágenes de cada servicio. El adaptador WSGI conserva validación,
JWT, autorización Redis, firmas internas, transacciones e idempotencia. No inicia
servidores HTTP internos ni cambia de backend tras un error. Cada módulo usa
credenciales limitadas a sus vistas del esquema compartido. La entrega fija el
código con versión y manifiesto; actualizar una API no cambia el monolito en uso.

Los workers propios del monolito entregan el outbox mediante el mismo adaptador.
Los workers de las API usan enrutamiento HTTP. Comparten colas con bloqueo SQL y
consumidores idempotentes. No hay doble escritura de entidades ni copia de reglas.

| Fallo | Web modular | Clientes JSON/XML | Límite |
| --- | --- | --- | --- |
| Una instancia API o worker | Opera con módulos y workers propios | Enruta a instancia restante | Respuesta perdida tras escritura exige consultar operación/idempotencia |
| Todas las instancias de un propietario API | Opera mientras sus dependencias de datos estén disponibles | Operaciones dependientes fallan controladamente | No se afirma continuidad API sin autoridad disponible |
| Redis | Rechaza operaciones protegidas | Rechaza operaciones protegidas | No se omite autenticación |
| PostgreSQL | Operaciones transaccionales indisponibles | Operaciones transaccionales indisponibles | No hay réplica de infraestructura en este alcance |
| MongoDB | SQL conserva outbox; consulta documental degradada | Mismo comportamiento | Recuperación y deduplicación posterior |
| GCS | Operaciones sin archivos continúan; archivo pendiente/error | Mismo comportamiento | No se declara verificado un objeto no comprobado |

## Recursos externos autorizados

Proyecto `sistemas-integracion-01`; bucket privado
`red-house-evidencias-sistemas-integracion-01`, `us-central1`, Standard; acceso
uniforme y prevención de acceso público. Cuenta `red-house-archivos`, permisos de
objetos limitados al bucket y firma limitada a esa cuenta. Sin claves privadas
versionadas. Configuración autorizada expresamente por el usuario durante esta ejecución.

## Evidencia y límites del cierre

La [regresión final](../evidencias/segundo-parcial/regresion-final.xml) aprobó 182 pruebas en 2005.90 s, sin fallos ni omisiones. La [prueba complementaria de salud](../evidencias/segundo-parcial/salud-complementaria.xml) aprobó después en 36.08 s; no se suma a esa ejecución como si ambas fueran una sola suite. Los [resultados](../evidencias/segundo-parcial/RESULTADOS.md) detallan esperado, obtenido, fallos y correcciones.

La actualización Docker sustituyó imágenes compatibles de Inventario A/B; no prueba compatibilidad con migraciones futuras desconocidas. La restauración de las 22 API incluyó suspensión por cierre de tapa, documentada por separado; su tiempo de pared no acredita RTO. No se ampliaron deadlines para obtener aprobaciones.

La base, Redis, MongoDB, gateway y host no tienen redundancia de infraestructura en este alcance. GCE, HTTPS público, operación clínica y capacidad productiva no quedan certificados. El respaldo local no copia objetos GCS: se deben conservar las generaciones referenciadas en el bucket.

Recuperación automatizada de contraseña, email/push, agenda detallada por sede/hora y reportes regulatorios certificados conservan justificación como pendientes de alcance posterior. La ayuda de acceso no recupera contraseñas; CSV de la página actual no equivale a exportación completa ni reporte regulatorio. Android y escritorio están excluidos expresamente del segundo parcial; sus contratos JSON/XML sí se prueban.

Las observaciones textuales del docente no fueron proporcionadas. El informe describe correcciones técnicas verificadas sin inventar su procedencia. Los nombres y la portada se omiten por instrucción del usuario. El equipo agregará los datos de identificación y la participación reales cuando corresponda.

La entrega académica completa sigue pendiente de presentación presencial y YouTube; no se atribuyen al código esos requisitos externos.

## Actualización de sesiones del 20 de octubre

El portal conserva credenciales cifradas y concesiones de renovación en Redis. Los cierres y revocaciones pendientes quedan en PostgreSQL, esquema `web_runtime`, con credenciales limitadas. Se mantienen las 71 tablas del dominio y se añade una tabla técnica; 72 tablas entre ambos esquemas. La [validación posterior](../evidencias/sesiones-redis/RESULTADOS.md) registra migración, concurrencia, caídas, recuperación, HTTP Docker y restauración. Las pruebas del cierre anterior mantienen su alcance y fecha.
