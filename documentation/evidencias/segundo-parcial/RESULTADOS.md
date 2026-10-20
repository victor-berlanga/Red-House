# Resultados del segundo parcial

Validación del 19 de octubre de 2026. Aplicación **0.3.0**. La regresión, continuidad Docker, navegador, restauración de respaldos e instalación desde clon limpio están aprobados. Los artefactos técnicos se entregan sin portada ni nombres. Presentación presencial y YouTube corresponden al equipo.

## Condiciones y datos

macOS, Python 3.12 local, Docker Desktop con 8 CPU y 7.75 GiB asignados; imágenes Python 3.13, PostgreSQL 14, Redis 7.4 y MongoDB 8. Datos ficticios y entornos aislados. El entorno habitual `.local/runtime` no se utilizó para las interrupciones. Bucket GCS privado real autorizado; credenciales fuera del expediente.

## Resultado esperado y obtenido

| Criterio | Esperado | Obtenido | Evidencia |
| --- | --- | --- | --- |
| Regresión final | Flujos, seguridad, contratos, concurrencia y persistencia correctos | **182 aprobadas**, cero fallos y cero omisiones; **2005.90 s** | [JUnit](regresion-final.xml), [salida](regresion-final.txt) |
| Salud complementaria | Negociación inválida 406; dependencia inaccesible 503 y recuperación 200 | **Una prueba adicional aprobada**, **36.08 s**, para los once propietarios | [JUnit](salud-complementaria.xml), [salida](salud-complementaria.txt) |
| Sangre por API Docker | Reserva única, traslado, solicitud cerrada y recurso recibido | Aprobado con comprobación SQL y custodia | [Nueve controles Docker](docker-release/docker-results.json) |
| Órganos y JSON/XML sin réplicas A | Flujo completo y consultas de los once servicios mediante B, incluida Identidad | Aprobado | [Intercambios Docker](docker-release/docker-http.json) |
| Web sin las 22 API | Sangre y órganos de principio a fin mediante backend propio | Ambos aprobados; restauración posterior completada | [Docker final](docker-release/docker-results.json) |
| Todas las autoridades API detenidas | Informar indisponibilidad sin eludir seguridad | Gateway **502** | [Docker final](docker-release/docker-results.json) |
| Actualización gradual | Sustituir A y B por imagen compatible conservando operaciones | IDs de imagen distintos; **100 consultas continuas, todas 200**; alta y consulta SQL después de cada sustitución | [Imágenes y resultados](docker-release/docker-results.json) |
| Reinicio de almacenes | Conservar datos y recuperar consultas autorizadas | Mismo ID, folio, estado y versión SQL; JSON/XML recuperados tras reiniciar PostgreSQL, Redis y MongoDB | [Comparación antes/después](docker-release/docker-results.json) |
| GCS real | Carga privada, descarga/hash, permisos, validación y recuperación | Web 303; descarga 200/hash idéntico; anónimo 403; inválido 422; ausente 404; expirado **400 ExpiredToken**; dependencia 503 y recuperación 200 | [Resultado GCS](gcs-real.json), [configuración de bucket](gcs-bucket.json) |
| Proyección MongoDB | Actualizar sin modificar eventos, deduplicar, ordenar, reconstruir e indexar | Versión 3; seis eventos reproducidos; duplicados/reconstrucción sin cambios; actualización de evento denegada; **IXSCAN regional_state**, tres claves/documentos examinados | [Resultado y explain](mongo-projection.json) |
| Navegador | Páginas autorizadas, gráficas reales, adaptación móvil, archivo y Swagger | **20 páginas, siete perfiles**, sin errores JavaScript; valores y etiquetas Highcharts coinciden; ancho 390 sin desbordamiento; carga VERIFIED y Swagger 200 | [Informe](browser/browser-results.json), [archivo](browser/gcs-web-verified.png), [Swagger ejecutado](browser/swagger-executed.png) |
| HTTP por endpoint | Solicitudes reales, errores aplicables, persistencia y captura | **284/284 con HTTP exitoso; 240 con error**; 44 rutas de documentación fija con justificación de no aplicabilidad; ninguna escritura capturada sin comprobación | [Visor](http/index.html), [cobertura](http/coverage.json), 284 capturas de endpoints y una del inventario |
| Respaldo y restauración aislada | Igualdad de datos, roles y estado temporal | **71 tablas / 15 122 filas SQL**, **7 632 documentos MongoDB**, cinco usuarios y cuatro roles documentales idénticos por conteo/hash; clave Redis restaurada con **TTL 3575 s** | [Comparación completa](backup-restore.json) |
| Instalación desde clon limpio | Secretos nuevos, esquema y volúmenes propios, arranque, negocio y bootstrap repetible | **Ocho etapas aprobadas**; 27 contenedores saludables; sangre por API, consultas JSON/XML de once propietarios y segunda ejecución de bootstrap | [Informe](clean-clone.json), [estado](clean-clone-start.json), [HTTP real](clean-clone-http.json) |

Los 182 casos pertenecen a una sola ejecución completa. La prueba de salud se agregó y ejecutó después, sin cambiar código de aplicación; se informa por separado. Las nueve comprobaciones Docker y los recorridos de navegador tampoco se suman como casos de esa regresión.

La prueba complementaria de salud dirige temporalmente cada dependencia a un puerto local cerrado. Los handlers intentan conexiones reales y se verifican sus respuestas HTTP y su recuperación; no se fabrican respuestas del adaptador. Los ensayos de reinicio Docker sí reinician los motores completos.

## Fallos conservados y correcciones

