> Evidencia histórica del 7 de octubre. [Corte vigente](../../markdowns/Pruebas_y_validacion.md). Las cifras de esta página no describen pruebas nuevas.

# Verificación del módulo de microservicios — 2026-10-07

Versión 0.1.0, Python 3.12.6, macOS Intel, PostgreSQL 14.23, Redis Server 8.10.2 y MongoDB Community 8.0.17. Las dependencias Python exactas están en `requirements-verified.txt`. Las pruebas usan bases y procesos aislados. El primer corte no modificó el monolito; el siguiente autorizó su integración por API y una nueva PRUEBA, conservando su base anterior como referencia sin cambios de negocio.

## Corte de integración web

**Regresión completa actual: 78 pruebas aprobadas, cero fallos, errores u omisiones, en 505.66 s.** [JUnit](../integracion/resultados/integrated-junit.xml). Incluye los 59 casos originales y 19 casos web nuevos; no se suman repeticiones. La duración refleja ejecución local con varias comprobaciones concurrentes y no mide latencia de producción.

`tests/test_web_integration.py` ejecuta la web real contra once servidores HTTP y PostgreSQL/Redis/MongoDB reales. Prohíbe el acceso SQL histórico en fixture y configura su conexión anterior como inaccesible. Comprueba siete perfiles, sangre y riñón/hígado/corazón hasta aceptación/cierre/XML, donante/campaña/cita/donación/procesamiento/procedencia, matching sin reservas, alta/desactivación de usuario y revocación, CSRF, captura rechazada/idempotencia, filtros/CSV/segregación, tokens cifrados, renovación/logout y caída/recuperación de Identidad con 503 seguro. La suite final pasó después de corregir selección de la campaña recién creada y la entrada de versión en el formulario de desactivación; las ejecuciones fallidas no se presentan como aprobadas.

**Regresión del modo SQL histórico: 121 aprobadas, ocho omitidas, sin fallos/errores, en 120.60 s.** [JUnit](../integracion/resultados/legacy-regression.xml). `scripts/check_legacy_web.py` utiliza bases PostgreSQL aleatorias en el clúster aislado y fuerza `BACKEND_MODE=local`. Las ocho omisiones son sus recorridos de navegador que requieren `--browser`; no se ejecutaron en ese corte. El navegador del nuevo portal se comprobó separadamente, sin contar esas ocho como aprobadas.

**Chrome real: 27 páginas**, escritorio 1440 × 1000 y móvil 390 × 844, cero errores JavaScript, cero fallos de recursos estáticos y sin desbordamiento del documento. Highcharts con datos reales, filtros, formularios, siete perfiles, administrador rechazado en inventario y apertura del menú móvil. [Informe y ocho capturas](../integracion/capturas-integracion/README.md), reproducibles mediante `apps/web/tests/integrated_browser.cjs`.

**PRUEBA comprobada en lectura:** seis instituciones ficticias, 108 donantes, 36 donaciones, 12 campañas, 36 citas, 72 receptores y 72 solicitudes, 216 unidades sanguíneas y 36 ofertas de órganos, 18 traslados con tres por estado. Se recomputaron y verificaron las 18 cadenas SHA-256 y secuencias; se compararon los ocho hashes y roles copiados contra la base anterior en transacción de solo lectura. Once readiness y liveness web HTTP 200, disponibilidad `X-Cache: HIT` y límites restaurados a 180 peticiones/minuto. [Informe](../integracion/resultados/integrated-environment.json), reproducible con `scripts/check_integrated.py`. El número de auditorías/avisos del informe es una observación puntual y crece con consultas y acciones.

OpenAPI estático validado en las once unidades y 36 XSD de solicitud compilados después de agregar los contratos de consulta. [Guía de integración y reproducción](../../../apps/web/README.md). Los datos de las pruebas aisladas no se suman a la carga visual.

## Criterios y evidencia

