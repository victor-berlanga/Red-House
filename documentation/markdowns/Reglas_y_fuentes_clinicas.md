# Registro de fuentes y reglas

## Estado vigente: fuentes públicas, 02/11/2026

Incremento local **0.4.4 / esquema 16**. Las secciones fechadas anteriores se conservan como historia; sus límites de catálogo y fuente vial se actualizan aquí. Continúa desactivada la aplicación clínica de perfiles académicos. No se recibió aprobación profesional ni se atribuye esa aprobación a las fuentes públicas.

`apps/services/redhouse/reference_data/public_rules_v1.json` registra cinco referencias documentales con ID, versión, emisor, URL, sección, jurisdicción, fechas, condiciones, excepciones y límite. Al crear un perfil se copian las referencias seleccionadas y su SHA-256 en `reference_snapshot`; cambiar el catálogo no reescribe perfiles existentes. La vigencia de la referencia se comprueba con intervalo `[inicio, fin)`, además de la vigencia propia del perfil.

| Referencia | Fuente primaria y sección | Aplicación y límite |
|---|---|---|
| MX-NOM253-2012-9.5.1 | [DOF, NOM-253-SSA1-2012](https://dof.gob.mx/normasOficiales/4917/salud3a/salud3a.html), 9.5.1.1–3 y 9.5.1.11 | Registro de pruebas según componente y responsabilidad del establecimiento. No impone una lista universal ni convierte resultados en compatibles. |
| MX-NOM253-2012-10.1 | Mismo texto, 10.1–10.2 | Identificación de unidades/muestras. La relación electrónica no acredita etiqueta física correcta. |
| MX-NOM253-2025-TRANSICION | [DOF, publicación del 12/10/2026](https://dof.gob.mx/nota_detalle.php?codigo=5800942&fecha=12/10/2026), vigencia/transitorios; [ficha oficial PLATIICA](https://platiica.economia.gob.mx/normalizacion/nom-253-ssa1-2025/) | Entrada publicada 10/04/2027; no se anticipa. La edición 2012 tiene fin documental en esa fecha. Requiere revisar la transición antes del uso real. |
| MX-TRASPLANTES-2014-33 | [Reglamento, Cámara de Diputados](https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_LGS_MT.pdf), arts. 1, 2 VIII y 33 I/IV/VI/VIII | Comité y laboratorio competentes. No regula sangre por extensión ni proporciona una puntuación local de asignación. |
| HLA-NAMING-2010-SYNTAX2 | [Naming Alleles](https://hla.alleles.org/pages/nomenclature/naming_alleles/) | Forma de nombres y resolución; ninguna equivalencia con histocompatibilidad. |

### Catálogo HLA verificable

Edición IPD-IMGT/HLA **3.66.0**, fechada 14/10/2026, fijada al commit `d972ae287948dc2e5468a40ff3b3d27227541189`. `hla_catalogues.json` contiene URL, atribución y SHA-256 `1913c5f748e6d649017996686e135dc6ffedc53215d4da7efad8f9165f3d2f35`. El importador descarga el archivo original sin modificarlo; los 970.839 bytes se verificaron nuevamente en un directorio temporal.

La [licencia del proveedor](https://www.ebi.ac.uk/ipd/imgt/hla/licence/) exige atribución y restringe modificaciones/redistribución. El repositorio conserva manifiesto y enlaces; el catálogo completo se instala localmente, sin publicarlo como espejo ni distribuir una versión modificada.

`catalogue_version` selecciona la edición independientemente de `nomenclature_version`, que selecciona sintaxis. El backend devuelve `EXACT` con identificador del alelo, `LOW_RESOLUTION` con cantidad de entradas, `NOT_FOUND` o `GROUP_NOT_ALLELE`. Ejemplo: `A*01:01:01:01` corresponde a `HLA00001`; `A*01:01`, a 303 entradas a esa resolución. Una coincidencia a baja resolución no identifica un alelo específico. Ambigüedad y grupos parciales siguen impidiendo completitud cuando se exige ese locus.

Sin edición seleccionada se informa `NOT_CHECKED`, conservando el flujo histórico. Con catálogo obligatorio, cualquier tipificación sin comprobación reconocida deja `HLA:CATALOGUE_UNVERIFIED`, incluso bajo un código como `CUSTOM_HLA`. Edición desconocida devuelve 422; archivo ausente o alterado, 503. Nunca se omite silenciosamente la comprobación solicitada. El resultado conserva edición, hash y pertenencia; corregir agrega otra fila.

### Alcance académico y dependencia clínica

Se pueden verificar registro, integridad, procedencia, versiones, completitud, restricciones y reproducción con datos ficticios. Las fuentes públicas sostienen documentación y validadores técnicos; no reemplazan protocolos por producto/órgano, aprobación competente ni responsabilidad del establecimiento.

La política de prioridad sigue siendo una simulación versionada; no se dedujeron pesos clínicos de las normas. Operación clínica requiere aprobación institucional de reglas, parámetros, estudios y competencias. Esta dependencia no impide completar el alcance académico permitido por el prompt 02. Fuente vial pública: [operación](../entrega-final/algoritmos/correccion/Operacion_y_reproduccion.md). GPS físico queda para el final por instrucción del usuario.

## Historia documental anterior

Consulta: **31 de octubre de 2026**, México. Responsable de esta integración técnica: agente de desarrollo; no es autor ni aprobador clínico. No se recibió protocolo institucional firmado. Ninguna cuenta sintética equivale a una acreditación profesional real.

## Fuentes primarias consultadas

| Documento / emisor | Sección y ámbito | Vigencia observada y limitaciones |
|---|---|---|
| [NOM-253-SSA1-2012, DOF / Secretaría de Salud](https://sidof.segob.gob.mx/notas/docFuente/5275587) | 1, 4 y 14; sangre y componentes con fines transfusionales, México | [PLATIICA / Secretaría de Economía](https://platiica.economia.gob.mx/normalizacion/nom-253-ssa1-2012/) la registra vigente. No regula selección HLA de órganos. No se trasladan sus criterios a órganos. |
| [NOM-253-SSA1-2025, DOF / Salud](https://diariooficial.gob.mx/normasOficiales/9582/salud/salud.html) | Norma sucesora; sangre y componentes, México | Publicada 12/10/2026. [Ficha oficial](https://platiica.economia.gob.mx/normalizacion/nom-253-ssa1-2025/) indica pendiente, entrada 10/04/2027. Requiere revisión institucional de transición antes de activar reglas; el programa no anticipa su vigencia. |
| [Reglamento de la Ley General de Salud en materia de trasplantes, Orden Jurídico Nacional](https://www.ordenjuridico.gob.mx/Documentos/Federal/html/wo93313.html) | Capítulo V, arts. 36–41; órganos, tejidos y células, México | Texto identificado como vigente por el repositorio oficial consultado. Distribución/asignación corresponden a comités y procedimientos institucionales; no se sustituye por suma local. Aplicabilidad concreta pendiente de responsable institucional. |
| [HLA nomenclature: Naming Alleles, comité de nomenclatura](https://hla.alleles.org/pages/nomenclature/naming_alleles/) | Nomenclatura con campos numéricos separados por dos puntos y sufijos de expresión | Convención internacional de nombres; no regla de compatibilidad. Se registra versión declarada del laboratorio. El validador comprueba forma, no existencia del alelo en una versión del diccionario ni interpretación de grupos. |

## Perfiles persistidos

`lab_profiles`: UUID, versión consecutiva, autor, institución, fuente, propósito, tipo/componente, pruebas y loci exigidos, fecha efectiva y `supersedes`. Estados admitidos: `DRAFT`, `IN_REVIEW`, `RETIRED`. `synthetic=true` y `clinical_enabled=false` son obligatorios; el esquema y el contrato impiden activación clínica. No hay aprobador ficticio ni transición automática a aprobado. Una nueva versión no modifica la anterior. El estado aprobado queda **no habilitado** hasta incorporar protocolo firmado, autoridad competente, ámbito y vigencia verificables; esto es una dependencia externa y un mecanismo de aprobación todavía no implementado, no una aprobación implícita.

La exigencia de loci es propia del perfil, nunca universal. Un órgano distinto requiere otro perfil. La completitud comprueba resultados revisados e informados y loci sin ambigüedad; no deduce PRA/cPRA, anticuerpos, prueba cruzada ni aptitud. Resultados inmunológicos diferentes usan códigos, valores/unidades, método, laboratorio y fuente explícitos.

Estados de resultado independientes de revisión: `NOT_PERFORMED`, `PENDING`, `INDETERMINATE`, `REPORTED`, `CORRECTED`. Desconocido no equivale a negativo. HLA registra loci, alternativas de alelos, ambigüedad, nomenclatura y resolución declaradas, muestra/fecha, emisión y responsable. Correcciones agregan filas. El documento privado se crea sobre el resultado existente y puede referenciarse en su corrección; solo se acepta un documento RESULT de la misma muestra y ámbito. Descarga y análisis permanecen bajo Documentos.

## Catálogo ejecutable y límites

| Versión | Fuente/propósito | Aprobación / alcance |
|---|---|---|
| RBC-1.0 | Filtro académico ABO/RhD heredado | Conservado; exclusivamente eritrocitos, sin aprobación clínica nueva |
| ORGAN-1.0 | Tipo y ABO idéntico heredados | Conservado; no interpreta HLA ni incorpora RhD como restricción |
| LOGISTICS-1.0 | Caducidad, minutos, distancia, ID | Conservado; urgencia y espera son contexto, no factores de orden |
| COVERAGE-HK-1.0 | Hopcroft–Karp sobre candidatos revisados | Cardinalidad máxima; no coste ni prioridad; no reserva |
| EXPLAIN-ACADEMIC-1.0 | Datos sintéticos y pruebas exigidas explícitas | Completitud técnica y exclusiones explicables, sin dictamen |
| LOGISTICS-SIM-2.0 | Política sintética lexicográfica | Urgencia y espera descendentes; caducidad, tiempo, distancia e ID ascendentes. Sin ponderaciones clínicas. Solo componentes sanguíneos declarados |
| ROUTE-DIJKSTRA-1.0 | Grafo dirigido sintético, pesos no negativos | Tiempo mínimo, distancia como desempate. No tráfico actual |
| DEMAND-SES-1.0 | Consumo sintético por ventanas uniformes | Suavizado exponencial simple, referencia persistencia y evaluación temporal |
| CONSISTENCY-1.0 | Reglas técnicas sobre instantánea sintética | Anomalías potenciales; no incidentes confirmados ni cambios de historia |

Dependencias externas: protocolos por componente/órgano; catálogo HLA y release institucional; acreditación de aprobadores; escala y procedencia de urgencia; políticas de vigencia y conservación; datos reales de consumo; proveedor/grafo vial autorizado; GPS físico. No se fijan umbrales clínicos por conveniencia técnica.

## Revisión correctiva: 31/10/2026 local, 01/11/2026 UTC

Vigencia verificada de nuevo en fuentes primarias durante esta ejecución; ninguna cita constituye aprobación del software o de los parámetros del proyecto.

| Emisor / documento | URL y sección consultada | Jurisdicción, vigencia y límite |
|---|---|---|
| Secretaría de Economía / PLATIICA, NOM-253-SSA1-2012; autoridad sanitaria emisora Secretaría de Salud | [Ficha oficial](https://platiica.economia.gob.mx/normalizacion/nom-253-ssa1-2012/), estado y fechas | México, disposición de sangre humana y componentes con fines terapéuticos. Ficha: vigente, publicación 26/10/2012, entrada 25/12/2012. No convierte el filtro académico RBC en protocolo clínico aprobado ni regula por extensión asignación de órganos. |
| Secretaría de Economía / PLATIICA, NOM-253-SSA1-2025 | [Ficha oficial](https://platiica.economia.gob.mx/normalizacion/nom-253-ssa1-2025/), publicación/entrada | México. Ficha pendiente: publicación 12/10/2026, entrada prevista 10/04/2027. Transición que requiere nueva revisión antes de aplicación futura; no se anticipa su vigencia. |
| Secretaría de Gobernación, Reglamento de la Ley General de Salud en Materia de Trasplantes | [Texto oficial](https://www.ordenjuridico.gob.mx/Documentos/Federal/html/wo93313.html), ámbito y artículos 36–41 | México; texto vigente consultado, reglamento de 2014. Separa sangre del ámbito de trasplantes del reglamento. Procedimientos y responsables autorizados externos; no se deriva una puntuación local oficial. |
| Comité de nomenclatura HLA / HLA Nomenclature | [Naming Alleles](https://hla.alleles.org/pages/nomenclature/naming_alleles/), campos y sufijos | Nomenclatura internacional, no norma mexicana de asignación. De dos a cuatro campos, sufijos N/L/S/C/A/Q. Validador comprueba forma; no prueba existencia de alelo ni pertenencia a una edición del catálogo. |

No se entregó protocolo institucional aprobado por órgano/producto, acreditación de aprobadores reales, política oficial de prioridad, umbral clínico de antigüedad/contradicción ni fuente vial autorizada. Registro técnico, estados y ejecución sintética ya no dependen de que esas fuentes externas lleguen: están implementados. Aplicación clínica permanece bloqueada hasta acreditar cada requisito, con segregación y documento privado verificable.

Registro ejecutable actual: `lab_profiles` inmutable + `rule_actions` append-only + gobernanza efectiva. La columna inicial `clinical_enabled=false` no es autorización; el permiso efectivo se deriva de aprobación, vigencia y competencia configurada, y los comandos operativos lo comprueban. [Política, transiciones, contratos y límites](../entrega-final/algoritmos/correccion/Operacion_y_reproduccion.md). Pruebas sintéticas de aprobación técnica no equivalen a revisión profesional y no deben presentarse como actas institucionales.
