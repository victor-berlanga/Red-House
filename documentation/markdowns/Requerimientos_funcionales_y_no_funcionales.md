# Requerimientos funcionales y no funcionales

> **Proyecto:** Red regional de bancos de sangre y donación de órganos — Equipo 01.
> **Estado:** borrador consolidado para validación académica.
> **Fecha:** 7 de septiembre de 2026.
> **Cobertura:** proyecto académico completo, con implementación gradual por parciales e incrementos.

## 1. Propósito y alcance

Este documento especifica los requerimientos funcionales y no funcionales de la solución completa, clasificados entre sistema web, microservicios, aplicación móvil, aplicación de escritorio, bases de datos, infraestructura, seguridad y monitoreo.

La fase **Primer parcial** identifica el subconjunto que deberá implementarse inicialmente; no elimina los requerimientos **Posteriores**. Los requerimientos **Transversales** deberán considerarse desde el diseño y aplicarse en los incrementos correspondientes.

La plataforma apoyará la coordinación y las decisiones, pero no sustituirá la evaluación médica, ética o normativa. Las reglas de compatibilidad, elegibilidad, urgencia, conservación, priorización y asignación deberán provenir de fuentes autorizadas, versionarse y validarse. Durante el proyecto académico solo se utilizarán datos ficticios y reglas demostrativas identificadas como tales.

## 2. Convenciones

### 2.1 Componentes

| Código | Componente |
| --- | --- |
| WEB | Sistema web empresarial |
| MS | Módulo de microservicios |
| MOV | Aplicación móvil Android |
| DESK | Aplicación de escritorio |
| DAT | Bases de datos y almacenamiento |
| INF | Infraestructura e integración |
| SEC | Seguridad y privacidad |
| MON | Monitoreo y observabilidad |

### 2.2 Fases y validación

| Clasificación | Valores utilizados |
| --- | --- |
| Fase | Primer parcial, Posterior o Transversal |
| Prioridad | Alta o Media |
| Validación | Técnica, Demostrativa o Clínica/normativa |

Los prefijos `RF` y `RNF` identifican requerimientos funcionales y no funcionales. La consolidación agrupa acciones del mismo objetivo, pero no implica que cada requisito deba convertirse en una historia de usuario independiente.

## 3. Sistema web empresarial

