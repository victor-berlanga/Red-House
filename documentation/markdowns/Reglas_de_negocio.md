# Reglas de negocio

> **Proyecto:** Red regional de bancos de sangre y donación de órganos — Equipo 01.  
> **Estado:** borrador consolidado para validación académica.  
> **Fecha:** 7 de septiembre de 2026.  
> **Cobertura:** proyecto académico completo, con aplicación gradual por parciales e incrementos.

## 1. Propósito y alcance

Las reglas de negocio establecen las condiciones que rigen la operación de la plataforma y la relación entre actores, procesos, información y decisiones. Se expresan como restricciones, autorizaciones, condiciones y consecuencias del dominio, con independencia de las pantallas, tecnologías o mecanismos utilizados para implementarlas.

La fase **Primer parcial** identifica las reglas necesarias para el producto mínimo funcional del sistema web. Las reglas **Posteriores** continúan dentro del alcance completo y deberán considerarse desde el análisis y la arquitectura, aunque su proceso todavía no esté implementado. Las reglas **Transversales** se aplicarán en todos los incrementos y componentes a los que correspondan.

La plataforma es una herramienta de coordinación y apoyo y no sustituye la evaluación médica, ética o normativa. Las reglas clínicas o regulatorias deberán validarse con fuentes vigentes y responsables competentes antes de utilizarse fuera de una demostración académica. Mientras esa validación no exista, se usarán únicamente datos ficticios y reglas demostrativas claramente identificadas.

El alcance se limita a las condiciones propias del negocio. Las decisiones de tecnología, arquitectura, rendimiento, despliegue y pruebas se consideran especificaciones técnicas separadas, salvo cuando condicionan directamente una operación, como la autorización, la trazabilidad, la prevención de una doble asignación o la protección de una evidencia.

## 2. Convenciones

### 2.1 Identificación

Cada regla utiliza el prefijo `RN`, seguido de un código de dominio y un número consecutivo. Los códigos no representan componentes técnicos, porque una misma regla puede aplicarse al sistema web, a los microservicios y a las aplicaciones cliente.

| Código | Dominio |
| --- | --- |
| GOB | Gobierno de reglas y responsabilidad humana |
| ACC | Acceso, perfiles, instituciones y catálogos |
| PER | Donantes, receptores, campañas y citas |
| INV | Inventario, caducidad y viabilidad de recursos |
| SOL | Solicitudes, estudios, compatibilidad y priorización |
| LOG | Asignación, traslado y cadena de custodia |
| COM | Alertas, paneles, reportes, evidencias y auditoría |

### 2.2 Fase y validación

| Clasificación | Significado |
| --- | --- |
| Primer parcial | Debe aplicarse al producto mínimo funcional definido para esta etapa. |
| Posterior | Pertenece al alcance completo y se aplicará cuando se implemente el proceso correspondiente. |
| Transversal | Debe considerarse desde el diseño y aplicarse en cada incremento pertinente. |
| Técnica | Puede validarse mediante decisiones administrativas, datos ficticios, pruebas y evidencia del proyecto. |
| Demostrativa | Solo representa comportamiento académico y no constituye una regla clínica oficial. |
| Clínica/normativa | Requiere validación de especialistas, autoridades o fuentes regulatorias competentes antes de uso real. |

Cada regla es obligatoria cuando el flujo al que pertenece forma parte del incremento correspondiente. La fase indica el momento de aplicación y no modifica su obligatoriedad.

## 3. Gobierno de reglas y responsabilidad humana

