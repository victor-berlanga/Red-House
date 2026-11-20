"""Navegación por perfil de la consola: cada rol ve exactamente sus secciones, sin opciones grises."""
import os
from types import SimpleNamespace
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtGui import QFont
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
    # Ventana ancha: así ninguna sección se desborda a «Más» por la fuente del sistema (en Windows la fuente es más
    # ancha que en macOS/Linux). Las pruebas de desbordamiento angostan la ventana de forma explícita.
    w=Window(); w.resize(2400,800); w.client=Cliente(role); w.stack.setCurrentIndex(1); w.mode=initial_section(role); w.show(); w.set_controls(True); w.update_navigation(); app.processEvents()
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
    assert not w.nav_overflow
    assert [a.text() for a in w.more_menu.actions()]==[SECTION_TITLES[m] for m in w.nav_overflow+NAV_PROFILES[role]['more']]
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


def accesibles(w):
    """Secciones alcanzables: botones visibles de la barra más lo que vive en «Más»."""
    return {m for m,b in w.nav_buttons.items() if b.isVisible()}|set(w.more_modes)


@pytest.mark.parametrize('escala',[1.0,1.5,2.0])
def test_barra_cabe_en_1000_px_aunque_la_fuente_sea_mas_ancha(escala):
    """Simula Windows (fuente/DPI mayores): el mínimo real de la ventana no depende del ancho de los botones."""
    # STYLE fija font-size:14px y pisa a QApplication.setFont, así que la fuente mayor se aplica también por hoja de estilo
    # (como Windows, donde la fuente de sistema y el DPI ensanchan los botones). Se usa también setFont por si cambia STYLE.
    base=app.font(); grande=QFont(base); grande.setPixelSize(round(14*escala)); app.setFont(grande); app.setStyleSheet(STYLE+'QWidget { font-size:%dpx; }'%round(14*escala))
    try:
        for role in ESPERADAS:
            w=abrir(role); w.resize(1000,700); app.processEvents()
            assert w.minimumSizeHint().width()<=1000 and w.width()==1000, (role,escala,w.minimumSizeHint().width())
            assert accesibles(w)==ESPERADAS[role]
            w.close()
    finally: app.setFont(base); app.setStyleSheet(STYLE)


@pytest.mark.parametrize('escala',[1.5,2.0])
def test_ninguna_seccion_rompe_el_limite_de_1000_px_con_fuente_grande(escala):
    """Además de la barra, la descripción y la fila de acciones de cada pantalla no deben fijar el ancho mínimo."""
    px=round(14*escala); base=app.font(); grande=QFont(base); grande.setPixelSize(px); app.setFont(grande); app.setStyleSheet(STYLE+'QWidget { font-size:%dpx; }'%px)
    try:
        for role in ESPERADAS:
            w=abrir(role); w.resize(1000,700); w.run=lambda *a,**k:None; w.journal=SimpleNamespace(list=None)
            for modo in sorted(ESPERADAS[role]):
                w.mode=modo; w.update_navigation(); w.load(); app.processEvents()
                assert w.minimumSizeHint().width()<=1000, (role,escala,modo,w.minimumSizeHint().width())
            w.close()
    finally: app.setFont(base); app.setStyleSheet(STYLE)


def test_ajuste_de_la_barra_no_encadena_redimensionados_ni_duplica_acciones():
    llamadas=[]; original=Window._fit_navigation
    Window._fit_navigation=lambda self:(llamadas.append(1),original(self))[1]
    try:
        w=abrir('OPERATOR'); llamadas.clear(); w.resize(900,700); app.processEvents()
        assert len(llamadas)==1  # un redimensionado = un ajuste, sin cascada
        llamadas.clear(); w.resize(900,800); app.processEvents(); assert not llamadas  # solo cambió el alto
        for i,ancho in enumerate((500,1700,640,1200,800)*6):
            if i%4==0: w.client=Cliente(('OPERATOR','MEDICAL','COORDINATOR')[i%3]); w.update_navigation()
            w.resize(ancho,700); app.processEvents(); perfil=NAV_PROFILES[w.nav_role]
            assert [a.text() for a in w.more_menu.actions()]==[SECTION_TITLES[m] for m in w.nav_overflow+perfil['more']]
            visibles=[m for m in perfil['bar'] if w.nav_buttons[m].isVisible()]
            assert visibles==perfil['bar'][:len(visibles)] and w.nav_overflow==perfil['bar'][len(visibles):]
        w.close()
    finally: Window._fit_navigation=original


def test_desbordamiento_pasa_secciones_a_mas_al_angostar_y_regresan_al_ensanchar():
    w=abrir('OPERATOR'); w.resize(1600,700); app.processEvents()
    ancha={m for m,b in w.nav_buttons.items() if b.isVisible()}; assert not w.nav_overflow and ancha==set(NAV_PROFILES['OPERATOR']['bar'])
    w.resize(760,700); app.processEvents()
    assert w.nav_overflow and accesibles(w)==ESPERADAS['OPERATOR'] and w.more_button.isVisible()
    assert w.nav_overflow==NAV_PROFILES['OPERATOR']['bar'][-len(w.nav_overflow):]
    assert [a.text() for a in w.more_menu.actions()]==[SECTION_TITLES[m] for m in w.nav_overflow+NAV_PROFILES['OPERATOR']['more']]
    assert not set(w.nav_overflow)&{m for m,b in w.nav_buttons.items() if b.isVisible()}
    w.resize(1600,700); app.processEvents()
    assert not w.nav_overflow and {m for m,b in w.nav_buttons.items() if b.isVisible()}==ancha
    w.close()


def test_perfil_sin_mas_propio_muestra_mas_solo_si_se_desborda():
    w=abrir('COORDINATOR'); w.resize(1600,700); app.processEvents()
    assert w.more_modes==['users']
    w.resize(500,700); app.processEvents()
    assert w.nav_overflow and accesibles(w)==ESPERADAS['COORDINATOR']
    w.close()


def test_seccion_activa_sigue_resaltada_al_desbordarse():
    w=abrir('OPERATOR'); w.resize(1600,700); w.mode='alerts'; w.update_navigation(); app.processEvents()
    assert w.nav_buttons['alerts'].objectName()=='activeNav' and w.more_button.objectName()!='activeNav'
    w.resize(700,700); app.processEvents()
    assert 'alerts' in w.nav_overflow and w.more_button.objectName()=='activeNav'
    assert all(b.objectName()!='activeNav' for b in w.nav_buttons.values())
    w.resize(1600,700); app.processEvents()
    assert w.nav_buttons['alerts'].objectName()=='activeNav' and w.more_button.objectName()!='activeNav'
    w.close()


def test_perfil_fuera_de_lista_no_truena():
    for role in ('ADMIN','DONOR','AUDITOR','TRANSPORT'):
        w=Window(); w.client=Cliente(role); w.stack.setCurrentIndex(1); w.mode=initial_section(role); w.show(); w.set_controls(True); w.update_navigation(); app.processEvents()
        assert not any(b.isVisible() for b in w.nav_buttons.values()) and not w.more_button.isVisible()
        w.close()
