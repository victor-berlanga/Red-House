# Despliegue GCP verificado — 20 de octubre de 2026

Actualización del 21 de octubre: [auditoría, hallazgos y formularios publicados](auditoria-formularios/RESULTADOS.md), esquema 7, respaldo/restauración comprobados, 27 contenedores saludables y verificación HTTPS. Las cifras siguientes conservan el alcance de la instalación inicial.

VM `red-house` creada con `gcloud` en `sistemas-integracion-01`, zona `me-central1-a`. Se conservaron CPU, RAM, disco, sistema operativo, red y opciones Shielded de `maquina01`: CentOS Stream 10, `e2-standard-2`, 2 vCPU, 8 GB y disco estándar de 20 GB. La instancia original permaneció detenida. [Configuraciones consultadas](instance.json).

La primera instalación utilizó túnel SSH y copia de los datos del Docker de demostración; el acceso público se habilitó posteriormente por solicitud del usuario. El código se transfirió desde el directorio de trabajo, incluidos los cambios todavía sin commit, excluyendo Git, entornos locales y credenciales personales. Docker construyó las imágenes para x86_64 en la VM.

## Acceso público verificado

El acceso vigente es **https://34.18.186.116**, con redirección desde HTTP y sin túneles. Se reservó la IP existente y se agregó una regla TCP 80/443 limitada a la etiqueta `red-house-web`; [estado GCP](public/control-plane.json). El monolito y las API usan Nginx, mientras PostgreSQL, MongoDB y Redis conservan redes privadas. El Compose local no publica esta entrada; el override se aplica únicamente en la VM.

| Criterio | Resultado comprobado | Evidencia |
| --- | --- | --- |
| Acceder directamente por IP | HTTP 308 hacia HTTPS; TLS 1.3 con cadena y SAN de la IP válidos. Readiness, Swagger, OpenAPI y XSD de once servicios en 200. | [Red pública](public/network.json) |
| Mantener el despliegue íntegro | 27 contenedores saludables; systemd activo/habilitado. Solo 80/443 públicos; puertos de diagnóstico en loopback. | [Estado remoto](public/runtime.json) |
| Operar por HTTPS | Sangre completa por API y por web; persistencia confirmada, custodia y consultas JSON/XML de los once propietarios. Las API permanecieron encendidas durante esta prueba web. | [Cuatro controles aprobados](public/http/docker-results.json), [HTTP redactado](public/http/docker-http.json) |
| Gestionar archivos privados | Carga web y descarga firmada con hash idéntico; acceso anónimo y usuario ajeno rechazados. Se conserva evidencia ficticia. | [Control GCS](public/http/docker-results.json) |
| Usar el navegador desde otro equipo | 20 páginas de siete perfiles, gráficas contrastadas con datos, ancho 390 sin desbordamiento y cero errores JavaScript. Ninguna petición de la aplicación apunta a localhost. | [Chrome](public/browser/results.json) |
| Conservar autenticación | Cookies Secure/HttpOnly/SameSite=Lax; renovación 200, logout 302 y cookie cerrada rechazada. Swagger ejecutó Inventario con JWT y respuesta 200. | [Sesiones y Swagger](public/browser/results.json) |
| Mantener aislamiento | Sin JWT, API 401; rutas internas 404. Ocho puertos de almacenes y diagnóstico no accesibles desde el cliente externo. | [Red pública](public/network.json) |
| Renovar HTTPS automáticamente | Certbot 5.8.0 y temporizador activo/habilitado cada seis horas. `renew --dry-run --run-deploy-hooks` completó renovación simulada, validación y recarga de Nginx. | [Renovación](public/renewal.json) |
| Dejar el equipo local libre de servicios del proyecto | Contenedores detenidos, Docker Desktop cerrado, PostgreSQL Homebrew parado y ningún portal, worker, API o túnel local de Red House. | [Cierre local](public/local-stop.json) |

Cambios: configuración pública Nginx/Compose, prefijos Swagger/OpenAPI, esquema HTTPS explícito en Waitress, cookies seguras y scripts de certificado. No se cambiaron reglas de negocio ni se añadieron bases. Certbot administra certificados en la VM; no es un componente de negocio.

Durante la comprobación se corrigieron dos supuestos del script de navegador: las gráficas vacías están ocultas y no tienen instancia Highcharts; Swagger necesita terminar de cargar su esquema antes de aplicar la autorización automática. El último caso se repitió aisladamente después de las 20 páginas aprobadas. Python de macOS carecía de almacén CA propio para la inspección TLS; el verificador usa explícitamente el mismo bundle `certifi` de Requests, conservando verificación de cadena y nombre. No se deshabilitó TLS ni se cambiaron límites de la aplicación para aprobar.

## Primera puesta en marcha: túnel SSH

La tabla siguiente conserva evidencia anterior a la publicación HTTPS; sus puertos y forma de acceso describen esa etapa.

