# Despliegue aislado del segundo parcial

El despliegue en Google Compute Engine está documentado en [gcp/README.md](gcp/README.md), con acceso público por IP y HTTPS, copia de datos y scripts `gcloud`. Esta guía conserva la operación del Compose local.

Docker Compose v2 y Python 3.12+ para generar secretos. No se montan archivos
físicos de `.local/runtime`. Los datos Docker se guardan en volúmenes propios del
proyecto `redhouse-parcial2`; la configuración privada está en `.local/compose`.

## Instalación desde un clon limpio

```sh
python3 deployment/prepare.py
docker compose --profile install build bootstrap
docker compose up -d --wait postgres redis mongodb
docker compose --profile install run --rm bootstrap
docker compose --parallel 2 build
python3 deployment/start.py
docker compose ps
```

`prepare.py` conserva una configuración existente. `bootstrap` es una operación
explícita para una base vacía: usa el SQL compartido versionado, crea vistas y
permisos por servicio, ACL Redis, claves y cuentas ficticias. Una repetición
verifica versión 6, aplica la migración documental aditiva y prepara el esquema técnico `web_runtime` y la ACL Redis del portal. Nunca se aplica
SQL destructivo al iniciar una API. Si la primera instalación queda interrumpida
antes de su marcador, revisar las bases y el log; no borrar volúmenes ni repetir
credenciales a ciegas. Las cuentas iniciales y su contraseña aleatoria están en
`state.json` privado; no copiarlas a informes.

Portal: `http://127.0.0.1:6050`. API por gateway: 6101 Identidad, 6102 Donantes,
6103 Receptores, 6104 Inventario, 6105 Compatibilidad, 6106 Priorización/geografía,
6107 Transporte, 6108 Custodia, 6109 Alertas, 6110 Auditoría y 6111 Monitoreo.
Swagger está en `/docs/` de cada puerto. Bases sin puertos publicados.

`start.py` espera salud por pares antes de iniciar el siguiente dominio. Inicia los consumidores de eventos antes que sus productores para drenar las colas conservadas. Esto limita el coste de arranque simultáneo de API y workers; conserva los mismos deadlines de salud. El arranque masivo puede saturar un equipo de desarrollo.

## Procesos y continuidad

Cada dominio tiene Dockerfile e imagen propios. Las instancias `-a` y `-b` ejecutan
una API y un worker supervisados: si uno termina, el contenedor termina y Docker
lo reinicia. El health check comprueba HTTP y el latido del worker de esa instancia,
además del latido SQL y las dependencias compartidas. El monolito tiene backend y
workers propios con el mismo código de aplicación. Los módulos usan credenciales
limitadas; el portal no depende de las API HTTP para ejecutar negocio.

El sondeo Docker usa `python -S` y una petición HTTP HEAD mediante socket, sin
importar la aplicación en cada verificación. Conserva límites de conexión/lectura
y comprueba la respuesta real de readiness. Las aplicaciones reutilizan conexiones
PostgreSQL mediante pools limitados a dos por credencial y módulo; no repiten
escrituras cuando se pierde la conexión.