| ID | Fase | Validación | Regla de negocio | Trazabilidad principal |
| --- | --- | --- | --- | --- |
| RN-GOB-001 | Transversal | Clínica/normativa | La plataforma podrá calcular, ordenar, alertar o recomendar alternativas, pero ninguna elegibilidad, compatibilidad, prioridad, asignación, liberación o baja que requiera juicio profesional quedará confirmada sin la intervención de la persona o autoridad autorizada. | RF-WEB-012, RF-WEB-013, RF-MS-003, RF-MS-004; HU-WEB-012, HU-MS-001, HU-DESK-003 |
| RN-GOB-002 | Transversal | Clínica/normativa | Toda regla de compatibilidad, elegibilidad, urgencia, conservación, priorización o asignación deberá identificar su fuente, versión, vigencia, ámbito de aplicación y responsable de aprobación antes de utilizarse como criterio autorizado. | RF-MS-003, RF-MS-004, RF-DESK-004; HU-MS-001, HU-DESK-003 |
| RN-GOB-003 | Transversal | Demostrativa | Los datos, parámetros y resultados creados para una demostración deberán identificarse como ficticios o demostrativos y no podrán mostrarse como decisiones clínicas, datos reales ni evidencia de cumplimiento regulatorio. | RF-WEB-008, RF-MS-002, RF-MS-009; HU-WEB-004, HU-WEB-008, HU-MS-004 |
| RN-GOB-004 | Transversal | Clínica/normativa | Los procesos de sangre y de órganos deberán conservar datos, estados, pruebas, tiempos, reglas, responsables y evidencias diferenciados; compartir infraestructura no autoriza a aplicar automáticamente las mismas reglas a ambos recursos. | RF-WEB-006, RF-WEB-007, RF-WEB-008, RF-WEB-009, RF-MS-001, RF-MS-002; HU-WEB-006, HU-WEB-007, HU-WEB-008, HU-WEB-009 |
| RN-GOB-005 | Transversal | Clínica/normativa | Cada resultado algorítmico deberá conservar las entradas relevantes, la versión de reglas o método, los factores utilizados, la fecha y una explicación reproducible. Una nueva versión producirá un resultado nuevo y no modificará el resultado previamente revisado. | RF-WEB-012, RF-MS-003, RF-MS-004, RF-MS-009; HU-MS-001, HU-MS-004, HU-DESK-003 |

## 4. Acceso, perfiles, instituciones y catálogos

| ID | Fase | Validación | Regla de negocio | Trazabilidad principal |
| --- | --- | --- | --- | --- |
| RN-ACC-001 | Primer parcial | Técnica | El alcance completo conservará los perfiles Administrador, Operador de banco de sangre, Personal médico autorizado, Coordinador regional, Personal de traslado, Donante y Auditor. Durante el primer parcial solo se habilitarán funcionalmente Administrador, Operador de banco de sangre y Auditor. | RF-WEB-003, RF-WEB-015, RF-SEC-002; HU-WEB-002, HU-WEB-003, HU-WEB-013 |
| RN-ACC-002 | Transversal | Técnica | Una operación protegida solo podrá ejecutarse cuando la identidad, la sesión, el perfil, la acción, el recurso y el ámbito institucional estén activos y autorizados. Conocer la dirección o el identificador de un recurso no concede acceso. | RF-WEB-002, RF-WEB-003, RF-MOV-001, RF-DESK-001, RF-SEC-001, RF-SEC-002, RNF-SEC-002; HU-WEB-002, HU-WEB-003, HU-WEB-016, HU-MOV-001, HU-DESK-001 |
| RN-ACC-003 | Transversal | Clínica/normativa | Administrar usuarios, instituciones o catálogos no otorga facultades clínicas. La asignación de un perfil clínico tampoco sustituye la acreditación, autorización profesional o designación institucional que deba comprobarse por separado. | RF-WEB-003, RF-SEC-002; HU-WEB-003 |
| RN-ACC-004 | Primer parcial | Técnica | El sitio público solo podrá mostrar información institucional y de contacto autorizada; no expondrá inventarios detallados, identidad, datos clínicos, logística, evidencias ni auditoría. | RF-WEB-001; HU-WEB-001 |
| RN-ACC-005 | Primer parcial | Técnica | La institución se administrará como una entidad y será la fuente conceptual única de la información institucional utilizada como catálogo de referencia por los demás procesos. Desactivarla no eliminará su historial ni sus relaciones anteriores. | RF-WEB-004, RF-WEB-005; HU-WEB-004, HU-WEB-005 |
| RN-ACC-006 | Primer parcial | Técnica | Un valor de catálogo que ya tenga historial o referencias no se eliminará de forma que invalide operaciones anteriores; se inactivará cuando corresponda. Las altas, modificaciones e inactivaciones conservarán responsable, fecha y evidencia de auditoría. | RF-WEB-004; HU-WEB-004 |