- La primera suite completa del 19/10 obtuvo 176 aprobados y un fallo GCS: autenticación/firma podían esperar sin límite explícito. Se acotaron esos RPC; la regresión final con GCS aprobó. No se amplió el timeout de las pruebas.
- Una aserción inicial esperaba 403 para URL expirada. GCS devuelve `400 ExpiredToken`; se ajustó al contrato documentado manteniendo la comprobación exacta del código XML. [Contrato XML GCS](https://docs.cloud.google.com/storage/docs/xml-api/reference-status).
- La captura optativa de archivos estáticos intentaba consumir `send_file` en modo streaming. Ahora materializa la respuesta solo cuando se solicita evidencia; la ejecución HTTP de todas las rutas pasó.
- Las primeras pruebas Docker encontraron directorios temporales Nginx incompatibles con raíz de solo lectura y carga tardía de configuración web privada. Se corrigieron y se repitieron los flujos.
- Las conexiones SQL costosas bajo carga motivaron pools acotados por aplicación, credencial y esquema. La regresión verifica reutilización, rollback, aislamiento y recuperación sin repetición automática de escrituras. [Pool Psycopg](https://www.psycopg.org/psycopg3/docs/advanced/pool.html).
- Un primer 504 durante la caída de réplicas permanece registrado. No se atribuye una causa única sin evidencia suficiente. Las repeticiones y el ensayo final completaron los procesos previstos.
- Restaurar muchas instancias simultáneamente agotó salud bajo carga del host superior a 300. Se ordenó el arranque por pares, consumidores primero. El sondeo mínimo conservó verificación HTTP y del worker, sin ampliar los 8 s del health check. La ejecución final completó ambas restauraciones.
- La restauración final de las 22 API incluyó suspensión del equipo: cierre de tapa a las **11:24:40** y apertura a las **12:16:02**. El [registro de energía](docker-release/host-suspension.json) distingue esa pausa; la duración de pared de la fase no mide RTO ni latencia. Los escenarios de negocio anteriores y actualización/reinicio posteriores terminaron con el equipo despierto.
- El capturador de navegador primero consultó una columna inexistente y después eligió un traslado cerrado. Se corrigió la consulta y se preparó un traslado abierto mediante API. La aplicación correctamente impide cargar nuevas evidencias fuera del periodo autorizado. [Incidente y repetición](browser-incidents.json).
- El ensayo de respaldo detectó escapado incorrecto del script embebido, pérdida de autenticación al restaurar MongoDB `admin` junto con índices, y orden variable en el agregado SQL. La restauración ahora separa credenciales y datos con nueva autenticación; compara SQL ordenado por tabla y verifica hashes de usuarios/roles. [Incidentes](backup-incidents.json), [comportamiento mongorestore](https://www.mongodb.com/docs/database-tools/mongorestore/).
- La primera selección del clon rechazó el marcador versionado `.codegraph/.gitignore`. Se permitió únicamente ese archivo de configuración, conservando el rechazo de secretos y cachés. [Diagnóstico](clean-clone-incidents.json).

- El primer intento de instalación del clon quedó detenido al fallar DNS de Docker Hub. Se comprobó después la resolución desde host y contenedor; otra instalación completa, con proyecto y volúmenes nuevos, aprobó. [Fallo conservado](clean-clone-dns-failure.json), [repetición aprobada](clean-clone.json).

Los [metadatos de regresiones intermedias](regresiones-intermedias.json) conservan fechas, hashes y fallos anteriores. Los informes Docker intermedios permanecen en sus carpetas; el cierre usa `docker-release`, no borra ni reetiqueta sus predecesores.

## Alcance y límites de la evidencia

El inventario se obtiene de rutas reales y excluye los métodos automáticos HEAD/OPTIONS. Cada método y ruta tiene su propia página, éxito, error cuando aplica, headers redactados, fecha, versión, correlación y huella de implementación. Los cuerpos completos quedan enlazados. Las capturas del visor corresponden a intercambios ejecutados; los ejemplos Swagger se distinguen de esa evidencia. El expediente separa HTTP, WSGI y llamadas modulares.

Las escrituras conservan consultas posteriores a idempotencia, operación, inbox o sesión SQL/Redis. Recibir un 200 por sí solo no se usa como prueba de persistencia. Las 44 rutas GET de documentación fija no reciben datos de negocio; se explica por qué no se fabrica un error de dominio para ellas.

La restauración compara datos con las aplicaciones pausadas y usa tres contenedores nuevos sin puertos publicados. Los archivos privados de respaldo incluyen configuración y claves. El objeto ficticio del navegador permanece en el bucket para demostración; el respaldo local no copia objetos GCS y su recuperación requiere conservar las generaciones referenciadas. Los objetos creados por la prueba automatizada GCS se eliminaron en su limpieza.

No se certifican carga productiva, migraciones futuras incompatibles, GCE/HTTPS público, alta disponibilidad de almacenes/host, validez clínica, presentación presencial ni publicación de YouTube. Las mediciones históricas de carga se conservan con su fecha y no se atribuyen a 0.3.0.

## Estado al entregar

Los contenedores de demostración, restauración y clones de prueba quedan detenidos; sus volúmenes y respaldos privados se conservan. Para recuperar el Compose principal desde la raíz: `python3 deployment/start.py`. El entorno habitual `.local/runtime` se mantiene separado. Los 630 archivos de aplicación/despliegue comparados coinciden con la instantánea del clon; los hashes de los once servicios coinciden con la regresión final. [Verificación de fuentes](source-validation.json).
