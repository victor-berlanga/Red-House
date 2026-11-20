# Matriz de acceso por aplicación

Corte: 19/11/2026. Requisito de la dirección del proyecto (Víctor, 19/11/2026): los siete perfiles de Identidad no cambian; cada aplicación admite solo los perfiles de esta distribución y **el servidor lo aplica**. Complementa la [Matriz de perfiles y permisos](Matriz_de_perfiles_y_permisos.md) (qué puede hacer cada perfil) con **dónde** puede hacerlo.

## 1. Distribución y mecanismo

| Aplicación | Perfiles admitidos | Cabecera de login |
| --- | --- | --- |
| Portal web privado | `ADMIN`, `OPERATOR`, `MEDICAL`, `COORDINATOR`, `AUDITOR` | `X-RedHouse-Client: web` |
| Consola de escritorio | `OPERATOR`, `MEDICAL`, `COORDINATOR` | `X-RedHouse-Client: desktop` |
| App móvil (Android e iOS) | `DONOR`, `TRANSPORT` | `X-RedHouse-Client: mobile` |
| Sitio público y campañas publicadas | Sin sesión | no aplica |

Implementación (Identidad y `redhouse/security.py`):

1. **Login.** `POST /api/v1/auth/login` exige la cabecera. Sin ella, o con un valor distinto de `web`, `desktop` o `mobile` (se distingue mayúsculas), responde **400 `client_required`** (falla cerrada, antes de revisar credenciales). Con credenciales válidas pero perfil fuera de la aplicación responde **403 `client_not_allowed`** con un mensaje en español que dice qué aplicación usar (por ejemplo: «Tu perfil no puede iniciar sesión en el portal web. Usa la aplicación móvil.»). Ese rechazo no cuenta como intento fallido ni bloquea la cuenta; queda en la bitácora como `LOGIN_FAILED` con `reason=client_not_allowed`.
2. **Sesión.** La aplicación se guarda en la sesión (tabla `sessions.client`, migración compartida 22; Redis `session:<sid>`) y como claim `client` del JWT.
3. **Cada petición protegida** (`authenticate()` en todos los servicios): si la sesión no tiene aplicación o el claim no coincide, **401** («inicia sesión de nuevo»); si el perfil vigente ya no corresponde a la aplicación de la sesión, **403 `client_not_allowed`**. Después se evalúan, sin cambios, rol de la operación, ámbito institucional y recurso.
4. **Refresh.** Conserva la aplicación y vuelve a validar perfil contra aplicación (403 si dejó de corresponder). Un cambio de perfil o estado ya revocaba las sesiones.
5. **Sesiones emitidas antes del cambio** no tienen aplicación: se rechazan con 401 y la persona debe iniciar sesión de nuevo. `apps/services/scripts/revocar_sesiones_sin_cliente.py` (`--dry-run` por omisión, `--aplicar`) las revoca en SQL y Redis al publicar; es idempotente. No afecta cuentas, roles, dispositivos ni datos. En Compose/VM se ejecuta dentro de la imagen bootstrap: `docker compose --profile install run --rm --entrypoint python bootstrap -m scripts.revocar_sesiones_sin_cliente --directory /run/install [--aplicar]` (después de `upgrade_compose.py`, que aplica la migración 22 y es requisito: sin ella los servicios no pasan su prueba de disponibilidad).
6. **Llamadas entre servicios** no se alteran: firman con su identidad de servicio (`internal_auth`); cuando delegan la identidad de una persona reenvían su JWT, que ya trae su aplicación.
7. **Móvil.** `POST /api/v1/mobile/devices` y su revocación quedan limitados a `DONOR` y `TRANSPORT`; el inicio de rastreo móvil ya era solo `TRANSPORT`.

## 2. Matriz aplicación × perfil × operación

Ámbito de datos: *propio* = registros de la persona; *institución* = su institución; *región* = región con vista minimizada. Cada operación sigue verificando rol, ámbito y recurso en el servidor, sin importar la aplicación. Columna **Prueba**: pasos de aceptación; `TA` = `apps/services/tests/test_acceso_por_aplicacion.py`.

### 2.1 Portal web

