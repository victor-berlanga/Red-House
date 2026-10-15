# Revisión de cumplimiento — segundo parcial

**Proyecto:** Red House, red regional de bancos de sangre y donación de órganos · Equipo 01.  
**Corte de revisión:** 14 de octubre de 2026. **Entrega:** jueves 22 de octubre de 2026.  
**Fuente de evaluación:** `/Users/victorberlanga/Programacion/integracion/stuff/entregaSegundoParcial.txt`, leído completo. Se contrastó con `AGENTS.md`, `PROJECT_STATUS.md`, implementación, contratos, pruebas y documentación del árbol de trabajo actual.

## 1. Dictamen

**El proyecto tiene una implementación distribuida sustancial, pero todavía no está listo para acreditar toda la segunda entrega.** Ya existen diez microservicios de negocio/seguridad y Monitoreo, un portal consumidor HTTP, PostgreSQL por propietario, Redis, MongoDB, contratos JSON/XML, Swagger y pruebas de integración. No corresponde describirlo como una maqueta ni como un proyecto sin backend.

Los bloqueos principales son:

1. **Docker no está implementado:** no se encontraron Dockerfiles ni Compose. El arranque por procesos locales no satisface el apartado 11.
2. **MongoDB cumple parcialmente:** hay inserción, consulta, filtrado e índices; no se encontraron actualizaciones funcionales de documentos ni pipelines de agregación. Falta demostrar uso de índices y búsquedas de negocio por identificadores relacionados.
3. **Falta un expediente completo de peticiones/respuestas reales por endpoint.** Los ejemplos generados y los resultados de pytest son útiles, pero no sustituyen las capturas, respuestas completas y comprobaciones de persistencia exigidas.
4. **Falta consolidar el documento técnico de esta arquitectura:** reporte integral, diagramas físicos por servicio, diseño detallado de MongoDB/Redis y matriz de cumplimiento con evidencia concreta.
5. **La carga y administración de archivos no está acreditada de principio a fin:** existe adaptador GCS y API, pero el bucket real sigue pendiente y no se localizó un flujo de carga en las rutas web revisadas.
6. **Debe resolverse la interpretación de independencia de la web:** el portal actual depende de las API para sus operaciones; el backend monolítico fue retirado.
7. **No se localizó un enlace de YouTube ni evidencia de ensayo integral para esta entrega.** Su posible existencia fuera del repositorio debe confirmarla el equipo.

No se asigna un porcentaje global: contar archivos o pruebas no demuestra el porcentaje de cumplimiento de una rúbrica ponderada.

## 2. Alcance y evidencia de esta revisión

Se inspeccionaron la organización completa del repositorio, los once contratos OpenAPI publicados en archivos, las guías actuales, la planificación semestral, los resultados conservados y las implementaciones transversales de seguridad, eventos, persistencia, contratos, archivos y web. Es una auditoría de cobertura para la entrega, no una certificación clínica ni una revisión exhaustiva de cada línea.

### Comprobaciones nuevas

- **19 pruebas aprobadas** en 32.95 s: `test_review_unit.py` y `test_algorithms.py`. Cubren aislamiento de paquetes, contratos y ejemplos, validación XML, sesiones web y algoritmos. El reporte se conserva en [revision-segundo-parcial-unit.xml](../historial/2026-10-14/resultados/revision-segundo-parcial-unit.xml).
- Consulta HTTP de lectura sobre los puertos reales de `.local/runtime/`: **once `/health/ready`, once `/docs/` y once `/openapi.json` respondieron 200**. La página pública del portal en 5050 respondió 200. No se publicaron credenciales ni contenido de sesiones.
- Los puertos 5101–5111 de los README son predeterminados; este entorno utiliza 57404–57414. No confundir una conexión rechazada al puerto de ejemplo con un servicio caído.
- Se contaron **127 operaciones método/ruta en los OpenAPI estáticos: 107 `/api/v1` y 20 `/internal/v1`**. No incluyen los endpoints de salud, documentación y esquemas registrados por infraestructura.
- Búsqueda de Dockerfiles/Compose: ninguno localizado en el árbol del proyecto fuera de entornos privados.

### Evidencia previa comprobada en archivos

