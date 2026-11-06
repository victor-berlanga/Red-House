# Evidencias y reproducción

## 1. Entorno y fuentes

La auditoría se ejecutó el 28 de octubre de 2026 en el repositorio local de macOS, con Python de `apps/services/.venv`, PostgreSQL/MongoDB/Redis temporales y datos ficticios. Los fixtures controlaron sus propios procesos y puertos. No se usó la base habitual, producción ni una instancia GCP como entorno de pruebas.

El sandbox requirió permiso para sockets locales y procesos de prueba. Las ejecuciones autorizadas mantuvieron ese ámbito. No se detuvieron procesos ajenos ni se desplegó código.

La identificación completa está en [el manifiesto original (archivo)](../../../documentation/evidencias/archivo/detalles-20261104.tar.gz): commit `8909baf8458dff797d40d15541c57c66c14ef964`, cambios locales, 3.105 archivos y SHA-256 agregado `d7f5ec0024d6ce058616fee97973f28895c312a9c8d59e98db7a1eec63370184`. No atribuir los resultados al commit limpio ni a cualquier modificación posterior.

## 2. Archivos y resultados

Las horas de comienzo son las registradas por JUnit con zona `-06:00`. Las duraciones siguientes proceden del XML; pueden diferir ligeramente del tiempo de consola/arranque del comando.

| Archivo original archivado | Inicio 28/10/2026 | Duración XML | Resultado |
| --- | --- | ---: | --- |
| [redhouse-audit-01-current.xml](evidencias/redhouse-audit-01-current.xml) | 09:17:52.540176 | 189.412 s | 323 casos: 119 aprobados, 202 errores de preparación, 2 omitidos |
| [redhouse-audit-01-startup.xml](evidencias/redhouse-audit-01-startup.xml) | 09:20:14.641654 | 89.649 s | 8 aprobados |
| [redhouse-audit-01-backend.xml](evidencias/redhouse-audit-01-backend.xml) | 09:22:22.476330 | 1266.982 s | 166 casos: 165 aprobados, 1 omitido |
| [redhouse-audit-01-withdrawal.xml](evidencias/redhouse-audit-01-withdrawal.xml) | 09:35:15.344089 | 126.720 s | 19 aprobados |
| [redhouse-audit-01-remaining.xml](evidencias/redhouse-audit-01-remaining.xml) | 09:44:59.392811 | 275.605 s | 82 casos: 81 aprobados, 1 omitido |
| [redhouse-audit-01-reconciliacion.json](evidencias/redhouse-audit-01-reconciliacion.json) | Cierre 15:55:09 UTC | No aplica | 321 casos distintos aprobados, 2 omitidos; ningún error de preparación pendiente |
| [redhouse-audit-01-schema.json](evidencias/redhouse-audit-01-schema.json) | Misma auditoría | No registrada | Construcción, instalación y restauración del esquema aprobadas |
| [redhouse-audit-01-manifest.json (archivo)](../../../documentation/evidencias/archivo/detalles-20261104.tar.gz) | 15:17:45 UTC | No aplica | Fuentes y hashes individuales del corte probado |

No sumar filas superpuestas. La reconciliación utiliza `(classname, name)` para identificar cada caso, incluye la lista de aprobados y registra ambas omisiones. Las rutas `/tmp` conservadas dentro del JSON son procedencia original; [el índice de archivo](evidencias/archivo_evidencias.json) las relaciona con las copias permanentes y sus hashes.

El intento inicial falló al resolver MongoDB: `RuntimeError: No se encontró mongod compatible (MongoDB 8.0)`. El binario local `.local/tools/mongodb-8.0.17/bin/mongod` estaba disponible. El arranque dirigido posterior funcionó; las ejecuciones restantes especificaron `REDHOUSE_TEST_MONGOD`. No se corrigió código para resolver ese error ni se afirma una causa exacta no comprobada de la detección inicial.

Los casos omitidos son:

- `tests.test_documents_storage::test_gcs_web_upload_private_download_validation_expiry_and_recovery`: requiere bucket real autorizado y ADC; no se simula nube para aprobar ese caso.
- `tests.test_validation_audit::test_browser_validation_and_finding_workflow`: requiere activación explícita `REDHOUSE_BROWSER_TESTS=1`, Node y Playwright.

## 3. Comandos de las ejecuciones

Se ejecutaron desde la raíz del repositorio. Los paths de salida son los originales y se preservaron antes de archivarlos. **Para una ejecución nueva, usar otro directorio temporal; no sobrescribir estas evidencias históricas.** Estos comandos describen pruebas existentes; no añaden ni implementan las pruebas pendientes de los hallazgos.

Intento inicial:

```sh
apps/services/.venv/bin/python -m pytest apps/services/tests \
  -q --tb=short -p no:cacheprovider \
  --junitxml=/tmp/redhouse-audit-01-current.xml
```

Aceptación dirigida de arranque:

```sh
apps/services/.venv/bin/python -m pytest apps/services/tests/test_final_acceptance.py \
  -x -q --tb=short -p no:cacheprovider \
  --junitxml=/tmp/redhouse-audit-01-startup.xml
```

Backend e integración:

```sh
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_final_*.py \
  apps/services/tests/test_algorithms.py \
  apps/services/tests/test_audit_migration.py \
  apps/services/tests/test_catalogue.py \
  apps/services/tests/test_continuity.py \
  apps/services/tests/test_evidence_catalog.py \
  apps/services/tests/test_flows.py \
  apps/services/tests/test_health_evidence.py \
  apps/services/tests/test_resilience.py \
  apps/services/tests/test_review_regressions.py \
  apps/services/tests/test_security_contracts.py \
  apps/services/tests/test_shared_database.py \
  apps/services/tests/test_validation_audit.py \
  -q --tb=short -p no:cacheprovider \
  --junitxml=/tmp/redhouse-audit-01-backend.xml
```

Baja e historial de donantes:

```sh
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
apps/services/.venv/bin/python -m pytest apps/services/tests/test_donor_withdrawal.py \
  -q --tb=short -p no:cacheprovider \
  --junitxml=/tmp/redhouse-audit-01-withdrawal.xml
```

Bloque restante de regresión:

```sh
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_documents_storage.py \
  apps/services/tests/test_form_limits.py \
  apps/services/tests/test_maintenance_web.py \
  apps/services/tests/test_product_ui.py \
  apps/services/tests/test_ui_cache.py \
  apps/services/tests/test_web_integration.py \
  apps/services/tests/test_web_sessions.py \
  -q --tb=short -p no:cacheprovider \
  --junitxml=/tmp/redhouse-audit-01-remaining.xml
```

Instalación/restauración estructural, sin regenerar el archivo de esquema:

```sh
apps/services/.venv/bin/python scripts/build_shared_schema.py --check \
  > /tmp/redhouse-audit-01-schema.json
```

Para repetir toda la regresión después de una implementación autorizada, puede ejecutarse la suite completa con la ruta de MongoDB explícita y una salida nueva:

```sh
AUDIT_RESULTS_DIR="$(mktemp -d /tmp/redhouse-etapa01-nueva.XXXXXX)"
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
apps/services/.venv/bin/python -m pytest apps/services/tests \
  -q --tb=short -p no:cacheprovider \
  --junitxml="$AUDIT_RESULTS_DIR/regresion.xml"
```

Ese último comando es una guía para la siguiente ejecución, **no una corrida adicional realizada en esta auditoría**. Antes de usarlo, comprobar binarios/fixtures y mantener aislamiento. No ejecutar comandos de migración sobre la base habitual como sustituto de la prueba temporal.

Ruff crítico (`E9,F63,F7,F82`) y `git diff --check` aprobaron durante la revisión. No hay un log independiente archivado de esos dos controles. Una futura verificación debe registrar su comando exacto y resultado; no atribuirles un JUnit inexistente.

## 4. Evidencia funcional concreta

| Criterio | Casos existentes ejecutados | Qué acredita y qué no |
| --- | --- | --- |
| Unidad única ante dos solicitudes | `test_flows.py::test_two_requests_cannot_reserve_same_resource` | Un ganador y un rechazo, comprobación persistida; no prueba F2 |
| Cobertura de solicitud de una unidad | `test_flows.py::test_two_units_cannot_overfill_one_unit_request` | No sobrecobertura concurrente |
| Reserva idempotente | `test_flows.py::test_idempotent_reservation_does_not_duplicate` | Repetición sin segunda reserva |
| Cupo campaña/franja | `test_catalogue.py::test_campaign_capacity_serializes_different_donors`; `test_final_operations.py::test_consent_agenda_capacity_reminders_processing_and_lineage` | Competencia, cancelación/reprogramación, asistencia y recordatorios; no elegibilidad clínica automática |
| Actor/tenant/asignación ajenos | `test_security_contracts.py::test_institution_role_and_assignment_authorization` y variantes de seguridad/calidad | Rechazo y permisos actuales en los escenarios cubiertos |
| Escritura con respuesta perdida | `test_resilience.py::test_lost_confirmation_response_can_resume_without_duplicate` | Escritura real y respuesta perdida inyectada; PENDING recuperable sin duplicación |
| Error de auditoría local | `test_resilience.py::test_local_audit_failure_rolls_back_and_compensates_hold` | Rollback y compensación de retención; no cubre ausencia de emit en F7 |
| Custodia caída | `test_custody_service_down_does_not_lose_physical_event` | Hecho persistido y consumo posterior; no obligatoriedad de custody de F3 |
| Recepciones concurrentes | `test_receipt_closes_multiunit_request_once` | Cierre único de solicitud multiunidad; recepción no equivale a transfusión/trasplante |
| Laboratorio y frío | `test_final_quality.py::test_laboratory_missing_results_correction_quarantine_and_final_destination` | Faltantes, autorización, cuarentena y destino válido; no corrección inválida F1 ni evaluación antigua tras autorización F2 |
| MFA y recuperación | `test_final_identity.py::test_mfa_reauth_contact_recovery_and_revocation` | TOTP, proof, contacto, token de un uso y revocación JSON/XML |
| Políticas y perfil operativo | `test_final_acceptance.py` | Catálogos/responsables, perfil requerido, ejemplos WSS, ACL preservada, correcciones inmutables y worker repetible |
| SMTP/push | `test_final_delivery_documents.py::test_smtp_push_retry_escalation_dedup_and_close` | Receptores locales TCP/HTTP, fallo/reintento, escalamiento/cierre; no lectura humana |
| Documentos/reportes | Otros casos de `test_final_delivery_documents.py` | Hash/generación, autorización, análisis, CSV/PDF/XLSX; doble GCS, receptor ClamD y EXPIRY, no todas las familias |
| Autonomía web | `test_continuity.py` | Flujos sangre/órgano/donación con API detenidas y Redis fallando/recuperado; políticas académicas |
| Migraciones | `test_audit_migration.py`, `test_shared_database.py` | Copias estructurales, datos sintéticos conservados, privilegios/relaciones y repetición |
| Contratos HTTP | `test_evidence_catalog.py::test_all_registered_routes_expose_real_http_contracts_and_controlled_errors` | Salud/documentación y errores JSON/XML de rutas registradas; no alta positiva de cada ruta |
| Datos comprometidos y recuperación | `test_evidence_catalog.py::test_edits_details_and_recovery_have_http_and_committed_evidence` | Ediciones/consultas, SQL persistido y reanudación; incluye ruta antigua de telemetría de F5 |
| Paquetes y ejemplos | `test_review_unit.py`, incluido `test_catalogue_schemas_and_examples_compile_without_dependencies` | Aislamiento de once paquetes y esquemas/ejemplos; no despliegue Docker/GCP |

