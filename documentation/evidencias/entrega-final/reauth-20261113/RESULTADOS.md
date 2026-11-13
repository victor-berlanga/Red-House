# Resultados de SEC y rutas autónomas

Trabajo en `/private/tmp/redhouse-reauth-20261113`, sin despliegue. Se usaron PostgreSQL, Redis y MongoDB aislados; en almacenamiento se añadieron Nginx HTTPS y ClamD reales. Los nombres de cuentas y datos fueron sintéticos.

- `primera-junit.xml`: 7 aprobados, estado anterior a la recuperación web y al protocolo final.
- `sandbox-junit.xml`: 5 aprobados y 13 errores de preparación: el sandbox impidió abrir un socket local. Se repitió con autorización acotada.
- `final-junit.xml`: 18 aprobados, snapshot anterior a la ruta definitiva y al ajuste de perfil. Sus hashes `final-before.sha256` y `final-after.sha256` coinciden.
- `revision-junit.xml`: 37 aprobados y 2 fallos (ambos `rule_transition`, JSON/XML): `InsufficientPrivilege` al intentar bloquear mediante la vista un perfil inmutable. Los hashes `revision-before.sha256` y `revision-after.sha256` coinciden. Entre los aprobados: protocolo definitivo, siete familias protegidas previas y adicionales salvo la transición, portal con APIs detenidas, API de Documentos con listener web detenido, HTTPS Nginx, revocación, carga mayor de 256 KiB y ClamAV real con EICAR detectado.
- `rule-expectation-junit.xml`: dos fallos en la aserción del ensayo, que esperaba `RaiseException` pero PostgreSQL devolvió `CheckViolation: Historical records are append-only`. El bloqueo de fila del rol de servicio fue rechazado con `InsufficientPrivilege`, como se esperaba.
- `rule-final-junit.xml`: 2 aprobados, 6 no seleccionados en 39,74 s, tras corregir únicamente la excepción esperada. Comprobaron permisos efectivos, trigger inmutable, reto sin efecto, ámbito ajeno, prueba, efecto único y recuperación de resultado. `rule-final-before.sha256` y `rule-final-after.sha256` coinciden.

La corrección tras `revision-junit.xml` eliminó los bloqueos de fila sobre el perfil inmutable en `redhouse/reauth.py` y `ms_compatibilidad/rules.py`. La transición conserva el advisory lock por perfil, la secuencia única y el historial inmutable; no se concedieron privilegios adicionales. Los 37 aprobados y 2 dirigidos pertenecen a ejecuciones distintas y no deben presentarse como 39/39 de una sola ejecución.

La comprobación Redis y el commit SQL no son atómicos entre sí; una revocación concurrente posterior a la comprobación puede coincidir con una operación ya iniciada. Tampoco se probaron todos los puntos de interrupción de la saga ni alta disponibilidad multihost. Para instalaciones existentes se requiere aplicar `apps/services/scripts/reauth_operations_retention.sql` como propietario autorizado antes de activar el protocolo; el despliegue de Identidad, propietarios y clientes compatibles debe coordinarse. La integración con cambios concurrentes de Identidad requiere regenerar contratos y nueva validación del árbol integrado.

## Reproducción

Desde el worktree aislado, con las dependencias y herramientas del árbol principal disponibles (sin copiar configuración privada):

```sh
RH_BASE=/Users/victorberlanga/Programacion/integracion/Red-House
RH_PY="$RH_BASE/apps/services/.venv/bin/python"
export REDHOUSE_TEST_MONGOD="$RH_BASE/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_NGINX="$RH_BASE/.local/tools/nginx-1.30.6/sbin/nginx"
export REDHOUSE_TEST_CLAMD_PORT=13310
export REDHOUSE_TEST_STARTUP_TIMEOUT=120
```

El receptor ClamD debe estar activo en `127.0.0.1:13310` con firmas reales y configuración privada válida. Para reproducir este entorno, si no existe otro ClamD en ese puerto, iniciarlo en otra terminal y conservar su proceso hasta terminar las pruebas:

```sh
cd "$RH_BASE"
.local/tools/clamav-1.5.4/sbin/clamd --config-file=.local/runtime/clamav/clamd.conf
```

La configuración local define directorio de firmas y puerto; no incluirla ni copiar secretos en evidencias. Si ya existe un ClamD compatible, reutilizarlo sin detenerlo. Tras la prueba, detener solo el proceso iniciado para ella. El test con antivirus real comprueba EICAR además de analizar el archivo sintético; no acredita actualización de firmas ni pruebas sobre GCS real.

Desde el worktree, el comando exacto de la revisión de 39 casos fue:

```sh
"$RH_PY" -m pytest \
  apps/services/tests/test_reauthentication_single_use.py \
  apps/services/tests/test_reauthentication_families.py \
  apps/services/tests/test_web_reauthentication_challenge.py \
  apps/services/tests/test_final_identity.py \
  apps/services/tests/test_correction_policies.py \
  apps/services/tests/test_portal_storage_targets.py \
  apps/services/tests/test_local_storage_autonomous.py \
  apps/services/tests/test_local_storage_https.py \
  --junitxml=documentation/evidencias/entrega-final/reauth-20261113/revision-junit.xml -q
```

Duró 339,71 segundos: 37 aprobados y 2 fallidos. Incluye esperas de intervalos TOTP. Tras corregir el bloqueo y la expectativa de excepción, se ejecutó únicamente:

```sh
"$RH_PY" -m pytest apps/services/tests/test_reauthentication_families.py \
  -k rule_transition \
  --junitxml=documentation/evidencias/entrega-final/reauth-20261113/rule-final-junit.xml -q
```

Duró 39,74 segundos: 2 aprobados y 6 no seleccionados. Los puertos TCP locales requieren un entorno con permisos para abrir sockets; no se contactó producción. Las rutas JUnit de estos ejemplos sobrescriben evidencia existente: usar nombres nuevos al reproducir si se desea conservarla.
