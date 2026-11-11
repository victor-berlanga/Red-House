# Rediseño web publicado — 10/11/2026 (Monterrey)

Autorización: solicitud explícita «Subelo», posterior al rediseño local. Destino existente: `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`, **https://34.18.186.116**. La VM permanece encendida.

## Resultado

Publicado **`redhouse/web:uiux-20261110`**, exclusivamente nueve archivos de presentación. Backend conserva `mobile04-20261110` y esquema 18; no se ejecutaron migraciones, cargas de datos ni escrituras de negocio. Las sesiones y auditoría normales de verificación sí se generan. Android/iOS no se distribuyen mediante esta publicación web.

- Fuentes locales idénticas a las revisadas; fuentes remotas anteriores cotejadas con la línea base antes del rediseño. [Manifiesto](source-manifest.json).
- Imagen derivada de la imagen web vigente, con una capa de nueve archivos. Sin actualizar dependencias ni reconstruir microservicios. Hashes verificados dentro de la imagen antes de recrear web.
- **30 contenedores activos sanos**. Los otros **29** conservan ID, imagen y estado. Los contenedores históricos terminados se preservan. [Runtime](runtime.json).
- Regresión local de presentación aprobada: siete perfiles, navegación, avisos inciertos, estados y compilación de plantillas.
- Chrome sobre HTTPS real, TLS 1.3 verificado: acceso actualizado, CSS público con SHA-256 idéntico al local, login/logout donante y operador, paneles y grupos únicos, campañas/citas/inventario/traslados HTTP 200 y acceso directo al expediente. Cero errores JavaScript. [Recorrido](browser.json).
- Capturas reales del despliegue a 1440×1000: [acceso](login.png), [panel donante](donor1-panel.png), [citas](donor1-citas.png), [panel operador](operator1-panel.png), [inventario](operator1-inventario.png), [traslados](operator1-traslados.png). No son fixtures locales.

## Respaldo y reversión

Antes del cambio se guardaron los nueve archivos originales, el override original de Compose y los IDs de imágenes/contenedores en `/opt/redhouse/.local/deploy-uiux-20261110`. La imagen anterior conserva además la etiqueta `redhouse/web:uiux-before-20261110`. Respaldo limitado a presentación/configuración de imagen: no se necesitó restaurar ni alterar bases de datos.

El instalador revierte automáticamente ante fallo durante la sustitución. No se activó esa reversión. Para una reversión manual expresamente decidida:

```sh
sudo python3 /opt/redhouse/.local/deploy-uiux-20261110/rollback.py
```

El script restaura los nueve archivos y el override original, y recrea únicamente web con la imagen previa. No restaura bases. Copias revisables: [instalador](deploy.py), [reversión](rollback.py), [ejecución](deploy.log).

## Intentos y límites

La clave SSH habitual fue rechazada; se registró una clave temporal OS Login con TTL de dos horas para este despliegue. La retirada se documenta en `cleanup.json`.

El primer control previo contó también contenedores históricos de restauración terminados y rechazó el estado esperado de 30 activos. Se detuvo antes de modificar archivos. Se corrigió para comprobar salud de los activos y conservar identidad/estado de todos los demás. [Intento inicial](deploy-first.log).

La verificación cubre dos perfiles y consultas, no todos los flujos funcionales, accesibilidad completa, operaciones clínicas, GCS ni ejecución física móvil. La publicación no cierra los pendientes del rediseño ni las etapas 03/04/06. iOS requiere recompilar e instalar el proyecto actual por el usuario.
