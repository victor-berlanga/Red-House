"""Laboratorio efímero con gateway TLS: sin uso de instalaciones persistentes."""
import datetime
import ipaddress
import threading
import uuid
from pathlib import Path

import pytest
import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from flask import Flask, Response, request
from werkzeug.serving import make_server
from tests.conftest import platform, QuietHandler
from redhouse_desktop.client import ApiError, Client

@pytest.fixture
def gateway(platform, tmp_path, monkeypatch):
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'127.0.0.1')])
    now=datetime.datetime.now(datetime.timezone.utc)
    cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1))
          .not_valid_after(now+datetime.timedelta(hours=1)).add_extension(x509.BasicConstraints(ca=True,path_length=None),True)
          .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),False)
          .sign(key,hashes.SHA256()))
    certpath=tmp_path/'cert.pem'; keypath=tmp_path/'key.pem'
    certpath.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    keypath.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    monkeypatch.setenv('REQUESTS_CA_BUNDLE',str(certpath))
    app=Flask(__name__)
    @app.route('/services/<service>/<path:path>',methods=['GET','POST','PATCH'])
    def proxy(service,path):
        service=service.replace('-','_')
        if service not in platform.urls: return Response(status=404)
        headers={k:v for k,v in request.headers if k.lower() not in ('host','content-length','connection')}
        upstream=requests.request(request.method,platform.urls[service]+'/'+path,params=request.args,
                                  data=request.get_data(),headers=headers,timeout=20)
        return Response(upstream.content,status=upstream.status_code,content_type=upstream.headers.get('Content-Type'))
    @app.route('/storage/v1/objects/<token>',methods=['GET'])
    def storage_proxy(token):
        upstream=requests.get(platform.urls['documentos']+'/storage/v1/objects/'+token,timeout=20,allow_redirects=False)
        return Response(upstream.content,status=upstream.status_code,content_type=upstream.headers.get('Content-Type'))
    server=make_server('127.0.0.1',0,app,threaded=True,request_handler=QuietHandler,ssl_context=(str(certpath),str(keypath)))
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try: yield 'https://127.0.0.1:'+str(server.server_port)
    finally: server.shutdown(); thread.join(); server.server_close()

def test_operator_inventory_sample_receipt_and_session(platform,gateway):
    p=platform; password=p.env.state['password']
    now=datetime.datetime.now(datetime.timezone.utc)
    iso=lambda t:t.isoformat()
    c=Client(gateway); user=c.login('operator1',password,''); assert user['role']=='OPERATOR'
    unit=c.authorized('inventario','/api/v1/resources','resource_create',method='POST',body={'folio':'DESK-'+uuid.uuid4().hex[:12],'kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':iso(now+datetime.timedelta(days=2))},request_schema='resource_create.xsd',key=str(uuid.uuid4()))
    profile=p.ok('compatibilidad','POST','/api/v1/laboratory/profiles',user='medical1',data={'name':'Perfil sintético de prueba','kind':'BLOOD','component':'RBC','version':1,'required_tests':['ABO'],'source':'Prueba sintética sin uso clínico','synthetic':True,'effective_at':iso(now)})
    sample=p.ok('compatibilidad','POST','/api/v1/laboratory/samples',user='operator1',data={'resource_id':unit['id'],'profile_id':profile['id'],'identifier':'DESK-'+uuid.uuid4().hex,'collected_at':iso(now-datetime.timedelta(minutes=5))})
    inventory=c.authorized('inventario','/api/v1/resources','resources_list',params={'page':1,'page_size':20,'q':unit['folio']})
    assert any(x['id']==unit['id'] for x in inventory['items'])
    detail=c.authorized('inventario','/api/v1/resources/'+unit['id'],'resource_detail'); assert detail['id']==unit['id']
    samples=c.authorized('compatibilidad','/api/v1/laboratory/samples','lab_samples_list',params={'page':1,'page_size':20,'q':sample['identifier']})
    assert any(x['id']==sample['id'] for x in samples['items'])
    path='/api/v1/laboratory/samples/'+sample['id']+'/receive'; body={'human_confirmation':'true','reason':'Recepción sintética autorizada','version':sample['version'],'decision':'RECEIVED'}
    received=c.authorized('compatibilidad',path,'lab_sample_receive',method='POST',body=body,request_schema='lab_sample_receive.xsd',key=str(uuid.uuid4()))
    assert received['status']=='RECEIVED'
    with pytest.raises(ApiError) as conflict:
        c.authorized('compatibilidad',path,'lab_sample_receive',method='POST',body=body,request_schema='lab_sample_receive.xsd',key=str(uuid.uuid4()))
    assert conflict.value.status in (409,412)
    result=c.authorized('compatibilidad','/api/v1/laboratory/results','lab_result_create',method='POST',body={'sample_id':sample['id'],'test_code':'ABO','value':'O','method':'Método sintético','laboratory':'Laboratorio sintético','reference':'Fuente sintética','measured_at':iso(now)},request_schema='lab_result_create.xsd',key=str(uuid.uuid4()))
    results=c.authorized('compatibilidad','/api/v1/laboratory/results','lab_results_list',params={'page':1,'page_size':20})
    assert any(x['id']==result['id'] for x in results['items'])
    review='/api/v1/laboratory/results/'+result['id']+'/review'
    review_body={'human_confirmation':'true','reason':'Revisión profesional sintética','version':result['version'],'decision':'AUTHORIZED'}
    with pytest.raises(ApiError) as denied:
        c.authorized('compatibilidad',review,'lab_result_review',method='POST',body=review_body,request_schema='lab_result_review.xsd',key=str(uuid.uuid4()))
    assert denied.value.status==403
    doctor=Client(gateway); doctor.login('medical1',password,'')
    reviewed=doctor.authorized('compatibilidad',review,'lab_result_review',method='POST',body=review_body,request_schema='lab_result_review.xsd',key=str(uuid.uuid4()))
    assert reviewed['status']=='AUTHORIZED'
    doctor.logout()
    assert isinstance(c.authorized('alertas','/api/v1/alerts','alerts_list')['items'],list)
    old=c.access; c.logout(); assert c.access is None and c.refresh is None
    c.access=old
    with pytest.raises(ApiError) as revoked:
        c.call('inventario','/api/v1/resources','resources_list')
    c.clear()
    assert revoked.value.status==401


