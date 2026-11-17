"""Fraccionamiento documentado; verificación de vínculos y derivados autorizados."""
import re
from datetime import datetime
from uuid import UUID

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .client import ContractError


def validate_fractionation(client, record, links):
    children = record['body']['children']
    if not isinstance(links, list) or len(links) != len(children):
        raise ContractError('Los derivados no corresponden al intento registrado.')
    parent = client.authorized('inventario', '/api/v1/resources/' + record['target']['identifier'], 'resource_detail', fresh_identity=True)
    if parent.get('id') != record['target']['identifier'] or not parent.get('donation_id'):
        raise ContractError('No se pudo comprobar la procedencia de la unidad.')
    seen = set()
    for link, expected in zip(links, children):
        try:
            child_id = link['child_id']
            if str(UUID(child_id)) != child_id or child_id in seen or link['parent_id'] != record['target']['identifier']:
                raise ValueError()
            seen.add(child_id)
            resource = client.authorized('inventario', '/api/v1/resources/' + child_id, 'resource_detail', fresh_identity=True)
            if resource['id'] != child_id or resource.get('donation_id') != link['donation_id'] or link['donation_id'] != parent['donation_id']:
                raise ValueError()
            if any(resource.get(field) != expected[field] for field in ('folio', 'component')):
                raise ValueError()
            actual = datetime.fromisoformat(resource['expires_at'].replace('Z', '+00:00'))
            planned = datetime.fromisoformat(expected['expires_at'].replace('Z', '+00:00'))
            if actual.tzinfo is None or planned.tzinfo is None or actual != planned:
                raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ContractError('Los derivados no corresponden al intento registrado.') from exc


def fractionation_dialog(window, item):
    dialog = QDialog(window)
    dialog.setWindowTitle('Registrar derivados de la unidad')
    dialog.resize(700, 500)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(12)
    heading = QLabel(dialog.windowTitle())
    heading.setObjectName('title')
    layout.addWidget(heading)
    hint = QLabel('Unidad ' + item['folio'] + '. Registra los productos y caducidades documentadas. La unidad de origen se retirará y los derivados quedarán en cuarentena.')
    hint.setWordWrap(True)
    layout.addWidget(hint)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setAccessibleName('Lista de derivados')
    rows_widget = QWidget()
    rows_layout = QVBoxLayout(rows_widget)
    rows_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
    scroll.setWidget(rows_widget)
    layout.addWidget(scroll, 1)
    rows = []
    def add_row():
        if len(rows) >= 8: return
        container = QWidget()
        form = QFormLayout(container)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        folio = QLineEdit()
        folio.setMaxLength(30)
        form.addRow('Folio del derivado', folio)
        component = QComboBox()
        component.addItem('Selecciona un producto', '')
        for title, code in (('Eritrocitos', 'RBC'), ('Plasma', 'PLASMA'), ('Plaquetas', 'PLATELETS')):
            component.addItem(title, code)
        form.addRow('Producto', component)
        expiry = QDateTimeEdit(QDateTime.currentDateTime())
        expiry.setCalendarPopup(True)
        expiry.setDisplayFormat('dd/MM/yyyy HH:mm:ss')
        form.addRow('Caducidad documentada · hora local', expiry)
        container.setMinimumHeight(container.sizeHint().height())
        rows.append((container, folio, component, expiry))
        rows_layout.addWidget(container)
        add.setEnabled(len(rows) < 8)
        remove.setEnabled(len(rows) > 1)
    def remove_row():
        if len(rows) <= 1: return
        if QMessageBox.question(dialog, 'Quitar derivado', '¿Quitar el último derivado capturado?') != QMessageBox.Yes: return
        container, *_ = rows.pop()
        rows_layout.removeWidget(container)
        container.deleteLater()
        add.setEnabled(True)
        remove.setEnabled(len(rows) > 1)
    navigation = QHBoxLayout()
    add, remove = QPushButton('Agregar derivado'), QPushButton('Quitar último')
    navigation.addWidget(add)
    navigation.addWidget(remove)
    navigation.addStretch()
    layout.addLayout(navigation)
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    reason = QLineEdit()
    reason.setMaxLength(1000)
    form.addRow('Motivo del procesamiento', reason)
    confirm = QCheckBox('Confirmo los derivados y sus caducidades documentadas.')
    form.addRow(confirm)
    layout.addLayout(form)
    controls = QHBoxLayout()
    save, cancel = QPushButton('Registrar derivados'), QPushButton('Cancelar')
    save.setObjectName('primary')
    controls.addWidget(save)
    controls.addWidget(cancel)
    layout.addLayout(controls)
    result = {'body': None}
    def submit():
        children = []
        for _, folio, component, expiry in rows:
            value = folio.text().strip()
            if not re.fullmatch(r'[A-Za-z0-9_-]{6,30}', value) or not component.currentData():
                QMessageBox.warning(dialog, 'Datos incompletos', 'Indica folio y producto de cada derivado.')
                return
            children.append({'folio': value, 'component': component.currentData(), 'expires_at': expiry.dateTime().toUTC().toString(Qt.ISODate)})
        if len({child['folio'] for child in children}) != len(children) or len(reason.text().strip()) < 6 or not confirm.isChecked():
            QMessageBox.warning(dialog, 'Datos incompletos', 'Revisa folios distintos, motivo y confirmación documentada.')
            return
        result['body'] = {'children': children, 'version': item['version'], 'reason': reason.text().strip(), 'human_confirmation': 'true'}
        dialog.accept()
    add.clicked.connect(add_row)
    remove.clicked.connect(remove_row)
    save.clicked.connect(submit)
    cancel.clicked.connect(dialog.reject)
    add_row()
    return result['body'] if dialog.exec() == QDialog.Accepted else None
