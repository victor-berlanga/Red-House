# Optimización local de Red House — 11–12/11/2026

Publicación posterior: el 12/11/2026 se desplegó el incremento de servidor y se verificó en GCP. [Expediente de publicación](../../gcp/optimization-20261112/RESULTADOS.md). Este informe conserva las condiciones y resultados del laboratorio previo; no acredita actualización de dispositivos móviles.

Se implementaron once archivos de producción pequeños, con comparación de consultas de monitoreo, disponibilidad por lote, sondeo de sesión, scripts innecesarios, concesiones WSS y CPU de parseo móvil. Se conserva la arquitectura y no se publicó nada. **El encargo OPT-01…OPT-12 permanece parcial**: la [matriz](../../../entrega-final/optimizacion/Matriz.md) distingue incrementos probados, objetivos no medidos y trabajo pendiente.

## Base y condiciones

Base Git `9ab04c45699bac945601902694eb76f906f6fcd1`. [baseline.json](baseline.json) registra hashes iniciales y cambios previos: `PROJECT_STATUS.md`, diagnóstico de mantenimiento y prompt de optimización; se conservaron. [scope-check.json](scope-check.json) compara fuentes/dependencias/configuración con esa base de trabajo. No hubo cambios de versiones, frameworks, esquemas PostgreSQL, contratos, endpoints públicos, servicios, Redis, GCP ni permisos clínicos. El único índice nuevo pertenece a MongoDB/Monitoreo.

Laboratorio desechable con datos ficticios: macOS 15.7.9 x86_64, Python 3.12.6, PostgreSQL 14.23, MongoDB 8.0.17, Redis 8.10.2; versiones Python y límites en [environment.json](environment.json). PostgreSQL conserva statement_timeout 5000 ms, lock_timeout 3000 ms y pool 0 en el fixture; Redis conserva noeviction y appendfsync always. Se arrancaron procesos y listeners locales, sin Docker ni datos productivos. No se verificó configuración desplegada.

Las variantes de cada comparación comparten datos, código de validación, identidad y límites. SQL/sesión usan un calentamiento y 12 muestras por variante; Mongo uno y cinco; CPU JVM dos y 20, con orden intercalado AB/BA y el mismo cliente/payload. Los tiempos SQL incluyen la consulta y materialización en el proceso de prueba. Son mediciones locales con cachés del motor calientes, no un ensayo de caché fría, carga sostenida ni SLA. Se publican muestras y medianas; cinco o doce observaciones no justifican p95/p99 de rendimiento. No se comparan cifras entre ejecuciones diferentes.

El volumen histórico reproduce el orden de magnitud del diagnóstico, no una copia de producción: 786.085 filas SQL y 786.084 documentos, distribuidos entre doce servicios sintéticos. El incidente GCP estimaba 786.081 filas; su timeout histórico no se usa como tiempo «antes» de este laboratorio. [Diagnóstico previo](../../mantenimiento/monitoreo-503-20261111/RESULTADOS.md).

## Coste observado