## 5. Donantes, receptores, campañas y citas

| ID | Fase | Validación | Regla de negocio | Trazabilidad principal |
| --- | --- | --- | --- | --- |
| RN-PER-001 | Posterior | Clínica/normativa | Un registro enviado por un donante desde la aplicación móvil será preliminar y permanecerá pendiente de validación presencial o profesional; no declarará elegibilidad ni creará automáticamente una donación. | RF-MOV-002, RF-MS-001; HU-MOV-002 |
| RN-PER-002 | Posterior | Clínica/normativa | El expediente de un donante contendrá únicamente los datos, consentimientos, restricciones y estados autorizados para el tipo de donación. Toda actualización conservará responsable, fecha e historial, y el sistema no declarará elegibilidad por sí mismo. | RF-WEB-006, RF-MS-001; HU-WEB-006 |
| RN-PER-003 | Posterior | Clínica/normativa | Un aviso de elegibilidad o seguimiento deberá originarse en una decisión autorizada, identificar fecha y entidad emisora y distinguir información, revisión pendiente y decisión confirmada. Leer o descartar el aviso no modificará el estado del donante. | RF-MOV-004; HU-MOV-004 |
| RN-PER-004 | Posterior | Clínica/normativa | El expediente de un receptor solo podrá ser consultado o modificado por personal y ámbitos autorizados. Registrar al receptor no creará automáticamente una cuenta, y la urgencia o condición clínica será capturada o confirmada por personal autorizado. | RF-WEB-007, RF-WEB-010; HU-WEB-007, HU-WEB-010 |
| RN-PER-005 | Posterior | Técnica | Una campaña deberá estar publicada y vigente para ofrecer citas. La programación validará disponibilidad antes de confirmar; cada cita tendrá un folio y un solo estado vigente, y su cancelación o cambio seguirá las transiciones definidas sin crear duplicados. | RF-MOV-003; HU-MOV-003 |

## 6. Inventario, caducidad y viabilidad de recursos

| ID | Fase | Validación | Regla de negocio | Trazabilidad principal |
| --- | --- | --- | --- | --- |
| RN-INV-001 | Primer parcial | Demostrativa | Cada unidad sanguínea ficticia tendrá un identificador de trazabilidad único y conservará institución, ubicación, tipo de componente, fechas y estado. Solo podrá seguir transiciones configuradas, y cada cambio conservará responsable, fecha y motivo cuando corresponda. | RF-WEB-008, RF-MS-002, RF-DESK-002; HU-WEB-008, HU-DESK-002 |
| RN-INV-002 | Primer parcial | Demostrativa | La proximidad de caducidad del primer parcial se calculará mediante un parámetro demostrativo visible y configurable. Una unidad vencida, dada de baja o en otro estado no disponible no podrá presentarse como disponible para una nueva operación. | RF-WEB-008; HU-WEB-008 |
| RN-INV-003 | Posterior | Clínica/normativa | La disponibilidad y viabilidad de un órgano se administrarán mediante un flujo especializado y reglas autorizadas; no se tratarán como inventario sanguíneo ordinario y un cambio de disponibilidad no equivaldrá a una asignación. | RF-WEB-009, RF-MS-002; HU-WEB-009 |
| RN-INV-004 | Posterior | Clínica/normativa | Una unidad o recurso no avanzará a un estado que requiera pruebas aprobadas mientras falten resultados obligatorios o exista una inconsistencia conforme a reglas validadas. Un resultado incompleto, contradictorio o pendiente no se considerará confirmado. | RF-WEB-011, RF-DESK-003; HU-WEB-011, HU-DESK-002 |
| RN-INV-005 | Posterior | Demostrativa | Un pronóstico de caducidad o una sugerencia de balanceo se distinguirá de la fecha y el estado reales del recurso, identificará datos, periodo, versión y limitaciones, y no modificará inventarios ni ejecutará transferencias automáticamente. | RF-MS-009; HU-MS-004 |
| RN-INV-006 | Posterior | Clínica/normativa | Una etiqueta utilizará únicamente la plantilla, codificación y campos autorizados para el tipo de recurso, y su código corresponderá al identificador de trazabilidad seleccionado. Toda reimpresión requerirá un motivo y conservará evidencia de auditoría. | RF-DESK-005; HU-DESK-004 |

