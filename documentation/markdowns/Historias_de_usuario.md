# Historias de usuario

> **Proyecto:** Red regional de bancos de sangre y donación de órganos — Equipo 01.  
> **Estado:** borrador consolidado para validación académica.  
> **Fecha:** 7 de septiembre de 2026.  
> **Cobertura:** proyecto académico completo, con implementación gradual por parciales e incrementos.

## 1. Propósito y alcance

Este documento define las historias de usuario de la solución completa a partir del análisis del problema y de los requerimientos funcionales y no funcionales consolidados. Las historias se agrupan por componente y por flujo de valor; no existe una correspondencia obligatoria de una historia por cada requerimiento.

La fase **Primer parcial** identifica el subconjunto inicial del sistema web. Las historias **Posteriores** continúan dentro del alcance del proyecto y deberán considerarse en la arquitectura, los datos y la planeación aunque todavía no estén implementadas. Las historias **Transversales** se incorporarán gradualmente en todos los incrementos a los que correspondan.

La plataforma será una herramienta de coordinación y apoyo. Ninguna historia autoriza que el sistema sustituya la evaluación médica, ética o normativa, ni que invente reglas de compatibilidad, elegibilidad, urgencia, conservación, priorización o asignación. Hasta contar con fuentes y validaciones autorizadas, los datos y las reglas utilizados en demostraciones serán ficticios y se identificarán como demostrativos.

## 2. Convenciones

### 2.1 Tipos de elementos

| Código | Tipo | Uso |
| --- | --- | --- |
| HU | Historia de usuario | Expresa un resultado valioso para una persona o perfil autorizado. |
| HE | Historia habilitadora | Expresa una capacidad técnica necesaria para entregar y verificar las historias de usuario. |

Las historias habilitadoras se utilizan para arquitectura, contratos, datos, infraestructura, seguridad y calidad. De esta forma, los requisitos técnicos permanecen trazables sin presentar al sistema, a una base de datos o a un “arquitecto” como usuario final del negocio.

### 2.2 Clasificaciones

| Clasificación | Valores utilizados |
| --- | --- |
| Fase | Primer parcial, Posterior o Transversal |
| Prioridad | Alta o Media |
| Validación | Técnica, Demostrativa o Clínica/normativa |
| Componente | Sistema web, Microservicios, Aplicación móvil, Aplicación de escritorio, Bases de datos, Infraestructura, Seguridad o Monitoreo |

### 2.3 Criterios transversales

Además de los criterios particulares de cada historia, se aplicarán los siguientes cuando correspondan:

1. Cada operación protegida deberá comprobar la identidad, el perfil, la acción, el recurso y el ámbito institucional del usuario.
2. Los cambios deberán persistirse realmente y las operaciones críticas deberán dejar evidencia auditable con actor, fecha, acción, entidad y resultado.
3. Los mensajes de error deberán ser comprensibles y no revelar datos personales o clínicos, secretos, tokens ni detalles internos.
4. Los procesos de sangre y los de órganos conservarán datos, estados, reglas y validaciones diferenciados.
5. Los resultados de compatibilidad, priorización, pronóstico o recomendación mostrarán su procedencia y requerirán la intervención humana autorizada que corresponda.
6. Los criterios clínicos o regulatorios pendientes no se considerarán aceptados por estar escritos en este documento; deberán validarse antes de utilizarse con fines distintos de una demostración académica.

## 3. Sistema web empresarial

### Épica WEB-01 — Acceso e identidad

### HU-WEB-001 — Consultar el sitio público

| Campo | Valor |
| --- | --- |
| Fase | Primer parcial |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Público general (sin perfil de acceso) |
| Requerimientos relacionados | RF-WEB-001 |

**Historia:** Como visitante, quiero consultar información pública sobre la red y sus medios de contacto, para comprender el propósito de la plataforma sin acceder a información restringida.

**Criterios de aceptación**

1. La página pública explica el propósito académico de la red y presenta únicamente contenido autorizado.
2. El visitante puede llegar al inicio de sesión desde la navegación pública.
3. La página no muestra inventarios detallados ni datos personales, clínicos, logísticos o de auditoría.
4. El contenido puede consultarse desde los tamaños de pantalla definidos para la demostración.

### HU-WEB-002 — Acceder de forma segura a la plataforma

| Campo | Valor |
| --- | --- |
| Fase | Transversal: inicio y cierre en el primer parcial; recuperación posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Primer parcial: Administrador; Operador de banco de sangre; Auditor. Posteriormente: Personal médico autorizado; Coordinador regional; Personal de traslado; Donante |
| Requerimientos relacionados | RF-WEB-002, RF-SEC-001, RF-SEC-003 |

**Historia:** Como usuario registrado, quiero iniciar sesión, cerrar sesión y recuperar mi acceso cuando corresponda, para utilizar únicamente las funciones autorizadas de mi perfil.

**Criterios de aceptación**

1. Una credencial válida y activa inicia una sesión y conduce al panel permitido para el perfil y ámbito del usuario.
2. Una credencial inválida, una cuenta inactiva o una sesión expirada produce un mensaje genérico y no concede acceso.
3. El cierre de sesión invalida la sesión o los tokens definidos y evita reutilizarlos en operaciones protegidas.
4. Los intentos relevantes de autenticación y el cierre de sesión quedan registrados sin almacenar contraseñas ni tokens completos.
5. En el incremento posterior, la recuperación utiliza un mecanismo temporal, de un solo uso y auditable que no revela si una cuenta existe.

### HU-WEB-003 — Administrar usuarios, perfiles y ámbitos

| Campo | Valor |
| --- | --- |
| Fase | Primer parcial |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Administrador |
| Requerimientos relacionados | RF-WEB-003, RF-SEC-002 |

**Historia:** Como Administrador, quiero gestionar usuarios y asignarles perfiles y ámbitos institucionales, para que cada persona acceda solo a las responsabilidades que le corresponden.

**Criterios de aceptación**

1. El Administrador puede crear, consultar, actualizar, activar o desactivar cuentas dentro de su propio ámbito.
2. Los siete perfiles permanecen definidos para el alcance completo; durante el primer parcial solo pueden asignarse y habilitarse funcionalmente Administrador, Operador de banco de sangre y Auditor.
3. En incrementos posteriores, la asignación de un perfil clínico no sustituye la acreditación o autorización profesional que deba validarse por separado.
4. El menú y las operaciones visibles cambian conforme al perfil y al ámbito institucional vigentes.
5. Un usuario fuera de ámbito recibe una denegación segura aunque conozca la dirección o el identificador del recurso.
6. Las altas, bajas y cambios de perfil o ámbito quedan auditados.

### Épica WEB-02 — Configuración de la red

### HU-WEB-004 — Mantener catálogos y parámetros autorizados

| Campo | Valor |
| --- | --- |
| Fase | Primer parcial |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Administrador |
| Requerimientos relacionados | RF-WEB-004 |

**Historia:** Como Administrador, quiero mantener catálogos y parámetros autorizados, para que las operaciones utilicen valores consistentes y controlados.

