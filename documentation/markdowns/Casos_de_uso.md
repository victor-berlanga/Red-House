# Casos de uso principales

> **Proyecto:** Red regional de bancos de sangre y donación de órganos — Equipo 01.  
> **Estado:** línea base documental del alcance completo.  
> **Fecha:** 7 de septiembre de 2026.  
> **Cobertura:** quince casos de uso principales, con implementación gradual por parciales e incrementos.

## 1. Propósito y alcance

Este documento describe las interacciones principales entre los actores y la plataforma regional. Los casos de uso cubren el sistema web, los microservicios, la aplicación móvil Android, la aplicación de escritorio, los almacenes de datos, la seguridad y el monitoreo, sin convertir cada requisito o cada pantalla en un caso independiente.

El alcance corresponde al proyecto completo. Los casos identificados para el primer parcial delimitan el producto mínimo funcional; los casos posteriores permanecen documentados para orientar los siguientes incrementos. La plataforma proporciona coordinación y apoyo a decisiones, pero no sustituye la evaluación médica, ética o normativa ni confirma automáticamente decisiones que requieran intervención humana autorizada.

Los flujos clínicos o regulatorios se ejecutarán con datos ficticios y reglas demostrativas mientras no existan fuentes vigentes y validación competente. Los flujos distinguen expresamente la sangre de los órganos y no establecen fórmulas, ponderaciones, tiempos de conservación ni reglas de compatibilidad no documentadas.

## 2. Convenciones y condiciones comunes

### 2.1 Identificación y fases

| Elemento | Convención |
| --- | --- |
| Identificador | `CU-01` a `CU-15`. |
| Primer parcial | Caso implementado total o parcialmente dentro del producto mínimo funcional web. |
| Posterior | Caso perteneciente al alcance completo que se implementará en los incrementos posteriores. |
| Transversal | Caso o control que inicia en el primer parcial y evoluciona durante el semestre. |
| Flujo principal | Secuencia esperada cuando se satisfacen permisos, datos y reglas aplicables. |
| Flujo alterno | Condición válida, rechazo o falla que modifica el recorrido sin cambiar el propósito del caso. |

### 2.2 Actores considerados

| Actor | Participación general |
| --- | --- |
| Administrador | Gestiona identidad, instituciones, catálogos y supervisión técnica autorizada, sin adquirir facultades clínicas. |
| Operador de banco de sangre | Mantiene unidades, inventario, pruebas capturadas, etiquetas y eventos operativos dentro de su institución. |
| Personal médico autorizado | Registra receptores, solicitudes, urgencia confirmada y decisiones clínicas permitidas dentro de su acreditación y ámbito. |
| Coordinador regional | Coordina disponibilidad, revisión de alternativas, asignaciones, traslados e información regional minimizada. |
| Personal de traslado | Ejecuta órdenes propias, escanea recursos y registra recolección, entrega, ubicación o evidencia autorizada. |
| Donante | Gestiona su registro preliminar, campañas, citas y avisos propios desde la aplicación móvil. |
| Auditor | Consulta trazabilidad y evidencia de solo lectura dentro del ámbito autorizado. |
| Público general | Consulta únicamente información pública; no constituye un perfil privado. |
| Receptor o paciente | Es sujeto protegido de información; no dispone de acceso directo en el alcance definido. |
| Institución participante | Determina el ámbito organizacional y actúa como origen o destino de procesos, pero no constituye un perfil. |

### 2.3 Condiciones transversales

1. Toda operación protegida valida identidad, sesión, revocación, perfil, acción, recurso y ámbito institucional.
2. Ninguna aplicación cliente accede directamente a PostgreSQL, MongoDB, Redis o Google Cloud Storage.
3. Los cambios aceptados utilizan persistencia real y generan auditoría proporcional a su sensibilidad.
4. Los datos personales, clínicos, logísticos, de ubicación y de evidencia se minimizan en interfaces, respuestas, archivos y registros técnicos.
5. Los resultados de compatibilidad, priorización, distancia, pronóstico o balanceo conservan versión, factores y explicación, y no ejecutan por sí mismos una decisión clínica o asignación.
6. Los procesos de sangre y de órganos mantienen datos, estados, reglas, pruebas, tiempos y responsables diferenciados.
7. Una falla no confirma una operación cuando no puede garantizarse su consistencia; el error se registra y se presenta de forma segura.

## 3. Catálogo de casos de uso

| ID | Caso de uso | Actor principal | Fase | Resultado esperado |
| --- | --- | --- | --- | --- |
| `CU-01` | Consultar información pública y acceder a la plataforma | Público general; usuario registrado | Transversal | Contenido público seguro o sesión válida con menú autorizado. |
| `CU-02` | Administrar usuarios, perfiles y ámbitos | Administrador | Primer parcial | Cuentas y autorizaciones vigentes y auditadas. |
| `CU-03` | Administrar instituciones, sedes y catálogos | Administrador | Primer parcial | Fuente institucional única y catálogos controlados. |
| `CU-04` | Gestionar disponibilidad de sangre y órganos | Operador; Personal médico autorizado | Transversal | Inventario sanguíneo o disponibilidad de órganos actualizados mediante flujos diferenciados. |
| `CU-05` | Gestionar la participación del donante | Donante; personal autorizado | Posterior | Registro preliminar, expediente, campaña, cita y avisos vinculados sin elegibilidad automática. |
| `CU-06` | Registrar un receptor y gestionar su solicitud | Personal médico autorizado | Posterior | Receptor y solicitud completa con urgencia autorizada e historial. |
| `CU-07` | Capturar y revisar pruebas o estudios | Operador; Personal médico autorizado | Posterior | Resultado identificado, protegido, revisable y no concluyente por sí solo. |
| `CU-08` | Evaluar compatibilidad y priorización explicables | Personal médico autorizado; Coordinador regional | Posterior | Candidatos y ranking explicables para revisión humana. |
| `CU-09` | Autorizar y controlar una asignación | Coordinador regional; autoridad humana aplicable | Posterior | Recurso reservado o asignado sin duplicidad y con decisión trazable. |
| `CU-10` | Planear y programar un traslado | Coordinador regional | Posterior | Orden de traslado con ruta, responsables y estado. |
| `CU-11` | Ejecutar traslado y documentar cadena de custodia | Personal de traslado; Operador; Coordinador | Posterior | Eventos secuenciales, evidencia privada y sincronización controlada. |
| `CU-12` | Supervisar paneles, alertas y pronósticos | Usuario autorizado según información | Transversal | Situación operativa visible sin ejecutar decisiones automáticas. |
| `CU-13` | Generar reportes y gestionar evidencia documental | Operador; Coordinador; Auditor | Posterior | Reporte o archivo autorizado, minimizado y auditable. |
| `CU-14` | Consultar auditoría y trazabilidad | Auditor | Transversal | Reconstrucción de eventos sin modificar el historial. |
| `CU-15` | Supervisar salud y disponibilidad técnica | Administrador | Posterior | Estado e historial de servicios, dependencias e incidentes. |

