# Manual técnico

Corte: 17/11/2026, rama `entrega-final`. Documento único de entrada para quien mantenga Red House. No sustituye a las guías que enlaza: resume qué contiene cada una y en qué orden consultarlas. Cuando una guía y este índice difieran, prevalece la guía del componente y su evidencia fechada. El [estado del proyecto](../../PROJECT_STATUS.md) distingue lo implementado de lo pendiente.

Este manual no ejecutó servicios, pruebas ni publicaciones. Los comandos se copian de las guías citadas; requieren sus prerrequisitos, credenciales privadas y autorización.

## 1. Ruta de lectura

| Necesidad | Empieza en | Después |
| --- | --- | --- |
| Entender el sistema | [Arquitectura](Arquitectura.md) | [Documento técnico final](Reporte_tecnico_final.md), [fichas de microservicios](../entrega-final/modelos/Fichas_microservicios.md), [diagramas](../entrega-final/modelos/diagramas/) |
| Instalar en un equipo | [Instalación y operación](Instalacion_y_operacion.md) | [Docker Compose](../../deployment/README.md) |
| Operar la VM de GCP | [GCE](../../deployment/gcp/README.md) | Sección 9 de este manual |
| Cambiar un microservicio | [Guía de servicios](../../apps/services/README.md) | [Datos y persistencia](Datos_y_persistencia.md), [esquema compartido](Esquema_compartido.md) |
| Cambiar el portal | [Portal web](../../apps/web/README.md) | [Integración web](Integracion_web.md), [pantallas y permisos](../entrega-final/portal/Pantallas_y_permisos.md), [operación del portal](../entrega-final/portal/Operacion.md) |
| Cambiar Android/iOS | [Móvil](../../apps/mobile/README.md) | [Matriz móvil](../entrega-final/mobile/Matriz.md) |
| Cambiar la consola de escritorio | [Escritorio](../../apps/desktop/README.md) | [Matriz de escritorio](../evidencias/entrega-final/desktop/MATRIZ.md), [distribución](../entrega-final/continuidad/Distribucion_escritorio.md) |
| Revisar algoritmos | [Algoritmos](Algoritmos.md) | [Reglas y fuentes clínicas](Reglas_y_fuentes_clinicas.md), [CONT-01 HLA](../entrega-final/continuidad/CONT01_HLA.md) |
| Probar | [Pruebas y validación](Pruebas_y_validacion.md) | Sección 6 de este manual |
| Diagnosticar un fallo conocido | [Registro de incidencias](../entrega-final/Registro_incidencias.md) | Sección 10 de este manual |
| Saber qué falta | [Matriz de continuidad](../entrega-final/continuidad/Matriz.md) | [Limitaciones del documento técnico](Reporte_tecnico_final.md) («Limitaciones, riesgos y trabajo pendiente») |

## 2. Mapa de componentes y puertos

Monorrepositorio con un portal Flask/Jinja2, doce unidades de servicio (once de dominio y Monitoreo), dos clientes nativos y la infraestructura de despliegue. Los puertos locales y de Compose solo escuchan en loopback; en la VM, Nginx publica HTTPS y enruta por prefijo.