**Criterios de aceptación**

1. El primer parcial ofrece al menos los catálogos funcionales de instituciones y tipos de componentes sanguíneos; las instituciones se obtienen de la entidad administrada en HU-WEB-005 como fuente conceptual única.
2. Cada catálogo permite las operaciones autorizadas de alta, consulta, actualización y cambio de estado con persistencia real.
3. Se validan los campos obligatorios, la unicidad definida y las referencias activas antes de guardar.
4. Un valor que ya tiene historial no se elimina de forma que rompa registros anteriores; se inactiva cuando corresponda.
5. Todo cambio conserva fecha, responsable y valores necesarios para auditoría.
6. Los parámetros demostrativos se identifican como tales y no se presentan como reglas clínicas válidas.

### HU-WEB-005 — Administrar instituciones participantes

| Campo | Valor |
| --- | --- |
| Fase | Primer parcial |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Administrador |
| Requerimientos relacionados | RF-WEB-005 |

**Historia:** Como Administrador, quiero registrar y mantener las instituciones y sedes participantes, para representar quiénes integran la red y cuáles son sus capacidades declaradas.

**Criterios de aceptación**

1. Se registran los datos institucionales, tipo, ubicación, contactos, capacidades declaradas y estado de participación definidos para el incremento; este registro es la fuente conceptual única utilizada como catálogo de referencia por los demás procesos.
2. El sistema detecta posibles duplicados mediante los identificadores y reglas administrativas acordadas.
3. Solo un Administrador con el ámbito correspondiente puede modificar o desactivar una institución.
4. Desactivar una institución no elimina su historial ni sus relaciones anteriores.
5. Las consultas permiten buscar y filtrar por los datos y estados autorizados.
6. Las modificaciones quedan auditadas.

### Épica WEB-03 — Personas y procesos de donación

### HU-WEB-006 — Mantener el expediente autorizado de un donante

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Operador de banco de sangre; Personal médico autorizado |
| Requerimientos relacionados | RF-WEB-006, RF-MS-001 |

**Historia:** Como Operador de banco de sangre o Personal médico autorizado, quiero registrar y actualizar la información permitida de un donante, para dar seguimiento a su participación sin atribuir al sistema decisiones de elegibilidad.

**Criterios de aceptación**

1. El formulario diferencia el tipo de donación y solicita únicamente los datos, consentimientos, restricciones y estados aprobados para ese proceso.
2. Los campos obligatorios y posibles duplicados se validan antes de guardar.
3. La información sensible solo es visible para perfiles y ámbitos autorizados.
4. Una actualización conserva responsable, fecha e historial suficiente para reconstruir el cambio.
5. El sistema no declara elegible a una persona por sí mismo; registra o muestra la decisión emitida por personal autorizado.
6. Las diferencias entre donación de sangre y donación de órganos no se reducen a un único flujo genérico.

### HU-WEB-007 — Mantener el expediente autorizado de un receptor

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Personal médico autorizado |
| Requerimientos relacionados | RF-WEB-007, RF-MS-001 |

**Historia:** Como Personal médico autorizado, quiero registrar y actualizar receptores y su participación en procesos o listas autorizadas, para gestionar sus necesidades con información vigente y protegida.

**Criterios de aceptación**

1. Se registran únicamente los datos de identificación, atención, necesidad, institución y estado definidos y autorizados para el proceso.
2. La urgencia y cualquier condición clínica son capturadas o confirmadas por personal autorizado, no inferidas por el sistema.
3. Los procesos de sangre y de órganos presentan campos, estados y validaciones diferenciados.
4. El receptor no obtiene una cuenta de acceso por el solo hecho de ser registrado.
5. Los cambios conservan autor, fecha, motivo cuando corresponda e historial auditable.
6. Una consulta fuera del ámbito autorizado se deniega y no revela la existencia del expediente.

### Épica WEB-04 — Inventario regional

### HU-WEB-008 — Gestionar inventario sanguíneo y caducidad demostrativa

| Campo | Valor |
| --- | --- |
| Fase | Primer parcial |
| Prioridad | Alta |
| Validación | Demostrativa |
| Usuario | Operador de banco de sangre |
| Requerimientos relacionados | RF-WEB-008, RF-MS-002 |

**Historia:** Como Operador de banco de sangre, quiero registrar, consultar y actualizar unidades sanguíneas ficticias, para conocer el inventario disponible y demostrar su trazabilidad y control de caducidad.

**Criterios de aceptación**

1. Cada unidad recibe un identificador de trazabilidad único y conserva el tipo de componente, los datos temporales, la ubicación y el estado definidos para el MVP.
2. Las consultas permiten búsqueda, filtros y paginación por institución, componente, estado y proximidad de caducidad.
3. Solo se permiten transiciones de estado configuradas y cada transición conserva responsable, fecha y motivo cuando aplique.
4. La proximidad de caducidad se calcula con un parámetro demostrativo visible y configurable, no con una regla presentada como criterio médico oficial.
5. Una unidad vencida o dada de baja no aparece como disponible para nuevas operaciones.
6. El alta y los cambios se guardan en PostgreSQL y producen evidencia básica de auditoría.

### HU-WEB-009 — Gestionar disponibilidad y viabilidad de órganos por separado

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Personal médico autorizado |
| Requerimientos relacionados | RF-WEB-009, RF-MS-002 |

**Historia:** Como Personal médico autorizado, quiero consultar y mantener la disponibilidad y viabilidad documentada de órganos mediante un flujo especializado, para evitar aplicarles el ciclo ordinario del inventario sanguíneo.

**Criterios de aceptación**

1. El flujo distingue órganos de unidades sanguíneas en datos, estados, tiempos y responsables.
2. Solo se capturan criterios de conservación o viabilidad provenientes de reglas autorizadas y versionadas.
3. El sistema muestra la procedencia, la hora de actualización y los datos faltantes relevantes.
4. Ningún cambio de disponibilidad equivale por sí mismo a una asignación o autorización clínica.
5. Los cambios quedan limitados al ámbito permitido y se registran para auditoría.

### Épica WEB-05 — Solicitudes, estudios y asignación

### HU-WEB-010 — Registrar y dar seguimiento a una solicitud

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Personal médico autorizado |
| Requerimientos relacionados | RF-WEB-010 |

**Historia:** Como Personal médico autorizado, quiero registrar y consultar solicitudes ordinarias o urgentes, para coordinar la atención de una necesidad documentada.

**Criterios de aceptación**

1. La solicitud conserva folio, receptor, institución solicitante, necesidad, responsable, fecha y urgencia autorizada.
2. El flujo y los datos obligatorios se diferencian entre sangre y órganos.
3. Una solicitud incompleta no avanza a evaluación y el sistema indica qué información falta.
4. La urgencia es registrada o confirmada por personal autorizado y no se deduce automáticamente de datos parciales.
5. Los cambios de estado siguen las transiciones definidas y conservan su historial.
6. El registro y los cambios críticos generan auditoría y las notificaciones configuradas.

