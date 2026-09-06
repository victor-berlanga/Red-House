# Sprint Backlog — Plan de trabajo del semestre

> **Proyecto:** Red regional de bancos de sangre y donación de órganos — Equipo 01.  
> **Versión:** cierre del primer parcial.  
> **Fecha:** 7 de septiembre de 2026.  
> **Cobertura:** cuatro sprints y 29 elementos derivados del plan de trabajo del semestre.

## 1. Propósito y alcance

El Sprint Backlog organiza los paquetes del plan semestral como elementos de trabajo verificables. Cada elemento conserva el identificador, la actividad, el frente responsable, las dependencias, la evidencia de cierre y el estado correspondiente. Los cuatro sprints coinciden con el primer parcial, el segundo parcial, el tercer parcial y la entrega final.

La secuencia se rige por las dependencias del plan. Cada elemento cuenta con una persona responsable principal, seleccionada por afinidad con las asignaciones del Sprint Backlog precedente; los demás integrantes podrán colaborar de acuerdo con el frente indicado. La persona revisora se asignará en el tablero antes del cierre de la actividad. Las fechas indicadas funcionan como hitos de cierre y deberán ajustarse si cambia el calendario oficial.

Cada elemento identifica los RF y RNF directamente relacionados. Esta relación operativa complementa la matriz de trazabilidad integral, en la cual también se vincularán historias, reglas, casos de uso y pruebas.

## 2. Criterios de administración

| Estado | Significado |
| --- | --- |
| Pendiente | El elemento no ha iniciado o todavía no cuenta con evidencia parcial registrada. |
| En proceso | Existe trabajo o evidencia parcial, pero aún no se satisface todo el criterio de cierre. |
| Terminado | El criterio de cierre y el criterio común de terminado están satisfechos y revisados. |

Un elemento solo podrá marcarse como terminado cuando su resultado sea verificable, sus dependencias estén resueltas y las pruebas, documentos o evidencias aplicables se encuentren actualizados. Los impedimentos, posibles reasignaciones, fechas reales y enlaces a evidencias se registrarán en el tablero operativo.

## 3. Sprint 1 — Primer parcial

> **Objetivo:** comprender el negocio, aprobar la arquitectura y ejecutar una base web funcional.  
> **Cierre de referencia:** 19 de septiembre.  
> **Incremento esperado:** sistema web mínimo con identidad, tres perfiles iniciales, catálogos, inventario sanguíneo ficticio, PostgreSQL y auditoría, ejecutado localmente sin contenedores.

