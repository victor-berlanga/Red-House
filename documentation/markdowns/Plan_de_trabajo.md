# Plan de trabajo del semestre

> **Proyecto:** Red regional de bancos de sangre y donación de órganos — Equipo 01.  
> **Estado:** plan semestral inicial para validación académica.  
> **Fecha:** 7 de septiembre de 2026.  
> **Cobertura:** primer parcial, segundo parcial, tercer parcial y entrega final.

## 1. Propósito y alcance

El trabajo del semestre se organizará en incrementos ejecutables que conduzcan desde el análisis y el producto mínimo funcional hasta una plataforma integrada, desplegada, probada y documentada. El alcance comprende el sistema web empresarial, el módulo independiente de microservicios, la aplicación móvil Android, la aplicación de escritorio, los almacenes de datos, la infraestructura, la seguridad y el monitoreo.

Cada parcial deberá cerrar con funcionamiento demostrable, persistencia real, pruebas y evidencia proporcional al incremento. Los diagramas, documentos, prototipos o interfaces estáticas apoyarán el desarrollo, pero no sustituirán la operación ejecutable exigida para cada etapa.

La plataforma permanecerá como herramienta de coordinación y apoyo. Ningún incremento automatizará decisiones médicas o regulatorias que requieran intervención humana, ni utilizará reglas clínicas inventadas. Hasta contar con validación competente se emplearán datos ficticios y criterios demostrativos claramente identificados.

El calendario operativo se regirá por los cuatro cortes oficiales. Las fechas de inicio y cierre se registrarán en el tablero una vez confirmadas por la institución, sin alterar las dependencias ni los criterios de logro.

## 2. Marco de planeación

### 2.1 Etapas del semestre

| Etapa | Periodo relativo | Objetivo principal | Incremento de salida |
| --- | --- | --- | --- |
| Primer parcial | Desde el inicio del semestre hasta el primer corte | Comprender el negocio, aprobar la arquitectura y ejecutar una base web funcional | Sistema web mínimo con identidad, tres perfiles iniciales, catálogos, inventario sanguíneo ficticio, PostgreSQL y auditoría, ejecutado localmente sin contenedores |
| Segundo parcial | Entre el primer y el segundo corte | Transformar la base inicial en una solución distribuida | Web ampliada, microservicios, aplicación móvil y aplicación de escritorio comunicados mediante JSON y XML, con JWT, Redis, MongoDB, Docker y contratos documentados |
| Tercer parcial | Entre el segundo y el tercer corte | Completar la integración, nube, seguridad, algoritmos y comportamiento bajo carga o fallos | Plataforma funcionalmente completa en GCP, monitoreo, buckets, algoritmos, tres flujos integrales y evidencia de rendimiento y resiliencia |
| Entrega final | Después del tercer corte y hasta la presentación final | Estabilizar, verificar y presentar profesionalmente la solución completa | Versión liberable, pruebas finales, documentación y manuales, video, presentación y demostración integral |

### 2.2 Principios de ejecución

- Se desarrollarán incrementos verticales pequeños que incluyan interfaz, lógica, persistencia, autorización, auditoría y prueba cuando corresponda.
- El sistema web conservará sus funciones propias aunque las aplicaciones móvil o de escritorio no estén disponibles.
- La aplicación móvil consumirá exclusivamente JSON y la aplicación de escritorio exclusivamente XML producido por los microservicios.
- Ningún cliente accederá directamente a PostgreSQL, MongoDB, Redis o Google Cloud Storage.
- Los contratos, la seguridad, la auditoría, el manejo de errores y las pruebas se trabajarán desde el incremento que los necesite y no se pospondrán hasta el cierre.
- Sangre y órganos conservarán procesos, datos, estados y reglas diferenciados, aunque compartan componentes de infraestructura.
- Los servicios opcionales de Google Cloud y el uso de clústeres solo se incorporarán cuando una necesidad de volumen, disponibilidad o procesamiento lo justifique.
- MongoDB, Redis y la contenerización con Docker se estudiarán de forma introductoria durante el primer parcial, pero su diseño detallado, configuración y uso funcional comenzarán en el segundo parcial. PostgreSQL permanecerá como almacenamiento real del producto mínimo.
- Cada paquete de trabajo conserva una persona responsable principal identificada en este plan; una persona revisora se asignará en el tablero antes de comenzar. Todos los integrantes deberán aportar evidencia de participación.

