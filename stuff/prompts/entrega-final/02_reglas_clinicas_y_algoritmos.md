# Completar reglas clínicas documentadas y algoritmos explicables

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md`, `stuff/prompts/entrega-final/00_contexto_y_reglas.md` y los contratos/modelos del prompt 01. Implementa las ampliaciones del motor de apoyo y sus explicaciones. No sustituyas decisiones profesionales ni inventes criterios clínicos.

## Punto de partida y límites

Inspecciona `ms_compatibilidad`, `ms_priorizacion_geografia`, sus algoritmos, pruebas y consumidores. Conserva las evaluaciones históricas, `RBC-1.0`, `ORGAN-1.0`, `LOGISTICS-1.0` y `COVERAGE-HK-1.0`. Cambiar una regla crea una versión; no recalcula el pasado silenciosamente.

La preselección de órganos por tipo y ABO idéntico no es interpretación HLA. El ranking actual guarda urgencia y fecha como contexto; no las utiliza para ordenar. Documenta el comportamiento nuevo sin atribuírselo a la versión anterior.

## Fuentes y aprobación de reglas

Consulta fuentes primarias oficiales vigentes para México y los protocolos institucionales disponibles. Verifica el texto y la vigencia aplicables de la NOM-253-SSA1-2012 y fuentes oficiales de donación/trasplante, sin asumir que una regla sanguínea regula órganos. Conserva URL o documento, emisor, fecha de consulta, sección, jurisdicción, alcance por recurso y limitaciones.

Construye un registro de perfiles/reglas con identificador, versión, autor, fuente, parámetros, datos exigidos, propósito, estado borrador/en revisión/aprobado/retirado, aprobador competente y vigencia. La aprobación no puede otorgársela el programa ni una cuenta técnica de prueba para aparentar revisión profesional real.

Completa registro, validación técnica y ejecución sintética aun si la revisión profesional externa falta. En ese caso usa perfiles etiquetados como académicos y desactiva su aplicación clínica. Registra la dependencia exacta. No bloquees las tareas técnicas independientes ni declares aprobado el motor clínico.

## Información de laboratorio y HLA

Implementa contratos y persistencia para asociar resultados a donante/receptor, muestra, órgano/recurso y solicitud según corresponda. Cada resultado debe conservar laboratorio/institución, método, fecha de muestra y emisión, nomenclatura/resolución declarada, unidades cuando apliquen, documento privado y responsable/revisión.

Modela tipificación HLA mediante loci y alelos declarados por el laboratorio, sin imponer una lista clínica universal. Valida sintaxis con la nomenclatura y versión documentadas. Representa explícitamente no realizado, pendiente, indeterminado, informado y corregido; la ausencia de valor no equivale a negativo.

Permite registrar otros datos inmunológicos y pruebas cruzadas pertinentes como resultados documentados con su fuente, método, fecha y revisión. No deduzcas PRA/cPRA, anticuerpos, compatibilidad ni aptitud a partir de texto libre o coincidencias de cadenas. No calcules indicadores clínicos derivados sin algoritmo autorizado y datos requeridos.

Expón cuatro niveles separados en API e interfaces: información registrada, completitud según perfil, evaluación/preselección y dictamen profesional. La completitud técnica no equivale a compatibilidad. Un perfil puede exigir pruebas diferentes por órgano/producto sin asumir equivalencia entre riñón, hígado y corazón.

Si se implementa comparación académica de alelos, identifícala como comparación de datos sintéticos sin capacidad de declarar trasplantabilidad. Una evaluación clínica solo se habilita con reglas aprobadas y conserva el razonamiento autorizado.

## Sangre y órganos con reglas diferenciadas

- Sangre: componente, ABO/Rh cuando corresponda, pruebas documentadas, liberación, caducidad y condiciones de conservación. Conserva el filtro académico RBC dentro de su alcance. Plasma, plaquetas y otros componentes no heredan esa matriz; completa sus flujos y solo activa filtros respaldados por reglas aprobadas.
- Órganos: tipo de órgano, información disponible, tiempos críticos capturados con procedencia, evaluaciones inmunológicas, autorizaciones y procedimiento oficial de asignación referido. RhD no se incorpora copiando el filtro de eritrocitos.
- Información faltante, contradictoria, obsoleta, recurso bloqueado o incidencia térmica produce exclusión o revisión pendiente según perfil documentado. No conviertas desconocido en favorable.
- El dictamen requiere profesional autorizado, ámbito, motivo, fecha y versión de datos. Si cambian resultados, recurso, solicitud o ruta relevante, señala obsolescencia y exige la reevaluación correspondiente; no reutilices una autorización inválida.

## Algoritmos de la entrega final

### ALG-01 Evaluación explicable

Implementa ejecución reproducible de perfiles versionados. Devuelve candidatos considerados, admitidos y excluidos; razones y datos que determinan cada resultado; datos faltantes; límites; duración y fuente. Conserva instantánea o referencias inmutables de entradas y resultados, evitando exponer expedientes ajenos.

Documenta complejidad, consumo y casos límite. No presentes una consulta SQL o una lista ordenada como toda la contribución algorítmica.

### ALG-02 Priorización y logística

Separa restricciones clínicas/legales de la comparación logística. La urgencia solo puede proceder de personal autorizado y una escala documentada. Para sangre y coordinación regional implementa una política operativa explicable que considere urgencia documentada, espera, riesgo de vencimiento, tiempo y distancia dentro de los criterios permitidos. Define desempates estables y qué sucede cuando falta un factor.

No asignes ponderaciones clínicas arbitrarias. Si no hay política aprobada, ejecuta comparaciones y simulaciones etiquetadas y muestra los factores sin afirmar prioridad oficial. Para órganos conserva el procedimiento autorizado externo; no construyas una lista oficial de receptores por una suma ponderada local.

Implementa alternativas geográficas mediante una fuente definida: proveedor autorizado o grafo regional versionado con pesos de tiempo/distancia y procedencia. Si usas Dijkstra/A* u otro algoritmo, documenta sus supuestos y contrástalo con un oráculo en grafos pequeños. Una distancia en línea recta no se etiqueta como ruta vial ni tiempo real. Conserva fecha, restricciones, indisponibilidad del proveedor e incertidumbre.

Aplica la [especificación de rastreo GPS y mapa de Nuevo León](09_rastreo_gps_websockets.md): utiliza únicamente posiciones observadas con fuente/fecha/calidad cuando intervengan en cálculos logísticos. Separa trayecto recibido por WebSockets, ruta planificada y ETA estimada. Un mapa actualizado o una coordenada del GPS no demuestra tráfico actual, cumplimiento térmico, entrega ni prioridad clínica. Conserva la antigüedad e incertidumbre de los datos y no extrapoles una posición como medición real.

### ALG-03 Cobertura y balanceo regional

Reutiliza Hopcroft–Karp y su oráculo exhaustivo. Las aristas solo utilizan candidatos permitidos y revisados cuando el flujo lo exige. Considera cantidades, disponibilidad y versiones; evita proponer dos veces el mismo recurso. No atribuyas al matching cardinalidad máxima una optimización de urgencia o coste que no realiza.

Si agregas prioridades o costes, implementa y justifica un algoritmo apropiado, por ejemplo flujo de coste mínimo con objetivos operativos documentados, y demuestra la diferencia respecto del matching anterior. Las propuestas no reservan ni transfieren por sí mismas y se revalidan al confirmar.

### ALG-04 Riesgo de caducidad y demanda

Construye un pronóstico o estimador reproducible a partir de consumo histórico y stock, por institución/componente y ventana definida. Compara contra una referencia sencilla, separa entrenamiento y evaluación por tiempo cuando corresponda y evita filtración de futuro. Identifica datos sintéticos y escasez de muestras.

Mide error y utilidad operativa con métricas justificadas; conserva parámetros, versión y rango de incertidumbre cuando el método lo permita. Expón sugerencias de rotación/abastecimiento para revisión, sin prolongar caducidades, modificar condiciones clínicas o ejecutar transferencias.

### ALG-05 Detección de inconsistencias

Detecta duplicados de identificador, recurso reservado varias veces, cantidades incompatibles, secuencias rotas, donación sin procedencia válida, resultado de muestra ajena, lecturas térmicas incoherentes y proyecciones desactualizadas. Usa reglas técnicas explicables y consultas/grafos según corresponda. Distingue anomalía potencial de incidente confirmado y abre revisión sin corregir historia automáticamente.

## Validación y criterios de aceptación

Entrega casos sintéticos reproducibles para datos completos/incompletos, ABO coincidente con HLA faltante, alelos ambiguos, pruebas pendientes/corregidas, órganos distintos, componentes sin perfil, unidad vencida, ruta insuficiente, excursión térmica, dictamen de otra institución y usuario sin permiso.

Demuestra que: completar HLA no genera dictamen; registrar dictamen no puede hacerlo un operador/transportista; cambiar una entrada crítica invalida la evaluación; una propuesta no crea reserva; la reserva exige revisión vigente; la urgencia modifica únicamente el resultado de una política que la utiliza; los resultados se reproducen con sus versiones.

Prueba propiedades de los algoritmos con oráculos independientes y escenarios donde una estrategia voraz falle. Mide tiempos y memoria para tamaños pequeños, medios y grandes, incluyendo límites de grafo y listas vacías. Verifica contratos JSON/XML y autorización de explicaciones y documentos.

Actualiza `documentation/markdowns/Algoritmos.md` y crea el catálogo de reglas y fuentes en la documentación vigente. Cada algoritmo debe incluir problema, entradas/salidas, variables, restricciones, pseudocódigo, complejidad, ejemplos, métricas, limitaciones y pruebas. Integra sus resultados con API y web modular; los prompts de cliente mostrarán esa misma información sin recalcularla. Actualiza matriz y `PROJECT_STATUS.md` sin declarar validación clínica que no exista.
