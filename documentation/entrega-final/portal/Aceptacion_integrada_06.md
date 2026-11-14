# Portal 03: ensayo pendiente de aceptación integrada en 06

## Actualización de continuidad — 13/11/2026

El plan histórico inferior se conserva como lista de recorridos pendientes. Sus referencias al esquema 17, a ausencia de herramientas locales y a permisos por obtener describen la inspección del 6 de noviembre; no son el estado vigente ni obligan a pedir otra confirmación para las pruebas aisladas ya incluidas en el plan autorizado por el usuario.

La VM correcta es `sistemas-integracion-01 / red-house / me-central1-a`, con esquema 20 y treinta contenedores saludables en la última comprobación. El proveedor operativo es almacenamiento privado local de servidor; GCS queda opcional para operar y conserva una prueba académica independiente. El antivirus real, su vigilancia periódica y el proxy publicado tienen evidencia fechada ([esquema 20](../../evidencias/gcp/scanner20-20261113/RESULTADOS.md), [salud periódica](../../evidencias/gcp/scanner-health-20261113/RESULTADOS.md), [GCS sintético](../../evidencias/entrega-final/gcs-sintetico-20261113/RESULTADOS.md)). Estas comprobaciones no se suman como una ejecución de I06-01…09.

La continuidad prepara ensayos en laboratorios locales nuevos, con motores, archivos, puertos y procesos propios. Solo la dirección asigna la ventana de ejecución pesada. Los cortes se limitan a esos procesos: no se detienen servicios productivos ni se crean recursos de nube. Los resultados deben diferenciar certificado efímero de prueba y cadena pública confiable, almacenamiento local y GCS, portal modular autónomo y transporte HTTP, cartografía bloqueada en el arnés y mapa con mosaicos reales. La tabla de casos mantiene su exigencia de recorridos, persistencia e inspección visual; ninguna preparación o compilación cierra por sí sola un caso.

## I06-07: recorrido local aceptado — 13/11/2026

Aceptado el recorrido acotado del [ensayo portal/gateway](../../evidencias/entrega-final/portal-gateway-20261113/RESULTADOS.md): **1/1 aprobado en 157,31 s**, intento 04; intentos 01 de sandbox, 02 de selector y 03 de espera de URL conservados por separado. Chrome real mantuvo el mapa por Nginx HTTPS/WSS del mismo origen, con tres handshakes 101, caída de una réplica de Transporte y luego ambas, conservación de los dos IDs previos y reconexión automática del mismo documento. Durante la caída total, DONOR canceló una inscripción sintética desde el portal modular; recarga, estado SQL, actor y evento de auditoría comprobados antes de restaurar. Primero volvió B y luego A; ambas terminaron con `live/ready=200`. Tres IDs/cursores iguales en SQL, Mongo `events.metadata.position` y filas del mapa, sin duplicados. La dirección inspeccionó las capturas de caída, cancelación y recuperación; 1394 hashes de fuentes permanecieron iguales y los procesos propios cerraron.

Los tres puntos usan las mismas coordenadas sintéticas `25.6866,-100.3161`: se aceptan identidad, cursor y reconexión, sin acreditar desplazamiento físico o geometría vial. La inscripción no tiene horario asignado. El laboratorio conserva `TESTING=True`, cuotas de prueba 100000, WSGI de ensayo, confianza TLS explícita Python/excepción SPKI efímera Chrome y mosaicos OSM bloqueados; no acepta CA del sistema, capacidad, MFA, cartografía, Docker/GCP ni operación productiva. No hubo sustitución/intercepción de WebSocket ni resultados inyectados. **Esta aceptación local de I06-07 no cierra I06-01…06, I06-08/09 ni toda la etapa 06.** El plan histórico y sus demás recorridos permanecen abiertos en lo no verificado; sus referencias antiguas se interpretan con la actualización vigente superior.

## Plan original del 6 de noviembre

