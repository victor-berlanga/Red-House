"""Diario cifrado y separado por servidor, institución y usuario.

El archivo nunca contiene JWT. La clave solo vive en el llavero nativo.
Un candado huérfano bloquea escrituras hasta revisión manual; no se elimina
automáticamente porque otra instancia podría seguir activa.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
import keyring
from cryptography.fernet import Fernet, InvalidToken

class JournalError(Exception):
    pass

class NativeKey:
    def get(self, identifier, exists):
        backend=keyring.get_keyring()
        if backend.__class__.__module__ not in ('keyring.backends.macOS','keyring.backends.Windows'):
            raise JournalError('El llavero seguro del sistema no está disponible; no se puede registrar la operación.')
        try:
            key=keyring.get_password('RedHouse desktop journal',identifier)
            if key is None:
                if exists: raise JournalError('Falta la clave del diario; solicita recuperación autorizada.')
                key=Fernet.generate_key().decode('ascii')
                keyring.set_password('RedHouse desktop journal',identifier,key)
                if keyring.get_password('RedHouse desktop journal',identifier)!=key:
                    raise JournalError('No se pudo comprobar la clave del diario.')
            return key.encode('ascii')
        except JournalError: raise
        except Exception as exc: raise JournalError('No se puede acceder al llavero seguro.') from exc

class Journal:
    def __init__(self, root, base, user_id, tenant_id, provider=None):
        scope=json.dumps([base.rstrip('/'),tenant_id,user_id],ensure_ascii=True,separators=(',',':'))
        self.identifier=hashlib.sha256(scope.encode()).hexdigest()
        self.root=Path(root); self.file=self.root/(self.identifier+'.bin'); self.lock=self.root/(self.identifier+'.lock')
        self.provider=provider or NativeKey()

    @contextmanager
    def locked(self):
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        try:
            fd=os.open(self.lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except FileExistsError as exc: raise JournalError('Diario ocupado o candado pendiente de revisión.') from exc
        try:
            os.close(fd)
            yield
        finally:
            self.lock.unlink(missing_ok=True)

    def _read(self):
        key=self.provider.get(self.identifier,self.file.exists())
        if not self.file.exists(): return [],key
        raw=self.file.read_bytes()
        if len(raw)>1_000_000: raise JournalError('Diario demasiado grande; solicita revisión.')
        try:
            records=json.loads(Fernet(key).decrypt(raw))
            if not isinstance(records,list): raise ValueError('journal')
            return records,key
        except (InvalidToken, ValueError, TypeError) as exc: raise JournalError('Diario inválido o inaccesible.') from exc

    def _write(self, records, key):
        raw=Fernet(key).encrypt(json.dumps(records,ensure_ascii=False,separators=(',',':')).encode())
        fd,path=tempfile.mkstemp(prefix='.journal-',dir=self.root)
        try:
            if hasattr(os,'fchmod'): os.fchmod(fd,0o600)
            with os.fdopen(fd,'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.replace(path,self.file)
            try:
                directory=os.open(self.root,os.O_RDONLY); os.fsync(directory); os.close(directory)
            except OSError: pass
        finally:
            if os.path.exists(path): os.unlink(path)

    def list(self):
        with self.locked(): return self._read()[0]

    def prepare(self, record):
        required={'key','body','state','operation_id','status'}
        if not required.issubset(record) or set(record)-required-{'kind','target'} or record['state'] not in ('PREPARED','UNCERTAIN'): raise JournalError('Registro inválido.')
        if record.get('kind','RESERVATION') not in ('RESERVATION','LABEL','COMMAND'): raise JournalError('Tipo de operación inválido.')
        if record.get('kind') in ('LABEL','COMMAND') and not record.get('target'): raise JournalError('Falta el destino de la operación.')
        with self.locked():
            records,key=self._read()
            if any(x['state']!='DONE' for x in records): raise JournalError('Hay una operación pendiente de recuperación.')
            records.append(record); self._write(records,key)

    def update(self, key_value, operation):
        with self.locked():
            records,key=self._read()
            record=next((x for x in records if x['key']==key_value),None)
            if record is None: raise JournalError('No se encontró la operación local.')
            record['operation_id']=operation['operation_id']; record['status']=operation['status']
            record['state']='DONE' if operation['status'] in ('COMPLETED','FAILED') else 'PENDING'
            self._write(records,key)

    def print_transition(self, key_value, issuance_id, action):
        """Registra envío incierto y revisión sin volver a usar la autorización."""
        transitions={'start':('AUTHORIZED','PRINT_UNCERTAIN','PENDING'),
                     'sent':('PRINT_UNCERTAIN','COMPLETED','DONE'),
                     'review':('PRINT_UNCERTAIN','PRINT_REVIEWED','DONE')}
        if action not in transitions: raise JournalError('Acción de impresión inválida.')
        with self.locked():
            records,key=self._read()
            record=next((x for x in records if x['key']==key_value),None)
            expected,status,state=transitions[action]
            if (not record or record.get('kind')!='LABEL' or record.get('state')!='PENDING'
                    or record.get('body',{}).get('action')!='PRINT' or record.get('operation_id')!=issuance_id
                    or record.get('status')!=expected):
                raise JournalError('La impresión requiere revisión; no se enviará otra copia.')
            record['status']=status; record['state']=state
            self._write(records,key)
