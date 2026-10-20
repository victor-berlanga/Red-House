# Instalación y operación

## Requisitos

Python 3.12+ con `venv` y `ensurepip`, PostgreSQL 14 para un entorno nuevo, Redis 7+ y MongoDB 8.0. Para un entorno existente se conserva el major de PostgreSQL registrado en sus datos. Esta modalidad local no requiere Docker. El segundo parcial incluye además un entorno Docker independiente, descrito en [deployment/README.md](../../deployment/README.md).

En Ubuntu, instala los paquetes del sistema antes de ejecutar el instalador, con un usuario normal. Los binarios deben estar en el PATH o configurados mediante `REDHOUSE_POSTGRES`, `REDHOUSE_INITDB`, `REDHOUSE_REDIS` y `REDHOUSE_MONGOD`. Se busca PostgreSQL también en `/usr/lib/postgresql/<major>/bin/`.

En macOS, `install.sh` puede instalar dependencias faltantes con Homebrew y descargar MongoDB verificado por SHA-256. `scripts/homebrew.sh` es exclusivo de macOS y rechaza Linux.

## Preparación y arranque

Desde la raíz del repositorio:

```bash
bash install.sh
bash start.sh
bash components.sh estado
bash stop.sh
```

El instalador crea entornos Python separados para `apps/web` y `apps/services`. La configuración y los datos persistentes se guardan en `.local/runtime/`, excluido de Git. En un entorno nuevo se crea una base PostgreSQL compartida, cuentas iniciales y configuraciones de Redis y MongoDB; al terminar la preparación se detienen los procesos creados por ella. Una instalación existente conserva sus datos y no vuelve a cargar registros.

`start.sh` inicia bases, API, workers y portal; no instala paquetes ni aplica migraciones. `stop.sh` detiene los procesos de ese entorno sin eliminar datos. El portal utiliza `http://127.0.0.1:5050` por defecto. `estado` informa disponibilidad; no garantiza por sí solo el funcionamiento de todos los procesos de negocio.

```bash
bash components.sh                       # Menú
bash components.sh ms                    # Todas las API y workers
bash components.sh web                   # Solo portal y worker de sesiones
bash components.sh bases                 # Solo infraestructura
bash components.sh inventario            # Una API y su worker
bash components.sh reiniciar donantes
bash components.sh detener web
```

## Windows: BAT mediante WSL

Los cuatro BAT de raíz ejecutan los SH en la distribución Linux predeterminada. No instalan WSL ni distribuciones y no son ejecutables nativos de toda la plataforma. Requieren WSL 2 con Ubuntu preparado según los requisitos anteriores.

```powershell
.\install.bat
.\start.bat
.\components.bat estado
.\stop.bat
```

Usa un clon dentro del sistema de archivos Linux de WSL. No copies entornos virtuales de Windows/macOS ni los archivos físicos de PostgreSQL entre sistemas. Los BAT fijan la raíz del repositorio como directorio de trabajo; `--directory` recibe una ruta Linux. Sus ayudas funcionan sin WSL. La ejecución nativa de estos lanzadores en Windows sigue pendiente de comprobación en ese sistema.

## Directorios y secretos

```bash
bash install.sh --directory /ruta/privada/red-house
bash start.sh --directory /ruta/privada/red-house --web-port 5051
bash stop.sh --directory /ruta/privada/red-house
```

El directorio predeterminado siempre se resuelve desde la raíz del repositorio; una ruta relativa explícita se resuelve desde la carpeta de ejecución. Evita espacios en el directorio de datos por la configuración actual de Redis. No inicies simultáneamente dos copias del mismo entorno: comparten puertos y representan los mismos registros.

`state.json`, los archivos JSON de cada servicio y `web-secrets.env` contienen secretos. No deben adjuntarse a reportes ni versionarse. El portal utiliza `MICROSERVICES_CONFIG`. En modo modular carga configuraciones por dominio con credenciales limitadas; en modo HTTP consume las API. Ningún secreto se publica al navegador.

## Actualizar una instalación existente

Respaldar antes de actualizar el código. Para cambios de esquema, detener las aplicaciones, mantener las bases encendidas y ejecutar:

```bash
bash components.sh detener web
bash components.sh detener ms
bash components.sh bases
apps/services/.venv/bin/python apps/services/scripts/migrate_shared.py --directory .local/runtime
bash start.sh
```

