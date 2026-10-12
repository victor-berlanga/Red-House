# Iniciar Red House con Bash

Desde la raíz del repositorio, en macOS:

```bash
bash instalar.sh  # Una vez, o cuando cambien/falten dependencias
bash iniciar.sh   # Cada vez que quieras iniciar el sistema
```

`instalar.sh` comprueba e instala las dependencias faltantes, prepara los entornos Python y la configuración privada. No inicia las aplicaciones; si crea un entorno nuevo, enciende temporalmente las bases para inicializarlas y las detiene al terminar. En un entorno existente conserva los procesos activos.

`iniciar.sh` inicia PostgreSQL, Redis, MongoDB, las diez API de negocio, Monitoreo, sus workers, el monolito integrado y su worker de revocaciones usando la configuración preparada. **No ejecuta pip ni revisa paquetes/versiones ni instala dependencias.** Conserva la comprobación de procesos, puertos y salud para confirmar el arranque. El portal se publica en <http://127.0.0.1:5050>; muestra las URLs Swagger reales del entorno.

Si el entorno no está preparado, indica ejecutar `bash instalar.sh` con el mismo `--directory`; el arranque no crea bases ni credenciales automáticamente.

Los procesos quedan en segundo plano y sus logs están en `.local/demo`. Puedes cerrar esa terminal. Después de reiniciar el equipo vuelve a ejecutar el mismo comando. No configura inicio automático al encender macOS.

## Menú y componentes

```bash
bash componentes.sh                    # Menú interactivo
bash componentes.sh todo               # Equivalente a iniciar.sh
bash componentes.sh ms                 # Todas las API y sus workers
bash componentes.sh inventario         # Solo Inventario y su worker
bash componentes.sh web                # Solo monolito integrado y worker web
bash componentes.sh bases              # Solo PostgreSQL, Redis y MongoDB
bash componentes.sh listar             # Nombres de servicios disponibles
bash componentes.sh estado             # Salud y URLs
bash componentes.sh reiniciar donantes # Reiniciar solo Donantes y su worker
bash componentes.sh reiniciar web      # Reiniciar solo web y worker web
bash componentes.sh detener donantes   # Detener solo Donantes y su worker
bash componentes.sh detener ms         # Detener API/workers; conservar web y bases
bash componentes.sh detener web        # Detener web/worker; conservar API y bases
bash componentes.sh detener todo       # Detener el entorno completo, conservar datos
bash componentes.sh --help
```

Nombres: `identidad_acceso`, `donantes`, `receptores`, `inventario`, `compatibilidad`, `priorizacion_geografia`, `transporte`, `custodia`, `alertas`, `auditoria`, `monitoreo`.

Iniciar un servicio inicia también las bases privadas del entorno cuando están detenidas. No inicia automáticamente otras API: para autenticarse necesitas Identidad y para operaciones cruzadas los propietarios correspondientes. La web sola puede mostrar el sitio/login; los procesos de negocio requieren sus API. `ms` incluye Monitoreo. Los comandos de inicio son repetibles: conservan procesos activos y recuperan los faltantes, incluso un worker cuya API sigue disponible. `reiniciar` sí detiene e inicia el componente solicitado.

## Instalación y conservación

Estas comprobaciones se ejecutan exclusivamente con `bash instalar.sh`:

- Python 3.12 o superior; cada aplicación conserva su propio `.venv` y `requirements.txt`. Solo consulta PyPI cuando faltan paquetes o las versiones instaladas no satisfacen los requisitos.
- PostgreSQL: conserva el major indicado en `pg/PG_VERSION` del entorno; para uno nuevo utiliza 14. Nunca intenta actualizar automáticamente un clúster a otro major.
- Redis 7 o superior, con ACL y persistencia del entorno existente.
- MongoDB de la serie 8.0. Si no encuentra un ejecutable compatible, descarga **8.0.17**, la versión utilizada por esta DEMO, a `.local/tools/mongodb-8.0.17`. Verifica SHA-256 antes de extraerlo. Ya no depende de `/private/tmp/red-house-mongodb-tools`.
- Python, PostgreSQL y Redis faltantes se instalan mediante Homebrew. Si falta Homebrew, se ejecuta su instalador oficial, que puede solicitar confirmación, herramientas de Apple o la contraseña de macOS. No se ejecuta `brew services start`; el lanzador controla las instancias privadas del proyecto.
- El instalador reutiliza las dependencias correctas. `bash instalar.sh --no-install` permite comprobar/preparar con lo ya instalado y muestra qué falta. El arranque normal no necesita esa opción: nunca instala.

El soporte de instalación automática es macOS 14+ Intel/Apple Silicon; se verificó en macOS Intel. En Linux se pueden usar los scripts con Python 3.12+, su soporte venv, PostgreSQL del major correspondiente, Redis 7+ y MongoDB 8.0 ya instalados. Linux, Apple Silicon y una instalación de Homebrew desde cero no quedan certificados por la prueba de esta máquina. Windows requiere otro instalador.

