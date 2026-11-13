"""Salida nativa de etiquetas ya autorizadas por Inventario.

Este módulo no autoriza emisiones. El llamador debe obtener y verificar una
emisión del servicio antes de invocar estas funciones.
"""
from pathlib import Path
import os
import tempfile
import qrcode
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtPrintSupport import QPrinter

class LabelOutputError(Exception):
    pass

def draw_label(printer, resource):
    qr=qrcode.QRCode(border=4); qr.add_data(resource['id']); qr.make(fit=True); matrix=qr.get_matrix()
    painter=QPainter()
    if not painter.begin(printer): raise LabelOutputError('No se pudo preparar la salida de etiqueta.')
    try:
        rect=painter.viewport(); unit=max(1,min(rect.width()//65,rect.height()//90)); left=unit*5; top=unit*5
        title=QFont('Helvetica'); title.setBold(True); title.setPointSize(18); painter.setFont(title)
        painter.drawText(QRect(left,top,unit*48,unit*6),Qt.AlignLeft|Qt.AlignVCenter,'Unidad '+str(resource.get('folio') or ''))
        text=QFont('Helvetica'); text.setPointSize(12); painter.setFont(text)
        painter.drawText(QRect(left,top+unit*7,unit*55,unit*5),Qt.AlignLeft|Qt.AlignVCenter,
                         'Producto: '+{'RBC':'Eritrocitos','PLASMA':'Plasma','PLATELETS':'Plaquetas'}.get(resource.get('component'),str(resource.get('component') or '—'))+'   Grupo: '+str(resource.get('blood_group') or '—'))
        painter.setPen(Qt.NoPen); painter.setBrush(QColor('black'))
        for y,row in enumerate(matrix):
            for x,black in enumerate(row):
                if black: painter.drawRect(left+x*unit,top+unit*15+y*unit,unit,unit)
    except Exception:
        painter.end()
        raise
    if not painter.end(): raise LabelOutputError('No se pudo completar la salida de etiqueta.')

def write_pdf(destination, resource, *, overwrite=False):
    """Escritura temporal en destino y reemplazo solo después de generar PDF."""
    target=Path(destination)
    if target.exists() and not overwrite: raise LabelOutputError('El archivo ya existe; confirma antes de reemplazarlo.')
    fd,temp=tempfile.mkstemp(prefix='.redhouse-label-',suffix='.pdf',dir=target.parent)
    os.close(fd)
    try:
        printer=QPrinter(QPrinter.HighResolution); printer.setOutputFormat(QPrinter.PdfFormat); printer.setOutputFileName(temp)
        draw_label(printer,resource)
        with open(temp,'rb+') as stream:
            header=stream.read(5); stream.seek(-min(1024,os.path.getsize(temp)),os.SEEK_END); tail=stream.read()
            if header!=b'%PDF-' or b'%%EOF' not in tail: raise LabelOutputError('No se pudo generar el PDF.')
            os.fsync(stream.fileno())
        if overwrite: os.replace(temp,target)
        else:
            try: os.link(temp,target)
            except FileExistsError as exc: raise LabelOutputError('El archivo ya existe; confirma antes de reemplazarlo.') from exc
            os.unlink(temp)
    finally:
        if os.path.exists(temp): os.unlink(temp)