`migrate_shared.py` respalda las bases y configuraciones anteriores, copia y compara filas y publica las conexiones compartidas solo al terminar. Conserva las bases originales y rechaza sobrescribir un destino existente. En un entorno ya compartido no repite la copia. `upgrade.py` verifica la versión global 6; no hay migraciones globales posteriores registradas. Ver [datos y persistencia](Datos_y_persistencia.md).

Para trasladar un entorno detenido se utiliza `apps/services/scripts/relocate.py --source ORIGEN --destination DESTINO`; copia los datos, actualiza rutas de configuración y conserva el origen. No reemplaza un respaldo exportable entre versiones o sistemas.

La reorganización del 14/10 trasladó el entorno de este equipo a `.local/runtime/`. Otras instalaciones anteriores deben trasladarse expresamente: el arranque no crea una instalación alternativa en silencio. Si el entorno predeterminado no está preparado, informa del error.

## Falta venv, ensurepip o pip durante la instalación

El mensaje identifica el Python y el entorno afectados. En Ubuntu instala `pythonX.Y-venv` para la versión seleccionada, desde el mismo proveedor de Python. Por ejemplo, Python 3.12 necesita `python3.12-venv`. Dentro de WSL la corrección se realiza en Ubuntu; instalar Python en Windows no modifica ese intérprete.

Si el entorno existe pero falta pip, el instalador intenta repararlo con `ensurepip --upgrade`. `--no-install` solo comprueba y no repara paquetes. Los errores distinguen causa y solución, conservando el código de fallo. No uses `sudo pip`.

## Diagnóstico

Los logs están en el directorio privado: `<servicio>.log`, `<servicio>-worker.log`, `postgres.log`, `redis.log`, `mongodb.log`, `web.log` y `web-sessions.log`.

- Un puerto ocupado no provoca que el lanzador mate su propietario.
- Si un binario desapareció, repetir el instalador con el mismo directorio permite revisar las dependencias conservando las bases.
- Si un servicio no está listo, revisar su log y `components.sh estado`; no borrar datos para corregir un fallo de proceso.
- Las operaciones por Bash usan un bloqueo compartido. Las llamadas Python directas no toman ese bloqueo.

Este lanzador no es un supervisor de producción. HTTPS, arranque automático del servidor y despliegue en GCE siguen pendientes. El bucket GCS privado del segundo parcial sí está configurado y probado.

## Docker y archivos privados

La guía [Docker del segundo parcial](../../deployment/README.md) contiene instalación desde cero, imágenes por servicio, dos réplicas, variables, redes, puertos, GCS y recuperación. Usa `.local/compose` y volúmenes independientes; no sustituye `.local/runtime` ni sus datos. El portal Docker escucha en 6050 y las API en 6101–6111, solo loopback.

Para ensayar continuidad sobre ese entorno: `apps/services/.venv/bin/python deployment/verify.py --phase all`. Para respaldo y restauración en contenedores nuevos: `apps/services/.venv/bin/python deployment/backup.py --verify`. Los dos comandos escriben únicamente datos ficticios y evidencia en el entorno de ensayo; el segundo pausa sus aplicaciones para obtener un corte coherente.

## Actualización de sesiones del portal (20 de octubre)

Sesiones y tokens cifrados usan Redis con TTL de hasta 24 horas; las concesiones de renovación duran 60 segundos. El portal recibe una ACL exclusiva para `web:*`. La cookie contiene un identificador opaco. Una credencial PostgreSQL separada solo accede a `web_runtime.session_revocations`, donde se guardan cierres y credenciales cifradas pendientes de revocar.

Para actualizar una instalación local existente, con el portal detenido:

```sh
apps/web/.venv/bin/python -m pip install -r apps/web/requirements.txt
apps/services/.venv/bin/python scripts/migrate_web_sessions.py --directory .local/runtime
```

La actualización conserva datos del dominio, claves de la web y configuración ajena a las sesiones. Las cookies previas dejan de servir: los usuarios deben iniciar sesión nuevamente. Los archivos privados del almacén anterior se conservan como respaldo y ya no se montan ni consultan. Los pendientes antiguos aún vigentes requieren exportación controlada antes del cambio; no deben eliminarse junto al respaldo.

El worker reintenta cada 30 segundos. Si Redis falla al cerrar sesión, PostgreSQL conserva la marca y el worker revoca después de la recuperación. Si PostgreSQL falla, las rutas protegidas responden 503; logout elimina la cookie y devuelve 503 porque no puede confirmar el cierre global. Los respaldos deben incluir el esquema `web_runtime`, la persistencia/ACL Redis y `SECRET_KEY`; la clave cifra los tokens.
