# Compilación XML protegida publicada en GCP — 16/11/2026

**Publicación validada y acceso temporal cerrado.** VM exacta: proyecto `sistemas-integracion-01`, instancia `red-house`, zona `me-central1-a`, ID `2861822465669755197`, IP `34.18.186.116`. Fecha local Monterrey: 16/11; recibos finales UTC: 17/11. Esta evidencia publica únicamente tres fuentes de servidor; no representa el HEAD completo ni cierra todas las etapas de entrega.

Se construyeron trece imágenes derivadas de las bases `server21` observadas y fijadas por ID, con permisos de directorios/archivos correctos y configuración de imagen conservada. Se actualizaron 25 aplicaciones; las cinco de infraestructura permanecieron iguales. Validación final: **30 saludables, esquema 21, backend monolítico y almacenamiento LOCAL**. Sin migración nueva, restauración de datos, dump adicional ni infraestructura nueva. El rollback preparado conserva datos/esquema 21 y cambia solo código/imágenes; no se ejecutó.

Las fuentes son `redhouse/codec.py`, `redhouse/xml_response.py` y `ms_transporte/tracking_contracts.py`, dentro de `apps/services/`. Los dos módulos comunes se incluyen en las trece imágenes; el módulo de Transporte, únicamente en Transporte y web. Hashes completos, bases/candidatas y alcance por imagen: [deployment.json](deployment.json) e [images.json](images.json). El candado por proceso protege construcción de esquemas, manteniendo validadores de petición, XSD, rechazo XXE y validación de respuestas. No cambia orden, autorización ni reglas de negocio.

La preparación comprobó las trece imágenes mediante pruebas frías ejecutadas con su usuario final: once imágenes tuvieron 144 intentos y Transporte/web 216, con los constructores que cada imagen empaqueta. Esas cantidades son intentos internos de contrato, no peticiones HTTP ni nuevos casos integrales. Las catorce pruebas puras y la incertidumbre del comparativo remoto están en [el expediente de la corrección](../carga-20261114/xml-compilation-lock-20261116/RESULTADOS.md).

Antes de release, Dirección verificó un **gate adicional** que une la carga HTTP12 del candado actual, mapas antes/después, hashes de las tres fuentes, manifiesto inmutable del paquete03 e IDs de las trece imágenes: [release-gate.json](release-gate.json). La [corrida local actual](../carga-20261114/xml-lock-http12-20261116/RESULTADOS.md) acredita doce usuarios, 1472 HTTP sin fallos y p95 máximo lectura/recorrido de 480/2000 ms. El campo `http_report_sha256` heredado de `validation.json` sigue apuntando a la carga anterior del parser aislado; no se reescribió el paquete para aparentar una captura posterior. La vinculación con la carga actual está explícitamente en este gate adicional, anterior al release.

Después del release aprobaron **40 controles protegidos JSON/XML por réplicas**: 30 respuestas 200, cuatro 403 esperados y seis 401 esperados tras revocación. Ocho solicitudes XML inválidas concurrentes, cuatro por réplica de Inventario, devolvieron 400 `invalid_body`; el oráculo SQL confirmó cero recursos y cero registros de idempotencia correspondientes. No hubo escrituras de negocio en esos probes. Las tres familias técnicas creadas quedaron revocadas. No se repitieron estos negativos para resolver el cierre público. [contracts.json](contracts.json) omite actores, claves, folios y correlaciones privadas.

| Fase observada | Resultado conservado | Duración |
|---|---|---:|
| Preflight del paquete03 | exit 0 | 72,998 s |
| Preparación de imágenes | recibo remoto 13/13 aprobado; transporte SSH local exit 255 | 794,862 s |
| Release | exit 0 | 231,321 s |
| Contratos y negativos | exit 0 | 44,680 s |
| Primer `finish` | exit 1, HTTP 503 público | 37,993 s |
| Segundo `finish`, sin repetir contratos | exit 0 | 66,322 s |
| Retirada del acceso temporal propio | exit 0 | 10,972 s |

La conexión SSH de preparación quedó abierta después de existir los trece recibos y de comprobar ausencia del proceso remoto de despliegue. Dirección cerró únicamente ese SSH local. El exit 255 permanece; no se sustituye por cero. El runner privado incorporó keepalive de 15 s y máximo tres faltas de respuesta para las fases posteriores; las imágenes y el paquete03 no cambiaron.

El primer `finish` falló con HTTPError 503 en `public_checks`, después de validar el estado interno y pasar por la restauración de nginx. No se conservaron URL/ronda del 503 ni evidencia suficiente para atribuir su causa. La señal de reload no prueba por sí sola una carrera; no se declara esa explicación ni se revirtió un despliegue sano. Un probe local posterior con urllib falló por confianza CA local; Dirección observó `SSLCertVerificationError` código 20, mientras el JSON conserva únicamente `URLError`. Ese intento tampoco se convierte en éxito.

La comprobación externa independiente con requests y validación CA normal aprobó dos rondas `/health/live` y `/login`, URL exacta, sin redirecciones/proxies ni cabecera de mantenimiento. Nunca se usó `verify=False`. Después se repitió **solo `finish` del paquete03 intacto**: revalidó fuentes, configuración, esquema, imágenes y recibo de contratos; dos rondas públicas adicionales devolvieron 200/200. [public-validation.json](public-validation.json) separa cada intento y conserva el fallo original con causa no establecida.

TLS final validó confianza e IP. Certificado observado hasta **21/11/2026 15:14:23 UTC**; no cubre aún el final del día de entrega del 23. Temporizador de renovación cargado, activo y habilitado; siguiente ejecución registrada 17/11 06:08:05 UTC y último servicio con resultado exitoso. Esta publicación no renovó el certificado. Debe comprobarse la renovación antes de la entrega; timer activo no equivale a vigencia futura acreditada.

El cierre de OSLogin confirma retirada de la única clave temporal propia, **dos claves anteriores conservadas** y eliminación de la clave privada local. También se comprobó ausencia de sus archivos privado/público. [access-cleanup.json](access-cleanup.json) no expone perfil, credenciales ni claves. Los originales privados se conservan; [private-receipt-hashes.json](private-receipt-hashes.json) permite cotejar sus huellas sin publicar configuración, logs internos ni secretos. No se ejecutaron motores o acciones remotas adicionales para redactar este expediente.
