"""Navegación y contexto Qt sin servidores; llamadas propietarias simuladas."""
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PySide6.QtWidgets import QApplication
from redhouse_desktop import cold_catalogue
from redhouse_desktop.app import Window, display_value, sections_for
from redhouse_desktop.client import ContractError


@pytest.fixture
def window():
    app=QApplication.instance() or QApplication([])
    value=Window();value.client=SimpleNamespace(user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL'},session_id=str(uuid4()))
    value.journal=object();value.run_in_context=lambda binding,work,done,*args:done(work())
    yield value
    value.client=None;value.close();app.processEvents()


def test_catalogue_navigation_routes_pagination_and_permissions(window):
    calls=[]
    def authorized(service,path,operation,**kwargs):
        calls.append((service,path,operation,kwargs));return {'items':[],'page':2,'total':23}
    window.client.authorized=authorized
    for role,mode,can_create,can_correct in [('OPERATOR','cold_equipment',True,False),('MEDICAL','cold_equipment',False,False),
                                            ('MEDICAL','cold_profiles',True,True),('OPERATOR','cold_profiles',False,False)]:
        window.client.user['role']=role;window.mode=mode;window.page=2;window.load()
        assert calls[-1][0]=='inventario' and calls[-1][3]['params']=={'page':2,'page_size':20}
        assert calls[-1][2]==('cold_equipment_list' if mode=='cold_equipment' else 'cold_profiles_list')
        assert (not window.cold_create_button.isHidden())==can_create
        assert (not window.cold_correct_button.isHidden())==can_correct
        assert window.cold_create_button.isEnabled()==can_create and not window.search.isEnabled()
        window.set_controls(False);assert not window.cold_create_button.isEnabled()
    window.client.user['role']='COORDINATOR';window.set_controls(True)
    assert all(mode not in sections_for('COORDINATOR') for mode in cold_catalogue.CATALOGUES)
    before=len(calls);cold_catalogue.load_catalogue(window,display_value);assert len(calls)==before


@pytest.mark.parametrize('changed',[False,True])
def test_binding_uses_fresh_controls_and_never_sends_after_session_switch(window,monkeypatch,changed):
    resource={'id':str(uuid4()),'current_institution_id':window.client.user['tenant_id'],'status':'AVAILABLE','version':7}
    controls={'id':resource['id'],'lab_profile_id':str(uuid4())};window.mode='inventory';window.selected=lambda:resource
    seen=[];sent=[]
    window.client.authorized=lambda service,path,operation:resource if operation=='resource_detail' else controls
    def form(owner,row,original,work):
        assert row==resource and original==controls;seen.append(True)
        if changed:window.client.session_id=str(uuid4())
        return {'version':row['version'],'lab_profile_id':original['lab_profile_id']}
    monkeypatch.setattr(cold_catalogue,'bind_dialog',form);window.secure_command=lambda *args:sent.append(args)
    cold_catalogue.bind_selected(window,object)
    assert seen==[True]
    assert sent==([] if changed else [('resource_controls_create',resource['id'],{'version':7,'lab_profile_id':controls['lab_profile_id']})])


def test_other_resource_controls_stop_before_dialog_or_command(window,monkeypatch):
    resource={'id':str(uuid4()),'current_institution_id':window.client.user['tenant_id'],'status':'QUARANTINE','version':3}
    window.mode='inventory';window.selected=lambda:resource
    window.client.authorized=lambda service,path,operation:resource if operation=='resource_detail' else {'id':str(uuid4()),'lab_profile_id':str(uuid4())}
    monkeypatch.setattr(cold_catalogue,'bind_dialog',lambda *a:pytest.fail('No debe abrir el formulario'))
    window.secure_command=lambda *a:pytest.fail('No debe enviar comando')
    with pytest.raises(ContractError):cold_catalogue.bind_selected(window,object)


def test_profile_correction_reads_exact_predecessor_and_retains_version(window,monkeypatch):
    previous={'id':str(uuid4()),'tenant_id':window.client.user['tenant_id'],'version':3};window.mode='cold_profiles';window.selected=lambda:previous
    calls=[];sent=[]
    def authorized(service,path,operation):
        calls.append((path,operation));return previous
    window.client.authorized=authorized
    monkeypatch.setattr(cold_catalogue,'dialog',lambda owner,kind,prior:{'version':prior['version']+1,'supersedes':prior['id']})
    window.secure_command=lambda *args:sent.append(args)
    cold_catalogue.edit_catalogue(window,True)
    assert calls==[('/api/v1/cold/profiles/'+previous['id'],'cold_profiles_detail')]
    assert sent==[('cold_profile_create',None,{'version':4,'supersedes':previous['id']})]
