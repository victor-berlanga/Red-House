# Completar seguridad infraestructura y continuidad operativa

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Implementa y verifica los controles de seguridad e infraestructura de toda la plataforma, incluyendo los componentes nuevos. Conserva lo que ya funciona en Docker/GCE/HTTPS; no reconstruyas la instalación desde cero ni borres datos para simplificar un despliegue.

Los prompts 01 a 05 son responsables de sus funciones y controles desde el desarrollo. Esta etapa revisa su cobertura conjunta y corrige brechas, no pospone autenticación o permisos hasta el final.

## Entrada y pendientes heredados

Lee la [continuidad obligatoria de 01–04 definida en 07](07_integracion_pruebas_y_rendimiento.md#continuidad-obligatoria-de-las-etapas-01-a-04), la [matriz del portal](../../../documentation/entrega-final/portal/Matriz.md), su [plan de aceptación integrada I06-01…09](../../../documentation/entrega-final/portal/Aceptacion_integrada_06.md), la [matriz móvil](../../../documentation/entrega-final/mobile/Matriz.md) y sus [dependencias externas](../../../documentation/entrega-final/mobile/Dependencias_externas.md). Abre o actualiza `documentation/entrega-final/continuidad/Matriz.md` al ejecutar, sin exigir que 07 haya terminado. Registra qué criterios CONT resuelve 06 y qué recorrido de cliente corresponde verificar después en 07.

Comprueba el entorno vigente antes de seguir instrucciones históricas: esquema, imágenes, gateway, permisos de ensayo, ClamAV y accesos a proveedores. La revisión del 11/11/2026 encontró referencias antiguas al esquema 17 y a dependencias ausentes; el estado posterior ya documenta esquema 18, gateway publicado y ClamAV preparado. No fijes esas versiones para siempre, no reviertas el entorno ni marques una dependencia como resuelta sin comprobar su alcance actual. Las autorizaciones de despliegue anteriores no autorizan nuevas pruebas destructivas sobre producción.

Resuelve I06-01…09 con evidencia aplicable: ciclo de archivos del modo operativo privado en servidor; verificación GCS separada como requisito académico aunque GCS sea opcional para el producto; documentos HLA y evidencia de traslado; versiones, conservación y bloqueos; EICAR aislado; fallos/recuperación; reportes CSV/PDF/XLSX de más de 1000 filas con filtros, conteos y ámbito coherentes; WSS con una y todas las réplicas detenidas, autonomía web, recuperación/revocación y manifiestos. Reutiliza los casos que ya acrediten el código y entorno actuales; repite los afectados por cambios o brechas demostradas. Conserva identificadores WEB/TRACK/CONT y evita contar el mismo ensayo varias veces.

## SEC-01 Identidad sesiones y operaciones críticas

Verifica hash de contraseña y parámetros vigentes con fuentes oficiales, JWT con algoritmo/emisor/audiencia/claims/expiración definidos, rotación de renovación, detección de reutilización, revocación, permisos versionados Redis y límites compartidos entre réplicas.

Completa MFA para personal crítico, enrolamiento seguro, verificación del factor, recuperación y revocación auditadas. Si usas TOTP, cifra semillas, limita intentos/repetición y protege códigos de recuperación con hash y un solo uso; no uses un segundo campo estático como MFA. Documenta alternativa cuando no se disponga de un factor configurado, sin permitir autoexención.

La reautenticación devuelve una autorización breve y de un uso vinculada a usuario, sesión, acción, recurso y datos/versión relevantes. Caducidad, logout o cambio de permisos invalidan su uso conforme a política. Todas las rutas alternativas de liberación, dictamen y asignación deben aplicar el mismo control.

Verifica recuperación de contraseña, dispositivo revocado, cierre con Redis/PostgreSQL inaccesible y comportamiento al restaurar sesiones antiguas. No reactivas cookies o tokens cerrados por restaurar una copia desactualizada. Las aplicaciones cliente deben limpiar sus propias credenciales sin poder revocar a otro usuario.

## SEC-02 Autorización y privacidad

Construye una matriz rol/acción/recurso/institución/región/relación por operación. Prueba de forma sistemática listados, detalles, edición, comandos, selectores, búsquedas, conteos, documentos, trabajos, exportaciones, etiquetas, mapas, alertas y sincronización.

Incluye cambios de UUID en URL, cuerpo y parámetros, recursos relacionados de otra institución y usuarios de otra región. Comprueba transportista no asignado, donante ajeno, coordinador sin facultades médicas, administrador sin acceso clínico y auditor sin modificación. Los ID aleatorios no sustituyen autorización.

Audita accesos sensibles, exportaciones y rechazos sin revelar existencia o contenido del recurso ajeno. Minimiza información personal en indicadores regionales, errores, telemetría, push, logs y archivos exportados. Define finalidad/retención para cada categoría y separación de datos de sangre/órganos.

Revisa inyección SQL, XXE, XML grande, JSON ambiguo, XSS, CSRF, cargas, URLs externas/SSRF cuando existan integraciones, inyección de fórmulas en CSV/XLSX y rutas/nombres de archivos. Corrige riesgos demostrados y evita incorporar controles sin caso aplicable.

## SEC-03 Documentos privados y antimalware

Mantén almacenamiento privado del servidor como ruta operativa principal. GCS es opcional para los flujos de producto, pero tiene verificación académica propia: prueba aislada y registra APROBADO/PARCIAL/FALLIDO/NO VERIFICADO por separado. No bloquees el producto cuando GCS no está configurado si el almacenamiento local autorizado funciona; tampoco atribuyas a GCS la evidencia del servidor privado.

Para el flujo de archivos, conserva clasificación y estados de preparación, carga, validación, análisis pendiente, limpio, rechazado, error, bloqueo y eliminación según política. Un archivo sin análisis válido no se ofrece para descarga operativa ni se considera evidencia verificada.

Integra un motor antimalware mantenido, por ejemplo ClamAV si satisface el entorno, con firmas actualizadas, worker aislado, timeout y límites de recursos. Registra motor/versión/firmas, generación/hash analizados, fecha y resultado. Una caída o análisis incompleto conserva cuarentena y reintento; nunca produce limpio por defecto.

Mantén validación estructural/MIME/tamaño/hash, límites de imágenes/PDF y detección de contenido activo; un antivirus no sustituye esos controles. Comprueba el ciclo del almacenamiento privado. Si existe integración GCS, prueba creación exclusiva, generación y descarga del objeto exacto como criterio separado. Evita procesar URLs arbitrarias enviadas por cliente y no entregues credenciales del bucket.

Define políticas versionadas de categoría, privacidad, retención, bloqueo legal/documental, eliminación lógica y física, recuperación autorizada, registro de borrado y verificación de integridad. Para pruebas usa periodos sintéticos identificados; los plazos clínicos reales requieren fuentes y aprobación competente. No borres registros/objetos existentes al activar una política nueva.

Demuestra archivo limpio, contenido inválido, archivo de prueba antimalware estándar en entorno aislado, motor caído, firma antigua, timeout, objeto sustituido/ausente, URL expirada y acceso de otra institución. No uses malware real ni mezcles archivos de prueba con expedientes reales.

Ante caída del almacenamiento usado, registra incidencia y evidencia pendiente sin afirmar carga/verificación. Prueba por separado el comportamiento del servidor privado y, si se configuró para ensayo, GCS. Permite solo transiciones autorizadas sin documento; bloquea las que lo exigen. Prueba recuperación sin duplicar objetos ni cerrar falsamente custodia.

Completa CONT-08 con un objeto real, almacenamiento privado y motor real en entorno aislado. Comprueba preparación, carga, análisis, hash, consulta/descarga y vínculo documental HLA o de traslado. Ejecuta además una prueba GCS independiente solo en el prefijo aislado autorizado disponible; si no existe acceso, registra dependencia académica externa pendiente sin bloquear flujos locales. El ensayo CLEAN/EICAR solo acredita el motor. Prueba revocación entre creación y descarga de reportes/documentos: impedir nuevas autorizaciones o firmas según contrato y documentar vigencia residual de URLs emitidas. Entrega a 07 condiciones reproducibles para clientes aplicables.

## Entrega push pendiente de 04

Asume CONT-07 con el propietario Alertas. Inspecciona su adaptador HTTP y adaptadores nativos. La entrega física FCM/APNs queda pendiente externa por decisión: no prepares cuentas, proyectos, certificados, claves ni dispositivos de proveedor. Completa y prueba lo independiente: bandeja interna, contratos y adaptadores con receptor identificado de laboratorio. Separa código, configuración, permiso y recepción; nunca llames push recibido a un adaptador o outbox verificado.

Preserva `event_id` como referencia de entrega/idempotencia y `alert_id` como referencia opaca para abrir la alerta. Verifica bandeja interna, destinatario autorizado, consentimiento, permisos, rotación, reintentos, deduplicación, expiración/revocación y payload mínimo sin datos clínicos. Mantén límite de destinos por cuenta/canal soportado. La recepción física FCM/APNs es NO VERIFICADA y queda pendiente por decisión; no prepares proyectos, cuentas, certificados ni claves de proveedor. Un 2xx, token registrado o outbox vacío no demuestra recepción.

## INF-01 Contenedores y despliegue

Actualiza imágenes por propietario, monolito, Monitoreo y workers necesarios. Cada servicio debe poder construirse/actualizarse individualmente. Integra nuevos servicios al gateway, DNS, salud, logs y configuración. Mantén al menos dos instancias de las API necesarias para la continuidad ya comprometida, incluida Identidad.

Revisa usuarios sin privilegios, sistema de archivos, redes privadas, puertos mínimos, volúmenes, permisos, límites de recursos y dependencias reproducibles. PostgreSQL, MongoDB y Redis no se publican al exterior. Secretos y claves quedan fuera de Git, imágenes, instalables, capturas y salidas.

Conserva GCE y HTTPS público, renovación del certificado, firewall, administración restringida y arranque supervisado. Verifica configuración actual mediante lectura antes de actuar. No cambies dominio/IP/proyecto ni habilites servicios facturables sin autorización vigente.

Prepara migración y publicación revisables: manifiesto de fuentes, respaldo, ensayo en copia restaurada, compatibilidad temporal, actualización por réplica, smoke tests y rollback. No ejecutes migraciones destructivas al arrancar. Un rollback de aplicación no revierte de forma segura nuevas escrituras: define conciliación cuando haga falta.

## Rastreo WSS y privacidad de ubicación

Aplica la [especificación de rastreo GPS por WebSockets](09_rastreo_gps_websockets.md), en particular TRACK-03, TRACK-07 y TRACK-09. Configura upgrade WSS/TLS en gateway y réplicas, drenaje, heartbeat, límites, reconexión y recuperación desde persistencia; no supongas migración automática de sockets ni durabilidad de Redis Pub/Sub. Prueba autorización antes de publicar/suscribirse y antes de entregar datos, incluyendo expiración, revocación, reasignación, logout y Redis inaccesible. Revisa orígenes del navegador sin tratarlos como credencial del GPS.

Monitoriza fuente GPS, ingreso, persistencia, canal y proveedor cartográfico por separado. Limita rastreo a tarea/periodo autorizados, retención e identidades mínimas; no registres tokens o recorridos completos en logs generales ni los entregues a un proveedor de mapas sin necesidad. Ensaya pérdida de una réplica, del servicio y de PostgreSQL/Redis/MongoDB, manteniendo estados honestos de dato antiguo y rechazo seguro. La ausencia de hardware no exime de probar el canal real con simulador.

## INF-02 Observabilidad y dependencias

Comprueba `/health/live`, `/health/ready`, `/health/database`, `/health/redis`, `/health/mongodb` y `/health/storage` donde apliquen. Distingue no aplicable de disponible; no informes GCS sano solo porque existe una variable. Si GCS no es la ruta operativa seleccionada, márcalo opcional/no aplicable al health operacional y conserva su verificación académica independiente.

Incluye salud del worker de cada réplica, antigüedad/tamaño del outbox, reintentos, conflictos, trabajo antimalware y entregas push/email. Si existe una cola nueva, monitoréala; no añadas un broker solo para cumplir una palabra de la retroalimentación.

Centraliza o prepara centralización de logs/metricas con servicio, versión, correlación, duración, código y dependencia sin cuerpos clínicos ni secretos. Monitoreo debe detectar caída, respuesta inválida, timeout, degradación y recuperación, y alertar a los responsables autorizados sin detener el negocio si falla el monitor.

## INF-03 Continuidad RTO y RPO

Documenta una matriz por operación y componente para: una réplica caída, todas las réplicas de un propietario, gateway caído, PostgreSQL caído, Redis caído, MongoDB caído, almacenamiento privado caído, GCS caído como destino opcional, worker detenido, red interrumpida y host perdido.

Define objetivos numéricos RTO y RPO por tipo de dato/servicio antes de los ensayos, con justificación académica y responsables. Diferencia objetivo propuesto, acuerdo operativo real y tiempo/pérdida medidos. No inventes un SLA clínico ni uses duración con equipo suspendido como RTO.

Conserva respaldo coordinado de PostgreSQL/roles, MongoDB/usuarios, Redis/ACL, configuración, claves y versiones. Define frecuencia, cifrado, acceso, retención, copia fuera del host y restauración. Incluye objetos GCS solo si se configuró ese destino: un respaldo SQL no contiene binarios externos. Mantén su verificación académica separada.

Restaura en infraestructura aislada sin sobrescribir el sistema activo. Mide desde el inicio del incidente hasta la recuperación funcional, no solo el arranque del proceso. Compara conteos/hashes/relaciones, eventos, permisos, TTL, documentos, objetos y operaciones pendientes. Calcula RPO con últimas transacciones conocidas; diferencia caída con volúmenes intactos de pérdida de disco/host.

Demuestra continuidad de clientes ante una réplica caída y de la web modular con API detenidas. Una caída total de PostgreSQL o Redis no se oculta omitiendo persistencia o autorización. Recupera outbox/inbox, análisis y notificaciones sin duplicar efectos.

La topología de un único host mantiene puntos únicos de fallo. Entrega diseño futuro justificado para host, gateway y almacenes, con redes, replicación, failover, consistencia y coste estimado. No es obligatorio contratar multizona ni GKE para declarar comprendida la limitación; no declares HA de infraestructura sin implementarla y probarla.

## INF-04 Integración continua y distribución

Configura pipeline para análisis estático, pruebas relevantes, migración/restauración, contratos JSON/XML/XSD, contenedores, Android y escritorio según runners disponibles. Revisa primero fallos conocidos, incluido formato de Auditoría, sin modificar reglas de negocio para silenciarlos.

Ejecuta CI remoto si hay acceso autorizado y conserva resultado real; una definición YAML sin ejecución no acredita pipeline aprobado. Protege secretos y artefactos, separa compilación de despliegue productivo y firma/publicación de instalables. Registra plataformas que realmente ejecutaron pruebas.

## Aceptación y entregables

Entrega matriz de seguridad negativa, políticas de archivos, ensayo antimalware, matriz de fallos, objetivos/mediciones RTO-RPO, respaldos restaurados, diagramas de red/despliegue, runbooks y pipeline con evidencia. Incluye el resultado de I06-01…09, CONT aplicables y el estado separado de implementación/configuración/recepción push. Demuestra que un usuario no autorizado recibe rechazo en acciones críticas y que una caída no confirma una operación incompleta.

Las pruebas destructivas y de saturación se ejecutan solo en entornos aislados autorizados. Publica cambios en la VM únicamente cuando exista autorización vigente y después de preparar un resultado concreto revisable. Actualiza documentación y `PROJECT_STATUS.md`, distinguiendo lo implementado, probado, diseñado y pendiente externo.

## Alcance móvil actualizado — 6 de noviembre de 2026

Incluye Android e iOS en CI con runners apropiados (macOS/Xcode para iOS), firma protegida y artefactos diferenciados. Verifica permisos de ubicación, almacenamiento seguro y push por plataforma. Ensaya bloqueo, suspensión, cierre forzado, ahorro de batería y revocación: ningún socket se presume permanente. La aplicación móvil es fuente principal; no exijas GPS externo opcional como condición de cierre.

Para Android usa emulador, sin exigir teléfono. Para iOS rige prueba en iPhone físico autorizada y no descargar runtime Simulator. Distingue compilación CI, firma, instalación y ejecución; declara lo no ejecutado. macOS y Windows 11 son plataformas de trabajo; Linux es objetivo adicional por verificar. No prepares cuentas push externas.
