# Control periódico de firmas publicado en Red House

El incremento `5970651` se publicó el 13/11/2026, hora de Monterrey, en **sistemas-integracion-01 / red-house / me-central1-a**, instancia `2861822465669755197`. El [manifiesto](manifest.json) limita la publicación a tres fuentes: generador de configuración, helper de salud y copia del helper en respaldos. Se recreó únicamente ClamAV, con la misma imagen, memoria y volumen de firmas. Los otros 29 contenedores conservaron identidad, imagen y estado; al terminar, los treinta estaban sanos.

El helper se monta en solo lectura y compara la versión cargada por ClamD con una cabecera `daily` estable, su antigüedad máxima de 48 horas y tolerancia de reloj. No recarga el motor, no analiza archivos históricos y no certifica criptográficamente todas las bases de firmas. Docker ejecuta el control cada 30 segundos. `/health/storage` conserva su significado de disponibilidad del almacenamiento; no se presenta como prueba de vigencia del antivirus.

## Aceptación y resultado

Preflight y configuración candidata pasaron antes de publicar: destino, fuentes anteriores, configuración de Documentos, espacio, imagen, montaje y configuración efectiva de los otros servicios. `deploy.py release` instaló los archivos, recreó solo ClamAV y aprobó la validación; no se requirió reversión. Las lecturas HTTP permanecieron abiertas. La recreación podía interrumpir temporalmente nuevos escaneos; no se midió esa ventana como disponibilidad continua.

La validación exigió dos controles periódicos satisfactorios, hash del helper dentro del contenedor, montaje de solo lectura, volumen de firmas conservado y análisis en RAM desde Documentos: **CLEAN para bytes sintéticos limpios e INFECTED para EICAR**. No creó archivos ni registros de negocio. La [captura posterior](remote-final.json), tomada a las `2026-11-14T01:37:36Z`, conservó cuatro controles exitosos distintos. Configuración de Documentos y proveedor local permanecieron iguales. No se ejecutaron migraciones ni comandos de escritura SQL.

Pasaron **cinco lecturas públicas HTTPS con certificado verificado**: login, readiness de Documentos, salud de almacenamiento y feed público JSON/XML. [Resultados y tiempos observados](public-final.json). Son comprobaciones puntuales sin autenticar, no pruebas de carga. Las 55 comprobaciones autenticadas y WSS del [despliegue anterior](../scanner20-20261113/RESULTADOS.md) siguen siendo evidencia separada.

## Reproducción y límites

El [procedimiento ejecutado](procedimiento/deploy.py) depende del estado y respaldos privados del despliegue anterior; no es un comando genérico para otra VM. En el destino se ejecutaron, por separado, `preflight`, `prepare` y `release`. El [colector](procedimiento/collect_remote.py) produce únicamente metadatos permitidos; configuraciones y claves no se versionan. [Huellas de estos artefactos](SHA256SUMS).

La simulación local de escritura por prefijo, preservación del inode, instalación atómica y rechazo de archivos desconocidos pasó con `python3 procedimiento/test_helpers.py`. No simula una caída real de Docker ni acredita una restauración completa. Los ensayos del helper y de la imagen real previos a instalarlo permanecen en [READINESS.md](../../entrega-final/antivirus-vigencia-20261113/READINESS.md).

La clave temporal OS Login se retiró al concluir; las dos claves previas se conservaron y la copia privada temporal se eliminó. [Comprobación de cierre de acceso](access-cleanup.json). Los 34 objetos GCS históricos pendientes no se reanalizaron. Continúan abiertos los recorridos integrales y la recuperación completa de la VM.
