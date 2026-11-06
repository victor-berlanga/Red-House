# Corrección de etapa 02 — expediente de ejecución

Alcance local, datos ficticios y almacenes temporales reales. Código 0.4.3, esquema 15. No despliegue. La aceptación clínica está separada y permanece sin aprobación profesional externa. [Matriz de 21 criterios](../../../../../entrega-final/algoritmos/correccion/Matriz_cierre.md) · [Guía de reproducción](../../../../../entrega-final/algoritmos/correccion/Operacion_y_reproduccion.md).

## Identidad y conservación

Commit de base `8909baf8458dff797d40d15541c57c66c14ef964`; árbol con cambios locales anteriores, conservados. `baseline.json` registra 1.456 archivos iniciales, no presupone equivalencia con la auditoría anterior de 3.278 archivos. `git-status-before.txt` identifica el árbol inicial. No se localizó un informe archivado específico de auditoría 02; el encargo conserva los hallazgos obligatorios.

Los dos JUnit históricos N1/N2 estaban disponibles y se copiaron a `historical-audit/`; sus 15/8 pruebas y los 68 casos antiguos no son nuevas ejecuciones. La comprobación de conservación registra cero archivos iniciales ausentes y ninguna alteración de evidencia previa. Los nuevos intentos permanecen aquí, sin sobrescribir los expedientes anteriores.

`commands-final.json` conserva las cuatro invocaciones seleccionadas y sus requisitos de entorno sin credenciales. `sources-final.json` cubre fuentes ejecutables, contratos, pruebas, assets y dependencias; `environment.json` identifica entorno. La comprobación final contrasta esos SHA-256. Las ediciones documentales posteriores se conservan en manifiesto separado.

## Reproducciones e intentos

| Artefacto | Resultado y alcance |
|---|---|
| `before.xml` | Primer intento: entorno restringió sockets; el validador de A*01 mostró el defecto. No acredita integración HTTP. |
| `before-real.xml` | Tres reproducciones reales fallaron como se esperaba antes de corregir: A*01 como alelo, perfil de riñón sobre receptor de hígado y uso de perfil futuro. |
| `first-fixes.xml` | Los tres casos pasaron después de la corrección inicial. No equivalen a toda la etapa. |
| `integration-first.xml` | 50 aprobados / 3 fallos intermedios: dos expectativas de normalización HLA y fixture de migración no actualizado. Se conservaron y corrigieron las expectativas para la salida ampliada y el esquema vigente. |
| `correction-flows.xml` | 16 aprobados / 2 fallos: intento de bloquear perfil inmutable con privilegio UPDATE. Sustituido por bloqueo advisory sin ampliar privilegios. |
| `correction-expanded.xml` | 26 aprobados intermedios; todavía no era el conjunto final. |
| `registry-migration.xml` | 3 aprobados: migración, aprobación técnica ficticia segregada y prueba cruzada. |
| `browser.xml`, `browser-attempt1/` | Reautenticación vinculada al UUID incorrecto; corregido con identificador de ruta antes que recurso del cuerpo. |
| `browser-migration-second.xml`, `browser-attempt2/` | Restauración/migración aprobada; navegador falló en presentación de secciones. Los enlaces creados no acreditaban visualización: hubo 500, ahora corregidos mediante detalle explícito. |
| `browser-third.xml`, `browser-attempt3/` | Faltó seleccionar una opción del formulario en la prueba; datos horarios adaptados a Monterrey. |
| `owner-oracles-first.xml` | 9 aprobados / 1 fallo del fixture: cantidad pertenecía a otra institución. Se verificó la cantidad desde el propietario/institución correcto. |
| `browser-owner-fourth.xml`, `browser-attempt4/` | Navegador aprobó 16 comprobaciones; caso posterior de anomalías falló por token del fixture revocado tras enrolamiento MFA. Navegador se ejecuta en proceso separado. |
| `final-core.xml` | 52 aprobados / 1 fallo / 1 error: importaciones públicas web retiradas por limpieza automática y fixture WSS sin importar. Se restauraron explícitamente; no fue fallo clínico. |
| `browser-final.xml` | Mismo fallo de importación, antes de abrir navegador. |
| `final-core-v2.xml` | 55 aprobados intermedios. Después se ampliaron comprobación visible de completitud, DTO de resultados y cobertura XML/antigüedad. |
| `browser-final-v2.xml`, `browser-attempt6/` | 19 comprobaciones aprobadas; incluye rol, institución y resolución por Auditoría. |
| `gcs-access*.json`, `gcs-object-access.json` | Restricción de red inicial; fuera del entorno aislado, metadatos del bucket denegados pero acceso a objetos permitido. No se confundieron permisos. |
| `gcs-first.xml`, `gcs-result.json` | Objeto RESULT real: carga firmada, generación/SHA-256, verificación, descarga firmada, 403 ajeno y anónimo; solo el objeto ficticio nuevo se elimina al terminar. |