## 3. Plan de trabajo por etapa

### 3.1 Primer parcial — Análisis, arquitectura y producto mínimo funcional

| ID | Paquete de trabajo | Responsable principal y frente | Dependencias | Evidencia y criterio de cierre |
| --- | --- | --- | --- | --- |
| P1-01 | Aprobar el análisis, RF/RNF, historias, reglas y matriz de perfiles; completar casos de uso principales y matriz de trazabilidad | Alejandra Morón — Análisis funcional y documentación | Borradores vigentes | Documentos coherentes, IDs estables, criterios verificables y relaciones sin referencias inexistentes |
| P1-02 | Diseñar contexto, contenedores, componentes, despliegue, red, secuencias, comunicación, autenticación y almacenamiento | Galia Sejudo — Arquitectura e integración | P1-01 | Diagramas revisados y justificación de web, microservicios, datos, contenedores futuros, Compute Engine y posibles procesos de clúster, distinguiendo la ejecución local del primer parcial de la arquitectura objetivo |
| P1-03 | Completar el diseño conceptual, lógico y físico inicial de PostgreSQL y registrar las fronteras conceptuales con los almacenes posteriores | Victor Berlanga — Datos y arquitectura | P1-01, P1-02 | Claves, restricciones, catálogos, auditoría y datos ficticios para PostgreSQL; distribución posterior de datos y archivos identificada sin diseñar ni implementar todavía MongoDB o Redis |
| P1-04 | Elaborar y revisar prototipos del sitio público, acceso, paneles iniciales, instituciones, tipos de componentes, inventario y auditoría | Alejandra Morón — Experiencia web y análisis funcional | P1-01 | Prototipos responsive alineados con permisos y criterios de aceptación, sin presentarlos como funcionalidad terminada |
| P1-05 | Configurar repositorio, ramas, incidencias, tablero, convenciones, dependencias y variables de entorno | Galia Sejudo — Desarrollo y operación | P1-02 | Entorno local reproducible para el sistema web y PostgreSQL sin contenedores; secretos fuera del repositorio y procedimientos documentados |
| P1-06 | Implementar la base web con Python, Flask, Jinja2, HTML5, CSS3 y JavaScript: página pública, inicio y cierre de sesión, JWT, menús y panel básico por perfil inicial | Alberto Reyna — Sistema web y seguridad | P1-03, P1-04, P1-05 | Administrador, Operador de banco de sangre y Auditor acceden solo a su menú y ámbito; la interfaz es responsive y maneja errores de forma segura |
| P1-07 | Implementar instituciones, tipos de componentes sanguíneos y gestión inicial del inventario ficticio con caducidad demostrativa | Alberto Reyna — Sistema web y datos | P1-03, P1-06 | Altas y consultas reales en PostgreSQL, filtros básicos, cambios de estado controlados, historial y auditoría con datos ficticios |
| P1-08 | Ejecutar pruebas, preparar datos iniciales y realizar la demostración técnica en el entorno local documentado | Alberto Reyna — Calidad e integración | P1-05, P1-06, P1-07 | Inicio de sesión, acceso por perfil, dos catálogos, proceso de inventario, consulta, persistencia en PostgreSQL y auditoría demostrados sin maquetas ni contenedores |