## 4. Casos de uso del núcleo inicial y transversal

### 4.1 CU-01 — Consultar información pública y acceder a la plataforma

| Campo | Definición |
| --- | --- |
| Actor principal | Público general o usuario registrado, conforme al canal habilitado. |
| Actores de apoyo | Servicio de identidad; Administrador para la habilitación de cuentas. |
| Fase | Transversal: sitio público, inicio y cierre en el primer parcial; recuperación y clientes adicionales posteriormente. |
| Componentes | Sistema web; posteriormente microservicios, aplicación móvil y aplicación de escritorio; Redis se incorpora a partir del segundo parcial. |
| Disparador | Una persona abre el sitio público o solicita iniciar, cerrar o recuperar una sesión. |
| Precondiciones | Para el acceso privado, la cuenta, el perfil y el ámbito deben encontrarse activos. |
| Postcondiciones | El visitante permanece en contenido público o el usuario obtiene una sesión válida y auditable; el cierre invalida las credenciales aplicables. |

**Flujo principal**

1. La plataforma presenta información pública autorizada y un acceso visible al portal privado.
2. El usuario proporciona sus credenciales mediante el canal habilitado.
3. El componente de identidad valida credenciales, estado de cuenta, sesión, perfil y ámbito sin revelar cuál dato falló.
4. La plataforma emite las credenciales de sesión definidas y registra el resultado de autenticación sin almacenar secretos ni tokens completos.
5. El canal muestra únicamente el menú, panel y operaciones autorizados para el perfil vigente.
6. Cuando el usuario cierra sesión, la plataforma revoca o invalida la sesión y elimina las credenciales locales que correspondan.

**Flujos alternos y excepciones**

- Si la cuenta es inválida, inactiva, está temporalmente bloqueada o la sesión expiró, se deniega el acceso mediante un mensaje genérico y auditable.
- Si el token fue revocado o no autoriza la operación solicitada, el canal interrumpe el flujo privado y solicita recuperar una sesión válida.
- La recuperación de acceso, cuando se implemente, utilizará un mecanismo temporal y de un solo uso sin revelar la existencia de una cuenta.
- A partir del segundo parcial, una falla de Redis o del servicio de identidad no permitirá confirmar una nueva operación protegida cuya autorización no pueda comprobarse.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-001, RF-WEB-002, RF-MOV-001, RF-DESK-001, RF-SEC-001, RF-SEC-003 |
| RNF | RNF-MS-003, RNF-MOV-002, RNF-MOV-003, RNF-DESK-003, RNF-SEC-001, RNF-SEC-002, RNF-SEC-004, RNF-SEC-005, RNF-SEC-006 |
| HU/HE | HU-WEB-001, HU-WEB-002, HU-MOV-001, HU-DESK-001, HE-SEC-001 |
| RN | RN-ACC-002, RN-ACC-004, RN-COM-005 |

### 4.2 CU-02 — Administrar usuarios, perfiles y ámbitos

| Campo | Definición |
| --- | --- |
| Actor principal | Administrador. |
| Actores de apoyo | Usuario cuya cuenta se administra; servicio de identidad. |
| Fase | Primer parcial y mantenimiento transversal. |
| Componentes | Sistema web; seguridad; PostgreSQL; Redis desde el segundo parcial cuando corresponda a sesiones o permisos temporales. |
| Disparador | El Administrador necesita crear, consultar, actualizar, activar o desactivar una cuenta o su asignación. |
| Precondiciones | El Administrador mantiene una sesión válida y permiso administrativo dentro de su ámbito. |
| Postcondiciones | La cuenta, el perfil y el ámbito quedan actualizados; el cambio conserva responsable, fecha y resultado. |

**Flujo principal**

1. El Administrador consulta las cuentas pertenecientes a su ámbito autorizado.
2. Selecciona una cuenta existente o inicia un alta y captura los datos administrativos permitidos.
3. Asigna uno de los perfiles habilitados para el incremento y el ámbito institucional correspondiente.
4. La plataforma valida campos obligatorios, unicidad, estado de la institución y límites de autorización del Administrador.
5. El Administrador confirma la operación y el sistema persiste el cambio.
6. Los permisos efectivos y sesiones afectadas se actualizan conforme a la política definida.
7. La plataforma registra el cambio en la bitácora y presenta el resultado sin exponer datos sensibles innecesarios.

**Flujos alternos y excepciones**

