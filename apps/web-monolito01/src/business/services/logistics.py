"""Asignación, transporte y recepción con permisos por etapa y recurso."""
from datetime import timedelta

from ..access import BusinessError,check_version,require
from .. import validators as v
from ...data_access.connection import transaction
from ...data_access.repositories.common import insert, pattern
from ...data_access.repositories import accounts,network
from . import regional as r


def allocation_row(conn,actor,identifier,lock=False):
    if not (actor.can('logistics') or actor.can('trace.read')):
        raise BusinessError('No tienes permiso de logística.',403)
    row=conn.execute('''SELECT a.*,q.request_code,o.region_name,o.institution_name AS origin_name,
        d.institution_name AS destination_name,b.traceability_code,u.expires_at,u.location_id,
        s.shipment_id,s.transport_id FROM blood_allocation a JOIN blood_request q USING(request_id)
        JOIN institution o ON o.institution_id=a.origin_id JOIN institution d ON d.institution_id=a.destination_id
        JOIN resource b USING(resource_id) JOIN blood_unit u USING(resource_id)
        LEFT JOIN shipment s USING(allocation_id) WHERE allocation_id=%s'''+(' FOR UPDATE OF a' if lock else ''),(identifier,)).fetchone()
    if not row or row['region_name']!=actor.region_name:
        raise BusinessError('La asignación no está disponible.',404)
    if actor.role_code=='TRANSPORT':
        allowed=row['transport_id']==actor.account_id
    else:
        allowed=actor.institution_id is None or actor.institution_id in (row['origin_id'],row['destination_id'])
    if not allowed:
        raise BusinessError('La asignación no está disponible en tu ámbito.',404)
    # La evidencia de autorización solo necesita la identidad y el hecho de aprobación.
    if not actor.can('allocation.authorize'):
        row.pop('authorization_reason',None)
    return row


def list_allocations(actor,page=1,query='',status='',shipment_status='',direction=''):
    if not (actor.can('logistics') or actor.can('trace.read')):
        raise BusinessError('No tienes permiso de logística.',403)
    clause='o.region_name=%s'; params=[actor.region_name]
    if actor.role_code=='TRANSPORT':
        clause+=' AND s.transport_id=%s';params.append(actor.account_id)
    elif actor.institution_id:
        clause+=' AND (a.origin_id=%s OR a.destination_id=%s)';params += [actor.institution_id]*2
    if direction:
        v.choice({'direction':direction},'direction',('destination',),'dirección')
        if actor.institution_id:
            clause+=' AND a.destination_id=%s';params.append(actor.institution_id)
    clause+=' AND (b.traceability_code ILIKE %s OR q.request_code ILIKE %s OR o.institution_name ILIKE %s OR d.institution_name ILIKE %s)'
    params += [pattern(query)] * 4
    if status == 'ACTIVE':
        clause+=" AND a.current_status IN ('RESERVED','ASSIGNED')"
    elif status:
        v.choice({'status':status},'status',('RESERVED','ASSIGNED','RECEIVED','CANCELLED'),'asignación')
        clause+=' AND a.current_status=%s'; params.append(status)
    if shipment_status == 'ACTIVE':
        clause+=" AND s.current_status NOT IN ('ACCEPTED','CANCELLED')"
    elif shipment_status:
        v.choice({'state':shipment_status},'state',('SCHEDULED','PREPARED','COLLECTED','IN_TRANSIT','DELIVERED','ACCEPTED','CANCELLED'),'traslado')
        clause+=' AND s.current_status=%s'; params.append(shipment_status)
    with transaction() as conn:
        source=''' FROM blood_allocation a JOIN institution o ON o.institution_id=a.origin_id
            JOIN institution d ON d.institution_id=a.destination_id JOIN resource b USING(resource_id)
            JOIN blood_request q USING(request_id) LEFT JOIN shipment s USING(allocation_id) WHERE '''+clause
        rows=conn.execute('''SELECT a.allocation_id,a.current_status,a.reserved_at,b.traceability_code,
            q.request_code,o.institution_name AS origin_name,d.institution_name AS destination_name,s.shipment_id,s.current_status AS shipment_status'''+source+
            ' ORDER BY a.reserved_at DESC,a.allocation_id LIMIT 12 OFFSET %s',[*params,(page-1)*12]).fetchall()
        r.event(conn,actor,'READ','BLOOD_ALLOCATION','LIST',actor.institution_id)
        return rows,conn.execute('SELECT count(*) AS n'+source,params).fetchone()['n']


