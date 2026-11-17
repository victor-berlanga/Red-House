# Reintento LOCAL y dos combinaciones restantes I06-08 — 16/11/2026

**Cuatro casos aprobados en una ejecución aislada**, exit 0. [JUnit](junit.xml): 4 pruebas, cero fallos/errores/omisiones, 210,707 s. [Envoltorio](runner.json): 247,075 s incluyendo preparación y cierre; 1.421 fuentes idénticas [antes](sources-before.json) y [después](sources-after.json), 136 procesos propios observados, ninguno restante y ninguna limpieza forzada. No se ejecutó carga ni se accedió a GCP. Los tiempos son del ensayo, no SLA ni RTO.

| Caso JUnit | Resultado y alcance |
|---|---|
| `test_missing_retry_same_document_and_immutable_object[json]` | 26,549 s; preparación y metadatos por contrato JSON. |
| `test_missing_retry_same_document_and_immutable_object[xml]` | 2,293 s; preparación y metadatos por contrato XML/XSD. |
| `test_portal_gateway_remaining_security[assignment_disconnected]` | 78,395 s; retirada de responsabilidad durante caída total, recuperación del observador autorizado. |
| `test_portal_gateway_remaining_security[role_live_gateway]` | 102,715 s; cambio real de rol por formulario del mismo Nginx con mapa abierto. |

## Reintento del mismo documento LOCAL

En ambos formatos, verificar antes de cargar produjo 404 `object_missing`. Repetir preparación con la misma clave mantuvo el UUID y permitió cargar después de MISSING. Dos PUT simultáneos con la misma capacidad produjeron exactamente 201 y 412; la verificación dejó VERIFIED/CLEAN con generación y SHA correctos, sujeto de resultado y un evento FILE_MISSING más uno FILE_VERIFIED. Un PUT posterior a VERIFIED devolvió 409.

Las negativas cubrieron otra institución 403, otro actor del mismo tenant 409 y estados ERROR/REJECTED 409. Estas negativas de propietario usan capacidades recifradas por el arnés con la clave del fixture y el endpoint LOCAL mediante `test_client`; los estados prohibidos se preparan por SQL propietario. No se presentan como obtención de capacidades ajenas por un cliente real ni como dos recorridos Chrome documentales. La preparación y consulta de metadatos sí usan los contratos JSON/XML y servicios del fixture. El laboratorio arrancó ClamD real; los casos no simulan CLEAN.

## Asignación durante caída total

[Runtime](assignment_disconnected/runtime.json) y [navegador](assignment_disconnected/browser.json): el transportista vio el punto A. Se detuvieron las dos réplicas de rastreo y se retiró su relación autorizada mediante **fallo controlado de SQL propietario del fixture**, no una operación administrativa de reasignación aceptada. La preparación había creado una cuenta sintética y dispositivo/asignación válidos por API para el emisor sustituto, restaurando al responsable original antes de abrir Chrome.

Al restaurar, el anterior responsable recibió 403 también en snapshot e historial; la página limpió coordenada, mapa e historial y no recibió B/C. El coordinador autorizado recuperó un socket autenticado/suscrito del mismo documento y recibió A/B/C. Tres IDs/cursores únicos coinciden en ACK PERSISTED_SQL, SQL, Mongo y filas finales del mapa; outbox de posiciones pendiente cero. La renderización de A durante recuperación se registra de nuevo, sin duplicar filas persistidas o visibles. Ambas réplicas quedaron sanas. La relación original se restituyó exactamente, conservando incremento monotónico de versión de cuatro.

Capturas intactas: [responsable sin acceso](assignment_disconnected/remaining-responsibility-still-denied.png) y [observador autorizado](assignment_disconnected/remaining-authorized-three-points.png).

## Cambio de rol por el mismo Nginx

[Runtime](role_live_gateway/runtime.json) y [navegador](role_live_gateway/browser.json): un administrador envió el formulario real de rol por el mismo origen Nginx, respuesta 302. SQL confirmó incremento de versión uno, dos familias revocadas y un evento de auditoría. Con mapa abierto, la sesión afectada recibió 401 y volvió a login, sin conservar el documento privado ni recibir B/C. El coordinador mantuvo los tres puntos correlacionados SQL/Mongo/mapa. El rol original se restauró y ambas réplicas terminaron saludables.

Capturas intactas: [sesión retirada](role_live_gateway/remaining-role-still-denied.png) y [observador aún autorizado](role_live_gateway/remaining-authorized-three-points.png). Se inspeccionaron realmente las cuatro capturas; Dirección confirmó además ambas negativas.

## Cierre y límites

Los escenarios Chrome acreditan específicamente cierre SQL/Redis de sus dos y tres familias nuevas. El cierre global del fixture acredita aislamiento y fin de todos los procesos propios; **no acredita revocación SQL/Redis de cada familia creada por los cuatro casos**. Se conserva esa diferencia en el gate LOCAL. No hay procesos sobrevivientes ni limpieza forzada.

TESTING y cuotas 100000 son la política previa del fixture, no aumentos para esta ejecución; no acredita MFA ni capacidad. Python valida el certificado efímero explícito; Chrome usa excepción SPKI acotada, no confianza CA del sistema. Nginx/WSS son reales, listeners loopback, WSGI de prueba, coordenadas sintéticas coincidentes y mosaicos OSM bloqueados. No demuestra movimiento GPS, rutas viales ni latencia física; las medidas conservadas son recepción–mapa por punto, incluido replay.

**Pendiente UX menor:** tras retirar asignación, el aviso genérico de mosaicos dice «Se conserva el último dato recibido» aunque la coordenada/historial ya fueron borrados y muestran Acceso terminado. No se observó fuga; queda como ajuste de presentación final, sin ampliar el payload ni repetir estos casos.

Los dos recorridos cubren las combinaciones exactas que faltaban en el [corte I06-08 del 14/11](../portal-security-20261114/RESULTADOS.md): rol por el mismo gateway y asignación durante caída total. Se componen con A/C/D y B03, cuyos fallos/versiones y límites permanecen separados; no se cuentan como una nueva suite conjunta ni se repiten I06-07 o los demás positivos. Esta aceptación local no cierra las etapas 06/07 ni acredita cortes productivos. El paquete GCP de cinco fuentes dispone ahora de evidencia local habilitante, pero aquí no se ejecutó publicación.
