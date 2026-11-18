# Recuperación coordinada aislada: tres repeticiones — 18 de noviembre de 2026

Resultado: **3/3 aprobadas**, con el mismo `apps/services/tests/test_storage_recovery.py` del [ensayo del 13/11](../recuperacion-20261113/RESULTADOS.md). La base era `4f08abf` y el equipo una Mac M1 con PostgreSQL 14.25, MongoDB 8.0.38 y Redis de Homebrew. Cada repetición usó su propio laboratorio temporal en `/private/tmp`, que se borró al terminar sin procesos residuales. No se accedió a GCP ni al laboratorio restaurado.

| Intento | Ventana UTC | Duración pytest | RTO observado | RPO observado | Dump SQL | Objetos posteriores al corte ausentes |
|---|---|---:|---:|---:|---:|---|
| 1 | 03:46:24–03:46:50 | 22.98 s | **4.287 s** | **6.585 s** | 735,221 B | 1 documento, 1 evento |
| 2 | 03:46:50–03:47:16 | 21.89 s | **3.886 s** | **6.990 s** | 735,214 B | 1 documento, 1 evento |
| 3 | 03:47:16–03:47:42 | 22.76 s | **4.086 s** | **6.963 s** | 735,238 B | 1 documento, 1 evento |

- **RTO:** de 3.9 a 4.3 s; mediana 4.09 s. Se mide desde el incidente simulado hasta la descarga autorizada tras restaurar PostgreSQL con roles, MongoDB, Redis con ACL y RDB, y el volumen privado.
- **RPO:** de 6.6 a 7.0 s; mediana 6.96 s. Es el intervalo entre la última confirmación documental conservada y el incidente.
- **En las tres repeticiones** se invalidaron las sesiones restauradas antes de abrir el backend. El documento y el evento creados después del corte no aparecen en la copia, como se esperaba. Las propiedades están en `intentoN-junit.xml`.
- **Escáner:** receptor doble (`test_receiver`), no ClamAV real.

Los valores del 13/11 (RTO 21.7 s, RPO 23.8 s) se tomaron en otro equipo. La diferencia viene del hardware y de la carga, no de un cambio en el ensayo. El código de la prueba no cambió.

## Lectura frente a los objetivos

Los objetivos propuestos están en el [plan de recuperación](../../../entrega-final/continuidad/Plan_recuperacion_coordinada.md#objetivos-propuestos-rto-y-rpo): RTO de 60 min y RPO de 24 h para las bases. El ensayo los cumple con amplio margen, pero solo mide la restauración técnica con copias ya disponibles en el mismo equipo. No incluye detectar el incidente, decidir, conseguir otro host, bajar copias externas ni rotar claves; eso consume la mayor parte del RTO real. Y el RPO real lo fija la frecuencia del respaldo, no este ensayo: hoy `deployment/backup.py` se corre a mano y no hay una tarea programada.

## Reproducción

```sh
RH_LAB="$(mktemp -d /private/tmp/rh-recuperacion-20261118.XXXXXXXX)"; mkdir -p "$RH_LAB/platform"
REDHOUSE_TEST_ROOT="$RH_LAB/platform" REDHOUSE_TEST_STARTUP_TIMEOUT=120 \
apps/services/.venv/bin/python -m pytest -q -p no:cacheprovider apps/services/tests/test_storage_recovery.py \
  --basetemp="$RH_LAB/pytest" --junitxml=/ruta/nueva/intento.xml
```

Repetir con un directorio nuevo cada vez y borrar solo ese directorio cuando terminen sus procesos.
