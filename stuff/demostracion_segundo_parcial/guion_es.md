# Qué decir y qué demostrar en el segundo parcial

Guion en español para la presentación presencial y el video de YouTube. Basado en el estado del proyecto del **20 de octubre de 2026** y en la consigna compartida. Duraciones propuestas para el ensayo; ajustar al tiempo que indique el docente. [English version](guide_en.md).

La recomendación es seguir una operación concreta y mostrar sus resultados. Cada tecnología debe tener una evidencia visible, además de una explicación. Los comandos del final son apoyo para quien opera la demostración; no hace falta leerlos durante la exposición.

## 1. Preparación

- Abrir el [portal GCP](https://34.18.186.116), [Swagger de Identidad](https://34.18.186.116/services/identidad-acceso/docs/), [Swagger de Inventario](https://34.18.186.116/services/inventario/docs/) y una terminal SSH de la VM `red-house`. Todo el procesamiento ocurre en GCP; no iniciar Docker ni servidores locales.
- Entrar al portal con `operator1` antes de iniciar la sesión de Swagger. Usar las contraseñas ya entregadas al equipo, sin copiarlas a estos documentos. Cubrir contraseñas, tokens y cookies durante la grabación, incluido el apartado Curl generado por Swagger.
- Preparar un folio ficticio nuevo, como `DEMO-AAAAMMDD-01`, y una fecha futura de caducidad con zona horaria. Reservar ese folio para la demostración.
- Para el proceso de traslado, preparar un caso ficticio propio, con solicitud, reserva y traslado vigente asignado a `transport1`. Dejarlo **En tránsito**, sin cambios de inventario pendientes. Tener acceso con `operator2` si Hospital 2 es el destino y con `auditor1` para la bitácora. Usar perfiles de navegador separados si se mantienen varias cuentas abiertas.
- Repartir los bloques entre todos los integrantes. Cada persona debe explicar una responsabilidad y ejecutar o interpretar una evidencia. Los nombres se asignan durante el ensayo.

## 2. Orden para la exposición presencial: 16–18 minutos

| Bloque | Qué decir | Qué enseñar | Tiempo |
| --- | --- | --- | --- |
| Problema y alcance | “Red House ayuda a coordinar recursos, solicitudes y traslados entre instituciones.” | Portal y un ejemplo de necesidad entre dos hospitales. | 1 min |
| Arquitectura actual | “Tenemos un portal autónomo y API independientes que comparten reglas y almacenamiento autorizado.” | Portal, Swagger y ubicación del sistema en GCP. | 1 min |
| Sistema web y proceso | “Cada perfil puede realizar determinadas acciones, y los cambios conservan un historial.” | Traslado preparado; registrar entrega y aceptación autorizadas. | 3 min |
| Microservicios, Swagger y formatos | “Esta petición llega a un servicio independiente y devuelve datos reales.” | Alta por API, consulta del mismo registro en JSON/XML y aparición en el portal. | 4 min |
| JWT y Redis | “El token identifica la sesión; Redis permite comprobar si sigue activa.” | Consulta autorizada, TTL de sesión, cierre y rechazo del mismo token. | 3 min |
| PostgreSQL, MongoDB y Docker | “Podemos seguir esta operación desde la respuesta hasta su almacenamiento y el contenedor que la atendió.” | Fila SQL, documento MongoDB, contenedores y registro de petición. | 4 min |
| Límites y siguiente etapa | “La entrega demuestra operación académica con datos ficticios; móvil y escritorio continúan pendientes.” | Monitoreo y referencia a las pruebas conservadas. | 1 min |

**Aclaración que conviene decir al mostrar la arquitectura:**

> “El portal actual trabaja en modo monolítico: ejecuta sus módulos dentro del proceso web. Las API también están desplegadas en contenedores independientes y las utilizaremos directamente desde Swagger. Comparten reglas y datos autorizados. Ver un registro en ambas interfaces demuestra coherencia; la petición a la API y su registro en Docker demuestran el uso del microservicio independiente.”

## 3. Demostración del proceso desde la página

Abrir el traslado preparado con `transport1`. Mostrar la solicitud y la reserva que lo originaron, su responsable y los pasos anteriores. Aclarar que esos antecedentes se prepararon antes de la exposición.

1. Desde **En tránsito**, registrar **Entregado**, con motivo ficticio y confirmación.
2. Con el operador de la institución destino —`operator2` en el caso preparado—, registrar **Aceptado**. Completar la ubicación de destino si el formulario la solicita.
3. Consultar la cadena de custodia, el estado del recurso y la solicitud asociada. Si esta solicitud pedía una sola unidad y quedó totalmente atendida, debe quedar cerrada.
4. Con `auditor1`, abrir la [bitácora](https://34.18.186.116/auditoria), localizar el evento de aceptación y abrir su detalle. Comprobar allí el identificador del traslado, la acción, el origen y la trazabilidad. Si está pendiente, esperar la sincronización y actualizar.

**Para decir:** “Aquí vemos quién actuó, qué cambió y qué resultado quedó registrado. La recepción documenta una entrega logística. La asignación requiere revisión humana y no representa una transfusión o un trasplante realizado.”

## 4. Demostración de API, JSON/XML, JWT y Redis

### A. Inicio de sesión independiente

1. En Swagger de Inventario, ejecutar `GET /api/v1/resources` **sin Authorize**. Resultado esperado: `401`.
2. En Swagger de Identidad, usar `POST /api/v1/auth/login` con `operator1` y su contraseña. Elegir cuerpo JSON. Resultado esperado: `200`.
3. Copiar `data.access_token` a **Authorize** de Inventario y de Identidad. Pegar solo el token, sin escribir de nuevo `Bearer`. La sesión del portal y esta sesión de API son distintas.

**Para decir:** “El servicio exige autenticación. El JWT tiene una duración limitada y los permisos dependen del usuario y de su institución.”

### B. Crear un dato real desde el microservicio

En Inventario, ejecutar `POST /api/v1/resources`. Elegir `Content-Type: application/json`, completar `Idempotency-Key` con una clave nueva, por ejemplo `demo-alta-AAAAMMDD-01`, y usar este cuerpo **después de sustituir folio y fecha**:

```json
{
  "folio": "DEMO-AAAAMMDD-01",
  "kind": "BLOOD",
  "component": "RBC",
  "blood_group": "O-",
  "expires_at": "FECHA_FUTURA_ISO_8601_CON_ZONA",
  "donation_id": null,
  "location_id": null,
  "collected_at": null
}
```

La fecha debe tener formato `AAAA-MM-DDTHH:MM:SSZ` y ser futura el día del ensayo. Es un dato ficticio, no una regla clínica de conservación. El resultado esperado es `201` y estado `QUARANTINE`.

Guardar **`data.id`** y **`meta.correlation_id`** del alta. Son las dos referencias que se usarán en las consultas del apartado 5. Para repetir la misma operación tras una respuesta perdida, conservar cuerpo y clave; para una nueva alta, usar folio y clave nuevos.

Con `operator1` en el [Inventario del portal](https://34.18.186.116/inventario), buscar el folio y abrirlo. Mostrar que coincide con el registro creado por API.

**Para decir:** “Acabamos de crear este registro mediante Inventario. El portal puede consultarlo porque ambos utilizan el almacenamiento compartido con sus permisos correspondientes.”

### C. Mostrar JSON y XML de la misma consulta

Ejecutar `GET /api/v1/resources/{identifier}` usando el `data.id` anterior. Mostrar **Request URL**, código `200`, `meta.service` y el cuerpo real de **Server response**.

Repetir la consulta seleccionando primero `application/json` y después `application/xml` como formato de respuesta. En Swagger, usar el selector de tipo de respuesta; si aparece también `Accept`, mantenerlo consistente. Comprobar el `Content-Type` recibido: cambiar únicamente **Example Value** no ejecuta otra petición.

Comparar el mismo identificador y folio entre ambas respuestas. Abrir el [XSD de respuesta de Inventario](https://34.18.186.116/services/inventario/schemas/response.xsd) como referencia de estructura; verlo no equivale a validar un XML.

**Para decir:** “Son los mismos datos expresados en dos formatos. Los contratos están listos para clientes JSON y XML; las aplicaciones móvil y de escritorio todavía no forman parte de esta entrega.”

### D. Mostrar sesión y revocación

1. Ejecutar la consulta de Redis del apartado 5. Debe mostrar `exists: 1` y `ttl_seconds` mayor que cero.
2. En Identidad, ejecutar `POST /api/v1/auth/logout`, autorizado con el mismo JWT y con una `Idempotency-Key` nueva, como `demo-logout-AAAAMMDD-01`. No requiere cuerpo. Esperar `200` y `revoked: true`.
3. Repetir en Inventario la consulta con **el mismo token anterior**. Resultado esperado: `401`.
4. Repetir la inspección de Redis. Para esa sesión, `exists: 0` y TTL `-2` indican que la clave ya no existe.

Entre ambas inspecciones, no abrir otra sesión con `operator1`: el comando selecciona su inicio de sesión más reciente. Si el JWT venció antes de completar el bloque, iniciar una sesión nueva y repetir el bloque completo.

**Para decir:** “Redis mantiene el estado temporal de la sesión. Después del cierre, conservar una copia del token ya no permite acceder.”

## 5. Evidencia en la VM: consultas de apoyo

Abrir **Google Cloud → Compute Engine → red-house → SSH**. Como alternativa, desde una terminal con acceso a la cuenta:

```sh
gcloud compute ssh red-house --project=sistemas-integracion-01 --zone=me-central1-a
```

**Todos los comandos siguientes se ejecutan dentro de esa SSH**, usando los contenedores existentes. Son consultas administrativas para la exposición. Las aplicaciones cliente no se conectan directamente a las bases. Los ejemplos leen la configuración privada dentro del contenedor y solo imprimen los campos seleccionados.

### PostgreSQL: la fila creada por Swagger

Sustituir `PASTE_RESOURCE_UUID` por `data.id` del alta:

```sh
sudo docker compose -f /opt/redhouse/compose.yaml exec -T inventario-a python - <<'PY'
import json
from pathlib import Path
from uuid import UUID
import psycopg
from psycopg.rows import dict_row
c = json.loads(Path('/run/secrets/config').read_text())
identifier = str(UUID('PASTE_RESOURCE_UUID'))
with psycopg.connect(c['DATABASE_URL'], connect_timeout=3, row_factory=dict_row) as db:
    db.execute('SET TRANSACTION READ ONLY')
    row = db.execute(
        'SELECT id,folio,status,version FROM access_inventario.resources WHERE id=%s',
        (identifier,),
    ).fetchone()
print(json.dumps(row, default=str))
PY
```

**Mostrar:** mismo identificador, folio y estado. `access_inventario.resources` es una vista de acceso a la base PostgreSQL compartida; no es otra copia de los datos.

### MongoDB: el documento de auditoría de esa alta

Sustituir `PASTE_CORRELATION_UUID` por `meta.correlation_id` del **POST del alta**, no el de una consulta posterior:

```sh
sudo docker compose -f /opt/redhouse/compose.yaml exec -T auditoria-a python - <<'PY'
import json
from pathlib import Path
from uuid import UUID
from pymongo import MongoClient
c = json.loads(Path('/run/secrets/config').read_text())
correlation = str(UUID('PASTE_CORRELATION_UUID'))
with MongoClient(c['MONGODB_URL'], serverSelectionTimeoutMS=3000) as client:
    row = client[c['MONGODB_DATABASE']].events.find_one(
        {'correlation_id': correlation, 'action': 'RESOURCE_CREATED'},
        {'_id': 0, 'source': 1, 'action': 1, 'resource_id': 1,
         'correlation_id': 1, 'occurred_at': 1},
    )
print(json.dumps(row, default=str))
PY
```

**Mostrar:** `source: inventario`, `action: RESOURCE_CREATED` y `resource_id` igual a la fila SQL. Si sale `null`, esperar unos segundos y repetir: los workers entregan los eventos en segundo plano. Si persiste, revisar el estado real; una captura anterior se presenta como evidencia histórica.

**Para decir:** “PostgreSQL conserva el registro operativo y MongoDB conserva este documento del evento. MongoDB también guarda eventos de custodia, monitoreo y seguimiento de traslados.” La página habitual de Auditoría consulta SQL; este comando sí consulta MongoDB directamente.

### Redis: existencia y vencimiento de la sesión de API

Ejecutar después del login de Swagger y repetir después de su logout. El comando no imprime tokens ni contraseñas:

```sh
sudo docker compose -f /opt/redhouse/compose.yaml exec -T identidad-acceso-a python - <<'PY'
import json
from pathlib import Path
import psycopg
import redis
c = json.loads(Path('/run/secrets/config').read_text())
with psycopg.connect(c['DATABASE_URL'], connect_timeout=3) as db:
    db.execute('SET TRANSACTION READ ONLY')
    row = db.execute(
        'SELECT s.id FROM access_identidad_acceso.sessions s '
        'JOIN access_identidad_acceso.users u ON u.id=s.user_id '
        'WHERE u.username=%s ORDER BY s.expires_at DESC LIMIT 1',
        ('operator1',),
    ).fetchone()
if row is None:
    raise SystemExit('No session found: sign in through Swagger first.')
sid = str(row[0])
with redis.Redis.from_url(c['REDIS_URL'], socket_timeout=3, socket_connect_timeout=3) as cache:
    key = c['REDIS_PREFIX'] + 'session:' + sid
    print(json.dumps({'session_ref': sid[:8], 'exists': cache.exists(key),
                      'ttl_seconds': cache.ttl(key)}))
PY
```

**Para decir:** “El TTL es el tiempo restante de esta clave de sesión. No es necesariamente el tiempo restante del JWT. Redis también mantiene permisos, revocaciones, límites de peticiones y caché.”

### Docker: contenedores y petición atendida

```sh
sudo docker compose -f /opt/redhouse/compose.yaml ps
sudo docker compose -f /opt/redhouse/compose.yaml logs --since 20m --no-color inventario-a inventario-b | grep -F -- 'PASTE_CORRELATION_UUID'
```

Reemplazar el UUID por la correlación del alta. En los logs, mostrar servicio, método `POST`, ruta `/api/v1/resources`, estado `201` y tiempo de respuesta. El prefijo del contenedor identifica qué réplica atendió la petición.

La configuración dispone de 27 contenedores de ejecución: 22 instancias API, web, gateway y tres almacenes. Mostrar el estado que realmente reporte `ps`; el contenedor de preparación `bootstrap` puede aparecer detenido si se consulta con `ps -a`.

**Para decir:** “Cada servicio tiene su contenedor y puede desplegarse por separado. Esta línea corresponde a la petición que acabamos de ejecutar.” Abrir después [Monitoreo](https://34.18.186.116/monitoreo) con `admin1`, `coordinator1` o `auditor1`; sus indicadores muestran disponibilidad, mientras que el log demuestra esta petición concreta.

## 6. Adaptación para YouTube: 18–22 minutos

Usar el mismo recorrido, con más espacio para explicar las peticiones y sus resultados:

| Capítulo | Contenido y captura sugerida |
| --- | --- |
| 00:00–02:00 | Problema, instituciones y objetivo. Portal en pantalla, sin portada obligatoria. |
| 02:00–04:00 | Arquitectura actual: portal autónomo, API, Docker, GCP y función de cada almacenamiento. |
| 04:00–08:00 | Proceso web: antecedentes preparados, entrega, aceptación, solicitud y custodia. |
| 08:00–13:00 | Swagger ejecutado: login, alta, JSON/XML y coincidencia del registro en el portal. |
| 13:00–18:00 | JWT/Redis antes y después del cierre; fila PostgreSQL, documento MongoDB y logs Docker. |
| 18:00–20:00 | Monitoreo, evidencia de pruebas y pendientes reales. Hasta dos minutos extra para preguntas frecuentes. |

Narrar cada operación con cuatro ideas: **qué vamos a hacer, qué enviamos, qué respondió y dónde quedó registrado**. Grabar las respuestas reales de `Server response`; los ejemplos del contrato y las capturas históricas sirven como apoyo identificado. Si se incluye GCS, mostrar una evidencia ficticia pequeña de un traslado y su descarga autorizada, sin exponer la URL firmada completa.

Cada integrante debe tener una intervención identificable y explicar su responsabilidad. El equipo decide el reparto nominal. Publicar el video como **público u oculto**, nunca privado, y comprobar que el enlace abre en una ventana sin sesión. Este documento no acredita que la grabación o publicación ya se hayan realizado.

## 7. Respuestas breves para preguntas del docente

- **¿Dónde se usan realmente los microservicios?** En las peticiones a `/services/...` que ejecutamos en Swagger; mostramos respuesta y log del contenedor. El portal actual usa módulos internos.
- **¿Por qué Redis?** Para sesiones y controles temporales que necesitan consulta rápida y vencimiento, además de caché.
- **¿Por qué MongoDB si existe PostgreSQL?** Para conservar eventos documentales y vistas de seguimiento; PostgreSQL mantiene las operaciones transaccionales.
- **¿Por qué Docker?** Para ejecutar y actualizar cada componente con sus dependencias de forma separada y reproducible.
- **¿Qué demuestra la integración?** La misma operación aparece con identificadores coherentes en API, portal, almacenamiento y auditoría; los permisos siguen aplicándose.
- **¿Qué sigue pendiente?** Android, escritorio, validación clínica y condiciones de operación productiva. No afirmar alta disponibilidad entre máquinas: el despliegue actual usa una sola VM.

## Referencias para preparar el ensayo

- [Estado vigente](../../PROJECT_STATUS.md) y [operación en GCP](../../deployment/gcp/README.md).
- [Resultados comprobados en GCP](../../documentation/evidencias/gcp/RESULTADOS.md).
- [Presentación técnica breve](../presentacion/tecnica/presentacion_es.md).
- [Contratos y encabezados](../../apps/services/redhouse/openapi.py), [alta de inventario](../../apps/services/ms_inventario/routes.py) y [modelo PostgreSQL](../../data/database/schema.sql).

Los comandos se contrastaron con el código y la configuración de despliegue. Este guion no representa una nueva ejecución de pruebas sobre la VM; ensayar con folios y fechas nuevos antes de presentar.
