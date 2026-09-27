"""Coordinación demostrativa de órganos; los dictámenes siempre son humanos."""
from uuid import uuid4
from datetime import timedelta
from psycopg import sql
from .. import validators as v
from ..access import BusinessError, require, check_version
from ...data_access.connection import transaction
from ...data_access.repositories.common import insert, scope, pattern
from ...data_access.repositories import accounts
from . import regional as r
from .auth import active

TYPES = {'KIDNEY':'Riñón','LIVER':'Hígado','HEART':'Corazón'}
VERSION = 'ORGAN-DEMO-1.0'
NOTICE = 'Preselección demostrativa por tipo y ABO idéntico. No determina compatibilidad clínica. Requiere evaluación humana de estudios, HLA, tamaño y prueba cruzada.'
STATES = {'AVAILABLE':'Disponible','RESERVED':'Reservado','SCHEDULED':'Programado','PREPARED':'Preparado','COLLECTED':'Recolectado','IN_TRANSIT':'En tránsito','DELIVERED':'Entregado','ACCEPTED':'Recepción aceptada','RECEIVED':'Recibido','WITHDRAWN':'Retirado','CANCELLED':'Cancelado','ACTIVE':'Activo','INACTIVE':'Inactivo','CLOSED':'Cerrado','INCIDENT':'Incidencia','FAVORABLE':'Favorable','REJECTED':'No favorable','URGENT':'Urgente','PRIORITY':'Prioritaria','ROUTINE':'Ordinaria','LIVING':'Vivo','DECEASED':'Fallecido'}


def confirm(data):
    if data.get('human_confirmation') != 'on':
        raise BusinessError('Confirma la evaluación humana autorizada para el ejercicio.')


def own(actor, institution_id):
    if not actor.institution_id or str(actor.institution_id) != str(institution_id):
        raise BusinessError('Esta operación corresponde al personal de la institución responsable.',403)


def institution(conn, identifier, region):
    row=conn.execute("SELECT * FROM institution WHERE institution_id=%s AND region_name=%s AND participation_status='ACTIVE'",(identifier,region)).fetchone()
    if not row: raise BusinessError('La institución no está activa en la región.',409)
    return row


def create_person(actor, kind, data):
    require(actor,'organ.medical'); confirm(data)
    if kind not in ('donor','recipient'): raise BusinessError('Tipo de expediente inválido.')
    with transaction() as conn:
        institution(conn,actor.institution_id,actor.region_name)
        code=v.code(data,'record_code','el folio')
        if len(code)<6: raise BusinessError('El folio debe tener de 6 a 30 caracteres.')
        values=dict(institution_id=actor.institution_id,record_code=code,display_name=v.text(data,'display_name','el nombre ficticio'),
            abo=v.choice(data,'abo',('O','A','B','AB'),'ABO'),studies=v.paragraph(data,'studies','los estudios y restricciones'),
            hla=v.paragraph(data,'hla','el resultado HLA o su justificación'),clinical_reference=v.text(data,'clinical_reference','la referencia de evaluación',240))
        if kind=='donor':
            values.update(donation_kind=v.choice(data,'donation_kind',('LIVING','DECEASED'),'tipo de donante'),
                consent_reference=v.text(data,'consent_reference','el consentimiento',240),reviewed_by=actor.account_id)
        else:
            wait=v.timestamp(data,'waiting_since')
            if wait>r.now(): raise BusinessError('La fecha de espera no puede ser futura.')
            values.update(organ_type=v.choice(data,'organ_type',TYPES,'órgano'),urgency=v.choice(data,'urgency',('URGENT','PRIORITY','ROUTINE'),'urgencia'),
                waiting_since=wait,responsible_id=actor.account_id)
        key=kind+'_id';row=insert(conn,'organ_'+kind,values,key)
        r.event(conn,actor,'CREATE','ORGAN_'+kind.upper(),row[key],actor.institution_id)
        return row[key]


