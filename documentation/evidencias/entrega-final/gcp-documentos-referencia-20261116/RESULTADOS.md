# Documentos y referencia publicados en GCP — 16/11/2026

**Publicación validada y acceso temporal cerrado.** VM exacta: `sistemas-integracion-01/red-house/me-central1-a`, ID `2861822465669755197`, IP `34.18.186.116`. Recibos finales del 17/11 UTC, fecha local Monterrey 16/11. [Despliegue y cinco huellas](deployment.json): 30 contenedores saludables, 27 sin cambios; dos imágenes derivadas actualizan únicamente Documentos A/B y web. [Bases e imágenes finales](images.json).

El lote contiene `ms_documentos/local_objects.py` y cuatro fuentes web: `routes/common.py`, `routes/requests.py`, `presentation.py`, `routes/quality.py`. Permite reintentar carga LOCAL del mismo documento MISSING conservando autorización/inmutabilidad; mantiene referencias de negocio en listado/CSV, etiqueta la constancia y eventos, y selecciona Órganos para destino de órgano. **LOCAL, monolith y esquema 21 conservados**, sin migración, restauración, cambios nginx/IAM ni nueva infraestructura. El rollback preparado cambia código/imágenes y conserva datos; no se ejecutó. No representa el HEAD completo.

El [gate local](local-release-gate.json) enlaza las cinco huellas con [cuatro casos LOCAL/I06-08](../portal-i06-08-local-20261116/RESULTADOS.md) y [dos relecturas Chrome](../portal-referencia-etiquetas-20261116/RESULTADOS.md). Distingue cierre de procesos del fixture aislado y cierre SQL/Redis de las familias propias de Chrome; no atribuye al primero revocación de todas sus familias. No reutiliza la aceptación XML anterior para aprobar este lote.

Después del release, [12 controles protegidos JSON/XML](protected.json) aprobaron: diez respuestas 200, dos 401 esperados tras revocar la única familia propia. Identidad y listas de exportación Documentos consultadas en ambas réplicas; familia confirmada revocada en SQL y ausente en Redis. Sin operaciones de negocio. No se repitió carga, archivo clínico ni relectura Chrome en producción.

| Fase | Exit | Duración |
|---|---:|---:|
| Preflight | 0 | 24,132 s |
| Preparación de dos imágenes | 0 | 59,570 s |
| Release de tres contenedores | 0 | 92,032 s |
| Primer probe protegido, credencial obsoleta | 1 | 21,706 s |
| Conciliación del 401 sin autenticar | 0 | 16,357 s |
| Probe protegido con credencial vigente | 0 | 23,204 s |
| Primer finish, dependencia host ausente | 1 | 16,493 s |
| Finish mediante biblioteca estándar | 0 | 27,109 s |
| Retirada de acceso temporal | 0 | 7,261 s |

[Recibos de fases](phases.json) y [fallos preservados](preserved-failures.json). El primer login usó una credencial obsoleta y recibió 401: cero familias nuevas, sin negocio. Al preparar su corrección, una selección local trató una lista de objetos de cuenta como lista de nombres; falló antes de enviar HTTP/SSH. La conciliación comprobó sesiones idénticas y archivó tres recibos con hashes. Se utilizó después la contraseña de la rotación ya confirmada del 11/11, solo por stdin; no se restableció ni adivinó ninguna contraseña y no se reconstruyeron imágenes.

El primer finish falló en `deploy.py:292`, `ModuleNotFoundError` al importar requests en Python host, antes de HTTP. Salud/login independientes ya devolvían 200. El companion revisado `finish_stdlib.py`, SHA-256 `c8adbade6969948117eb8ec1c36533fb6824198c8d3c4292fd3569edd4810639`, reutilizó destino, paquete, gate, estado y proof exactos; sustituyó únicamente el cliente HTTP por urllib con CA predeterminada, sin proxies/redirecciones, timeout de 15 s y cuerpo máximo de 2 MiB. No se instaló requests ni se modificaron paquete sellado, producto o dependencias.

[Validación pública final](public-validation.json): dos rondas separadas cinco segundos, `/health/live` y `/login` 200, sin mantenimiento, TLS/IP verificados. Certificado observado hasta **21/11/2026 15:14:23 UTC**; temporizador activo/habilitado y último servicio exitoso. No cubre todavía el 23: debe comprobarse la renovación antes de entrega, sin convertir el temporizador en prueba de vigencia futura.

[Cierre OSLogin](access-cleanup.json): clave temporal propia retirada, dos anteriores conservadas y privada local eliminada. El adaptador privado añadió `action=finish-stdlib` requerido por el helper y hash del validation original, sin modificar ese recibo. [Huellas de originales privados](private-receipt-hashes.json); se omiten credenciales, SIDs, factores, cookies, URLs firmadas y configuración secreta. No hubo nuevas acciones remotas al preparar esta evidencia. Las etapas 06/07 y el pendiente UX del aviso de mosaicos conservan sus límites.
