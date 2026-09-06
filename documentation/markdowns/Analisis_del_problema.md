# Análisis del problema

> **Estado del documento:** línea base académica revisada.
> **Fecha de validación documental:** 7 de septiembre de 2026.
> **Cobertura documental:** proyecto académico completo, con implementación gradual por parciales e incrementos.
> **Alcance de la validación:** consistencia con la consigna del proyecto y contraste con fuentes públicas oficiales; no sustituye un levantamiento institucional, una validación clínica ni una opinión jurídica.

## 1. Introducción

La disponibilidad de sangre y órganos es un problema regional de coordinación, oportunidad y trazabilidad. Una institución puede enfrentar una necesidad urgente mientras otra institución cercana dispone de un recurso potencialmente útil. Si los inventarios, solicitudes, estudios de compatibilidad y capacidades de traslado permanecen aislados, la identificación de opciones depende de comunicaciones fragmentadas y de consultas realizadas bajo presión. Esto puede aumentar el tiempo de respuesta, favorecer el desperdicio de recursos con vida útil limitada y dificultar la explicación posterior de una decisión.

El proyecto propone una red regional que conecte bancos de sangre, hospitales, coordinadores, personal de traslado y otros participantes autorizados. La plataforma deberá ofrecer una visión compartida y controlada del inventario, apoyar la búsqueda de candidatos compatibles, priorizar solicitudes y preservar la cadena de custodia desde el origen hasta la recepción del recurso.

La plataforma no será una autoridad médica ni un mecanismo automático de asignación. Su función será organizar información, aplicar reglas previamente validadas, presentar alternativas explicables, emitir alertas y conservar evidencia. La evaluación clínica, la autorización y las decisiones sujetas a regulación permanecerán bajo responsabilidad de personal humano autorizado.

Este planteamiento es coherente con el marco general de la Organización Mundial de la Salud (OMS, 2026, s. f.-a): para sangre, recomienda servicios coordinados, políticas y sistemas de calidad que cubran recolección, pruebas, procesamiento, almacenamiento y distribución; para trasplantes, mantiene principios orientados a seguridad, ética, transparencia y supervisión (OMS, s. f.-c). La necesidad de interoperabilidad y decisiones informadas también aparece en su enfoque de salud digital (OMS, s. f.-b), mientras que la gobernanza de datos exige calidad, privacidad y uso responsable de algoritmos (Organización Mundial de la Salud, Oficina Regional para Europa, 2025). Estas referencias sustentan el análisis general, pero no reemplazan la normativa de la jurisdicción donde se despliegue la plataforma.

### 1.1 Enfoque académico y límites deliberados

El proyecto se desarrollará dentro de un semestre y por un equipo académico. Por ello, el análisis busca demostrar comprensión del negocio y orientar una solución ejecutable, pero no pretende reproducir por completo la operación de una red sanitaria nacional ni definir decisiones clínicas reales. Su cobertura documental comprende la solución completa prevista para el proyecto; los parciales determinan el orden de implementación y no reducen el alcance que deberá quedar analizado, especificado y diseñado.

Para mantener un alcance viable se adoptan los siguientes límites:

- Las instituciones, personas y operaciones utilizadas en demostraciones serán ficticias.
- No se almacenarán datos clínicos reales ni se conectará la solución académica a sistemas hospitalarios reales.
- Las reglas de compatibilidad, elegibilidad, urgencia, conservación y asignación no se inventarán. Podrán representarse como reglas demostrativas claramente identificadas, pero no como criterios válidos para uso médico.
- La validación de esta versión es documental. La validación con especialistas e instituciones se registra como trabajo necesario antes de cualquier uso real.
- El análisis, los requisitos y la arquitectura completa abarcarán sangre y órganos, así como el sistema web, los microservicios, la aplicación móvil y la aplicación de escritorio. El producto mínimo del primer parcial se concentrará en un proceso acotado de inventario sanguíneo, sin automatizar decisiones clínicas.
- La documentación conservará las capacidades previstas para todo el proyecto, aunque se implementen en incrementos posteriores.
- En cada incremento se favorecerán decisiones sencillas, trazables y demostrables sobre diseños complejos que no aporten evidencia a la fase correspondiente.

## 2. Contexto del problema

Los procesos de donación y asignación involucran información que cambia con rapidez y que se distribuye entre varias instituciones. Entre los datos relevantes se encuentran la disponibilidad real del recurso, su ubicación, condiciones de conservación, vigencia, resultados de pruebas, compatibilidad, urgencia clínica, tiempo acumulado de espera, distancia y capacidad de traslado.

Una parte importante del problema no consiste únicamente en conocer que existe una unidad u órgano. También es necesario determinar si continúa disponible, si su información es suficiente y confiable, si puede utilizarse para un receptor determinado, si existe otra solicitud con mayor prioridad, si el traslado es viable y si cada entrega o cambio de custodia ha sido confirmado por el personal correcto.

La coordinación regional agrega complejidad porque cada institución conserva responsabilidades sobre sus pacientes, donantes, inventarios y registros. La colaboración requiere compartir solamente la información necesaria, con diferentes niveles de detalle según el perfil, la institución y el momento del proceso. La utilidad de una vista regional no debe implicar acceso irrestricto a datos clínicos o personales.

