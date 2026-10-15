Trabaja en:
/Users/victorberlanga/Programacion/integracion/Red-House

OBJETIVO

Completar los faltantes del segundo parcial mediante implementación funcional, pruebas reales, documentación y evidencias. No te limites a proponer cambios.

Fuente de requisitos:
/Users/victorberlanga/Programacion/integracion/stuff/entregaSegundoParcial.txt

Fecha de entrega: 22 de octubre de 2026.

1. REVISIÓN INICIAL OBLIGATORIA

Lee AGENTS.md, PROJECT_STATUS.md, el enunciado completo y:
- documentation/markdowns/Revision_segundo_parcial.md
- documentation/markdowns/Esquema_compartido.md
- Las guías vigentes de arquitectura, instalación, persistencia y pruebas.

Usa CodeGraph antes de buscar o leer código. Comprueba su estado y sincronízalo cuando corresponda.

Inspecciona el árbol de trabajo y respeta todos los cambios existentes. No reviertas trabajo ajeno ni sobrescribas datos.

El informe del 14 de octubre es una referencia histórica:
- PostgreSQL ahora utiliza una base compartida red_house, con permisos por servicio.
- Monitoreo ya tiene pipelines de agregación MongoDB.
- Comprueba el estado actual antes de declarar faltantes o implementar duplicados.
- No atribuyas al código actual resultados de pruebas anteriores.

Crea una matriz de trabajo con requisito, estado comprobado, implementación pendiente, dependencias, prueba y evidencia de cierre.

2. DECISIONES CONFIRMADAS POR EL USUARIO

A. Continuidad:
La web debe mantener sus operaciones de negocio aunque un microservicio esté detenido o actualizándose. Una página pública accesible o un mensaje 503 no satisfacen este requisito.

Los futuros clientes móvil y escritorio también deben conservar servicio ante la caída de una instancia. No basta con que sus pantallas abran.

B. PostgreSQL:
Conservar la base compartida red_house y los datos existentes. No regresar a once bases ni eliminar permisos institucionales o por servicio.

C. GCP:
El usuario tiene Google Cloud. Puedes inspeccionar configuración, identidad activa, proyectos y buckets mediante comandos gcloud de lectura. No imprimir secretos.

D. Segundo parcial:
Android y escritorio están excluidos de implementación. Preparar y probar sus contratos JSON/XML y la disponibilidad de sus API, sin construir esas aplicaciones.

3. RESOLVER PRIMERO LA ARQUITECTURA DE CONTINUIDAD

El portal actual consume las API y carece de backend monolítico autónomo. No declares independencia mientras siga dependiendo obligatoriamente de ellas.

Diseña, documenta e implementa una solución que cumpla:

- Operaciones web comprometidas disponibles al detener las API de negocio.
- Reutilización controlada y versionada de reglas de aplicación/dominio para evitar implementaciones divergentes entre monolito y servicios.
- Monolito con backend propio y acceso autorizado a persistencia; ninguna lógica clínica principal en JavaScript.
- Microservicios independientes de vistas, plantillas y sesiones internas web.
- Móvil y escritorio consumen exclusivamente API JSON/XML. Nunca acceden directamente a PostgreSQL, MongoDB o Redis.
- API con descubrimiento/enrutamiento y redundancia para soportar la caída o actualización de una instancia.
- Considerar también Identidad, workers y demás dependencias del flujo; replicar únicamente Donantes no acredita continuidad global.

Distingue explícitamente:
1) caída de una instancia;
2) caída de todas las instancias de un servicio;
3) caída de Redis o PostgreSQL.

No prometas operaciones completas cuando todas sus autoridades están inaccesibles. Implementa redundancia para el fallo previsto y documenta los límites restantes. Si una decisión necesaria cambia el alcance confirmado, solicita aclaración concreta mientras continúas tareas independientes.

Preserva JWT, revocación y permisos Redis. No eludas autenticación para simular disponibilidad.