- Durante el primer parcial solo se habilitan funcionalmente Administrador, Operador de banco de sangre y Auditor, aunque los siete perfiles permanezcan definidos.
- Una solicitud fuera del ámbito del Administrador se deniega aunque conozca el identificador de la cuenta.
- La asignación de un perfil clínico posterior no concede por sí misma una acreditación profesional.
- Si una cuenta posee historial, la desactivación conserva sus relaciones y no elimina las operaciones anteriores.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-003, RF-SEC-002 |
| RNF | RNF-WEB-004, RNF-DAT-001, RNF-SEC-002, RNF-SEC-006 |
| HU/HE | HU-WEB-003, HE-SEC-001 |
| RN | RN-ACC-001, RN-ACC-002, RN-ACC-003 |

### 4.3 CU-03 — Administrar instituciones, sedes y catálogos

| Campo | Definición |
| --- | --- |
| Actor principal | Administrador. |
| Actores de apoyo | Institución participante. |
| Fase | Primer parcial, con ampliación posterior de catálogos. |
| Componentes | Sistema web; PostgreSQL; auditoría. |
| Disparador | Se requiere incorporar, actualizar o inactivar información administrativa utilizada por los procesos. |
| Precondiciones | El Administrador posee permiso sobre el ámbito correspondiente. |
| Postcondiciones | La institución o valor de catálogo queda persistido como registro vigente o inactivo, sin romper referencias históricas. |

**Flujo principal**

1. El Administrador selecciona la administración de instituciones, sedes o catálogos permitidos.
2. La plataforma consulta la fuente institucional única o el catálogo correspondiente con búsqueda y filtros.
3. El Administrador captura o modifica los datos autorizados, incluidos ubicación, contactos, capacidades declaradas y estado cuando apliquen.
4. El sistema valida obligatoriedad, formato, posibles duplicados, unicidad y referencias activas.
5. El Administrador confirma y la plataforma persiste la operación.
6. Los demás procesos utilizan la institución registrada como referencia y no mantienen una copia conceptual independiente.
7. El cambio queda registrado con actor, fecha, entidad y resultado.

**Flujos alternos y excepciones**

- Si existe un posible duplicado, la plataforma solicita revisar el registro encontrado antes de crear otro.
- Un valor referenciado por operaciones anteriores se inactiva en lugar de eliminarse de forma destructiva.
- Un parámetro demostrativo se identifica como tal y no se presenta como regla clínica autorizada.
- Desactivar una institución impide nuevas operaciones según las reglas aplicables, pero conserva historial y relaciones existentes.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-004, RF-WEB-005, RF-DAT-001 |
| RNF | RNF-WEB-003, RNF-WEB-004, RNF-DAT-004, RNF-SEC-002, RNF-SEC-003 |
| HU/HE | HU-WEB-004, HU-WEB-005, HE-DAT-001 |
| RN | RN-GOB-003, RN-ACC-005, RN-ACC-006 |

### 4.4 CU-04 — Gestionar disponibilidad de sangre y órganos

| Campo | Definición |
| --- | --- |
| Actor principal | Operador de banco de sangre para unidades sanguíneas; Personal médico autorizado para órganos. |
| Actores de apoyo | Administrador para catálogos; Coordinador regional para consulta autorizada. |
| Fase | Primer parcial para inventario sanguíneo ficticio; posterior para órganos y operación distribuida. |
| Componentes | Sistema web; posteriormente microservicio de inventario y aplicación de escritorio; PostgreSQL y auditoría. |
| Disparador | Se registra un recurso o debe consultarse o actualizarse su disponibilidad. |
| Precondiciones | Institución y catálogos vigentes; actor autorizado; para cambios avanzados, pruebas o validaciones requeridas disponibles. |
| Postcondiciones | El estado autoritativo del recurso y su historial quedan actualizados mediante el flujo correspondiente. |

**Flujo principal**

1. El actor selecciona expresamente el proceso de sangre o el proceso especializado de órganos.
2. Para sangre, registra o consulta la unidad con identificador único, institución, ubicación, componente, fechas y estado; para órganos, captura únicamente disponibilidad, viabilidad y datos autorizados del flujo especializado.
3. La plataforma valida campos, duplicados, referencias y transición solicitada sin mezclar reglas entre tipos de recurso.
4. En el inventario sanguíneo del primer parcial se calcula la proximidad de caducidad mediante el parámetro demostrativo visible.
5. El actor confirma la operación y la plataforma persiste el nuevo estado y el movimiento correspondiente.
6. En el incremento de escritorio, el Operador puede previsualizar e imprimir una etiqueta autorizada vinculada con el identificador de la unidad.
7. La plataforma registra la operación y actualiza las consultas autorizadas de inventario o disponibilidad.

**Flujos alternos y excepciones**

- Una unidad vencida, dada de baja o en estado no disponible no se ofrece para una nueva operación.
- Una transición inválida se rechaza sin perder la información previamente persistida.
- Un órgano con información obligatoria faltante conserva un estado explícito y no se presenta como viable o asignado.
- Capturar disponibilidad o viabilidad no equivale a autorizar una asignación.
- Una reimpresión de etiqueta requiere el motivo definido y genera auditoría.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-008, RF-WEB-009, RF-MS-002, RF-DESK-002, RF-DESK-005, RF-DAT-001, RF-DAT-005 |
| RNF | RNF-WEB-003, RNF-WEB-004, RNF-DAT-001, RNF-DAT-004, RNF-SEC-002, RNF-SEC-003 |
| HU/HE | HU-WEB-008, HU-WEB-009, HU-DESK-002, HU-DESK-004, HE-DAT-001 |
| RN | RN-GOB-003, RN-GOB-004, RN-INV-001, RN-INV-002, RN-INV-003, RN-INV-006 |

## 5. Casos de uso de personas, solicitudes y decisiones

### 5.1 CU-05 — Gestionar la participación del donante

