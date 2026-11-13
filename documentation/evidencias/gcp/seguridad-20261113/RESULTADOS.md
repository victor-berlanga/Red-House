# Seguridad, identidad operativa y rutas de archivos en GCP

Publicado el servidor de **`1f02c0cc7e3e13c9d7593e659fbd407165ef9823`** el 13/11/2026 en el proyecto **sistemas-integracion-01**, VM **red-house**, ID `2861822465669755197`, zona **me-central1-a**, origen **https://34.18.186.116**. El despliegue verificó proyecto, nombre e ID mediante metadata de la propia VM. No publicó los cambios de clientes que continuaban en desarrollo.

## Cambio y criterios comprobados

- 67 archivos tomados de blobs Git, sobre la publicación `53844ab`; 13 imágenes construidas sin red ni dependencias nuevas. SHA-256 del payload: `57b836b3b7747958a5d4cc05ea0a4a3efea7456e7b5db3154209577d535dba0e`.
- Reautenticación ligada al comando, sesión, permiso, cuerpo y clave idempotente; endpoint anterior retirado con 410. Se restringió DELETE de `access_inventario.operations` para `rh_inventario`. No hubo migración de esquema ni modificación de registros de negocio por el despliegue.
- Identidad operativa del transportista asignado disponible mediante la proyección autorizada de Transporte. La consulta conserva auditoría; el nombre de cuenta no acredita identidad legal.
- `/storage/v1/objects/` llega a Documentos; `/portal-storage/v1/objects/` llega al backend modular del portal. El almacenamiento local sigue activo; GCS histórico permanece disponible según los permisos y estados previos.
- Se actualizaron secuencialmente 24 réplicas API y web. Gateway, PostgreSQL, MongoDB, Redis y ClamAV conservaron contenedor e imagen. Treinta contenedores terminaron sanos; 67 hashes de fuentes coinciden y el esquema sigue en 19.
- La configuración efectiva se comparó completa y solo cambiaron las imágenes previstas; las configuraciones de aplicación conservaron sus valores. Nginx recibió únicamente las rutas generadas y el mantenimiento temporal. La huella de las 39 referencias de archivo —proveedor, ruta, generación y SHA-256— permaneció idéntica. No se reanalizó ni modificó GCS histórico.

## Publicación y respaldo

Respaldo PostgreSQL de 40.116.678 bytes, SHA-256 `503b34f69c0968ce083b87065e9f588f9466ff7fcb0cbf5e26abf790a1f1d50c`, con catálogo validado por `pg_restore --list`. **No se restauró esta copia**. El respaldo no es una instantánea coordinada de PostgreSQL, MongoDB, Redis y archivos. Configuraciones, fuentes e imágenes anteriores se conservaron en la VM; sus contenidos privados no se incorporan al repositorio.

Nginx rechazó mutaciones HTTP con 503 desde aproximadamente **20:50:49 hasta 21:03:58 UTC**, unos 13 min 9 s. Se esperaron al menos 125 s antes de publicar para agotar los retos/pruebas anteriores. La configuración se validó antes de aplicarla, preservando el inode del archivo montado, y se comprobó continuidad del bloqueo entre réplicas. Fue un bloqueo de métodos HTTP: **no detuvo workers ni mensajes de conexiones WSS existentes** y no se presenta como ausencia global de escritores.

Identidad se actualizó primero. La reapertura exigió las dos réplicas listas, lecturas autorizadas y comprobaciones del nuevo protocolo. La recuperación prevista durante el mantenimiento avanza hacia el protocolo nuevo; no vuelve a habilitar pruebas genéricas antiguas. No se ejecutó reversión ni restauración de producción.

## Verificación y fallos conservados

1. **40 comprobaciones internas aprobadas**: salud de las 24 réplicas API; login/perfil, 410 del endpoint antiguo, rechazo del reto inválido, lecturas autorizadas y revocación de las sesiones creadas para ambas réplicas. Transporte HTTP privado; no sustituye pruebas TLS.
2. **39 comprobaciones públicas HTTPS aprobadas**, con verificación de certificado: salud, portal por perfiles, sesiones, JSON/XML, agenda y próximas citas, evidencia visible y denegación de inventario a donante. WSS JSON/XML autenticó y respondió heartbeat; no publicó ubicación.
3. **21 comprobaciones públicas adicionales aprobadas**: proyección del transportista JSON/XML concordante con identidad/versión del traslado; descarga de los dos PDF sintéticos ya existentes por API y portal, SHA-256 y `no-store`; rechazo de las capacidades después de revocar cada sesión propia. No se crearon archivos ni se confirmaron movimientos físicos. No se detuvieron servicios productivos para demostrar autonomía; esa prueba corresponde al laboratorio enlazado abajo.

El primer arnés de rutas falló tras cinco comprobaciones porque su expresión regular no admitía el padding `=` legítimo de Fernet. La API emitió acceso correctamente, pero el arnés se detuvo antes de descargar. Se conservaron script y reporte iniciales, se corrigió solo la validación del arnés y se repitió con los mismos archivos. No se suman ambos intentos como una suite única.

Los dos primeros preflight contaron contenedores históricos de restauración detenidos; el segundo log está conservado. El primero solo quedó registrado en la traza de herramientas. Se corrigió la selección a contenedores activos, excluyendo tareas puntuales y exigiendo igualdad exacta con los servicios Compose esperados. El tercer preflight pasó. Los contenedores históricos no se eliminaron.

La clave temporal OS Login se retiró; se comprobó igualdad de las dos claves previas antes/después y se eliminó la clave privada temporal local. La VM permanece encendida para el equipo. No se publican credenciales, perfiles OS Login, dump, configuraciones privadas, tokens ni URLs de capacidad.

## Reproducción y límites

Los JSON y logs registran el resultado; `artifacts.sha256` identifica los archivos copiados. `procedimiento/` conserva los scripts exactos ejecutados. Los scripts públicos se ejecutaron desde `.local/deploy-sec-20261113/`, con la raíz del repositorio dos niveles arriba; no deben ejecutarse directamente desde esta carpeta documental. Requieren la configuración privada existente. El despliegue está fijado a esta VM y esta versión; no es un instalador genérico ni debe repetirse sobre otro estado sin preparar un nuevo preflight.

`publish.log` conserva los espacios al final de línea emitidos por Docker Compose. `git diff --check` los señaló durante el commit documental; no se alteraron los bytes ni el hash del log. Una excepción de atributo limitada a ese archivo omite únicamente esa comprobación de espacios.

Comandos locales de lectura utilizados:

```sh
PYTHONPATH=apps/services apps/services/.venv/bin/python .local/deploy-sec-20261113/verify_http.py security
apps/services/.venv/bin/python .local/deploy-sec-20261113/verify_routes.py
```

No acredita las nueve mutaciones críticas en producción, restauración de GCP, carga sostenida, funcionamiento físico de clientes, push de proveedor ni cierre de etapas 04–07. Las mutaciones y la independencia ante procesos detenidos se ensayaron con datos sintéticos: [seguridad/autonomía](../../entrega-final/reauth-20261113/RESULTADOS.md), [integración JSON/XML](../../entrega-final/reauth-20261113/integracion/README.md), [proyección nominal](../../entrega-final/transporte-nominal-20261113/README.md). La [recuperación coordinada](../../entrega-final/recuperacion-20261113/RESULTADOS.md) es un ensayo distinto, aislado, con límites propios.
