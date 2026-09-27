from flask import Blueprint, g, request, render_template, redirect, url_for, flash
from ...business.services import organs as s
from ...business import validators as v
from ...business.access import BusinessError, require
from ...data_access.connection import transaction
from .regional import field, form

bp=Blueprint('organs',__name__,url_prefix='/organos')


def label(value):
    return s.TYPES.get(value,s.STATES.get(value,value)) if isinstance(value,str) else value


def show(title,*,rows=None,columns=None,facts=None,forms=None,links=None,note='',page=None):
    forms=forms or []
    if request.method=='POST' and getattr(g,'organ_error',None):
        for f in forms:
            action=next((x['value'] for x in f['fields'] if x['name']=='action'),None)
            if action != request.form.get('action'): continue
            for x in f['fields']:
                if x['kind']!='hidden': x['value']=request.form.get(x['name'],x['value'])
            if f['version'] is not None: f['version']=request.form.get('version_no','')
    return render_template('organs/page.html',title=title,active='organos-logistica' if '/traslados' in request.path else 'organos',rows=rows,columns=columns or [],facts=facts or [],forms=forms,
        links=links or [],note=note,error=getattr(g,'organ_error',None),label=label,number=page),getattr(g,'organ_error_status',200)


def operation(fn):
    try:
        result=fn();flash('Operación registrada.','success');return result,True
    except BusinessError as e:
        if e.status in (403,404): raise
        g.organ_error=e.message;g.organ_error_status=e.status;return None,False


def medical_fields():
    return [field('studies','Estudios y restricciones (datos ficticios)',kind='textarea'),field('hla','Resultado HLA o justificación de no aplicabilidad',kind='textarea'),
        field('clinical_reference','Referencia de evaluación médica',limit=240),field('human_confirmation','Confirmo la evaluación humana autorizada',kind='checkbox')]


def pagination_number():
    return v.integer({'page':request.args.get('page',1)},'page',1,100000)


@bp.get('')
@bp.get('/')
def index():
    rows=s.offers(g.principal,v.text(request.args,'q','búsqueda',100,False),pagination_number())
    for row in rows: row['url']=url_for('organs.offer',identifier=row['offer_id'])
    return show('Disponibilidad de órganos',rows=rows,columns=[('record_code','Folio'),('organ_type','Órgano'),('abo','ABO'),('origin','Institución'),('current_status','Estado'),('preservation_until','Límite registrado')],note=s.NOTICE,page=pagination_number())


@bp.route('/personas/<kind>',methods=['GET','POST'])
def people(kind):
    require(g.principal,'organ.medical')
    if kind not in ('donor','recipient'): raise BusinessError('No existe ese tipo de expediente.',404)
    if request.method=='POST':
        _,ok=operation(lambda:s.create_person(g.principal,kind,request.form))
        if ok:return redirect(url_for('organs.people',kind=kind))
    fs=[field('record_code','Folio del expediente'),field('display_name','Nombre ficticio'),field('abo','ABO',[(x,x) for x in ('O','A','B','AB')])]
    if kind=='donor': fs += [field('donation_kind','Tipo de donante',[('LIVING','Vivo'),('DECEASED','Fallecido')]),field('consent_reference','Referencia de consentimiento',limit=240)]
    else: fs += [field('organ_type','Órgano requerido',list(s.TYPES.items())),field('urgency','Urgencia registrada',[(x,s.STATES[x]) for x in ('URGENT','PRIORITY','ROUTINE')]),field('waiting_since','Inicio de espera',kind='datetime-local')]
    fs+=medical_fields()
    rows=s.people(g.principal,kind,v.text(request.args,'q','búsqueda',100,False),pagination_number())
    for row in rows:row['url']=url_for('organs.person',kind=kind,identifier=row[kind+'_id'])
    return show('Donantes de órganos' if kind=='donor' else 'Receptores de órganos',rows=rows,columns=[('record_code','Folio'),('display_name','Nombre'),('abo','ABO')],
        forms=[form('Registrar expediente',request.path,fs)],note='Expedientes clínicos de tu institución. Registra exclusivamente datos ficticios.',page=pagination_number())


