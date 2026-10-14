# Pruebas y validación

Los tests ejecutables permanecen junto al código. Los informes seleccionados están dentro de `documentation/historial/<entrega>/`, no en una carpeta independiente de evidencias.

## Reproducción

```bash
apps/services/.venv/bin/python -m pip install -r apps/services/requirements-dev.txt
apps/services/.venv/bin/python -m pytest apps/services/tests -q
apps/services/.venv/bin/python apps/services/scripts/check_launcher.py --report /tmp/launcher.json
```

Requiere PostgreSQL, Redis y MongoDB locales. `REDHOUSE_TEST_MONGOD` permite indicar el binario de MongoDB. Las pruebas crean un entorno temporal propio; no recargan las bases del portal. Los recorridos de navegador del portal se encuentran en `apps/web/tests/`.

La suite cubre contratos JSON/XML/XSD, autenticación y permisos, migraciones, reserva/traslado/custodia, archivos, resiliencia, caché y portal integrado. La comprobación del lanzador recorre preparación, inicio, parada, conflictos y conservación de configuración.

## Resultados

Reorganización del 14/10/2026: **164 pruebas aprobadas** en 597.68 s, **14 comprobaciones reales** del lanzador y **51 visitas de Chrome**. La comparación durante la migración conservó las filas de 111 tablas; se verificaron las 18 cadenas de custodia del entorno regional.

- [Estado y límites de la reorganización](../historial/2026-10-14/REORGANIZACION.md).
- [Validaciones anteriores](../historial/integracion/VALIDACION_HASTA_2026_10_12.md), con sus fechas; no acreditan por sí solas el código actual.

Conservar un informe por ejecución relevante y sus condiciones. No sumar casos repetidos ni declarar éxito por ausencia de errores en una captura. El CI remoto y las plataformas no ejecutadas deben identificarse como pendientes.
