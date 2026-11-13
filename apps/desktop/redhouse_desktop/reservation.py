"""Validaciones de coherencia del resultado asincrónico de una reserva."""
from .journal import JournalError


def validate_operation(record, result):
    if result.get('status') not in ('PENDING','ROLLBACK_PENDING','FAILED','COMPLETED'):
        raise JournalError('El servicio devolvió un estado de reserva desconocido.')
    if record.get('operation_id') and record['operation_id']!=result.get('operation_id'):
        raise JournalError('La operación recibida no corresponde al intento guardado.')
    reservation=result.get('reservation')
    if result['status']=='COMPLETED' and not reservation:
        raise JournalError('La operación completada no incluye una reserva verificable.')
    if reservation and (reservation.get('resource_id')!=record['body']['resource_id'] or
                        reservation.get('evaluation_id')!=record['body']['evaluation_id']):
        raise JournalError('La reserva recibida no corresponde a la solicitud guardada.')
    return result