@bp.get('/personas/<kind>/<uuid:identifier>')
def person(kind,identifier):
    row=s.person_detail(g.principal,kind,identifier)
    fields=[('record_code','Folio'),('display_name','Nombre'),('abo','ABO'),('studies','Estudios y restricciones'),('hla','HLA'),('clinical_reference','Evaluación humana'),('registered_at','Registro')]
    fields+= [('consent_reference','Consentimiento'),('donation_kind','Tipo de donante')] if kind=='donor' else [('organ_type','Órgano'),('urgency','Urgencia'),('waiting_since','En espera desde'),('current_status','Estado')]
    return show('Expediente de órganos',facts=[(lab,row[key]) for key,lab in fields],note='Registro histórico. Los estudios no representan por sí solos una autorización de asignación.')


@bp.route('/registrar',methods=['GET','POST'])
def create_offer():
    require(g.principal,'organ.medical')
    if request.method=='POST':
        rid,ok=operation(lambda:s.create_offer(g.principal,request.form))
        if ok:return redirect(url_for('organs.offer',identifier=rid))
    with transaction() as conn:
        donors=conn.execute('SELECT donor_id,record_code FROM organ_donor WHERE institution_id=%s ORDER BY record_code',(g.principal.institution_id,)).fetchall()
    fs=[field('donor_id','Donante',[(str(x['donor_id']),x['record_code']) for x in donors]),field('record_code','Folio del órgano'),field('organ_type','Órgano',list(s.TYPES.items())),
        field('anatomical_description','Descripción anatómica: lado o segmento',limit=240),field('recovered_at','Recuperación',kind='datetime-local'),field('preservation_until','Límite de conservación autorizado',kind='datetime-local'),
        field('preservation_reference','Referencia médica de liberación y conservación',limit=240),field('human_confirmation','Confirmo la liberación humana autorizada',kind='checkbox')]
    return show('Registrar disponibilidad',forms=[form('Liberar órgano para evaluación',request.path,fs)],note='El límite de conservación debe provenir de una evaluación humana; no se calcula una vida útil clínica.')


@bp.route('/disponibilidad/<uuid:identifier>',methods=['GET','POST'])
def offer(identifier):
    if request.method=='POST':
        _,ok=operation(lambda:s.evaluate(g.principal,identifier))
        if ok:return redirect(request.path)
    row,rows=s.detail(g.principal,identifier)
    for c in rows:
        if g.principal.can('organ.medical') and c['destination_id']==g.principal.institution_id:c['url']=url_for('organs.candidate',identifier=c['candidate_id'])
    fs=[form('Generar candidatos',request.path,[])] if g.principal.can('organ.evaluate') and row['current_status']=='AVAILABLE' else []
    return show('Evaluación de '+row['record_code'],facts=[('Órgano',row['organ_type']),('Origen',row['origin']),('ABO',row['abo']),('Estado',row['current_status']),('Recuperación',row['recovered_at']),('Límite registrado',row['preservation_until']),('Descripción anatómica',row['anatomical_description'])],
        rows=rows,columns=[('rank_no','Orden'),('recipient_code','Receptor'),('destination','Destino'),('explanation','Factores y límites'),('evaluated_at','Evaluación')],forms=fs,
        note=s.NOTICE+' Sin resultados: comprueba tipo, ABO idéntico, receptor activo, ruta y conservación. El orden combina urgencia registrada, espera, tiempo y distancia.')


@bp.route('/candidatos/<uuid:identifier>',methods=['GET','POST'])
def candidate(identifier):
    if request.method=='POST':
        if request.form.get('action')=='reserve':
            aid,ok=operation(lambda:s.reserve(g.principal,identifier,request.form))
            if ok:return redirect(url_for('organs.allocation',identifier=aid))
        else:
            _,ok=operation(lambda:s.review(g.principal,identifier,request.form))
            if ok:return redirect(request.path)
    c,p,d,reviews=s.clinical_candidate(g.principal,identifier)
    review_fields=[field('action','Acción',kind='hidden',value='review'),field('decision','Dictamen',[('FAVORABLE','Favorable'),('REJECTED','No favorable')]),
        field('hla_assessment','Interpretación HLA para este órgano',kind='textarea'),field('size_assessment','Evaluación de tamaño y condiciones',kind='textarea'),field('crossmatch_reference','Prueba cruzada o justificación clínica',limit=240),
        field('clinical_reference','Referencia del dictamen',limit=240),field('human_confirmation','Confirmo la evaluación humana de la pareja',kind='checkbox')]
    forms=[form('Registrar dictamen',request.path,review_fields)]
    if reviews and reviews[0]['decision']=='FAVORABLE':forms.append(form('Autorizar y reservar',request.path,[field('action','Acción',kind='hidden',value='reserve'),field('review_id','Dictamen',kind='hidden',value=str(reviews[0]['review_id'])),field('authorization_reference','Referencia de autorización',limit=240),field('human_confirmation','Confirmo la autorización humana de esta asignación',kind='checkbox')]))
    return show('Revisión de candidato',facts=[('Receptor',p['record_code']),('Estudios del receptor',p['studies']),('HLA del receptor',p['hla']),('Estudios del donante seudonimizado',d['studies']),('HLA del donante',d['hla']),('Factores',c['explanation'])],
        rows=reviews,columns=[('decision','Dictamen'),('hla_assessment','Evaluación HLA'),('size_assessment','Tamaño'),('crossmatch_reference','Prueba cruzada'),('occurred_at','Fecha')],forms=forms,note=s.NOTICE)