def cancel(actor,identifier,data):
    require(actor,'shipment.plan')
    with transaction() as conn:
        # Mismo orden de bloqueo que reserva/cierre: solicitud, asignación, unidad.
        initial=allocation_row(conn,actor,identifier)
        conn.execute('SELECT request_id FROM blood_request WHERE request_id=%s FOR UPDATE',(initial['request_id'],))
        row=allocation_row(conn,actor,identifier,True)
        check_version(row,v.integer(data,'version_no'))
        if row['current_status'] not in ('RESERVED','ASSIGNED'):
            raise BusinessError('No se puede cancelar una entrega iniciada o terminada.',409)
        shipment=conn.execute('SELECT * FROM shipment WHERE allocation_id=%s FOR UPDATE',(identifier,)).fetchone()
        if shipment and shipment['current_status'] not in ('SCHEDULED','PREPARED'):
            raise BusinessError('La recolección ya comenzó. Registra la incidencia y conserva la custodia.',409)
        reason=v.paragraph(data,'observation','el motivo',240)
        conn.execute('SELECT resource_id FROM blood_unit WHERE resource_id=%s FOR UPDATE',(row['resource_id'],))
        conn.execute("UPDATE blood_allocation SET current_status='CANCELLED',version_no=version_no+1 WHERE allocation_id=%s",(identifier,))
        conn.execute("UPDATE blood_unit SET current_status='AVAILABLE',version_no=version_no+1 WHERE resource_id=%s",(row['resource_id'],))
        if shipment:
            conn.execute("UPDATE shipment SET current_status='CANCELLED',version_no=version_no+1 WHERE shipment_id=%s",(shipment['shipment_id'],))
            custody(conn,actor,shipment['shipment_id'],'CANCELLED',row['origin_name'],reason,'Cancelación administrativa registrada')
        r.move_unit(conn,actor,row['resource_id'],'RESERVED','AVAILABLE',row['location_id'],row['location_id'],'Cancelación de reserva DEMO')
        conn.execute('UPDATE blood_request SET version_no=version_no+1 WHERE request_id=%s',(row['request_id'],))
        r.request_event(conn,actor,row['request_id'],'CANCEL_RESERVE','Reserva cancelada; historial conservado')
        r.event(conn,actor,'CANCEL','BLOOD_ALLOCATION',identifier,row['origin_id'])


def plan(actor,identifier,data):
    require(actor,'shipment.plan')
    with transaction() as conn:
        row=allocation_row(conn,actor,identifier,True)
        check_version(row,v.integer(data,'version_no'))
        if row['current_status']!='RESERVED' or row['shipment_id']:
            raise BusinessError('La reserva ya tiene traslado o no está activa.',409)
        transport=accounts.by_id(conn,v.identifier(data,'transport_id'))
        from .auth import active
        if not active(transport) or transport['role_code']!='TRANSPORT' or transport['institution_id']!=row['origin_id']:
            raise BusinessError('Selecciona personal de traslado activo de la institución de origen.')
        departure=v.timestamp(data,'departure_at');eta=v.timestamp(data,'eta')
        route=conn.execute('SELECT * FROM regional_route WHERE origin_id=%s AND destination_id=%s',(row['origin_id'],row['destination_id'])).fetchone()
        if not route or departure<r.now()-timedelta(minutes=5) or eta<=departure or eta>=row['expires_at'] or eta<departure+timedelta(minutes=route['travel_minutes']):
            raise BusinessError('Revisa salida, ETA, ruta registrada y caducidad capturada.')
        for iid in (row['origin_id'],row['destination_id']):
            if not conn.execute("SELECT 1 FROM institution WHERE institution_id=%s AND participation_status='ACTIVE'",(iid,)).fetchone():
                raise BusinessError('Una institución está inactiva.',409)
        shipment=insert(conn,'shipment',dict(allocation_id=identifier,transport_id=transport['account_id'],
            vehicle=v.text(data,'vehicle','el vehículo'),departure_at=departure,eta=eta),'shipment_id')
        conn.execute("UPDATE blood_allocation SET current_status='ASSIGNED',version_no=version_no+1 WHERE allocation_id=%s",(identifier,))
        custody(conn,actor,shipment['shipment_id'],'SCHEDULED',row['origin_name'],'Traslado programado','Orden de traslado '+str(shipment['shipment_id']))
        r.event(conn,actor,'ASSIGN','BLOOD_ALLOCATION',identifier,row['origin_id'],transport_id=transport['account_id'],
                audit_reason=v.paragraph(data,'audit_reason','el motivo de la programación (sin datos sensibles)',240))
        return shipment['shipment_id']


def custody(conn,actor,shipment_id,status,location,observation,evidence):
    sequence=conn.execute('SELECT coalesce(max(sequence),0)+1 AS n FROM custody_event WHERE shipment_id=%s',(shipment_id,)).fetchone()['n']
    return insert(conn,'custody_event',dict(shipment_id=shipment_id,sequence=sequence,status=status,actor_id=actor.account_id,
        location_description=location,observation=observation,evidence_reference=evidence),'event_id')