Además, aunque la sangre y los órganos comparten necesidades de compatibilidad, prioridad, transporte y trazabilidad, no constituyen un mismo tipo de recurso. Sus pruebas, tiempos, condiciones, restricciones y procesos de autorización pueden ser diferentes. La solución deberá admitir esas diferencias y evitar imponer un flujo genérico que simplifique indebidamente decisiones clínicas o normativas.

## 3. Situación problemática

El problema central es la ausencia de una coordinación regional oportuna, consistente y auditable entre la demanda de sangre u órganos y la disponibilidad distribuida en distintas instituciones.

Esta situación se manifiesta en varios problemas relacionados:

1. **Visibilidad fragmentada del inventario.** Una institución puede desconocer qué recursos están disponibles en otra ubicación, en qué estado se encuentran o durante cuánto tiempo continuarán siendo utilizables.
2. **Solicitudes dispersas.** Las necesidades ordinarias y urgentes pueden registrarse y comunicarse por medios diferentes, sin un seguimiento uniforme de su estado, responsable, prioridad o tiempo de atención.
3. **Evaluación tardía de compatibilidad.** La información necesaria puede estar incompleta o distribuida, retrasando la identificación de candidatos y obligando a repetir búsquedas o verificaciones.
4. **Priorización poco transparente.** Cuando intervienen compatibilidad, urgencia, tiempo, distancia y disponibilidad, una decisión no documentada resulta difícil de explicar, revisar o auditar.
5. **Riesgo de pérdidas por caducidad.** Sin alertas y una perspectiva regional, una unidad puede vencer en una institución mientras existe demanda atendible en otra.
6. **Coordinación insuficiente del traslado.** Una asignación puede fallar si no se consideran ubicación, tiempo estimado, capacidad de transporte, confirmaciones y contingencias.
7. **Trazabilidad incompleta.** Si la recolección, preparación, salida, transferencia, recepción y entrega no se registran de forma consistente, se debilita la cadena de custodia.
8. **Acceso riesgoso a información sensible.** La colaboración entre instituciones puede provocar exposición excesiva de identidad, datos clínicos, ubicación o evidencias si no existen controles por rol, recurso e institución.
9. **Información inconsistente o desactualizada.** Duplicados, estados contradictorios, registros incompletos o cachés obsoletos pueden generar recomendaciones incorrectas o intentos de asignación simultánea.
10. **Dependencia de operaciones manuales.** Las verificaciones repetitivas, alertas y consolidaciones manuales consumen tiempo que es especialmente crítico durante solicitudes urgentes.

## 4. Formulación del problema

¿Cómo coordinar de manera regional, segura, oportuna y auditable los inventarios, solicitudes, estudios de compatibilidad, prioridades, asignaciones y traslados de sangre y órganos, de modo que las instituciones puedan identificar recursos potencialmente adecuados y reducir demoras o pérdidas, sin sustituir la evaluación médica ni vulnerar la privacidad y las obligaciones regulatorias?

## 5. Causas principales

### 5.1 Fragmentación institucional

Cada hospital o banco puede administrar su información de manera local. La falta de una vista regional impide relacionar rápidamente una necesidad con recursos disponibles fuera de la institución solicitante.

### 5.2 Falta de un modelo común de información

Si las instituciones representan de forma distinta los estados del inventario, solicitudes, pruebas, asignaciones y traslados, la información no puede compararse ni intercambiarse de forma confiable. Los identificadores ambiguos también dificultan seguir un recurso a través de varias etapas.

### 5.3 Actualización no oportuna

La disponibilidad, caducidad, ubicación y prioridad pueden cambiar durante el proceso. Si estos cambios no se reflejan a tiempo, otras instituciones pueden actuar sobre información que ya no es válida.

### 5.4 Criterios de compatibilidad y prioridad no integrados

La búsqueda regional requiere relacionar datos del recurso, receptor y solicitud. Sin reglas validadas y versionadas, el sistema no puede producir resultados consistentes ni explicar por qué presentó una alternativa antes que otra.

### 5.5 Coordinación débil entre asignación y transporte

Encontrar un recurso compatible no garantiza que pueda entregarse dentro del periodo requerido. La decisión debe considerar disponibilidad efectiva, ubicación, tiempo, traslado, aceptación y continuidad de la cadena de custodia.

### 5.6 Trazabilidad distribuida

Cuando cada participante registra solamente su parte o utiliza medios no integrados, reconstruir quién realizó una acción, cuándo ocurrió, qué evidencia existía y bajo qué autorización se vuelve difícil.

### 5.7 Controles de acceso insuficientes o demasiado amplios

Un sistema regional debe permitir colaboración sin convertir todos los datos en información visible para todos. La ausencia de autorización por institución y recurso puede exponer información sensible; controles demasiado restrictivos, en cambio, pueden impedir actuar durante una urgencia. Este equilibrio requiere reglas explícitas y auditables.

### 5.8 Capacidad limitada para anticipar demanda y caducidad

Sin análisis de historiales, tendencias y distribución regional, las instituciones reaccionan a faltantes o vencimientos cuando ya existe poco margen de acción.

## 6. Consecuencias

Las causas anteriores pueden producir:

- Mayor tiempo para localizar recursos potencialmente compatibles.
- Retrasos en la atención de solicitudes urgentes.
- Caducidad y desperdicio de unidades que podrían haberse redistribuido.
- Uso ineficiente del inventario regional y acumulación desigual entre instituciones.
- Traslados iniciados sin información completa o con tiempos poco viables.
- Conflictos por asignaciones simultáneas o por cambios de estado no sincronizados.
- Repetición de captura, verificaciones y comunicaciones.
- Dificultad para justificar prioridades, recomendaciones y decisiones.
- Pérdida de continuidad en la cadena de custodia.
- Reportes regulatorios incompletos o costosos de reconstruir.
- Exposición indebida de datos personales, clínicos, ubicaciones o fotografías.
- Menor confianza entre instituciones, personal, donantes y receptores.