| Componente | Carpeta | Local (`start.sh`) | Compose local | Prefijo público HTTPS |
| --- | --- | --- | --- | --- |
| Portal web y su worker de sesiones | [`apps/web/`](../../apps/web/README.md) | 5050 | 6050 | `/` |
| Identidad y acceso | `apps/services/ms_identidad_acceso/` | 5101 | 6101 | `/services/identidad-acceso` |
| Donantes | `apps/services/ms_donantes/` | 5102 | 6102 | `/services/donantes` |
| Receptores | `apps/services/ms_receptores/` | 5103 | 6103 | `/services/receptores` |
| Inventario | `apps/services/ms_inventario/` | 5104 | 6104 | `/services/inventario` |
| Compatibilidad | `apps/services/ms_compatibilidad/` | 5105 | 6105 | `/services/compatibilidad` |
| Priorización y geografía | `apps/services/ms_priorizacion_geografia/` | 5106 | 6106 | `/services/priorizacion-geografia` |
| Transporte | `apps/services/ms_transporte/` | 5107 | 6107 | `/services/transporte` |
| Custodia | `apps/services/ms_custodia/` | 5108 | 6108 | `/services/custodia` |
| Alertas | `apps/services/ms_alertas/` | 5109 | 6109 | `/services/alertas` |
| Auditoría | `apps/services/ms_auditoria/` | 5110 | 6110 | `/services/auditoria` |
| Monitoreo | [`apps/services/servicio_monitoreo/`](../../apps/services/servicio_monitoreo/README.md) | 5111 | 6111 | `/services/monitoreo` |
| Documentos y reportes | `apps/services/ms_documentos/` | 5112 | 6112 | `/services/documentos` |
| PostgreSQL, Redis, MongoDB | [`data/database/`](../../data/database/README.md) | Configuración privada | Sin puerto publicado | No publicados |
| ClamAV (análisis de archivos) | [`deployment/gcp/`](../../deployment/gcp/README.md) | — | Override privado | No publicado |
| App Android/iOS (Kotlin Multiplatform) | [`apps/mobile/`](../../apps/mobile/README.md) | — | — | Consume `https://34.18.186.116` por defecto |
| Consola de escritorio (PySide6) | [`apps/desktop/`](../../apps/desktop/README.md) | — | — | Consume `https://34.18.186.116` por defecto (`REDHOUSE_BASE_URL`) |

Fuentes: tabla de puertos de la [guía de servicios](../../apps/services/README.md), puertos Compose de [`deployment/README.md`](../../deployment/README.md) y [`compose.yaml`](../../compose.yaml), prefijos de [GCE](../../deployment/gcp/README.md). Cada servicio expone `/docs`, `/openapi.json`, `/schemas/<operación>.xsd`, `/health/live` y `/health/ready`; las rutas `/internal/` están bloqueadas en la entrada pública.

**Procesos.** Cada API tiene un worker de eventos (cada cinco segundos); Monitoreo sondea cada treinta. En Compose hay dos réplicas por API (`-a` y `-b`), cada una con API y worker supervisados. El portal opera en `BACKEND_MODE=monolith` (módulos propios con credenciales limitadas) o `microservices` (consume HTTP); el modo se fija antes de operar.

**Clientes.** Móvil usa solo JSON; escritorio usa XML validado contra XSD. Ninguno accede a bases de datos ni reutiliza cookies del portal.

## 3. Arquitectura, datos y reglas

- [Arquitectura](Arquitectura.md): decisiones de propiedad por servicio, reserva y compensación, traslado y recepción, caché y límites técnicos.
- [Datos y persistencia](Datos_y_persistencia.md) y [esquema compartido](Esquema_compartido.md): base PostgreSQL `red_house` con vistas y roles por servicio, Redis para sesiones/caché/ACL y MongoDB para eventos y proyecciones. Esquema vigente: [`schema.sql`](../../data/database/schema.sql); [modelo físico](../entrega-final/modelos/Modelo_fisico.md) y [relacional](../entrega-final/modelos/Modelo_relacional.md).
- [Expediente backend](../entrega-final/backend/README.md): veinticuatro responsabilidades en doce servicios, outbox, adaptadores y rastreo WSS.
- [Reglas de negocio](Reglas_de_negocio.md) y [perfiles y permisos](Matriz_de_perfiles_y_permisos.md): siete perfiles (Administrador, Operador, Médico, Coordinador, Personal de traslado, Auditor, Donante). La autorización efectiva la decide el servicio propietario en cada petición.
- [Algoritmos](Algoritmos.md): preselección ABO/RhD, orden operativo, cobertura Hopcroft–Karp, rutas, demanda y consistencia, con versión y explicación. Son apoyo; el dictamen y la liberación son humanos.