### 3.1 Requerimientos funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RF-WEB-001 | Primer parcial | Alta | Técnica | El sistema web deberá ofrecer una página pública informativa y acceso al portal privado, sin exponer inventarios detallados ni información personal o clínica. |
| RF-WEB-002 | Transversal | Alta | Técnica | El sistema web deberá permitir iniciar y cerrar sesión y, en el incremento correspondiente, recuperar la contraseña mediante un flujo temporal, seguro y auditable. |
| RF-WEB-003 | Primer parcial | Alta | Técnica | El Administrador deberá poder gestionar usuarios y asignar perfiles y ámbitos institucionales; durante el primer parcial solo se habilitarán funcionalmente Administrador, Operador de banco de sangre y Auditor, mientras los siete perfiles permanecerán definidos para el alcance completo. Cada usuario deberá visualizar únicamente el perfil, menú y operaciones autorizados. |
| RF-WEB-004 | Primer parcial | Alta | Técnica | El Administrador deberá poder gestionar catálogos y parámetros autorizados, incluidos durante el primer parcial instituciones —utilizadas como catálogo de referencia desde la entidad administrada en RF-WEB-005, sin duplicar información— y tipos de componentes sanguíneos, conservando auditoría de los cambios. |
| RF-WEB-005 | Primer parcial | Alta | Técnica | El Administrador deberá poder registrar y mantener instituciones, sedes, ubicación, contactos, capacidades y estado de participación en la red, como fuente conceptual única de la información institucional utilizada por los demás procesos. |
| RF-WEB-006 | Posterior | Alta | Clínica/normativa | El personal autorizado deberá poder registrar y actualizar donantes con los datos, consentimientos, restricciones y estados pertinentes al tipo de donación. |
| RF-WEB-007 | Posterior | Alta | Clínica/normativa | El Personal médico autorizado deberá poder registrar y actualizar receptores o pacientes y su participación en listas o procesos autorizados, sin crear por defecto un acceso directo para el receptor. |
| RF-WEB-008 | Primer parcial | Alta | Demostrativa | El Operador de banco de sangre deberá poder registrar unidades sanguíneas ficticias, consultar su inventario, cambiar estados de forma controlada, conservar su historial y visualizar proximidad de caducidad mediante un parámetro demostrativo. |
| RF-WEB-009 | Posterior | Alta | Clínica/normativa | El personal autorizado deberá poder mantener la disponibilidad y viabilidad de órganos mediante un flujo especializado y separado del inventario ordinario de unidades sanguíneas. |
| RF-WEB-010 | Posterior | Alta | Clínica/normativa | El Personal médico autorizado deberá poder registrar y dar seguimiento a solicitudes ordinarias y urgentes, asociándolas con receptor, institución, necesidad y urgencia autorizada. |
| RF-WEB-011 | Posterior | Alta | Clínica/normativa | El personal autorizado deberá poder capturar y consultar pruebas y estudios, diferenciando los aplicables a sangre de los correspondientes a órganos y tejidos. |
| RF-WEB-012 | Posterior | Alta | Clínica/normativa | El Personal médico autorizado y el Coordinador regional deberán poder consultar candidatos, compatibilidad y priorización con factores, datos faltantes, versión y explicación, y registrar aceptación, rechazo, reevaluación o excepción justificada. |
| RF-WEB-013 | Posterior | Alta | Clínica/normativa | El personal autorizado deberá poder reservar, asignar, cancelar, liberar o reasignar un recurso mediante confirmación humana y transiciones que eviten la doble asignación. |
| RF-WEB-014 | Posterior | Alta | Técnica | El Coordinador regional deberá poder programar y consultar traslados, incidencias, confirmaciones y eventos de cadena de custodia. |
| RF-WEB-015 | Primer parcial | Alta | Técnica | Durante el primer parcial, el sistema web deberá mostrar un panel principal básico para cada perfil inicial, con datos persistidos y accesos acordes con su autorización; posteriormente deberá evolucionar hacia un panel regional con notificaciones, indicadores y gráficas Highcharts. |
| RF-WEB-016 | Posterior | Media | Clínica/normativa | Los usuarios autorizados deberán poder generar, filtrar y exportar reportes operativos o regulatorios conforme a formatos previamente definidos. |
| RF-WEB-017 | Posterior | Media | Técnica | Los usuarios autorizados deberán poder cargar, consultar y descargar archivos y evidencias mediante referencias controladas al almacenamiento de objetos. |
| RF-WEB-018 | Primer parcial | Alta | Técnica | El Auditor deberá poder buscar, filtrar y consultar sin modificar la bitácora correspondiente a usuarios, catálogos, unidades y cambios dentro de su ámbito autorizado. |

### 3.2 Requerimientos no funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RNF-WEB-001 | Primer parcial | Alta | Técnica | El sistema web deberá construirse con Python, Flask, Jinja2, HTML5, CSS3 y JavaScript; las gráficas deberán utilizar Highcharts. |
| RNF-WEB-002 | Transversal | Alta | Técnica | El sistema web deberá conservar sus funciones propias cuando la aplicación móvil o la aplicación de escritorio no estén disponibles. |
| RNF-WEB-003 | Primer parcial | Alta | Técnica | La interfaz deberá ser responsive, navegable mediante teclado y ofrecer etiquetas, contraste, mensajes, búsqueda, filtros y paginación apropiados para las tareas y navegadores definidos. |
| RNF-WEB-004 | Primer parcial | Alta | Técnica | Las operaciones demostradas deberán utilizar persistencia real y manejar errores de forma consistente sin revelar secretos, trazas internas o información sensible. |

## 4. Módulo de microservicios