- [Regresión del 14/10](../historial/2026-10-14/resultados/regresion.xml): 164 casos, cero fallos, errores u omisiones; el XML registra 597.378 s. **No se volvió a ejecutar esta suite completa en la presente revisión.**
- [Reorganización](../historial/2026-10-14/REORGANIZACION.md): reporta 14 verificaciones del lanzador, 51 visitas de navegador, conservación de filas de 111 tablas y 18 cadenas de custodia verificadas.
- Existen pruebas de flujos HTTP, concurrencia, permisos, caídas y recuperación. Los resultados de carga anteriores están en el historial; no prueban por sí solos el futuro despliegue Docker.

El repositorio contiene numerosos cambios previos y archivos sin seguimiento por una reorganización. Se evaluó el árbol disponible, no únicamente el último commit. Esta revisión no modifica código funcional ni revierte esos cambios.

## 3. Matriz contra el enunciado

**Estados:** implementado = código y evidencia identificados; parcial = faltan elementos o acreditación; pendiente = no localizado; por confirmar = depende de una decisión o evidencia externa. Incluso lo implementado debe volver a demostrarse en la versión final contenerizada.

| Apartado | Estado | Qué tenemos | Qué falta para cerrar |
| --- | --- | --- | --- |
| 1. Evolución a sistema distribuido | Parcial | Web HTTP, servicios separados, persistencia real y procesos del dominio. | Docker, evidencia final y resolver la condición de independencia web. |
| 2. Corregir y ampliar el primer parcial | Parcial | Análisis, requisitos, casos de uso, permisos, planificación, guías actuales e historial de correcciones. | Incorporar observaciones reales del docente; actualizar alcance comprometido, diagramas, diferencias entre parciales y trazabilidad requisito→implementación→prueba→evidencia. |
| 3. Ampliación web | Parcial avanzado | Perfiles, administración, donantes, receptores, inventario, solicitudes, evaluación, reservas, traslados, custodia, filtros, paginación, Highcharts, CSV, alertas y auditoría. | Archivos reales desde la web; especificar alcance de reportes; comprobar conservación de funciones anteriores e independencia acordada. |
| 4. Microservicios | Parcial avanzado | Diez servicios más Monitoreo, responsabilidades, API v1, JWT, roles, JSON/XML, validación, errores, logs, salud, OpenAPI, migraciones y pruebas. | Contenedor/Dockerfile por servicio y ficha individual completa con despliegue y evidencia ejecutada. |
| 5. Request/response por endpoint | Parcial | Contratos, ejemplos, pruebas HTTP y capturas del portal. | Expediente exhaustivo por método/ruta: solicitud y respuesta reales, errores, captura y efecto en almacenamiento. |
| 6. JSON/XML/XSD | Implementado con evidencia por completar | Modelos, ejemplos de entrada, XSD, esquemas de salida y pruebas de paridad/XXE. | Demostración por operación/formato acordado; explicar validación estructural y semántica de XML; completar ejemplos de error. |
| 7. MongoDB | Parcial | Proyecciones de eventos, inserción deduplicada, consulta regional, filtro e índice compuesto. | Actualización de documentos de negocio adecuados, pipelines, evidencia de índices y recuperación por referencias. |
| 8. Redis | Implementado con evidencia por completar | Sesiones, revocación, permisos/versiones, TTL, rate limiting, contadores y caché autorizada; ACL y persistencia local. | Catálogo completo de claves y capturas reales de TTL, revocación, HIT/MISS, invalidación y efecto funcional. |
| 9. Seguridad integrada | Implementado con límites | JWT RS256, renovación, revocación, autorización por rol/recurso/institución, validación y errores uniformes. | Dossier demostrable de usuario permitido, sin permiso, JWT inválido/expirado y sesión revocada en el despliegue final. |
| 10. OpenAPI/Swagger | Implementado con mejoras | Once Swagger/OpenAPI accesibles y respuestas JSON/XML documentadas. | Ejecutar y capturar operaciones reales desde Swagger; ampliar ejemplos de error y explicar la firma de rutas internas. |
| 11. Docker/despliegue | Pendiente | Instaladores y lanzadores locales, configuración privada y requisitos. | Dockerfiles, Compose, redes, puertos, volúmenes, inicialización, secretos, workers, health checks, arranque/parada y evidencia reproducible. |
| 12. Pruebas | Parcial avanzado | Suites unitarias e integración real; reporte previo de 164 casos y 19 comprobaciones nuevas. | Matriz objetivo/entrada/esperado/obtenido/estado/evidencia y ejecución final sobre Docker, incluyendo nuevas capacidades MongoDB/archivos. |
| 13. Documento técnico integral | Parcial | Fuentes técnicas distribuidas y reporte histórico del monolito. | Nueva edición integral fiel al código, con todos los contenidos y anexos de esta entrega. |
| 14. Presencial y YouTube | Parcial / por confirmar | Apuntes por servicio en `stuff/presentacion/`. | Guion integrado, reparto de participación, ensayo, grabación real, publicación y enlace accesible. |
| 15. Proceso completo | Implementado en pruebas; demostración pendiente | Donación/procesamiento y solicitud→reserva→traslado→custodia→recepción, con auditoría/alertas. | Ejecutar al menos uno en Docker y mostrar correlación, datos persistentes, JSON/XML y resultado en web. |
| 18. Criterio de logro | Parcial | Gran parte del núcleo funcional existe. | Cerrar bloqueos de arquitectura reproducible, MongoDB, archivos, documentación y presentación. |