Evita doble escritura, divergencia de reglas, reservas duplicadas y reintentos inseguros. Ante pérdida de respuesta de una escritura, utiliza idempotencia y consulta de estado antes de repetirla o cambiar de backend.

Documenta una matriz de fallos con comportamiento esperado por operación y componente.

4. DOCKER Y DESPLIEGUE REPRODUCIBLE

El enunciado exige Dockerfile y contenedor propio por microservicio.

Implementa:
- Dockerfile por servicio; imágenes construibles y actualizables individualmente.
- Contenedores para monolito, Monitoreo y procesos auxiliares necesarios.
- Workers con ciclo de vida y salud verificables.
- Compose con PostgreSQL, MongoDB, Redis, aplicaciones y enrutamiento/redundancia necesarios.
- Redes y DNS internos, puertos mínimos publicados y configuración por entorno.
- Usuarios sin privilegios cuando corresponda.
- Volúmenes persistentes y secretos externos a imágenes/repositorio.
- Inicialización repetible de esquema compartido, permisos, ACL, claves y datos ficticios.
- Migraciones explícitas y compatibles con actualizaciones; no migraciones destructivas al arrancar.
- Readiness, liveness, límites de espera, recuperación y logs.

No introduzcas Kubernetes ni servicios adicionales sin necesidad demostrada.

Mantén el entorno local existente. Desarrolla y prueba Compose en un entorno separado. No montes simultáneamente los archivos físicos de la base local en otro motor.

Comprueba instalación desde un clon limpio, reinicio conservando datos y actualización de una instancia manteniendo las operaciones previstas.

5. COMPLETAR MONGODB

Reutiliza las agregaciones de Monitoreo existentes y verifica su funcionamiento.

Demuestra:
- Inserción.
- Consulta.
- Actualización.
- Filtrado.
- Pipelines.
- Creación y uso de índices.
- Recuperación mediante identificadores relacionados con PostgreSQL.

Implementa las actualizaciones faltantes sobre una proyección mutable útil del negocio, con propietario, permisos y versión. No modifiques eventos de auditoría o custodia inmutables para satisfacer la rúbrica.

Prueba deduplicación, eventos desordenados, reconstrucción y recuperación cuando aplique. Justifica índices mediante planes de ejecución y consultas reales.

6. ARCHIVOS REALES EN GOOGLE CLOUD STORAGE

Inspecciona GCP mediante gcloud sin exponer credenciales. Si hay varios proyectos o buckets posibles, pregunta cuál corresponde antes de utilizarlos.

Implementa el flujo web completo:
- Selección y carga.
- Asociación autorizada al proceso.
- Validación de tamaño, contenido, MIME y hash.
- Estados persistentes.
- Consulta y descarga privada mediante URLs firmadas.

Reutiliza el adaptador existente. Prueba bucket real, permisos, objeto ausente, archivo inválido, URL expirada y fallos de dependencia.

No publiques objetos ni otorgues permisos amplios. Antes de crear recursos con coste o cambiar IAM, presenta la configuración concreta y solicita la autorización necesaria. Continúa el trabajo local independiente mientras tanto.

7. WEB, SEGURIDAD Y CONTRATOS

Conserva y prueba perfiles, administración, donantes, receptores, inventario, solicitudes, evaluación humana, reservas, traslados, custodia, alertas, auditoría, filtros, paginación y Highcharts.

Completa las brechas del alcance comprometido. Distingue exportación de página, exportación completa y reporte regulatorio. No presentes ayuda de acceso como recuperación de contraseña funcional.

Mantén:
- JWT validado, renovación y revocación.
- Autorización institucional y por recurso.
- Sesiones y permisos Redis coherentes entre monolito y API.
- Rate limiting, TTL y caché autorizada.
- JSON/XML, XSD, errores uniformes, correlación e idempotencia.
- Protección XML contra XXE.
- Swagger ejecutable con ejemplos correctos y de error.

