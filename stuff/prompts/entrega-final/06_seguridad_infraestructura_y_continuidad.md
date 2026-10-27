# Completar seguridad infraestructura y continuidad operativa

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Implementa y verifica los controles de seguridad e infraestructura de toda la plataforma, incluyendo los componentes nuevos. Conserva lo que ya funciona en Docker/GCE/HTTPS; no reconstruyas la instalación desde cero ni borres datos para simplificar un despliegue.

Los prompts 01 a 05 son responsables de sus funciones y controles desde el desarrollo. Esta etapa revisa su cobertura conjunta y corrige brechas, no pospone autenticación o permisos hasta el final.

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

Amplía el flujo GCS existente con clasificación y estados de preparación, carga, validación, análisis pendiente, limpio, rechazado, error, bloqueo y eliminación según política. Un archivo sin análisis válido no se ofrece para descarga operativa ni se considera evidencia verificada.

Integra un motor antimalware mantenido, por ejemplo ClamAV si satisface el entorno, con firmas actualizadas, worker aislado, timeout y límites de recursos. Registra motor/versión/firmas, generación/hash analizados, fecha y resultado. Una caída o análisis incompleto conserva cuarentena y reintento; nunca produce limpio por defecto.

Mantén validación estructural/MIME/tamaño/hash, límites de imágenes/PDF y detección de contenido activo; un antivirus no sustituye esos controles. Comprueba creación exclusiva, generación GCS y descarga del objeto exacto. Evita procesar URLs arbitrarias enviadas por cliente y no entregues credenciales del bucket.

Define políticas versionadas de categoría, privacidad, retención, bloqueo legal/documental, eliminación lógica y física, recuperación autorizada, registro de borrado y verificación de integridad. Para pruebas usa periodos sintéticos identificados; los plazos clínicos reales requieren fuentes y aprobación competente. No borres registros/objetos existentes al activar una política nueva.

Demuestra archivo limpio, contenido inválido, archivo de prueba antimalware estándar en entorno aislado, motor caído, firma antigua, timeout, objeto sustituido/ausente, URL expirada y acceso de otra institución. No uses malware real ni mezcles archivos de prueba con expedientes reales.

Ante GCS caído durante un traslado, registra la incidencia y evidencia pendiente sin afirmar carga/verificación. Permite solo las transiciones que el protocolo autoriza sin ese documento; bloquea las que lo exigen. Prueba recuperación sin duplicar objetos ni cerrar falsamente custodia.

## INF-01 Contenedores y despliegue

Actualiza imágenes por propietario, monolito, Monitoreo y workers necesarios. Cada servicio debe poder construirse/actualizarse individualmente. Integra nuevos servicios al gateway, DNS, salud, logs y configuración. Mantén al menos dos instancias de las API necesarias para la continuidad ya comprometida, incluida Identidad.

Revisa usuarios sin privilegios, sistema de archivos, redes privadas, puertos mínimos, volúmenes, permisos, límites de recursos y dependencias reproducibles. PostgreSQL, MongoDB y Redis no se publican al exterior. Secretos y claves quedan fuera de Git, imágenes, instalables, capturas y salidas.

Conserva GCE y HTTPS público, renovación del certificado, firewall, administración restringida y arranque supervisado. Verifica configuración actual mediante lectura antes de actuar. No cambies dominio/IP/proyecto ni habilites servicios facturables sin autorización vigente.

Prepara migración y publicación revisables: manifiesto de fuentes, respaldo, ensayo en copia restaurada, compatibilidad temporal, actualización por réplica, smoke tests y rollback. No ejecutes migraciones destructivas al arrancar. Un rollback de aplicación no revierte de forma segura nuevas escrituras: define conciliación cuando haga falta.

## Rastreo WSS y privacidad de ubicación

Aplica la [especificación de rastreo GPS por WebSockets](09_rastreo_gps_websockets.md), en particular TRACK-03, TRACK-07 y TRACK-09. Configura upgrade WSS/TLS en gateway y réplicas, drenaje, heartbeat, límites, reconexión y recuperación desde persistencia; no supongas migración automática de sockets ni durabilidad de Redis Pub/Sub. Prueba autorización antes de publicar/suscribirse y antes de entregar datos, incluyendo expiración, revocación, reasignación, logout y Redis inaccesible. Revisa orígenes del navegador sin tratarlos como credencial del GPS.

