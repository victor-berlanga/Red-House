"""Seguimiento WSS XML de un traslado, sin publicar posiciones."""
from datetime import datetime
import math
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID
from lxml import etree
from PySide6.QtCore import QObject, Signal, QTimer, QUrl
from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWebSockets import QWebSocket, QWebSocketHandshakeOptions
from .client import ContractError, read_xml, request_xml, schema

PROTOCOL='redhouse.tracking.v1.xml'
STATES={'LIVE','STALE','NO_DATA','NO_FIX','FINALIZED'}
EVENT_SCHEMA=schema('tracking_event.xsd')

def event_xml(raw,shipment):
    if len(raw.encode('utf-8'))>16384: raise ContractError('Evento excesivo.')
    root=read_xml(raw.encode('utf-8'))
    if not EVENT_SCHEMA.validate(root): raise ContractError('Evento contrario al contrato.')
    value={child.tag:child for child in root}
    typ=value['type'].text
    fields=set(value)-{'type','schema_version'}
    allowed={'authenticated':set(),'subscribed':{'shipment_id','cursor','position','state'},'unsubscribed':{'shipment_id'},'position.updated':{'shipment_id','cursor','position'},'tracking.status':{'shipment_id','state','cursor'},'resync.required':{'shipment_id','code'},'error':{'code','message'},'heartbeat':set()}
    if typ not in allowed or not fields<=allowed[typ]: raise ContractError('Campos incompatibles con el evento.')
    if 'schema_version' in value and value['schema_version'].text!='1': raise ContractError('Versión no compatible.')
    target=value.get('shipment_id')
    if target is not None and target.text!=shipment: raise ContractError('Evento de otro traslado.')
    if typ in ('subscribed','position.updated','tracking.status','resync.required') and target is None: raise ContractError('Falta el traslado.')
    out={'type':typ}
    for key in ('state','code','message'):
        if key in value: out[key]=value[key].text or ''
    if typ in ('subscribed','position.updated'):
        if 'cursor' not in value: raise ContractError('Falta cursor.')
        cursor=int(value['cursor'].text)
        if not 0<=cursor<=9007199254740991: raise ContractError('Cursor inválido.')
        out['cursor']=cursor
    if typ=='tracking.status' and 'cursor' in value:
        cursor=int(value['cursor'].text)
        if not 0<=cursor<=9007199254740991: raise ContractError('Cursor inválido.')
    if typ in ('subscribed','tracking.status') and out.get('state') not in STATES: raise ContractError('Estado no reconocido.')
    point=value.get('position')
    if point is not None and point.get('{http://www.w3.org/2001/XMLSchema-instance}nil')!='true':
        fields={child.tag:child.text for child in point}
        required=('event_id','shipment_id','captured_at','fix_valid','cursor')
        if any(not fields.get(key) for key in required) or fields['shipment_id']!=shipment: raise ContractError('Posición incompleta.')
        try:
            UUID(fields['event_id']); UUID(fields['device_id']); captured=datetime.fromisoformat(fields['captured_at'].replace('Z','+00:00')); received=datetime.fromisoformat(fields['received_at'].replace('Z','+00:00'))
            if captured.tzinfo is None or received.tzinfo is None: raise ValueError()
            fix={'true':True,'false':False,'1':True,'0':False}[fields['fix_valid']]
            cursor=int(fields['cursor'])
            lat=float(fields['latitude']) if fields.get('latitude') else None
            lon=float(fields['longitude']) if fields.get('longitude') else None
            if not 0<=cursor<=9007199254740991 or (lat is None)!=(lon is None) or (fix and lat is None) or any(v is not None and not math.isfinite(v) for v in (lat,lon)):
                raise ValueError()
            for key,lower,upper in (('accuracy_m',0,100000),('speed_m_s',0,1000),('heading_deg',0,360),('altitude_m',-12000,100000),('battery_percent',0,100)):
                if fields.get(key) is not None:
                    number=float(fields[key])
                    if not math.isfinite(number) or number<lower or number>upper or (key=='heading_deg' and number==360): raise ValueError()
        except (KeyError,ValueError,TypeError) as exc: raise ContractError('Posición inválida.') from exc
        out['position']={'event_id':fields['event_id'],'shipment_id':shipment,'captured_at':fields['captured_at'],'cursor':cursor,'fix_valid':fix,'latitude':lat,'longitude':lon,'source':fields.get('source',''),'simulated':fields.get('simulated','false') in ('true','1')}
    if typ=='position.updated' and ('position' not in out or out['position']['cursor']!=out['cursor']): raise ContractError('Posición o cursor no coinciden.')
    return out

