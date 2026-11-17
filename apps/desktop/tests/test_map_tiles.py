"""Validación de cabeceras y política de caché de mosaicos."""
from email.utils import formatdate
import time

import pytest
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QColor, QImage
from PySide6.QtNetwork import QNetworkReply
from PySide6.QtWidgets import QApplication
from redhouse_desktop.native_map import RegionMap

app = QApplication.instance() or QApplication([])


class TileReply:
    def __init__(self, png, headers):
        self.png, self.headers = png, headers

    def error(self): return QNetworkReply.NoError
    def attribute(self, _key): return 200
    def readAll(self): return self.png
    def rawHeader(self, name):
        if not isinstance(name, str): raise TypeError('Qt requiere str')
        return self.headers.get(name, '').encode()
    def deleteLater(self): pass


def png_bytes():
    image = QImage(256, 256, QImage.Format_RGB32)
    image.fill(QColor('white'))
    data = QByteArray()
    buffer = QBuffer(data)
    assert buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, 'PNG')
    buffer.close()
    return bytes(data)


@pytest.mark.parametrize('headers', [
    {'Cache-Control': 'max-age=3600'},
    {'Expires': formatdate(time.time()+3600, usegmt=True)},
])
def test_valid_tile_is_cached(tmp_path, headers):
    view = RegionMap()
    view.directory, view.available = tmp_path, True
    view.schedule_trim = lambda: None
    view.finished_tile((7, 28, 54), TileReply(png_bytes(), headers))
    assert (7, 28, 54) in view.cache and not view.unavailable
    assert len(list(tmp_path.glob('*.png'))) == 1
    assert len(list(tmp_path.glob('*.json'))) == 1
    view.stop()
    view.close()


def test_no_store_is_not_cached(tmp_path):
    view = RegionMap()
    view.directory, view.available = tmp_path, True
    view.schedule_trim = lambda: None
    view.finished_tile((7, 28, 54), TileReply(png_bytes(), {'Cache-Control': 'no-store'}))
    assert not view.cache and not list(tmp_path.glob('*.png'))
    view.stop()
    view.close()
