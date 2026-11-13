# Recuperación coordinada aislada — 13 de noviembre de 2026

Resultado: **1 caso aprobado en 91,28 s**, con PostgreSQL, MongoDB y Redis reales en procesos temporales y datos sintéticos. El código base era el commit `beb71cc12b3fdb11a997777d913d569143b408c8` y el ensayo adicional quedó identificado por los hashes de esta evidencia. El caso restauró un clúster PostgreSQL nuevo con roles y contraseñas SCRAM del fixture, MongoDB desde copia física bloqueada, Redis desde RDB y ACL, y el volumen de archivos en otro directorio. Se reutilizaron las claves de firma de aplicación del fixture. No se accedió a GCP ni a una instalación real.

El corte cerró todos los listeners HTTP del fixture, comprobó que sus puertos no aceptaban conexiones y verificó que no había workers. Bajo ese corte se guardaron las cuatro fuentes. Tras el corte se crearon un documento y un evento, se cambió un marcador Redis y se revocó una sesión. La copia restaurada conservó el documento y el evento `FILE_VERIFIED` previos y no contenía el documento ni el evento posteriores. También se compararon proveedor, ruta, generación, SHA-256, análisis CLEAN, bytes y permisos SQL; el servicio de Auditoría accedió a MongoDB con su credencial restaurada.

Antes de habilitar el backend restaurado se invalidaron explícitamente todas las sesiones, renovaciones, pruebas y cachés de permisos de la instancia Redis desechable. La prueba confirmó que la sesión anterior existía en la copia, pero que, tras invalidarla, JWT, refresh y capacidad previamente emitida fueron rechazados mientras seguían vigentes. Otro tenant recibió 403; una sesión nueva autorizada descargó los bytes correctos. Al ocultar el objeto o cambiar los permisos del directorio privado, la descarga devolvió 503, sin llamar a GCS; al restaurar el archivo y permisos se recuperó la descarga.

- Última confirmación documental conservada: `2026-11-13T21:04:20.255014+00:00`.
- Incidente simulado: `2026-11-13T21:04:44.041252+00:00`.
- RPO observado del documento: **23,787 s**; se perdieron de la copia, intencionalmente, un documento y su evento posteriores al corte.
- RTO observado desde el incidente hasta la descarga autorizada: **21,733 s**.
- Dump PostgreSQL: 734.571 bytes; roles privados: 4.442 bytes; volumen: un objeto.
- Escáner: **receptor doble**, no ClamAV real en esta ejecución. El resultado CLEAN demuestra conservación del registro de prueba, no capacidad antivirus real.

El tráfico de aplicación restaurado se ejerció mediante `ApplicationKernel` y `test_client` dentro del proceso; no se restauraron ni probaron listeners de aplicación, TLS o proxy. Los tiempos son observaciones de este caso; no son objetivos aprobados, SLA ni evidencia de alta disponibilidad. No incluyen detección de incidente, reconstrucción de host, descarga de copias externas, recuperación de claves de firma o sesiones web, escrituras concurrentes, GCS real ni recuperación a través de infraestructura independiente. La invalidación de sesiones fue una acción explícita del ensayo, no un mecanismo automático ya implantado para producción. No se atribuye este resultado al entorno GCP.

La restauración importó todos los roles SQL del volcado y la ACL Redis; se compararon cuatro privilegios SQL representativos y se ejercieron conexiones de Identidad, Documentos y Auditoría. No se verificaron exhaustivamente todos los privilegios ni todas las configuraciones de rol específicas por base.

Mejora pendiente: retirar los cuerpos de respuesta de los mensajes de aserción de login y descarga, para impedir que un fallo futuro vuelque accidentalmente un token o capacidad. La ejecución conservada aprobó y su JUnit no contiene esos cuerpos.

`intento1-junit.xml` conserva las propiedades medidas; pytest avisó que `record_property` no es compatible con el formato xunit2, aunque dichas propiedades constan en el XML. Los manifiestos `intento1-before.sha256` e `intento1-after.sha256` coincidieron. El plan editorial se actualizó después de la ejecución para reflejar los resultados; el código del ensayo no cambió. Los procesos se cerraron y el directorio privado de la ejecución, con copias y credenciales sintéticas, se eliminó.

## Reproducción

Usar un directorio temporal exclusivo para el fixture y la carpeta de pytest; guardar el JUnit fuera de ese directorio y eliminarlo solo después de confirmar que terminaron los procesos. No reutilizar un PostgreSQL, MongoDB, Redis o volumen existente. La ejecución real usó el siguiente comando desde el worktree, con una ruta temporal recién creada en lugar de `$RH_LAB`:

```sh
RH_BASE=/Users/victorberlanga/Programacion/integracion/Red-House
RH_LAB="$(mktemp -d /private/tmp/redhouse-recovery-20261113.XXXXXXXX)"
mkdir -p "$RH_LAB/platform"
REDHOUSE_TEST_ROOT="$RH_LAB/platform" \
REDHOUSE_TEST_MONGOD="$RH_BASE/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_STARTUP_TIMEOUT=120 \
"$RH_BASE/apps/services/.venv/bin/python" -m pytest \
  apps/services/tests/test_storage_recovery.py \
  --basetemp="$RH_LAB/pytest" \
  --junitxml=/ruta/privada/nueva/recuperacion.xml -q
```

Se omitió `REDHOUSE_TEST_CLAMD_PORT` deliberadamente, por lo que se usó el receptor doble. El entorno debe permitir sockets TCP locales. No sobrescribir el JUnit conservado; revisar que no permanezcan procesos del laboratorio antes de borrar exclusivamente el directorio temporal creado para la reproducción.