El primer parcial se considerará cerrado cuando exista una base técnica ejecutable y no solamente documentación. MongoDB, Redis y los contenedores Docker se limitarán en esta etapa a la investigación introductoria y a su representación como elementos futuros de la arquitectura. Matching clínico, HLA, ranking, órganos, optimización geográfica, aplicación móvil y aplicación de escritorio también permanecerán fuera de este incremento funcional, pero dentro de la arquitectura y del plan semestral.

### 3.2 Segundo parcial — Componentes distribuidos y contratos

| ID | Paquete de trabajo | Responsable principal y frente | Dependencias | Evidencia y criterio de cierre |
| --- | --- | --- | --- | --- |
| P2-01 | Confirmar Java o Kotlin para Android, la tecnología de escritorio, los límites de los microservicios y la estrategia de contenedores Docker; definir contratos versionados JSON y XML, esquemas XSD, errores y autenticación | Galia Sejudo — Arquitectura e integración | Cierre P1, reglas y modelos aprobados | Decisiones registradas, contratos de solicitud y respuesta, ejemplos de ambos formatos, criterios de compatibilidad hacia atrás y distribución local de contenedores definida |
| P2-02 | Implementar con Flask y REST versionado los microservicios necesarios para los flujos priorizados, cada uno con responsabilidad y contenedor propios | Victor Berlanga — Microservicios | P2-01 | Rutas versionadas, validación, JSON y XML, códigos HTTP, correlación, logs, límites de consumo, OpenAPI y endpoints de salud por servicio |
| P2-03 | Implementar autenticación y autorización comunes con JWT y Redis | Galia Sejudo — Seguridad y microservicios | P2-01, P2-02 | Inicio, renovación, expiración, revocación, permisos y ámbitos validados en peticiones protegidas; intentos relevantes auditados |
| P2-04 | Ampliar el sistema web con perfiles posteriores, procesos autorizados, búsquedas, filtros, paginación, reportes, gráficas Highcharts, archivos, notificaciones e historial | Alejandra Morón — Sistema web | P2-01, P2-02, P2-03 | Procesos persistentes y autorizados; el sistema web continúa operando aunque los clientes no estén disponibles |
| P2-05 | Construir la aplicación móvil para registro preliminar, campañas, citas y avisos del Donante, y para escaneo, recolección, entrega, ubicación y evidencia del Personal de traslado | Galia Sejudo — Aplicación móvil | P2-01, P2-02, P2-03 | Consumo exclusivo de JSON y al menos cuatro microservicios; sesión segura, menú por rol, formularios, conectividad, cierre y dos capacidades pertinentes del dispositivo |
| P2-06 | Construir la aplicación de escritorio para unidades, pruebas, inventario, revisión autorizada, etiquetas, custodia y reportes del Operador de banco de sangre y el Coordinador regional | Alejandra Morón — Aplicación de escritorio | P2-01, P2-02, P2-03 | Consumo exclusivo de XML validado con XSD y al menos cuatro microservicios; captura, consulta, filtros, exportación e impresión dentro de un proceso distinto al móvil |
| P2-07 | Completar los diseños y poner en operación MongoDB y Redis; configurar Docker Compose para el entorno distribuido local | Victor Berlanga — Datos y microservicios | P1-03, P2-01, P2-02, P2-03 | MongoDB demuestra inserción, consulta, actualización, agregación, índices y filtros; Redis demuestra sesiones, revocación, caché, límites, contadores, temporales y bloqueos aplicables; PostgreSQL, MongoDB, Redis y los componentes implementados se ejecutan mediante la configuración de contenedores documentada |
| P2-08 | Integrar los cuatro productos, ejecutar pruebas unitarias y de integración iniciales y actualizar Swagger y el manual técnico parcial | Victor Berlanga — Calidad e integración | P2-02 a P2-07 | Un proceso cruza clientes y servicios, valida JWT y Redis, persiste datos y puede consultarse en componentes autorizados mediante JSON o XML |

