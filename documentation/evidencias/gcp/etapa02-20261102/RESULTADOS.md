# Publicación de etapa 02 en GCP — 02/11/2026

Autorización expresa: «Antes que nada, sube todo a gcp». Publicado en **https://34.18.186.116**, VM `red-house`, proyecto `sistemas-integracion-01`, zona `me-central1-a`. La VM estaba apagada; se encendió y queda disponible. No se creó otra VM ni se copiaron bases locales sobre las remotas.

## Versión y conservación

Release **0.4.4 / esquema 16**. Compatibilidad y Priorización/Geografía anuncian 0.4.4; los otros diez módulos mantienen su versión propia 0.4.1. Todas las imágenes de aplicación se reconstruyeron desde el árbol local actual y se etiquetaron 0.4.4. No se sustituyó el árbol por el antiguo main de GitHub. La comprobación compara versiones propias, hashes e IDs de imagen; una etiqueta por sí sola no acredita el contenido.

Paquete: **3.565 archivos**, 140.588.116 bytes, SHA-256 en `package.json`. Antes del empaquetado se cotejaron las 1.117 fuentes de la validación local. El paquete excluye secretos locales, ADC, claves SSH, entornos y `.local`. El catálogo original HLA se transfirió por separado, con SHA-256 verificado y montaje de solo lectura en las dos réplicas de Compatibilidad y en la web.

Se preservaron código, configuración e imágenes previas en `/opt/redhouse/.local/deploy-20261102`. Respaldo coordinado privado: `/opt/redhouse/.local/compose/backups/20261102T181525Z`. **Restauración real de PostgreSQL, MongoDB y Redis aprobada** en contenedores aislados antes de migrar. Se compararon 108 conjuntos SQL, contenido MongoDB, roles, permisos y Redis/TTL. Los respaldos no se descargaron ni versionaron.

Migración 13→16, repetida de forma idempotente. Comparación de las columnas históricas de 107 tablas del esquema de dominio: **106 idénticas**, solo `schema_migration` añadió las versiones previstas. No hubo diferencias inesperadas. Las columnas nuevas no reescriben resultados históricos; los registros y configuraciones permanecen. **73 campos/archivos de credenciales, claves y cuentas comparados dentro de la VM resultaron iguales**, sin mostrar sus valores.

`source-manifest.json` conserva el paquete inicial; `deployment-delta.json` documenta el único ajuste posterior del despliegue: valor predeterminado de etiquetas Compose 0.4.1→0.4.4. `source-manifest-final.json` identifica las fuentes cotejadas en el host y `runtime-final.json` los IDs de imágenes y salud. La documentación de cierre se sincroniza después y se identifica por separado; no cambia los binarios.

## Comprobaciones actuales

| Evidencia | Resultado |
|---|---|
| `backup-report.json` | Respaldo y restauración aislada aprobados; datos/permisos iguales |
| `data-preservation.json`, `data-before.json`, `data-after.json` | Historia conservada al migrar; única diferencia esperada en registro de migraciones |
| `configuration-preservation.json` | 73 campos/archivos sensibles conservados; valores redactados |
| `runtime-final.json` | **30 contenedores sanos**, 3.565 fuentes del host coincidentes; hashes de código en imágenes coincidentes; catálogo HLA idéntico en tres montajes |
| `health-final.json` | **24 consultas HTTPS**: liveness/readiness de los doce servicios, versiones propias correctas y dependencias disponibles |
| `api-final.json` | **28 respuestas JSON/XML** validadas con JSON Schema y XML/XSD; doce servicios y dos catálogos nuevos |
| `api-final.json` | Perfil/muestra/receptor/resultado HLA ficticios persistidos; `HLA00001` reconocido en 3.66.0, aprobación clínica falsa. Grafo público importado, ejecución y reproducción persistidas |
| `gcs-final.json` | Identidad adjunta de Compute Engine; PUT/GET firmados 200, descarga anónima 403, contenido idéntico y objeto temporal eliminado |
| `browser-final.json` | Chrome real contra HTTPS público: **8 comprobaciones** con MFA, cookie Secure, fuentes, HLA, completitud, ruta, perfiles e importación; recarga/persistencia; cero errores de consola/red |

