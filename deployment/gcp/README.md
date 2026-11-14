# Red House en Google Compute Engine

## Estado vigente — 14/11/2026

Destino vigente: VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`, instancia `2861822465669755197`, acceso HTTPS `https://34.18.186.116`. El corte actual conserva esquema 20, ClamAV con control periódico de vigencia y almacenamiento privado `LOCAL`; GCS es opcional y tiene verificación académica separada. Véanse [publicación del esquema 20 y escáner](../../documentation/evidencias/gcp/scanner20-20261113/RESULTADOS.md), [control periódico de firmas](../../documentation/evidencias/gcp/scanner-health-20261113/RESULTADOS.md) y [proxy WSS vigente](../../documentation/evidencias/gcp/proxy-wss-20261114/RESULTADOS.md).

Los siguientes registros del 10/11 conservan un corte histórico de esquema 18; no describen la versión actualmente publicada.

> Corte histórico del **10/11/2026**: UI web `redhouse/web:uiux-20261110`; backend `mobile04-20261110` / esquema 18. [Verificación y reversión de ese corte](../../documentation/evidencias/gcp/uiux-20261110/RESULTADOS.md).

> Corte histórico del **10/11/2026**: **https://34.18.186.116**, tag **`mobile04-20261110` / esquema 18**, 30 contenedores sanos. [Respaldo, migración y verificación HTTPS/WSS de ese corte](../../documentation/evidencias/gcp/mobile04-20261110/RESULTADOS.md).

VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`. Referencia: `maquina01`, con CentOS Stream 10, tipo `e2-standard-2` (2 vCPU, 8 GB de RAM), disco `pd-standard` de 20 GB, red `default`, OS Login y las mismas opciones de Shielded VM. Se utilizó su imagen de origen `centos-stream-10-v20260609`.

El proyecto reside en `/opt/redhouse` y se ejecuta por completo en la VM: monolito, microservicios, PostgreSQL, MongoDB, Redis y workers. Docker Compose conserva dos instancias por API. El corte vigente usa almacenamiento privado `LOCAL`; no se debe asumir que archivos de producción estén en GCS. Las referencias a GCS más abajo describen la ruta opcional explícita.

## Abrir el portal

Abrir **https://34.18.186.116** desde cualquier navegador. También se puede escribir `http://34.18.186.116`: redirige a HTTPS. No se necesita iniciar Docker, ejecutar comandos locales, abrir un túnel SSH ni tener el repositorio descargado.

Las cuentas de Red House conservan las credenciales del Docker de demostración copiado. El registro privado está en `/opt/redhouse/.local/compose/state.json` dentro de la VM. No proyectar ni versionar ese archivo.

Swagger de Inventario: **https://34.18.186.116/services/inventario/docs/**. Cada API mantiene sus contratos y JWT; el prefijo público identifica al servicio:

| Servicio | Prefijo público |
| --- | --- |
| Identidad y acceso | `/services/identidad-acceso` |
| Donantes | `/services/donantes` |
| Receptores | `/services/receptores` |
| Inventario | `/services/inventario` |
| Compatibilidad | `/services/compatibilidad` |
| Priorización y geografía | `/services/priorizacion-geografia` |
| Transporte | `/services/transporte` |
| Custodia | `/services/custodia` |
| Alertas | `/services/alertas` |
| Auditoría | `/services/auditoria` |
| Monitoreo | `/services/monitoreo` |
| Documentos y reportes | `/services/documentos` |

Agregar `/docs/`, `/openapi.json`, `/health/live` o la ruta del contrato, por ejemplo `/api/v1/resources`. Las rutas `/internal/` quedan bloqueadas en la entrada pública. PostgreSQL, MongoDB y Redis no tienen puertos publicados. La comunicación interna entre componentes conserva sus direcciones Docker.

La IP se reservó como `red-house-public` en `me-central1`. La regla `red-house-web` permite TCP 80/443 únicamente a instancias con la etiqueta de red homónima. Nginx termina TLS y dirige el tráfico al monolito y a las réplicas de cada API.