| Campo | Definición |
| --- | --- |
| Actor principal | Donante; Operador de banco de sangre o Personal médico autorizado para el expediente validado. |
| Actores de apoyo | Institución participante; servicio de donantes y receptores; servicio de alertas. |
| Fase | Posterior. |
| Componentes | Aplicación móvil mediante JSON; sistema web; microservicios; PostgreSQL y Redis según la operación. |
| Disparador | Una persona desea iniciar su registro, consultar campañas, gestionar una cita o revisar un aviso propio. |
| Precondiciones | Para operaciones privadas, sesión válida; campaña publicada y vigente cuando se solicite una cita. |
| Postcondiciones | Registro preliminar, expediente autorizado, cita o aviso quedan vinculados con el donante y conservan el estado correspondiente. |

**Flujo principal**

1. El Donante accede a las opciones permitidas de su perfil móvil.
2. Envía un registro preliminar con los datos mínimos y consentimientos definidos; la plataforma valida formato y posibles duplicados sin revelar expedientes existentes.
3. El sistema entrega un folio y mantiene el registro como pendiente de validación presencial o profesional.
4. El Donante consulta campañas publicadas y selecciona una institución, fecha y horario disponible.
5. La plataforma valida disponibilidad y confirma una cita con folio y un solo estado vigente.
6. El personal autorizado valida o mantiene posteriormente el expediente conforme al tipo de donación y registra cualquier decisión permitida.
7. El Donante recibe avisos de seguimiento o elegibilidad originados en una decisión autorizada y consulta únicamente la información propia permitida.

**Flujos alternos y excepciones**

- El registro preliminar no declara elegibilidad ni crea automáticamente una donación.
- Si el horario deja de estar disponible, se informa el conflicto sin generar una cita duplicada.
- Una cancelación sigue las transiciones y plazos definidos y conserva el historial de la cita.
- Leer o descartar un aviso no cambia el estado clínico o de elegibilidad.
- Si una operación permitida queda sin conexión, se conserva de forma protegida y se sincroniza con un identificador idempotente; los conflictos permanecen visibles.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-006, RF-MS-001, RF-MOV-002, RF-MOV-003, RF-MOV-004, RF-MOV-007 |
| RNF | RNF-MS-002, RNF-MOV-001 a RNF-MOV-004, RNF-SEC-002, RNF-SEC-006, RNF-SEC-008 |
| HU/HE | HU-WEB-006, HU-MOV-002, HU-MOV-003, HU-MOV-004, HU-MOV-007, HE-MOV-001 |
| RN | RN-GOB-004, RN-PER-001, RN-PER-002, RN-PER-003, RN-PER-005, RN-COM-001 |

### 5.2 CU-06 — Registrar un receptor y gestionar su solicitud

| Campo | Definición |
| --- | --- |
| Actor principal | Personal médico autorizado. |
| Actores de apoyo | Institución solicitante; Coordinador regional; servicio de donantes y receptores. |
| Fase | Posterior. |
| Componentes | Sistema web; microservicios; PostgreSQL; alertas y auditoría. |
| Disparador | Existe una necesidad documentada de sangre u órgano para un receptor. |
| Precondiciones | El actor mantiene acreditación, permiso y ámbito vigentes; los catálogos necesarios se encuentran disponibles. |
| Postcondiciones | El receptor y la solicitud quedan registrados con folio, estado, urgencia autorizada e historial, o se informa la información faltante. |

**Flujo principal**

1. El Personal médico autorizado busca al receptor dentro de su ámbito y registra un expediente cuando no existe uno autorizado.
2. Selecciona el proceso de sangre o de órganos y captura únicamente los datos permitidos para dicho proceso.
3. Crea una solicitud con receptor, institución, necesidad, responsable, fecha y urgencia registrada o confirmada por personal autorizado.
4. La plataforma valida campos obligatorios, posibles duplicados, ámbito y consistencia del estado solicitado.
5. El usuario revisa y confirma la información.
6. El sistema asigna un folio, persiste la solicitud y registra el evento de auditoría.
7. Se generan las notificaciones operativas configuradas sin iniciar automáticamente una compatibilidad, reserva o asignación definitiva.

**Flujos alternos y excepciones**

- Registrar un receptor no crea una cuenta de acceso para el paciente.
- Si faltan datos obligatorios, la solicitud permanece incompleta y no avanza a evaluación.
- La plataforma no infiere ni modifica la urgencia a partir de datos parciales.
- Una consulta fuera del ámbito se deniega sin revelar si el expediente existe.
- Un cambio posterior de estado conserva autor, fecha, motivo e historial.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-007, RF-WEB-010, RF-MS-001 |
| RNF | RNF-WEB-003, RNF-WEB-004, RNF-DAT-001, RNF-SEC-002, RNF-SEC-003, RNF-SEC-006, RNF-SEC-008 |
| HU/HE | HU-WEB-007, HU-WEB-010, HE-DAT-001, HE-SEC-001 |
| RN | RN-GOB-004, RN-PER-004, RN-SOL-001, RN-SOL-002 |

### 5.3 CU-07 — Capturar y revisar pruebas o estudios

| Campo | Definición |
| --- | --- |
| Actor principal | Operador de banco de sangre o Personal médico autorizado, según el tipo de estudio. |
| Actores de apoyo | Revisor autorizado; institución responsable de la prueba. |
| Fase | Posterior. |
| Componentes | Sistema web y aplicación de escritorio; microservicios; PostgreSQL o almacenamiento semiestructurado justificado; auditoría. |
| Disparador | Se dispone de una prueba o estudio autorizado relacionado con una persona, muestra o recurso. |
| Precondiciones | El sujeto o recurso existe; el actor posee permiso; el tipo de prueba y su esquema están definidos. |
| Postcondiciones | El resultado queda identificado con estado, fuente, responsable e historial, sin producir por sí solo una decisión de disponibilidad o compatibilidad. |

**Flujo principal**