## Criterios y resultados

| Criterio | Resultado comprobado | Evidencia |
| --- | --- | --- |
| Conservar los datos de demostración | 15 263 filas de 72 tablas SQL y 7 721 documentos MongoDB idénticos por conteo/hash antes de iniciar aplicaciones; usuarios y roles documentales comparados. Redis restaurado mediante RDB y persistencia AOF habilitada. | [Respaldo de origen](source-backup.json), [restauración y estado](runtime.json) |
| Mantener permisos | El rol web conserva acceso a su tabla técnica y carece de acceso al esquema de dominio. | [Estado](runtime.json) |
| Ejecutar todo el despliegue | 27 contenedores saludables; servicio `redhouse` activo y habilitado. Solo se publican puertos en `127.0.0.1`. | [Inspección](runtime.json) |
| Ejecutar operaciones reales | Flujo completo de sangre, recepción, custodia y consultas JSON/XML de los once servicios. | [Resultado HTTP](http/docker-results.json), [intercambios redactados](http/docker-http.json) |
| GCS con identidad de la VM | Carga y descarga firmadas correctas, hash idéntico y acceso anónimo 403. Objeto de prueba directa eliminado. | [Prueba de identidad adjunta](gcs-vm.json) |
| Conservar funcionamiento local de GCS | Misma prueba aprobada con ADC impersonada local; objeto temporal eliminado. | [Prueba local](gcs-local.json) |
| Gestionar archivos desde la web remota | Archivo ficticio verificado y descargado con hash idéntico; usuario ajeno recibe 403. Se conserva un traslado abierto con evidencia para demostración. | [Resultado HTTP](http/docker-results.json) |
| Mantener sesiones Redis/PostgreSQL | Login 302, renovación 200, logout 302 y cookie cerrada redirigida al login; tokens cifrados y sin volumen local de sesiones. | [Sesiones](sessions.json) |
| Acceder desde el equipo por SSH | Página de acceso 200, login 302, panel y CSS 200, logout 302; se utilizaron las cuentas copiadas. | [Túnel real](tunnel.json) |

Se verificaron los hashes de `compose.yaml`, `deployment/start.py`, el adaptador GCS y el módulo de sesiones contra el código local. Los archivos correspondientes de la imagen web coinciden con sus fuentes. El análisis Ruff, formato Python y sintaxis de los scripts shell pasaron; durante la adaptación también pasaron las 14 pruebas del módulo unitario de revisión. Estas comprobaciones no se suman a las suites históricas como casos únicos.

## Decisiones y límites

- Cuenta adjunta `red-house-archivos`, con acceso al bucket ya autorizado y permiso de firma sobre sí misma. No se copiaron ADC personales ni se descargaron claves de cuenta de servicio. El adaptador ahora admite firma IAM con credenciales de Compute Engine y conserva la firma local impersonada.
- La imagen de referencia tiene una versión posterior recomendada por GCP; se mantuvo la imagen exacta de `maquina01`. Docker se instaló desde su repositorio oficial para CentOS.
- La clave SSH personal estaba cifrada y no podía usarse sin entrada interactiva. El despliegue usó una clave temporal de OS Login; la guía de acceso utiliza la clave personal habitual.
- La VM es un despliegue académico con acceso público HTTPS. No se certifican alta disponibilidad entre hosts, carga sostenida ni uso clínico. El arranque automático está configurado; no se ejecutó un reinicio completo de la VM en esta verificación.
- Las cifras de restauración corresponden al instante anterior a las pruebas. Los flujos posteriores agregaron registros ficticios y auditoría. La copia local y la remota no se sincronizan.
- Los objetos GCS existentes mantienen sus referencias en el mismo bucket. Los respaldos SQL/MongoDB/Redis no contienen los objetos de ese bucket.

La VM queda encendida. El Docker local volvió a quedar detenido con sus datos conservados. [Acceso, arranque, parada y scripts de reproducción](../../../deployment/gcp/README.md).

## Baja de donantes y navegación (21 de octubre)

La revisión posterior incorporó la baja de donantes y retiró el aviso al salir de formularios. Se comprobaron 27 pruebas aisladas, ambos tipos de baja desde el portal público y la conservación de los registros anteriores. [Resultados de bajas y navegación](bajas-donantes/RESULTADOS.md).

## Ampliación de la demostración (21 de octubre)

Se agregaron datos ficticios relacionados mediante las API de la VM: 68 donantes, 60 campañas, 118 citas y 30 traslados nuevos, además de inventario, solicitudes y catálogos. Se alcanzó el mínimo de 30 en las tablas operativas de negocio; las tablas heredadas y los catálogos cerrados conservan sus cantidades justificadas. [Conteos actuales, pruebas y capturas](datos-demo/RESULTADOS.md). Las cifras de restauración de este informe siguen siendo evidencia del despliegue original.