def test_authenticated_qt_inventory_and_detail(platform,gateway,monkeypatch):
    """Ventanas reales con datos sintéticos servidos por el laboratorio TLS."""
    import os
    from PySide6.QtCore import QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from redhouse_desktop.app import Window, STYLE
    now=datetime.datetime.now(datetime.timezone.utc)
    platform.ok('inventario','POST','/api/v1/resources',user='operator1',data={'folio':'GUI-SINTETICA-01','kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':(now+datetime.timedelta(days=2)).isoformat()})
    monkeypatch.setenv('REDHOUSE_BASE_URL',gateway)
    app=QApplication.instance() or QApplication([]); app.setStyleSheet(STYLE)
    window=Window(); window.show(); window.username.setText('operator1'); window.password.setText(platform.env.state['password']); window.login()
    for _ in range(1500):
        QTest.qWait(20)
        if window.stack.currentIndex()==1 and not window.busy and window.rows: break
    assert window.stack.currentIndex()==1 and any(row.get('folio')=='GUI-SINTETICA-01' for row in window.rows)
    out=Path(os.environ['DESKTOP_CAPTURE_DIR']); out.mkdir(parents=True,exist_ok=True)
    window.grab().save(str(out/'laboratorio-inventario.png'))
    index=next(i for i,row in enumerate(window.rows) if row.get('folio')=='GUI-SINTETICA-01'); window.table.selectRow(index)
    captured=[]
    def capture_detail():
        modal=QApplication.activeModalWidget()
        if modal:
            modal.grab().save(str(out/'laboratorio-detalle.png')); captured.append(True); modal.reject()
        else: QTimer.singleShot(100,capture_detail)
    QTimer.singleShot(100,capture_detail); window.open_selected()
    for _ in range(1000):
        QTest.qWait(20)
        if captured and not window.busy: break
    assert captured
    summary=[]
    def capture_summary():
        modal=QApplication.activeModalWidget()
        if modal and modal.windowTitle()=='Resumen operativo':
            modal.grab().save(str(out/'laboratorio-resumen.png')); summary.append(True); modal.reject()
        elif not summary: QTimer.singleShot(100,capture_summary)
    QTimer.singleShot(100,capture_summary); window.open_summary()
    for _ in range(1000):
        QTest.qWait(20)
        if summary and not window.busy: break
    assert summary
    window.close()
    for _ in range(500):
        QTest.qWait(20)
        if not window.busy: break


def test_report_request_and_owner_scope_over_xml(platform,gateway):
    c=Client(gateway); c.login('operator1',platform.env.state['password'],'')
    now=datetime.datetime.now(datetime.timezone.utc)
    body={'report':'INVENTORY','format':'CSV','from_at':(now-datetime.timedelta(days=1)).isoformat(),'until_at':(now+datetime.timedelta(days=1)).isoformat(),'timezone':'America/Monterrey'}
    job=c.authorized('documentos','/api/v1/export-jobs','export_create',method='POST',body=body,request_schema='export_create.xsd',key=str(uuid.uuid4()))
    found=c.authorized('documentos','/api/v1/export-jobs/'+job['id'],'export_detail')
    assert found['id']==job['id'] and found['report']=='INVENTORY'
    other=Client(gateway); other.login('operator2',platform.env.state['password'],'')
    with pytest.raises(ApiError) as denied: other.authorized('documentos','/api/v1/export-jobs/'+job['id'],'export_detail')
    assert denied.value.status==403
    other.logout(); c.logout()


