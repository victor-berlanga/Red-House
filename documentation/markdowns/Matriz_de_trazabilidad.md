# Matriz de trazabilidad integral

> **Proyecto:** Red regional de bancos de sangre y donación de órganos — Equipo 01.  
> **Estado:** línea base documental del alcance completo.  
> **Fecha:** 7 de septiembre de 2026.<br>
> **Cobertura:** 94 requerimientos, 44 historias, 40 reglas de negocio y 15 casos de uso principales.

## 1. Propósito y alcance

La matriz vincula cada requerimiento funcional y no funcional con la historia de usuario o habilitadora que lo desarrolla, las reglas de negocio aplicables, el caso de uso principal que lo materializa y la evidencia prevista para comprobarlo. La definición completa de cada elemento permanece en su documento de origen; los textos breves de esta matriz sirven únicamente para facilitar su identificación.

La cobertura corresponde a todo el semestre. La fase **Primer parcial** delimita el producto mínimo funcional, **Posterior** identifica capacidades de los siguientes incrementos y **Transversal** señala obligaciones que se aplican cada vez que el proceso relacionado entra en operación. La matriz no presenta como implementados los elementos que solo se encuentran documentados.

Las relaciones clínicas o regulatorias conservan su clasificación original. Hasta disponer de validación competente, su verificación académica utilizará datos ficticios, reglas demostrativas identificadas y comprobación explícita de la intervención humana.

## 2. Modelo de trazabilidad

### 2.1 Elementos relacionados

| Elemento | Función dentro de la matriz |
| --- | --- |
| RF / RNF | Necesidad funcional o cualidad verificable que constituye el punto de partida de cada fila. |
| HU / HE | Historia de usuario o historia habilitadora que expresa el valor o capacidad técnica relacionada. |
| RN | Regla de negocio existente que condiciona la operación. Un guion indica que el requisito es un control técnico sin regla de negocio específica. |
| CU | Caso de uso principal que organiza el comportamiento observable. En un RNF puede indicarse una aplicación transversal a varios casos. |
| VT | Tipo de evidencia mediante la cual se comprobará el requisito en el incremento correspondiente. |

### 2.2 Tipos de verificación

| Código | Evidencia prevista |
| --- | --- |
| `VT-01` | Prueba funcional o demostración del flujo con resultado esperado, persistencia real y auditoría cuando corresponda. |
| `VT-02` | Prueba de autenticación, autorización, ámbito, sesión, revocación, ocultamiento o manejo seguro de errores. |
| `VT-03` | Prueba de contrato HTTP, JSON, XML/XSD, versionamiento, validación y documentación OpenAPI/Swagger. |
| `VT-04` | Prueba de persistencia, integridad, transacción, índices, metadatos, retención, respaldo o restauración. |
| `VT-05` | Evidencia reproducible de repositorio, variables, contenedores, integración continua, red o despliegue. |
| `VT-06` | Prueba de salud, timeout, dependencia inaccesible, degradación, recuperación e idempotencia. |
| `VT-07` | Medición de carga, concurrencia, consumo, media, p95, p99, errores y recuperación mediante el conjunto de datos definido. |
| `VT-08` | Prueba de interfaz, accesibilidad, dispositivo, conectividad, sincronización o tarea de usabilidad. |
| `VT-09` | Validación clínica/normativa o, mientras esté pendiente, demostración identificada con datos ficticios, explicación y control humano. |

## 3. Resumen de cobertura

| Componente | RF | RNF | Total | Historias principales |
| --- | --- | --- | --- | --- |
| Sistema web | 18 | 4 | 22 | HU-WEB-001 a HU-WEB-016; HE-WEB-001 |
| Microservicios | 9 | 6 | 15 | HU-MS-001 a HU-MS-004; HE-MS-001 |
| Aplicación móvil | 7 | 4 | 11 | HU-MOV-001 a HU-MOV-007; HE-MOV-001 |
| Aplicación de escritorio | 7 | 4 | 11 | HU-DESK-001 a HU-DESK-006; HE-DESK-001 |
| Bases de datos y almacenamiento | 5 | 4 | 9 | HE-DAT-001 y HU funcionales relacionadas |
| Infraestructura e integración | 0 | 8 | 8 | HE-INF-001, HE-INF-002 |
| Seguridad y privacidad | 3 | 8 | 11 | HE-SEC-001 y HU de acceso o auditoría relacionadas |
| Monitoreo y observabilidad | 4 | 3 | 7 | HU-MON-001, HU-MON-002, HE-MON-001 |
| **Total** | **53** | **41** | **94** | **35 HU y 9 HE** |