### 4.1 Requerimientos funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RF-MS-001 | Posterior | Alta | Clínica/normativa | Los servicios de donantes y receptores deberán administrar por separado sus registros, estados, datos autorizados, consentimientos y necesidades, sin mezclar sus responsabilidades clínicas. |
| RF-MS-002 | Posterior | Alta | Demostrativa | El servicio de inventario deberá administrar unidades sanguíneas, disponibilidad, estados y movimientos regionales, preservando un tratamiento especializado para órganos. |
| RF-MS-003 | Posterior | Alta | Clínica/normativa | El servicio de compatibilidad deberá ejecutar matching sanguíneo y HLA únicamente con reglas autorizadas y versionadas, señalar información faltante y devolver una explicación auditable. |
| RF-MS-004 | Posterior | Alta | Clínica/normativa | El servicio de priorización deberá ordenar candidatos o solicitudes mediante ranking multicriterio, utilizando solo la urgencia registrada por personal autorizado e incorporando, cuando corresponda, resultados autorizados de comparación u optimización por distancia y tiempo; deberá devolver factores, ponderaciones, versión y explicación. |
| RF-MS-005 | Posterior | Media | Técnica | El servicio geográfico deberá calcular, comparar u optimizar alternativas por distancia y tiempo estimado, mediante una fuente definida, para apoyar la priorización y la planeación de traslados, conservando procedencia, fecha y limitaciones del cálculo. |
| RF-MS-006 | Posterior | Alta | Técnica | Los servicios de transporte y cadena de custodia deberán gestionar órdenes, estados, incidencias, ubicación autorizada y eventos append-only de recolección y entrega con responsable, tiempo, condición y evidencia. |
| RF-MS-007 | Posterior | Alta | Técnica | El servicio de alertas deberá generar, dirigir, deduplicar y cerrar alertas de urgencia, caducidad, retraso e inconsistencias detectadas en duplicados, estados, secuencias o inventarios. |
| RF-MS-008 | Posterior | Alta | Técnica | El servicio de auditoría deberá recibir y permitir consultar eventos autorizados de autenticación, acceso, cambio, resultados algorítmicos, decisiones y cadena de custodia. |
| RF-MS-009 | Posterior | Media | Demostrativa | El módulo deberá pronosticar riesgo de caducidad y sugerir balanceo regional mediante datos históricos o sintéticos, indicando limitaciones y sin ejecutar transferencias automáticamente. |

### 4.2 Requerimientos no funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RNF-MS-001 | Posterior | Alta | Técnica | A partir del segundo parcial, los microservicios deberán implementarse con Flask y REST versionado, permanecer separados del sistema web, atender responsabilidades justificadas y desplegarse en contenedores independientes. |
| RNF-MS-002 | Posterior | Alta | Técnica | Los microservicios deberán producir respuestas tanto en JSON como en XML según el consumidor. Las API deberán documentarse mediante OpenAPI o Swagger y definir autenticación, parámetros, contratos y ejemplos de ambos formatos, códigos HTTP, validaciones y formato uniforme de errores; las respuestas XML deberán validarse mediante XSD donde corresponda. |
| RNF-MS-003 | Posterior | Alta | Técnica | Toda petición protegida deberá validar JWT, sesión, revocación y permisos mediante los mecanismos definidos, incluida Redis. |
| RNF-MS-004 | Posterior | Alta | Técnica | Toda petición deberá aplicar límites configurables y registrar servicio, versión, tiempo, resultado e identificador de correlación sin exponer datos sensibles. |
| RNF-MS-005 | Posterior | Alta | Técnica | Los servicios deberán manejar timeouts, dependencias inaccesibles, reintentos seguros e idempotencia donde corresponda, evitando corrupción y fallos en cascada. |
| RNF-MS-006 | Posterior | Media | Técnica | Los algoritmos y flujos críticos deberán medirse con media, p95 y p99 bajo datos y concurrencia documentados; Locust deberá incluir varios perfiles, errores, saturación y recuperación. |

## 5. Aplicación móvil Android

