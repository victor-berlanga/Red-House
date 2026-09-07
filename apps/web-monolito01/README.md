# Red House · Monolito web

Incremento local del primer parcial. Un solo proceso Flask renderiza Jinja2 y ejecuta los casos de negocio contra PostgreSQL; no consume ni implementa microservicios. Todos los datos de la demostración deben ser ficticios.

## Qué funciona

| Área | Implementación de este incremento |
| --- | --- |
| Sitio público y acceso | Presentación, inicio y cierre de sesión, JWT de 15 minutos, revocación y bloqueo temporal de intentos fallidos. |
| Administración | Alta, edición y desactivación de instituciones, sedes, ubicaciones, componentes y cuentas; contacto institucional y capacidades declaradas; asignación de perfil y ámbito. |
| Inventario sanguíneo | Alta de unidades, detalle, cambios de estado DEMO y movimientos internos con motivo e historial; búsqueda, filtros y paginación de 12 registros. |
| Caducidad | Exclusión de unidades vencidas de la disponibilidad al consultar; umbral regional de aviso, versionado y expresamente DEMO. |
| Panel | Conteos reales del ámbito autorizado, gráfica Highcharts local y tabla accesible con los mismos valores. |
| Auditoría | Registro transaccional de cambios, accesos y movimientos; consulta autorizada con búsqueda, resultado, fechas y paginación. |
| Interfaz | Diseño responsive, menú móvil, navegación por teclado y vistas diferenciadas por perfil. |

Donantes, receptores, órganos, compatibilidad, solicitudes urgentes, asignación/traslados y cadena de custodia tienen **vistas futuras sin funcionalidad**. La recuperación de acceso también es una vista deshabilitada: no envía correos ni modifica contraseñas. No existen expedientes, cálculos clínicos, asignaciones automáticas, mapas de seguimiento ni operaciones simuladas detrás de estas pantallas.

Los siete perfiles del análisis aparecen en configuración; solamente Administrador, Operador y Auditor están habilitados. No se implementó un editor de permisos arbitrarios.

## Preparación automática (recomendada)

Necesitas **Python 3.12 o superior y PostgreSQL 14 o superior instalado y encendido**. La primera instalación necesita Internet para descargar las dependencias Python y una cuenta PostgreSQL con permiso para crear una base (`CREATEDB`). No necesitas Node.js, npm ni tener `psql` en el PATH. El instalador no instala PostgreSQL, no cambia su autenticación y no arranca servicios del sistema.

Desde la raíz del repositorio, ejecuta una sola vez:

**macOS / Linux**

```sh
cd apps/web-monolito01
sh setup.sh
```

**Windows**, desde CMD o PowerShell:

```powershell
cd apps\web-monolito01
.\setup.cmd
```

Ambos ejecutan el mismo [instalador Python](scripts/setup_local.py). Crean `.venv`, instalan `requirements.txt`, generan un `.env` privado con dos claves aleatorias diferentes, crean la base nueva y ejecutan el esquema y la carga DEMO existentes. No duplican SQL ni reglas de negocio.

En una instalación nueva se solicitan el servidor local, puerto, usuario y contraseña de PostgreSQL, el nombre de una base nueva y el puerto web (5050 por defecto). Después eliges y confirmas una contraseña de 12–128 caracteres para las cuatro cuentas DEMO. **La contraseña PostgreSQL y la contraseña de las cuentas web son distintas**; la segunda se almacena únicamente como hash. Las contraseñas se capturan con entrada oculta y no tienen valores predeterminados.

Después, para iniciar desde `apps/web-monolito01`, basta con:

```sh
python run.py
```

En macOS/Linux puedes usar `python3 run.py`; en Windows, `py run.py` si utilizas el lanzador de Python. `run.py` elige automáticamente la `.venv` de esta carpeta: no hace falta activarla, no instala paquetes al arrancar ni reinicializa la base. Abre la dirección que indique el instalador, normalmente <http://127.0.0.1:5050>, y detén Flask con `Ctrl+C`. PostgreSQL debe permanecer encendido.

### Repetición y comprobación segura

