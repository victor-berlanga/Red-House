"""Proceso sanguíneo académico integrado. Toda escritura conserva auditoría atómica."""
from datetime import datetime, timezone

from psycopg import sql

from .. import validators as v
from ..access import BusinessError, check_version, require
from ...data_access.connection import transaction
from ...data_access.repositories import audit, inventory, network
from ...data_access.repositories.common import insert, scope, pattern
from .administration import permitted_reference


def now():
    return datetime.now(timezone.utc)


def event(conn, actor, action, entity, row_id, institution_id, *, audit_reason='Proceso regional académico', **values):
    # Solo identificadores/estados: nunca antecedentes, estudios o justificaciones clínicas.
    audit.record(conn, actor, action, entity, row_id, audit_reason,
                 institution_id=institution_id, after=values)


def own_institution(conn, actor, institution_id):
    return permitted_reference(conn, 'institutions', actor, institution_id)


def person(conn, actor, kind, identifier, *, lock=False):
    if kind not in ('donor', 'recipient'):
        raise ValueError(kind)
    require(actor, 'donor.write' if kind == 'donor' else 'recipient.write')
    clause, params = scope(actor, 'i')
    row = conn.execute(sql.SQL('SELECT p.*, i.region_name, i.institution_name FROM {} p '
        'JOIN institution i USING (institution_id) WHERE ' + clause + ' AND {}=%s' +
        (' FOR UPDATE OF p' if lock else '')).format(sql.Identifier(kind), sql.Identifier(kind+'_id')),
        [*params, identifier]).fetchone()
    if not row:
        raise BusinessError('El expediente no está disponible en tu ámbito.', 404)
    return row


def people(actor, kind, query='', page=1):
    require(actor, 'donor.write' if kind == 'donor' else 'recipient.write')
    clause, params = scope(actor, 'i')
    with transaction() as conn:
        source = sql.SQL(' FROM {} p JOIN institution i USING(institution_id) WHERE ' + clause +
                         ' AND (p.record_code ILIKE %s OR p.display_name ILIKE %s)').format(sql.Identifier(kind))
        params += [pattern(query)] * 2
        total = conn.execute(sql.SQL('SELECT count(*) AS n') + source, params).fetchone()['n']
        history = sql.SQL('EXISTS(SELECT 1 FROM {} h WHERE h.{}=p.{}) AS has_history').format(
            sql.Identifier('donation' if kind=='donor' else 'blood_request'),sql.Identifier(kind+'_id'),sql.Identifier(kind+'_id'))
        rows = conn.execute(sql.SQL('SELECT p.*, i.institution_name, ') + history + source +
            sql.SQL(' ORDER BY registered_at DESC, record_code LIMIT 12 OFFSET %s'), [*params,(page-1)*12]).fetchall()
        event(conn, actor, 'SENSITIVE_READ', kind.upper(), 'LIST', actor.institution_id)
        return rows, total


