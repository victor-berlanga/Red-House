# Línea base sostenida de lectura — 14/11/2026

**Aprobada:** seis identidades/perfiles durante 30 segundos de calentamiento y 120,005 segundos medidos. Las 1.029 lecturas del corte medido tuvieron cero errores: 8,575 peticiones/s. Todos los endpoints cumplieron el objetivo académico previo de p95 menor de 2 segundos; el mayor p95 fue 430 ms. Se comprobó la revocación de las seis familias nuevas en PostgreSQL y Redis. La prueba terminó con código 0, sin activar guardas y con los motores propios cerrados.

## Condiciones y alcance

Mac Intel de 16 GiB, generador y servicios en el mismo equipo; una instancia por servicio en loopback, sin Nginx ni réplicas. Procesos reales `run.py`: Waitress de ocho hilos, Transporte/gevent, workers activos. `TESTING=False`, MFA conservado para los perfiles obligados, límites HTTP 180 e internos 1.800; configuración efectiva en [topology.json](topology.json). Operador consume XML/XSD, los otros cinco perfiles JSON. No es capacidad de GCP, concurrencia clínica ni medición de escrituras.

Datos sintéticos: 2.000 donantes, 10.000 recursos y 100.000 eventos **SQL**, semilla `20261113`. La escala del 10 % respeta el presupuesto de este equipo; Mongo participa en el entorno, sin atribuirle ese volumen SQL. Preparación: 164,776 s, incluidos 138,215 s de guardas; no representa latencia SQL pura. PostgreSQL creció 56.459.264 bytes y el directorio 124.041.776 bytes lógicos frente al estado inicializado.

Las 66 muestras conservaron al menos 10.776.944.640 bytes libres; máximo propio 418.855.972 bytes, por debajo de 1,5 GiB. Máximo RSS sumado: 2.235.088 KiB; máximo CPU sumado informado por `ps`: 348,6 %. RSS puede contar memoria compartida varias veces y CPU no es lectura instantánea. No hubo Gradle, Xcode, emulador o ClamD durante la corrida.

## Corte de 120 segundos

| Operación | Peticiones | Media ms | p95 ms | p99 ms |
| --- | ---: | ---: | ---: | ---: |
| inventario / Disponibilidad regional | 85 | 232.8 | 400 | 470 |
| receptores / Solicitudes propias | 85 | 204.4 | 330 | 410 |
| auditoria / Bitácora | 92 | 273.7 | 430 | 680 |
| priorizacion_geografia / Rutas | 72 | 214.7 | 390 | 460 |
| donantes / Agenda propia | 74 | 228.1 | 340 | 510 |
| inventario / Inventario propio | 81 | 254.4 | 430 | 540 |
| transporte / Tareas propias | 84 | 224.0 | 400 | 530 |
| donantes / Campañas | 81 | 208.3 | 340 | 460 |
| transporte / Traslados | 72 | 239.0 | 420 | 580 |
| alertas / Avisos propios | 74 | 215.5 | 340 | 380 |
| alertas / Avisos de traslado | 84 | 207.7 | 330 | 390 |
| monitoreo / Estado regional | 72 | 210.5 | 340 | 380 |
| donantes / Feed público | 73 | 116.8 | 180 | 210 |

[measurement.json](measurement.json) se tomó antes del drenado. Los CSV versionados normalizan únicamente finales de línea CRLF a LF; se comprobó igualdad de todas sus celdas y se conservaron las huellas originales en `original-csv.sha256`, con los originales privados intactos. Los CSV históricos/finales tienen sus propios instantes de escritura y pueden incluir peticiones al terminar; no deben sustituir ese corte ni sumarse como otra ejecución. La mediana del corte exacto no se conservó; el arnés deberá incluirla en las siguientes mediciones, sin repetir esta corrida solo por ese dato. Calentamiento: 276 peticiones y cero fallos; seis usuarios presentes durante ambas fases. Las credenciales/MFA y logs originales permanecen privados.

## Reproducción y evidencia

Desde la raíz, con los demás trabajos pesados detenidos:

```sh
PYTHONPATH=.:apps/services apps/services/.venv/bin/python apps/services/scripts/prepare_load.py --scale-percent 10 --seed 20261113 --mongod "$PWD/.local/tools/mongodb-8.0.17/bin/mongod" --sustained-read
```

Fuentes de servicios del corte `d735668`; [944 fuentes y configuraciones](fuentes.json) iguales antes/después. Dirección cotejó salida, conteos, tiempos, guardas y cierre. Laboratorio privado conservado: `/private/tmp/rh-load-wg6_128a`; no reutilizar sus PID ni conexiones sin verificar procesos/propiedad. Log del lanzador: `.local/artifacts/load-baseline-20261114-01.private.log`. [Resumen](resumen.json), CSV y [huellas](artefactos.sha256) conservan el resultado; los intentos fallidos anteriores quedan separados.

**Etapa 07 sigue abierta:** faltan niveles superiores, comparación de caché, estrés/recuperación y métricas transaccionales. Esta corrida sí completa la primera línea base de lectura prevista en el [plan](../../carga-20261113/PLAN.md).
