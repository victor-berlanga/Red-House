"""Interfaz Qt para el primer incremento operativo de escritorio."""
import os
import math
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Qt, QTimer, QDateTime, QStandardPaths, QTimeZone
from PySide6.QtGui import QImage, QPixmap, QColor, QPainter
import qrcode
from PySide6.QtWidgets import (QApplication, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QStackedWidget, QTableWidget, QComboBox, QDateTimeEdit,
    QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QFileDialog, QCheckBox, QSpinBox)
from .client import ApiError, Client, ContractError
from .journal import Journal, JournalError
from .durable_commands import prepare_command, submit_command, update_shipment_command
from .shipment_planning import planning_dialog
from .resource_edit import resource_edit_dialog
from .fractionation import fractionation_dialog
from .institutional_catalogue import catalogue_dialog
from .donation_selector import select_processed_donation
from .donation_workflows import collect_dialog, processing_dialog
from .reservation import validate_operation
from .label_issuance import prepare_label, submit_label
from .label_output import draw_label, write_pdf
from .download import download, DownloadError
from .native_map import RegionMap
from .tracking import TrackingSocket, latest_position, validate_snapshot_point
from .user_creation import lookup_user, prepare_user, submit_user
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

# La emisión se autoriza en el servicio antes de producir la salida local.
LABEL_ISSUANCE_ENABLED = True
CUSTODY_ACCEPT_ENABLED = True
USER_CREATION_ENABLED = True

LABELS = {'OPERATOR':'Operador', 'MEDICAL':'Personal médico', 'COORDINATOR':'Coordinación', 'ADMIN':'Administración', 'AUDITOR':'Auditoría', 'QUARANTINE':'En cuarentena', 'AVAILABLE':'Disponible', 'BLOOD':'Sangre', 'ORGAN':'Órgano', 'OPEN':'Abierta', 'IN_PROGRESS':'En curso', 'RESERVED':'Reservada', 'PREPARED':'Preparado', 'COLLECTED':'Recolectado', 'IN_TRANSIT':'En tránsito', 'DELIVERED':'Entregado', 'ACCEPTED':'Aceptado', 'CANCELLED':'Cancelado', 'INCIDENT':'Incidencia', 'CAPTURED':'Capturado', 'AUTHORIZED':'Autorizado', 'REQUESTED':'Solicitada', 'RECEIVED':'Recibida', 'REJECTED':'Rechazada', 'ACKNOWLEDGED':'Reconocido', 'CLOSED':'Cerrado', 'RBC':'Eritrocitos', 'PLASMA':'Plasma', 'PLATELETS':'Plaquetas', 'RESOURCE_RESERVED':'Unidad reservada', 'SHIPMENT_CREATED':'Traslado registrado', 'REQUEST_CREATED':'Solicitud registrada', 'APPOINTMENT_BOOKED':'Cita programada', 'INVENTORY':'Inventario', 'EXPIRY':'Caducidad', 'REQUESTS':'Solicitudes', 'SHIPMENTS':'Traslados', 'ACTIVITY':'Actividad', 'PENDING':'Pendiente', 'COMPLETE':'Listo', 'FAILED':'No disponible'}
LABELS.update({'WITHDRAWN':'Retirada','PLANNED':'Planeado','ACTIVE':'Activo','INACTIVE':'Inactivo','KIDNEY':'Riñón','LIVER':'Hígado','HEART':'Corazón'})

def label(value):
    return LABELS.get(str(value), str(value)) if value is not None else '—'

def display_value(key,value):
    if value is not None and key in ('created_at','expires_at','collected_at','captured_at','received_at','departure_at','eta','occurred_at'):
        moment=QDateTime.fromString(str(value),Qt.ISODate)
        if moment.isValid(): return moment.toLocalTime().toString('dd/MM/yyyy HH:mm')+' local'
    return label(value)

STYLE = '''
QWidget { background:#f6f7f9; color:#202c39; font-size:14px; }
QLabel#brand { color:#a32035; font-size:23px; font-weight:700; }
QLabel#title { font-size:24px; font-weight:700; }
QLabel#hint { color:#536474; }
QPushButton { background:#fff; border:1px solid #b8c3cc; border-radius:5px; padding:8px 14px; }
QPushButton:hover { border-color:#a32035; }
QPushButton:focus, QLineEdit:focus, QTableWidget:focus { border:2px solid #245b87; }
QPushButton#activeNav { background:#fbecef; border:1px solid #a32035; color:#8d182c; font-weight:700; }
QPushButton#primary { background:#a32035; border:1px solid #a32035; color:white; font-weight:600; }
QPushButton:disabled { color:#88939a; background:#e6eaed; border-color:#d3dbe1; }
QLineEdit, QTableWidget { background:white; border:1px solid #bcc8d0; border-radius:4px; padding:7px; }
QHeaderView::section { background:#eaf0f3; border:0; padding:8px; font-weight:600; }
'''

class Signals(QObject):
    done = Signal(object)
    failed = Signal(object)

class Work(QRunnable):
    def __init__(self, fn):
        super().__init__(); self.fn = fn; self.signals = Signals()
    def run(self):
        try: self.signals.done.emit(self.fn())
        except Exception as exc: self.signals.failed.emit(exc)

