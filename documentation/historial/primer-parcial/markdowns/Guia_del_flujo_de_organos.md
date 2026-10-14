# Guía del flujo de órganos

## Actualización

Ejecutar `migrate-db` desde la aplicación, con respaldo previo. La migración `004_organs.sql` añade ocho tablas y sus restricciones; no crea cuentas, contraseñas ni datos de presentación. En la instalación local se aplicó después de verificar una copia restaurada. El menú se habilita por perfil; las cuentas médicas, de coordinación y transporte se administran desde Usuarios.

## Recorrido por responsable

1. **Médico de origen → Órganos y HLA → Donantes:** registrar folio, nombre ficticio, ABO, tipo de donante, consentimiento, estudios, HLA y referencia de revisión humana.
2. **Médico de destino → Receptores:** registrar el órgano requerido, estudios/HLA, urgencia registrada, inicio de espera y referencia médica.
3. **Médico de origen → Registrar órgano:** indicar donante, riñón/hígado/corazón, descripción anatómica, recuperación, límite de conservación y referencia de liberación. No utilizar vidas útiles inventadas como criterios clínicos.
4. **Coordinador → Rutas y estimaciones:** completar origen/destino, kilómetros y minutos si aún no existe la ruta.
5. **Coordinador o médico → Disponibilidad → Abrir → Generar candidatos:** consultar tipo, ABO idéntico, instituciones, orden, fechas, traslado y explicación. Una lista vacía exige revisar receptor activo, ruta y conservación.
6. **Médico de destino → candidato → Abrir:** revisar información seudonimizada del donante, estudios del receptor, HLA, tamaño y prueba cruzada. Registrar dictamen favorable o no favorable con su fundamento y referencia.
7. **Médico de destino:** autorizar y reservar usando el último dictamen favorable. La disponibilidad y las versiones se vuelven a comprobar; nunca se reserva automáticamente.
8. **Coordinador → Traslados de órganos:** seleccionar transportista activo del origen, vehículo, salida, ETA y orden de traslado.
9. **Médico u operador de origen:** registrar preparación.
10. **Transportista asignado:** registrar recolección, tránsito y entrega, cada uno con ubicación, observación y referencia de evidencia.
11. **Médico u operador de destino:** aceptar la recepción. Se cierra el receptor dentro del ejercicio y se marca el órgano recibido. Esto no registra una cirugía realizada.
12. **Auditor:** consultar custodia y bitácora, con información mínima y sin permisos de modificación clínica.

Las incidencias conservan el estado actual. El coordinador puede cancelar antes de la recolección; se liberan órgano y receptor y se exige una evaluación nueva. Las capturas rechazadas se conservan en el formulario. Los expedientes clínicos de este incremento son registros históricos; no se habilita su sobrescritura retrospectiva.

## Persistencia y permisos

| Tabla nueva | Contenido y protección |
| --- | --- |
| `organ_donor` | Institución, identidad ficticia, ABO, consentimiento, estudios/HLA y revisor. Inmutable. |
| `organ_recipient` | Órgano solicitado, estudios/HLA, prioridad humana, espera, responsable y estado/versionado. |
| `organ_offer` | Donante, tipo, descripción anatómica, recuperación, límite autorizado, estado y versión. |
| `organ_evaluation` | Ejecución, actor y versión de regla; conserva también evaluaciones sin candidatos. Inmutable. |
| `organ_candidate` | Pareja, posición, explicación, ruta y versiones de origen. Inmutable. |
| `organ_review` | Dictamen humano, HLA, tamaño, prueba cruzada y referencia médica. Inmutable. |
| `organ_allocation` | Reserva, autorización, traslado, actor, vehículo, ETA y estado. Unicidad activa por órgano y receptor. |
| `organ_custody_event` | Actor, fecha, estado, ubicación, observación y referencia. Inmutable. |

El SQL completo está en `documentation/historial/primer-parcial/database/migrations/004_organs.sql`. El esquema previo y sus normalizaciones permanecen como antecedente; esta extensión usa claves foráneas y tablas independientes, sin insertar órganos en `blood_inventory`.

- Médico: expedientes propios; estudios del donante seudonimizado solo para candidato de su institución; dictamen y autorización en destino.
- Coordinador: disponibilidad, candidatos y logística regional; sin expedientes ni estudios clínicos.
- Operador: disponibilidad regional minimizada y preparación/recepción dentro de su institución.
- Transportista: únicamente asignaciones a su cuenta.
- Auditor: disponibilidad minimizada y custodia de su ámbito, sin operaciones de cambio.
- Administrador: usuarios e instituciones; sin acceso clínico por ser administrador.

[Reglas, fuentes y límites](Reglas_del_flujo_de_organos.md). [Capturas reales por requisito](../capturas/README.md).