def save_person(actor, kind, data, identifier=None):
    require(actor, 'donor.write' if kind == 'donor' else 'recipient.write')
    with transaction() as conn:
        existing = person(conn, actor, kind, identifier, lock=True) if identifier else None
        if existing:
            check_version(existing, v.integer(data, 'version_no'))
        institution = own_institution(conn, actor, v.identifier(data, 'institution_id'))
        if existing and institution['institution_id'] != existing['institution_id']:
            raise BusinessError('Un expediente no cambia de institución.', 409)
        values = dict(institution_id=institution['institution_id'],
                      record_code=v.code(data,'record_code','el folio del expediente'),
                      display_name=v.text(data,'display_name','el nombre'),
                      blood_group=v.choice(data,'blood_group',inventory.GROUPS,'ABO/Rh'),
                      restrictions=v.paragraph(data,'restrictions','las restricciones o su ausencia',1000))
        if kind == 'donor':
            consent_at = v.timestamp(data,'consent_at')
            if consent_at > now():
                raise BusinessError('El consentimiento no puede tener fecha futura.')
            values.update(donation_kind=v.choice(data,'donation_kind',('VOLUNTARY','REPLACEMENT'),'tipo de donación'),
                background=v.paragraph(data,'background','los antecedentes',1000),
                consent_reference=v.text(data,'consent_reference','la referencia de consentimiento',240),
                consent_at=consent_at, current_status='PENDING')
            if existing and conn.execute('SELECT 1 FROM donation WHERE donor_id=%s LIMIT 1',(identifier,)).fetchone():
                raise BusinessError('El donante ya tiene donaciones: registra una nueva revisión; no reescribas su identificación histórica.',409)
            if not existing:
                values['created_by'] = actor.account_id
        else:
            if existing and conn.execute("SELECT 1 FROM blood_request WHERE recipient_id=%s LIMIT 1",(identifier,)).fetchone():
                raise BusinessError('El expediente ya respalda solicitudes. Para preservar su historia no se reescribe; una corrección requiere un expediente versionado posterior.',409)
            values.update(requirement=v.paragraph(data,'requirement','el requerimiento',1000),
                          urgency=v.choice({'urgency':data.get('urgency','ROUTINE')},'urgency',('URGENT','PRIORITY','ROUTINE'),'urgencia registrada'),
                          studies=v.paragraph(data,'studies','los estudios',1000),
                          responsible_id=actor.account_id,
                          current_status=v.choice(data,'current_status',('ACTIVE','INACTIVE'),'estado'))
        if existing:
            from ...data_access.repositories.common import update
            row = update(conn, kind, kind+'_id', identifier, values, existing['version_no'])
        else:
            row = insert(conn,kind,values,kind+'_id')
        event(conn,actor,'UPDATE' if existing else 'CREATE',kind.upper(),row[kind+'_id'],institution['institution_id'],
              audit_reason=v.paragraph(data,'audit_reason','el motivo del cambio (sin datos clínicos)',240) if existing else 'Registro de expediente')
        return row[kind+'_id']


def person_detail(actor, kind, identifier):
    with transaction() as conn:
        row = person(conn,actor,kind,identifier)
        event(conn,actor,'SENSITIVE_READ',kind.upper(),identifier,row['institution_id'])
        related = conn.execute('SELECT r.*, p.party_name FROM donor_review r JOIN user_account u ON u.account_id=r.actor_id JOIN party p USING(party_id) WHERE donor_id=%s ORDER BY occurred_at DESC',
                               (identifier,)).fetchall() if kind == 'donor' else []
        return row, related


def review_donor(actor, identifier, data):
    require(actor,'donor.review')
    with transaction() as conn:
        row = person(conn,actor,'donor',identifier,lock=True)
        check_version(row,v.integer(data,'version_no'))
        own_institution(conn,actor,row['institution_id'])
        decision=v.choice(data,'decision',('ELIGIBLE','DEFERRED'),'decisión humana')
        if data.get('human_confirmation') != 'on':
            raise BusinessError('Confirma que registras una decisión humana autorizada para el ejercicio.')
        review=insert(conn,'donor_review',dict(donor_id=identifier,decision=decision,
            reason=v.paragraph(data,'reason','el fundamento de revisión',1000),actor_id=actor.account_id),'review_id')
        conn.execute('UPDATE donor SET current_status=%s,version_no=version_no+1 WHERE donor_id=%s',(decision,identifier))
        event(conn,actor,'AUTHORIZE','DONOR_REVIEW',review['review_id'],row['institution_id'],decision=decision)


def donation_row(conn, actor, identifier, lock=False):
    require(actor,'donor.write')
    clause, params=scope(actor,'i')
    row=conn.execute('''SELECT d.*, p.institution_id, p.record_code AS donor_code, p.blood_group,
        p.current_status AS donor_status, i.region_name, i.institution_name
        FROM donation d JOIN donor p USING(donor_id) JOIN institution i USING(institution_id)
        WHERE '''+clause+' AND donation_id=%s'+(' FOR UPDATE OF d' if lock else ''),[*params,identifier]).fetchone()
    if not row:
        raise BusinessError('La donación no está disponible en tu ámbito.',404)
    return row


def donations(actor, page=1, query='', status=''):
    require(actor,'donor.write')
    with transaction() as conn:
        clause,params=scope(actor,'i')
        clause+=' AND (d.donation_code ILIKE %s OR p.record_code ILIKE %s)'
        params += [pattern(query)] * 2
        if status:
            v.choice({'status':status},'status',('REGISTERED','COLLECTED','PROCESSED','CANCELLED'),'estado')
            clause+=' AND d.current_status=%s'; params.append(status)
        source=' FROM donation d JOIN donor p USING(donor_id) JOIN institution i USING(institution_id) WHERE '+clause
        rows=conn.execute('SELECT d.*,p.record_code AS donor_code,i.institution_name'+source+
                          ' ORDER BY registered_at DESC,donation_id LIMIT 12 OFFSET %s',[*params,(page-1)*12]).fetchall()
        event(conn,actor,'SENSITIVE_READ','DONATION','LIST',actor.institution_id)
        return rows,conn.execute('SELECT count(*) AS n'+source,params).fetchone()['n']


