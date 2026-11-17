# Inventario N+1 publicado en GCP — 17/11/2026

La corrección de disponibilidad de Inventario quedó publicada y verificada en `sistemas-integracion-01`, VM `red-house`, zona `me-central1-a`. Una imagen derivada actualizó únicamente `inventario-a` e `inventario-b`; treinta contenedores saludables y veintiocho sin cambios. Esquema 21, almacenamiento LOCAL, backend monolítico y JavaScript de seguimiento conservaron sus versiones.

## Evidencia y aceptación

- Fuente SHA-256 `6714dd289d983f7c4060c33d6abfc40523277f14629625d24786acd048eeafa6`; imagen `redhouse/inventario:inventory-nplus1-20261117-01`, ID `sha256:fa43724f2d475872c1f8c8ef90eb3f8c7ea756828ad60dff06b3aec2ba72afca`.
- Gate local: [equivalencia SQL y regresiones](../inventario-consulta-20261117/RESULTADOS.md) y [cobertura finita compuesta](../carga-finita-20261117/RESULTADOS.md). El raw de carga conserva su fallo CLEANUP; su cierre corregido tiene evidencia posterior separada.
- Doce controles protegidos: diez respuestas 200 JSON/XML, contratos e institución comprobados en A/B; dos rechazos 401 después de revocar la única familia técnica. Cierre confirmado en SQL/Redis. Sin escrituras de negocio.
- Dos rondas públicas de cinco GET verificaron HTTPS, identidad IP, salud y acceso. No hubo migraciones, restauración de base, cambios IAM, buckets o Nginx.
- Clave temporal propia retirada; dos claves previas conservadas y privada local eliminada. Rollback preparado, sin ejecución.

## Intentos conservados

La revisión automática rechazó la transferencia inicial antes de ejecutarla. Se retiró el acceso temporal y el usuario autorizó expresamente el paquete y destino. El segundo intento realizó preflight, preparación y publicación.

La primera comprobación protegida del segundo intento falló con JSONDecodeError antes de autenticar o crear familias: un subproceso de salud consumía stdin. Un adaptador revisado leyó la entrada acotada en memoria antes de ejecutar el mismo driver sellado. La comprobación posterior aprobó, sin reconstruir ni volver a publicar imágenes. Ambos recibos permanecen separados.

## Límites

El certificado HTTPS observado el 17/11 a las 19:04 UTC vence el **21/11 a las 15:14:23 UTC**; todavía no cubre el día 23. Temporizador activo/habilitado y último servicio exitoso, sin renovación forzada. Debe comprobarse la siguiente emisión real.

La publicación acredita este cambio y los controles enumerados; no mide disponibilidad continua, capacidad de GCP, GPS/WSS ni cierre total de etapas. El [resumen reproducible](resumen.json) identifica fuentes, manifest, fases, resultados y límites sin credenciales.
