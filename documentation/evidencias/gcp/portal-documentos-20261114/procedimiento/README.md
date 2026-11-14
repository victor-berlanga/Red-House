# Publicación acotada de documentos del portal

**Estado: publicado y validado el 14/11/2026.** La preparación inicial y sus pasos se conservan aquí como procedimiento. [Resultado remoto, reintento y límites](../RESULTADOS.md).

Destino exclusivo: proyecto `sistemas-integracion-01`, VM `red-house`, zona `me-central1-a`, ID `2861822465669755197`, IP `34.18.186.116`. El control remoto valida estos cinco datos mediante metadata. Esquema esperado: **20**. Almacenamiento: **LOCAL**.

## Alcance y elección de imagen

Se incluyen exactamente estas fuentes actuales:

- `apps/web/src/integration/routes/common.py`
- `apps/web/src/integration/routes/documents.py`
- `apps/web/src/presentation/templates/integration/document_upload.html`

`documents.py` está limpio frente al HEAD local al preparar el paquete; se incluye porque el origen publicado puede ser anterior. No se presupone que los tres archivos difieran de la VM. Los hashes del paquete fijan el contenido revisado, incluido el ajuste posterior del texto `ERROR` y el enlace subrayado del conflicto 412.

La imagen deriva del **ID exacto de la imagen web que esté ejecutándose en el preflight**, mediante una etiqueta local de respaldo cuyo ID se coteja antes y después, con tres `COPY --chmod=0644`. Construcción: `docker build --network=none --pull=false`. No ejecuta `RUN`, instala dependencias ni migra datos. Se exige que `Config` completo coincida con la imagen anterior, incluidos usuario, entrypoint, comando, entorno, healthcheck y etiquetas. Se rechaza una imagen base con hooks `ONBUILD` o montajes que oculten `/app`.

Esto evita reconstruir todas las dependencias por tres fuentes y conserva el entorno ya desplegado. La reproducción depende de conservar la imagen base local, fijada por ID y retenida también mediante una etiqueta de respaldo. No se afirma reproducibilidad independiente de esa base. No se publica una imagen nueva en registros remotos.

## Preparación local realizada

`prepare_local.py` solo lee las tres fuentes y Git, comprueba sintaxis Python y crea una copia privada. No usa red, Docker, SSH ni GCP. El destino debe ser nuevo y estar bajo `.local/`:

```sh
python3 documentation/evidencias/gcp/portal-documentos-20261114/procedimiento/prepare_local.py --root "$PWD" --output "$PWD/.local/gcp/portal-documentos-20261114/package"
```

El paquete contiene `manifest.json`, `source.json`, el diff completo de las tres fuentes desde `982d592^`, `deploy.py` y `payload/`. `source.json` fija también el commit resuelto y los tres hashes de esa base conocida. Si cambia cualquiera de las fuentes o el procedimiento después de empaquetar, crear otra carpeta privada y volver a cotejar los hashes. No sobrescribir un paquete ya usado.

## Secuencia de publicación

Los pasos originales se conservan para revisión. El primer `prepare` falló porque BuildKit interpretó `FROM sha256:<ID>` como repositorio; se conservó el fallo y se usó `prepare_retry` con un paquete nuevo `--package /tmp/redhouse-portal-documentos-20261114-retry`, sin repetir preflight ni sobrescribir su respaldo. La etiqueta local verificada resolvió el candidato; se publicaron exactamente las tres fuentes. `--network=none` limita la red de las instrucciones de construcción, no la resolución de metadatos del registro; el primer intento consultó el registro y no obtuvo imagen.

Para una ejecución nueva: No ejecutar durante la serie de carga local.

1. Revisar capturas finales y cotejar las tres fuentes contra `manifest.json`. La inspección visual local no certifica producción.
2. Añadir acceso temporal con `access.py add --directory <ruta-absoluta-bajo-.local>/access`. Comprueba VM y exige las dos claves OS Login previas; crea una tercera propia con TTL de 30 minutos. Material privado fuera de la documentación versionada.
3. Usar SSH/SCP con la clave recién creada, usuario `victor_berlangam_gmail_com`, `IdentitiesOnly=yes` y `StrictHostKeyChecking=yes`. Reutilizar únicamente una clave de host ya verificada; no aceptar `ssh-keyscan` como única verificación ni deshabilitar comprobación de host. No copiar el directorio `access` a la VM.
4. Crear como usuario SSH un directorio **nuevo** `/tmp/redhouse-portal-documentos-20261114`, modo 0700; copiar allí el contenido del paquete, conservando `payload/`. Rechazar ruta existente o enlaces simbólicos. Las credenciales temporales no pertenecen al paquete.
5. Ejecutar por SSH cada fase separada, conservando salidas privadas. Todos los comandos siguientes son futuros y se ejecutan **en la VM**:

```sh
sudo python3 /tmp/redhouse-portal-documentos-20261114/deploy.py preflight
sudo python3 /tmp/redhouse-portal-documentos-20261114/deploy.py prepare
sudo python3 /tmp/redhouse-portal-documentos-20261114/deploy.py release
```

