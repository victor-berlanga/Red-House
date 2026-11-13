# Gateway ejecutado y red privada — 13/11/2026

La suite conjunta ejecutó 44 casos: 40 aprobados y cuatro fallidos en 204,62 segundos. Los fallos corresponden a contratos de carga local de evidencia (JSON/XML) y al nuevo evento de verificación de identificador de traslado (JSON/XML). No se presenta la suite íntegra como aprobada. [Resultado original](../almacenamiento-local-20261113/final-junit.xml) y manifiestos de fuentes en el mismo directorio; antes y después coinciden 1286 archivos. La corrección y repetición de esos casos se registran por separado.

Repetición posterior: siete casos dirigidos aprobados en 112,44 s, incluyendo los cuatro fallidos, reasignación concurrente y regresión GCS con doble. [JUnit dirigido](../almacenamiento-local-20261113/dirigida-junit.xml). No se suman ambos recuentos como una ejecución única. El evento final es `SHIPMENT_RESOURCE_IDENTIFIER_VERIFIED`, con ámbito del traslado y sin presumir el dispositivo usado.

En esta pasada aprobaron:

- Dos casos de agenda Donantes JSON/XML: próxima cita por horario vigente y listado paginado con título y horario, incluidas citas antiguas sin horario. Conserva el contrato anterior y añade `/appointments/agenda`.
- Dos casos de autorización de etiquetas JSON/XML: control de versión, institución que mantiene actualmente la unidad, motivo, autorización humana, repetición idempotente, concurrencia y rechazo tras cambio de custodia. Autorizar una emisión no demuestra impresión física.
- Ocho casos de límites del proxy: peer explícito, saneamiento de cabeceras, cuotas aisladas, Waitress real y configuración generada. Los alias de gateway, web y API solo se publican en la red `data`; los destinos de Nginx usan esos alias para evitar direcciones ambiguas en contenedores con dos redes.
- Un caso Nginx HTTPS/WSS real: JSON/XML autenticados, rechazo sin token, límite de cuerpo API, rutas internas bloqueadas, publicación y recepción persistida de una posición sintética, caída de una réplica y de ambas, recuperación por cursor y rechazo de donante.
- Almacenamiento HTTPS con portal autónomo: carga de PNG mayor que 256 KiB, creación exclusiva, análisis ClamAV real, descarga íntegra, revocación y ausencia de capacidades en el log capturado. Los detalles y límites de almacenamiento se registran en su informe propio; no se suman dos veces estos casos.

## Entorno y reproducción

macOS local, PostgreSQL/Redis/MongoDB temporales, datos sintéticos, Nginx compilado desde fuente oficial 1.30.6 y ClamAV 1.5.4 con firmas locales. SHA-256 del archivo fuente Nginx: `3cf46f5ed7504d460125866b7bea99fb357f31d887e2e63b35503310e9b8b6c8`. El archivo procede de `https://nginx.org/download/nginx-1.30.6.tar.gz`; no se atribuye verificación PGP. Primera compilación interrumpida deliberadamente por presión de memoria; se completó luego con `make -j1` y `make install`.

```sh
REDHOUSE_TEST_NGINX="$PWD/.local/tools/nginx-1.30.6/sbin/nginx" \
  apps/services/.venv/bin/python \
  documentation/evidencias/entrega-final/almacenamiento-local-20261113/run-final.py
```

El arnés inicia ClamD temporal y exige Nginx. Las pruebas de gateway generan certificado efímero para loopback, confiado explícitamente por el cliente; conservan verificación TLS. Se sustituyen exclusivamente destinos/puertos/rutas temporales del Nginx generado para conectar con el laboratorio.

## Límites

No es despliegue GCP, prueba Docker DNS ni ensayo del Nginx 1.28 que declara Compose. La unicidad de alias se verifica estructuralmente aquí y requiere comprobar resolución y dirección real al desplegar. El fallo de Transporte se induce sobre las dos réplicas utilizadas por ese gateway aislado; otros listeners de la fixture permanecen. El caso WSS usa servicios reales y persistencia, sin ejecución de clientes móviles o de escritorio. No mide SLA, rendimiento bajo carga ni recuperación de un host completo.

Si cambia la dirección privada del gateway, deben reiniciarse sus consumidores para fijar el nuevo peer autorizado. En publicación se recrea primero gateway, después consumidores y se recarga Nginx al final; no se recrea gateway después de fijar la confianza.
