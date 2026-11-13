"""Contratos de seguimiento sintéticos; no abre conexiones."""
import pytest
from redhouse_desktop.client import ContractError, request_xml
from redhouse_desktop.tracking import event_xml, validate_snapshot_point
from redhouse_desktop.native_map import world, coordinates

SHIPMENT='00000000-0000-4000-8000-000000000001'
EVENT='00000000-0000-4000-8000-000000000002'
DEVICE='00000000-0000-4000-8000-000000000003'

def point():
    return {'event_id':EVENT,'shipment_id':SHIPMENT,'device_id':DEVICE,'sequence':1,'captured_at':'2030-01-01T00:00:00+00:00','received_at':'2030-01-01T00:00:01+00:00','cursor':5,'fix_valid':True,'latitude':25.7,'longitude':-100.3,'source':'SIMULATOR','simulated':True}

def event():
    return f'''<request><type>position.updated</type><shipment_id>{SHIPMENT}</shipment_id><cursor>5</cursor><position><event_id>{EVENT}</event_id><shipment_id>{SHIPMENT}</shipment_id><device_id>{DEVICE}</device_id><source>SIMULATOR</source><simulated>true</simulated><sequence>1</sequence><captured_at>2030-01-01T00:00:00+00:00</captured_at><latitude>25.7</latitude><longitude>-100.3</longitude><fix_valid>true</fix_valid><cursor>5</cursor><received_at>2030-01-01T00:00:01+00:00</received_at></position></request>'''

def test_tracking_xml_dto_and_mismatches():
    parsed=event_xml(event(),SHIPMENT)
    assert parsed['position']['latitude']==25.7 and parsed['position']['simulated'] is True
    assert validate_snapshot_point(point(),SHIPMENT)['cursor']==5
    with pytest.raises(ContractError): event_xml(event().replace('<cursor>5</cursor>','<cursor>6</cursor>',1),SHIPMENT)
    with pytest.raises(ContractError): event_xml(event().replace('<latitude>25.7</latitude>','<latitude>NaN</latitude>'),SHIPMENT)
    with pytest.raises(ContractError): event_xml('<!DOCTYPE request><request><type>heartbeat</type></request>',SHIPMENT)
    with pytest.raises(ContractError): validate_snapshot_point(dict(point(),longitude=None),SHIPMENT)
    assert b'<type>heartbeat</type>' in request_xml({'type':'heartbeat'},'tracking_message.xsd')

def test_tracking_status_allows_server_cursor():
    raw=f'<request><type>tracking.status</type><shipment_id>{SHIPMENT}</shipment_id><cursor>5</cursor><state>LIVE</state></request>'
    assert event_xml(raw,SHIPMENT)['state']=='LIVE'

def test_map_projection_roundtrip():
    x,y=world(25.7,-100.3,7); lat,lon=coordinates(x,y,7)
    assert abs(lat-25.7)<1e-8 and abs(lon+100.3)<1e-8


def test_tile_cache_prunes_expired_then_lru_only_owned_files(tmp_path):
    import json, os, time
    from redhouse_desktop.native_map import trim_cache
    now=time.time(); prefix='0123456789abcdef'; pairs=[]
    for index,expires in enumerate((now-1,now+3600,now+3600)):
        image=tmp_path/f'{prefix}-7-{index}-1.png'; meta=image.with_suffix('.json')
        image.write_bytes(b'x'*80); meta.write_text(json.dumps({'expires':expires}))
        os.utime(image,(now-30+index,now-30+index)); pairs.append((image,meta))
    unrelated=tmp_path/'no-borrar.txt'; unrelated.write_text('conservar')
    one_size=pairs[2][0].stat().st_size+pairs[2][1].stat().st_size
    total=trim_cache(tmp_path,limit=one_size,now=now)
    assert total<=one_size and not pairs[0][0].exists() and not pairs[1][0].exists() and pairs[2][0].exists()
    assert unrelated.read_text()=='conservar'
