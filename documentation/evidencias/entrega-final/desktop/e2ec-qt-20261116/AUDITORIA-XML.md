# Consulta XML de auditoría sobre el recorrido compartido

El 16/11/2026, una sesión sintética de `auditor1` consultó por HTTPS/XML el listado y detalle de eventos asociados a los identificadores privados del recorrido iOS–Qt–web. El lector terminó con salida 0 y cerró su sesión. Usó `audit_list` con filtro `resource`, categorías explícitas y paginación; verificó cada detalle por `resource_id` o `resource_refs`. No accedió directamente a bases de datos ni ejecutó escrituras de negocio. Login y logout producen sus propios eventos de seguridad.

| Referencia del recorrido | Eventos | Acciones distintas observadas |
| --- | ---: | --- |
| Cita conservada | 3 | APPOINTMENT_BOOKED, READ |
| Donación | 9 | DONATION_COLLECTED, DONATION_PROCESSED, RESOURCE_CONTROLS_BOUND, RESOURCE_CREATED, RESOURCE_FRACTIONATED, RESOURCE_RELEASED, READ |
| Unidad origen | 10 | RESOURCE_CREATED, RESOURCE_FRACTIONATED, REJECTED, READ |
| Derivado AVAILABLE | 14 | RESOURCE_CONTROLS_BOUND, RESOURCE_RELEASED, READ |
| Derivado QUARANTINE | 4 | READ |
| Muestra | 2 | LAB_SAMPLE_REQUESTED, LAB_SAMPLE_RECEIVED |
| Resultado | 2 | LAB_RESULT_RECORDED, LAB_RESULT_AUTHORIZED |

Los recuentos incluyen lecturas generadas por el propio ensayo y no miden actividad clínica ni cobertura total del sistema. Para el derivado QUARANTINE la consulta solo devolvió eventos READ; **esta consulta no reconstruye por sí sola su linaje completo**. La asociación de ambos derivados con el origen se comprobó por separado en el recorrido Qt y sus oráculos de propietario. El lector no incorpora los IDs ni datos personales en la salida pública.

Comando ejecutado una vez; el envoltorio privado impuso un límite total de 60 segundos y conservó log y resumen con modo 0600:

```sh
PYTHONPATH=apps/desktop \
  E2EC_RECEIPT="$PWD/.local/artifacts/desktop/e2ec-run-20261116/private/handoff-web.json" \
  AUDIT_PRIVATE_OUTPUT="$PWD/.local/artifacts/desktop/audit-e2ec-run-20261116/private" \
  apps/desktop/.venv/bin/python .local/artifacts/desktop/audit-e2ec-prepared-20261116/runner.py
```

Huellas SHA-256: runner `2d3cb1790f5c779f628f8bdcd5c0dd514ae54ffce4099ab6128e18981e957710`; resumen privado `59ba12c55ed19fb523915d52e585da59c6e50e2438012679388d20152219528c`. El recibo, log y resumen permanecen privados. El entorno era académico sintético; esto no acredita exhaustividad de auditoría ni una autorización clínica.
