# Continuidad publicada en GCP — 13/11/2026

Destino comprobado: proyecto `sistemas-integracion-01`, VM existente `red-house`, ID `2861822465669755197`, zona `me-central1-a`, acceso **https://34.18.186.116**. Se arrancó la VM que estaba detenida. El código publicado corresponde a `53844ab` y sus incrementos previos, con [42 fuentes verificadas](manifest.json) respecto a la base `6d8b88d`. No incluye todavía los worktrees de reautenticación ni de nombre operativo del transportista.

## Resultado comprobado

- Treinta contenedores sanos, systemd activo y 42 hashes de fuentes coincidentes. Se prepararon trece imágenes finales y dos imágenes de compatibilidad GCS, derivadas de las imágenes existentes sin actualizar dependencias. PostgreSQL, MongoDB, Redis y ClamAV conservaron sus contenedores. [Estado final](runtime-final.json), [imágenes](builds.json).
- PostgreSQL migró de 18 a 19. Las 37 referencias GCS históricas conservan ruta, generación y SHA-256; los tres trabajos de exportación previos siguen asociados a GCS. [Migración](migration.json), [comparación histórica](historical-preservation.json).
- Documentos y el backend del portal usan almacenamiento privado local para nuevas escrituras. Ambos lectores conservan el proveedor registrado en cada objeto. Dos PDF identificados como pruebas técnicas sintéticas completaron preparación, carga, análisis ClamAV y descarga íntegra; no registraron recolección, entrega ni decisión clínica.
- Volumen compartido por web y las dos réplicas de Documentos: propietario y UID de ejecución `10001`, directorio `0700`, sin enlace simbólico. Los dos archivos nuevos quedaron `VERIFIED` con análisis `CLEAN`. [Conteos y análisis](storage-final.json).
- Una descarga técnica de un reporte histórico GCS con análisis limpio conservó sus 635 bytes, hash y condición de generación, usando el adaptador y permisos vigentes de Documentos. La transacción SQL fue de solo lectura. [Resultado](gcs-read-only.json). Esta prueba no acredita el recorrido de sesión/MFA del propietario por la API.
- Alias de gateway y consumidores limitados a la red privada `data`. Los 25 consumidores resolvieron `gateway-private` únicamente a `172.18.0.6`; Nginx cargó los upstreams privados y su configuración pasó `nginx -t`. [Montajes](effective-mounts.json), [estado de publicación](staged.json).

## Pruebas y ensayos

| Pasada | Resultado | Evidencia y límite |
| --- | --- | --- |
| Compatibilidad previa, todavía esquema 18 | 35 comprobaciones HTTP aprobadas; WSS JSON/XML autenticación y heartbeat | [HTTPS](https-compatibility.json). Son lecturas, sesiones y permisos; no carga sostenida. |
| Código final con esquema 19, antes de activar local | 39 comprobaciones HTTP aprobadas; WSS JSON/XML aprobado | [HTTPS](https-staged.json). Incluye nueva agenda próxima/paginada JSON/XML y seis lecturas de archivos. |
| Tras activar local y recrear sus tres consumidores | 39 comprobaciones HTTP aprobadas; WSS JSON/XML aprobado | [HTTPS final](https-local.json). Repite la comprobación pública después del cambio de configuración. |
| Ciclo local, primera tentativa | Se detuvo antes de crear archivos por no encontrar GCS descargable en diez traslados | [Resultado original](storage-smoke-attempt1.json). No se presenta como prueba aprobada. |
| Ciclo local, segunda tentativa | JSON completó carga 201, repetición 412, análisis 200, rechazo al donante 403 y descarga 200; XML preparó 201 | [Resultado original](storage-smoke-attempt2.json). El lector XML del arnés buscaba nodos directos, pero el contrato usa `field name=...`. |
| Finalización de los dos comandos originales | 17 comprobaciones aprobadas | [Resultado](storage-completion.json). Se conservaron claves y archivos originales; XML completó carga/análisis/descarga. Ambas capacidades devolvieron 401 después de revocar su sesión. Ningún archivo de sustitución. |
| Lectura histórica del almacén GCS | Aprobada, solo lectura | [Resultado técnico](gcs-read-only.json). No equivale a un flujo clínico ni a recepción de push. |

Las pasadas se conservan por separado; no se suman como una suite nueva. La respuesta XML de preparación se obtuvo enviando XML real. La comprobación de descarga comparó bytes y `Cache-Control: no-store`. ClamAV desplegado: `1.4.6`, firmas `28181`, fecha informada `Thu Nov 12 06:27:14 2026`.

