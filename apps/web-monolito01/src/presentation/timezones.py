"""Zona de interfaz explícita; almacenamiento y servicios conservan UTC."""
from datetime import timezone
from zoneinfo import ZoneInfo
from flask import g, has_request_context, request

ZONES={'UTC':'UTC', 'America/Monterrey':'Monterrey'}

def selected_zone():
    if not has_request_context(): return 'UTC'
    value=request.form.get('_timezone',request.cookies.get('display_timezone','UTC')) if request.method=='POST' else request.cookies.get('display_timezone','UTC')
    return value if value in ZONES else 'UTC'

def local_value(value):
    return value.astimezone(ZoneInfo(selected_zone()))

def datefmt(value):
    return local_value(value).strftime('%d/%m/%Y · %H:%M') if value else '—'

def inputfmt(value):
    return local_value(value).strftime('%Y-%m-%dT%H:%M') if value else ''