def step(actor,identifier,data):
    require(actor,'logistics')
    with transaction() as conn:
        row=allocation_row(conn,actor,identifier,True)
        shipment=conn.execute('SELECT * FROM shipment WHERE allocation_id=%s FOR UPDATE',(identifier,)).fetchone()
        if not shipment:
            raise BusinessError('Primero debe programarse el traslado.',409)
        check_version(shipment,v.integer(data,'version_no'))
        target=v.choice(data,'status',('PREPARED','COLLECTED','IN_TRANSIT','DELIVERED','ACCEPTED','INCIDENT'),'evento')
        allowed={'SCHEDULED':'PREPARED','PREPARED':'COLLECTED','COLLECTED':'IN_TRANSIT','IN_TRANSIT':'DELIVERED','DELIVERED':'ACCEPTED'}
        if shipment['current_status'] in ('ACCEPTED','CANCELLED') or (target!='INCIDENT' and allowed.get(shipment['current_status'])!=target):
            raise BusinessError('El evento no corresponde a la etapa actual.',409)
        if target=='PREPARED':
            permitted=actor.role_code=='OPERATOR' and actor.institution_id==row['origin_id']
        elif target=='ACCEPTED':
            permitted=actor.role_code in ('OPERATOR','MEDICAL') and actor.institution_id==row['destination_id']
        elif target=='INCIDENT':
            permitted=actor.role_code in ('OPERATOR','MEDICAL','COORDINATOR') or shipment['transport_id']==actor.account_id
        else:
            permitted=actor.role_code=='TRANSPORT' and shipment['transport_id']==actor.account_id
        if not permitted:
            raise BusinessError('Tu perfil no puede registrar este evento en esta asignación.',403)
        observation=v.paragraph(data,'observation','la observación sin datos clínicos',1000)
        location=v.text(data,'location_description','la ubicación del evento',240)
        evidence=v.text(data,'evidence_reference','la referencia de evidencia',240)
        unit=conn.execute('SELECT * FROM blood_unit WHERE resource_id=%s FOR UPDATE',(row['resource_id'],)).fetchone()
        if target in ('PREPARED','COLLECTED','IN_TRANSIT') and (unit['expires_at']<=r.now() or shipment['eta']>=unit['expires_at']):
            raise BusinessError('La viabilidad temporal capturada no permite iniciar el traslado. Registra la incidencia.',409)
        if target=='ACCEPTED':
            if unit['expires_at'] <= r.now():
                raise BusinessError('La unidad llegó caducada: registra una incidencia; no puede aceptarse ni cerrar la solicitud como atendida.',409)
            destination=r.own_institution(conn,actor,row['destination_id'])
            loc=network.one(conn,'locations',actor,v.identifier(data,'location_id'))
            if not loc or not loc['is_active'] or loc['institution_id']!=destination['institution_id']:
                raise BusinessError('Selecciona una ubicación activa de la institución receptora.')
            r.permitted_reference(conn,'sites',actor,loc['site_id'])
            target_state='DELIVERED'
            conn.execute('UPDATE blood_unit SET current_status=%s,location_id=%s,version_no=version_no+1 WHERE resource_id=%s',
                         (target_state,loc['location_id'],row['resource_id']))
            conn.execute("UPDATE blood_allocation SET current_status='RECEIVED',received_at=now(),version_no=version_no+1 WHERE allocation_id=%s",(identifier,))
            r.move_unit(conn,actor,row['resource_id'],unit['current_status'],target_state,unit['location_id'],loc['location_id'],'Recepción documentada; no implica transfusión')
        elif target=='IN_TRANSIT':
            conn.execute("UPDATE blood_allocation SET current_status='IN_TRANSIT',version_no=version_no+1 WHERE allocation_id=%s",(identifier,))
            conn.execute("UPDATE blood_unit SET current_status='IN_TRANSIT',version_no=version_no+1 WHERE resource_id=%s",(row['resource_id'],))
            r.move_unit(conn,actor,row['resource_id'],unit['current_status'],'IN_TRANSIT',unit['location_id'],unit['location_id'],'Salida bajo custodia')
        if target!='INCIDENT':
            conn.execute('UPDATE shipment SET current_status=%s,version_no=version_no+1 WHERE shipment_id=%s',(target,shipment['shipment_id']))
        else:
            conn.execute('UPDATE shipment SET version_no=version_no+1 WHERE shipment_id=%s',(shipment['shipment_id'],))
        custody(conn,actor,shipment['shipment_id'],target,location,observation,evidence)
        r.event(conn,actor,target,'SHIPMENT',shipment['shipment_id'],actor.institution_id or row['origin_id'])
