# Serie sostenida de lecturas y recuperación — 14/11/2026

**Seis fases válidas; cinco cumplen el objetivo de rendimiento.** Las cuatro fases de 12 usuarios terminaron sin errores y con p95 por endpoint inferior a 2 s. Con 24 usuarios tampoco hubo errores, pero el listado de traslados alcanzó p95 de 2.100 ms; no cumple el objetivo previo. Conforme al plan, se omitió el estrés de 36 usuarios y se ejecutó recuperación con seis: cero errores y p95 máximo de 840 ms. No se cambió el umbral después de medir.

## Resultados del corte medido

| Fase, en orden | Usuarios | Segundos | Lecturas | Errores | HTTP/s | Media ponderada ms | Mayor p95 de endpoint ms | Mayor p99 de endpoint ms | Cumple |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Caché activa A | 12 | 120,075 | 1.734 | 0 | 14,441 | 336,6 | 780 | 850 | Sí |
| Bypass A | 12 | 120,006 | 1.728 | 0 | 14,399 | 345,4 | 830 | 1.100 | Sí |
| Caché activa B | 12 | 120,045 | 1.716 | 0 | 14,295 | 358,1 | 910 | 1.300 | Sí |
| Bypass B | 12 | 120,007 | 1.700 | 0 | 14,166 | 352,8 | 1.100 | 1.200 | Sí |
| Caché activa | 24 | 120,076 | 2.260 | 0 | 18,821 | 746,1 | 2.100 | 3.100 | No |
| Recuperación, caché activa | 6 | 60,005 | 471 | 0 | 7,849 | 278,4 | 840 | 970 | Sí |

Cada `measurement.json` conserva conteo, media, **mediana**, p95 y p99 por operación. La tabla no presenta máximos de percentiles por endpoint como percentiles globales, ni promedia medianas. La media global se pondera por peticiones. [Comparación numérica](comparacion.json) y [gráfica](comparacion.png).

En la fase de 24, los listados de Traslados y Tareas propias tuvieron p95 de 2.100 y 2.000 ms, respectivamente; el objetivo exige estrictamente menos de 2.000 ms. Bitácora alcanzó 1.800 ms. La prueba identifica un límite de rendimiento bajo esta carga, no su causa exacta ni un máximo universal de usuarios. No hubo rechazo 429 ni fallos de autenticación/cierre. No se forzó saturación adicional después del incumplimiento.

## Entorno y aislamiento

Mac Intel, 16 GiB; generador y doce servicios comparten equipo. Una instancia local por servicio, Waitress con ocho hilos y Transporte/gevent; workers activos, sin Nginx ni réplicas. `TESTING=False`, cuotas HTTP 180 e internas 1.800 intactas. Seis identidades de seis perfiles con familias independientes: dos familias por identidad a 12 usuarios y cuatro a 24; no son 12/24 personas diferentes. Operador usa XML/XSD; los otros perfiles JSON. MFA conservado para los perfiles obligados, con serialización por cuenta y periodo TOTP. Cada fase esperó todas las sesiones y calentó 30 s antes del corte.

Una sola población: 2.000 donantes, 10.000 recursos y 100.000 eventos **SQL**, semilla `20261113`; SHA-256 del dataset `1ccd82602ee0dfb0b92b41f31ad6d6b0cfba12d3459f235c7191de264880abcb`. No atribuye ese volumen a MongoDB. Preparación: 165,752 s, incluidos 138,340 s acumulados de guardas; no es latencia SQL pura. Planes, índices, distribución y crecimiento se conservan en [preparacion.json](preparacion.json).

Las 384 muestras registraron al menos 11.163.066.368 bytes libres y un máximo propio de 496.026.184 bytes. Máximo RSS sumado: 2.406.204 KiB; máximo CPU sumado informado por `ps`: 454,0 %. RSS puede contar memoria compartida varias veces; CPU de `ps` no es una lectura instantánea. Generación de documentos, compilaciones y emuladores quedaron detenidos durante la medición. Estos datos no identifican por sí solos un cuello de botella del servidor.

## Caché y recuperación

Las fases activas A/B observaron HIT/MISS 255/24 y 256/23; los bypass observaron 280/280 respuestas BYPASS y ningún HIT/MISS. Redis siguió autorizando todas las peticiones protegidas. La caché solo cubre parte de esta mezcla de lecturas: no equivale a apagar Redis ni a comparar todo el sistema con/sin Redis.

Las dos repeticiones por modo muestran variación y medias globales próximas; no sustentan una mejora general porcentual atribuible a caché. La fase de recuperación vuelve a cumplir el objetivo de latencia. No demuestra volver exactamente al rendimiento de la línea base anterior, ni recuperación de una dependencia caída: en esta serie se redujo la concurrencia.

## Integridad y reproducción

- Lanzador terminó con código 0; `summary.json` registra las seis ejecuciones válidas y el estrés omitido. Código 0 no convierte la fase de 24 en aceptada.
- Las 78 familias nuevas se comprobaron revocadas en PostgreSQL y ausentes en Redis; conteos por identidad e IDs únicos verificados por fase. Cero fallos de limpieza o drenado.
- Las 945 fuentes de preparación y 20 huellas de runtime/configuración permanecieron iguales antes/después. [Huellas](fuentes.json).
- Al terminar se comprobó ausencia de los 24 PID de API/workers y de `pg/postmaster.pid`; no se detuvieron recursos ajenos. El fixture privado permanece en `/private/tmp/rh-load-c92ed10k` para reutilización controlada.
- CSV publicados: únicamente CRLF→LF, igualdad de celdas verificada. [Huellas originales](original-csv.sha256); originales privados intactos. CSV/final incluyen su propio instante de cierre y pueden incluir drenado; el corte medido procede de `measurement.json`.
- Credenciales, factores MFA y logs originales siguen privados. No se ejecutó ninguna carga en GCP.

Comando ejecutado desde la raíz:

```sh
PYTHONPATH=.:apps/services apps/services/.venv/bin/python apps/services/scripts/prepare_load.py --scale-percent 10 --seed 20261113 --mongod "$PWD/.local/tools/mongodb-8.0.17/bin/mongod" --sustained-series
```

Log privado del lanzador: `.local/artifacts/carga-serie-20261114/runner.private.log`. [Plan previo](../serie-plan.md). Etapa 07 conserva pendientes las mediciones transaccionales y restantes ensayos integrales; esta evidencia no prueba escrituras, GPS bajo carga, capacidad de GCP ni aceptación clínica.