1. El actor selecciona el sujeto o recurso y el tipo de prueba correspondiente al proceso de sangre, órgano o tejido.
2. La plataforma presenta los campos y validaciones autorizados para ese tipo, sin reutilizar indiscriminadamente un esquema de otro proceso.
3. El actor captura resultado, fuente, fecha, responsable y estado.
4. El sistema valida obligatoriedad, formato, relación con el recurso y consistencia básica.
5. Cuando corresponda, un revisor autorizado confirma el estado de revisión sin alterar el resultado capturado.
6. La plataforma persiste la versión y registra el acceso o cambio conforme a su sensibilidad.

**Flujos alternos y excepciones**

- Un resultado incompleto, contradictorio o pendiente se muestra con ese estado y no se considera confirmado.
- Si una corrección es necesaria, se conserva el resultado anterior, el motivo y el responsable.
- La ausencia de una prueba obligatoria impide avanzar a un estado que la requiera conforme a las reglas validadas.
- Capturar o revisar el resultado no autoriza automáticamente disponibilidad, compatibilidad o asignación.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-011, RF-DESK-003 |
| RNF | RNF-DESK-002, RNF-DESK-003, RNF-DAT-001, RNF-DAT-004, RNF-SEC-002, RNF-SEC-003, RNF-SEC-006 |
| HU/HE | HU-WEB-011, HU-DESK-002, HE-DESK-001, HE-DAT-001 |
| RN | RN-GOB-004, RN-INV-004, RN-SOL-003 |

### 5.4 CU-08 — Evaluar compatibilidad y priorización explicables

| Campo | Definición |
| --- | --- |
| Actor principal | Personal médico autorizado o Coordinador regional. |
| Actores de apoyo | Servicios de compatibilidad, priorización y geografía. |
| Fase | Posterior. |
| Componentes | Sistema web o aplicación de escritorio; microservicios; PostgreSQL, MongoDB o Redis conforme al dato; auditoría. |
| Disparador | Una solicitud completa requiere identificar y ordenar alternativas compatibles. |
| Precondiciones | Solicitud, recursos y datos mínimos disponibles; reglas autorizadas y versionadas o reglas demostrativas identificadas. |
| Postcondiciones | Se conserva una evaluación inmutable con candidatos, posición, factores, versión, explicación y decisión humana relacionada cuando exista. |

**Flujo principal**

1. El actor selecciona una solicitud autorizada y solicita una evaluación.
2. El servicio reúne los datos mínimos de la solicitud y de los recursos candidatos sin trasladar reglas principales al cliente.
3. El servicio de compatibilidad aplica únicamente las reglas versionadas del proceso sanguíneo o HLA correspondiente e identifica información faltante.
4. El servicio de priorización ordena los candidatos con los factores autorizados, incluida la urgencia registrada y, cuando corresponda, resultados de distancia y tiempo provenientes de una fuente identificada.
5. La plataforma presenta candidatos, datos faltantes, factores, ponderaciones autorizadas, versión, fecha y explicación reproducible.
6. El actor registra aceptación, rechazo, solicitud de reevaluación o excepción justificada según su competencia.
7. El cálculo original y la decisión humana quedan vinculados y auditados sin que uno sobrescriba al otro.

**Flujos alternos y excepciones**

- La falta de información se muestra expresamente y no se interpreta como compatibilidad.
- La urgencia no es inferida ni alterada por el algoritmo.
- Si una regla o método cambia, se produce una nueva evaluación y se conserva la anterior.
- Un servicio geográfico no disponible se reporta como dato faltante o degradación según el flujo autorizado; no se inventa distancia ni tiempo.
- El resultado no reserva, asigna ni descarta definitivamente un recurso por sí mismo.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-012, RF-MS-003, RF-MS-004, RF-MS-005, RF-DESK-004 |
| RNF | RNF-MS-001 a RNF-MS-006, RNF-DESK-002, RNF-DAT-001, RNF-DAT-004, RNF-SEC-002, RNF-SEC-006, RNF-SEC-008 |
| HU/HE | HU-MS-001, HU-DESK-003, HE-MS-001, HE-DAT-001 |
| RN | RN-GOB-001, RN-GOB-002, RN-GOB-005, RN-SOL-002, RN-SOL-004, RN-SOL-005, RN-SOL-006 |

### 5.5 CU-09 — Autorizar y controlar una asignación

| Campo | Definición |
| --- | --- |
| Actor principal | Coordinador regional, sujeto a la autorización clínica o normativa aplicable. |
| Actores de apoyo | Personal médico autorizado; servicio de inventario; servicio de auditoría. |
| Fase | Posterior. |
| Componentes | Sistema web; microservicios; PostgreSQL; Redis para bloqueo temporal cuando corresponda; alertas y auditoría. |
| Disparador | Existe una solicitud y un recurso candidato que requieren una decisión de reserva o asignación. |
| Precondiciones | Solicitud y recurso vigentes; resultados y advertencias disponibles; actor autorizado; recurso sin asignación activa incompatible. |
| Postcondiciones | La reserva, asignación, liberación, cancelación o reasignación queda confirmada una sola vez, con estado, motivo e historial. |

**Flujo principal**

1. El Coordinador abre la solicitud y selecciona un recurso candidato.
2. La plataforma muestra solicitud, recurso, evaluación disponible, versión, datos faltantes y advertencias aplicables.
3. El sistema vuelve a validar disponibilidad, permisos y ausencia de otra reserva o asignación activa incompatible.
4. El actor registra la confirmación humana, la justificación y la autorización adicional que corresponda.
5. La plataforma ejecuta la transición mediante la transacción, restricción o bloqueo definido.
6. Se persisten el nuevo estado y la relación con el cálculo revisado sin modificar el resultado algorítmico original.
7. Se generan auditoría y notificaciones para las instituciones y personas autorizadas.

**Flujos alternos y excepciones**

