# Publicación de servicios y esquema 21 en GCP — 16/11/2026

**Publicación validada** en `sistemas-integracion-01 / red-house / me-central1-a`, instancia `2861822465669755197`, IP `34.18.186.116`. Treinta contenedores saludables: se actualizaron 25 aplicaciones mediante trece imágenes derivadas; los cinco contenedores de infraestructura conservaron identidad, imagen y arranque. El portal continúa en modo monolítico y el proveedor de archivos sigue siendo LOCAL, con GCS opcional. [Resumen verificable](resumen.json) y [huellas de recibos privados](recibos-sha256.json).

## Alcance y aceptación

El paquete fijó 21 fuentes: índice y despacho de eventos, firma de generación GCS, formatos de reportes, etiquetas de campaña/sede y contratos correspondientes, y correcciones del portal. No publica indiscriminadamente todo el repositorio. Se comprobaron fuentes del host, imágenes y contenedores, configuración de las imágenes, contratos y mantenimiento de la configuración operativa. Las imágenes se derivaron de bases locales verificadas, sin descargar dependencias ni ejecutar instalaciones.

Con la entrada pública en mantenimiento y las aplicaciones detenidas se creó un respaldo PostgreSQL de **51.233.064 bytes**, cuyo catálogo se verificó. La migración oficial 20→21 conservó las huellas y cantidades de **115 tablas y 1.311.517 filas físicas**, además del historial anterior, columnas y permisos. Las filas incluyen datos técnicos y de auditoría; no representan pacientes únicos. El cambio estructural es un índice aditivo. No se ensayó una restauración de este respaldo ni se ejecutó rollback.

Antes de reabrir se ejecutaron **40 comprobaciones HTTP protegidas**: JSON y XML/XSD en ambas réplicas de Identidad, Donantes y Documentos; perfil, nombres de campaña/sede en lista y detalle, rechazo 403 de otra institución y listado autorizado de reportes. Las tres familias de sesión creadas para esas pruebas se revocaron y su rechazo se comprobó desde ambas réplicas. No se realizaron escrituras de negocio; sí autenticación y auditoría técnica. El recibo está ligado a los identificadores de imagen y al hash exacto del verificador.

La validación pública final realizó dos rondas de `/health/live` y `/login`: **200, TLS y dirección IP verificados, sin redirección ni mantenimiento**. Volvió a comprobar los treinta contenedores, las fuentes y la configuración. La clave OS Login temporal se retiró; las dos claves previas permanecieron intactas y la copia privada propia se eliminó.

## Fallos conservados y recuperación

- Las guardas iniciales se corrigieron antes de la publicación: presupuesto de conexiones sin duplicar la capacidad ya existente, copia de configuración sin recursión sobre respaldos históricos y un hash de `run.py` cuya diferencia era de formato, con AST equivalente. Se conservaron las ejecuciones anteriores.
- La clave temporal caducó antes de un intento de preparación. Reagregarla mientras todavía existía no había extendido su vigencia. Se restableció únicamente esa misma clave después de su expiración y se verificó su nuevo vencimiento; no se alteraron claves ajenas.
- La primera imagen preparada falló por permisos de directorios: `COPY --chmod=0644` impedía recorrerlos con el usuario final. Se conservaron imagen, contexto y error; una preparación independiente normalizó exclusivamente los contextos a directorios 0755 y archivos 0644. Las trece imágenes aprobaron lectura y compilación con su usuario sin privilegios.
- El primer paso `open` restauró Nginx y registró un `HTTPError` al comprobar el acceso público; no conservó su código HTTP. Comprobaciones externas posteriores devolvieron 200. Una validación posterior independiente repitió controles internos y públicos y aprobó. **El `open` original sigue con exit 1 y su causa no está establecida**; no se presenta como una ejecución sin fallos.

## Limpieza y límites

Se eliminaron **794 copias históricas duplicadas**, equivalentes a **949.001.048 bytes**, después de comparar tamaño y SHA-256 con sus originales. Se conservaron todos los originales, configuraciones operativas, datos y respaldos de base en las raíces de despliegue. El espacio libre observado pasó de 1.518.141.440 a 2.468.855.808 bytes inmediatamente después de esa limpieza.

El certificado público observado vence el **21/11/2026 a las 15:14:23 UTC**. El temporizador de renovación está habilitado y su última ejecución registrada fue exitosa; esta publicación no renovó el certificado y **todavía no acredita cobertura hasta el final del día 23**. Debe verificarse la renovación posterior. Tampoco se midió capacidad sostenida de GCP ni saturación del presupuesto de conexiones. La actualización interrumpió temporalmente solicitudes y WebSocket; no se promete disponibilidad continua durante la ventana.

Los procedimientos, salidas completas y recibos de esta ejecución permanecen privados en `.local/gcp/server21-20261116-plan/` y `.local/gcp/server21-20261116-run/`. El paquete inmutable usado fue `package-review-06`; las reparaciones de preparación y validación se ejecutaron como procedimientos independientes sin modificar sus fuentes. Ningún secreto, dump ni configuración con credenciales se incluye en este expediente público.
