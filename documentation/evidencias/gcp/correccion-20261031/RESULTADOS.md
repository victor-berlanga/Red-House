# Despliegue correctivo en GCP — 31 de octubre de 2026

El usuario autorizó encender y actualizar GCP y pidió una demostración visible sin grabación. Proyecto `sistemas-integracion-01`, VM `red-house`, zona `me-central1-a`, portal https://34.18.186.116. Las marcas técnicas UTC pertenecen al 1 de noviembre; la fecha local de Monterrey es 31 de octubre.

## Despliegue comprobado

- Publicadas fuentes locales correctivas 0.4.1; se conservaron los cambios locales y no se sustituyeron por el antiguo `main` de GitHub. Paquete inicial: 1.383 archivos; `package.json` registra SHA-256.
- Antes del corte: código 0.3.0 y esquema 7. Respaldo coordinado de PostgreSQL, MongoDB, Redis, configuración y código; imágenes anteriores conservadas. Restauración real en tres contenedores aislados aprobada, con igualdad de hashes/conteos y permisos web: `backup-restore.json`.
- Respaldo privado remoto: `/opt/redhouse/.local/compose/backups/20261101T031359Z`; incluye metadatos de 36 objetos GCS. Código/configuración/imágenes previos en `/opt/redhouse/.local/deploy-20261031`.
- Migración aditiva a esquema 13. Las 75 tablas originales permanecen; total posterior 108. `data-preservation.json` distingue las tablas idénticas de contadores, caducidades y eventos procesados por workers tras arrancar. No se vació ni restauró encima de la instalación existente.
- 30 contenedores permanentes sanos: 24 réplicas API/worker, web, gateway, tres almacenes y ClamAV. Versiones y dependencias de doce API, más web, comprobadas por HTTPS: `health-final.json` y `containers.json`.
- Certificado vencido durante el apagado renovado con Certbot; conexión validada sin ignorar TLS. Timer de renovación conserva su habilitación.
- ClamAV oficial 1.4.6 fijado por digest, con firmas reales y sin puertos publicados. Desde Documentos: texto limpio aceptado y EICAR rechazado (`clamav.json`). GCS usa identidad adjunta a la VM; no se copiaron ADC personales.
- No se configuró SMTP ni push externo. Las pruebas usan exclusivamente datos ficticios autorizados.

## Ajustes necesarios durante la publicación

El primer intento de migración se revirtió transaccionalmente y dejó esquema 7. El migrador ahora concede el permiso CREATE sobre la base al dueño del esquema solo dentro de la transacción y lo retira antes del commit. También admite instalaciones antiguas con contraseña Redis administrativa en archivo separado. La regresión aislada ejecuta dos veces el migrador y comprueba conservación de sesiones, credenciales y ausencia de privilegios adicionales: `migration-regression.xml`, 1 caso aprobado.

El empaquetado remoto inicial creó carpetas nuevas sin permiso de recorrido para UID 10001. Readiness detectó el problema y bloqueó la web; se corrigieron exclusivamente directorios de fuentes y se reconstruyeron imágenes. Configuración y respaldos privados conservaron sus restricciones.

Se añadió `deployment/gcp/configure_scanner.py` y se adaptó `deployment/backup.py` para incluir overrides GCP, TLS y el escáner en el procedimiento de mantenimiento. El código de negocio validado el 29 de octubre permanece sin cambios.

La revisión automática rechazó trasladar credenciales del servidor al equipo. Se utilizó la copia local preexistente del respaldo de despliegue; no se realizó ese traslado. Los factores MFA y sesiones de prueba quedan en archivos privados ignorados por Git, nunca en estas evidencias.

## Demostración

**Completada en Chrome visible contra la IP pública.** Veintiséis comprobaciones distintas consolidadas; segundo intento 24/24 aprobado. Incluye laboratorio corregido, rechazo de dictamen obsoleto, reserva, custodia obligatoria, publicación/reconexión WSS, recepción, destino e historial, rechazo entre instituciones, cambio de rol con invalidación de sesión, reporte privado descargado desde GCS, auditoría responsive y cierre de sesión. `browser-summary.json` identifica criterios y registros ficticios.

Solo se conservan estados de comprobación y errores redactados: no hay imágenes, vídeo, HAR ni trazas del navegador. Chrome quedó abierto en inventario para exploración manual. El primer recorrido validó MFA, cookies Secure, rechazo sin reautenticación y liberación persistente; se detuvo porque la automatización buscó el receptor por UUID en un selector que busca por nombre. El segundo reutilizó esa misma unidad y buscó por nombre; no se borraron datos para ocultar el intento.

Verificación adicional: **24 respuestas de doce servicios**, una JSON y una XML por servicio, validadas contra contratos JSON Schema y XSD/DTO (`contracts.json`). El certificado TLS 1.3 validó con el almacén CA de certifi y navegador, con vencimiento registrado en `tls.json`.

## Límites

Esta ejecución no sustituye una nueva revisión independiente de la etapa ni constituye validación clínica. Permanecen pendientes mapas/clientes, GPS físico, HLA ampliado y aprobaciones institucionales. Infraestructura: una VM y una instancia por almacén; las réplicas API no eliminan ese punto único de falla. No se repitió toda la regresión de 370 casos ni pruebas de carga sostenida.