### HU-WEB-011 — Capturar y consultar pruebas o estudios

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Operador de banco de sangre; Personal médico autorizado |
| Requerimientos relacionados | RF-WEB-011 |

**Historia:** Como Operador de banco de sangre o Personal médico autorizado, quiero capturar y consultar pruebas y estudios, para que el proceso utilice resultados identificables y revisables.

**Criterios de aceptación**

1. Cada resultado conserva tipo de prueba o estudio, sujeto o recurso relacionado, responsable, fecha, estado y fuente definida.
2. Los campos y validaciones aplicables a sangre se mantienen separados de los correspondientes a órganos y tejidos.
3. Los resultados incompletos, contradictorios o pendientes se muestran con su estado y no se presentan como confirmados.
4. La modificación o corrección conserva el resultado anterior, la justificación y el responsable.
5. Capturar un resultado no autoriza automáticamente una disponibilidad, compatibilidad o asignación.
6. El acceso y los cambios se auditan conforme a su sensibilidad.

### HU-WEB-012 — Autorizar y controlar una asignación

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Coordinador regional |
| Requerimientos relacionados | RF-WEB-013 |

**Historia:** Como Coordinador regional con la autorización humana requerida, quiero reservar, asignar, liberar, cancelar o reasignar un recurso, para coordinar su uso sin duplicidades y con una decisión transparente.

**Criterios de aceptación**

1. Antes de confirmar se muestran la solicitud, el recurso, el resultado de apoyo disponible, los datos faltantes y las advertencias aplicables.
2. La asignación exige confirmación de la persona autorizada y conserva decisión, responsable, fecha y justificación.
3. Una transacción, restricción o bloqueo impide que el mismo recurso quede asignado simultáneamente a más de una solicitud.
4. Liberar, cancelar o reasignar requiere una transición válida y un motivo; no sobrescribe la decisión anterior.
5. El cálculo que apoyó la decisión permanece sin alteración y se vincula con la aceptación, rechazo o excepción humana.
6. Las instituciones y personas involucradas reciben las notificaciones autorizadas y la operación queda auditada.

### Épica WEB-06 — Supervisión, documentos y auditoría

### HU-WEB-013 — Consultar un panel acorde con el perfil

| Campo | Valor |
| --- | --- |
| Fase | Transversal: panel inicial en el primer parcial y regional posteriormente |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Primer parcial: Administrador; Operador de banco de sangre; Auditor. Posteriormente: Personal médico autorizado; Coordinador regional |
| Requerimientos relacionados | RF-WEB-015 |

**Historia:** Como usuario autorizado, quiero consultar un panel y mis notificaciones conforme a mi perfil, para identificar el estado de las tareas que debo atender.

**Criterios de aceptación**

1. El panel muestra únicamente indicadores, accesos y notificaciones permitidos por el perfil y el ámbito institucional.
2. En el primer parcial, el panel principal básico de los perfiles iniciales presenta datos persistidos del inventario sanguíneo ficticio, catálogos y operaciones auditadas.
3. En incrementos posteriores evoluciona a una vista regional con solicitudes, caducidades, traslados y desempeño autorizado.
4. En la evolución regional, las gráficas se elaboran con Highcharts y sus valores pueden contrastarse con la consulta que los origina.
5. En incrementos posteriores, las notificaciones permiten distinguir al menos pendientes y leídas sin alterar el hecho que las produjo.
6. Un dato inexistente o no disponible se indica expresamente y no se reemplaza con cifras simuladas no identificadas.

### HU-WEB-014 — Generar reportes autorizados

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Media |
| Validación | Clínica/normativa |
| Usuario | Coordinador regional; Operador de banco de sangre; Auditor |
| Requerimientos relacionados | RF-WEB-016 |

**Historia:** Como Coordinador regional, Operador o Auditor autorizado, quiero filtrar, generar y exportar reportes, para documentar operaciones y atender necesidades de seguimiento previamente definidas.

**Criterios de aceptación**

1. El usuario elige únicamente plantillas, periodos, instituciones y datos permitidos para su perfil.
2. El reporte identifica fecha de generación, filtros, responsable y procedencia de los datos.
3. La exportación conserva el mínimo de información necesaria y aplica el ocultamiento definido.
4. Un formato no validado por la autoridad se identifica como reporte académico u operativo y no como cumplimiento regulatorio.
5. La generación y descarga de reportes sensibles quedan auditadas.

### HU-WEB-015 — Gestionar archivos y evidencias autorizadas

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Media |
| Validación | Técnica |
| Usuario | Operador de banco de sangre; Personal médico autorizado; Coordinador regional; Auditor, según permiso |
| Requerimientos relacionados | RF-WEB-017, RF-DAT-004 |

**Historia:** Como usuario autorizado, quiero adjuntar y consultar archivos o evidencias vinculados con una operación, para completar su documentación sin exponer los objetos privados.

**Criterios de aceptación**

1. El sistema valida tipo, tamaño, finalidad y permisos antes de aceptar un archivo.
2. El objeto se almacena de forma privada en Google Cloud Storage y las bases conservan su referencia y metadatos, no el archivo grande.
3. La consulta o descarga utiliza un mecanismo temporal autorizado y no revela una ruta pública permanente.
4. Cada archivo se vincula con su propietario o evento y conserva tipo, tamaño, hash, privacidad, estado y fecha cuando correspondan.
5. Una carga rechazada explica la causa sin procesar contenido inseguro ni dejar referencias huérfanas.
6. La carga, consulta y descarga sensibles quedan auditadas.

### HU-WEB-016 — Consultar la trazabilidad y la auditoría

| Campo | Valor |
| --- | --- |
| Fase | Transversal: alcance básico en el primer parcial |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Auditor |
| Requerimientos relacionados | RF-WEB-018, RF-MS-008, RF-DAT-005, RF-SEC-003 |

**Historia:** Como Auditor, quiero buscar y consultar el historial autorizado de accesos, cambios y decisiones, para reconstruir qué ocurrió sin modificar la operación revisada.

**Criterios de aceptación**

1. La consulta permite filtrar por periodo, actor, institución, acción, entidad, resultado y nivel autorizado de sensibilidad.
2. Cada evento muestra como mínimo identificador, actor, tiempo, acción, entidad y resultado; incluye la información adicional necesaria para reconstruir operaciones críticas.
3. En el primer parcial se auditan autenticación, usuarios, catálogos e inventario; posteriormente se agregan accesos sensibles, algoritmos, aprobaciones, asignaciones y custodia.
4. El Auditor tiene acceso de solo lectura y no puede editar ni eliminar eventos ni operaciones examinadas.
5. Una corrección se registra como un evento adicional relacionado y no sobrescribe el historial original.
6. La exportación respeta ámbito, minimización y permisos, y su propia ejecución también queda auditada.

## 4. Módulo de microservicios

Las siguientes historias expresan resultados del negocio proporcionados principalmente por los microservicios. Las aplicaciones cliente podrán presentarlos únicamente a los perfiles autorizados y mediante el contrato correspondiente.