`preflight` exige que los tres hashes del host coincidan íntegramente con la base conocida `git show 982d592^:<ruta>` o íntegramente con el candidato. Coteja esos hashes contra el web en ejecución y su imagen inmutable, mediante una sonda desechable sin red. Un contenido desconocido o mezcla parcial aborta antes de respaldar o sobrescribir; comparar diferencias antes de continuar. Conserva fuentes anteriores, configuración privada completa, Compose efectivo, inspecciones de contenedor e imagen, hashes y etiqueta de imagen previa en `/opt/redhouse/.local/deploy-portal-documentos-20261114/`. No continúa sobre un backup preexistente: una publicación ya intentada se valida o revierte usando su evidencia. No se hace respaldo de bases porque no se modifican esquemas ni datos; las operaciones normales siguen habilitadas.

También lee el certificado HTTPS servido realmente, validando confianza del sistema e IP; registra huella y vencimiento, y consulta `redhouse-certbot.timer` y el último resultado de `redhouse-certbot.service`. La configuración local documenta renovación cada seis horas, con hasta 15 minutos aleatorios; eso no acredita que esté activa en la VM. El informe indicará si el certificado observado cubre el final del 23 de noviembre en Monterrey. Un certificado corto puede necesitar la renovación ya programada: no se presume cobertura futura ni éxito del timer. No se ejecuta Certbot, renovación, dry-run ni cambios de cuentas/timers. La dirección registrará vencimiento y siguiente renovación observados; la entrega requiere evidencia vigente entonces.

`prepare` construye la candidata sin red y comprueba hashes, sintaxis Python y sintaxis Jinja en un contenedor desechable sin red, solo lectura y sin capacidades. El contexto contiene solo las tres fuentes y el Dockerfile. No inicia la aplicación ni monta secretos. Conserva el candidato de `gcs.compose.yaml`; todavía no cambia la configuración efectiva.

`release` vuelve a exigir runtime/configuración/fuentes idénticos al preflight. Sustituye atómicamente las tres fuentes del host y cambia **solo `services.web.image`** en `gcs.compose.yaml`. Rechaza cualquier otra diferencia en el Compose efectivo. Ejecuta `up --no-deps --no-build --pull never --wait web`; no recrea API, workers, proxy, bases, escáner ni almacenamiento. La sustitución del único web puede causar una interrupción breve del portal y cortar peticiones web en curso; no hay gate global ni detención de escrituras del resto de la plataforma.

La validación exige **30 saludables**, los otros **29 contenedores exactamente iguales** por ID, imagen, etiqueta, inicio y salud, hashes correctos en host y web, configuración restante intacta, esquema 20 y proveedor local. Comprueba HTTPS público con confianza TLS normal en `/health/live` y `/login` y vuelve a registrar certificado/timer. La versión efectiva de la entrega queda identificada por imagen base, imagen candidata y tres hashes. El HEAD local queda solo como contexto del empaquetado; las etiquetas heredadas de revisión no afirman que se desplegó ese monorepositorio completo. No inventa un incremento de versión semántica. No repite operaciones de documentos ni introduce datos en producción.

6. Descargar `validation.json` y los informes necesarios al directorio privado local; revisar antes de retirar acceso. No publicar configuraciones, dumps de inspección, logs privados ni claves. Conservar también el ID de imagen anterior y la ruta de rollback.
7. Retirar exclusivamente la clave propia después de la validación:

```sh
python3 documentation/evidencias/gcp/portal-documentos-20261114/procedimiento/access.py remove --directory <directorio-privado>/access --receipt <directorio-privado>/validation.json
```

La retirada verifica la huella propia contra la clave pública local, conserva exactamente las dos claves anteriores y comprueba el resultado antes de borrar los archivos locales de la clave temporal. Si el TTL ya venció, verifica su ausencia sin eliminar ninguna otra clave. Si la publicación se revierte, utilizar `rollback.json` validado como recibo. Un fallo anterior al preflight no produce recibo: conservar diagnóstico y retirar manualmente **solo la huella propia demostrada**; el TTL evita acceso indefinido. No prolongar ni renovar la clave sin revisar el estado.

## Rollback explícito

`release` intenta rollback ante fallo posterior al inicio de publicación. Tras una interrupción de SSH o del proceso, inspeccionar los informes y ejecutar, en la misma VM:

```sh
sudo python3 /opt/redhouse/.local/deploy-portal-documentos-20261114/deploy.py rollback
```

Restaura solo las tres fuentes y el override anterior, exige que la etiqueta anterior siga apuntando al ID respaldado y recrea únicamente web. Admite que el web fallido esté detenido; los otros 29 deben seguir intactos. Repite validación de hashes, esquema, almacenamiento, configuración y HTTPS. No restaura bases, volúmenes, sesiones ni datos de negocio; tampoco revierte cambios desconocidos concurrentes. No borra imágenes, backups ni laboratorios.

Si encuentra fuentes/configuración desconocidas, un archivo temporal `.portal-new`, una etiqueta anterior desplazada o cambios en otro contenedor, falla sin sustituir datos desconocidos. La dirección debe reconciliar ese estado con el backup; no borrar archivos temporales sin cotejar su contenido. No repetir `preflight` ni sobrescribir evidencia para forzar una aprobación.

## Límites

La preparación estática inicial se conserva en `preparacion-local.json` como corte histórico, con el hash del procedimiento anterior al reintento. El resultado remoto y la retirada de acceso se conservan por separado. La ejecución publicada utilizó el procedimiento corregido y verificó imagen, tres hashes y entorno. La validación remota propuesta comprueba despliegue y disponibilidad; no reemplaza el recorrido de documentos privados ya previsto en laboratorio ni prueba continuidad de una petición cortada durante la recreación.
