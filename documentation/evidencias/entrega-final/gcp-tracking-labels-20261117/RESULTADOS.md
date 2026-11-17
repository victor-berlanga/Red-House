# Etiquetas de seguimiento publicadas en GCP — 17/11/2026

## Resultado y alcance

Publicación aprobada en `sistemas-integracion-01/red-house/me-central1-a`, VM `2861822465669755197`, IP `34.18.186.116`. Una fuente JavaScript, una imagen derivada y un único contenedor web actualizado; veintinueve contenedores conservaron identificador, imagen e inicio. Los treinta quedaron saludables. Almacenamiento LOCAL, backend monolith y esquema 21 permanecieron.

`apps/web/src/presentation/static/js/tracking.js`, commit `83ec338`, reconoce iPhone, muestra la condición simulada y mantiene coherente el aviso de cartografía. SHA-256 publicado `64c9986e24385e498507791e6160e63eb358cdaa842ab0ad75c8d7a0a1c81503`; base Git `83ec338^`, SHA `4a50a29b7c9b8e01723f6da5b7018e14d619a331926819ae35eb8b3ad24bf47f`. El gate local corresponde a la [consulta final E2E-A](../e2ea-cierre-20261117/RESULTADOS.md), con negocio/fuentes estables y familia propia cerrada.

La [imagen resultante](builds.json) `sha256:8f25712cbc20d718e4cfef2a268d06d287db4a3aec4636b21862bf849e6d5a7a` deriva de la web anterior `sha256:7ad4e8abcc6619116e9454b139afd530ac603d8e9477e1678e909d22433e47fe`. Solo añade el JS; Config y capas padre se comprobaron. Preflight cotejó fuente en host, contenedor e imagen; conservó respaldo exacto de JS, imagen y selectores Compose. Rollback de código preparado, sin ejecutar ni restaurar datos.

## Verificación

[Validación final](validation.json): dos rondas HTTPS con CA del sistema y sin redirects obtuvieron 200 en `/health/live`, `/login` y `/static/js/tracking.js`. Ambas descargas del JS coincidieron exactamente con el SHA aprobado; health identificó web/monolith y login conservó formulario de contraseña. No se creó sesión técnica ni se hicieron escrituras de negocio.

[Publicación](released.json) y [fases](phases.json) conservan resultados y huellas sin logs, configuraciones, claves ni credenciales. Acceso, staging, preflight, prepare, release y finish terminaron con salida 0; recibos recuperados. [Limpieza](access-cleanup.json) confirmó retirada de la clave OSLogin temporal, dos claves anteriores intactas y eliminación de la privada propia; access-remove terminó con salida 0.

TLS validó confianza e IP. Certificado observado hasta el 21/11/2026 a las 15:14:23 UTC; timer de renovación activo y habilitado, último servicio con éxito el 17/11 a las 12:13:20 UTC. No se forzó renovación y sigue pendiente comprobar cobertura del día 23.

Sin cambios IAM, Nginx, migraciones ni reinicio de toda la plataforma. Esta comprobación pública no repite autenticación protegida, WSS, GPS, operaciones clínicas, pruebas móviles ni el recorrido integral E2E-A. No cierra por sí sola las etapas 04–07. Recibos privados originales en `.local/gcp/tracking-labels-20261117-run/receipts/20261117T173937Z-dca4324e/deploy-tracking-labels-20261117-01`; claves y configuraciones no se publican.
