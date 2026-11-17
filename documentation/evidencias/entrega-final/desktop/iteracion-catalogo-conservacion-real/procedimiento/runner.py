"""Recorrido Qt de conservación sobre unidad sintética separada; sin crear servicios."""
import base64,hashlib,hmac,importlib.util,json,os,struct,subprocess,sys,time
import ipaddress
from pathlib import Path
from urllib.parse import urlsplit
import requests
from cryptography.fernet import Fernet
from PySide6.QtWidgets import QApplication
import redhouse_desktop.app as desktop
from redhouse_desktop.journal import Journal
from cold_gui import run
from session_oracle import snapshot,closure

SUPPORT=Path('.local/artifacts/desktop/e2ec-prepared-20261116').resolve();sys.path.insert(0,str(SUPPORT))
spec=importlib.util.spec_from_file_location('e2ec_support',SUPPORT/'runner.py');support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
def require(value,message):
    if not value:raise RuntimeError(message)


def main():
    hand=json.loads(support.private_file(Path(os.environ['COLD_HANDOFF']).resolve()).read_text());ready=json.loads(support.private_file(Path(hand['runtime_ready_json']).resolve()).read_text());state=json.loads(support.private_file(Path(hand['state_json']).resolve()).read_text());lab=json.loads(support.private_file(Path(hand['lab_json']).resolve()).read_text());fixture=Path(hand['fixture_root']).resolve()
    require(ready['phase']=='RUNNING_SHARED' and ready['scenario']=='E2E-B' and Path(ready['fixture_root']).resolve()==fixture and Path(state['directory']).resolve()==fixture and ready['state_json']==hand['state_json'] and ready['lab_json']==hand['lab_json'],'fixture distinto')
    pid=ready['fixture_pid'];require(type(pid) is int and pid>1,'PID inválido');os.kill(pid,0);process=subprocess.run(['ps','-p',str(pid),'-o','uid=','-o','command='],check=True,capture_output=True,text=True).stdout.strip();require(process.startswith(str(os.getuid())+' ') and hand['fixture_command_marker'] in process,'proceso distinto')
    target=urlsplit(hand['gateway']);ca=Path(hand['ca_pem']).resolve();require(hand['gateway']==ready['gateway']==lab['gateway'] and Path(ready['ca_pem']).resolve()==ca and Path(lab['ca']).resolve()==ca and target.scheme=='https' and ipaddress.ip_address(target.hostname).is_private and target.port==18443 and not(target.username or target.password or target.query or target.fragment),'origen distinto')
    for config in ready['effective_configuration'].values():require(config['TESTING'] is False and config['OPERATION_SCOPE']=='ACADEMIC','configuración distinta')
    actor_op=state['accounts'][hand['operator_actor']];actor_med=state['accounts'][hand['medical_actor']];require(actor_op['role']=='OPERATOR' and actor_med['role']=='MEDICAL' and actor_op['tenant_id']==actor_med['tenant_id'],'actores distintos')
    factor_path=support.private_file(Path(os.environ['COLD_FACTOR']).resolve());credentials=json.loads(factor_path.read_text());require(credentials['user_id']==actor_med['id'] and credentials['state']=='CONFIRMED','factor distinto')
    factor=base64.b32decode(credentials['totp_secret'].upper()+'='*(-len(credentials['totp_secret'])%8),casefold=True)
    def code():
        period=int(time.time())//30;digest=hmac.new(factor,struct.pack('>Q',period),hashlib.sha1).digest();offset=digest[-1]&15
        return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6),period
    with support.postgres(state,'identidad_acceso',fixture/'pg') as conn:
        row=conn.execute('SELECT last_counter FROM security_factors WHERE id=%s AND active',(actor_med['id'],)).fetchone()
    require(row is not None,'factor inactivo');last=max(row[0],credentials['last_mfa_period'])
    resource_id=support.uid(hand['resource_id']);lab_profile_id=support.uid(hand['lab_profile_id'])
    with support.postgres(state,'inventario',fixture/'pg') as conn:
        row=conn.execute('SELECT status,version,current_institution_id::text FROM resources WHERE id=%s',(resource_id,)).fetchone();controls=conn.execute('SELECT lab_profile_id::text,cold_equipment_id,cold_profile_id FROM resource_controls WHERE id=%s',(resource_id,)).fetchone()
    require(row==('QUARANTINE',2,actor_med['tenant_id']) and controls==(lab_profile_id,None,None),'unidad no corresponde')
    output=Path(os.environ['COLD_OUTPUT']).resolve();require(output.is_dir() and output.stat().st_uid==os.getuid() and output.stat().st_mode&0o777==0o700,'salida inválida')
    session=requests.Session();session.trust_env=False
    def request(method,address,**kwargs):
        u=urlsplit(address);require((u.scheme,u.hostname,u.port)==(target.scheme,target.hostname,target.port),'origen distinto');kwargs['verify']=str(ca);return session.request(method,address,**kwargs)
    requests.request=request;os.environ['REQUESTS_CA_BUNDLE']=str(ca);os.environ['REDHOUSE_BASE_URL']=hand['gateway']
    class Keys:
        def __init__(self):
            self.key=Fernet.generate_key();fd=os.open(output/'journal-key',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as stream:stream.write(self.key);stream.flush();os.fsync(stream.fileno())
        def get(self,_id,_exists):return self.key
    keys=Keys();desktop.Journal=lambda _root,base,user,tenant:Journal(output/'journal',base,user,tenant,keys)
    users=[actor_op['id'],actor_med['id']];before=snapshot(support.postgres,state,fixture,users)
    fd=os.open(output/'sessions-before.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(sorted(before),stream)
    app=QApplication.instance() or QApplication([]);app.setStyleSheet(desktop.STYLE);windows=[];active_count=0
    try:
        operator=desktop.Window();windows.append(operator);operator.show();operator.username.setText(hand['operator_actor']);operator.password.setText(lab['password']);operator.login();require(support.wait_until(lambda:not operator.busy) and operator.client and operator.client.user and operator.client.user.get('id')==actor_op['id'],'login operador');active_count+=1
        medical=desktop.Window();windows.append(medical);medical.show();medical.username.setText(hand['medical_actor']);medical.password.setText(lab['password']);medical.login();require(support.wait_until(lambda:not medical.busy),'login médico pendiente')
        if medical.stack.currentIndex()==0 and not medical.otp.isHidden():
            deadline=time.monotonic()+35
            while True:
                otp,period=code()
                if period>last and 30-int(time.time())%30>=8:break
                require(time.monotonic()<deadline,'periodo MFA no disponible');app.processEvents();time.sleep(.1)
            fd=os.open(output/'mfa-login-period.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as stream:json.dump({'period':period},stream)
            medical.password.setText(lab['password']);medical.otp.setText(otp);medical.login();require(support.wait_until(lambda:not medical.busy),'MFA pendiente')
        require(medical.client and medical.client.user and medical.client.user.get('id')==actor_med['id'],'login médico');active_count+=1
        resource=medical.client.authorized('inventario','/api/v1/resources/'+resource_id,'resource_detail',fresh_identity=True)
        result=run(operator,medical,resource,lab_profile_id,output,support.wait_until)
        with support.postgres(state,'inventario',fixture/'pg') as conn:
            linked=conn.execute('SELECT lab_profile_id::text,cold_equipment_id::text,cold_profile_id::text FROM resource_controls WHERE id=%s',(resource_id,)).fetchone()
            require(linked==(lab_profile_id,result['equipment_id'],result['profile_id']),'vínculo no persistido')
            for identifier,action,actor in ((result['equipment_id'],'COLD_EQUIPMENT_CREATED',actor_op['id']),(result['profile_id'],'COLD_PROFILE_CREATED',actor_med['id'])):
                require(support.event_count(conn,identifier,action,actor)==1,'evento no corresponde')
        fd=os.open(output/'cold-receipt.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(result,stream)
    finally:
        for window in reversed(windows):
            if window.busy:support.wait_until(lambda:not window.busy)
            active=bool(window.client and window.client.access);window.close()
            if active:support.wait_until(lambda:window.closing)
        session.close();closed=closure(support.postgres,support.private_file,state,fixture,users,before)
        fd=os.open(output/'sessions-closed.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(closed,stream)
        require(len(closed)==active_count,'cierre de sesiones distinto')


if __name__=='__main__':main()