## 4. Matriz general de trazabilidad

La siguiente matriz presenta el encadenamiento general entre los ocho componentes, sus requerimientos, las historias que los desarrollan, las familias de reglas aplicables, los casos de uso y las evidencias previstas. Integra elementos de las matrices detalladas para facilitar una lectura inicial del sistema completo antes de consultar cada relación individual.

Los rangos y las familias representan cobertura agrupada y no significan que cada regla, caso de uso o tipo de verificación se aplique a todos los requerimientos del componente. Las asociaciones exactas y la fase **Primer parcial**, **Posterior** o **Transversal** se especifican en los apartados siguientes.

| Componente y alcance | RF/RNF | HU/HE | RN | CU | VT |
| --- | --- | --- | --- | --- | --- |
| **Sistema web**<br>Portal público y privado, administración, operación, paneles, archivos y auditoría. | RF-WEB-001 a RF-WEB-018;<br>RNF-WEB-001 a RNF-WEB-004 | HU-WEB-001 a HU-WEB-016;<br>HU-MS-001, HU-MS-002;<br>HE-WEB-001 | Familias RN-GOB, RN-ACC, RN-PER, RN-INV, RN-SOL, RN-LOG y RN-COM | CU-01 a CU-14 | VT-01, VT-02 y VT-04 a VT-09 |
| **Microservicios**<br>Capacidades compartidas del dominio, contratos, integración, algoritmos y resiliencia. | RF-MS-001 a RF-MS-009;<br>RNF-MS-001 a RNF-MS-006 | HU-MS-001 a HU-MS-004;<br>HE-MS-001;<br>historias consumidoras de web, móvil y escritorio | Familias RN-GOB, RN-PER, RN-INV, RN-SOL, RN-LOG y RN-COM | CU-01 y CU-04 a CU-15 | VT-01 a VT-07 y VT-09 |
| **Aplicación móvil**<br>Participación del Donante y ejecución autorizada del traslado mediante JSON. | RF-MOV-001 a RF-MOV-007;<br>RNF-MOV-001 a RNF-MOV-004 | HU-MOV-001 a HU-MOV-007;<br>HE-MOV-001 | Familias RN-ACC, RN-PER, RN-LOG y RN-COM | CU-01, CU-05 y CU-10 a CU-12 | VT-01 a VT-06, VT-08 y VT-09 |
| **Aplicación de escritorio**<br>Operación interna, revisión, etiquetas, custodia y reportes mediante XML/XSD. | RF-DESK-001 a RF-DESK-007;<br>RNF-DESK-001 a RNF-DESK-004 | HU-DESK-001 a HU-DESK-006;<br>HE-DESK-001 | Familias RN-GOB, RN-ACC, RN-INV, RN-SOL, RN-LOG y RN-COM | CU-01, CU-04, CU-07, CU-08, CU-11 y CU-13 | VT-01 a VT-06, VT-08 y VT-09 |
| **Bases de datos y almacenamiento**<br>Persistencia estructurada y documental, datos temporales, archivos y trazabilidad. | RF-DAT-001 a RF-DAT-005;<br>RNF-DAT-001 a RNF-DAT-004 | HE-DAT-001;<br>HU-WEB-015 y HU-WEB-016 | RN-LOG-002, RN-LOG-005, RN-COM-004 y RN-COM-005 | CU-01 a CU-15 | VT-01 a VT-04, VT-06 y VT-07 |
| **Infraestructura e integración**<br>Repositorio, contenedores, despliegue, procesos integrales y recuperación. | RNF-INF-001 a RNF-INF-008 | HE-INF-001 y HE-INF-002 | Sin RN específica; aplican controles técnicos transversales | Habilita CU-01 a CU-15 | VT-01 a VT-09 |
| **Seguridad y privacidad**<br>Identidad, autorización, protección de datos, secretos y auditoría de accesos. | RF-SEC-001 a RF-SEC-003;<br>RNF-SEC-001 a RNF-SEC-008 | HE-SEC-001;<br>historias de acceso y auditoría relacionadas | Familias RN-ACC, RN-LOG y RN-COM | Transversal a CU-01 a CU-15 | VT-01 a VT-09 |
| **Monitoreo y observabilidad**<br>Salud, dependencias, disponibilidad, métricas, incidentes y avisos técnicos. | RF-MON-001 a RF-MON-004;<br>RNF-MON-001 a RNF-MON-003 | HU-MON-001, HU-MON-002 y HE-MON-001 | Sin RN específica; aplican controles técnicos y de seguridad | CU-15 | VT-01, VT-02 y VT-04 a VT-08 |
| **Cobertura integral**<br>Relación consolidada de los ocho componentes. | 53 RF y 41 RNF | 35 HU y 9 HE | 40 RN | 15 CU | 9 VT |