Estas consecuencias no tienen la misma gravedad en todos los casos. Un retraso administrativo puede ser recuperable, mientras que una decisión basada en información incompatible, vencida o mal identificada puede tener efectos críticos. Por ello, el sistema deberá tratar la integridad, actualidad y trazabilidad de los datos como propiedades esenciales y no solamente como funciones administrativas.

## 7. Actores y perfiles de acceso

Para evitar una cantidad innecesaria de roles en un proyecto académico, la plataforma utilizará **siete perfiles consolidados**. El alcance regional o institucional se manejará como una restricción de acceso del perfil Administrador, no como dos roles distintos. De la misma forma, las tareas operativas del banco de sangre y la captura autorizada de pruebas se agrupan en un solo perfil, sin otorgarle facultades médicas que no le correspondan.

### 7.1 Perfiles consolidados del sistema

| Perfil | Responsabilidad principal | Acceso conceptual | Componente principal | Etapa prevista |
| --- | --- | --- | --- | --- |
| Administrador | Gestionar instituciones, usuarios, catálogos y configuración según su ámbito autorizado | Configuración regional o institucional; no decide asuntos clínicos | Web | Primer parcial |
| Operador de banco de sangre | Registrar y mantener unidades, movimientos, inventario y, posteriormente, pruebas autorizadas | Inventario y trazabilidad de las instituciones permitidas | Web y, posteriormente, escritorio | Primer parcial |
| Personal médico autorizado | Registrar solicitudes, interpretar información clínica y revisar resultados o candidatos | Expedientes y solicitudes expresamente autorizados | Web | Etapas posteriores |
| Coordinador regional | Coordinar solicitudes, asignaciones, disponibilidad y traslados | Vista regional minimizada, justificada y auditable | Web y, posteriormente, escritorio | Etapas posteriores |
| Personal de traslado | Confirmar recolección, custodia, ubicación y entrega del traslado asignado | Datos logísticos indispensables y temporales; sin información clínica innecesaria | Móvil | Etapas posteriores |
| Donante | Realizar su registro preliminar, consultar campañas, programar citas y recibir avisos | Información propia y contenido público autorizado | Móvil | Etapas posteriores |
| Auditor | Consultar evidencia, accesos y cambios sin modificar operaciones | Registros de auditoría autorizados y datos minimizados | Web | Primer parcial |

La consolidación no elimina los límites de responsabilidad. El Administrador no obtiene autoridad clínica; el Operador de banco de sangre solo ejecuta acciones autorizadas; el Personal médico conserva la revisión clínica; y el Auditor mantiene acceso de consulta sin capacidad de alterar las operaciones examinadas.

Los siete perfiles forman parte del alcance completo del proyecto. La etapa indicada en la tabla únicamente expresa cuándo se prevé habilitarlos y no convierte a los perfiles posteriores en elementos opcionales de la documentación funcional.

### 7.2 Perfiles que se implementarán en el primer parcial

El producto mínimo funcional habilitará únicamente los perfiles **Administrador**, **Operador de banco de sangre** y **Auditor**. Con ellos se demostrará el acceso diferenciado, la operación de catálogos, la gestión básica del inventario y la consulta de la bitácora. Los otros cuatro perfiles permanecerán documentados para incrementos posteriores y no necesitan cuentas, menús ni pantallas funcionales durante este parcial.

### 7.3 Participantes que no constituyen roles adicionales

- Los receptores o pacientes serán personas protegidas cuyos datos consultará únicamente personal autorizado. No tendrán acceso directo en el primer alcance.
- Los hospitales, bancos de sangre e instituciones participantes definirán el ámbito al que pertenecen los usuarios y los datos; no son perfiles de usuario.
- Las autoridades regulatorias podrán recibir los reportes que correspondan, pero no se define por ahora un acceso ordinario a la plataforma.
- El personal técnico y de soporte atenderá la infraestructura sin convertirse en un perfil funcional del negocio ni recibir acceso general a datos clínicos. Todo acceso excepcional deberá justificarse y auditarse.

## 8. Procesos actuales de referencia y límites del levantamiento

No se contó con acceso a expedientes, sistemas internos ni entrevistas con una institución participante. En consecuencia, los siguientes procesos representan un **modelo de referencia documental**, no una afirmación sobre la forma de trabajo de un hospital específico. Esta distinción evita inventar evidencia y permite avanzar académicamente con supuestos visibles.

### 8.1 Sangre y componentes sanguíneos

De forma general, el proceso comprende:

1. Promoción o convocatoria de la donación.
2. Registro e identificación del donante.
3. Evaluación y autorización por personal competente.
4. Recolección e identificación única de la donación.
5. Pruebas, procesamiento y separación de componentes cuando corresponda.
6. Liberación, almacenamiento y control de vigencia por personal autorizado.
7. Recepción de una solicitud y verificación de disponibilidad.
8. Selección y pruebas de compatibilidad conforme a procedimientos autorizados.
9. Reserva, entrega, traslado y confirmación de recepción.
10. Registro de uso, devolución, descarte, incidente o cierre según corresponda.

