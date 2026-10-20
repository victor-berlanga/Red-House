# Estado vigente de Red House

Actualizado: **20 de octubre de 2026**. Leer junto con `AGENTS.md` y el [índice documental](documentation/README.md). El historial detallado está separado del estado actual.

## VM Google Compute Engine con acceso público (20 de octubre)

El sistema implementado está disponible en **https://34.18.186.116**. HTTP redirige a HTTPS. Monolito, once propietarios de API con dos réplicas, workers, PostgreSQL, MongoDB y Redis se ejecutan en la VM; los archivos privados residen en GCS. No requiere túneles ni procesos locales. La IP quedó reservada como `red-house-public`; Nginx publica únicamente TCP 80/443 y mantiene los puertos de diagnóstico en loopback. Las bases no tienen puertos publicados. [Guía y comandos](deployment/gcp/README.md).

La VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`, conserva las características comprobadas de `maquina01`: CentOS Stream 10, `e2-standard-2`, 2 vCPU, 8 GB RAM y disco `pd-standard` de 20 GB. La instancia original no se modificó. La copia inicial conservó **15 263 filas de 72 tablas SQL y 7 721 documentos MongoDB**, con conteos/hashes iguales, además de Redis y permisos. Las pruebas posteriores agregan datos ficticios; esas cifras no representan el conteo actual.

Criterios del acceso público: abrir todo el portal desde la IP sin dependencias locales; mantener JWT, CSRF y archivos privados; permitir las API y Swagger en `/services/<servicio>/`; conservar las bases privadas; renovar TLS automáticamente y detener los servicios locales. [Resultados](documentation/evidencias/gcp/RESULTADOS.md): **27 contenedores saludables**, sistema habilitado al arranque, cuatro controles HTTP aprobados (sangre por API, JSON/XML de once servicios, sangre por web y GCS), **20 páginas de siete perfiles** en Chrome, gráficas, cookies seguras, renovación/cierre de sesión, rechazo de cookie cerrada y ejecución Swagger 200. Once servicios pasaron readiness, documentación, OpenAPI y XSD por HTTPS; ocho puertos internos no resultaron accesibles desde el cliente externo.

Let's Encrypt emitió un certificado válido para la IP. Certbot 5.8.0 comprueba la renovación cada seis horas mediante systemd; la simulación de renovación y recarga de Nginx pasó. La web declara HTTPS explícitamente en Waitress y usa cookies `Secure`, `HttpOnly`, `SameSite=Lax`. OpenAPI/Swagger reconoce los prefijos públicos; las rutas internas están bloqueadas en la entrada externa. No se agregaron motores de datos ni se cambió la lógica clínica.

La VM queda encendida en `/opt/redhouse`. Docker Desktop, el contenedor auxiliar de compilación y PostgreSQL de Homebrew quedaron detenidos en el equipo local; tampoco hay portal, APIs ni túneles de Red House ejecutándose localmente. Código y datos locales se conservan como copia independiente. La verificación de navegador actúa únicamente como cliente externo y termina al finalizar.

GCS utiliza identidad adjunta de Compute Engine y firma IAM acotada, sin ADC personales ni claves privadas de cuenta de servicio. Las cuentas de aplicación conservan las del Docker copiado. Se mantiene la evidencia anterior del túnel como primera etapa, reemplazada por este acceso público. No se ensayó un reinicio completo de la VM ni se certifican redundancia entre hosts, carga sostenida u operación clínica/productiva. Las ediciones Word/PDF anteriores conservan su fecha y alcance.

## Guiones de demostración presencial y video (20 de octubre)

Se agregaron dos guiones en `stuff/demostracion_segundo_parcial/`, en [español](stuff/demostracion_segundo_parcial/guion_es.md) e [inglés](stuff/demostracion_segundo_parcial/guide_en.md), a partir de la consigna de presentación compartida por el usuario. Ambos cubren qué decir y qué enseñar en clase y en YouTube, sin portada ni nombres. El índice de `stuff` enlaza el nuevo material.

Criterios de aceptación: cubrir sistema web, microservicios, JSON/XML, Swagger, JWT, MongoDB, Redis, Docker y proceso de negocio con evidencias reales; conservar equivalencia entre idiomas; repartir responsabilidades entre todos los integrantes; indicar publicación pública u oculta. El recorrido propone un traslado preparado y un alta por Swagger seguida por identificador y correlación hasta el portal, PostgreSQL, MongoDB y logs Docker. Redis se demuestra mediante existencia/TTL de sesión antes y después del logout. Se distingue expresamente el portal monolítico del consumo HTTP de las API, la bitácora SQL del documento MongoDB y los indicadores de salud de una petición de negocio.

Validación documental: 28 enlaces locales comprobados entre los nuevos guiones y el índice; sintaxis correcta en diez bloques shell, seis fragmentos Python embebidos y dos plantillas JSON. Comandos iguales entre idiomas; cinco métodos/rutas contrastados con OpenAPI y cuatro nombres de servicios con Compose. Las consultas usan las vistas y permisos existentes y muestran campos seleccionados. No se ejecutaron los comandos de demostración ni se alteró GCP, datos o servicios locales. Ensayo con folios/fechas nuevos, participación, grabación y publicación siguen pendientes del equipo; el guion no acredita esas actividades.

## Material breve para la exposición (20 de octubre)

Se agregaron [cuatro guías de presentación](stuff/presentacion/README.md): nivel general y técnico, cada uno en español e inglés. Cada guía tiene ocho bloques, notas para hablar y demostración propuesta; duración orientativa de 8–10 o 12–15 minutos según el nivel. Se actualizaron el índice de `stuff`, la lectura inicial y el enlace al guion ampliado.

Criterios de aceptación: resumir avances y funcionamiento del parcial, mantener equivalencia entre idiomas, omitir portada e integrantes y distinguir lo implementado de lo pendiente. Las guías reflejan el portal autónomo, Docker, sesiones Redis/PostgreSQL, archivos privados y resultados fechados; las cantidades de distintas ejecuciones no se suman como casos únicos.

Validación documental: las cuatro guías conservan ocho bloques; 41 enlaces locales comprobados en los siete Markdown de presentación e índice, sin destinos ausentes. Se revisaron cifras, equivalencia de contenido y formato. Solo se modificó documentación; no se repitieron pruebas de aplicación ni se iniciaron servicios. Ensayo, exposición y grabación siguen a cargo del equipo.

## Sesiones del portal en Redis (20 de octubre)

Por solicitud del usuario se retiró el almacenamiento local de sesiones de la aplicación. Redis conserva tokens cifrados con TTL de hasta 86400 s y concesiones de renovación de 60 s. PostgreSQL conserva cierres y revocaciones pendientes en `web_runtime.session_revocations`. Credenciales separadas: ACL `web_sessions` limitada al prefijo del portal y rol `rh_web_sessions` limitado a la tabla técnica. El esquema del dominio mantiene 71 tablas; con la tabla técnica son 72 en la misma base.

Criterios: no importar ni montar el almacén anterior; preservar cookie opaca, cifrado, expiración, permisos, concurrencia y cierre seguro; actualizar instalaciones local/Docker sin modificar filas del dominio; conservar pendientes ante fallos y documentar la operación. [Resultados y reproducción](documentation/evidencias/sesiones-redis/RESULTADOS.md): **121 pruebas de regresión aprobadas** (798.33 s) y **9 pruebas finales del módulo** (82.26 s), incluido rechazo de revocaciones indescifrables. Las ocho pruebas originales del módulo se repiten; no se suman como casos únicos.

Migración aplicada a `.local/runtime` y `.local/compose`: 120 681 y 15 122 filas de dominio conservadas respectivamente; bootstrap Docker repetido sin rotar credenciales. No existían sesiones o revocaciones antiguas vigentes. Respaldos privados conservados. Docker comprobó login, renovación y logout por HTTP con todas las API detenidas, cifrado/TTL Redis y rechazo de cookie cerrada; sin volumen local de sesiones. Respaldo restaurado en motores nuevos: **15209 filas de 72 tablas** idénticas y permisos del portal conservados. Word/PDF y guías actualizados.

Límites: PostgreSQL es necesario para verificar las marcas de cierre; ante su caída, acceso protegido y cierre global responden 503, aunque se elimina la cookie del navegador. Si Redis cae, la marca se conserva y el worker completa la revocación al recuperarse. Si falta la clave de cifrado, el pendiente se conserva. Los usuarios deben iniciar sesión nuevamente. Los entornos intervenidos quedan detenidos con datos conservados. Las evidencias del cierre del 19 de octubre son antecedentes y no se atribuyen a esta revisión.

## Segundo parcial: cierre técnico documentado (19 de octubre)

Aplicación **0.3.0**. Se completó el incremento de `stuff/prompts/completar_segundo_parcial.md`, con los límites y pendientes externos indicados en la [matriz final](documentation/markdowns/Cierre_segundo_parcial.md). El entorno habitual `.local/runtime` y sus datos permanecen separados de las pruebas.

Implementado: backend web modular autónomo con reglas/JWT/Redis compartidos y workers propios; Dockerfiles por servicio/web, dos instancias por API incluyendo Identidad/Monitoreo, gateway DNS, volúmenes y secretos privados; proyección MongoDB versionada/reconstruible; flujo web GCS privado con validación de contenido/hash, estados y firmas; expediente HTTP con persistencia y capturas. El [informe integral](documentation/markdowns/Reporte_tecnico_segundo_parcial.md), once fichas, diagramas y catálogo físico de 71 tablas/145 índices se entregan en [Word/PDF](documentation/segundo-parcial/README.md), sin portada ni nombres.

Pruebas finales verificadas:

- [Regresión](documentation/evidencias/segundo-parcial/regresion-final.xml): **182 aprobadas**, cero fallos y omisiones, **2005.90 s**, con GCS real. Incluye 40 pruebas del lanzador. [Salud complementaria](documentation/evidencias/segundo-parcial/salud-complementaria.xml): una prueba posterior aprobada en **36.08 s**, informada por separado.
- [HTTP](documentation/evidencias/segundo-parcial/http/index.html): **284/284 métodos/rutas con éxito y captura**, 240 con error; 44 documentos fijos con justificación de no aplicabilidad. Todas las escrituras capturadas tienen comprobación de persistencia.
- [Docker](documentation/evidencias/segundo-parcial/docker-release/docker-results.json): **nueve controles aprobados**. Sangre por API; órganos y JSON/XML de once propietarios sin las réplicas A; sangre/órganos por web con las 22 API apagadas; gateway 502 sin autoridades; ambas imágenes de Inventario sustituidas con **100 consultas continuas 200** y altas persistidas; reinicio de los tres almacenes con SQL conservado y lecturas recuperadas.
- [Navegador](documentation/evidencias/segundo-parcial/browser/browser-results.json): **20 páginas de siete perfiles**, series Highcharts contrastadas con datos del servidor, ancho 390 sin desbordamiento, carga GCS verificada y Swagger ejecutado 200; sin errores JavaScript.
- [Respaldo/restauración](documentation/evidencias/segundo-parcial/backup-restore.json): **15 122 filas SQL de 71 tablas**, **7 632 documentos MongoDB**, cinco usuarios y cuatro roles documentales iguales por conteo/hash; clave Redis restaurada con TTL 3575 s. Motores nuevos, sin puertos publicados.
- [Clon limpio](documentation/evidencias/segundo-parcial/clean-clone.json): **ocho etapas aprobadas**, secretos y volúmenes nuevos, **27 contenedores saludables**, sangre por API y JSON/XML de once propietarios; bootstrap repetido. Instantánea Git temporal local, sin publicar commits. [630 archivos de aplicación/despliegue idénticos](documentation/evidencias/segundo-parcial/source-validation.json) y hashes de servicios iguales a los capturados en la regresión.

GCP autorizado: bucket privado `red-house-evidencias-sistemas-integracion-01`, Standard, `us-central1`, acceso uniforme y bloqueo público; cuenta `red-house-archivos`, permisos de objetos limitados al bucket y firma limitada a esa cuenta. ADC impersonada, sin claves privadas descargadas. [Prueba real](documentation/evidencias/segundo-parcial/gcs-real.json): carga, descarga/hash, rechazo público, archivo inválido, objeto ausente, expiración `400 ExpiredToken`, fallo 503 y recuperación 200. La evidencia ficticia del navegador permanece para demostración; la prueba automatizada limpió sus propios objetos.

Los [resultados](documentation/evidencias/segundo-parcial/RESULTADOS.md) conservan los incidentes y sus correcciones: esperas GCS, configuración Docker, conexiones SQL, sondeos de salud, datos de captura, autenticación durante restauración MongoDB, orden del agregado SQL y DNS del primer clon. La restauración final de las API incluyó cierre de tapa de 11:24:40 a 12:16:02; [registro](documentation/evidencias/segundo-parcial/docker-release/host-suspension.json). Esa duración de pared no mide RTO. No se ampliaron deadlines para aprobar.

[Revisión final de artefactos](documentation/evidencias/segundo-parcial/validacion-artefactos.json): informe de 36 páginas y catálogo físico de 41, Word íntegros, figuras/tablas inspeccionadas y sin texto fuera de página; 2214 enlaces locales válidos, 1204 archivos de evidencia revisados sin los patrones de credenciales buscados. Ruff y formato de 163 archivos, sintaxis JavaScript, `git diff --check` y sincronización CodeGraph aprobados.

Los Compose de demostración y prueba quedan **detenidos**, con datos y respaldos privados conservados. Inicio del principal: `python3 deployment/start.py`. Presentación presencial, participación real y grabación/publicación de YouTube siguen pendientes del equipo. Los límites funcionales y productivos figuran abajo y en la matriz; no se declara completa la entrega académica externa.

## Decisión de arquitectura (15 de octubre)

Por indicación del usuario se implementa una base PostgreSQL compartida por todos los servicios, como Bookstore. El [nuevo esquema compartido](data/database/schema.sql) deriva de main local `44eeaf90c445b4d9564c2f0ab2dd3167f0296418` y conserva sus 45 tablas, agregando 26 (71 en total) tras adaptar los contratos ejecutables. La propuesta inicial de 60 tablas quedó ampliada. [Cambios y correspondencia por servicio](documentation/markdowns/Esquema_compartido.md). La base inicial de main tiene 23 tablas y sus migraciones 002–004 agregan 22; las menciones previas a 46 no coinciden con ese SQL fijado.

**Implementado y aplicado al entorno local:** instalador, acceso SQL, colas y migrador utilizan `red_house`, con tablas físicas compartidas y vistas de permisos por servicio. La conversión verificó **111 tablas de origen y 118 428 filas sin diferencias** antes de publicar conexiones. Las once bases antiguas y sus respaldos privados permanecen conservados; las aplicaciones ya no las utilizan. Los SQL por servicio quedan como referencia del origen.

## Sistema actual

- `apps/web/`: portal Flask/Jinja2 con backend modular propio o consumo HTTP explícito. El backend histórico permanece retirado; no hay doble escritura ni cambio automático de backend tras un fallo.
- `apps/services/`: diez microservicios y Monitoreo, con contratos JSON/XML, JWT, Redis, PostgreSQL y MongoDB.
- PostgreSQL conserva una base operativa compartida, `red_house`, con 71 tablas y credenciales separadas por servicio. MongoDB conserva documentos/proyecciones; Redis mantiene sesiones y datos temporales. La web conserva sesiones técnicas cifradas y bloqueos en Redis; una tabla técnica adicional en `web_runtime` conserva cierres y revocaciones pendientes (72 tablas totales entre ambos esquemas).
- La carga regional es ficticia, pero sus operaciones y almacenamiento son reales. No se reinicializa al arrancar. Las reglas de compatibilidad y priorización no sustituyen la revisión médica.
- Android y escritorio están fuera de este parcial. Docker, bucket GCS y VM GCE con acceso por IP y HTTPS están implementados; operación productiva y redundancia continúan pendientes.

## Operación

Acceso habitual: **https://34.18.186.116**, con todo el procesamiento en GCP. Los comandos siguientes son para desarrollo local opcional y no son necesarios para usar la VM.

Desde la raíz: `bash install.sh`, `bash start.sh`, `bash components.sh estado` y `bash stop.sh`. Los BAT de Windows utilizan WSL/Ubuntu; no son un port nativo.

El entorno predeterminado es `.local/runtime/`, privado y excluido de Git. El origen del traslado y los respaldos previos a las migraciones se conservaron. No ejecutar simultáneamente copias del mismo entorno. Portal: http://127.0.0.1:5050.

[Instalación y diagnóstico](documentation/markdowns/Instalacion_y_operacion.md) · [Datos y migraciones](documentation/markdowns/Datos_y_persistencia.md) · [Mapa de bases](data/database/README.md).

## Reorganización y validación del 14 de octubre

- Directorios principales `apps/`, `data/`, `documentation/` y `stuff/` conservados como hermanos. Análisis, requisitos, planificación semestral y modelos lógicos conservados en sus carpetas por formato; guías vigentes consolidadas. Entregas de implementaciones anteriores, bitácora y resultados agrupados en `documentation/historial/`.
- Rutas web, lanzadores, requisitos, CI, generadores y contratos actualizados. Identificadores redundantes normalizados con migraciones, conservando auditoría y cadenas firmadas.
- 39 pruebas del lanzador aprobadas; Chrome recorrió 51 páginas sin errores registrados. Once servicios y portal respondieron HTTP 200 con los registros regionales conservados; 18 cadenas de custodia verificadas.
- Comparación de 111 tablas durante la migración: ninguna fila perdida ni cambio inesperado; usuarios e historiales preservados.
- Regresión final: **164 pruebas aprobadas**, cero fallos/errores/omisiones, 597.68 s. Ciclo de vida real del lanzador: **14 comprobaciones aprobadas**. Enlaces, contratos, sintaxis y formato verificados.

[Criterios, cambios, resultados y límites de esta entrega](documentation/historial/2026-10-14/REORGANIZACION.md). [Historial anterior](documentation/historial/README.md).

## Pendientes

- Validación clínica/normativa de reglas, HLA, elegibilidad, asignación, retención y acceso institucional.
- Agenda detallada por sede/hora, recuperación automatizada de contraseña, email/push y reportes regulatorios certificados.
- Presentación presencial, participación nominal, grabación/publicación de YouTube y enlace accesible del equipo.
- Android, escritorio XML, operación productiva y redundancia de infraestructura; la VM GCE académica ya ejecuta Docker con supervisión por instancia y HTTPS público.
- Carga sostenida, saturación, alta disponibilidad y ejecución de CI remoto. Windows/WSL y Ubuntu completos no están certificados por las pruebas de este Mac.

El diagrama físico compartido, catálogo de 71 tablas, informe integral y evidencias de archivos/continuidad pertenecen al incremento actual descrito al inicio. Los modelos 0FN–4FN y las once ediciones Word de planificación se conservan como referencias del semestre; el reporte del monolito anterior es un antecedente.

## Revisión documental del 14 de octubre

Se restituyeron once documentos de planificación con sus once Word y diez archivos de diseño/normalización. Avisos de alcance, índices y enlaces corregidos. Verificación: cero enlaces locales rotos, once Word íntegros y validador de normalización aprobado con 49 diagramas. El backlog conserva explícitamente su corte original; no es un tablero actualizado de ejecución.

## Revisión de la entrega del segundo parcial (14 de octubre)

Se contrastó el enunciado externo `entregaSegundoParcial.txt` (entrega 22/10) con el árbol de trabajo, contratos, código y evidencia. [Informe de cumplimiento y pendientes](documentation/markdowns/Revision_segundo_parcial.md). Docker es obligatorio para esta entrega, aunque la implementación actual y las guías lo mantienen pendiente. También faltan actualizaciones/pipelines funcionales MongoDB, expediente exhaustivo request/response, reporte integral vigente, evidencia de archivos reales y presentación/YouTube; se debe resolver la interpretación de independencia de la web. Android y escritorio están excluidos expresamente del parcial.

Criterio de aceptación de esta revisión: cubrir los apartados del enunciado, distinguir implementación de evidencia y proponer cierres verificables. Evidencia nueva: 19 pruebas unitarias/contratos/algoritmos aprobadas en 32.95 s, [JUnit](documentation/historial/2026-10-14/resultados/revision-segundo-parcial-unit.xml); once servicios respondieron 200 en readiness, Swagger y OpenAPI usando sus puertos reales, y la página pública del portal respondió 200. Los 164 casos de regresión son evidencia previa, no una nueva ejecución. Se contabilizaron 127 operaciones OpenAPI (107 API y 20 internas). No se cambió código funcional ni se declara terminado el parcial. Riesgo: la evidencia y las pruebas locales actuales no acreditan todavía el futuro despliegue Docker.

## Esquemas físicos PostgreSQL (15 de octubre)

Se añadieron once [esquemas SQL consolidados](data/database/README.md), uno por servicio, generados desde el esquema común y todas las migraciones mediante `scripts/export_schemas.py`. Incluyen 111 tablas y sus índices, restricciones, funciones y disparadores. Las migraciones continúan como fuente ejecutable; los SQL generados son referencias estructurales sin datos, propietarios, permisos ni registros de versiones.

Criterios de aceptación: generación aislada sin leer bases del entorno, restauración de cada SQL en una base vacía y comparación estructural, reproducibilidad y enlaces válidos. La generación y las once restauraciones pasaron con PostgreSQL 14.23; una segunda ejecución con `--check` volvió a restaurar las once bases y confirmó que todos los archivos coinciden. Se verificaron enlaces y análisis estático del generador. No se cambiaron las bases persistentes ni el código de la aplicación. Los diagramas físicos por servicio continúan pendientes; estos archivos no sustituyen el instalador ni sus permisos.

## Validación de la propuesta inicial del esquema compartido

Criterios: preservar tablas y columnas de main salvo dos renombres explícitos; aplicar la ampliación sin eliminar la estructura heredada; importar el SQL resultante en una base vacía; comprobar relaciones, historial y catálogos, y regenerar de forma reproducible. El generador `scripts/build_shared_schema.py` reconstruye el commit fijado más `shared/005_services.sql` en PostgreSQL temporal aislado, sin leer el entorno privado.

Generación y segunda ejecución `--check` aprobadas con SQL idéntico (PostgreSQL 14.23): 45 tablas heredadas, 15 nuevas, 60 restauradas; claves foráneas rechazan huérfanos, traslado exige exactamente una asignación, historial no admite modificaciones, caché incrementa su revisión y existen cinco versiones estructurales/siete perfiles habilitados. Durante la verificación se corrigió una referencia no calificada del disparador de caché y se normalizó la representación de casts de arrays varchar de PostgreSQL 14 al exportar/restaurar. No se cambiaron reglas clínicas ni se ejecutó la aplicación sobre esta base; esa integración sigue pendiente.

## Migración operativa a una base compartida (15 de octubre)

Criterios de aceptación: una sola base PostgreSQL para once conexiones de servicios; conservar contratos JSON/XML, permisos, datos, fechas, auditoría y hashes; integrar referencias entre módulos; instalar desde cero y migrar con respaldo sin sobrescribir el origen; mantener el estado de Monitoreo consultable desde MongoDB cuando falla PostgreSQL.

Implementación: se preservan las 45 tablas de main y se agregan 26, con 50 relaciones adicionales entre módulos. Los esquemas `access_*` contienen vistas y funciones, **cero tablas físicas**. Las colas técnicas comparten tablas con claves delimitadas por servicio. La coordinación entre APIs continúa por HTTP; este cambio no transforma esos flujos en una transacción SQL global. [Detalle de tablas, columnas y límites](documentation/markdowns/Esquema_compartido.md).

Validación del código: el generador restauró y reprodujo el SQL de 71 tablas con `--check`; Ruff y formato aprobados; 40 pruebas del lanzador aprobadas. La [regresión de 171 casos](documentation/historial/2026-10-15/resultados/base-compartida-regresion.xml) obtuvo **169 aprobados y dos fallos 503 en preparación de sesiones web**, en 1158.479 s. Los [dos casos repetidos aisladamente](documentation/historial/2026-10-15/resultados/base-compartida-sesiones.xml) pasaron en 75.04 s. No se presenta esa ejecución completa como libre de fallos: la investigación posterior identificó suspensión del equipo coincidente con ambos fallos (véase diagnóstico más abajo). Pasaron los cuatro flujos de sangre/órganos desde el portal, XML, permisos SQL, rechazo de huérfanos, aislamiento de colas, migración de datos y Monitoreo con PostgreSQL inaccesible. Los tokens del fixture se renuevan entre pruebas cuando vencen; la duración de tokens de producción no cambió.

Migración local: se detuvieron portal, APIs y workers; se exportaron once respaldos y configuraciones privados en `.local/runtime/backups/shared-20261015T174321780766Z/`; se creó `red_house`, se copiaron y compararon 111 tablas/118 428 filas y se publicaron las conexiones. El origen permanece íntegro para recuperación. Los IDs, fechas y contenidos comparados incluyen historiales y versiones; no se recalcularon hashes. El instalador crea directamente la base compartida y el lanzador rechaza entornos antiguos pendientes de convertir.

Verificación posterior: las once credenciales consultaron `current_database() = red_house`, las 71 tablas están en el esquema común y `access_*` no contiene tablas. Once servicios y portal respondieron HTTP 200; conteos funcionales conservados, 18 cadenas de custodia válidas y caché de inventario HIT. Auditoría creció por las consultas de verificación, como corresponde. [Informe sin secretos](documentation/historial/2026-10-15/resultados/base-compartida-entorno.json). Los once respaldos se restauraron en bases desechables y conservaron sus datos al repetir migraciones: [resultado](documentation/historial/2026-10-15/resultados/base-compartida-respaldos.json).

Los respaldos contienen secretos y datos; no se versionan. Volver al origen después de nuevas escrituras requiere reconciliar datos y restaurar también el código/configuración anteriores. La migración ejecutada convierte el entorno de microservicios anterior, no una base poblada arbitraria de main. Windows/WSL, Ubuntu, Docker y GCP no quedan certificados por esta validación local.

## Diagnóstico de los dos 503 (15 de octubre)

Se revisaron código, orden de pruebas, registros del sistema y auditoría del PostgreSQL temporal de la suite fallida. `pmset -g log` registró cierre de tapa (`Clamshell Sleep`) a las 11:24:26, seguido de despertares parciales y nuevas suspensiones. A las 11:27:22 comenzó una suspensión de 73 segundos; los logins de las dos pruebas fallidas están registrados a las **11:27:23.721634 y 11:27:42.763976**, respectivamente. El primero corresponde al login que devolvió 503; el segundo precede al GET de formulario que devolvió 503. La consulta histórica usó exclusivamente el clúster temporal de pruebas, iniciado en modo de lectura y detenido al terminar.

La ejecución sufrió suspensión del equipo, incompatible con probar disponibilidad mediante deadlines de 1 s de conexión y 8 s de lectura HTTP, además de deadlines de dependencias. La atribución anterior a carga era una hipótesis; ahora hay evidencia directa de suspensión coincidente con los fallos. **Límite:** el reporte original no conservó la excepción concreta de cada 503; no puede afirmarse si cada uno agotó HTTP, Redis o PostgreSQL. No se ha cambiado lógica, tiempos de espera ni reintentos para ocultar los fallos.

La nueva ejecución del módulo web completo terminó con **19 aprobados, cero fallos**, en 444.23 s. Registró 1 317 respuestas API, ninguna 5xx, y máximo observado de 1 512.914 ms. La única excepción de conexión web fue la esperada al detener Identidad deliberadamente. [JUnit](documentation/historial/2026-10-15/resultados/diagnostico-503-web.xml) · [Diagnóstico estructurado](documentation/historial/2026-10-15/resultados/diagnostico-503.json). No se declara repetida la suite completa de 171 casos.

Medidas: guía de pruebas actualizada para mantener la tapa abierta; `caffeinate -i` evita inactividad, pero no el cierre de tapa. CI actualizado para conservar logs INFO y captura de fallos JUnit junto al reporte. Criterios de aceptación: localizar los horarios reales, distinguir hechos de inferencias, repetir todo el módulo web y conservar contexto técnico útil para futuros fallos sin publicar secretos. La ejecución remota del CI permanece pendiente.

## Índice CodeGraph (15 de octubre)

Se inicializó CodeGraph 1.6.2 en la raíz mediante `codegraph init --yes .`. El índice local `.codegraph/` contiene 242 archivos, 2 222 nodos y 6 133 relaciones; `codegraph status` confirmó que está actualizado. Se verificó una consulta `codegraph explore 'redhouse.security authenticate'`, que devolvió código y relaciones entre autenticación, API y sesiones web. Criterio de aceptación: índice creado y consultable desde este repositorio. No se modificó lógica de negocio. Para consultar: `codegraph explore "símbolo o pregunta"`; para actualizar tras cambios: `codegraph sync`; para comprobar estado: `codegraph status`. El índice es una ayuda de navegación, no una prueba de funcionamiento ni cobertura exhaustiva del proyecto.

## Mantenimiento

Actualizar el documento vigente de cada tema. Registrar cambios y resultados por entrega en el historial, sin crear un documento nuevo por conversación. Conservar las migraciones y pruebas necesarias; retirar duplicados comprobados. No publicar secretos ni confundir un resultado histórico con una verificación actual.
