"""Cliente XML aislado: contratos fijados, TLS verificado y sesión en memoria."""
from __future__ import annotations
import json
import math
import re
import time
import threading
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import requests
from jsonschema import Draft202012Validator, FormatChecker
from lxml import etree

CONTRACTS = Path(__file__).parent / 'contracts'
MAX_BYTES = 2_000_000
IDENTITY_READ_TTL = 5.0
# Versiones de proceso verificadas por servicio; no son la versión de OpenAPI.
SERVICE_VERSIONS = {
    'identidad': frozenset({'0.4.1'}), 'inventario': frozenset({'0.4.1'}), 'donantes': frozenset({'0.4.1'}),
    'receptores': frozenset({'0.4.1'}), 'alertas': frozenset({'0.4.1'}),
    'transporte': frozenset({'0.4.1'}), 'documentos': frozenset({'0.4.1'}),
    'custodia': frozenset({'0.4.1'}), 'auditoria': frozenset({'0.4.1'}),
    'compatibilidad': frozenset({'0.4.4'}), 'priorizacion_geografia': frozenset({'0.4.4'}),
}

class ContractError(Exception):
    pass

CLIENT_HEADER, CLIENT_NAME = 'X-RedHouse-Client', 'desktop'


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status, self.code = status, code
        self.details = details or []

    def challenge(self):
        if self.status != 403 or self.code != 'reauthentication_required': return None
        matches=[item.get('challenge') for item in self.details if isinstance(item,dict) and item.get('field')=='reauthentication' and item.get('code')=='challenge']
        if len(matches)!=1 or not isinstance(matches[0],str) or not 1<=len(matches[0])<=4096: raise ContractError('Reto de confirmación inválido.')
        return matches[0]


def parser():
    return etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False)


def read_xml(raw):
    if len(raw) > MAX_BYTES or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ContractError('XML rechazado por seguridad.')
    try:
        root = etree.fromstring(raw, parser())
        if root.getroottree().docinfo.doctype:
            raise ContractError('DTD no permitido.')
        if sum(1 for _ in root.iter()) > 20000 or any(len(list(n.iterancestors())) > 40 for n in root.iter()):
            raise ContractError('XML excede límites.')
        return root
    except etree.XMLSyntaxError as exc:
        raise ContractError('XML inválido.') from exc


def schema(name):
    return etree.XMLSchema(etree.parse(str(CONTRACTS / name), parser()))


def request_xml(data, name):
    root = etree.Element('request')
    def add(parent, key, value, depth=0):
        if depth>32: raise ContractError('Solicitud demasiado profunda.')
        try: child=etree.SubElement(parent,key)
        except (TypeError,ValueError) as exc: raise ContractError('Campo XML inválido.') from exc
        if value is None: child.set('{http://www.w3.org/2001/XMLSchema-instance}nil','true')
        elif isinstance(value,dict):
            for nested,item in value.items(): add(child,nested,item,depth+1)
        elif isinstance(value,list):
            for item in value: add(child,'item',item,depth+1)
        elif isinstance(value,bool): child.text='true' if value else 'false'
        elif isinstance(value,float) and not math.isfinite(value): raise ContractError('Número no finito.')
        else: child.text=str(value)
    for key, value in data.items(): add(root,key,value)
    if sum(1 for _ in root.iter())>20000: raise ContractError('Solicitud demasiado grande.')
    if not schema(name).validate(root):
        raise ContractError('Datos no cumplen el contrato de solicitud.')
    return etree.tostring(root, encoding='UTF-8', xml_declaration=True)


def value(node):
    kind = node.get('type')
    children = list(node)
    if kind in ('object','array') and ((node.text or '').strip() or any((child.tail or '').strip() for child in children)):
        raise ContractError('Contenido XML mixto inválido.')
    if kind == 'object':
        if any(x.tag != 'field' or not x.get('name') for x in children): raise ContractError('Objeto XML inválido.')
        names = [x.get('name') for x in children]
        if len(names) != len(set(names)): raise ContractError('Campo duplicado.')
        return {x.get('name'): value(x) for x in children}
    if kind == 'array':
        if any(x.tag != 'item' for x in children): raise ContractError('Lista XML inválida.')
        return [value(x) for x in children]
    if children: raise ContractError('Valor XML inválido.')
    text = node.text or ''
    try:
        if kind == 'string': return text
        if kind == 'integer':
            if not re.fullmatch(r'-?[0-9]+',text): raise ValueError()
            return int(text)
        if kind == 'number':
            number=float(text)
            if not math.isfinite(number): raise ValueError()
            return number
        if kind == 'boolean' and text in ('true', 'false'): return text == 'true'
        if kind == 'null' and not text.strip(): return None
    except ValueError as exc: raise ContractError('Tipo XML inválido.') from exc
    raise ContractError('Tipo XML inválido.')


def decode(raw, service, operation, success):
    root = read_xml(raw)
    if not schema('response.xsd').validate(root): raise ContractError('Respuesta no cumple XSD.')
    result = value(root)
    spec = json.loads((CONTRACTS / (service + '.json')).read_text())
    definition = 'Response_' + operation if success else 'Error'
    validator = Draft202012Validator({'$ref': '#/components/schemas/' + definition, 'components': spec['components']}, format_checker=FormatChecker())
    if not validator.is_valid(result): raise ContractError('Respuesta no cumple DTO de operación.')
    expected_service = 'identidad_acceso' if service == 'identidad' else service
    if result['meta']['service'] != expected_service or result['meta']['version'] not in SERVICE_VERSIONS.get(service, frozenset()):
        raise ContractError('Servicio o versión incompatibles con el contrato instalado.')
    return result