def test_real_local_report_download_with_verified_tls(platform,gateway,tmp_path,monkeypatch):
    import os
    from ms_documentos.reports import process
    from redhouse_desktop.download import DownloadError, download
    port=os.environ.get('REDHOUSE_TEST_CLAMD_PORT')
    if not port: pytest.skip('Requiere ClamAV local real en un puerto de laboratorio.')
    p=platform; document=p.apps['documentos']; root=tmp_path/'objects'; root.mkdir(mode=0o700)
    monkeypatch.setitem(document.config,'STORAGE_PROVIDER','local')
    monkeypatch.setitem(document.config,'STORAGE_LOCAL_ROOT',str(root))
    monkeypatch.setitem(document.config,'STORAGE_PUBLIC_BASE_URL',gateway)
    now=datetime.datetime.now(datetime.timezone.utc)
    unit=p.ok('inventario','POST','/api/v1/resources',user='operator1',data={'folio':'REPORT-'+uuid.uuid4().hex[:12],'kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':(now+datetime.timedelta(days=2)).isoformat()})
    c=Client(gateway); c.login('operator1',p.env.state['password'],'')
    body={'report':'INVENTORY','format':'CSV','from_at':(now-datetime.timedelta(days=1)).isoformat(),'until_at':(now+datetime.timedelta(days=1)).isoformat(),'timezone':'America/Monterrey'}
    job=c.authorized('documentos','/api/v1/export-jobs','export_create',method='POST',body=body,request_schema='export_create.xsd',key=str(uuid.uuid4()))
    monkeypatch.setitem(document.config,'CLAMD_HOST','127.0.0.1'); monkeypatch.setitem(document.config,'CLAMD_PORT',int(port))
    with document.app_context(): process(limit=1)
    ready=c.authorized('documentos','/api/v1/export-jobs/'+job['id'],'export_detail')
    assert ready['status']=='COMPLETE' and ready['file_id'], (ready['status'],ready.get('last_error'))
    verified=c.authorized('documentos','/api/v1/documents/'+ready['file_id']+'/verified','document_verified')
    assert verified['analysis']=='CLEAN' and verified['file_status']=='VERIFIED'
    access=c.authorized('documentos','/api/v1/files/'+ready['file_id']+'/download','file_download')
    destination=tmp_path/'reporte.csv'
    download(access['download_url'],gateway,verified['sha256'],destination)
    assert unit['folio'] in destination.read_text(encoding='utf-8-sig')
    c.logout()
    with pytest.raises(DownloadError): download(access['download_url'],gateway,verified['sha256'],tmp_path/'revocado.csv')
    assert not (tmp_path/'revocado.csv').exists()


def test_summary_projections_over_xml(platform,gateway):
    for actor in ('operator1','coordinator1'):
        c=Client(gateway); c.login(actor,platform.env.state['password'],'')
        for service in ('inventario','receptores','transporte'):
            data=c.authorized(service,'/api/v1/summary','portal_summary')
            assert data['total']==sum(row['value'] for row in data['statuses'])
            if service=='inventario': assert data['expiring']>=0
        c.logout()
    donor=Client(gateway); donor.login('donor1',platform.env.state['password'],'')
    with pytest.raises(ApiError) as denied:
        donor.authorized('inventario','/api/v1/summary','portal_summary')
    assert denied.value.status==403
    donor.logout()


def test_medical_creates_request_through_qt(platform,gateway,monkeypatch,tmp_path):
    import os
    from cryptography.fernet import Fernet
    from PySide6.QtCore import QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton, QSpinBox, QTableWidget
    import redhouse_desktop.app as desktop
    from redhouse_desktop.journal import Journal
    from tests.helpers import recipient_request
    person,_=recipient_request(platform)
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,identifier,exists): return self.key
    keys=Keys()
    monkeypatch.setattr(desktop,'Journal',lambda _root,base,user,tenant:Journal(tmp_path,base,user,tenant,keys))
    monkeypatch.setenv('REDHOUSE_BASE_URL',gateway)
    app=QApplication.instance() or QApplication([]); app.setStyleSheet(desktop.STYLE)
    window=desktop.Window(); window.show(); window.username.setText('medical2'); window.password.setText(platform.env.state['password']); window.login()
    for _ in range(1500):
        QTest.qWait(20)
        if window.stack.currentIndex()==1 and not window.busy: break
    assert window.stack.currentIndex()==1
    window.switch('requests')
    for _ in range(1500):
        QTest.qWait(20)
        if not window.busy: break
    assert window.request_create_button.isVisible() and window.request_create_button.isEnabled()
    captured=[]; state={'search_started':False,'alive':True}
    def interact():
        if not state['alive']: return
        modal=QApplication.activeModalWidget()
        if modal and modal.windowTitle()=='Registrar solicitud':
            table=modal.findChild(QTableWidget)
            if not state['search_started'] and table.rowCount()>0:
                field=next(x for x in modal.findChildren(QLineEdit) if x.placeholderText()=='Buscar receptor por folio o nombre')
                field.setText(person['folio']); state['search_started']=True
                next(b for b in modal.findChildren(QPushButton) if b.text()=='Buscar').click()
            elif state['search_started']:
                row=next((i for i in range(table.rowCount()) if table.item(i,0) and table.item(i,0).text()==person['folio']),None)
                if row is not None:
                    table.selectRow(row); choices=modal.findChildren(QComboBox)
                    choices[0].setCurrentIndex(choices[0].findData('RBC')); choices[1].setCurrentIndex(choices[1].findData(2))
                    modal.findChild(QSpinBox).setValue(2); app.processEvents()
                    out=Path(os.environ['DESKTOP_CAPTURE_DIR']); out.mkdir(parents=True,exist_ok=True)
                    modal.grab().save(str(out/'laboratorio-solicitud.png')); captured.append(True)
                    next(b for b in modal.findChildren(QPushButton) if b.text()=='Registrar solicitud').click()
        QTimer.singleShot(100,interact)
    QTimer.singleShot(100,interact); window.open_request_form()
    for _ in range(2000):
        QTest.qWait(20)
        if captured and not window.busy and any(row.get('recipient_id')==person['id'] and row.get('quantity')==2 for row in window.rows): break
    state['alive']=False
    assert captured and any(row.get('recipient_id')==person['id'] and row.get('quantity')==2 for row in window.rows)
    window.close()


