# Recepción y cierre documental E2E-A — 17/11/2026

## Alcance y aceptación

Misma unidad sintética RBC O+ `7e153323-64b5-481e-80ef-1a23e0bb7f00` y traslado `a42353cb-b9a0-4bfe-b127-8eb8a5f9fc19` previamente entregado desde Android. La población y los tiempos originales se conservaron. Recepción y destino ocurrieron antes de la caducidad real del 17/11 a las 19:50:41 UTC; no se modificó su vigencia.

Qt, mediante XML y las pantallas reales, registró una única recepción ACCEPTED versión 7 con `operator2`. `medical2`, con MFA y reautenticación, registró un único destino DISCARDED documental de esta unidad de ensayo. No se registró una transfusión ni se atribuye autorización clínica real a la prueba.

Ambos procesos terminaron con salida 0. Cada uno cerró su propia familia técnica en SQL/Redis. Dirección abrió y revisó visualmente [recepción](recepcion-qt.png) y [destino](destino-qt.png): identificación, sello, referencia, confirmaciones y acciones legibles. El motivo largo del destino se desplaza dentro del campo; la captura no muestra todo su contenido.

El [oráculo de solo lectura](oracle-summary.json) aprobó **39 controles**, 18 eventos fuente coincidentes con Auditoría SQL y MongoDB y 17 destinatarios de avisos esperados/encontrados. Confirmó solicitud CLOSED, reserva RECEIVED, traslado ACCEPTED sin operación de inventario pendiente, unidad WITHDRAWN, destino único y actores/secuencias correctos. Conservó la evidencia anterior de foto GCS VERIFIED/CLEAN y del único GPS Android simulado mediante recibos y conciliación histórica; no volvió a publicar posición, cargar foto ni escanear QR.

No hubo lecturas de conservación térmica en este caso (cero registros); no se acredita temperatura por ausencia de excursiones. Los avisos son persistencia de bandeja, no push real ni recepción humana.

## Ejecución y límites

Laboratorio privado conservado `/private/tmp/red-house-ms-tests-kojcusww`, esquema 21, ACADEMIC y TESTING=False; servidor LOCAL, ClamD real, MFA y reautenticación activas. El primer arranque `run-07` terminó antes de iniciar motores: el sandbox impidió comprobar el puerto y el helper lo reportó ocupado. Una comprobación con permisos del host no encontró listener y confirmó la misma IP; `run-08` inició sin intervenir procesos ajenos.

Fuentes web integran únicamente las etiquetas revisadas de seguimiento: iPhone reconocido, `simulated=true` visible y aviso de cartografía coherente. JavaScript coincide con SHA-256 `64c9986e24385e498507791e6160e63eb358cdaa842ab0ad75c8d7a0a1c81503`; sintaxis aprobada. Los siete casos dirigidos y la inspección visual controlada anteriores corresponden al mismo candidato. Publicación GCP pendiente.

Recibos privados reproducibles: `.local/artifacts/e2ea-preparacion-20261116/cierre-final/{recepcion-run-01,destino-run-01,oracle-run-01}`; servidor `.local/artifacts/e2eb-preserved-20261116/run-08-e2ea-local`. Las credenciales, factores MFA, diarios y configuraciones permanecen privados.

## Consulta final web y cierre

Chrome real aprobó cinco GET de negocio con `medical2`: [unidad retirada](01-recurso.png), [destino documental](02-destino.png), [traslado aceptado](03-traslado.png), [solicitud cerrada](04-solicitud.png) y [seguimiento finalizado](05-seguimiento-terminal.png). Dirección abrió las cinco capturas: sección sanguínea correcta, estados coherentes, secuencia de custodia y marcador/historial visibles. El formulario de corrección de destino se consultó sin enviarlo; no acredita lectura de todos los campos del destino histórico.

El mapa conserva el mismo evento/cursor 1 en FINALIZED, etiquetado «Teléfono Android · SIMULADO», sin nueva conexión WSS ni publicación GPS. No representa latencia en vivo. HTTPS validó CA y origen; negocio y fuentes permanecieron iguales; la familia propia quedó cerrada SQL/Redis. Recibo privado `cierre-final/web-run-01/receipt.json`, salida 0. No se capturaron contraseñas ni OTP.

El servidor LOCAL cerró ordenadamente con salida 0: tres procesos de infraestructura propios terminados, configuración/fuentes originales iguales y archivos/población conservados. Su salida conserva un aviso `mfa_verification_rejected` anterior al acceso exitoso; no se desactivó MFA ni se atribuye una causa no registrada. Ninguna nueva imagen se cargó a GCS durante este cierre.

Queda acreditado este recorrido Android→Qt→web por evidencia compuesta. No acredita E2E-A de iPhone, Windows, carga ni cierre íntegro de las etapas 04–07.