def people(actor,kind,query='',page=1):
    require(actor,'organ.medical')
    if kind not in ('donor','recipient'): raise BusinessError('Expediente inexistente.',404)
    with transaction() as conn:
        rows=conn.execute(sql.SQL('SELECT * FROM {} WHERE institution_id=%s AND record_code ILIKE %s ORDER BY registered_at DESC LIMIT 12 OFFSET %s').format(sql.Identifier('organ_'+kind)),
            (actor.institution_id,pattern(query),(page-1)*12)).fetchall()
        r.event(conn,actor,'SENSITIVE_READ','ORGAN_'+kind.upper(),'LIST',actor.institution_id)
        return rows


def person_detail(actor,kind,identifier):
    require(actor,'organ.medical')
    if kind not in ('donor','recipient'): raise BusinessError('Expediente inexistente.',404)
    with transaction() as conn:
        row=conn.execute(sql.SQL('SELECT * FROM {} WHERE {}=%s AND institution_id=%s').format(sql.Identifier('organ_'+kind),sql.Identifier(kind+'_id')),(identifier,actor.institution_id)).fetchone()
        if not row: raise BusinessError('Expediente no disponible.',404)
        r.event(conn,actor,'SENSITIVE_READ','ORGAN_'+kind.upper(),identifier,actor.institution_id)
        return row


OFFER_SQL='''SELECT o.*,d.institution_id AS origin_id,d.abo,d.donation_kind,i.region_name,i.institution_name AS origin
 FROM organ_offer o JOIN organ_donor d USING(donor_id) JOIN institution i USING(institution_id)'''


def offer_row(conn,actor,identifier,lock=False):
    row=conn.execute(OFFER_SQL+' WHERE o.offer_id=%s AND i.region_name=%s'+(' FOR UPDATE OF o' if lock else ''),(identifier,actor.region_name)).fetchone()
    if not row: raise BusinessError('Órgano no disponible en tu región.',404)
    return row


def create_offer(actor,data):
    require(actor,'organ.medical');confirm(data)
    with transaction() as conn:
        donor=conn.execute('SELECT * FROM organ_donor WHERE donor_id=%s AND institution_id=%s',(v.identifier(data,'donor_id'),actor.institution_id)).fetchone()
        if not donor: raise BusinessError('Selecciona un donante de tu institución.',404)
        institution(conn,actor.institution_id,actor.region_name)
        typ=v.choice(data,'organ_type',TYPES,'órgano')
        if typ=='HEART' and donor['donation_kind']!='DECEASED': raise BusinessError('El corazón requiere un donante fallecido registrado.')
        recovered=v.timestamp(data,'recovered_at');until=v.timestamp(data,'preservation_until')
        if recovered>r.now() or until<=r.now() or until<=recovered: raise BusinessError('Revisa recuperación y límite de conservación autorizado.')
        row=insert(conn,'organ_offer',dict(donor_id=donor['donor_id'],record_code=v.code(data,'record_code','el folio del órgano'),organ_type=typ,
            anatomical_description=v.text(data,'anatomical_description','la descripción anatómica',240),recovered_at=recovered,preservation_until=until,
            preservation_reference=v.text(data,'preservation_reference','la referencia de liberación y conservación',240),released_by=actor.account_id),'offer_id')
        r.event(conn,actor,'AUTHORIZE','ORGAN_OFFER',row['offer_id'],actor.institution_id)
        return row['offer_id']


def offers(actor,query='',page=1):
    require(actor,'organ.read')
    with transaction() as conn:
        rows=conn.execute(OFFER_SQL+' WHERE i.region_name=%s AND o.record_code ILIKE %s ORDER BY o.registered_at DESC LIMIT 12 OFFSET %s',(actor.region_name,pattern(query),(page-1)*12)).fetchall()
        r.event(conn,actor,'READ','ORGAN_OFFER','LIST',actor.institution_id)
        return rows


def valid_pair(conn,actor,offer,recipient):
    institution(conn,offer['origin_id'],actor.region_name);institution(conn,recipient['institution_id'],actor.region_name)
    route=conn.execute('SELECT * FROM regional_route WHERE origin_id=%s AND destination_id=%s FOR SHARE',(offer['origin_id'],recipient['institution_id'])).fetchone()
    if (offer['current_status']!='AVAILABLE' or recipient['current_status']!='ACTIVE' or offer['organ_type']!=recipient['organ_type'] or offer['abo']!=recipient['abo']
        or not route or r.now()+timedelta(minutes=route['travel_minutes'])>=offer['preservation_until']):
        raise BusinessError('Disponibilidad, ABO, receptor, ruta o viabilidad cambiaron. Evalúa nuevamente.',409)
    return route


