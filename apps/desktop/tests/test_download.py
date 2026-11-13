import hashlib
import pytest
from redhouse_desktop.download import DownloadError, approved_url, download

class Response:
    status_code=200
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def iter_content(self,size): yield b'reporte ficticio'

def test_download_checks_origin_hash_and_overwrite(tmp_path,monkeypatch):
    monkeypatch.setattr('redhouse_desktop.download.requests.get',lambda *args,**kwargs:Response())
    expected=hashlib.sha256(b'reporte ficticio').hexdigest(); path=tmp_path/'reporte.pdf'
    download('https://storage.googleapis.com/bucket/obj?signature=x','https://lab',expected,path)
    assert path.read_bytes()==b'reporte ficticio'
    with pytest.raises(DownloadError): download('https://storage.googleapis.com/bucket/obj?signature=x','https://lab',expected,path)
    with pytest.raises(DownloadError): download('https://storage.googleapis.com/bucket/obj?signature=x','https://lab','0'*64,path,overwrite=True)
    assert path.read_bytes()==b'reporte ficticio'
    with pytest.raises(DownloadError): approved_url('https://evil.example/file','https://lab')
    with pytest.raises(DownloadError): approved_url('http://storage.googleapis.com/bucket/object','https://lab')
    approved_url('https://lab/storage/v1/objects/token','https://lab')
    with pytest.raises(DownloadError): approved_url('https://lab/api/v1/private','https://lab')


def test_explicit_storage_origin_is_required_for_alternate_host(monkeypatch):
    with pytest.raises(DownloadError): approved_url('https://store.example/storage/v1/objects/token','https://lab')
    monkeypatch.setenv('REDHOUSE_STORAGE_ORIGIN','https://store.example')
    approved_url('https://store.example/storage/v1/objects/token','https://lab')
    with pytest.raises(DownloadError): approved_url('https://store.example/otro/token','https://lab')


@pytest.mark.parametrize('path',[
    '/storage/v1/objects/../private', '/storage/v1/objects/%2e%2e/private',
    '/storage/v1/objects/token/extra', '/storage/v1/objects/token?x=1',
    '/storage/v1/objects/token?', '/storage/v1/objects/',
])
def test_local_capability_rejects_extra_path_and_query(path,monkeypatch):
    monkeypatch.setenv('REDHOUSE_STORAGE_ORIGIN','https://store.example')
    for host in ('lab','store.example'):
        with pytest.raises(DownloadError): approved_url('https://'+host+path,'https://lab')