### 5.1 Requerimientos funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RF-MOV-001 | Posterior | Alta | Técnica | La aplicación deberá permitir iniciar, renovar y cerrar sesión mediante JWT, consultar el perfil y mostrar un menú diferenciado entre Donante y Personal de traslado. |
| RF-MOV-002 | Posterior | Alta | Clínica/normativa | El Donante deberá poder enviar un registro preliminar con datos mínimos y consultar su estado pendiente de validación presencial o profesional. |
| RF-MOV-003 | Posterior | Media | Técnica | El Donante deberá poder consultar campañas y programar, consultar o cancelar citas conforme a la información publicada. |
| RF-MOV-004 | Posterior | Media | Clínica/normativa | El Donante deberá poder recibir avisos de elegibilidad o seguimiento emitidos a partir de una decisión autorizada. |
| RF-MOV-005 | Posterior | Alta | Técnica | El Personal de traslado deberá poder consultar sus órdenes, escanear el recurso asignado y confirmar recolección y entrega con responsable, fecha, ubicación y resultado de verificación. |
| RF-MOV-006 | Posterior | Media | Técnica | La aplicación deberá capturar ubicación y evidencia fotográfica únicamente durante el traslado, evento y periodo autorizados. |
| RF-MOV-007 | Posterior | Alta | Técnica | La aplicación deberá conservar temporalmente operaciones permitidas sin conexión y sincronizarlas al recuperar conectividad, informando conflictos o rechazos. |

### 5.2 Requerimientos no funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RNF-MOV-001 | Posterior | Alta | Técnica | La aplicación se desarrollará para Android en Java o Kotlin, consumirá exclusivamente JSON y utilizará al menos cuatro microservicios. |
| RNF-MOV-002 | Posterior | Alta | Técnica | El dispositivo, los tokens y los datos temporales deberán registrarse y almacenarse de forma segura, eliminarse al cerrar sesión y respetar la finalidad y retención de ubicación y fotografías. |
| RNF-MOV-003 | Posterior | Alta | Técnica | La interfaz deberá indicar conectividad, validar formularios y manejar errores y sincronización sin perder silenciosamente información capturada. |
| RNF-MOV-004 | Posterior | Media | Técnica | La aplicación deberá incorporar al menos dos capacidades pertinentes del dispositivo y evaluar mediante tareas los flujos de Donante y Personal de traslado. |

## 6. Aplicación de escritorio

### 6.1 Requerimientos funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RF-DESK-001 | Posterior | Alta | Técnica | La aplicación deberá permitir iniciar y cerrar sesión mediante JWT y mostrar las operaciones autorizadas para Operador de banco de sangre y Coordinador regional. |
| RF-DESK-002 | Posterior | Alta | Demostrativa | El Operador deberá poder registrar y actualizar unidades y gestionar inventario, movimientos, estados y alertas mediante los microservicios. |
| RF-DESK-003 | Posterior | Alta | Clínica/normativa | El Operador deberá poder capturar y consultar pruebas con estado, responsable y revisión autorizada. |
| RF-DESK-004 | Posterior | Alta | Clínica/normativa | El personal autorizado deberá poder consultar compatibilidad y priorización explicables y registrar aceptación, rechazo, reevaluación o excepción sin alterar el cálculo original. |
| RF-DESK-005 | Posterior | Media | Clínica/normativa | El Operador deberá poder imprimir etiquetas mediante una plantilla o codificación previamente autorizada. |
| RF-DESK-006 | Posterior | Alta | Técnica | El personal autorizado deberá poder registrar y consultar eventos de cadena de custodia mediante los microservicios. |
| RF-DESK-007 | Posterior | Media | Clínica/normativa | El personal autorizado deberá poder consultar tablas, buscar, filtrar, generar y exportar reportes operativos o regulatorios en los formatos definidos. |

### 6.2 Requerimientos no funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RNF-DESK-001 | Posterior | Alta | Técnica | La tecnología deberá seleccionarse entre las opciones autorizadas y la aplicación deberá operar desacoplada de las vistas y sesiones internas del sistema web. |
| RNF-DESK-002 | Posterior | Alta | Técnica | La aplicación deberá consumir exclusivamente XML validado mediante XSD, protegerse contra XXE y utilizar al menos cuatro microservicios. |
| RNF-DESK-003 | Posterior | Alta | Técnica | La aplicación deberá validar sesión y permisos mediante servicios y manejar errores de autenticación, contrato y red sin perder silenciosamente formularios. |
| RNF-DESK-004 | Posterior | Media | Técnica | Los flujos repetitivos de captura, consulta, exportación e impresión deberán evaluarse mediante tareas de usabilidad para los perfiles internos. |

