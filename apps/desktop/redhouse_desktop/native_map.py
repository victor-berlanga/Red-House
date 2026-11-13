"""Mapa de mosaicos interactivo nativo; sólo descarga el área visible."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import tempfile
import threading
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from urllib.parse import urlsplit
from PySide6.QtCore import QPointF, QRectF, Qt, QUrl, QStandardPaths, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QWidget

TILE_SIZE=256
CACHE_LIMIT=64*1024*1024
CACHE_NAME=re.compile(r'[0-9a-f]{16}-[0-9]+-[0-9]+-[0-9]+\.png')

def trim_cache(directory,limit=CACHE_LIMIT,now=None):
    now=time.time() if now is None else now
    entries=[]; total=0
    for image in Path(directory).iterdir():
        if not CACHE_NAME.fullmatch(image.name) or image.is_symlink(): continue
        meta=image.with_suffix('.json')
        if meta.is_symlink(): continue
        try:
            image_stat=image.stat(); meta_stat=meta.stat()
            if image_stat.st_size>1_000_000 or meta_stat.st_size>4096: raise ValueError()
            metadata=json.loads(meta.read_text()); size=image_stat.st_size+meta_stat.st_size; expires=float(metadata['expires'])
            if not math.isfinite(expires): raise ValueError()
        except (OSError,ValueError,TypeError,KeyError):
            # No tocar una escritura de mosaico todavía en curso.
            try:
                if now-image.stat().st_mtime>300:
                    image.unlink(); meta.unlink(missing_ok=True)
            except OSError: pass
            continue
        entries.append((expires>now,image_stat.st_mtime,size,image,meta)); total+=size
    for meta in Path(directory).iterdir():
        if not re.fullmatch(r'[0-9a-f]{16}-[0-9]+-[0-9]+-[0-9]+\.json',meta.name) or meta.is_symlink(): continue
        try:
            if not meta.with_suffix('.png').exists() and now-meta.stat().st_mtime>300: meta.unlink()
        except OSError: pass
    for fresh,_mtime,size,image,meta in sorted(entries,key=lambda entry:(entry[0],entry[1])):
        if fresh and total<=limit: break
        try:
            image.unlink(); meta.unlink(missing_ok=True); total-=size
        except OSError: pass
    return total

def atomic_cache(path,data):
    fd,temporary=tempfile.mkstemp(prefix='.tile-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream: stream.write(data)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def world(latitude,longitude,zoom):
    latitude=max(-85.05112878,min(85.05112878,latitude)); size=TILE_SIZE*(2**zoom)
    x=(longitude+180.0)/360.0*size
    y=(1-math.asinh(math.tan(math.radians(latitude)))/math.pi)/2*size
    return x,y

def coordinates(x,y,zoom):
    size=TILE_SIZE*(2**zoom); x=x%size; y=max(0,min(size,y)); longitude=(x/size*360.0)-180.0
    latitude=math.degrees(math.atan(math.sinh(math.pi*(1-2*y/size))))
    return latitude,longitude

class RegionMap(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.setMinimumSize(360,250); self.setAccessibleName('Mapa interactivo de Nuevo León')
        self.template=os.environ.get('REDHOUSE_TILE_URL','https://tile.openstreetmap.org/{z}/{x}/{y}.png')
        parsed=urlsplit(self.template)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or not all('{'+k+'}' in self.template for k in ('z','x','y')):
            raise ValueError('Proveedor cartográfico inválido.')
        if self.template!='https://tile.openstreetmap.org/{z}/{x}/{y}.png' and (not os.environ.get('REDHOUSE_TILE_ATTRIBUTION') or not os.environ.get('REDHOUSE_TILE_ATTRIBUTION_URL')):
            raise ValueError('Falta atribución del proveedor cartográfico.')
        self.attribution=os.environ.get('REDHOUSE_TILE_ATTRIBUTION','© OpenStreetMap contributors')
        self.attribution_url=os.environ.get('REDHOUSE_TILE_ATTRIBUTION_URL','https://www.openstreetmap.org/copyright')
        attribution_url=urlsplit(self.attribution_url)
        if attribution_url.scheme!='https' or not attribution_url.hostname or attribution_url.username or attribution_url.password: raise ValueError('Atribución cartográfica inválida.')
        self.setToolTip('Arrastra para mover el mapa; rueda para acercar. Pulsa la atribución para consultar la licencia.')
        self.zoom=7; self.center=(25.7,-100.3); self.points=[]; self.anchors=[]; self.cache={}; self.inflight={}; self.failed={}; self.drag=None
        self.network=QNetworkAccessManager(self)
        root=QStandardPaths.writableLocation(QStandardPaths.CacheLocation); self.available=bool(root); self.unavailable=False
        self.directory=Path(root)/'map-tiles' if root else None
        try:
            if self.directory: self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        except OSError: self.available=False
        self.provider=hashlib.sha256(self.template.encode()).hexdigest()[:16]; self.trim_lock=threading.Lock(); self.touched={}
        self.trim_timer=QTimer(self); self.trim_timer.setInterval(60000); self.trim_timer.timeout.connect(self.schedule_trim); self.trim_timer.start(); self.schedule_trim()

    def schedule_trim(self):
        if not self.available or not self.trim_lock.acquire(False): return
        def work():
            try: trim_cache(self.directory)
            except OSError: pass
            finally: self.trim_lock.release()
        threading.Thread(target=work,daemon=True).start()

    def touch(self,key):
        now=time.monotonic()
        if now-self.touched.get(key,0)<60: return
        self.touched[key]=now
        while len(self.touched)>256: self.touched.pop(next(iter(self.touched)))
        try: os.utime(self.paths(key)[0],None,follow_symlinks=False)
        except OSError: pass

    def stop(self):
        self.available=False; self.trim_timer.stop()
        for reply in list(self.inflight.values()): reply.abort()
        self.inflight.clear(); self.points=[]; self.anchors=[]; self.cache.clear()

    def set_anchors(self,anchors):
        self.anchors=[a for a in anchors if isinstance(a.get('latitude'),(int,float)) and isinstance(a.get('longitude'),(int,float)) and math.isfinite(a['latitude']) and math.isfinite(a['longitude']) and -90<=a['latitude']<=90 and -180<=a['longitude']<=180]
        self.update()

    def add_position(self,point):
        if point.get('fix_valid'):
            self.points=[p for p in self.points if p['event_id']!=point['event_id']]
            self.points.append(point); self.points.sort(key=lambda p:(datetime.fromisoformat(p['captured_at'].replace('Z','+00:00')).astimezone(timezone.utc),p['cursor']))
            self.points=self.points[-1000:]; self.update()

    def clear_positions(self): self.points=[]; self.update()
    def center_latest(self):
        if self.points:
            self.center=(self.points[-1]['latitude'],self.points[-1]['longitude']); self.update()

    def tiles_for_view(self):
        cx,cy=world(*self.center,self.zoom); x0=cx-self.width()/2; y0=cy-self.height()/2; count=2**self.zoom
        for yy in range(math.floor(y0/TILE_SIZE),math.floor((y0+self.height())/TILE_SIZE)+1):
            if not 0<=yy<count: continue
            for xx in range(math.floor(x0/TILE_SIZE),math.floor((x0+self.width())/TILE_SIZE)+1):
                yield (self.zoom,xx%count,yy),QPointF(xx*TILE_SIZE-x0,yy*TILE_SIZE-y0)

    def paths(self,key):
        stem=self.provider+'-'+'-'.join(map(str,key)); return self.directory/(stem+'.png'),self.directory/(stem+'.json')

    def tile(self,key):
        if not self.available: return None
        if key in self.cache:
            image,expires=self.cache[key]
            if expires>time.time(): self.touch(key); return image
            self.cache.pop(key,None)
        image_path,meta_path=self.paths(key)
        try:
            meta=json.loads(meta_path.read_text())
            if meta['expires']>time.time() and image_path.stat().st_size<=1_000_000:
                image=QPixmap(str(image_path))
                if image.size().width()==256 and image.size().height()==256:
                    self.remember(key,image,meta['expires']); self.touch(key); return image
        except (OSError,ValueError,KeyError,TypeError): pass
        if key not in self.inflight and time.monotonic()>=self.failed.get(key,0): self.fetch(key)
        return None

    def remember(self,key,image,expires):
        self.cache[key]=(image,expires)
        while len(self.cache)>128: self.cache.pop(next(iter(self.cache)))

    def fetch(self,key):
        z,x,y=key; url=self.template.replace('{z}',str(z)).replace('{x}',str(x)).replace('{y}',str(y))
        request=QNetworkRequest(QUrl(url)); request.setRawHeader(b'User-Agent',b'RedHouseDesktop/0.1')
        request.setAttribute(QNetworkRequest.RedirectPolicyAttribute,QNetworkRequest.ManualRedirectPolicy)
        reply=self.network.get(request); self.inflight[key]=reply
        reply.downloadProgress.connect(lambda received,total:reply.abort() if received>1_000_000 or total>1_000_000 else None)
        reply.finished.connect(lambda:self.finished_tile(key,reply))

    def finished_tile(self,key,reply):
        self.inflight.pop(key,None)
        try:
            if reply.error()!=QNetworkReply.NoError or reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)!=200: raise ValueError()
            data=bytes(reply.readAll())
            if len(data)>1_000_000: raise ValueError()
            image=QPixmap()
            if not image.loadFromData(data,'PNG') or image.width()!=256 or image.height()!=256: raise ValueError()
            cache_control=bytes(reply.rawHeader(b'Cache-Control')).decode('ascii','ignore').lower()
            if 'no-store' in cache_control or 'no-cache' in cache_control: raise ValueError()
            match=re.search(r'(?:^|,)\s*max-age\s*=\s*(\d+)',cache_control)
            expires=time.time()+int(match.group(1)) if match else None
            if expires is None:
                try: expires=parsedate_to_datetime(bytes(reply.rawHeader(b'Expires')).decode('ascii')).timestamp()
                except (ValueError,TypeError,OverflowError):
                    if 'must-revalidate' in cache_control: raise ValueError()
                    expires=time.time()+7*86400
            if expires<=time.time(): raise ValueError()
            self.remember(key,image,expires); self.unavailable=False
            image_path,meta_path=self.paths(key)
            atomic_cache(image_path,data)
            atomic_cache(meta_path,json.dumps({'expires':expires}).encode()); self.schedule_trim()
        except (OSError,ValueError,TypeError): self.unavailable=True; self.failed[key]=time.monotonic()+30
        finally: reply.deleteLater(); self.update()

    def paintEvent(self,_event):
        painter=QPainter(self); painter.fillRect(self.rect(),QColor('#e4e9eb'))
        for key,at in self.tiles_for_view():
            tile=self.tile(key)
            if tile: painter.drawPixmap(at,tile)
        cx,cy=world(*self.center,self.zoom)
        def point(lat,lon):
            x,y=world(lat,lon,self.zoom); return QPointF(x-cx+self.width()/2,y-cy+self.height()/2)
        painter.setRenderHint(QPainter.Antialiasing); painter.setPen(QPen(QColor('#a32035'),3))
        for first,second in zip(self.points,self.points[1:]): painter.drawLine(point(first['latitude'],first['longitude']),point(second['latitude'],second['longitude']))
        for index,anchor in enumerate(self.anchors):
            at=point(anchor['latitude'],anchor['longitude']); painter.setBrush(QColor('#176338' if anchor.get('label')=='Origen' else '#285b8c')); painter.drawEllipse(at,6,6)
            painter.drawText(at+QPointF(8,-10 if index%2==0 else 20),anchor.get('label','Institución')+(' · sintético' if anchor.get('synthetic') else ''))
        if self.points:
            at=point(self.points[-1]['latitude'],self.points[-1]['longitude']); painter.setBrush(QColor('#a32035')); painter.drawEllipse(at,8,8)
        if not self.available or self.unavailable:
            painter.setPen(QColor('#202c39')); painter.drawText(QRectF(8,8,self.width()-16,24),Qt.AlignLeft|Qt.AlignVCenter,'Cartografía no disponible; se conservan las observaciones autorizadas.')
        painter.fillRect(QRectF(0,self.height()-23,self.width(),23),QColor(255,255,255,220)); painter.setPen(QColor('#202c39'))
        painter.drawText(QRectF(6,self.height()-23,self.width()-12,23),Qt.AlignRight|Qt.AlignVCenter,self.attribution)
        painter.end()

    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton and event.position().y()>=self.height()-23:
            QDesktopServices.openUrl(QUrl(self.attribution_url)); return
        if event.button()==Qt.LeftButton: self.drag=event.position()
    def mouseMoveEvent(self,event):
        if self.drag is not None:
            delta=event.position()-self.drag; x,y=world(*self.center,self.zoom); self.center=coordinates(x-delta.x(),y-delta.y(),self.zoom); self.drag=event.position(); self.update()
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.LeftButton: self.drag=None
    def wheelEvent(self,event):
        delta=1 if event.angleDelta().y()>0 else -1; self.zoom=max(5,min(16,self.zoom+delta)); self.update()
