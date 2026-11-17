# Lecturas sostenidas con cuota intacta — 17/11/2026

La continuación con espera uniforme de **4 a 6 segundos después de cada ciclo completo** terminó con salida 0: tres fases aceptadas, cero errores HTTP medidos y **66 familias propias cerradas en PostgreSQL y ausentes en Redis**. Se usaron las mismas seis identidades sintéticas, población conservada y configuración de límites. No se ejecutaron flujos de negocio ni otra semilla.

## Métricas y resultado

Cada fase tuvo 30 segundos de calentamiento, separados de la medición. Son sesiones concurrentes: cuatro, seis y una por cada identidad para 24, 36 y seis sesiones. Los conteos siguientes incluyen únicamente GET medidos; no suman autenticación, calentamiento o logout.

| Corrida | Sesiones | Medición s | GET | GET/s | Errores | Mayor p95 por endpoint ms | Mayor p99 por endpoint ms | Medición |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Histórico rápido | 24 | 120.065 | 4097 | 34.123 | 244 | 1300 | 1400 | No aceptada |
| Ritmo 4–6 s | 24 | 120.039 | 1334 | 11.113 | 0 | 890 | 1000 | Aprobada |
| Ritmo 4–6 s | 36 | 60.007 | 981 | 16.348 | 0 | 1000 | 1100 | Aprobada |
| Ritmo 4–6 s | 6 | 60.021 | 173 | 2.882 | 0 | 620 | 620 | Aprobada |

Los máximos de percentiles por endpoint **no son percentiles globales**. [Detalle por operación](endpoints.csv) conserva media, mediana, p95 y p99 sin promediar medianas. [Resumen sanitizado](resumen.json) conserva duración, caché, errores, muestras de recursos y controles. Las muestras de RSS y `ps` abarcan la fase completa, incluida autenticación; su CPU no es una medición instantánea ni demuestra saturación.

## Fallo anterior y cambio de metodología

El intento anterior permanece **FAIL / medición no aceptada**: 24 sesiones, espera de 0,5–1,5 s, 244 respuestas 429 de Transporte, de las cuales 138 fueron Tareas propias y 106 Traslados. Su ejecución y limpieza aprobaron; no se ejecutaron después las fases 36/seis en ese intento. No se borraron ni sobrescribieron sus resultados.

`redhouse/security.py:44–60` aplica 180 peticiones por minuto y servicio a `tenant_id:user_id`, compartidas entre las sesiones de esa identidad (`redhouse/api.py:48`). Listado y detalle de Transporte consumen la misma cuota. La continuación importa el mismo `SustainedUser` y cambia únicamente su espera; el runner, los seis perfiles, las operaciones, la cuota, MFA, los umbrales y los oráculos permanecen. Un adaptador privado sustituye exclusivamente el argumento del workload en el comando Locust; el archivo versionado no fue modificado.

**Es otra tasa ofrecida.** La tabla conserva ambos resultados para mostrar las condiciones y sus límites; no demuestra mejora porcentual de capacidad, 36 personas independientes ni ausencia de saturación con mayor demanda. El rechazo 429 anterior prueba actuación de la cuota, no identifica por sí solo un cuello de botella del servidor. No se relajó el límite para aprobar.

## Procedimiento identificado

Dirección ejecutó una sola continuación revisada:

```sh
PYTHONDONTWRITEBYTECODE=1 apps/services/.venv/bin/python .local/artifacts/inventory-query-20261117/readonly-paced-prepared/run.py --execute --principal-runtime-closed
```

El comando requiere el fixture propio conservado y frío, configuración/población verificadas, factores existentes y manifest aprobado; no es una orden para repetir sobre otra instalación. Los hashes identifican wrapper/workload y manifiesto revisados. El fixture mantenía 10.676 recursos; no se creó población nueva para esta corrida.

## Controles y cierre

Las tres fases verificaron usuarios activos mínimos, duración, revocación SQL/Redis, número exacto de familias, cero errores de limpieza y caché activa con HIT/MISS. Se mantuvieron los criterios previos: mayor p95 de GET inferior a 2000 ms y proporción de fallos inferior al 1 %. Las tres fases tuvieron cero fallos y cero respuestas 429. El retorno a seis sesiones acredita recuperación al reducir la demanda; no es recuperación de una dependencia caída.

Población, muestra histórica, diarios de negocio, configuraciones efectivas, fuentes y topología conservaron sus controles antes/después. Doce API y sus workers usaron los pools ya preparados; el wrapper cerró todos sus procesos y retiró únicamente su lock. El fixture y sus datos se conservaron. Autenticación y permisos Redis siguieron activos. Los [hashes de procedencia](procedencia-sha256.json) identifican los registros originales privados; no se publican credenciales, tokens, IDs de cuenta ni filas de negocio.

Entorno aislado local, esquema 21, lecturas JSON por perfiles y XML para operador. No se midieron transacciones de negocio/s, GPS/WSS bajo carga, recuperación de dependencia, Nginx, réplicas ni capacidad GCP. No cierra por sí solo toda la etapa 07 ni sustituye las series históricas con/sin caché o los flujos finitos ya aceptados.
