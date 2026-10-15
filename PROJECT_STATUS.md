# Estado vigente de Red House

Actualizado: **15 de octubre de 2026**. Leer junto con `AGENTS.md` y el [índice documental](documentation/README.md). El historial detallado está separado del estado actual.

## Decisión de arquitectura (15 de octubre)

Por indicación del usuario se implementa una base PostgreSQL compartida por todos los servicios, como Bookstore. El [nuevo esquema compartido](data/database/schema.sql) deriva de main local `44eeaf90c445b4d9564c2f0ab2dd3167f0296418` y conserva sus 45 tablas, agregando 26 (71 en total) tras adaptar los contratos ejecutables. La propuesta inicial de 60 tablas quedó ampliada. [Cambios y correspondencia por servicio](documentation/markdowns/Esquema_compartido.md). La base inicial de main tiene 23 tablas y sus migraciones 002–004 agregan 22; las menciones previas a 46 no coinciden con ese SQL fijado.

**Implementado y aplicado al entorno local:** instalador, acceso SQL, colas y migrador utilizan `red_house`, con tablas físicas compartidas y vistas de permisos por servicio. La conversión verificó **111 tablas de origen y 118 428 filas sin diferencias** antes de publicar conexiones. Las once bases antiguas y sus respaldos privados permanecen conservados; las aplicaciones ya no las utilizan. Los SQL por servicio quedan como referencia del origen.

## Sistema actual

- `apps/web/`: portal Flask/Jinja2 que consume HTTP. El backend SQL histórico y sus instaladores fueron retirados; no hay doble escritura ni fallback local.
- `apps/services/`: diez microservicios y Monitoreo, con contratos JSON/XML, JWT, Redis, PostgreSQL y MongoDB.
- PostgreSQL conserva una base operativa compartida, `red_house`, con 71 tablas y credenciales separadas por servicio. MongoDB conserva documentos/proyecciones; Redis mantiene sesiones y datos temporales. La web conserva sesiones técnicas cifradas en SQLite privado.
- La carga regional es ficticia, pero sus operaciones y almacenamiento son reales. No se reinicializa al arrancar. Las reglas de compatibilidad y priorización no sustituyen la revisión médica.
- Android, escritorio, Docker y GCP permanecen en una etapa posterior; no se eligieron nuevas tecnologías cliente.

## Operación

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
- Agenda por sede/hora, recuperación de acceso, email/push y administración institucional definitiva.
- Bucket GCS real, archivos grandes, firmas y fallos de nube.
- Android, escritorio XML, contenedores, HTTPS, GCP, supervisión y operación productiva.
- Carga sostenida, saturación, alta disponibilidad y ejecución de CI remoto. Windows/WSL y Ubuntu completos no están certificados por las pruebas de este Mac.
- Diagrama físico de la base compartida y nueva edición del reporte integral Word/PDF para el sistema integrado. Los modelos 0FN–4FN y las once ediciones Word de planificación siguen siendo referencias del semestre; el reporte del monolito permanece como antecedente.

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
