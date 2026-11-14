# Esquema 020, antivirus y recibo de alta en GCP

Publicado el conjunto de trece archivos fijados en [el manifiesto](manifest.json), desde `9648bf4` hasta el corte `1163e2c`, en **sistemas-integracion-01 / red-house / me-central1-a**, instancia `2861822465669755197`. Se actualizaron trece imágenes de aplicación, sus veinticinco contenedores y la configuración de ClamAV; la imagen del antivirus, sus 2 GiB y el volumen de firmas permanecieron. Gateway, PostgreSQL, MongoDB y Redis conservaron sus contenedores. No se crearon recursos de nube. No representa el despliegue de aplicaciones cliente ni de todos los archivos del commit.

El estado final comprobó treinta contenedores sanos, esquema 20 y las mismas 39 referencias privadas por huella. El proveedor sigue siendo local. El proxy original se restituyó y las escrituras están abiertas. [Comprobación posterior](post-public-check.json).

## Respaldo, ensayo e incidentes previos

El respaldo PostgreSQL tiene **40.824.752 bytes**, SHA-256 `daade6d74558aec4f96037eb4d15df9282c5d338457d2cf20c786200504cd6cc`. Se verificó su catálogo y se restauró en una base temporal privada, sin acceso de los roles de aplicación. No fue una restauración coordinada de toda la plataforma.

La inspección inicial encontró cuatro contenedores MongoDB detenidos de restauraciones anteriores con etiquetas compartidas. El selector se corrigió para reconocer los contenedores canónicos activos y conservar esos históricos. El primer intento de ensayo se detuvo por margen de disco antes de crear la base. Se retiraron únicamente 174.548.800 bytes de duplicados recién creados por esta preparación, comparados por SHA con sus originales; los respaldos originales permanecen. [Referencias y alcance](historical-backup-references.json).

El intento posterior restauró la base privada, pero el comando de migración omitía `docker run -i` y no recibió el JSON esperado. Se reprodujo ese fallo sin cambiar esquema y después se corrigió. La [repetición dirigida](rehearsal.json) pasó: migración 19→20, 39 referencias, cinco análisis y tres exportaciones conservados; permisos de tablas/columnas iguales y nuevos metadatos históricos en NULL. Sus **13,384 s** corresponden a esa fase dirigida, no a todo el proceso de restauración. Solo después del éxito se eliminó la base temporal. Los intentos se distinguen; no se declara un ensayo inicial sin fallos.

## Publicación y comprobaciones

Las mutaciones HTTP se pausaron y se esperaron al menos 125 s antes de publicar. Workers y conexiones WSS no quedaron globalmente detenidos. La migración usó bloqueo de las tablas afectadas, comparación de estado y registro durable de intención; el procedimiento permite reconocer una confirmación SQL perdida sin repetir la migración a ciegas. La recuperación de interrupciones del procedimiento se simuló localmente; no se provocó una caída real durante la migración productiva.

La migración publicada conservó datos y permisos. [Resultado SQL](migration.json). ClamAV cargó las firmas **28182**, fechadas `2026-11-13T06:24:28Z`, tras recrearse. Antes tenía cargadas 28181 aunque el disco ya contenía 28182; el registro es compatible con la [incidencia de arranque descrita por ClamAV](https://github.com/Cisco-Talos/clamav-docker/issues/83), sin probar internamente esa causa. Se configuraron doce comprobaciones de actualización por día, UTC y recarga sin dos motores simultáneos, siguiendo las [opciones oficiales](https://docs.clamav.net/manual/Installing/Docker.html). La recarga puede bloquear temporalmente escaneos; una indisponibilidad no autoriza marcar archivos como limpios.

La comparación de VERSION con dos lecturas estables de la cabecera daily pasó; no fue necesario solicitar RELOAD. Esto no certifica criptográficamente todas las bases del motor. Ambas réplicas de Documentos analizaron bytes sintéticos limpios y EICAR con resultado CLEAN/INFECTED, firmas vigentes y máximo de 48 horas. No escribieron archivos ni filas de negocio y no reanalizaron objetos históricos. [Alineación](scanner-alignment-final.json), [análisis reales](scanner-validation.json).

El [primer control interno](internal-validation-initial.json) alcanzó 48 respuestas esperadas y falló en el login administrativo al omitir MFA en el arnés. Se utilizó el factor existente, sin deshabilitarlo ni guardar sus códigos en evidencia. La [repetición](internal-validation.json) aprobó **64 controles**: ambas réplicas, lectura, negociación JSON/XML, contrato del recibo, búsqueda de dispositivos y denegaciones. El pase no sustituye el intento fallido. Los controles del recibo no crean usuarios en GCP.

Después de abrir escrituras pasaron **55 controles públicos HTTPS**, con TLS verificado, roles, feed, formularios de lectura, recibo inexistente y rechazo de sesiones cerradas. WSS JSON/XML autenticó y respondió heartbeat; no publicó ubicación. [Resultados públicos](https-final.json). No se midió capacidad, disponibilidad continua ni carga sostenida.

## Límites y continuidad

El control periódico de firmas preparado en `5970651` no forma parte de este corte: se publicó después en un [incremento separado](../scanner-health-20261113/RESULTADOS.md). Este corte verifica la alineación en momentos concretos. Los análisis históricos conservan metadatos desconocidos, sin backfill inventado. Los 34 objetos GCS históricos pendientes no fueron reanalizados.

Los [procedimientos](procedimiento/deploy.py) dependen de respaldos/configuración privados y del estado exacto de este despliegue; no son comandos genéricos para repetir sobre cualquier VM. Los secretos no se incluyen. La clave temporal OS Login se retiró después de la publicación adicional del control de salud; las dos claves previas se conservaron y la copia privada temporal se eliminó. [Cierre de acceso](access-cleanup.json).
