# Optimización de servidor publicada en GCP — 12/11/2026

Autorización: «Subelos». Publicado el incremento de servidor en **https://34.18.186.116**, VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`. La VM queda encendida. Última comprobación: **18:20:14 UTC**, treinta contenedores sanos, systemd activo y fuentes/configuración coincidentes. [Estado final](final-check.json).

**El despliegue está completado; el encargo OPT-01…OPT-12 sigue parcial.** Los cambios móviles no se instalan en Android/iOS mediante este despliegue. Criterios pendientes y resultados locales: [matriz](../../../entrega-final/optimizacion/Matriz.md), [laboratorio previo](../../optimizacion/20261111/RESULTADOS.md).

## Alcance y preservación

Siete archivos de servidor, con SHA idénticos a los validados localmente: disponibilidad de horarios, concesiones WSS, caché opcional, consulta de monitoreo/índice Mongo, sesión web y scripts de gráficas. [Manifiesto](manifest.json).

Seis imágenes derivadas de las imágenes vigentes, sin red durante su construcción ni actualización de dependencias. Tag `optimization-20261112` para `redhouse/identidad_acceso`, `redhouse/donantes`, `redhouse/inventario`, `redhouse/transporte`, `redhouse/monitoreo` y `redhouse/web`. Se comprobaron hashes y compilación Python dentro de cada imagen; Env, Entrypoint, Cmd, User y WorkingDir coinciden con su base. [Imágenes y archivos incorporados](builds.json).

Sustitución secuencial de las dos réplicas de cada uno de esos cinco servicios y web: **once contenedores**. Los otros **diecinueve** conservan ID, imagen y salud; no se reiniciaron PostgreSQL, MongoDB, Redis, gateway ni ClamAV. Se conservan configuración protegida, credenciales, permisos, recursos, timeouts, pools y esquema PostgreSQL. El override de despliegue cambia únicamente las imágenes seleccionadas. [Antes](runtime-before.json), [después](runtime-after.json), [resultado](result.json), [registro de sustitución y nginx -t](rollout.log).

El índice parcial `monitor_latest` se creó directamente con la definición validada, sin ejecutar migraciones ajenas. Orden: `service ASC, checked_at DESC, event_id ASC`; filtro: `source=monitoreo` y presencia de `checked_at`. **889.901 documentos estimados**, **6.304,461 ms** de construcción, **64.286.720 bytes**; índices previos conservados. Esto mide construcción, no coste sostenido de escrituras. [Índice](index.json).

## Verificación pública

| Comprobación | Resultado | Evidencia |
|---|---|---|
| `/monitoreo` antes | 503, una apertura de 8.466,384 ms | [Antes](https-before.json) |
| `/monitoreo` después | Cuatro aperturas HTTP 200; últimas dos: 992,827 y 823,331 ms. Dos vistas Chrome 200 | [Primer intento](https-after-attempt1.json), [repetición final](https-after.json), [Chrome](browser-after.json) |
| API independientes | Doce `/health/ready` responden 200 | [HTTPS final](https-after.json) |
| Portal autenticado | Monitoreo, paneles, citas, campañas, inventario y traslados: 200. Sesión conserva campos y no-store; logout termina en 401 | [Procedimiento](verify_http.py), [resultados](https-after.json) |
| API por rol | Monitoreo e inventario JSON/XML; horarios y traslados JSON: 200. Donante/inventario: 403 esperado | [Veintinueve comprobaciones HTTP finales](https-after.json) |
| WSS | JSON y XML: autenticación y heartbeat, TLS verificado, sin publicar posiciones ni suscribirse a un traslado | [WSS final](https-after.json) |
| Chrome real | Auditor/monitoreo y paneles donante/operador, 1440 y 390 px: seis vistas sin desbordamiento ni errores JavaScript; tres logout con sesión 401 | [Procedimiento](verify_browser.cjs), [resultados](browser-after.json) |
| Gráficas en navegador | Donante: cero scripts y solicitudes de gráficas. Operador: tres scripts y catorce gráficas renderizadas en ambos anchos | [Chrome](browser-after.json) |