## Administrar la VM

```sh
gcloud compute ssh red-house --project=sistemas-integracion-01 --zone=me-central1-a
sudo systemctl status redhouse
sudo systemctl stop redhouse
sudo systemctl start redhouse
sudo journalctl -u redhouse -n 50 --no-pager
sudo docker compose -f /opt/redhouse/compose.yaml ps
```

El servicio `redhouse` inicia los componentes por grupos y queda habilitado al arrancar la VM. El código y la configuración privada pertenecen a `root`; administrar requiere `sudo`. Los datos permanecen en volúmenes Docker.

Para actualizar o recuperar componentes, usar `sudo python3 /opt/redhouse/deployment/start.py`; incorpora automáticamente los archivos privados `gcs.compose.yaml` y `public.compose.yaml`. Un `docker compose up` con solo el archivo base no incluye la entrada HTTPS. Las configuraciones y certificados privados no se versionan.

Apagar o encender la VM desde tu equipo:

```sh
gcloud compute instances stop red-house --project=sistemas-integracion-01 --zone=me-central1-a
gcloud compute instances start red-house --project=sistemas-integracion-01 --zone=me-central1-a
```

Detener conserva el disco y la IP reservada; el portal deja de responder mientras la VM está apagada. La VM, su disco y la dirección externa están sujetos a las tarifas de GCP.

## HTTPS y renovación

[`publish.sh`](publish.sh), ejecutado como root dentro de la VM, configura Nginx y obtiene un certificado de Let's Encrypt para la IP. Certbot es una herramienta de administración del certificado, instalada en `/opt/redhouse-certbot`; no forma parte de la lógica de negocio.

El certificado de IP tiene vigencia corta. `redhouse-certbot.timer` comprueba su renovación cada seis horas. El hook [`reload_certificate.sh`](reload_certificate.sh) instala la clave con lectura limitada al grupo de Nginx y recarga el gateway. Los desafíos ACME usan HTTP sin detener la aplicación.

```sh
sudo systemctl status redhouse-certbot.timer
sudo journalctl -u redhouse-certbot.service -n 30 --no-pager
sudo /opt/redhouse-certbot/bin/certbot certificates
sudo /opt/redhouse-certbot/bin/certbot renew --dry-run
```

La web usa cookies `Secure`, `HttpOnly` y `SameSite=Lax`. Waitress recibe explícitamente el esquema HTTPS; no confía en cabeceras enviadas por el navegador. El formulario mantiene la protección CSRF. El acceso HTTP directo a `127.0.0.1:6050` sirve para diagnóstico del proceso; usar HTTPS para iniciar sesión.

## Crear otra instalación equivalente

[`create.sh`](create.sh) contiene el comando `gcloud compute instances create` con los valores verificados. Crea una VM nueva e instala Docker mediante [`startup.sh`](startup.sh). Para cambiar el nombre:

```sh
REDHOUSE_GCP_INSTANCE=red-house-otra bash deployment/gcp/create.sh
```

El script histórico `create.sh` está preparado para la variante GCS: exige la cuenta `red-house-archivos` y concede firma sobre esa misma cuenta, sin claves descargadas ni permiso de firma sobre otras cuentas. No es un requisito para operar una instalación `LOCAL` existente ni un aprovisionador neutral respecto al almacenamiento. El scope `cloud-platform` permite invocar GCS e IAM; los permisos IAM mantienen el acceso a objetos limitado al bucket autorizado.

Procedimiento de copia:

1. Con aplicaciones locales detenidas y bases iniciadas, ejecutar `deployment/backup.py` indicando un informe nuevo. El respaldo conserva datos, roles y configuración.
2. Ejecutar `deployment/gcp/package.py --report RUTA_DEL_INFORME --output RUTA_PRIVADA_NUEVA`. Produce `project.tar.gz` y `data.tar.gz`. Excluye `.local`, entornos Python, Git, ADC personales y claves SSH del código. Del respaldo incluye exclusivamente la configuración necesaria para conservar usuarios y cifrado.
3. Transferir los archivos mediante `gcloud compute scp`. Extraer el código en `/opt/redhouse` y el respaldo en un directorio privado de la VM.
4. Construir imágenes desde `/opt/redhouse` con `sudo docker compose --parallel 1 build`. Ejecutar `sudo python3 deployment/gcp/restore.py RUTA_DEL_SNAPSHOT`. Exige un destino nuevo y compara SQL y MongoDB por conteo/hash antes de iniciar aplicaciones. Comprueba Redis y permisos.
5. Instalar `deployment/gcp/redhouse.service` en `/etc/systemd/system/`. Ejecutar `sudo systemctl daemon-reload` y `sudo systemctl enable --now redhouse`.
6. Reservar la IP externa de esa nueva VM, aplicar una regla de firewall TCP 80/443 limitada a su etiqueta y ejecutar `sudo bash /opt/redhouse/deployment/gcp/publish.sh IP_DE_LA_NUEVA_VM`. No reutilizar la reserva de la instancia actual.

El respaldo contiene secretos y debe permanecer privado. El restaurador rechaza destinos existentes; no sirve para sobrescribir una instalación en uso. `docker compose down -v` elimina los volúmenes y sus datos.

## GCS opcional y verificación específica

Esta sección aplica solo si una instalación autorizada opta por GCS; no describe el proveedor activo de la VM vigente. [`configure.py`](configure.py) escribe bucket/proyecto y un override GCS para web y Documentos, usando la identidad adjunta a la VM. [`configure_local_storage.py`](../configure_local_storage.py) conserva la ruta existente `LOCAL` mediante un directorio absoluto privado. No cambiar el proveedor de una instalación activa sin procedimiento y autorización propios; nunca transferir ADC personales ni claves privadas de cuentas de servicio.

[`verify.py`](verify.py) ejecuta sangre de principio a fin, consultas JSON/XML de once servicios y carga/descarga web con GCS real. Con `public.json` configurado usa la dirección HTTPS e incluye un flujo web completo. Comprueba persistencia, contenido, rechazo anónimo y autorización por recurso. Deja registros ficticios para demostración. [`verify_public.cjs`](verify_public.cjs) comprueba el navegador cliente, siete perfiles, gráficas, sesiones y Swagger contra la IP pública; no inicia servicios locales. Requiere Playwright y Chrome en el equipo que ejecute esa prueba.

El despliegue tiene una VM y una instancia de cada almacén. Las réplicas API permiten ensayar fallos de aplicación; la infraestructura completa no tiene redundancia. El acceso público utiliza HTTPS, sin dominio. El cliente Android 0.3.1 apunta a este gateway; su aceptación integral, escritorio, validación clínica y operación productiva siguen pendientes. [Resultados y límites verificados](../../documentation/evidencias/gcp/RESULTADOS.md).

## Datos para la demostración

El 21 de octubre se amplió la base de GCP con datos ficticios relacionados, conservando los registros anteriores. Cada hospital original dispone de 34 donantes, 30 campañas, 59 citas y 30 donaciones. También se agregaron inventarios, receptores, solicitudes y 30 traslados con archivos reales privados. `donor1` y `donor2` tienen expediente propio y 30 citas cada uno. Los listados muestran 20 filas por página; usar «Siguiente» para ver el resto.

La carga [`populate_demo.py`](populate_demo.py) está acotada a esta VM y a este conjunto de demostración. Usa las credenciales privadas existentes y las API autenticadas; sus consultas administrativas SQL son de lectura. Conserva fechas, identificadores y claves de idempotencia en `/opt/redhouse/.local/compose/demo-20261021/checkpoint.json`. Exige el manifiesto del respaldo previo y bloquea ejecuciones simultáneas. Para reanudar este mismo conjunto, dentro de la VM:

```sh
sudo python3 /opt/redhouse/deployment/gcp/populate_demo.py --apply
```

La carga ya está aplicada; no forma parte del arranque normal. Conservar el checkpoint y el respaldo en `demo-20261021/backup-before/`. No borrar ese directorio para generar otro conjunto. Las fechas de campaña y caducidad pertenecen a esta demostración; repetir el comando no las renueva. El script no es un instalador ni un restaurador para otra VM.

