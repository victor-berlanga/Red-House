# Serie de lectura sostenida: preparación

La serie prepara una sola población sintética y mantiene seis perfiles con familias de sesión independientes. Ejecuta, en orden, 12 usuarios con caché activa, 12 con bypass, 12 activos, 12 con bypass y 24 activos. Cada fase usa 30 s de calentamiento y 120 s medidos. Solo si la fase de 24 cumple los criterios y las guardas siguen vigentes se ejecuta estrés de 36 usuarios durante 60 s; después se mide recuperación con seis usuarios durante 60 s. Si una fase no completa las verificaciones del arnés, se detiene la serie. Si 24 completa la ejecución pero no alcanza el objetivo, se omite estrés y se mantiene recuperación, siempre que las guardas lo permitan.

La barrera espera todas las sesiones antes de lecturas. MFA se serializa por cuenta y periodo TOTP, después del periodo usado para enrolar o ejecutar la fase anterior; el presupuesto de autenticación crece con la multiplicidad. Los factores permanecen en memoria y pasan al proceso por descriptor anónimo. Se comprueban la cantidad de familias por cuenta, IDs únicos, revocación SQL y ausencia en Redis; un fallo final de drenado o de usuario invalida la fase. Redis continúa activo para autorización en ambos modos de caché.

La validez de ejecución se informa separada de la aceptación: para esta última se exigen p95 de lecturas inferior a 2000 ms y menos de 1 % de errores, conforme a `carga-20261113/PLAN.md`, además de señales de caché coherentes. Se registran mediana, p95, p99 y contadores observados HIT/MISS/BYPASS. Las respuestas HTTP 429 se identifican como cuota y se cuentan como fallos; no prueban saturación de infraestructura. Se mantienen las guardas de presupuesto, propiedad, procesos y limpieza existentes; no se alteraron cuotas ni pools del producto.

La preparación pasó 29 pruebas puras y Ruff, observados en salida de herramienta sin JUnit ni log archivados. Después se añadió un caso dirigido de error durante el drenado final: 1/1 y Ruff pasaron por separado. Estas comprobaciones no ejecutaron motores. **La serie real aún no se ha ejecutado**, por lo que no existen resultados de capacidad, comparación de caché ni recuperación para este plan.

Comando previsto desde la raíz, con una ruta nueva para log privado y sin recursos de nube:

```sh
umask 077
mkdir -m 700 .local/artifacts/carga-serie-20261114
PYTHONPATH=.:apps/services apps/services/.venv/bin/python apps/services/scripts/prepare_load.py --scale-percent 10 --seed 20261113 --mongod "$PWD/.local/tools/mongodb-8.0.17/bin/mongod" --sustained-series > .local/artifacts/carga-serie-20261114/runner.private.log 2>&1
```

El fixture crea su propio directorio temporal y deja allí los resultados privados. Registrar el directorio y revisar los resúmenes antes de publicar evidencia; no copiar secretos ni logs privados al repositorio. La ejecución requiere una ventana exclusiva y debe respetar las guardas de recursos.