La plataforma académica solo apoyará los registros y controles que se definan expresamente. No decidirá si una persona puede donar ni si una unidad puede transfundirse.

### 8.2 Donación y trasplante de órganos

El proceso de referencia incluye identificación de un posible donante, consentimiento y evaluaciones autorizadas, registro de receptores candidatos, estudios de compatibilidad, revisión de criterios médicos, distribución o asignación por las autoridades y comités competentes, conservación, traslado y documentación del resultado. Este flujo depende de estructuras y registros oficiales y no debe tratarse como un inventario ordinario.

Durante el primer parcial este proceso permanecerá en el análisis y la arquitectura. No se implementará una asignación real ni una simulación que pueda confundirse con una regla oficial.

### 8.3 Coordinación interinstitucional que origina el problema

Como hipótesis de trabajo, una institución que no dispone de un recurso debe consultar a otras mediante los canales y sistemas que tenga disponibles. Si no existe una vista regional común, puede haber múltiples contactos, recaptura de información, estados desactualizados y dificultad para reconstruir tiempos y decisiones. Esta hipótesis explica la propuesta, pero deberá contrastarse con al menos un procedimiento o entrevista si el equipo obtiene acceso a una institución.

### 8.4 Aspectos que todavía requieren validación de campo

- Canales realmente utilizados entre instituciones y responsables de cada comunicación.
- Datos mínimos, identificadores y comprobantes exigidos en cada etapa.
- Estados y transiciones autorizadas para unidades, solicitudes, asignaciones y traslados.
- Excepciones, cancelaciones, correcciones y procedimientos de contingencia.
- Reportes, periodos de conservación e integraciones existentes.

Estos pendientes no bloquean el prototipo académico de inventario. Sí bloquean cualquier afirmación de que la plataforma está lista para operar en una institución real.

## 9. Información necesaria

La plataforma necesitará administrar, como mínimo conceptual, las siguientes categorías de información. Los campos concretos y su legitimidad deberán definirse posteriormente:

- Instituciones, sedes, capacidades, horarios y contactos operativos.
- Usuarios, perfiles, permisos, institución y estado de acceso.
- Identidad y datos autorizados de donantes y receptores.
- Consentimientos, restricciones y evidencias correspondientes.
- Campañas, citas y evaluaciones preliminares.
- Inventario, tipo de recurso, estado, ubicación y vigencia.
- Muestras, pruebas, estudios y resultados validados.
- Solicitudes, urgencia, tiempos, estado y responsables.
- Candidatos, factores considerados, versión de reglas y explicación del resultado.
- Reservas, asignaciones, autorizaciones, rechazos y cancelaciones.
- Rutas, traslados, personal, tiempos, ubicaciones y confirmaciones.
- Eventos de cadena de custodia.
- Archivos y evidencias con propietario, integridad, privacidad y retención.
- Alertas, notificaciones e incidentes.
- Eventos de auditoría y accesos a información sensible.

No toda esta información debe ser visible ni almacenarse de la misma forma. El diseño deberá aplicar minimización: capturar y mostrar solamente lo necesario para una finalidad autorizada.

Para esta etapa se utilizará la siguiente clasificación mínima, sin intentar definir todavía todos los campos:

| Categoría | Responsable conceptual | Sensibilidad | Uso permitido en el proyecto académico |
| --- | --- | --- | --- |
| Instituciones y catálogos | Administración regional o institucional | Interna | Datos ficticios para configuración y consultas |
| Usuarios, roles y permisos | Administración autorizada | Confidencial | Identidades ficticias y control de acceso demostrativo |
| Donantes y receptores | Institución responsable de la atención | Sensible | Datos completamente sintéticos |
| Inventario sanguíneo | Banco de sangre responsable | Sensible operacional | Registro, consulta, estados y auditoría del MVP |
| Pruebas y compatibilidad | Personal clínico o de laboratorio autorizado | Clínica sensible | Solo estructuras o valores marcados como demostrativos |
| Solicitudes y asignaciones | Institución solicitante y responsables autorizados | Clínica y operacional | Diseño documental; implementación posterior |
| Traslado, ubicación y fotografías | Coordinación del traslado | Sensible y temporal | Diseño documental; no captura real en el primer parcial |
| Auditoría | Operador autorizado de la plataforma | Confidencial | Evidencia ficticia de accesos y cambios del MVP |

La propiedad jurídica, los periodos de retención y las reglas de intercambio dependerán del tipo de institución y deberán confirmarse antes de una implementación real.

## 10. Decisiones que la plataforma debe apoyar

La solución deberá proporcionar información y cálculos para apoyar preguntas como:

- ¿Qué recursos se encuentran disponibles, vigentes y en condiciones de ser evaluados?
- ¿Qué candidatos cumplen las reglas de compatibilidad validadas?
- ¿Qué datos o pruebas faltan antes de continuar?
- ¿Qué solicitudes requieren atención inmediata?
- ¿Qué alternativas presentan una mejor combinación de urgencia, tiempo y distancia conforme a las reglas vigentes?
- ¿Es logísticamente viable el traslado dentro del periodo requerido?
- ¿Qué inventario está próximo a caducar y dónde existe demanda potencial?
- ¿Qué institución presenta faltantes o excedentes que justifican balanceo?
- ¿Qué registros o eventos presentan inconsistencias?
- ¿En qué etapa se encuentra un traslado y quién mantiene la custodia?

