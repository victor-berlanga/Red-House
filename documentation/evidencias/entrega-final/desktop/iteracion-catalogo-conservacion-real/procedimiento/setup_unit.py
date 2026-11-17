"""Unidad sintética independiente para DESK-10; no inicia fixture."""
import base64
import hashlib
import hmac
import ipaddress
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import UUID, uuid4
import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import requests
from redhouse.examples import request_xml
from redhouse.xml_response import validate_response
from session_oracle import snapshot, closure


def require(value,message):
    if not value: raise RuntimeError(message)


def private(path):
    path=Path(path); require(path.is_absolute() and path.resolve()==path and not path.is_symlink(),'ruta privada inválida')
    info=path.stat()
    require(path.is_file() and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o600,'archivo privado inválido')
    return path


def save(path,value):
    temp=path.with_suffix('.tmp'); fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'w') as stream: json.dump(value,stream,indent=2); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp,path)
    finally: temp.unlink(missing_ok=True)


def read_only(state,service,fixture):
    admin=conninfo_to_dict(state['database_admin']); params=conninfo_to_dict(state['database_owners'][service])
    require(admin.get('host')=='127.0.0.1' and params.get('host')=='127.0.0.1' and admin.get('port')==params.get('port'),'DSN no local')
    for value in (admin,params): value['options']=(value.get('options','')+' -c default_transaction_read_only=on').strip(); value['connect_timeout']='3'
    with psycopg.connect(make_conninfo(**admin)) as guard:
        require(Path(guard.execute('SHOW data_directory').fetchone()[0]).resolve()==fixture/'pg','directorio PG distinto')
        started=guard.execute('SELECT pg_postmaster_start_time()').fetchone()[0]
        conn=psycopg.connect(make_conninfo(**params))
        if conn.execute('SHOW transaction_read_only').fetchone()[0]!='on' or conn.execute('SELECT pg_postmaster_start_time()').fetchone()[0]!=started:
            conn.close(); raise RuntimeError('solo lectura no confirmado')
        return conn


def totp(secret):
    factor=base64.b32decode(secret.upper()+'='*(-len(secret)%8),casefold=True); period=int(time.time())//30
    digest=hmac.new(factor,struct.pack('>Q',period),hashlib.sha1).digest(); offset=digest[-1]&15
    return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6),period


def next_code(secret,last):
    deadline=time.monotonic()+35
    while True:
        code,period=totp(secret)
        if period>last and 30-int(time.time())%30>=8: return code,period
        require(time.monotonic()<deadline,'periodo MFA no disponible'); time.sleep(.1)


