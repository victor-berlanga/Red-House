# Red House: avances del segundo parcial

**Versión general · Español · 8–10 minutos, incluida demostración.**

Estado al 20 de octubre de 2026. Usar los puntos como contenido de diapositivas y las notas como apoyo para hablar.

## 1. Qué problema atendemos

- Una institución tiene un recurso disponible y otra lo necesita.
- Red House organiza solicitudes, disponibilidad, autorizaciones y traslados de sangre y órganos.
- Cada etapa permite consultar qué ocurrió y quién participó.

**Para explicar:** Queremos que las instituciones compartan información y coordinen la entrega. El sistema apoya al personal; la decisión médica sigue requiriendo autorización humana.

## 2. Qué avanzó este parcial

- Integramos registros, solicitudes, reservas y traslados con datos guardados realmente.
- Preparamos el portal y los servicios en Docker, tanto localmente como en Google Cloud.
- Incorporamos archivos privados, seguimiento del traslado y comprobaciones de recuperación.

**Para explicar:** El avance principal es poder recorrer procesos completos. Una acción cambia registros que después pueden consultar los usuarios autorizados.

## 3. Cómo funciona un caso completo

1. El banco registra un recurso y el médico autoriza su disponibilidad.
2. Otra institución registra una solicitud y revisa los candidatos propuestos.
3. El personal autorizado confirma la reserva y organiza el traslado.
4. El responsable registra la entrega; el destino acepta y se actualizan inventario y solicitud.

**Para explicar:** La revisión humana está presente antes de comprometer el recurso. Durante el recorrido quedan registros de custodia, avisos internos e historial de acciones. Sangre y órganos mantienen procesos diferenciados.

## 4. Cómo organizamos el sistema

- El portal ofrece pantallas según la responsabilidad del usuario.
- Diez microservicios reparten tareas; un servicio adicional vigila su estado.
- Cada servicio tiene su propio contenedor y dos instancias en la configuración Docker.

**Para explicar:** Un contenedor reúne lo necesario para ejecutar un componente. El portal actual también incluye sus propios módulos de negocio: puede operar con las API apagadas mientras sus bases de datos y demás dependencias necesarias estén disponibles.

## 5. Cómo cuidamos los datos y el acceso

- Cada usuario accede según su rol, institución y relación con el registro.
- Redis conserva las sesiones; PostgreSQL registra cierres y revocaciones pendientes.
- Los archivos quedan privados en Google Cloud Storage y se consultan mediante enlaces temporales autorizados.

**Para explicar:** PostgreSQL guarda las operaciones y MongoDB conserva eventos y seguimiento. Esta separación organiza la información según su uso. La cadena de custodia permite revisar quién recibió o entregó un recurso.

## 6. Qué comprobamos

- Recorrimos 20 páginas de siete perfiles y contrastamos las gráficas con los datos guardados.
- Probamos procesos con una instancia de cada API detenida y el portal con todas las API apagadas.
- Restauramos respaldos y verificamos cargas y descargas de archivos privados.

**Para explicar:** Son resultados de pruebas con datos ficticios. Las verificaciones generales corresponden al 19 de octubre; el 20 se comprobó la actualización de sesiones. Estos ensayos demuestran casos concretos de funcionamiento y recuperación.

## 7. Demostración breve: unos tres minutos

1. **Mostrar la necesidad:** abrir una solicitud y el inventario disponible.
2. **Explicar la decisión:** mostrar candidatos, revisión humana y reserva ya preparada.
3. **Mostrar una acción real:** cargar una evidencia ficticia en un traslado abierto, verificarla y descargarla con autorización.
4. **Mostrar el resultado:** abrir un traslado completado, su custodia y la solicitud atendida.

**Para preparar:** Tener los registros y las cuentas autorizadas listos antes de comenzar. Explicar cuáles etapas ya estaban preparadas. La evidencia se carga durante un traslado abierto; después del cierre no se admiten nuevas cargas.

## 8. Qué sigue

- Desarrollar las aplicaciones Android y de escritorio con las API preparadas.
- Ampliar las pruebas de capacidad y recuperación de la VM. El sistema ya se abre por IP con HTTPS, sin iniciar nada localmente.
- Ampliar pruebas de carga, redundancia de infraestructura y validación clínica de las reglas.

**Para explicar:** Hoy contamos con el entorno Docker probado, una VM accesible mediante conexión privada y archivos reales en la nube. El trabajo siguiente incluye acceso público y la validación necesaria para una operación real.

---

Material de apoyo: [guía de uso y evidencias](../README.md) · [versión técnica](../tecnica/presentacion_es.md) · [English version](presentation_en.md).