- Si otro proceso reservó o asignó el recurso, la confirmación se rechaza y se solicita actualizar las alternativas.
- Una liberación, cancelación o reasignación requiere transición válida y motivo; la operación anterior permanece en el historial.
- La falta de autorización humana aplicable impide confirmar la asignación.
- Un timeout con resultado incierto debe resolverse consultando el estado idempotente antes de reintentar.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-013, RF-DAT-003, RF-DAT-005, RF-SEC-003 |
| RNF | RNF-MS-003, RNF-MS-005, RNF-DAT-002, RNF-DAT-004, RNF-SEC-002, RNF-SEC-006, RNF-SEC-008 |
| HU/HE | HU-WEB-012, HE-DAT-001, HE-SEC-001 |
| RN | RN-GOB-001, RN-GOB-005, RN-SOL-006, RN-LOG-001, RN-LOG-002 |

## 6. Casos de uso de logística, supervisión y control

### 6.1 CU-10 — Planear y programar un traslado

| Campo | Definición |
| --- | --- |
| Actor principal | Coordinador regional. |
| Actores de apoyo | Instituciones de origen y destino; Personal de traslado; servicios geográfico y de transporte. |
| Fase | Posterior. |
| Componentes | Sistema web o aplicación de escritorio; microservicios; PostgreSQL; alertas. |
| Disparador | Un recurso asignado o autorizado requiere movimiento entre instituciones. |
| Precondiciones | Recurso, origen y destino identificados; autorización aplicable vigente; responsables disponibles. |
| Postcondiciones | Existe una orden de traslado con recurso, ruta, origen, destino, responsable, horario y estado inicial. |

**Flujo principal**

1. El Coordinador selecciona el recurso y las instituciones de origen y destino autorizadas.
2. La plataforma solicita al servicio geográfico las alternativas de distancia y tiempo estimado disponibles.
3. El servicio devuelve origen, destino, fuente, fecha, limitaciones y alternativas comparables, sin imponer una decisión.
4. El Coordinador elige la alternativa autorizada, asigna al Personal de traslado y establece el horario operativo.
5. La plataforma valida que la asignación del recurso y los participantes continúen vigentes.
6. Se crea la orden con estado inicial y se notifica únicamente a los participantes autorizados.
7. La creación y cualquier actualización posterior quedan auditadas.

**Flujos alternos y excepciones**

- Si la fuente geográfica no responde, la plataforma informa la degradación y aplica únicamente el procedimiento alternativo previamente autorizado.
- Una distancia o tiempo calculados conservan su fuente y limitaciones y no se presentan como garantía del traslado.
- Si el recurso deja de estar disponible antes de crear la orden, el flujo se detiene y no genera un traslado huérfano.
- El Personal de traslado solo recibe la información logística y clínica mínima indispensable.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-014, RF-MS-005, RF-MS-006, RF-MOV-005 |
| RNF | RNF-MS-002 a RNF-MS-005, RNF-DAT-001, RNF-SEC-002, RNF-SEC-005, RNF-SEC-006 |
| HU/HE | HU-MS-002, HU-MOV-005, HE-MS-001 |
| RN | RN-SOL-005, RN-LOG-003, RN-LOG-004, RN-LOG-005 |

### 6.2 CU-11 — Ejecutar traslado y documentar cadena de custodia

| Campo | Definición |
| --- | --- |
| Actor principal | Personal de traslado; Operador de banco de sangre o Coordinador regional según el evento. |
| Actores de apoyo | Instituciones de origen y destino; servicios de transporte, custodia, archivos y auditoría. |
| Fase | Posterior. |
| Componentes | Aplicación móvil mediante JSON; aplicación de escritorio mediante XML; microservicios; MongoDB o PostgreSQL según el evento; Redis y Google Cloud Storage. |
| Disparador | El Personal de traslado inicia la recolección o un actor autorizado debe registrar el siguiente evento de custodia. |
| Precondiciones | Orden activa y asignada; recurso identificado; actor y evento autorizados; periodo de captura vigente. |
| Postcondiciones | El evento queda registrado una sola vez, en secuencia, con responsable, fecha, condición y evidencia autorizada. |

**Flujo principal**

1. El Personal de traslado consulta únicamente sus órdenes activas y selecciona la correspondiente.
2. Escanea el código del recurso; la plataforma compara orden, recurso y siguiente evento esperado.
3. Cuando coinciden, el actor registra condición, confirmación y ubicación autorizada; puede adjuntar evidencia fotográfica dentro del periodo permitido.
4. La aplicación envía el evento con un identificador idempotente al servicio de custodia.
5. El servicio valida secuencia y permisos, registra el evento como append-only y actualiza el estado derivado de la orden.
6. La evidencia se almacena de forma privada en Google Cloud Storage y se conservan únicamente su referencia y metadatos autorizados.
7. En destino, el Operador o Coordinador registra el evento permitido desde móvil o escritorio y consulta el historial combinado sin duplicados.
8. Los componentes autorizados muestran el nuevo estado y la operación queda auditada.

**Flujos alternos y excepciones**

- Una discrepancia de código, orden o evento bloquea la confirmación y permite registrar una incidencia.
- Solo las operaciones definidas como seguras se conservan sin conexión; ninguna asignación o decisión clínica se confirma localmente.
- Al recuperar conectividad, la sincronización no duplica eventos y mantiene visibles los conflictos, rechazos o vencimientos.
- Una corrección genera un evento relacionado y no edita ni elimina el evento confirmado.
- Si se deniega cámara o ubicación, se presenta el procedimiento alternativo autorizado; la captura no continúa fuera del periodo permitido.
- Las copias locales innecesarias se eliminan al completar su finalidad.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-MS-006, RF-MOV-005, RF-MOV-006, RF-MOV-007, RF-DESK-006, RF-DAT-004, RF-DAT-005 |
| RNF | RNF-MS-002, RNF-MS-005, RNF-MOV-001 a RNF-MOV-004, RNF-DESK-002, RNF-DESK-003, RNF-DAT-001, RNF-DAT-003, RNF-SEC-002, RNF-SEC-003, RNF-SEC-006, RNF-SEC-007 |
| HU/HE | HU-MS-002, HU-MOV-005, HU-MOV-006, HU-MOV-007, HU-DESK-005, HE-MOV-001, HE-DESK-001, HE-DAT-001 |
| RN | RN-LOG-003, RN-LOG-004, RN-LOG-005, RN-LOG-006, RN-LOG-007, RN-COM-004 |