Preparado el 6 de noviembre de 2026. **Plan revisable, no ejecución ni autorización.**
El usuario confirmó mantener estas pruebas integradas pendientes de 06.
El encargo vigente permite continuar a 04 si el alcance local está aprobado y solo
quedan comprobaciones identificadas de infraestructura. Los siete criterios siguen
PARCIALES hasta reunir la evidencia indicada. No se reconstruyen 01 ni 02.

## Responsabilidad y prerrequisitos

Responsable de ejecución: **Equipo 01 / Infraestructura y seguridad (etapa 06)**.
Corresponsables: **QA web 03** para Chrome y persistencia; **Documentos** para archivos,
reportes y conservación; **Transporte/Identidad** para WSS, sesión y permisos.
Son asignaciones por función; el equipo debe designar a las personas al programar la ventana.
La integración móvil y escritorio corresponde a 04/05/07, sin condicionar el simulador web.

Antes de ejecutar, registrar un expediente de ensayo con:

- URL HTTPS del entorno aislado, proyecto Compose/host y servicios/PID exactos que se pueden detener. Datos ficticios, bases/Redis/MongoDB y volúmenes exclusivos; nunca la demostración habitual.
- Hash de fuentes e imágenes, esquema 17 compatible y configuración efectiva. La publicación posterior autorizada de 03 ya cotejó esquema 17 y fuentes/imágenes en la VM habitual ([evidencia GCP](../../evidencias/gcp/portal03-20261106/RESULTADOS.md)); esa VM no constituye por ello un entorno aislado autorizado para este ensayo. La evidencia histórica de etapa 02 conserva esquema 16.
- Bucket GCS privado existente y autorizado, identidad de prueba y alcance de escritura/lectura. Si comparte bucket, el permiso debe cubrir únicamente los prefijos de instituciones/traslados del ensayo (`documents/<tenant>/`, `reports/<tenant>/`, `evidence/<region>/<shipment>/`), con aislamiento verificable. Es preferible un bucket exclusivo ya autorizado. No listar ni borrar objetos habituales.
- ClamAV real: imagen/binario, versión, fecha de firmas, health y respuesta del motor al archivo antivirus estándar. Un receptor que devuelve `CLEAN/INFECTED` de forma programada no cumple.
- Nginx/gateway real con certificado válido, Upgrade y timeouts; mantener abierto el mapa por la URL habitual del ensayo, sin interceptar WSS en Playwright ni sustituir el destino por TLS directo.
- Ventana aprobada para fallos de **ese** entorno, mecanismo de restauración y presupuesto previamente autorizado si exige encender/crear recursos. No extender permisos de negocio o desactivar MFA para completar el ensayo.

La inspección actual no encontró un entorno aislado operativo confirmado: Docker local
no tiene socket disponible; las tres VM del proyecto consultado están detenidas; solo
aparece el bucket histórico. Hay credenciales/configuración locales antiguas, pero no
configuración local del propietario Documentos ni binarios ClamAV/Nginx en PATH.
La presencia de credenciales no concede autorización para usar un bucket compartido.
Ver [inventario y límites](../../evidencias/entrega-final/portal/aceptacion-20261106/RESULTADOS.md).

## Secuencia y criterios exactos de cierre

Todos los casos se ejecutan desde Chrome con cuentas ficticias y capturas de resultado,
excepto las verificaciones técnicas auxiliares indicadas. Registrar esperado/obtenido,
fecha UTC, caso, perfil, ID ficticio, estado persistido y hash de fuentes. Mantener
separados HTTP explícito y backend modular; nunca introducir fallback tras escritura.

