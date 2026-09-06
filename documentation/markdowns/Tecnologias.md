# Tecnologías a utilizar: MongoDB, Redis y contenedores Docker

> **Proyecto:** Red regional de bancos de sangre y donación de órganos — Equipo 01.  
> **Estado:** investigación tecnológica introductoria.  
> **Fecha:** 7 de septiembre de 2026.  
> **Alcance temporal:** estudio durante el primer parcial; diseño detallado, configuración y uso funcional a partir del segundo parcial.

## 1. Propósito y delimitación

Este documento presenta los fundamentos de MongoDB, Redis y la contenerización con Docker, así como su aplicación prevista dentro de la plataforma regional. Su finalidad es establecer una base conceptual común antes de que estas tecnologías se estudien e implementen formalmente durante el segundo parcial.

La investigación no constituye un diseño físico, una instalación ni evidencia de funcionamiento. Durante el primer parcial, el producto mínimo funcional utilizará PostgreSQL como almacenamiento real y se ejecutará localmente mediante dependencias y variables documentadas, sin requerir MongoDB, Redis o Docker. Los diagramas arquitectónicos pueden mostrar las tres tecnologías porque describen la solución objetivo del semestre, pero deberán identificarlas como componentes posteriores.

Las propuestas de uso aquí descritas proceden del análisis, los requerimientos, las historias de usuario, las reglas de negocio y el diseño arquitectónico vigentes. Las estructuras concretas de documentos, claves, índices, expiraciones, volúmenes, redes y archivos de configuración se definirán cuando comience el segundo parcial y exista suficiente conocimiento técnico para validarlas.

## 2. Papel de las tecnologías en la solución

MongoDB, Redis y Docker resuelven problemas diferentes y no sustituyen a PostgreSQL ni entre sí.

| Tecnología | Tipo | Responsabilidad prevista | No deberá utilizarse para |
| --- | --- | --- | --- |
| PostgreSQL | Base de datos relacional transaccional | Conservar desde el primer parcial instituciones, usuarios, permisos, catálogos, inventario, estados y auditoría básica; ampliar después los datos estructurados autorizados | Almacenar archivos grandes o datos temporales que no requieran persistencia duradera |
| MongoDB | Base de datos documental | Conservar desde el segundo parcial documentos flexibles, telemetría autorizada, historiales extensos o resultados semiestructurados cuando el modelo documental esté justificado | Duplicar sin control el estado transaccional de inventarios, solicitudes o asignaciones |
| Redis | Almacén de estructuras de datos de acceso rápido | Administrar desde el segundo parcial sesiones, revocaciones, caché, límites, bloqueos, contadores y otros datos temporales con expiración definida | Ser la única fuente duradera de una operación clínica, logística o de auditoría |
| Docker | Plataforma de contenerización | Empaquetar desde el segundo parcial el web, los microservicios y sus dependencias; reproducir el entorno distribuido mediante Docker Compose | Reemplazar el diseño de seguridad, los respaldos, el monitoreo o la separación lógica de responsabilidades |

La selección del almacén dependerá de la estructura, duración, consistencia y patrón de consulta de cada dato. La selección de Docker dependerá de qué componentes sean desplegables; las aplicaciones Android y de escritorio seguirán distribuyéndose como clientes y no como contenedores de backend.

## 3. MongoDB

### 3.1 Concepto general

MongoDB es una base de datos documental. Su unidad básica es el documento y los registros se almacenan en BSON, una representación binaria relacionada con JSON que admite tipos adicionales, documentos anidados y arreglos (MongoDB, Inc., s. f.-a). Este modelo permite representar información cuya estructura puede evolucionar o contener grupos de campos variables sin forzarla de inmediato a un conjunto rígido de tablas.