### 6.3 CU-12 — Supervisar paneles, alertas y pronósticos

| Campo | Definición |
| --- | --- |
| Actor principal | Administrador, Operador, Personal médico autorizado, Coordinador regional, Personal de traslado, Donante o Auditor, según la información dirigida. |
| Actores de apoyo | Servicios de inventario, alertas, priorización y pronóstico. |
| Fase | Transversal: panel básico para tres perfiles en el primer parcial; panel regional, alertas y pronósticos posteriormente. |
| Componentes | Sistema web; aplicación móvil para avisos; microservicios; PostgreSQL, MongoDB o Redis conforme al dato. |
| Disparador | Un usuario consulta su panel o recibe una alerta, o el Coordinador solicita un pronóstico autorizado. |
| Precondiciones | Sesión y ámbito válidos; datos persistidos disponibles; regla o método de alerta o pronóstico identificado. |
| Postcondiciones | La información se muestra al destinatario autorizado y cualquier acción sobre una alerta conserva su estado e historial. |

**Flujo principal**

1. El usuario accede al panel correspondiente a su perfil y ámbito.
2. En el primer parcial, la plataforma presenta únicamente datos persistidos y accesos autorizados de catálogos, inventario sanguíneo ficticio y auditoría.
3. En incrementos posteriores, el panel incorpora solicitudes, caducidad, traslados, indicadores regionales y gráficas Highcharts sustentadas por consultas verificables.
4. El servicio de alertas dirige eventos de urgencia, caducidad, retraso o inconsistencia solo a perfiles capaces de actuar y relaciona o deduplica repeticiones.
5. El usuario autorizado marca una alerta como leída, atendida o cerrada conforme al flujo permitido.
6. Cuando el Coordinador solicita un pronóstico, la plataforma muestra periodo, datos históricos o sintéticos, versión, factores, explicación y limitaciones.
7. El sistema registra las consultas o acciones sensibles que correspondan.

**Flujos alternos y excepciones**

- Un dato inexistente o no disponible se señala expresamente y no se reemplaza por una cifra simulada no identificada.
- Una alerta orienta la revisión, pero no ejecuta automáticamente una baja, transferencia o decisión clínica.
- Un pronóstico no modifica la fecha ni el estado real de la unidad y una sugerencia de balanceo no inicia automáticamente un traslado.
- Si una fuente se encuentra degradada, el panel diferencia la falta de datos de un valor igual a cero.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-015, RF-MS-007, RF-MS-009, RF-MOV-004 |
| RNF | RNF-WEB-001 a RNF-WEB-004, RNF-MS-004 a RNF-MS-006, RNF-SEC-002, RNF-SEC-006 |
| HU/HE | HU-WEB-013, HU-MS-003, HU-MS-004, HU-MOV-004, HE-WEB-001, HE-MS-001 |
| RN | RN-GOB-003, RN-GOB-005, RN-INV-005, RN-COM-001, RN-COM-002 |

### 6.4 CU-13 — Generar reportes y gestionar evidencia documental

| Campo | Definición |
| --- | --- |
| Actor principal | Operador de banco de sangre, Coordinador regional o Auditor, según permiso; otros perfiles autorizados para adjuntar evidencia. |
| Actores de apoyo | Servicio de archivos; Google Cloud Storage; institución responsable de los datos. |
| Fase | Posterior. |
| Componentes | Sistema web y aplicación de escritorio; microservicios; Google Cloud Storage y bases de metadatos. |
| Disparador | Un usuario necesita generar o exportar un reporte, o adjuntar, consultar o descargar evidencia de una operación. |
| Precondiciones | Sesión, ámbito, plantilla, operación y finalidad autorizados; almacenamiento disponible. |
| Postcondiciones | El reporte o archivo queda generado o vinculado con metadatos, privacidad y auditoría correspondientes. |

**Flujo principal**

1. El actor selecciona un reporte autorizado o una operación que admite evidencia.
2. Para un reporte, define únicamente periodo, institución, filtros y campos permitidos; para un archivo, selecciona el tipo y la finalidad autorizados.
3. La plataforma valida permisos, formato, tamaño, contenido permitido y disponibilidad de la fuente.
4. El reporte se genera con fecha, filtros, fuente y responsable, o el archivo se carga en un objeto privado con identificador, hash y metadatos.
5. La consulta o descarga utiliza un mecanismo temporal autorizado y no expone una ruta pública permanente.
6. La plataforma registra generación, carga, consulta o descarga cuando corresponda a información sensible.

**Flujos alternos y excepciones**

- Un formato no validado se identifica como académico u operativo y no como reporte regulatorio oficial.
- Una carga inválida se rechaza sin procesar contenido inseguro ni crear una referencia huérfana.
- Los archivos grandes no se almacenan directamente en PostgreSQL o MongoDB.
- Una exportación fuera de ámbito se deniega y no incluye columnas sensibles no autorizadas.
- Si Storage no está disponible, no se confirma la carga y se presenta una acción segura de reintento.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-016, RF-WEB-017, RF-DESK-007, RF-DAT-004 |
| RNF | RNF-DESK-002 a RNF-DESK-004, RNF-DAT-001, RNF-DAT-003, RNF-DAT-004, RNF-SEC-002, RNF-SEC-003, RNF-SEC-005, RNF-SEC-006 |
| HU/HE | HU-WEB-014, HU-WEB-015, HU-DESK-006, HE-DAT-001 |
| RN | RN-COM-003, RN-COM-004 |

