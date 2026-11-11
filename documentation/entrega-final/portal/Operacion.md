# Portal: operación y corrección del 6 de noviembre de 2026

Estado vigente: **APTA LOCALMENTE PARA CONTINUAR A 04**, con aceptación integrada pendiente de 06 confirmada por el usuario. Este incremento no acredita cierre integral del prompt 03. [Revisión y pruebas nuevas](../../evidencias/entrega-final/portal/aceptacion-20261106/RESULTADOS.md); [responsables, prerrequisitos y ensayo de infraestructura](Aceptacion_integrada_06.md). Los 90 casos anteriores siguen siendo históricos, no una ejecución nueva. Conserva Flask/Jinja2,
backend modular propio (`BACKEND_MODE=monolith`) y selección HTTP explícita
(`microservices`). No modifica el adaptador de escritura ni introduce fallback.

Por autorización posterior, esta base ya está publicada en **https://34.18.186.116**,
tag `portal03-20261106`, esquema 17. [Comprobaciones nuevas de GCP](../../evidencias/gcp/portal03-20261106/RESULTADOS.md):
perfiles/MFA, persistencia, permisos, responsive y WSS del gateway con revocación de
dispositivo. No es aceptación integral: no se probaron posiciones nuevas, caída total
ni ciclos documentales GCS/ClamAV. Los párrafos sobre ejecución exclusivamente local
describen la corrección previa; no deben usarse como inventario remoto vigente.

## Recorridos y permisos

| Perfil | Recorrido | Autoridad y controles |
|---|---|---|
| Donante | Mi expediente → consentimiento e historial; campañas → horarios por sede → reservar; citas → gestionar horario | Donantes: usuario vinculado, institución, versión e idempotencia. Retirar consentimiento conserva historia. |
| Operador | Campañas → horarios por sede → crear; citas → confirmar/reprogramar/asistencia; inventario, donaciones y procesamiento existentes | Donantes/Inventario; asistencia exclusiva del operador. No agrega permiso de dictamen. |
| Médico | Expediente → consentimiento; laboratorio → perfil; evaluación, dictamen, reserva y destino existentes | Compatibilidad/Inventario/Donantes; conserva reautenticación y revisión humana. |
| Coordinador | Traslados → expediente completo → mapa y seguimiento | Transporte autoriza región y traslado en cada entrega. |
| Transportista | Traslados asignados → mapa; recolección, tránsito, entrega y evidencia existentes | Transporte exige responsable asignado y asignación vigente de dispositivo. |
| Administrador | Configuración → presentación institucional/política; dispositivos → crear/rotar/revocar; usuarios/sedes/capacidades | Identidad valida institución, versión y facultades. Administrar no concede acceso clínico ni al mapa. |
| Auditor | Auditoría/hallazgos y exportaciones existentes | No se agrega acceso al mapa; historial inmutable. |
| Público | Login → recuperar acceso → solicitar → confirmar token | Identidad; CSRF, respuesta no enumerativa, correo verificado, token de 15 minutos de un uso, revocación de sesiones. |

La solicitud de recuperación no confirma entrega de correo. Identidad encola y su
worker envía mediante SMTP configurado. No se envían mensajes a personas en las
pruebas; se usa receptor SMTP temporal. Configurar/verificar correo sigue siendo
un requisito previo de cada cuenta. El token se introduce en un formulario POST;
no aparece en URLs ni se vuelve a mostrar junto con contraseñas tras un error.

## Mapa y contrato

`GET /traslados/<id>/mapa` obtiene una instantánea autorizada del propietario,
incluso desde el backend modular sin API HTTP. El botón del expediente abre la
página completa. Donantes y responsables ajenos reciben rechazo del servidor.

`POST /traslados/<id>/mapa/acceso` exige sesión web y CSRF. Solicita al propietario
`POST /api/v1/shipments/<id>/tracking/ticket`. Transporte crea un secreto opaco de
90 segundos, indexado por SHA-256 en Redis, limitado a lectura de ese traslado.
El navegador no recibe JWT de usuario. Cada autorización del ticket vuelve a
validar el JWT/sesión vigente en Redis; logout, expiración, cambio de rol y
reasignación conservan los controles existentes. El ticket no sirve para publicar
ni para otra suscripción. No se conserva en almacenamiento local ni URLs.