def create_donation(actor,data):
    require(actor,'donation.write')
    with transaction() as conn:
        donor=person(conn,actor,'donor',v.identifier(data,'donor_id'),lock=True)
        own_institution(conn,actor,donor['institution_id'])
        if donor['current_status']!='ELIGIBLE':
            raise BusinessError('Se requiere una revisión humana de elegibilidad registrada.',409)
        review=conn.execute('SELECT * FROM donor_review WHERE donor_id=%s ORDER BY occurred_at DESC,review_id DESC LIMIT 1',(donor['donor_id'],)).fetchone()
        if not review or review['decision']!='ELIGIBLE':
            raise BusinessError('No existe una revisión vigente favorable.',409)
        row=insert(conn,'donation',dict(donor_id=donor['donor_id'],review_id=review['review_id'],
                   donation_code=v.code(data,'donation_code','el folio de donación'),created_by=actor.account_id),'donation_id')
        insert(conn,'donation_event',dict(donation_id=row['donation_id'],status='REGISTERED',actor_id=actor.account_id,
               observation='Registro asociado a revisión humana documentada'),'event_id')
        event(conn,actor,'CREATE','DONATION',row['donation_id'],donor['institution_id'])
        return row['donation_id']


def progress_donation(actor,identifier,data):
    require(actor,'donation.write')
    with transaction() as conn:
        row=donation_row(conn,actor,identifier,True)
        check_version(row,v.integer(data,'version_no'))
        own_institution(conn,actor,row['institution_id'])
        target=v.choice(data,'status',('COLLECTED','PROCESSED','CANCELLED'),'estado')
        allowed={'REGISTERED':('COLLECTED','CANCELLED'),'COLLECTED':('PROCESSED','CANCELLED')}
        if target not in allowed.get(row['current_status'],()):
            raise BusinessError('Transición de donación no permitida.',409)
        if target!='CANCELLED':
            donor=person(conn,actor,'donor',row['donor_id'],lock=True)
            if donor['current_status']!='ELIGIBLE':
                raise BusinessError('La revisión vigente del donante no permite continuar.',409)
        observation=v.paragraph(data,'observation','la evidencia de la etapa',1000)
        conn.execute('UPDATE donation SET current_status=%s,version_no=version_no+1 WHERE donation_id=%s',(target,identifier))
        if target in ('COLLECTED','PROCESSED'):
            column='collected_at' if target=='COLLECTED' else 'processed_at'
            conn.execute(sql.SQL('UPDATE donation SET {}=now() WHERE donation_id=%s').format(sql.Identifier(column)),(identifier,))
        insert(conn,'donation_event',dict(donation_id=identifier,status=target,actor_id=actor.account_id,observation=observation),'event_id')
        event(conn,actor,target,'DONATION',identifier,row['institution_id'])


