# Próxima cita del donante — 13/11/2026

`GET /api/v1/appointments/next` devuelve `data.appointment` con la reserva futura más cercana del donante autenticado, o `null`. Usa la hora del horario vigente, no la fecha de creación de la reserva ni el orden de una página del listado. Solo devuelve estado BOOKED con horario BOOKED/CONFIRMED, dentro de la misma institución y expediente del usuario. Una cancelación/asistencia deja de ser candidata; reprogramar cambia el horario consultado. La lectura no modifica reglas de reserva ni cupo.

Contrato aditivo: id, campaña/título, horario/sede, inicio/fin, estado de reserva, estado y versión del horario. OpenAPI y ejemplo de respuesta regenerados con `apps/services/.venv/bin/python apps/services/scripts/document.py --contracts-only`.

Prueba con PostgreSQL, Redis, MongoDB y servicios HTTP temporales:

```sh
REDHOUSE_TEST_MONGOD=.local/tools/mongodb-8.0.17/bin/mongod apps/services/.venv/bin/pytest apps/services/tests/test_next_appointment.py -q --tb=short --junitxml=documentation/evidencias/entrega-final/mobile/next-appointment-20261113/junit.xml
```

Dos casos aprobados, JSON y XML/XSD, sin omisiones; 111,12 s. Se comprueban ausencia inicial, 105 canceladas posteriores a la reserva activa, reprogramación, confirmación, cancelación y denegación al operador. Otro donante de la misma institución y otro tenant no ven la cita. Datos exclusivamente sintéticos; SQL del propietario prepara el volumen de canceladas, mientras las aserciones usan la API. Este resultado no acredita por sí solo el recorrido visual móvil, iOS ni el cierre de etapa 04.