WSS usa la ruta existente `/services/transporte/ws/v1/tracking/json` y subprotocolo
`redhouse.tracking.v1.json`. El mensaje authenticate admite `credential_kind=browser`
además de user/device. Es una ampliación compatible de JSON Schema/XSD y OpenAPI.
La renovación abre un socket nuevo con acceso nuevo; reconexión exponencial con
jitter, máximo aproximado 30 segundos, heartbeat cada 20 segundos. Se conserva el
cursor confirmado por entrega, y `resync.required` reinicia la instantánea. No hay
polling de posiciones ni publicación local simulada en el mapa.

Se conservan hasta 1000 puntos recibidos en la vista, ordenados por captura. Una
posición retrasada entra al recorrido sin mover hacia atrás la observación más
reciente. La línea conecta observaciones; no representa ruta vial ni ETA. Fuente,
SIMULADO, hora en zona seleccionada, antigüedad, precisión ausente y pérdida de
señal/socket se muestran por separado. Sin HTTPS no se abre WS inseguro.

Leaflet 1.9.4 y licencia se sirven localmente. Mosaicos HTTPS de OpenStreetMap con
atribución visible y caché normal del navegador, sin precarga/offline. Solo esta
página permite el dominio de imágenes; Referer externo contiene origen sin ruta.
El proveedor recibe solicitudes de mosaicos, nunca identificadores, tokens ni
expedientes. La fecha de actualización por zona es desconocida; consultar mosaicos
actuales no garantiza actualidad vial. La caída cartográfica conserva la posición
y el negocio web. Fuentes consultadas el 06/11/2026:
[Leaflet](https://leafletjs.com/download.html),
[política de mosaicos](https://operations.osmfoundation.org/policies/tiles/).

Los marcadores de origen/destino proceden de la presentación institucional autorizada.
Administración captura coordenadas, fuente, fecha y condición sintética. No se deducen
por nombre ni se publican en el sitio público. Sin coordenadas registradas, ese marcador
queda pendiente. Los ensayos locales usan coordenadas ficticias identificadas. La fuente
principal futura será la aplicación móvil iOS/Android (04/07); GPS externo es opcional.
Las pruebas locales usan SIMULATOR. La corrección original no desplegó en GCP; la
publicación posterior comprobó suscripción y revocación por su gateway real. Los
ensayos de caída total, recuperación/cursor y continuidad simultánea siguen en 06.

## Operaciones añadidas

- **Publicación:** Administración → Configuración → presentación de institución. Operador → campaña → publicación. Publicar exige confirmación y versión; el sitio público devuelve únicamente campos autorizados y campañas abiertas futuras.
- **Consentimiento y agenda:** el donante solo accede a su expediente. Selecciona campaña, sede y horario con cupos disponibles. Lista y expediente muestran sede, inicio/fin de cita y estado del horario; el periodo de campaña se conserva aparte. Las inscripciones antiguas sin horario se identifican como pendientes. La retirada conserva versiones. Confirmar, cambiar horario, cancelar y registrar asistencia pasan por Donantes; el cupo se bloquea transaccionalmente.
- **Procesamiento:** registrar donación tras evaluación humana, procesarla, vincular la unidad y abrir «Componentes». Los derivados quedan en cuarentena, con linaje y etiqueta Code128. La etiqueta identifica el recurso; no certifica aptitud clínica.
- **Conservación:** operador registra equipos y lecturas; médico registra perfiles sintéticos, controles y revisión de incidencias. No hay temperaturas clínicas predeterminadas. La revisión no sustituye la liberación médica.
- **Laboratorio:** listas de muestras/resultados, recepción, captura ABO/HLA, revisión y corrección versionada. Las fuentes y la completitud documental no constituyen dictamen. El formulario de constancias externas de una solicitud de órgano conserva emisor, referencia, vigencia e historia; no emite autorizaciones oficiales.
- **Destino final:** después de aceptación y materialización de inventario, médico documenta uso, devolución, descarte u otro destino permitido para el tipo de recurso. Una corrección crea historia; aceptar el traslado no equivale a transfundir/trasplantar.
- **Documentos:** centro por sujeto autorizado, preparación, carga JPEG/PNG/PDF hasta 10 MiB, análisis, estado, nueva versión y conservación/bloqueo. El propietario vuelve a validar sujeto, generación y análisis antes de firmar una descarga. No hay descarga local alternativa al fallar GCS o antivirus.
- **Hallazgos:** auditor vincula hechos y asigna coordinador; responsable atiende y remite; auditor distinto verifica. Los cambios son aditivos y mantienen historia.

## Escrituras inciertas y recuperación

Una reserva `PENDING` muestra advertencia y seguimiento. `COMPLETED` confirma finalización;
`FAILED` comunica que no se completó. Ante pérdida de respuesta se consulta la clave y
huella del mismo comando antes de reenviar; nunca cambia automáticamente a otro backend.
«Reanudar operación» actúa sobre el mismo identificador. Cambiar el cuerpo con la misma
clave produce conflicto. No se debe iniciar otra reserva para resolver una incertidumbre.

Un traslado con `inventory_pending` advierte confirmación pendiente. Un trabajo de exportación
aceptado todavía no está listo para descarga. Conserva el identificador y vuelve a consultar
su estado; si requiere reintento, vuelve a validar la sesión autorizada.

## Indicadores y exportaciones

El panel solicita agregados a cada propietario con periodo UTC explícito, ámbito, población,
denominador, unidad y fecha de actualización. Highcharts tiene tabla equivalente. Un valor
desconocido permanece desconocido. Inventario/solicitudes/donaciones/laboratorio/traslados
no se convierten en una población regional clínica por cambiar el rol del visor.

El CSV del listado indica que exporta la página actual e incluye filtros/alcance/zona/fecha.
Su contexto distingue perfil, institución de la cuenta y región; el propietario mantiene
la autorización por recurso. La institución de la cuenta no se presenta como el único
ámbito de un perfil regional.
Para el conjunto completo usa **Reportes → nuevo trabajo**, con el mismo filtro y orden.
El worker recorre páginas autorizadas de hasta 100 filas, con límite explícito de 50.000:
superarlo o detectar cambios en conteo/duplicación rechaza la extracción; no trunca a 1.000.
La autorización de extracción se guarda cifrada, se comprueba con Identidad/Redis y se
elimina al materializar filas. Si vence o se revoca, el trabajo no obtiene archivo y exige
reintento autorizado. Descarga vuelve a comprobar rol, ámbito, sujeto, estado y análisis.
PDF/CSV/XLSX incluyen contexto y convierten fechas; CSV/XLSX no ejecutan fórmulas del dato.
El formato operativo identifica que está sujeto a revisión; no es certificación regulatoria.

## Configuración técnica y dependencias

Aplicar migración aditiva **017**, conservando propietarios y contratos. Instalar las
dependencias declaradas de web (incluye ReportLab para etiquetas). No conectar las vistas
a tablas de otro propietario. `BACKEND_MODE=monolith` conserva núcleo propio; el modo HTTP
se selecciona explícitamente como `microservices`. No existe conmutación tras una escritura.

Proveedor: `MAP_TILE_URL`, `MAP_PROVIDER_NAME`, `MAP_ATTRIBUTION`,
`MAP_ATTRIBUTION_URL` y `MAP_UPDATED_AT` según la configuración de la ruta.
Debe usar HTTPS y atribución; la fecha de consulta no prueba fecha de actualización vial.
La política institucional versiona frecuencia, antigüedad y zona. La línea une observaciones,
sin inferir tráfico, velocidad o ETA. `resync.required` comunica el hueco y obtiene instantánea.

La aceptación local usa TLS WSGI con la ruta WSS real; no acredita Nginx productivo.
GCS privado, daemon ClamAV, SMTP institucional y gateway de destino deben verificarse en 06
con configuración autorizada. `TestBucket` y el receptor TCP ClamD de pruebas son dobles;
sus casos prueban lógica/contratos, no esos servicios externos.

## Reproducción

Desde raíz, dependencias del proyecto ya instaladas:

La aceptación ampliada se puede ejecutar con el wrapper local. Cada invocación crea
almacenes propios y conserva JUnit/logs en una carpeta nueva; no reutilizar una carpeta
de evidencia anterior. `features` comprueba las correcciones y los doce contratos;
`regression` ejecuta continuidad, permisos, calidad, documentos y rastreo. Los dos
modos de navegador son casos separados con PostgreSQL/Redis/MongoDB nuevos.

```sh
bash scripts/accept_portal.sh features /private/tmp/rh-portal-correction-repeticion/features
bash scripts/accept_portal.sh browser-http /private/tmp/rh-portal-correction-repeticion/http
bash scripts/accept_portal.sh browser-monolith /private/tmp/rh-portal-correction-repeticion/modular
bash scripts/accept_portal.sh agenda-browser /private/tmp/rh-portal-correction-repeticion/agenda
bash scripts/accept_portal.sh regression /private/tmp/rh-portal-correction-repeticion/regression
bash scripts/accept_portal.sh migration /private/tmp/rh-portal-correction-repeticion/migration
bash scripts/accept_portal.sh browser-degraded /private/tmp/rh-portal-correction-repeticion/degraded
```

El wrapper usa los binarios locales indicados abajo y axe-core instalado en el
expediente temporal de esta corrección. En otro equipo, configura su ruta antes de
usar el comando pytest equivalente. No cambia TTL, permisos ni timeouts del producto.
Los manifiestos del navegador deben coincidir antes/después; no editar fuentes
durante una ejecución que se pretenda acreditar.

```sh
apps/services/.venv/bin/python apps/services/scripts/document.py --contracts-only
REDHOUSE_BROWSER_TESTS=1 apps/services/.venv/bin/python -m pytest apps/services/tests/test_portal_tracking.py -q
apps/services/.venv/bin/python -m pytest apps/services/tests/test_final_tracking.py apps/services/tests/test_web_integration.py apps/services/tests/test_continuity.py -q
```

Las pruebas crean y detienen sus propios almacenes. Requieren puertos locales,
MongoDB 8.0, PostgreSQL 14, Redis, Chrome y Playwright en
`.local/gcp-public/browser/node_modules/playwright`. No usan la instalación habitual.
El verificador `verify_portal_tracking.cjs` comprueba mosaicos bloqueados; su salida
nueva usa `REDHOUSE_BROWSER_RESULTS` o el directorio temporal de pytest, preservando
la evidencia histórica. Usa TLS directo con sustitución del destino WSS únicamente
en ese ensayo de degradación; no acredita el gateway. La aceptación ampliada `verify_backend_corrections.cjs` utiliza
la ruta WSS del mismo origen TLS, sin sustitución de URL, y mosaicos en línea con caché
normal; mide recepción backend–renderizado del mapa, no captura física–mapa.

```sh
REDHOUSE_BROWSER_TESTS=1 REDHOUSE_TEST_GATEWAY=embedded \
REDHOUSE_BROWSER_RESULTS=/ruta/temporal/evidencia \
REDHOUSE_AXE_PATH=/ruta/instalada/axe-core/axe.min.js \
REDHOUSE_TEST_MONGOD=/ruta/instalada/mongod \
apps/services/.venv/bin/python -m pytest apps/services/tests/test_correction_browser.py -q
```

No actives `REDHOUSE_GCS_TEST_BUCKET` contra un bucket habitual. Su ausencia deja la
descarga real sin verificar; no habilita una alternativa menos protegida.

### CSV inmediato de auditoría

Conserva exactamente los filtros y el orden del listado autorizado. «Exportar página»
identifica la página; «Exportar resultados filtrados» admite hasta 5.000 resultados
y rechaza con explicación cuando se supera el límite. Incluye ámbito regional, filtros,
zona, fecha UTC de generación y conteos; convierte la fecha de ejecución a la zona
seleccionada. No debe confundirse con los trabajos paginados de reportes generales.
