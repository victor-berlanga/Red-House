"""WSS XML real y mapa Qt con datos sintéticos; requiere laboratorio aislado."""
import os
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtNetwork import QSslCertificate, QSslConfiguration
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from tests.conftest import platform, p
from tests.test_final_tracking import tracking, connect, send, receive, point
from redhouse_desktop.native_map import RegionMap
from redhouse_desktop.tracking import TrackingSocket, latest_position


def wait_until(predicate, limit=1000):
    for _ in range(limit):
        QTest.qWait(20)
        if predicate(): return True
    return False


def test_qt_wss_replay_revocation_and_native_map(p, tracking, monkeypatch):
    app=QApplication.instance() or QApplication([])
    original=QSslConfiguration.defaultConfiguration()
    certs=QSslCertificate.fromPath(tracking['cert'])
    assert certs
    shipment=tracking['shipment']['id']; base=tracking['url'].replace('wss://','https://').split('/ws/')[0]
    bad=TrackingSocket(base,shipment); bad.url=tracking['url']+'xml'; bad_states=[]
    bad.state.connect(bad_states.append)
    bad.start(p.tokens['coordinator1'])
    assert wait_until(lambda:bad.stopped)
    assert any('segura' in message for message in bad_states)
    config=QSslConfiguration.defaultConfiguration(); config.setCaCertificates(config.caCertificates()+certs)
    QSslConfiguration.setDefaultConfiguration(config)
    QStandardPaths.setTestModeEnabled(True)
    monkeypatch.setattr(RegionMap,'schedule_trim',lambda _self:None)
    map_view=RegionMap(); map_view.available=False; map_view.unavailable=True; map_view.resize(760,460); map_view.show()
    map_view.set_anchors([
        {'label':'Origen sintético','latitude':25.68,'longitude':-100.35},
        {'label':'Destino sintético','latitude':25.71,'longitude':-100.27},
    ])
    positions=[]; states=[]; terminated=[]; latest=[]
    tracker=TrackingSocket(base,shipment); tracker.url=tracking['url']+'xml'
    def on_position(value):
        positions.append(value); map_view.add_position(value)
        latest[:]=[latest_position(latest[0] if latest else None,value)]
    def on_terminated():
        terminated.append(True); map_view.clear_positions()
    tracker.position.connect(on_position); tracker.state.connect(states.append); tracker.terminated.connect(on_terminated)
    tracker.reconnect.connect(lambda:tracker.start(p.tokens['coordinator1']))
    publisher=None
    try:
        tracker.start(p.tokens['coordinator1'])
        assert wait_until(lambda:'NO_DATA' in states or 'LIVE' in states)
        publisher=connect(tracking,tracking['credential']['credential'],'device'); receive(publisher,'authenticated')
        first=point(tracking)
        send(publisher,{'type':'position.publish','position':first}); receive(publisher,'position.ack')
        assert wait_until(lambda:any(value['event_id']==first['event_id'] for value in positions))
        tracker.socket.abort()
        assert wait_until(lambda:tracker.retry.isActive())
        second=point(tracking,2,latitude=25.70,longitude=-100.29)
        send(publisher,{'type':'position.publish','position':second}); receive(publisher,'position.ack')
        no_fix=point(tracking,3,fix_valid=False,latitude=None,longitude=None)
        send(publisher,{'type':'position.publish','position':no_fix}); receive(publisher,'position.ack')
        assert wait_until(lambda:tracker.cursor==3 and 'NO_FIX' in states,1500)
        assert any(value['event_id']==second['event_id'] for value in positions)
        assert latest[0]['event_id']==no_fix['event_id']
        assert map_view.points[-1]['event_id']==second['event_id']
        live=point(tracking,4,latitude=25.71,longitude=-100.27)
        send(publisher,{'type':'position.publish','position':live}); receive(publisher,'position.ack')
        assert wait_until(lambda:tracker.cursor==4 and states[-1]=='LIVE',1500)
        assert latest[0]['event_id']==live['event_id']
        output=Path(os.environ['DESKTOP_CAPTURE_DIR']); output.mkdir(parents=True,exist_ok=True)
        app.processEvents(); map_view.grab().save(str(output/'mapa-wss-sintetico.png'))
        p.ok('transporte','POST',f"/api/v1/tracking/assignments/{tracking['assignment']['id']}/revoke",user='coordinator1',data={'version':1,'human_confirmation':True,'reason':'Fin de seguimiento sintético'})
        assert wait_until(lambda:bool(terminated),1500)
        assert tracker.stopped and not map_view.points
    finally:
        if publisher: publisher.close()
        tracker.stop(); bad.stop(); map_view.stop(); map_view.close()
        QSslConfiguration.setDefaultConfiguration(original)
        QStandardPaths.setTestModeEnabled(False)