Consultar nombres completos parametrizados y resultados en el [JSON de reconciliación](evidencias/redhouse-audit-01-reconciliacion.json). No trasladar el nombre de una prueba a un archivo diferente sin comprobarlo; la lista de aprobados conserva la clase/módulo exactos.

## 5. Rastreo y métricas

`test_final_tracking.py` ejecutó canales WSS reales JSON/XML con TLS, autorización de dispositivo/suscriptor, persistencia y replay; duplicados/desorden; datos inválidos/XXE; normalizador RMC; sincronización y conflictos; CLI con reconexión; caída de Redis, PostgreSQL y MongoDB; límites/Origin/ámbito; recepción separada de destino final; dos procesos WSS y concurrencia.

`test_concurrent_emitters_subscribers_and_delayed_consumer` registra en el JUnit backend:

| Propiedad | Valor actual |
| --- | ---: |
| `publishers` | 2 |
| `delayed_subscribers` | 2 |
| `points` | 24 |
| `ack_mean_ms` | 422.755 |
| `ack_p95_ms` | 540.881 |

Pytest emitió una advertencia por `record_property` con `junit_family=xunit2`; las propiedades quedaron registradas. No fue un fallo funcional. Estos valores sustituyen únicamente la medición local de esta auditoría, no reescriben los históricos 304.948/427.112 ms.

La prueba de dos procesos no acredita caída total de API ni interrupción de socket abierto: ver F10. Los escenarios de F4/F6 no están cubiertos por las aserciones existentes. La latencia medida no llega a mapa, teléfono ni equipo físico.

## 6. Aplicabilidad de evidencia anterior

El [expediente de implementación anterior](../../../documentation/evidencias/entrega-final/backend/RESULTADOS.md) conserva regresión de 283 casos (280 aprobados, un fallo, dos omitidos), integración 18, cierre 53, políticas 32 (30 aprobados y dos fallos), corrección 8 y autonomía/contratos 8. No sumar esos intentos ni presentarlos como una ejecución actual de todas las fuentes modificadas.

Sus JSON identifican versión y hash de esquema, pero no un manifiesto completo equivalente de todas las fuentes locales del runtime. Esta auditoría aporta identificación y reejecución actuales. Los resultados históricos no prueban despliegue nuevo, hardware, mapas ni corrección de F1–F11.

## 7. Integridad y conservación

Los ocho originales se copiaron byte a byte a `evidencias/`. El [índice de archivo](evidencias/archivo_evidencias.json) contiene ruta de procedencia, copia relativa, tamaño y SHA-256. No se reescribieron los JUnit ni sus errores para producir un resultado más favorable. Los JSON originales mantienen sus rutas `/tmp` de procedencia; los documentos de este expediente enlazan las copias permanentes.

El manifiesto de fuentes se preserva tal como se creó antes del archivado. Añadir este expediente y el enlace de `PROJECT_STATUS.md` no convierte esas modificaciones documentales en parte de la ejecución auditada. Una siguiente implementación necesita un nuevo manifiesto y pruebas aplicables a sus fuentes finales.

**NO APTA PARA CONTINUAR**