La numeración salta del 15 al 18 en el archivo recibido; no se inventaron apartados 16 y 17.

## 4. Inventario real de servicios

Cada carpeta está en `apps/services/`, con README, `run.py`, requisitos, rutas, migraciones, `outputs.json` y `contracts/`. Los apuntes individuales añaden propósito, tecnología y escenarios, pero no constituyen el expediente completo exigido.

| Servicio | Responsabilidad | Operaciones OpenAPI |
| --- | --- | ---: |
| `ms_identidad_acceso` | Identidad, instituciones, usuarios, permisos, sesiones y catálogos | 36 |
| `ms_donantes` | Donantes, consentimiento, campañas, citas, dictámenes y donaciones | 19 |
| `ms_receptores` | Receptores, solicitudes y retenciones de capacidad | 15 |
| `ms_inventario` | Unidades/ofertas, movimientos, disponibilidad y reservas | 18 |
| `ms_compatibilidad` | Evaluaciones y revisión humana | 5 |
| `ms_priorizacion_geografia` | Rutas, rankings y propuestas de matching | 12 |
| `ms_transporte` | Traslados, telemetría, incidencias y referencias de archivos | 11 |
| `ms_custodia` | Cadena y eventos de custodia | 2 |
| `ms_alertas` | Bandejas y acuses | 3 |
| `ms_auditoria` | Auditoría y consulta documental | 4 |
| `servicio_monitoreo` | Disponibilidad, sondeos y estadísticas técnicas | 2 |

**No hace falta crear más servicios para llegar a una cantidad.** Se debe explicar que son diez servicios y un componente transversal de monitoreo; los seis a diez del enunciado son referencia. Tampoco hace falta implementar DELETE o PUT artificialmente: las operaciones corresponden al negocio y la conservación de historiales puede requerir bajas lógicas.

Por cada servicio falta consolidar en una ficha: identificación, justificación con requisitos, arquitectura interna, dependencias, endpoints, entradas/headers, salidas/códigos, seguridad, tablas/colecciones/claves, integraciones, Dockerfile/puerto, evidencia y pruebas. El contenido existente debe reutilizarse, evitando once documentos que repitan información desactualizada.

## 5. Pendientes técnicos y criterios de cierre

### P0-01. Contenerizar y demostrar el despliegue

**Evidencia:** no hay Dockerfile/Compose; `scripts/local.py` inicia procesos y `.github/workflows/services.yml` instala dependencias locales sin contenedores.

- [ ] Dockerfile por microservicio; incluir Monitoreo y una forma reproducible de ejecutar el portal.
- [ ] Compose con PostgreSQL, MongoDB, Redis, API, workers de eventos, worker de sesiones web y monitoreo.
- [ ] Redes, DNS interno, puertos publicados y URLs configurables; no trasladar `127.0.0.1` del host como dirección entre contenedores.
- [ ] Volúmenes para datos y sesiones técnicas cuando corresponda; secretos fuera de las imágenes y del control de versiones.
- [ ] Inicialización reproducible de la base compartida, roles, migraciones, usuarios MongoDB, ACL Redis y datos ficticios mínimos (arquitectura revisada el 15/10).
- [ ] Health checks, dependencias listas, reintentos, logs y parada ordenada; verificar que los workers realmente entregan eventos.
- [ ] Documentar levantar, consultar estado, detener, reiniciar un servicio y preservar datos.
- [ ] Ensayar desde un clon limpio, sin `.venv` ni `.local/runtime` heredados; conservar salida de build, estado y comunicaciones.

