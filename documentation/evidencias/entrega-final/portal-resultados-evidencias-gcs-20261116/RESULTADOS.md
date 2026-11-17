# I06-02 — resultados de laboratorio y evidencias de traslado en GCS

**Aprobados RESULT y evidencia de traslado: positivos y sus negativas.** Ejecuciones del 16 de noviembre de 2026, horario de Monterrey; los recibos expresan UTC del 17. No se atribuye aceptación completa a I06-02 ni a la etapa 06. No se repitió acreditación.

## RESULT: fallo de arnés conservado y continuación del mismo documento

El primer intento inició sesión como `medical2`, envió exactamente un POST documental y llegó a la pantalla «Verificado / Sin amenazas detectadas». Falló después: el arnés exigía un href literal sin query, mientras la presentación añadía `return_to`. Se conserva como **FAIL** en [su recibo](result-primer-intento/receipt.json) y [captura original](result-primer-intento/fallo.png). No fue rechazo de GCS ni del escáner; tampoco se transforma retrospectivamente en un caso aprobado.

La [continuación aprobada](result-continuacion-get/receipt.json) abrió por GET el mismo UUID ya creado. No volvió a preparar, subir ni verificar el documento. El enlace se validó por origen y pathname exactos; solo se admitió un `return_to` local del mismo origen. La descarga ordinaria del objeto firmado devolvió exactamente el PNG original de 116 bytes y su SHA-256. [Captura del mismo documento](result-continuacion-get/verified.png); sus bytes coinciden con la captura del primer intento.

El oráculo comprobó archivo VERIFIED, propietario y expediente RESULT/LAB_RESULT, generación y hash, un análisis CLEAN del motor real `CLAMD_INSTREAM`, y exactamente dos eventos documentales correlacionados con sus dos proyecciones en Auditoría SQL y MongoDB. El resultado HLA autorizado y su muestra conservaron la correlación del handoff. La fila HLA completa fue idéntica antes y después de la continuación. **La fila previa al POST original solo estuvo en memoria y no se persistió: esta evidencia no acredita una comparación completa anterior y posterior a aquel POST.** El archivo nuevo no sustituye el resultado HLA del handoff.

La [negativa con `medical1`](result-negativa/receipt.json), de otra institución, recibió 403 en detalle y descarga. No obtuvo URL firmada ni enlace de descarga y no alteró documentos o la fila del sujeto. [Captura](result-negativa/denied.png).

## Evidencia de traslado

El [recorrido SHIPMENT positivo](shipment-positivo/receipt.json) aprobó: `transport1` cargó por formulario real un JPEG nuevo de 645 bytes y descargó exactamente esos bytes. El archivo quedó VERIFIED, con generación/hash correlacionados, un análisis CLEAN de ClamD real y dos eventos únicos conservados en Auditoría SQL y MongoDB. La fila del traslado permaneció intacta. [Captura positiva](shipment-positivo/verified.png).

La [negativa de `transport2`](shipment-negativa/receipt.json), responsable no asignado, recibió dos 403: listado documental del traslado y descarga del objeto. No obtuvo URL firmada ni alteró documentos o traslado. [Captura de rechazo](shipment-negativa/denied.png). Raíz confirmó ambos resultados y el cierre de una familia propia en cada caso.

Se usó el traslado original autorizado del laboratorio, distinto del traslado E2E-B que terminó custodia. No se atribuye a este ensayo recepción o destino de aquel órgano.

## Entorno, sesiones y límites

Portal monolítico real en Chrome, configuración efectiva GCS coincidente en web y API de Documentos, bucket existente y datos sintéticos. Se reutilizó el runtime `run-03-gcs`, su CA de laboratorio y binding de proceso/rutas; Chrome confió solo en el SPKI efímero revisado. No se usó `ignoreHTTPS` ni se simuló almacenamiento. Esta evidencia no acredita TLS público de producción, aplicación nativa, carga de rendimiento ni nueva política clínica.

Cada ejecución terminada cerró su única familia nueva mediante logout y oráculo SQL/Redis; no se publican identificadores de sesión, tokens, cookies, factores ni URLs firmadas. Los mapas antes/después de fuentes coinciden en cada ejecución. [Mapa completo de referencia](sources-reviewed.json), [resumen](summary.json) y hashes de los recibos privados enlazan el corte; las capturas se copian intactas. No se cerró el fixture compartido desde estos casos; su cierre global corresponde al responsable del runtime.

Los dos objetos web sintéticos (PNG RESULT y JPEG SHIPMENT) se conservan como evidencia en el fixture/bucket con su generación identificada. La limpieza propia del ensayo nativo iOS no comprende estos archivos; este expediente no afirma su eliminación. La configuración de bucket observada previamente mantiene eliminación reversible de siete días; no acredita borrado físico inmediato ni retención legal de bucket. No se cambiaron IAM, infraestructura ni firmas del escáner.