Fuentes de instalación: [MongoDB mediante archivo oficial](https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-on-os-x-tarball/), [SHA-256 Intel](https://fastdl.mongodb.org/osx/mongodb-macos-x86_64-8.0.17.tgz.sha256), [SHA-256 Apple Silicon](https://fastdl.mongodb.org/osx/mongodb-macos-arm64-8.0.17.tgz.sha256) y [Homebrew](https://brew.sh/). La descarga fijada conserva la versión anterior; no constituye una política de actualizaciones de producción.

Si `.local/demo/state.json` ya existe, se conserva la configuración, cuentas y bases: no se vuelve a cargar la DEMO. El instalador repara las rutas de ejecutables; el arranque actualiza los PID. Si el directorio contiene archivos pero falta su estado, se detiene la preparación para no sobrescribirlo.

Un directorio nuevo se inicializa con las dos instituciones y cuentas ficticias básicas de `local.py`; **no** replica automáticamente las seis instituciones ni los expedientes de Nuevo León. Sus credenciales aleatorias quedan únicamente en su `state.json` privado. El instalador utiliza conexiones reales para provisionarlo y detiene únicamente las bases que él mismo acaba de crear.

El instalador crea la configuración web si falta. Las claves se conservan en `web-secrets.env` privado: en su primera creación reutiliza las claves existentes del entorno/`.env` web cuando existen; de otro modo genera claves aleatorias. Los arranques siguientes usan ese archivo. Si necesitas rotar claves, actualiza ese archivo privado y reinicia la web; las sesiones cifradas anteriores dejarán de ser utilizables. No se imprime ninguna contraseña ni se escribe ningún secreto versionado.

Este arranque corresponde al modo web integrado vigente. El modo histórico `BACKEND_MODE=local` conserva su instalador `apps/web-monolito01/setup.sh`. Docker, clientes móvil/escritorio y GCP siguen pendientes; no son requisitos del arranque local actual.

## Directorios, puertos y diagnóstico

```bash
bash instalar.sh --directory .local/otra-demo
bash iniciar.sh --directory .local/otra-demo --web-port 5051
bash componentes.sh estado --directory .local/otra-demo
bash componentes.sh detener todo --directory .local/otra-demo
```

El directorio predeterminado siempre es `.local/demo` del repositorio, incluso al llamar al script desde otra carpeta. Una ruta relativa pasada explícitamente con `--directory` se interpreta desde tu carpeta actual. Puedes usar rutas absolutas con espacios entre comillas.

El instalador, para binarios fuera de las ubicaciones habituales, admite `REDHOUSE_MONGOD`, `REDHOUSE_POSTGRES`, `REDHOUSE_INITDB` y `REDHOUSE_REDIS`. Un override inválido produce error; no se ignora silenciosamente. Se buscan también los prefijos Homebrew de Intel y Apple Silicon y los binarios PostgreSQL de Linux.

- Puerto ocupado: no mata al proceso propietario. Elige otro `--web-port` o detén el entorno propietario del puerto. No inicies simultáneamente copias del mismo `state.json`.
- API sin readiness: el comando devuelve error e identifica el servicio; los procesos ya iniciados permanecen registrados para diagnóstico/reintento. Consulta `SERVICIO.log`, `SERVICIO-worker.log`, `postgres.log`, `redis.log`, `mongodb.log`, `web.log` y `web-sessions.log` dentro del directorio privado.
- Ejecutable eliminado o dependencias modificadas: vuelve a ejecutar `bash instalar.sh` con el mismo directorio; las bases existentes se conservan.
- Descarga bloqueada durante la instalación: revisa conexión/proxy; el comando termina sin declarar éxito. Una descarga con checksum incorrecto no se instala.
- Otro lanzador activo: espera su terminación; los Bash coordinan instalación/operación mediante un bloqueo local que el sistema libera al terminar el proceso.
- Los comandos Python anteriores siguen funcionando. `local.py start --service NOMBRE` y `integrated.py start-web` permiten el arranque parcial sin pasar por el instalador. Usar directamente esos comandos no toma el bloqueo de los Bash.

El lanzador es una herramienta de desarrollo local: verifica salud al iniciar, pero no sustituye un supervisor que reinicie procesos después de una caída. `estado` es una consulta informativa; muestra `down` o HTTP 503 cuando corresponde.

## Evidencia y reproducción

```bash
apps/services/.venv/bin/python -m pytest apps/services/tests/test_launcher.py -q
apps/services/.venv/bin/python apps/services/scripts/check_launcher.py --report /tmp/launcher-lifecycle.json
```

La segunda comprobación verifica que el arranque sin preparación falle sin crear datos y que el instalador prepare un clúster nuevo sin dejar procesos activos; después verifica selección, reinicios, recuperación de worker, conflicto de puerto, bloqueo concurrente y conservación de configuración/cuentas; detiene sus propios procesos al terminar. Requiere las dependencias preparadas y puertos locales disponibles. No utiliza los datos de `.local/demo`.

Evidencia de la separación, 12/10/2026: **26 pruebas unitarias** (incluida la ausencia de comprobaciones/instalaciones durante inicio, reinicio, estado y detención) y **14 comprobaciones reales** del ciclo de vida. Informes: [pruebas unitarias](evidence/launcher-unit.xml), [ciclo de vida real](evidence/launcher-lifecycle.json) y [datos/salud de la DEMO conservada](evidence/launcher-demo.json). Estas pruebas cubren el lanzador y su integración; no se presentan como repetición completa de todas las pruebas del negocio.