**Aceptación:** otra persona levanta el conjunto siguiendo únicamente la guía, completa un flujo y reinicia conservando sus registros. La imagen de cada servicio puede construirse y actualizarse individualmente. No borrar volúmenes para simular un reinicio exitoso.

### P0-02. Completar MongoDB sin alterar auditoría inmutable

**Evidencia:** `redhouse/events.py` usa `insert_one` y `find_one`; `ms_auditoria/routes.py` usa `find`, filtro regional, orden, paginación y conteo. `scripts/local.py` crea índice `(region_id, source)` y usuarios con permisos `find`/`insert`. No se encontraron `update_one`, `update_many` ni `aggregate` en el Python inspeccionado.

- [ ] Definir una colección/proyección mutable vinculada al negocio, con propietario, esquema, versión y permisos mínimos; por ejemplo, resumen documental del seguimiento de un traslado.
- [ ] Implementar una actualización real y autorizada de esa proyección, conservando los eventos originales. **No habilitar cambios en el historial inmutable solo para satisfacer el requisito.**
- [ ] Implementar un pipeline útil, por ejemplo estadísticas de eventos por servicio/periodo o incidencias logísticas, restringido al ámbito autorizado.
- [ ] Incorporar recuperación por referencia PostgreSQL, filtros y paginación adecuados al caso. La deduplicación por `_id` ya existe, pero no sustituye mostrar una consulta funcional por traslado/recurso.
- [ ] Documentar índices y comprobar su utilización con un plan de ejecución y datos pertinentes; crear un índice no acredita su uso.
- [ ] Capturar inserción, consulta, actualización, filtrado, agregación, índices y relación con PostgreSQL, con pruebas y manejo de indisponibilidad.

**Aceptación:** las siete operaciones/capacidades del apartado 7 pueden mostrarse sobre datos generados por un proceso real, sin una colección de ejemplo desconectada del sistema.

### P0-03. Expediente de request/response

Los `*.example.json/xml` se generan desde esquemas; son ejemplos contractuales. Los XML de pytest certifican resultados de tests, pero no contienen necesariamente solicitudes y respuestas completas de las 127 operaciones.

- [ ] Inventariar todos los métodos/rutas publicados, incluyendo internos y auxiliares; indicar cómo se demuestra cada uno y cuáles requieren firma entre servicios.
- [ ] Vincular cada operación a su objetivo, servicio, rol y requisito.
- [ ] Guardar URL completa, método, parámetros, headers, cuerpo, estado HTTP, respuesta, explicación y captura de ejecución real.
- [ ] Añadir consulta posterior y evidencia SQL/MongoDB/Redis cuando aplique; registrar explícitamente cuando no hay escritura.
- [ ] Cubrir éxito, entrada inválida, recurso inexistente, falta de autenticación, falta de permisos y conflicto de negocio donde correspondan.
- [ ] Mostrar recepción y generación de JSON/XML en las operaciones que ofrecen esos formatos.
- [ ] Incluir fecha, versión/commit y correlación para relacionar evidencia y código; ocultar passwords, JWT, refresh tokens y URLs firmadas utilizables.

**Aceptación:** ninguna operación implementada queda sin ficha o sin una explicación comprobable de su evidencia. Una colección Postman o un ejecutor HTTP facilita la repetición; no es obligatorio elegir Postman si otra herramienta satisface la captura requerida.

### P0-04. Conservar funcionalidad web y aclarar independencia

`apps/web/README.md` indica que las operaciones requieren los microservicios. `test_identity_outage_reports_503_without_legacy_fallback` comprueba la caída controlada de Identidad. La independencia frente a móvil/escritorio sí es coherente con la arquitectura; independencia operativa total frente a las API no está implementada.

- [ ] Registrar la interpretación del docente sobre «continuar funcionando de manera independiente» y contrastarla con el alcance aprobado.
- [ ] Si significa independencia de aplicaciones cliente, documentar esa condición y demostrar el portal funcionando sin ellas.
- [ ] Si exige conservar operación de negocio sin los microservicios, tratarlo como brecha arquitectónica real y acordar/implementar la solución; una página pública con HTTP 200 no acredita esa independencia.
- [ ] Comparar los casos de uso del primer parcial contra la web actual: acceso, usuarios, instituciones, inventario, paneles y permisos; registrar cambios o pérdidas explícitas.

