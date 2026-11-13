# CONT-01: vínculo documental HLA — 13 de noviembre de 2026

Resultado: **2 casos aprobados en 67,67 s**, JSON y XML, en laboratorio aislado con PostgreSQL, Redis, MongoDB y ClamD real. El daemon informó `ClamAV 1.5.4/28178/Mon Nov 9 00:24:16 2026`; la detección directa de EICAR se comprobó en ambos casos. Las firmas observadas no acreditan una política de vigencia ni se guardaron por análisis. El PNG sintético fue analizado CLEAN, almacenado localmente y asociado a un resultado HLA; no se usó GCS real.

La reproducción inicial mostró que un documento CLEAN asociado a un resultado ABO podía utilizarse para crear un resultado HLA corregido de la misma muestra: ambos formatos devolvieron 201 cuando se esperaba 409. La corrección exige que el resultado al que pertenece el documento tenga, además de la muestra ya comprobada, el mismo `test_code` que el resultado nuevo. El error 409 `evidence_mismatch` no devuelve los identificadores usados en el caso. No se reescribieron registros históricos ni se introdujo una interpretación clínica.

La repetición final comprobó también documento HLA versión 2, metadatos `supersedes`, hash y generación en `document_snapshot`, rechazo de otro tenant, revisión humana, completitud académica y ausencia de aprobación clínica. Un documento previo de la misma muestra y prueba se aceptó para una versión posterior; esa reutilización conserva el comportamiento existente y no certifica suficiencia clínica. La versión posterior permaneció pendiente de autorización. El intercambio de binarios usó `test_client` dentro del proceso, no TLS ni navegador.

## Pasadas y límites

- `negativa-junit.xml`: 2 fallos esperados que reproducen la aceptación indebida HTTP 201, con JSON/XML y ClamD real. `antes-negativa.sha256` y `despues-negativa.sha256` coinciden.
- `intermedia-junit.xml`: 2 fallos posteriores al control de prueba; el vínculo correcto se registró, pero la aserción de completitud fue falsa. La implementación exige documento para todos los resultados presentes y el resultado ABO auxiliar estaba pendiente sin snapshot. Esa posible causa se dedujo estáticamente; el fallo no conservó el campo `missing`. Para la pasada final se documentó y autorizó también el ABO auxiliar, sin alterar la lógica de completitud. `antes-intermedia.sha256` y `despues-intermedia.sha256` coinciden.
- `final-junit.xml`: 2 aprobados después de documentar el resultado auxiliar y añadir cobertura de reutilización de evidencia de la misma prueba. `antes-final.sha256` y `despues-final.sha256` coinciden. Las pasadas se conservan separadas y no se suman como una suite única.

La revisión humana y los estados de completitud son controles informáticos. No establecen compatibilidad HLA, asignación clínica, adecuación del contenido del documento ni aprobación sanitaria. No se verificaron firma antigua, indisponibilidad del motor, EICAR incrustado en formato admitido, navegador, GCS real ni todos los permisos o carreras distribuidas. La suficiencia y vigencia del documento y la política de reutilización por versión requieren decisión profesional e institucional; no se impuso igualdad automática con `supersedes`.

La [regresión existente](../cont01-regresion-20261113/RESULTADOS.md) `test_result_private_document_binding_generation_analysis_and_scope` pasó después en JSON/XML; usa dobles de GCS/ClamD y cubre un documento válido y otra muestra. Su evidencia se conserva por separado de los dos casos nuevos.

## Reproducción

Iniciar un ClamD de laboratorio con firmas reales y esperar PONG. No detener un daemon compartido ni copiar sus credenciales. Desde el worktree, crear un directorio temporal privado nuevo para la infraestructura y pytest; guardar el JUnit fuera de él:

```sh
RH_BASE=/Users/victorberlanga/Programacion/integracion/Red-House
RH_LAB="$(mktemp -d /private/tmp/redhouse-hla-doc-20261113.XXXXXXXX)"
mkdir -p "$RH_LAB/platform"
REDHOUSE_TEST_ROOT="$RH_LAB/platform" \
REDHOUSE_TEST_MONGOD="$RH_BASE/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_CLAMD_PORT=13310 REDHOUSE_TEST_STARTUP_TIMEOUT=120 \
"$RH_BASE/apps/services/.venv/bin/python" -m pytest \
  apps/services/tests/test_cont01_hla_documents.py \
  --basetemp="$RH_LAB/pytest" \
  --junitxml=/ruta/privada/nueva/hla-documental.xml -q --tb=short
```

El binario de la ejecución fue `.local/tools/clamav-1.5.4/sbin/clamd` y su configuración privada local `.local/runtime/clamav/clamd.conf`, vinculada a 127.0.0.1:13310. El fixture exige `REDHOUSE_TEST_CLAMD_PORT`: si falta, marca los casos omitidos y no acredita ClamAV. Tras confirmar el cierre de sus procesos se eliminaron únicamente los directorios temporales propios; no se accedió a GCP.