## 7. Bases de datos y almacenamiento

### 7.1 Requerimientos funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RF-DAT-001 | Primer parcial | Alta | Técnica | PostgreSQL deberá persistir instituciones, usuarios, permisos, catálogos, inventario, estados y auditoría básica, incluir datos ficticios iniciales y ampliar posteriormente los datos estructurados aprobados. |
| RF-DAT-002 | Posterior | Alta | Técnica | MongoDB deberá almacenar documentos flexibles, telemetría, historiales extensos o resultados semiestructurados cuyo modelo documental esté justificado. |
| RF-DAT-003 | Posterior | Alta | Técnica | A partir del segundo parcial, Redis deberá administrar sesiones, revocaciones, permisos temporales, rate limiting, caché autorizada, bloqueos, contadores y datos temporales con expiración definida. |
| RF-DAT-004 | Posterior | Alta | Técnica | Google Cloud Storage deberá almacenar evidencias, documentos, reportes e imágenes, conservando en las bases únicamente referencias y metadatos autorizados. |
| RF-DAT-005 | Transversal | Alta | Técnica | Los registros de auditoría y custodia deberán conservar identificadores, actor, tiempo, acción, entidad, resultado y datos mínimos necesarios para reconstruir cada evento. |

### 7.2 Requerimientos no funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RNF-DAT-001 | Transversal | Alta | Técnica | Los clientes no deberán acceder directamente a los almacenes y la distribución deberá definir un único propietario autoritativo para cada dato. |
| RNF-DAT-002 | Transversal | Alta | Técnica | Las reservas y asignaciones deberán utilizar transacciones, restricciones o bloqueos que impidan estados contradictorios y doble asignación. |
| RNF-DAT-003 | Posterior | Alta | Técnica | Los archivos grandes no deberán almacenarse en bases de datos y los objetos privados deberán entregarse mediante URLs firmadas con vigencia limitada. |
| RNF-DAT-004 | Transversal | Alta | Técnica | Cada almacén deberá definir claves, restricciones, índices, crecimiento, retención, eliminación lógica, segregación, respaldo y restauración; las pruebas deberán medir volumen, caché y consumo de recursos. |

## 8. Infraestructura e integración

### 8.1 Requerimientos no funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RNF-INF-001 | Primer parcial | Alta | Técnica | El repositorio deberá documentar estrategia de ramas, incidencias, tablero, estándares de codificación y convenciones de nombres. |
| RNF-INF-002 | Primer parcial | Alta | Técnica | Cada componente deberá declarar dependencias y variables de entorno sin almacenar secretos o valores reales en el repositorio. |
| RNF-INF-003 | Posterior | Alta | Técnica | A partir del segundo parcial, los componentes desplegables deberán contar con Dockerfile y Docker Compose deberá reproducir el entorno local con PostgreSQL, MongoDB y Redis. |
| RNF-INF-004 | Posterior | Alta | Técnica | La distribución en Google Compute Engine deberá documentar web, microservicios, datos, archivos y monitoreo, utilizando redes privadas, firewall, puertos mínimos y comunicaciones cifradas. |
| RNF-INF-005 | Posterior | Media | Técnica | La integración continua deberá ejecutar validaciones y permitir desplegar componentes independientes sin exigir el despliegue simultáneo de toda la plataforma. |
| RNF-INF-006 | Posterior | Alta | Técnica | La plataforma deberá demostrar al menos tres procesos integrales y, en uno de ellos, la consulta coherente desde distintos clientes respetando JSON para móvil y XML para escritorio. |
| RNF-INF-007 | Posterior | Alta | Técnica | Ante una falla parcial, la plataforma deberá detectarla, registrarla, evitar corrupción y recuperar la operación cuando la dependencia se restablezca. |
| RNF-INF-008 | Transversal | Alta | Técnica | Cada incremento deberá aportar pruebas proporcionales al riesgo: unitarias, integración, sistema, regresión, extremo a extremo, contratos, autenticación, fallos, concurrencia, archivos, datos masivos, seguridad y usabilidad. |

