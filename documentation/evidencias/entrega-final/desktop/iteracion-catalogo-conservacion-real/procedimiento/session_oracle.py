"""Familias nuevas y cierre: lecturas SQL/Redis del fixture conservado."""
import json
from pathlib import Path
from urllib.parse import urlsplit
import redis


def snapshot(postgres,state,fixture,user_ids):
    with postgres(state,'identidad_acceso',fixture/'pg') as conn:
        rows=conn.execute('SELECT id,user_id,revoked_at FROM sessions WHERE user_id=ANY(%s::uuid[])',(user_ids,)).fetchall()
    return {str(row[0]) for row in rows}


def closure(postgres,private,state,fixture,user_ids,before):
    with postgres(state,'identidad_acceso',fixture/'pg') as conn:
        rows=conn.execute('SELECT id,user_id,revoked_at FROM sessions WHERE user_id=ANY(%s::uuid[])',(user_ids,)).fetchall()
    created=[row for row in rows if str(row[0]) not in before]
    if len({str(row[0]) for row in created})!=len(created) or any(str(row[1]) not in user_ids or row[2] is None for row in created):
        raise RuntimeError('Familias nuevas no revocadas o ajenas')
    config=json.loads(private(fixture/'identidad_acceso.json').read_text())
    url=state['redis_admin']; parsed=urlsplit(url)
    if parsed.hostname!='127.0.0.1': raise RuntimeError('Redis no corresponde a fixture local')
    client=redis.Redis.from_url(url,socket_connect_timeout=3,socket_timeout=3)
    try:
        keys=[config['REDIS_PREFIX']+'session:'+str(row[0]) for row in created]
        if keys and any(value is not None for value in client.mget(keys)): raise RuntimeError('Sesión aún presente en Redis')
    finally: client.close()
    return [{'id':str(row[0]),'user_id':str(row[1])} for row in created]