Los conteos corresponden a comprobaciones de distinta naturaleza y no se suman como casos únicos. Los 110 casos locales anteriores siguen siendo evidencia local, no una suite ejecutada nuevamente en GCP. Los seis identificadores ficticios creados constan en `api-final.json`; no se modificaron expedientes anteriores para simular éxito. El resultado HLA sigue capturado, sin aprobación clínica automática. Navegador sin capturas, vídeo, HAR ni trazas.

## Incidencias conservadas

1. La clave SSH habitual era aceptada por el servidor, pero requería contraseña interactiva y el agente SSH no tenía identidad cargada. Se usó otra clave temporal OS Login con expiración de dos horas; la clave privada habitual no se modificó. Se retirará el acceso temporal al finalizar.
2. El primer comprobador de conservación esperaba `schema_migrations`, pero la tabla real se llama `schema_migration`. La migración ya había llegado a 16; el comprobador detuvo el arranque. Se corrigió el nombre, se repitió el migrador y se verificó conservación antes de arrancar. No fue una pérdida ni una restauración encima de datos reales.
3. `systemctl is-active` devolvió 3 durante el estado `activating`; se consultaron ActiveState/SubState para distinguir inicio de fallo.
4. El primer probe HTTPS exigía 0.4.4 para todos los módulos. Se corrigió para cotejar cada VERSION del código local; módulos sin cambio conservan 0.4.1. Se mantuvo la comprobación adicional de fuentes e imágenes.

Procedimientos ejecutados bajo `procedimiento/`; contienen rutas y verificaciones, nunca credenciales. El diagnóstico de conectividad temporal creado durante SSH se elimina al cerrar. Los errores y ajustes constan también en `deployment-events.json`.

## Operación y límites

`OPERATION_SCOPE=ACADEMIC`, laboratorio/órganos exigidos, MFA previo conservado y reautenticación en operaciones críticas. No se incorporó ninguna acreditación clínica ni se configuraron canales externos SMTP/push. Las fuentes HLA y viales conservan ediciones, hashes y límites. Tres trayectos urbanos públicos no equivalen a cobertura hospitalaria, tráfico medido ni GPS físico.

Este despliegue cierra la publicación y las comprobaciones GCP aquí descritas. No certifica reglas clínicas ni prueba GPS físico; este queda al final por instrucción del usuario. No se repitieron todos los flujos clínicos/documentales, WSS, carga sostenida, fallos de infraestructura ni la auditoría independiente completa de plataforma. GCS se verificó con el adaptador real de firma/privacidad; no se afirma un nuevo recorrido completo de documento HLA privado en nube.

Rollback: detener escritores; preservar cualquier cambio posterior en otro respaldo; restaurar en copia y comprobar los respaldos/configuración/imágenes previos. No bajar esquema con DROP ni reemplazar solo binarios frente a esquema incompatible. Conciliar las nuevas operaciones antes de cualquier restauración del servicio.


## Archivo de detalles — 04/11/2026

Los manifiestos extensos, capturas de estado Git y muestras HTTP de este expediente se conservan sin alterar sus bytes en [el archivo comprimido](../../archivo/detalles-20261104.tar.gz); el [índice](../../archivo/detalles-20261104.json) identifica cada ruta original, tamaño y SHA-256. Los resultados, JUnit e incidencias siguen visibles. Antes de ejecutar verificadores históricos que lean esos detalles, restaurar las rutas desde la raíz del repositorio con `tar -xzf documentation/evidencias/archivo/detalles-20261104.tar.gz`. Extraer en una carpeta temporal para una consulta sin escrituras en el repositorio. Los hashes históricos corresponden al corte original, no al árbol actual.
