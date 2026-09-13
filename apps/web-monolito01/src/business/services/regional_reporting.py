from datetime import timedelta

from ..access import require
from ...data_access.connection import transaction
from ...data_access.repositories.common import scope
from ...data_access.repositories import network
from . import regional as r, matching


def dashboard(actor):
    require(actor,'regional.read')
    with transaction() as conn:
        clause,params=scope(actor,'i')
        parameter=network.parameter(conn,actor.region_name)
        hours=parameter['scalar_value'] if parameter else 72
        groups=conn.execute('''SELECT i.recorded_group_code AS label,count(*) FILTER(WHERE i.is_available) AS value,
            count(*) FILTER(WHERE i.is_available AND i.expires_at<=now()+%s*interval '1 hour') AS soon
            FROM blood_inventory i WHERE '''+clause+' GROUP BY i.recorded_group_code ORDER BY i.recorded_group_code',[hours,*params]).fetchall()
        institutions=conn.execute('''SELECT i.institution_name,i.institution_type,i.city,i.operating_hours,i.participation_status,
            count(v.resource_id) FILTER(WHERE v.is_available) AS available FROM institution i
            LEFT JOIN blood_inventory v USING(institution_id) WHERE '''+clause+' GROUP BY i.institution_id ORDER BY i.institution_name',params).fetchall()
        qs=' FROM blood_request q JOIN recipient p USING(recipient_id) JOIN institution i USING(institution_id) WHERE '+clause
        requests=conn.execute('''SELECT count(*) FILTER(WHERE q.current_status IN ('OPEN','IN_PROGRESS')) AS active,
            count(*) FILTER(WHERE q.current_status IN ('OPEN','IN_PROGRESS') AND q.urgency='URGENT') AS urgent'''+qs,params).fetchone()
        aq=' FROM blood_allocation a JOIN institution i ON i.institution_id=a.destination_id WHERE '+clause
        allocations=conn.execute('''SELECT count(*) FILTER(WHERE a.current_status IN ('RESERVED','ASSIGNED')) AS reserved,
            round(avg(extract(epoch from(a.reserved_at-q.requested_at))/60),1) AS response_minutes
            FROM blood_allocation a JOIN blood_request q USING(request_id) JOIN institution i ON i.institution_id=a.destination_id WHERE '''+clause,params).fetchone()
        shipments=conn.execute("SELECT count(*) AS n FROM shipment s JOIN blood_allocation a USING(allocation_id) JOIN institution i ON i.institution_id=a.destination_id WHERE "+clause+" AND s.current_status NOT IN ('ACCEPTED','CANCELLED')",params).fetchone()['n']
        urgency=conn.execute('SELECT q.urgency AS label,count(*) AS value'+qs+" AND q.current_status IN ('OPEN','IN_PROGRESS') GROUP BY q.urgency ORDER BY q.urgency",params).fetchall()
        trends=conn.execute('SELECT q.requested_at::date AS day,count(*) AS requests'+qs+" AND q.requested_at>=now()-interval '7 days' GROUP BY q.requested_at::date ORDER BY day",params).fetchall()
        soon=conn.execute('SELECT i.* FROM blood_inventory i WHERE '+clause+" AND i.is_available AND i.expires_at<=now()+%s*interval '1 hour' ORDER BY i.expires_at LIMIT 20",[*params,hours]).fetchall()
        movements=conn.execute('''SELECT m.occurred_at,m.new_status,b.traceability_code,i.institution_name
            FROM blood_movement m JOIN resource b USING(resource_id) JOIN blood_inventory i USING(resource_id)
            WHERE '''+clause+' ORDER BY m.occurred_at DESC,m.movement_id DESC LIMIT 15',params).fetchall()
        opportunities=[]
        # Demanda observada, sin presentar pronósticos ni transferencias automáticas.
        active=conn.execute('''SELECT q.request_id,q.request_code,q.component_id,p.blood_group,p.institution_id,i.region_name,i.institution_name'''+qs+
            " AND q.current_status IN ('OPEN','IN_PROGRESS') ORDER BY q.requested_at LIMIT 20",params).fetchall()
        for q in active:
            component=conn.execute('SELECT component_code FROM blood_component WHERE component_id=%s',(q['component_id'],)).fetchone()
            if component['component_code']!='RBC-DEMO':
                continue
            for unit in matching.candidate_rows(conn,q):
                if unit['institution_id']!=q['institution_id'] and unit['expires_at']<=r.now()+timedelta(hours=hours) and matching.compatible(unit['recorded_group_code'],q['blood_group']):
                    opportunities.append(dict(request_id=q['request_id'],request_code=q['request_code'],traceability_code=unit['traceability_code'],origin=unit['institution_name'],destination=q['institution_name']))
                    if len(opportunities)>=10: break
            if len(opportunities)>=10: break
        r.event(conn,actor,'READ','REGIONAL_DASHBOARD','SUMMARY',actor.institution_id)
        return dict(groups=groups,institutions=institutions,urgency=urgency,trends=trends,soon=soon,movements=movements,opportunities=opportunities,hours=hours,
            stats=[('Unidades disponibles',sum(x['value'] for x in groups)),('Próximas a caducar',sum(x['soon'] for x in groups)),
                ('Solicitudes activas',requests['active']),('Solicitudes urgentes',requests['urgent']),('Recursos reservados',allocations['reserved']),
                ('Traslados activos',shipments),('Respuesta media (min)',allocations['response_minutes'] if allocations['response_minutes'] is not None else 'Sin reservas'),
                ('Instituciones participantes',sum(x['participation_status']=='ACTIVE' for x in institutions))])