El segundo parcial se considerará cerrado cuando web, microservicios, móvil y escritorio existan y se comuniquen mediante contratos explícitos, y cuando MongoDB, Redis y los contenedores Docker se utilicen de forma funcional y reproducible. La cantidad de microservicios se definirá según responsabilidades reales y se mantendrá dentro del rango recomendado cuando la separación del dominio lo justifique.

El catálogo funcional de referencia comprende donantes, receptores, inventario, compatibilidad, priorización, geografía, transporte, alertas, cadena de custodia y auditoría. Sus límites, propietarios de datos y dependencias se validarán antes de la implementación. La ampliación web cubrirá gradualmente donantes, receptores, órganos, solicitudes, estudios, asignaciones, traslados, custodia, panel regional, archivos y reportes conforme sus reglas estén validadas.

### 3.3 Tercer parcial — Nube, integración completa, algoritmos y carga

| ID | Paquete de trabajo | Responsable principal y frente | Dependencias | Evidencia y criterio de cierre |
| --- | --- | --- | --- | --- |
| P3-01 | Diseñar y desplegar la distribución en Google Cloud Platform | Alberto Reyna — Nube y operación | Cierre P2, decisiones de infraestructura | Google Compute Engine, redes privadas, firewall, puertos mínimos, variables, credenciales protegidas, HTTPS cuando sea posible y logs centralizables |
| P3-02 | Configurar Google Cloud Storage para evidencias, documentos, reportes e imágenes autorizadas | Galia Sejudo — Nube, datos y seguridad | P3-01 | Objetos privados con metadatos, hash, privacidad y referencias en base de datos; carga y consulta mediante URLs firmadas |
| P3-03 | Completar health checks y el servicio central de monitoreo | Alejandra Morón — Monitoreo y microservicios | P2-02, P3-01 | Estados de proceso, PostgreSQL, MongoDB, Redis y Storage; latencia, versión, errores, historial y alertas visibles sin detener los servicios supervisados |
| P3-04 | Completar el endurecimiento de seguridad de extremo a extremo | Alberto Reyna — Seguridad y calidad | P2-03, P3-01, P3-02 | Permisos por recurso, rate limiting, validación JSON, XML/XSD y archivos, protección XXE, secretos, auditoría, ocultamiento y errores seguros verificados |
| P3-05 | Implementar y documentar las capacidades algorítmicas priorizadas del dominio | Alberto Reyna — Algoritmos, datos y análisis funcional | Reglas clínicas o demostrativas validadas, P2-07 | Matching sanguíneo y HLA, ranking con urgencia, tiempo y distancia, pronóstico de caducidad, balanceo e inconsistencias se organizan en incrementos explicables; al menos un algoritmo no trivial queda integrado, medido y probado |
| P3-06 | Generar el conjunto de datos de volumen y ejecutar mediciones y pruebas Locust | Galia Sejudo — Calidad, datos y rendimiento | P3-03, P3-05 y flujos estables | Inserción, consulta, índices, caché, recursos, comportamiento con y sin Redis, usuarios concurrentes, RPS, media, p95, p99, errores, saturación y recuperación documentados |
| P3-07 | Completar al menos tres flujos integrales de principio a fin | Victor Berlanga — Integración de productos | P3-01 a P3-05 | Cada flujo involucra usuario, cliente, microservicios, Redis, PostgreSQL o MongoDB, auditoría, notificación y visualización; incluye bucket cuando maneja archivos |
| P3-08 | Ejecutar pruebas de fallos y realizar la demostración en la nube | Alberto Reyna — Calidad, monitoreo y operación | P3-03, P3-04, P3-06, P3-07 | Se detectan y registran caídas, dependencias inaccesibles y timeouts; se informa sin corrupción y la operación se recupera al restablecerse el servicio |

El tercer parcial cerrará con la plataforma funcionalmente completa. Los servicios opcionales, un clúster o procesamiento distribuido solo se añadirán cuando las mediciones demuestren que resuelven una necesidad concreta.

