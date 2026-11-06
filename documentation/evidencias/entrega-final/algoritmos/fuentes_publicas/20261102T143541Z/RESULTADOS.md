# Fuentes públicas: resultados del 02/11/2026

Incremento local **0.4.4 / esquema 16**, base Git `8909baf8458dff797d40d15541c57c66c14ef964`, con cambios preexistentes sin commit conservados. `baseline.json` identifica el estado inicial; `sources-final.json`, 1.117 archivos de código, contratos, pruebas y configuración finales. `changed-runtime.json` separa cambios/novedades del incremento. `conservation.json` comprueba 1.993 archivos históricos sin cambios ni ausencias. No se modificaron instalaciones habituales, producción, cuentas reales ni hardware GPS.

## Resultado y alcance

**110 casos únicos aprobados**, consolidados por classname/nombre: 109 de regresión y un caso de navegador con 23 comprobaciones internas. `consolidation.json` indica qué JUnit acredita cada identidad. Reintentos y las 22 pruebas seleccionadas del auditor no aumentan ese total. No se presenta una ejecución fallida como pasada: la primera ejecución final de 109 tuvo un fallo Redis 503 y se conserva íntegra.

Pruebas sobre PostgreSQL, Redis y MongoDB reales temporales con datos ficticios, permisos runtime y puertos aislados en macOS. Chrome real, HTTPS local, MFA/reautenticación, controles de laboratorio/órganos activados. La prueba de navegador detuvo exclusivamente los listeners API de su fixture; la web siguió usando sus módulos de dominio y almacenes temporales. Android/escritorio no se ejecutaron; se verificaron sus contratos JSON/XML/XSD en el backend.

| Archivo | Resultado / significado |
|---|---|
| `public-sources-first.xml` | 13 aprobados antes de incorporar el caso encontrado por auditor; no acredita cierre F1 |
| `audit-F1-before.xml` | Dos fallos esperados JSON/XML: `CUSTOM_HLA` podía eludir catálogo obligatorio; completitud incorrecta, sin aprobación clínica |
| `public-sources-after-audit.xml` | 15 aprobados, incluidos HLA/CUSTOM_HLA × JSON/XML; 130,356 s |
| `regression-first.xml` | 107 aprobados en 702 s, ejecución anterior a corrección final; referencia de diagnóstico |
| `browser-first.xml`, `browser-attempt1/` | Fallo tras cuatro comprobaciones: detalle no mostraba `catalogue_check` persistido; captura y reporte conservados |
| `browser-final.xml`, `browser/` | Un caso aprobado en 263,064 s; 23 comprobaciones. Cero errores de consola; HTTP 409 esperado por reserva obsoleta |
| `regression-final.xml` | 108 aprobados, un fallo en 614,577 s; API rechazó con `redis_unavailable` 503 al consultar evaluación de plaquetas |
| `regression-retry.xml` | El caso afectado pasó en 91,609 s, nuevo fixture aislado, sin cambiar código. No se demostró causa raíz del incidente puntual Redis |
| `independent-public-final.xml` | 22 casos aprobados por otro agente en 3,54 s; oráculos/helpers seleccionados, no suite integral nueva |
| `independent-public-references.xml`, `independent-road-integrity.xml`, `independent-public-oracles.xml` | Primeros intentos del auditor, conservados como historia; no sumados |

Correcciones F1/F2: exigir pertenencia sobre toda tipificación, independientemente del código de prueba; los loci no reconocidos no satisfacen el perfil. Disponibilidad vial requiere ventana temporal e integridad de archivos. Presentación: el detalle muestra la comprobación HLA con su límite clínico. No se rebajaron expectativas para conseguir aprobación.

## Fuentes y adquisición real

- `hla-download.json`: edición 3.66.0, commit/URL/hash/bytes del archivo público original. SHA-256 `1913c5f748e6d649017996686e135dc6ffedc53215d4da7efad8f9165f3d2f35`, 970.839 bytes. Descarga original local y reproducción en directorio temporal; catálogo íntegro no incluido en este expediente ni redistribuido modificado.
- Primer intento del importador con urllib falló por verificación de certificado local. Se cambió a Requests con CA bundle/TLS verificado y soporte `REQUESTS_CA_BUNDLE`; la adquisición posterior obtuvo los bytes exactos. No se desactivó TLS.
- `road-download.json` identifica la fuente instalada `NL-OSRM-20261102`, descargada el 02/11. Los tres cuerpos JSON originales y hashes están en `apps/services/redhouse/reference_data/roads/` y el manifiesto final los identifica.
- `road-refresh/` conserva una segunda adquisición real mediante el CLI, ID `NL-OSRM-20261102T161707Z`, con los tres cuerpos originales. No reemplazó la fuente instalada. Tiene atribución © OpenStreetMap contributors, ODbL y enlace a condiciones de demo OSRM; uso razonable no comercial, sin SLA.
- Las cinco referencias normativas/documentales constan en `public_rules_v1.json` y en [registro de fuentes](../../../../../markdowns/Reglas_y_fuentes_clinicas.md). Se consultaron fuentes primarias y vigencias; ninguna cita se convirtió en regla clínica aprobada.