def produce_unit(actor,identifier,data):
    require(actor,'unit.release')
    with transaction() as conn:
        row=donation_row(conn,actor,identifier,True)
        own_institution(conn,actor,row['institution_id'])
        if row['current_status']!='PROCESSED' or row['donor_status']!='ELIGIBLE':
            raise BusinessError('Se requiere una donación procesada y revisión vigente del donante.',409)
        if data.get('human_confirmation')!='on':
            raise BusinessError('Confirma la revisión y autorización de liberación de la unidad.')
        expires=v.timestamp(data,'expires_at')
        if expires <= now() or expires<=row['collected_at']:
            raise BusinessError('La fecha capturada de caducidad debe ser posterior a recolección y liberación.')
        location=permitted_reference(conn,'locations',actor,v.identifier(data,'location_id'))
        permitted_reference(conn,'sites',actor,location['site_id'])
        if location['institution_id']!=row['institution_id']:
            raise BusinessError('La unidad nace en la institución de la donación.',403)
        component=permitted_reference(conn,'components',actor,v.identifier(data,'component_id'))
        reference=v.paragraph(data,'release_reference','la referencia de pruebas y liberación humana',240)
        resource=insert(conn,'resource',dict(traceability_code=v.code(data,'traceability_code','el folio de unidad')),'resource_id')
        rid=resource['resource_id']
        insert(conn,'blood_unit',dict(resource_id=rid,component_id=component['component_id'],location_id=location['location_id'],
               collected_at=row['collected_at'],expires_at=expires,current_status='AVAILABLE'),'resource_id')
        insert(conn,'blood_classification',dict(resource_id=rid,recorded_group_code=row['blood_group'],source_reference=row['donation_code']),'resource_id')
        insert(conn,'donation_unit',dict(resource_id=rid,donation_id=identifier,released_by=actor.account_id,release_reference=reference),'resource_id')
        move_unit(conn,actor,rid,None,'AVAILABLE',None,location['location_id'],'Liberación humana de componente DEMO')
        event(conn,actor,'AUTHORIZE','BLOOD_UNIT',rid,row['institution_id'],donation_id=identifier)
        return rid


def move_unit(conn,actor,rid,previous,target,origin,destination,reason):
    sequence=conn.execute('SELECT coalesce(max(sequence),0)+1 AS n FROM blood_movement WHERE resource_id=%s',(rid,)).fetchone()['n']
    insert(conn,'blood_movement',dict(resource_id=rid,sequence=sequence,previous_status=previous,new_status=target,
           origin_location_id=origin,destination_location_id=destination,actor_id=actor.account_id,reason=reason),'movement_id')


def request_row(conn,actor,identifier,*,clinical=False,lock=False):
    require(actor,'request.write' if clinical else 'regional.read')
    # Los coordinadores regionales consultan folios y requisitos, nunca expediente clínico.
    clause,params=scope(actor,'i')
    row=conn.execute('''SELECT q.*, r.institution_id,r.blood_group,r.version_no AS recipient_version,
        r.current_status AS recipient_status,i.region_name,i.institution_name,c.component_code,c.component_name
        FROM blood_request q JOIN recipient r USING(recipient_id) JOIN institution i USING(institution_id)
        JOIN blood_component c USING(component_id) WHERE '''+clause+' AND request_id=%s'+(' FOR UPDATE OF q' if lock else ''),[*params,identifier]).fetchone()
    if not row:
        raise BusinessError('La solicitud no está disponible en tu ámbito.',404)
    if not actor.can('request.write'):
        row.pop('justification',None)
        row.pop('recipient_id',None)
    return row


def create_request(actor,data):
    require(actor,'request.write')
    with transaction() as conn:
        rec=person(conn,actor,'recipient',v.identifier(data,'recipient_id'),lock=True)
        own_institution(conn,actor,rec['institution_id'])
        if rec['current_status']!='ACTIVE':
            raise BusinessError('El receptor está inactivo.',409)
        component=permitted_reference(conn,'components',actor,v.identifier(data,'component_id'))
        row=insert(conn,'blood_request',dict(request_code=v.code(data,'request_code','el folio de solicitud'),
            recipient_id=rec['recipient_id'],component_id=component['component_id'],quantity=v.integer(data,'quantity',1,100),
            urgency=v.choice(data,'urgency',('URGENT','PRIORITY','ROUTINE'),'urgencia registrada'),
            justification=v.paragraph(data,'justification','la justificación clínica',1000),responsible_id=actor.account_id),'request_id')
        request_event(conn,actor,row['request_id'],'CREATE','Solicitud registrada por personal médico')
        event(conn,actor,'CREATE','BLOOD_REQUEST',row['request_id'],rec['institution_id'],urgency=row['urgency'],quantity=row['quantity'])
        return row['request_id']


def request_event(conn,actor,identifier,action,observation):
    insert(conn,'request_event',dict(request_id=identifier,action=action,actor_id=actor.account_id,observation=observation),'event_id')