## 4. Instalación y arranque

| Escenario | Guía | Comandos de entrada |
| --- | --- | --- |
| Equipo local (macOS verificado; Ubuntu con paquetes previos; Windows vía WSL) | [Instalación y operación](Instalacion_y_operacion.md) | `bash install.sh`, `bash start.sh`, `bash components.sh estado`, `bash stop.sh` |
| Servicios sin lanzador | [Guía de servicios](../../apps/services/README.md) | `scripts/local.py init/start/status/stop --directory RUTA` |
| Docker Compose aislado | [Docker](../../deployment/README.md) | `python3 deployment/prepare.py`, bootstrap y `python3 deployment/start.py` |
| VM de GCP | [GCE](../../deployment/gcp/README.md) | `sudo systemctl status redhouse`; `sudo python3 /opt/redhouse/deployment/start.py` |
| Android | [Móvil](../../apps/mobile/README.md) | `./gradlew :composeApp:testDebugUnitTest :composeApp:assembleDebug` |
| iOS | [Móvil](../../apps/mobile/README.md), sección iOS | `xcodegen generate` y Xcode con firma propia |
| Escritorio (macOS x86_64, Python 3.12.6) | [Escritorio](../../apps/desktop/README.md) | `.venv/bin/python -m redhouse_desktop` |

Datos y secretos locales viven en `.local/runtime/` (o `.local/compose/` para Docker), fuera de Git. `state.json`, `web-secrets.env` y los JSON por servicio contienen credenciales: no se adjuntan a reportes. Las actualizaciones con cambio de esquema siguen el procedimiento de [actualizar una instalación existente](Instalacion_y_operacion.md) y, para 0.4.1 en adelante, el [plan de despliegue y rollback](../entrega-final/backend/correccion/Despliegue_y_rollback.md). Nunca se aplica el bootstrap de instalación vacía sobre datos existentes ni `docker compose down -v`.

## 5. Contratos JSON/XML y Swagger

Cada servicio guarda en `contracts/` su `openapi.json`, los XSD de entrada, los ejemplos JSON/XML y las respuestas de referencia (por ejemplo, [Alertas](../../apps/services/ms_alertas/contracts/)). La consola de escritorio conserva una copia en [`redhouse_desktop/contracts/`](../../apps/desktop/redhouse_desktop/contracts/). Swagger publicado: `https://34.18.186.116/services/<servicio>/docs/`.

Los contratos se generan desde el código; no se editan a mano. Desde la raíz, con dependencias de servicios instaladas y sin bases de datos:

```bash
python apps/services/scripts/document.py --openapi-only     # regenera los doce openapi.json
python apps/services/scripts/document.py --check-openapi    # comprueba sin escribir (lo ejecuta CI)
python apps/services/scripts/document.py --contracts-only   # contratos y XSD sin reescribir los apuntes
python -m pytest apps/services/tests/test_openapi_documentation.py -q
```

Sin opciones, `document.py` regenera contratos y además los apuntes TXT de `stuff/presentacion/`. Después de cambiar un contrato que consume escritorio, desde `apps/desktop`: `python sync_contracts.py` y luego `python sync_contracts.py --check`; repetir sus pruebas. El móvil valida la envoltura y los tipos que usa cada operación; no hay copia de XSD en móvil.

Convenciones para consumir la API (login, `Authorization: Bearer`, `Accept`, `Idempotency-Key`, `X-Correlation-ID`, paginación y respuestas 202): [Consumir la API](../../apps/services/README.md).

## 6. Pruebas por componente

