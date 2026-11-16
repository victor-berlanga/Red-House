# Repetición transaccional de doce identidades — 16/11/2026

**Resultado no aceptado:** el oráculo de propagación volvió a vencer después de 30,17 segundos (`event_propagation`). La ejecución terminó con código 1. El ensayo anterior conserva su propio fallo; esta repetición no demuestra pérdida permanente ni entrega posterior. [Resumen saneado](resumen.json) y [huellas](huellas.json).

Se reutilizaron el fixture conservado en esquema 21 y sus doce cuentas; una campaña y dos horarios sintéticos nuevos se crearon por API. No se alteraron la campaña, horarios ni cantidad de citas históricas comprobadas. Los tres eventos de preparación aparecieron una vez tanto en Donantes como en Auditoría, con identificadores correlacionados. Fuentes y topología se mantuvieron iguales según el wrapper.

Durante 120,043 segundos se observaron 1.270 solicitudes HTTP sin fallos. El máximo p95 de lectura fue 800 ms; el p95 de los recorridos fue 2.700 ms para operador y 3.800 ms para donante. Se contabilizaron 197 recorridos dentro de medición. Sumando calentamiento y drenado: 756 escrituras confirmadas, ninguna incierta, 252 recorridos completos y 12 repeticiones idempotentes confirmadas. Estos datos cumplen los límites de latencia, pero no subsanan el fallo del oráculo integral.

El oráculo comparó eventos esperados de negocio en `audit_events` y avisos de cita propios en Alertas. El resumen guardado contiene únicamente la categoría `event_propagation`: **no conserva el desglose de eventos o avisos faltantes, ni instantáneas de cola**, por lo que no permite identificar qué servicio o destino quedó retrasado, medir crecimiento del backlog o afirmar entrega posterior. La ausencia de desglose no convierte el fallo en éxito.

Los logs de workers se abren en modo agregado. El archivo de Auditoría conserva tres mensajes de indisponibilidad de base de datos, pero su última modificación es del 14/11/2026, anterior a esta repetición; no se atribuyen a ella. Los archivos de workers de Donantes y Alertas permanecen vacíos. El material existente no demuestra errores de worker durante esta corrida ni descarta errores no registrados.

Se verificó la revocación de las doce familias de carga y de la familia de preparación, y su ausencia de Redis. Los procesos propios cerraron, desapareció `postmaster.pid` y se retiró el candado de ejecución. Las 81 muestras de presupuesto registraron como mínimo 12.390.985.728 bytes libres y máximo 509.599.829 bytes propios. El fixture y los diarios privados se conservaron; no se reintentó la carga. Generador y servicios compartieron el equipo y no se midió GCP ni capacidad de producción.

Comando ejecutado una sola vez, con salida privada:

```sh
umask 077
apps/services/.venv/bin/python .local/artifacts/carga-20261116-repeticion/runner.py > .local/artifacts/carga-20261116-repeticion/ejecucion-01.private.log 2>&1
```

Resultado privado: `/private/tmp/rh-load-c92ed10k/transactions-repeat-20261116T223116Z-628f31c3/`. Los datos privados contienen identificadores y diarios de intentos; no se publican credenciales ni tokens.

## Inspección posterior sin workers

Una consulta independiente a las 22:39:59 UTC reconstruyó las 756 intenciones de esta corrida y sus identificadores exactos, con PostgreSQL en transacciones de solo lectura y MongoDB. No inició APIs, workers ni Locust. [Conteos saneados](inspeccion-posterior.json) y [huellas](inspeccion-sha256.txt).

- Los 756 eventos de negocio aparecieron una vez en su fuente. Auditoría conservaba 697 y faltaban 59; Alertas mostraba 99 de 118 avisos propios esperados. En MongoDB aparecían 697 de los 756 identificadores de evento.
- Para esos eventos, Donantes tenía 60 entregas pendientes hacia Auditoría (una con intento) y 59 hacia Alertas (ninguna con intento). Ninguna de esas pendientes tenía el próximo intento programado en el futuro. Las 60 entregas pendientes no equivalen por sí mismas a los 59 eventos ausentes en Auditoría.
- Inventario y Compatibilidad mostraban 134 y 268 entregas respectivamente hacia Auditoría, todas registradas como entregadas; Auditoría mostraba 697 entregas a MongoDB. Los conteos de cola corresponden solo a los eventos seleccionados, no al backlog global.

La inspección observó el estado posterior, no una fotografía del instante exacto de 30 segundos. La cola pendiente indica propagación incompleta al observarla; no demuestra pérdida permanente ni que llegara después. Los dos motores iniciados por la inspección cerraron y `postmaster.pid` quedó ausente. El resultado inicial de la carga permanece fallido.