La flexibilidad no significa ausencia de diseño. Cada colección deberá tener un propósito, un propietario de datos, reglas de validación, referencias, índices y políticas de crecimiento y retención. MongoDB crea un identificador único `_id` para los documentos y limita el tamaño de cada documento BSON a 16 MiB; por ello, fotografías, estudios y demás archivos grandes seguirán almacenándose en Google Cloud Storage y las bases conservarán únicamente referencias y metadatos autorizados (MongoDB, Inc., s. f.-a).

### 3.2 Usos previstos en el proyecto

MongoDB se reservará para información cuyo carácter documental, semiestructurado o de crecimiento histórico aporte una ventaja clara.

| Información candidata | Motivo de uso documental | Límite de la propuesta |
| --- | --- | --- |
| Telemetría autorizada de traslados | Cada evento puede reunir ubicación, tiempo, precisión, estado del dispositivo y contexto operativo variable | Solo se conservará durante periodos y finalidades autorizados; la ubicación reciente podrá permanecer temporalmente en Redis |
| Historiales extensos de evaluaciones | Permiten conservar entradas, versión, factores, advertencias y explicación de una ejecución sin sobrescribir versiones anteriores | El resultado es apoyo a la decisión y no sustituye la aprobación humana ni el estado transaccional de la solicitud |
| Eventos técnicos y de monitoreo | Los atributos pueden variar según servicio, dependencia, versión o tipo de falla | No deberán incluir secretos, tokens completos ni información sensible innecesaria |
| Documentos o resultados semiestructurados | Algunos estudios o evidencias derivadas pueden tener campos variables según su tipo y versión | Su uso deberá justificarse; los datos relacionales estables permanecerán en PostgreSQL y los binarios en Cloud Storage |

Estas categorías son candidatas arquitectónicas, no colecciones aprobadas. Durante el segundo parcial se determinará si conviene embeber datos relacionados dentro de un documento o utilizar referencias entre documentos. La decisión deberá considerar cómo se consulta y actualiza la información, su tamaño, su crecimiento y quién es su fuente autoritativa.

### 3.3 Consultas, índices y consistencia

Los índices permiten reducir la cantidad de documentos que MongoDB debe revisar para resolver una consulta, aunque también agregan costo a las escrituras porque cada inserción o actualización debe mantenerlos (MongoDB, Inc., s. f.-b). Por ello, no se crearán índices para cada campo. Se definirán a partir de consultas reales, filtros frecuentes y evidencia obtenida con planes de ejecución o mediciones.

Las operaciones sobre un solo documento son atómicas. MongoDB también admite transacciones que abarcan varios documentos cuando se requiere atomicidad, pero su documentación advierte que tienen un costo mayor y no sustituyen un modelo adecuado (MongoDB, Inc., s. f.-c). En este proyecto, las asignaciones, reservas y demás estados transaccionales críticos permanecerán principalmente en PostgreSQL; MongoDB no se adoptará para evitar deliberadamente las restricciones relacionales que protegen esos procesos.

### 3.4 Beneficios, riesgos y controles iniciales

- **Beneficio esperado:** representar historiales y documentos variables sin crear una tabla nueva para cada variación legítima.
- **Riesgo:** duplicar datos que ya tienen una fuente autoritativa en PostgreSQL. **Control:** conservar identificadores comunes, propietario definido y una sola ruta autorizada de escritura.
- **Riesgo:** acumular documentos sin límite. **Control:** definir retención, archivado, índices y mediciones de crecimiento antes de usar datos reales.
- **Riesgo:** asumir que flexibilidad equivale a aceptar cualquier estructura. **Control:** validar los documentos y versionar su esquema lógico desde los contratos del servicio propietario.
- **Riesgo:** guardar archivos o datos sensibles innecesarios. **Control:** almacenar binarios en Cloud Storage, minimizar campos y aplicar autorización y auditoría.

## 4. Redis

### 4.1 Concepto general