Para los demás defectos se conserva diagnóstico estático y pruebas posteriores del flujo; no se afirma disponer de una reproducción HTTP anterior para cada fila. Una prueba nueva no se hace pasar por evidencia de la implementación antigua.

## Ejecuciones finales

**117 casos distintos aprobados, cero fallos/errores y cero omitidos** en la selección final. [Consolidación por identidad](consolidation.json), sin sumar repeticiones ni N1/N2/68 históricos. No se presenta como una corrida única.

| Ejecución | Casos aprobados |
|---|---|
| `final-core-v3.xml` | 58 |
| `final-stage01-regression.xml` | 57 |
| `browser-final-v3.xml` | 1 |
| `gcs-final.xml` | 1 |

Chrome: **20 comprobaciones**, MFA/reauth y controles de laboratorio/órganos expresamente activos, todos los listeners API del fixture detenidos; sin errores de consola. El único error de red de la página principal fue el 409 esperado de reserva obsoleta; otros contextos comprueban 403 por rol/institución. La captura `browser/final.png` se revisó visualmente: seis ejecuciones persistidas y tabla legible. Es automatización, no estudio con participantes.

Aplicabilidad: `sources-final.json` coincide con 1.050 archivos. Core-v3 y GCS arrancaron después de ese corte. Navegador-v3/regresión etapa01 precedieron al último ajuste del reloj `age_checked_at` en la lectura geográfica de Transporte; sus recorridos no ejecutan esa rama con `shipment_id`. Core-v3 verifica el ingreso WSS, persistencia y antigüedad con el código final. Los cambios restantes de formularios/completitud ya estaban presentes al arrancar Chrome. El benchmark precede a cambios de presentación/DTO; los núcleos medidos no cambiaron.

`static-checks.json`: Ruff aprobado en el conjunto correctivo indicado y `git diff --check` sin errores. El barrido adicional completo de Priorización conserva seis avisos de estilo/importación en `__init__.py`, `run.py` y `routes.py` (I001/F401/C408); no se presenta como Ruff global aprobado. No son fallos de flujo y quedan como limpieza opcional separada.

## Métricas y límites

[Tabla de mediciones](METRICAS.md) y `benchmark-final.json`: 31 combinaciones, cinco repeticiones cada una, tamaños pequeños/medios/grandes, grafos dispersos/densos y límite de 100.000 aristas HK. Incluye reproducción de ALG-01, detector desde instantánea y ventanas autoritativas además de núcleos académicos. `tracemalloc` mide asignaciones Python; máximo RSS es del proceso y usa unidades de la plataforma. El host tenía carga compartida; no se deduce capacidad productiva.

`http-latencies.json`: solicitudes de integración JSON, éxito y rechazos esperados; endpoint normalizado, n, media, mediana, p95 y p99. No suma XML no instrumentado, no mide estrés sostenido ni presenta muestras escasas como SLA. Núcleos y extracción SQL/HTTP son magnitudes distintas.

GCS es real para el archivo ficticio; el receptor de protocolo ClamD es controlado, no certifica análisis antimalware real. WSS es un socket real y emisor SIMULATOR, no hardware GPS. Migración/restauración usa bases temporales pobladas, no respaldo productivo. Navegador utiliza TLS local con excepción al certificado del fixture; no representa validación HTTPS del nuevo despliegue.

## Dependencias y cierre

Externas: protocolos clínicos por producto/órgano, acreditaciones profesionales y aprobaciones reales, política oficial de prioridad, catálogo institucional HLA, fuente vial regional autorizada y hardware GPS. Consumo sintético no acredita precisión con datos físicos reales. Etapas posteriores: mapas/clientes completos y comprobación productiva del incremento, dentro de autorización nueva aplicable.

La documentación de normas y los casos sintéticos no certifican reglas clínicas. Se requiere una nueva comprobación independiente sobre las fuentes finales; esta autoevaluación no la sustituye. **CONTINUACIÓN PARCIAL POR DEPENDENCIA DECLARADA.** La etapa no queda cerrada clínicamente ni con fuente vial real. Solo continuar tareas independientes o dirigidas a resolver esas dependencias; volver a comprobarlas al integrar. No hay defectos funcionales pendientes detectados en las pruebas finales seleccionadas. La comprobación productiva del incremento requiere autorización aplicable y ensayo de despliegue/restauración; localhost no la acredita.


## Archivo de detalles — 04/11/2026

Los manifiestos extensos, capturas de estado Git y muestras HTTP de este expediente se conservan sin alterar sus bytes en [el archivo comprimido](../../../../archivo/detalles-20261104.tar.gz); el [índice](../../../../archivo/detalles-20261104.json) identifica cada ruta original, tamaño y SHA-256. Los resultados, JUnit e incidencias siguen visibles. Antes de ejecutar verificadores históricos que lean esos detalles, restaurar las rutas desde la raíz del repositorio con `tar -xzf documentation/evidencias/archivo/detalles-20261104.tar.gz`. Extraer en una carpeta temporal para una consulta sin escrituras en el repositorio. Los hashes históricos corresponden al corte original, no al árbol actual.
