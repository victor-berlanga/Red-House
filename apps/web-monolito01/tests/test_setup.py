"""Instalación segura: archivos temporales y bases aleatorias, nunca el .env real."""
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from urllib.parse import quote, urlencode
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import pytest

from scripts import setup_local as setup


@pytest.fixture
def new_database():
    base = os.getenv('TEST_POSTGRES_URL')
    if not base:
        pytest.skip('Requiere TEST_POSTGRES_URL hacia un clúster dedicado a pruebas.')
    name = 'red_house_test_' + uuid4().hex
    with psycopg.connect(base, autocommit=True) as control:
        assert not control.execute('SELECT 1 FROM pg_database WHERE datname=%s', (name,)).fetchone()
    try:
        yield make_conninfo(base, dbname=name)
    finally:
        # Nombre único comprobado ausente antes del caso: solo puede ser su base de prueba.
        with psycopg.connect(base, autocommit=True) as control:
            if control.execute('SELECT 1 FROM pg_database WHERE datname=%s', (name,)).fetchone():
                control.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))


def configuration(connection):
    return {'APP_ENV':'development', 'DATABASE_URL':connection,
            'SECRET_KEY':secrets.token_urlsafe(48), 'JWT_SECRET_KEY':secrets.token_urlsafe(48),
            'HOST':'127.0.0.1', 'PORT':'5050', 'HIGHCHARTS_ENABLED':'true'}


@pytest.mark.parametrize('name', ['postgres','template0','template1','UPPER','a-b',"x';drop",'a'*64,''])
def test_unsafe_database_names_are_rejected(name):
    with pytest.raises(setup.SetupError):
        setup.valid_database_name(name)


@pytest.mark.parametrize('value', ['0','65536','NaN','1.5',None])
def test_invalid_ports_are_rejected(value):
    with pytest.raises(setup.SetupError):
        setup.valid_port(value)


@pytest.mark.parametrize('url', ['postgresql://remote.example/red_house',
    'postgresql:///red_house', 'postgresql://127.0.0.1/postgres',
    'dbname=red_house host=/tmp,remote.example',
    'dbname=red_house host=localhost hostaddr=198.51.100.1',
    'dbname=red_house host=localhost service=external'])
def test_installer_refuses_nonlocal_or_system_targets(url):
    with pytest.raises(setup.SetupError):
        setup.local_connection(url)


def test_malformed_connection_does_not_print_credentials():
    with pytest.raises(setup.SetupError) as error:
        setup.local_connection('fake_password_value secret')
    assert 'fake_password_value' not in str(error.value)


def test_platform_paths_and_readonly_bootstrap(tmp_path):
    assert setup.virtual_python(tmp_path, windows=True) == tmp_path / '.venv/Scripts/python.exe'
    assert setup.virtual_python(tmp_path, windows=False) == tmp_path / '.venv/bin/python'
    with pytest.raises(setup.SetupError):
        setup.bootstrap(tmp_path, check_only=True)
    assert not (tmp_path / '.venv').exists()


def test_existing_incomplete_venv_is_not_replaced(tmp_path):
    target = tmp_path / '.venv'
    target.mkdir()
    sentinel = target / 'keep.txt'
    sentinel.write_text('No borrar', encoding='utf8')
    with pytest.raises(setup.SetupError):
        setup.bootstrap(tmp_path, check_only=False)
    assert sentinel.read_text() == 'No borrar'


def test_private_env_roundtrip_and_exclusive_creation(tmp_path):
    password = "special '#$\\@:&%? prueba"
    uri = 'postgresql://postgres:' + quote(password, safe='') + '@/red_house?' + urlencode({'host':'127.0.0.1','port':5432})
    values = configuration(uri)
    target = tmp_path / '.env'
    setup.write_configuration(target, values)
    assert setup.read_configuration(target) == values
    assert conninfo_to_dict(setup.local_connection(values['DATABASE_URL']))['password'] == password
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        setup.write_configuration(target, configuration(uri))
    assert target.read_bytes() == original
    if os.name != 'nt':
        assert target.stat().st_mode & 0o777 == 0o600


def test_invalid_existing_env_is_preserved(tmp_path):
    target = tmp_path / '.env'
    target.write_text('APP_ENV=production\n',encoding='utf8')
    with pytest.raises(setup.SetupError):
        setup.read_configuration(target)
    assert target.read_text() == 'APP_ENV=production\n'


