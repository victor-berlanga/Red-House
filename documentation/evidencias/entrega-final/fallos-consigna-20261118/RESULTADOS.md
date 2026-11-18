# Pruebas de fallas de la consigna — 18 de noviembre de 2026

Base: `2f6fe78` más los cambios de este bloque (instalador con almacenamiento de Documentos y prueba nueva de tiempo de espera). Datos sintéticos, procesos en `127.0.0.1`, sin GCP y sin tocar el laboratorio restaurado.

## 1. Suite automatizada en laboratorio nuevo

Laboratorio temporal propio (`REDHOUSE_TEST_ROOT` en `/private/tmp`, borrado al terminar, sin procesos residuales). Inicio 03:36:35 UTC, fin 03:38:32 UTC. **43 aprobadas, 1 omitida, 0 fallidas** ([junit.xml](junit.xml), [pytest.txt](pytest.txt)).

| Archivo | Casos | Qué prueba |
|---|---:|---|
| `test_resilience.py` | 8 | Dependencias caídas, reintentos y bandeja de salida |
| `test_health_evidence.py` | 1 | Salud `live`/`ready` con dependencias reales |
| `test_continuity.py` | 4 | Continuidad operativa ante caídas |
| `test_malware_freshness_unit.py` | 9 | Firma antivirus vencida o ausente: falla cerrada |
| `test_dependency_timeout_unit.py` (nueva) | 11 | Tiempo agotado, conexión rechazada o cerrada y respuestas inválidas de una dependencia |
| `test_flows.py` | 9 | Flujos completos de extremo a extremo (regresión) |
| `test_documents_storage.py` | 2 (1 omitida) | Almacén local; la omitida requiere GCS real autorizado |

La prueba nueva cubre el hueco detectado en el plan: `redhouse/client.py` usa tiempo de conexión 1 s y de lectura 3 s, pero no había prueba del tiempo agotado. Levanta servidores HTTP reales que no responden, responden HTML, JSON sin envoltura o truncado, o cierran la conexión. En todos los casos la llamada termina en un 503 `dependency_unavailable` controlado. El tiempo agotado se corta entre 2.5 y 5 s, y un error legítimo de la dependencia (409) conserva su código.

## 2. Demostración en vivo con los comandos documentados

Instalación nueva y desechable (`install.sh` + `start.sh`). Los servicios se detuvieron y reiniciaron solo con `bash components.sh detener <servicio>` y `bash components.sh reiniciar <servicio>`. Script reproducible: [demo_servicio_caido.py](demo_servicio_caido.py). Bitácora con hora de cada paso: [demo.json](demo.json). No guarda contraseñas ni tokens.

**Escenario 1. Cae Alertas (dependencia asíncrona).**
- Con Alertas detenido, los otros 11 servicios siguieron con `/health/ready` 200.
- Donantes registró al donante, creó la campaña y agendó la cita (201 cada uno, de 16 a 28 ms).
- La bandeja de avisos no respondió (conexión rechazada), como era de esperar.
- Al reiniciar Alertas (1.4 s), el aviso `APPOINTMENT_BOOKED` de esa cita llegó a la bandeja del donante 3.4 s después: la bandeja de salida de Donantes lo retuvo y lo entregó sin pérdida.

**Escenario 2. Cae Identidad (dependencia síncrona).**
- Los otros 11 servicios siguieron en 200 y el inicio de sesión falló (conexión rechazada).
- Un token ya emitido siguió sirviendo en Donantes (200), porque la sesión se valida en Redis.
- Inventario registró una unidad sin ubicación (201), una operación que no consulta Identidad.
- La misma alta con ubicación sí consulta Identidad: respondió 503 `dependency_unavailable` en 9 ms, sin quedarse colgada.
- Tras reiniciar Identidad, la misma petición llegó a Identidad y respondió 404 `not_found`, porque la ubicación ficticia no existe.

Se usó `operator1` porque la instalación operativa exige MFA a ADMIN, MEDICAL y COORDINATOR (`mfa_enrollment_required`).

## 3. Defecto corregido en este bloque (clon limpio)

El [ensayo de clon limpio](../clon-limpio-20261118/RESULTADOS.md) encontró dos defectos que impedían arrancar una instalación nueva. Ambos se corrigieron y se volvió a instalar desde una copia limpia: `install.sh` y `start.sh` terminaron con código 0, 12/12 servicios con `/health/ready` 200, Documentos con `/health/storage` `up` (proveedor `local`, directorio 0700) y el portal en 200.
- **D1.** `scripts/manage.py` instala `requirements-storage.txt`, que incluye `requirements.txt`, en el entorno de servicios. El almacén local usa las excepciones de `google-api-core`.
- **D2.** `provision.py` escribe `STORAGE_LOCAL_ROOT` en la instalación nueva (sin fijar `STORAGE_PROVIDER`, para que `configure_gcs.py` siga activando GCS con solo `GCS_BUCKET`): `.local/runtime/private-files` en local y `/var/lib/redhouse-private` en Compose. El origen HTTPS de los enlaces temporales sigue siendo un paso explícito con `deployment/configure_local_storage.py`, porque el portal local usa HTTP y la regla HTTPS no se relajó.

La ruta Compose corregida no se volvió a ensayar completa: el stack completo no cabe en los 3.8 GB de Docker Desktop de esta Mac (D3, límite del equipo).

## Límites

- No se probó una caída de PostgreSQL, Redis o MongoDB en vivo; esos casos los cubren `test_resilience.py` y el [ensayo de recuperación](../recuperacion-20261118/RESULTADOS.md).
- La demostración fue local, no en la VM de GCP.
- Una falla preexistente no relacionada sigue abierta: `test_private_storage_local.py::test_gateway_rejects_unsafe_binary_requests` no encuentra el módulo `src` del portal al correrse desde la raíz. Falla igual sin los cambios de este bloque. También es preexistente `test_evidence_catalog.py::test_all_registered_routes_expose_real_http_contracts_and_controlled_errors`: espera que `/api/v1/public/institutions` rechace una petición sin credenciales, pero esa ruta es pública y responde 200.
- **Actualización:** las dos pruebas preexistentes se corrigieron después (INC-433 e INC-434): eran expectativas desactualizadas en las pruebas, no defectos del producto. `test_private_storage_local.py`, `test_evidence_catalog.py` y `test_final_delivery_documents.py` dan 17/17.
- Al revisar el catálogo se detectó que fijar `STORAGE_PROVIDER=local` en la instalación desactivaba GCS en los despliegues que lo activan con solo `GCS_BUCKET`. Por eso el instalador escribe solo `STORAGE_LOCAL_ROOT`. Con ese ajuste, `test_final_delivery_documents.py` pasa (JSON y XML) y una tercera instalación limpia volvió a dar 12/12 listos y Documentos `up`.