## 5. Sistema web empresarial

| Requisito y alcance breve | HU/HE | RN aplicables | CU principal | Verificación |
| --- | --- | --- | --- | --- |
| **RF-WEB-001**<br>Primer parcial<br>Sitio público sin información restringida. | HU-WEB-001 | RN-ACC-004 | CU-01 | VT-01, VT-02, VT-08 |
| **RF-WEB-002**<br>Transversal<br>Inicio, cierre y recuperación segura de sesión. | HU-WEB-002 | RN-ACC-002 | CU-01 | VT-01, VT-02 |
| **RF-WEB-003**<br>Primer parcial<br>Usuarios, perfiles, ámbitos y menús autorizados. | HU-WEB-003 | RN-ACC-001, RN-ACC-002, RN-ACC-003 | CU-02 | VT-01, VT-02 |
| **RF-WEB-004**<br>Primer parcial<br>Catálogos y parámetros controlados. | HU-WEB-004 | RN-ACC-005, RN-ACC-006 | CU-03 | VT-01, VT-02, VT-04 |
| **RF-WEB-005**<br>Primer parcial<br>Instituciones y sedes como fuente conceptual única. | HU-WEB-005 | RN-ACC-005 | CU-03 | VT-01, VT-02, VT-04 |
| **RF-WEB-006**<br>Posterior<br>Expediente autorizado de donantes. | HU-WEB-006 | RN-GOB-004, RN-PER-002 | CU-05 | VT-01, VT-02, VT-09 |
| **RF-WEB-007**<br>Posterior<br>Expediente protegido de receptores o pacientes. | HU-WEB-007 | RN-GOB-004, RN-PER-004 | CU-06 | VT-01, VT-02, VT-09 |
| **RF-WEB-008**<br>Primer parcial<br>Inventario sanguíneo ficticio y caducidad demostrativa. | HU-WEB-008 | RN-GOB-003, RN-GOB-004, RN-INV-001, RN-INV-002 | CU-04 | VT-01, VT-04, VT-09 |
| **RF-WEB-009**<br>Posterior<br>Disponibilidad y viabilidad de órganos mediante flujo separado. | HU-WEB-009 | RN-GOB-004, RN-INV-003 | CU-04 | VT-01, VT-02, VT-09 |
| **RF-WEB-010**<br>Posterior<br>Solicitudes ordinarias y urgentes. | HU-WEB-010 | RN-PER-004, RN-SOL-001, RN-SOL-002 | CU-06 | VT-01, VT-02, VT-09 |
| **RF-WEB-011**<br>Posterior<br>Captura y consulta de pruebas o estudios diferenciados. | HU-WEB-011 | RN-INV-004, RN-SOL-003 | CU-07 | VT-01, VT-02, VT-09 |
| **RF-WEB-012**<br>Posterior<br>Candidatos, compatibilidad y priorización explicables. | HU-MS-001 | RN-GOB-001, RN-GOB-005, RN-SOL-004, RN-SOL-006 | CU-08 | VT-01, VT-07, VT-09 |
| **RF-WEB-013**<br>Posterior<br>Reserva y asignación con confirmación humana. | HU-WEB-012 | RN-GOB-001, RN-LOG-001, RN-LOG-002 | CU-09 | VT-01, VT-02, VT-04, VT-09 |
| **RF-WEB-014**<br>Posterior<br>Programación y seguimiento de traslados y custodia. | HU-MS-002 | RN-LOG-003 | CU-10, CU-11 | VT-01, VT-02, VT-06 |
| **RF-WEB-015**<br>Primer parcial<br>Panel básico por perfil y evolución regional. | HU-WEB-013 | RN-ACC-001, RN-COM-002 | CU-12 | VT-01, VT-02, VT-08 |
| **RF-WEB-016**<br>Posterior<br>Reportes operativos o regulatorios autorizados. | HU-WEB-014 | RN-COM-003 | CU-13 | VT-01, VT-02, VT-09 |
| **RF-WEB-017**<br>Posterior<br>Carga y consulta controlada de archivos y evidencias. | HU-WEB-015 | RN-COM-004 | CU-13 | VT-01, VT-02, VT-04 |
| **RF-WEB-018**<br>Primer parcial<br>Consulta de auditoría de solo lectura. | HU-WEB-016 | RN-COM-005 | CU-14 | VT-01, VT-02, VT-04 |
| **RNF-WEB-001**<br>Primer parcial<br>Tecnologías web obligatorias y Highcharts. | HE-WEB-001 | — | CU-01 a CU-04, CU-12, CU-14 | VT-05, VT-08 |
| **RNF-WEB-002**<br>Transversal<br>Independencia respecto de móvil y escritorio. | HE-WEB-001 | — | Transversal a los CU del sistema web | VT-05, VT-06 |
| **RNF-WEB-003**<br>Primer parcial<br>Interfaz responsive, accesible y consultable. | HE-WEB-001 | — | Transversal a los CU del sistema web | VT-01, VT-08 |
| **RNF-WEB-004**<br>Primer parcial<br>Persistencia real y errores seguros. | HE-WEB-001 | — | Transversal a los CU del sistema web | VT-01, VT-02, VT-04, VT-06 |