Redis es un servidor de estructuras de datos. Además de valores simples, ofrece estructuras como cadenas, hashes, listas, conjuntos, conjuntos ordenados y otras opciones orientadas a caché, colas o procesamiento de eventos (Redis, s. f.-a). Sus operaciones rápidas y la posibilidad de asignar una vigencia a los datos lo hacen apropiado para información temporal o de coordinación.

Redis puede configurarse sin persistencia, con instantáneas RDB, con un registro AOF de operaciones o con una combinación de ambos mecanismos (Redis, s. f.-b). La elección depende de cuánto dato puede perderse y de cómo debe recuperarse el servicio. En esta plataforma no se asumirá que Redis es durable: los hechos que deban reconstruir una decisión, un movimiento o una cadena de custodia deberán conservarse en el almacén autoritativo correspondiente.

### 4.2 Usos previstos en el proyecto

| Uso previsto | Finalidad | Condición necesaria |
| --- | --- | --- |
| Sesiones y tokens revocados | Compartir el estado de autenticación entre web y microservicios y rechazar un token antes de su vencimiento | Comienza en el segundo parcial; cada entrada tendrá expiración congruente con la vigencia de la sesión o del token |
| Caché de consultas autorizadas | Evitar cálculos o lecturas repetitivas cuando el resultado pueda reutilizarse de forma segura | Debe existir una estrategia de invalidación y no podrá servir información de otro perfil o institución |
| Rate limiting y contadores | Limitar peticiones, registrar ventanas temporales y apoyar bloqueos por intentos fallidos | Los límites deberán ser configurables y medirse para no impedir operaciones legítimas |
| Bloqueos e idempotencia | Coordinar temporalmente operaciones concurrentes o evitar el procesamiento duplicado de una solicitud | El estado definitivo se confirmará en PostgreSQL; el bloqueo tendrá duración y liberación controladas |
| Alertas, deduplicación y ubicación reciente | Mantener información de corta duración utilizada para coordinación inmediata | Cada dato tendrá finalidad, propietario y tiempo de expiración; el historial autorizado se enviará al almacén duradero correspondiente |

### 4.3 Beneficios, riesgos y controles iniciales

- **Beneficio esperado:** centralizar estado temporal compartido sin depender de la memoria de un único proceso.
- **Riesgo:** perder datos por expiración, reinicio o configuración de persistencia. **Control:** no utilizar Redis como única evidencia de negocio y documentar la recuperación ante su caída.
- **Riesgo:** entregar información obsoleta desde caché. **Control:** definir vigencia e invalidación según el cambio del dato autoritativo.
- **Riesgo:** dejar claves sin vencimiento. **Control:** asignar TTL a sesiones, revocaciones, bloqueos, contadores y datos temporales cuando corresponda.
- **Riesgo:** mezclar instituciones o responsabilidades. **Control:** establecer convenciones de nombres, propietario por familia de claves y autorización en el servicio; ningún cliente accederá directamente a Redis.

## 5. Contenedores Docker

### 5.1 Concepto general

Un contenedor es un proceso aislado que incluye los archivos y dependencias necesarios para ejecutar un componente. A diferencia de una máquina virtual completa, comparte el núcleo del sistema anfitrión, lo que reduce la sobrecarga, aunque no elimina la necesidad de configurar recursos, redes y seguridad (Docker, Inc., s. f.-c). La imagen es el paquete inmutable a partir del cual se crea el contenedor, mientras que el Dockerfile contiene las instrucciones para construir esa imagen.

Docker Compose permite definir y ejecutar aplicaciones con varios contenedores mediante un archivo YAML que reúne servicios, redes y volúmenes (Docker, Inc., s. f.-a). En el proyecto se utilizará a partir del segundo parcial para que el equipo pueda levantar una configuración distribuida consistente sin instalar manualmente cada dependencia con versiones diferentes.

Los datos no deberán depender de la capa escribible de un contenedor. Los volúmenes administrados por Docker conservan información fuera del ciclo de vida del contenedor y son el mecanismo recomendado para persistir datos generados por estos procesos (Docker, Inc., s. f.-b). Aun así, un volumen no reemplaza una política de respaldo y restauración.

