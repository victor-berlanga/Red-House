# Red House en Google Compute Engine

VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`. Referencia: `maquina01`, con CentOS Stream 10, tipo `e2-standard-2` (2 vCPU, 8 GB de RAM), disco `pd-standard` de 20 GB, red `default`, OS Login y las mismas opciones de Shielded VM. Se utilizó su imagen de origen `centos-stream-10-v20260609`.

El proyecto reside en `/opt/redhouse` y se ejecuta por completo en la VM: monolito, microservicios, PostgreSQL, MongoDB, Redis y workers. Docker Compose conserva dos instancias por API. Los archivos privados permanecen en Google Cloud Storage. Los datos remotos y locales son copias independientes: los cambios posteriores no se sincronizan.

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

La cuenta `red-house-archivos` y su acceso al bucket deben existir. El script concede firma sobre esa misma cuenta, sin claves descargadas ni permiso de firma sobre otras cuentas. El scope `cloud-platform` permite invocar GCS e IAM; los permisos IAM mantienen el acceso a objetos limitado al bucket autorizado.

Procedimiento de copia:

1. Con aplicaciones locales detenidas y bases iniciadas, ejecutar `deployment/backup.py` indicando un informe nuevo. El respaldo conserva datos, roles y configuración.
2. Ejecutar `deployment/gcp/package.py --report RUTA_DEL_INFORME --output RUTA_PRIVADA_NUEVA`. Produce `project.tar.gz` y `data.tar.gz`. Excluye `.local`, entornos Python, Git, ADC personales y claves SSH del código. Del respaldo incluye exclusivamente la configuración necesaria para conservar usuarios y cifrado.
3. Transferir los archivos mediante `gcloud compute scp`. Extraer el código en `/opt/redhouse` y el respaldo en un directorio privado de la VM.
4. Construir imágenes desde `/opt/redhouse` con `sudo docker compose --parallel 1 build`. Ejecutar `sudo python3 deployment/gcp/restore.py RUTA_DEL_SNAPSHOT`. Exige un destino nuevo y compara SQL y MongoDB por conteo/hash antes de iniciar aplicaciones. Comprueba Redis y permisos.
5. Instalar `deployment/gcp/redhouse.service` en `/etc/systemd/system/`. Ejecutar `sudo systemctl daemon-reload` y `sudo systemctl enable --now redhouse`.
6. Reservar la IP externa de esa nueva VM, aplicar una regla de firewall TCP 80/443 limitada a su etiqueta y ejecutar `sudo bash /opt/redhouse/deployment/gcp/publish.sh IP_DE_LA_NUEVA_VM`. No reutilizar la reserva de la instancia actual.

El respaldo contiene secretos y debe permanecer privado. El restaurador rechaza destinos existentes; no sirve para sobrescribir una instalación en uso. `docker compose down -v` elimina los volúmenes y sus datos.

## GCS y verificación

La VM reutiliza el bucket privado autorizado; los registros conservan referencias a los objetos existentes. [`configure.py`](configure.py) configura Transporte y web para utilizar la cuenta adjunta a la VM mediante metadatos. La firma de URLs usa IAM con esperas acotadas. No se transfieren ADC personales ni claves privadas de cuentas de servicio.

[`verify.py`](verify.py) ejecuta sangre de principio a fin, consultas JSON/XML de once servicios y carga/descarga web con GCS real. Con `public.json` configurado usa la dirección HTTPS e incluye un flujo web completo. Comprueba persistencia, contenido, rechazo anónimo y autorización por recurso. Deja registros ficticios para demostración. [`verify_public.cjs`](verify_public.cjs) comprueba el navegador cliente, siete perfiles, gráficas, sesiones y Swagger contra la IP pública; no inicia servicios locales. Requiere Playwright y Chrome en el equipo que ejecute esa prueba.

El despliegue tiene una VM y una instancia de cada almacén. Las réplicas API permiten ensayar fallos de aplicación; la infraestructura completa no tiene redundancia. El acceso público utiliza HTTPS, sin dominio. Android, escritorio, validación clínica y operación productiva siguen fuera de este despliegue. [Resultados y límites verificados](../../documentation/evidencias/gcp/RESULTADOS.md).

Referencias utilizadas: [crear VM con gcloud](https://docs.cloud.google.com/sdk/gcloud/reference/compute/instances/create), [Docker en CentOS](https://docs.docker.com/engine/install/centos/), [firma de URLs de GCS](https://docs.cloud.google.com/storage/docs/access-control/signing-urls-with-helpers), [certificados IP con Certbot](https://letsencrypt.org/2026/03/11/shorter-certs-certbot/) y [Waitress detrás de un proxy](https://docs.pylonsproject.org/projects/waitress/en/stable/reverse-proxy.html).