## 6. Módulo de microservicios

| Requisito y alcance breve | HU/HE | RN aplicables | CU principal | Verificación |
| --- | --- | --- | --- | --- |
| **RF-MS-001**<br>Posterior<br>Servicios separados para donantes y receptores. | HU-WEB-006, HU-WEB-007, HU-MOV-002 | RN-GOB-004, RN-PER-001, RN-PER-002 | CU-05, CU-06 | VT-01, VT-02, VT-03, VT-09 |
| **RF-MS-002**<br>Posterior<br>Inventario sanguíneo y tratamiento especializado de órganos. | HU-WEB-008, HU-WEB-009, HU-DESK-002 | RN-GOB-003, RN-GOB-004, RN-INV-001, RN-INV-003 | CU-04 | VT-01, VT-03, VT-04, VT-09 |
| **RF-MS-003**<br>Posterior<br>Matching sanguíneo y HLA versionado y explicable. | HU-MS-001 | RN-GOB-001, RN-GOB-002, RN-GOB-005, RN-SOL-004 | CU-08 | VT-01, VT-03, VT-07, VT-09 |
| **RF-MS-004**<br>Posterior<br>Ranking multicriterio con urgencia autorizada, tiempo y distancia. | HU-MS-001 | RN-GOB-001, RN-GOB-002, RN-GOB-005, RN-SOL-002, RN-SOL-005 | CU-08 | VT-01, VT-03, VT-07, VT-09 |
| **RF-MS-005**<br>Posterior<br>Comparación u optimización por distancia y tiempo. | HU-MS-002 | RN-SOL-005 | CU-08, CU-10 | VT-01, VT-03, VT-06, VT-09 |
| **RF-MS-006**<br>Posterior<br>Transporte y cadena de custodia secuencial. | HU-MS-002 | RN-LOG-003, RN-LOG-005 | CU-10, CU-11 | VT-01, VT-03, VT-06 |
| **RF-MS-007**<br>Posterior<br>Alertas de urgencia, caducidad, retraso e inconsistencias. | HU-MS-003 | RN-COM-001 | CU-12 | VT-01, VT-03, VT-06 |
| **RF-MS-008**<br>Posterior<br>Recepción y consulta de eventos de auditoría. | HU-WEB-016 | RN-COM-005 | CU-14 | VT-01, VT-02, VT-03, VT-04 |
| **RF-MS-009**<br>Posterior<br>Pronóstico de caducidad y sugerencias de balanceo. | HU-MS-004 | RN-GOB-003, RN-GOB-005, RN-INV-005 | CU-12 | VT-01, VT-07, VT-09 |
| **RNF-MS-001**<br>Posterior<br>Flask REST versionado y contenedores independientes desde el segundo parcial. | HE-MS-001 | — | Transversal a CU-05 a CU-15 | VT-03, VT-05 |
| **RNF-MS-002**<br>Posterior<br>Respuestas JSON y XML, OpenAPI/Swagger y XSD. | HE-MS-001 | — | Transversal a CU-05 a CU-15 | VT-03 |
| **RNF-MS-003**<br>Posterior<br>Validación de JWT, sesión, revocación y permisos. | HE-MS-001 | — | CU-01 y operaciones protegidas de CU-05 a CU-15 | VT-02, VT-03 |
| **RNF-MS-004**<br>Posterior<br>Límites de consumo, logs y correlación. | HE-MS-001 | — | Transversal a CU-05 a CU-15 | VT-02, VT-03, VT-07 |
| **RNF-MS-005**<br>Posterior<br>Timeouts, reintentos, idempotencia y fallos controlados. | HE-MS-001 | — | CU-08 a CU-15 | VT-03, VT-06 |
| **RNF-MS-006**<br>Posterior<br>Métricas de algoritmos y carga con Locust. | HE-MS-001 | — | CU-08, CU-11, CU-12, CU-15 | VT-07 |