### Épica MS-01 — Apoyo explicable a las decisiones

### HU-MS-001 — Evaluar compatibilidad y priorización de forma explicable

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Personal médico autorizado; Coordinador regional |
| Requerimientos relacionados | RF-WEB-012, RF-MS-003, RF-MS-004 |

**Historia:** Como Personal médico autorizado o Coordinador regional, quiero recibir candidatos compatibles y un ranking explicable, para revisar alternativas sin delegar al sistema la decisión clínica o de asignación.

**Criterios de aceptación**

1. La evaluación utiliza únicamente datos suficientes y reglas de compatibilidad, urgencia y prioridad autorizadas, versionadas o identificadas expresamente como demostrativas; cuando corresponda, puede considerar resultados autorizados de comparación u optimización por distancia y tiempo.
2. Los procesos sanguíneos y HLA se calculan y explican conforme a sus reglas diferenciadas; la falta de información se muestra y no se interpreta como compatibilidad.
3. La urgencia utilizada corresponde a la registrada por personal autorizado y no es creada o modificada por el algoritmo.
4. Cada resultado conserva entradas relevantes, factores, ponderaciones, versión, fecha, posición y explicación reproducible.
5. El usuario puede registrar aceptación, rechazo, solicitud de reevaluación o excepción justificada sin alterar el cálculo original.
6. El resultado indica que es apoyo a la decisión y nunca reserva, asigna o descarta definitivamente un recurso por sí mismo.

### HU-MS-002 — Planear y seguir un traslado con cadena de custodia

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Coordinador regional |
| Requerimientos relacionados | RF-WEB-014, RF-MS-005, RF-MS-006 |

**Historia:** Como Coordinador regional, quiero comparar u optimizar alternativas por distancia y tiempo, programar un traslado y consultar su cadena de custodia, para coordinar el movimiento del recurso entre instituciones.

**Criterios de aceptación**

1. La comparación u optimización presenta distancia y tiempo estimado e identifica origen, destino, fuente geográfica, fecha del cálculo y sus limitaciones.
2. La orden de traslado conserva recurso, instituciones, responsable asignado, horario y estado, mostrando solo la información clínica mínima indispensable.
3. Recolección, salida, incidencias, entrega y recepción se registran como eventos consecutivos con responsable, tiempo, condición y ubicación autorizada cuando aplique.
4. Los eventos de custodia son append-only; una corrección crea un nuevo evento relacionado y no borra el anterior.
5. Reintentar una confirmación no duplica el evento y una secuencia inválida se rechaza de manera segura.
6. El coordinador puede consultar el estado actual y el historial, incluida la evidencia autorizada, sin modificar eventos ya confirmados.

### Épica MS-02 — Alertas y optimización operativa

### HU-MS-003 — Recibir y atender alertas operativas

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Administrador; Operador de banco de sangre; Personal médico autorizado; Coordinador regional; Personal de traslado; Donante; Auditor, según el tipo de alerta |
| Requerimientos relacionados | RF-MS-007 |

**Historia:** Como usuario autorizado, quiero recibir y atender alertas relevantes para mis responsabilidades, para reaccionar a urgencias, caducidades, retrasos o inconsistencias sin recibir duplicados innecesarios.

**Criterios de aceptación**

1. Cada alerta conserva tipo, origen, entidad relacionada, prioridad operativa, destinatario, fecha y estado.
2. La alerta se dirige únicamente a perfiles y ámbitos que pueden actuar sobre su causa.
3. Los eventos repetidos dentro de la regla definida se deduplican o relacionan sin ocultar su frecuencia.
4. El usuario puede marcarla como leída, atendida o cerrada conforme al flujo permitido y queda registro de la acción.
5. Las reglas de urgencia, caducidad o inconsistencia son configuradas y versionadas; las demostrativas se muestran como tales.
6. Una alerta informa y orienta la revisión, pero no ejecuta automáticamente una baja, transferencia o decisión clínica.

### HU-MS-004 — Consultar pronósticos de caducidad y sugerencias de balanceo

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Media |
| Validación | Demostrativa |
| Usuario | Coordinador regional |
| Requerimientos relacionados | RF-MS-009 |

**Historia:** Como Coordinador regional, quiero consultar riesgos pronosticados de caducidad y sugerencias de balanceo, para identificar posibles excedentes o faltantes antes de decidir una transferencia.

**Criterios de aceptación**

1. El resultado identifica el periodo, los datos históricos o sintéticos utilizados, la versión del método y sus limitaciones.
2. El pronóstico se distingue de la fecha de caducidad registrada y no modifica el estado real de una unidad.
3. La sugerencia considera únicamente inventario y demanda autorizados dentro del ámbito regional disponible.
4. Se muestran factores y una explicación suficiente para revisar por qué se sugirió una acción.
5. Ninguna transferencia se ejecuta automáticamente; el personal autorizado decide si inicia el proceso correspondiente.
6. El método cuenta con casos de prueba y métricas documentadas que permiten comparar su comportamiento.

## 5. Aplicación móvil Android

### Épica MOV-01 — Experiencia del donante

### HU-MOV-001 — Acceder al perfil móvil autorizado

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Donante; Personal de traslado |
| Requerimientos relacionados | RF-MOV-001, RF-SEC-001 |

**Historia:** Como Donante o Personal de traslado, quiero iniciar y cerrar sesión y consultar mi perfil desde la aplicación móvil, para utilizar únicamente las funciones correspondientes a mi rol.

**Criterios de aceptación**

1. Una sesión válida muestra el perfil y un menú diferenciado entre Donante y Personal de traslado.
2. La aplicación renueva el acceso solo mediante el mecanismo seguro definido y no solicita credenciales en cada operación válida.
3. Un token expirado, revocado o sin permisos impide la operación y conduce al flujo de recuperación correspondiente.
4. Al cerrar sesión se revocan o invalidan las credenciales aplicables y se elimina su copia local según la política definida.
5. El cambio de conectividad o un error del servicio se informa sin mostrar detalles internos ni mezclar datos de otra sesión.

### HU-MOV-002 — Enviar un registro preliminar de donante

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Donante |
| Requerimientos relacionados | RF-MOV-002, RF-MS-001 |

**Historia:** Como Donante potencial, quiero enviar un registro preliminar desde el móvil, para iniciar el contacto con una institución antes de la validación presencial o profesional.

**Criterios de aceptación**

1. El formulario solicita solo los datos mínimos aprobados, explica su finalidad y obtiene las confirmaciones o consentimientos definidos.
2. Los campos se validan antes del envío y los posibles duplicados se manejan sin revelar expedientes existentes.
3. El registro queda identificado como preliminar y pendiente de validación; no declara elegibilidad ni crea automáticamente una donación.
4. El usuario recibe un folio o confirmación y puede consultar el estado permitido de su registro.
5. La información se envía al microservicio correspondiente y no se conecta directamente con ningún almacén.

