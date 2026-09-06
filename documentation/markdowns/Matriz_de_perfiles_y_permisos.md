# Matriz de perfiles y permisos

> **Proyecto:** Red regional de bancos de sangre y donación de órganos — Equipo 01.  
> **Estado:** borrador consolidado para validación académica.  
> **Fecha:** 7 de septiembre de 2026.  
> **Cobertura:** proyecto académico completo, con habilitación gradual por parciales e incrementos.

## 1. Propósito y alcance

Las autorizaciones de la plataforma se organizan mediante siete perfiles funcionales, el ámbito institucional asignado y las condiciones particulares de cada recurso u operación. La pertenencia a un perfil no concede acceso general: toda acción protegida requiere identidad y sesión activas, permiso vigente, ámbito autorizado y acceso al recurso solicitado.

La matriz comprende el sistema web, la aplicación móvil Android, la aplicación de escritorio y las operaciones expuestas por los microservicios. Ningún perfil accede directamente a PostgreSQL, MongoDB, Redis o Google Cloud Storage; dichos recursos se utilizan únicamente a través de los componentes autorizados de la plataforma.

Los siete perfiles pertenecen al alcance completo. Durante el primer parcial solo se habilitarán funcionalmente **Administrador**, **Operador de banco de sangre** y **Auditor**. Las autorizaciones clínicas y regulatorias descritas para etapas posteriores permanecerán sujetas a validación competente y no se interpretarán como acreditaciones profesionales.

## 2. Criterios de autorización

### 2.1 Principios aplicables

- Se aplicará denegación por defecto y mínimo privilegio: toda operación no concedida expresamente permanecerá bloqueada.
- La autorización comprobará perfil, acción, recurso y ámbito institucional; conocer una dirección o un identificador no concede acceso.
- Un perfil administrativo u operativo no otorga facultades clínicas, y un perfil clínico no sustituye la acreditación profesional o institucional correspondiente.
- Las consultas regionales mostrarán únicamente la información necesaria para la finalidad autorizada y quedarán sujetas a auditoría.
- La compatibilidad, la priorización y las recomendaciones algorítmicas serán elementos de apoyo; las decisiones que lo requieran conservarán intervención humana autorizada.
- La ubicación, las fotografías y los datos logísticos solo estarán disponibles durante el proceso, finalidad y periodo autorizados.
- Las operaciones sensibles, los cambios de permisos, los accesos restringidos y las decisiones quedarán registrados sin exponer secretos ni información innecesaria.

### 2.2 Fases de habilitación

| Fase | Aplicación en la matriz |
| --- | --- |
| Primer parcial | Permisos funcionales del producto mínimo: identidad, perfiles iniciales, instituciones, catálogos, inventario sanguíneo ficticio, panel básico y auditoría. |
| Posterior | Permisos del alcance completo que se habilitarán con microservicios, aplicación móvil, aplicación de escritorio y procesos clínicos u operativos posteriores. |
| Transversal | Controles que se aplican desde el inicio y continúan en todo componente e incremento pertinente. |

### 2.3 Tipos de permiso

| Código | Significado |
| --- | --- |
| CON | Consultar información autorizada sin modificarla. |
| REG | Registrar o actualizar información dentro del flujo permitido. |
| ADM | Administrar altas, cambios, activaciones o inactivaciones de una entidad de configuración. |
| REV | Revisar información de apoyo y registrar una decisión humana autorizada. |
| EJE | Ejecutar o confirmar una operación asignada. |
| EXP | Generar o exportar información autorizada. |

Los códigos describen el tipo de acción, no una jerarquía entre perfiles. Un permiso solo es efectivo dentro de su fase, componente, ámbito y condiciones de validación.

## 3. Perfiles y niveles de autorización

