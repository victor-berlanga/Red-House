"""Captura estados sintéticos del texto de cobertura; no consulta servicios."""
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QTableWidget
from redhouse_desktop.app import STYLE, Window

app = QApplication([])
app.setStyleSheet(STYLE)
window = Window()
window.client = type('Client', (), {'user': {'role': 'COORDINATOR'}, 'access': None})()
output = Path(__file__).parent

def capture(name, select):
    dialog = app.activeModalWidget()
    if select:
        dialog.findChild(QTableWidget).selectRow(0)
        app.processEvents()
    if not dialog.grab().save(str(output / name)):
        raise RuntimeError('No se guardó la captura')
    dialog.reject()

base = {'algorithm_version': 'COVERAGE-HK-1.0', 'created_at': '2030-01-01T12:00:00Z', 'snapshots': {}}
row = {'request_id': '00000000-0000-4000-8000-000000000001', 'resource_id': '00000000-0000-4000-8000-000000000002'}
QTimer.singleShot(0, lambda: capture('propuesta-doble.png', True))
window.coverage_detail(dict(base, slot_count=2, matched_count=1, result=[row]))
QTimer.singleShot(0, lambda: capture('vacia-doble.png', False))
window.coverage_detail(dict(base, slot_count=1, matched_count=0, result=[]))
window.client = None
window.close()
