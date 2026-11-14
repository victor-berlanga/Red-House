# Comprobación de firmas cargadas en imagen real

El ensayo usó la imagen ClamAV fijada por digest, el daemon existente y el script SHA-256 `71b312e8edac0e9b374f1b60ffa9f36153a31e6bf6049ab9e929e6e4ad6e4049`. El [resultado original](readiness-image-test.json) registra tres casos: base real saludable, cabecera sintética vencida y versión sintética distinta. No se instalaron el helper ni un healthcheck; los temporales se eliminaron y no se modificaron las firmas reales.

El [arnés exacto](probe_readiness_image.py) se transmitió por SSH y se ejecutó como `sudo python3 -`, recibiendo el código por entrada estándar. Depende del módulo privado del despliegue en `/tmp/redhouse-scanner20-20261113/deploy.py` y del helper almacenado en su directorio de entrada; no es un procedimiento autónomo ni una autorización para repetirlo contra producción. La comparación de cabecera y `VERSION` no comprueba la integridad completa de las bases ni todas sus versiones cargadas.

Las pruebas locales de límites y carreras usan dobles; no sustituyen la validación de instalación, recreación o ejecución periódica bajo Docker.
