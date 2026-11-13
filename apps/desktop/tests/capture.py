"""Capturas de estados ficticios; no se conecta a servicios ni usa datos reales."""
import os
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from redhouse_desktop.app import Window, STYLE
app=QApplication([]); app.setStyleSheet(STYLE)
w=Window(); w.show(); app.processEvents()
out=Path(os.environ['DESKTOP_CAPTURE_DIR']); out.mkdir(parents=True,exist_ok=True)
w.grab().save(str(out/'login.png'))
from redhouse_desktop.client import ApiError
w.failed(ApiError(401,'mfa_required','Requiere verificación.')); app.processEvents(); w.grab().save(str(out/'login-verificacion.png'))
w.otp.hide(); w.otp_label.hide(); w.login_status.setText('Usa tu cuenta institucional para continuar.')
w.stack.setCurrentIndex(1); w.identity.setText('operador · Operador'); w.heading.setText('Inventario institucional'); w.description.setText('Unidades y disponibilidad autorizadas para tu perfil.')
w.mode='inventory'; w.update_navigation(); w.table.setHorizontalHeaderLabels(['Folio','Producto','Grupo','Estado','Caducidad']); w.receive_button.setEnabled(False); w.show_rows({'items':[{'id':'example','folio':'RH-2026-031','component':'RBC','blood_group':'O+','status':'QUARANTINE','expires_at':'2026-12-09'}], 'page':1,'total':1}); w.table.selectRow(0); app.processEvents(); w.grab().save(str(out/'inventario.png'))
w.resize(800,600); app.processEvents(); w.grab().save(str(out/'inventario-compacto.png'))
w.mode='alerts'; w.update_navigation(); w.table.setColumnCount(4); w.heading.setText('Avisos'); w.description.setText('Bandeja autorizada para tu cuenta y tu institución.'); w.table.setHorizontalHeaderLabels(['Aviso','Estado','Severidad','Fecha']); w.show_rows({'items':[], 'page':1, 'total':0}); app.processEvents(); w.grab().save(str(out/'avisos-vacio.png'))
from types import SimpleNamespace
w.client=SimpleNamespace(user={'username':'operador','role':'OPERATOR'},access=None)
w.mode='results'; w.table.setColumnCount(5); w.update_navigation(); w.heading.setText('Resultados de laboratorio'); w.description.setText('Consulta resultados documentados. La revisión corresponde al personal médico.'); w.search.setPlaceholderText('Buscar resultados'); w.table.setHorizontalHeaderLabels(['Prueba','Resultado','Estado','Laboratorio','Versión']); w.show_rows({'items':[{'id':'ejemplo','test_code':'ABO','value':'O','status':'CAPTURED','laboratory':'Laboratorio ficticio','version':1}], 'page':1, 'total':1}); app.processEvents(); w.grab().save(str(out/'resultados.png'))
w.mode='requests'; w.update_navigation(); w.heading.setText('Solicitudes'); w.description.setText('Solicitudes autorizadas para tu institución.'); w.table.setColumnCount(5); w.table.setHorizontalHeaderLabels(['Producto','Cantidad','Urgencia','Estado','Fecha']); w.search.setPlaceholderText('Buscar en solicitudes'); w.show_rows({'items':[{'id':'ejemplo','kind':'BLOOD','component':'RBC','quantity':2,'urgency':2,'status':'OPEN','created_at':'2030-01-01 10:00'}], 'page':1, 'total':1}); app.processEvents(); w.grab().save(str(out/'solicitudes.png'))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
def capture_dialog():
    dialog=QApplication.activeModalWidget()
    if dialog: dialog.grab().save(str(out/'etiqueta-previa.png')); dialog.reject()
QTimer.singleShot(100,capture_dialog)
w.show_label({'id':'00000000-0000-4000-8000-000000000001','folio':'RH-2026-031','component':'RBC','blood_group':'O+'})
w.mode='pending'; w.update_navigation(); w.heading.setText('Operaciones pendientes'); w.description.setText('Recupera operaciones de esta cuenta sin duplicarlas.'); w.table.setColumnCount(2); w.table.setHorizontalHeaderLabels(['Operación','Estado']); w.show_pending([{'kind':'COMMAND','state':'UNCERTAIN','status':None}]); app.processEvents(); w.grab().save(str(out/'operaciones-pendientes.png'))