class Window(QMainWindow):
    def __init__(self):
        super().__init__(); self.client = None; self.busy = False; self.rows = []; self.page = 1; self.mode = 'inventory'; self.total = 0; self.uncertain = False; self.reservation_uncertain = False; self.last_operation = None; self.last_operation_status = None; self.journal = None; self.tracking = None; self.closing = False; self.select_transport = False
        self.setWindowTitle('Red House | Consola institucional'); self.resize(1150, 720)
        self.pool = QThreadPool(self); self.pool.setMaxThreadCount(1)
        self.stack = QStackedWidget(); self.setCentralWidget(self.stack)
        self.build_login(); self.build_workspace()

    def build_login(self):
        page = QWidget(); outer = QVBoxLayout(page); outer.addStretch(); row = QHBoxLayout(); row.addStretch()
        box = QWidget(); box.setMaximumWidth(430); layout = QVBoxLayout(box); layout.setSpacing(14)
        brand = QLabel('RED HOUSE'); brand.setObjectName('brand'); layout.addWidget(brand)
        title = QLabel('Acceso institucional'); title.setObjectName('title'); layout.addWidget(title)
        hint = QLabel('Consola para operación de la red regional.'); hint.setObjectName('hint'); layout.addWidget(hint)
        form = QFormLayout(); self.server_url = os.environ.get('REDHOUSE_BASE_URL','https://34.18.186.116')
        self.username = QLineEdit(); form.addRow('Cuenta',self.username)
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password); form.addRow('Contraseña',self.password)
        self.otp = QLineEdit(); self.otp.setMaxLength(6); self.otp.setPlaceholderText('Seis dígitos'); form.addRow('Código de verificación',self.otp); self.otp_label=form.labelForField(self.otp); self.otp.hide(); self.otp_label.hide()
        layout.addLayout(form); self.login_button = QPushButton('Iniciar sesión'); self.login_button.setObjectName('primary'); self.login_button.clicked.connect(self.login); layout.addWidget(self.login_button)
        self.login_status = QLabel('Usa tu cuenta institucional para continuar.'); self.login_status.setWordWrap(True); self.login_status.setObjectName('hint'); layout.addWidget(self.login_status)
        row.addWidget(box); row.addStretch(); outer.addLayout(row); outer.addStretch(); self.stack.addWidget(page)

    def build_workspace(self):
        page = QWidget(); outer = QVBoxLayout(page); outer.setContentsMargins(28,20,28,20); outer.setSpacing(14)
        head = QHBoxLayout(); brand = QLabel('RED HOUSE'); brand.setObjectName('brand'); head.addWidget(brand); head.addStretch(); self.summary_button=QPushButton('Resumen'); self.summary_button.clicked.connect(self.open_summary); head.addWidget(self.summary_button); self.identity = QLabel(); head.addWidget(self.identity)
        self.logout_button = QPushButton('Cerrar sesión'); self.logout_button.clicked.connect(self.logout); head.addWidget(self.logout_button); outer.addLayout(head)
        nav = QHBoxLayout(); self.inventory_button = QPushButton('Inventario'); self.inventory_button.clicked.connect(lambda: self.switch('inventory')); nav.addWidget(self.inventory_button)
        self.samples_button = QPushButton('Muestras'); self.samples_button.clicked.connect(lambda: self.switch('samples')); nav.addWidget(self.samples_button); self.results_button = QPushButton('Resultados'); self.results_button.clicked.connect(lambda: self.switch('results')); nav.addWidget(self.results_button); self.alerts_button = QPushButton('Avisos'); self.alerts_button.clicked.connect(lambda: self.switch('alerts')); nav.addWidget(self.alerts_button); nav.addStretch(); outer.addLayout(nav)
        self.requests_button=QPushButton('Solicitudes',self); self.evaluations_button=QPushButton('Evaluaciones',self); self.reservations_button=QPushButton('Reservas',self)
        for button in (self.requests_button,self.evaluations_button,self.reservations_button): button.hide()
        self.areas=QComboBox(); self.areas.setAccessibleName('Otras áreas de trabajo')
        for title,mode in (('Más áreas',''),('Solicitudes','requests'),('Evaluaciones','evaluations'),('Reservas','reservations'),('Traslados','shipments'),('Auditoría','audit'),('Usuarios','users'),('Operaciones pendientes','pending'),('Reportes','reports'),('Cobertura','coverage'),('Dispositivos','devices'),('Receptores','recipients'),('Sedes','sites'),('Capacidades','capacities'),('Donaciones','donations')): self.areas.addItem(title,mode)
        self.areas.currentIndexChanged.connect(lambda _index: self.switch(self.areas.currentData()) if self.areas.currentData() else None)
        nav.insertWidget(nav.count()-1,self.areas)
        self.heading = QLabel(); self.heading.setObjectName('title'); outer.addWidget(self.heading)
        self.description = QLabel(); self.description.setObjectName('hint'); outer.addWidget(self.description)
        tools = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText('Buscar por folio o identificador'); self.search.returnPressed.connect(self.search_now); tools.addWidget(self.search)
        self.search_button = QPushButton('Buscar'); self.search_button.clicked.connect(self.search_now); tools.addWidget(self.search_button)
        self.reload_button = QPushButton('Actualizar'); self.reload_button.clicked.connect(self.load); tools.addWidget(self.reload_button); outer.addLayout(tools)
        self.table = QTableWidget(); self.table.setColumnCount(5); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setSelectionMode(QTableWidget.SingleSelection); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.verticalHeader().hide(); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.itemDoubleClicked.connect(self.open_selected); outer.addWidget(self.table,1)
        actions = QHBoxLayout(); self.trace_button=QPushButton('Trazabilidad'); self.trace_button.setToolTip('Disponible para personal médico autorizado. Selecciona una unidad para consultarla.'); self.trace_button.setAccessibleDescription('Disponible para personal médico autorizado. Selecciona una unidad para consultarla.'); self.trace_button.clicked.connect(self.open_trace); actions.addWidget(self.trace_button); self.cold_button=QPushButton('Conservación'); self.cold_button.clicked.connect(self.open_cold); actions.addWidget(self.cold_button); self.user_state_button=QPushButton('Cambiar estado'); self.user_state_button.clicked.connect(self.change_user_state); actions.addWidget(self.user_state_button); self.user_role_button=QPushButton('Cambiar perfil'); self.user_role_button.clicked.connect(self.change_user_role); actions.addWidget(self.user_role_button); self.download_button=QPushButton('Descargar reporte'); self.download_button.clicked.connect(self.download_report); actions.addWidget(self.download_button); self.report_button=QPushButton('Solicitar reporte'); self.report_button.clicked.connect(self.create_report); actions.addWidget(self.report_button); self.resume_button=QPushButton('Reanudar reserva'); self.resume_button.clicked.connect(self.resume_operation); actions.addWidget(self.resume_button); self.label_button=QPushButton('Vista previa de etiqueta'); self.label_button.clicked.connect(self.preview_label); actions.addWidget(self.label_button); self.operation_button=QPushButton('Consultar operación'); self.operation_button.clicked.connect(self.check_operation); actions.addWidget(self.operation_button); self.evaluate_button=QPushButton('Generar evaluación'); self.evaluate_button.clicked.connect(self.evaluate_request); actions.addWidget(self.evaluate_button); self.create_button = QPushButton('Registrar unidad'); self.create_button.clicked.connect(self.create_resource); actions.addWidget(self.create_button); self.detail_button = QPushButton('Ver detalle'); self.detail_button.clicked.connect(self.open_selected); actions.addWidget(self.detail_button)
        self.request_create_button=QPushButton('Registrar solicitud'); self.request_create_button.setToolTip('El registro corresponde a personal médico autorizado.'); self.request_create_button.setAccessibleDescription('El registro corresponde a personal médico autorizado.'); self.request_create_button.clicked.connect(self.open_request_form); actions.addWidget(self.request_create_button)
        self.device_create_button=QPushButton('Registrar dispositivo'); self.device_create_button.clicked.connect(self.begin_device_create); actions.addWidget(self.device_create_button)
        self.device_revoke_button=QPushButton('Revocar dispositivo'); self.device_revoke_button.clicked.connect(self.revoke_device); actions.addWidget(self.device_revoke_button)
        self.user_create_button=QPushButton('Registrar cuenta'); self.user_create_button.clicked.connect(self.create_user); actions.addWidget(self.user_create_button)
        self.recipient_create_button=QPushButton('Registrar receptor'); self.recipient_create_button.clicked.connect(self.create_recipient); actions.addWidget(self.recipient_create_button)
        self.recipient_edit_button=QPushButton('Corregir receptor'); self.recipient_edit_button.clicked.connect(self.edit_recipient); actions.addWidget(self.recipient_edit_button)
        self.request_edit_button=QPushButton('Editar solicitud'); self.request_edit_button.clicked.connect(self.edit_request); actions.addWidget(self.request_edit_button)
        self.request_cancel_button=QPushButton('Cancelar solicitud'); self.request_cancel_button.clicked.connect(self.cancel_request); actions.addWidget(self.request_cancel_button)
        self.collect_button=QPushButton('Registrar colecta'); self.collect_button.clicked.connect(self.create_donation); actions.addWidget(self.collect_button)
        self.process_donation_button=QPushButton('Documentar procesamiento'); self.process_donation_button.clicked.connect(self.process_donation); actions.addWidget(self.process_donation_button)
        self.catalogue_create_button=QPushButton('Registrar'); self.catalogue_create_button.clicked.connect(lambda:self.catalogue_action(False)); actions.addWidget(self.catalogue_create_button)
        self.catalogue_edit_button=QPushButton('Corregir'); self.catalogue_edit_button.clicked.connect(lambda:self.catalogue_action(True)); actions.addWidget(self.catalogue_edit_button)
        self.fractionate_button=QPushButton('Registrar derivados'); self.fractionate_button.clicked.connect(self.fractionate_resource); actions.addWidget(self.fractionate_button)
        self.resource_edit_button=QPushButton('Corregir unidad'); self.resource_edit_button.clicked.connect(self.edit_resource); actions.addWidget(self.resource_edit_button)
        self.shipment_create_button=QPushButton('Planificar traslado'); self.shipment_create_button.clicked.connect(self.plan_shipment); actions.addWidget(self.shipment_create_button)
        self.sample_create_button=QPushButton('Registrar muestra'); self.sample_create_button.clicked.connect(self.create_sample); actions.addWidget(self.sample_create_button)
        self.receive_button = QPushButton('Registrar recepción'); self.receive_button.setObjectName('primary'); self.receive_button.clicked.connect(self.receive); actions.addWidget(self.receive_button); self.capture_button = QPushButton('Capturar resultado'); self.capture_button.clicked.connect(self.capture_result); actions.addWidget(self.capture_button); self.review_button = QPushButton('Revisar resultado'); self.review_button.setToolTip('La revisión corresponde al personal médico autorizado.'); self.review_button.clicked.connect(self.review_result); actions.addWidget(self.review_button); self.ack_button = QPushButton('Acusar recibo'); self.ack_button.clicked.connect(self.acknowledge); actions.addWidget(self.ack_button); actions.addStretch(); outer.addLayout(actions)
        actions = QHBoxLayout(); actions.addStretch()
        self.prev = QPushButton('Anterior'); self.prev.clicked.connect(lambda:self.turn(-1)); actions.addWidget(self.prev); self.page_label = QLabel(); actions.addWidget(self.page_label); self.next = QPushButton('Siguiente'); self.next.clicked.connect(lambda:self.turn(1)); actions.addWidget(self.next); outer.addLayout(actions)
        self.status = QLabel(''); self.status.setWordWrap(True); self.status.setObjectName('hint'); outer.addWidget(self.status)
        for button in (self.trace_button,self.cold_button,self.user_state_button,self.user_role_button,self.download_button,self.report_button,self.resume_button,self.label_button,self.operation_button,self.evaluate_button,self.create_button,self.request_create_button,self.recipient_create_button,self.recipient_edit_button,self.request_edit_button,self.request_cancel_button,self.sample_create_button,self.receive_button,self.capture_button,self.review_button,self.ack_button): button.hide()
        self.collect_button.hide(); self.process_donation_button.hide()
        self.catalogue_create_button.hide(); self.catalogue_edit_button.hide()
        self.fractionate_button.hide()
        self.resource_edit_button.hide()
        self.shipment_create_button.hide()
        self.device_create_button.hide(); self.device_revoke_button.hide()
        self.user_create_button.hide()
        self.stack.addWidget(page)

    def run(self, fn, success, label, failure=None):
        if self.busy: return
        self.busy = True; self.set_controls(False); self.status.setText(label); self.login_status.setText(label)
        worker = Work(fn); self._worker=worker; worker.signals.done.connect(lambda result: self.finished(success,result)); worker.signals.failed.connect(failure or self.failed); self.pool.start(worker)

    def set_controls(self, enabled):
        self.areas.setEnabled(enabled)
        is_admin=bool(enabled and self.client and self.client.user and self.client.user.get('role')=='ADMIN')
        self.device_create_button.setEnabled(is_admin and self.mode in ('users','devices'))
        self.device_revoke_button.setEnabled(is_admin and self.mode=='devices')
        self.user_create_button.setEnabled(is_admin and self.mode=='users' and USER_CREATION_ENABLED)
        self.collect_button.setEnabled(bool(enabled and self.mode=='donations' and self.client and self.client.user and self.client.user.get('role')=='MEDICAL'))
        self.process_donation_button.setEnabled(bool(enabled and self.mode=='donations' and self.client and self.client.user and self.client.user.get('role')=='OPERATOR'))
        self.catalogue_create_button.setEnabled(is_admin and self.mode in ('sites','capacities'))
        self.catalogue_edit_button.setEnabled(is_admin and self.mode in ('sites','capacities'))
        self.fractionate_button.setEnabled(bool(enabled and self.mode=='inventory' and self.client and self.client.user and self.client.user.get('role')=='OPERATOR'))
        self.resource_edit_button.setEnabled(bool(enabled and self.mode=='inventory' and self.client and self.client.user and self.client.user.get('role')=='OPERATOR'))
        self.shipment_create_button.setEnabled(bool(enabled and self.mode=='shipments' and self.client and self.client.user and self.client.user.get('role')=='COORDINATOR'))
        self.request_create_button.setEnabled(enabled and self.mode=='requests' and bool(self.client and self.client.user and self.client.user.get('role')=='MEDICAL'))
        for widget in (self.username,self.password,self.otp,self.search,self.table,self.login_button,self.logout_button,self.summary_button,self.inventory_button,self.samples_button,self.results_button,self.alerts_button,self.requests_button,self.evaluations_button,self.reservations_button,self.search_button,self.reload_button,self.trace_button,self.cold_button,self.user_state_button,self.user_role_button,self.download_button,self.report_button,self.resume_button,self.label_button,self.operation_button,self.evaluate_button,self.create_button,self.detail_button,self.recipient_create_button,self.recipient_edit_button,self.request_edit_button,self.request_cancel_button,self.sample_create_button,self.receive_button,self.capture_button,self.review_button,self.ack_button,self.prev,self.next): widget.setEnabled(enabled)
        if enabled and self.mode=='donations':
            self.search.setEnabled(False); self.search_button.setEnabled(False)
        if enabled and self.mode != 'samples': self.receive_button.setEnabled(False)
        if enabled and self.mode != 'alerts': self.ack_button.setEnabled(False)
        if enabled:
            self.prev.setEnabled(self.page>1); self.next.setEnabled(self.page*20<self.total)
        if enabled and self.client and self.client.user:
            role = self.client.user.get('role'); self.requests_button.setEnabled(role in ('OPERATOR','MEDICAL')); self.evaluations_button.setEnabled(role == 'MEDICAL'); self.reservations_button.setEnabled(role in ('OPERATOR','MEDICAL','COORDINATOR'));
            for button in (self.inventory_button,self.samples_button,self.results_button): button.setVisible(role!='ADMIN')
            self.summary_button.setEnabled(role in ('OPERATOR','MEDICAL','COORDINATOR','TRANSPORT'))
            for index,button in ((1,self.requests_button),(2,self.evaluations_button),(3,self.reservations_button)): self.areas.model().item(index).setEnabled(button.isEnabled())
            self.areas.model().item(4).setEnabled(role in ('OPERATOR','MEDICAL','COORDINATOR','TRANSPORT'))
            self.areas.model().item(5).setEnabled(role == 'AUDITOR'); self.areas.model().item(6).setEnabled(role in ('ADMIN','COORDINATOR')); self.areas.model().item(8).setEnabled(role in ('OPERATOR','MEDICAL','COORDINATOR','TRANSPORT','AUDITOR')); self.areas.model().item(9).setEnabled(role in ('MEDICAL','COORDINATOR'))
            self.areas.model().item(10).setEnabled(role=='ADMIN'); self.areas.model().item(11).setEnabled(role in ('OPERATOR','MEDICAL'))
            self.areas.model().item(12).setEnabled(role=='ADMIN'); self.areas.model().item(13).setEnabled(role=='ADMIN'); self.areas.model().item(14).setEnabled(role in ('OPERATOR','MEDICAL'))
            for button in (self.recipient_create_button,self.recipient_edit_button,self.request_edit_button,self.request_cancel_button): button.setEnabled(role=='MEDICAL')
            self.inventory_button.setEnabled(role in ('OPERATOR','MEDICAL','COORDINATOR'))
            self.trace_button.setEnabled(role=='MEDICAL' and self.mode=='inventory'); self.cold_button.setEnabled(role in ('OPERATOR','MEDICAL') and self.mode=='inventory'); self.user_state_button.setEnabled(role=='ADMIN' and self.mode=='users'); self.user_role_button.setEnabled(role=='ADMIN' and self.mode=='users'); self.operation_button.setEnabled(self.mode == 'pending' or (role == 'MEDICAL' and self.mode == 'reservations')); self.resume_button.setEnabled(role == 'MEDICAL' and self.last_operation_status in ('PENDING','ROLLBACK_PENDING')); self.evaluate_button.setEnabled(role == 'MEDICAL' and self.mode == 'requests'); self.create_button.setEnabled(role == 'OPERATOR' and self.mode == 'inventory'); self.review_button.setEnabled(role == 'MEDICAL' and self.mode == 'results'); self.samples_button.setEnabled(role in ('OPERATOR','MEDICAL')); self.results_button.setEnabled(role in ('OPERATOR','MEDICAL')); self.receive_button.setEnabled(role in ('OPERATOR','MEDICAL') and self.mode == 'samples')
            self.capture_button.setEnabled(role in ('OPERATOR','MEDICAL') and self.mode=='samples'); self.sample_create_button.setEnabled(role in ('OPERATOR','MEDICAL') and self.mode=='samples')

    def finished(self, callback, result):
        self.busy = False; self._worker=None; self.set_controls(True); callback(result)

    def failed(self, exc):
        self.busy = False; self._worker=None; self.set_controls(True)
        if self.stack.currentIndex()==1 and self.client and not self.client.user:
            self.rows=[]; self.table.setRowCount(0); self.client=None; self.journal=None; self.stack.setCurrentIndex(0)
            self.login_status.setText('La sesión terminó. Inicia sesión para continuar.'); return
        if isinstance(exc, ApiError) and exc.code == 'mfa_required' and self.stack.currentIndex()==0:
            self.otp_label.show(); self.otp.show(); self.otp.setFocus(); text='Introduce el código de verificación de tu cuenta.'
        elif isinstance(exc, ApiError) and exc.status in (409,412): text = 'La información cambió. Actualiza la lista y revisa antes de volver a intentar.'
        elif isinstance(exc, (JournalError,DownloadError)): text = str(exc)
        elif isinstance(exc, ConnectionError):
            self.uncertain = True
            text = 'Sin conexión o resultado incierto. Actualiza y consulta el estado antes de repetir una operación.'
        else: text = str(exc) if isinstance(exc, ApiError) else 'No se pudo completar la operación. Comprueba tu conexión o contacta a soporte institucional.'
        if self.stack.currentIndex()==0 and not (isinstance(exc,ApiError) and exc.code=='mfa_required'): self.password.clear()
        self.status.setText(text); self.login_status.setText(text)

    def login(self):
        try: client = Client(self.server_url.strip())
        except ValueError: self.login_status.setText('El acceso no está disponible. Contacta a soporte institucional.'); return
        username,password,otp = self.username.text().strip(),self.password.text(),self.otp.text().strip()
        self.client = client
        self.run(lambda:client.login(username,password,otp),self.logged_in,'Validando acceso…')

    def logged_in(self,user):
        self.password.clear(); self.otp.clear(); self.otp.hide(); self.otp_label.hide()
        self.last_operation=None; self.last_operation_status=None; self.reservation_uncertain=False
        self.journal=Journal(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)+'/journal',self.client.base,user['id'],user['tenant_id'])
        self.identity.setText(user.get('username','') + ' · ' + label(user.get('role',''))); self.stack.setCurrentIndex(1); self.switch({'ADMIN':'users','AUDITOR':'audit','TRANSPORT':'shipments'}.get(user.get('role'),'inventory'))

    def logout(self):
        if self.tracking: self.tracking.stop(); self.tracking=None
        client = self.client
        def complete(_): self.stack.setCurrentIndex(0); self.client = None; self.login_status.setText('Sesión local eliminada.')
        def logout_safe():
            try: client.logout(); return True
            except Exception: return False
        def done(revoked):
            complete(None)
            if not revoked: self.login_status.setText('Sesión local eliminada; no se confirmó la revocación en servidor.')
        self.run(logout_safe,done,'Cerrando sesión…')

    def switch(self,mode):
        self.mode=mode; self.page=1; self.search.clear(); self.update_navigation(); self.load()

    def update_navigation(self):
        self.areas.blockSignals(True); self.areas.setCurrentIndex(max(0,self.areas.findData(self.mode))); self.areas.blockSignals(False)
        for button,mode in ((self.inventory_button,'inventory'),(self.samples_button,'samples'),(self.results_button,'results'),(self.alerts_button,'alerts'),(self.requests_button,'requests'),(self.evaluations_button,'evaluations'),(self.reservations_button,'reservations')):
            button.setObjectName('activeNav' if self.mode == mode else '')
            button.style().unpolish(button); button.style().polish(button)

    def search_now(self): self.page=1; self.load()
    def turn(self,delta): self.page=max(1,self.page+delta); self.load()
    def load(self):
        if not self.client or self.busy: return
        self.rows=[]; self.table.setRowCount(0); self.page_label.setText('')
        self.collect_button.hide(); self.process_donation_button.hide()
        self.catalogue_create_button.hide(); self.catalogue_edit_button.hide()
        self.fractionate_button.hide()
        self.resource_edit_button.hide()
        self.shipment_create_button.hide()
        self.device_create_button.hide(); self.device_revoke_button.hide()
        self.user_create_button.hide()
        for button in (self.trace_button,self.cold_button,self.user_state_button,self.user_role_button,self.download_button,self.report_button,self.resume_button,self.label_button,self.operation_button,self.evaluate_button,self.create_button,self.request_create_button,self.recipient_create_button,self.recipient_edit_button,self.request_edit_button,self.request_cancel_button,self.sample_create_button,self.receive_button,self.capture_button,self.review_button,self.ack_button): button.hide()
        self.table.setColumnCount(2 if self.mode in ('reservations','pending') else (3 if self.mode == 'shipments' else (4 if self.mode in ('audit','users','alerts','reports','coverage','devices','recipients','sites','capacities','donations') else 5)))
        self.table.setColumnHidden(1,self.mode=='recipients' and (self.client.user or {}).get('role')!='MEDICAL')
        if self.mode == 'pending':
            self.heading.setText('Operaciones pendientes'); self.description.setText('Recupera operaciones de esta cuenta sin duplicarlas.'); self.table.setHorizontalHeaderLabels(['Operación','Estado'])
            self.run(self.journal.list,self.show_pending,'Consultando operaciones…'); return
        if self.mode in ('requests','evaluations','reservations','shipments','audit','users','reports','coverage','devices','recipients','sites','capacities','donations'):
            specs={'donations':('Donaciones','Colectas autorizadas de tu institución.','donantes','/api/v1/donations','donations_list',['Tipo','Producto','Estado','Colecta']),
                   'sites':('Sedes','Sedes de tu institución.','identidad-acceso','/api/v1/catalogues/sites','sites_list_rows',['Nombre','Municipio','Estado','Versión']),
                   'capacities':('Capacidades','Capacidades registradas para las sedes.','identidad-acceso','/api/v1/catalogues/capacities','capacities_list_rows',['Nombre','Producto','Cantidad','Estado']),
                   'recipients':('Receptores','Expedientes autorizados de tu institución.','receptores','/api/v1/recipients','recipients',['Folio','Nombre','Tipo','Estado']),
                   'requests':('Solicitudes','Solicitudes autorizadas para tu institución.','receptores','/api/v1/requests','requests_list',['Producto','Cantidad','Urgencia','Estado','Fecha']),
                   'evaluations':('Evaluaciones','Preselección para revisión profesional; no constituye una decisión clínica.','compatibilidad','/api/v1/evaluations','evaluation_list',['Recurso','Versión de solicitud','Algoritmo','Candidatos','Fecha']),
                   'reservations':('Reservas','Reservas dentro de tu ámbito autorizado.','inventario','/api/v1/reservations','reservation_list',['Estado','Creada']),
                   'shipments':('Traslados','Seguimiento de traslados dentro de tu ámbito autorizado.','transporte','/api/v1/shipments','shipment_list',['Estado','Salida prevista','Llegada prevista']),
                   'audit':('Auditoría','Eventos disponibles en tu ámbito autorizado.','auditoria','/api/v1/events','audit_list',['Fecha','Acción','Responsable','Resultado']),
                   'users':('Usuarios','Cuentas disponibles en tu ámbito autorizado.','identidad-acceso','/api/v1/users','user_list',['Cuenta','Perfil','Estado','Versión']),
                   'devices':('Dispositivos','Dispositivos de traslado registrados en tu institución.','identidad-acceso','/api/v1/devices','device_list',['Dispositivo','Fuente','Estado','Vigencia']),
                   'reports':('Reportes','Solicitudes de reporte de esta cuenta.','documentos','/api/v1/export-jobs','export_list',['Reporte','Formato','Estado','Fecha']),
                   'coverage':('Cobertura','Propuestas de apoyo logístico; requieren autorización humana y nueva verificación.','priorizacion-geografia','/api/v1/allocation-proposals','proposal_list',['Necesidades','Propuestas','Versión','Fecha'])}
            title,description,service,path,operation,headers=specs[self.mode]
            if self.mode=='requests' and self.client.user.get('role')!='MEDICAL': description += ' El registro y la evaluación corresponden al personal médico.'
            self.heading.setText(title); self.description.setText(description); self.table.setHorizontalHeaderLabels(headers)
            params={'page':self.page,'page_size':20}; q=self.search.text().strip()
            if q and self.mode!='donations': params['q']=q
            self.search.setPlaceholderText(('Busca donante al registrar colecta' if self.client.user.get('role')=='MEDICAL' else 'Consulta colectas desde Documentar procesamiento') if self.mode=='donations' else 'Buscar por nombre de dispositivo' if self.mode=='devices' else 'Buscar en '+title.lower())
            self.run(lambda:self.client.authorized(service,path,operation,params=params),self.show_rows,'Consultando '+title.lower()+'…'); return
        self.search.setPlaceholderText('Buscar en avisos' if self.mode == 'alerts' else 'Buscar resultados' if self.mode == 'results' else 'Buscar por folio o identificador')
        if self.mode == 'results':
            self.heading.setText('Resultados de laboratorio'); self.description.setText('Consulta y revisión profesional de resultados documentados.' if self.client.user.get('role') == 'MEDICAL' else 'Consulta resultados documentados. La revisión corresponde al personal médico.')
            self.table.setHorizontalHeaderLabels(['Prueba','Resultado','Estado','Laboratorio','Versión'])
            params={'page':self.page,'page_size':20}; q=self.search.text().strip()
            if q: params['q']=q
            self.run(lambda:self.client.authorized('compatibilidad','/api/v1/laboratory/results','lab_results_list',params=params),self.show_rows,'Consultando resultados…'); return
        if self.mode == 'alerts':
            self.heading.setText('Avisos'); self.description.setText('Bandeja autorizada para tu cuenta y tu institución.')
            self.table.setHorizontalHeaderLabels(['Aviso','Estado','Severidad','Fecha'])
            params={'page':self.page,'page_size':20}; q=self.search.text().strip()
            if q: params['q']=q
            self.run(lambda:self.client.authorized('alertas','/api/v1/alerts','alerts_list',params=params),self.show_rows,'Consultando avisos…'); return
        samples = self.mode == 'samples'; self.heading.setText('Muestras de laboratorio' if samples else 'Inventario institucional')
        self.description.setText('Consulta y recepción documentada de muestras.' if samples else 'Unidades y disponibilidad autorizadas para tu perfil.')
        self.table.setHorizontalHeaderLabels(['Identificador','Estado','Colecta','Recepción','Versión'] if samples else ['Folio','Producto','Grupo','Estado','Caducidad'])
        params={'page':self.page,'page_size':20}; q=self.search.text().strip()
        if q: params['q']=q
        service,path,op = ('compatibilidad','/api/v1/laboratory/samples','lab_samples_list') if samples else ('inventario','/api/v1/resources','resources_list')
        self.run(lambda:self.client.authorized(service,path,op,params=params),self.show_rows,'Consultando datos…')

    def show_pending(self,records):
        pending=[r for r in records if r['state']!='DONE']; self.rows=pending; self.total=len(pending); self.page=1; self.table.setRowCount(len(pending))
        for index,record in enumerate(pending):
            kind=record.get('kind','RESERVATION'); name={'COMMAND':'Operación registrada','RESERVATION':'Reserva','LABEL':'Etiqueta','USER_CREATE':'Alta de cuenta'}.get(kind,'Operación')
            if kind=='COMMAND' and record.get('target',{}).get('operation')=='request_create': name='Solicitud'
            if kind=='COMMAND' and record.get('target',{}).get('operation')=='shipment_create': name='Planificación de traslado'
            self.table.setItem(index,0,QTableWidgetItem(name)); self.table.setItem(index,1,QTableWidgetItem('Requiere revisión' if record.get('status')=='CONFLICT' else 'Por confirmar' if record['state'] in ('PREPARED','UNCERTAIN') else 'Pendiente'))
        self.operation_button.show(); self.resume_button.setVisible(self.last_operation_status in ('PENDING','ROLLBACK_PENDING')); self.detail_button.setEnabled(False); self.search.setEnabled(False); self.search_button.setEnabled(False); self.prev.setEnabled(False); self.next.setEnabled(False); self.page_label.setText(''); self.status.setText('Selecciona Consultar operación para recuperar.' if pending else 'No hay operaciones pendientes.')

    def show_rows(self,data):
        self.collect_button.setVisible(self.mode=='donations' and bool(self.client and self.client.user and self.client.user.get('role')=='MEDICAL'))
        self.process_donation_button.setVisible(self.mode=='donations' and bool(self.client and self.client.user and self.client.user.get('role')=='OPERATOR'))
        self.catalogue_create_button.setVisible(self.mode in ('sites','capacities') and bool(self.client and self.client.user and self.client.user.get('role')=='ADMIN'))
        self.catalogue_edit_button.setVisible(self.mode in ('sites','capacities') and bool(self.client and self.client.user and self.client.user.get('role')=='ADMIN'))
        self.fractionate_button.setVisible(self.mode=='inventory' and bool(self.client and self.client.user and self.client.user.get('role')=='OPERATOR'))
        self.resource_edit_button.setVisible(self.mode=='inventory' and bool(self.client and self.client.user and self.client.user.get('role')=='OPERATOR'))
        self.shipment_create_button.setVisible(self.mode=='shipments' and bool(self.client and self.client.user and self.client.user.get('role')=='COORDINATOR'))
        self.device_create_button.setVisible(self.mode in ('users','devices')); self.device_revoke_button.setVisible(self.mode=='devices')
        self.user_create_button.setVisible(self.mode=='users' and USER_CREATION_ENABLED)
        self.request_create_button.setVisible(self.mode=='requests'); self.request_edit_button.setVisible(self.mode=='requests'); self.request_cancel_button.setVisible(self.mode=='requests'); self.recipient_create_button.setVisible(self.mode=='recipients'); self.recipient_edit_button.setVisible(self.mode=='recipients')
        self.trace_button.setVisible(self.mode == 'inventory'); self.cold_button.setVisible(self.mode == 'inventory'); self.user_state_button.setVisible(self.mode == 'users'); self.user_role_button.setVisible(self.mode == 'users'); self.download_button.setVisible(self.mode == 'reports'); self.report_button.setVisible(self.mode == 'reports'); self.resume_button.setVisible(self.mode == 'reservations' and self.last_operation_status in ('PENDING','ROLLBACK_PENDING')); self.label_button.setVisible(self.mode == 'inventory'); self.operation_button.setVisible(self.mode in ('reservations','pending')); self.evaluate_button.setVisible(self.mode == 'requests'); self.create_button.setVisible(self.mode == 'inventory'); self.sample_create_button.setVisible(self.mode == 'samples'); self.receive_button.setVisible(self.mode == 'samples'); self.capture_button.setVisible(self.mode == 'samples'); self.review_button.setVisible(self.mode == 'results'); self.ack_button.setVisible(self.mode == 'alerts')
        self.uncertain=False; self.rows=data['items']; self.total=data['total']; self.page=data['page']; self.table.setRowCount(len(self.rows))
        if self.mode in ('requests','evaluations','reservations','shipments','audit','users','reports','coverage','devices','recipients','sites','capacities','donations'):
            keys={'donations':('kind','component','status','collected_at'),'sites':('name','municipality','user_state','version'),'capacities':('name','component','quantity','user_state'),'recipients':('folio','display_name','kind','status'),'requests':('component','quantity','urgency','status','created_at'),'evaluations':('kind','request_version','algorithm_version','candidate_count','created_at'),'reservations':('status','created_at'),'shipments':('status','departure_at','eta'),'audit':('created_at','action_label','actor_display','result_label'),'users':('username','role','user_state','version'),'devices':('label','source','user_state','expires_at'),'reports':('report','format','status','created_at'),'coverage':('slot_count','matched_count','algorithm_version','created_at')}[self.mode]
            for row,item in enumerate(self.rows):
                for column,key in enumerate(keys):
                    v=len(item.get('candidates') or []) if key=='candidate_count' else ('Activa' if item.get('active') else 'Inactiva') if key=='user_state' else item.get(key)
                    if self.mode=='donations' and key=='status': v={'COLLECTED':'Pendiente de procesamiento','PROCESSED':'Procesada','REJECTED':'Rechazada'}.get(v,'Estado no disponible')
                    if self.mode=='devices' and key=='source': v={'ANDROID':'Teléfono Android','IOS':'Teléfono iOS','GPS_BRIDGE':'Equipo GPS','SIMULATOR':'Simulador'}.get(v,'Otra fuente')
                    if self.mode=='devices' and key=='user_state': v='Activo' if item.get('active') else 'Revocado'
                    self.table.setItem(row,column,QTableWidgetItem(display_value(key,v)))
            self.page_label.setText(f'Página {self.page} · {self.total} '+('registro' if self.total==1 else 'registros')); self.status.setText('Selecciona una cuenta de traslado activa y pulsa Registrar dispositivo.' if self.mode=='users' and self.select_transport else 'Sin resultados.' if not self.rows else 'Selecciona una fila para consultar su detalle.'); self.select_transport=False; self.set_controls(True); return
        keys = ('test_code','value','status','laboratory','version') if self.mode=='results' else (('message_code','status','severity','created_at') if self.mode=='alerts' else (('identifier','status','collected_at','received_at','version') if self.mode=='samples' else ('folio','component','blood_group','status','expires_at')))
        for row,item in enumerate(self.rows):
            for column,key in enumerate(keys): self.table.setItem(row,column,QTableWidgetItem(display_value(key,item.get(key))))
        self.page_label.setText(f'Página {self.page} · {self.total} '+('registro' if self.total==1 else 'registros'))
        message='Sin resultados.' if not self.rows else 'Selecciona una fila para consultar su detalle.'
        if self.mode=='inventory' and self.client and self.client.user and self.client.user.get('role')!='MEDICAL': message+=' La trazabilidad está disponible para personal médico autorizado.'
        self.status.setText(message); self.set_controls(True)

    def selected(self):
        index=self.table.currentRow()
        return self.rows[index] if 0 <= index < len(self.rows) else None

    def open_summary(self):
        role=self.client.user.get('role')
        services=['transporte'] if role=='TRANSPORT' else ['inventario','receptores','transporte']
        def fetch():
            result={}
            for service in services:
                try: result[service]=self.client.authorized(service,'/api/v1/summary','portal_summary')
                except ApiError as error:
                    if error.status==401: raise
                    result[service]=None
                except (ConnectionError,ContractError): result[service]=None
            return result
        self.run(fetch,self.summary_dialog,'Consultando resumen…')

    def summary_dialog(self,data):
        role=self.client.user.get('role'); regional=role=='COORDINATOR'
        dialog=QDialog(self); dialog.setWindowTitle('Resumen operativo'); dialog.resize(620,420); layout=QVBoxLayout(dialog)
        text='Cifras autorizadas al momento de la consulta.'
        if 'receptores' in data: text+=' Las solicitudes corresponden a tu institución.'
        note=QLabel(text); note.setWordWrap(True); layout.addWidget(note)
        for service,title,scope in (('inventario','Inventario','Región' if regional else 'Institución'),('receptores','Solicitudes','Institución'),('transporte','Traslados','Región' if regional else 'Tareas asignadas' if role=='TRANSPORT' else 'Institución')):
            if service not in data: continue
            heading=QLabel(title+' · '+scope); heading.setObjectName('title'); layout.addWidget(heading)
            row=data[service]
            if row is None: layout.addWidget(QLabel('Información no disponible.')); continue
            layout.addWidget(QLabel('Total: '+str(row['total'])))
            if service=='inventario': layout.addWidget(QLabel('Disponibles por vencer en 48 horas: '+str(row['expiring'])))
            counts=', '.join(label(entry['status'])+': '+str(entry['value']) for entry in row['statuses'])
            detail=QLabel(counts or 'Sin registros.'); detail.setWordWrap(True); layout.addWidget(detail)
        layout.addStretch(); close=QPushButton('Cerrar'); close.clicked.connect(dialog.accept); layout.addWidget(close); dialog.exec()

    def open_selected(self,*_):
        item=self.selected()
        if not item: self.status.setText('Selecciona una fila.'); return
        if self.mode=='pending': return
        if self.mode=='donations':
            self.run(lambda:self.client.authorized('donantes','/api/v1/donations/'+item['id'],'donation_detail'),self.detail,'Consultando donación…'); return
        if self.mode in ('sites','capacities'):
            dialog=QDialog(self); dialog.setWindowTitle('Detalle institucional'); form=QFormLayout(dialog)
            for title,key in (('Nombre','name'),('Municipio','municipality'),('Dirección','address'),('Producto','component'),('Cantidad','quantity')):
                if item.get(key) is not None: form.addRow(title,QLabel(str(item[key])))
            form.addRow('Estado',QLabel('Activo' if item.get('active') else 'Inactivo'))
            close=QPushButton('Cerrar'); close.clicked.connect(dialog.accept); form.addRow(close); dialog.exec(); return
        if self.mode=='coverage':
            self.run(lambda:self.client.authorized('priorizacion-geografia','/api/v1/allocation-proposals/'+item['id'],'proposal_detail'),self.coverage_detail,'Abriendo propuesta…'); return
        if self.mode=='reports':
            self.run(lambda:self.client.authorized('documentos','/api/v1/export-jobs/'+item['id'],'export_detail'),self.detail,'Abriendo reporte…'); return
        if self.mode=='audit':
            self.run(lambda:self.client.authorized('auditoria','/api/v1/events/'+item['id'],'audit_detail'),self.detail,'Abriendo evento…'); return
        if self.mode in ('users','recipients'): self.detail(item); return
        if self.mode=='devices':
            dialog=QDialog(self); dialog.setWindowTitle('Dispositivo de traslado'); form=QFormLayout(dialog)
            source={'ANDROID':'Teléfono Android','IOS':'Teléfono iOS','GPS_BRIDGE':'Equipo GPS','SIMULATOR':'Simulador'}.get(item.get('source'),'Otra fuente')
            for title,value in (('Dispositivo',item.get('label')),('Fuente',source),('Estado','Activo' if item.get('active') else 'Revocado'),('Vigencia',display_value('expires_at',item.get('expires_at')))):
                form.addRow(title,QLabel(str(value or 'No disponible')))
            close=QPushButton('Cerrar'); close.clicked.connect(dialog.accept); form.addRow(close); dialog.exec(); return
        if self.mode=='shipments':
            self.run(lambda:self.client.authorized('transporte','/api/v1/shipments/'+item['id'],'shipment_detail'),self.shipment_detail,'Abriendo traslado…'); return
        if self.mode=='evaluations':
            self.run(lambda:self.client.authorized('compatibilidad','/api/v1/evaluations/'+item['id'],'evaluation_detail'),self.evaluation_detail,'Consultando candidatos…'); return
        if self.mode=='requests':
            def request_detail():
                result=self.client.authorized('receptores','/api/v1/requests/'+item['id'],'request_detail')
                if self.client.user.get('role')=='MEDICAL':
                    person=self.client.authorized('receptores','/api/v1/recipients/'+result['recipient_id'],'recipient_detail')
                    result['recipient_folio']=person.get('folio'); result['recipient_name']=person.get('display_name')
                return result
            self.run(request_detail,self.detail,'Abriendo solicitud…'); return
        if self.mode=='reservations':
            self.run(lambda:self.client.authorized('inventario','/api/v1/reservations/'+item['id'],'reservation_detail'),self.detail,'Abriendo reserva…'); return
        if self.mode in ('samples','results','alerts'): self.detail(item); return
        self.run(lambda:self.client.authorized('inventario','/api/v1/resources/'+item['id'],'resource_detail'),self.detail,'Abriendo detalle…')

    def detail(self,item):
        fields = [('Reporte',item.get('report')),('Formato',item.get('format')),('Receptor',item.get('recipient_name') or item.get('display_name')),('Folio de receptor',item.get('recipient_folio')),('Cuenta',item.get('username')),('Perfil',item.get('role')),('Acción',item.get('action_label')),('Responsable',item.get('actor_display')),('Resultado',item.get('result_label')),('Motivo',item.get('reason')),('Tipo de recurso',item.get('kind')),('Producto',item.get('component')),('Cantidad',item.get('quantity')),('Urgencia',item.get('urgency')),('Prueba',item.get('test_code')),('Resultado',item.get('value')),('Método',item.get('method')),('Laboratorio',item.get('laboratory')),('Referencia',item.get('reference')),('Evento',item.get('message_code')),('Severidad',item.get('severity')),('Fecha de registro',item.get('created_at')),('Folio',item.get('folio')),('Identificador',item.get('identifier')),('Grupo',item.get('blood_group')),('Estado',item.get('status')),('Caducidad',item.get('expires_at')),('Colecta',item.get('collected_at')),('Versión',item.get('version'))]
        dialog=QDialog(self); dialog.setWindowTitle('Detalle'); layout=QFormLayout(dialog)
        for name,v in fields:
            if v is not None: layout.addRow(name,QLabel(display_value({'Fecha de registro':'created_at','Caducidad':'expires_at','Colecta':'collected_at'}.get(name,''),v)))
        close=QPushButton('Cerrar'); close.clicked.connect(dialog.accept); layout.addRow(close); dialog.exec()

    def durable(self,operation,identifier,body,proof=None):
        record=prepare_command(self.journal,operation,identifier,body)
        return submit_command(self.client,self.journal,record,fresh=True,proof=proof)

    def reauthenticate(self,operation,resource_id,challenge,continuation):
        dialog=QDialog(self); dialog.setWindowTitle('Confirmar identidad'); form=QFormLayout(dialog)
        password=QLineEdit(); password.setEchoMode(QLineEdit.Password); form.addRow('Contraseña',password)
        otp=QLineEdit(); otp.setMaxLength(6); otp.setPlaceholderText('Si tu cuenta lo requiere'); form.addRow('Código de verificación nuevo',otp)
        confirm=QPushButton('Confirmar identidad'); confirm.clicked.connect(dialog.accept); form.addRow(confirm)
        while dialog.exec()==QDialog.Accepted:
            if len(password.text())>=12 and (not otp.text() or re.fullmatch(r'[0-9]{6}',otp.text())): break
            QMessageBox.warning(self,'Datos incompletos','Escribe tu contraseña y, si corresponde, un código de seis dígitos.')
        else:
            password.clear(); otp.clear(); return
        body={'password':password.text(),'challenge':challenge}
        if otp.text(): body['otp']=otp.text()
        password.clear(); otp.clear()
        def authenticate():
            result=self.client.authorized('identidad-acceso','/api/v1/auth/reauthentication-proofs','reauthenticate',method='POST',body=body,request_schema='reauthenticate.xsd')
            if result['operation']!=operation or result['resource_id']!=resource_id or not 40<=len(result['proof'])<=200 or not 1<=result['expires_in']<=120: raise ContractError('Confirmación no corresponde a la acción.')
            return result['proof']
        def auth_failed(error):
            if isinstance(error,ApiError) and error.status==403 and error.code=='reauthentication_required' and self.client and self.client.user:
                self.busy=False; self._worker=None; self.set_controls(True); continuation(None)
            else: self.failed(error)
        self.run(authenticate,continuation,'Confirmando identidad…',auth_failed)

    def secure_attempt(self,record,operation,resource_id,submit,success):
        def attempt(proof=None):
            def work():
                try: return ('result',submit(proof))
                except ApiError as exc:
                    challenge=exc.challenge()
                    if challenge is None: raise
                    return ('challenge',challenge)
            def completed(result):
                if result[0]=='result': success(result[1])
                else: self.reauthenticate(operation,resource_id,result[1],attempt)
            self.run(work,completed,'Registrando operación…')
        attempt()

    def secure_command(self,operation,identifier,body):
        def prepare(): return prepare_command(self.journal,operation,identifier,body)
        def ready(record):
            callback=self.shipment_plan_result if operation=='shipment_create' else lambda _:self.received()
            self.secure_attempt(record,operation,identifier,lambda proof:submit_command(self.client,self.journal,record,fresh=True,proof=proof),callback)
        self.run(prepare,ready,'Preparando operación…')

    def receive(self):
        if self.uncertain:
            self.status.setText('Actualiza la lista y verifica el estado antes de continuar.'); return
        item=self.selected()
        if not item: self.status.setText('Selecciona una muestra.'); return
        if item.get('status')!='REQUESTED': self.status.setText('La muestra ya fue atendida. Actualiza para consultar su estado.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Recepción de muestra'); dialog.resize(520,160); form=QFormLayout(dialog)
        form.addRow('Muestra',QLabel(item['identifier'])); reason=QLineEdit(); reason.setMaxLength(1000); reason.setPlaceholderText('Describe la recepción (mínimo 6 caracteres)'); form.addRow('Motivo',reason)
        confirm=QPushButton('Confirmar recepción'); confirm.setObjectName('primary'); confirm.clicked.connect(dialog.accept); form.addRow(confirm)
        while dialog.exec()==QDialog.Accepted:
            if len(reason.text().strip())>=6: break
            QMessageBox.warning(self,'Motivo incompleto','Escribe al menos seis caracteres.')
        else: return
        body={'decision':'RECEIVED','reason':reason.text().strip(),'version':item['version'],'human_confirmation':'true'}; key=str(uuid.uuid4())
        self.run(lambda:self.durable('lab_sample_receive',item['id'],body),lambda _:self.received(),'Registrando recepción…')

    def open_trace(self):
        item=self.selected()
        if not item: self.status.setText('Selecciona una unidad.'); return
        self.run(lambda:self.client.authorized('inventario','/api/v1/resources/'+item['id']+'/trace','resource_trace'),lambda data:self.trace_dialog(item,data),'Consultando trazabilidad…')

    def trace_dialog(self,item,data):
        if data['resource_id']!=item['id']: self.status.setText('La trazabilidad no corresponde a la unidad.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Trazabilidad · '+label(item.get('folio'))); dialog.resize(760,480); layout=QVBoxLayout(dialog)
        summary=QLabel(('Destino final documentado.' if data['final_destination_recorded'] else 'Sin destino final documentado.')+' · '+str(len(data['shipment_ids']))+' traslados relacionados.'); summary.setWordWrap(True); layout.addWidget(summary)
        note=QLabel(data['notice']); note.setWordWrap(True); layout.addWidget(note)
        if data['restricted_or_unavailable_sources']:
            warning=QLabel('Algunas fuentes no están disponibles o no se pueden consultar con tu perfil.'); warning.setWordWrap(True); layout.addWidget(warning)
        names={'RESOURCE_CREATED':'Unidad registrada','RESOURCE_RELEASED':'Liberación registrada','RESOURCE_RESERVED':'Reserva registrada','SHIPMENT_PLANNED':'Traslado planeado','SHIPMENT_PREPARED':'Traslado preparado','SHIPMENT_COLLECTED':'Unidad recolectada','SHIPMENT_IN_TRANSIT':'Traslado en tránsito','SHIPMENT_DELIVERED':'Entrega documentada','SHIPMENT_ACCEPTED':'Recepción documentada','LAB_SAMPLE_RECEIVED':'Muestra recibida','LAB_RESULT_RECORDED':'Resultado registrado'}
        events=data['events']; table=QTableWidget(len(events),2); table.setHorizontalHeaderLabels(['Fecha','Evento']); table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); table.setEditTriggers(QTableWidget.NoEditTriggers)
        for row,event in enumerate(events):
            table.setItem(row,0,QTableWidgetItem(display_value('occurred_at',event['occurred_at']))); table.setItem(row,1,QTableWidgetItem(names.get(event['action'],'Otro evento documentado')))
        layout.addWidget(table,1); close=QPushButton('Cerrar'); close.clicked.connect(dialog.accept); layout.addWidget(close); dialog.exec()

    def open_cold(self):
        item=self.selected()
        if not item: self.status.setText('Selecciona una unidad.'); return
        self.run(lambda:self.client.authorized('inventario','/api/v1/resources/'+item['id']+'/cold-readings','cold_readings_list',params={'page':1,'page_size':20}),lambda data:self.cold_dialog(item,data),'Consultando conservación…')

    def cold_dialog(self,item,initial):
        dialog=QDialog(self); dialog.setWindowTitle('Conservación · '+label(item.get('folio'))); dialog.resize(760,480); layout=QVBoxLayout(dialog)
        notice=QLabel('Lecturas documentadas; las alertas y límites proceden del servicio.'); notice.setWordWrap(True); layout.addWidget(notice)
        table=QTableWidget(); table.setColumnCount(4); table.setHorizontalHeaderLabels(['Fecha','Temperatura °C','Fuente','Revisión']); table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); table.setEditTriggers(QTableWidget.NoEditTriggers); layout.addWidget(table,1)
        status=QLabel(); layout.addWidget(status); controls=QHBoxLayout(); previous=QPushButton('Anterior'); following=QPushButton('Siguiente'); page_label=QLabel(); controls.addWidget(previous); controls.addWidget(page_label); controls.addWidget(following); controls.addStretch()
        if self.client.user.get('role')=='OPERATOR':
            create=QPushButton('Registrar lectura'); create.clicked.connect(lambda:dialog.done(2)); controls.addWidget(create)
        close=QPushButton('Cerrar'); close.clicked.connect(dialog.reject); controls.addWidget(close); layout.addLayout(controls); state={'page':1,'alive':True}
        def show(data):
            if not state['alive']: return
            state['page']=data['page']; table.setRowCount(len(data['items']))
            for row,value in enumerate(data['items']):
                review=' · '.join([text for condition,text in ((value.get('excursion'),'Excursión'),(value.get('gap'),'Intervalo incompleto')) if condition]) or 'Sin alerta registrada'
                for col,text in enumerate((value.get('captured_at'),value.get('temperature_c'),value.get('source'),review)): table.setItem(row,col,QTableWidgetItem(display_value('captured_at' if col==0 else '',text)))
            page_label.setText('Página '+str(data['page'])+' · '+str(data['total'])+' lecturas'); previous.setEnabled(data['page']>1); following.setEnabled(data['page']*20<data['total']); status.setText('Sin lecturas registradas.' if not data['items'] else '')
        def fetch(page):
            previous.setEnabled(False); following.setEnabled(False); status.setText('Consultando lecturas…')
            worker=Work(lambda:self.client.authorized('inventario','/api/v1/resources/'+item['id']+'/cold-readings','cold_readings_list',params={'page':page,'page_size':20})); dialog.page_worker=worker
            worker.signals.done.connect(show)
            def failed(error):
                if state['alive']: status.setText(str(error) if isinstance(error,ApiError) else 'No se pudo consultar las lecturas.')
            worker.signals.failed.connect(failed); self.pool.start(worker)
        previous.clicked.connect(lambda:fetch(state['page']-1)); following.clicked.connect(lambda:fetch(state['page']+1)); show(initial)
        choice=dialog.exec(); state['alive']=False
        if choice==2: self.create_cold_reading(item)

    def create_cold_reading(self,item):
        dialog=QDialog(self); dialog.setWindowTitle('Registrar lectura'); form=QFormLayout(dialog)
        temperature=QLineEdit(); temperature.setPlaceholderText('Ejemplo: 4.2'); form.addRow('Temperatura °C',temperature)
        captured=QDateTimeEdit(QDateTime.currentDateTime()); captured.setCalendarPopup(True); captured.setDisplayFormat('dd/MM/yyyy HH:mm'); form.addRow('Fecha observada',captured)
        source=QLineEdit(); source.setMaxLength(200); form.addRow('Fuente de lectura',source)
        calibration=QLineEdit(); calibration.setMaxLength(200); form.addRow('Referencia de calibración (opcional)',calibration)
        confirm=QPushButton('Registrar lectura'); confirm.clicked.connect(dialog.accept); form.addRow(confirm)
        while dialog.exec()==QDialog.Accepted:
            try:
                value=float(temperature.text().strip().replace(',','.'))
                if not math.isfinite(value) or not -273.15<=value<=100 or not source.text().strip(): raise ValueError()
                break
            except ValueError: QMessageBox.warning(self,'Datos incompletos','Indica temperatura válida y fuente de lectura.')
        else: return
        body={'temperature_c':value,'captured_at':captured.dateTime().toUTC().toString(Qt.ISODate),'source':source.text().strip()}
        if calibration.text().strip(): body['calibration_reference']=calibration.text().strip()
        self.run(lambda:self.durable('cold_reading_create',item['id'],body),lambda _:self.received(),'Registrando lectura…')

    def administrable_user(self):
        item=self.selected()
        if not item: self.status.setText('Selecciona una cuenta.'); return None
        if self.client.user.get('role')!='ADMIN' or item.get('tenant_id')!=self.client.user.get('tenant_id'):
            self.status.setText('Solo puedes administrar cuentas de tu institución.'); return None
        if item['id']==self.client.user['id']:
            self.status.setText('No puedes cambiar tu propia cuenta desde esta acción.'); return None
        return item

    def create_user(self):
        if not USER_CREATION_ENABLED or not self.client or self.client.user.get('role')!='ADMIN': return
        dialog=QDialog(self); dialog.setWindowTitle('Registrar cuenta'); dialog.resize(480,250); form=QFormLayout(dialog)
        name=QLineEdit(); name.setMaxLength(80); form.addRow('Cuenta',name)
        roles=QComboBox()
        roles.addItem('Selecciona un perfil',None)
        for title,code in (('Administración','ADMIN'),('Operación','OPERATOR'),('Personal médico','MEDICAL'),('Coordinación','COORDINATOR'),('Traslado','TRANSPORT'),('Auditoría','AUDITOR'),('Donante','DONOR')): roles.addItem(title,code)
        form.addRow('Perfil',roles)
        password=QLineEdit(); password.setEchoMode(QLineEdit.Password); form.addRow('Contraseña inicial',password)
        repeated=QLineEdit(); repeated.setEchoMode(QLineEdit.Password); form.addRow('Repite la contraseña',repeated)
        save=QPushButton('Registrar cuenta'); save.clicked.connect(dialog.accept); form.addRow(save)
        while dialog.exec()==QDialog.Accepted:
            secret=password.text()
            if len(name.text().strip())>=3 and roles.currentData() and 12<=len(secret)<=128 and secret==repeated.text(): break
            QMessageBox.warning(self,'Datos incompletos','Indica una cuenta, selecciona un perfil y repite la contraseña inicial de 12 a 128 caracteres.')
        else:
            password.clear(); repeated.clear(); return
        username=name.text().strip(); role=roles.currentData(); password.clear(); repeated.clear()
        def ready(record):
            self.secure_attempt(record,'user_create',None,lambda proof:submit_user(self.client,self.journal,record,secret,proof,fresh=True),lambda _:self.received())
        self.run(lambda:prepare_user(self.journal,self.client.user,username,role,secret),ready,'Preparando alta…')

    def recover_user(self,record):
        if not USER_CREATION_ENABLED: self.status.setText('La recuperación de cuentas aún no está disponible.'); return
        def checked(result):
            if result:
                self.received(); return
            dialog=QDialog(self); dialog.setWindowTitle('Recuperar alta de cuenta'); dialog.resize(480,180); form=QFormLayout(dialog)
            note=QLabel('No hay confirmación disponible. La solicitud puede seguir en curso. Para recuperar el mismo intento, vuelve a introducir la contraseña inicial.'); note.setWordWrap(True); form.addRow(note)
            form.addRow('Cuenta',QLabel(record['body']['username']))
            password=QLineEdit(); password.setEchoMode(QLineEdit.Password); form.addRow('Contraseña inicial',password)
            retry=QPushButton('Recuperar intento'); retry.clicked.connect(dialog.accept); form.addRow(retry)
            if dialog.exec()!=QDialog.Accepted:
                password.clear(); return
            secret=password.text(); password.clear()
            if not 12<=len(secret)<=128: self.status.setText('La contraseña debe tener entre 12 y 128 caracteres.'); return
            self.secure_attempt(record,'user_create',None,lambda proof:submit_user(self.client,self.journal,record,secret,proof),lambda _:self.received())
        self.run(lambda:lookup_user(self.client,self.journal,record),checked,'Consultando confirmación…')

    def begin_device_create(self):
        if self.mode=='devices':
            self.select_transport=True; self.switch('users'); return
        self.create_device()

    def create_device(self):
        item=self.selected()
        if not item or not self.client or self.client.user.get('role')!='ADMIN':
            self.status.setText('Selecciona una cuenta de traslado de tu institución.'); return
        if item.get('tenant_id')!=self.client.user.get('tenant_id') or item.get('role')!='TRANSPORT' or not item.get('active'):
            self.status.setText('Selecciona una cuenta de traslado activa de tu institución.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Registrar dispositivo de traslado'); dialog.resize(480,230); form=QFormLayout(dialog)
        form.addRow('Cuenta',QLabel(item['username']))
        name=QLineEdit(); name.setMaxLength(200); form.addRow('Nombre del dispositivo',name)
        source=QComboBox()
        for title,code in (('Teléfono Android','ANDROID'),('Teléfono iOS','IOS'),('Equipo GPS','GPS_BRIDGE'),('Simulador','SIMULATOR')): source.addItem(title,code)
        form.addRow('Tipo',source)
        expiry=QDateTimeEdit(QDateTime.currentDateTime().addDays(1)); expiry.setCalendarPopup(True); expiry.setDisplayFormat('dd/MM/yyyy HH:mm'); form.addRow('Vigencia hasta',expiry)
        confirm=QCheckBox('Confirmo la vigencia indicada'); form.addRow(confirm)
        save=QPushButton('Registrar'); save.clicked.connect(dialog.accept); form.addRow(save)
        while dialog.exec()==QDialog.Accepted:
            moment=expiry.dateTime().toPython()
            if name.text().strip() and confirm.isChecked() and 0<(moment.astimezone(timezone.utc)-datetime.now(timezone.utc)).total_seconds()<=30*86400: break
            QMessageBox.warning(self,'Datos incompletos','Indica el nombre y confirma una vigencia futura de hasta 30 días.')
        else: return
        body={'id':str(uuid.uuid4()),'user_id':item['id'],'source':source.currentData(),'label':name.text().strip(),'expires_at':moment.astimezone(timezone.utc).isoformat()}
        self.secure_command('device_create',None,body)

    def revoke_device(self):
        item=self.selected()
        if not item or not self.client or self.client.user.get('role')!='ADMIN':
            self.status.setText('Selecciona un dispositivo.'); return
        if not item.get('active'):
            self.status.setText('El dispositivo ya está revocado.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Revocar dispositivo'); dialog.resize(480,180); form=QFormLayout(dialog)
        form.addRow('Dispositivo',QLabel(item['label']))
        reason=QLineEdit(); reason.setMaxLength(1000); form.addRow('Motivo',reason)
        confirm=QCheckBox('Confirmo la revocación'); form.addRow(confirm)
        save=QPushButton('Revocar'); save.clicked.connect(dialog.accept); form.addRow(save)
        while dialog.exec()==QDialog.Accepted:
            if confirm.isChecked() and len(reason.text().strip())>=6: break
            QMessageBox.warning(self,'Datos incompletos','Confirma la revocación e indica un motivo de al menos seis caracteres.')
        else: return
        self.secure_command('device_revoke',item['id'],{'version':item['version'],'human_confirmation':True,'reason':reason.text().strip()})

    def change_user_state(self):
        item=self.administrable_user()
        if not item: return
        new_state=not item['active']; action='activar' if new_state else 'desactivar'
        detail=' Las sesiones abiertas de esta cuenta se cerrarán.' if not new_state else ''
        if QMessageBox.question(self,'Cambiar estado','¿Deseas '+action+' la cuenta '+item['username']+'?'+detail) != QMessageBox.Yes: return
        body={'active':new_state,'version':item['version']}
        self.secure_command('user_state',item['id'],body)

    def change_user_role(self):
        item=self.administrable_user()
        if not item: return
        if item['role'] in ('ADMIN','AUDITOR','COORDINATOR'):
            self.status.setText('Los perfiles regionales requieren provisión autorizada.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Cambiar perfil'); form=QFormLayout(dialog)
        form.addRow('Cuenta',QLabel(item['username'])); role=QComboBox(); role.addItem('Selecciona un perfil','')
        for name,code in (('Operador','OPERATOR'),('Personal médico','MEDICAL'),('Transporte','TRANSPORT'),('Donante','DONOR')): role.addItem(name,code)
        form.addRow('Nuevo perfil',role); reason=QLineEdit(); reason.setMaxLength(1000); form.addRow('Motivo documentado',reason)
        note=QLabel('Las sesiones abiertas se cerrarán.'); note.setWordWrap(True); form.addRow(note)
        confirm=QPushButton('Confirmar cambio'); confirm.clicked.connect(dialog.accept); form.addRow(confirm)
        while dialog.exec()==QDialog.Accepted:
            if role.currentData() and role.currentData()!=item['role'] and len(reason.text().strip())>=6: break
            QMessageBox.warning(self,'Datos incompletos','Elige un perfil distinto y escribe un motivo de al menos seis caracteres.')
        else: return
        body={'human_confirmation':True,'reason':reason.text().strip(),'role':role.currentData(),'version':item['version']}
        self.secure_command('user_role',item['id'],body)

    def coverage_detail(self,item):
        slots=item.get('slot_count'); matched=item.get('matched_count'); result=item.get('result')
        def valid_id(value):
            try: return isinstance(value,str) and str(uuid.UUID(value))==value
            except ValueError: return False
        if isinstance(slots,bool) or not isinstance(slots,int) or isinstance(matched,bool) or not isinstance(matched,int) or not isinstance(result,list) or len(result)!=matched or not 0<=matched<=slots<=500 or any(not isinstance(row,dict) or not valid_id(row.get('request_id')) or not valid_id(row.get('resource_id')) for row in result):
            self.status.setText('No se pudo mostrar la propuesta. Actualiza la lista y vuelve a intentarlo.'); return
        snapshots=item.get('snapshots') if isinstance(item.get('snapshots'),dict) else {}
        medical=bool(self.client and self.client.user and self.client.user.get('role')=='MEDICAL')
        dialog=QDialog(self); dialog.setWindowTitle('Propuesta de cobertura'); dialog.resize(700,480); layout=QVBoxLayout(dialog)
        summary=QLabel(f'Unidades propuestas: {matched} · requeridas: {slots}'); summary.setWordWrap(True); layout.addWidget(summary)
        calculation=QLabel('Cálculo: '+label(item.get('algorithm_version'))+' · Fecha: '+display_value('created_at',item.get('created_at'))); calculation.setWordWrap(True); layout.addWidget(calculation)
        note=QLabel('La propuesta no reserva unidades. El personal médico debe revisar la vigencia y autorizar cada reserva.'); note.setWordWrap(True); layout.addWidget(note)
        table=QTableWidget(len(result),2); table.setHorizontalHeaderLabels(['Solicitud','Unidad propuesta']); table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); table.setSelectionBehavior(QTableWidget.SelectRows); table.setSelectionMode(QTableWidget.SingleSelection); table.setEditTriggers(QTableWidget.NoEditTriggers)
        request_numbers={}
        for index,row in enumerate(result):
            number=request_numbers.setdefault(row['request_id'],len(request_numbers)+1)
            table.setItem(index,0,QTableWidgetItem(f'Solicitud {number}')); table.setItem(index,1,QTableWidgetItem(f'Unidad propuesta {index+1}'))
        layout.addWidget(table)
        hint=QLabel('Los números identifican filas solo en esta propuesta; no son folios. Selecciona una unidad para consultar su folio y estado.' if result else 'No hay unidades propuestas. Consulta una evaluación actualizada con el personal médico.'); hint.setWordWrap(True); layout.addWidget(hint)
        controls=QHBoxLayout(); unit=QPushButton('Consultar unidad'); evaluation=QPushButton('Abrir evaluación'); close=QPushButton('Cerrar')
        def selected_row():
            index=table.currentRow(); return result[index] if 0<=index<len(result) else None
        def selection_changed():
            row=selected_row(); snapshot=snapshots.get(row['request_id']) if row else None
            unit.setEnabled(bool(row)); evaluation.setEnabled(bool(medical and isinstance(snapshot,dict) and valid_id(snapshot.get('evaluation_id'))))
        table.itemSelectionChanged.connect(selection_changed); selection_changed()
        evaluation.setVisible(medical); unit.clicked.connect(lambda:dialog.done(1)); evaluation.clicked.connect(lambda:dialog.done(2)); close.clicked.connect(dialog.reject)
        for button in (unit,evaluation,close): controls.addWidget(button)
        layout.addLayout(controls); choice=dialog.exec(); row=selected_row()
        if choice==1 and row:
            self.run(lambda:self.client.authorized('inventario','/api/v1/resources/'+row['resource_id'],'resource_detail'),self.detail,'Consultando unidad…')
        elif choice==2 and row:
            identifier=snapshots[row['request_id']]['evaluation_id']
            self.run(lambda:self.client.authorized('compatibilidad','/api/v1/evaluations/'+identifier,'evaluation_detail'),self.evaluation_detail,'Consultando evaluación…')

    def download_report(self):
        item=self.selected()
        if not item: self.status.setText('Selecciona un reporte.'); return
        if item.get('status')!='COMPLETE' or not item.get('file_id'):
            self.status.setText('El reporte todavía no está disponible para descargar.'); return
        suffix={'PDF':'pdf','CSV':'csv','XLSX':'xlsx'}.get(item.get('format'))
        if not suffix: self.status.setText('El formato del reporte no es válido.'); return
        target,_=QFileDialog.getSaveFileName(self,'Guardar reporte','reporte.'+suffix,'Archivo '+suffix.upper()+' (*.'+suffix+')')
        if not target: return
        overwrite=Path(target).exists()
        if overwrite and QMessageBox.question(self,'Reemplazar archivo','El archivo existe. ¿Deseas reemplazarlo?') != QMessageBox.Yes: return
        def transfer():
            job=self.client.authorized('documentos','/api/v1/export-jobs/'+item['id'],'export_detail')
            if job['status']!='COMPLETE' or job['file_id']!=item['file_id']: raise DownloadError('El reporte cambió. Actualiza e inténtalo de nuevo.')
            metadata=self.client.authorized('documentos','/api/v1/documents/'+job['file_id']+'/verified','document_verified')
            if metadata.get('analysis')!='CLEAN' or metadata.get('file_status')!='VERIFIED': raise DownloadError('El reporte aún no terminó la verificación.')
            access=self.client.authorized('documentos','/api/v1/files/'+job['file_id']+'/download','file_download')
            download(access['download_url'],self.client.base,metadata['sha256'],target,overwrite=overwrite)
        self.run(transfer,lambda _:self.status.setText('Reporte descargado y verificado.'),'Descargando reporte…')

    def create_report(self):
        role=self.client.user.get('role'); available=[]
        for title,code,roles in (
            ('Inventario','INVENTORY',('OPERATOR','MEDICAL','COORDINATOR')),
            ('Caducidad','EXPIRY',('OPERATOR','MEDICAL','COORDINATOR')),
            ('Solicitudes','REQUESTS',('OPERATOR','MEDICAL')),
            ('Traslados','SHIPMENTS',('OPERATOR','MEDICAL','COORDINATOR','TRANSPORT')),
            ('Actividad','ACTIVITY',('AUDITOR',))):
            if role in roles: available.append((title,code))
        if not available: self.status.setText('Tu perfil no tiene reportes disponibles.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Solicitar reporte'); form=QFormLayout(dialog)
        report=QComboBox(); report.addItem('Selecciona un reporte','')
        for title,code in available: report.addItem(title,code)
        form.addRow('Reporte',report)
        output=QComboBox(); output.addItem('Selecciona un formato',''); output.addItems(['PDF','CSV','XLSX']); form.addRow('Formato',output)
        start=QDateTimeEdit(QDateTime.currentDateTime().addDays(-30)); start.setCalendarPopup(True); start.setDisplayFormat('dd/MM/yyyy HH:mm'); form.addRow('Desde',start)
        end=QDateTimeEdit(QDateTime.currentDateTime()); end.setCalendarPopup(True); end.setDisplayFormat('dd/MM/yyyy HH:mm'); form.addRow('Antes de',end)
        note=QLabel('El reporte es una solicitud de información autorizada; su disponibilidad depende del servicio.'); note.setWordWrap(True); form.addRow(note)
        confirm=QPushButton('Solicitar reporte'); confirm.clicked.connect(dialog.accept); form.addRow(confirm)
        while dialog.exec()==QDialog.Accepted:
            if report.currentData() and output.currentIndex()>0 and start.dateTime()<end.dateTime(): break
            QMessageBox.warning(self,'Datos incompletos','Elige reporte, formato y un periodo válido.')
        else: return
        body={'report':report.currentData(),'format':output.currentText(),'from_at':start.dateTime().toUTC().toString(Qt.ISODate),'until_at':end.dateTime().toUTC().toString(Qt.ISODate),'timezone':'America/Monterrey'}
        def requested(_):
            self.load(); self.status.setText('Reporte solicitado. Consulta su estado antes de descargarlo.')
        self.run(lambda:self.durable('export_create',None,body),requested,'Solicitando reporte…')

    def preview_label(self):
        item=self.selected()
        if not item: self.status.setText('Selecciona una unidad.'); return
        self.run(lambda:self.client.authorized('inventario','/api/v1/resources/'+item['id'],'resource_detail'),self.show_label,'Verificando unidad…')

    def show_label(self,item):
        qr=qrcode.QRCode(border=4,box_size=4); qr.add_data(item['id']); qr.make(fit=True); matrix=qr.get_matrix(); scale=5
        image=QImage(len(matrix)*scale,len(matrix)*scale,QImage.Format_RGB32); image.fill(QColor('white'))
        painter=QPainter(image); painter.setPen(Qt.NoPen); painter.setBrush(QColor('black'))
        for y,row in enumerate(matrix):
            for x,black in enumerate(row):
                if black: painter.drawRect(x*scale,y*scale,scale,scale)
        painter.end()
        dialog=QDialog(self); dialog.setWindowTitle('Vista previa de etiqueta'); layout=QVBoxLayout(dialog)
        title=QLabel('Unidad '+label(item.get('folio'))); title.setObjectName('title'); layout.addWidget(title)
        layout.addWidget(QLabel('Producto: '+label(item.get('component'))+' · Grupo: '+label(item.get('blood_group'))))
        code=QLabel(); code.setPixmap(QPixmap.fromImage(image)); code.setAlignment(Qt.AlignCenter); layout.addWidget(code)
        if LABEL_ISSUANCE_ENABLED and self.client.user.get('role') in ('OPERATOR','MEDICAL'):
            reason=QLineEdit(); reason.setMaxLength(1000); reason.setPlaceholderText('Motivo de emisión'); layout.addWidget(reason)
            buttons=QHBoxLayout(); pdf=QPushButton('Guardar PDF'); printer=QPushButton('Imprimir')
            pdf.clicked.connect(lambda:dialog.done(1)); printer.clicked.connect(lambda:dialog.done(2)); buttons.addWidget(pdf); buttons.addWidget(printer); layout.addLayout(buttons)
        else:
            note=QLabel('Vista previa. La impresión y reimpresión auditadas aún no están disponibles.'); note.setWordWrap(True); layout.addWidget(note)
        close=QPushButton('Cerrar'); close.clicked.connect(dialog.reject); layout.addWidget(close)
        while True:
            choice=dialog.exec()
            if choice not in (1,2) or not LABEL_ISSUANCE_ENABLED: return
            if len(reason.text().strip())>=6: break
            QMessageBox.warning(self,'Motivo incompleto','Escribe al menos seis caracteres.')
        action='EXPORT_PDF' if choice==1 else 'PRINT'; text=reason.text().strip()
        def issue():
            record=prepare_label(self.journal,item,action,text); result=submit_label(self.client,self.journal,record); return record,result
        self.run(issue,lambda pair:self.label_authorized(item,pair[0],pair[1]['issuance_id']),'Autorizando emisión…')

    def label_authorized(self,resource,record,issuance_id):
        QMessageBox.information(self,'Emisión autorizada','La emisión quedó registrada. A continuación elige dónde producir la etiqueta.')
        if record['body']['action']=='EXPORT_PDF':
            target,_=QFileDialog.getSaveFileName(self,'Guardar etiqueta','','PDF (*.pdf)')
            if not target: self.status.setText('Emisión autorizada; salida pendiente.'); return
            overwrite=Path(target).exists()
            if overwrite and QMessageBox.question(self,'Reemplazar archivo','El archivo existe. ¿Deseas reemplazarlo?') != QMessageBox.Yes: return
            def output():
                write_pdf(target,resource,overwrite=overwrite)
                self.journal.update(record['key'],{'operation_id':issuance_id,'status':'COMPLETED'})
            self.run(output,lambda _:self.status.setText('Etiqueta guardada en PDF.'),'Generando PDF…')
        else:
            printer=QPrinter(QPrinter.HighResolution); choice=QPrintDialog(printer,self)
            if choice.exec()!=QDialog.Accepted: self.status.setText('Emisión autorizada; impresión pendiente.'); return
            def output():
                self.journal.print_transition(record['key'],issuance_id,'start')
                draw_label(printer,resource)
                self.journal.print_transition(record['key'],issuance_id,'sent')
            self.run(output,lambda _:self.status.setText('Solicitud enviada a impresión. Verifica el resultado en la impresora.'),'Enviando a impresión…')

    def plan_shipment(self):
        if self.uncertain:
            self.status.setText('Actualiza la lista antes de planificar.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='COORDINATOR':
            self.status.setText('La planificación corresponde a coordinación.'); return
        body=planning_dialog(self,Work,lambda value:display_value('expires_at',value) if isinstance(value,str) and 'T' in value else label(value))
        if body: self.secure_command('shipment_create',None,body)

    def shipment_plan_result(self,result):
        if result.get('status')=='REJECTED':
            self.status.setText('El traslado no pudo vincularse a la reserva. Solicita revisión.'); return
        if result.get('inventory_pending'):
            self.status.setText('La planificación sigue pendiente de confirmación. Consulta Operaciones pendientes antes de intentar otra.'); return
        if result.get('status') not in ('PLANNED','PREPARED','COLLECTED','IN_TRANSIT','DELIVERED','ACCEPTED'):
            self.status.setText('El traslado requiere revisión autorizada. Consulta Operaciones pendientes.'); return
        self.load()
        self.status.setText('Traslado planificado. Consulta su detalle para continuar la coordinación.')

    def shipment_detail(self,item):
        role=self.client.user.get('role')
        if role in ('OPERATOR','COORDINATOR','TRANSPORT'):
            self.run(lambda:self.client.authorized('transporte','/api/v1/shipments/'+item['id']+'/operational-context','operational_context'),lambda context:self.shipment_context(item,context),'Consultando instituciones…')
        else: self.shipment_context(item,None)

    def shipment_context(self,item,context):
        dialog=QDialog(self); dialog.setWindowTitle('Detalle del traslado'); layout=QFormLayout(dialog)
        layout.addRow('Estado',QLabel(label(item.get('status')))); layout.addRow('Salida prevista',QLabel(label(item.get('departure_at')))); layout.addRow('Llegada prevista',QLabel(label(item.get('eta'))))
        if context:
            layout.addRow('Origen',QLabel(context['origin']['name'])); layout.addRow('Destino',QLabel(context['destination']['name']))
        track=QPushButton('Ver seguimiento'); track.clicked.connect(lambda:dialog.done(1)); layout.addRow(track)
        custody=QPushButton('Ver cadena de custodia'); custody.clicked.connect(lambda:dialog.done(3)); layout.addRow(custody)
        if context and self.client.user.get('role')=='OPERATOR' and self.client.user.get('tenant_id')==context['origin']['id'] and item.get('status')=='PLANNED' and not item.get('inventory_pending'):
            prepare=QPushButton('Documentar preparación'); prepare.clicked.connect(lambda:dialog.done(2)); layout.addRow(prepare)
        if CUSTODY_ACCEPT_ENABLED and context and self.client.user.get('role')=='OPERATOR' and self.client.user.get('tenant_id')==context['destination']['id'] and item.get('status')=='DELIVERED' and not item.get('inventory_pending'):
            accept=QPushButton('Documentar recepción'); accept.clicked.connect(lambda:dialog.done(4)); layout.addRow(accept)
        close=QPushButton('Cerrar'); close.clicked.connect(dialog.reject); layout.addRow(close)
        choice=dialog.exec()
        if choice==1: self.open_tracking(item)
        elif choice==2: self.prepare_shipment(item)
        elif choice==3:
            self.run(lambda:self.client.authorized('custodia','/api/v1/chains/'+item['id'],'chain_detail'),lambda data:self.custody_dialog(item,data),'Consultando cadena de custodia…')
        elif choice==4:
            self.run(lambda:self.client.authorized('transporte','/api/v1/shipments/'+item['id']+'/operational-handover','operational_handover'),lambda data:self.accept_shipment(item,context,data),'Verificando responsable…')

    def accept_shipment(self,item,context,handover):
        if (handover['shipment_id']!=item['id'] or handover['shipment_version']!=item['version']
                or context['shipment_version']!=item['version'] or handover['transport_user']['id']!=context['transport_user_id']
                or item['transport_user_id']!=context['transport_user_id']):
            self.status.setText('El traslado cambió. Actualiza antes de documentar la recepción.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Documentar recepción'); dialog.resize(760,260); form=QFormLayout(dialog)
        form.addRow('Cuenta operativa del transportista',QLabel(handover['transport_user']['name']))
        code=QLineEdit(); code.setPlaceholderText('Identificador leído de la unidad'); form.addRow('Código de la unidad',code)
        seal=QLineEdit(); seal.setMaxLength(200); form.addRow('Sello documentado',seal)
        reason=QLineEdit(); reason.setMaxLength(1000); form.addRow('Motivo de recepción',reason)
        confirm=QCheckBox('Confirmo la unidad, el sello y la entrega con la cuenta indicada.'); form.addRow(confirm)
        save=QPushButton('Confirmar recepción'); save.clicked.connect(dialog.accept); form.addRow(save)
        while dialog.exec()==QDialog.Accepted:
            try:
                value=code.text().strip()
                if str(uuid.UUID(value))!=value or not seal.text().strip() or len(reason.text().strip())<6 or not confirm.isChecked(): raise ValueError()
                break
            except ValueError:
                QMessageBox.warning(self,'Datos incompletos','Verifica el código, el sello, el motivo y la confirmación.')
        else: return
        body={'human_confirmation':True,'reason':reason.text().strip(),'version':item['version'],'state':'ACCEPTED',
              'custody':{'scanned_resource_id':value,'seal':seal.text().strip(),'captured_at':QDateTime.currentDateTimeUtc().toString(Qt.ISODate),
                         'reported_handover_user_id':handover['transport_user']['id'],'electronic_acceptance':True}}
        def verified(result):
            if (result.get('shipment_id')!=item['id'] or result.get('resource_id')!=value
                    or result.get('version')!=item['version'] or result.get('status')!='DELIVERED'
                    or result.get('verified') is not True):
                self.status.setText('La verificación no corresponde al traslado. Actualiza y revisa.'); return
            self.secure_command('shipment_transition',item['id'],body)
        self.run(lambda:self.durable('shipment_scan',item['id'],{'scanned_resource_id':value}),verified,'Verificando código de la unidad…')

    def custody_dialog(self,item,data):
        if data['chain']['id']!=item['id'] or any(event['shipment_id']!=item['id'] for event in data['events']):
            self.status.setText('La cadena no corresponde al traslado seleccionado.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Cadena de custodia'); dialog.resize(700,460); layout=QVBoxLayout(dialog)
        notice=QLabel('La recepción documentada no confirma una transfusión ni un trasplante.'); notice.setWordWrap(True); layout.addWidget(notice)
        table=QTableWidget(len(data['events']),3); table.setHorizontalHeaderLabels(['Orden','Fecha','Estado documentado']); table.setEditTriggers(QTableWidget.NoEditTriggers); table.verticalHeader().hide(); table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row,event in enumerate(data['events']):
            values=(str(event['sequence']),display_value('occurred_at',event['event']['occurred_at']),label(event['event']['metadata'].get('state')))
            for column,value in enumerate(values): table.setItem(row,column,QTableWidgetItem(value))
        layout.addWidget(table); close=QPushButton('Cerrar'); close.clicked.connect(dialog.accept); layout.addWidget(close); dialog.exec()

    def prepare_shipment(self,item):
        dialog=QDialog(self); dialog.setWindowTitle('Preparar traslado'); form=QFormLayout(dialog)
        reason=QLineEdit(); reason.setMaxLength(1000); form.addRow('Motivo documentado',reason)
        confirm=QPushButton('Confirmar preparación'); confirm.clicked.connect(dialog.accept); form.addRow(confirm)
        while dialog.exec()==QDialog.Accepted:
            if len(reason.text().strip())>=6: break
            QMessageBox.warning(self,'Motivo incompleto','Escribe al menos seis caracteres.')
        else: return
        body={'human_confirmation':True,'reason':reason.text().strip(),'version':item['version'],'state':'PREPARED'}
        self.run(lambda:self.durable('shipment_transition',item['id'],body),lambda _:self.received(),'Registrando preparación…')

    def open_tracking(self,item):
        client=self.client; shipment=item['id']; actor=client.user['id']
        def fetch():
            snapshot=client.authorized('transporte','/api/v1/shipments/'+shipment+'/tracking/snapshot','tracking_snapshot')
            if snapshot.get('head'):
                snapshot=client.authorized('transporte','/api/v1/shipments/'+shipment+'/tracking/snapshot','tracking_snapshot',params={'cursor':max(0,snapshot['head']-100)})
            for key in ('cursor','head'):
                value=snapshot.get(key)
                if isinstance(value,bool) or not isinstance(value,int) or not 0<=value<=9007199254740991: raise ContractError('Cursor de seguimiento inválido.')
            if snapshot.get('shipment_id')!=shipment or snapshot['cursor']>snapshot['head'] or snapshot.get('state') not in ('LIVE','STALE','NO_DATA','NO_FIX','FINALIZED') or len(snapshot.get('events',[]))>100: raise ContractError('Instantánea no válida.')
            anchors=[]
            for field,title in (('origin_id','Origen'),('destination_id','Destino')):
                location=client.authorized('identidad-acceso','/api/v1/institutions/'+item[field]+'/presentation','institution_presentation')
                anchors.append({'label':title,**location})
            points=[validate_snapshot_point(p,shipment) for p in snapshot.get('events',[])]
            if snapshot.get('position'): points.append(validate_snapshot_point(snapshot['position'],shipment))
            policy=client.authorized('identidad-acceso','/api/v1/portal-policy','portal_policy')
            client.authorized('identidad-acceso','/api/v1/auth/me','me')
            if not client.user or client.user['id']!=actor: raise ApiError(401,'session','La sesión cambió.')
            return snapshot,anchors,points,client.access,policy
        self.run(fetch,lambda data:self.tracking_view(client,item,data),'Preparando seguimiento…')

    def tracking_view(self,client,item,data):
        shipment=item['id']
        snapshot,anchors,points,token,policy=data; stale_seconds=policy['tracking_stale_seconds']; dialog=QDialog(self); dialog.setWindowTitle('Seguimiento del traslado'); dialog.resize(900,650); layout=QVBoxLayout(dialog)
        heading=QLabel('Seguimiento en Nuevo León'); heading.setObjectName('title'); layout.addWidget(heading)
        status=QLabel('Preparando seguimiento…'); status.setWordWrap(True); layout.addWidget(status)
        notice=QLabel('La cartografía externa recibe el área que visualizas. Las posiciones se muestran solo con autorización.'); notice.setWordWrap(True); layout.addWidget(notice)
        try: map_view=RegionMap(dialog)
        except (OSError,ValueError):
            QMessageBox.warning(self,'Mapa no disponible','No fue posible preparar la cartografía.'); return
        map_view.set_anchors(anchors)
        for point in points: map_view.add_position(point)
        layout.addWidget(map_view,1); latest=QLabel('Sin observaciones de ubicación.'); latest.setWordWrap(True); layout.addWidget(latest)
        tracker=TrackingSocket(client.base,shipment,dialog); tracker.cursor=snapshot.get('cursor'); self.tracking=tracker
        states={'LIVE':'En vivo','STALE':'Última observación retrasada','NO_DATA':'Sin observaciones','NO_FIX':'Sin señal GPS','FINALIZED':'Traslado finalizado'}
        tracker.state.connect(lambda text:status.setText(states.get(text,text)))
        last={'point':None}
        def update_age():
            point=last['point']
            if not point: return
            timestamp=datetime.fromisoformat(point['captured_at'].replace('Z','+00:00'))
            age=max(0,int((datetime.now(timezone.utc)-timestamp.astimezone(timezone.utc)).total_seconds()))
            freshness=' · Retrasada' if age>stale_seconds else ''
            outside=point['fix_valid'] and not (23.1<=point['latitude']<=27.85 and -101.3<=point['longitude']<=-98.35)
            zone=QTimeZone(policy['timezone'].encode()); moment=QDateTime.fromString(point['captured_at'],Qt.ISODate)
            displayed=moment.toTimeZone(zone).toString('dd/MM/yyyy HH:mm:ss') if zone.isValid() and moment.isValid() else point['captured_at']
            coordinate=(' · '+str(point['latitude'])+', '+str(point['longitude'])) if point['fix_valid'] else ''
            source={'SIMULATOR':'Simulador','GPS_BRIDGE':'Equipo GPS','ANDROID':'Teléfono Android','IOS':'Teléfono iOS'}.get(point['source'],'Fuente no informada')
            latest.setText('Última observación: '+displayed+' · Hace '+str(age)+' s · '+source+coordinate+freshness+(' · Simulada' if point['source']=='SIMULATOR' or point.get('simulated') else '')+(' · Sin señal' if not point['fix_valid'] else '')+(' · Fuera del encuadre regional inicial' if outside else ''))
        def receive(point):
            map_view.add_position(point)
            previous=last['point']; last['point']=latest_position(previous,point)
            if last['point'] is point: update_age()
        def clear_tracking():
            map_view.clear_positions(); map_view.set_anchors([]); last['point']=None; latest.setText('Seguimiento sin autorización activa.')
        def reset_history():
            map_view.clear_positions(); last['point']=None; latest.setText('Actualizando observaciones disponibles.'); status.setText('Recuperando seguimiento…')
        tracker.position.connect(receive); tracker.terminated.connect(clear_tracking); tracker.resync.connect(reset_history)
        for point in points: receive(point)
        age_timer=QTimer(dialog); age_timer.setInterval(5000); age_timer.timeout.connect(update_age); age_timer.start()
        alive={'value':True}; actor=client.user['id']
        def reconnect():
            if not alive['value'] or self.client is not client: return
            def credentials():
                client.authorized('identidad-acceso','/api/v1/auth/me','me')
                if not client.user or client.user['id']!=actor: raise ApiError(401,'session','Sesión no disponible.')
                refreshed=[]
                for field,title in (('origin_id','Origen'),('destination_id','Destino')):
                    location=client.authorized('identidad-acceso','/api/v1/institutions/'+item[field]+'/presentation','institution_presentation')
                    refreshed.append({'label':title,**location})
                return client.access,refreshed
            worker=Work(credentials); dialog.refresh_worker=worker
            def ready(value):
                if alive['value']: map_view.set_anchors(value[1]); tracker.start(value[0])
            worker.signals.done.connect(ready)
            def failed(error):
                if not alive['value']: return
                if not client.user or isinstance(error,ApiError) and error.status in (401,403):
                    tracker.stop(); clear_tracking(); status.setText('No se pudo confirmar el acceso al seguimiento.')
                else:
                    status.setText('Sin conexión; se conserva la última observación.'); tracker.disconnected()
            worker.signals.failed.connect(failed); self.pool.start(worker)
        tracker.reconnect.connect(reconnect)
        controls=QHBoxLayout(); center=QPushButton('Ver última posición'); center.clicked.connect(map_view.center_latest); controls.addWidget(center)
        close=QPushButton('Cerrar'); close.clicked.connect(dialog.accept); controls.addWidget(close); layout.addLayout(controls)
        if snapshot.get('state')=='FINALIZED': status.setText('Traslado finalizado.')
        else: tracker.start(token)
        dialog.exec(); alive['value']=False; tracker.stop(); map_view.stop(); self.tracking=None

    def evaluate_request(self):
        item=self.selected()
        if self.uncertain: self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if not item: self.status.setText('Selecciona una solicitud.'); return
        if QMessageBox.question(self,'Generar evaluación','Se generará una preselección para revisión médica. ¿Continuar?') != QMessageBox.Yes: return
        body={'request_id':item['id']}; key=str(uuid.uuid4())
        def created(evaluation):
            self.run(lambda:self.client.authorized('compatibilidad','/api/v1/evaluations/'+evaluation['id'],'evaluation_detail'),self.evaluation_detail,'Comprobando vigencia…')
        self.run(lambda:self.durable('evaluation_create',None,body),created,'Generando evaluación…')

    def open_request_form(self):
        if self.uncertain:
            self.status.setText('Actualiza y verifica las operaciones pendientes antes de continuar.'); return
        if not self.client or self.client.user.get('role')!='MEDICAL':
            self.status.setText('El registro corresponde a personal médico autorizado.'); return
        self.request_form()

    def request_form(self):
        client=self.client
        dialog=QDialog(self); dialog.setWindowTitle('Registrar solicitud'); dialog.resize(760,560)
        layout=QVBoxLayout(dialog)
        note=QLabel('Busca y selecciona un receptor de tu institución. La solicitud requiere revisión profesional.'); note.setWordWrap(True); layout.addWidget(note)
        search_row=QHBoxLayout(); search=QLineEdit(); search.setPlaceholderText('Buscar receptor por folio o nombre'); search_row.addWidget(search)
        find=QPushButton('Buscar'); search_row.addWidget(find); layout.addLayout(search_row)
        table=QTableWidget(0,3); table.setHorizontalHeaderLabels(['Folio','Nombre','Estado']); table.setSelectionBehavior(QTableWidget.SelectRows); table.setSelectionMode(QTableWidget.SingleSelection); table.setEditTriggers(QTableWidget.NoEditTriggers); table.verticalHeader().hide(); table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(table,1)
        nav=QHBoxLayout(); previous=QPushButton('Anterior'); following=QPushButton('Siguiente'); page_label=QLabel(); nav.addWidget(previous); nav.addWidget(page_label); nav.addWidget(following); nav.addStretch(); layout.addLayout(nav)
        fields=QFormLayout(); component=QComboBox(); component.addItem('Selecciona un receptor','')
        fields.addRow('Recurso solicitado',component); quantity=QSpinBox(); quantity.setRange(1,100); fields.addRow('Cantidad',quantity)
        urgency=QComboBox(); urgency.addItem('Selecciona urgencia',None)
        for number in (1,2,3): urgency.addItem(str(number),number)
        fields.addRow('Urgencia documentada',urgency); layout.addLayout(fields)
        status=QLabel(''); status.setWordWrap(True); layout.addWidget(status)
        buttons=QHBoxLayout(); confirm=QPushButton('Registrar solicitud'); cancel=QPushButton('Cancelar'); buttons.addWidget(confirm); buttons.addWidget(cancel); layout.addLayout(buttons)
        state={'page':1,'total':0,'rows':[],'alive':True,'busy':False,'body':None}
        def choose_recipient():
            component.clear(); component.addItem('Selecciona un recurso','')
            quantity.setMaximum(100)
            index=table.currentRow()
            if not 0<=index<len(state['rows']): return
            person=state['rows'][index]
            status.setText('Receptor seleccionado: '+label(person.get('folio')) if person.get('status')=='ACTIVE' else 'El receptor seleccionado está inactivo.')
            if person.get('kind')=='BLOOD':
                for title,code in (('Eritrocitos','RBC'),('Plasma','PLASMA'),('Plaquetas','PLATELETS')): component.addItem(title,code)
            elif person.get('kind')=='ORGAN' and person.get('organ_type') in ('KIDNEY','LIVER','HEART'):
                quantity.setMaximum(1)
                component.addItem(label(person['organ_type']),person['organ_type'])
        def show(data):
            if not state['alive']: return
            state.update(page=data['page'],total=data['total'],rows=data['items'],busy=False)
            table.setRowCount(len(state['rows']))
            for index,row in enumerate(state['rows']):
                for column,value in enumerate((row.get('folio'),row.get('display_name'),row.get('status'))): table.setItem(index,column,QTableWidgetItem(label(value)))
            page_label.setText('Página '+str(state['page'])+' · '+str(state['total'])+(' registro' if state['total']==1 else ' registros'))
            previous.setEnabled(state['page']>1); following.setEnabled(state['page']*20<state['total']); confirm.setEnabled(True)
            status.setText('Sin receptores para esta búsqueda.' if not state['rows'] else 'Selecciona un receptor activo.')
        def fetch(page):
            if state['busy']: return
            state.update(busy=True,rows=[]); table.setRowCount(0); component.clear(); component.addItem('Selecciona un receptor',''); previous.setEnabled(False); following.setEnabled(False); confirm.setEnabled(False); status.setText('Consultando receptores…')
            params={'page':page,'page_size':20}; term=search.text().strip()
            if term: params['q']=term
            worker=Work(lambda:client.authorized('receptores','/api/v1/recipients','recipients',params=params))
            if not hasattr(self,'_request_workers'): self._request_workers=[]
            self._request_workers.append(worker)
            def completed(data):
                self._request_workers.remove(worker)
                show(data)
            worker.signals.done.connect(completed)
            def failed(error):
                self._request_workers.remove(worker)
                if not state['alive']: return
                state['busy']=False; confirm.setEnabled(False)
                status.setText(str(error) if isinstance(error,ApiError) else 'No se pudo consultar receptores.')
            worker.signals.failed.connect(failed); self.pool.start(worker)
        def save():
            index=table.currentRow()
            if not 0<=index<len(state['rows']) or state['rows'][index].get('status')!='ACTIVE' or not component.currentData() or urgency.currentData() is None:
                QMessageBox.warning(dialog,'Datos incompletos','Selecciona un receptor activo, el recurso y la urgencia.'); return
            state['body']={'recipient_id':state['rows'][index]['id'],'component':component.currentData(),'quantity':quantity.value(),'urgency':urgency.currentData()}
            dialog.accept()
        table.itemSelectionChanged.connect(choose_recipient); find.clicked.connect(lambda:fetch(1)); search.returnPressed.connect(lambda:fetch(1)); previous.clicked.connect(lambda:fetch(state['page']-1)); following.clicked.connect(lambda:fetch(state['page']+1)); confirm.clicked.connect(save); cancel.clicked.connect(dialog.reject)
        QTimer.singleShot(0,lambda:fetch(1)); accepted=dialog.exec(); state['alive']=False
        if accepted==QDialog.Accepted and state['body']:
            self.run(lambda:self.durable('request_create',None,state['body']),lambda _:self.received(),'Registrando solicitud…')

    def evaluation_detail(self,evaluation):
        candidates=evaluation.get('candidates') or []
        dialog=QDialog(self); dialog.setWindowTitle('Candidatos para revisión'); dialog.resize(760,540); layout=QVBoxLayout(dialog)
        notice=QLabel(evaluation.get('snapshot',{}).get('clinical_notice') or 'Preselección de apoyo: requiere evaluación y decisión del profesional autorizado.'); notice.setWordWrap(True); layout.addWidget(notice)
        if not candidates:
            layout.addWidget(QLabel('No hay candidatos en esta evaluación.')); close=QPushButton('Cerrar'); close.clicked.connect(dialog.reject); layout.addWidget(close); dialog.exec(); return
        table=QTableWidget(len(candidates),4); table.setHorizontalHeaderLabels(['Unidad','Distancia','Tiempo estimado','Caducidad']); table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); table.setSelectionBehavior(QTableWidget.SelectRows); table.setSelectionMode(QTableWidget.SingleSelection); table.setEditTriggers(QTableWidget.NoEditTriggers)
        for row,candidate in enumerate(candidates):
            values=(label(candidate.get('resource_folio')),label(candidate.get('distance_km'))+' km',label(candidate.get('travel_minutes'))+' min',display_value('expires_at',candidate.get('expires_at')))
            for col,value in enumerate(values): table.setItem(row,col,QTableWidgetItem(value))
        layout.addWidget(table); explanation=QLabel('Selecciona un candidato para consultar su explicación.'); explanation.setWordWrap(True); explanation.setMinimumHeight(76); layout.addWidget(explanation)
        reason=QLineEdit(); reason.setMaxLength(1000); reason.setPlaceholderText('Motivo documentado de la decisión'); layout.addWidget(reason)
        buttons=QHBoxLayout(); favorable=QPushButton('Dictamen favorable'); unfavorable=QPushButton('Dictamen desfavorable'); reserve=QPushButton('Reservar unidad')
        reserve.setToolTip('Requiere un dictamen favorable registrado; el servicio comprobará nuevamente la reserva.')
        reserve.setAccessibleDescription('Requiere un dictamen favorable registrado; el servicio comprobará nuevamente la reserva.')
        validity=evaluation.get('validity') or {}; candidate_validity={entry.get('resource_id'):entry for entry in validity.get('candidates',[]) if isinstance(entry,dict)}
        hint=QLabel(); hint.setWordWrap(True)
        def selection_changed():
            index=table.currentRow(); candidate=candidates[index] if index>=0 else None
            check=candidate_validity.get(candidate.get('resource_id')) if candidate else None
            current=bool(check and check.get('current') is True)
            if candidate:
                text=str(candidate.get('explanation') or 'No hay explicación disponible.')
                text+='\nVigencia comprobada al consultar; el servicio la verificará nuevamente.' if current else '\nLa vigencia no está confirmada. Genera una nueva evaluación antes de decidir.'
                explanation.setText(text)
            else: explanation.setText('Selecciona un candidato para consultar su explicación.')
            review=next((item for item in (evaluation.get('reviews') or []) if candidate and isinstance(item,dict) and item.get('resource_id')==candidate['resource_id']),None)
            for button in (favorable,unfavorable): button.setEnabled(current and review is None)
            reserve.setEnabled(current and bool(review and review.get('decision')=='FAVORABLE'))
            if not candidate: hint.setText('Selecciona un candidato para consultar su dictamen.')
            elif not current: hint.setText('La vigencia no está confirmada. Genera una nueva evaluación antes de decidir.')
            elif review and review.get('decision')=='FAVORABLE': hint.setText('Dictamen favorable registrado. El servicio comprobará la reserva.')
            elif review: hint.setText('Dictamen desfavorable registrado. Esta unidad no puede reservarse con esta evaluación.')
            else: hint.setText('Para reservar, primero registra un dictamen favorable.')
        table.itemSelectionChanged.connect(selection_changed); selection_changed()
        for button,code in ((favorable,1),(unfavorable,2),(reserve,3)):
            button.clicked.connect(lambda _checked=False,c=code:dialog.done(c)); buttons.addWidget(button)
        close=QPushButton('Cerrar'); close.clicked.connect(dialog.reject); buttons.addWidget(close)
        layout.addLayout(buttons)
        layout.addWidget(hint)
        while True:
            choice=dialog.exec()
            if not choice: return
            if table.currentRow()>=0 and len(reason.text().strip())>=6: break
            QMessageBox.warning(self,'Datos incompletos','Selecciona un candidato y documenta un motivo de al menos seis caracteres.')
        candidate=candidates[table.currentRow()]; common={'human_confirmation':'true','reason':reason.text().strip(),'resource_id':candidate['resource_id']}; key=str(uuid.uuid4())
        if choice==3:
            if self.reservation_uncertain:
                self.status.setText('La reserva anterior tiene resultado incierto. No repitas la operación; consulta su estado con soporte autorizado.'); return
            body=dict(common,evaluation_id=evaluation['id']); record={'key':key,'body':body,'state':'PREPARED','operation_id':None,'status':None,'target':{'service':'inventario','path':'/api/v1/reservations','method':'POST','schema':'reservation_create.xsd'}}
            def prepare_reservation(): self.journal.prepare(record); return record
            def ready_reservation(_):
                self.reservation_uncertain=True
                def submit_reservation(proof):
                    result=self.client.authorized('inventario','/api/v1/reservations','reservation_create',method='POST',body=body,request_schema='reservation_create.xsd',key=key,proof=proof)
                    validate_operation(record,result); self.journal.update(key,result); return result
                self.secure_attempt(record,'reservation_create',candidate['resource_id'],submit_reservation,self.reservation_result)
            self.run(prepare_reservation,ready_reservation,'Preparando reserva…')
        else:
            body=dict(common,decision='FAVORABLE' if choice==1 else 'UNFAVORABLE')
            self.secure_command('evaluation_review',evaluation['id'],body)

    def reservation_result(self,data):
        self.reservation_uncertain=False; self.last_operation=data['operation_id']; self.last_operation_status=data.get('status')
        self.operation_button.setEnabled(True); self.resume_button.setEnabled(data.get('status') in ('PENDING','ROLLBACK_PENDING'))
        self.resume_button.setVisible(self.mode in ('pending','reservations') and data.get('status') in ('PENDING','ROLLBACK_PENDING'))
        state=data.get('status')
        if state=='COMPLETED' and data.get('reservation'):
            message='Reserva confirmada. Puedes consultar el estado en Reservas.'
        elif state=='FAILED': message='La reserva no se completó. Consulta la operación para revisar el estado.'
        else: message='La reserva está pendiente de confirmación. Consulta la operación antes de intentar otra.'
        QMessageBox.information(self,'Estado de la reserva',message+'\nReferencia de operación: '+self.last_operation)
        self.status.setText(message)

    def resume_operation(self):
        if not self.journal or not self.last_operation: return
        self.run(self.journal.list,self.resume_pending,'Consultando operación…')

    def resume_pending(self,records):
        record=next((r for r in records if r.get('operation_id')==self.last_operation and r['state']=='PENDING' and r.get('kind','RESERVATION')=='RESERVATION'),None)
        if not record: self.status.setText('No hay una reserva pendiente para reanudar.'); return
        if QMessageBox.question(self,'Reanudar reserva','¿Reanudar la operación pendiente?') != QMessageBox.Yes: return
        def resume():
            result=self.client.authorized('inventario','/api/v1/operations/'+record['operation_id']+'/resume','operation_resume',method='POST',key=record['key'])
            validate_operation(record,result); self.journal.update(record['key'],result); return result
        self.run(resume,self.reservation_result,'Reanudando reserva…')

    def check_operation(self):
        if not self.journal: self.status.setText('Inicia sesión para recuperar operaciones.'); return
        self.run(self.journal.list,self.recover_operation,'Buscando operaciones…')

    def recover_operation(self,records):
        pending=[r for r in records if r['state']!='DONE']
        if not pending:
            self.status.setText('No hay operaciones pendientes para esta cuenta.'); return
        record=pending[-1]
        if record.get('kind')=='USER_CREATE': self.recover_user(record); return
        if record.get('kind')=='COMMAND':
            if record.get('status')=='CONFLICT':
                if record['target']['operation']=='shipment_create':
                    if QMessageBox.question(self,'Revisar planificación','El resultado anterior requiere revisión. ¿Consultar la reserva sin enviar otra planificación?') != QMessageBox.Yes: return
                    def inspect_reservation():
                        reservation=self.client.authorized('inventario','/api/v1/reservations/'+record['body']['reservation_id'],'reservation_detail',fresh_identity=True)
                        if reservation['id']!=record['body']['reservation_id']: raise ContractError('La reserva consultada no corresponde al intento.')
                        shipment_id=reservation.get('shipment_id')
                        if not shipment_id: return None
                        shipment=self.client.authorized('transporte','/api/v1/shipments/'+shipment_id,'shipment_detail',fresh_identity=True)
                        if shipment['id']!=shipment_id or shipment.get('reservation_id')!=reservation['id']: raise ContractError('El traslado consultado no corresponde a la reserva.')
                        return shipment
                    def show_inspection(shipment):
                        if not shipment:
                            message='La reserva no muestra un traslado vinculado. Esto no confirma el resultado anterior; solicita revisión autorizada.'
                        else:
                            account='La cuenta de traslado coincide con la seleccionada.' if shipment.get('transport_user_id')==record['body']['transport_user_id'] else 'La cuenta de traslado es distinta de la seleccionada.'
                            message='Traslado vinculado: '+label(shipment.get('status'))+'. '+account+' La consulta no demuestra que corresponda al intento anterior. Solicita revisión autorizada.'
                        QMessageBox.information(self,'Revisión de planificación',message)
                        self.status.setText('La operación sigue pendiente de revisión; no se envió otra planificación.')
                    self.run(inspect_reservation,show_inspection,'Consultando reserva…'); return
                self.status.setText('La operación requiere revisión autorizada antes de continuar.'); return
            if record['target']['operation']=='shipment_create' and record.get('operation_id'):
                def poll_shipment():
                    result=self.client.authorized('transporte','/api/v1/shipments/'+record['operation_id'],'shipment_detail',fresh_identity=True)
                    outcome=update_shipment_command(self.journal,record,result)
                    return result,outcome
                self.run(poll_shipment,lambda value:self.shipment_plan_result(value[0]),'Consultando traslado…'); return
            if QMessageBox.question(self,'Recuperar operación','La respuesta anterior no llegó. ¿Recuperar el mismo intento?') != QMessageBox.Yes: return
            operation=record['target']['operation']; identifier=record['target']['identifier']
            callback=self.shipment_plan_result if operation=='shipment_create' else lambda _:self.received()
            self.secure_attempt(record,operation,identifier,lambda proof:submit_command(self.client,self.journal,record,proof=proof),callback)
            return
        if record.get('kind')=='LABEL':
            if not LABEL_ISSUANCE_ENABLED: self.status.setText('La recuperación de etiqueta aún no está disponible.'); return
            if record.get('status')=='PRINT_UNCERTAIN':
                message=('No se sabe si la impresora recibió la solicitud. Revisa la impresora y las copias existentes. '
                         'Al cerrar esta revisión no se enviará otra copia; una nueva impresión requiere una nueva emisión autorizada. ¿Ya revisaste?')
                if QMessageBox.question(self,'Revisar impresión',message)!=QMessageBox.Yes: return
                self.run(lambda:self.journal.print_transition(record['key'],record['operation_id'],'review'),
                         lambda _:self.status.setText('Revisión registrada. Para otra copia solicita una nueva emisión.'),
                         'Registrando revisión…')
                return
            if QMessageBox.question(self,'Recuperar etiqueta','¿Continuar la emisión pendiente?') != QMessageBox.Yes: return
            def recover_label():
                result=submit_label(self.client,self.journal,record) if record['state']=='UNCERTAIN' else None
                resource=self.client.authorized('inventario','/api/v1/resources/'+record['target'],'resource_detail')
                if resource['version']!=record['body']['version']: raise JournalError('La unidad cambió. Solicita revisión antes de emitir la etiqueta.')
                return resource,result['issuance_id'] if result else record['operation_id']
            self.run(recover_label,lambda pair:self.label_authorized(pair[0],record,pair[1]),'Recuperando etiqueta…'); return
        if record.get('kind','RESERVATION')!='RESERVATION':
            self.status.setText('La operación pendiente requiere revisión autorizada.'); return
        if record.get('target') and record['target']!={'service':'inventario','path':'/api/v1/reservations','method':'POST','schema':'reservation_create.xsd'}:
            self.status.setText('El contrato de la reserva pendiente cambió; solicita revisión.'); return
        operation_id=record.get('operation_id'); key=record['key']
        if operation_id:
            def poll():
                result=self.client.authorized('inventario','/api/v1/operations/'+operation_id,'operation_detail',fresh_identity=True)
                validate_operation(record,result); self.journal.update(key,result); return result
            self.run(poll,self.reservation_result,'Consultando operación…'); return
        if QMessageBox.question(self,'Recuperar reserva','La respuesta anterior no llegó. ¿Recuperar la solicitud sin duplicarla?') != QMessageBox.Yes: return
        def retry(proof):
            result=self.client.authorized('inventario','/api/v1/reservations','reservation_create',method='POST',body=record['body'],request_schema='reservation_create.xsd',key=key,proof=proof)
            validate_operation(record,result); self.journal.update(key,result); return result
        self.secure_attempt(record,'reservation_create',record['body']['resource_id'],retry,self.reservation_result)

    def create_donation(self):
        if self.uncertain:
            self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='MEDICAL':
            self.status.setText('El registro de colecta corresponde al personal médico.'); return
        client=self.client; actor=(client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))
        body=collect_dialog(self,Work)
        if not body: return
        if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
            self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
        self.secure_command('donation_create',None,body)

    def process_donation(self):
        if self.uncertain:
            self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='OPERATOR':
            self.status.setText('El procesamiento corresponde al personal operador.'); return
        client=self.client; actor=(client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))
        chosen=select_processed_donation(self,Work,label,status='COLLECTED')
        if not chosen: return
        if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
            self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
        def fetch():
            result=client.authorized('donantes','/api/v1/donations/'+chosen['id'],'donation_detail',fresh_identity=True)
            if result.get('id')!=chosen['id'] or result.get('donor_id')!=chosen['donor_id'] or result.get('tenant_id')!=actor[1]:
                raise ContractError('La colecta no corresponde a la selección.')
            return dict(result,_donor_folio=chosen['_donor_folio'],_donor_name=chosen['_donor_name'])
        def ready(item):
            if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
                self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
            if item.get('status')!='COLLECTED':
                self.status.setText('La colecta ya fue atendida. Actualiza la lista.'); return
            body=processing_dialog(self,item)
            if not body: return
            if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
                self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
            self.secure_command('donation_step',item['id'],body)
        self.run(fetch,ready,'Consultando colecta…')

    def catalogue_action(self, edit):
        if self.uncertain:
            self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if self.mode not in ('sites','capacities') or not self.client or not self.client.user or self.client.user.get('role')!='ADMIN':
            self.status.setText('Esta operación corresponde a administración.'); return
        item=self.selected() if edit else None
        if edit and not item:
            self.status.setText('Selecciona una fila para corregir.'); return
        client=self.client; actor=(client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))
        kind=self.mode; identifier=item['id'] if item else None
        body=catalogue_dialog(self,kind,item)
        if not body: return
        if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
            self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
        self.secure_command(kind+('_edit' if edit else '_create'),identifier,body)

    def fractionate_resource(self):
        if self.uncertain:
            self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='OPERATOR':
            self.status.setText('El procesamiento corresponde al personal operador autorizado.'); return
        item=self.selected()
        if not item:
            self.status.setText('Selecciona una unidad.'); return
        client=self.client; actor=(client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))
        def ready(resource):
            if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
                self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
            if resource.get('id')!=item['id']:
                self.status.setText('La unidad consultada no corresponde a la selección.'); return
            if resource.get('status')!='QUARANTINE' or resource.get('kind')!='BLOOD' or not resource.get('donation_id'):
                self.status.setText('Selecciona una unidad sanguínea trazable en cuarentena.'); return
            body=fractionation_dialog(self,resource)
            if not body: return
            if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
                self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
            self.secure_command('resource_fractionate',resource['id'],body)
        self.run(lambda:client.authorized('inventario','/api/v1/resources/'+item['id'],'resource_detail'),ready,'Consultando unidad…')

    def edit_resource(self):
        if self.uncertain:
            self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='OPERATOR':
            self.status.setText('La corrección corresponde al personal operador autorizado.'); return
        item=self.selected()
        if not item:
            self.status.setText('Selecciona una unidad.'); return
        if item.get('status')!='QUARANTINE':
            self.status.setText('Solo se puede corregir una unidad en cuarentena.'); return
        client=self.client; actor=(client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))
        def fetch():
            resource=client.authorized('inventario','/api/v1/resources/'+item['id'],'resource_detail')
            required=('id','folio','kind','component','blood_group','expires_at','collected_at','location_id','donation_id','version','status')
            if any(key not in resource for key in required) or resource['id']!=item['id']:
                raise ContractError('No se recibieron todos los datos necesarios para conservar la unidad.')
            name='Sin ubicación registrada'
            if resource['location_id']:
                location=client.authorized('identidad-acceso','/api/v1/catalogues/locations/'+resource['location_id'],'locations_detail')
                if location['id']!=resource['location_id']: raise ContractError('La ubicación no corresponde a la unidad.')
                name=location['name']+(' · Inactiva' if not location['active'] else '')
            return resource,name
        def ready(result):
            if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
                self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
            resource,name=result
            if resource['status']!='QUARANTINE':
                self.status.setText('La unidad ya no está en cuarentena. Actualiza la lista.'); return
            body=resource_edit_dialog(self,resource,name,Work,label)
            if not body: return
            if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
                self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
            self.secure_command('resource_edit',resource['id'],body)
        self.run(fetch,ready,'Consultando unidad…')

    def create_resource(self):
        if self.uncertain: self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='OPERATOR':
            self.status.setText('El registro corresponde al personal operador autorizado.'); return
        client=self.client; actor=(client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))
        dialog=QDialog(self); dialog.setWindowTitle('Registrar unidad u oferta'); dialog.resize(620,420); form=QFormLayout(dialog)
        folio=QLineEdit(); folio.setMaxLength(30); form.addRow('Folio de unidad',folio)
        kind=QComboBox(); kind.addItem('Selecciona un tipo',''); kind.addItem('Sangre','BLOOD'); kind.addItem('Órgano','ORGAN'); form.addRow('Tipo de recurso',kind)
        component=QComboBox(); component.addItem('Selecciona un tipo primero',''); form.addRow('Producto u órgano',component)
        def choose_kind():
            component.clear(); component.addItem('Selecciona una opción','')
            choices=(('Eritrocitos','RBC'),('Plasma','PLASMA'),('Plaquetas','PLATELETS')) if kind.currentData()=='BLOOD' else (('Riñón','KIDNEY'),('Hígado','LIVER'),('Corazón','HEART')) if kind.currentData()=='ORGAN' else ()
            for name,code in choices: component.addItem(name,code)
        kind.currentIndexChanged.connect(choose_kind)
        group=QComboBox(); group.addItem('Selecciona un grupo', '');
        for blood_group in ('O-','O+','A-','A+','B-','B+','AB-','AB+'): group.addItem(blood_group,blood_group)
        form.addRow('Grupo sanguíneo',group)
        has_collection=QCheckBox('Registrar fecha documentada de obtención o colecta'); form.addRow(has_collection)
        collected=QDateTimeEdit(QDateTime.currentDateTime()); collected.setCalendarPopup(True); collected.setDisplayFormat('dd/MM/yyyy HH:mm'); collected.setEnabled(False); has_collection.toggled.connect(collected.setEnabled); form.addRow('Obtención o colecta',collected)
        source={'row':None}
        source_name=QLabel('Sin donación vinculada'); source_name.setWordWrap(True); form.addRow('Procedencia',source_name)
        source_ref=QLineEdit(); source_ref.setReadOnly(True); source_ref.setAccessibleName('Referencia completa de la donación vinculada'); form.addRow('Referencia de donación',source_ref)
        source_actions=QHBoxLayout(); select_source=QPushButton('Seleccionar donación'); clear_source=QPushButton('Quitar donación'); clear_source.setEnabled(False); source_actions.addWidget(select_source); source_actions.addWidget(clear_source); form.addRow(source_actions)
        def choose_source():
            row=select_processed_donation(self,Work,label)
            if not row: return
            parsed=QDateTime.fromString(row['collected_at'],Qt.ISODate)
            if row.get('component') not in ('RBC','PLASMA','PLATELETS') or group.findData(row.get('blood_group'))<0 or not parsed.isValid():
                QMessageBox.warning(dialog,'Donación no disponible','Los datos de esta donación no se pueden usar en este formulario. Solicita revisión.'); return
            kind.setCurrentIndex(kind.findData('BLOOD'))
            component.setCurrentIndex(component.findData(row['component']))
            group.setCurrentIndex(group.findData(row['blood_group']))
            has_collection.setChecked(True); collected.setDateTime(parsed.toLocalTime())
            for widget in (kind,component,group,has_collection,collected): widget.setEnabled(False)
            source['row']=row; source_ref.setText(row['id']); source_name.setText(row['_donor_folio']+' · '+row['_donor_name']); clear_source.setEnabled(True)
        def clear_source_selection():
            source['row']=None; source_ref.clear(); source_name.setText('Sin donación vinculada'); clear_source.setEnabled(False)
            for widget in (kind,component,group,has_collection): widget.setEnabled(True)
            collected.setEnabled(has_collection.isChecked())
            kind.setCurrentIndex(0); group.setCurrentIndex(0); has_collection.setChecked(False)
        select_source.clicked.connect(choose_source); clear_source.clicked.connect(clear_source_selection)
        expiry=QDateTimeEdit(QDateTime.currentDateTime()); expiry.setCalendarPopup(True); expiry.setDisplayFormat('dd/MM/yyyy HH:mm'); form.addRow('Caducidad',expiry)
        confirm_expiry=QCheckBox('Confirmo que la caducidad coincide con el documento de la unidad.'); form.addRow(confirm_expiry)
        note=QLabel('La unidad ingresará en cuarentena.'); note.setWordWrap(True); form.addRow(note)
        confirm=QPushButton('Registrar unidad'); confirm.clicked.connect(dialog.accept); form.addRow(confirm)
        while dialog.exec()==QDialog.Accepted:
            if re.fullmatch(r'[A-Za-z0-9_-]{6,30}',folio.text().strip()) and kind.currentData() and component.currentData() and group.currentData() and confirm_expiry.isChecked(): break
            QMessageBox.warning(self,'Datos incompletos','Indica folio, tipo, producto y grupo; confirma la caducidad documentada.')
        else: return
        body={'folio':folio.text().strip(),'kind':kind.currentData(),'component':component.currentData(),'blood_group':group.currentData(),'expires_at':expiry.dateTime().toUTC().toString(Qt.ISODate)}
        if self.client is not client or not client.user or (client.user.get('id'),client.user.get('tenant_id'),client.user.get('role'))!=actor:
            self.status.setText('La sesión cambió. Vuelve a consultar antes de guardar.'); return
        if source['row']:
            body['donation_id']=source['row']['id']; body['collected_at']=source['row']['collected_at']
        elif has_collection.isChecked(): body['collected_at']=collected.dateTime().toUTC().toString(Qt.ISODate)
        self.run(lambda:self.durable('resource_create',None,body),lambda _:self.received(),'Registrando unidad…')

    def create_recipient(self):
        if not self.client or not self.client.user or self.client.user.get('role')!='MEDICAL': self.status.setText('El registro corresponde al personal médico.'); return
        if self.uncertain: self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        self.recipient_form(None)

    def edit_recipient(self):
        item=self.selected()
        if not item: self.status.setText('Selecciona un receptor.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='MEDICAL': self.status.setText('La corrección corresponde al personal médico.'); return
        if self.uncertain: self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        self.run(lambda:self.client.authorized('receptores','/api/v1/recipients/'+item['id'],'recipient_detail'),self.recipient_form,'Consultando expediente…')

    def recipient_form(self,item):
        if item and not item.get('can_edit'):
            self.status.setText('El expediente ya tiene solicitudes y no admite esta corrección.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Corregir receptor' if item else 'Registrar receptor'); dialog.resize(600,530); form=QFormLayout(dialog)
        folio=QLineEdit(); folio.setMaxLength(30); form.addRow('Folio',folio)
        name=QLineEdit(); name.setMaxLength(200); form.addRow('Nombre documentado',name)
        kind=QComboBox(); kind.addItem('Selecciona un tipo',''); kind.addItem('Sangre','BLOOD'); kind.addItem('Órgano','ORGAN'); form.addRow('Tipo de recurso',kind)
        organ=QComboBox(); organ.addItem('Selecciona un órgano','')
        for title,code in (('Riñón','KIDNEY'),('Hígado','LIVER'),('Corazón','HEART')): organ.addItem(title,code)
        form.addRow('Órgano solicitado',organ)
        def choose_kind():
            organ.setCurrentIndex(0); form.setRowVisible(organ,kind.currentData()=='ORGAN')
        kind.currentIndexChanged.connect(choose_kind); choose_kind()
        group=QComboBox(); group.addItem('Selecciona un grupo','')
        for value in ('O-','O+','A-','A+','B-','B+','AB-','AB+'): group.addItem(value,value)
        form.addRow('Grupo sanguíneo documentado',group)
        studies=QLineEdit(); studies.setMaxLength(1000); form.addRow('Estudios documentados',studies)
        restrictions=QLineEdit(); restrictions.setMaxLength(1000); form.addRow('Restricciones documentadas · opcional',restrictions)
        requirement=QLineEdit(); requirement.setMaxLength(1000); form.addRow('Necesidad documentada · opcional',requirement)
        state=QComboBox(); state.addItem('Activo','ACTIVE'); state.addItem('Inactivo','INACTIVE')
        if item: form.addRow('Estado',state)
        reason=QLineEdit(); reason.setMaxLength(1000)
        confirmation=QCheckBox('Confirmo la corrección documentada.')
        if item:
            form.addRow('Motivo de corrección',reason); form.addRow(confirmation)
            folio.setText(item['folio']); name.setText(item['display_name']); kind.setCurrentIndex(max(0,kind.findData(item['kind']))); organ.setCurrentIndex(max(0,organ.findData(item.get('organ_type')))); group.setCurrentIndex(max(0,group.findData(item['blood_group']))); studies.setText(item.get('studies') or ''); restrictions.setText(item.get('restrictions') or ''); requirement.setText(item.get('requirement') or ''); state.setCurrentIndex(max(0,state.findData(item['status'])))
        note=QLabel('La información se conserva según el expediente autorizado; la corrección requiere versión vigente.'); note.setWordWrap(True); form.addRow(note)
        save=QPushButton('Guardar corrección' if item else 'Registrar receptor'); save.clicked.connect(dialog.accept); form.addRow(save)
        while dialog.exec()==QDialog.Accepted:
            optional=[restrictions.text().strip(),requirement.text().strip()]
            if re.fullmatch(r'[A-Za-z0-9_-]{6,30}',folio.text().strip()) and name.text().strip() and kind.currentData() and group.currentData() and len(studies.text().strip())>=6 and all(not x or len(x)>=6 for x in optional) and (kind.currentData()!='ORGAN' or organ.currentData()) and (not item or (len(reason.text().strip())>=6 and confirmation.isChecked())): break
            QMessageBox.warning(dialog,'Datos incompletos','Verifica folio, nombre, tipo, grupo y estudios; confirma el motivo si corriges.')
        else: return
        body={'folio':folio.text().strip(),'display_name':name.text().strip(),'kind':kind.currentData(),'blood_group':group.currentData(),'studies':studies.text().strip()}
        if kind.currentData()=='ORGAN': body['organ_type']=organ.currentData()
        if restrictions.text().strip(): body['restrictions']=restrictions.text().strip()
        if requirement.text().strip(): body['requirement']=requirement.text().strip()
        if item: body.update(status=state.currentData(),version=item['version'],reason=reason.text().strip(),human_confirmation='true')
        self.secure_command('recipient_edit' if item else 'recipient_create',item['id'] if item else None,body)

    def edit_request(self):
        item=self.selected()
        if not item: self.status.setText('Selecciona una solicitud.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='MEDICAL': self.status.setText('La edición corresponde al personal médico.'); return
        if self.uncertain: self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        def fetch():
            request=self.client.authorized('receptores','/api/v1/requests/'+item['id'],'request_detail')
            person=self.client.authorized('receptores','/api/v1/recipients/'+request['recipient_id'],'recipient_detail')
            return request,person
        self.run(fetch,lambda pair:self.request_edit_form(*pair),'Consultando solicitud…')

    def request_edit_form(self,item,person):
        if not item.get('can_edit'):
            self.status.setText('La solicitud no admite edición: consulta sus retenciones o estado.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Editar solicitud'); form=QFormLayout(dialog)
        component=QComboBox()
        choices=(('Eritrocitos','RBC'),('Plasma','PLASMA'),('Plaquetas','PLATELETS')) if item['kind']=='BLOOD' else ((label(person['organ_type']),person['organ_type']),)
        for title,code in choices: component.addItem(title,code)
        component.setCurrentIndex(max(0,component.findData(item['component']))); form.addRow('Recurso solicitado',component)
        quantity=QSpinBox(); quantity.setRange(1,1 if item['kind']=='ORGAN' else 100); quantity.setValue(item['quantity']); form.addRow('Cantidad',quantity)
        urgency=QComboBox()
        for number in (1,2,3): urgency.addItem(str(number),number)
        urgency.setCurrentIndex(max(0,urgency.findData(item['urgency']))); form.addRow('Urgencia documentada',urgency)
        reason=QLineEdit(); reason.setMaxLength(1000); form.addRow('Motivo de corrección',reason)
        confirm=QCheckBox('Confirmo la corrección; las evaluaciones anteriores deberán revisarse.'); form.addRow(confirm)
        save=QPushButton('Guardar corrección'); save.clicked.connect(dialog.accept); form.addRow(save)
        while dialog.exec()==QDialog.Accepted:
            if len(reason.text().strip())>=6 and confirm.isChecked(): break
            QMessageBox.warning(dialog,'Datos incompletos','Documenta el motivo y confirma la corrección.')
        else: return
        body={'component':component.currentData(),'quantity':quantity.value(),'urgency':urgency.currentData(),'version':item['version'],'reason':reason.text().strip(),'human_confirmation':'true'}
        self.secure_command('request_edit',item['id'],body)

    def cancel_request(self):
        item=self.selected()
        if not item: self.status.setText('Selecciona una solicitud.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='MEDICAL': self.status.setText('La cancelación corresponde al personal médico.'); return
        if self.uncertain: self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        self.run(lambda:self.client.authorized('receptores','/api/v1/requests/'+item['id'],'request_detail'),self.request_cancel_form,'Consultando solicitud…')

    def request_cancel_form(self,item):
        if item.get('status') not in ('OPEN','IN_PROGRESS'):
            self.status.setText('La solicitud ya no admite cancelación.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Cancelar solicitud'); dialog.resize(560,230); form=QFormLayout(dialog)
        note=QLabel('El servicio comprobará que no existan retenciones ni reservas pendientes.'); note.setWordWrap(True); form.addRow(note)
        reason=QLineEdit(); reason.setMaxLength(1000); form.addRow('Motivo documentado',reason)
        confirm=QCheckBox('Confirmo la cancelación de esta solicitud.'); form.addRow(confirm)
        save=QPushButton('Confirmar cancelación'); save.clicked.connect(dialog.accept); form.addRow(save)
        while dialog.exec()==QDialog.Accepted:
            if len(reason.text().strip())>=6 and confirm.isChecked(): break
            QMessageBox.warning(dialog,'Datos incompletos','Documenta el motivo y confirma la cancelación.')
        else: return
        self.secure_command('request_cancel',item['id'],{'version':item['version'],'reason':reason.text().strip(),'human_confirmation':'true'})

    def create_sample(self):
        if self.uncertain:
            self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if not self.client or not self.client.user or self.client.user.get('role') not in ('OPERATOR','MEDICAL'):
            self.status.setText('El registro corresponde al personal de laboratorio autorizado.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Registrar muestra de unidad'); dialog.resize(760,620); layout=QVBoxLayout(dialog)
        guidance=QLabel('Selecciona la unidad y el perfil documentado. El servicio comprobará su vigencia y correspondencia.'); guidance.setWordWrap(True); layout.addWidget(guidance)
        search_row=QHBoxLayout(); search=QLineEdit(); search.setPlaceholderText('Buscar unidad por folio'); search_row.addWidget(search); find=QPushButton('Buscar unidad'); search_row.addWidget(find); layout.addLayout(search_row)
        panels={}
        for key,title,headers in (('unit','Unidad',['Folio','Producto','Estado']),('profile','Perfil de laboratorio',['Nombre','Producto','Versión'])):
            layout.addWidget(QLabel(title)); table=QTableWidget(0,3); table.setAccessibleName(title); table.setHorizontalHeaderLabels(headers); table.setSelectionBehavior(QTableWidget.SelectRows); table.setSelectionMode(QTableWidget.SingleSelection); table.setEditTriggers(QTableWidget.NoEditTriggers); table.verticalHeader().hide(); table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(table,1)
            nav=QHBoxLayout(); previous=QPushButton('Anterior'); following=QPushButton('Siguiente'); previous.setAccessibleName('Página anterior de '+title.lower()); following.setAccessibleName('Página siguiente de '+title.lower()); page=QLabel(); nav.addWidget(previous); nav.addWidget(page); nav.addWidget(following); nav.addStretch(); layout.addLayout(nav)
            panels[key]={'table':table,'previous':previous,'following':following,'page_label':page,'page':1,'total':0,'rows':[],'busy':False}
        fields=QFormLayout(); identifier=QLineEdit(); identifier.setMaxLength(200); fields.addRow('Identificador de la muestra',identifier)
        collected=QDateTimeEdit(QDateTime.currentDateTime()); collected.setCalendarPopup(True); collected.setDisplayFormat('dd/MM/yyyy HH:mm:ss'); fields.addRow('Fecha documentada de colecta · hora local',collected)
        confirm_date=QCheckBox('Confirmo la fecha y hora documentadas.'); fields.addRow(confirm_date); layout.addLayout(fields)
        status=QLabel(''); status.setWordWrap(True); layout.addWidget(status)
        controls=QHBoxLayout(); save=QPushButton('Registrar muestra'); cancel=QPushButton('Cancelar'); controls.addWidget(save); controls.addWidget(cancel); layout.addLayout(controls)
        state={'alive':True,'body':None}
        def selection(key):
            panel=panels[key]; index=panel['table'].currentRow()
            return panel['rows'][index] if 0<=index<len(panel['rows']) else None
        def ready():
            save.setEnabled(not any(p['busy'] for p in panels.values()) and bool(selection('unit')) and bool(selection('profile')))
            if save.isEnabled(): status.setText('Unidad y perfil seleccionados. Confirma la fecha documentada.')
        def fetch(key,page):
            panel=panels[key]
            if panel['busy']: return
            panel.update(busy=True,rows=[]); panel['table'].setRowCount(0); panel['previous'].setEnabled(False); panel['following'].setEnabled(False); ready(); status.setText('Consultando '+('unidades' if key=='unit' else 'perfiles')+'…')
            service,path,operation=('inventario','/api/v1/resources','resources_list') if key=='unit' else ('compatibilidad','/api/v1/laboratory/profiles','lab_profiles_list')
            params={'page':page,'page_size':20}
            if key=='unit' and search.text().strip(): params['q']=search.text().strip()
            worker=Work(lambda:self.client.authorized(service,path,operation,params=params))
            if not hasattr(self,'_request_workers'): self._request_workers=[]
            self._request_workers.append(worker)
            def done(data):
                self._request_workers.remove(worker)
                if not state['alive']: return
                panel.update(page=data['page'],total=data['total'],rows=data['items'],busy=False); table=panel['table']; table.setRowCount(len(panel['rows']))
                for index,row in enumerate(panel['rows']):
                    values=(row.get('folio'),row.get('component'),row.get('status')) if key=='unit' else (row.get('name'),row.get('component'),row.get('version'))
                    for column,value in enumerate(values): table.setItem(index,column,QTableWidgetItem(label(value)))
                panel['page_label'].setText('Página '+str(panel['page'])+' · '+str(panel['total'])+(' registro' if panel['total']==1 else ' registros')); panel['previous'].setEnabled(panel['page']>1); panel['following'].setEnabled(panel['page']*20<panel['total']); status.setText('Selecciona unidad y perfil.' if panel['rows'] else 'No hay '+('unidades' if key=='unit' else 'perfiles')+' para mostrar.'); ready()
            def failed(error):
                self._request_workers.remove(worker)
                if not state['alive']: return
                panel['busy']=False; status.setText('No se pudieron consultar '+('las unidades' if key=='unit' else 'los perfiles')+'. Vuelve a intentar.'); ready()
            worker.signals.done.connect(done); worker.signals.failed.connect(failed); self.pool.start(worker)
        for key,panel in panels.items():
            panel['table'].itemSelectionChanged.connect(ready); panel['previous'].clicked.connect(lambda _=False,k=key:fetch(k,panels[k]['page']-1)); panel['following'].clicked.connect(lambda _=False,k=key:fetch(k,panels[k]['page']+1))
        find.clicked.connect(lambda:fetch('unit',1)); search.returnPressed.connect(lambda:fetch('unit',1)); cancel.clicked.connect(dialog.reject)
        def submit():
            unit=selection('unit'); profile=selection('profile')
            if not unit or not profile or not identifier.text().strip() or not confirm_date.isChecked():
                QMessageBox.warning(dialog,'Datos incompletos','Selecciona unidad y perfil; escribe el identificador y confirma la fecha documentada.'); return
            state['body']={'resource_id':unit['id'],'profile_id':profile['id'],'identifier':identifier.text().strip(),'collected_at':collected.dateTime().toUTC().toString(Qt.ISODate)}; dialog.accept()
        save.clicked.connect(submit); ready(); QTimer.singleShot(0,lambda:fetch('unit',1)); QTimer.singleShot(0,lambda:fetch('profile',1))
        accepted=dialog.exec(); state['alive']=False
        if accepted==QDialog.Accepted and state['body']:
            self.secure_command('lab_sample_create',None,state['body'])

    def capture_result(self):
        item=self.selected()
        if self.uncertain: self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if not self.client or not self.client.user or self.client.user.get('role') not in ('OPERATOR','MEDICAL'): self.status.setText('La captura requiere personal autorizado.'); return
        if not item: self.status.setText('Selecciona una muestra.'); return
        if item.get('status')!='RECEIVED': self.status.setText('Selecciona una muestra recibida antes de capturar el resultado.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Capturar resultado'); dialog.resize(540,380); form=QFormLayout(dialog)
        form.addRow('Muestra',QLabel(item['identifier'])); fields={}
        for key,title in [('test_code','Código de prueba'),('value','Resultado'),('method','Método'),('laboratory','Laboratorio'),('reference','Referencia')]:
            fields[key]=QLineEdit(); fields[key].setMaxLength(60 if key=='test_code' else 2000 if key=='value' else 200); form.addRow(title,fields[key])
        measured=QDateTimeEdit(QDateTime.currentDateTime()); measured.setCalendarPopup(True); measured.setDisplayFormat('dd/MM/yyyy HH:mm:ss'); form.addRow('Medición documentada (hora local)',measured)
        verified=QCheckBox('Confirmo la fecha de medición documentada.'); form.addRow(verified)
        confirm=QPushButton('Registrar resultado'); confirm.clicked.connect(dialog.accept); form.addRow(confirm)
        while dialog.exec()==QDialog.Accepted:
            values={k:v.text().strip() for k,v in fields.items()}
            if all(values.values()) and verified.isChecked() and re.fullmatch(r'[A-Z0-9_.-]{1,60}',values['test_code']): break
            QMessageBox.warning(self,'Datos incompletos','Completa los campos y confirma la fecha documentada. El código de prueba usa letras mayúsculas, números, punto, guion o guion bajo.')
        else: return
        body=dict(values,sample_id=item['id'],measured_at=measured.dateTime().toUTC().toString(Qt.ISODate)); key=str(uuid.uuid4())
        self.run(lambda:self.durable('lab_result_create',None,body),lambda _:self.received(),'Registrando resultado…')

    def review_result(self):
        item=self.selected()
        if self.uncertain: self.status.setText('Actualiza y verifica el estado antes de continuar.'); return
        if not item: self.status.setText('Selecciona un resultado.'); return
        if not self.client or not self.client.user or self.client.user.get('role')!='MEDICAL': self.status.setText('La revisión corresponde al personal médico autorizado.'); return
        if item.get('status')!='CAPTURED': self.status.setText('El resultado ya fue revisado o no está disponible para revisión.'); return
        dialog=QDialog(self); dialog.setWindowTitle('Revisión profesional'); dialog.resize(540,300); form=QFormLayout(dialog)
        form.addRow('Prueba',QLabel(label(item.get('test_code')))); result_label=QLabel(label(item.get('value'))); result_label.setWordWrap(True); form.addRow('Resultado',result_label)
        for key,title in (('method','Método'),('laboratory','Laboratorio'),('reference','Referencia')):
            if item.get(key):
                detail=QLabel(label(item[key])); detail.setWordWrap(True); form.addRow(title,detail)
        decision=QComboBox(); decision.addItem('Selecciona una decisión',''); decision.addItem('Autorizar','AUTHORIZED'); decision.addItem('Rechazar','REJECTED'); form.addRow('Decisión',decision)
        reason=QLineEdit(); reason.setMaxLength(1000); form.addRow('Motivo de revisión',reason)
        confirm=QPushButton('Registrar revisión'); confirm.clicked.connect(dialog.accept); form.addRow(confirm)
        while dialog.exec()==QDialog.Accepted:
            if decision.currentData() and len(reason.text().strip())>=6: break
            QMessageBox.warning(self,'Datos incompletos','Selecciona una decisión y escribe un motivo de al menos seis caracteres.')
        else: return
        body={'human_confirmation':'true','reason':reason.text().strip(),'version':item['version'],'decision':decision.currentData()}; key=str(uuid.uuid4())
        self.secure_command('lab_result_review',item['id'],body)

    def acknowledge(self):
        item=self.selected()
        if self.uncertain: self.status.setText('Actualiza la lista y verifica el estado antes de continuar.'); return
        if not item: self.status.setText('Selecciona un aviso.'); return
        if item.get('status') in ('ACKNOWLEDGED','CLOSED'): self.status.setText('El aviso ya fue atendido.'); return
        if QMessageBox.question(self,'Acusar recibo','¿Confirmas que leíste este aviso?') != QMessageBox.Yes: return
        key=str(uuid.uuid4())
        self.run(lambda:self.durable('alert_ack',item['id'],None),lambda _:self.received(),'Registrando acuse…')

    def received(self):
        self.load(); self.status.setText('Operación confirmada por el servicio.')

    def closeEvent(self,event):
        if self.tracking: self.tracking.stop(); self.tracking=None
        if self.closing: event.accept(); return
        if self.busy: event.ignore(); self.status.setText('Espera a que termine la operación.'); return
        if not self.client or not self.client.access: event.accept(); return
        event.ignore(); client=self.client
        def close_session():
            try: client.logout(); return True
            except Exception: return False
        def finish_close(revoked):
            if not revoked: QMessageBox.warning(self,'Cierre de sesión','No fue posible confirmar el cierre en el servidor. La sesión local se eliminó.')
            self.closing=True; self.close()
        self.run(close_session,finish_close,'Cerrando sesión…')

def smoke_report(target):
    """Comprueba arranque y recursos empaquetados sin sesión ni red."""
    import json
    from .client import CONTRACTS, decode, request_xml

    app=QApplication.instance() or QApplication(['RedHouse'])
    app.setOrganizationName('RedHouse'); app.setApplicationName('Consola'); app.setStyleSheet(STYLE)
    window=Window(); window.show(); app.processEvents()
    request_xml({'username':'synthetic','password':'synthetic-password'},'login.xsd')
    spec=json.loads((CONTRACTS/'identidad.json').read_text())
    sample=spec['paths']['/api/v1/auth/login']['post']['responses']['200']['content']['application/xml']['example']
    decode(sample.encode('utf-8'),'identidad','login',True)
    app.processEvents(); window.close(); app.processEvents()
    Path(target).write_text(json.dumps({'ok':True,'window':True,'xsd':'login.xsd','operation':'login'})+'\n',encoding='utf-8')


def main():
    app=QApplication(sys.argv); app.setOrganizationName('RedHouse'); app.setApplicationName('Consola'); app.setStyleSheet(STYLE); window=Window(); window.show()
    if os.environ.get('REDHOUSE_SMOKE_TEST') == '1': QTimer.singleShot(1000,app.quit)
    sys.exit(app.exec())

if __name__=='__main__': main()