Nginx resuelve DNS Docker y distribuye cada API entre dos instancias. Reintenta
conexiones fallidas; no activa `non_idempotent`. Una escritura ya enviada cuya
respuesta se pierde requiere consultar la operación antes de repetir con su misma
clave. [Reglas de reintento Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream).
El descubrimiento sigue [DNS de Compose](https://docs.docker.com/compose/how-tos/networking/).

Caer todas las API de un propietario conserva las operaciones web; los clientes
JSON/XML que necesitan ese propietario reciben fallo controlado. PostgreSQL,
Redis, MongoDB, el host Docker y el gateway siguen siendo puntos comunes de fallo.
No se promete alta disponibilidad de toda la infraestructura. La matriz detallada
está en [Cierre del segundo parcial](../documentation/markdowns/Cierre_segundo_parcial.md).

## Secretos y nube

Los contenedores de aplicación usan UID 10001, sistema de archivos de solo lectura,
directorio temporal privado, sin capabilities y con `no-new-privileges`. Cada API
monta únicamente su configuración. El monolito monta las configuraciones de sus
módulos, sin credenciales de administración de las bases. Los procesos de bootstrap
y las imágenes oficiales de bases usan su mecanismo de inicialización autorizado.

Para GCS local se requiere Google Cloud CLI y acceso a los recursos autorizados:

```sh
gcloud auth application-default login --project=sistemas-integracion-01 --impersonate-service-account=red-house-archivos@sistemas-integracion-01.iam.gserviceaccount.com
python3 deployment/configure_gcs.py --adc "$HOME/.config/gcloud/application_default_credentials.json" --bucket red-house-evidencias-sistemas-integracion-01 --project sistemas-integracion-01
python3 deployment/start.py
```

El bucket y los permisos IAM deben existir previamente. La autenticación requiere
una cuenta con permiso de impersonación. `start.py` incorpora automáticamente el
override privado para Transporte y la web. El configurador conserva una copia ADC
existente; si se reautoriza la cuenta, actualizar también `.local/compose/gcs-adc.json`
con la nueva ADC y recrear esas instancias para cargarla. Conservar el directorio
privado con modo 0700 y el secreto legible por el UID del contenedor mediante su
montaje controlado. Las credenciales permanecen fuera de imágenes y Git.
En GCE se debe usar identidad adjunta a la VM;
las credenciales de desarrollo del usuario no son el mecanismo de producción.
El Compose base publica HTTP solo en loopback para la demostración local. El
override de GCE agrega HTTPS público; su evidencia se conserva por separado en
[los resultados GCP](../documentation/evidencias/gcp/RESULTADOS.md).

## Reinicio y actualización

```sh
docker compose stop
python3 deployment/start.py
docker compose ps
docker compose build donantes-a
docker compose up -d --no-deps --wait --force-recreate donantes-a
docker compose up -d --no-deps --wait --force-recreate donantes-b
docker compose down
```

Repetir la secuencia A/B por propietario, incluyendo Identidad y Monitoreo. Verificar
negocio entre ambas sustituciones. No recrear ambas instancias simultáneamente.
El esquema y los contratos deben seguir siendo compatibles con las dos versiones
durante la transición. El monolito fija su propia imagen; actualizar una API no
modifica su código. Una modificación de reglas requiere desplegar también una
versión compatible del monolito. No ejecutar `down -v`: elimina persistencia.

## Respaldo y recuperación

Exportar PostgreSQL con `pg_dump` y roles con `pg_dumpall --globals-only`, MongoDB
con `mongodump` autenticado, y Redis mediante su AOF/RDB consistente. Conservar
también la configuración privada y las versiones de imágenes, cifradas y con acceso
limitado. Pausar las escrituras antes de tomar un respaldo coordinado entre almacenes.
Restaurar en volúmenes nuevos; comprobar cuentas, cantidades, idempotencia, outbox y
cadenas antes de cambiar conexiones. Nunca restaurar encima del entorno habitual
para ensayar. Los objetos GCS referenciados deben conservar sus generaciones.

Los resultados verificados y las limitaciones se registran en `PROJECT_STATUS.md`;
la existencia de este procedimiento por sí sola no acredita una restauración.

## Ensayo reproducible y respaldo verificado

```sh
apps/services/.venv/bin/python deployment/verify.py --phase all
apps/services/.venv/bin/python deployment/backup.py --verify
```

`verify.py` realiza reservas/traslados, consultas JSON/XML, detiene las once réplicas A, detiene todas las API para operar desde la web, construye y sustituye Inventario por etapas y reinicia los almacenes. Guarda respuestas redactadas y comprobaciones SQL. La actualización diferencia recreación de una imagen idéntica y sustitución por otro ID de imagen.

`backup.py` pausa las aplicaciones de este Compose, exporta PostgreSQL con roles, MongoDB y Redis RDB después de `SAVE`, y conserva la configuración privada. `--verify` restaura en tres contenedores nuevos sin puertos publicados. Compara conteos y hashes de todas las filas SQL y documentos MongoDB, y comprueba el valor/TTL de una clave ficticia Redis. Copia los archivos Redis a su volumen nuevo, preservando intactos los archivos del respaldo; al terminar restaura por pares únicamente las aplicaciones que estaban encendidas. Los backups contienen secretos: permanecen bajo `.local/compose/backups`, nunca en Git. El informe público contiene únicamente conteos, hashes y estados. Los objetos GCS no se descargan en ese respaldo; conservar las generaciones referenciadas y la política privada del bucket es parte de la recuperación.

La restauración espera al servidor definitivo de cada imagen. MongoDB restaura
primero `admin` y luego las bases `rh_*` mediante un proceso autenticado nuevo.
Restaurar `admin` reemplaza credenciales; mezclar ese cambio con la creación de
índices produjo un fallo de autenticación en el ensayo. También se comparan hashes
de usuarios y roles sin publicar sus documentos.
[Comportamiento documentado de mongorestore](https://www.mongodb.com/docs/database-tools/mongorestore/).

Para certificar un clon de la versión local en desarrollo, detener este Compose y ejecutar `python3 deployment/check_clean_clone.py`. El script crea una instantánea Git temporal de los archivos no ignorados, clona esa instantánea e instala datos nuevos en un proyecto `redhouse-clean-<identificador>` exclusivo de esa ejecución. No modifica ni publica commits del repositorio original. Al terminar detiene sus contenedores y conserva los volúmenes para diagnóstico. Después, `python3 deployment/start.py` recupera la demostración habitual.

Si el respaldo forma parte de ese mantenimiento, `backup.py --verify --leave-stopped`
mantiene las aplicaciones de demostración apagadas después de verificar los datos.
El informe registra explícitamente cuáles quedan detenidas. Esto permite ejecutar
el clon limpio antes de recuperar la demostración mediante `start.py`.

## Actualizar las sesiones de una instalación existente

```sh
docker compose stop web
docker compose --profile install build bootstrap web
docker compose up -d --wait postgres redis mongodb
docker compose --profile install run --rm bootstrap
python3 deployment/start.py
```

El bootstrap agrega `web_runtime.session_revocations` y una credencial PostgreSQL limitada; prepara la ACL `web_sessions` solo para las claves `web:*`. Conserva las credenciales si se repite. Las sesiones activas cifradas y las concesiones pasan a Redis. El portal deja de montar almacenamiento local para sesiones; los archivos privados anteriores permanecen como respaldo. Los usuarios deben iniciar sesión nuevamente. Conservar o exportar los pendientes de revocación anteriores todavía vigentes antes del cambio.

El respaldo incluye la tabla técnica, sus permisos y las sesiones Redis; su verificación compara también `web_runtime.session_revocations`. No hay cambios en las 71 tablas del dominio.

Verificación reproducible de sesiones (portal iniciado):

```sh
apps/services/.venv/bin/python deployment/verify_web_sessions.py
```

Comprueba login, renovación, cierre, rechazo de cookie cerrada, TTL y cifrado Redis, rol PostgreSQL limitado y ausencia de volumen local de sesiones. El informe registra las API realmente encendidas durante la prueba.

## Auditoría y hallazgos: esquema 7

El incremento de auditoría agrega tres tablas de seguimiento: 74 tablas de dominio y 75 contando las revocaciones del portal. Las instalaciones con esquema 6 requieren respaldo y migración aditiva antes de arrancar el código nuevo. `python3 deployment/migrate_audit.py --directory /ruta/privada/de/compose` respalda PostgreSQL/roles y aplica la migración; no recrea la base ni modifica eventos históricos. Repetirlo sobre versión 7 no vuelve a migrar.

Consultar [procedimiento y permisos](../documentation/markdowns/Auditoria_y_formularios.md#actualización-conservando-datos) y [evidencia del incremento](../documentation/evidencias/auditoria-formularios/RESULTADOS.md) antes de atribuir estos cambios al despliegue público.