## 7. Solicitudes, estudios, compatibilidad y priorización

| ID | Fase | Validación | Regla de negocio | Trazabilidad principal |
| --- | --- | --- | --- | --- |
| RN-SOL-001 | Posterior | Clínica/normativa | Una solicitud conservará folio, receptor, institución solicitante, necesidad, responsable, fecha y urgencia autorizada. Una solicitud incompleta no avanzará a evaluación y deberá indicar la información faltante. | RF-WEB-010; HU-WEB-010 |
| RN-SOL-002 | Posterior | Clínica/normativa | La urgencia será registrada o confirmada exclusivamente por personal autorizado; el sistema y los algoritmos no la inferirán de datos parciales ni la modificarán por cuenta propia. | RF-WEB-010, RF-MS-004; HU-WEB-007, HU-WEB-010, HU-MS-001 |
| RN-SOL-003 | Posterior | Clínica/normativa | Cada prueba o estudio conservará tipo, sujeto o recurso relacionado, responsable, fecha, estado y fuente. Una corrección mantendrá el resultado anterior, la justificación y el responsable; capturar un resultado no autorizará automáticamente disponibilidad, compatibilidad o asignación. | RF-WEB-011, RF-DESK-003; HU-WEB-011, HU-DESK-002 |
| RN-SOL-004 | Posterior | Clínica/normativa | El cálculo de compatibilidad solo utilizará datos suficientes y reglas autorizadas y versionadas para el proceso correspondiente. La falta de información se mostrará expresamente y no se interpretará como compatibilidad. | RF-WEB-012, RF-MS-003; HU-MS-001, HU-DESK-003 |
| RN-SOL-005 | Posterior | Clínica/normativa | La priorización solo utilizará factores autorizados. Podrá considerar urgencia registrada, tiempo y distancia cuando corresponda, pero no incorporará fórmulas ni ponderaciones inventadas. Todo cálculo geográfico identificará origen, destino, fuente, fecha y limitaciones. | RF-MS-004, RF-MS-005; HU-MS-001, HU-MS-002, HU-DESK-003 |
| RN-SOL-006 | Posterior | Clínica/normativa | La aceptación, el rechazo, la reevaluación o una excepción se registrarán como decisiones humanas con responsable y motivo, vinculadas con la versión exacta del resultado revisado. La decisión no alterará el cálculo original. | RF-WEB-012, RF-DESK-004; HU-MS-001, HU-DESK-003 |

## 8. Asignación, traslado y cadena de custodia

| ID | Fase | Validación | Regla de negocio | Trazabilidad principal |
| --- | --- | --- | --- | --- |
| RN-LOG-001 | Posterior | Clínica/normativa | Antes de confirmar una asignación se mostrarán la solicitud, el recurso, los resultados de apoyo disponibles, los datos faltantes y las advertencias aplicables. La asignación requerirá confirmación humana autorizada y conservará responsable, fecha y justificación. | RF-WEB-013; HU-WEB-012 |
| RN-LOG-002 | Posterior | Clínica/normativa | Un recurso no podrá mantener más de una reserva o asignación activa incompatible al mismo tiempo. Liberar, cancelar o reasignar requerirá una transición válida y un motivo, conservará el historial y no sobrescribirá la decisión anterior. | RF-WEB-013, RNF-DAT-002; HU-WEB-012 |
| RN-LOG-003 | Posterior | Técnica | Una orden de traslado identificará recurso, instituciones de origen y destino, responsable asignado, horario y estado. Solo mostrará al personal de traslado la información clínica mínima indispensable para ejecutar la orden. | RF-WEB-014, RF-MS-006; HU-MS-002, HU-MOV-005 |
| RN-LOG-004 | Posterior | Técnica | Antes de confirmar una recolección o entrega, el código escaneado deberá coincidir con el recurso y con el evento esperado de la orden. Una discrepancia bloqueará la confirmación y permitirá registrar una incidencia. | RF-MOV-005; HU-MOV-005 |
| RN-LOG-005 | Posterior | Técnica | Los eventos de cadena de custodia se registrarán en secuencia con responsable, fecha, condición, ubicación autorizada e evidencia cuando corresponda. Un evento confirmado no se editará ni eliminará; una corrección generará un evento relacionado y un reintento no deberá duplicarlo. | RF-MS-006, RF-DESK-006, RF-DAT-005; HU-MS-002, HU-MOV-005, HU-DESK-005 |
| RN-LOG-006 | Posterior | Clínica/normativa | La ubicación y la evidencia fotográfica solo podrán capturarse para una orden, evento, finalidad y periodo autorizados. Se vincularán con el evento correspondiente, se almacenarán de forma privada y las copias locales innecesarias se eliminarán al terminar su finalidad. | RF-MOV-006, RNF-SEC-007; HU-MOV-006 |
| RN-LOG-007 | Posterior | Técnica | Solo las operaciones previamente definidas como seguras podrán conservarse sin conexión. Una decisión clínica o asignación no se confirmará sin validación del servidor; la sincronización será idempotente y todo conflicto, rechazo o vencimiento permanecerá visible hasta su resolución. | RF-MOV-007; HU-MOV-007 |

