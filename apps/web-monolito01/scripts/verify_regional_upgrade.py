"""Respalda, prueba en copia y opcionalmente migra la instalación existente.

La copia se crea con UUID en un clúster de pruebas indicado explícitamente.
Las credenciales se transmiten a pg_dump por entorno, nunca se imprimen.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict,make_conninfo
from psycopg.rows import dict_row

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.config.settings import settings
from src.data_access.migrations import migrate


def connect(dsn):
    return psycopg.connect(dsn,row_factory=dict_row,options='-c search_path=red_house,pg_catalog -c statement_timeout=30000')


def fingerprint(conn,columns=None):
    if columns is None:
        rows=conn.execute("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema='red_house' AND table_name<>'blood_inventory' ORDER BY table_name,ordinal_position").fetchall()
        columns={}
        for row in rows:columns.setdefault(row['table_name'],[]).append(row['column_name'])
    result={}
    for table,names in columns.items():
        rows=conn.execute(sql.SQL('SELECT {} FROM {}').format(sql.SQL(',').join(map(sql.Identifier,names)),sql.Identifier(table))).fetchall()
        if table=='role':
            # Único cambio de datos planificado: habilitar los tres perfiles nuevos.
            for row in rows:
                if row['role_code'] in ('MEDICAL','COORDINATOR','TRANSPORT'):row['is_enabled']=True
        encoded=sorted(json.dumps(row,sort_keys=True,default=str,ensure_ascii=False) for row in rows)
        result[table]={'rows':len(rows),'sha256':hashlib.sha256('\n'.join(encoded).encode()).hexdigest()}
    return columns,result


def pgenv(dsn):
    values=conninfo_to_dict(dsn)
    env=dict(os.environ)
    for k,v in values.items():
        variable={'dbname':'PGDATABASE','host':'PGHOST','port':'PGPORT','user':'PGUSER','password':'PGPASSWORD','sslmode':'PGSSLMODE'}.get(k)
        if variable:env[variable]=v
    return env


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--test-connection')
    parser.add_argument('--backup-dir',type=Path)
    parser.add_argument('--report',type=Path)
    parser.add_argument('--catalog-only',type=Path)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    original=settings()['DATABASE_URL']
    if args.catalog_only:
        with connect(original) as conn:
            conn.read_only=True
            columns=conn.execute("""SELECT c.table_name,c.column_name,c.data_type,c.character_maximum_length,c.is_nullable,c.column_default
                FROM information_schema.columns c JOIN information_schema.tables t USING(table_catalog,table_schema,table_name)
                WHERE c.table_schema='red_house' AND t.table_type='BASE TABLE' ORDER BY c.table_name,c.ordinal_position""").fetchall()
            constraints=conn.execute("""SELECT r.relname AS table_name,c.conname AS name,c.contype AS type,pg_get_constraintdef(c.oid) AS definition
                FROM pg_constraint c JOIN pg_class r ON r.oid=c.conrelid JOIN pg_namespace n ON n.oid=r.relnamespace
                WHERE n.nspname='red_house' ORDER BY r.relname,c.conname""").fetchall()
            indexes=conn.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='red_house' ORDER BY tablename,indexname").fetchall()
        args.catalog_only.parent.mkdir(parents=True,exist_ok=True)
        args.catalog_only.write_text(json.dumps({'columns':columns,'constraints':constraints,'indexes':indexes},indent=2,default=str)+'\n')
        print(json.dumps({'result':'PASS','catalog_tables':len({x['table_name'] for x in columns})}))
        return
    if not all((args.test_connection,args.backup_dir,args.report)):
        parser.error('Indica test-connection, backup-dir y report para verificar una actualización.')
    original_parts=conninfo_to_dict(original);test_parts=conninfo_to_dict(args.test_connection)
    if (original_parts.get('host',''),original_parts.get('port','5432'))==(test_parts.get('host',''),test_parts.get('port','5432')):
        raise RuntimeError('Se requiere un clúster distinto para la copia de verificación.')
    args.backup_dir.mkdir(parents=True,exist_ok=True);args.backup_dir.chmod(0o700)
    backup=args.backup_dir/('before-regional-'+uuid4().hex+'.dump')
    with connect(original) as conn:
        conn.read_only=True
        columns,before=fingerprint(conn)
    old_umask=os.umask(0o077)
    try:
        result=subprocess.run(['pg_dump','-Fc','--no-owner','--no-acl','--schema=red_house','--file='+str(backup)],env=pgenv(original),capture_output=True)
    finally:os.umask(old_umask)
    if result.returncode:raise RuntimeError('No se pudo generar el respaldo; no se modificó la base original.')
    backup.chmod(0o600)
    name='red_house_upgrade_'+uuid4().hex
    copydsn=make_conninfo(args.test_connection,dbname=name)
    with psycopg.connect(args.test_connection,autocommit=True) as control:
        control.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    try:
        result=subprocess.run(['pg_restore','--no-owner','--no-acl','--exit-on-error','--dbname='+name,str(backup)],env=pgenv(copydsn),capture_output=True)
        if result.returncode:raise RuntimeError('No se restauró la copia; la base original permanece intacta.')
        with connect(copydsn) as conn:
            assert fingerprint(conn,columns)[1]==before,'La copia no coincide con el estado inicial.'
            versions=migrate(conn)
            assert fingerprint(conn,columns)[1]==before,'La migración cambió datos que debían conservarse.'
        with connect(copydsn) as conn:
            assert migrate(conn)==[],'La repetición no fue idempotente.'
            tables=conn.execute("SELECT count(*) AS n FROM information_schema.tables WHERE table_schema='red_house' AND table_type='BASE TABLE'").fetchone()['n']
        applied=False
        if args.apply:
            with connect(original) as conn:
                assert fingerprint(conn,columns)[1]==before,'La base cambió desde el respaldo: repetir la verificación.'
                migrate(conn)
                assert fingerprint(conn,columns)[1]==before,'Se rechazó una modificación inesperada.'
            applied=True
        report={'result':'PASS','copy_restored':True,'copy_migrated':True,'repeat_idempotent':True,
            'original_migrated':applied,'versions':versions,'tables_after':tables,'preserved_tables':before,
            'backup_file':str(backup),'backup_mode':'600','limit':'Solo cambia la habilitación de MEDICAL, COORDINATOR y TRANSPORT; no se crean cuentas ni datos clínicos.'}
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({k:report[k] for k in ('result','copy_restored','copy_migrated','repeat_idempotent','original_migrated','tables_after')}))
    finally:
        with psycopg.connect(args.test_connection,autocommit=True) as control:
            control.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))


if __name__=='__main__':main()