| Caso | Recorrido y resultado exigido | Criterios | Responsable |
|---|---|---|---|
| I06-01 | Verificar TLS, configuración efectiva, imágenes/esquema, bucket con acceso público impedido e identidad autorizada; descargar un objeto ficticio sin firma debe dar 401/403. Confirmar ClamAV real con firmas y muestra de control. Un health 200 solo habilita iniciar el ensayo. | WEB-19/24, TRACK-09 | Infraestructura/seguridad 06 |
| I06-02 | Médico/laboratorio abre resultado propio → Documentos → carga PNG/PDF ficticio admitido → análisis → verificación → descarga. Repetir documento general de acreditación y evidencia de traslado por responsable asignado antes de cerrar custodia. SQL debe conservar sujeto, propietario, objeto, generación, tamaño, SHA-256 y análisis CLEAN; bytes descargados coinciden. Otra institución/orden falla por URL y endpoint, sin URL firmada. | WEB-12/15/19 | QA 03 + Documentos/Transporte + 06 |
| I06-03 | Desde el documento crear versión 2 que sustituye a 1; ambas conservan objeto/historia y cada descarga corresponde a su generación analizada. Intentar bifurcar desde versión ya sustituida: 412. Cambiar conservación/bloqueo autorizado con razón; versión de política obsoleta: 412; reducción de plazo con bloqueo vigente: 409. Comprobar SQL/auditoría tras recarga. Metadatos de aplicación no acreditan por sí solos una retención/hold de GCS; verificar por separado la política de bucket/objeto comprometida en 06, sin bloquear irreversiblemente un bucket habitual. | WEB-19 | Documentos + QA 03 + seguridad 06 |
| I06-04 | Usar el archivo estándar EICAR, sin malware real. Primero confirmar detección por ClamAV. Para pasar por formulario usar un PDF/imagen admitido que contenga la muestra y cuya detección por ese motor esté comprobada. No cambiar la validación MIME ni contabilizar un rechazo de formato como detección antivirus. Debe quedar INFECTED/REJECTED, nunca descargable; confirmar 409/denegación por endpoint además del estado visual. Si no hay muestra válida admitida, registrar esa parte NO VERIFICADA. | WEB-19/24 | Seguridad 06 + QA 03 |
| I06-05 | Detener únicamente ClamAV del ensayo; cargar/verificar un archivo nuevo: error seguro, sin estado VERIFIED ni descarga. Restaurar el motor y repetir con el mismo documento, sin duplicar registros. Separadamente cortar salida a GCS **solo** de web/Documentos del ensayo (regla de red o proxy de fallos acotado aprobado); verificar fallo seguro, restaurar y comprobar objeto/generación. No revocar IAM compartido ni borrar objetos para simular caída. | WEB-19/24 | Infraestructura 06 + Documentos |
| I06-06 | Reportes → crear CSV/PDF/XLSX con filtros/periodo/zona → trabajo pendiente → worker extrae y analiza → listo → descarga. Comparar bytes/contexto/conteo con población autorizada, incluyendo más de 1.000 filas. Revocar sesión o cambiar rol **entre creación y solicitud de descarga**: 401/403 y ninguna firma nueva; otra cuenta/tenant también rechaza. Repetir revocación antes de extracción: sin archivo autorizado. | WEB-21 | QA 03 + Documentos/Identidad + 06 |
| I06-07 | Con mapa abierto y posición A persistida, detener una réplica de rastreo y luego todas las réplicas WSS del ensayo, manteniendo gateway, web y almacenes. Esperar estado desconectado/antiguo; no inventar puntos ni enviar ACK de persistencia durante caída. En otra pestaña del portal modular completar alta/edición de cita o solicitud ficticia, recargar y comprobar persistencia/auditoría. Restaurar primero una réplica y luego ambas; publicar B/C por ingreso autorizado y comprobar mismos IDs en Mongo/SQL y mapa, sin recarga/polling, con cursor y sin duplicados. | WEB-24, TRACK-09 | Infraestructura 06 + Transporte + QA 03 |
| I06-08 | Repetir corte con cursor fuera de ventana: `resync.required`, instantánea autorizada, hueco explícito y ninguna posición inventada. Durante corte revocar sesión/asignación en una cuenta: al restaurar no recibe B/C ni conserva datos privados visibles. Cuenta aún autorizada sí recupera. Probar cambio de rol, expiración y logout con mapa abierto por el mismo gateway. Medir recepción backend–mapa con IDs; no atribuirlo a captura física. | TRACK-09/10 | Transporte/Identidad + QA 03 + 06 |
| I06-09 | Consolidar casos, manifiesto de fuentes/imágenes, logs saneados, capturas y consultas de persistencia. Separar los 90 casos históricos, las pruebas locales añadidas y los nuevos recorridos de infraestructura. No sumar subpasos como casos. Solo cerrar criterios con evidencia obtenida y aplicable. | TRACK-10 | QA + responsables 03/06 |

