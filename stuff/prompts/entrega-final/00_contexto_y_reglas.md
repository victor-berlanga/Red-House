# Contexto y reglas para la entrega final

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Completa el componente solicitado con código funcional, persistencia, integración, pruebas y documentación. Mantén este contexto al ejecutar cualquiera de los prompts de esta carpeta.

## Fuentes y revisión inicial

1. Lee `AGENTS.md`, `PROJECT_STATUS.md`, el prompt de la etapa y este archivo completos.
2. Consulta `documentation/markdowns/Arquitectura.md`, `Datos_y_persistencia.md`, `Algoritmos.md`, `Requerimientos_funcionales_y_no_funcionales.md`, `Matriz_de_trazabilidad.md`, las guías vigentes de instalación y los contratos afectados.
3. Lee la retroalimentación original si está disponible: `/Users/victorberlanga/Programacion/integracion/stuff/retroalimentacionSegundoParcial.txt`. Su cobertura funcional queda incorporada a estos prompts para que puedan usarse aunque ese archivo externo no acompañe al repositorio.
4. Inspecciona el árbol de trabajo y preserva todos los cambios previos. Si existe `.codegraph/`, consulta CodeGraph antes de localizar o leer código; no inicialices un índice inexistente.
5. Contrasta documentación, código, migraciones y evidencia. Las secciones más recientes de `PROJECT_STATUS.md` prevalecen sobre conteos y pendientes históricos. No supongas que los resultados anteriores verifican nuevas modificaciones.
6. Mantén una matriz por requisito con ID, origen, propietario, estado comprobado, acción, dependencia, criterio de aceptación, prueba y evidencia. Clasifica: existente verificado, ampliación, nuevo, pendiente externo o fallo. No confundas implementación con aprobación clínica.
7. Lee el [complemento 09 de rastreo GPS por WebSockets y mapa de Nuevo León](09_rastreo_gps_websockets.md) desde el prompt 01. Su número identifica el archivo, no una etapa que deba aplazarse hasta después del 08. Incorpóralo al backend, clientes, seguridad, pruebas y documentación según su matriz de responsabilidades, sin repetir implementación.

## Base existente que debe conservarse

La revisión del 26 de octubre identificó un portal Flask/Jinja2 autónomo, diez servicios de dominio más Monitoreo, contratos JSON/XML/XSD, JWT y sesiones/permisos Redis, PostgreSQL compartido, documentos MongoDB, GCS privado, Docker y GCE con HTTPS. Hay revisiones humanas, reservas concurrentes, idempotencia, traslados, custodia, auditoría investigable y pruebas en navegador.

Los algoritmos existentes incluyen `RBC-1.0`, `ORGAN-1.0`, `LOGISTICS-1.0` y `COVERAGE-HK-1.0`. Hopcroft–Karp ya tiene prueba frente a búsqueda exhaustiva. El ranking actual usa vencimiento, minutos, distancia e identificador; guarda urgencia y fecha de solicitud como contexto, sin usarlas para ordenar. No declares ausente esa documentación ni presentes ese ranking como prioridad clínica.

HLA clínico, cadena de frío completa, cierre hasta uso o destino final, antimalware y políticas operativas necesitan ampliación. Móvil y escritorio no formaron parte del segundo parcial y ahora sí son productos de la entrega final. RTO/RPO no estaban definidos y validados; los ensayos de respaldo existentes se conservan y deben actualizarse.

La evidencia anterior incluye 182 pruebas de una regresión del 19 de octubre y verificaciones posteriores con alcances propios. No sumes ejecuciones superpuestas ni presentes esas cifras como pruebas recién ejecutadas. La estructura más reciente registrada incorpora 74 tablas de dominio y una técnica del portal; vuelve a comprobar el esquema antes de migrar.

## Decisiones de producto y arquitectura

### Aclaraciones vigentes para cierre y aceptación

Estas decisiones posteriores prevalecen sobre instrucciones heredadas incompatibles de los prompts y la retroalimentación, sin borrar su contexto histórico:

- **Archivos:** el modo operativo principal usa almacenamiento privado en el servidor. Google Cloud Storage (GCS) es opcional para el producto y no condiciona sus flujos; se conserva como requisito académico independiente, con su propia prueba/evidencia y estado. No declares verificada una integración GCS por documentación, variables configuradas o un ensayo del almacenamiento local.
- **Conectividad móvil:** no se exige funcionamiento offline universal. Define cada operación que pueda conservar borrador o caché local; el servidor sigue siendo autoridad. No confirmes en local decisiones, reservas, asignaciones ni custodia.
- **Push:** la entrega física mediante FCM/APNs es una dependencia externa pendiente. No configures cuentas, proyectos, certificados, claves ni dispositivos de proveedor. Sí implementa y verifica la bandeja interna y los adaptadores/contratos de forma aislada, identificando cualquier receptor de laboratorio; no presentes eso como recepción push real.
- **Plataformas de aceptación:** prueba Android en emulador, sin exigir teléfono Android. Prueba iOS en iPhone físico autorizado y no descargues ni exijas Simulator. macOS y Windows 11 son plataformas de trabajo; Linux es objetivo adicional cuyo alcance y evidencia se deben verificar, no presumir.
- **Donante:** la entrada es un feed/inicio de campañas y citas; su agenda existente requiere completar las brechas y verificar su aceptación. Compartir información pública se limita al texto mediante selector nativo del sistema. No agregues cuentas sociales, chat, likes ni feed social.
- **Transportista:** el mapa es la pantalla protagonista durante el traslado. La tarea asignada y su siguiente acción deben quedar visibles y priorizadas.
- **Presentación:** conserva los cinco roles y capacidades ya definidas. Revisa pantallas efectivamente renderizadas y recorridos completos en cada plataforma aplicable; conteos, medidas o análisis de píxeles no sustituyen revisión visual real.
- **Entregables humanos:** grabación de video final, exposición/presentación, subida a Ubiquitous, reflexiones individuales y entrega individual requieren acciones o aportes humanos. Prepara guiones/plantillas e inventario, pero no inventes autoría, evento, respuesta ni evidencia.

Estas aclaraciones no convierten requisitos pendientes en implementados. Conserva los criterios originales que no contradigan una decisión explícita y registra estado, responsable, dependencia, aceptación y prueba en la matriz de continuidad.

- Actualización de alcance del 6 de noviembre de 2026: aplicación móvil para **iOS y Android**, con **Kotlin Multiplatform y Compose Multiplatform** como base del encargo actualizado. Sustituye el alcance anterior exclusivamente Android; no atribuyas esta ampliación a la decisión del 26 de octubre. Escritorio conserva **PySide6 con Python**.
- Conserva las etapas 01 y 02 realizadas; no las reejecutes por añadir iOS. La etapa 03 está implementada pero sigue pendiente de corrección y aceptación: usa también `stuff/prompts/correccion_comprobacion/03_correccion_y_comprobacion.md`. Solo amplía contratos/propietarios existentes si una integración demuestra una carencia concreta, con regresión proporcional.
- Conserva `apps/web/`, `apps/services/`, `data/`, `documentation/` y `stuff/`. Ubica el nuevo proyecto móvil compartido en `apps/mobile/`, con destinos Android e iOS, y escritorio en `apps/desktop/`. Inspecciona ubicaciones existentes antes de crear o mover archivos; no migres una aplicación previa sin necesidad.
- La web conserva backend propio y operaciones de negocio con las API detenidas, si sus dependencias necesarias siguen disponibles. Los módulos compartidos deben estar versionados para evitar divergencia y doble escritura.
- Android e iOS consumen exclusivamente contratos JSON de microservicios mediante HTTPS. Escritorio consume exclusivamente contratos XML mediante HTTPS y valida entradas y respuestas con XSD y tipos por operación. Ninguno usa sesiones internas web ni conecta a PostgreSQL, MongoDB o Redis.
- Los archivos se autorizan mediante las API. La transferencia binaria puede usar una URL GCS firmada emitida por ellas; no equivale a consumir un contrato JSON/XML diferente ni permite credenciales de bucket en clientes. No inventes una prohibición de transferencia firmada incompatible con el flujo existente.
- Conserva PostgreSQL compartido, credenciales por servicio, vistas y permisos. Cada dato tiene un propietario autoritativo. La base compartida no autoriza a un servicio a saltarse las reglas del propietario vecino.
- El profesor recomendó una arquitectura objetivo de **24 microservicios**. Usa su catálogo como referencia y cubre las 24 responsabilidades descritas en el prompt 01, con una correspondencia explícita desde los once servicios actuales. No es obligatorio terminar con exactamente 24 microservicios independientes: justifica conservar, ampliar, agrupar o separar cada responsabilidad para evitar duplicar funciones, reglas o propietarios de datos. Mantén visibles las 24 responsabilidades aunque compartan servicio. Un microservicio declarado independiente requiere imagen, proceso/contenedor, contrato y actualización independientes; los módulos agrupados y las réplicas se cuentan por separado.
- Conserva los puertos existentes documentados. Los 5201–5224 del TXT son propuestas, no una obligación de renumerar el sistema.
- Evita infraestructura opcional sin necesidad comprobada. HL7/FHIR solo se incorpora con caso de intercambio, versión y contraparte definidos; JSON/XML/XSD completos sí son obligatorios.
- Rastreo: implementa **WebSockets seguros WSS** con mapa interactivo actual de **Nuevo León**, fuente GPS desacoplada y simulador identificado hasta comprobar la aplicación móvil. Android e iOS intercambian mensajes JSON y escritorio XML/XSD también en WSS; las capas cartográficas no autorizan a eludir esa separación. No declares probado el GPS físico por ejecutar un simulador.