## 9. Alertas, paneles, reportes, evidencias y auditoría

| ID | Fase | Validación | Regla de negocio | Trazabilidad principal |
| --- | --- | --- | --- | --- |
| RN-COM-001 | Posterior | Técnica | Cada alerta conservará tipo, origen, entidad relacionada, prioridad operativa, destinatario, fecha y estado; solo se dirigirá a perfiles y ámbitos capaces de actuar. Los eventos repetidos se deduplicarán o relacionarán, y una alerta no ejecutará automáticamente una decisión clínica, baja o transferencia. | RF-MS-007, RF-MOV-004; HU-MS-003, HU-MOV-004 |
| RN-COM-002 | Transversal | Técnica | Durante el primer parcial, el panel principal básico mostrará a los perfiles iniciales únicamente datos persistidos y accesos autorizados de catálogos, inventario sanguíneo ficticio y auditoría. Posteriormente podrá evolucionar al panel regional; un dato inexistente no se sustituirá por una cifra simulada no identificada. | RF-WEB-015; HU-WEB-013 |
| RN-COM-003 | Posterior | Clínica/normativa | Un reporte solo incluirá plantillas, periodos, instituciones y campos autorizados para el perfil. Identificará fecha, filtros, fuente y responsable; mientras un formato no haya sido validado se presentará como académico u operativo y no como reporte regulatorio oficial. | RF-WEB-016, RF-DESK-007; HU-WEB-014, HU-DESK-006 |
| RN-COM-004 | Posterior | Técnica | Un archivo o evidencia deberá superar las validaciones de tipo, tamaño, finalidad y permiso, se almacenará de forma privada y conservará referencia y metadatos autorizados. Su consulta utilizará acceso temporal y las cargas, consultas y descargas sensibles quedarán auditadas. | RF-WEB-017, RF-DAT-004, RNF-DAT-003; HU-WEB-015 |
| RN-COM-005 | Transversal | Técnica | Un evento de auditoría conservará identificador, actor, tiempo, acción, entidad y resultado. Los eventos no se editarán ni eliminarán; una corrección generará un evento relacionado. El Auditor tendrá acceso de solo lectura dentro de su ámbito y toda exportación respetará minimización y también quedará auditada. | RF-WEB-018, RF-MS-008, RF-DAT-005, RF-SEC-003; HU-WEB-016 |

## 10. Vigencia y control de cambios

La vigencia de cada regla dependerá de su clasificación y de las validaciones requeridas. Las reglas **Demostrativas** conservarán una identificación visible y no se reutilizarán como criterios reales sin una validación posterior. Las reglas **Clínicas/normativas** permanecerán pendientes hasta contar con una fuente vigente y la aprobación competente.

Toda modificación deberá registrar la versión, la fecha de vigencia, el responsable y los procesos afectados. Las operaciones ya registradas conservarán la versión aplicada, sin alterar retrospectivamente resultados, decisiones ni evidencias auditadas.