### HU-MOV-003 — Consultar campañas y gestionar citas

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Media |
| Validación | Técnica |
| Usuario | Donante |
| Requerimientos relacionados | RF-MOV-003 |

**Historia:** Como Donante, quiero consultar campañas y programar, consultar o cancelar una cita, para organizar mi participación en una institución disponible.

**Criterios de aceptación**

1. La aplicación muestra campañas publicadas con institución, ubicación, periodo, disponibilidad y condiciones informativas autorizadas.
2. El usuario puede filtrar campañas con los criterios definidos sin exponer datos internos de inventario o de otros donantes.
3. Al programar una cita se valida el horario disponible y se presenta un resumen antes de confirmar.
4. La cita confirmada conserva folio, institución, fecha, estado y campaña relacionada cuando aplique.
5. Consultar o cancelar respeta las transiciones y plazos definidos y actualiza la información real del servicio.
6. Un conflicto de disponibilidad informa alternativas o la necesidad de reintentar sin crear citas duplicadas.

### HU-MOV-004 — Recibir avisos de elegibilidad o seguimiento

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Media |
| Validación | Clínica/normativa |
| Usuario | Donante |
| Requerimientos relacionados | RF-MOV-004 |

**Historia:** Como Donante, quiero recibir avisos autorizados sobre elegibilidad o seguimiento, para conocer el siguiente paso sin interpretar una notificación como evaluación médica autónoma.

**Criterios de aceptación**

1. El aviso deriva de una decisión registrada por personal o reglas autorizadas y muestra su fecha y entidad emisora.
2. El contenido se limita a la información necesaria y no incluye datos clínicos sensibles en una notificación visible sin autenticación.
3. El usuario puede abrir el aviso dentro de la sesión y consultar las instrucciones permitidas.
4. El aviso distingue entre información, pendiente de revisión y decisión confirmada.
5. Leer o descartar la notificación no modifica por sí mismo el estado clínico del donante.

### Épica MOV-02 — Operación del traslado

### HU-MOV-005 — Verificar y confirmar recolección o entrega

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Personal de traslado |
| Requerimientos relacionados | RF-MOV-005 |

**Historia:** Como Personal de traslado, quiero consultar mi orden, escanear el recurso y confirmar la recolección o entrega, para mantener la custodia vinculada con el objeto correcto.

**Criterios de aceptación**

1. La aplicación muestra únicamente las órdenes asignadas al usuario y los datos logísticos indispensables.
2. El código escaneado se compara con el recurso y el evento esperado de la orden antes de permitir la confirmación.
3. Una discrepancia bloquea la confirmación, informa el motivo operativo y permite registrar la incidencia.
4. Una confirmación válida conserva responsable, fecha, ubicación autorizada, condición y resultado de la verificación.
5. Repetir el envío por un problema de red no duplica el evento confirmado.
6. El nuevo estado puede consultarse desde los demás componentes autorizados.

### HU-MOV-006 — Registrar ubicación y evidencia durante un traslado

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Media |
| Validación | Técnica |
| Usuario | Personal de traslado |
| Requerimientos relacionados | RF-MOV-006 |

**Historia:** Como Personal de traslado, quiero registrar ubicación y evidencia fotográfica solo durante una orden autorizada, para documentar el recorrido o la condición del recurso con una finalidad limitada.

**Criterios de aceptación**

1. La captura se habilita únicamente para una orden, evento y periodo activos asignados al usuario.
2. La aplicación solicita los permisos del dispositivo en contexto e informa la finalidad de ubicación y fotografía.
3. La evidencia permite confirmar o cancelar antes del envío y se vincula con el evento correspondiente.
4. Las imágenes se cargan al almacenamiento privado y la ubicación se conserva con la precisión y retención definidas.
5. Al finalizar el periodo autorizado cesa la captura y se eliminan las copias locales que ya no sean necesarias.
6. Una denegación de permiso se maneja de forma segura y muestra el procedimiento alternativo autorizado.

### HU-MOV-007 — Continuar operaciones permitidas sin conexión

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Donante; Personal de traslado |
| Requerimientos relacionados | RF-MOV-007 |

**Historia:** Como usuario móvil, quiero conservar temporalmente las operaciones permitidas cuando pierda conectividad y sincronizarlas después, para no perder información capturada durante una tarea autorizada.

**Criterios de aceptación**

1. La aplicación indica claramente si está en línea, sin conexión o sincronizando.
2. Solo las operaciones previamente definidas como seguras pueden guardarse temporalmente; una decisión clínica o asignación no se confirma sin validación del servidor.
3. Los datos pendientes se protegen localmente y permanecen asociados con el usuario, dispositivo y operación correctos.
4. Al volver la conexión, los envíos usan identificadores idempotentes y no crean eventos duplicados.
5. Un conflicto, rechazo o token vencido permanece visible y requiere la acción indicada; no se descarta silenciosamente.
6. El usuario puede consultar qué operaciones están pendientes, confirmadas o rechazadas.

## 6. Aplicación de escritorio

### Épica DESK-01 — Operación interna del banco

### HU-DESK-001 — Acceder a las funciones internas autorizadas

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Operador de banco de sangre; Coordinador regional |
| Requerimientos relacionados | RF-DESK-001, RF-SEC-001 |

**Historia:** Como Operador de banco de sangre o Coordinador regional, quiero iniciar y cerrar sesión en la aplicación de escritorio, para utilizar solo las operaciones internas permitidas para mi perfil.

**Criterios de aceptación**

1. La aplicación autentica mediante los servicios y presenta un menú distinto para Operador y Coordinador.
2. La sesión expirada, revocada o sin permisos impide continuar y preserva de forma segura un formulario no enviado cuando corresponda.
3. El usuario no puede abrir una operación fuera de su perfil o ámbito aunque conozca el identificador del recurso.
4. Cerrar sesión invalida las credenciales aplicables y limpia los datos locales sensibles definidos.
5. Los eventos de acceso quedan auditados sin registrar secretos ni tokens completos.

### HU-DESK-002 — Registrar unidades, pruebas e inventario local

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Operador de banco de sangre |
| Requerimientos relacionados | RF-DESK-002, RF-DESK-003, RF-MS-002 |

**Historia:** Como Operador de banco de sangre, quiero registrar el detalle de una unidad, capturar sus pruebas autorizadas y gestionar su inventario, para completar el flujo operativo interno con trazabilidad.

**Criterios de aceptación**

1. La unidad conserva un identificador único y los datos de origen, componente, ubicación y estado definidos.
2. Cada prueba registra tipo, resultado, responsable, fecha, estado y revisión autorizada cuando corresponda.
3. La unidad no avanza a un estado que requiera pruebas aprobadas mientras falten resultados o exista una inconsistencia conforme a las reglas validadas.
4. El usuario puede buscar, filtrar y consultar unidades, movimientos, estados y alertas de su institución.
5. Las transiciones inválidas se rechazan sin perder la captura y los cambios aceptados quedan auditados.
6. Toda consulta o modificación se realiza mediante microservicios y nunca con acceso directo a las bases de datos.