| Tarea y unidad | Antes | Después | Evidencia y alcance |
|---|---:|---:|---|
| Última muestra SQL, mediana ms | 353,607 | 1,014 | [monitor-sql.json](monitor-sql.json), 786.085 filas/12 servicios, igualdad exacta |
| Última muestra Mongo, mediana ms | 1179,803 | 7,099 | [monitor-mongo.json](monitor-mongo.json), 786.084 documentos/12 servicios |
| Enriquecer 20 horarios, ms / consultas | 3,890 / 20 | 0,533 / 1 | [slots.json](slots.json), tablas temporales PostgreSQL reales |
| Enriquecer 100 horarios, ms / consultas | 18,979 / 100 | 1,418 / 1 | Mismos conteos y orden que detalle |
| Enriquecer un horario, ms / consultas | 0,371 / 1 | 0,401 / 1 | Pequeño sobrecoste; no se declara mejora en ese tamaño |
| Sondeo de sesión, mediana ms | 117,189 | 58,251 | [session-poll.json](session-poll.json), catálogo de etiquetas frío en cada petición |
| Llamadas de catálogo en 12 sondeos + calentamiento | 13 | 0 | Autenticación durable/Redis/revocación permanece |
| Scripts de gráficas en panel sin gráficas | 3 | 0 | [dashboard-assets.json](dashboard-assets.json), HTML autenticado de donante |
| Bytes originales de esos scripts | 416.345 | 0 | No son bytes gzip/transferidos ni medición de LCP |
| Renovaciones de concesión Redis en 20 heartbeats | 42 | 2 | [antes](tracking-leases-before.json), [después](tracking-leases-after.json), WSS real sin suscripciones |
| Autorizaciones en esa misma ráfaga WSS | 22 | 22 | Sin reducción del control de seguridad |
| CPU del hilo llamador JVM, mediana ms | 49,444 | 21,506 | [parsing-cpu.json](parsing-cpu.json), payload de 895.882 bytes, MockEngine/hilo sintético |
| Guardar observación durante HTTP simulado de 250 ms, mediana ms | 256,824 | 0,730 | [antes](queue-enqueue-before.json), [después](queue-enqueue-after.json), JVM/almacén en memoria, un calentamiento y cinco muestras |

El tiempo de la única ráfaga WSS no acredita una mejora estadística de latencia. La reducción comprobada es de llamadas lease, no del total de comandos Redis ni de consultas SQL. `/monitoreo` respondió 200 con las API independientes detenidas: mediana 258,078 ms en cinco aperturas mediante Flask test client, sin navegador ni comparación temporal anterior. [monolith-monitor.json](monolith-monitor.json).

## Cambios y criterios conservados

**Monitoreo.** `servicio_monitoreo/routes.py` obtiene las claves reales de servicio mediante búsquedas B-tree y una fila por clave. No limita a servicios configurados ni a muestras de 24 horas. El plan anterior procesó 786.085 filas; el nuevo entrega doce, con búsquedas indexadas de una clave y aproximadamente dos filas por búsqueda del último registro. Usa los índices existentes sobre la tabla física `red_house.service_health_check`, accesible mediante `checks`; no se añadió índice PostgreSQL. Conserva el desempate `created_at DESC,id`, estados antiguos degradados, roles y estadísticas.

MongoDB avanza por servicio con `find_one` ordenado. El plan de una búsqueda examinó una clave y un documento; doce servicios requieren trece búsquedas contando el final. Se conserva toda la historia. El índice parcial `monitor_latest(service, checked_at DESC, event_id)` ocupa **51.466.240 bytes** adicionales en esta distribución y tardó **3320,309 ms** en construirse. No se midió su coste de escritura continuo: debe medirse antes de aceptar el incremento completo. El migrador documental existente lo crea explícitamente; los lectores no reciben permisos nuevos.

La primera alternativa Mongo —índice seguido de sort/group con primer documento completo— resultó peor: 2986,150 frente a 4877,940 ms en su propia ejecución. Fue descartada, no es la implementación final. [Datos](monitor-mongo-rejected.json), [fallo](monitor-mongo-rejected.log). En el JSON final, `plans.rejected_group` identifica ese tipo de plan y `seek_plan` corresponde a la búsqueda implementada; se corrigió la etiqueta original `plans.after` sin alterar muestras. El desempate Mongo antes era indeterminado para fechas iguales; ahora usa event_id. Falta un caso documental dedicado con empate; SQL sí lo prueba.

**Agenda.** `ms_donantes/agenda.py` agrega occupied/attended únicamente para los IDs de la página ya autorizada. Rellena cero, conserva orden y available limitado a cero. No modifica reservas, bloqueos, cancelaciones ni confirmaciones. La prueba compara 1/20/100 filas con la función original de detalle. El N+1 de enriquecimiento web de citas sigue pendiente.