@pytest.mark.skipif(os.name == 'nt', reason='La prueba de shell POSIX se ejecuta en macOS/Linux.')
def test_shell_wrapper_accepts_paths_and_arguments_with_spaces(tmp_path):
    project = tmp_path / 'red house folder'
    (project / 'scripts').mkdir(parents=True)
    shutil.copyfile(setup.APP_ROOT / 'setup.sh', project / 'setup.sh')
    (project / 'scripts/setup_local.py').write_text('import sys\nprint(sys.argv[1])\n',encoding='utf8')
    result = subprocess.run(['sh',str(project/'setup.sh'),'argumento con espacios'],cwd=tmp_path,
                            capture_output=True,text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == 'argumento con espacios'


@pytest.mark.skipif(os.name == 'nt', reason='El intérprete señuelo es un script POSIX.')
def test_run_selects_local_venv_without_activation(tmp_path):
    project = tmp_path / 'red house'
    (project / '.venv/bin').mkdir(parents=True)
    shutil.copyfile(setup.APP_ROOT / 'run.py', project / 'run.py')
    executable = project / '.venv/bin/python'
    executable.write_text('#!/bin/sh\nprintf "%s\\n" "VENV_SELECTED" "$1"\n',encoding='utf8')
    executable.chmod(0o700)
    result = subprocess.run([sys.executable,str(project/'run.py')],cwd=tmp_path,capture_output=True,text=True)
    assert result.returncode == 0
    assert result.stdout.splitlines() == ['VENV_SELECTED',str(project/'run.py')]


def test_run_without_setup_has_clear_error(tmp_path):
    shutil.copyfile(setup.APP_ROOT/'run.py',tmp_path/'run.py')
    result = subprocess.run([sys.executable,str(tmp_path/'run.py')],capture_output=True,text=True)
    assert result.returncode != 0
    assert 'setup.cmd' in result.stderr and 'setup.sh' in result.stderr


def test_fresh_install_then_repeat_and_check_preserve_data(new_database, tmp_path, monkeypatch):
    values = configuration(new_database)
    monkeypatch.setattr(setup,'new_configuration',lambda:values)
    password = secrets.token_urlsafe(24)
    prompts = []
    monkeypatch.setattr(setup,'demo_password',lambda:prompts.append(1) or password)
    assert setup.configure(tmp_path,setup.SCHEMA_PATH) == {'institutions':2,'accounts':4,'units':36}
    original = (tmp_path/'.env').read_bytes()
    with psycopg.connect(new_database) as conn:
        before = conn.execute('SELECT account_id,password_hash FROM red_house.user_account ORDER BY account_id').fetchall()
        event_count = conn.execute('SELECT count(*) FROM red_house.audit_event').fetchone()
    setup.configure(tmp_path,setup.SCHEMA_PATH)
    setup.configure(tmp_path,setup.SCHEMA_PATH,check_only=True)
    assert (tmp_path/'.env').read_bytes() == original
    assert len(prompts) == 1
    with psycopg.connect(new_database) as conn:
        assert conn.execute('SELECT account_id,password_hash FROM red_house.user_account ORDER BY account_id').fetchall() == before
        assert conn.execute('SELECT count(*) FROM red_house.audit_event').fetchone() == event_count


def test_database_name_collision_does_not_write_env(new_database, tmp_path, monkeypatch):
    setup.create_database(new_database,allow_existing=False)
    monkeypatch.setattr(setup,'new_configuration',lambda:configuration(new_database))
    with pytest.raises(setup.SetupError,match='ya existe'):
        setup.configure(tmp_path,setup.SCHEMA_PATH)
    assert not (tmp_path/'.env').exists()


def test_existing_foreign_objects_are_not_touched(new_database, tmp_path):
    setup.create_database(new_database,allow_existing=False)
    with psycopg.connect(new_database) as conn:
        conn.execute('CREATE TABLE public.sentinel (value text)')
        conn.execute("INSERT INTO public.sentinel VALUES ('Conservar')")
    setup.write_configuration(tmp_path/'.env',configuration(new_database))
    with pytest.raises(setup.SetupError,match='objetos ajenos'):
        setup.configure(tmp_path,setup.SCHEMA_PATH)
    with psycopg.connect(new_database) as conn:
        assert conn.execute('SELECT value FROM public.sentinel').fetchone() == ('Conservar',)
        assert conn.execute("SELECT 1 FROM pg_namespace WHERE nspname='red_house'").fetchone() is None


def test_cancelled_seed_rolls_back_schema_and_can_resume(new_database, tmp_path, monkeypatch):
    monkeypatch.setattr(setup,'new_configuration',lambda:configuration(new_database))
    def cancel():
        raise EOFError('Cancelación de prueba')
    monkeypatch.setattr(setup,'demo_password',cancel)
    with pytest.raises(EOFError):
        setup.configure(tmp_path,setup.SCHEMA_PATH)
    original = (tmp_path/'.env').read_bytes()
    with psycopg.connect(new_database) as conn:
        assert conn.execute("SELECT 1 FROM pg_namespace WHERE nspname='red_house'").fetchone() is None
    monkeypatch.setattr(setup,'demo_password',lambda:secrets.token_urlsafe(24))
    assert setup.configure(tmp_path,setup.SCHEMA_PATH)['accounts'] == 4
    assert (tmp_path/'.env').read_bytes() == original


def test_partial_schema_is_not_repaired_or_overwritten(new_database):
    setup.create_database(new_database,allow_existing=False)
    with psycopg.connect(new_database) as conn:
        conn.execute('CREATE SCHEMA red_house')
        conn.execute('CREATE TABLE red_house.sentinel (value integer)')
    with pytest.raises(setup.SetupError,match='no coincide'):
        setup.prepare_database(new_database,setup.SCHEMA_PATH)
    with psycopg.connect(new_database) as conn:
        assert conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='red_house'").fetchall() == [('sentinel',)]


def test_check_only_never_initializes_an_empty_database(new_database):
    setup.create_database(new_database,allow_existing=False)
    with pytest.raises(setup.SetupError,match='Falta el esquema'):
        setup.prepare_database(new_database,setup.SCHEMA_PATH,check_only=True)
    with psycopg.connect(new_database) as conn:
        assert conn.execute("SELECT 1 FROM pg_namespace WHERE nspname='red_house'").fetchone() is None