| ID | Tarea y criterio de cierre | Responsable, frente y dependencias | Estado |
| --- | --- | --- | --- |
| `P1-01` | **Tarea:** Aprobar el análisis, RF/RNF, historias, reglas y matriz de perfiles; completar casos de uso principales y matriz de trazabilidad.<br>**Cierre:** Documentos coherentes, IDs estables, criterios verificables y relaciones sin referencias inexistentes. | **Responsable:** Alejandra Morón.<br>**Frente:** Análisis funcional y documentación.<br>**Dependencias:** borradores vigentes. | Terminado |
| `P1-02` | **Tarea:** Diseñar contexto, contenedores, componentes, despliegue, red, secuencias, comunicación, autenticación y almacenamiento.<br>**Cierre:** Diagramas revisados y justificación de web, microservicios, datos, contenedores futuros, Compute Engine y posibles procesos de clúster, distinguiendo la ejecución local del primer parcial de la arquitectura objetivo. | **Responsable:** Galia Sejudo.<br>**Frente:** Arquitectura e integración.<br>**Dependencias:** `P1-01`. | Terminado |
| `P1-03` | **Tarea:** Completar el diseño conceptual, lógico y físico inicial de PostgreSQL y registrar las fronteras conceptuales con los almacenes posteriores.<br>**Cierre:** Claves, restricciones, catálogos, auditoría y datos ficticios para PostgreSQL; distribución posterior de datos y archivos identificada sin diseñar ni implementar todavía MongoDB o Redis. | **Responsable:** Victor Berlanga.<br>**Frente:** Datos y arquitectura.<br>**Dependencias:** `P1-01`, `P1-02`. | Terminado |
| `P1-04` | **Tarea:** Elaborar y revisar prototipos del sitio público, acceso, paneles iniciales, instituciones, tipos de componentes, inventario y auditoría.<br>**Cierre:** Prototipos responsive alineados con permisos y criterios de aceptación, sin presentarlos como funcionalidad terminada. | **Responsable:** Alejandra Morón.<br>**Frente:** Experiencia web y análisis funcional.<br>**Dependencias:** `P1-01`. | Terminado |
| `P1-05` | **Tarea:** Configurar repositorio, ramas, incidencias, tablero, convenciones, dependencias y variables de entorno.<br>**Cierre:** Entorno local reproducible para el sistema web y PostgreSQL sin contenedores; secretos fuera del repositorio y procedimientos documentados. | **Responsable:** Galia Sejudo.<br>**Frente:** Desarrollo y operación.<br>**Dependencias:** `P1-02`. | Terminado |
| `P1-06` | **Tarea:** Implementar la base web con Python, Flask, Jinja2, HTML5, CSS3 y JavaScript: página pública, inicio y cierre de sesión, JWT, menús y panel básico por perfil inicial.<br>**Cierre:** Administrador, Operador de banco de sangre y Auditor acceden solo a su menú y ámbito; la interfaz es responsive y maneja errores de forma segura. | **Responsable:** Alberto Reyna.<br>**Frente:** Sistema web y seguridad.<br>**Dependencias:** `P1-03`, `P1-04`, `P1-05`. | Terminado |
| `P1-07` | **Tarea:** Implementar instituciones, tipos de componentes sanguíneos y gestión inicial del inventario ficticio con caducidad demostrativa.<br>**Cierre:** Altas y consultas reales en PostgreSQL, filtros básicos, cambios de estado controlados, historial y auditoría con datos ficticios. | **Responsable:** Alberto Reyna.<br>**Frente:** Sistema web y datos.<br>**Dependencias:** `P1-03`, `P1-06`. | Terminado |
| `P1-08` | **Tarea:** Ejecutar pruebas, preparar datos iniciales y realizar la demostración técnica en el entorno local documentado.<br>**Cierre:** Inicio de sesión, acceso por perfil, dos catálogos, proceso de inventario, consulta, persistencia en PostgreSQL y auditoría demostrados sin maquetas ni contenedores. | **Responsable:** Alberto Reyna.<br>**Frente:** Calidad e integración.<br>**Dependencias:** `P1-05`, `P1-06`, `P1-07`. | Terminado |

### 3.1 Requerimientos relacionados

| ID | RF/RNF relacionados |
| --- | --- |
| `P1-01` | RF-WEB-001 a RF-WEB-018; RNF-WEB-001 a RNF-WEB-004; RF-MS-001 a RF-MS-009; RNF-MS-001 a RNF-MS-006; RF-MOV-001 a RF-MOV-007; RNF-MOV-001 a RNF-MOV-004; RF-DESK-001 a RF-DESK-007; RNF-DESK-001 a RNF-DESK-004; RF-DAT-001 a RF-DAT-005; RNF-DAT-001 a RNF-DAT-004; RNF-INF-001 a RNF-INF-008; RF-SEC-001 a RF-SEC-003; RNF-SEC-001 a RNF-SEC-008; RF-MON-001 a RF-MON-004; RNF-MON-001 a RNF-MON-003. |
| `P1-02` | RNF-WEB-002; RNF-MS-001, RNF-MS-005; RNF-MOV-001; RNF-DESK-001, RNF-DESK-002; RNF-DAT-001; RNF-INF-003 a RNF-INF-007; RNF-SEC-002, RNF-SEC-005; RNF-MON-002, RNF-MON-003. |
| `P1-03` | RF-DAT-001, RF-DAT-005; RNF-DAT-001, RNF-DAT-002, RNF-DAT-004; RF-WEB-005, RF-WEB-008, RF-WEB-018; RF-SEC-003. |
| `P1-04` | RF-WEB-001 a RF-WEB-005; RF-WEB-008, RF-WEB-015, RF-WEB-018; RNF-WEB-003, RNF-WEB-004; RF-SEC-002; RNF-SEC-002, RNF-SEC-006. |
| `P1-05` | RNF-INF-001, RNF-INF-002; RNF-SEC-005. |
| `P1-06` | RF-WEB-001 a RF-WEB-003; RF-WEB-015; RNF-WEB-001 a RNF-WEB-004; RF-SEC-001 a RF-SEC-003; RNF-SEC-001 a RNF-SEC-006. |
| `P1-07` | RF-WEB-004, RF-WEB-005, RF-WEB-008, RF-WEB-018; RF-DAT-001, RF-DAT-005; RNF-WEB-003, RNF-WEB-004; RNF-SEC-002, RNF-SEC-003, RNF-SEC-006. |
| `P1-08` | RF-WEB-001 a RF-WEB-005; RF-WEB-008, RF-WEB-015, RF-WEB-018; RF-DAT-001, RF-DAT-005; RF-SEC-001 a RF-SEC-003; RNF-WEB-001 a RNF-WEB-004; RNF-INF-001, RNF-INF-002, RNF-INF-008; RNF-SEC-001 a RNF-SEC-006. |