La caída total se refiere a los procesos de rastreo, no a apagar el gateway compartido
con el portal: apagar la entrada completa impediría probar continuidad web por esa
misma entrada. Si el despliegue usa un gateway exclusivo de rastreo, agregar también
su parada/restauración; documentar topología y alcance exactos.

Las URL firmadas duran actualmente cinco minutos. La revocación se verifica antes de
emitir una nueva firma; una URL ya emitida es una credencial temporal independiente.
El ensayo debe registrar esa ventana y no prometer revocación instantánea de una URL
ya entregada. Si 06 exige invalidación inmediata, resolver ese requisito antes de
aceptar integralmente; no ocultarlo bajo una prueba de permiso previo.

## Preparación técnica reutilizable y límites

Código existente que debe revisarse y aplicarse **solo al entorno autorizado**:
`deployment/gcp/configure_scanner.py` prepara el motor privado para Documentos/web;
`deployment/gcp/configure_public.py` prepara TLS/WSS y orígenes;
`deployment/nginx.conf` define los upstreams. No se ejecutaron estos configuradores
en la instalación habitual. Sus defaults apuntan a `.local/compose`: no usarlos sin
`--directory` del ensayo. La copia local histórica solo monta GCS en web/Transporte;
no es una configuración suficiente del propietario Documentos actual.

Para un proyecto Compose **ya aislado y validado**, el operador puede preparar los
comandos de corte con variables explícitas; estos ejemplos no arrancan ni crean recursos:

```sh
# Establecer TEST_COMPOSE y TEST_PROJECT con los valores aprobados en el expediente.
# Antes de cada corte, comprobar IDs y etiquetas del proyecto de prueba.
docker compose -f "$TEST_COMPOSE" -p "$TEST_PROJECT" ps --format json
# I06-05: únicamente tras aprobación de la ventana y comprobación de aislamiento.
docker compose -f "$TEST_COMPOSE" -p "$TEST_PROJECT" stop clamav
docker compose -f "$TEST_COMPOSE" -p "$TEST_PROJECT" start clamav
# I06-07: aplicar únicamente si estas réplicas son las autoridades WSS identificadas.
docker compose -f "$TEST_COMPOSE" -p "$TEST_PROJECT" stop transporte-a transporte-b
docker compose -f "$TEST_COMPOSE" -p "$TEST_PROJECT" start transporte-a
docker compose -f "$TEST_COMPOSE" -p "$TEST_PROJECT" start transporte-b
```

No ejecutar `deployment/verify.py --phase all`, `start.py`, `create.sh` o `publish.sh`
sobre sus defaults para cumplir este plan: pueden mutar/reiniciar la demostración o
crear recursos. El ensayo no requiere aprobar todas esas acciones ni gastos implícitos.

Restaurar únicamente componentes/red del ensayo que estaban disponibles al comenzar.
Verificar salud y operación después, conservar artefactos y programar limpieza por
IDs/prefijos exactos según retención. No usar borrado masivo ni `down -v`.

## Solicitud mínima para ejecutar lo pendiente

Identificar **un entorno aislado existente** (URL/host/proyecto, bucket/prefijos,
identidad y ClamAV), confirmar que puede ejecutar el árbol/esquema 17 y autorizar
únicamente escritura de datos ficticios y cortes/restauración de los componentes de
I06-05/07/08. Si requiere recursos nuevos o encender la VM habitual, primero presentar
alternativa aislada y coste para aprobación separada. No se solicita acceso a datos
reales, cambios IAM generales ni permiso para detener producción.

Sin esos prerrequisitos, los casos I06-01 a I06-09 quedan pendientes de aceptación
integrada en 06; mantener la aceptación local y sus límites en la matriz vigente.