def requests_list(actor,page=1,query='',status='',urgency=''):
    require(actor,'regional.read')
    with transaction() as conn:
        clause,params=scope(actor,'i')
        clause+=' AND q.request_code ILIKE %s'
        params.append(pattern(query))
        if status and status != 'ACTIVE':
            if status not in ('OPEN','IN_PROGRESS','CLOSED','CANCELLED'):
                raise BusinessError('Estado de solicitud no válido.')
            clause+=' AND q.current_status=%s'; params.append(status)
        if status == 'ACTIVE':
            clause+=" AND q.current_status IN ('OPEN','IN_PROGRESS')"
        if urgency:
            v.choice({'urgency':urgency},'urgency',('URGENT','PRIORITY','ROUTINE'),'urgencia')
            clause+=' AND q.urgency=%s'; params.append(urgency)
        source=' FROM blood_request q JOIN recipient r USING(recipient_id) JOIN institution i USING(institution_id) JOIN blood_component c USING(component_id) WHERE '+clause
        rows=conn.execute('''SELECT q.request_id,q.request_code,q.quantity,q.urgency,q.current_status,q.requested_at,
             r.blood_group,i.institution_name,c.component_name'''+source+''' ORDER BY
             CASE q.urgency WHEN 'URGENT' THEN 0 WHEN 'PRIORITY' THEN 1 ELSE 2 END,q.requested_at,q.request_id LIMIT 12 OFFSET %s''',[*params,(page-1)*12]).fetchall()
        event(conn,actor,'READ','BLOOD_REQUEST','LIST',actor.institution_id)
        return rows,conn.execute('SELECT count(*) AS n'+source,params).fetchone()['n']


def close_request(actor,identifier,data):
    require(actor,'request.write')
    with transaction() as conn:
        row=request_row(conn,actor,identifier,clinical=True,lock=True)
        check_version(row,v.integer(data,'version_no'))
        if row['current_status'] not in ('OPEN','IN_PROGRESS'):
            raise BusinessError('La solicitud ya terminó.',409)
        target=v.choice(data,'status',('CLOSED','CANCELLED'),'cierre')
        allocations=conn.execute("SELECT current_status FROM blood_allocation WHERE request_id=%s AND current_status<>'CANCELLED'",(identifier,)).fetchall()
        if target=='CANCELLED' and allocations:
            raise BusinessError('Cancela las reservas sin traslado antes de cancelar la solicitud; una entrega recibida debe cerrarse.',409)
        if target=='CLOSED' and (len(allocations)!=row['quantity'] or any(a['current_status']!='RECEIVED' for a in allocations)):
            raise BusinessError('El cierre exige recibir todas las unidades solicitadas.',409)
        conn.execute('UPDATE blood_request SET current_status=%s,closed_at=now(),version_no=version_no+1 WHERE request_id=%s',(target,identifier))
        request_event(conn,actor,identifier,target,v.paragraph(data,'observation','el motivo del cierre',240))
        event(conn,actor,target,'BLOOD_REQUEST',identifier,row['institution_id'])


def save_route(actor,data,identifier=None):
    require(actor,'route.write')
    with transaction() as conn:
        origin=own_institution(conn,actor,v.identifier(data,'origin_id'))
        dest=own_institution(conn,actor,v.identifier(data,'destination_id'))
        if identifier:
            previous=conn.execute('SELECT * FROM regional_route WHERE route_id=%s AND origin_id=%s AND destination_id=%s FOR UPDATE',(identifier,origin['institution_id'],dest['institution_id'])).fetchone()
            check_version(previous,v.integer(data,'version_no'))
        distance=v.integer(data,'distance_km',0,5000)
        minutes=v.integer(data,'travel_minutes',1,10080)
        source=v.paragraph(data,'source_reference','la fuente de la estimación',240)
        row=conn.execute('''INSERT INTO regional_route(origin_id,destination_id,distance_km,travel_minutes,source_reference,recorded_by)
            VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(origin_id,destination_id) DO UPDATE
            SET distance_km=excluded.distance_km,travel_minutes=excluded.travel_minutes,source_reference=excluded.source_reference,
                recorded_by=excluded.recorded_by,recorded_at=now(),version_no=regional_route.version_no+1 RETURNING *''',
            (origin['institution_id'],dest['institution_id'],distance,minutes,source,actor.account_id)).fetchone()
        event(conn,actor,'UPDATE','REGIONAL_ROUTE',row['route_id'],origin['institution_id'],distance_km=distance,travel_minutes=minutes,version_no=row['version_no'],
              audit_reason=v.paragraph(data,'audit_reason','el motivo del cambio (sin datos sensibles)',240))