def evaluate(actor,identifier):
    require(actor,'organ.evaluate')
    with transaction() as conn:
        offer=offer_row(conn,actor,identifier,True)
        if offer['current_status']!='AVAILABLE': raise BusinessError('El órgano ya no está disponible.',409)
        institution(conn,offer['origin_id'],actor.region_name)
        rows=conn.execute('''SELECT p.*,t.version_no AS route_version,t.travel_minutes,t.distance_km
          FROM organ_recipient p JOIN institution i USING(institution_id)
          JOIN regional_route t ON t.destination_id=p.institution_id AND t.origin_id=%s
          WHERE i.region_name=%s AND i.participation_status='ACTIVE' AND p.current_status='ACTIVE'
          AND p.organ_type=%s AND p.abo=%s AND now()+t.travel_minutes*interval '1 minute'<%s
          ORDER BY CASE p.urgency WHEN 'URGENT' THEN 0 WHEN 'PRIORITY' THEN 1 ELSE 2 END,
          p.waiting_since,t.travel_minutes,t.distance_km,p.record_code''',(offer['origin_id'],actor.region_name,offer['organ_type'],offer['abo'],offer['preservation_until'])).fetchall()
        eid=insert(conn,'organ_evaluation',dict(offer_id=identifier,evaluated_by=actor.account_id,algorithm_version=VERSION),'evaluation_id')['evaluation_id']
        for rank,p in enumerate(rows,1):
            explanation=f"ABO idéntico {offer['abo']}; {TYPES[offer['organ_type']]}. Urgencia registrada: {STATES[p['urgency']]}; espera desde {p['waiting_since'].isoformat()}. Traslado {p['travel_minutes']} min / {p['distance_km']} km. Límite capturado: {offer['preservation_until'].isoformat()}. HLA, tamaño y prueba cruzada pendientes de dictamen humano. {VERSION}."
            insert(conn,'organ_candidate',dict(evaluation_id=eid,offer_id=identifier,recipient_id=p['recipient_id'],offer_version=offer['version_no'],recipient_version=p['version_no'],route_version=p['route_version'],rank_no=rank,
                algorithm_version=VERSION,explanation=explanation,distance_km=p['distance_km'],travel_minutes=p['travel_minutes'],evaluated_by=actor.account_id),'candidate_id')
        r.event(conn,actor,'EVALUATE','ORGAN_OFFER',identifier,offer['origin_id'],algorithm_version=VERSION,candidate_count=len(rows))
        return eid


CANDIDATE_SQL='''SELECT c.*,p.record_code AS recipient_code,p.institution_id AS destination_id,p.current_status AS recipient_status,
 i.region_name,i.institution_name AS destination FROM organ_candidate c JOIN organ_recipient p USING(recipient_id) JOIN institution i USING(institution_id)'''


def candidate_row(conn,actor,identifier):
    row=conn.execute(CANDIDATE_SQL+' WHERE c.candidate_id=%s AND i.region_name=%s',(identifier,actor.region_name)).fetchone()
    if not row: raise BusinessError('Candidato no disponible.',404)
    if actor.role_code=='MEDICAL': own(actor,row['destination_id'])
    return row


def detail(actor,identifier):
    require(actor,'organ.read')
    with transaction() as conn:
        offer=offer_row(conn,actor,identifier)
        # La vista regional expone folios seudonimizados, nunca estudios o identidades.
        candidates=conn.execute(CANDIDATE_SQL+''' WHERE c.offer_id=%s AND c.evaluation_id=(SELECT evaluation_id FROM organ_evaluation WHERE offer_id=%s ORDER BY evaluated_at DESC,evaluation_id DESC LIMIT 1)
            ORDER BY rank_no''',(identifier,identifier)).fetchall()
        r.event(conn,actor,'READ','ORGAN_OFFER',identifier,offer['origin_id'])
        return offer,candidates