| Perfil | Nivel de autorización | Ámbito funcional | Componentes utilizados | Habilitación |
| --- | --- | --- | --- | --- |
| Administrador | Administración acotada por ámbito | Usuarios, perfiles, instituciones, catálogos, configuración y supervisión técnica autorizada; sin facultades clínicas | Sistema web y, posteriormente, panel de monitoreo | Primer parcial |
| Operador de banco de sangre | Operación institucional | Donantes autorizados, unidades sanguíneas, inventario, pruebas capturadas, etiquetas, custodia y reportes operativos | Sistema web y, posteriormente, aplicación de escritorio | Primer parcial |
| Personal médico autorizado | Acceso clínico restringido | Donantes, receptores, solicitudes, estudios y revisión explicable de compatibilidad o priorización conforme a su autorización | Sistema web y, posteriormente, aplicación de escritorio para la revisión especializada autorizada | Posterior |
| Coordinador regional | Coordinación regional minimizada y auditable | Solicitudes, candidatos, asignaciones, disponibilidad, traslados, cadena de custodia, alertas e indicadores regionales | Sistema web y aplicación de escritorio | Posterior |
| Personal de traslado | Operación logística temporal y asignada | Órdenes propias, identificación del recurso, recolección, entrega, incidencias, ubicación y evidencia autorizada | Aplicación móvil Android | Posterior |
| Donante | Autoservicio sobre información propia | Registro preliminar, perfil propio, campañas, citas y avisos autorizados | Aplicación móvil Android y contenido público del sistema web | Posterior |
| Auditor | Consulta independiente de solo lectura | Bitácoras, trazabilidad, evidencias y reportes autorizados dentro de su ámbito | Sistema web | Primer parcial |

El consumo de microservicios será indirecto a través del sistema web o de las aplicaciones cliente. El perfil no modifica esta separación ni habilita conexiones directas con los almacenes de datos.

## 4. Responsabilidades e información autorizada

| Perfil | Responsabilidades | Información que puede consultar | Información que puede registrar o modificar | Restricciones principales |
| --- | --- | --- | --- | --- |
| Administrador | Configurar el acceso y la representación administrativa de la red dentro de su ámbito | Usuarios, perfiles, ámbitos, instituciones, sedes, catálogos, parámetros, panel propio y estado técnico autorizado | Cuentas, asignaciones de perfil y ámbito, instituciones, sedes, catálogos y parámetros administrativos | No consulta datos clínicos por el solo hecho de administrar; no confirma elegibilidad, compatibilidad, prioridad ni asignación |
| Operador de banco de sangre | Mantener la operación del inventario y la trazabilidad institucional | Donantes autorizados, unidades, movimientos, estados, caducidad, pruebas capturadas, alertas, custodia, evidencias y reportes operativos permitidos | Datos autorizados de donantes, unidades, movimientos, estados, resultados capturados, etiquetas, eventos de custodia y archivos operativos | No determina elegibilidad ni sustituye la revisión médica; no modifica cálculos, decisiones clínicas o auditoría |
| Personal médico autorizado | Registrar y revisar información clínica necesaria para solicitudes y decisiones humanas | Donantes, receptores, solicitudes, urgencia registrada, estudios, recursos candidatos, datos faltantes, compatibilidad y priorización explicables | Expedientes autorizados, solicitudes, urgencia confirmada, estudios y decisiones de aceptación, rechazo, reevaluación o excepción | Solo actúa dentro de su acreditación y ámbito; no administra cuentas o configuración ni utiliza reglas clínicas pendientes como criterios reales |
| Coordinador regional | Coordinar disponibilidad, asignaciones y traslados entre instituciones | Vista regional minimizada de solicitudes, candidatos, inventario pertinente, asignaciones, traslados, custodia, alertas, indicadores, evidencias y reportes | Decisiones autorizadas, reservas o asignaciones, órdenes de traslado, incidencias, eventos de custodia y documentación operativa | No altera resultados algorítmicos ni sustituye decisiones médicas o regulatorias; toda excepción requiere motivo y auditoría |
| Personal de traslado | Ejecutar el traslado asignado y conservar su cadena de custodia | Identificador del recurso, origen, destino, horario, estado, instrucciones logísticas mínimas y eventos de la orden propia | Escaneos, confirmaciones de recolección y entrega, incidencias, ubicación y evidencia fotográfica autorizada | No consulta expedientes ni información clínica innecesaria; el acceso termina con el periodo autorizado y no puede confirmar asignaciones |
| Donante | Gestionar su participación preliminar en campañas y citas | Perfil y estado propios, campañas publicadas, citas propias y avisos emitidos por personal autorizado | Registro preliminar propio y operaciones permitidas sobre sus citas | No consulta inventarios, receptores ni datos de terceros; el registro preliminar no declara elegibilidad ni crea una donación confirmada |
| Auditor | Examinar evidencia y trazabilidad sin intervenir en la operación | Autenticaciones, accesos, usuarios, catálogos, unidades, cambios, decisiones, custodia, evidencias y reportes autorizados y minimizados | Ningún dato del negocio; sus consultas o exportaciones autorizadas generan su propia evidencia de auditoría | Acceso de solo lectura; no corrige, elimina, aprueba ni ejecuta operaciones y no obtiene acceso clínico indiscriminado |