Los puntos son referencias urbanas públicas, no hospitales, personas ni posiciones GPS. El proveedor no informó edad del mapa. La fecha de descarga y la caducidad técnica del paquete no son evidencia de actualización vial ni tráfico. El escenario y la ETA siguen siendo académicos/modelados.

## Comandos reproducibles

Desde raíz del repositorio, dependencias instaladas y HLA adquirido:

```sh
apps/services/.venv/bin/python apps/services/scripts/fetch_public_references.py hla --version 3.66.0 --directory .local/reference-data/hla
apps/services/.venv/bin/python apps/services/scripts/fetch_public_references.py roads --output /ruta/nueva/instantanea-vial
apps/services/.venv/bin/python apps/services/scripts/document.py --contracts-only
apps/services/.venv/bin/python -m pytest apps/services/tests/test_public_reference_sources.py apps/services/tests/test_stage02_corrections.py apps/services/tests/test_stage02_oracles.py apps/services/tests/test_stage02_migration.py apps/services/tests/test_final_algorithms_hla.py apps/services/tests/test_final_quality.py apps/services/tests/test_security_contracts.py -q --junitxml=/ruta/nueva/regression.xml
apps/services/.venv/bin/python -m pytest 'apps/services/tests/test_stage02_corrections.py::test_profile_execution_manual_products_and_all_candidate_branches[json-PLATELETS]' -q --junitxml=/ruta/nueva/retry.xml
REDHOUSE_STAGE02_EVIDENCE=/ruta/nueva/browser-evidence apps/services/.venv/bin/python -m pytest apps/services/tests/test_stage02_browser.py -q --junitxml=/ruta/nueva/browser.xml
```

Para el navegador se requiere Chrome y Playwright, con `REDHOUSE_PLAYWRIGHT` si no se usa la ruta local predeterminada. No ejecutar contra instalaciones habituales. Los tests levantan sus propios almacenes; requieren permisos de sockets. Las fuentes tienen vigencia finita: renovar por nueva versión cuando corresponda, conservando originales y expectativas anteriores.

Ruff: `ruff check --select E9,F63,F7,F82 apps/services apps/web/src/integration` aprobado. Formato aprobado en nueve archivos nuevos/modificados del incremento. Contratos se regeneraron; CI incorpora adquisición de HLA, sin atribuirle ejecución remota. `http-latencies.json` corresponde a capturas del fixture, no Locust ni capacidad productiva; benchmarks anteriores no se republican como mediciones nuevas.

## Revisión independiente y pendientes

El usuario autorizó explícitamente otro agente auditor. Revisó fuentes sin modificarlas, informó F1/F2, repitió sus reproducciones y ejecutó 22 pruebas. Su comprobación del implementador distingue JUnit persistido de ejecución propia. [Informe independiente](AUDITORIA_INDEPENDIENTE.md).

El incremento entrega fuentes públicas trazables, validación HLA por edición y fuente vial real limitada. Continúan externas las aprobaciones/protocolos clínicos, elección institucional de políticas y cobertura/actualidad vial requerida para operación real. El GPS físico se aplazó expresamente. No se repitieron GCS real, CI remoto ni GCP para 0.4.4; no se atribuye despliegue actual a la evidencia 0.4.1.

El cierre integral de etapa conserva **CONTINUACIÓN PARCIAL POR DEPENDENCIA DECLARADA**. Se puede continuar con tareas académicas y de integración; no se declara habilitación clínica, publicación ni aceptación de hardware. [Matriz por requisito y acciones](../../../../../entrega-final/algoritmos/correccion/Matriz_fuentes_publicas.md).


## Archivo de detalles — 04/11/2026

Los manifiestos extensos, capturas de estado Git y muestras HTTP de este expediente se conservan sin alterar sus bytes en [el archivo comprimido](../../../../archivo/detalles-20261104.tar.gz); el [índice](../../../../archivo/detalles-20261104.json) identifica cada ruta original, tamaño y SHA-256. Los resultados, JUnit e incidencias siguen visibles. Antes de ejecutar verificadores históricos que lean esos detalles, restaurar las rutas desde la raíz del repositorio con `tar -xzf documentation/evidencias/archivo/detalles-20261104.tar.gz`. Extraer en una carpeta temporal para una consulta sin escrituras en el repositorio. Los hashes históricos corresponden al corte original, no al árbol actual.