@bp.get('/traslados')
def allocations():
    rows=s.allocations(g.principal,pagination_number())
    for row in rows: row['url']=url_for('organs.allocation',identifier=row['allocation_id'])
    return show('Asignaciones y traslados de órganos',rows=rows,columns=[('organ_code','Órgano'),('organ_type','Tipo'),('origin','Origen'),('destination','Destino'),('current_status','Estado'),('eta','ETA')],page=pagination_number())


@bp.route('/traslados/<uuid:identifier>',methods=['GET','POST'])
def allocation(identifier):
    if request.method=='POST':
        fn=s.plan if request.form.get('action')=='plan' else s.step
        _,ok=operation(lambda:fn(g.principal,identifier,request.form))
        if ok:return redirect(request.path)
    row,events=s.allocation_detail(g.principal,identifier);forms=[];a=g.principal
    if a.can('organ.plan') and row['current_status']=='RESERVED':
        with transaction() as conn:
            users=conn.execute('''SELECT u.account_id,p.party_name FROM user_account u JOIN party p USING(party_id) JOIN account_role ar USING(account_id) WHERE ar.role_code='TRANSPORT' AND ar.institution_id=%s''',(row['origin_id'],)).fetchall()
        forms.append(form('Programar traslado',request.path,[field('action','Acción',kind='hidden',value='plan'),field('transport_id','Transportista',[(str(x['account_id']),x['party_name']) for x in users]),field('vehicle','Vehículo'),field('departure_at','Salida',kind='datetime-local'),field('eta','ETA',kind='datetime-local'),field('evidence_reference','Orden de traslado',limit=240)],version=row['version_no']))
    next_state={'SCHEDULED':'PREPARED','PREPARED':'COLLECTED','COLLECTED':'IN_TRANSIT','IN_TRANSIT':'DELIVERED','DELIVERED':'ACCEPTED'}
    target=next_state.get(row['current_status']);allowed=[]
    if target and ((target=='PREPARED' and a.role_code in ('OPERATOR','MEDICAL') and a.institution_id==row['origin_id']) or (target=='ACCEPTED' and a.role_code in ('OPERATOR','MEDICAL') and a.institution_id==row['destination_id']) or (target in ('COLLECTED','IN_TRANSIT','DELIVERED') and a.role_code=='TRANSPORT' and a.account_id==row['transport_id'])):allowed.append(target)
    if a.can('organ.plan') and row['current_status'] in ('RESERVED','SCHEDULED','PREPARED'):allowed.append('CANCELLED')
    if a.role_code!='AUDITOR' and row['current_status'] not in ('ACCEPTED','CANCELLED'):allowed.append('INCIDENT')
    if allowed:forms.append(form('Registrar evento de custodia',request.path,[field('status','Evento',[(x,s.STATES[x]) for x in allowed]),field('location_description','Ubicación',limit=240),field('observation','Observación o motivo sin datos clínicos',kind='textarea'),field('evidence_reference','Referencia de evidencia',limit=240)],version=row['version_no']))
    return show('Custodia de '+row['organ_code'],facts=[('Órgano',row['organ_type']),('Origen',row['origin']),('Destino',row['destination']),('Estado',row['current_status']),('Vehículo',row['vehicle']),('Salida',row['departure_at']),('ETA',row['eta']),('Límite registrado',row['preservation_until'])],
        rows=events,columns=[('status','Evento'),('party_name','Responsable'),('occurred_at','Fecha'),('location_description','Ubicación'),('observation','Observación'),('evidence_reference','Evidencia')],forms=forms,
        note='El historial conserva los eventos originales. La recepción cierra la logística; no certifica un trasplante realizado.')