No se recomienda reintroducir doble escritura ni copiar reglas de negocio al portal como arreglo rápido. Esta decisión debe preceder a una modificación estructural.

### P1-01. Carga y administración de archivos

`ms_transporte/files.py` prepara una URL firmada, verifica tamaño/MIME/firma/hash y permite descarga autorizada; acepta JPEG, PNG y PDF hasta 10 MiB. `redhouse/storage.py` contiene el adaptador GCS. Las guías reconocen que el bucket real no está verificado. No se localizaron controles de carga/descarga en las rutas de logística web inspeccionadas.

- [ ] Conectar un bucket privado real y demostrar carga, verificación, consulta y descarga autorizada.
- [ ] Incorporar el flujo web y estados comprensibles: pendiente, verificado, error o acceso denegado.
- [ ] Probar tipo/tamaño/hash incorrectos, objeto ausente, URL expirada, usuario ajeno y dependencia inaccesible.
- [ ] Mostrar metadatos persistidos y objeto real; conservar el límite autorizado de archivos.

**Aceptación:** un usuario autorizado adjunta evidencia a un traslado desde el portal y otro autorizado la consulta; alguien sin permisos no puede obtenerla. Un adaptador sin bucket o una prueba simulada no cumple este cierre.

### P1-02. Completar evidencia de Redis y seguridad

La base está implementada en `redhouse/security.py`, `redhouse/cache.py` e Identidad; no debe rehacerse desde cero.

- [ ] Catálogo de prefijos/claves: propietario, dato, propósito, TTL, creación, invalidación y permisos.
- [ ] Mostrar login y sesión, acceso autorizado, JWT inválido/expirado, usuario sin permisos y rechazo tras logout/revocación.
- [ ] Mostrar TTL antes/después, caché HIT/MISS, invalidación por escritura y rate limiting, sin exponer valores secretos.
- [ ] Explicar que la sesión técnica cifrada en SQLite del portal no reemplaza la autoridad de Redis.
- [ ] Documentar autenticación interna con firma de servicio y los casos sin JWT humano delegado; demostrar sus permisos y protección contra repetición.

**Aceptación:** el mismo usuario/sesión tiene decisiones de autorización coherentes en web y API, y Redis inaccesible produce fallo controlado en las operaciones protegidas.

### P1-03. Contratos y Swagger

- [ ] Mantener sincronizados OpenAPI servido y archivos `contracts/` después de los cambios.
- [ ] Agregar ejemplos concretos de respuestas de error; el generador actual define esquemas/códigos, pero sus respuestas de error no incluyen ejemplos como las exitosas.
- [ ] Demostrar `Try it out` en los servicios desplegados, con autenticación y bodies JSON/XML válidos.
- [ ] Explicar que `response.xsd` valida la envoltura XML y `xml_response.validate_response` valida el DTO/tipos por operación; el XSD genérico por sí solo no valida todo el contrato de negocio.
- [ ] Preparar un mecanismo reproducible para rutas internas firmadas; no prometer que un JWT de usuario basta para ejecutarlas.

### P1-04. Pruebas de la entrega final

- [ ] Reejecutar la regresión sobre la versión congelada y conservar JUnit/condiciones de entorno.
- [ ] Añadir pruebas proporcionales a MongoDB mutable/agregaciones, archivos reales y contenedores.
- [ ] Matriz por caso con objetivo, entradas, esperado, obtenido, estado y enlace a evidencia.
- [ ] Probar flujo completo, revocación, permisos institucionales, idempotencia y conflictos de reserva.
- [ ] Verificar caída/recuperación de dependencias y reentrega de eventos sin duplicar cambios en Docker.
- [ ] Comprobar que los reportes no acumulan como pruebas distintas varias ejecuciones del mismo caso.

## 6. Documento técnico y trazabilidad pendientes

Las fuentes existen, pero la planificación semestral todavía usa fases y estados históricos. El reporte integral Word/PDF conservado en el historial describe el monolito; no debe presentarse como descripción actual.