## 4. Sprint 2 — Segundo parcial

> **Objetivo:** transformar la base inicial en una solución distribuida.  
> **Cierre de referencia:** 24 de octubre.  
> **Incremento esperado:** web ampliada, microservicios, aplicación móvil y aplicación de escritorio comunicados mediante JSON y XML, con JWT, Redis, MongoDB, Docker y contratos documentados.

| ID | Tarea y criterio de cierre | Responsable, frente y dependencias | Estado |
| --- | --- | --- | --- |
| `P2-01` | **Tarea:** Confirmar Java o Kotlin para Android, la tecnología de escritorio, los límites de los microservicios y la estrategia de contenedores Docker; definir contratos versionados JSON y XML, esquemas XSD, errores y autenticación.<br>**Cierre:** Decisiones registradas, contratos de solicitud y respuesta, ejemplos de ambos formatos, criterios de compatibilidad hacia atrás y distribución local de contenedores definida. | **Responsable:** Galia Sejudo.<br>**Frente:** Arquitectura e integración.<br>**Dependencias:** cierre de Sprint 1, reglas y modelos aprobados. | Pendiente |
| `P2-02` | **Tarea:** Implementar con Flask y REST versionado los microservicios necesarios para los flujos priorizados, cada uno con responsabilidad y contenedor propios.<br>**Cierre:** Rutas versionadas, validación, JSON y XML, códigos HTTP, correlación, logs, límites de consumo, OpenAPI y endpoints de salud por servicio. | **Responsable:** Victor Berlanga.<br>**Frente:** Microservicios.<br>**Dependencias:** `P2-01`. | Pendiente |
| `P2-03` | **Tarea:** Implementar autenticación y autorización comunes con JWT y Redis.<br>**Cierre:** Inicio, renovación, expiración, revocación, permisos y ámbitos validados en peticiones protegidas; intentos relevantes auditados. | **Responsable:** Galia Sejudo.<br>**Frente:** Seguridad y microservicios.<br>**Dependencias:** `P2-01`, `P2-02`. | Pendiente |
| `P2-04` | **Tarea:** Ampliar el sistema web con perfiles posteriores, procesos autorizados, búsquedas, filtros, paginación, reportes, gráficas Highcharts, archivos, notificaciones e historial.<br>**Cierre:** Procesos persistentes y autorizados; el sistema web continúa operando aunque los clientes no estén disponibles. | **Responsable:** Alejandra Morón.<br>**Frente:** Sistema web.<br>**Dependencias:** `P2-01`, `P2-02`, `P2-03`. | Pendiente |
| `P2-05` | **Tarea:** Construir la aplicación móvil para registro preliminar, campañas, citas y avisos del Donante, y para escaneo, recolección, entrega, ubicación y evidencia del Personal de traslado.<br>**Cierre:** Consumo exclusivo de JSON y al menos cuatro microservicios; sesión segura, menú por rol, formularios, conectividad, cierre y dos capacidades pertinentes del dispositivo. | **Responsable:** Galia Sejudo.<br>**Frente:** Aplicación móvil.<br>**Dependencias:** `P2-01`, `P2-02`, `P2-03`. | Pendiente |
| `P2-06` | **Tarea:** Construir la aplicación de escritorio para unidades, pruebas, inventario, revisión autorizada, etiquetas, custodia y reportes del Operador de banco de sangre y el Coordinador regional.<br>**Cierre:** Consumo exclusivo de XML validado con XSD y al menos cuatro microservicios; captura, consulta, filtros, exportación e impresión dentro de un proceso distinto al móvil. | **Responsable:** Alejandra Morón.<br>**Frente:** Aplicación de escritorio.<br>**Dependencias:** `P2-01`, `P2-02`, `P2-03`. | Pendiente |
| `P2-07` | **Tarea:** Completar los diseños y poner en operación MongoDB y Redis; configurar Docker Compose para el entorno distribuido local.<br>**Cierre:** MongoDB demuestra inserción, consulta, actualización, agregación, índices y filtros; Redis demuestra sesiones, revocación, caché, límites, contadores, temporales y bloqueos aplicables; PostgreSQL, MongoDB, Redis y los componentes implementados se ejecutan mediante la configuración de contenedores documentada. | **Responsable:** Victor Berlanga.<br>**Frente:** Datos y microservicios.<br>**Dependencias:** `P1-03`, `P2-01`, `P2-02`, `P2-03`. | Pendiente |
| `P2-08` | **Tarea:** Integrar los cuatro productos, ejecutar pruebas unitarias y de integración iniciales y actualizar Swagger y el manual técnico parcial.<br>**Cierre:** Un proceso cruza clientes y servicios, valida JWT y Redis, persiste datos y puede consultarse en componentes autorizados mediante JSON o XML. | **Responsable:** Victor Berlanga.<br>**Frente:** Calidad e integración.<br>**Dependencias:** `P2-02` a `P2-07`. | Pendiente |