def clinical_candidate(actor,identifier):
    require(actor,'organ.medical')
    with transaction() as conn:
        c=candidate_row(conn,actor,identifier);own(actor,c['destination_id'])
        p=conn.execute('SELECT * FROM organ_recipient WHERE recipient_id=%s',(c['recipient_id'],)).fetchone()
        d=conn.execute('''SELECT d.abo,d.hla,d.studies FROM organ_donor d JOIN organ_offer o USING(donor_id) WHERE o.offer_id=%s''',(c['offer_id'],)).fetchone()
        reviews=conn.execute('SELECT * FROM organ_review WHERE candidate_id=%s ORDER BY occurred_at DESC,review_id DESC',(identifier,)).fetchall()
        r.event(conn,actor,'SENSITIVE_READ','ORGAN_CANDIDATE',identifier,c['destination_id'])
        return c,p,d,reviews


def review(actor,identifier,data):
    require(actor,'organ.medical');confirm(data)
    with transaction() as conn:
        c=candidate_row(conn,actor,identifier);own(actor,c['destination_id'])
        o=offer_row(conn,actor,c['offer_id'],True)
        p=conn.execute('SELECT * FROM organ_recipient WHERE recipient_id=%s FOR UPDATE',(c['recipient_id'],)).fetchone()
        route=valid_pair(conn,actor,o,p)
        if (o['version_no'],p['version_no'],route['version_no'])!=(c['offer_version'],c['recipient_version'],c['route_version']): raise BusinessError('Evaluación obsoleta. Genera nuevos candidatos.',409)
        row=insert(conn,'organ_review',dict(candidate_id=identifier,decision=v.choice(data,'decision',('FAVORABLE','REJECTED'),'dictamen'),
            hla_assessment=v.paragraph(data,'hla_assessment','la interpretación HLA'),size_assessment=v.paragraph(data,'size_assessment','la evaluación de tamaño'),
            crossmatch_reference=v.text(data,'crossmatch_reference','la prueba cruzada o justificación',240),clinical_reference=v.text(data,'clinical_reference','la referencia médica',240),reviewed_by=actor.account_id),'review_id')
        r.event(conn,actor,'AUTHORIZE','ORGAN_REVIEW',row['review_id'],c['destination_id'],decision=row['decision'])
        return row['review_id']


def reserve(actor,identifier,data):
    require(actor,'organ.medical');confirm(data)
    with transaction() as conn:
        c=candidate_row(conn,actor,identifier);own(actor,c['destination_id'])
        o=offer_row(conn,actor,c['offer_id'],True)
        p=conn.execute('SELECT * FROM organ_recipient WHERE recipient_id=%s FOR UPDATE',(c['recipient_id'],)).fetchone()
        route=valid_pair(conn,actor,o,p)
        if (o['version_no'],p['version_no'],route['version_no'])!=(c['offer_version'],c['recipient_version'],c['route_version']) or c['algorithm_version']!=VERSION:
            raise BusinessError('Evaluación obsoleta. Genera nuevos candidatos.',409)
        rev=conn.execute('SELECT * FROM organ_review WHERE candidate_id=%s ORDER BY occurred_at DESC,review_id DESC LIMIT 1',(identifier,)).fetchone()
        if not rev or rev['decision']!='FAVORABLE' or str(rev['review_id'])!=str(data.get('review_id')):
            raise BusinessError('Se requiere el último dictamen humano favorable de esta pareja.',409)
        row=insert(conn,'organ_allocation',dict(candidate_id=identifier,review_id=rev['review_id'],offer_id=o['offer_id'],recipient_id=p['recipient_id'],authorized_by=actor.account_id,
            authorization_reference=v.text(data,'authorization_reference','la autorización',240)),'allocation_id')
        conn.execute("UPDATE organ_offer SET current_status='RESERVED',version_no=version_no+1 WHERE offer_id=%s",(o['offer_id'],))
        conn.execute("UPDATE organ_recipient SET current_status='RESERVED',version_no=version_no+1 WHERE recipient_id=%s",(p['recipient_id'],))
        custody(conn,actor,row['allocation_id'],'RESERVED',o['origin'],'Reserva autorizada',row['authorization_reference'])
        r.event(conn,actor,'RESERVE','ORGAN_ALLOCATION',row['allocation_id'],p['institution_id'])
        return row['allocation_id']