### 3.4 Entrega final — Estabilización y presentación

| ID | Paquete de trabajo | Responsable principal y frente | Dependencias | Evidencia y criterio de cierre |
| --- | --- | --- | --- | --- |
| EF-01 | Congelar nuevas funciones y clasificar los defectos funcionales, de integración, seguridad, datos, sincronización, archivos y rendimiento | Victor Berlanga — Coordinación y calidad | Cierre P3 | Lista priorizada sin módulos faltantes disfrazados de defectos; responsables y evidencia definidos |
| EF-02 | Corregir defectos y completar pruebas unitarias, integración, sistema, regresión, contratos, seguridad, carga, estrés, recuperación, roles, archivos, datos masivos y usabilidad | Alejandra Morón — Todos los frentes técnicos | EF-01 | Pruebas reproducibles, defectos críticos cerrados y resultados conservados |
| EF-03 | Optimizar consultas, índices, caché, consumo, interfaces y recuperación sin alterar reglas aprobadas | Alberto Reyna — Datos, calidad y experiencia | EF-02 | Comparación antes y después, ausencia de regresiones y límites conocidos documentados |
| EF-04 | Completar expediente técnico, manuales, scripts, Swagger, evidencias de GCP, bitácora de participación, registro de incidencias y paquete de instalación o despliegue | Alejandra Morón — Documentación y operación | EF-02, EF-03 | Documentación consistente con la versión liberada y procedimientos reproducibles |
| EF-05 | Preparar video, presentación, ensayo de la demostración integral y entrega de código, aplicaciones, contenedores y evidencias | Galia Sejudo — Equipo completo | EF-04 | Demostración de web, móvil, escritorio, microservicios, seguridad, datos, algoritmo, nube, monitoreo, carga y recuperación; participación de los cuatro integrantes |

El despliegue en el entorno institucional denominado `ubiquitous` quedará condicionado a la disponibilidad de acceso y especificaciones técnicas, además del despliegue en GCP. La entrega final no se utilizará para desarrollar componentes que debieron quedar completos durante el tercer parcial.

## 4. Flujos integrales objetivo

| ID | Flujo | Componentes y evidencia esperada |
| --- | --- | --- |
| FI-01 | Registro preliminar de donante, campaña, cita y aviso | Donante en Android mediante JSON; servicios de donantes, alertas y procesos relacionados; JWT y Redis; persistencia autorizada; auditoría; consulta web del resultado por personal permitido |
| FI-02 | Solicitud, compatibilidad, priorización y decisión humana | Personal médico o Coordinador en web o escritorio; servicios de receptores, inventario, compatibilidad, priorización y geografía; explicación versionada; persistencia; auditoría; alerta y visualización sin decisión clínica automática |
| FI-03 | Asignación, traslado y cadena de custodia | Coordinador en web o escritorio, Personal de traslado en Android, servicios de transporte y custodia, JSON móvil y XML de escritorio, Redis, datos transaccionales, evidencia en bucket, alertas, auditoría y consulta final autorizada |

Los flujos podrán ajustarse si cambia una regla aprobada, pero deberán conservar la integración mínima exigida y la separación de responsabilidades entre clientes, servicios y almacenes.

## 5. Dependencias críticas

