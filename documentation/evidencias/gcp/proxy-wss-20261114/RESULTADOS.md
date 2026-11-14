# Proxy WSS publicado — 14 de noviembre de 2026

Publicado **`3cd5a1b`**, únicamente dos fuentes de proxy y su configuración Nginx generada. Destino comprobado: **sistemas-integracion-01 / red-house / me-central1-a**, VM **2861822465669755197**, `https://34.18.186.116`. Storage **LOCAL** conservado.

Nginx efectivo **1.28.3**, misma imagen `nginx:1.28-alpine`. Dos fuentes previas y configuración activa coincidieron exactamente con el baseline revisado. Candidato generado con JSON vacíos en staging; no se ejecutó `configure_public` sobre `.local/compose` habitual. Diff limitado al grupo/zona WSS, sus dos rutas y failover explícito. HTTP, TLS y almacenamiento conservados. [Preflight](preflight.json), [publicación y hashes](release.json), [manifiesto](manifest.json).

Backup: `/opt/redhouse/.local/proxy-wss-3cd5a1b-7vzfho9n/backup`. `nginx -t` pasó sobre candidato y activo dentro del mismo gateway. Escritura in situ con fsync; inode montado **35537734** antes/después. Reload señalado sin recrear contenedores. Treinta contenedores conservan ID/imagen y siguen healthy; veinte JSON/overrides conservan sus huellas. Web/Documentos permanecen LOCAL. Sin recursos, imágenes, migraciones ni cortes de réplicas.

| Smoke posterior | Resultado |
| --- | --- |
| GET público `/login` | 200 |
| Salud pública Transporte | 200 |
| Login técnico TRANSPORT | 200 |
| WSS nuevo JSON por gateway | 101 y `authenticated` |
| Logout de esa sesión | 200 |
| Reutilización de su token | 401 |

TLS público verificado normalmente por el cliente, sin excepción SPKI/SSL en este smoke. Credenciales solo en memoria/stdin del proceso propio; no se guardan en evidencia. No se crearon entidades de negocio ni se consultó un traslado. [Procedimiento previo](remote_preflight.py), [instalación, smoke y rollback preparado](remote_publish.py). No fue necesario rollback; no se ensayó una falla del rollback.

Incidencia de staging conservada: `docker cp` no pudo escribir en el rootfs readonly del contenedor. Se transfirió exclusivamente el candidato al tmpfs `/tmp` mediante stdin; luego `nginx -t` pasó. La configuración activa aún estaba intacta durante ese diagnóstico. [Registro](staging-transport-diagnosis.json). No fue un rechazo de sintaxis del producto.

Acceso OS Login propio TTL 15 minutos retirado; las **dos claves preexistentes** permanecen. Par temporal local borrado y candidato del contenedor retirado. Backup y reportes privados conservados. [Cleanup](access-cleanup.json).

[B03 local](../../entrega-final/portal-security-20261114/logout-disconnected/intento-03/RESULTADOS.md) aprobó 1/1 en 249,836 s y dirección aceptó sus dos capturas. No se repitió I06-07: HTTP quedó igual y conserva su prueba previa. El discriminante local 1.30.6 y B03 se separan de este smoke sobre 1.28.3. Aquí no se detuvieron réplicas ni se probaron recuperación productiva, carga o replay. Un segundo limita TCP, no todo el Upgrade; lectura de 75 s puede demorar un peer vivo sin cabeceras. No hay replay después de 101. Roles/asignación e I06-08 integral siguen abiertos.
