"""Navegación por perfil de la consola: cada rol ve exactamente sus secciones, sin opciones grises."""
import os
from types import SimpleNamespace
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from redhouse_desktop.app import NAV_PROFILES, SECTION_TITLES, STYLE, Window, initial_section, sections_for

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)

# Secciones esperadas (copia deliberada de la matriz de perfiles; si cambia, debe cambiar aquí).
ESPERADAS = {
    'OPERATOR': {'inventory','samples','results','donations','requests','reservations','shipments','alerts','recipients','cold_equipment','cold_profiles','reports','pending'},
    'MEDICAL': {'inventory','samples','results','requests','evaluations','reservations','recipients','alerts','donations','shipments','coverage','cold_equipment','cold_profiles','reports','pending'},
    'COORDINATOR': {'shipments','inventory','reservations','coverage','alerts','reports','pending','users'},
}
EXCLUSIVAS_OTROS = {'devices','sites','capacities','audit'}


class Cliente:
    def __init__(self, role): self.user={'username':'prueba','id':'1','tenant_id':'2','role':role}; self.access=None; self.session_id='3'
    def authorized(self,*a,**k): return {'items':[],'page':1,'page_size':20,'total':0}


def abrir(role):
    w=Window(); w.client=Cliente(role); w.stack.setCurrentIndex(1); w.mode=initial_section(role); w.show(); w.set_controls(True); w.update_navigation(); app.processEvents()
    return w


def visibles(w):
    barra={m for m,b in w.nav_buttons.items() if b.isVisible()}
    return barra, set(w.more_modes)


@pytest.mark.parametrize('role',sorted(ESPERADAS))
def test_cada_perfil_ve_exactamente_sus_secciones(role):
    w=abrir(role); barra,mas=visibles(w)
    assert barra|mas==ESPERADAS[role] and not barra&mas and set(sections_for(role))==ESPERADAS[role]
    assert not (barra|mas)&EXCLUSIVAS_OTROS
    assert w.more_button.isVisible()==bool(mas)
    assert [a.text() for a in w.more_menu.actions()]==[SECTION_TITLES[m] for m in NAV_PROFILES[role]['more']]
    w.close()


@pytest.mark.parametrize('role',sorted(ESPERADAS))
def test_ninguna_opcion_de_navegacion_esta_deshabilitada(role):
    w=abrir(role)
    assert all(b.isEnabled() for m,b in w.nav_buttons.items() if b.isVisible()) and w.more_button.isEnabled()
    assert all(a.isEnabled() for a in w.more_menu.actions())
    w.close()


def test_seccion_inicial_por_perfil_y_resaltado():
    assert {r:initial_section(r) for r in ESPERADAS}=={'OPERATOR':'inventory','MEDICAL':'inventory','COORDINATOR':'shipments'}
    for role in ESPERADAS:
        w=abrir(role); assert w.nav_buttons[initial_section(role)].objectName()=='activeNav'
        assert sum(b.objectName()=='activeNav' for b in w.nav_buttons.values())==1
        w.close()


def test_resaltado_en_menu_mas_y_cambio_de_perfil_reconstruye_barra():
    w=abrir('OPERATOR'); w.mode='reports'; w.update_navigation()
    assert w.more_button.objectName()=='activeNav' and all(b.objectName()!='activeNav' for b in w.nav_buttons.values())
    w.client=Cliente('COORDINATOR'); w.set_controls(True); w.mode='shipments'; w.update_navigation(); app.processEvents()
    assert {m for m,b in w.nav_buttons.items() if b.isVisible()}==set(NAV_PROFILES['COORDINATOR']['bar']) and w.more_modes==['users']
    assert w.more_button.objectName()!='activeNav'
    w.close()


def test_accion_deshabilitada_por_estado_explica_el_paso_que_falta():
    w=abrir('MEDICAL'); w.mode='pending'; w.show_pending([]); w.set_controls(True); w.show_pending([]); app.processEvents()
    assert not w.detail_button.isEnabled() and 'Consultar operación' in w.detail_button.toolTip()
    assert not w.next.isEnabled() and w.next.toolTip()
    w.close()


def test_acciones_solo_por_rol_se_ocultan():
    w=abrir('OPERATOR'); w.mode='requests'; w.show_rows({'items':[],'page':1,'total':0}); app.processEvents()
    assert not any(b.isVisible() for b in (w.request_create_button,w.request_edit_button,w.request_cancel_button,w.evaluate_button))
    w.mode='results'; w.show_rows({'items':[],'page':1,'total':0}); assert not w.review_button.isVisible()
    w.close()


def test_coordinador_conserva_la_lista_de_personal_de_traslado():
    """El servidor permite user_list a COORDINATOR; la vista «Usuarios» no puede quedar sin acceso."""
    w=abrir('COORDINATOR'); assert 'users' in w.more_modes and w.more_button.isVisible()
    w.mode='users'; w.update_navigation(); assert w.more_button.objectName()=='activeNav'
    w.close()


def test_motivos_no_se_quedan_pegados_al_cambiar_de_pantalla():
    w=abrir('MEDICAL'); w.mode='pending'; w.set_controls(True); w.show_pending([])
    assert w.search.toolTip()
    w.mode='inventory'; w.set_controls(True)
    assert w.search.isEnabled() and w.search.toolTip()=='' and (w.detail_button.isEnabled() or 'pendientes' not in w.detail_button.toolTip())
    w.close()


def test_barra_cabe_en_1000_px_en_todos_los_perfiles():
    for role in ESPERADAS:
        w=abrir(role); w.resize(1000,700); app.processEvents()
        assert w.minimumSizeHint().width()<=1000 and w.width()==1000
        w.close()


def test_perfil_fuera_de_lista_no_truena():
    for role in ('ADMIN','DONOR','AUDITOR','TRANSPORT'):
        w=Window(); w.client=Cliente(role); w.stack.setCurrentIndex(1); w.mode=initial_section(role); w.show(); w.set_controls(True); w.update_navigation(); app.processEvents()
        assert not any(b.isVisible() for b in w.nav_buttons.values()) and not w.more_button.isVisible()
        w.close()
