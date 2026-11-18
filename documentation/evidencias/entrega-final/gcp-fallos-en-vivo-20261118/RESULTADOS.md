# Fallos de la consigna ensayados en la VM de GCP — 18/11/2026

**Los 12 casos y `estado` pasaron en la VM real** (`https://34.18.186.116`), con un solo comando por caso: [`deployment/gcp/fallo.py`](../../../../deployment/gcp/fallo.py) (SHA-256 `079dddb1…7d80e43`, igual en el repo y en `/opt/redhouse/deployment/gcp/fallo.py`). Cada caso que detiene algo se restableció de inmediato; al final había 30/30 contenedores sanos y los 12 `/health/ready` en 200. Salida completa, sin credenciales: [salida_vm.txt](salida_vm.txt).

Uso: `sudo python3 /opt/redhouse/deployment/gcp/fallo.py <caso> [restablecer]`. Guion: [Guion_fallos_en_vivo.md](../../../entrega-final/continuidad/Guion_fallos_en_vivo.md#atajo-en-la-vm-un-comando-por-caso).

| Caso | Qué se vio en la VM | Recuperación |
|---|---|---|
| `token` | Sesión A: 200 → revocada → 401 al reusar y 401 al renovar; sesión B del mismo usuario sigue en 200 | No aplica |
| `invalida` | JSON mal formado 400 `invalid_body`; tipos inválidos 422 `validation`; id inválido 400; siempre con sobre de error | No aplica |
| `inexistente` | Descarga y metadatos de un archivo inexistente: 404 `not_found` | No aplica |
| `permisos` | operator2 sobre donante del Hospital 1: 403; donor1 registrando inventario: 403; sin token: 401 | No aplica |
| `logs` | 403 provocado; la línea del log con su `correlation_id` aparece en la réplica que atendió (a o b), con ruta, estado, código y tiempo | No aplica |
| `sobrecarga` | 240 peticiones simultáneas de operator1: 175 × 200 y 65 × 429 `rate_limit` con `Retry-After: 60`; operator2 en 200 durante la ráfaga | Termina sola |
| `tiempo` | Identidad congelada (`pause`): Inventario responde 503 `dependency_unavailable` en **3.05 s**; al reanudar, la misma alta da 404 (ubicación ficticia) y no se creó nada | Docker marcó Identidad como no sana ~30 s y volvió solo a 30/30 |
| `microservicio` | Inventario a/b detenidos: su API 502; Donantes, Identidad y portal 200; Monitoreo registró `down` | Sanos en 26 s; Monitoreo `up` |
| `archivos` | Documentos a/b detenidos: 502; Inventario y portal 200 | Sanos en 22 s; almacenamiento `up`, proveedor `gcs` |
| `redis` | `ready` 503 con `redis` caído, `live` 200; consulta autenticada e inicio de sesión: 503 `redis_unavailable` en 0.04 s | Sano en 6 s; **el mismo token volvió a servir** |
| `mongodb` | Auditoría `ready` 503 con `mongodb` caído; el inicio de sesión (auditado) siguió en 200 y la bandeja de salida subió de 0 a 2 pendientes | Sano en 6 s; pendientes en 0 (entregados) |
| `postgres` | `ready` 503 con `database` y `worker` caídos; inicio de sesión 503 `database_unavailable` | Sano en 6 s. En la primera corrida los servicios tardaron unos segundos en reconectar; el restablecimiento ahora espera a `ready` 200 y en la segunda corrida estuvo listo de inmediato |

## Ajustes hechos al ensayar

- Desde la VM, Nginx cierra las conexiones a `127.0.0.1`; el script usa el origen de `public.json`.
- `postgres restablecer` espera hasta que `/health/ready` vuelva a 200 y dice cuánto tardó.
- `logs` imprime el comando `grep` de la réplica donde encontró la línea.

## Límites

- Las cuentas usadas son sintéticas y sin MFA (operator1, operator2, donor1, transport1). Cada inicio de sesión del script queda en Auditoría.
- Mientras Redis, MongoDB o PostgreSQL estuvieron caídos, toda la plataforma sintió el efecto unos segundos. En la presentación hay que avisar y restablecer en menos de un minuto.
- «Respuesta inválida» se demuestra con peticiones inválidas del cliente. Las respuestas inválidas entre servicios se cubren con `apps/services/tests/test_dependency_timeout_unit.py` (11/11).