### 4.1 Requerimientos relacionados

| ID | RF/RNF relacionados |
| --- | --- |
| `P2-01` | RNF-MS-001 a RNF-MS-005; RNF-MOV-001; RNF-DESK-001, RNF-DESK-002; RNF-INF-003, RNF-INF-005; RNF-SEC-003, RNF-SEC-005; RNF-DAT-001. |
| `P2-02` | RF-MS-001 a RF-MS-009; RNF-MS-001, RNF-MS-002, RNF-MS-004, RNF-MS-005; RF-MON-001; RNF-MON-001. |
| `P2-03` | RF-SEC-001 a RF-SEC-003; RF-DAT-003; RNF-SEC-001, RNF-SEC-002, RNF-SEC-004 a RNF-SEC-006; RNF-MS-003, RNF-MS-004. |
| `P2-04` | RF-WEB-006 a RF-WEB-017; RNF-WEB-001 a RNF-WEB-004; RNF-SEC-002, RNF-SEC-003, RNF-SEC-006. |
| `P2-05` | RF-MOV-001 a RF-MOV-007; RNF-MOV-001 a RNF-MOV-004; RNF-SEC-002, RNF-SEC-006, RNF-SEC-007. |
| `P2-06` | RF-DESK-001 a RF-DESK-007; RNF-DESK-001 a RNF-DESK-004; RNF-SEC-002, RNF-SEC-003, RNF-SEC-006. |
| `P2-07` | RF-DAT-002, RF-DAT-003; RNF-DAT-001, RNF-DAT-004; RNF-INF-003; RNF-MS-003 a RNF-MS-005; RNF-SEC-001, RNF-SEC-004. |
| `P2-08` | RNF-INF-005 a RNF-INF-008; RNF-MS-002 a RNF-MS-005; RNF-MOV-001, RNF-MOV-003; RNF-DESK-002, RNF-DESK-003; RNF-SEC-002, RNF-SEC-003, RNF-SEC-005, RNF-SEC-006. |

## 5. Sprint 3 — Tercer parcial

> **Objetivo:** completar la integración, la nube, la seguridad, los algoritmos y el comportamiento bajo carga o fallos.  
> **Cierre de referencia:** 16 de noviembre.  
> **Incremento esperado:** plataforma funcionalmente completa en GCP, monitoreo, buckets, algoritmos, tres flujos integrales y evidencia de rendimiento y resiliencia.

