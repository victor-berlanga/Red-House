"""Descarga privada sin redirecciones, con origen restringido y SHA-256."""
import hashlib
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
import requests

MAX_DOWNLOAD=100*1024*1024
class DownloadError(Exception):
    pass

def approved_url(url,base):
    target=urlsplit(url); origin=urlsplit(base)
    if target.scheme!='https' or not target.hostname or target.username or target.password or target.fragment:
        raise DownloadError('La dirección de descarga no es válida.')
    local_capability=bool(re.fullmatch(r'/storage/v1/objects/[A-Za-z0-9_-]+=*',target.path)) and not target.query and '?' not in url
    same_origin=(target.hostname==origin.hostname and (target.port or 443)==(origin.port or 443) and local_capability)
    configured=os.environ.get('REDHOUSE_STORAGE_ORIGIN','')
    storage_origin=urlsplit(configured.rstrip('/')) if configured else None
    additional=bool(storage_origin and storage_origin.scheme=='https' and storage_origin.hostname and not storage_origin.username and not storage_origin.password and not storage_origin.path and not storage_origin.query and not storage_origin.fragment and target.hostname==storage_origin.hostname and (target.port or 443)==(storage_origin.port or 443) and local_capability)
    gcs=(target.hostname=='storage.googleapis.com' and (target.port or 443)==443)
    if not (same_origin or additional or gcs): raise DownloadError('El origen del archivo no está autorizado.')

def download(url,base,expected_sha256,destination,*,overwrite=False):
    approved_url(url,base)
    if not re.fullmatch(r'[0-9a-f]{64}',expected_sha256): raise DownloadError('No hay una huella verificable del archivo.')
    target=Path(destination)
    if target.exists() and not overwrite: raise DownloadError('El archivo ya existe; confirma antes de reemplazarlo.')
    fd,temp=tempfile.mkstemp(prefix='.redhouse-download-',dir=target.parent); digest=hashlib.sha256(); size=0
    try:
        with os.fdopen(fd,'wb') as stream:
            try:
                response=requests.get(url,stream=True,timeout=(5,30),allow_redirects=False)
                with response:
                    if response.status_code!=200: raise DownloadError('No se pudo descargar el archivo.')
                    for chunk in response.iter_content(65536):
                        size+=len(chunk)
                        if size>MAX_DOWNLOAD: raise DownloadError('El archivo supera el tamaño admitido.')
                        digest.update(chunk); stream.write(chunk)
            except requests.RequestException as exc: raise DownloadError('No se pudo descargar el archivo.') from exc
            stream.flush(); os.fsync(stream.fileno())
        if digest.hexdigest()!=expected_sha256: raise DownloadError('La huella del archivo no coincide; no se guardó.')
        if overwrite: os.replace(temp,target)
        else:
            try: os.link(temp,target)
            except FileExistsError as exc: raise DownloadError('El archivo ya existe; confirma antes de reemplazarlo.') from exc
            os.unlink(temp)
    finally:
        if os.path.exists(temp): os.unlink(temp)
