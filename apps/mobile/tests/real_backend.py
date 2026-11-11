"""Disposable real service lab. No cloud writes; secrets live only in a private /tmp directory."""
import sys, os, json, signal, threading, tempfile, ipaddress
from pathlib import Path
from datetime import datetime, timedelta, timezone
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'apps/services'))
from tests.conftest import platform, QuietHandler
from tests.helpers import resource, recipient_request, evaluation, reservation, plan, move
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import make_server
from werkzeug.wrappers import Response

def main():
    directory=Path(tempfile.mkdtemp(prefix='redhouse-mobile-lab-'));directory.chmod(0o700)
    fixture=platform.__wrapped__();p=next(fixture)
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Red House ephemeral mobile lab')])
    cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(datetime.now(timezone.utc)-timedelta(minutes=1)).not_valid_after(datetime.now(timezone.utc)+timedelta(days=2))
          .add_extension(x509.BasicConstraints(ca=True,path_length=None),critical=True)
          .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address('127.0.0.1')),x509.IPAddress(ipaddress.ip_address('10.0.2.2'))]),critical=False).sign(key,hashes.SHA256()))
    (directory/'ca.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    (directory/'key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));(directory/'key.pem').chmod(0o600)
    unit=resource(p);_,demand=recipient_request(p);allocation=reservation(p,evaluation(p,demand,[unit]),unit)
    shipment=move(p,plan(p,allocation['reservation']),'PREPARED','operator1')
    mounts={'/services/'+s.replace('_','-'):app for s,app in p.apps.items()}
    gateway=DispatcherMiddleware(Response('Not found',status=404),mounts)
    server=make_server('127.0.0.1',18443,gateway,threaded=True,ssl_context=(str(directory/'ca.pem'),str(directory/'key.pem')),request_handler=QuietHandler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    data={'gateway':'https://127.0.0.1:18443','android_gateway':'https://10.0.2.2:18443','ca':str(directory/'ca.pem'),'password':p.env.state['password'],'shipment_id':shipment['id'],'resource_id':unit['id'], 'accounts':{k:v['id'] for k,v in p.env.state['accounts'].items()}}
    (directory/'lab.json').write_text(json.dumps(data));(directory/'lab.json').chmod(0o600)
    print(str(directory/'lab.json'),flush=True)
    stopped=threading.Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stopped.set())
    try:
        while not stopped.wait(2):p.drain(2)
    finally:
        server.shutdown();server.server_close();fixture.close()
if __name__=='__main__':main()
