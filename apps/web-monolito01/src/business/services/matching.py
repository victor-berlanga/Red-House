"""Filtro ABO/RhD para eritrocitos. No determina compatibilidad clínica."""
from datetime import timedelta
from time import perf_counter

from ..access import BusinessError, check_version, require
from .. import validators as v
from ...data_access.connection import transaction
from ...data_access.repositories.common import insert
from . import regional as r

VERSION='RBC-DEMO-1.0'
SOURCE='https://www.lifeblood.com.au/health-professionals/products/component-compatibility'
ABO={'O':{'O'},'A':{'O','A'},'B':{'O','B'},'AB':{'O','A','B','AB'}}
NOTICE='Compatibilidad computacional demostrativa. Requiere validación clínica.'


def compatible(donor,recipient):
    if recipient[:-1] not in ABO or donor[:-1] not in ABO or donor[-1:] not in ('+','-') or recipient[-1:] not in ('+','-'):
        return False
    return donor[:-1] in ABO[recipient[:-1]] and (recipient[-1]=='+' or donor[-1]=='-')


def candidate_rows(conn,request):
    return conn.execute('''SELECT v.*,t.distance_km,t.travel_minutes,t.version_no AS route_version,t.source_reference AS route_source
        FROM blood_inventory v JOIN regional_route t ON t.origin_id=v.institution_id AND t.destination_id=%s
        WHERE v.region_name=%s AND v.component_id=%s AND v.is_available
        AND v.expires_at>now()+t.travel_minutes*interval '1 minute'
        ORDER BY v.expires_at,t.travel_minutes,t.distance_km,v.resource_id''',
        (request['institution_id'],request['region_name'],request['component_id'])).fetchall()