- Si ya existe `.env`, se conserva sin cambiar claves ni credenciales. Si hay cuentas, no se repite la carga ni se cambia ninguna contraseña.
- Si el nombre elegido ya existe y no hay `.env` que lo vincule al proyecto, la instalación se detiene antes de escribir la configuración. Elige un nombre nuevo; no borres la base anterior.
- Si la base contiene objetos ajenos, un esquema incompleto o datos previos sin cuentas, se rechaza la inicialización. No hay borrado, migración ni reparación automática.
- Si cancelas la carga nueva, el esquema y los datos de esa transacción se revierten. La base vacía y `.env` pueden quedar creados para reintentar ejecutando el mismo instalador.
- Si falla la conexión, verifica que PostgreSQL esté encendido y que la cuenta, puerto, contraseña y permiso `CREATEDB` sean correctos. No se muestra la conexión completa en los errores.

Puedes comprobar una instalación existente sin instalar paquetes ni escribir en la base:

```sh
sh setup.sh --check
```

En Windows: `.\setup.cmd --check`. Si ya configuraste manualmente una conexión por socket, indica su directorio local explícitamente en `DATABASE_URL` para usar este instalador; no se admiten destinos remotos ni bases del sistema.

`.env` está excluido de Git; en macOS/Linux se crea con permisos `600`. En Windows hereda los permisos de la carpeta: conserva el proyecto dentro de tu directorio privado y revisa sus permisos antes de compartirlo. No copies `.env` ni `.venv` a otro equipo; ejecuta allí el instalador para crear un entorno propio. El uso del intérprete del entorno sin activación sigue la [documentación de Python](https://docs.python.org/3/library/venv.html); la creación de la base requiere el permiso descrito por [PostgreSQL](https://www.postgresql.org/docs/14/sql-createdatabase.html).

Se verificó la instalación completa en macOS con PostgreSQL real, incluyendo rutas con espacios, repetición y cancelación. La lógica compartida tiene pruebas automatizadas. La ejecución nativa de `setup.cmd` en Windows fue realizada por otros integrantes del equipo, según la confirmación del usuario recibida el 6 de septiembre de 2026; no se presenta como una prueba ejecutada en este Mac.

## Antecedente de instalación local

La instalación del 5 de septiembre descrita en este apartado corresponde al repositorio de origen. El 6 de septiembre se reconstruyó un `.venv` propio en la ruta actual de `Red-House`, conservando `.env`, credenciales y base de datos. La comprobación y el arranque directo desde esta ubicación están verificados; no necesitas repetir el instalador sobre la base existente.

El 2026-09-05 se completó la instalación en este equipo: `.venv` con las dependencias del proyecto, `.env` privado excluido de Git y con permisos `600`, esquema y carga DEMO en la base nueva `red_house`. Se utiliza el PostgreSQL de Homebrew ya existente, mediante el socket `/tmp` y puerto `5432`; no se modificaron otras bases ni se cambiaron contraseñas de PostgreSQL.

La dirección configurada es **<http://127.0.0.1:5050>**. Se eligió 5050 porque macOS ocupa el puerto 5000. La contraseña de las cuatro cuentas DEMO se entregó en la conversación: no se guardó en texto plano en el proyecto y no se debe volver a ejecutar la carga para recuperarla.

En la instalación original se dejó la aplicación ejecutándose en una ventana de Terminal. La comprobación del entorno actual utilizó un servidor temporal y lo detuvo al terminar; no modificó el servidor habitual. Para iniciar la aplicación desde este repositorio:

```sh
cd apps/web-monolito01
python3 run.py
```

No necesitas repetir la instalación, activar manualmente el entorno virtual ni reinicializar la base. PostgreSQL debe seguir disponible; el servidor Flask no se configura para arrancar automáticamente al encender el equipo. Los pasos siguientes se conservan para una instalación nueva en otro entorno.

## Instalación manual (alternativa)

No repitas estos pasos si utilizaste el instalador automático o ya tienes la base preparada. Esta alternativa permite configurar cada paso manualmente; los comandos de entorno mostrados son para macOS/Linux. Requisitos comprobados: Python 3.12, PostgreSQL 14 y conexión local. Las dependencias Python directas están fijadas en `requirements.txt`.

1. Crea una base **nueva y exclusiva** para la demostración con tu instalación local de PostgreSQL:

   ```sh
   createdb red_house
   ```

   Si ese nombre ya existe, no lo borres: elige otro nombre vacío y ajusta `DATABASE_URL`. La cuenta de conexión debe poder crear el esquema y sus tablas. La configuración de usuarios y autenticación de PostgreSQL depende de tu instalación; no se incluye ninguna contraseña real.

2. Desde la raíz del repositorio, prepara el entorno:

   ```sh
   cd apps/web-monolito01
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   cp .env.example .env
   ```

3. Edita el `.env` local. Mantén `APP_ENV=development` para HTTP local, configura `DATABASE_URL` y asigna valores aleatorios diferentes a `SECRET_KEY` y `JWT_SECRET_KEY`, de al menos 32 caracteres cada uno. Puedes generar cada valor ejecutando por separado:

   ```sh
   python -c 'import secrets; print(secrets.token_urlsafe(48))'
   ```

   No compartas ni versiones los valores. La aplicación rechaza secretos ausentes, demasiado cortos o iguales. `.env` está excluido de Git. Si tu PostgreSQL acepta conexiones por socket local, puedes usar `postgresql:///red_house`; si utiliza TCP, configura el usuario y la autenticación correspondientes.

4. Inicializa y carga la demostración:

   ```sh
   python -m flask --app run init-db
   python -m flask --app run seed-demo
   ```

   La carga solicita y confirma una contraseña de 12–128 caracteres para las cuatro cuentas ficticias. No hay contraseña predeterminada en el código; se guarda únicamente su hash scrypt. `init-db` no sobrescribe un esquema existente y `seed-demo` rechaza una base que ya contiene instituciones o cuentas. Ambos comandos confirman toda la operación en una transacción o la revierten.

5. Inicia la aplicación:

   ```sh
   python run.py
   ```

   Abre <http://127.0.0.1:5000>. Si el puerto está ocupado, modifica `PORT` en `.env`. El servidor de desarrollo no se debe publicar en Internet.

La carga inicial contiene dos instituciones ficticias, dos sedes, cuatro ubicaciones, tres componentes, cuatro cuentas y 36 unidades sintéticas. Las fechas se calculan al cargar para ejercitar los estados de ejemplo; **no representan vidas útiles autorizadas** por componente.

## Cuentas y permisos DEMO

Todas usan la contraseña elegida durante el instalador o al ejecutar manualmente `seed-demo`.

| Correo | Perfil y ámbito | Acceso |
| --- | --- | --- |
| `admin@red-house.test` | Administrador regional de `DEMO-NORTE` | Red institucional, cuentas, catálogos y parámetro; no inventario operativo ni auditoría clínica. |
| `operador@red-house.test` | Operador del Banco Regional Norte | Consulta, alta, movimientos internos y baja lógica de su inventario. |
| `operador.valle@red-house.test` | Operador del Hospital del Valle | Las mismas operaciones, exclusivamente en su institución. |
| `auditor@red-house.test` | Auditor regional de `DEMO-NORTE` | Inventario y bitácora de la región, sin permisos de modificación. |

También se pueden crear cuentas administrativas o auditoras institucionales. Un administrador institucional no puede ampliar su ámbito, modificar el catálogo regional ni incorporar otras instituciones. Una cuenta mantiene un solo perfil y ámbito vigentes en este incremento. Los perfiles no forman una jerarquía de privilegios clínicos.

Para comprobar el flujo: inicia como Operador, registra una unidad ficticia con fechas UTC, consulta su detalle, registra un movimiento con motivo y, si todavía no tiene movimientos operativos posteriores al alta, ejecuta la baja lógica con un motivo. Recarga para verificar persistencia y confirma que la unidad ya no aparece en el inventario ni en el panel, aunque su detalle e historial siguen conservados. Después, inicia como Auditor para consultar la evidencia. La segunda cuenta operadora no puede acceder a esa unidad, ni siquiera mediante su URL directa.

## Reglas técnicas del incremento

- Todos los horarios se capturan, almacenan y muestran en UTC. La caducidad debe ser posterior a la recolección; no se admite recolección futura ni alta disponible con caducidad vencida.
- Los estados persistidos son `AVAILABLE`, `QUARANTINED` y `WITHDRAWN`. Las transiciones operativas son demostrativas; `WITHDRAWN` se alcanza mediante la baja lógica exclusiva del Operador y no se revierte desde esta interfaz. La cuarentena de ejemplo no constituye validación de laboratorio.
- `EXPIRED` y `UNAVAILABLE` se derivan al consultar. Caducidad o referencias inactivas impiden contabilizar una unidad como disponible sin borrar su historial.
- La ventana inicial de aviso es **72 horas DEMO**; el administrador regional puede registrar otra versión entre 1 y 720 horas. Es un parámetro de interfaz, no una regla de conservación. No modifica las fechas capturadas. Si aún no existe una versión, la consulta utiliza el mismo valor DEMO de 72 horas.
- Folio, componente, clasificación y fechas quedan inmutables después del alta. La interfaz permite cambios de estado y ubicación dentro de la misma institución; las correcciones clínicas y los traslados entre instituciones requieren procesos posteriores.
- Las escrituras administrativas llevan control de versión. Los movimientos bloquean la unidad durante la transacción y verifican su versión: ante dos ediciones simultáneas, una se confirma y la otra recibe un conflicto 409.
- La operación, su movimiento y su auditoría se confirman conjuntamente. Si falla la bitácora, no se guarda parcialmente la operación.
- No se eliminan físicamente unidades ni cuentas desde las vistas: se usa baja o desactivación. La baja de una unidad conserva el folio, historial y auditoría, pero la excluye de los listados, contadores, avisos y últimas unidades del panel. Se bloquea si existe cualquier movimiento operativo posterior al alta; en el MVP esto cubre conservadoramente asignación, traslado, entrega u otro evento posterior. La modificación de una cuenta revoca sus sesiones previas; desactivar una institución revoca los accesos asociados.

## Seguridad y límites

El JWT está en una cookie `HttpOnly` y `SameSite=Lax`, nunca en almacenamiento JavaScript; contiene identificadores, no información clínica. Cada petición protegida comprueba firma HS256, emisor, audiencia, tiempos, sesión activa, perfil y ámbito actuales. Como Redis está calendarizado para el segundo parcial, **la revocación y los controles temporales del MVP residen en PostgreSQL**. No hay renovación automática: al vencer los 15 minutos hay que iniciar sesión de nuevo.

Flask-WTF protege los formularios contra CSRF. Se utilizan consultas parametrizadas, escape de Jinja2, límites de entrada, cabeceras de seguridad, identificadores de correlación y mensajes sin detalles internos. El bloqueo de acceso considera cinco fallos por identidad o treinta por dirección en quince minutos, con respuesta 429. No se confía en `X-Forwarded-For` sin un proxy configurado.

Con `APP_ENV` distinto de `development`, las cookies requieren HTTPS y se envía HSTS. Esto **no configura un despliegue productivo**: aún faltan servidor WSGI, TLS, proxy confiable, permisos mínimos de PostgreSQL, respaldos, retención, pruebas de carga, revisión de seguridad y validaciones normativas. La autorización institucional está en los repositorios y servicios, no en políticas RLS de PostgreSQL. No utilices datos reales.

La auditoría guarda referencias, motivos y cambios técnicos autorizados; no contraseñas, JWT, correos de acceso ni cuerpos completos de formularios. Los cambios de contacto se señalan sin duplicar sus medios personales. Los intentos anónimos sin institución/región identificable se conservan sin asignarlos a un auditor regional arbitrario. Los triggers rechazan `UPDATE` y `DELETE` de historiales; no sustituyen los privilegios del servidor ni protegen frente a un propietario de base con capacidad de alterar el esquema.

`/health/live` comprueba únicamente que el proceso responde. Si PostgreSQL no está disponible, las operaciones dependientes fallan de forma cerrada con 503; el sitio público puede seguir disponible. No es todavía el sistema de monitoreo distribuido del semestre.

El mantenimiento opcional `python -m flask --app run prune-auth` elimina intentos temporales de más de un día y sesiones vencidas hace más de un día. No elimina auditoría ni registros de negocio. No se agenda automáticamente.

## Pruebas reproducibles

Para los comandos de desarrollo sí activa el entorno (`source .venv/bin/activate` en macOS/Linux, `.venv\Scripts\activate.bat` en CMD) o usa directamente su intérprete. Instala las dependencias de pruebas dentro de ese entorno:

```sh
python -m pip install -r requirements-dev.txt
```

Usa un **clúster PostgreSQL dedicado a pruebas**, con una cuenta que pueda crear bases. `TEST_POSTGRES_URL` es una conexión de control: cada caso crea una base de nombre aleatorio, carga el esquema, realiza operaciones reales y elimina exclusivamente esa base creada por el caso. No apunta ni limpia la base funcional indicada en `DATABASE_URL`.

```sh
export TEST_POSTGRES_URL='postgresql:///postgres'
python -m pytest -q
```

Adapta esa conexión a tu clúster de pruebas. Sin la variable solo se ejecutan las pruebas independientes de la base; pytest informa las demás como omitidas, no como aprobadas.

Para el recorrido de navegador se requieren Node.js, Chrome y Playwright como herramientas externas de verificación. No generan dependencias de ejecución para Flask:

```sh
red_house_browser_tools=$(mktemp -d)
npm install --prefix "$red_house_browser_tools" playwright
export NODE_PATH="$red_house_browser_tools/node_modules"
python -m pytest -q --browser -s
```

La prueba inicia y detiene su propio servidor local. Las capturas se generan en el directorio temporal de pytest; opcionalmente define `BROWSER_ARTIFACTS` hacia una carpeta de evidencias. No se guarda la contraseña aleatoria de pruebas en archivos.

La cobertura incluye autenticación, CSRF, revocación, rol y ámbito, escrituras y rollback, fechas y referencias inactivas, paginación, auditoría, conflictos concurrentes, datos escapados, vistas futuras, pérdida de conexión y recuperación. `tests/test_setup.py` verifica configuración privada, destinos permitidos, instalación nueva, repetición sin cambios, conflictos de nombre, protección de objetos ajenos, rollback al cancelar y modo de solo lectura. Chrome verifica además altas mediante formularios, persistencia al recargar, Highcharts, menú móvil y ausencia de desbordamiento horizontal de página. No equivale a carga masiva, auditoría externa de accesibilidad ni certificación sanitaria. Los resultados concretos se registran en [PROJECT_STATUS.md](../../PROJECT_STATUS.md).

### Revisión desde Red-House

El 6 de septiembre de 2026 se ejecutaron **65 pruebas, todas aprobadas y sin omisiones**, desde los archivos actuales de este repositorio, usando un entorno Python recién creado para la revisión, un clúster PostgreSQL temporal exclusivo y Chrome. La ejecución duró 40.80 segundos. Se conservaron el [informe y las capturas](../../documentation/evidence/primer-parcial/README.md), y se detuvo el clúster temporal después de retirar únicamente las bases creadas para pruebas. La base habitual se comprobó solo mediante `setup.sh --check`, sin reinicializarla.

Después de detectar las rutas antiguas del `.venv` copiado, se reconstruyó el entorno por autorización del usuario en `apps/web-monolito01/.venv`. La activación, `pip`, `pytest`, Flask y `sys.prefix` apuntan ahora a `Red-House`; `pip check` y `setup.sh --check` aprobaron. Las **65 pruebas volvieron a aprobar con este entorno, sin omisiones, en 40.92 s**, y `python3 run.py` respondió HTTP 200 en `/health/live`, `/` y `/login` sin activación manual. El entorno anterior se conservó fuera del repositorio como respaldo temporal. No se cambiaron código, SQL, `.env`, credenciales ni datos. La prueba de Windows y la revisión del equipo están confirmadas por el usuario; el [informe de cierre](../../documentation/evidence/primer-parcial/README.md#cierre-del-primer-parcial) distingue esa confirmación de las pruebas ejecutadas aquí.

## Diseño y dependencias visuales

Se adaptó el ZIP local `Blood_and_Organ_Donation_Platform (1).zip`: barra lateral azul oscuro, acento rojo, tarjetas, tablas, formularios, Inter y DM Sans. Las vistas son Jinja2; no hay React, Vite, Recharts ni componentes de ejemplo desconectados de PostgreSQL.

Los iconos Lucide y las fuentes se sirven localmente con sus licencias en `src/presentation/static/img/icons/` y `fonts/`. Highcharts 12.4.0 y su módulo de accesibilidad están en `static/vendor/highcharts/`, sin exportación remota. Sus condiciones son independientes: revisa [el aviso local](src/presentation/static/vendor/highcharts/NOTICE.md) antes de un uso fuera de la demostración académica. Con `HIGHCHARTS_ENABLED=false` permanece la tabla de valores.

Las decisiones de implementación siguen las referencias oficiales de [seguridad de Flask](https://flask.palletsprojects.com/en/stable/web-security/), [CSRF de Flask-WTF](https://flask-wtf.readthedocs.io/en/1.2.x/csrf/), [parámetros de Psycopg](https://www.psycopg.org/psycopg3/docs/basic/params.html), [validación de PyJWT](https://pyjwt.readthedocs.io/en/stable/api.html) y [accesibilidad de Highcharts](https://www.highcharts.com/docs/accessibility/accessibility-module).

El esquema físico y su relación con la normalización previa se explican en [data/database/README.md](../../data/database/README.md). El [análisis vigente](../../documentation/markdowns/Analisis_del_problema.md) y el [modelo lógico](../../documentation/database-diagrams/Modelo_4FN.md) están en `documentation/`; el ZIP y los modelos sustituidos permanecen como antecedentes en el repositorio de origen.