### HU-DESK-003 — Revisar compatibilidad, priorización y decisión humana

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Clínica/normativa |
| Usuario | Coordinador regional; Personal médico autorizado |
| Requerimientos relacionados | RF-DESK-004 |

**Historia:** Como Coordinador regional o personal autorizado, quiero revisar desde el escritorio la compatibilidad, el ranking y su explicación, para registrar una decisión humana sin alterar el cálculo original.

**Criterios de aceptación**

1. La vista muestra factores, ponderaciones, versión, datos faltantes, advertencias y explicación de cada resultado autorizado.
2. El usuario puede comparar candidatos sin recibir una indicación presentada como decisión médica definitiva.
3. Las ponderaciones o resultados calculados no pueden editarse desde la aplicación.
4. El usuario autorizado puede registrar aceptación, rechazo, reevaluación o excepción con motivo y evidencia cuando corresponda.
5. La decisión queda vinculada con la versión exacta del cálculo revisado y se audita.
6. Un cambio posterior de reglas genera una evaluación nueva y no reescribe la anterior.

### HU-DESK-004 — Imprimir una etiqueta trazable

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Media |
| Validación | Clínica/normativa |
| Usuario | Operador de banco de sangre |
| Requerimientos relacionados | RF-DESK-005 |

**Historia:** Como Operador de banco de sangre, quiero previsualizar e imprimir una etiqueta autorizada, para identificar físicamente una unidad sin perder su relación con el registro digital.

**Criterios de aceptación**

1. La etiqueta utiliza una plantilla, codificación y campos previamente aprobados para el tipo de recurso.
2. El código impreso corresponde al identificador de trazabilidad de la unidad seleccionada.
3. Antes de imprimir se muestra una previsualización y se valida que la unidad y la plantilla estén vigentes.
4. La impresión conserva fecha, usuario, impresora o destino cuando esté disponible y resultado.
5. Una reimpresión requiere el motivo definido y queda auditada.

### HU-DESK-005 — Documentar eventos de cadena de custodia

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Operador de banco de sangre; Coordinador regional |
| Requerimientos relacionados | RF-DESK-006 |

**Historia:** Como Operador o Coordinador autorizado, quiero registrar y consultar eventos de cadena de custodia desde el escritorio, para completar la trazabilidad operativa que no se capture en el móvil.

**Criterios de aceptación**

1. El usuario selecciona una orden y solo puede registrar el siguiente evento permitido para su perfil.
2. El evento conserva responsable, fecha, condición, ubicación autorizada, incidencia y evidencia relacionada cuando corresponda.
3. La secuencia y el recurso se validan antes de confirmar.
4. Los eventos confirmados no se editan ni eliminan; una corrección se registra como un evento relacionado.
5. El historial combina coherentemente los eventos originados en móvil, escritorio y servicios sin duplicarlos.
6. Toda captura y consulta sensible queda auditada.

### HU-DESK-006 — Consultar y exportar reportes internos

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Media |
| Validación | Clínica/normativa |
| Usuario | Operador de banco de sangre; Coordinador regional |
| Requerimientos relacionados | RF-DESK-007 |

**Historia:** Como Operador o Coordinador autorizado, quiero consultar tablas y exportar reportes operativos o regulatorios definidos, para respaldar el seguimiento interno de la institución.

**Criterios de aceptación**

1. Las tablas permiten búsqueda, filtros, orden y paginación sobre el ámbito autorizado.
2. El usuario solo puede seleccionar formatos y campos permitidos para su perfil.
3. El reporte conserva periodo, filtros, fecha, fuente y responsable de generación.
4. Un formato académico o pendiente de validación se identifica y no se presenta como reporte regulatorio oficial.
5. La exportación protege los datos sensibles y queda auditada.

## 7. Monitoreo y observabilidad

### Épica MON-01 — Estado operativo de la plataforma

### HU-MON-001 — Consultar el estado de servicios y dependencias

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Administrador |
| Requerimientos relacionados | RF-MON-001, RF-MON-002 |

**Historia:** Como Administrador, quiero consultar el estado de los servicios y sus dependencias, para distinguir una operación saludable de una degradación o caída.

**Criterios de aceptación**

1. El servicio de monitoreo consulta periódicamente los endpoints de salud definidos para proceso, PostgreSQL, MongoDB, Redis y Storage cuando apliquen.
2. El panel distingue disponible, degradado y caído, e identifica proceso detenido, dependencia inaccesible, respuesta inválida o timeout.
3. Para cada servicio se muestra versión, última verificación, tiempo de respuesta, número de errores y última causa conocida autorizada.
4. Una dependencia no aplicable se indica como tal y no se reporta falsamente como saludable.
5. El acceso al detalle operativo se limita a perfiles autorizados y no expone secretos ni datos clínicos.

### HU-MON-002 — Consultar historial y recibir avisos operativos

| Campo | Valor |
| --- | --- |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Usuario | Administrador |
| Requerimientos relacionados | RF-MON-003, RF-MON-004 |

**Historia:** Como Administrador, quiero consultar el historial de disponibilidad y recibir avisos de cambio de estado, para atender y comprobar incidentes de la plataforma.

**Criterios de aceptación**

1. Cada cambio de estado conserva servicio, estado anterior y nuevo, fecha, duración y causa conocida.
2. El historial puede consultarse por servicio y periodo sin depender únicamente del estado actual.
3. Una caída, degradación o recuperación genera un aviso dirigido a los responsables configurados.
4. Los eventos repetidos se agrupan o deduplican según la política definida sin perder la duración del incidente.
5. La recuperación cierra o actualiza el incidente correspondiente y no borra sus eventos anteriores.

## 8. Historias habilitadoras técnicas

Estas historias no agregan perfiles al sistema. Representan condiciones técnicas necesarias para que las historias de usuario sean ejecutables, seguras y verificables. Su aceptación deberá demostrarse con configuración, código, pruebas o evidencia de operación, según corresponda.

### HE-WEB-001 — Disponer de una base web usable y persistente

| Campo | Valor |
| --- | --- |
| Componente | Sistema web |
| Fase | Transversal: base en el primer parcial |
| Prioridad | Alta |
| Validación | Técnica |
| Responsable técnico | Equipo de desarrollo |
| Requerimientos relacionados | RNF-WEB-001, RNF-WEB-002, RNF-WEB-003, RNF-WEB-004 |

**Historia habilitadora:** Como equipo de desarrollo, necesitamos una base web usable, desacoplada y con persistencia real, para implementar y demostrar los procesos del negocio de forma consistente.

**Criterios de aceptación**

1. El sistema web utiliza Python, Flask, Jinja2, HTML5, CSS3 y JavaScript; sus gráficas utilizan Highcharts.
2. Las funciones propias de la web continúan disponibles cuando la aplicación móvil o de escritorio no lo están.
3. Las vistas definidas son responsive, navegables con teclado y ofrecen etiquetas, contraste y mensajes comprensibles.
4. Las listas pertinentes incluyen búsqueda, filtros y paginación acordes con el volumen de prueba.
5. Las operaciones demostradas guardan y consultan información real; una maqueta o respuesta fija no se considera aceptada.
6. Los errores se presentan de forma uniforme y segura, sin revelar trazas internas, secretos o datos sensibles.