## 7. Aplicación móvil Android

| Requisito y alcance breve | HU/HE | RN aplicables | CU principal | Verificación |
| --- | --- | --- | --- | --- |
| **RF-MOV-001**<br>Posterior<br>Sesión JWT, perfil y menú para Donante y Traslado. | HU-MOV-001 | RN-ACC-002 | CU-01 | VT-01, VT-02, VT-08 |
| **RF-MOV-002**<br>Posterior<br>Registro preliminar del donante. | HU-MOV-002 | RN-PER-001 | CU-05 | VT-01, VT-02, VT-03, VT-09 |
| **RF-MOV-003**<br>Posterior<br>Campañas y gestión de citas. | HU-MOV-003 | RN-PER-005 | CU-05 | VT-01, VT-03, VT-08 |
| **RF-MOV-004**<br>Posterior<br>Avisos autorizados de elegibilidad o seguimiento. | HU-MOV-004 | RN-PER-003, RN-COM-001 | CU-05, CU-12 | VT-01, VT-02, VT-09 |
| **RF-MOV-005**<br>Posterior<br>Órdenes, escaneo, recolección y entrega. | HU-MOV-005 | RN-LOG-004 | CU-10, CU-11 | VT-01, VT-03, VT-08 |
| **RF-MOV-006**<br>Posterior<br>Ubicación y evidencia fotográfica autorizadas. | HU-MOV-006 | RN-LOG-006 | CU-11 | VT-01, VT-02, VT-04, VT-08 |
| **RF-MOV-007**<br>Posterior<br>Operación temporal sin conexión y sincronización. | HU-MOV-007 | RN-LOG-007 | CU-05, CU-11 | VT-01, VT-06, VT-08 |
| **RNF-MOV-001**<br>Posterior<br>Android en Java o Kotlin y consumo exclusivo de JSON. | HE-MOV-001 | — | CU-01, CU-05, CU-10 a CU-12 | VT-03, VT-05, VT-08 |
| **RNF-MOV-002**<br>Posterior<br>Protección de dispositivo, tokens y datos temporales. | HE-MOV-001 | — | CU-01, CU-05, CU-11 | VT-02, VT-08 |
| **RNF-MOV-003**<br>Posterior<br>Conectividad, validación y errores sin pérdida silenciosa. | HE-MOV-001 | — | CU-01, CU-05, CU-11 | VT-06, VT-08 |
| **RNF-MOV-004**<br>Posterior<br>Capacidades del dispositivo y pruebas de usabilidad. | HE-MOV-001 | — | CU-05, CU-11 | VT-08 |