| Dependencia | Habilita | Control |
| --- | --- | --- |
| Aprobación de análisis, requisitos, historias, reglas y permisos | Casos de uso, interfaces, datos y aceptación | No implementar una interpretación dudosa sin registrar y resolver el cambio |
| Límites de componentes y propietarios de datos | Modelos, microservicios y transacciones | Evitar duplicación de reglas, acceso directo desde clientes y dependencias circulares |
| Modelo de identidad, JWT, sesión y autorización | Web, móvil, escritorio y APIs protegidas | Definir contrato común antes de integrar los clientes |
| Contratos JSON, XML y XSD versionados | Desarrollo paralelo de móvil y escritorio | Ejecutar pruebas de contrato y mantener ejemplos equivalentes de ambos formatos |
| Reglas clínicas, regulatorias o demostrativas validadas | Compatibilidad, priorización, caducidad y asignación | Bloquear uso real de criterios pendientes y conservar versión y explicación |
| Integración local estable | Despliegue en GCP y pruebas de fallos | Resolver primero errores reproducibles en contenedores locales |
| Flujos funcionales completos | Datos de volumen, Locust y optimización | No medir endpoints aislados como sustituto de escenarios reales |
| Cierre funcional del tercer parcial | Estabilización final | No aceptar nuevas funciones salvo corrección indispensable y aprobada |

## 6. Frentes de responsabilidad y participación

| Frente | Responsabilidad principal | Evidencia de participación |
| --- | --- | --- |
| Coordinación y análisis funcional | Alcance, prioridades, criterios, reglas, tablero, riesgos y control de cambios | Decisiones, revisiones, tareas cerradas y participación en demostraciones |
| Arquitectura e integración | Límites, diagramas, contratos, secuencias, dependencias y coherencia entre componentes | Diagramas versionados, contratos revisados y pruebas integradas |
| Sistema web | Portal público y privado, perfiles, procesos, paneles, reportes y persistencia web | Commits, revisiones, pruebas y evidencia ejecutable |
| Microservicios | APIs, lógica de dominio, JSON/XML, salud, errores, auditoría y despliegue independiente | Servicios ejecutables, OpenAPI, pruebas y logs controlados |
| Aplicaciones cliente | Android y escritorio, capacidades del dispositivo, XML/XSD, manejo de red e interfaces por perfil | Aplicaciones instalables o ejecutables, pruebas y demostración de flujos |
| Datos y nube | PostgreSQL, MongoDB, Redis, Storage, índices, respaldos, redes y despliegue | Modelos, scripts, mediciones, contenedores y evidencia de GCP |
| Seguridad y calidad | Autenticación, autorización, validaciones, pruebas, carga, fallos, usabilidad y defectos | Casos ejecutados, resultados, incidencias y verificaciones de recuperación |
| Documentación y presentación | Expediente, manuales, evidencias, video, presentación y bitácora | Documentos consistentes con la versión, material audiovisual y participación registrada |

El equipo está integrado por Alejandra Morón, Alberto Reyna, Galia Sejudo y Victor Berlanga. Los responsables principales de cada paquete se indican en este plan; la persona revisora se asignará en el tablero antes de comenzar. Una misma persona podrá participar en varios frentes y la bitácora deberá mostrar contribuciones de los cuatro integrantes en construcción, revisión, pruebas, documentación o demostración.

## 7. Criterio común de terminado

Un paquete de trabajo se considerará terminado únicamente cuando:

1. Cumpla sus criterios de aceptación y no dependa de datos simulados no identificados.
2. Tenga código, configuración o documento versionado y revisado por otra persona del equipo.
3. Incluya pruebas proporcionales al riesgo y conserve sus resultados.
4. Aplique autenticación, autorización, validación, auditoría y manejo seguro de errores cuando correspondan.
5. Actualice contratos, modelos, diagramas y manuales afectados.
6. Pueda ejecutarse o reproducirse mediante las instrucciones y contenedores definidos.
7. No exponga secretos, tokens, datos clínicos, ubicaciones o evidencias innecesarias.
8. Cuente con evidencia verificable para la demostración del parcial.

## 8. Riesgos del plan y respuesta prevista