### 5.2 Uso previsto en el proyecto

- Un Dockerfile para el sistema web y para cada microservicio desplegable cuando se incorporen en el segundo parcial.
- Contenedores independientes para los microservicios implementados, de modo que puedan ejecutarse, probarse y actualizarse por separado.
- Contenedores de PostgreSQL, MongoDB y Redis en el entorno distribuido de desarrollo desde el segundo parcial.
- Docker Compose para declarar servicios, redes privadas de desarrollo, variables no secretas, dependencias, volúmenes y verificaciones de salud aplicables.
- Perfiles o configuraciones que permitan iniciar únicamente los componentes necesarios para una prueba, sin obligar a ejecutar toda la plataforma.

La aplicación Android y la aplicación de escritorio consumirán las API publicadas, pero no se ejecutarán como contenedores del backend. Tampoco accederán directamente a las bases de datos o a Redis.

### 5.3 Beneficios, riesgos y controles iniciales

- **Beneficio esperado:** obtener un entorno repetible entre integrantes, pruebas y despliegues.
- **Riesgo:** considerar que una imagen ejecutable ya es una solución segura. **Control:** usar imágenes confiables, versiones controladas, usuarios sin privilegios innecesarios, secretos externos y superficie mínima.
- **Riesgo:** perder datos al recrear un contenedor. **Control:** utilizar volúmenes, procedimientos de respaldo y pruebas de restauración.
- **Riesgo:** exponer bases o puertos internos. **Control:** publicar solo los puertos necesarios y mantener los almacenes en redes privadas.
- **Riesgo:** agregar demasiados contenedores antes de estabilizar las responsabilidades. **Control:** contenerizar en el segundo parcial únicamente los componentes implementados y conservar la cantidad de microservicios basada en necesidades reales.

## 6. Integración prevista en la plataforma

Las tres tecnologías se utilizarán a través de componentes del backend. El sistema web podrá acceder únicamente a los almacenes autorizados para sus responsabilidades; Android y escritorio deberán comunicarse con los microservicios mediante JSON y XML, respectivamente. Ninguna aplicación cliente tendrá credenciales de PostgreSQL, MongoDB o Redis.

| Flujo previsto desde el segundo parcial | MongoDB | Redis | Docker |
| --- | --- | --- | --- |
| Autenticación compartida | No participa como fuente de identidad | Sesiones, revocación y permisos temporales | Aísla el servicio de identidad y permite conectarlo por una red interna |
| Consulta o actualización de dominio | Documentos flexibles solo cuando el propietario lo justifique | Caché o coordinación temporal cuando corresponda | Ejecuta servicios y almacenes con configuración reproducible |
| Traslado y cadena de custodia | Telemetría o historiales autorizados | Ubicación reciente, deduplicación o idempotencia temporal | Separa transporte, custodia, alertas y dependencias |
| Monitoreo y recuperación | Historial técnico semiestructurado cuando se justifique | Estado temporal o contadores cuando corresponda | Proporciona health checks y permite detener o reiniciar componentes de forma controlada |

La falla de MongoDB, Redis o un contenedor deberá detectarse y registrarse. La plataforma no confirmará una operación si no puede garantizar su consistencia y deberá recuperarse sin duplicarla cuando la dependencia vuelva a estar disponible. Estos comportamientos se implementarán y probarán en los incrementos posteriores que incorporen cada tecnología.

## 7. Adopción durante el semestre