**Caché y sesión.** `redhouse/cache.py` captura exclusivamente `redis_unavailable` del GET/SET opcional; errores de autorización, auditoría y fuente siguen propagándose. Claves, revisión transaccional, ámbito y TTL no cambian. Se inyectaron fallos selectivos de caché y autorización: estos casos son dobles de fallo sobre una fuente real, no una caída real de todo Redis. La regresión WSS sí detiene Redis real en un laboratorio aislado. `/sesion/estado` omite etiquetas solo después de autenticar y conserva no-store, respuesta mínima y revocación real.

**Presentación y WSS.** Highcharts, accesibilidad y charts.js solo se incluyen cuando hay charts/metrics. No se retiraron tablas o funciones de gráficas. Las concesiones WSS se renuevan cada 10 s manteniendo vigencia de 40 s y TTL de clave de 45 s; cada iteración mantiene autorización. Se probó renovación después de 10 s con socket abierto. Snapshot y bloqueo SQL por suscripción todavía ocurren cada 0,5 s; no se declara optimizado el trabajo de datos multiespectador.

**Móvil.** El parseo y validación JSON pasan a Dispatchers.Default, manteniendo límites, errores y contratos; la medida cuantifica CPU del llamador, no CPU total, latencia de red ni frames. Se conserva también [el ensayo secuencial previo](parsing-cpu-sequential.json), reemplazado para la conclusión por la comparación intercalada que reduce sesgo de calentamiento JVM. App cierra clientes descartados tras errores de restauración/login, reemplazo y salida de composición. TransportScreen reutiliza la imagen decodificada para los mismos bytes. Estos dos últimos cambios están compilados, pero no tienen medición de memoria ni captura física. No cambia archivo, hash, GPS, cifrado o permisos.

**Sincronización móvil.** ObservationQueue mantiene un mutex de envío por proceso y usa el mutex de almacenamiento solo al seleccionar/persistir y confirmar. El estado SENDING, ID y cuerpo quedan guardados antes de HTTP. La confirmación relee el archivo y actualiza únicamente el mismo comando/propietario todavía presente, conservando observaciones añadidas durante la espera. Si un GET devuelve 404, se comprueba que el pendiente sigue presente y la identidad no cambió antes de iniciar el POST. Una operación ya enviada puede haber confirmado en servidor aunque el usuario borre su estado local: borrar o cancelar la espera no revierte el commit.

Una respuesta perdida o una escritura local final fallida dejan SENDING recuperable mediante GET, sin inventar éxito. Se conservan máximo de 100 registros, 24 horas, cinco intentos automáticos, backoff, cifrado/atomicidad del adaptador y contrato de idempotencia. La revisión observable solo contiene un contador; no contiene credenciales o datos de negocio. TransportScreen actualiza estados a partir de ese contador y ya no ejecuta su propio ciclo de sincronización de 30 s. App y los workers existentes siguen coordinados por el mutex de envío del proceso.

Las pruebas usan HTTP y SecureStore dobles: guardar mientras hay una espera de 250 ms conserva ambos comandos; dos ejecutores hacen un solo POST; cancelación después del commit recupera con GET; borrar/cambiar cuenta durante GET no inicia el comando retirado ni sobrescribe la cola nueva; un fallo de escritura final conserva recuperación. No son pruebas de cierre de proceso nativo, disco cifrado o varios procesos independientes. Releer al confirmar añade trabajo de almacenamiento para evitar pérdida de actualizaciones; no se afirma que haya menos lecturas/cifrado. Los primeros tests nuevos fallaron por firma JUnit y tipos de aserción; se corrigió únicamente el arnés, con [logs](queue-baseline-attempt1.log) y [compilación fallida](queue-build-attempt1.log) conservados. La [línea base](queue-baseline2.log) se ejecutó antes de modificar ObservationQueue; su [fuente anterior](before-ObservationQueue.kt) permite reconstruir ese ensayo en una copia aislada. `OPT_QUEUE_BASELINE=1` etiqueta la medición, no restaura fuentes.

## Pruebas y resultados

**46 casos backend únicos con último resultado aprobado**, según [backend-tests.json](backend-tests.json). La unión usa classname/name; no suma repeticiones como casos nuevos:

- [optimization.xml](optimization.xml): siete casos aprobados, incluyendo equivalencia con volumen, sondeo/revocación, assets, caída real SQL/Mongo, recuperación y monolito autónomo.
- [regression.xml](regression.xml): 24 casos aprobados; tres se solapan con optimization. Incluye agenda JSON/XML, competencia por último cupo, autorización/CSRF/sesiones, paneles y caché/invalidation.
- [tracking-attempt1.xml](tracking-attempt1.xml): 19 casos, 16 aprobados y tres fallidos. Incluye WSS/TLS, replay, JSON/XML/XXE, concurrencia, dispositivos/revocación, custodia/sync y dos procesos WSS con caída parcial/total.
- [tracking-recheck.xml](tracking-recheck.xml): cuatro aprobados; repite los tres fallos y amplía el mismo caso de concesiones con renovación después de 10 s. El fallo selectivo SET de caché está en el informe tracking inicial y pasó.

Los fallos iniciales WSS fueron dos ConnectionTimeout/503 y un 401 inesperado en un caso de custodia. Pasaron en laboratorio nuevo sin cambiar código productivo, límites, permisos o expectativas. **No se demostró su causa**: no se etiquetan automáticamente como fallos del arnés. Se conservan [log inicial](tracking-attempt1.log) y [repetición](tracking-recheck.log). El resultado no acredita estabilidad bajo carga sostenida.

En el primer ensayo de caídas, el arnés comprobaba procesos ya detenidos al esperar recuperación; se corrigió su inventario de procesos. Ese fallo produjo también una redirección posterior del monolito. [Intento conservado](optimization-attempt1.log), [repetición aprobada](optimization-final.log). Los primeros intentos de pytest/Gradle dentro del sandbox no pudieron abrir sockets locales; se repitieron con acceso autorizado al laboratorio. Un error de sintaxis del test JVM se corrigió antes del build aprobado. Los logs anteriores permanecen en esta carpeta.

**Móvil: 29 casos JVM, 27 aprobados y dos omitidos** porque requieren `REDHOUSE_MOBILE_LAB`; [JUnit](mobile-tests/), [ejecución final](queue-final2.log). No se cuentan esas omisiones como pruebas reales de microservicios desde Kotlin. Android APK debug y Kotlin/iOS arm64 compilaron [sin descargas](queue-final2.log). [Artefacto y SHA-256](mobile-artifacts.json): APK de 14.094.917 bytes, `3373f7584086ce322eb2451a432c37849cc5c8a3f26939be1ae5272da782a95a`. No se enlazó/firmó/instaló una app iOS nueva en este incremento.

El iPhone 16 Pro aparece `unavailable`; adb no lista dispositivos. [Comprobación](devices.json). No se descargó runtime Simulator. Compilación arm64, JVM y vistas renderizadas no acreditan fluidez, batería, memoria física, accesibilidad ni tareas Android/iOS completas.

Los dos archivos Python nuevos pasan Ruff. La [comparación con HEAD](lint-comparison.json) de todos los Python modificados detecta cero diagnósticos introducidos y 30 preexistentes en ese conjunto/configuración; no se afirma que el repositorio esté libre de lint. `git diff --check` y comprobación reversible del parche aprobadas.

## Reproducción

Desde la raíz, con binarios/dependencias existentes y acceso a puertos locales. No usar rutas o credenciales de producción. Cada invocación pytest crea su propio entorno temporal. `OPTIMIZATION_EVIDENCE` debe apuntar a una carpeta nueva para conservar este expediente.

```sh
OPTIMIZATION_EVIDENCE=/tmp/redhouse-optimization-repeat \
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
apps/services/.venv/bin/pytest apps/services/tests/test_optimization.py \
  -q --tb=short --junitxml=/tmp/redhouse-optimization-repeat.xml

REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
apps/services/.venv/bin/pytest apps/services/tests/test_final_operations.py \
  apps/services/tests/test_web_sessions.py apps/services/tests/test_ui_cache.py \
  apps/services/tests/test_final_tracking.py apps/services/tests/test_optimization_tracking.py \
  -q --tb=short --junitxml=/tmp/redhouse-regression-repeat.xml

OPTIMIZATION_MOBILE_EVIDENCE=/tmp/redhouse-optimization-repeat \
GRADLE_USER_HOME=/private/tmp/redhouse-gradle-home \
JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home \
./apps/mobile/gradlew -p apps/mobile :composeApp:testDebugUnitTest \
  :composeApp:assembleDebug :composeApp:compileKotlinIosArm64 \
  --offline --max-workers=2
```