## 9. Seguridad y privacidad

### 9.1 Requerimientos funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RF-SEC-001 | Transversal | Alta | Técnica | El componente de seguridad deberá autenticar usuarios y emitir, renovar, rotar, expirar y revocar tokens y sesiones mediante los mecanismos definidos. |
| RF-SEC-002 | Primer parcial | Alta | Técnica | El Administrador deberá poder asignar perfiles y ámbitos institucionales sin otorgar facultades clínicas adicionales. |
| RF-SEC-003 | Transversal | Alta | Técnica | El sistema deberá registrar intentos fallidos y auditar autenticaciones, accesos sensibles, permisos, operaciones críticas, resultados algorítmicos, aprobaciones y anulaciones. |

### 9.2 Requerimientos no funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RNF-SEC-001 | Transversal | Alta | Técnica | En el primer parcial, las contraseñas deberán usar hash seguro y los JWT de acceso deberán tener expiración definida. A partir del segundo parcial, los tokens de renovación deberán rotarse o aplicar un control equivalente y la sesión y revocación deberán validarse mediante Redis. |
| RNF-SEC-002 | Transversal | Alta | Técnica | Toda petición protegida deberá aplicar mínimo privilegio y validar rol, acción, recurso y ámbito institucional. |
| RNF-SEC-003 | Transversal | Alta | Técnica | Las consultas deberán ser parametrizadas y las entradas JSON, XML, formularios y archivos deberán validarse, incluyendo protección contra inyección y XXE. |
| RNF-SEC-004 | Transversal | Alta | Técnica | Los endpoints deberán aplicar rate limiting, registrar intentos fallidos y realizar bloqueo temporal conforme al riesgo configurado. |
| RNF-SEC-005 | Transversal | Alta | Técnica | Las comunicaciones deberán cifrarse y los secretos deberán mantenerse fuera del código y de archivos versionados. |
| RNF-SEC-006 | Transversal | Alta | Técnica | Interfaces, respuestas, logs y errores deberán minimizar u ocultar datos personales, clínicos, ubicación, fotografías, tokens y secretos. |
| RNF-SEC-007 | Posterior | Alta | Clínica/normativa | La ubicación y las fotografías deberán limitarse a perfiles, finalidades, traslados y periodos autorizados y eliminarse localmente cuando dejen de ser necesarias. |
| RNF-SEC-008 | Transversal | Alta | Clínica/normativa | Las políticas de consentimiento, retención, bloqueo, eliminación e intercambio interinstitucional deberán validarse antes de utilizar datos reales. |

## 10. Monitoreo y observabilidad

### 10.1 Requerimientos funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RF-MON-001 | Posterior | Alta | Técnica | El servicio de monitoreo deberá consultar periódicamente los endpoints de salud, incluidos proceso y dependencias aplicables de base de datos, Redis, MongoDB y Storage. |
| RF-MON-002 | Posterior | Alta | Técnica | El panel deberá mostrar servicios disponibles, degradados o caídos, tiempo promedio, último error, dependencia causante, versión, fecha de verificación y número de errores. |
| RF-MON-003 | Posterior | Media | Técnica | El servicio deberá conservar y permitir consultar el historial de disponibilidad y cambios de estado. |
| RF-MON-004 | Posterior | Alta | Técnica | El servicio deberá generar avisos de caída, degradación y recuperación dirigidos a los responsables configurados. |

### 10.2 Requerimientos no funcionales

| ID | Fase | Prioridad | Validación | Requerimiento |
| --- | --- | --- | --- | --- |
| RNF-MON-001 | Posterior | Alta | Técnica | Los health checks deberán distinguir proceso detenido, dependencia inaccesible, respuesta inválida y timeout mediante estados diferenciados. |
| RNF-MON-002 | Posterior | Alta | Técnica | La indisponibilidad del monitoreo no deberá detener las operaciones propias de los componentes supervisados. |
| RNF-MON-003 | Posterior | Alta | Técnica | Logs y métricas deberán ser centralizables, usar timestamps e identificadores de correlación y no almacenar datos clínicos o secretos innecesarios. |
