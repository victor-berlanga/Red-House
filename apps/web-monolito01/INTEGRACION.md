# Portal web integrado — 8 de octubre de 2026

El portal Flask/Jinja2 consume los diez microservicios y Monitoreo por HTTP. Sus formularios, tablas, gráficas y procesos utilizan persistencia real en las bases independientes de los servicios. La web no ejecuta consultas a sus antiguas tablas de negocio ni importa las implementaciones de dominio de los microservicios.

## Operar el entorno preparado

Portal: <http://127.0.0.1:5050>. Las rutas Swagger actuales se encuentran en [Entorno local](../services/docs/ENTORNO_LOCAL_ACTUAL.md).

Desde la raíz del repositorio:

```sh
apps/services/.venv/bin/python apps/services/scripts/integrated.py start --directory /Users/victorberlanga/Programacion/integracion/Red-House/.local/demo
apps/services/.venv/bin/python apps/services/scripts/integrated.py status --directory /Users/victorberlanga/Programacion/integracion/Red-House/.local/demo
apps/services/.venv/bin/python apps/services/scripts/integrated.py stop --directory /Users/victorberlanga/Programacion/integracion/Red-House/.local/demo
```

El lanzador administra exclusivamente los procesos de ese directorio; detiene también workers y dependencias propias, conserva los datos y permite cambiar el puerto con `--web-port`. No sustituye un supervisor productivo. El directorio privado debe conservarse: contiene bases, claves y configuración; perderlo requiere crear otro entorno y reconfigurar la web.

La instalación habitual tiene `BACKEND_MODE=microservices` y `MICROSERVICES_CONFIG` apuntando al archivo privado `web-client.json`. `python run.py` desde esta carpeta inicia únicamente la web; los servicios deben estar encendidos por separado o mediante el lanzador conjunto. El modo explícito `BACKEND_MODE=local` conserva el funcionamiento histórico contra PostgreSQL; los datos de ambos modos son independientes y no se sincronizan. Nunca se activa como respaldo automático ante una caída de las API.

## Acceso y responsabilidades

Se conservaron ocho cuentas activas de la instalación anterior, sus roles y hashes: se puede iniciar sesión con sus correos y contraseñas habituales. Sus ámbitos se asignaron a instituciones de la demostración según municipio, usando Monterrey cuando no había coincidencia. Las cuentas DEMO `admin1`, `operator1`, `medical1`, `coordinator1`, `transport1`, `auditor1`, `donor1` representan Monterrey; el sufijo 2 corresponde a San Nicolás, hasta el 6 para Santa Catarina. Su contraseña aleatoria se consulta **localmente** en el `state.json` privado; no está versionada ni debe mostrarse en la presentación.

| Perfil | Recorrido autorizado |
| --- | --- |
| Administrador | Instituciones, primer administrador, cuentas y catálogos de su ámbito y monitoreo; sin acceso clínico por ser administrador |
| Operador | Donantes, citas, procesamiento, ingreso de recursos, preparación y aceptación física institucional |
| Médico | Receptores, solicitudes, dictámenes, liberación, evaluación, ranking, propuesta y reserva autorizada |
| Coordinador | Inventario regional minimizado, reservas, rutas, planificación de traslados y monitoreo |
| Personal de traslado | Órdenes asignadas, recolección, tránsito, entrega y ubicación durante estados autorizados |
| Auditor | Registro regional minimizado y monitoreo |
| Donante | Su expediente, campañas, citas y avisos autorizados |

Los permisos finales, estados y versiones se comprueban siempre en la API. Las alertas y la auditoría se reciben mediante outbox/inbox; su centralización es eventual. El portal muestra operaciones pendientes y permite consultar/reanudar una reserva sin asumir que un timeout equivale a fallo.

## Datos de demostración

Se eligió una carga nueva coherente entre servicios, preservando la base anterior como referencia. No se borraron ni modificaron sus registros de negocio. Los nombres de pacientes, instituciones y operaciones son ficticios; los municipios representan Nuevo León.

| Elemento | Carga inicial |
| --- | ---: |
| Instituciones en Monterrey, San Nicolás, Guadalupe, Apodaca, Escobedo y Santa Catarina | 6 |
| Cuentas DEMO + cuentas anteriores conservadas | 42 + 8 |
| Donantes | 108 |
| Donaciones, campañas y citas | 36, 12 y 36 |
| Receptores y solicitudes | 72 y 72 |
| Unidades sanguíneas y ofertas de órganos | 216 y 36 |
| Rutas capturadas, con procedencia ficticia explícita | 36 |
| Traslados interhospitalarios | 18 |

Los 18 traslados cubren programado, preparado, en tránsito, entregado, aceptado y cancelado. Se crearon mediante roles reales y API: revisión humana representada por el médico, evaluación versionada, reserva, planificación y pasos físicos. Incluyen custodia verificable, avisos, auditoría y ubicación autorizada para los tres traslados en tránsito. Las pruebas automáticas crean datos adicionales en bases aisladas; no aumentan esta carga. Operaciones posteriores realizadas en el portal sí cambian sus conteos.

Para mostrar un recorrido, usar Operador del origen para ingreso en cuarentena, Médico del origen para liberación, Médico del destino para receptor/solicitud/evaluación/dictamen/reserva, Coordinador para planificación, Operador del origen para preparación, Traslado asignado para recolección/tránsito/entrega y Operador del destino para aceptación. El recurso cambia de ubicación institucional y la solicitud cierra cuando recibe la cantidad completa. Esto no certifica una transfusión o trasplante realizado.

