# Presentación documental publicada en Red House — 14/11/2026

**Publicación aprobada en `sistemas-integracion-01 / red-house / me-central1-a`.** Se verificaron ID `2861822465669755197` e IP `34.18.186.116`. Solo se recreó el contenedor web: treinta saludables, los otros veintinueve conservaron ID, imagen, inicio y estado. Esquema 20, proveedor LOCAL y configuración restante intactos. HTTPS público `/health/live` y `/login` respondieron 200 con confianza TLS normal.

Se publicaron exactamente tres fuentes: `integration/routes/common.py`, `integration/routes/documents.py` y `presentation/templates/integration/document_upload.html`, bajo `apps/web/src`. El portal presenta estados comprensibles, conserva la recuperación de documentos preparados y, ante versión obsoleta, oculta la carga e indica consultar la versión vigente mediante enlace visible. La dirección inspeccionó la [captura final](../../entrega-final/portal-documentos-20261114/presentacion-final/version-obsoleta.png). El [recorrido funcional local](../../entrega-final/portal-documentos-20261114/RESULTADOS.md) conserva su fallo de oráculo original y su comprobación posterior; no se repitieron cargas privadas en producción.

La imagen nueva `sha256:98f27169bc43704d11627adde2a5f0c7528fe73aac5411f94824641e6a10329a` deriva de la imagen anterior `sha256:3cb7e602427c2fc125f025caf52dd9361bbf31cf16f59108612544e220904179`. Configuración de imagen idéntica, sin instalaciones o migraciones; las capas anteriores se conservaron y se verificaron las tres fuentes dentro de imagen/contenedor/host. Los hashes de [validation.json](validation.json) identifican el contenido publicado. `candidate_head` es contexto del primer empaquetado, no una afirmación de que toda esa revisión del monorepositorio esté desplegada.

## Fallo de construcción conservado y reintento

Preflight aprobó y creó respaldo. El primer build falló: BuildKit interpretó `FROM sha256:<ID>` como un nombre de registro y su resolución de metadatos fue rechazada. No produjo candidata ni cambió el web activo. `--network=none` no bloquea esa resolución; no se presenta aquel intento como ausencia total de red.

El procedimiento se corrigió para usar la etiqueta local de respaldo, cotejando su ID antes y después de construir. El reintento verificó contenido exacto del contexto fallido, conservó Dockerfile/error/procedimiento originales y utilizó un paquete nuevo. No repitió preflight ni sobrescribió el respaldo. Build posterior y publicación aprobaron; no fue necesario ejecutar rollback.

Respaldo remoto privado: `/opt/redhouse/.local/deploy-portal-documentos-20261114/`. Etiqueta anterior retenida: `redhouse-web:before-portal-documentos-20261114`. El [procedimiento](procedimiento/README.md) describe la reversión exclusiva de web; no afecta bases ni datos de negocio. La recreación de un único web puede cortar una petición en curso; no se afirma continuidad sin interrupciones.

## TLS, modo del monolito y acceso

Certificado servido comprobado el 14/11/2026 a las 20:07:27 UTC: vence el **18/11/2026 a las 05:34:04 UTC**. Timer `redhouse-certbot.timer` activo y habilitado; último servicio exitoso el 14 a las 18:14:19 UTC, siguiente disparo observado el 15 a las 00:10:16 UTC. No se ejecutó renovación manual. El certificado observado no cubre el día 23: se requiere comprobar el certificado vigente para la entrega, sin interpretar el éxito anterior del timer como garantía futura.

La [configuración leída](web-mode.json) mantiene `BACKEND_MODE=monolith`. El campo `backend` del endpoint live era una etiqueta constante `microservices`; no describe el modo configurado. Se detectó y corrigió esa etiqueta en fuente después de este despliegue, pendiente de la siguiente publicación. No se cambió el funcionamiento del monolito ni se provocaron caídas productivas en este lote.

Se retiró exclusivamente la clave OS Login temporal propia y se verificó conservación de las dos previas; archivos locales de la clave eliminados. [Recibo de cierre](access-cleanup.json). No se crearon recursos GCP ni se publicaron credenciales. La validación acredita este cambio acotado y disponibilidad observada, no la aceptación integral de la etapa 06.
