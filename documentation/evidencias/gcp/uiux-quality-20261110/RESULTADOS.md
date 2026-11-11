# Corrección de calidad visual publicada — 10/11/2026

Autorización explícita: **«Publicala»**, posterior a la entrega local y sus límites. Publicada la corrección **web** en [Red House](https://34.18.186.116), VM existente `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`. La VM permanece encendida.

## Publicación y comprobación

- Imagen: **`redhouse/web:uiux-quality-20261110`**, ID `sha256:6c84aabf40495db2b2feb5864bfb62bf64d58bb7982169107d5ffe23e9efced7`.
- Veinte archivos de presentación: catorce modificados y seis nuevos. Los hashes remotos anteriores coincidieron con la copia inicial de la revisión. [Manifiesto](source-manifest.json).
- Capa construida sobre la imagen web vigente, sin red ni instalación de dependencias. Hashes del paquete y sintaxis de todas las plantillas Jinja comprobados dentro de la imagen antes de sustituir el servicio.
- **30 contenedores activos sanos**; los otros **29** conservan ID, imagen y estado. Solo se recreó web. No hubo migraciones, cambios de microservicios, cargas de datos ni escrituras de negocio. Se generan las sesiones y auditoría normales de comprobación. [Runtime antes/después](runtime.json), [ejecución](deploy.log).
- Chrome real sobre HTTPS con TLS verificado: login/logout de donante y operador, siete rutas a **1440 y 320 CSS px**, catorce vistas sin desbordamiento y cero errores JavaScript. Campañas, notificaciones, documentos, citas, inventario, traslados y conservación respondieron 200. [Verificación posterior](browser-after.json).
- Vista rápida, tooltip por foco, cierre con Escape y retorno del foco comprobados; detalle completo accesible desde el nombre. Formularios de lectura conservan CSRF e idempotencia; no se enviaron reconocimientos de avisos ni operaciones clínicas.
- Los ocho recursos estáticos incluidos coinciden con los SHA locales y se entregan con `Cache-Control: no-cache`. Selectores de Documentos con altura real de 44 px en ambos anchos.

## Capturas reales del despliegue

La comparación utiliza la misma cuenta de demostración, registros existentes y viewport **1440×1000**, sin cambiar el zoom. Estas capturas proceden del portal privado GCP, no de fixtures. [Mediciones](comparison.json), [comprobación anterior](browser-before.json).

| Pantalla | Antes | Después | Filas completas visibles |
| --- | --- | --- | --- |
| Campañas | [Captura](before-donor1-campanas-1440.png) | [Captura](after-donor1-campanas-1440.png) | 5 → 11; primera fila 93,89 → 56,5 px. |
| Notificaciones | [Captura](before-donor1-notificaciones-1440.png) | [Captura](after-donor1-notificaciones-1440.png) | 3 → 11; primera fila 128,73 → 56,5 px. |
| Documentos | [Captura](before-donor1-documentos-1440.png) | [Captura](after-donor1-documentos-1440.png) | Secuencia con espacio interior y ancho contenido. |
| Acceso | [Captura](before-login.png) | [Captura](after-login.png) | Ayudas iniciales simplificadas; MFA y recuperación conservados. |
| Inventario | [Captura](before-operator1-inventario-1440.png) | [Captura](after-operator1-inventario-1440.png) | Patrón de acciones compartido. |

Compacto: [avisos](after-donor1-notificaciones-320.png), [documentos](after-donor1-documentos-320.png), [inventario](after-operator1-inventario-320.png). También se conservan capturas de citas, traslados y conservación.

## Respaldo y reversión

Respaldo en `/opt/redhouse/.local/deploy-uiux-quality-20261110`: fuentes anteriores, manifiestos, override original de Compose, runtime y script de reversión. Imagen anterior preservada como `redhouse/web:uiux-quality-before-20261110`, ID `sha256:5d3e719ec1077cf6f3cc4b8bc05cd78e08d651ed64ff7fdf059378338405e064`.

El instalador revierte automáticamente ante fallo durante la sustitución. No fue necesario activarlo. Para una reversión manual expresamente decidida:

```sh
sudo python3 /opt/redhouse/.local/deploy-uiux-quality-20261110/rollback.py
```

Restaura los catorce archivos anteriores, retira los seis nuevos, recupera el override y recrea únicamente web con la imagen previa. No restaura bases de datos. [Instalador](deploy.py), [reversión](rollback.py), [verificador](verify.cjs).

La conexión utilizó una clave temporal OS Login con duración de una hora y comprobación estricta de host. Su retirada se registra en [cleanup.json](cleanup.json); las claves previas no se eliminan.

## Límites que permanecen

Esta publicación valida dos perfiles y consultas representativas; no cierra la matriz de todos los roles, estados o operaciones ni la aceptación integral del rediseño. El bloqueo del portal **local** no se modificó; las rutas anteriores sí se comprobaron en GCP. Safari real ya había sido revisado durante la fase local; esta comprobación de publicación usa Chrome.

Android/iOS no se actualizan mediante un despliegue web. El APK corregido sigue disponible en `.local/artifacts/mobile/RedHouse-uiux-quality-20261110-debug.apk`; iOS requiere compilar/instalar desde el proyecto. Permanecen los límites nativos documentados: omisión visual intermitente de Avisos en capturas de transporte y ensayo de rotación agotado a 412 dp/200 %. [Revisión local y pendientes](../../uiux/20261110-calidad/RESULTADOS.md). No se cierran las etapas 03/04/06 ni se implementa 05.