| Riesgo | Impacto | Respuesta prevista |
| --- | --- | --- |
| Alcance mayor que la capacidad académica | Componentes incompletos o integración tardía | Priorizar cortes verticales, respetar el MVP y completar funcionalidad antes del cierre del tercer parcial |
| Reglas clínicas o regulatorias no validadas | Resultados incorrectos o afirmaciones indebidas | Usar datos y reglas demostrativas identificadas; mantener revisión humana y bloquear uso real |
| Contratos JSON y XML divergentes | Móvil y escritorio interpretan resultados distintos | Definir una semántica común, versionar contratos y automatizar pruebas JSON y XSD |
| Modelo de datos prematuro o duplicado | Migraciones costosas e inconsistencias | Aprobar propietarios, claves y ciclos de vida antes de consolidar el modelo físico |
| Seguridad agregada tardíamente | Retrabajo y exposición de información | Incorporar identidad, permisos, validación, auditoría y secretos desde el primer incremento pertinente |
| Integración acumulada al final | Fallos difíciles de aislar | Integrar de forma continua y demostrar un flujo creciente en cada parcial |
| Dependencia de servicios o créditos de nube | Bloqueo del despliegue o costos inesperados | Mantener entorno local reproducible, controlar consumo y usar servicios opcionales solo con justificación |
| Volumen o rendimiento sin objetivos | Mediciones sin conclusión | Definir conjunto, carga y umbrales antes de Locust y comparar índices y caché con una línea base |
| Participación desigual del equipo | Riesgo académico y conocimiento concentrado | Asignar responsable y revisor, rotar revisiones y conservar bitácora de contribuciones |
| Entrega final utilizada para funciones pendientes | Falta de tiempo para estabilizar | Aplicar cierre funcional en el tercer parcial y congelar nuevas funciones al iniciar la etapa final |

## 9. Seguimiento y evidencia

| Indicador | Forma de seguimiento | Criterio por corte |
| --- | --- | --- |
| Paquetes terminados | Paquetes aceptados respecto de los planeados para la etapa | Todos los paquetes obligatorios del corte cumplen el criterio común de terminado |
| Cobertura de aceptación | Historias y criterios vinculados con pruebas o evidencia | No existen funciones demostradas sin criterio y resultado verificable |
| Calidad | Pruebas aprobadas, fallidas y defectos por severidad | No quedan defectos críticos abiertos al cerrar un parcial |
| Integración | Flujos que atraviesan componentes autorizados | Un proceso en el primer parcial, integración distribuida en el segundo y al menos tres flujos en el tercero |
| Seguridad | Casos de autenticación, autorización, validación, auditoría y secretos | Los controles aplicables al incremento tienen evidencia positiva y negativa |
| Rendimiento | RPS, media, p95, p99, errores, saturación y recuperación | Objetivos definidos antes de la prueba y resultados explicados, no solo capturados |
| Participación | Tareas, revisiones, pruebas, documentación y demostraciones por integrante | Los cuatro integrantes conservan evidencia de contribución durante el semestre |
| Documentación | Artefactos actualizados frente a cambios del producto | La documentación entregada describe la versión que realmente se demuestra |

## 10. Control del plan

El tablero de tareas, el registro de incidencias y la bitácora de participación se revisarán al menos una vez por semana y antes de cada demostración. Cada paquete deberá mantener sincronizados el responsable principal indicado en este plan, la persona revisora, las dependencias, el criterio de aceptación, la evidencia y el estado.

Los cambios de alcance se evaluarán por su efecto en requisitos, historias, reglas, permisos, arquitectura, datos, contratos, pruebas y manuales. Un cambio clínico o normativo no se incorporará como regla autorizada sin fuente y aprobación competentes. Si aparece una desviación de calendario, se reordenarán tareas o servicios opcionales antes de comprometer la seguridad, la trazabilidad o los entregables obligatorios.

Al concluir cada parcial se realizará una revisión de cierre: funcionamiento ejecutable, integración alcanzada, controles aplicados, pruebas realizadas, despliegue reproducible, documentación actualizada y participación del equipo. El resultado de esa revisión establecerá la línea base del siguiente incremento.