## 8. Aplicación de escritorio

| Requisito y alcance breve | HU/HE | RN aplicables | CU principal | Verificación |
| --- | --- | --- | --- | --- |
| **RF-DESK-001**<br>Posterior<br>Sesión JWT y menú para Operador y Coordinador. | HU-DESK-001 | RN-ACC-002 | CU-01 | VT-01, VT-02, VT-03 |
| **RF-DESK-002**<br>Posterior<br>Registro de unidades e inventario mediante servicios. | HU-DESK-002 | RN-INV-001 | CU-04 | VT-01, VT-03, VT-04, VT-09 |
| **RF-DESK-003**<br>Posterior<br>Captura y consulta de pruebas con revisión. | HU-DESK-002 | RN-INV-004, RN-SOL-003 | CU-07 | VT-01, VT-03, VT-09 |
| **RF-DESK-004**<br>Posterior<br>Revisión de compatibilidad, priorización y decisión humana. | HU-DESK-003 | RN-GOB-002, RN-SOL-006 | CU-08 | VT-01, VT-03, VT-09 |
| **RF-DESK-005**<br>Posterior<br>Impresión de etiquetas autorizadas. | HU-DESK-004 | RN-INV-006 | CU-04 | VT-01, VT-08, VT-09 |
| **RF-DESK-006**<br>Posterior<br>Registro y consulta de cadena de custodia. | HU-DESK-005 | RN-LOG-005 | CU-11 | VT-01, VT-03, VT-06 |
| **RF-DESK-007**<br>Posterior<br>Tablas, búsqueda, filtros y exportación de reportes. | HU-DESK-006 | RN-COM-003 | CU-13 | VT-01, VT-02, VT-08, VT-09 |
| **RNF-DESK-001**<br>Posterior<br>Tecnología autorizada y desacoplamiento del sistema web. | HE-DESK-001 | — | CU-01, CU-04, CU-07, CU-08, CU-11, CU-13 | VT-03, VT-05 |
| **RNF-DESK-002**<br>Posterior<br>Consumo exclusivo de XML, XSD y protección XXE. | HE-DESK-001 | — | CU-01, CU-04, CU-07, CU-08, CU-11, CU-13 | VT-02, VT-03 |
| **RNF-DESK-003**<br>Posterior<br>Sesión, permisos y recuperación segura de captura. | HE-DESK-001 | — | CU-01, CU-04, CU-07, CU-08, CU-11, CU-13 | VT-02, VT-03, VT-06 |
| **RNF-DESK-004**<br>Posterior<br>Usabilidad de captura, consulta, exportación e impresión. | HE-DESK-001 | — | CU-04, CU-07, CU-08, CU-11, CU-13 | VT-08 |

## 9. Bases de datos y almacenamiento