### HE-MS-001 — Proveer microservicios independientes, contratados y resilientes

| Campo | Valor |
| --- | --- |
| Componente | Microservicios |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Responsable técnico | Equipo de integración |
| Requerimientos relacionados | RNF-MS-001, RNF-MS-002, RNF-MS-003, RNF-MS-004, RNF-MS-005, RNF-MS-006 |

**Historia habilitadora:** Como equipo de integración, necesitamos microservicios independientes con contratos verificables y comportamiento resiliente, para que web, móvil y escritorio compartan capacidades sin acoplarse entre sí.

**Criterios de aceptación**

1. Cada servicio se implementa con Flask y REST versionado, atiende una responsabilidad justificada y puede ejecutarse y desplegarse en su propio contenedor.
2. Cada microservicio produce respuestas tanto en JSON como en XML según el consumidor; los contratos OpenAPI o Swagger documentan autenticación, encabezados, parámetros, paginación, contratos y ejemplos de ambos formatos, respuestas y códigos HTTP, y las respuestas XML utilizan XSD donde corresponde.
3. Toda petición protegida valida JWT, sesión, revocación y permisos mediante los mecanismos definidos, incluida Redis.
4. Las entradas se validan y los errores usan un formato uniforme; se aplican límites de consumo configurables.
5. Cada petición registra servicio, versión, tiempo, resultado e identificador de correlación sin incluir datos sensibles innecesarios.
6. Los timeouts, reintentos seguros, idempotencia y dependencias inaccesibles se manejan sin corrupción ni fallos en cascada.
7. Locust ejecuta varios perfiles y flujos, y reporta concurrencia, peticiones por segundo, media, p95, p99, errores, saturación, recuperación y endpoints lentos.
8. Los algoritmos críticos documentan entradas, salidas, versión, casos de prueba, limitaciones y tiempo de ejecución.

### HE-MOV-001 — Integrar una aplicación Android segura mediante JSON

| Campo | Valor |
| --- | --- |
| Componente | Aplicación móvil |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Responsable técnico | Equipo móvil |
| Requerimientos relacionados | RNF-MOV-001, RNF-MOV-002, RNF-MOV-003, RNF-MOV-004 |

**Historia habilitadora:** Como equipo móvil, necesitamos una aplicación Android segura y tolerante a fallas de red, para entregar los flujos de Donante y Personal de traslado mediante contratos JSON.

**Criterios de aceptación**

1. La aplicación se desarrolla en Java o Kotlin después de registrar la decisión tecnológica y consume exclusivamente JSON de al menos cuatro microservicios.
2. Integra al menos dos capacidades pertinentes del dispositivo; para los flujos definidos se contemplan escaneo, cámara, ubicación, notificaciones o almacenamiento temporal.
3. El dispositivo, los tokens y los datos temporales se registran y almacenan de forma segura y se eliminan conforme al cierre de sesión y la retención definida.
4. Los formularios y respuestas JSON se validan; los errores de red no provocan pérdida silenciosa ni mezcla de sesiones.
5. La interfaz informa conectividad y sincronización y restringe menús y operaciones por perfil.
6. Los flujos principales de Donante y Personal de traslado se verifican mediante tareas de usabilidad y pruebas con servicios reales o entornos controlados.

### HE-DESK-001 — Integrar la aplicación de escritorio mediante XML validado

| Campo | Valor |
| --- | --- |
| Componente | Aplicación de escritorio |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Responsable técnico | Equipo de escritorio |
| Requerimientos relacionados | RNF-DESK-001, RNF-DESK-002, RNF-DESK-003, RNF-DESK-004 |

**Historia habilitadora:** Como equipo de escritorio, necesitamos un cliente interno desacoplado y seguro que consuma XML validado, para ejecutar procesos distintos de la web y de la aplicación móvil.

**Criterios de aceptación**

1. La tecnología se selecciona entre las opciones autorizadas y la decisión queda registrada antes de implementar.
2. La aplicación consume exclusivamente XML de al menos cuatro microservicios y valida los mensajes con XSD.
3. El procesamiento XML deshabilita entidades externas y aplica protección contra XXE.
4. La sesión y los permisos se validan mediante los servicios; el cliente no usa las vistas, sesiones internas ni almacenes del sistema web.
5. Un error de autenticación, contrato o red conserva de forma segura la captura no enviada cuando corresponda y muestra una acción de recuperación.
6. Las tareas repetitivas de captura, búsqueda, filtrado, exportación e impresión se evalúan con los perfiles internos previstos.

### HE-DAT-001 — Distribuir y proteger los datos según su ciclo de vida

| Campo | Valor |
| --- | --- |
| Componente | Bases de datos y almacenamiento |
| Fase | Transversal: PostgreSQL en el primer parcial; MongoDB y Redis desde el segundo; demás almacenes posteriormente |
| Prioridad | Alta |
| Validación | Técnica |
| Responsable técnico | Equipo de datos |
| Requerimientos relacionados | RF-DAT-001, RF-DAT-002, RF-DAT-003, RF-DAT-004, RF-DAT-005, RNF-DAT-001, RNF-DAT-002, RNF-DAT-003, RNF-DAT-004 |

**Historia habilitadora:** Como equipo de datos, necesitamos asignar cada dato a un almacén y propietario autoritativo acorde con su estructura y duración, para conservar consistencia, seguridad y trazabilidad.

**Criterios de aceptación**

1. PostgreSQL persiste en el primer parcial instituciones, usuarios, permisos, catálogos, inventario, estados y auditoría básica con datos ficticios iniciales.
2. A partir del segundo parcial, MongoDB se utiliza solo para documentos flexibles, telemetría, historiales extensos o resultados semiestructurados cuya justificación esté documentada.
3. A partir del segundo parcial, Redis administra sesiones, revocaciones, permisos temporales, rate limiting, caché autorizada, bloqueos, contadores y datos temporales con expiración definida.
4. Google Cloud Storage conserva archivos privados y las bases guardan únicamente referencias y metadatos; el acceso utiliza URLs firmadas de vigencia limitada.
5. Cada dato tiene un propietario autoritativo y ninguna aplicación cliente se conecta directamente con PostgreSQL, MongoDB, Redis o Storage.
6. Las reservas y asignaciones utilizan transacciones, restricciones o bloqueos que impiden estados contradictorios y doble asignación.
7. Auditoría y custodia conservan los datos mínimos necesarios para reconstruir el evento sin guardar secretos ni duplicar información sensible sin justificación.
8. Cada almacén documenta claves, restricciones, índices, crecimiento, retención, eliminación lógica, segregación, respaldo y restauración.
9. Las pruebas miden inserción, consulta, índices, caché, consumo de recursos, volumen y comportamiento con y sin Redis conforme a objetivos documentados.