| Criterio | Comprobación | Evidencia |
| --- | --- | --- |
| Diez servicios y monitoreo ejecutables | Once fábricas Flask, procesos HTTP individuales y workers; endpoints de salud y Swagger por unidad | Código por carpeta y prueba parametrizada para las once unidades |
| Persistencia y comunicación reales | PostgreSQL, Redis y MongoDB con autenticación; llamadas HTTP entre servicios | Fixture `tests/conftest.py`, `scripts/local.py` |
| Tres procesos de negocio | Donante/campaña/cita/dictamen; sangre hasta recepción; órganos hasta recepción | `test_flows.py` y `test_catalogue.py`; riñón, hígado y corazón |
| Sin doble asignación | Un recurso/dos solicitudes; dos recursos/solicitud de uno; reservas idempotentes | `test_flows.py` |
| Cobertura y cierre consistentes | Dos recepciones concurrentes cierran solicitud una vez | `test_resilience.py` |
| JWT y sesión | Alg:none, HS256 inesperado, emisor/audiencia, expiración, claims, renovación, reutilización, logout y desactivación | `test_security_contracts.py` |
| Segregación y mínimo privilegio | Institución, rol, asignación, bases distintas, Redis con ACL y permisos versionados | `test_security_contracts.py` |
| Contratos seguros | JSON/XML equivalentes, XSD, XXE, campos/nulos/tipos inválidos, controles NUL, media types y errores | `test_security_contracts.py`; contratos estáticos por servicio |
| Fallos y recuperación | PostgreSQL/Redis/MongoDB detenidos, Custodia caída, respuesta perdida, rollback local y compensación | `test_resilience.py` |
| Algoritmo no trivial | Matching máximo frente a un oráculo exhaustivo para los 512 grafos 3×3; propuestas sin reservas | `test_algorithms.py`, `test_catalogue.py` |
| Monitoreo | Caída, recuperación, promedio, historial y versión | `test_resilience.py`, API de Monitoreo |
| Volumen, índices y caché | 5000 unidades ficticias, EXPLAIN ANALYZE e iteraciones alternadas autenticadas | Archivos JSON en `evidence/` |

**Regresión del primer corte independiente: 59 pruebas aprobadas, cero fallos, errores u omisiones, en 205.34 segundos.** [JUnit reproducible](../integracion/resultados/junit.xml). Las ejecuciones anteriores y repeticiones no se suman como casos nuevos. Las últimas verificaciones manuales añaden comprobación del encabezado X-Cache, índices y reinicio del lanzador, sin incrementar el número de pruebas pytest.

También se compilaron los 36 XSD de solicitudes generados y el XSD común de respuesta; OpenAPI se valida para las once unidades. El esquema de envoltura XML no sustituye el contrato de campos y tipos del DTO equivalente publicado en OpenAPI.

## Carga inicial

Locust 2.46.7, ocho usuarios, incremento de dos usuarios/s y límite solicitado de 25 segundos, con consultas de cinco perfiles. La captura CSV conservada registra **164 peticiones, cero errores, 10.12 RPS, media 337.63 ms, p95 aproximado 660 ms y p99 aproximado 1500 ms**. El resumen de consola al cierre registró 171 peticiones; el CSV periódico corresponde a la última captura previa a la parada, no se suman ambas cifras.

Endpoints incluidos: login, disponibilidad, inventario, campañas, citas, solicitudes, traslados, rutas, alertas, auditoría y monitoreo. Operador solicita XML; los demás perfiles JSON. El login fue el endpoint más lento de esa muestra, incluyendo hash scrypt y arranque concurrente; no se redujo la seguridad para mejorar su tiempo.

Archivos: [estadísticas](../integracion/resultados/load-cache_stats.csv), [historial](../integracion/resultados/load-cache_stats_history.csv), [fallos](../integracion/resultados/load-cache_failures.csv) y [excepciones](../integracion/resultados/load-cache_exceptions.csv). Son una muestra inicial de consultas autorizadas, con procesos y pruebas compartiendo equipo; no equivalen a carga de reservas, estrés, saturación máxima o escalabilidad institucional. El modelo de perfiles se dejó posteriormente determinista para nuevas mediciones comparables.

## Volumen e índices

[Carga inicial](../integracion/resultados/volume.json): 5000 unidades ficticias en 277.33 ms; primera consulta top-20, 2.127 ms, recorrido secuencial con ordenamiento.

