# Vigencia antivirus — laboratorio aislado

ClamD 1.5.4, con zona horaria UTC y base real 28182 del 13 de noviembre de 2026 a las 06:24 UTC, detectó EICAR en un flujo Flate de un PDF que pasó el validador. La [sonda directa](pdf-probe-junit.xml) pasó **1/1**. La [repetición integrada](reintento-junit.xml) pasó **4/4 en 54,56 s**: el archivo limpio se recuperó después de un error de vigencia y se descargó; el PDF con EICAR se rechazó y no obtuvo descarga. CSV, PDF y XLSX conservaron metadatos por generación y hash; se comprobaron permisos con la credencial real `rh_documentos`: INSERT sí, UPDATE y DELETE no en la vista de análisis. Las exportaciones emplearon un receptor doble, no ClamD real. La recuperación con error se provocó ajustando el umbral de prueba a una hora; el análisis exitoso usó el valor predeterminado de 48 horas.

La [pasada inicial](actual-junit.xml) conservada registró **14 aprobados y 4 fallidos en 70,06 s**. Incluyó PostgreSQL, MongoDB y Redis aislados, contratos de traslado JSON/XML, migración de datos históricos 019→020 y comprobaciones con doble. Tres fallos de privilegios consultaron erróneamente el superusuario del fixture; se corrigieron y repitieron con el rol real. Su fuente original está en [attempt1-test_malware_reports_integration.py](attempt1-test_malware_reports_integration.py). El cuarto fallo es una limitación observada: ClamD 1.5.4/28182 informó CLEAN para un PNG estructuralmente válido con EICAR añadido después de IEND; se verificó y quedó descargable. La [fuente de esa reproducción](attempt1-test_malware_documents_real.py) se conserva fuera de la colección automática. EICAR directo y el flujo PDF sí se detectaron; ninguno de esos casos demuestra detección universal de malware.

El [ensayo separado de firmas antiguas](antigua-junit.xml) pasó **1/1**: ClamD con base 28178 del 9 de noviembre de 2026 se consultó realmente, se confirmó una antigüedad superior a 48 horas y el adaptador rechazó el análisis con el límite predeterminado. El [ensayo estructural PDF](pdf-estructura-junit.xml) pasó **2/2** sin daemon: los adjuntos se rechazan y el PDF de flujo Flate pasa ese control.

Las [pruebas de configuración y estructura](configuracion-junit.xml) pasaron **4/4** sin Docker: zona UTC del contenedor generado, límite configurable conservado, configuración compartida con el kernel web y ausencia de suposición de zona en una configuración local sin declarar. No prueban el despliegue existente.

La [compatibilidad de lectura](legacy-junit.xml) pasó **2/2 JSON/XML en 66,50 s**: un proceso Documentos separado, cargado desde código histórico `9648bf4c0cb857498566e2f3a68c253887deb13f`, consultó salud de base y leyó un documento con análisis nuevo en esquema 020; se validaron contratos históricos. PostgreSQL, Redis y MongoDB eran aislados y el scanner fue un doble. El archivo de `git archive` de `apps/services/redhouse` y `apps/services/ms_documentos` para esa revisión tuvo SHA-256 `966b327d0f83e4feed2bb6819759eae7e87c518dc60a8198a5c9ab02f6bb0904`. No se construyó imagen Docker ni se probó escritura desde código anterior. Los [34 hashes anteriores](antes-legacy.sha256) y [posteriores](despues-legacy.sha256) coinciden.

Después de esa pasada se ajustó únicamente una línea en blanco de `configure_scanner.py` para Ruff. La [copia histórica](legacy-configure_scanner.py) coincide con el hash del manifiesto; se comprobó que su AST y el de la versión formateada son idénticos. La prueba de proceso anterior no invocó ese generador.

Los manifiestos de la pasada inicial [`antes.sha256`](antes.sha256) y [`despues.sha256`](despues.sha256) coinciden en 26 fuentes; los del [reintento anterior](antes-reintento.sha256) y [posterior](despues-reintento.sha256) coinciden en 29. Registran rutas históricas; la prueba PNG fallida se trasladó después, sin modificar bytes, a la copia enlazada arriba. Los resultados son de un laboratorio de un solo equipo, con datos sintéticos y almacenamiento local. No ejercitan GCS real, TLS, despliegue ni disponibilidad continua.

Para reproducir, usar el worktree revisado y crear directorios temporales propios de nombres cortos; iniciar ClamD con `TZ=UTC` y `REDHOUSE_TEST_CLAMD_PORT` en loopback. Es necesaria una base de firmas cuya fecha sea menor a 48 horas para los casos positivos; la prueba de un umbral de una hora requiere que esa misma base tenga más de una hora. La verificación de firmas antiguas requiere otra base con más de 48 horas y un daemon separado. Con el daemon reciente ya activo:

```sh
RH_BASE=/Users/victorberlanga/Programacion/integracion/Red-House
RH_LAB="$(mktemp -d /tmp/rhav.XXXXXX)"
mkdir -p "$RH_LAB/p"
export REDHOUSE_TEST_ROOT="$RH_LAB/p"
export REDHOUSE_TEST_MONGOD="$RH_BASE/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_STARTUP_TIMEOUT=120
export REDHOUSE_TEST_CLAMD_PORT=13311
"$RH_BASE/apps/services/.venv/bin/python" -m pytest \
  apps/services/tests/test_malware_pdf_probe_real.py \
  apps/services/tests/test_malware_documents_pdf_real.py \
  apps/services/tests/test_malware_reports_integration.py::test_export_scan_metadata_and_append_only_role \
  --basetemp="$RH_LAB/t" --junitxml=/ruta/privada/nueva/reintento.xml -q --tb=short
```

El caso antiguo se reproduce con `REDHOUSE_TEST_EXPECT_STALE=1`, `REDHOUSE_TEST_CLAMD_PORT` apuntando al daemon con base antigua y `pytest apps/services/tests/test_malware_clamd_real.py::test_real_clamd_stale_signatures_rejected_at_operational_default`. El proceso de actualización de firmas, sus hashes y condiciones operativas están en [CLAMD_VIGENCIA.md](../../../entrega-final/continuidad/CLAMD_VIGENCIA.md). No se ha ensayado todavía una recarga real durante un análisis ni transición de históricos GCS; no desplegar el incremento como si esos límites estuvieran resueltos.

Con las mismas variables de fixture y sin ClamD externo, `pytest apps/services/tests/test_malware_legacy_schema20.py --basetemp="$RH_LAB/t" --junitxml=/ruta/privada/nueva/legacy.xml -q --tb=short` reproduce el ensayo de código anterior; requiere que el objeto Git `9648bf4` esté disponible y emplea el receptor doble.