| Componente | Comando o arnés | Notas |
| --- | --- | --- |
| Servicios (suite completa) | Desde `apps/services`: `REDHOUSE_TEST_MONGOD=/ruta/a/mongod .venv/bin/python -m pytest tests -q` | Crea PostgreSQL, Redis y MongoDB temporales; conserva el directorio para diagnóstico |
| Algoritmos y HLA | `apps/services/.venv/bin/python -m pytest apps/services/tests/test_final_algorithms_hla.py -q` | Ensayo aislado 13→14 con datos ficticios |
| Contratos OpenAPI | `python apps/services/scripts/document.py --check-openapi` | Sin bases ni secretos |
| Portal (integración HTTP) | Incluidas en `apps/services/tests/` (`test_web_*.py`, `test_portal_*.py`) | Se ejecutan con la suite de servicios |
| Portal (navegador) | Recorridos Chrome/Playwright en `apps/web/tests/*.cjs` | Leen un `state.json` privado; no publican credenciales |
| Portal (plantillas) | `apps/web/tests/test_list_references.py` con `apps/web/requirements-dev.txt` | Sin servicios ni sesión |
| Docker | `apps/services/.venv/bin/python deployment/verify.py --phase all` | Caídas de réplicas, sustitución por etapas y reinicio de almacenes |
| Respaldo Docker | `apps/services/.venv/bin/python deployment/backup.py --verify` | Restaura en contenedores nuevos y compara conteos y hashes |
| Sesiones web | `apps/services/.venv/bin/python deployment/verify_web_sessions.py` | Portal iniciado |
| Clon limpio | `python3 deployment/check_clean_clone.py` | Con el Compose habitual detenido |
| Android (JVM) | `./apps/mobile/gradlew -p apps/mobile :composeApp:testDebugUnitTest` | Con `REDHOUSE_MOBILE_LAB` usa servicios reales del laboratorio |
| Android (instrumentación) | `adb shell am instrument ...` por clase | Orden y requisitos por clase en la [guía móvil](../../apps/mobile/README.md) |
| iOS | `./gradlew :composeApp:compileTestKotlinIosArm64` | Compila pruebas; no las ejecuta en iOS |
| Escritorio | `.venv/bin/python -m pytest tests/test_client.py tests/test_journal.py tests/test_ui.py tests/test_label_output.py` | CI ejecuta `tests` sin `*_lab.py` ([workflow](../../.github/workflows/desktop.yml)) |
| Escritorio empaquetado | Ejecutable con `--smoke-report RUTA` | Sin sesión ni red; `QT_QPA_PLATFORM=offscreen` en CI |
| Carga | `apps/services/tests/locustfile.py` con `REDHOUSE_LOAD_ISOLATED=1` | Solo laboratorio aislado; [arnés y límites](../evidencias/entrega-final/carga-20261113/RESULTADOS.md) |

CI está definida en [`services.yml`](../../.github/workflows/services.yml) y [`desktop.yml`](../../.github/workflows/desktop.yml). Un pase local no acredita una ejecución remota del workflow. Los resultados y fallos conservados están en [Pruebas y validación](Pruebas_y_validacion.md) y en cada `RESULTADOS.md` de `documentation/evidencias/`.

## 7. Seguridad

Resumen; detalle en la sección «Seguridad, privacidad y auditoría» del [documento técnico final](Reporte_tecnico_final.md) y en [Seguridad y resiliencia](../../apps/services/README.md) de la guía de servicios.