def test_operator_creates_organ_through_qt(platform,gateway,monkeypatch,tmp_path):
    import os
    from cryptography.fernet import Fernet
    from PySide6.QtCore import QDateTime, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDateTimeEdit, QLineEdit, QPushButton
    import redhouse_desktop.app as desktop
    from redhouse_desktop.journal import Journal
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,identifier,exists): return self.key
    keys=Keys()
    monkeypatch.setattr(desktop,'Journal',lambda _root,base,user,tenant:Journal(tmp_path,base,user,tenant,keys))
    monkeypatch.setenv('REDHOUSE_BASE_URL',gateway)
    app=QApplication.instance() or QApplication([]); app.setStyleSheet(desktop.STYLE)
    window=desktop.Window(); window.show(); window.username.setText('operator1'); window.password.setText(platform.env.state['password']); window.login()
    for _ in range(1500):
        QTest.qWait(20)
        if window.stack.currentIndex()==1 and not window.busy: break
    assert window.stack.currentIndex()==1
    folio='GUI-ORG-'+uuid.uuid4().hex[:8]; captured=[]
    def fill():
        modal=QApplication.activeModalWidget()
        if not modal: QTimer.singleShot(50,fill); return
        modal.findChild(QLineEdit).setText(folio)
        boxes=modal.findChildren(QComboBox); boxes[0].setCurrentIndex(boxes[0].findData('ORGAN'))
        boxes[1].setCurrentIndex(boxes[1].findData('KIDNEY')); boxes[2].setCurrentIndex(boxes[2].findData('O+'))
        checks=modal.findChildren(QCheckBox); checks[0].setChecked(True); checks[1].setChecked(True); dates=modal.findChildren(QDateTimeEdit)
        dates[0].setDateTime(QDateTime.currentDateTime().addDays(-1)); dates[1].setDateTime(QDateTime.currentDateTime().addDays(1))
        app.processEvents(); out=Path(os.environ['DESKTOP_CAPTURE_DIR']); out.mkdir(parents=True,exist_ok=True)
        modal.grab().save(str(out/'laboratorio-unidad-organo.png')); captured.append(True)
        next(button for button in modal.findChildren(QPushButton) if button.text()=='Registrar unidad').click()
    QTimer.singleShot(50,fill); window.create_resource()
    for _ in range(2000):
        QTest.qWait(20)
        if captured and not window.busy and any(row.get('folio')==folio for row in window.rows): break
    assert captured and any(row.get('folio')==folio and row.get('kind')=='ORGAN' and row.get('component')=='KIDNEY' and row.get('status')=='QUARANTINE' for row in window.rows)
    window.close()


def test_blood_components_are_registered_in_quarantine_over_xml(platform,gateway,tmp_path):
    from cryptography.fernet import Fernet
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    from redhouse_desktop.journal import Journal
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,identifier,exists): return self.key
    client=Client(gateway); user=client.login('operator1',platform.env.state['password'],'')
    journal=Journal(tmp_path,gateway,user['id'],user['tenant_id'],Keys())
    now=datetime.datetime.now(datetime.timezone.utc)
    for component in ('PLASMA','PLATELETS'):
        body={'folio':'GUI-'+uuid.uuid4().hex[:12],'kind':'BLOOD','component':component,'blood_group':'O-',
              'collected_at':(now-datetime.timedelta(hours=1)).isoformat(),'expires_at':(now+datetime.timedelta(days=1)).isoformat()}
        result=submit_command(client,journal,prepare_command(journal,'resource_create',None,body),fresh=True)
        assert result['component']==component and result['status']=='QUARANTINE'
    client.logout()