[Comparación del índice de paginación](../integracion/resultados/volume-index.json): misma base de 5000 unidades, consulta antes 6.865 ms y después 0.668 ms. El segundo plan utiliza `Index Only Scan` sobre `availability_page`, sin consultas al heap. La diferencia corresponde a esa observación local, no a una garantía de latencia. La migración inicial incluye el índice para instalaciones nuevas.

[Comprobación posterior al reinicio](../integracion/resultados/restart-volume.json): cero unidades añadidas y 5000 registros conservados. Los once servicios respondieron HTTP 200 en readiness después de detener e iniciar nuevamente el entorno.

## Caché y recursos

[Comparación alternada](../integracion/resultados/cache-comparison.json): treinta pares del mismo endpoint y cuenta, manteniendo JWT, permisos, límites y auditoría en ambos modos; cero errores. Se verificaron 29 HIT, un MISS y treinta BYPASS.

| Modo | Media | Mediana | p95 |
| --- | --- | --- | --- |
| Caché habilitada | 66.01 ms | 55.88 ms | 135.19 ms |
| Caché omitida | 84.81 ms | 81.38 ms | 122.72 ms |

La media mejoró en esta muestra, mientras el p95 con caché fue mayor: no se afirma mejora uniforme ni causalidad estadística. El JSON incluye RSS y CPU durante la muestra para 25 procesos, incluidos dependencias, servidores y workers. RSS es por proceso y no debe sumarse como memoria física única.

## Límites pendientes

- Reglas clínicas oficiales, interpretación HLA, elegibilidad específica y prioridad normativa: requieren especialistas y fuentes aprobadas. Este corte utiliza reglas o dictámenes humanos.
- Móvil, escritorio, Docker, HTTPS productivo, GCP e integración continua: pendientes. La web ya consume las API. Los catálogos históricos detallados y ediciones generales de expedientes/unidades necesitan nuevos contratos propietarios; no se presentan como disponibles en el portal integrado.
- GCS: adaptador implementado pero sin bucket/credenciales reales ni evidencia de carga, firma, descarga, caída o archivos grandes en nube. Sin configuración devuelve 503.
- Retención institucional, respaldo/recuperación productiva, alta disponibilidad, onboarding institucional definitivo, permisos administrativos regionales y credenciales de laboratorios: requieren definición posterior.
- Campañas y citas no incluyen todavía agenda clínica detallada por horario/sede; alertas son una bandeja persistente, sin proveedor de email/push.
- Las operaciones sin grant ni reserva local tras un timeout conservan estado pendiente y requieren reintento autorizado; los workers no guardan JWT. Las retenciones interrumpidas se recuperan/compensan y se procesan sin dejar que las más antiguas monopolicen el lote.
- El sistema no registra una transfusión o trasplante como realizado por recibir el recurso.

## Reproducir

Desde `apps/services`, con MongoDB disponible:

```sh
REDHOUSE_TEST_MONGOD=/ruta/a/mongod .venv/bin/python -m pytest tests -q --junitxml=/ruta/privada/resultados.xml
.venv/bin/python scripts/local.py init --directory /ruta/privada/entorno --mongo-bin /ruta/a/mongod
.venv/bin/python scripts/local.py start --directory /ruta/privada/entorno
.venv/bin/python scripts/prepare_load.py --directory /ruta/privada/entorno --units 5000 --report /ruta/privada/volumen.json
REDHOUSE_LOAD_STATE=/ruta/privada/entorno/state.json .venv/bin/python -m locust -f tests/locustfile.py --headless -u 8 -r 2 -t 25s --host http://127.0.0.1 --csv /ruta/privada/carga --only-summary
.venv/bin/python scripts/benchmark_cache.py --state /ruta/privada/entorno/state.json --pairs 30 --report /ruta/privada/cache.json
.venv/bin/python scripts/local.py stop --directory /ruta/privada/entorno
```

Cada ejecución genera identidades, contraseñas y claves nuevas fuera del repositorio. No publicar configuración, credenciales ni JWT; los archivos de evidencia conservados contienen resultados técnicos y datos ficticios, no secretos.