## Seguridad y separación

Identidad emite JWT RS256 de 15 minutos y renovación opaca rotada. Cada petición protegida de la web consulta `/auth/me`; cada operación de negocio consulta JWT, sesión, revocación y permisos mediante Redis en el servicio correspondiente. Disponibilidad regional usa caché autorizada breve; evaluación y reserva vuelven a consultar las fuentes autoritativas.

El navegador recibe únicamente un identificador aleatorio de sesión con cookie HttpOnly/SameSite. Los tokens permanecen cifrados con Fernet en un SQLite privado de la web, con permisos 0600 y fuera de Git. **Ese archivo guarda credenciales temporales, nunca expedientes ni inventario**; Redis de los servicios continúa siendo la autoridad de sesión. La cookie Flask conserva solamente CSRF y preferencias. CSRF, escape HTML, tiempos de espera, correlación, CSV protegido contra fórmulas y errores uniformes se mantienen. Ante dependencia inaccesible se informa 503 y no se vuelve a la base anterior.

## Reproducir una instalación nueva

Instalar las dependencias propias de `apps/services/requirements-dev.txt` y `apps/web-monolito01/requirements.txt` en sus respectivos `.venv`. Requiere Python 3.12+, PostgreSQL, Redis y MongoDB; macOS Intel está comprobado. Sustituir las rutas siguientes por un directorio **nuevo** fuera de Git y por el binario local `mongod`:

```sh
apps/services/.venv/bin/python apps/services/scripts/local.py init --directory /ruta/privada/demo --mongo-bin /ruta/a/mongod
apps/services/.venv/bin/python apps/services/scripts/seed_nuevo_leon.py provision --directory /ruta/privada/demo
apps/services/.venv/bin/python apps/services/scripts/local.py start --directory /ruta/privada/demo
apps/services/.venv/bin/python apps/services/scripts/seed_nuevo_leon.py populate --directory /ruta/privada/demo
apps/services/.venv/bin/python apps/services/scripts/seed_nuevo_leon.py restore --directory /ruta/privada/demo
apps/services/.venv/bin/python apps/services/scripts/local.py stop --directory /ruta/privada/demo
apps/services/.venv/bin/python apps/services/scripts/integrated.py start --directory /ruta/privada/demo
```

Agregar `--preserve-web-accounts` a `provision` solamente si se desea leer las cuentas de una instalación anterior accesible mediante su `.env`; la lectura usa transacción de solo lectura. Configurar en el `.env` web `BACKEND_MODE=microservices`, `MICROSERVICES_CONFIG=/ruta/privada/demo/web-client.json` y dos secretos propios distintos. `provision` requiere inventario vacío; `populate` rechaza una carga ya completada. No es un importador de expedientes históricos ni un migrador reanudable tras una carga parcial; ante esa situación crear otro entorno exclusivo, sin borrar bases ajenas.

## Alcance y evidencia

Pruebas de flujos reales desde Flask a los servicios: [test_web_integration.py](../services/tests/test_web_integration.py). La fixture prohíbe SQL del monolito y apunta su antigua conexión a un destino inaccesible. Incluye sangre y riñón/hígado/corazón hasta recepción, procedencia de donación, matching sin reserva automática, administración/revocación, roles, filtros, CSV, CSRF, renovación y caída/recuperación de Identidad. Resultados comprobados: [VALIDACION](../services/docs/VALIDACION.md).

El recorrido [integrated_browser.cjs](tests/integrated_browser.cjs) comprueba Chrome real, Highcharts, filtros, vistas por perfil y pantallas de 1440 y 390 píxeles. Requiere Playwright y Chrome instalados; recibe `--state` privado y `--output` para sus capturas e informe, sin publicar credenciales.

Esta integración incluye catálogos de sedes, horarios, contactos, capacidades y ubicaciones administrados por Identidad y ediciones versionadas de registros en estados permitidos. El detalle de restricciones y propietarios está en [la matriz de revisión](../services/docs/REVISION_2026_10_08.md). Los catálogos clínicos y roles se muestran para consulta, sin permitir alterar reglas desde una pantalla. Los formularios usan el contrato disponible de cada servicio, no todos los campos históricos del monolito. HLA sigue documental y las reglas DEMO conservan sus límites clínicos. Correos/push, archivos reales en GCS, móvil, escritorio, Docker y despliegue GCP continúan pendientes. El reporte Word/PDF y capturas anteriores describen el corte histórico del monolito; este documento y `PROJECT_STATUS.md` registran el nuevo corte.


## Incremento del 8 de octubre

La sesión local se elimina incluso si Identidad no responde al logout; una revocación cifrada pendiente se procesa con `scripts/session_worker.py`, incluido en el lanzador integrado. La renovación no mantiene el bloqueo SQLite durante la llamada HTTP. Si se inicia únicamente `run.py`, debe iniciarse también ese worker o ejecutar el comando Flask `retry-session-revocations` periódicamente.

Los selectores permiten buscar y cargar más opciones, sin truncar los registros a la primera página. Los motivos de edición/cancelación y los actores aparecen en el historial autorizado. Los registros con historia operativa no admiten una edición retrospectiva libre: consultar la matriz de revisión.

El entorno anterior temporal se conservó como respaldo detenido. No iniciar esa copia al mismo tiempo que `.local/demo`, porque conserva los mismos puertos. Catálogos DEMO: `apps/services/scripts/seed_catalogues.py`; usa las API, solo admite la demostración previamente provisionada y evita repetir nombres existentes.
