# Verificación vigente — 8 de octubre de 2026

Servicios 0.2.0 y portal Flask integrado. Pruebas locales en macOS Intel con Python 3.12, PostgreSQL, Redis y MongoDB reales. Versiones Python exactas: `requirements-verified.txt`. [Resultados históricos del 7 de octubre](historial/VALIDACION_2026_10_07.md).

## Ejecuciones y alcance

| Verificación | Resultado | Evidencia |
| --- | --- | --- |
| Suite completa de servicios y web | **113 aprobadas**, cero fallos/errores/omisiones, **354.41 s** | [JUnit](evidence/review-junit.xml) |
| Ajuste final de consultas e historial por propietario | **51 aprobadas**, 278.25 s; regresiones de revisión, paquetes aislados y web | [JUnit](evidence/review-final-targeted.xml) |
| Contratos finales y evidencias dentro de Transporte | **50 aprobadas**, 85.74 s; seguridad, XSD, OpenAPI y once paquetes sin módulos vecinos | [JUnit](evidence/review-contracts-final.xml) |
| Modo histórico del monolito | **121 aprobadas, 8 omitidas**, 324.90 s; bases aleatorias aisladas | [JUnit](evidence/review-legacy.xml) |
| Chrome | **33 páginas**, 1440×1000 y 390×844, búsqueda por API comprobada, cero errores JavaScript/fallos estáticos/desbordamiento del documento | [Informe y capturas](../../../documentation/capturas-revision/README.md) |
| Reinicio selectivo | Solo cambian API/worker de Donantes; se conservan otros 10 API, 10 workers y 2 procesos web; Inventario y portal HTTP 200 durante la operación | [Informe](evidence/review-independence.json) |
| Respaldo y migración | Once respaldos restaurados en bases desechables; dos aplicaciones de migración, registros anteriores conservados | [Informe](evidence/review-backup.json) |
| DEMO y cuentas históricas | 6 instituciones, 108 donantes, 72 solicitudes, 252 recursos y 18 cadenas de custodia verificadas; 8 hashes/roles conservados | [Informe](evidence/review-demo.json) |
| Catálogos por API | 54 registros administrativos ficticios en seis instituciones; sin alterar expedientes o estados clínicos | [Informe](evidence/review-catalogues.json) |
| Formato y análisis estático | Ruff: formato conforme y selección E9/F63/F7/F82 sin errores | Comandos siguientes y workflow CI |

Los 51 y 50 casos son subconjuntos repetidos después de ajustes finales; **no se suman a los 113**. Las ocho omisiones del monolito requieren `--browser` en su suite histórica; no equivalen a aprobaciones. El navegador del portal integrado se comprobó por separado.

La primera ejecución completa produjo un 503 de notificaciones y 112 aprobadas. El caso no se reprodujo en la suite web aislada ni en la siguiente ejecución completa. Se añadió diagnóstico de tipo de excepción/correlación sin datos sensibles; no se afirma una causa no demostrada. Chrome encontró una colisión entre atributos HTML del selector nuevo y del antiguo: se separaron y el recorrido final pasó sin errores. La comprobación de reinicio detectó que el lanzador regresaba antes de escuchar HTTP; ahora espera al proceso y a liveness.

## Criterios de aceptación

La [matriz de revisión](REVISION_2026_10_08.md) relaciona cada problema con su cambio y prueba. Las suites usan HTTP real y dependencias físicas aisladas; el fixture web prohíbe el acceso a SQL histórico. Cubren:

- Flujos de donación/procesamiento, sangre y riñón/hígado/corazón hasta recepción, custodia, auditoría y avisos; dictamen humano y algoritmo sin asignación automática.
- Concurrencia, doble reserva, exceso de cobertura, cierre único, idempotencia y compensación de operaciones interrumpidas.
- JWT, roles, instituciones, asignaciones, renovación/reutilización, revocación, rollback SQL/permisos Redis, nulos y entradas inválidas.
- JSON/XML, XXE, evidencia opcional anidada, **56 XSD de entrada**, esquema de respuesta y DTO por operación; OpenAPI para once unidades. El XSD estructural de salida requiere además validación semántica, disponible en `redhouse.xml_response`.
- Caídas de PostgreSQL, Redis, MongoDB y servicios, recuperación y errores seguros. GCS configurado se comprueba con mock en la prueba de health: **no es evidencia de nube real**.
- Catálogos, edición con versión/motivo, primer administrador, protección de historia, selectores más allá de cien registros, sesiones web cifradas, logout con revocación pendiente y ausencia de bloqueo SQLite durante HTTP.

