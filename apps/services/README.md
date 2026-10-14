# Microservicios Red House

Diez servicios Flask y un componente de monitoreo, independientes del portal. API REST v1 en JSON y XML, Swagger local, PostgreSQL real, Redis real y MongoDB real para los propietarios que lo necesitan. El [portal web ya consume las API](../../documentation/markdowns/Integracion_web.md); móvil, escritorio y Docker siguen pendientes.

| Unidad | Puerto predeterminado | Propietario |
| --- | --- | --- |
| ms_identidad_acceso | 5101 | Identidad, instituciones, sesiones, permisos |
| ms_donantes | 5102 | Donantes, dictámenes, donaciones, campañas, citas |
| ms_receptores | 5103 | Receptores, solicitudes, retenciones de capacidad |
| ms_inventario | 5104 | Recursos, movimientos, reservas, operaciones |
| ms_compatibilidad | 5105 | Evaluaciones, candidatos y dictámenes |
| ms_priorizacion_geografia | 5106 | Rutas, rankings y propuestas de matching |
| ms_transporte | 5107 | Traslados, incidencias, telemetría, referencias de evidencia |
| ms_custodia | 5108 | Secuencia y registro de custodia |
| ms_alertas | 5109 | Bandejas y acuses de alertas |
| ms_auditoria | 5110 | Registro central y proyección documental |
| servicio_monitoreo | 5111 | Sondeos y estadísticas técnicas |

Cada unidad tiene fábrica Flask, entrada ejecutable, requisitos, OpenAPI, XSD y ejemplos. `redhouse/` contiene infraestructura común; los módulos de dominio no importan las reglas, tablas ni vistas de otros servicios. Su comunicación se realiza por HTTP autenticado. Los flujos de llamadas no recursan: los contratos de consulta y los comandos de coordinación tienen responsabilidades distintas.

## Arranque simplificado

Desde la raíz: `bash install.sh` instala las dependencias faltantes y prepara la configuración; después `bash start.sh` inicia bases, API, workers y web sin revisar paquetes ni versiones. `bash components.sh` abre un menú; admite `ms`, `web`, `bases` o un servicio como `donantes`, además de `estado`, `detener` y `reiniciar`. Conserva el entorno existente y recupera solo los procesos faltantes. [Guía completa del lanzador](../../documentation/markdowns/Instalacion_y_operacion.md).

## Instalar y probar sin Docker

Requisitos: Python 3.12+, PostgreSQL 14+ con `initdb`/`postgres` disponibles, Redis 7+ para ACL de claves, MongoDB Community 8.x con `mongod` disponible. La verificación de este incremento se realizó en macOS Intel. Windows y Linux nativos todavía no están comprobados.

`requirements-verified.txt` conserva las versiones exactas del entorno de pruebas; `requirements.txt` y `requirements-dev.txt` separan ejecución y herramientas. Una configuración manual usa el `.env.example` de cada unidad, con credenciales exclusivamente propias.