ALLOCATION_SQL='''SELECT a.*,o.record_code AS organ_code,o.organ_type,o.preservation_until,d.institution_id AS origin_id,p.institution_id AS destination_id,
 i.region_name,i.institution_name AS origin,j.institution_name AS destination
 FROM organ_allocation a JOIN organ_offer o USING(offer_id) JOIN organ_donor d USING(donor_id)
 JOIN organ_recipient p ON p.recipient_id=a.recipient_id JOIN institution i ON i.institution_id=d.institution_id JOIN institution j ON j.institution_id=p.institution_id'''


def allocation_scope(actor):
    if actor.role_code=='TRANSPORT': return 'a.transport_id=%s',[actor.account_id]
    if actor.institution_id: return '(d.institution_id=%s OR p.institution_id=%s)',[actor.institution_id,actor.institution_id]
    return 'i.region_name=%s',[actor.region_name]


def allocation_row(conn,actor,identifier,lock=False):
    clause,params=allocation_scope(actor)
    row=conn.execute(ALLOCATION_SQL+' WHERE a.allocation_id=%s AND '+clause+(' FOR UPDATE OF a' if lock else ''),[identifier,*params]).fetchone()
    if not row: raise BusinessError('Asignación no disponible en tu ámbito.',404)
    return row


def allocations(actor,page=1):
    require(actor,'organ.logistics')
    with transaction() as conn:
        clause,params=allocation_scope(actor)
        rows=conn.execute(ALLOCATION_SQL+' WHERE '+clause+' ORDER BY a.reserved_at DESC LIMIT 12 OFFSET %s',[*params,(page-1)*12]).fetchall()
        r.event(conn,actor,'READ','ORGAN_ALLOCATION','LIST',actor.institution_id)
        return rows


def allocation_detail(actor,identifier):
    require(actor,'organ.logistics')
    with transaction() as conn:
        row=allocation_row(conn,actor,identifier)
        events=conn.execute('SELECT e.*,p.party_name FROM organ_custody_event e JOIN user_account u ON u.account_id=e.actor_id JOIN party p USING(party_id) WHERE allocation_id=%s ORDER BY occurred_at,event_id',(identifier,)).fetchall()
        r.event(conn,actor,'READ','ORGAN_ALLOCATION',identifier,row['origin_id'])
        return row,events


def custody(conn,actor,identifier,status,location,observation,evidence):
    insert(conn,'organ_custody_event',dict(allocation_id=identifier,status=status,actor_id=actor.account_id,location_description=location,observation=observation,evidence_reference=evidence),'event_id')


def plan(actor,identifier,data):
    require(actor,'organ.plan')
    with transaction() as conn:
        row=allocation_row(conn,actor,identifier,True);check_version(row,v.integer(data,'version_no'))
        if row['current_status']!='RESERVED': raise BusinessError('La asignación ya no admite programación.',409)
        institution(conn,row['origin_id'],actor.region_name);institution(conn,row['destination_id'],actor.region_name)
        user=accounts.by_id(conn,v.identifier(data,'transport_id'))
        if not user or not active(user) or user['role_code']!='TRANSPORT' or user['institution_id']!=row['origin_id']: raise BusinessError('Selecciona un transportista activo del origen.')
        route=conn.execute('SELECT * FROM regional_route WHERE origin_id=%s AND destination_id=%s',(row['origin_id'],row['destination_id'])).fetchone()
        departure=v.timestamp(data,'departure_at');eta=v.timestamp(data,'eta')
        if not route or departure<r.now()-timedelta(minutes=5) or eta<=departure or eta<departure+timedelta(minutes=route['travel_minutes']) or eta>=row['preservation_until']:
            raise BusinessError('Salida, ETA o ruta no respetan el límite de conservación registrado.')
        conn.execute("UPDATE organ_allocation SET current_status='SCHEDULED',transport_id=%s,vehicle=%s,departure_at=%s,eta=%s,version_no=version_no+1 WHERE allocation_id=%s",
            (user['account_id'],v.text(data,'vehicle','el vehículo'),departure,eta,identifier))
        ref=v.text(data,'evidence_reference','la orden de traslado',240)
        custody(conn,actor,identifier,'SCHEDULED',row['origin'],'Programación autorizada',ref)
        r.event(conn,actor,'ASSIGN','ORGAN_ALLOCATION',identifier,row['origin_id'])