def test_destination_accepts_verified_handover_over_xml(platform,gateway,tmp_path):
    from cryptography.fernet import Fernet
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    from redhouse_desktop.journal import Journal
    from tests.helpers import resource, recipient_request, evaluation, reservation, plan, move

    p=platform; unit=resource(p); _,request=recipient_request(p)
    allocation=reservation(p,evaluation(p,request,[unit]),unit)['reservation']
    shipment=plan(p,allocation)
    for state,actor in (('PREPARED','operator1'),('COLLECTED','transport1'),('IN_TRANSIT','transport1'),('DELIVERED','transport1')):
        shipment=move(p,shipment,state,actor)
    c=Client(gateway); user=c.login('operator2',p.env.state['password'],'')
    path='/api/v1/shipments/'+shipment['id']
    detail=c.authorized('transporte',path,'shipment_detail')
    context=c.authorized('transporte',path+'/operational-context','operational_context')
    person=c.authorized('transporte',path+'/operational-handover','operational_handover')
    assert person['shipment_version']==context['shipment_version']==detail['version']
    assert person['transport_user']['id']==context['transport_user_id']==detail['transport_user_id']
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,identifier,exists): return self.key
    journal=Journal(tmp_path,gateway,user['id'],user['tenant_id'],Keys())
    scanned=submit_command(c,journal,prepare_command(journal,'shipment_scan',shipment['id'],{'scanned_resource_id':unit['id']}))
    assert scanned['verified'] and scanned['resource_id']==unit['id'] and scanned['version']==detail['version']
    body={'state':'ACCEPTED','version':detail['version'],'human_confirmation':True,'reason':'Recepción sintética autorizada',
          'custody':{'scanned_resource_id':unit['id'],'seal':'Sello sintético','captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'reported_handover_user_id':person['transport_user']['id'],'electronic_acceptance':True}}
    accepted=submit_command(c,journal,prepare_command(journal,'shipment_transition',shipment['id'],body))
    assert accepted['status']=='ACCEPTED'
    c.logout()


def test_destination_handover_in_authenticated_qt(platform,gateway,tmp_path,monkeypatch):
    import os
    from cryptography.fernet import Fernet
    from PySide6.QtCore import QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QCheckBox, QLineEdit, QPushButton
    import redhouse_desktop.app as desktop
    from redhouse_desktop.journal import Journal
    from tests.helpers import resource, recipient_request, evaluation, reservation, plan, move

    p=platform; unit=resource(p); _,request=recipient_request(p)
    shipment=plan(p,reservation(p,evaluation(p,request,[unit]),unit)['reservation'])
    for state,actor in (('PREPARED','operator1'),('COLLECTED','transport1'),('IN_TRANSIT','transport1'),('DELIVERED','transport1')):
        shipment=move(p,shipment,state,actor)
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,identifier,exists): return self.key
    keys=Keys()
    monkeypatch.setattr(desktop,'Journal',lambda _root,base,user,tenant:Journal(tmp_path,base,user,tenant,keys))
    monkeypatch.setattr(desktop,'CUSTODY_ACCEPT_ENABLED',True)
    monkeypatch.setenv('REDHOUSE_BASE_URL',gateway)
    app=QApplication.instance() or QApplication([]); app.setStyleSheet(desktop.STYLE)
    window=desktop.Window(); window.show(); window.username.setText('operator2'); window.password.setText(p.env.state['password']); window.login()
    for _ in range(1500):
        QTest.qWait(20)
        if window.stack.currentIndex()==1 and not window.busy and window.rows: break
    assert window.stack.currentIndex()==1 and not window.busy
    window.switch('shipments')
    for _ in range(1500):
        QTest.qWait(20)
        if not window.busy and any(row['id']==shipment['id'] for row in window.rows): break
    index=next(i for i,row in enumerate(window.rows) if row['id']==shipment['id']); window.table.selectRow(index)
    captured=[]; deadline={'active':True}
    def interact():
        if not deadline['active']: return
        modal=QApplication.activeModalWidget()
        if modal and modal.windowTitle()=='Detalle del traslado':
            button=next((b for b in modal.findChildren(QPushButton) if b.text()=='Documentar recepción'),None)
            assert button is not None
            button.click()
        elif modal and modal.windowTitle()=='Documentar recepción':
            fields=modal.findChildren(QLineEdit)
            fields[0].setText(unit['id']); fields[1].setText('Sello sintético'); fields[2].setText('Recepción sintética autorizada')
            modal.findChild(QCheckBox).setChecked(True); app.processEvents()
            output=Path(os.environ['DESKTOP_CAPTURE_DIR']); output.mkdir(parents=True,exist_ok=True)
            modal.grab().save(str(output/'laboratorio-recepcion-custodia.png')); captured.append(True)
            next(b for b in modal.findChildren(QPushButton) if b.text()=='Confirmar recepción').click()
        QTimer.singleShot(100,interact)
    QTimer.singleShot(100,interact); window.open_selected()
    for _ in range(2000):
        QTest.qWait(20)
        if captured and not window.busy and any(row['id']==shipment['id'] and row['status']=='ACCEPTED' for row in window.rows): break
    deadline['active']=False
    assert captured and any(row['id']==shipment['id'] and row['status']=='ACCEPTED' for row in window.rows)
    window.close()


def test_medical_request_evaluation_and_reservation(platform,gateway):
    from tests.helpers import resource, recipient_request, route
    p=platform
    unit=resource(p)
    _,req=recipient_request(p)
    route(p)
    c=Client(gateway); c.login('medical2',p.env.state['password'],'')
    requests_data=c.authorized('receptores','/api/v1/requests','requests_list',params={'page':1,'page_size':100})
    assert any(x['id']==req['id'] for x in requests_data['items'])
    body={'request_id':req['id']}
    evaluation=c.authorized('compatibilidad','/api/v1/evaluations','evaluation_create',method='POST',body=body,request_schema='evaluation_create.xsd',key=str(uuid.uuid4()))
    detail=c.authorized('compatibilidad','/api/v1/evaluations/'+evaluation['id'],'evaluation_detail')
    assert any(x['resource_id']==unit['id'] for x in detail['candidates'])
    decision={'human_confirmation':'true','reason':'Dictamen médico sintético','resource_id':unit['id'],'decision':'FAVORABLE'}
    c.authorized('compatibilidad','/api/v1/evaluations/'+evaluation['id']+'/reviews','evaluation_review',method='POST',body=decision,request_schema='evaluation_review.xsd',key=str(uuid.uuid4()))
    reserve={'human_confirmation':'true','reason':'Reserva médica sintética','resource_id':unit['id'],'evaluation_id':evaluation['id']}
    saved=c.authorized('inventario','/api/v1/reservations','reservation_create',method='POST',body=reserve,request_schema='reservation_create.xsd',key=str(uuid.uuid4()))
    if saved['status'] != 'COMPLETED':
        saved=c.authorized('inventario','/api/v1/operations/'+saved['operation_id']+'/resume','operation_resume',method='POST',key=str(uuid.uuid4()))
    assert saved['status']=='COMPLETED' and saved['reservation']['resource_id']==unit['id']
    assert any(x['id']==saved['reservation']['id'] for x in c.authorized('inventario','/api/v1/reservations','reservation_list',params={'page':1,'page_size':100})['items'])
    c.logout()


def test_label_authorization_recovery_reuses_idempotency(platform,gateway,tmp_path):
    from cryptography.fernet import Fernet
    from redhouse_desktop.journal import Journal
    from redhouse_desktop.label_issuance import prepare_label, submit_label
    class Keys:
        def get(self,identifier,exists): return secret
    secret=Fernet.generate_key(); c=Client(gateway); user=c.login('operator1',platform.env.state['password'],'')
    now=datetime.datetime.now(datetime.timezone.utc)
    unit=c.authorized('inventario','/api/v1/resources','resource_create',method='POST',body={'folio':'LAB-'+uuid.uuid4().hex[:12],'kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':(now+datetime.timedelta(days=2)).isoformat()},request_schema='resource_create.xsd',key=str(uuid.uuid4()))
    journal=Journal(tmp_path,gateway,user['id'],user['tenant_id'],Keys()); record=prepare_label(journal,unit,'EXPORT_PDF','Etiqueta sintética de prueba')
    class LostResponse:
        first=None
        def authorized(self,*args,**kwargs):
            self.first=c.authorized(*args,**kwargs)
            raise ConnectionError('respuesta perdida')
    lost=LostResponse()
    with pytest.raises(ConnectionError): submit_label(lost,journal,record)
    restored=Journal(tmp_path,gateway,user['id'],user['tenant_id'],Keys()); response=submit_label(c,restored,restored.list()[0])
    assert response['issuance_id']==lost.first['issuance_id']
    assert restored.list()[0]['state']=='PENDING' and restored.list()[0]['status']=='AUTHORIZED'
    c.logout()


def test_native_keychain_recovers_real_committed_response_after_process_exit(platform,gateway,tmp_path):
    import json, os, subprocess, sys
    import keyring
    from redhouse_desktop.journal import Journal
    from redhouse_desktop.label_issuance import submit_label
    if os.environ.get('REDHOUSE_NATIVE_LAB')!='1' or sys.platform!='darwin':
        pytest.skip('Requiere llavero macOS real autorizado para prueba sintética.')
    p=platform; now=datetime.datetime.now(datetime.timezone.utc)
    unit=p.ok('inventario','POST','/api/v1/resources',user='operator1',data={'folio':'KEY-'+uuid.uuid4().hex[:12],'kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':(now+datetime.timedelta(days=2)).isoformat()})
    client=Client(gateway); user=client.login('operator1',p.env.state['password'],'')
    journal=Journal(tmp_path,gateway,user['id'],user['tenant_id'])
    try:
        request={'gateway':gateway,'username':'operator1','password':p.env.state['password'],'unit':unit,'directory':str(tmp_path)}
        worker=Path(__file__).with_name('native_lab_worker.py')
        subprocess.run([sys.executable,str(worker)],input=json.dumps(request),text=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=40)
        records=journal.list(); assert len(records)==1 and records[0]['state']=='UNCERTAIN'
        response=submit_label(client,journal,records[0])
        assert response['resource_id']==unit['id'] and response['reissue'] is False
        with p.owner('inventario') as conn:
            count=conn.execute("SELECT count(*) FROM activity_events WHERE event->>'resource_id'=%s AND event->>'action'='LABEL_ISSUANCE_AUTHORIZED'",(unit['id'],)).fetchone()[0]
        assert count==1 and journal.list()[0]['status']=='AUTHORIZED'
        client.logout()
    finally:
        client.clear()
        if keyring.get_password('RedHouse desktop journal',journal.identifier) is not None:
            keyring.delete_password('RedHouse desktop journal',journal.identifier)



def sec_contract_overlay(monkeypatch,tmp_path):
    """Permite validar un worktree aislado sin alterar contratos instalados."""
    import os, shutil
    import redhouse_desktop.client as client_module
    source=os.environ.get('REDHOUSE_SEC_CONTRACT_SOURCE')
    if not source: return
    root=Path(source); target=tmp_path/'contracts'; shutil.copytree(client_module.CONTRACTS,target)
    for service,name in (('identidad_acceso','identidad'),('compatibilidad','compatibilidad'),('inventario','inventario')):
        shutil.copyfile(root/('ms_'+service)/'contracts'/'openapi.json',target/(name+'.json'))
    shutil.copyfile(root/'ms_identidad_acceso'/'contracts'/'reauthenticate.xsd',target/'reauthenticate.xsd')
    monkeypatch.setattr(client_module,'CONTRACTS',target)


def test_mfa_proofs_for_evaluation_and_reservation(platform,gateway,monkeypatch,tmp_path):
    """Evalúa dos acciones críticas reales, cada una con código TOTP distinto."""
    import time
    from ms_identidad_acceso.strong_auth import totp
    from tests.helpers import resource, recipient_request, route
    sec_contract_overlay(monkeypatch,tmp_path)
    p=platform; password=p.env.state['password']; unit=resource(p); _,req=recipient_request(p); route(p)
    evaluation=p.ok('compatibilidad','POST','/api/v1/evaluations',user='medical2',data={'request_id':req['id']})
    assert any(x['resource_id']==unit['id'] for x in evaluation['candidates'])
    enrolled=p.ok('identidad_acceso','POST','/api/v1/auth/mfa/enrollment',user=None,data={'username':'medical2','password':password})
    p.ok('identidad_acceso','POST','/api/v1/auth/mfa/confirm',user=None,data={'challenge':enrolled['challenge'],'code':totp(enrolled['secret'],int(time.time())//30-1)})
    identity=p.apps['identidad_acceso']; compatibility=p.apps['compatibilidad']; inventory=p.apps['inventario']
    old_roles=identity.config['MFA_REQUIRED_ROLES']; old_eval=compatibility.config['REAUTH_REQUIRED_OPERATIONS']; old_reserve=inventory.config['REAUTH_REQUIRED_OPERATIONS']
    identity.config['MFA_REQUIRED_ROLES']=['MEDICAL']; compatibility.config['REAUTH_REQUIRED_OPERATIONS']=['evaluation_review']; inventory.config['REAUTH_REQUIRED_OPERATIONS']=['reservation_create']
    try:
        c=Client(gateway); c.login('medical2',password,totp(enrolled['secret'],int(time.time())//30))
        evaluation_path='/api/v1/evaluations/'+evaluation['id']+'/reviews'
        decision={'human_confirmation':'true','reason':'Dictamen médico sintético','resource_id':unit['id'],'decision':'FAVORABLE'}
        decision_key=str(uuid.uuid4())
        with pytest.raises(ApiError) as denied:
            c.authorized('compatibilidad',evaluation_path,'evaluation_review',method='POST',body=decision,request_schema='evaluation_review.xsd',key=decision_key)
        assert denied.value.code=='reauthentication_required'
        counter=int(time.time())//30+1
        proof=c.authorized('identidad-acceso','/api/v1/auth/reauthentication-proofs','reauthenticate',method='POST',body={'password':password,'otp':totp(enrolled['secret'],counter),'challenge':denied.value.challenge()},request_schema='reauthenticate.xsd')
        c.authorized('compatibilidad',evaluation_path,'evaluation_review',method='POST',body=decision,request_schema='evaluation_review.xsd',key=decision_key,proof=proof['proof'])
        reservation={'human_confirmation':'true','reason':'Reserva médica sintética','resource_id':unit['id'],'evaluation_id':evaluation['id']}
        reservation_key=str(uuid.uuid4())
        with pytest.raises(ApiError) as denied_reservation:
            c.authorized('inventario','/api/v1/reservations','reservation_create',method='POST',body=reservation,request_schema='reservation_create.xsd',key=reservation_key)
        assert denied_reservation.value.code=='reauthentication_required'
        deadline=time.monotonic()+35
        while int(time.time())//30+1<=counter and time.monotonic()<deadline: time.sleep(0.5)
        assert int(time.time())//30+1>counter
        proof=c.authorized('identidad-acceso','/api/v1/auth/reauthentication-proofs','reauthenticate',method='POST',body={'password':password,'otp':totp(enrolled['secret'],int(time.time())//30+1),'challenge':denied_reservation.value.challenge()},request_schema='reauthenticate.xsd')
        saved=c.authorized('inventario','/api/v1/reservations','reservation_create',method='POST',body=reservation,request_schema='reservation_create.xsd',key=reservation_key,proof=proof['proof'])
        assert saved['status'] in ('PENDING','COMPLETED') and saved['operation_id']
        c.logout()
    finally:
        identity.config['MFA_REQUIRED_ROLES']=old_roles; compatibility.config['REAUTH_REQUIRED_OPERATIONS']=old_eval; inventory.config['REAUTH_REQUIRED_OPERATIONS']=old_reserve

def test_mfa_and_critical_review_require_real_proof(platform,gateway,monkeypatch,tmp_path):
    """Fuerza controles productivos en el fixture; datos y factor son efímeros."""
    import time
    from ms_identidad_acceso.strong_auth import totp
    sec_contract_overlay(monkeypatch,tmp_path)
    p=platform; password=p.env.state['password']; now=datetime.datetime.now(datetime.timezone.utc)
    unit=p.ok('inventario','POST','/api/v1/resources',user='operator1',data={'folio':'MFA-'+uuid.uuid4().hex[:12],'kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':(now+datetime.timedelta(days=2)).isoformat()})
    profile=p.ok('compatibilidad','POST','/api/v1/laboratory/profiles',user='medical1',data={'name':'Perfil sintético MFA','kind':'BLOOD','component':'RBC','version':1,'required_tests':['ABO'],'source':'Prueba sintética sin uso clínico','synthetic':True,'effective_at':now.isoformat()})
    sample=p.ok('compatibilidad','POST','/api/v1/laboratory/samples',user='operator1',data={'resource_id':unit['id'],'profile_id':profile['id'],'identifier':'MFA-'+uuid.uuid4().hex,'collected_at':(now-datetime.timedelta(minutes=5)).isoformat()})
    p.ok('compatibilidad','POST','/api/v1/laboratory/samples/'+sample['id']+'/receive',user='operator1',data={'human_confirmation':True,'reason':'Recepción sintética','version':1,'decision':'RECEIVED'})
    result=p.ok('compatibilidad','POST','/api/v1/laboratory/results',user='operator1',data={'sample_id':sample['id'],'test_code':'ABO','value':'O','method':'Método sintético','laboratory':'Laboratorio sintético','reference':'Referencia sintética','measured_at':now.isoformat()})
    enrolled=p.ok('identidad_acceso','POST','/api/v1/auth/mfa/enrollment',user=None,data={'username':'medical1','password':password})
    p.ok('identidad_acceso','POST','/api/v1/auth/mfa/confirm',user=None,data={'challenge':enrolled['challenge'],'code':totp(enrolled['secret'],int(time.time())//30-1)})
    identity=p.apps['identidad_acceso']; compatibility=p.apps['compatibilidad']
    old_roles=identity.config['MFA_REQUIRED_ROLES']; old_critical=compatibility.config['REAUTH_REQUIRED_OPERATIONS']
    identity.config['MFA_REQUIRED_ROLES']=['MEDICAL']; compatibility.config['REAUTH_REQUIRED_OPERATIONS']=['lab_result_review']
    try:
        c=Client(gateway)
        with pytest.raises(ApiError) as missing: c.login('medical1',password,'')
        assert missing.value.code=='mfa_required'
        c.login('medical1',password,totp(enrolled['secret'],int(time.time())//30))
        path='/api/v1/laboratory/results/'+result['id']+'/review'
        body={'human_confirmation':'true','reason':'Revisión médica sintética','version':1,'decision':'AUTHORIZED'}
        review_key=str(uuid.uuid4())
        with pytest.raises(ApiError) as denied:
            c.authorized('compatibilidad',path,'lab_result_review',method='POST',body=body,request_schema='lab_result_review.xsd',key=review_key)
        assert denied.value.code=='reauthentication_required'
        challenge=c.authorized('identidad-acceso','/api/v1/auth/reauthentication-proofs','reauthenticate',method='POST',body={'password':password,'otp':totp(enrolled['secret'],int(time.time())//30+1),'challenge':denied.value.challenge()},request_schema='reauthenticate.xsd')
        reviewed=c.authorized('compatibilidad',path,'lab_result_review',method='POST',body=body,request_schema='lab_result_review.xsd',key=review_key,proof=challenge['proof'])
        assert reviewed['status']=='AUTHORIZED'
        c.logout()
    finally:
        identity.config['MFA_REQUIRED_ROLES']=old_roles; compatibility.config['REAUTH_REQUIRED_OPERATIONS']=old_critical