| Requisito y alcance breve | HU/HE | RN aplicables | CU principal | Verificación |
| --- | --- | --- | --- | --- |
| **RF-DAT-001**<br>Primer parcial<br>Persistencia estructurada inicial en PostgreSQL. | HE-DAT-001 | — | CU-02, CU-03, CU-04, CU-06, CU-07, CU-09, CU-14 | VT-01, VT-04 |
| **RF-DAT-002**<br>Posterior<br>Documentos flexibles, telemetría e historiales en MongoDB. | HE-DAT-001 | — | CU-08, CU-11, CU-12, CU-14, CU-15 | VT-01, VT-04, VT-07 |
| **RF-DAT-003**<br>Posterior<br>Sesiones, revocación, caché, límites y temporales en Redis desde el segundo parcial. | HE-DAT-001 | — | CU-01, CU-09, CU-12 | VT-02, VT-04, VT-06 |
| **RF-DAT-004**<br>Posterior<br>Archivos y evidencias en Google Cloud Storage. | HU-WEB-015, HE-DAT-001 | RN-COM-004 | CU-11, CU-13 | VT-01, VT-02, VT-04, VT-06 |
| **RF-DAT-005**<br>Transversal<br>Datos mínimos para reconstruir auditoría y custodia. | HU-WEB-016, HE-DAT-001 | RN-LOG-005, RN-COM-005 | CU-04, CU-09, CU-11, CU-14 | VT-01, VT-04 |
| **RNF-DAT-001**<br>Transversal<br>Sin acceso directo de clientes y un propietario por dato. | HE-DAT-001 | — | Transversal a CU-01 a CU-15 | VT-02, VT-03, VT-04 |
| **RNF-DAT-002**<br>Transversal<br>Prevención de estados contradictorios y doble asignación. | HE-DAT-001 | RN-LOG-002 | CU-09 | VT-04, VT-06 |
| **RNF-DAT-003**<br>Posterior<br>Archivos grandes fuera de bases y URLs firmadas. | HE-DAT-001 | RN-COM-004 | CU-11, CU-13 | VT-02, VT-04, VT-06 |
| **RNF-DAT-004**<br>Transversal<br>Claves, índices, crecimiento, retención, respaldo y pruebas. | HE-DAT-001 | — | Transversal a CU-01 a CU-15 | VT-04, VT-07 |

## 10. Infraestructura e integración

| Requisito y alcance breve | HU/HE | RN aplicables | CU principal | Verificación |
| --- | --- | --- | --- | --- |
| **RNF-INF-001**<br>Primer parcial<br>Ramas, incidencias, tablero, estándares y nombres. | HE-INF-001 | — | Habilita todos los CU | VT-05 |
| **RNF-INF-002**<br>Primer parcial<br>Dependencias y variables sin secretos versionados. | HE-INF-001 | — | Habilita todos los CU | VT-02, VT-05 |
| **RNF-INF-003**<br>Posterior<br>Dockerfile y Docker Compose con los tres almacenes desde el segundo parcial. | HE-INF-001 | — | Habilita los CU distribuidos desde el segundo parcial | VT-05, VT-06 |
| **RNF-INF-004**<br>Posterior<br>Distribución segura en Google Compute Engine. | HE-INF-001 | — | Habilita todos los CU desplegados | VT-02, VT-05, VT-06 |
| **RNF-INF-005**<br>Posterior<br>Integración y despliegue independientes. | HE-INF-001 | — | Habilita todos los CU desplegados | VT-05, VT-06 |
| **RNF-INF-006**<br>Posterior<br>Tres procesos integrales y consulta entre clientes autorizados. | HE-INF-002 | — | CU-05; CU-06 a CU-11 | VT-01, VT-03, VT-05 |
| **RNF-INF-007**<br>Posterior<br>Detección y recuperación ante fallas parciales. | HE-INF-002 | — | Transversal a los CU integrados | VT-06 |
| **RNF-INF-008**<br>Transversal<br>Pruebas proporcionales al riesgo de cada incremento. | HE-INF-002 | — | Transversal a CU-01 a CU-15 | VT-01 a VT-09 |

## 11. Seguridad y privacidad