- [ ] Portada, integrantes, identificación y fecha/versión de entrega.
- [ ] Resumen ejecutivo, problema, objetivos y alcance específico comprometido del segundo parcial.
- [ ] RF/RNF actualizados, procesos y actores; separar lo entregado, lo pendiente justificado y lo excluido.
- [ ] Observaciones reales del primer parcial, corrección aplicada y prueba de cierre; no inventar comentarios del docente.
- [ ] Matriz actual de roles, permisos, recursos y ámbito institucional, contrastada con código.
- [ ] Arquitectura ejecutable y diagramas de componentes, comunicación, despliegue Docker, secuencias y datos.
- [ ] Modelos lógico/físico actuales de PostgreSQL por servicio: tablas, claves, restricciones, índices, migraciones y referencias externas. Los modelos 0FN–4FN académicos no sustituyen este mapa físico.
- [ ] Diseño MongoDB: colecciones, ejemplos, relaciones, índices, actualizaciones, pipelines, consistencia eventual y justificación frente a SQL.
- [ ] Diseño Redis: claves, TTL, permisos, sesiones, revocación, caché, contadores y fallos.
- [ ] Fichas de los once componentes con los trece elementos del apartado 4.
- [ ] Contratos JSON/XML/XSD, seguridad y endpoints; anexar evidencia por operación.
- [ ] Integración web, configuración Docker, variables sin secretos y procedimiento de arranque/parada.
- [ ] Pruebas y resultados, problemas/soluciones, conclusiones y pendientes explícitos.
- [ ] Matriz de trazabilidad: ID del enunciado/RF/RNF → servicio/ruta web → implementación → prueba → evidencia → estado → justificación pendiente.
- [ ] Explicar para cada componente qué se hizo, cómo, por qué, cómo se validó y qué evidencia lo acredita.
- [ ] Consolidar una versión legible para entrega y sincronizar exportaciones si se presentan Word/PDF. El enunciado exige el documento técnico; no especifica que ambos formatos sean obligatorios.

**Aceptación:** cada afirmación de funcionalidad apunta a código y evidencia de la misma versión. Documentar una justificación pendiente mejora la transparencia, pero no equivale a cumplir el requisito ni a obtener aceptación automática del docente.

## 7. Presentación y demostración

### Flujo recomendado

Usar datos ficticios nuevos y un recurso/solicitud identificables. La recomendación aprovecha `test_full_reservation_transport_receipt_from_web_and_xml` y `test_resource_to_receipt_custody_audit_and_notification`.

1. Mostrar contenedores y salud; acceder con roles diferentes.
2. Registrar/liberar un recurso de sangre con revisión humana y crear una solicitud autorizada.
3. Generar evaluación, registrar dictamen y reservar sin duplicar disponibilidad.
4. Planificar traslado, registrar recolección, entrega y recepción; verificar custodia.
5. Mostrar el resultado en web y consultar el mismo recurso mediante JSON y XML.
6. Relacionar IDs con PostgreSQL, documentos MongoDB y auditoría/alertas; demostrar una agregación y actualización documental autorizada.
7. Mostrar Redis: TTL/caché y revocación; repetir una petición con sesión revocada y observar rechazo.
8. Mostrar un error de validación/conflicto controlado y la persistencia tras reiniciar el componente elegido.

- [ ] Guion cronometrado, responsables por bloque y participación de todos los integrantes.
- [ ] Ensayo completo en la misma máquina/versión que se presentará; registrar duración e incidencias.
- [ ] Grabación que muestre problema, arquitectura, funcionamiento integrado, Swagger, solicitudes/respuestas, bases, Redis y Docker.
- [ ] Publicar en YouTube como público u oculto; verificar accesibilidad sin sesión y añadir enlace al documento técnico.
- [ ] Preparar recuperación del entorno y datos ficticios de demostración; nunca proyectar `state.json` ni credenciales.

La entrega requiere al menos **un** proceso completo en vivo. Los tres procesos integrales de `AGENTS.md` pertenecen al alcance global del proyecto y conviene conservarlos, sin confundirlos con el mínimo explícito de esta evaluación.

## 8. Mejoras recomendadas y alcance que no debe confundirse

