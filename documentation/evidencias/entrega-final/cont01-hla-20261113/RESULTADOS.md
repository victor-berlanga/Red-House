# CONT-01: continuidad académica HLA — 13 de noviembre de 2026

Resultado: **2 casos aprobados en 78,50 segundos**, uno JSON y otro XML, con PostgreSQL, Redis y MongoDB reales en un fixture aislado, datos sintéticos y servicios HTTP del laboratorio. La prueba valida contratos publicados para respuestas y errores. El código base era el commit `78fcd06a4706ceea592c127e502edc085ab3ed19`, con el ensayo adicional identificado en los manifiestos de SHA. Los archivos incluidos en `intento1-before.sha256` e `intento1-after.sha256` coincidieron; el documento editorial CONT01_HLA.md se actualizó después para registrar el resultado.

El recorrido usó un receptor y órgano sintéticos. Verificó HLA incompleto, evaluación sin dictamen y rechazo de revisión, registro sin autorización, autorización humana, invalidación de evaluación anterior con motivo `RECIPIENT_LABORATORY_CHANGED`, evaluación nueva, dictamen humano académico, corrección versionada que conserva el dictamen histórico pero vuelve obsoleta la evaluación, rechazo de nueva revisión sobre ella y nueva evaluación tras autorizar la corrección. Se comprobaron `ORGAN-1.0`, versión de perfil, huellas distintas, explicación, alcance académico, ausencia de dictamen automático y rechazo de evaluación clínica sin perfil autorizado. El resultado no muestra una interpretación de HLA ni aprueba una asignación clínica.

La prueba no adjunta PDF/PNG a los resultados ni ejecuta Documentos o ClamAV; ese vínculo HLA documental y su versión siguen pendientes. Tampoco prueba GCS, precisión clínica, políticas oficiales ni aprobación institucional. El fixture ejecutó el flujo en modo académico de pruebas y no demuestra autenticación reforzada real en cada acción ni operación productiva. La revisión de fuentes y validación por especialistas siguen siendo necesarias antes de habilitar cualquier uso clínico. No se cierra la aceptación integral de CONT-01 con este ensayo.

## Reproducción

Desde el worktree y en un entorno que permita sockets TCP locales, crear un directorio temporal privado exclusivo para el fixture. Mantener el JUnit fuera de ese directorio y conservar la evidencia existente usando un nombre nuevo:

```sh
RH_BASE=/Users/victorberlanga/Programacion/integracion/Red-House
RH_LAB="$(mktemp -d /private/tmp/redhouse-cont01-20261113.XXXXXXXX)"
mkdir -p "$RH_LAB/platform"
REDHOUSE_TEST_ROOT="$RH_LAB/platform" \
REDHOUSE_TEST_MONGOD="$RH_BASE/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_STARTUP_TIMEOUT=120 \
"$RH_BASE/apps/services/.venv/bin/python" -m pytest \
  apps/services/tests/test_cont01_hla_evaluation.py \
  --basetemp="$RH_LAB/pytest" \
  --junitxml=/ruta/privada/nueva/cont01-hla.xml -q --tb=short
```

Se comprobaron procesos terminados y se eliminó únicamente el directorio temporal propio. No se accedió a GCP. La ejecución adicional unitaria `test_missing_hla_ambiguity_and_states` pasó antes del laboratorio; no se agrega al total de 2 casos integrados.