Por indicación del usuario, los nombres actuales y el generador omiten la etiqueta `DEMO`. Los folios usan `RH26`; las 16 cuentas adicionales son `donor_1_01`–`donor_1_08` y `donor_2_01`–`donor_2_08`, con sus mismas contraseñas. [`normalize_labels.py`](normalize_labels.py) documenta la corrección de los 743 registros originales mediante una transacción limitada a sus textos actuales. Sin argumentos muestra los cambios pendientes; `--apply` exige el respaldo privado de `labels-20261021/`. La corrección ya está aplicada y conserva UUID, cantidades, relaciones, versiones y estados. Los eventos históricos y el checkpoint original permanecen intactos.

[`verify_demo.cjs`](verify_demo.cjs) revisa los listados por HTTPS con Chrome/Playwright y la copia privada de credenciales. Se ejecuta desde la raíz del repositorio, en un equipo cliente con esas dependencias disponibles; no inicia servicios. [Cantidades, excepciones por tabla, comprobaciones y capturas](../../documentation/evidencias/gcp/datos-demo/RESULTADOS.md).

## Baja de donantes

Desde el 21 de octubre, el perfil médico puede usar **Donantes → icono de papelera** (etiqueta «Retirar donante») en su institución. Sin historia se elimina la fila; con dictámenes, donaciones, citas o correcciones se conserva como inactiva, fuera de listados y selectores. Se cancelan las citas pendientes y se conserva auditoría. Volver, Cancelar y recargar un formulario ya no muestran el aviso nativo de cambios sin guardar. [Criterios, verificación en GCP y límites](../../documentation/evidencias/gcp/bajas-donantes/RESULTADOS.md).

La baja por sí sola conserva el arranque habitual y no necesita migraciones ni cargar nuevamente los datos. [`verify_donor_withdrawal.cjs`](verify_donor_withdrawal.cjs) comprueba la función desde un navegador cliente; crea dos registros propios y da de baja ambos, por lo que no se ejecuta automáticamente al iniciar.

