"""Descarga privada sin redirecciones, con origen restringido y SHA-256."""
import hashlib
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote, urlsplit
import requests

MAX_DOWNLOAD=100*1024*1024
class DownloadError(Exception):
    pass

def approved_url(url,base):
    try: target=urlsplit(url); origin=urlsplit(base)
    except ValueError as exc: raise DownloadError('La dirección de descarga no es válida.') from exc
    if target.scheme!='https' or not target.hostname or target.username or target.password or target.fragment:
        raise DownloadError('La dirección de descarga no es válida.')
    try: target_port=target.port or 443; origin_port=origin.port or 443
    except ValueError as exc: raise DownloadError('La dirección de descarga no es válida.') from exc
    local_capability=bool(re.fullmatch(r'/storage/v1/objects/[A-Za-z0-9_-]+=*',target.path)) and not target.query and '?' not in url
    same_origin=(target.hostname==origin.hostname and target_port==origin_port and local_capability)
    configured=os.environ.get('REDHOUSE_STORAGE_ORIGIN','')
    try: storage_origin=urlsplit(configured.rstrip('/')) if configured else None
    except ValueError as exc: raise DownloadError('La configuración de almacenamiento no es válida.') from exc
    try: storage_port=(storage_origin.port or 443) if storage_origin else None
    except ValueError as exc: raise DownloadError('La configuración de almacenamiento no es válida.') from exc
    additional=bool(storage_origin and storage_origin.scheme=='https' and storage_origin.hostname and not storage_origin.username and not storage_origin.password and not storage_origin.path and not storage_origin.query and not storage_origin.fragment and target.hostname==storage_origin.hostname and target_port==storage_port and local_capability)
    bucket=os.environ.get('REDHOUSE_GCS_BUCKET','')
    bucket_valid=bool(re.fullmatch(r'[a-z0-9][a-z0-9._-]{1,220}[a-z0-9]',bucket)) and '..' not in bucket
    decoded=unquote(target.path)
    parts=decoded.split('/')
    safe_object=(len(parts)>2 and all(part not in ('','.','..') for part in parts[2:])
                 and '\\' not in decoded and '%' not in decoded and not any(ord(c)<32 for c in decoded))
    gcs=(bucket_valid and target.hostname=='storage.googleapis.com' and target_port==443
         and target.path.startswith('/'+bucket+'/') and safe_object and parts[1]==bucket)
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
