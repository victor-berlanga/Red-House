from datetime import timedelta
from .. import validators as v
from ...data_access.repositories.inventory import GROUPS

from ..access import require
from ...data_access.connection import transaction
from ...data_access.repositories.common import scope
from ...data_access.repositories import network
from . import regional as r, matching


def dashboard(actor, zone='UTC'):
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
        allocations=conn.execute('''SELECT count(*) FILTER(WHERE a.current_status IN ('RESERVED','ASSIGNED')) AS reserved,
            round(avg(extract(epoch from(a.reserved_at-q.requested_at))/60),1) AS response_minutes
            FROM blood_allocation a JOIN blood_request q USING(request_id) JOIN institution i ON i.institution_id=a.destination_id WHERE '''+clause,params).fetchone()
        shipments=conn.execute("SELECT count(*) AS n FROM shipment s JOIN blood_allocation a USING(allocation_id) JOIN institution i ON i.institution_id=a.destination_id WHERE "+clause+" AND s.current_status NOT IN ('ACCEPTED','CANCELLED')",params).fetchone()['n']
        urgency=conn.execute('SELECT q.urgency AS label,count(*) AS value'+qs+" AND q.current_status IN ('OPEN','IN_PROGRESS') GROUP BY q.urgency ORDER BY q.urgency",params).fetchall()
        v.choice({'zone':zone},'zone',('UTC','America/Monterrey'),'zona horaria')
        today=conn.execute("SELECT (now() AT TIME ZONE %s)::date AS day",(zone,)).fetchone()['day']
        trend_rows=conn.execute('SELECT (q.requested_at AT TIME ZONE %s)::date AS day,count(*) AS requests'+qs+
            " AND q.requested_at >= (%s::date::timestamp AT TIME ZONE %s) AND q.requested_at < ((%s::date+1)::timestamp AT TIME ZONE %s) GROUP BY day ORDER BY day",
            [zone,*params,today-timedelta(days=6),zone,today,zone]).fetchall()
        counts={row['day']:row['requests'] for row in trend_rows}
        trends=[dict(day=today-timedelta(days=offset),requests=counts.get(today-timedelta(days=offset),0)) for offset in range(6,-1,-1)]

        soon=conn.execute('SELECT i.* FROM blood_inventory i WHERE '+clause+" AND i.is_available AND i.expires_at<=now()+%s*interval '1 hour' ORDER BY i.expires_at LIMIT 20",[*params,hours]).fetchall()
        movements=conn.execute('''SELECT m.occurred_at,m.new_status,b.traceability_code,i.institution_name
            FROM blood_movement m JOIN resource b USING(resource_id) JOIN blood_inventory i USING(resource_id)
            WHERE '''+clause+' ORDER BY m.occurred_at DESC,m.movement_id DESC LIMIT 15',params).fetchall()
        # Una consulta conjunta; los pares provienen de la misma regla versionada del motor.
        pairs=[(donor,recipient) for donor in GROUPS for recipient in GROUPS if matching.compatible(donor,recipient)]
        values=','.join(['(%s,%s)']*len(pairs))
        opportunities=conn.execute("""WITH compatible(donor_group,recipient_group) AS (VALUES """+values+"""), active AS (
            SELECT q.request_id,q.request_code,q.component_id,q.requested_at,p.blood_group,p.institution_id,i.region_name,i.institution_name"""+qs+"""
            AND q.current_status IN ('OPEN','IN_PROGRESS') ORDER BY q.requested_at,q.request_id LIMIT 20)
            SELECT q.request_id,q.request_code,u.traceability_code,u.institution_name AS origin,q.institution_name AS destination
            FROM active q JOIN blood_component c USING(component_id)
            JOIN compatible k ON k.recipient_group=q.blood_group
            JOIN blood_inventory u ON u.component_id=q.component_id AND u.region_name=q.region_name AND u.recorded_group_code=k.donor_group
            JOIN regional_route t ON t.origin_id=u.institution_id AND t.destination_id=q.institution_id
            WHERE c.component_code='RBC-DEMO' AND u.is_available AND u.institution_id<>q.institution_id
            AND u.expires_at>now()+t.travel_minutes*interval '1 minute'
            AND u.expires_at<=now()+%s*interval '1 hour'
            ORDER BY q.requested_at,q.request_id,u.expires_at,t.travel_minutes,t.distance_km,u.resource_id LIMIT 10""",
            [*(value for pair in pairs for value in pair),*params,hours]).fetchall()
        r.event(conn,actor,'READ','REGIONAL_DASHBOARD','SUMMARY',actor.institution_id)
        return dict(trend_chart=[{'label':row['day'].strftime('%d/%m'),'value':row['requests']} for row in trends],urgency_chart=[{'label':{'URGENT':'Urgente','PRIORITY':'Prioritaria','ROUTINE':'Ordinaria'}[row['label']],'value':row['value']} for row in urgency],groups=groups,institutions=institutions,urgency=urgency,trends=trends,soon=soon,movements=movements,opportunities=opportunities,hours=hours,
            stats=[('Unidades disponibles',sum(x['value'] for x in groups)),('Próximas a caducar',sum(x['soon'] for x in groups)),
                ('Solicitudes activas',requests['active']),('Solicitudes urgentes',requests['urgent']),('Recursos reservados',allocations['reserved']),
                ('Traslados activos',shipments),('Respuesta media (min)',allocations['response_minutes'] if allocations['response_minutes'] is not None else 'Sin reservas'),
                ('Instituciones participantes',sum(x['participation_status']=='ACTIVE' for x in institutions))])