HTTPS y Chrome verifican el certificado; Chrome negoció TLS 1.3. JSON/XML se interpretaron con los analizadores existentes; estas consultas HTTP no constituyen una nueva validación XSD exhaustiva. WSS usa los contratos existentes. Se revocaron las sesiones API creadas por el arnés y se cerraron las sesiones web. No se enviaron escrituras de negocio, cargas de archivos ni posiciones GPS; la autenticación, lectura, caché, auditoría y monitoreo mantienen sus efectos normales.

Los tiempos son observaciones de aceptación desde la máquina local, no un benchmark comparable de carga, percentiles, LCP o SLA. La segunda comprobación HTTP coincidió parcialmente con Chrome. No se atribuyen porcentajes de mejora ni validación física móvil.

## Respaldo y reversión

Respaldo privado en `/opt/redhouse/.local/deploy-optimization-20261112`, accesible a root: fuentes anteriores, override, imágenes anteriores fijadas y archivo lógico de `rh_monitoreo.events`. Archivo Mongo: **38.664.460 bytes**, integridad gzip comprobada y SHA registrado. Es un respaldo de esa colección con la plataforma activa; **no se ensayó restaurarlo y no equivale a un respaldo integral consistente de todas las bases**. No contiene cambios destructivos de datos. [Informe sin datos privados](backup-report.json).

Reversión preparada, sin ejecutarla. En la VM:

```sh
sudo python3 /opt/redhouse/.local/deploy-optimization-20261112/rollback.py
```

Restaura los siete archivos, el override y las imágenes de los once contenedores, verificando salud e imágenes previas. Conserva el índice aditivo compatible. El despliegue ejecuta esta reversión automáticamente ante un fallo durante la sustitución. [Implementación](deploy.py), [entrada de reversión](rollback.py).

## Procedimiento e incidencias conservadas

Paquete limitado a siete fuentes, manifiesto, comprobaciones previas y procedimiento; transporte por SSH con clave temporal OS Login y host conocido verificado. No se copiaron bases locales ni secretos. Comandos principales ejecutados en la VM:

```sh
sudo python3 /tmp/redhouse-optimization-20261112/deploy.py prepare
sudo python3 /opt/redhouse/.local/deploy-optimization-20261112/deploy.py index
sudo python3 /opt/redhouse/.local/deploy-optimization-20261112/deploy.py rollout
```

El primer `prepare` se detuvo al comparar un metadato Docker `Cmd` ausente. Se corrigió el acceso opcional, conservando la misma comparación de configuración; ninguna aplicación había sido sustituida. [Intento inicial](prepare-attempt1.log), [preparación aprobada](prepare2.log).

El primer arnés posterior aprobó las 29 comprobaciones HTTP, pero WSS falló antes del handshake por un certificado raíz ausente en el Python local. Se configuró el bundle CA utilizado por Requests y se repitió el recorrido completo con verificación TLS activa. No se cambió el certificado del servidor ni se usó `verify=False`/`CERT_NONE`. [Arnés original](verify_http-attempt1.py), [fallo](https-after-attempt1.log), [repetición](https-after.log).

Las copias públicas de los arneses registran el código ejecutado. Para repetir desde la raíz del repositorio, se colocan en `.local/deploy-optimization-20261112/`; requieren el entorno Python/Playwright existente y el fichero privado de cuentas de demostración, excluido de esta evidencia:

```sh
PYTHONPATH=apps/services apps/services/.venv/bin/python .local/deploy-optimization-20261112/verify_http.py after
node .local/deploy-optimization-20261112/verify_browser.cjs
```

Clave temporal OS Login retirada a las **18:21:19 UTC**; claves anteriores conservadas y clave privada temporal local eliminada. [Limpieza](ssh-cleanup.json). No se ejecutaron nuevas pruebas de carga, fallos inducidos ni operaciones clínicas en GCP; la regresión funcional extensa corresponde al laboratorio previo.
