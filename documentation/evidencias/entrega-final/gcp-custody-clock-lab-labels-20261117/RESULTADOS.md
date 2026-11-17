# Validación temporal de custodia y textos web publicados en GCP — 17/11/2026

La publicación acotada terminó **PASS** en `sistemas-integracion-01`, VM `red-house`, zona `me-central1-a`: **dos imágenes y tres contenedores actualizados**, treinta saludables y veintisiete conservados. Incluye la corrección de validación temporal de custodia en Transporte y su copia del monolito, y los textos web de laboratorio/conservación ya revisados. El almacenamiento sigue LOCAL, el backend monolítico y el esquema 21.

**TLS aprobado por evidencia compuesta y acceso SSH temporal propio retirado.** El certificado renovado vence el 24/11/2026 a las 14:08:33 UTC y cubre el día local del 23/11.

## Cambio y huellas

Paquete revisado SHA-256 `351922b37c3e78f63a5786448b57114d63acef0c308131f7cb22badd577f8bea`. Destinos únicos: `transporte-a`, `transporte-b` y `web`. Se derivaron imágenes desde las bases existentes, conservando el resto de contenedores y la configuración del despliegue. Las cinco fuentes únicas publicadas son:

| Fuente | SHA-256 anterior | SHA-256 publicada |
|---|---|---|
| `apps/services/ms_transporte/routes.py` | `04ccaeea8ac980dbcff9e8a516e8746cb2be72ebce21b7ee647444a7b050e20b` | `d6e189dadc602c102a5f3dd7d8e95a5609729ce14b06fdea67a1a73f228d0896` |
| `apps/services/ms_transporte/custody_time.py` | No existía | `4b5a7ad6692960147718645bef8cb13bbb6464f133ab9750133daac1ade09d12` |
| `apps/web/src/integration/routes/common.py` | `bdbcbe643659e61be3c616d57024751d3b3d40b3ab676f5fe151edfea6103934` | `9c667b6cdf52e95752cf4e7149b24cfc46209c369561e800955ab0c57fffb5a3` |
| `apps/web/src/integration/presentation.py` | `2c8ed28cdd17eadbdc375f4a3062d3b210ae431c1dcaec668ea47a2c552560e0` | `e9ad016027f32ed5e402ae5732b28fed68d307b6930ad8580756025e0a136c86` |
| `apps/web/src/integration/routes/conservation.py` | `7b3f6aa51e3bd76b70a67d11e3b9f43c79c44d227427cf45dc9b10ea3dd7e174` | `106d2e144ce3da084d89165912ac08e4bedc8abbfbe55433a8a0e1536b20a4ad` |

| Imagen | ID publicado | Base conservada |
|---|---|---|
| `transporte` | `sha256:4b5fa58040b9370e7e5fc63f61d2fb374486ba35ae10c94d515b48e2731fe3ed` | `sha256:784d2b285144f09e8a0fabcfa0422404947189146ba3ae8f484ad156309266df` |
| `web` | `sha256:4a17d3ef9cf1ecc8609df67c397e03734b3a6de8251457f313a3422f2c14dff3` | `sha256:671ccee75e3033f079dfacd70ac7cb071f2cb5bf7e676dd50895099793daeab8` |

Los tags publicados se conservan en el [resumen estructurado](resumen.json). Inventario A/B mantiene la imagen `sha256:fa43724f2d475872c1f8c8ef90eb3f8c7ea756828ad60dff06b3aec2ba72afca`; no se recrearon esos contenedores ni se revirtió su corrección N+1. Web parte de la imagen monolítica que ya incorporaba esa corrección. El JavaScript público de seguimiento conserva SHA-256 `64c9986e24385e498507791e6160e63eb358cdaa842ab0ad75c8d7a0a1c81503`.

La evidencia local previa de [presentación web/Qt](../presentacion-web-qt-20261117/RESULTADOS.md), los cierres sintéticos y sus controles conservan su aceptación y límites propios. No se repitieron pruebas ni operaciones de negocio para redactar este informe.

## Publicación y comprobación remota

Preflight, preparación, release y validación final aprobaron según sus recibos. Las dos rondas HTTPS comprobaron cinco rutas cada una: salud viva y preparada de Transporte, salud monolítica web, formulario login y hash de `tracking.js`. Las diez respuestas fueron HTTP 200; el cliente utilizó CA predeterminada y no siguió redirecciones. Estos GET públicos no acreditan otra autenticación ni recorrido protegido remoto.

Se conservaron los otros veintisiete contenedores, incluidos Inventario y gateway. No hubo login técnico, escritura de negocio, restauración de base ni cambio de Nginx. No se tocaron permisos ni buckets. La recreación de los tres destinos pudo producir una interrupción breve; dos rondas saludables no demuestran disponibilidad continua ni capacidad productiva. Los recibos originales permanecen privados y sus hashes figuran en el resumen; no se publican configuraciones, secretos ni credenciales de acceso.

## Renovación TLS y cierre de acceso

El recibo de publicación conserva la observación anterior a la renovación. CA e IP aprobaron con el certificado SHA-256 `a5c19375af97ae6d4beef5a8a16ae939512052670bf0fc804b63397cbff3e737`, cuyo vencimiento del 21/11 a las 15:14:23 UTC quedaba antes del 23/11.

Certbot terminó con código 0 en 12,446 s y una única emisión. Se conserva el **FAIL** del ejecutor original, código 1, porque su comparación exigía el modo anterior del archivo de renovación. Certbot cambió ese modo de `0644` a `0600`. El contenido, las opciones y el propietario del archivo se conservaron.

La conciliación de solo lectura aprobó con código 0. El certificado de Certbot, la copia instalada y el servido comparten SHA-256 `d88b61893df86a26263c17933de7b24d893ae6d363d63b0bdef7f3afe5c038a6` y vencimiento el 24/11 a las 14:08:33 UTC. El corte exigido era el 24/11 a las 06:00 UTC. La copia instalada del certificado y su clave conservaron UID 0, GID 101 y modo `0640`. El temporizador quedó activo y habilitado.

Los 30 contenedores conservaron ID, imagen, hora de inicio y estado saludable. Coincidieron los hashes de 184 archivos ajenos a TLS y se conservaron las unidades y hooks. `nginx -t` aprobó. Dos rondas de `GET /health/live` y `GET /login` dieron cuatro HTTP 200 con validación de CA e IP, sin redirecciones, cookies ni autenticación. La conciliación no repitió la renovación ni recargó Nginx. Tampoco restauró el certificado ni exportó claves.

La retirada SSH terminó con código 0. Eliminó la clave temporal propia de OS Login y sus dos archivos locales. Las dos claves previas se conservaron. Los recibos privados quedan identificados por SHA-256 en el resumen. La aceptación cubre esta ventana de TLS y acceso SSH. GPS/WSS y las etapas integrales conservan su evidencia separada. [Resumen estructurado](resumen.json)