## Límite clínico y normativo

Implementa registro, verificación de información, explicaciones, autorizaciones humanas y trazabilidad. Ningún algoritmo declara a un donante apto, autoriza una transfusión, libera por sí mismo una unidad ni adjudica un órgano.

Antes de activar reglas clínicas, consulta fuentes primarias oficiales vigentes, documenta jurisdicción, versión, alcance y revisión competente. La existencia de una norma o una búsqueda web no equivale a validación profesional. No inventes umbrales de temperatura, vigencia de pruebas, tiempos de conservación, loci HLA exigibles, prioridades oficiales ni retención de expedientes.

Cuando falte aprobación externa, completa el mecanismo técnico con perfiles sintéticos identificados y deja deshabilitada su aplicación clínica. Distingue registro, completitud, preselección académica, evaluación con reglas aprobadas y dictamen profesional. Una coincidencia ABO, un archivo adjunto o un resultado incompleto nunca se presentan como aprobación clínica. Registra la dependencia externa exacta y continúa las tareas técnicas independientes.

## Seguridad y consistencia comunes

- JWT de acceso breve; renovación rotativa; sesión, revocación y permisos comprobados en Redis en cada petición protegida. Redis inaccesible implica rechazo seguro.
- Autorización de servidor por rol, acción, institución, región y relación con el recurso. Ocultar botones no autoriza ni protege una operación.
- Datos mínimos en respuestas, búsquedas, paneles, exportaciones, push, registros y errores. Audita accesos sensibles y rechazos sin filtrar el contenido del expediente ajeno.
- SQL parametrizado, validación JSON/XML/XSD, XXE deshabilitado, CSRF web, límites de consumo y secretos fuera del repositorio.
- Comandos críticos requieren versión, confirmación humana, motivo y autorización; añade reautenticación donde corresponda. No confíes en fecha, rol o dictamen enviado por el cliente.
- Reserva sin duplicación ni sobrecobertura mediante transacciones, restricciones y bloqueos. Conserva outbox/inbox, correlación y operaciones recuperables. Un timeout posterior al envío deja resultado incierto; consulta estado antes de repetir con la misma clave.
- Las colas offline solo contienen operaciones permitidas. No confirman asignaciones, liberaciones, reservas ni cierres verificados de custodia. Cada comando conserva identidad de usuario/institución, versión e idempotencia y se reautoriza al sincronizar.
- Auditoría y custodia permanecen append-only. Una corrección agrega un evento y conserva el anterior; no modifica el pasado.

## Ejecución y dependencias externas

Trabaja por incrementos verticales ejecutables. No termines con interfaces simuladas, endpoints vacíos, TODO críticos, respuestas fijas ni pruebas que solo comprueben un mock. Los dobles de prueba se admiten para casos unitarios, identificados y complementados con integración real.

Desarrolla y prueba sobre datos ficticios y entornos aislados. No borres volúmenes, reinicialices datos, sustituyas respaldos sobre la instalación ni detengas servicios ajenos para demostrar fallos. Ensaya migraciones sobre copia restaurada y compara datos, permisos e historial.

Consulta documentación oficial actual antes de fijar dependencias, versiones de SDK, compatibilidad o configuración de seguridad. Registra versiones reproducibles y las plataformas realmente verificadas.

Utiliza la autorización vigente de la conversación. Prepara cambios y validación antes de pedir una aprobación que realmente falte. Una petición de implementar localmente no autoriza por sí sola nuevos gastos, cambios productivos, publicación en tiendas, envío de mensajes a personas ni una aprobación clínica. Si una credencial o acceso externo falta, deja el adaptador completo, configuración segura, diagnóstico y prueba local reproducible; registra qué verificación real queda pendiente sin simular éxito.

## Cierre de cada etapa

1. Ejecuta pruebas proporcionales, incluyendo regresión de lo afectado. Corrige fallos hasta cumplir los criterios técnicos o aislar una dependencia externa real.
2. Conserva evidencias en `documentation/evidencias/entrega-final/<etapa>/`, con fecha, versión/commit o manifiesto de fuentes, entorno, comandos, esperado, obtenido, errores y límites. No publiques tokens ni expedientes reales.
3. Actualiza documentación vigente, matriz de trazabilidad y `PROJECT_STATUS.md` con estado, decisiones, criterios, pruebas, pendientes y riesgos. No alteres resultados históricos para hacerlos coincidir con el código nuevo.
4. Entrega comandos de instalación/ejecución, artefactos verificables y resumen breve de lo implementado. Expón por separado aprobación clínica pendiente, acceso externo pendiente, plataforma no probada y defecto técnico.
5. No marques completa la entrega final si queda un criterio requerido sin implementar o verificar. Una limitación clínica identificada es una condición de operación; no convierte una simulación en un motor clínico validado.