## 5. Matriz consolidada de permisos

| Área | Operación protegida | Perfil o perfiles autorizados | Permiso | Fase y condición |
| --- | --- | --- | --- | --- |
| Identidad | Iniciar y cerrar la sesión propia y consultar el perfil vigente | Los siete perfiles, conforme se habiliten | CON, EJE | Primer parcial para los tres perfiles iniciales; posterior para los cuatro restantes |
| Identidad | Recuperar el acceso mediante el flujo seguro definido | Los siete perfiles con cuenta habilitada | EJE | Posterior |
| Acceso | Administrar usuarios, perfiles y ámbitos institucionales | Administrador | ADM | Primer parcial; limitado al ámbito propio y con auditoría |
| Red | Administrar instituciones y sedes participantes | Administrador | ADM | Primer parcial; la institución es la fuente conceptual única |
| Configuración | Administrar catálogos y parámetros autorizados | Administrador | ADM | Primer parcial para instituciones y tipos de componentes sanguíneos; ampliación posterior |
| Paneles | Consultar el panel principal básico según el perfil | Administrador, Operador de banco de sangre y Auditor | CON | Primer parcial; únicamente datos persistidos y accesos iniciales |
| Paneles | Consultar indicadores y panel regional permitidos | Coordinador regional; los demás perfiles internos solo respecto de indicadores expresamente autorizados | CON | Posterior; vista minimizada por perfil y ámbito |
| Donantes | Registrar o mantener el expediente autorizado de un donante | Operador de banco de sangre y Personal médico autorizado | REG, CON | Posterior; sin declaración automática de elegibilidad |
| Receptores | Registrar o mantener el expediente y la participación autorizada de un receptor | Personal médico autorizado | REG, CON | Posterior; el receptor no obtiene una cuenta por defecto |
| Donantes | Enviar y consultar un registro preliminar propio | Donante | REG, CON | Posterior; pendiente de validación presencial o profesional |
| Campañas y citas | Consultar campañas y programar, consultar o cancelar citas propias | Donante | CON, REG | Posterior; solo campañas publicadas y vigentes |
| Avisos | Consultar avisos propios de elegibilidad o seguimiento | Donante | CON | Posterior; el aviso debe proceder de una decisión autorizada |
| Inventario sanguíneo | Registrar unidades ficticias, consultar inventario y cambiar estados permitidos | Operador de banco de sangre | REG, CON | Primer parcial con caducidad demostrativa; ampliación posterior |
| Órganos | Mantener disponibilidad y viabilidad mediante el flujo especializado | Personal médico autorizado | REG, CON | Posterior; separado del inventario sanguíneo y sujeto a validación clínica |
| Pruebas y estudios | Capturar resultados y consultar su estado e historial | Operador de banco de sangre y Personal médico autorizado | REG, CON | Posterior; la captura no confirma compatibilidad ni disponibilidad |
| Etiquetas | Imprimir o reimprimir una etiqueta trazable | Operador de banco de sangre | EJE | Posterior; plantilla autorizada y motivo de reimpresión |
| Solicitudes | Registrar y dar seguimiento a solicitudes ordinarias o urgentes | Personal médico autorizado | REG, CON | Posterior; urgencia registrada o confirmada por personal autorizado |
| Compatibilidad | Consultar candidatos, datos faltantes y resultados explicables | Personal médico autorizado y Coordinador regional | CON, REV | Posterior; reglas autorizadas y versionadas |
| Priorización | Consultar el ordenamiento y sus factores de urgencia, tiempo y distancia | Personal médico autorizado y Coordinador regional | CON, REV | Posterior; sin fórmulas ni ponderaciones inventadas |
| Revisión humana | Registrar aceptación, rechazo, reevaluación o excepción justificada | Personal médico autorizado y Coordinador regional, según la competencia validada | REV | Posterior; no modifica el cálculo original |
| Asignación | Reservar, asignar, liberar, cancelar o reasignar un recurso | Coordinador regional, sujeto a la autorización clínica o normativa aplicable | REV, EJE | Posterior; confirmación humana y prevención de doble asignación |
| Traslado | Programar órdenes y consultar su seguimiento regional | Coordinador regional | REG, CON | Posterior |
| Traslado | Consultar y ejecutar la orden asignada mediante escaneo | Personal de traslado | CON, EJE | Posterior; coincidencia obligatoria entre orden, recurso y evento |
| Traslado | Registrar ubicación y evidencia fotográfica | Personal de traslado | REG | Posterior; únicamente durante la orden, evento y periodo autorizados |
| Custodia | Registrar o consultar eventos de recolección, traslado y entrega | Personal de traslado, Operador de banco de sangre y Coordinador regional, según el evento asignado | REG, CON, EJE | Posterior; eventos secuenciales y no editables |
| Operación móvil | Conservar y sincronizar operaciones seguras permitidas sin conexión | Donante y Personal de traslado | EJE | Posterior; no incluye decisiones clínicas o asignaciones sin validación del servidor |
| Alertas | Consultar y atender alertas dirigidas al perfil | Los siete perfiles, únicamente según el tipo de alerta y su capacidad de actuación | CON, EJE | Posterior |
| Reportes | Consultar, filtrar y exportar reportes autorizados | Operador de banco de sangre, Coordinador regional y Auditor | CON, EXP | Posterior; los formatos no validados no se presentan como regulatorios oficiales |
| Archivos | Cargar archivos o evidencias vinculados con una operación | Operador de banco de sangre, Personal médico autorizado y Coordinador regional | REG | Posterior; tipo, tamaño, finalidad y permiso validados |
| Archivos | Consultar o descargar archivos y evidencias autorizados | Operador de banco de sangre, Personal médico autorizado, Coordinador regional y Auditor | CON | Posterior; acceso privado, temporal y auditado |
| Auditoría | Buscar, filtrar y consultar la bitácora autorizada | Auditor | CON | Primer parcial para usuarios, catálogos, unidades y cambios; ampliación transversal |
| Monitoreo | Consultar salud, disponibilidad, errores e historial de los servicios | Administrador | CON | Posterior; no concede acceso al contenido clínico de logs o trazas |

## 6. Participantes sin perfil funcional

| Participante | Tratamiento dentro de la plataforma |
| --- | --- |
| Público general | Consulta únicamente el contenido público autorizado; no posee permisos privados. |
| Receptor o paciente | Es una persona protegida y sujeto de información; no dispone de acceso directo en el alcance definido. |
| Institución u hospital | Determina el ámbito de usuarios y datos y se administra como entidad; no constituye un perfil. |
| Autoridad regulatoria | Puede recibir reportes autorizados cuando corresponda; no se define un acceso ordinario a la plataforma. |
| Personal técnico o de soporte | Opera infraestructura fuera de los perfiles del negocio; cualquier acceso excepcional a datos debe justificarse, limitarse y auditarse. |
