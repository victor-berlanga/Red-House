# Instalación y operación

## Requisitos

Python 3.12+ con `venv` y `ensurepip`, PostgreSQL 14 para un entorno nuevo, Redis 7+ y MongoDB 8.0. Para un entorno existente se conserva el major de PostgreSQL registrado en sus datos. No se requiere Docker.

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

El instalador crea entornos Python separados para `apps/web` y `apps/services`. La configuración y los datos persistentes se guardan en `.local/runtime/`, excluido de Git. En un entorno nuevo se crean once bases PostgreSQL, cuentas iniciales y configuraciones de Redis y MongoDB; al terminar la preparación se detienen los procesos creados por ella. Una instalación existente conserva sus datos y no vuelve a cargar registros.

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

`state.json`, los archivos JSON de cada servicio y `web-secrets.env` contienen secretos. No deben adjuntarse a reportes ni versionarse. El portal no necesita `DATABASE_URL`: utiliza `MICROSERVICES_CONFIG` y las API.

## Actualizar una instalación existente

Respaldar antes de actualizar el código. Para cambios de esquema, detener las aplicaciones, mantener las bases encendidas y ejecutar:

```bash
bash components.sh detener web
bash components.sh detener ms
bash components.sh bases
apps/services/.venv/bin/python apps/services/scripts/upgrade.py --directory .local/runtime
bash start.sh
```

`upgrade.py` crea un respaldo por base antes de migrarla; `--service inventario` limita la operación a ese propietario. Las migraciones no se repiten si ya están registradas. Ver [datos y persistencia](Datos_y_persistencia.md).

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

Este lanzador no es un supervisor de producción. HTTPS, arranque automático del servidor y despliegue GCP siguen pendientes.