### HE-INF-001 — Disponer de entornos reproducibles y despliegue controlado

| Campo | Valor |
| --- | --- |
| Componente | Infraestructura |
| Fase | Transversal: base local sin contenedores en el primer parcial, Docker desde el segundo y nube posteriormente |
| Prioridad | Alta |
| Validación | Técnica |
| Responsable técnico | Equipo de desarrollo y operación |
| Requerimientos relacionados | RNF-INF-001, RNF-INF-002, RNF-INF-003, RNF-INF-004, RNF-INF-005 |

**Historia habilitadora:** Como equipo de desarrollo y operación, necesitamos entornos reproducibles y despliegues independientes, para construir y ejecutar la plataforma sin depender de configuraciones personales no documentadas.

**Criterios de aceptación**

1. El repositorio documenta estrategia de ramas, incidencias, tablero, estándares de codificación y convenciones de nombres con un alcance académico viable.
2. Cada componente declara dependencias y variables de entorno; no se versionan secretos ni valores reales de archivos de entorno.
3. A partir del segundo parcial, los componentes desplegables cuentan con Dockerfile y Docker Compose levanta el entorno local requerido con PostgreSQL, MongoDB y Redis.
4. El despliegue posterior en Google Compute Engine documenta web, servicios, datos, archivos y monitoreo con redes privadas, firewall, puertos mínimos y comunicaciones cifradas.
5. La integración continua ejecuta las validaciones acordadas y permite desplegar un componente sin obligar a publicar toda la plataforma.
6. Un servicio opcional de Google Cloud se incorpora únicamente cuando existe una necesidad y justificación registradas.

### HE-INF-002 — Verificar integración completa y recuperación ante fallos

| Campo | Valor |
| --- | --- |
| Componente | Infraestructura e integración |
| Fase | Posterior y transversal a cada incremento integrado |
| Prioridad | Alta |
| Validación | Técnica |
| Responsable técnico | Equipo de calidad e integración |
| Requerimientos relacionados | RNF-INF-006, RNF-INF-007, RNF-INF-008 |

**Historia habilitadora:** Como equipo de calidad e integración, necesitamos comprobar flujos completos y fallas parciales, para demostrar que los componentes cooperan sin corromper datos.

**Criterios de aceptación**

1. Se demuestran al menos tres procesos de principio a fin con usuario, cliente, microservicios, JWT, Redis, PostgreSQL o MongoDB, auditoría, notificación y objeto en bucket cuando el flujo maneja archivos.
2. Al menos un proceso puede consultarse coherentemente desde los clientes autorizados, respetando JSON para móvil y XML para escritorio.
3. Las pruebas de falla cubren PostgreSQL, MongoDB, Redis, Storage y microservicios, además de timeouts, respuestas inválidas, recursos inexistentes y recuperación.
4. Una falla se detecta y registra, produce un mensaje apropiado y no confirma una operación si no puede garantizarse su consistencia.
5. Al restablecerse la dependencia, el flujo se recupera o presenta una acción explícita sin duplicar la operación.
6. Cada incremento aporta pruebas proporcionales al riesgo: unitarias, integración, sistema, regresión, extremo a extremo, contratos, seguridad, concurrencia, archivos, datos masivos y usabilidad según apliquen.
7. La evidencia de prueba registra escenario, versión, datos, resultado esperado, resultado obtenido y defectos encontrados.

### HE-SEC-001 — Aplicar seguridad y privacidad de extremo a extremo

| Campo | Valor |
| --- | --- |
| Componente | Seguridad y privacidad |
| Fase | Transversal: controles básicos desde el primer parcial |
| Prioridad | Alta |
| Validación | Técnica y clínica/normativa según el control |
| Responsable técnico | Responsable de seguridad y privacidad |
| Requerimientos relacionados | RF-SEC-001, RF-SEC-002, RF-SEC-003, RNF-SEC-001, RNF-SEC-002, RNF-SEC-003, RNF-SEC-004, RNF-SEC-005, RNF-SEC-006, RNF-SEC-007, RNF-SEC-008 |

**Historia habilitadora:** Como responsable de seguridad y privacidad, necesitamos controles consistentes en todos los componentes, para proteger identidad, datos clínicos, ubicación, evidencias y operaciones críticas.

**Criterios de aceptación**

1. En el primer parcial, las contraseñas utilizan un hash seguro y los JWT de acceso tienen expiración definida; a partir del segundo parcial, la renovación aplica rotación o un control equivalente y la revocación se valida mediante Redis.
2. Toda petición protegida comprueba identidad, sesión, revocación, perfil, acción, recurso y ámbito institucional con mínimo privilegio.
3. Las consultas son parametrizadas y se validan formularios, JSON, XML, XSD y archivos, incluida la protección contra inyección y XXE.
4. Los endpoints aplican rate limiting, registran intentos fallidos y ejecutan el bloqueo temporal configurado sin facilitar enumeración de cuentas.
5. Las comunicaciones se cifran y los secretos permanecen fuera del código, los logs y los archivos versionados.
6. Interfaces, respuestas, errores y bitácoras minimizan u ocultan datos personales, clínicos, ubicación, fotografías, tokens y secretos.
7. La captura de ubicación y fotografías se limita a perfiles, finalidades, traslados y periodos autorizados y elimina copias locales innecesarias.
8. Las políticas de consentimiento, retención, bloqueo, eliminación e intercambio interinstitucional se documentan y validan antes de utilizar datos reales.
9. Las pruebas comprueban autenticación, autorización, expiración, renovación, revocación, acceso cruzado entre ámbitos y manejo de entradas maliciosas.

### HE-MON-001 — Centralizar señales operativas sin afectar el negocio

| Campo | Valor |
| --- | --- |
| Componente | Monitoreo |
| Fase | Posterior |
| Prioridad | Alta |
| Validación | Técnica |
| Responsable técnico | Equipo de operación |
| Requerimientos relacionados | RNF-MON-001, RNF-MON-002, RNF-MON-003 |

**Historia habilitadora:** Como equipo de operación, necesitamos health checks, logs y métricas centralizables y no intrusivos, para observar la plataforma sin convertir el monitoreo en una dependencia de las operaciones del negocio.

**Criterios de aceptación**

1. Los endpoints de salud distinguen proceso detenido, dependencia inaccesible, respuesta inválida y timeout con estados definidos.
2. Se implementan los endpoints `/health/live`, `/health/ready`, `/health/database`, `/health/redis`, `/health/mongodb` y `/health/storage` cuando correspondan al servicio.
3. La indisponibilidad del servicio de monitoreo no detiene las funciones propias de los componentes supervisados.
4. Logs y métricas utilizan timestamps, servicio, versión e identificadores de correlación que permiten seguir una petición distribuida.
5. Las señales operativas no almacenan datos clínicos, tokens, secretos, ubicaciones o fotografías innecesarias.
6. Los periodos de conservación y el acceso a logs, métricas e historial se configuran y documentan.
