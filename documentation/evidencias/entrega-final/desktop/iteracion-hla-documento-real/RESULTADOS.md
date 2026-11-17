# Resultado HLA y documento: ensayo académico real

El 16 de noviembre se utilizó el fixture local conservado E2E-B, con 12 servicios en `TESTING=False`, alcance `ACADEMIC`, autorización de órganos y perfil de laboratorio exigidos. ClamAV respondió CLEAN para una imagen sintética y detectó el control EICAR antes de abrir el gateway. La CA del laboratorio se verificó; no se usó GCP.

Sobre una muestra de un órgano KIDNEY sintético, Qt/XML registró un resultado HLA `PENDING`. En una reanudación sobre ese mismo resultado, Qt preparó y cargó un PNG, el servicio verificó CLEAN, Qt creó una corrección con HLA estructurada y el documento verificado, y una cuenta MEDICAL autorizó la revisión. SQL de solo lectura correlacionó muestra, antecedente, autor, documento, hash, generación, evento y revisión; `file_scans` confirmó CLEAN con `CLAMD_INSTREAM`. El logout de la sesión propia se comprobó en SQL y Redis.

Una rama separada del cliente XML, no del formulario Qt, preparó otro documento del mismo resultado: verificó ausencia `object_missing`, conservó clave e identificador y envió dos PUT concurrentes. Respondieron 201 y 412; la verificación posterior obtuvo CLEAN. Esta rama no acredita GCS ni una caída de red real.

## Capturas y alcance

- [Resultado pendiente](01-pendiente.png): primera ejecución Qt real.
- [Adjuntar](02-adjuntar.png), [corrección](03-correccion.png) y [revisión](04-revision.png): ejecución real posterior sobre el mismo resultado. El selector y botones fueron accionados por un adaptador privado programado al abrir los formularios; el transporte, validaciones y persistencia fueron reales.
- [Corrección](correccion.png) y [revisión](revision.png): vista posterior sin envío, con datos sintéticos leídos del resultado persistido. Para abrir la revisión se sustituyó su estado por `CAPTURED` solo en memoria; el resultado persistido seguía `AUTHORIZED`. Estas capturas verifican el ajuste de ancho, la referencia y el locus/alelo completos y las etiquetas traducidas; no constituyen otra autorización.

[SHA256SUMS](SHA256SUMS) contiene las huellas de capturas. El recibo de IDs y comprobaciones permanece privado. Este caso no demuestra trasplante ni autorización clínica real; la cadena E2E-B completa continúa pendiente.

## Intentos conservados

El primer arranque del fixture falló al serializar una fecha de la evidencia del scanner; cerró sus procesos y se conservó. El segundo arrancó correctamente con serialización corregida. El bootstrap guardó unidad y perfil; su arnés esperó 200 donde el control devolvía 201. SQL reconcilió el control y su clave antes de continuar con los mismos IDs, sin reenviar esa operación.

Dos intentos Qt posteriores guardaron o reutilizaron el mismo `PENDING`, pero el temporizador privado no completó el diálogo de carga. Se cancelaron y sus sesiones quedaron revocadas en SQL y Redis; no prepararon documento. Un adaptador privado programó la interacción al abrir cada formulario real y permitió completar el tercer intento. No se atribuye la corrección visual posterior a esa ejecución real.
