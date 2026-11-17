# Inventario N+1 propagado a web monolítica en GCP — 17/11/2026

La imagen web incorpora la corrección de disponibilidad de Inventario ya publicada en los dos contenedores del servicio. Se actualizó exclusivamente `web` en `sistemas-integracion-01`, VM `red-house`, zona `me-central1-a`: treinta contenedores saludables y veintinueve sin cambios. Se conservaron las imágenes de Inventario, el JavaScript de seguimiento, el esquema 21, el almacenamiento LOCAL y el backend monolítico.

## Cambio y criterios de aceptación

El Dockerfile web incluye el código de los módulos de dominio; publicar únicamente Inventario no actualizaba esa copia embebida. Se derivó una imagen desde la web previamente verificada, cambiando solo `apps/services/ms_inventario/routes.py` mediante una capa COPY, sin descargar dependencias ni reconstruir el producto completo.

- Fuente candidata SHA-256 `6714dd289d983f7c4060c33d6abfc40523277f14629625d24786acd048eeafa6`, commit `2c6a8a7`. Fuente anterior dentro de web `4bd431c084dc92e30d8168a69bdd1ba204dcf6291ed19578c2ed737613ba2a29`.
- Imagen publicada `redhouse-web:web-inventory-nplus1-20261117-01`, ID `sha256:671ccee75e3033f079dfacd70ac7cb071f2cb5bf7e676dd50895099793daeab8`; base `sha256:8f25712cbc20d718e4cfef2a268d06d287db4a3aec4636b21862bf849e6d5a7a`.
- El host ya contenía la fuente candidata desde la publicación anterior de Inventario; esta operación no reescribió ni degradó ese archivo. Se verificaron la configuración/USER idénticos de la imagen, las capas padre, la lectura de la fuente y su compilación/importación con el usuario final.
- Se conservaron los ID, las imágenes, los tags, los tiempos de inicio y la salud de los otros veintinueve contenedores. El JavaScript público conserva SHA-256 `64c9986e24385e498507791e6160e63eb358cdaa842ab0ad75c8d7a0a1c81503`.

La [equivalencia SQL y las diecisiete pruebas dirigidas](../inventario-consulta-20261117/RESULTADOS.md), la [aceptación compuesta de carga finita](../carga-finita-20261117/RESULTADOS.md) y la [publicación previa de Inventario](../gcp-inventario-20261117/RESULTADOS.md) se reutilizaron. No se repitieron esas pruebas ni los controles protegidos remotos del servicio.

## Gate Chrome del monolito local

Un único recorrido con Chrome real utilizó el formulario de inicio de sesión, medical1 del Hospital 1 y su factor MFA existente. Consultó inventario y el detalle de la misma unidad sintética iOS, en estado **Reservado**, con dos respuestas HTTP 200. Las capturas reales se inspeccionaron: institución, folio, estado, resumen, movimientos y dictámenes legibles. No se registró ninguna mutación de negocio, tercero consumido ni error JavaScript. La CA y el nombre del servidor se verificaron antes de usar su SPKI concreto en Chrome.

El navegador terminó con salida 0 y confirmó POST de logout HTTP 302 seguido de la página de login. La única familia técnica nueva quedó cerrada en SQL y ausente de Redis; recurso, reservas y fuentes permanecieron iguales. La procedencia de la fuente candidata se acredita por el snapshot del launcher anterior a los imports, su hash fijado y el mismo PID/listener; no constituye introspección de bytecode.

**El wrapper conserva su fallo original, salida 1.** Su observador escuchaba peticiones de la página principal y omitió el logout enviado desde otra página del mismo contexto. Por ello rechazó la lista de POST después de que el navegador completara lectura y cierre. La aceptación es compuesta: navegador, cierre SQL/Redis y conservación del estado. No se repitió el login ni se alteró el recibo fallido. El listener se corrigió para usos futuros, sin ejecutar esa nueva versión ni atribuirle los resultados anteriores.

El [resumen verificable](resumen.json) contiene hashes de los scripts exactamente ejecutados, los recibos originales, la conciliación y ambas capturas. Los originales permanecen privados; este informe no publica cookies, factores, credenciales ni imágenes privadas.

## Publicación y comprobación remota

El paquete revisado tiene manifiesto SHA-256 `da7440ec811c97223ddf3d604024228f02f97d8d91e087c72b9febc44a2ba3aa`. Las siete fases registradas —acceso temporal, staging, preflight, preparación, publicación, comprobación final y retirada— terminaron con salida 0. La recuperación separada obtuvo nueve recibos, cuyos hashes se verificaron antes de redactar esta evidencia.

Se recreó únicamente web con `--no-deps --no-build --pull never --wait`. Dos rondas HTTPS verificaron salud monolítica, formulario login y el hash exacto del JavaScript: seis respuestas HTTP 200, sin redirecciones inesperadas. No se creó sesión protegida en GCP ni se ejecutaron operaciones de negocio, migraciones, restauraciones, cambios IAM, buckets o Nginx.

Se retiró exclusivamente la clave temporal propia, se conservaron dos claves previas y se eliminó la privada local. El rollback conserva la imagen anterior y el override exacto; no se ejecutó y no requiere degradar la fuente ya actualizada del host ni restaurar datos.

## Límites

El certificado observado el 17/11 a las 20:12 UTC vence el **21/11 a las 15:14:23 UTC**. Temporizador activo/habilitado y último servicio exitoso; no se forzó renovación y todavía no se acredita cobertura para el día 23.

Esta evidencia cubre la propagación de una fuente a web y los controles enumerados. No mide disponibilidad continua ni capacidad de GCP, no acredita un nuevo recorrido autenticado remoto y no cierra GPS/WSS ni las etapas completas. La recreación pudo producir una interrupción breve de web. Los fixtures locales no se iniciaron ni reiniciaron para esta publicación.
