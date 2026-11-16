# XML concurrente y configuración de carga — 16/11/2026

**Último ensayo aprobado:** doce identidades activas durante calentamiento y medición, 1.396 HTTP medidos sin fallos, p95 máximo de consultas 520 ms y de recorridos 2.500 ms. Las 822 escrituras del recorrido completo quedaron confirmadas, sin ciclos incompletos, y se comprobaron doce repeticiones idempotentes. [Resultado aprobado](02-parser-aislado-aprobado.json). No sustituye los ensayos fallidos anteriores.

## Escenario y fallo previo

Se conservaron las doce cuentas —seis donantes JSON y seis operadores XML— y se crearon por API una campaña y horarios sintéticos nuevos para cada ejecución. Una API y un worker por cada uno de los doce servicios, con `DATABASE_POOL_SIZE=2` e intervalo worker de dos segundos, como los parámetros del despliegue generado. Los JSON originales permanecieron intactos; las copias derivadas con credenciales son privadas. Se mantuvieron cuotas y límites: 30 s de calentamiento, 120 s de medida, p95 de consulta menor de 2 s, p95 de recorrido menor de 5 s y comprobación de propagación dentro de 30 s.

Esta topología local admite hasta 48 conexiones de pools; se reservaron otras cinco de margen operativo. PostgreSQL informó máximo 100, tres reservadas y un cliente existente al verificar. Los pools son perezosos: ese techo no significa 48 conexiones simultáneas observadas. No representa las dos réplicas de GCP ni certifica su capacidad. Las pruebas usan población sintética y generador/servicios en la misma computadora. Son escenarios de configuración distinta respecto del anterior sin pool API; no una comparación A/B controlada.

La [primera ejecución de esta configuración](01-xml-calentamiento-fallido.json) terminó con **exit 1**. Dos operadores recibieron 500 `internal_error` al compilar el XSD de `ResourceCreate`; los logs correlacionaron `XMLSchemaParseError` con esos POST XML, antes de la operación transaccional. Los otros cuatro operadores XML sí completaron operaciones. El calentamiento registró cuatro fallos contados entre HTTP y marcadores de recorrido, y calentamiento/medición conservaron mínimo diez usuarios. Sus 1.264 HTTP medidos sin fallos, p95 bajos y propagación confirmada no acreditan doce usuarios. Hubo 717 escrituras confirmadas y dos intentos no comprometidos; la ejecución se conserva rechazada.

## Corrección y límites del diagnóstico

El XSD y ambos cuerpos conservados validaron secuencialmente. Una ejecución pura con ocho hilos reprodujo un fallo interno de libxml2 2.14.6 al compilar el mismo XSD intercalado con parseo. Una compilación con parser explícito completó 640 comprobaciones sin error. Sin embargo, la comparación posterior en procesos nuevos también completó sin errores 640 compilaciones y 640 parseos tanto en baseline como en candidato: el fallo es intermitente, y esa comparación no demuestra por sí sola causalidad.

`codec.parse` ahora crea un parser independiente para analizar el XSD generado, con DTD, entidades externas, acceso a red y árboles enormes deshabilitados. La validación XSD permanece obligatoria y los bytes del esquema no cambian. No se captura un fallo del compilador para aceptar el cuerpo ni se sustituye XML por JSON. La [documentación oficial de lxml](https://lxml.de/FAQ.html#can-i-use-threads-to-concurrently-access-the-lxml-api) contempla parsers propios y también aislamiento por hilo del predeterminado; no se afirma que el predeterminado sea siempre compartido o inseguro.

[Once pruebas integradas](unit-junit.xml) aprobaron en 10,44 s: XML válido e inválido concurrentes, paridad JSON/XML de inventario, muestra y HLA, rechazo XXE/DOCTYPE, duplicados y propagación de fallo del compilador sin bypass. La secuencia diagnóstica que invoca directamente el parser predeterminado de la biblioteca permanece privada: no se añadió una prueba CI ajena al camino corregido. El archivo de prueba se ordenó y formateó después; no se repitieron las pruebas por ese cambio de estilo. Ruff no encuentra problemas en el nuevo test ni hallazgos nuevos en `codec.py`; dos observaciones preexistentes de este último permanecen.

## Aceptación HTTP posterior

Después del cambio se ejecutó **una sola nueva carga**, con todos los operadores XML activos: doce usuarios mínimos en ambas ventanas, cero fallos de calentamiento y medición, 218 recorridos medidos y 274 completos incluyendo calentamiento/drenado. Las 822 escrituras y doce replays quedaron reconciliados. Al consultar el oráculo final, los eventos y avisos esperados ya se confirmaron en **0,081 s de espera/verificación**, dentro del límite de 30 s; esta cifra no es una distribución de latencia individual de entrega.

Las doce familias de carga y la de preparación se verificaron revocadas, con cierre de procesos y retiro del candado. Fuentes, configuración efectiva y población histórica comprobada conservaron sus huellas. El wrapper comparó sus mapas de fuente en memoria; no persistió el mapa inicial. La vinculación con el hash de `codec.py` se documenta mediante el corte observado por dirección, la prohibición de cambios durante la ejecución y la comprobación de igualdad del wrapper, sin inventar un artefacto de inicio.

El último resultado valida este escenario HTTP real; no prueba ausencia universal del fallo intermitente ni todos los escenarios de estrés. La corrección de `codec.py` todavía requiere publicación en GCP en este corte. Los directorios privados de diagnóstico y ejecución se conservan bajo `.local/artifacts/xml-resource-schema-20261116/`, `.local/artifacts/carga-20261116-api-pool2-preparacion/` y `/private/tmp/rh-load-c92ed10k/`.

Prueba pura reproducible, sin motores:

```sh
PYTHONPATH=apps/services apps/services/.venv/bin/pytest --noconftest -q apps/services/tests/test_codec_concurrency.py
```