CI está definida en `.github/workflows/services.yml`, con dependencias locales y sin Docker. No se ha ejecutado en GitHub. Linux/Windows nativos no se presentan como comprobados.

## Caché y carga

Treinta pares alternados del mismo endpoint/cuenta, manteniendo JWT, permisos y auditoría: **30 BYPASS, 1 MISS, 29 HIT, cero errores**, 4.346 s en total. [Informe y recursos por proceso](evidence/review-cache.json).

| Modo | Media | Mediana | p95 de la muestra |
| --- | ---: | ---: | ---: |
| Caché | 59.637 ms | 57.259 ms | 87.128 ms |
| Sin caché | 85.161 ms | 79.004 ms | 133.044 ms |

Muestra pequeña local sobre la DEMO de 252 recursos; no demuestra causalidad estadística ni escalabilidad. La evidencia previa de 5000 unidades e índice se conserva en el corte histórico y no se presenta como una carga nueva. El RSS del informe es por proceso y no debe sumarse como memoria física única.

Locust: ocho usuarios concurrentes, cinco perfiles, incremento de dos usuarios/s y ejecución solicitada de 25 s, JSON/XML y doce grupos de operaciones. CSV conservado: **299 peticiones, 0 fallos**, 12.44 RPS, media 172.90 ms, p95 aproximado 340 ms y p99 650 ms. [Estadísticas](evidence/review-load_stats.csv), [historial](evidence/review-load_stats_history.csv), [fallos](evidence/review-load_failures.csv). El cierre de consola registró 301 peticiones; el CSV periódico corresponde a su corte conservado y no se suman ambos. Se conservaron límites de 180/minuto; no es estrés ni una prueba de transacciones de reserva bajo carga. Login fue la operación más lenta e incluye hash de contraseña.

## Reproducción

Desde la raíz, con Python/PostgreSQL/Redis/MongoDB instalados:

```sh
apps/services/.venv/bin/python -m pytest apps/services/tests -q --junitxml=/ruta/privada/services.xml
apps/services/.venv/bin/ruff check --select E9,F63,F7,F82 apps/services apps/web-monolito01/src/integration
apps/services/.venv/bin/ruff format --check apps/services apps/web-monolito01/src/integration
apps/services/.venv/bin/python apps/services/scripts/document.py
apps/services/.venv/bin/ruff format apps/services
apps/services/.venv/bin/python apps/services/scripts/check_independence.py --directory .local/demo --report /ruta/privada/independencia.json
apps/services/.venv/bin/python apps/services/scripts/check_legacy_web.py --directory .local/demo --report /ruta/privada/legacy.xml
```

`REDHOUSE_TEST_MONGOD` permite indicar el binario mongod; `REDHOUSE_TEST_ROOT` el directorio temporal. Para verificar un respaldo propio: `scripts/check_backup.py --directory DIRECTORIO --backup DIRECTORIO/backups/CORTE --report REPORTE`. Solo elimina las bases aleatorias que crea para la comprobación.

Navegador: `node apps/web-monolito01/tests/integrated_browser.cjs --state .local/demo/state.json --output /ruta/privada/capturas`, con Playwright y Chrome disponibles. No publicar state.json, secretos, sesiones, contraseñas ni JWT. Se conservan únicamente resultados sanitizados y datos ficticios de las capturas.

## Límites que siguen abiertos

Reglas clínicas oficiales/HLA, agenda clínica detallada, políticas de retención, recuperación de contraseña, email/push, GCS real y archivos grandes, aplicaciones móvil/escritorio, Docker, GCP, HTTPS productivo, redundancia, estrés/saturación y validación institucional. La separación de entregas no evita fallas en dependencias comunes ni hace compatibles cambios arbitrarios de contratos. PostgreSQL y Redis siguen compartiendo instancia física en esta DEMO.
