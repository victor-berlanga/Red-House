"""Solo salida local sintética; no implica emisión ni impresión física."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
from PySide6.QtWidgets import QApplication
from redhouse_desktop.label_output import LabelOutputError, write_pdf

app=QApplication.instance() or QApplication([])

def test_pdf_generation_and_overwrite_guard(tmp_path):
    path=tmp_path/'etiqueta.pdf'
    unit={'id':'00000000-0000-4000-8000-000000000001','folio':'RH-PRUEBA','component':'RBC','blood_group':'O+'}
    write_pdf(path,unit)
    before=path.read_bytes()
    assert before.startswith(b'%PDF-') and b'%%EOF' in before[-1024:]
    with pytest.raises(LabelOutputError): write_pdf(path,unit)
    assert path.read_bytes()==before
    write_pdf(path,unit,overwrite=True)
    assert path.read_bytes().startswith(b'%PDF-')
