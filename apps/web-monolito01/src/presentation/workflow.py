"""Orientación de interfaz; los servicios siguen autorizando cada transición."""
FLOWS = {
    'donor': [('PENDING','Registro','Registrar evaluación humana','Personal médico'),
              ('ELIGIBLE','Evaluación favorable','Registrar donación con revisión vigente','Operador del banco de sangre')],
    'recipient': [('ACTIVE','Expediente activo','Registrar solicitud','Personal médico de la institución')],
    'donation': [('REGISTERED','Registro','Documentar recolección','Operador del banco de sangre'),
                 ('COLLECTED','Recolección','Documentar procesamiento','Operador del banco de sangre'),
                 ('PROCESSED','Procesamiento','Revisar pruebas y autorizar liberación de unidad','Personal médico'),
                 ('RELEASED','Unidad liberada','Consultar inventario y atender solicitudes','Personal autorizado de la red')],
    'request': [('OPEN','Solicitud','Generar alternativas para revisión','Médico o coordinador regional'),
                ('EVALUATED','Alternativas','Revisar estudios y autorizar cada reserva','Personal médico de la institución solicitante'),
                ('RESERVED','Reserva y traslado','Completar reservas y coordinar la entrega','Médico, coordinador y personal de traslado'),
                ('RECEIVED','Recepción','Revisar recepción completa y cerrar solicitud','Personal médico de la institución solicitante'),
                ('CLOSED','Cierre','Consultar historial y auditoría','Personal autorizado')],
    'shipment': [('RESERVED','Reserva','Asignar responsable y programar traslado','Coordinador regional'),
                 ('SCHEDULED','Programación','Preparar el recurso','Operador de la institución de origen'),
                 ('PREPARED','Preparación','Registrar recolección','Transportista asignado'),
                 ('COLLECTED','Recolección','Registrar salida en tránsito','Transportista asignado'),
                 ('IN_TRANSIT','En tránsito','Registrar entrega en destino','Transportista asignado'),
                 ('DELIVERED','Entrega','Aceptar recepción y registrar ubicación','Operador o médico de la institución de destino'),
                 ('ACCEPTED','Recepción','Cerrar solicitud al recibir su cantidad completa','Personal médico de la institución solicitante')],
}


def progress(kind, status):
    flow=FLOWS[kind]
    index=next((i for i,item in enumerate(flow) if item[0]==status),None)
    if index is None:
        label={'CANCELLED':'Cancelado','DEFERRED':'Diferido','INACTIVE':'Inactivo'}.get(status,status)
        return dict(steps=[(label,'current')],next='Consultar historial; no avanzar mientras el registro permanezca en este estado.',owner='Personal autorizado de la institución')
    return dict(steps=[(item[1],'done' if i<index else 'current' if i==index else 'pending') for i,item in enumerate(flow)],next=flow[index][2],owner=flow[index][3])