| Requisito y alcance breve | HU/HE | RN aplicables | CU principal | Verificación |
| --- | --- | --- | --- | --- |
| **RF-SEC-001**<br>Transversal<br>Emisión, renovación, rotación, expiración y revocación. | HU-WEB-002, HU-MOV-001, HU-DESK-001, HE-SEC-001 | RN-ACC-002 | CU-01 | VT-01, VT-02, VT-03 |
| **RF-SEC-002**<br>Primer parcial<br>Asignación de perfiles y ámbitos sin facultad clínica implícita. | HU-WEB-003, HE-SEC-001 | RN-ACC-001, RN-ACC-002, RN-ACC-003 | CU-02 | VT-01, VT-02 |
| **RF-SEC-003**<br>Transversal<br>Registro de intentos, accesos y operaciones críticas. | HU-WEB-002, HU-WEB-016, HE-SEC-001 | RN-COM-005 | CU-01, CU-09, CU-14 | VT-01, VT-02, VT-04 |
| **RNF-SEC-001**<br>Transversal<br>Hash y expiración iniciales; renovación y revocación con Redis desde el segundo parcial. | HE-SEC-001 | — | CU-01 | VT-02 |
| **RNF-SEC-002**<br>Transversal<br>Mínimo privilegio por rol, acción, recurso y ámbito. | HE-SEC-001 | RN-ACC-002 | Transversal a CU-01 a CU-15 | VT-02 |
| **RNF-SEC-003**<br>Transversal<br>Consultas y entradas seguras, incluida protección XXE. | HE-SEC-001 | — | Transversal a CU-01 a CU-15 | VT-02, VT-03 |
| **RNF-SEC-004**<br>Transversal<br>Rate limiting, intentos fallidos y bloqueo temporal. | HE-SEC-001 | — | CU-01 y servicios protegidos | VT-02, VT-07 |
| **RNF-SEC-005**<br>Transversal<br>Comunicaciones cifradas y secretos fuera del código. | HE-SEC-001 | — | Transversal a CU-01 a CU-15 | VT-02, VT-05 |
| **RNF-SEC-006**<br>Transversal<br>Minimización en interfaces, respuestas, logs y errores. | HE-SEC-001 | — | Transversal a CU-01 a CU-15 | VT-02, VT-08 |
| **RNF-SEC-007**<br>Posterior<br>Finalidad y periodo autorizados para ubicación y fotografías. | HE-SEC-001 | RN-LOG-006 | CU-11 | VT-02, VT-04, VT-08, VT-09 |
| **RNF-SEC-008**<br>Transversal<br>Consentimiento, retención, eliminación e intercambio validados. | HE-SEC-001 | — | CU-04 a CU-14 según el dato | VT-02, VT-04, VT-09 |

## 12. Monitoreo y observabilidad

| Requisito y alcance breve | HU/HE | RN aplicables | CU principal | Verificación |
| --- | --- | --- | --- | --- |
| **RF-MON-001**<br>Posterior<br>Consulta periódica de proceso y dependencias. | HU-MON-001 | — | CU-15 | VT-01, VT-06 |
| **RF-MON-002**<br>Posterior<br>Panel de estado, latencia, errores, versión y causa. | HU-MON-001 | — | CU-15 | VT-01, VT-06, VT-08 |
| **RF-MON-003**<br>Posterior<br>Historial de disponibilidad y cambios de estado. | HU-MON-002 | — | CU-15 | VT-01, VT-04, VT-06 |
| **RF-MON-004**<br>Posterior<br>Avisos de caída, degradación y recuperación. | HU-MON-002 | — | CU-15 | VT-01, VT-06 |
| **RNF-MON-001**<br>Posterior<br>Estados diferenciados para proceso, dependencia y timeout. | HE-MON-001 | — | CU-15 | VT-06 |
| **RNF-MON-002**<br>Posterior<br>Monitoreo no bloqueante para el negocio. | HE-MON-001 | — | CU-15 | VT-06, VT-07 |
| **RNF-MON-003**<br>Posterior<br>Logs y métricas centralizables, correlacionados y minimizados. | HE-MON-001 | — | CU-15 | VT-02, VT-05, VT-06 |

## 13. Control de integridad y cambios

La línea base contiene una fila única para cada uno de los 53 RF y 41 RNF consolidados. Una relación indica cobertura documental y planificada; no demuestra por sí misma que la funcionalidad esté implementada o que una regla clínica haya sido autorizada.

Cuando cambie un elemento se deberán revisar sus relaciones en ambos sentidos:

1. Un RF o RNF modificado deberá conservar o actualizar su HU/HE, reglas, caso de uso y verificación.
2. Una historia o regla modificada deberá revisarse contra todos los requerimientos que la citan.
3. Un caso de uso modificado deberá mantener consistencia con actores, permisos, arquitectura y criterios de aceptación.
4. La evidencia de una versión ejecutada no se sobrescribirá cuando cambie posteriormente una regla, contrato o algoritmo.
5. Los identificadores eliminados o sustituidos deberán conservarse en el historial de cambios para no crear referencias silenciosamente inválidas.