No inventes reglas clínicas, HLA, prioridad o conservación. Preserva revisión humana y límites académicos documentados.

8. EVIDENCIA POR ENDPOINT

Genera un inventario actualizado de métodos/rutas; no fijes el número histórico de operaciones.

Para cada endpoint, conserva:
- Objetivo, URL, método, parámetros y headers.
- Petición y respuesta reales.
- Código HTTP.
- Evidencia de persistencia cuando corresponda.
- Error controlado aplicable.
- Captura de ejecución mediante Swagger, Postman o equivalente.
- Fecha, versión y correlación.

Incluye éxito, validación, recurso inexistente, autenticación, autorización y conflictos según corresponda.

Cubre JSON/XML y contratos internos firmados. No confundas ejemplos generados con peticiones ejecutadas.

Automatiza la recopilación reproducible y redacta secretos antes de guardar artefactos. No debilites seguridad para ejecutar ejemplos.

9. PRUEBAS Y CRITERIOS DE CIERRE

Ejecuta pruebas unitarias, integración y recorridos web relevantes en la versión final.

Demuestra, como mínimo:
- Flujo completo de sangre.
- Flujo separado de órganos dentro del alcance existente.
- Donación/procesamiento.
- JWT inválido/expirado, logout, revocación y permisos.
- JSON/XML/XSD.
- Concurrencia, idempotencia y prevención de reservas duplicadas.
- MongoDB, Redis y archivos GCS reales.
- Persistencia tras reiniciar contenedores.
- Web operativa con API detenidas.
- Consumo JSON/XML operativo al detener una instancia detrás del enrutamiento.
- Actualización controlada sin interrumpir las operaciones previstas.
- Fallos de dependencias con recuperación sin corrupción.

Las pruebas de disponibilidad deben ejecutar operaciones de negocio, no limitarse a health checks.

No aumentes timeouts ni ocultes fallos para obtener resultados verdes. Conserva diagnóstico, esperado, obtenido y evidencia. No detengas servicios del entorno habitual para pruebas destructivas.

10. DOCUMENTACIÓN Y PRESENTACIÓN

Actualiza las fuentes vigentes y el informe de cumplimiento.

Entrega documento técnico integral con:
- Problema, objetivos, alcance, integrantes y actores.
- Requisitos y correcciones del primer parcial comprobadas.
- Arquitectura y decisiones de continuidad.
- Diagramas actuales de componentes, despliegue, comunicación, secuencia y datos.
- Modelo físico PostgreSQL compartido.
- Diseño MongoDB y Redis.
- Ficha completa de cada servicio.
- Contratos, seguridad y evidencias HTTP.
- Instalación Docker, operación, respaldo y recuperación.
- Pruebas, resultados, limitaciones y trazabilidad.

Prepara guion presencial, reparto de participación, demostración reproducible y material para video de YouTube.

No inventes participación, grabación ni publicación. Si publicar requiere intervención del usuario, deja el material preparado y especifica la acción pendiente. No declares completa la entrega mientras falten requisitos externos obligatorios.

11. FORMA DE TRABAJO

Avanza por incrementos ejecutables. Primero arquitectura de continuidad y despliegue; después brechas funcionales, evidencias y documentación.

No pidas confirmación para decisiones rutinarias ya autorizadas. Pregunta solo por ambigüedades materiales, acceso externo o acciones que requieran autorización.

Actualiza PROJECT_STATUS.md después de trabajo material, con decisiones, pruebas, riesgos y pendientes. Mantén CodeGraph sincronizado.

No declares “todo funciona” sin evidencia. Al terminar, entrega:
- Cambios realizados.
- Comandos reproducibles.
- Resultados de pruebas.
- Enlaces a documentación y evidencias.
- Matriz final de cumplimiento.
- Pendientes y bloqueos concretos, con su impacto.

Comienza inspeccionando el estado real y continúa con la implementación. No termines únicamente con un plan.