El resultado de estas funciones debe incluir explicaciones suficientes para que un usuario autorizado comprenda los factores considerados. Una puntuación sin desglose no es adecuada para un proceso de alto impacto.

## 11. Decisiones que deben permanecer bajo responsabilidad humana

La automatización no debe sustituir, al menos, las siguientes decisiones:

- Confirmar la elegibilidad clínica de un donante.
- Interpretar pruebas y determinar compatibilidad clínica definitiva.
- Establecer o modificar una urgencia clínica sin autorización.
- Aprobar una asignación cuando la normativa exija intervención profesional.
- Resolver excepciones, contraindicaciones o información contradictoria.
- Autorizar cambios que interrumpan o invaliden la cadena de custodia.
- Determinar el uso de un recurso ante escenarios no contemplados por las reglas.
- Decidir qué datos pueden compartirse fuera de la institución cuando exista duda legal o ética.

El sistema deberá registrar quién tomó la decisión, con qué rol, qué información estaba disponible, qué recomendación produjo el algoritmo y si la decisión humana coincidió o se apartó de ella. La justificación exigible deberá definirse según el proceso y la regulación.

## 12. Automatización pertinente

Sin sustituir las decisiones anteriores, existen actividades que pueden automatizarse o asistirse:

- Actualizar paneles regionales a partir de movimientos confirmados.
- Buscar recursos y candidatos conforme a reglas validadas.
- Generar rankings explicables.
- Detectar proximidad de caducidad, faltantes y excedentes.
- Calcular distancias o tiempos estimados con fuentes autorizadas.
- Enviar alertas y recordatorios a responsables.
- Evitar reservas o asignaciones concurrentes incompatibles.
- Validar integridad, obligatoriedad y consistencia de datos.
- Detectar duplicados, secuencias imposibles o estados contradictorios.
- Generar etiquetas, comprobantes y reportes.
- Registrar automáticamente eventos técnicos y de auditoría.
- Escalar incidentes cuando una dependencia o microservicio no esté disponible.

Cada automatización deberá tener condiciones de activación, destinatarios, tolerancias, reintentos, caducidad y mecanismo de revisión definidos.

## 13. Alcance conceptual de la solución

La solución comprenderá:

- Una red de instituciones autorizadas.
- Registro y gestión de donantes y receptores.
- Inventarios regionales diferenciados por tipo de recurso.
- Solicitudes ordinarias y urgentes.
- Captura y consulta de pruebas y estudios.
- Compatibilidad y priorización como apoyo explicable.
- Asignación bajo control humano autorizado.
- Traslado y cadena de custodia.
- Campañas y citas para donantes.
- Alertas, notificaciones, paneles y reportes.
- Evidencias, auditoría y control de acceso.
- Pronóstico de caducidad, balanceo de inventario y detección de inconsistencias.

En términos de productos, este alcance se distribuirá entre el sistema web empresarial, el módulo independiente de microservicios, la aplicación móvil Android y la aplicación de escritorio. La arquitectura definirá sus límites e integración, pero los cuatro productos pertenecen a la visión completa aunque no se implementen simultáneamente.

Este alcance no implica que todas las funciones tengan la misma prioridad ni que deban implementarse simultáneamente. Para el ejercicio académico, la delimitación del primer incremento se establece a continuación y no pretende adelantar reglas clínicas pendientes.

### 13.1 Alcance viable del primer parcial

Para evitar que el alcance total impida entregar una base funcional, el primer parcial se concentrará en el sistema web y en un proceso de bajo riesgo clínico: **gestión inicial del inventario de componentes sanguíneos**.

El incremento deberá demostrar, como mínimo:

- Página pública, inicio y cierre de sesión, roles iniciales, menú diferenciado y panel principal básico para cada uno de los perfiles iniciales, limitado a la información y los accesos del primer parcial.
- Dos catálogos funcionales: instituciones —administradas como entidades y reutilizadas como catálogo de referencia— y tipos de componentes sanguíneos.
- Registro de una unidad ficticia con identificador único, institución, tipo, fechas y estado.
- Consulta del inventario con búsqueda o filtros básicos.
- Cambio controlado de estado y señalamiento de unidades próximas a caducar mediante una regla demostrativa configurable, sin presentarla como norma clínica.
- Persistencia real en PostgreSQL y registro básico de auditoría.
- Ejecución local reproducible mediante dependencias y variables documentadas, con PostgreSQL como almacenamiento real del incremento.

Durante el primer parcial, MongoDB, Redis y los contenedores Docker se abordarán únicamente mediante investigación introductoria y dentro de la arquitectura objetivo del semestre. Su instalación, configuración, diseño detallado y uso funcional comenzarán en el segundo parcial.

El primer parcial **no** incluirá matching clínico, HLA, ranking, asignación de órganos, optimización geográfica, seguimiento móvil, aplicación de escritorio ni integración real con hospitales. Esos elementos permanecerán documentados en el análisis, los requisitos, las historias de usuario y la arquitectura general, y se incorporarán gradualmente cuando existan requisitos y reglas suficientemente validados.

Esta delimitación no elimina el alcance total del proyecto académico. Establece una secuencia viable: primero identidad, acceso, catálogos, persistencia, inventario y auditoría; después solicitudes, compatibilidad, asignación, traslado y clientes adicionales.

## 14. Exclusiones y límites iniciales

Hasta contar con validación expresa, se consideran fuera del alcance o no asumidos:

- Diagnóstico médico o recomendación terapéutica autónoma.
- Sustitución de comités, autoridades o profesionales responsables.
- Declaración automática de elegibilidad definitiva.
- Reglas clínicas o normativas inventadas por el equipo de desarrollo.
- Garantía de compatibilidad basada únicamente en una puntuación informática.
- Acceso público a inventarios detallados, identidad o datos clínicos.
- Seguimiento permanente de ubicación fuera de un traslado autorizado.
- Almacenamiento o reutilización de fotografías sin finalidad y consentimiento definidos.
- Integración con sistemas externos específicos que todavía no hayan sido identificados.
- Operación sanitaria real mientras no se definan la región, las instituciones participantes y sus obligaciones específicas.

## 15. Diferencias que deben preservarse entre sangre y órganos

Aunque una plataforma común aporta coordinación, el análisis y el diseño posteriores deberán separar:

- Tipos de recurso y unidades de inventario.
- Reglas de compatibilidad y pruebas aplicables.
- Formas de obtención, conservación y traslado.
- Ventanas de uso, caducidad o viabilidad.
- Estados del proceso y participantes autorizados.
- Criterios y autoridades de priorización y asignación.
- Evidencias requeridas y eventos de cadena de custodia.
- Consentimientos, confidencialidad y retención.
- Manejo de cancelaciones, descartes e incidentes.

Compartir infraestructura o componentes no significa compartir todas las reglas. Cuando una abstracción común oculte una diferencia crítica, deberán existir flujos y modelos especializados.

## 16. Riesgos del negocio y de la operación

| Riesgo | Posible impacto | Tratamiento esperado |
| --- | --- | --- |
| Inventario desactualizado | Búsqueda o reserva de un recurso ya no disponible | Estados transaccionales, confirmaciones, bloqueo de operaciones concurrentes y alertas de desactualización |
| Compatibilidad calculada con datos incompletos | Candidatos incorrectos o retrasos | Validación de datos mínimos, identificación de faltantes y revisión humana |
| Regla clínica incorrecta o antigua | Priorización o recomendación inadecuada | Reglas validadas, versionadas, probadas, fechadas y auditables |
| Asignación simultánea | Conflicto entre instituciones y pérdida de tiempo | Reserva atómica, control de concurrencia e idempotencia |
| Pérdida de cadena de custodia | Recurso no verificable o reporte incompleto | Identificación única, escaneo, eventos ordenados, responsables y evidencia íntegra |
| Retraso o falla del traslado | Pérdida de viabilidad y atención tardía | Seguimiento, tiempos límite, alertas, contingencias y escalamiento |
| Exposición de datos sensibles | Daño a personas, incumplimiento y pérdida de confianza | Mínimo privilegio, segregación institucional, cifrado, auditoría y minimización |
| Ubicación o fotografía usada fuera de finalidad | Riesgo de privacidad y seguridad personal | Consentimiento, acceso temporal, retención limitada y registro de acceso |
| Dependencia tecnológica caída | Interrupción parcial del proceso | Health checks, degradación controlada, reintentos seguros y recuperación |
| Alertas excesivas o tardías | Fatiga de alertas o falta de reacción | Clasificación, responsables, deduplicación, escalamiento y métricas |
| Algoritmo opaco o sesgado | Decisiones difíciles de justificar o inequidad | Explicaciones, revisión de variables, métricas, auditoría y capacidad de anulación humana |
| Confusión entre reglas de sangre y órganos | Flujo o decisión inadecuada | Modelos y reglas separados con validaciones específicas |

## 17. Restricciones legales, éticas y de privacidad por validar

Para dar una base concreta al ejercicio sin convertirlo en asesoría legal, se adopta **México como jurisdicción académica provisional**. La región exacta, las instituciones participantes y la naturaleza pública o privada de cada una todavía deberán confirmarse.

La revisión documental realizada el 31 de agosto de 2026 identificó como referencias principales:

- La Ley General de Salud vigente y el Reglamento de la Ley General de Salud en Materia de Trasplantes reconocen autoridades, comités, registros y responsabilidades humanas específicas para donación y trasplantes (Cámara de Diputados del H. Congreso de la Unión, 2026; Diario Oficial de la Federación, 2014).
- La plataforma oficial de normalización reporta la NOM-253-SSA1-2012 como vigente para sangre humana y sus componentes. Cualquier proyecto de actualización deberá identificarse como tal y no como norma vigente mientras no complete el proceso correspondiente (Secretaría de Economía, s. f.).
- La Ley Federal de Protección de Datos Personales en Posesión de los Particulares y la Ley General de Protección de Datos Personales en Posesión de Sujetos Obligados se consideraron porque la red podría involucrar instituciones privadas y públicas (Cámara de Diputados del H. Congreso de la Unión, 2025a, 2025b).
- La información institucional del Centro Nacional de Trasplantes confirma la existencia de redes, comités y procedimientos institucionales que una plataforma académica no puede sustituir (Centro Nacional de Trasplantes, 2016).

Estas fuentes permiten justificar controles generales, pero no autorizan al equipo a traducir por su cuenta el marco normativo en reglas clínicas. Antes de una implementación real deberán validarse, como mínimo:

- Requisitos para tratamiento y transferencia interinstitucional de datos personales y clínicos.
- Bases legales y consentimiento para registro de donantes, ubicación, fotografías y comunicaciones.
- Autoridades responsables de compatibilidad, prioridad, asignación y liberación de recursos.
- Reglas de anonimización o seudonimización entre donantes y receptores.
- Periodos de conservación, bloqueo, eliminación y disponibilidad para auditoría.
- Requisitos de trazabilidad, cadena de custodia, firmas, etiquetas y evidencias.
- Obligaciones de notificación ante incidentes de seguridad o pérdida de información.
- Reglas de acceso de auditores, reguladores, soporte e instituciones distintas a la propietaria.
- Condiciones para intercambiar datos fuera de la región o con sistemas externos.
- Requisitos de continuidad, respaldo y recuperación para información crítica.

Esta validación deberá involucrar especialistas clínicos, responsables de bancos de sangre, coordinación de trasplantes, privacidad, seguridad y asesoría jurídica o regulatoria competente.

## 18. Beneficios esperados

Si se implementa y adopta correctamente, la plataforma puede aportar:

- Mayor visibilidad de disponibilidad regional para usuarios autorizados.
- Reducción del tiempo necesario para localizar alternativas compatibles.
- Atención más ordenada y trazable de solicitudes urgentes.
- Disminución de pérdidas por caducidad mediante alertas y redistribución oportuna.
- Mejor balance de inventarios entre instituciones.
- Menos duplicidad de captura y comunicaciones manuales.
- Mayor consistencia en la aplicación de reglas previamente validadas.
- Decisiones más explicables gracias al registro de factores y versiones.
- Mejor seguimiento de traslados y cadena de custodia.
- Auditorías y reportes regulatorios sustentados en evidencia íntegra.
- Detección temprana de inconsistencias y fallos operativos.

Estos beneficios son resultados esperados y no garantías. Su cumplimiento deberá medirse con una línea base y datos posteriores a la adopción.

## 19. Indicadores para evaluar el problema y la mejora

Antes de implementar, deberán obtenerse valores de referencia. Algunos indicadores candidatos son:

- Tiempo desde el registro de una solicitud hasta la identificación de candidatos.
- Tiempo desde la solicitud hasta la asignación autorizada.
- Tiempo desde la asignación hasta la recolección y entrega.
- Porcentaje de solicitudes atendidas, canceladas y vencidas.
- Unidades descartadas por caducidad, por institución y periodo.
- Recursos redistribuidos antes de caducar.
- Diferencia de inventario y disponibilidad entre instituciones.
- Porcentaje de registros con datos o pruebas incompletas.
- Número de conflictos por reservas o asignaciones simultáneas.
- Eventos de cadena de custodia faltantes o registrados fuera de tiempo.
- Recomendaciones aceptadas, rechazadas o anuladas y sus motivos.
- Incidentes de acceso no autorizado o exposición de datos.
- Disponibilidad de servicios y tiempo de recuperación ante fallos.
- Tiempo de respuesta de búsquedas, matching, ranking y paneles.
- Tasa de alertas atendidas, ignoradas, duplicadas o vencidas.

Las metas cuantitativas se establecerán posteriormente con datos reales y acuerdos institucionales. No deben elegirse cifras arbitrarias solamente para completar el documento.

## 20. Resultado de la validación del análisis

La estructura del análisis se revisó considerando la separación entre necesidades del negocio y requisitos del sistema propuesta por ISO/IEC/IEEE 29148 (International Organization for Standardization, 2018). La cobertura conceptual se evaluó para el proyecto académico completo; la calidad y verificabilidad de los requisitos funcionales y no funcionales se revisarán posteriormente con apoyo del modelo de calidad de ISO/IEC 25010 (International Organization for Standardization, 2023).

| Dimensión revisada | Resultado | Límite reconocido |
| --- | --- | --- |
| Coherencia con la consigna | Suficiente para continuar | Debe conservar trazabilidad hacia requisitos, historias y pruebas |
| Comprensión del problema | Suficiente como línea base académica | La situación de una institución concreta no fue observada directamente |
| Actores y responsabilidades | Suficiente como línea base del proyecto académico completo | La matriz detallada de permisos y la validación regulatoria permanecen pendientes |
| Procesos de sangre y órganos | Diferenciados correctamente a nivel conceptual | No se han validado procedimientos clínicos detallados |
| Cobertura funcional total | Identificada a nivel conceptual | Debe derivarse en requisitos, historias y trazabilidad por componente y fase |
| Alcance del primer parcial | Viable y demostrable | Se limita a inventario sanguíneo básico y auditoría |
| Restricciones legales y éticas | Identificadas documentalmente para México | No constituye dictamen de cumplimiento ni asesoría jurídica |
| Reglas clínicas y algoritmos | Deliberadamente no validados | No deben implementarse como reglas reales |

El análisis queda **validado como base académica para revisar y derivar los requisitos funcionales y no funcionales de todo el proyecto**. Estos deberán abarcar la solución objetivo, clasificarse por componente y fase, y distinguir el subconjunto que se implementará durante el primer parcial. Los procesos clínicos y algorítmicos permanecen dentro del alcance documental, aunque su implementación como reglas aplicables estará condicionada a la validación correspondiente. El análisis no queda validado para despliegue sanitario real.

## 21. Conclusión

El proyecto aborda un problema de coordinación regional de alto impacto, donde la oportunidad de la información es tan importante como su exactitud, privacidad y trazabilidad. La dificultad no se limita a consolidar inventarios: es necesario relacionar solicitudes, compatibilidad, prioridad, distancia, caducidad, traslado, autorizaciones y cadena de custodia sin confundir una recomendación informática con una decisión clínica.