| Mejora | Motivo / alcance |
| --- | --- |
| Etiquetar CSV como exportación de la página actual o añadir exportación completa filtrada | `routes/common.py` exporta los `items` cargados de la página. Ya hay CSV, pero no demuestra un reporte integral/regulatorio. |
| Implementar recuperación de contraseña o declarar su pendiente | `/recuperar-acceso` redirige a ayuda de acceso; no es recuperación con token. Es requisito general y debe revisarse si forma parte del alcance comprometido de este parcial. |
| Precisar agenda por sede/hora y capacidad | Hay campañas/citas; el estado del proyecto reconoce que falta agenda detallada. No presentarla como agenda completa. |
| Diferenciar reportes operativos de regulatorios | Las exportaciones y paneles no acreditan formatos normativos aprobados. |
| Mejorar instalación reproducible y CI | Hay workflow, pero falta evidencia remota. Añadir build/arranque Docker y pruebas de integración evitará dependencia del Mac preparado. |
| Cerrar la reorganización en control de versiones | Hay movimientos y archivos sin seguimiento. Validar desde un clon limpio para no omitir web, migraciones o documentos de la entrega. |
| Consolidar documentación por tema | Evita contradicciones entre guías, Word, planificación y el sistema real. Este informe nuevo responde a la revisión solicitada; no reemplaza las fuentes técnicas. |
| Mantener límites clínicos explícitos | ABO, ranking y matching académico no equivalen a HLA validado ni a asignación clínica oficial. No introducir nuevas reglas sin validación y trazabilidad. |

**Excluidos expresamente del segundo parcial:** aplicaciones Android y de escritorio. No deben ocupar el esfuerzo prioritario ni contabilizarse como faltantes de esta entrega. Sí se exigen JSON/XML implementados y probados.

**Pendientes generales que deben conservarse, con alcance separado:** GCE/HTTPS productivo, supervisión productiva, alta disponibilidad, carga/estrés sostenidos, validación clínica/normativa, HLA, retención aprobada, email/push y archivos grandes. El texto de esta entrega no exige expresamente GCE, Locust ni alta disponibilidad como apartados independientes; no convertirlos en condiciones nuevas sin revisar el alcance aprobado. Docker sí es obligatorio ahora. La carga/administración de archivos sí aparece en el alcance web y GCS es la tecnología de almacenamiento establecida para el proyecto.

## 9. Orden propuesto hasta el 22 de octubre

| Periodo sugerido | Resultado prioritario |
| --- | --- |
| 14–15 octubre | Acordar alcance e independencia web; inventario de endpoints/evidencias y diseño Docker. |
| 15–17 octubre | Docker reproducible, completar operaciones MongoDB y flujo de archivos comprometido. |
| 17–19 octubre | Regresión final, seguridad y flujo integral sobre contenedores; capturas por endpoint. |
| 19–20 octubre | Documento técnico, diagramas y trazabilidad con la evidencia obtenida. |
| 20–21 octubre | Ensayo presencial, grabación, publicación y validación del enlace; corregir fallos. |
| 22 octubre | Presentar la versión congelada y reproducible con todos los anexos. |

Es una propuesta de orden, no una estimación garantizada. El volumen de 127 operaciones hace que el expediente de evidencia deba prepararse desde el inicio.

La rúbrica concentra **45% en microservicios e integración** (25% + 20%), **35% en documentación y evidencias/contratos** (20% + 15%), 10% en pruebas/cumplimiento y 10% en presentaciones. Por eso la prioridad es cerrar Docker/MongoDB y acreditar lo que ya existe, antes de añadir nuevas pantallas o servicios.

## 10. Condiciones para declarar lista la entrega

- [ ] Alcance del segundo parcial y condición de independencia web registrados.
- [ ] Dockerfiles/Compose funcionales y verificados desde una instalación limpia.
- [ ] Siete capacidades MongoDB demostradas en procesos del dominio.
- [ ] Web ampliada y funcional, incluidos los archivos comprometidos.
- [ ] Request/response real y evidencia de almacenamiento por operación aplicable.
- [ ] JSON/XML/XSD y Swagger comprobados en servicios desplegados.
- [ ] JWT/Redis/roles/revocación demostrados con casos positivos y negativos.
- [ ] Pruebas unitarias e integración con resultados de la versión final.
- [ ] Documento integral, diagramas actuales y matriz de trazabilidad completos.
- [ ] Un proceso de principio a fin ensayado y reproducible.
- [ ] Todos los integrantes preparados; video publicado y enlace accesible.
- [ ] Código, configuración sin secretos y documentación incluidos en la versión entregada.

**Hasta cerrar estos puntos, el estado correcto es “implementación avanzada con pendientes de cumplimiento”, no “segundo parcial terminado”.**
