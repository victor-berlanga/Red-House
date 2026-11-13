# Feed público — 13 de noviembre de 2026

**Dos casos aprobados en 70,92 s**, uno JSON y otro XML, contra servicios HTTP y PostgreSQL/Redis/MongoDB reales en laboratorio temporal aislado. Cada caso preparó 110 campañas sintéticas mediante SQL: 105 públicas vigentes y cinco excluidas por publicación/estado/vigencia. Esto prueba lectura y paginación, no el formulario de creación de campañas. No se accedió a GCP ni al iPhone.

Se recorrieron seis páginas de 20 conservando orden, total y filtros; la última tuvo cinco registros y la siguiente quedó vacía. El conjunto estable no presentó duplicados ni truncamiento. Se verificaron las cinco propiedades públicas, búsqueda por sede, caracteres `%`, `_` y `\` literales, fechas inclusiva/exclusiva, límites de paginación, duplicados y parámetros no permitidos, NUL y ventana inválida. El endpoint anterior mantuvo su respuesta. Una revisión independiente detectó previamente que NUL llegaba a psycopg y habría causado error interno; se corrigió antes del ensayo.

`attempt1.log` y `attempt1-junit.xml` conservan la ejecución; ambos se revisaron sin encontrar contraseña del fixture ni JWT. Los 173 archivos de `sources-before.json` y `sources-after.json` coinciden: módulos Python de servicios/soporte y archivos específicos de prueba/contrato. `artifacts.sha256` identifica estos cuatro artefactos. No se trata de un hash de todo el repositorio ni una ejecución nativa del cliente móvil.

Reproducción desde la raíz, con dependencias del proyecto y autorización para sockets locales:

```sh
RH_LAB="$(mktemp -d /private/tmp/redhouse-feed.XXXXXXXX)"
mkdir -p "$RH_LAB/platform"
REDHOUSE_TEST_ROOT="$RH_LAB/platform" \
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_STARTUP_TIMEOUT=120 \
apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_public_campaign_feed.py -q --tb=short --show-capture=no \
  --basetemp="$RH_LAB/pytest" --junitxml=/ruta/privada/nueva/feed.xml
```

El fixture cerró los procesos. Su directorio temporal se elimina por separado tras revisar reportes, sin afectar otros laboratorios. La prueba utiliza HTTP local sin proxy; no demuestra TLS, Nginx, carga, estabilidad entre páginas bajo publicaciones concurrentes, UI nativa ni despliegue. CONT-06 permanece parcial hasta comprobar los recorridos del cliente con este endpoint y sus filtros.