Desde `apps/services`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/local.py init --directory /private/tmp/red-house-ms-local --mongo-bin /ruta/a/mongod
.venv/bin/python scripts/local.py start --directory /private/tmp/red-house-ms-local
.venv/bin/python scripts/local.py status --directory /private/tmp/red-house-ms-local
```

`init` crea un clúster exclusivo, once bases PostgreSQL, roles con privilegios limitados, usuarios Redis con ACL, cuatro bases documentales y cuentas ficticias. Usa puertos libres y conserva sus URLs en `state.json`. **No utiliza `.env`, cuentas ni datos del monolito.** Rechaza reinicializar un directorio que ya tenga datos.

El directorio privado tiene permiso 0700; las configuraciones y credenciales generadas tienen 0600. `state.json` incluye las cuentas y su contraseña aleatoria; leerlo localmente, sin pegarlo en logs, Git ni presentaciones. Cada proceso recibe una configuración propia: solo Identidad conserva la clave privada RS256; cada servicio recibe su propia clave Ed25519 y las públicas de los demás.

Abrir `URL_DEL_SERVICIO/docs` para Swagger, `/openapi.json` para el contrato y `/schemas/OPERACION.xsd` para entrada XML. Los contratos estáticos se encuentran en cada carpeta `contracts/`; sus ejemplos contienen identificadores ficticios que deben sustituirse por los recibidos de operaciones previas.

```sh
.venv/bin/python scripts/local.py stop --directory /private/tmp/red-house-ms-local
.venv/bin/python scripts/local.py start --directory /private/tmp/red-house-ms-local
```

`stop` señala únicamente procesos cuyos comandos corresponden al directorio indicado; conserva sus datos. `start` recupera las dependencias de ese entorno cuando sea necesario y publica los servicios y workers faltantes, conservando los activos. `start --service donantes` limita la selección a una API/worker. No es un supervisor de producción. Para un servicio aislado:

```sh
.venv/bin/python run.py inventario --config /ruta/privada/inventario.json
.venv/bin/python worker.py inventario --config /ruta/privada/inventario.json
```

El worker entrega eventos cada cinco segundos; Monitoreo sondea cada treinta. Detenerlo conserva eventos pendientes pero retrasa la centralización. Una instalación nueva se provisiona con `scripts/local.py`. La carga regional explícita crea datos ficticios por API mediante `scripts/seed_nuevo_leon.py`; no importa expedientes históricos ni esquemas de prototipos. El lanzador `scripts/integrated.py` inicia/detiene también la web; instrucciones completas en la [guía de integración](../web/README.md).

## Consumir la API

1. En Identidad, `POST /api/v1/auth/login` con usuario y contraseña privados. Recibir JWT de acceso y renovación opaca.
2. En todas las operaciones protegidas: `Authorization: Bearer JWT` y `Accept: application/json` o `application/xml`.
3. Para cuerpos: `Content-Type` del formato correspondiente. Para cambios idempotentes: `Idempotency-Key` de 8–100 caracteres.
4. Propagar `X-Correlation-ID` UUID. Se genera uno cuando no se proporciona un valor válido.
5. Ante 202, revisar `data.status`, `inventory_pending` o `/api/v1/operations/ID`. Un timeout no demuestra que la operación no se haya ejecutado.

JSON de éxito: `{"data": ..., "meta": {"correlation_id": "UUID", "service": "inventario", "version": "0.2.0"}}`. Error: `{"error": {"code": "...", "message": "...", "details": []}, "meta": ...}`. Las respuestas 202 de reservas pueden indicar `COMPLETED`, `PENDING`, `ROLLBACK_PENDING` o `FAILED`; planificar exige reserva confirmada. La reanudación de una operación es naturalmente idempotente y consulta su estado actual.

Los ejemplos XML de entrada usan raíz `request`, campos del contrato, `item` para listas y `xsi:nil="true"` únicamente en campos anulables. La salida XML conserva tipos mediante elementos `field`/`item` y atributo `type`; el esquema de envoltura está en `/schemas/response.xsd`. Los campos concretos y sus tipos están en OpenAPI y `x-json-equivalent-schema`: el XSD de envoltura no reemplaza esa validación de datos del consumidor. Los errores también respetan `Accept`.

Los listados autorizados incorporan `page`, `page_size` (máximo 100), `items` y `total`. Un listado minimizado puede omitir columnas clínicas según rol. Inventario y su resumen tienen caché de 10 segundos, Disponibilidad de 15 y catálogos institucionales de 30. Las claves incluyen usuario, institución, región, rol, ruta, filtros y revisión SQL del propietario; las escrituras confirmadas cambian esa revisión dentro de la misma transacción. Los tokens y permisos se validan antes de cada HIT. `Cache-Control: no-cache` permite medir la consulta sin caché y mantiene toda la autenticación Redis. Nunca se utiliza la caché para autorizar reservas.

## Flujos incluidos

- Donante → consentimiento → campaña/cita → dictamen humano → donación/recolección → procesamiento → ingreso en cuarentena → liberación humana.
- Receptor/solicitud de sangre → evaluación RBC → dictamen favorable → ranking/propuesta opcional → reserva → traslado → custodia → recepción → cierre → auditoría/alertas.
- Receptor/solicitud de órgano → preselección separada por tipo/ABO → dictamen humano → reserva exclusiva → traslado → custodia → recepción/cierre.

Las fuentes de inventario externas pueden registrarse sin una donación local; quedan en cuarentena hasta liberación humana. Cuando se proporciona `donation_id`, se valida su procedencia procesada por contrato y se conservan referencias. La ubicación institucional del recurso cambia a destino al recibir; el origen histórico no se pierde. `RECEIVED` nunca equivale a sangre disponible para uso clínico, transfusión o trasplante realizado.

Las estimaciones de ruta son capturadas con procedencia y versión. RBC-1.0 y ORGAN-1.0 conservan el alcance académico documentado del proyecto; no interpretan HLA ni sustituyen pruebas, conservación autorizada, criterios legales o decisiones médicas. La propuesta Hopcroft–Karp maximiza cobertura sobre instantáneas con dictamen favorable; no reserva recursos ni implementa prioridad clínica oficial.

## Seguridad y resiliencia

JWT RS256 de 900 segundos, renovación opaca de hasta 24 horas con rotación y detección de reutilización. Redis valida sesión, revocación, permisos y versión en cada petición protegida. Si Redis falla, la API protegida devuelve 503. No existen permisos implícitos de administrador sobre expedientes.

Las llamadas internas se firman con Ed25519 sobre método, ruta, timestamp, nonce y hash del cuerpo. El nonce impide repetición; la ventana técnica es de 30 segundos. Los contratos interactivos también exigen JWT delegado. Los consumidores de eventos y la recuperación usan credenciales de servicio con listas explícitas de emisores, sin fingir ser un usuario.

PostgreSQL garantiza cambios locales, eventos y outbox juntos; no se promete una transacción ACID distribuida. Receptores retiene capacidad; Inventario confirma o compensa. Las operaciones interrumpidas con retención y sin reserva local pueden compensarse después de un margen técnico de 60 segundos. Eventos de recepción/cancelación se aplican eventualmente y deduplicados. Custodia exige secuencia continua. Una recolección física nunca se compensa devolviendo disponibilidad automáticamente.

Redis local usa AOF con `appendfsync always`, política `noeviction`, autenticación y ACL por usuario/prefijo. MongoDB local exige autenticación; sus usuarios de aplicación solo pueden insertar y consultar su colección de eventos. Las credenciales PostgreSQL no son propietarias de base/esquema y no pueden conectarse a otra base; los historiales no admiten UPDATE/DELETE bajo credenciales de aplicación.

El entorno local enlaza únicamente a 127.0.0.1 y usa HTTP para pruebas. HTTPS, gestión institucional de claves, retención aprobada, respaldo/recuperación de producción y despliegue en GCP son pendientes explícitos. No exponer directamente este entorno local en una red pública.

## Pruebas, evidencia y presentación

```sh
REDHOUSE_TEST_MONGOD=/ruta/a/mongod .venv/bin/python -m pytest tests -q
.venv/bin/python scripts/document.py
```

La suite crea dependencias físicas aisladas y servidores HTTP para todos los servicios; detiene sus propios procesos al terminar y conserva el directorio privado para diagnóstico. Casos y resultados: [VALIDACION](../../documentation/markdowns/Pruebas_y_validacion.md). Arquitectura y decisiones: [ARQUITECTURA](../../documentation/markdowns/Arquitectura.md). Algoritmos: [ALGORITMOS](../../documentation/markdowns/Algoritmos.md).

URLs y comandos del entorno actualmente preparado: [ENTORNO_LOCAL_ACTUAL](../../documentation/markdowns/Instalacion_y_operacion.md).

Apuntes de exposición: [stuff/presentacion](../../stuff/presentacion/00-LEER-PRIMERO.txt), con un TXT por servicio y un índice. No son una certificación clínica ni de producción.

Carga: `scripts/prepare_load.py` agrega unidades ficticias exclusivamente en un entorno `local.py`; `tests/locustfile.py` ejercita cinco perfiles, JSON/XML y varios servicios. `REDHOUSE_LOAD_STATE` referencia el `state.json` privado. Los resultados de carga inicial no equivalen a estrés, disponibilidad institucional o escalabilidad en nube.

Archivos: el adaptador GCS requiere `requirements-storage.txt`, bucket privado y credenciales ADC con capacidad de firma V4. Sin configuración devuelve 503; no hay carga real en GCP comprobada en este incremento. Los binarios no se guardan en las bases.

## Actualizar un propietario

Desde `apps/services`, respaldar y aplicar únicamente sus migraciones, y reiniciar su API/worker:

```sh
.venv/bin/python scripts/upgrade.py --directory /ruta/privada/entorno --service donantes
.venv/bin/python scripts/local.py restart-service --directory /ruta/privada/entorno --service donantes
.venv/bin/python scripts/package_service.py donantes --output /ruta/nueva/entregas/donantes-0.2.0
```

La entrega contiene un único dominio, contratos, migraciones y utilidades fijadas por su manifiesto. Conservar el respaldo y la entrega anterior. Una reversión de aplicación solo es válida si el contrato y esquema anterior siguen siendo compatibles; nunca ejecutar una migración destructiva para deshacer una entrega.

La web puede reiniciarse por separado con `scripts/integrated.py restart-web --directory /ruta/privada/entorno`.

El entorno habitual está en `.local/runtime` de la raíz, ignorado por Git, con permisos privados; no depende de la limpieza automática de `/tmp`. `scripts/relocate.py` permite copiar un entorno **detenido** conservando el origen. Deben actualizarse las referencias privadas de la web al nuevo `web-client.json`.

Catálogos institucionales, primer administrador, ediciones permitidas y límites: [revisión implementada](../../documentation/historial/integracion/REVISION_2026_10_08.md). El validador de salida XML se puede ejecutar con `scripts/validate_response.py`; consultar `--help`. El estado del worker está en `/health/worker`. El lanzador integrado incluye el worker web de revocaciones pendientes.

CI definida en `.github/workflows/services.yml`, con bases locales sin Docker. Su ejecución remota solo puede afirmarse después de recibir un resultado de GitHub; las pruebas locales se documentan por separado.