El directorio de evidencia móvil debe existir. Rutas SDK/JDK/Mongo corresponden al equipo ensayado; no autorizan instalar versiones nuevas. Las pruebas web reconstruyen únicamente el hook/template anterior revisado, conservado en [before-identify.py](before-identify.py) y [before-dashboard.html](before-dashboard.html). SQL y horarios mantienen el oráculo anterior explícito. El test WSS no restaura código: `OPT_TRACKING_BASELINE=1` solo etiqueta la medición; para reproducir el antes se requiere una copia aislada de las fuentes anteriores con el test actual. No activar esa variable sobre el código nuevo para fabricar una línea base.

## Preparación y reversión

[production.patch](production.patch) contiene exclusivamente los once archivos productivos modificados; excluye cambios previos, documentación y tests. Se comprobó `git apply --reverse --check` contra el árbol actual, sin ejecutar la reversión. En una copia de revisión se puede aplicar inversamente para reconstruir las fuentes previas. No usar reset/checkout global ni sobrescribir cambios posteriores. Reversión futura de aplicación requiere reconstruir las imágenes/APK con fuentes anteriores y conservar configuración/secretos del entorno.

El índice Mongo se prepara mediante el migrador existente antes de activar el código nuevo:

```sh
apps/services/.venv/bin/python apps/services/scripts/migrate_documents.py \
  --directory /ruta/al/laboratorio-aislado
```

Ese directorio contiene el state privado del laboratorio; no se copia al expediente. La provisión de cada fixture ejecutó el migrador. El índice es aditivo, sin modificar documentos; la consulta previa sigue funcionando con él. Rollback de aplicación puede dejar el índice: no requiere borrar historia ni revertir escrituras. Una eventual eliminación de `monitor_latest` debe ser una operación separada del propietario después de retirar lectores nuevos. Este documento no ejecuta migración/publicación en GCP.

No hay ampliación de contratos ni cambios de Redis/durabilidad. Falta medir tasa de inserción, tamaño bajo otra distribución, bloqueo durante construcción y presupuesto antes de despliegue. La corrección local no certifica que el 503 productivo esté resuelto.

## Pendientes explícitos

La matriz conserva dueño y acción para listados profundos, enriquecimiento web de citas, evaluaciones, sondeo SQL WSS, estampidas/memoria Redis, paneles/varias pestañas, fingerprint/gzip efectivos, cargas/paginación móvil, disco/cifrado/cámara, sincronización y outbox/pools. Son trabajo técnico pendiente, no impedimentos externos inventados. No se introdujeron concesiones durables o cachés adicionales sin medición y prueba de recuperación. El candidato Mongo sort/group sí fue descartado por evidencia negativa; los otros objetivos no medidos no se confunden con él.

Las pruebas físicas necesitan dispositivo disponible; GCS/proveedores conservan sus autorizaciones y pendientes previos. No se cerró CONT-01…CONT-10 ni WEB/MOV/TRACK por este incremento. No hubo despliegue, reinicio productivo, cambio de datos reales ni nuevas dependencias.

## Referencias técnicas

Interpretación de planes y límites: [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html). La elección SQL se apoya en el plan ejecutado de PostgreSQL 14.23. El descarte de la agregación se basó en explain real, no en suponer una optimización de grupo: [MongoDB aggregation optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/). Contexto de coroutines y propiedad del cliente: [Android coroutines](https://developer.android.com/kotlin/coroutines/coroutines-best-practices), [Ktor HttpClient](https://ktor.io/docs/client-create-and-configure.html). Estas referencias no sustituyen mediciones ni autorizan actualizar versiones.
