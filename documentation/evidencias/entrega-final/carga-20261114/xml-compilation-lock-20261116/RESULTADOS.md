# Compilación XML concurrente: corrección y límites

Fecha: 16 de noviembre de 2026. La preparación de publicación se detuvo antes de cambiar servicios activos.

## Hallazgo real

La imagen aislada de Alertas construida en `sistemas-integracion-01/red-house/me-central1-a`, Python 3.13.18, lxml 6.1.3 y libxml2 2.14.6, produjo `XMLSchemaParseError` al construir el XSD: `the given type is not a built-in type`. Usaba el parser propio del commit 45a70ab. Por ello, el pase local previo con doce identidades no acredita una resolución universal. La infraestructura y las aplicaciones de la publicación server21 continuaron activas; no hubo release ni gate de mantenimiento en este intento.

Se conservan por separado los errores de preparación previos: importación de un servicio no empaquetado en la imagen aislada y `NameError: TAG` del primer helper. El probe posterior alcanzó el compilador real y falló allí. El primer lanzamiento del nuevo discriminante se detuvo localmente al detectar cambio del hash del runner; no se conectó. Ninguno se presenta como aprobación.

## Cambio

Un candado por proceso protege la construcción de esquemas en `codec.parse`, `tracking_contracts.decode` y el envelope XML. La generación del XSD, su parsing y compilación quedan dentro. Cada petición conserva su validador y sus errores; la validación y el negocio quedan fuera. El caché existente del envelope permanece. No se omite XSD, no se aceptan entidades externas y no se incorpora una dependencia.

## Evidencia

- 14 pruebas dirigidas aprobadas, sin motores, HTTP ni bases de datos, en 26,62 s. Incluyen un proceso nuevo con tres constructores reales, nueve hilos y 216 intentos: 72 válidos y 144 rechazos de duplicados/XXE. [Recibo](unit.json) y [JUnit](unit.xml); únicamente se retiró hostname de la copia pública.
- Un control y un candidato fríos sobre la misma imagen GCP, ocho hilos, 192 intentos por variante. Ambos pasaron: 64 válidos, 64 duplicados rechazados y 64 XXE rechazados. El candidato usó el archivo real montado en lectura; el control usó la imagen sin ese montaje. [Comparación completa](gcp-isolated-comparison.json).
- Contenedores temporales ejecutados como UID/GID 10001, sin red y con imagen de solo lectura. Ambos terminaron normalmente y se comprobó su ausencia; no hubo limpieza forzada ni cambio del runtime activo.

El comparativo **no reprodujo** el fallo en su control. Acredita funcionamiento del candidato, no identifica causalmente una versión defectuosa de libxml2. Los 1,039 s del control y 2,829 s del candidato son tiempos de este probe; no son latencia HTTP ni comparación de capacidad. La compilación serializada puede introducir espera y queda pendiente medirla con carga HTTP.

## Reproducción y pendientes

Los tests están en `apps/services/tests/test_xml_compilation_isolation.py`, `test_codec_concurrency.py` y los dos casos enumerados en el recibo. Ejecutar la selección con el entorno de servicios y `pytest --noconftest`, sin iniciar motores. El [probe](probe.py) y [runner remoto](run_remote.py) fijan hashes e imagen; requieren preparar explícitamente la fuente candidata exacta. No administran credenciales ni publican servicios.

Faltan construcción/publicación de las imágenes finales con las tres fuentes, controles JSON/XML por réplica y medición HTTP posterior. El probe remoto cubre `codec.parse`; la cobertura conjunta de tracking/envelope corresponde al test local, no a ese contenedor. Etapas 06–07 permanecen abiertas.
