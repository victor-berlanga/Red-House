"""Proceso efímero: termina tras una respuesta real antes de registrarla localmente."""
import json
import os
import sys
from redhouse_desktop.client import Client
from redhouse_desktop.journal import Journal
from redhouse_desktop.label_issuance import prepare_label, submit_label

input_data=json.load(sys.stdin)
client=Client(input_data['gateway'])
user=client.login(input_data['username'],input_data['password'],'')
store=Journal(input_data['directory'],client.base,user['id'],user['tenant_id'])
record=prepare_label(store,input_data['unit'],'EXPORT_PDF','Emisión sintética de recuperación')

class InterruptedResponse:
    def authorized(self,*args,**kwargs):
        client.authorized(*args,**kwargs)
        os._exit(0)

submit_label(InterruptedResponse(),store,record)
raise AssertionError('No se interrumpió el proceso.')