| Perfil | Operaciones | Ámbito | Prueba de aceptación |
| --- | --- | --- | --- |
| ADMIN | Cuentas (alta, estado, perfil), instituciones, catálogos (sedes, capacidades, contactos, horarios, ubicaciones), dispositivos de traslado, configuración y política, monitoreo | Institución propia (instituciones de la región solo lectura) | Iniciar en web con `admin1`: 200 (`TA::test_login_by_role_and_client_matrix`); `/administracion/users`, `/catalogos/sites`, `/administracion/dispositivos` abren; `operator1` en `/configuracion` recibe 403 |
| OPERATOR | Inventario, donantes autorizados, donaciones y procesamiento, citas y campañas, conservación y etiquetas, traslados (preparar en origen, aceptar en destino, incidencia), reportes, archivos | Institución | Login web `operator1` 200; `/inventario`, `/citas`, `/traslados` abren; recurso de otra institución: 403/404 (`TA::test_resource_outside_the_scope_stays_denied_with_a_desktop_session`) |
| MEDICAL | Donantes y receptores, solicitudes, evaluaciones y reservas, laboratorio, consentimientos de donantes, apoyo a decisiones, órganos, reportes | Institución; solo expedientes autorizados | Login web `medical1` 200; `/solicitudes`, `/laboratorio` abren; `/traslados/<id>/mapa` y `/inventario?format=csv` denegados a perfiles sin permiso |
| COORDINATOR | Disponibilidad regional, reservas, propuestas de cobertura, traslados y rutas, rastreo y mapa, hallazgos, monitoreo | Región (minimizada) | Login web `coordinator1` 200; `/disponibilidad`, `/traslados/<id>/mapa` abren |
| AUDITOR | Bitácora, trazabilidad, hallazgos, reportes y monitoreo, solo lectura | Región | Login web `auditor1` 200; ninguna operación de escritura; `/inventario?format=csv` 403 |
| DONOR, TRANSPORT | Ninguna: el login web es 403 `client_not_allowed` («Usa la aplicación móvil») | — | `TA::test_portal_login_refuses_mobile_profiles_with_a_clear_message`; `TA::test_direct_access_to_private_sections_with_a_donor_never_opens_them` (acceso directo a `/panel`, `/campanas`, `/citas`, `/traslados`… sin sesión redirige a `/login`) |

### 2.2 Consola de escritorio

| Perfil | Operaciones | Ámbito | Prueba de aceptación |
| --- | --- | --- | --- |
| OPERATOR | Inventario, captura de resultados, etiquetas, custodia institucional, conservación, donaciones y fraccionamiento, preparar y aceptar traslados | Institución | Login `desktop` 200 (`TA` matriz); `test_client.py::test_every_request_declares_the_desktop_client` |
| MEDICAL | Revisión de pruebas y candidatos, solicitudes, evaluaciones, decisiones, liberación de unidades, receptores | Institución | Login `desktop` 200 |
| COORDINATOR | Planificar traslados, seguimiento de custodia, cobertura, reservas, reportes | Región | Login `desktop` 200 |
| ADMIN, AUDITOR, DONOR, TRANSPORT | Ninguna: 403 `client_not_allowed` con «Usa el portal web» / «la aplicación móvil»; el diálogo de acceso muestra el mensaje del servidor | — | `TA` matriz; `test_client.py::test_login_rejected_for_other_application_keeps_the_server_message` |

### 2.3 App móvil

| Perfil | Operaciones | Ámbito | Prueba de aceptación |
| --- | --- | --- | --- |
| DONOR | Registro preliminar, perfil y nombre propios, consentimiento, campañas y horarios, citas, avisos | Propio | Login `mobile` 200 (`TA` matriz); `SessionTest.loginUsesJsonAndDoesNotStorePassword` envía `mobile`; donante ajeno 403 (`test_donor_personal.py`) |
| TRANSPORT | Órdenes asignadas, escaneo, recolección, tránsito y entrega, incidencias, ubicación y evidencia, registro de dispositivo propio | Tareas asignadas | Login `mobile` 200; `TA::test_mobile_device_registration_is_exclusive_to_mobile_profiles`; `test_mobile_transport.py` |
| ADMIN, OPERATOR, MEDICAL, COORDINATOR, AUDITOR | Ninguna: 403 `client_not_allowed`; la app muestra «Tu perfil no usa la aplicación móvil. Entra al portal web o a la consola de escritorio.» | — | `TA` matriz; `SessionTest.loginRefusedForAnotherApplicationExplainsWhereToEnter` |

### 2.4 Comprobaciones transversales