def step(actor,identifier,data):
    require(actor,'organ.logistics')
    with transaction() as conn:
        row=allocation_row(conn,actor,identifier,True);check_version(row,v.integer(data,'version_no'))
        # Bloquea órgano antes del receptor: mismo orden que reserva.
        conn.execute('SELECT offer_id FROM organ_offer WHERE offer_id=%s FOR UPDATE',(row['offer_id'],))
        conn.execute('SELECT recipient_id FROM organ_recipient WHERE recipient_id=%s FOR UPDATE',(row['recipient_id'],))
        target=v.choice(data,'status',('PREPARED','COLLECTED','IN_TRANSIT','DELIVERED','ACCEPTED','CANCELLED','INCIDENT'),'evento')
        permitted=False
        if target=='CANCELLED': permitted=actor.can('organ.plan') and row['current_status'] in ('RESERVED','SCHEDULED','PREPARED')
        elif target=='INCIDENT': permitted=actor.role_code in ('MEDICAL','OPERATOR','COORDINATOR','TRANSPORT') and row['current_status'] not in ('ACCEPTED','CANCELLED')
        else:
            next_state={'SCHEDULED':'PREPARED','PREPARED':'COLLECTED','COLLECTED':'IN_TRANSIT','IN_TRANSIT':'DELIVERED','DELIVERED':'ACCEPTED'}
            if next_state.get(row['current_status'])!=target: raise BusinessError('El evento no corresponde a la etapa actual.',409)
            if target=='PREPARED': permitted=actor.role_code in ('MEDICAL','OPERATOR') and actor.institution_id==row['origin_id']
            elif target=='ACCEPTED': permitted=actor.role_code in ('MEDICAL','OPERATOR') and actor.institution_id==row['destination_id']
            else: permitted=actor.role_code=='TRANSPORT' and actor.account_id==row['transport_id']
        if not permitted: raise BusinessError('Tu perfil no puede registrar este evento.',403)
        if target not in ('INCIDENT','CANCELLED'):
            institution(conn,row['origin_id'],actor.region_name);institution(conn,row['destination_id'],actor.region_name)
            if row['preservation_until']<=r.now() or (target in ('PREPARED','COLLECTED','IN_TRANSIT') and row['eta']>=row['preservation_until']):
                raise BusinessError('Se excedió el límite de conservación. Registra una incidencia.',409)
        custody(conn,actor,identifier,target,v.text(data,'location_description','la ubicación',240),v.paragraph(data,'observation','el motivo u observación sin datos clínicos'),v.text(data,'evidence_reference','la referencia de evidencia',240))
        if target=='CANCELLED':
            conn.execute("UPDATE organ_offer SET current_status='AVAILABLE',version_no=version_no+1 WHERE offer_id=%s",(row['offer_id'],))
            conn.execute("UPDATE organ_recipient SET current_status='ACTIVE',version_no=version_no+1 WHERE recipient_id=%s",(row['recipient_id'],))
        if target=='ACCEPTED':
            conn.execute("UPDATE organ_offer SET current_status='RECEIVED',version_no=version_no+1 WHERE offer_id=%s",(row['offer_id'],))
            conn.execute("UPDATE organ_recipient SET current_status='CLOSED',version_no=version_no+1 WHERE recipient_id=%s",(row['recipient_id'],))
            conn.execute('UPDATE organ_allocation SET received_at=now() WHERE allocation_id=%s',(identifier,))
        if target=='IN_TRANSIT': conn.execute("UPDATE organ_offer SET current_status='IN_TRANSIT',version_no=version_no+1 WHERE offer_id=%s",(row['offer_id'],))
        conn.execute('UPDATE organ_allocation SET current_status=%s,version_no=version_no+1 WHERE allocation_id=%s',(row['current_status'] if target=='INCIDENT' else target,identifier))
        r.event(conn,actor,target,'ORGAN_ALLOCATION',identifier,row['destination_id'] if target=='ACCEPTED' else row['origin_id'])