from .session_context import session_id

class Client:
    def __init__(self, base):
        u = urlsplit(base)
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('Se requiere URL HTTPS sin credenciales ni parámetros.')
        self.base = base.rstrip('/')
        self.access = self.refresh = None
        self.user = None
        self.session_id = None
        self.last_identity_check = 0.0
        self.lock = threading.RLock()

    def call(self, service, path, operation, method='GET', body=None, request_schema=None, params=None, key=None, auth=True, proof=None):
        if not path.startswith('/api/v1/') or '..' in path: raise ValueError('Ruta inválida.')
        # X-RedHouse-Client: aplicación declarada ante Identidad; el servidor rechaza con 403
        # `client_not_allowed` (mensaje en español) al perfil que no corresponde a la consola.
        headers = {'Accept':'application/xml', 'X-Correlation-ID':str(uuid.uuid4()), CLIENT_HEADER:CLIENT_NAME}
        if auth and self.access: headers['Authorization'] = 'Bearer ' + self.access
        if key: headers['Idempotency-Key'] = key
        if proof: headers['X-Reauthentication-Proof'] = proof
        payload = None
        if body is not None:
            payload = request_xml(body, request_schema)
            headers['Content-Type'] = 'application/xml'
        try:
            response = requests.request(method, self.base + '/services/' + service + path, headers=headers, data=payload, params=params, timeout=(5, 15), allow_redirects=False, stream=True)
            with response:
                if response.headers.get('Content-Type','').split(';')[0].strip().lower() != 'application/xml': raise ContractError('El servicio no respondió XML.')
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > MAX_BYTES: raise ContractError('Respuesta demasiado grande.')
                    chunks.append(chunk)
                success = 200 <= response.status_code < 300
                contract_service='identidad' if service=='identidad-acceso' else service.replace('-','_')
                document = decode(b''.join(chunks), contract_service, operation, success)
                if not success:
                    error = document['error']
                    raise ApiError(response.status_code, error['code'], error['message'], error.get('details'))
                return document['data']
        except requests.RequestException as exc:
            raise ConnectionError('No fue posible conectar. Verifica la red y el certificado.') from exc

    def login(self, username, password, otp):
        with self.lock:
            self.clear()
            fields = {'username':username, 'password':password}
            if otp: fields['otp'] = otp
            data = self.call('identidad-acceso','/api/v1/auth/login','login','POST',fields,'login.xsd',auth=False)
            sid = session_id(data['access_token'])
            if not sid: self.clear(); raise ContractError('La sesión recibida no tiene identificador válido.')
            self.access, self.refresh, self.user, self.session_id = data['access_token'], data['refresh_token'], data['user'], sid
            return self.user

    def _check_identity(self, current):
        before=self.user
        if not before or not current.get('active') or any(current.get(key)!=before.get(key) for key in ('id','tenant_id','region_id','role')):
            self.clear()
            raise ApiError(401,'identity_changed','La cuenta o sus permisos cambiaron. Inicia sesión otra vez.')
        self.user=current
        self.last_identity_check=time.monotonic()
        return current

    def _rotate(self):
        token=self.refresh
        self.access=self.refresh=None
        try:
            data=self.call('identidad-acceso','/api/v1/auth/refresh','refresh','POST',{'refresh_token':token},'refresh.xsd',auth=False)
            if not self.session_id or session_id(data['access_token'])!=self.session_id: raise ContractError('La renovación cambió la sesión.')
            self.access,self.refresh=data['access_token'],data['refresh_token']
            current=self.call('identidad-acceso','/api/v1/auth/me','me')
            return self._check_identity(current)
        except Exception:
            self.clear()
            raise

    def authorized(self, service, path, operation, *, fresh_identity=False, **kwargs):
        with self.lock:
            if not self.access: raise ApiError(401,'session','Inicia sesión.')
            is_profile=service=='identidad-acceso' and path=='/api/v1/auth/me'
            needs_check=(is_profile or fresh_identity or kwargs.get('method','GET')!='GET' or
                         not self.last_identity_check or time.monotonic()-self.last_identity_check>=IDENTITY_READ_TTL)
            if needs_check:
                try:
                    current=self.call('identidad-acceso','/api/v1/auth/me','me')
                except ApiError as exc:
                    if exc.status!=401: raise
                    current=self._rotate()
                self._check_identity(current)
                if is_profile: return current
            try: return self.call(service,path,operation,**kwargs)
            except ApiError as exc:
                if exc.status!=401 or exc.code!='unauthorized' or (service=='identidad-acceso' and path=='/api/v1/auth/reauthentication-proofs'): raise
                self._rotate()
                return self.call(service,path,operation,**kwargs)

    def logout(self):
        with self.lock:
            try:
                if self.access: self.call('identidad-acceso','/api/v1/auth/logout','logout','POST',key=str(uuid.uuid4()))
            finally: self.clear()

    def clear(self):
        self.access = self.refresh = self.user = self.session_id = None
        self.last_identity_check = 0.0
