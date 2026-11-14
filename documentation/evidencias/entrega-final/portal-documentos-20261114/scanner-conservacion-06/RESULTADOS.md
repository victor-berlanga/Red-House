# I06-03/04/05: conservación y recuperación del escáner — 14/11/2026

**Un caso integrado aprobado: 1/1 en 138,13 s; envoltorio 140,752 s.** Chrome real, monolito autónomo sin listeners API, PostgreSQL/MongoDB/Redis privados y almacén LOCAL. ClamD propio 1.5.4 con firmas 28182 del 13/11/2026 06:24:28 UTC; se mantuvo la vigencia máxima del producto de 172800 s. [JUnit](junit.xml), [navegador](browser.json), [persistencia READ ONLY](persistencia.json) y [cierre](runner.json).

El control previo real confirmó INFECTED para el PDF admitido y CLEAN para el PNG. El PDF usa exactamente el generador sintético EICAR del ensayo previo `test_malware_documents_pdf_real.py`: contenido comprimido de una página, sin malware real. Se validó estructura y MIME `application/pdf`; el PNG limpio usó `image/png`. No se alteraron MIME, antivirus ni estados para obtener aprobación.

| Alcance | Resultado observado |
|---|---|
| I06-04, formulario y descarga | PDF admitido recibió 422 al verificar; persistió REJECTED con análisis INFECTED. Detalle sin descarga y endpoint de descarga 409, sin redirección ni contenido. |
| I06-05, ClamD propio | Se detuvo únicamente el proceso del ensayo. PNG admitido recibió 503 y persistió ERROR, sin descarga. Tras reiniciar ClamD, el mismo UUID fue VERIFIED con secuencia de análisis ERROR→CLEAN; descarga con bytes/hash exactos. PDF infectado permaneció bloqueado. |
| I06-03, conservación | Sobre el PNG recuperado se guardó retención futura sintética, hold=true, referencia y razón confirmadas. Recarga y SQL comprobaron policy_version=2, instante UTC equivalente al formulario America/Monterrey, decisión y evento únicos con el mismo actor/razón. Formulario anterior recibió 412; formulario vigente con plazo menor recibió 409. SQL posterior idéntico. |

Dos preparaciones y una re-verificación; un DOCUMENT_PREPARED por documento. Generación/hash de cada análisis cotejados con archivo y contenido. La comparación de política incluye las decisiones y eventos SQL; no se presume propagación a Mongo por ese oráculo.

Dirección inspeccionó las cuatro capturas: [infectado rechazado](infectado-rechazado.png), [escáner detenido](scanner-no-disponible.png), [mismo documento recuperado](mismo-documento-recuperado.png) y [reducción bloqueada](conservacion-bloqueo.png). **Limitación visual registrada:** en los detalles REJECTED/ERROR, el campo «Análisis» muestra «Pendiente» aunque `file_scans` conserva INFECTED/ERROR. La consulta de presentación busca la generación vigente del archivo, que no queda fijada al fallar la verificación. No muestra VERIFIED ni habilita descarga; el ensayo funcional sigue aprobado. Después del ensayo se corrigió únicamente la presentación: «Sin análisis vigente; la descarga permanece bloqueada.» para ERROR/REJECTED sin generación vigente. No modifica estados, permisos ni análisis del backend. La [comprobación dirigida](presentacion.json) conserva sintaxis válida y cero hallazgos nuevos de Ruff (cuatro previos); no se repitió el recorrido ni se atribuye al texto nuevo una captura posterior.

## Integridad, intentos y límites

[1.308 fuentes](fuentes.json) idénticas antes/después: `apps/services`, `apps/web`, `packages`, `data/database/schema.sql` y el script Chrome. Cuarenta y cinco procesos propios observados terminaron, sin limpieza forzada ni supervivientes. [Huellas de artefactos](artefactos.sha256). No hubo cambios de producto durante la ejecución.

Se conservan los [tres intentos previos fallidos](intentos-previos.json), sus resultados y hashes de originales privados, sin sumarlos como éxitos:

- 03: sandbox impidió consultar procesos mediante psutil; ningún motor o Chrome iniciado.
- 04: PostgreSQL no arrancó por ruta de socket Unix demasiado larga; se usó después una raíz temporal corta. No llegó a ClamD/Chrome.
- 05: PNG estructuralmente admitido con muestra de control resultó CLEAN ante el motor real; el preflight abortó antes de Chrome. La muestra se sustituyó por el PDF ya validado, sin cambiar políticas del escáner.

El resultado acepta I06-04 local y la parte ClamD de I06-05. La conservación de aplicación de I06-03 se compone con las versiones 1/2 y bifurcación 412 del [ensayo previo](../RESULTADOS.md); no se repitieron esas operaciones. I06-03 integral conserva pendiente la política de objeto/bucket GCS; I06-05 integral conserva pendiente el corte/recuperación de GCS. No acredita caída de GCS, retención nativa del bucket, reportes masivos, otros tipos de documentos ni el cierre de toda la etapa 06.

HTTPS local con certificado efímero y `ignoreHTTPSErrors` del contexto Chrome; no prueba confianza CA del sistema ni publicación GCP. Fixture funcional con TESTING y cuotas de ensayo existentes; no es medición de capacidad ni MFA. No se cambiaron timeouts/cuotas del producto. Los tiempos incluyen preparación/cierre y no son latencias de operación o RTO. El período futuro usado es exclusivamente sintético, no una regla normativa. No hubo nuevas sesiones ni operaciones en producción.

## Reproducción acotada

Con ventana local asignada, Mongo/Chrome/binario ClamD disponibles y firmas vigentes, usar directorios nuevos de resultados y raíz temporal corta:

```sh
REDHOUSE_BROWSER_TESTS=1 REDHOUSE_TEST_SCANNER_FAILURES=1 \
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_CLAMD_DATABASE="$PWD/.local/clamav-vigencia-20261113/database" \
REDHOUSE_TEST_ROOT=/private/tmp/rh-pdoc-repeticion \
REDHOUSE_BROWSER_RESULTS="$PWD/.local/artifacts/portal-documentos-repeticion" \
PYTHONPATH=.:apps/services apps/services/.venv/bin/python -m pytest \
 apps/services/tests/test_portal_private_document_browser.py::test_infected_document_and_scanner_restart_in_browser \
 -q --tb=short --junitxml=.local/artifacts/portal-documentos-repeticion/junit.xml
```

La ejecución registrada usó el envoltorio privado existente para huellas antes/después, log privado, JUnit y censo/cierre de procesos. Los datos privados permanecen fuera de Git; el directorio público contiene únicamente recibos saneados y capturas sintéticas.
