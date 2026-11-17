# GCS y adaptadores nativos — 16/11/2026

**Android e iPhone aprobaron** el camino real `MobileRepository → Ktor OkHttp/Darwin → JSON de Documentos → PUT HTTPS firmado GCS → verificación`. Cada plataforma cargó una copia nueva de la misma muestra JPEG sintética de 289.695 bytes. Los [recibos](RECIBOS-GCS.json) correlacionan VERIFIED/CLEAN, hash, generación, dos eventos en Auditoría SQL/Mongo y revocación de la familia técnica exacta tanto en SQL como en Redis.

Cada cliente nativo hizo además un GET **sin firma** del mismo objeto y generación: ambos recibieron HTTP 403 con TLS normal. El oráculo SDK descargó esa generación y comprobó el hash. Tras inspeccionar sus metadatos, se eliminó solo la generación nueva propia con `if_generation_match`. No se tocaron objetos históricos, IAM ni configuración del bucket. No se acredita vencimiento físico del soft-delete.

## Privacidad y política nativa

ADC no pudo consultar los metadatos del bucket: `storage.buckets.get` devolvió 403. Se conserva ese límite. Una lectura separada de raíz con una identidad ya autorizada observó `public_access_prevention=enforced`, acceso uniforme activo, metageneración 2 y soft-delete de 604.800 segundos. Su recibo CLI no informó retención, versionado ni hold predeterminado; no se inventan valores. Los campos de hold/retención ausentes en los objetos propios permanecen `null` en los recibos.

La negativa anónima acredita estos dos objetos, sin sustituir la lectura de política ni extender por sí sola el resultado a todos los prefijos. La conservación de la aplicación y la política del bucket son controles separados. No se supone un plazo legal.

## Ejecución y cierre

Android usó el mismo APK Lab y el APK de pruebas privado ya compilados para E2E-B. El preflight comprobó sus hashes y la ausencia de sesión, diario, cola, respaldos y fixture anteriores; el caso no abrió Activity ni capturó cámara/QR/GPS. La [instrumentación GCS](instrumentacion-gcs-android.txt) aprobó un caso. La lease temporal se consumió por archivo privado de un solo uso y se retiraron sus archivos propios. Los almacenes del producto siguieron ausentes.

En iPhone se compiló un host temporal privado con la misma identidad Lab, CA, origen y grupos Keychain. El puente ejecutó las clases reales de repositorio/sesión y el motor Darwin con credenciales técnicas en memoria. Los tokens estuvieron temporalmente en un recurso privado del bundle; el host no abrió Keychain ni los diarios del producto. El usuario confirmó «transferencia verificada y sesión cerrada» y se recuperó el recibo nativo. Después se restauró Lab distribuible como actualización sin desinstalar ni tocar la app normal, y se retiró la lease de la copia local privada. El usuario confirmó que Lab volvió a su cuenta de donante tras la restauración, sin pedirle otra contraseña.

El primer arranque de compilación privada falló por especificar fingerprint como identidad de firma automática. Se corrigió a `Apple Development` y se cotejó el certificado efectivo existente. La compilación posterior aprobó; dos verificaciones auxiliares se corrigieron sin recompilar: prefijo opcional de `codesign` y ubicación del framework estático. El perfil observado vence el 21/11 a las 18:32:33 UTC; no cubre todavía el 23. Ningún host, APK de pruebas, lease, contraseña ni URL firmada se publica aquí.

## Permisos y ciclo de vida

Los [recibos de permisos](PERMISOS.json) acreditan callbacks iOS con Cámara/Localización denegadas: sin bytes ni coordenadas. El usuario confirmó ambos mensajes. Se restablecieron y observaron los permisos originales 3/4 —cámara autorizada y ubicación al usar la aplicación—. Ir a Inicio con la cámara abierta canceló la captura sin foto; el callback y la confirmación humana coinciden.

BGAppRefresh pasó de cero a una solicitud pendiente a las 02:43:44 UTC. No se observó callback hasta el corte de 90 segundos ni en la copia posterior. La copia única terminó a las 02:45:45 UTC; el recibo distingue esa hora del corte 02:45:14. El observador privado no ejecutó la cola del producto y no se simuló una oportunidad del sistema. Se acredita programación observada, no ejecución garantizada en segundo plano.

Android aprobó las [dos negativas precompiladas](instrumentacion-permisos-android.txt): permiso de cámara denegado sin lector/código y ubicación denegada sin punto. Se restauraron los grants originales. Android API30 no implementa el comando auxiliar para limpiar flags: ese fallo ocurrió antes de instrumentar y se conserva como preparación del arnés. La ejecución aceptada no usó reset global ni `pm clear`; permaneció el historial `USER_SET=true`, con `USER_FIXED=false`, documentado antes/después. No se declara estado de flags idéntico.

## Alcance

Estas pruebas acreditan transferencia por los adaptadores nativos, privacidad de los objetos propios y los negativos/cancelación descritos. El host iOS es privado y no representa una nueva inspección visual de la interfaz distribuible. No se repitieron los positivos anteriores de cámara, QR, GPS, agenda o sincronización. Alta preliminar Android y aceptación completa de etapa04 continúan separadas. Los [hashes](FUENTES.json) fijan fuentes y recibos; los identificadores de sesión y secretos permanecen fuera de esta evidencia pública.