### 6.5 CU-14 — Consultar auditoría y trazabilidad

| Campo | Definición |
| --- | --- |
| Actor principal | Auditor. |
| Actores de apoyo | Servicios de auditoría y de los procesos que originan eventos. |
| Fase | Transversal: alcance básico en el primer parcial y ampliación posterior. |
| Componentes | Sistema web; microservicio de auditoría; PostgreSQL o MongoDB conforme al diseño autoritativo. |
| Disparador | El Auditor necesita reconstruir una autenticación, cambio, decisión o evento dentro de su ámbito. |
| Precondiciones | Sesión de Auditor válida; permiso de consulta; periodo y ámbito definidos. |
| Postcondiciones | Se presentan eventos minimizados y de solo lectura; la propia consulta o exportación sensible queda registrada. |

**Flujo principal**

1. El Auditor abre la bitácora y define filtros de periodo, actor, institución, acción, entidad o resultado.
2. La plataforma valida el ámbito y el nivel de sensibilidad que puede consultar.
3. El servicio recupera los eventos autorizados con identificador, actor, tiempo, acción, entidad y resultado.
4. El Auditor consulta el detalle y las relaciones necesarias para reconstruir la secuencia sin modificar la operación.
5. Cuando posee permiso de exportación, genera una salida minimizada con filtros y responsable identificados.
6. La consulta o exportación sensible se registra como un nuevo evento de auditoría.

**Flujos alternos y excepciones**

- El Auditor no puede editar, eliminar, aprobar ni ejecutar la operación examinada.
- Una corrección del negocio aparece como un evento relacionado y no reemplaza el original.
- Los datos fuera de ámbito se omiten o se ocultan sin revelar su contenido.
- En el primer parcial la cobertura se limita a autenticación, usuarios, catálogos, unidades y cambios del MVP.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-WEB-018, RF-MS-008, RF-DAT-005, RF-SEC-003 |
| RNF | RNF-WEB-004, RNF-MS-004, RNF-DAT-001, RNF-DAT-004, RNF-SEC-002, RNF-SEC-006, RNF-SEC-008 |
| HU/HE | HU-WEB-016, HE-DAT-001, HE-SEC-001 |
| RN | RN-COM-005 |

### 6.6 CU-15 — Supervisar salud y disponibilidad técnica

| Campo | Definición |
| --- | --- |
| Actor principal | Administrador. |
| Actores de apoyo | Servicio de monitoreo; componentes supervisados; responsables técnicos configurados. |
| Fase | Posterior. |
| Componentes | Servicio y panel de monitoreo; endpoints de salud; logs y métricas centralizables. |
| Disparador | Se ejecuta una verificación periódica, cambia el estado de un componente o el Administrador consulta el panel. |
| Precondiciones | Endpoints de salud configurados y acceso técnico autorizado. |
| Postcondiciones | El estado actual, historial, causa conocida y aviso aplicable quedan registrados sin afectar la operación del negocio. |

**Flujo principal**

1. El servicio de monitoreo consulta periódicamente los endpoints aplicables de proceso, PostgreSQL, MongoDB, Redis y Storage.
2. Clasifica cada resultado como disponible, degradado o caído y distingue proceso detenido, dependencia inaccesible, respuesta inválida y timeout.
3. Registra versión, fecha de verificación, latencia, errores y causa conocida con timestamps e identificadores de correlación.
4. El Administrador consulta el estado actual y el historial por servicio y periodo.
5. Una caída, degradación o recuperación genera un aviso a los responsables configurados y actualiza el incidente relacionado.
6. La recuperación conserva los eventos anteriores y permite comprobar la duración del incidente.

**Flujos alternos y excepciones**

- Una dependencia no aplicable se identifica como tal y no se reporta falsamente como saludable.
- La indisponibilidad del monitoreo no detiene las funciones propias de los servicios supervisados.
- Las señales operativas no incluyen datos clínicos, tokens, secretos, ubicaciones o fotografías innecesarias.
- Los avisos repetidos se agrupan o relacionan sin perder la duración ni los cambios de estado.

**Trazabilidad principal**

| Tipo | Identificadores |
| --- | --- |
| RF | RF-MON-001, RF-MON-002, RF-MON-003, RF-MON-004 |
| RNF | RNF-MS-004, RNF-MS-005, RNF-INF-007, RNF-MON-001, RNF-MON-002, RNF-MON-003 |
| HU/HE | HU-MON-001, HU-MON-002, HE-MON-001, HE-INF-002 |
| RN | No existe una regla de negocio específica; aplican los controles técnicos y de seguridad transversales. |

## 7. Cobertura incremental

| Incremento | Casos de uso considerados |
| --- | --- |
| Primer parcial | `CU-01`, `CU-02`, `CU-03`, flujo sanguíneo inicial de `CU-04`, panel básico de `CU-12` y alcance básico de `CU-14`. |
| Segundo parcial | `CU-05` a `CU-11` y `CU-13`, junto con la ampliación distribuida de los casos transversales. |
| Tercer parcial | Integración completa de `CU-08` a `CU-15`, algoritmos, nube, monitoreo, volumen y recuperación ante fallos. |
| Entrega final | Regresión y demostración integral de los quince casos conforme al alcance implementado. |

La inclusión de un caso en un incremento posterior no autoriza a anticipar reglas clínicas sin validar. Del mismo modo, documentar el alcance completo no implica que todos los casos estén implementados en el primer parcial.

## 8. Criterio de mantenimiento

Un cambio de requerimiento, historia, regla, perfil o arquitectura deberá revisarse contra los casos relacionados y contra la matriz de trazabilidad integral. Se conservarán los identificadores de los casos mientras su objetivo permanezca estable; una modificación material del objetivo deberá registrarse como una nueva versión para no alterar retrospectivamente la evidencia de pruebas o decisiones ya documentadas.