| Etapa | Trabajo previsto | Evidencia esperada |
| --- | --- | --- |
| Primer parcial | Investigar conceptos, usos, beneficios y riesgos; mostrar las tecnologías solo en la arquitectura objetivo; ejecutar el web y PostgreSQL localmente sin contenedores | Este documento, diagramas con fases diferenciadas y producto mínimo con persistencia real en PostgreSQL |
| Segundo parcial | Completar diseños de MongoDB y Redis; definir colecciones, documentos, índices, claves y expiraciones; crear Dockerfiles y Docker Compose; poner las tres tecnologías en operación | Inserciones, consultas, actualizaciones, agregaciones e índices en MongoDB; sesiones, revocaciones, caché y temporales en Redis; contenedores y servicios reproducibles |
| Tercer parcial | Desplegar, monitorear y probar dependencias, rendimiento, fallos y recuperación en la infraestructura definida | Health checks, métricas, pruebas con y sin Redis, fallas controladas, respaldos y evidencia de despliegue |
| Entrega final | Corregir, optimizar y documentar la configuración realmente liberada | Manuales, scripts, configuraciones, resultados de pruebas y demostración integral coherentes con la versión final |

## 8. Criterios para el diseño del segundo parcial

Antes de implementar se deberá responder, como mínimo:

- Qué problema concreto resuelve cada tecnología y por qué PostgreSQL no es suficiente para ese caso.
- Qué servicio es propietario de cada dato y cuál es la fuente autoritativa.
- Qué consultas, escrituras, volumen y crecimiento se esperan.
- Qué validación, índice, expiración, invalidación o transacción requiere el dato.
- Qué sucede si MongoDB o Redis no están disponibles.
- Qué datos deben respaldarse, restaurarse, retenerse o eliminarse.
- Qué imágenes, versiones, puertos, redes, volúmenes y health checks necesita cada contenedor.
- Cómo se mantendrán secretos y credenciales fuera del código y de los archivos versionados.
- Qué prueba reproducible demostrará que el uso de la tecnología aporta valor y no duplica responsabilidades.

Estas respuestas deberán incorporarse a los diseños y contratos correspondientes, sin inventar reglas clínicas ni almacenar datos reales mientras no existan las autorizaciones necesarias.

## 9. Conclusión

MongoDB, Redis y Docker complementarán la arquitectura distribuida del proyecto a partir del segundo parcial. MongoDB atenderá información documental o semiestructurada justificada; Redis administrará estado temporal y coordinación; Docker permitirá reproducir y aislar los componentes desplegables. PostgreSQL continuará siendo la base transaccional y la única tecnología de almacenamiento que deberá funcionar en el producto mínimo del primer parcial.

La adopción gradual evita utilizar herramientas aún no estudiadas como dependencias del primer incremento, sin eliminarlas del alcance completo. El valor de cada tecnología se comprobará mediante responsabilidades claras, datos reales de prueba, fallos controlados y evidencia reproducible durante las etapas posteriores.

## 10. Referencias

Docker, Inc. (s. f.-a). *Docker Compose*. Docker Docs. Recuperado el 3 de septiembre de 2026, de https://docs.docker.com/compose/

Docker, Inc. (s. f.-b). *Volumes*. Docker Docs. Recuperado el 3 de septiembre de 2026, de https://docs.docker.com/engine/storage/volumes/

Docker, Inc. (s. f.-c). *What is a container?* Docker Docs. Recuperado el 3 de septiembre de 2026, de https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/

MongoDB, Inc. (s. f.-a). *Documents*. MongoDB Docs. Recuperado el 3 de septiembre de 2026, de https://www.mongodb.com/docs/manual/core/document/

MongoDB, Inc. (s. f.-b). *Indexes*. MongoDB Docs. Recuperado el 3 de septiembre de 2026, de https://www.mongodb.com/docs/manual/indexes/

MongoDB, Inc. (s. f.-c). *Transactions*. MongoDB Docs. Recuperado el 3 de septiembre de 2026, de https://www.mongodb.com/docs/manual/core/transactions/

Redis. (s. f.-a). *Redis data types*. Redis Docs. Recuperado el 3 de septiembre de 2026, de https://redis.io/docs/latest/develop/data-types/

Redis. (s. f.-b). *Redis persistence*. Redis Docs. Recuperado el 3 de septiembre de 2026, de https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
