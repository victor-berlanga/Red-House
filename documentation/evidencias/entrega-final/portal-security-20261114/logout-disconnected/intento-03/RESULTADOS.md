# B03: logout durante caída y recuperación autorizada

**1/1 aprobado en 249,836 s**, commit `3cd5a1b` y arnés S2. Es un intento nuevo; B01/B02 fallidos se conservan. No se repitió I06-07: HTTP permaneció igual y su regresión anterior sigue separada.

Dos sesiones reales de TRANSPORT; una cerró sesión mientras ambas réplicas de Transporte estaban detenidas, con la red del portal disponible. SQL/Redis: una familia revocada y otra activa; un LOGOUT, revocación web y auditoría únicos. Al restaurar B, un socket nuevo autenticado/suscrito de la cuenta autorizada abrió en el mismo documento. El nuevo publicador obtuvo ACK `PERSISTED_SQL` para puntos 2/3. La cuenta revocada siguió en login sin mapa/historial privado. Después volvió A y ambas réplicas terminaron live/ready 200.

Traslado sintético: `8cbb13e6-cbae-4b48-9a07-8ba583e58781`.

| Cursor | event_id igual en ACK / SQL / Mongo |
| --- | --- |
| 1 | `eb91914a-0a0e-4313-878c-fd826007de77` |
| 2 | `874d1d5d-bff0-4025-a4b4-c59a2e28b370` |
| 3 | `2e1db87d-f2cc-4054-a4fb-f8714fb4ef0b` |

Mongo real: `events.metadata.position`; tres puntos únicos y outbox pendiente 0. Se mantuvo la identidad del documento y no hubo filas duplicadas. [Runtime](portal-gateway-logout_disconnected/runtime.json), [navegador](portal-gateway-logout_disconnected/browser.json), [JUnit](junit.xml), [comando y hashes](command.json), [revisión/cierre](review.json).

Se inspeccionaron [mapa autorizado final](portal-gateway-logout_disconnected/security-06-authorized-both-restored.png) y [sesión revocada en login](portal-gateway-logout_disconnected/security-05-revoked-stays-private.png). El mapa indica En vivo/SIMULADO y cartografía no disponible. Mismas coordenadas sintéticas: identidad/reconexión, no desplazamiento físico. 1395 huellas iguales antes/después; procesos propios cerrados y ventana devuelta a dirección. [Entorno efímero asociado](environment-link.json), conservado sin borrar.

Límites previos intactos: TESTING/cuotas ampliadas, certificado efímero/SPKI específico, WSGI, OSM bloqueado; sin aceptación de MFA, CA del sistema, cartografía, GPS, capacidad ni GCP. Cambio de rol y revocación de asignación permanecen pendientes; I06-08 y etapa 06 no se cierran. Publicación de dos fuentes de proxy preparada solo localmente; Nginx remoto 1.28/configuración efectiva y reload siguen pendientes.
