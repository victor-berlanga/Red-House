"""Colecta y procesamiento Qt/XML sobre un donante sintético con consentimiento."""
import os
import time
from pathlib import Path
from uuid import uuid4

import redhouse_desktop.app as desktop
from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QLineEdit,
    QPushButton,
    QTableWidget,
)
from redhouse_desktop.donation_selector import select_processed_donation
from redhouse_desktop.journal import Journal
from test_real_lab import gateway as gateway  # noqa: PLC0414 - fixture compartido
from tests.conftest import platform as platform  # noqa: PLC0414 - fixture compartido
from tests.helpers import iso


def wait_until(predicate):
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate(): return True
        time.sleep(0.02)
    return False


def test_medical_collects_operator_processes_and_selector_finds_donation(platform, gateway, monkeypatch, tmp_path):
    suffix = uuid4().hex[:8]
    confirm = {'human_confirmation': True, 'reason': 'Registro sintético documentado'}
    donor = platform.ok('donantes', 'POST', '/api/v1/donors', user='operator1', data={'folio': 'DONOR-' + suffix, 'display_name': 'Donante ficticio', 'blood_group': 'O-', 'consent': True})
    platform.ok('donantes', 'POST', '/api/v1/donors/' + donor['id'] + '/consents', user='medical1', data={**confirm, 'version': donor['version'], 'policy_version': 'SYNTHETIC-1', 'reference': 'Consentimiento sintético', 'effective_at': iso(minutes=-3), 'granted': True})
    platform.ok('donantes', 'POST', '/api/v1/donors/' + donor['id'] + '/reviews', user='medical1', data={**confirm, 'version': donor['version'] + 1, 'decision': 'ELIGIBLE'})
    class Keys:
        def __init__(self): self.key = Fernet.generate_key()
        def get(self, identifier, exists): return self.key
    keys = Keys()
    monkeypatch.setattr(desktop, 'Journal', lambda _root, base, user, tenant: Journal(tmp_path, base, user, tenant, keys))
    monkeypatch.setenv('REDHOUSE_BASE_URL', gateway)
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(desktop.STYLE)
    output = Path(os.environ['DESKTOP_CAPTURE_DIR'])
    output.mkdir(parents=True, exist_ok=True)
    errors = []
    medical = desktop.Window()
    medical.show()
    def login(window, username):
        window.username.setText(username)
        window.password.setText(platform.env.state['password'])
        window.login()
        assert wait_until(lambda: window.client and window.client.user and window.stack.currentIndex() == 1 and not window.busy)
        window.switch('donations')
        assert wait_until(lambda: not window.busy)
    def close(window):
        if window.busy: wait_until(lambda: not window.busy)
        session = bool(window.client and window.client.access)
        window.close()
        if session: assert wait_until(lambda: window.closing)
    try:
        login(medical, 'medical1')
        actor_medical = medical.client.user['id']
        deadline = time.monotonic() + 30
        def collect():
            dialog = app.activeModalWidget()
            if time.monotonic() >= deadline:
                errors.append('Tiempo agotado en colecta')
                if dialog: dialog.reject()
                return
            if not dialog: QTimer.singleShot(25, collect); return
            table = dialog.findChild(QTableWidget)
            if not table or not table.rowCount(): QTimer.singleShot(25, collect); return
            try:
                index = next(i for i in range(table.rowCount()) if table.item(i, 0).text() == donor['folio'])
                table.selectRow(index)
                choices = dialog.findChildren(QComboBox)
                choices[0].setCurrentIndex(choices[0].findData('BLOOD'))
                choices[1].setCurrentIndex(choices[1].findData('RBC'))
                date = dialog.findChild(QDateTimeEdit)
                date.setDateTime(date.dateTime().addSecs(-120))
                next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Colecta sintética documentada')
                for check in dialog.findChildren(QCheckBox): check.setChecked(True)
                assert dialog.grab().save(str(output / 'colecta-qt.png'))
                next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Registrar colecta').click()
            except Exception as exc:  # noqa: BLE001 - solo clase sin datos privados
                errors.append(type(exc).__name__)
                dialog.reject()
        QTimer.singleShot(0, collect)
        medical.create_donation()
        assert not errors
        assert wait_until(lambda: not medical.busy and any(row.get('donor_id') == donor['id'] and row.get('status') == 'COLLECTED' for row in medical.rows))
        donation = next(row for row in medical.rows if row.get('donor_id') == donor['id'] and row.get('status') == 'COLLECTED')
    finally:
        close(medical)
    operator = desktop.Window()
    operator.show()
    try:
        login(operator, 'operator1')
        actor_operator = operator.client.user['id']
        deadline = time.monotonic() + 30
        def process():
            dialog = app.activeModalWidget()
            if time.monotonic() >= deadline:
                errors.append('Tiempo agotado en procesamiento')
                if dialog: dialog.reject()
                return
            if not dialog: QTimer.singleShot(25, process); return
            try:
                if dialog.windowTitle() == 'Seleccionar colecta pendiente':
                    table = dialog.findChild(QTableWidget)
                    if not table or not table.rowCount(): QTimer.singleShot(25, process); return
                    index = next(i for i in range(table.rowCount()) if donor['folio'] in table.item(i, 0).text())
                    table.selectRow(index)
                    reference = next(x for x in dialog.findChildren(QLineEdit) if x.isReadOnly())
                    assert reference.text() == donation['id']
                    assert dialog.grab().save(str(output / 'colecta-pendiente-qt.png'))
                    QTimer.singleShot(25, process)
                    next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Usar donación').click()
                    return
                if dialog.windowTitle() != 'Documentar procesamiento': QTimer.singleShot(25, process); return
                choice = dialog.findChild(QComboBox)
                assert choice.currentData() == ''
                choice.setCurrentIndex(choice.findData('PROCESSED'))
                next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Proceso sintético documentado')
                dialog.findChild(QCheckBox).setChecked(True)
                assert dialog.grab().save(str(output / 'procesamiento-qt.png'))
                next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Registrar resultado').click()
            except Exception as exc:  # noqa: BLE001 - solo clase sin datos privados
                errors.append(type(exc).__name__)
                dialog.reject()
        QTimer.singleShot(0, process)
        operator.process_donation()
        assert wait_until(lambda: bool(errors) or (not operator.busy and any(row.get('id') == donation['id'] and row.get('status') == 'PROCESSED' for row in operator.rows)))
        assert not errors
        updated = next(row for row in operator.rows if row['id'] == donation['id'])
        assert updated['version'] == donation['version'] + 1
        deadline = time.monotonic() + 30
        def select_processed():
            dialog = app.activeModalWidget()
            if time.monotonic() >= deadline:
                errors.append('Tiempo agotado en selector')
                if dialog: dialog.reject()
                return
            if not dialog: QTimer.singleShot(25, select_processed); return
            table = dialog.findChild(QTableWidget)
            if not table or not table.rowCount(): QTimer.singleShot(25, select_processed); return
            try:
                index = next(i for i in range(table.rowCount()) if donor['folio'] in table.item(i, 0).text())
                table.selectRow(index)
                assert next(x for x in dialog.findChildren(QLineEdit) if x.isReadOnly()).text() == donation['id']
                assert dialog.grab().save(str(output / 'procesada-selector-qt.png'))
                next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Usar donación').click()
            except Exception as exc:  # noqa: BLE001 - solo clase sin datos privados
                errors.append(type(exc).__name__)
                dialog.reject()
        QTimer.singleShot(0, select_processed)
        chosen = select_processed_donation(operator, desktop.Work, desktop.label)
        assert not errors and chosen['id'] == donation['id']
        with platform.owner('donantes') as conn:
            row = conn.execute('SELECT donor_id,status,version FROM donations WHERE id=%s', (donation['id'],)).fetchone()
            events = conn.execute("SELECT event->>'action',event->>'actor_id' FROM activity_events WHERE event->>'resource_id'=%s", (donation['id'],)).fetchall()
        assert str(row[0]) == donor['id'] and row[1] == 'PROCESSED' and row[2] == donation['version'] + 1
        assert ('DONATION_COLLECTED', actor_medical) in events and ('DONATION_PROCESSED', actor_operator) in events
    finally:
        close(operator)