| ID | Tarea y criterio de cierre | Responsable, frente y dependencias | Estado |
| --- | --- | --- | --- |
| `P3-01` | **Tarea:** Diseñar y desplegar la distribución en Google Cloud Platform.<br>**Cierre:** Google Compute Engine, redes privadas, firewall, puertos mínimos, variables, credenciales protegidas, HTTPS cuando sea posible y logs centralizables. | **Responsable:** Alberto Reyna.<br>**Frente:** Nube y operación.<br>**Dependencias:** cierre de Sprint 2 y decisiones de infraestructura. | Pendiente |
| `P3-02` | **Tarea:** Configurar Google Cloud Storage para evidencias, documentos, reportes e imágenes autorizadas.<br>**Cierre:** Objetos privados con metadatos, hash, privacidad y referencias en base de datos; carga y consulta mediante URLs firmadas. | **Responsable:** Galia Sejudo.<br>**Frente:** Nube, datos y seguridad.<br>**Dependencias:** `P3-01`. | Pendiente |
| `P3-03` | **Tarea:** Completar health checks y el servicio central de monitoreo.<br>**Cierre:** Estados de proceso, PostgreSQL, MongoDB, Redis y Storage; latencia, versión, errores, historial y alertas visibles sin detener los servicios supervisados. | **Responsable:** Alejandra Morón.<br>**Frente:** Monitoreo y microservicios.<br>**Dependencias:** `P2-02`, `P3-01`. | Pendiente |
| `P3-04` | **Tarea:** Completar el endurecimiento de seguridad de extremo a extremo.<br>**Cierre:** Permisos por recurso, rate limiting, validación JSON, XML/XSD y archivos, protección XXE, secretos, auditoría, ocultamiento y errores seguros verificados. | **Responsable:** Alberto Reyna.<br>**Frente:** Seguridad y calidad.<br>**Dependencias:** `P2-03`, `P3-01`, `P3-02`. | Pendiente |
| `P3-05` | **Tarea:** Implementar y documentar las capacidades algorítmicas priorizadas del dominio.<br>**Cierre:** Matching sanguíneo y HLA, ranking con urgencia, tiempo y distancia, pronóstico de caducidad, balanceo e inconsistencias se organizan en incrementos explicables; al menos un algoritmo no trivial queda integrado, medido y probado. | **Responsable:** Alberto Reyna.<br>**Frente:** Algoritmos, datos y análisis funcional.<br>**Dependencias:** reglas validadas, `P2-07`. | Pendiente |
| `P3-06` | **Tarea:** Generar el conjunto de datos de volumen y ejecutar mediciones y pruebas Locust.<br>**Cierre:** Inserción, consulta, índices, caché, recursos, comportamiento con y sin Redis, usuarios concurrentes, RPS, media, p95, p99, errores, saturación y recuperación documentados. | **Responsable:** Galia Sejudo.<br>**Frente:** Calidad, datos y rendimiento.<br>**Dependencias:** `P3-03`, `P3-05` y flujos estables. | Pendiente |
| `P3-07` | **Tarea:** Completar al menos tres flujos integrales de principio a fin.<br>**Cierre:** Cada flujo involucra usuario, cliente, microservicios, Redis, PostgreSQL o MongoDB, auditoría, notificación y visualización; incluye bucket cuando maneja archivos. | **Responsable:** Victor Berlanga.<br>**Frente:** Integración de productos.<br>**Dependencias:** `P3-01` a `P3-05`. | Pendiente |
| `P3-08` | **Tarea:** Ejecutar pruebas de fallos y realizar la demostración en la nube.<br>**Cierre:** Se detectan y registran caídas, dependencias inaccesibles y timeouts; se informa sin corrupción y la operación se recupera al restablecerse el servicio. | **Responsable:** Alberto Reyna.<br>**Frente:** Calidad, monitoreo y operación.<br>**Dependencias:** `P3-03`, `P3-04`, `P3-06`, `P3-07`. | Pendiente |

### 5.1 Requerimientos relacionados

| ID | RF/RNF relacionados |
| --- | --- |
| `P3-01` | RNF-INF-002 a RNF-INF-005; RNF-INF-007; RNF-DAT-004; RNF-SEC-005; RNF-MON-003. |
| `P3-02` | RF-DAT-004; RF-WEB-017; RF-MOV-006; RNF-DAT-003, RNF-DAT-004; RNF-MOV-002; RNF-SEC-003, RNF-SEC-005 a RNF-SEC-008. |
| `P3-03` | RF-MON-001 a RF-MON-004; RNF-MON-001 a RNF-MON-003; RNF-MS-004, RNF-MS-005; RNF-INF-007. |
| `P3-04` | RF-SEC-001 a RF-SEC-003; RNF-SEC-001 a RNF-SEC-008; RNF-MS-003 a RNF-MS-005; RNF-DAT-001, RNF-DAT-003, RNF-DAT-004; RNF-INF-004, RNF-INF-007, RNF-INF-008. |
| `P3-05` | RF-WEB-012; RF-MS-003 a RF-MS-005; RF-MS-007, RF-MS-009; RF-DESK-004; RF-DAT-005; RNF-MS-006; RNF-DAT-004; RNF-SEC-008. |
| `P3-06` | RNF-MS-006; RNF-DAT-004; RNF-INF-008; RNF-MON-003. |
| `P3-07` | RF-WEB-010 a RF-WEB-014; RF-WEB-017; RF-MS-001 a RF-MS-008; RF-MOV-002 a RF-MOV-006; RF-DESK-003, RF-DESK-004, RF-DESK-006; RF-DAT-003 a RF-DAT-005; RF-SEC-003; RNF-INF-006, RNF-INF-008. |
| `P3-08` | RF-MON-001 a RF-MON-004; RNF-MS-005, RNF-MS-006; RNF-DAT-004; RNF-INF-007, RNF-INF-008; RNF-MON-001 a RNF-MON-003. |