def evaluate(actor,identifier):
    require(actor,'candidate.evaluate')
    start=perf_counter()
    with transaction() as conn:
        request=r.request_row(conn,actor,identifier,lock=True)
        if request['current_status'] not in ('OPEN','IN_PROGRESS') or request['recipient_status']!='ACTIVE':
            raise BusinessError('La solicitud o el receptor no están activos.',409)
        r.own_institution(conn,actor,request['institution_id'])
        # Catálogo explícito: nunca deducir el componente del nombre libre.
        if request['component_code']!='RBC-DEMO':
            raise BusinessError('Este componente requiere revisión manual externa al motor. Solo RBC-DEMO tiene una regla computacional autorizada para el ejercicio.',409)
        rows=[u for u in candidate_rows(conn,request) if compatible(u['recorded_group_code'],request['blood_group'])]
        evaluation=insert(conn,'candidate_evaluation',dict(request_id=identifier,algorithm_version=VERSION,
            request_version=request['version_no'],recipient_version=request['recipient_version'],actor_id=actor.account_id,
            elapsed_ms=round((perf_counter()-start)*1000,3)),'evaluation_id')
        wait=max(0,int((r.now()-request['requested_at']).total_seconds()//60))
        for rank,unit in enumerate(rows,1):
            explanation=(f"ABO/RhD potencial: {unit['recorded_group_code']} → {request['blood_group']}. "
                f"Urgencia registrada {request['urgency']}; espera {wait} min. Orden logístico DEMO: "
                f"caducidad capturada, traslado {unit['travel_minutes']} min, distancia {unit['distance_km']} km y folio estable. "
                f"Ruta: {unit['route_source']}. No evalúa anticuerpos, pruebas cruzadas ni excepciones clínicas.")
            insert(conn,'blood_candidate',dict(evaluation_id=evaluation['evaluation_id'],resource_id=unit['resource_id'],
                rank_no=rank,unit_version=unit['version_no'],donor_group=unit['recorded_group_code'],recipient_group=request['blood_group'],
                urgency=request['urgency'],wait_minutes=wait,distance_km=unit['distance_km'],travel_minutes=unit['travel_minutes'],
                route_version=unit['route_version'],expires_at=unit['expires_at'],explanation=explanation),'candidate_id')
        r.event(conn,actor,'EVALUATE','BLOOD_REQUEST',identifier,request['institution_id'],algorithm_version=VERSION,candidate_count=len(rows))
        return evaluation['evaluation_id']


def reserve(actor,identifier,data):
    require(actor,'allocation.authorize')
    if data.get('human_confirmation')!='on':
        raise BusinessError('La reserva exige revisión y autorización humana explícita.')
    reason=v.text(data,'reason','el fundamento de autorización (sin datos clínicos personales)',240)
    with transaction() as conn:
        request=r.request_row(conn,actor,identifier,clinical=True,lock=True)
        check_version(request,v.integer(data,'version_no'))
        r.own_institution(conn,actor,request['institution_id'])
        if request['current_status'] not in ('OPEN','IN_PROGRESS') or request['recipient_status']!='ACTIVE':
            raise BusinessError('La solicitud ya no admite reservas.',409)
        used=conn.execute("SELECT count(*) AS n FROM blood_allocation WHERE request_id=%s AND current_status<>'CANCELLED'",(identifier,)).fetchone()['n']
        if used>=request['quantity']:
            raise BusinessError('La cantidad solicitada ya está cubierta.',409)
        candidate=conn.execute('''SELECT c.*,e.algorithm_version,e.request_id,e.recipient_version FROM blood_candidate c
            JOIN candidate_evaluation e USING(evaluation_id) WHERE c.candidate_id=%s AND e.request_id=%s''',
            (v.identifier(data,'candidate_id'),identifier)).fetchone()
        if not candidate or candidate['algorithm_version']!=VERSION or candidate['recipient_version']!=request['recipient_version']:
            raise BusinessError('El resultado no corresponde a una evaluación vigente de esta solicitud.',409)
        conn.execute('SELECT resource_id FROM blood_unit WHERE resource_id=%s FOR UPDATE',(candidate['resource_id'],))
        unit=conn.execute('SELECT * FROM blood_inventory WHERE resource_id=%s',(candidate['resource_id'],)).fetchone()
        route=conn.execute('SELECT * FROM regional_route WHERE origin_id=%s AND destination_id=%s FOR SHARE',
                           (unit['institution_id'],request['institution_id'])).fetchone()
        if (not unit['is_available'] or unit['version_no']!=candidate['unit_version'] or unit['component_id']!=request['component_id']
            or unit['region_name']!=request['region_name'] or not compatible(unit['recorded_group_code'],request['blood_group'])
            or not route or route['version_no']!=candidate['route_version']
            or unit['expires_at']<=r.now()+timedelta(minutes=route['travel_minutes'])):
            raise BusinessError('La disponibilidad, ruta o viabilidad cambió. Genera y revisa candidatos otra vez.',409)
        allocation=insert(conn,'blood_allocation',dict(request_id=identifier,candidate_id=candidate['candidate_id'],resource_id=unit['resource_id'],
            origin_id=unit['institution_id'],destination_id=request['institution_id'],authorized_by=actor.account_id,authorization_reason=reason),'allocation_id')
        conn.execute("UPDATE blood_unit SET current_status='RESERVED',version_no=version_no+1 WHERE resource_id=%s",(unit['resource_id'],))
        conn.execute("UPDATE blood_request SET current_status='IN_PROGRESS',version_no=version_no+1 WHERE request_id=%s",(identifier,))
        r.move_unit(conn,actor,unit['resource_id'],unit['current_status'],'RESERVED',unit['location_id'],unit['location_id'],'Reserva con autorización humana DEMO')
        r.request_event(conn,actor,identifier,'RESERVE','Autorización humana y reserva transaccional')
        r.event(conn,actor,'AUTHORIZE','BLOOD_ALLOCATION',allocation['allocation_id'],request['institution_id'],evaluation_id=candidate['evaluation_id'])
        r.event(conn,actor,'RESERVE','BLOOD_UNIT',unit['resource_id'],unit['institution_id'],request_id=identifier)
        return allocation['allocation_id']
