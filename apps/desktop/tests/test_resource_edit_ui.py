"""Formulario de corrección con catálogo sintético."""
import os
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLineEdit, QPushButton
from redhouse_desktop.app import STYLE, Window, Work, label
from redhouse_desktop.resource_edit import resource_edit_dialog

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


def test_correction_selects_location_and_preserves_documented_data():
    old, new, donation = (str(uuid4()) for _ in range(3))
    item = {'id': str(uuid4()), 'folio': 'UNIT-001', 'kind': 'BLOOD', 'component': 'RBC',
            'blood_group': 'O-', 'expires_at': '2026-11-16T12:00:01.123456Z',
            'collected_at': '2026-11-14T10:00:00Z', 'location_id': old, 'donation_id': donation,
            'version': 2, 'status': 'QUARANTINE'}
    class Client:
        access = None
        def authorized(self, _service, _path, operation, **_kwargs):
            assert operation == 'locations_list_rows'
            return {'items': [{'id': new, 'name': 'Refrigerador 1', 'active': True}], 'page': 1, 'total': 1}
    window = Window()
    window.client = Client()
    errors = []
    def choose():
        dialog = app.activeModalWidget()
        if not dialog: QTimer.singleShot(20, choose); return
        combo = dialog.findChild(QComboBox)
        if combo.count() < 3: QTimer.singleShot(20, choose); return
        try:
            combo.setCurrentIndex(2)
            next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Corrección documentada')
            for check in dialog.findChildren(QCheckBox): check.setChecked(True)
            if os.environ.get('DESKTOP_CAPTURE_DIR'):
                assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'correccion-doble.png'))
            next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Guardar corrección').click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados
            errors.append(type(exc).__name__)
            dialog.reject()
    QTimer.singleShot(0, choose)
    body = resource_edit_dialog(window, item, 'Ubicación anterior', Work, label)
    assert not errors
    assert body['location_id'] == new and body['version'] == 2
    assert body['donation_id'] == donation and body['collected_at'] == item['collected_at']
    assert body['expires_at'] == item['expires_at']