El inventario previo mostró 34 evidencias GCS de traslados sin un análisis `CLEAN` asociado y tres reportes con análisis limpio. Las primeras continúan requiriendo análisis antes de descargar; no se modificó su estado ni se reinterpretó `VERIFIED` como análisis limpio. La cuenta `operator1` no tenía reportes propios; el intento de acceso con la cuenta propietaria devolvió 401. Se conservaron [ambos](historical-gcs-attempt1.json) [resultados](historical-gcs.json). La revisión automática rechazó una propuesta de reanálisis porque modificaría evidencia histórica sin autorización específica; no se ejecutó. La alternativa aprobada fue la lectura técnica del reporte limpio, sin POST ni cambios de estado.

## Respaldo y conservación

El respaldo PostgreSQL previo a 019 tiene 39.596.885 bytes, catálogo legible y SHA-256 registrado en [sus metadatos](database-backup.json). Ese archivo registra el momento de creación, anterior al ensayo. Después se restauró en una base temporal privada con acceso público revocado, se aplicó 019 y se compararon metadatos antes/después. El ensayo final duró **41,61 s**, mantuvo producción en 18 y no cambió sus contenedores. La copia temporal se eliminó tras éxito. [Restauración y migración](rehearsal.json), [limpieza de la copia](rehearsal-cleanup.json).

Es un respaldo lógico de PostgreSQL, no una instantánea coordinada de PostgreSQL, MongoDB, Redis, objetos, roles globales y credenciales. El tiempo del ensayo no es RTO de la plataforma. El volumen privado necesita entrar en el procedimiento coordinado de respaldo y recuperación; ese cierre sigue pendiente. El disco final informó aproximadamente 2,85 GB libres. No se eliminaron imágenes, volúmenes ni evidencia histórica para obtener espacio.

## Incidencias corregidas

1. Construcción de compatibilidad: el primer `FROM sha256:...` se interpretó como repositorio; se fijó la etiqueta de la imagen previa. Dos intentos posteriores encontraron directorios copiados sin acceso para UID 10001; se declaró el modo de copia y se verificaron los hashes con el usuario real de la imagen. Los intentos originales se conservan en `prepare*.log`.
2. Primer ensayo de migración: el procedimiento suponía una clave `database_admin` ausente en esta instalación. Se corrigió para usar la credencial de bootstrap ya montada, sin imprimirla. Producción permaneció en 18. La segunda restauración/migración pasó.
3. La versión instalada de Compose no acepta `run --no-build`; se comprobó su ayuda antes de inicializar el volumen y se utilizó la imagen preparada con `--pull never`.
4. Primer cambio de proveedor: Compose dejó los contenedores ejecutándose porque el contenido de un JSON montado no cambia su configuración declarativa. La salud todavía informaba GCS. Se corrigió con `--force-recreate` limitado a web y ambas réplicas Documentos; se comprobó proveedor local en ambos procesos. No había archivos locales en el primer intento. [Intento](enable-local.log), [corrección](enable-local-retry.log).
5. El lector XML y la búsqueda de evidencia histórica del arnés se corrigieron conservando los resultados y los dos comandos originales, según la tabla anterior.

## Recuperación y límites actuales

El procedimiento [deploy.py](deploy.py) conserva las fuentes/configuración privadas, imágenes anteriores y respaldo en `/opt/redhouse/.local/deploy-continuidad-20261113`. Antes de activar local podía volver a las imágenes GCS de compatibilidad manteniendo 019. Después de crear objetos locales debe conservarse el adaptador de ambos proveedores, el volumen y 019. `recover-gcs-writes` permite cambiar futuras escrituras a GCS sin reasignar objetos existentes; está preparado, no ejecutado ni presentado como recuperación ensayada. Un archivo local perdido requiere restaurar su propio objeto y metadatos consistentes.

La ruta binaria pública actual pasa por el bridge del portal. La web conserva autonomía, pero móvil/escritorio todavía dependen del proceso web para esa transferencia local. Se prepara un incremento separado: ruta API hacia Documentos y ruta de portal hacia su backend autónomo, sin fallback de escrituras. Por este motivo no se cierra todavía WORK-STORAGE/WORK-PROXY integralmente.

Tampoco se acreditan alta disponibilidad de host, carga/estrés, todos los fallos I06, restauración de toda la plataforma, recepción FCM/APNs ni aceptación completa de clientes. Las nuevas fuentes móviles/escritorio se verifican y entregan por separado.

Los scripts aquí conservados son los utilizados en `.local/deploy-continuidad-20261113`; para reproducirlos deben colocarse en ese contexto privado, con las credenciales ya autorizadas, y revisar el destino antes de ejecutar. El repositorio contiene resultados, hashes y procedimientos, nunca respaldos de datos, configuraciones privadas, tokens, URLs de capacidades ni claves SSH.

La clave temporal OS Login se retiró y se eliminó su clave privada local. Se comprobaron las otras dos claves del usuario, que permanecen registradas. [Limpieza](ssh-cleanup.json). La VM queda encendida para el equipo.
