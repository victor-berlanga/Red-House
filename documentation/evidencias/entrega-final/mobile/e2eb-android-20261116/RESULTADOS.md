# Tramo Android de E2E-B — 16/11/2026

El mismo órgano, reserva y traslado preparados desde Qt avanzaron por la interfaz Android: `PLANNED → PREPARED → COLLECTED → IN_TRANSIT → DELIVERED`. OPERADOR preparó la unidad; TRANSPORTISTA realizó recolección, tránsito y entrega con sello y contrapartes autorizadas. Las cuatro transiciones ocurrieron una sola vez. Dos lecturas ópticas se aceptaron, una para cada entrega de custodia. La recepción institucional `ACCEPTED` queda para Qt.

El [recibo sanitizado](RECIBO.json) acredita versión/secuencia 5, vínculo original conservado, `inventory_pending=false`, seis eventos coincidentes en Auditoría SQL/Mongo y tres familias técnicas propias revocadas en SQL y ausentes en Redis. El AVD cerró con salida 0, conservando datos. El servidor compartido siguió activo para la recepción de escritorio. Ninguna escritura de negocio se realizó desde el oráculo.

Dirección inspeccionó la [captura Android original](entregado.png): estado «Entregado» legible y mapa regional. La pantalla dice expresamente que no recibió ubicación; este tramo no acredita una nueva captura GPS. La imagen no fue recortada ni editada y `FLAG_SECURE` permaneció activo.

## Intento inicial y continuación dirigida

La [instrumentación original](instrumentacion-inicial.txt) **falló** después de confirmar PREPARED: agotó 90 segundos esperando la verificación del QR. Su duración informada fue 152,028 segundos. El oráculo posterior confirmó PREPARED, cero lecturas aceptadas y cierre de las dos familias técnicas iniciales. Este resultado no se convierte en una prueba JUnit aprobada.

La inspección real del lector mostró el póster virtual recortado y parcialmente tapado por la mesa, además de un aviso del emulador. Se corrigió únicamente el encuadre de la cámara, conservando el mismo PNG/UUID, producto y traslado. Los cambios del modelo físico no se reflejaron inmediatamente en el preview activo; la reapertura dirigida aplicó la pose y ZXing informó lectura. Dirección inspeccionó el [QR completo en el lector nativo](qr-encuadrado.png) antes de continuar. La captura conserva el PNG sintético original proyectado en la escena; no contiene una credencial.

La continuación utilizó la UI nativa mediante controles de accesibilidad y la misma sesión del transportista. No se repitieron PREPARED ni la suite. Antes de confirmar recolección se cotejó el sello completo; un timeout del proceso de teclado había dejado un prefijo y se completó solo el sufijo faltante. La lectura adicional previa a DELIVERED fue la segunda lectura exigida por la custodia. El cierre final verificó las tres familias técnicas creadas por ambas fases.

## Preparación conservada y límites

La compilación del APK de pruebas terminó en 2 min 59 s. Un control posterior detectó `assets/lab.json` heredado: el original quedó privado y no se instaló. Una copia derivada eliminó exclusivamente esa entrada; 119 entradas sin firma permanecieron idénticas. Se verificaron alineación, firma y certificado debug existente. El fixture se entregó por archivo privado de un solo uso; el cleanup solo elimina un archivo reclamado por ese intento. El APK de producto permaneció idéntico al lote preliminar/GCS.

Se conservan también el paquete gRPC externo incompleto, su reparación privada desde el wheel oficial 1.68.1 ya cacheado, el bloqueo automático previo a la autorización explícita del usuario y los fallos iniciales de lectura del árbol/selector durante el diagnóstico. No hubo nuevas dependencias de producto, SDK, claves ni renderer. Los [hashes](FUENTES.json) fijan prueba, preflight, host y captura.

Esta evidencia cubre el tramo Android de la cadena sintética compartida. No acredita recepción Qt, transferencia GCS nativa, permisos negativos nuevos, alta preliminar nativa ni cierre total de etapa04.