class TrackingSocket(QObject):
    position=Signal(object)
    state=Signal(str)
    reconnect=Signal()
    resync=Signal()
    terminated=Signal()

    def __init__(self,base,shipment,parent=None):
        super().__init__(parent)
        parsed=urlsplit(base)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment: raise ValueError('Se requiere HTTPS.')
        self.url=urlunsplit(('wss',parsed.netloc,parsed.path.rstrip('/')+'/services/transporte/ws/v1/tracking/xml','',''))
        if str(UUID(shipment))!=shipment: raise ValueError('Traslado inválido.')
        self.shipment=shipment; self.cursor=None; self.token=None; self.stopped=True; self.attempt=0
        self.socket=QWebSocket(parent=self); self.socket.setMaxAllowedIncomingFrameSize(16384); self.socket.setMaxAllowedIncomingMessageSize(16384)
        self.socket.connected.connect(self.connected); self.socket.textMessageReceived.connect(self.received)
        self.socket.binaryMessageReceived.connect(lambda _data:self.protocol_failure())
        self.socket.disconnected.connect(self.disconnected); self.socket.errorOccurred.connect(self.socket_error); self.socket.sslErrors.connect(lambda _errors:self.tls_failure())
        self.timer=QTimer(self); self.timer.setInterval(15000); self.timer.timeout.connect(lambda:self.send({'type':'heartbeat'}))
        self.retry=QTimer(self); self.retry.setSingleShot(True); self.retry.timeout.connect(self.reconnect.emit)

    def start(self,token):
        if not token: raise ValueError('Sesión requerida.')
        self.stopped=False; self.token=token
        options=QWebSocketHandshakeOptions(); options.setSubprotocols([PROTOCOL]); self.state.emit('Conectando…')
        self.socket.open(QUrl(self.url),options)

    def send(self,message):
        try: self.socket.sendTextMessage(request_xml(message,'tracking_message.xsd').decode('utf-8'))
        except Exception: self.protocol_failure()

    def connected(self):
        if self.socket.subprotocol()!=PROTOCOL: self.protocol_failure(); return
        token=self.token; self.token=None
        self.send({'type':'authenticate','credential_kind':'user','credential':token})

    def received(self,raw):
        try: event=event_xml(raw,self.shipment)
        except Exception: self.protocol_failure(); return
        typ=event['type']
        if typ=='authenticated':
            message={'type':'subscribe','shipment_id':self.shipment}
            if self.cursor is not None: message['cursor']=self.cursor
            self.send(message); self.timer.start()
        elif typ=='subscribed':
            self.attempt=0
            if self.cursor is None: self.cursor=event['cursor']
            self.state.emit(event['state'])
            if event.get('position'): self.position.emit(event['position'])
        elif typ=='position.updated':
            if self.cursor is None or event['cursor']>self.cursor:
                self.cursor=event['cursor']; self.position.emit(event['position']); self.state.emit('Observación recibida')
        elif typ=='tracking.status': self.state.emit(event['state'])
        elif typ=='resync.required':
            self.cursor=None; self.resync.emit(); self.send({'type':'subscribe','shipment_id':self.shipment})
        elif typ=='error':
            if event.get('code') in ('forbidden','tracking_closed'):
                self.stop(); self.terminated.emit()
            elif event.get('code')=='unauthorized':
                self.terminated.emit(); self.socket.close()
            else: self.socket.close()

    def socket_error(self,_error):
        if not self.stopped and self.socket.state()==QAbstractSocket.UnconnectedState: self.disconnected()

    def disconnected(self):
        self.timer.stop(); self.token=None
        if self.retry.isActive(): return
        if not self.stopped and self.attempt<8:
            self.state.emit('Desconectado; última observación conservada.'); self.retry.start(min(30000,1000*2**self.attempt)); self.attempt+=1
        elif not self.stopped: self.state.emit('Sin conexión. Intenta nuevamente.')

    def tls_failure(self):
        self.state.emit('No se pudo verificar la conexión segura.')
        self.stop()
        self.terminated.emit()
    def protocol_failure(self):
        self.state.emit('No se pudo validar la información recibida.')
        self.stop()
        self.terminated.emit()
    def stop(self):
        self.stopped=True; self.timer.stop(); self.retry.stop(); self.token=None; self.socket.abort()


def latest_position(previous, point):
    """Conserva la observación de captura más reciente, incluso tras replay."""
    if previous is None:
        return point
    captured = datetime.fromisoformat(point['captured_at'].replace('Z', '+00:00'))
    old = datetime.fromisoformat(previous['captured_at'].replace('Z', '+00:00'))
    return point if captured >= old else previous


def validate_snapshot_point(point,shipment):
    """Comprueba posición de snapshot además del DTO HTTP publicado."""
    if not isinstance(point,dict) or point.get('shipment_id')!=shipment or point.get('schema_version',1)!=1:
        raise ContractError('Posición de otro traslado o versión.')
    try:
        UUID(point['event_id']); UUID(point['device_id']); captured=datetime.fromisoformat(point['captured_at'].replace('Z','+00:00')); received=datetime.fromisoformat(point['received_at'].replace('Z','+00:00'))
        cursor=point['cursor']; fix=point['fix_valid']; lat=point.get('latitude'); lon=point.get('longitude')
        if captured.tzinfo is None or received.tzinfo is None or isinstance(cursor,bool) or not isinstance(cursor,int) or not 0<=cursor<=9007199254740991 or not isinstance(fix,bool): raise ValueError()
        for value,limit in ((lat,90),(lon,180)):
            if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or abs(value)>limit): raise ValueError()
        if (lat is None)!=(lon is None) or (fix and lat is None): raise ValueError()
        for key,lower,upper in (('accuracy_m',0,100000),('speed_m_s',0,1000),('heading_deg',0,360),('altitude_m',-12000,100000),('battery_percent',0,100)):
            value=point.get(key)
            if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<lower or value>upper or (key=='heading_deg' and value==360)): raise ValueError()
        if point.get('source') not in ('SIMULATOR','GPS_BRIDGE','ANDROID','IOS') or not isinstance(point.get('simulated',False),bool): raise ValueError()
    except (KeyError,TypeError,ValueError,AttributeError) as exc: raise ContractError('Posición no válida.') from exc
    return {key:point.get(key) for key in ('event_id','shipment_id','captured_at','cursor','fix_valid','latitude','longitude','source','simulated')}
