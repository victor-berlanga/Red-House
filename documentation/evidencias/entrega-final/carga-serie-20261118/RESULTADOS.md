# Serie sostenida de lecturas repetida en Mac M1 — 18/11/2026

**Seis fases válidas. Cinco cumplen. La de 24 usuarios cumple con holgura la latencia, pero no la tasa de errores:** 575 respuestas 429 de la cuota HTTP del producto, el 10.9 %. Conforme al plan, se omitió el estrés de 36 usuarios (`stress_skipped: "24 no aceptado"`) y se ejecutó la recuperación con seis.

Comando y arnés: los mismos de la [serie del 14/11](../carga-20261114/serie-12-24/RESULTADOS.md), sin cambios en el código de carga. Las huellas de las fuentes están en [serie-summary.json](serie-summary.json).

```sh
PYTHONPATH=.:apps/services apps/services/.venv/bin/python apps/services/scripts/prepare_load.py \
  --scale-percent 10 --seed 20261113 --mongod /opt/homebrew/bin/mongod --sustained-series
```

Base `5f79557`. Ventana de 03:49:01 a 04:09:39 UTC. Laboratorio propio en `/private/tmp`, borrado al terminar sin procesos residuales; el log privado no se publica.

## Resultados del corte medido

| Fase, en orden | Usuarios | Segundos | Lecturas | Errores | HTTP/s | Media ponderada ms | Mayor p95 de endpoint ms | Mayor p99 de endpoint ms | Cumple |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Caché activa A | 12 | 120.011 | 2,947 | 0 | 24.56 | 25.6 | 59 | 80 | Sí |
| Bypass A | 12 | 120.010 | 2,893 | 0 | 24.11 | 24.9 | 74 | 86 | Sí |
| Caché activa B | 12 | 120.005 | 2,920 | 0 | 24.33 | 25.3 | 75 | 84 | Sí |
| Bypass B | 12 | 120.006 | 2,935 | 0 | 24.46 | 25.9 | 82 | 94 | Sí |
| Caché activa | 24 | 120.011 | 5,274 | **575 (429)** | 43.95 | 25.9 | 90 | 100 | **No** (errores ≥ 1 %) |
| Recuperación, caché activa | 6 | 60.004 | 733 | 0 | 12.22 | 29.6 | 130 | 140 | Sí |

- **Fuente de los datos:** el `phase.json` y el `measurement.json` de cada carpeta conservan conteo, media, mediana, p95 y p99 por operación. `run_failures.csv` desglosa los 429.
- **Caché:** coherente en todas las fases. Las fases activas tuvieron HIT y MISS (24 usuarios: 696 HIT y 18 MISS); las de bypass, solo BYPASS.
- **Sesiones:** cero errores de usuario y de autenticación en las seis fases.

## Lectura

- **Latencia:** con 24 usuarios, el mayor p95 por endpoint fue de **90 ms**, contra 2,100 ms del 14/11 en una Mac Intel de 16 GiB. Esta Mac M1 de 8 GB responde mucho más rápido con el mismo arnés, la misma semilla y la misma población (2,000 donantes, 10,000 recursos y 100,000 eventos SQL).
- **Errores:** al responder más rápido, cada usuario repite su ciclo más seguido. Con 24 usuarios el sistema atendió 43.95 HTTP/s, frente a 18.8 el 14/11, y la cuota HTTP del producto (180, intacta) empezó a responder 429 a los 2 min 17 s de la fase. Seis endpoints acumularon de 84 a 104 rechazos cada uno, entre 04:05:47 y 04:06:59 UTC.
- **Interpretación:** las 24 sesiones comparten seis identidades sintéticas, es decir, cuatro familias por cuenta. Los 429 son la protección por cuenta funcionando, no una falla del servicio. Aun así cuentan como errores para el criterio de aceptación (menos del 1 %). La [continuación con ritmo de 4 a 6 s](../carga-lecturas-paced-20261117/RESULTADOS.md) ya mostró 24 y 36 sesiones sin errores con cuota intacta. No se determinó si la cuota se aplica por identidad o por familia.
- **INC-290:** esta corrida no la cierra. INC-290 pide repetir en las mismas condiciones, y el hardware es distinto. El dato nuevo indica que el p95 de 2,100 ms del 14/11 depende del equipo: con el mismo código, la latencia queda dos órdenes de magnitud por debajo del umbral.

## Límites

- El generador y los doce servicios comparten el equipo, con una instancia por servicio, sin Nginx ni réplicas. No es GCP.
- No se ejecutó el estrés de 36 usuarios sin espera ni flujos transaccionales.
- El arnés transaccional multiperfil (`--transaction-directory`) requiere un laboratorio con esquema 20, y los laboratorios nuevos son de esquema 21. Por eso esa carga no se pudo repetir; el último resultado transaccional sigue siendo [HTTP12 del 16/11](../carga-20261114/xml-lock-http12-20261116/RESULTADOS.md).
- Docker Desktop siguió abierto durante la corrida, con otros contenedores ajenos activos.