Monitoriza fuente GPS, ingreso, persistencia, canal y proveedor cartográfico por separado. Limita rastreo a tarea/periodo autorizados, retención e identidades mínimas; no registres tokens o recorridos completos en logs generales ni los entregues a un proveedor de mapas sin necesidad. Ensaya pérdida de una réplica, del servicio y de PostgreSQL/Redis/MongoDB, manteniendo estados honestos de dato antiguo y rechazo seguro. La ausencia de hardware no exime de probar el canal real con simulador.

## INF-02 Observabilidad y dependencias

Comprueba `/health/live`, `/health/ready`, `/health/database`, `/health/redis`, `/health/mongodb` y `/health/storage` donde apliquen. Distingue no aplicable de disponible; no informes GCS sano solo porque existe una variable.

Incluye salud del worker de cada réplica, antigüedad/tamaño del outbox, reintentos, conflictos, trabajo antimalware y entregas push/email. Si existe una cola nueva, monitoréala; no añadas un broker solo para cumplir una palabra de la retroalimentación.

Centraliza o prepara centralización de logs/metricas con servicio, versión, correlación, duración, código y dependencia sin cuerpos clínicos ni secretos. Monitoreo debe detectar caída, respuesta inválida, timeout, degradación y recuperación, y alertar a los responsables autorizados sin detener el negocio si falla el monitor.

## INF-03 Continuidad RTO y RPO

Documenta una matriz por operación y componente para: una réplica caída, todas las réplicas de un propietario, gateway caído, PostgreSQL caído, Redis caído, MongoDB caído, GCS caído, worker detenido, red interrumpida y host perdido.

Define objetivos numéricos RTO y RPO por tipo de dato/servicio antes de los ensayos, con justificación académica y responsables. Diferencia objetivo propuesto, acuerdo operativo real y tiempo/pérdida medidos. No inventes un SLA clínico ni uses duración con equipo suspendido como RTO.

Conserva respaldo coordinado de PostgreSQL/roles, MongoDB/usuarios, Redis/ACL, configuración, claves, versiones y referencias a objetos GCS. Define frecuencia, cifrado, acceso, retención, copia fuera del host y restauración. El respaldo SQL no incluye el binario del bucket: protege generaciones GCS y prueba su recuperación según el mecanismo realmente configurado.

Restaura en infraestructura aislada sin sobrescribir el sistema activo. Mide desde el inicio del incidente hasta la recuperación funcional, no solo el arranque del proceso. Compara conteos/hashes/relaciones, eventos, permisos, TTL, documentos, objetos y operaciones pendientes. Calcula RPO con últimas transacciones conocidas; diferencia caída con volúmenes intactos de pérdida de disco/host.

Demuestra continuidad de clientes ante una réplica caída y de la web modular con API detenidas. Una caída total de PostgreSQL o Redis no se oculta omitiendo persistencia o autorización. Recupera outbox/inbox, análisis y notificaciones sin duplicar efectos.

La topología de un único host mantiene puntos únicos de fallo. Entrega diseño futuro justificado para host, gateway y almacenes, con redes, replicación, failover, consistencia y coste estimado. No es obligatorio contratar multizona ni GKE para declarar comprendida la limitación; no declares HA de infraestructura sin implementarla y probarla.

## INF-04 Integración continua y distribución

Configura pipeline para análisis estático, pruebas relevantes, migración/restauración, contratos JSON/XML/XSD, contenedores, Android y escritorio según runners disponibles. Revisa primero fallos conocidos, incluido formato de Auditoría, sin modificar reglas de negocio para silenciarlos.

Ejecuta CI remoto si hay acceso autorizado y conserva resultado real; una definición YAML sin ejecución no acredita pipeline aprobado. Protege secretos y artefactos, separa compilación de despliegue productivo y firma/publicación de instalables. Registra plataformas que realmente ejecutaron pruebas.

## Aceptación y entregables

Entrega matriz de seguridad negativa, políticas de archivos, ensayo antimalware, matriz de fallos, objetivos/mediciones RTO-RPO, respaldos restaurados, diagramas de red/despliegue, runbooks y pipeline con evidencia. Demuestra que un usuario no autorizado recibe rechazo en acciones críticas y que una caída no confirma una operación incompleta.

Las pruebas destructivas y de saturación se ejecutan solo en entornos aislados autorizados. Publica cambios en la VM únicamente cuando exista autorización vigente y después de preparar un resultado concreto revisable. Actualiza documentación y `PROJECT_STATUS.md`, distinguiendo lo implementado, probado, diseñado y pendiente externo.