- JWT RS256 de 900 s, renovación opaca de hasta 24 h con rotación y detección de reutilización. Redis valida sesión, revocación y permisos en cada petición; si Redis falla, la API protegida responde 503.
- Llamadas internas firmadas con Ed25519 (nonce, ventana de 30 s) y JWT delegado; credenciales de servicio con listas explícitas de emisores.
- MFA de seis dígitos y reautenticación para acciones críticas. El comprobante de reautenticación aún no está ligado al cuerpo ni es de un solo uso ([INC-185](../entrega-final/Registro_incidencias.md#inc-185); [diseño propuesto](../entrega-final/continuidad/Diseno_reautenticacion_un_uso.md)).
- Portal: CSRF, cookies `Secure`/`HttpOnly`/`SameSite=Lax`, sesiones cifradas en Redis y revocaciones pendientes en `web_runtime.session_revocations`.
- Archivos: análisis ClamD con vigencia de firmas; un escáner caído o antiguo falla seguro ([vigilancia](../entrega-final/continuidad/CLAMD_VIGENCIA.md)). Almacenamiento privado `LOCAL` por defecto; GCS opcional.
- Secretos, ADC, claves, `state.json` y respaldos nunca entran en Git ni en evidencias.

## 8. Monitoreo y salud

- [Servicio de Monitoreo](../../apps/services/servicio_monitoreo/README.md) (5111): sondea cada treinta segundos y conserva disponibilidad, latencia, versión y dependencia que falla. En el portal: **Estado de la plataforma** (`/monitoreo`) para Administrador, Coordinador y Auditor.
- `/health/live` indica que el proceso responde; `/health/ready` comprueba esquema y dependencias aplicables; `/health/worker` el worker. Una respuesta sana es un instante; no prueba el negocio completo.
- Logs locales en el directorio privado (`<servicio>.log`, `<servicio>-worker.log`, `web.log`, bases). En la VM: `sudo journalctl -u redhouse` y `sudo docker compose ps` ([GCE](../../deployment/gcp/README.md)).

## 9. Respaldo, recuperación y publicación

**Respaldo y recuperación.** Docker: [Respaldo y recuperación](../../deployment/README.md) y `deployment/backup.py --verify`. VM nueva desde respaldo: procedimiento de copia en [GCE](../../deployment/gcp/README.md) (`package.py`, `restore.py`, `redhouse.service`, `publish.sh`). Ensayo coordinado y valores observados (RTO 21,733 s, RPO 23,787 s, no son SLA): [plan de recuperación](../entrega-final/continuidad/Plan_recuperacion_coordinada.md). La restauración en otro equipo sigue sin probar ([INC-420](../entrega-final/Registro_incidencias.md#inc-420)).

**Publicación acotada en GCP.** Procedimiento usado el 18/11/2026 para publicar la corrección `0edf74d` de Alertas, sin reconstruir dependencias ni tocar otros contenedores ([resultado](../evidencias/entrega-final/gcp-alert-detail-20261118/RESULTADOS.md)):

1. Acceder a la VM `red-house` (proyecto `sistemas-integracion-01`, zona `me-central1-a`) por OS Login/IAP con cuenta propia y clave temporal.
2. Comprobar por SHA-256 que las fuentes en ejecución en `/opt/redhouse` coinciden con el commit base, para que la imagen nueva solo cambie la corrección.
3. Derivar la imagen nueva de la imagen en uso con un `Dockerfile` de `COPY` de las fuentes cambiadas (propietario UID 10001), con etiqueta nueva y conservando la base.
4. Respaldar en `/opt/redhouse/.local/compose/backups/<corte>/` las fuentes y el override privado `gcs.compose.yaml`; actualizar las fuentes y la etiqueta de las dos réplicas en ese override.
5. Recrear solo las réplicas del servicio: `REDHOUSE_COMPOSE_DIR=/opt/redhouse/.local/compose docker compose -f compose.yaml -f .local/compose/gcs.compose.yaml -f .local/compose/public.compose.yaml up -d --wait --no-deps --no-build <svc>-a <svc>-b`.
6. Comparar `docker ps` antes y después: solo deben cambiar los destinos; los demás conservan ID e imagen y los treinta quedan `healthy`.
7. Verificar desde fuera por HTTPS: `/health/live` y `/health/ready` del servicio, salud y `/login` del portal, `openapi.json` publicado y el comportamiento esperado de la ruta (en ese caso, 401 sin sesión).
8. Borrar temporales de `/tmp` en la VM, retirar la clave SSH temporal del perfil OS Login y sus copias locales. No tocar TLS, Nginx, IAM, buckets ni migraciones si el cambio no lo exige.

Los demás cortes recientes siguen la misma pauta y documentan su rollback preparado: [Inventario 17/11](../evidencias/entrega-final/gcp-inventario-20261117/RESULTADOS.md), [custodia y TLS 17/11](../evidencias/entrega-final/gcp-custody-clock-lab-labels-20261117/RESULTADOS.md), [XML 16/11](../evidencias/entrega-final/gcp-xmlschema-20261116/RESULTADOS.md). Para una actualización completa usar `sudo python3 /opt/redhouse/deployment/start.py`, que incorpora los overrides privados; un `docker compose up` con solo el archivo base omite la entrada HTTPS. El certificado TLS de IP vence el 24/11/2026 14:08:33 UTC y se renueva con `redhouse-certbot.timer`.

**Artefactos de cliente.** Android (cuatro variantes, debug): [lote final 17/11](../evidencias/entrega-final/mobile/final-build-20261117/RESULTADOS.md). iOS: [renovación de perfiles](../evidencias/entrega-final/mobile/profile-renewal-20261117/RESULTADOS.md), vigentes hasta el 24/11/2026. Escritorio macOS Intel: [paquete final 02](../evidencias/entrega-final/desktop/paquete-macos-20261117-02/RESULTADOS.md); sin firma ni notarización, Windows 11 sin aceptación ([INC-423](../entrega-final/Registro_incidencias.md#inc-423)).

## 10. Problemas conocidos

El [registro de incidencias](../entrega-final/Registro_incidencias.md) es la fuente única: 424 entradas al 17/11/2026, 31 abiertas, con causa, acción y fuente citada. Las abiertas que más afectan el mantenimiento:

| Incidencia | Efecto para quien mantiene |
| --- | --- |
| [INC-282](../entrega-final/Registro_incidencias.md#inc-282) | `/health/live` del portal publicado informa un backend fijo; corregido en fuente, pendiente de publicar |
| [INC-290](../entrega-final/Registro_incidencias.md#inc-290) | p95 sobre 2.000 ms con 24 usuarios en Traslados y Tareas propias |
| [INC-185](../entrega-final/Registro_incidencias.md#inc-185) | Reautenticación sin comprobante de un solo uso ligado al cuerpo |
| [INC-203](../entrega-final/Registro_incidencias.md#inc-203) | Transferencia binaria de móvil y escritorio aún pasa por el portal |
| [INC-144](../entrega-final/Registro_incidencias.md#inc-144) | Claves de idempotencia móviles en memoria fuera del diario durable |
| [INC-103](../entrega-final/Registro_incidencias.md#inc-103) | Push FCM/APNs sin proveedor configurado; la bandeja interna funciona |
| [INC-420](../entrega-final/Registro_incidencias.md#inc-420) | Restauración en otro equipo no probada |
| [INC-423](../entrega-final/Registro_incidencias.md#inc-423) / [INC-424](../entrega-final/Registro_incidencias.md#inc-424) | Windows 11 y accesibilidad con lector de pantalla sin aceptación |

Guías de diagnóstico: [Diagnóstico local](Instalacion_y_operacion.md) (puertos, binarios, logs, venv/pip) y [Escrituras inciertas y recuperación](../entrega-final/portal/Operacion.md) (reservas `PENDING`, `inventory_pending`, reanudar con la misma clave).

## 11. Reglas de mantenimiento

- Actualizar el documento del tema y su evidencia fechada; no crear un documento por conversación ([índice documental](../README.md)).
- Un FAIL conservado no se reescribe como PASS; una repetición posterior se registra aparte.
- Datos de prueba siempre ficticios. No proyectar ni versionar `state.json`, ADC, certificados ni respaldos.
- Las migraciones son aditivas y por propietario; no se ejecutan sobre las vistas compartidas ni se usa una migración destructiva para revertir.
- Cada cambio de contrato regenera OpenAPI/XSD, sincroniza la copia de escritorio y repite las pruebas del consumidor.