La confirmación presenta solo las consecuencias para el usuario. Los detalles técnicos quedan en las vistas autorizadas de administración y auditoría. [`verify_portal_copy.cjs`](verify_portal_copy.cjs) revisa el icono, textos y visibilidad por perfil consultando registros existentes, sin enviar formularios de negocio. [Resultados de esta revisión](../../documentation/evidencias/gcp/bajas-donantes/RESULTADOS.md#ajuste-posterior-de-presentación).

## Auditoría, hallazgos y formularios

Publicados el 21 de octubre de 2026. La instalación utiliza esquema global **7** y Auditoría **3**, con 74 tablas de dominio y una tabla técnica de sesiones. Se conservaron datos y credenciales. La bitácora incorpora filtros, exportación e investigación relacionada; el seguimiento de hallazgos separa atención del coordinador y verificación del auditor. Los formularios muestran límites y errores por campo conservando la captura. [Resultados del despliegue](../../documentation/evidencias/gcp/auditoria-formularios/RESULTADOS.md).

Para otra instalación que todavía use esquema 6, preparar imágenes nuevas antes del corte, respaldar y verificar la restauración, detener aplicaciones y ejecutar:

```sh
sudo python3 /opt/redhouse/deployment/migrate_audit.py --directory /opt/redhouse/.local/compose
```

La herramienta realiza otro respaldo PostgreSQL privado y aplica la migración aditiva; en versión 7 no modifica nada. No sustituir la base existente por `schema.sql`. Después, iniciar las imágenes nuevas con los overrides privados mediante `deployment/start.py` y verificar readiness. Conservar los permisos de lectura/recorrido de los directorios de código al empaquetar: las imágenes ejecutan como UID 10001. Las carpetas privadas de configuración y respaldo mantienen acceso restringido.

[`verify_audit_forms.cjs`](verify_audit_forms.cjs) recibe por stdin `password`, `coordinator` y `output`, usando Chrome/Playwright. Envía cuatro formularios de donante inválidos y conserva un hallazgo ficticio cerrado; no se ejecuta en el arranque. [`verify_audit_forms.py`](verify_audit_forms.py), dentro de la VM, recibe `--finding`, `--resource` y `--output`; consulta JSON/XML, permisos, historial, avisos y detalles seguros de validación. Ambos requieren una verificación autorizada del entorno académico.

Referencias utilizadas: [crear VM con gcloud](https://docs.cloud.google.com/sdk/gcloud/reference/compute/instances/create), [Docker en CentOS](https://docs.docker.com/engine/install/centos/), [firma de URLs de GCS](https://docs.cloud.google.com/storage/docs/access-control/signing-urls-with-helpers), [certificados IP con Certbot](https://letsencrypt.org/2026/03/11/shorter-certs-certbot/) y [Waitress detrás de un proxy](https://docs.pylonsproject.org/projects/waitress/en/stable/reverse-proxy.html).

## Referencia histórica: configuración GCS y actualización correctiva del 31 de octubre

Este procedimiento conserva el corte GCS de esa fecha. No es requisito para la ruta privada `LOCAL` vigente ni una indicación para modificar la VM actual.

El migrador `apps/services/scripts/upgrade_compose.py` admite el estado de la instalación v7: conserva la contraseña Redis administrativa existente y limita el permiso CREATE del dueño del esquema a la transacción de actualización. No ejecutar bootstrap de instalación sobre una base poblada. Mantener respaldo verificado y escritores detenidos.

Después de `configure.py`, ejecutar `configure_scanner.py` para incorporar ClamAV privado y sus dependencias al override GCS, antes de `configure_public.py` y `deployment/start.py`. El escáner no publica puertos y conserva firmas en un volumen propio. `deployment/backup.py` incluye los overrides y TLS en el respaldo privado y contempla el escáner al reanudar aplicaciones. Conservar directorios de fuentes con modo 755 y archivos legibles por UID 10001 al transferir; la configuración privada mantiene permisos restringidos.

FreshClam comprueba actualizaciones 12 veces al día (`FRESHCLAM_CHECKS=12`); esto no garantiza que ClamD haya cargado la versión más reciente. La política de antigüedad máxima de firmas permanece en 48 horas y la salud del proceso no demuestra por sí sola la coincidencia entre firmas cargadas y disponibles en disco.

`CLAMD_CONF_ConcurrentDatabaseReload=no` evita mantener dos motores de firmas durante la recarga. Durante esa operación el escaneo puede no estar disponible; Documentos debe rechazar la verificación si el escáner no responde, sin marcar archivos como limpios.

`configure_scanner.py` copia `clamav_readiness.sh` al directorio privado de configuración con modo 0444 y lo monta en ClamAV de solo lectura. Docker lo ejecuta cada 30 segundos: consulta dos veces `VERSION` por TCP local y comprueba versión y antigüedad de la cabecera daily. El resultado Docker no modifica `/health/storage`, que informa sobre el almacenamiento del producto. La comprobación no verifica la integridad completa ni todas las bases cargadas. Al cambiar el helper o el límite de antigüedad en Documentos, volver a generar la configuración, recrear ClamAV y validar el healthcheck antes de reabrir el servicio. La etiqueta SHA-256 permite a Compose detectar cambios del helper. El respaldo incluye el script.

La demostración usa `deployment/gcp/prepare_correction_demo.py --directory DIRECTORIO_PRIVADO` con una copia local preexistente de las credenciales ficticias. Conserva factores MFA y checkpoint privados, reutiliza registros al reanudar y nunca imprime secretos. `scripts/demonstrate_gcp_corrections.cjs` recibe la entrada por stdin, abre Chrome visible y no captura pantalla ni graba. `deployment/gcp/verify_correction_contracts.py` comprueba lecturas JSON/XML contra DTO/XSD. Ejecutarlos solo bajo autorización de cuentas y datos ficticios; no forman parte del arranque normal.