## 6. Sprint 4 — Entrega final

> **Objetivo:** estabilizar, verificar y presentar profesionalmente la solución completa.  
> **Cierre de referencia:** 5 de diciembre.  
> **Incremento esperado:** versión liberable, pruebas finales, documentación y manuales, video, presentación y demostración integral.

| ID | Tarea y criterio de cierre | Responsable, frente y dependencias | Estado |
| --- | --- | --- | --- |
| `EF-01` | **Tarea:** Congelar nuevas funciones y clasificar los defectos funcionales, de integración, seguridad, datos, sincronización, archivos y rendimiento.<br>**Cierre:** Lista priorizada sin módulos faltantes disfrazados de defectos; responsables y evidencia definidos. | **Responsable:** Victor Berlanga.<br>**Frente:** Coordinación y calidad.<br>**Dependencias:** cierre de Sprint 3. | Pendiente |
| `EF-02` | **Tarea:** Corregir defectos y completar pruebas unitarias, integración, sistema, regresión, contratos, seguridad, carga, estrés, recuperación, roles, archivos, datos masivos y usabilidad.<br>**Cierre:** Pruebas reproducibles, defectos críticos cerrados y resultados conservados. | **Responsable:** Alejandra Morón.<br>**Frente:** Todos los frentes técnicos.<br>**Dependencias:** `EF-01`. | Pendiente |
| `EF-03` | **Tarea:** Optimizar consultas, índices, caché, consumo, interfaces y recuperación sin alterar reglas aprobadas.<br>**Cierre:** Comparación antes y después, ausencia de regresiones y límites conocidos documentados. | **Responsable:** Alberto Reyna.<br>**Frente:** Datos, calidad y experiencia.<br>**Dependencias:** `EF-02`. | Pendiente |
| `EF-04` | **Tarea:** Completar expediente técnico, manuales, scripts, Swagger, evidencias de GCP, bitácora de participación, registro de incidencias y paquete de instalación o despliegue.<br>**Cierre:** Documentación consistente con la versión liberada y procedimientos reproducibles. | **Responsable:** Alejandra Morón.<br>**Frente:** Documentación y operación.<br>**Dependencias:** `EF-02`, `EF-03`. | Pendiente |
| `EF-05` | **Tarea:** Preparar video, presentación, ensayo de la demostración integral y entrega de código, aplicaciones, contenedores y evidencias.<br>**Cierre:** Demostración de web, móvil, escritorio, microservicios, seguridad, datos, algoritmo, nube, monitoreo, carga y recuperación; participación de los cuatro integrantes. | **Responsable:** Galia Sejudo.<br>**Frente:** Equipo completo.<br>**Dependencias:** `EF-04`. | Pendiente |

### 6.1 Requerimientos relacionados

| ID | RF/RNF relacionados |
| --- | --- |
| `EF-01` | Todos los RF y RNF consolidados, de acuerdo con la clasificación del defecto registrado. |
| `EF-02` | Todos los RF y RNF consolidados, como alcance de la verificación final. |
| `EF-03` | RNF-WEB-002 a RNF-WEB-004; RNF-MS-005, RNF-MS-006; RNF-MOV-003, RNF-MOV-004; RNF-DESK-003, RNF-DESK-004; RNF-DAT-004; RNF-INF-005, RNF-INF-007, RNF-INF-008; RNF-MON-001 a RNF-MON-003. |
| `EF-04` | Todos los RF y RNF consolidados, como alcance de la documentación y de las evidencias finales. |
| `EF-05` | Todos los RF y RNF consolidados, como alcance de la demostración integral. |

## 7. Seguimiento del backlog

El backlog se revisará durante el seguimiento semanal y antes de cada demostración. Toda actualización conservará el identificador del elemento y registrará el cambio de estado, la persona responsable, la persona revisora, las fechas reales, los impedimentos y la ubicación de la evidencia.

Los cambios de alcance deberán reflejarse primero en el plan de trabajo y después en el Sprint Backlog. Una actividad nueva no reemplazará silenciosamente un paquete comprometido ni permitirá omitir seguridad, trazabilidad, pruebas o documentación necesarias para su cierre.