| Comprobación | Prueba |
| --- | --- |
| Siete perfiles × tres aplicaciones: 200 solo en las combinaciones de la distribución, 403 `client_not_allowed` en el resto | `TA::test_login_by_role_and_client_matrix` (21 casos) |
| Login sin cabecera o con valor desconocido: 400 `client_required` | `TA::test_login_without_or_with_unknown_client_fails_closed` |
| La aplicación queda en SQL, Redis y JWT | `TA::test_client_is_stored_in_sql_and_redis_session` |
| Refresh conserva la aplicación y revalida el perfil | `TA::test_refresh_keeps_client_and_revalidates_role` |
| Perfil vigente que ya no corresponde: 403 en cada petición | `TA::test_active_session_is_rejected_when_current_role_no_longer_fits_the_client` |
| Sesión previa al cambio: 401, sin refresh; el script la revoca | `TA::test_session_issued_before_the_change_is_rejected_and_the_script_revokes_it` |
| El rechazo de aplicación no bloquea la cuenta | `TA::test_wrong_application_does_not_count_as_failed_attempt` |
| Los permisos del portal excluyen DONOR y TRANSPORT | `TA::test_portal_permissions_exclude_mobile_profiles` |

## 3. Huecos de acceso detectados y cerrados (sin cambiar la distribución)

Tareas que un perfil hacía en una aplicación que pierde. Las tres se cerraron el 20/11/2026 en la aplicación autorizada
(móvil), con los endpoints y permisos que ya existían; no se cambió la distribución ni el contrato de la API.

| # | Perfil | Tarea | Dónde existía | Cómo quedó (móvil) | Prueba de aceptación |
| --- | --- | --- | --- | --- | --- |
| H1 | DONOR | Consultar sus «Evaluaciones humanas» | Portal: `people.py` (`person_detail`, sección `reviews`) | Cuenta › Mi expediente › «Evaluaciones del personal médico» (fecha, resultado y nota; sin el id del evaluador) con `GET /api/v1/donors/{id}` | `test_donor_expediente_movil.py` (otro donante de la misma institución recibe 403); `DonorDocumentsTest` |
| H2 | DONOR | Cargar su consentimiento firmado (sujeto `DONOR`, tipo `CONSENT`) | Portal: `documents.py` y `/documentos/nuevo` | Expediente › «Consentimiento firmado»: foto JPEG, progreso, estado (en revisión, verificado, rechazado) y reemplazo con `supersedes`; si falta, aparece como siguiente paso en Inicio | `test_donor_expediente_movil.py` (flujo completo, ámbito, reemplazo e idempotencia); `DonorDocumentsTest` |
| H3 | TRANSPORT | Resumen de tareas, indicadores y reportes de sus traslados | Escritorio: `app.py` (resumen, indicadores, reportes) y `analytics.py` | Inicio › tarjeta «Resumen» y sección con contadores (`/summary`), indicadores (`/portal-metrics`) y reporte CSV de traslados (`/export-jobs`, verificado por SHA-256, para ver y compartir) | `test_transporte_resumen.py` (solo traslados propios); `TransportSummaryTest` |

Límites: el consentimiento se carga como foto (no hay selector de archivos PDF en la app); el reporte móvil es CSV
(el escritorio también ofrecía otros formatos). Falta verlos en emulador e iOS.

Revisadas sin hueco (con la vía en la aplicación autorizada):

- ADMIN en escritorio (usuarios, estado y perfil, registro y revocación de dispositivos, sedes, capacidades; `app.py:188-216`, `institutional_catalogue.py`): el portal los cubre (`administration.py:85,124,174,209`; `configuration.py:143-206`; `maintenance.py:95-160`).
- AUDITOR en escritorio (bitácora, reportes): portal `/auditoria`, `/hallazgos`, `/reportes` (`audit.py:147`, `quality.py:279`).
- OPERATOR en móvil (preparar en origen, aceptar en destino, lectura manual de conservación; `TransportNextStep.kt:13-14`, `TransportScreen.kt:67-121,288`, `OperationalScreens.kt:23`): portal `logistics.py:~230` y `conservation.py:268`; escritorio `app.py:1095` (aceptar), `1136` (preparar), `626-664` (lecturas). Solo el escaneo con cámara es exclusivo del móvil; en escritorio y portal el código de la unidad se captura a mano.
- COORDINATOR y MEDICAL en móvil (`App.kt:32-40`, cancelar antes de recolección en `TransportScreen.kt:264`): portal (`/disponibilidad`, `/reservas`, `/solicitudes`, `/laboratorio`, cancelación en `logistics.py:~262`) y escritorio.
- TRANSPORT en portal (traslados, pasos, incidencias, evidencias, ubicación): móvil (`TransportScreen.kt`, `MobileRepository.kt:151-197`). La página de captura de ubicación del navegador (`logistics.py:344`) queda sin uso.
- DONOR en portal (campañas, citas, avisos, nombre y consentimiento propios): móvil (`DonorScreen.kt`, `MobileRepository.kt:127-134`).