Una solución adecuada deberá proporcionar información regional confiable, reglas explicables y evidencia completa, al mismo tiempo que limita el acceso según institución, rol y recurso. También deberá preservar las diferencias entre sangre y órganos, manejar fallos parciales y evitar que la presión de una urgencia elimine controles esenciales.

La revisión permite avanzar sin fingir un nivel de certeza que el proyecto académico no posee. El primer parcial puede demostrar una base sólida mediante autenticación, roles, catálogos, inventario sanguíneo ficticio, persistencia y auditoría, mientras la arquitectura conserva la visión regional completa.

El siguiente paso es revisar y derivar los requisitos funcionales y no funcionales de todo el proyecto, clasificándolos por componente, prioridad y fase, y señalando cuáles integrarán el primer parcial. Los procesos de compatibilidad, priorización, órganos, traslados y decisiones clínicas continuarán documentados como parte de la solución completa, aunque la implementación de sus reglas quedará condicionada a fuentes, validaciones y responsables autorizados.

## 22. Referencias

Las referencias se presentan en formato APA 7.ª edición. Se utilizaron para comprender responsabilidades y restricciones generales, no para derivar reglas clínicas por cuenta del equipo.

Cámara de Diputados del H. Congreso de la Unión. (2025a). *Ley Federal de Protección de Datos Personales en Posesión de los Particulares* (texto vigente; última reforma publicada el 14 de noviembre de 2025). [https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf](https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf)

Cámara de Diputados del H. Congreso de la Unión. (2025b). *Ley General de Protección de Datos Personales en Posesión de Sujetos Obligados* (texto vigente; última reforma publicada el 14 de noviembre de 2025). [https://www.diputados.gob.mx/LeyesBiblio/pdf/LGPDPPSO.pdf](https://www.diputados.gob.mx/LeyesBiblio/pdf/LGPDPPSO.pdf)

Cámara de Diputados del H. Congreso de la Unión. (2026). *Ley General de Salud* (texto vigente; últimas reformas publicadas el 15 de enero de 2026). [https://www.diputados.gob.mx/LeyesBiblio/pdf/LGS.pdf](https://www.diputados.gob.mx/LeyesBiblio/pdf/LGS.pdf)

Centro Nacional de Trasplantes. (2016, 22 de julio). *Distribución y asignación de órganos y tejidos*. Gobierno de México. [https://www.gob.mx/cenatra/acciones-y-programas/distribucion-y-asignacion-de-organos-y-tejidos](https://www.gob.mx/cenatra/acciones-y-programas/distribucion-y-asignacion-de-organos-y-tejidos)

Diario Oficial de la Federación. (2014, 26 de marzo). *Reglamento de la Ley General de Salud en Materia de Trasplantes*. [https://dof.gob.mx/nota_detalle.php?codigo=5338349&fecha=26/03/2014](https://dof.gob.mx/nota_detalle.php?codigo=5338349&fecha=26/03/2014)

International Organization for Standardization. (2018). *Systems and software engineering—Life cycle processes—Requirements engineering* (ISO/IEC/IEEE Standard No. 29148:2018). [https://www.iso.org/standard/72089.html](https://www.iso.org/standard/72089.html)

International Organization for Standardization. (2023). *Systems and software engineering—Systems and software Quality Requirements and Evaluation (SQuaRE)—Product quality model* (ISO/IEC Standard No. 25010:2023). [https://www.iso.org/standard/78176.html](https://www.iso.org/standard/78176.html)

Organización Mundial de la Salud. (s. f.-a). *Blood transfusion safety*. Recuperado el 31 de agosto de 2026, de [https://www.who.int/health-topics/blood-transfusion-safety](https://www.who.int/health-topics/blood-transfusion-safety)

Organización Mundial de la Salud. (s. f.-b). *Digital health*. Recuperado el 31 de agosto de 2026, de [https://www.who.int/health-topics/digital-health](https://www.who.int/health-topics/digital-health)

Organización Mundial de la Salud. (s. f.-c). *Transplantation*. Recuperado el 31 de agosto de 2026, de [https://www.who.int/health-topics/transplantation](https://www.who.int/health-topics/transplantation)

Organización Mundial de la Salud. (2026, 12 de junio). *Blood safety and availability*. [https://www.who.int/news-room/fact-sheets/detail/blood-safety-and-availability](https://www.who.int/news-room/fact-sheets/detail/blood-safety-and-availability)

Organización Mundial de la Salud, Oficina Regional para Europa. (2025, 20 de marzo). *Health data governance in the age of artificial intelligence: Policy imperatives for the WHO European Region*. [https://www.who.int/europe/publications/i/item/WHO-EURO-2025-11462-51234-78079](https://www.who.int/europe/publications/i/item/WHO-EURO-2025-11462-51234-78079)

Secretaría de Economía. (s. f.). *NOM-253-SSA1-2012: Para la disposición de sangre humana y sus componentes con fines terapéuticos*. Recuperado el 31 de agosto de 2026, de [https://platiica.economia.gob.mx/normalizacion/nom-253-ssa1-2012/](https://platiica.economia.gob.mx/normalizacion/nom-253-ssa1-2012/)

Las reglas específicas deberán obtenerse y validarse posteriormente con autoridades, normas vigentes y especialistas competentes. El equipo deberá volver a comprobar la vigencia de estas referencias antes de una entrega futura que dependa de ellas.