def main():
    ready=json.loads(private(os.environ['E2EB_READY']).read_text()); lab=json.loads(private(ready['lab_json']).read_text()); state=json.loads(private(ready['state_json']).read_text())
    fixture=Path(ready['fixture_root']).resolve(); require(ready['phase']=='RUNNING_SHARED' and ready['scenario']=='E2E-B' and Path(state['directory']).resolve()==fixture,'fixture distinto')
    pid=ready['fixture_pid']; require(type(pid) is int and pid>1,'PID inválido'); os.kill(pid,0)
    process=subprocess.run(['ps','-p',str(pid),'-o','uid=','-o','command='],check=True,capture_output=True,text=True).stdout.strip()
    require(process.startswith(str(os.getuid())+' ') and '/private/tmp/rh_e2eb_preserved.py' in process,'proceso distinto')
    gateway=urlsplit(ready['gateway']); ca=private(ready['ca_pem']); require(ready['gateway']==lab['gateway'] and Path(lab['ca']).resolve()==ca,'CA/origen distintos')
    require(gateway.scheme=='https' and ipaddress.ip_address(gateway.hostname).is_private and gateway.port==18443 and not(gateway.username or gateway.password or gateway.query or gateway.fragment) and gateway.path in ('','/'),'origen inválido')
    for config in ready['effective_configuration'].values(): require(config['TESTING'] is False and config['OPERATION_SCOPE']=='ACADEMIC' and config['REQUIRE_ORGAN_AUTHORIZATION'] is True and config['REQUIRE_LAB_PROFILE'] is True,'configuración incompatible')
    out=Path(os.environ['E2EB_BOOTSTRAP_PRIVATE']).resolve(); require(out.is_dir() and out.stat().st_uid==os.getuid() and stat.S_IMODE(out.stat().st_mode)==0o700,'salida inválida')
    progress=out/'bootstrap.json'; require(not progress.exists(),'salida ya usada; inspeccionar antes de continuar')
    ledger={'phase':'STARTED','steps':{}}; save(progress,ledger)
    operator=state['accounts']['operator1']; medical=state['accounts']['medical1']
    require(operator['role']=='OPERATOR' and medical['role']=='MEDICAL' and operator['tenant_id']==medical['tenant_id'],'actores incompatibles')
    users=[operator['id'],medical['id']]
    pg=lambda value,service,pgdir:read_only(value,service,pgdir.parent)
    before=snapshot(pg,state,fixture,users); save(out/'sessions-before.json',sorted(before))
    session=requests.Session(); session.trust_env=False; session.verify=str(ca); active=[]
    def call(service,path,method='GET',body=None,token=None,key=None,expected=200):
        headers={'Accept':'application/xml'}
        if token: headers['Authorization']='Bearer '+token
        if key: headers['Idempotency-Key']=key
        if body is not None: headers['Content-Type']='application/xml'
        response=session.request(method,ready['gateway']+'/services/'+service+path,headers=headers,data=request_xml(body).encode() if body is not None else None,timeout=(5,15),allow_redirects=False)
        try:
            require(response.status_code==expected and response.headers.get('Content-Type','').split(';')[0]=='application/xml','API rechazó la etapa')
            return validate_response(response.content,{'type':'object'})['data']
        finally: response.close()
    def step(name,service,path,body,token):
        require(name not in ledger['steps'],'etapa ya intentada'); key=str(uuid4())
        ledger['steps'][name]={'key':key,'state':'PREPARED','body':body}; save(progress,ledger)
        result=call(service,path,'POST',body,token,key,201 if name in ('resource','controls') else 200)
        ledger['steps'][name].update(state='CONFIRMED',id=result.get('id')); save(progress,ledger)
        return result
    def login(alias,otp=None):
        ledger.setdefault('logins',{})[alias]='REQUESTED'; save(progress,ledger)
        body={'username':alias,'password':lab['password']}
        if otp: body['otp']=otp
        result=call('identidad-acceso','/api/v1/auth/login','POST',body)
        expected=state['accounts'][alias]; user=result['user']
        require(all(user.get(k)==expected[k] for k in ('id','role','tenant_id')),'identidad distinta')
        active.append(result['access_token']); ledger['logins'][alias]='CONFIRMED'; save(progress,ledger); return result['access_token']
    try:
        with read_only(state,'identidad_acceso',fixture) as conn:
            row=conn.execute('SELECT last_counter FROM security_factors WHERE id=%s',(medical['id'],)).fetchone()
        factor_path=Path(os.environ['E2EB_MFA_PRIVATE']).resolve()
        if row:
            factor=json.loads(private(factor_path).read_text()); require(factor.get('user_id')==medical['id'],'factor existente no corresponde')
            secret=factor['totp_secret']; last=row[0]
        else:
            require(not factor_path.exists(),'factor privado previo requiere revisión')
            enrollment=call('identidad-acceso','/api/v1/auth/mfa/enrollment','POST',{'username':'medical1','password':lab['password']})
            factor={'user_id':medical['id'],'totp_secret':enrollment['secret'],'challenge':enrollment['challenge'],'state':'PENDING_CONFIRMATION'}; save(factor_path,factor)
            otp,last=next_code(factor['totp_secret'],-1)
            confirm=call('identidad-acceso','/api/v1/auth/mfa/confirm','POST',{'challenge':factor['challenge'],'code':otp})
            require(confirm.get('accepted') is True,'factor no confirmado')
            factor.pop('challenge'); factor.update(state='CONFIRMED',last_mfa_period=last); save(factor_path,factor); secret=factor['totp_secret']
        otp,period=next_code(secret,last); med=login('medical1',otp); factor.update(last_mfa_period=period); save(factor_path,factor)
        op=login('operator1')
        now=datetime.now(timezone.utc); iso=lambda value:value.isoformat(timespec='seconds').replace('+00:00','Z')
        source=json.loads(private(os.environ['E2EB_EXISTING_HANDOFF']).read_text()); profile_id=source['source_profile_id']
        with read_only(state,'compatibilidad',fixture) as conn:
            profile=conn.execute('SELECT tenant_id::text,kind,component FROM lab_profiles WHERE id=%s',(profile_id,)).fetchone()
        require(profile==(medical['tenant_id'],'ORGAN','KIDNEY'),'perfil de laboratorio no corresponde')
        unit=step('resource','inventario','/api/v1/resources',{'folio':'COLD-E2EB-'+uuid4().hex[:9],'kind':'ORGAN','component':'KIDNEY','blood_group':'O+','expires_at':iso(now+timedelta(days=2))},op)
        step('controls','inventario','/api/v1/resources/'+unit['id']+'/controls',{'human_confirmation':True,'reason':'Preparación académica sintética','version':1,'lab_profile_id':profile_id},med)
        with read_only(state,'inventario',fixture) as conn:
            saved=conn.execute('SELECT status,version,current_institution_id::text FROM resources WHERE id=%s',(unit['id'],)).fetchone()
            controls=conn.execute('SELECT lab_profile_id::text,cold_equipment_id,cold_profile_id FROM resource_controls WHERE id=%s',(unit['id'],)).fetchone()
        require(saved==('QUARANTINE',2,medical['tenant_id']) and controls==(profile_id,None,None),'unidad o perfil distintos')
        handoff={'fixture_root':str(fixture),'runtime_ready_json':str(Path(os.environ['E2EB_READY']).resolve()),'state_json':ready['state_json'],'lab_json':ready['lab_json'],'fixture_command_marker':'/private/tmp/rh_e2eb_preserved.py','gateway':ready['gateway'],'ca_pem':str(ca),'resource_id':unit['id'],'lab_profile_id':profile_id,'operator_actor':'operator1','medical_actor':'medical1'}
        ledger['phase']='PREPARED_PENDING_LOGOUT'; save(progress,ledger)
    finally:
        failed=False
        for token in reversed(active):
            try: call('identidad-acceso','/api/v1/auth/logout','POST',token=token,key=str(uuid4()))
            except Exception: failed=True  # noqa: BLE001 - conservar resultado sin secretos
        ledger['logout_attempted']=len(active); ledger['logout_errors']=failed
        ledger['unresolved_login']=any(value=='REQUESTED' for value in ledger.get('logins',{}).values())
        try:
            created=closure(pg,private,state,fixture,users,before); save(out/'sessions-closed.json',created)
            if len(created)!=len(active): failed=True
        except Exception: failed=True  # noqa: BLE001 - no exponer DSN ni identidades en logs
        ledger['sessions_closed_confirmed']=not failed; save(progress,ledger); session.close()
        if failed or ledger['unresolved_login']: raise RuntimeError('Cierre de sesiones requiere revisión')
    save(out/'handoff.json',handoff); ledger['phase']='READY_FOR_QT'; save(progress,ledger)


if __name__=='__main__': main()
