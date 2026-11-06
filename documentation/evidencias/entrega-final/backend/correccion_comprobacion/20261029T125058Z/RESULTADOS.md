# Resultado correctivo local 0.4.1 / esquema 13

Fecha: 29 de octubre de 2026. Commit base `8909baf8458dff797d40d15541c57c66c14ef964` más cambios locales conservados. **No constituye auditoría independiente ni aceptación productiva. La etapa sigue NO APTA mientras falte su aceptación obligatoria.**

## Resultado reproducible

- **370 casos distintos aprobados, cero fallos pendientes y cero omitidos**, deduplicados por `classname::name` en [consolidado.json](consolidado.json). No es una sola ejecución de 370 casos: combina regresión 21, límites 22, focalizadas 23, verificador 26 y navegador 30. Se conservan todos los intentos fallidos.
- La regresión 21 dio 356 aprobados y nueve fallos; cada fallo tiene corrección y repetición aprobada en 22/23. La ampliación incorpora reasignación durante replay y el verificador Compose. El navegador opcional y GCS real se activaron expresamente.
- Navegador Chrome real: **27 comprobaciones**, Nginx 1.28.0 nativo con TLS/WSS, cookies Secure y las cuatro políticas operativas. [Resultado y errores de red](browser-30/correcciones-operativas/resultados.json); capturas en la misma carpeta. Hubo rechazos esperados 401/403/409; cero errores JavaScript y cero respuestas 5xx en el recorrido aprobado. Los nombres y expedientes son sintéticos.
- Complementos de navegador: [formularios, auditoría y hallazgos](browser-regresion-21/navegador.json) y [geolocalización solicitada por botón, denegación y guardado único](browser-23/ubicacion/location-report.json), ambos aprobados.
- Flujo completo: MFA/reauth, solicitud/evaluación/revisión, laboratorio corregido que invalida dictamen, reserva nueva, traslado/custodia/aceptación, destino y corrección histórica, acceso ajeno, rol revocado, sesión vencida, filtros, reporte privado GCS, auditoría responsive y logout. PostgreSQL confirmó dos versiones de destino, dos resultados de laboratorio y traslado ACCEPTED.
- WSS por Nginx: publicación/recepción/reconexión con simulador identificado. **No acredita mapa, GPS físico ni clientes Android/escritorio completos.** F4/F6/F10 añaden casos HTTP/JSON/XML/XSD, revocación/reasignación/finalización/expiración/Redis, historia durable y caída real de una/todas las instancias.
- GCS y ClamAV reales: [gcs-autonomia-07.xml](gcs-autonomia-07.xml), repetidos en regresión 21; [clamav-real.json](clamav-real.json) registra firmas oficiales, EICAR, timeout controlado y recuperación. Las pruebas de formatos que usan dobles no se confunden con esas integraciones.
- **12 paquetes independientes**: [paquetes.json](paquetes.json). **14 imágenes**: 12 servicios, web y bootstrap; [imagenes.json (archivo)](../../../../archivo/detalles-20261104.tar.gz) conserva IDs, versiones y hashes de archivos contrastados con el árbol. Cada imagen de servicio cargó su aplicación aislada, sin red/almacenes, con un solo paquete de dominio, UID 10001, liveness y OpenAPI 200 mediante cliente Flask dentro del contenedor. Además, [documentos-contenedor.json](documentos-contenedor.json) acredita el entrypoint real de Documentos: API HTTP autenticada JSON/XML y worker con PostgreSQL/Redis temporales, con la API documental del fixture detenida. No prueba readiness GCS ni capacidad sostenida.
- Migración v11→13 dos veces, conservación de referencias/idempotencia/outbox, pg_dump y restauración real: [arquitectura-08.xml](arquitectura-08.xml). Entrada de actualización Compose/configuración/ACL ensayada sobre estructura privada equivalente en regresión 21. **No se repitió el despliegue completo de 29 contenedores.**
- Conservación: [conservacion.json](conservacion.json), 3.123 archivos iniciales y cero ausentes; 1.769 archivos del expediente histórico conservan exactamente su SHA-256. Manifiestos inicial/final y respaldo privado disponibles; ningún reset/checkout/commit ni actualización de la instalación habitual.

## Arquitectura y cierre por criterio

[Arquitectura y decisiones](../../../../../entrega-final/backend/correccion/Arquitectura_y_decisiones.md) compara conservar/reorganizar/extraer, documenta 24 responsabilidades, dependencias, ciclos y fronteras transaccionales. Resultado: 12 servicios independientes (11 propietarios de dominio y Monitoreo), 24 réplicas API/worker en Compose; web, gateway y tres almacenes completan 29 contenedores permanentes. Bootstrap es una tarea de instalación.

Documentos/Reportes es el nuevo propietario (`ms_documentos`, 5112/6112). Transporte conserva logística/rastreo/sincronización y delega rutas v1 documentales una sola vez. SQL/ACL, worker, gateway, módulos web, contratos JSON/XML/XSD y configuraciones Docker/GCP se actualizaron sin doble autoridad ni acceso SQL cruzado. La web conserva operación modular autónoma, probada con API detenidas.

[Matriz de 50 criterios](../../../../../entrega-final/backend/correccion/Matriz_cierre.md): F1–F11, BE-01–24, TRACK-01–10 y transversales. El JSON vincula identidades de prueba a evidencia. F4 simula la reasignación de responsable en estado PostgreSQL del fixture para comprobar reautorización; no acredita un endpoint público de reasignación que no existe.

## Producción y límites

La consulta GCP observó `red-house` / `sistemas-integracion-01` / `me-central1-a` en **TERMINATED**. [Navegador de producción](produccion-navegador.json): HTTPS `34.18.186.116`, timeout, sin escrituras y sin validación de 0.4.1/esquema 13. No se encendió la VM ni se desplegó/migró producción.

Pendiente autorización explícita de encendido/coste, despliegue/migración y recorridos con tenant/cuentas sintéticos. El [plan de despliegue y rollback](../../../../../entrega-final/backend/correccion/Despliegue_y_rollback.md) exige mantenimiento, respaldo privado, restauración comprobada y verificación de web/API/workers/esquema antes de recorridos HTTPS. No enviar avisos externos a personas.

Otros límites: mapa/interfaz completa TRACK-05/06, aceptación integral TRACK-10, GPS físico, HLA clínico ampliado y validación experta, políticas sanitarias aprobadas, entrega SMTP/push productiva y estrés/RTO/RPO sostenidos. Las pruebas locales no certifican esos requisitos. Hace falta una nueva comprobación independiente sobre las fuentes finales.

[Comandos e intentos](COMANDOS.md) · [Fuentes finales (archivo)](../../../../archivo/detalles-20261104.tar.gz) · [Manifiesto de evidencia](MANIFEST.json).


## Archivo de detalles — 04/11/2026

Los manifiestos extensos, capturas de estado Git y muestras HTTP de este expediente se conservan sin alterar sus bytes en [el archivo comprimido](../../../../archivo/detalles-20261104.tar.gz); el [índice](../../../../archivo/detalles-20261104.json) identifica cada ruta original, tamaño y SHA-256. Los resultados, JUnit e incidencias siguen visibles. Antes de ejecutar verificadores históricos que lean esos detalles, restaurar las rutas desde la raíz del repositorio con `tar -xzf documentation/evidencias/archivo/detalles-20261104.tar.gz`. Extraer en una carpeta temporal para una consulta sin escrituras en el repositorio. Los hashes históricos corresponden al corte original, no al árbol actual.
