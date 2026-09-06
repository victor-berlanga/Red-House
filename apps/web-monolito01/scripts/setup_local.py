"""Instalador local compartido por setup.sh y setup.cmd; nunca borra datos."""
import argparse
import getpass
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
from urllib.parse import quote, urlencode
import venv
import warnings

APP_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = APP_ROOT.parents[1] / 'data' / 'database' / 'schema.sql'
sys.path.insert(0, str(APP_ROOT))


class SetupError(Exception):
    pass


def virtual_python(root, windows=None):
    windows = os.name == 'nt' if windows is None else windows
    return root / '.venv' / ('Scripts/python.exe' if windows else 'bin/python')


def bootstrap(root, check_only):
    """Instala solo en el venv del proyecto, no en el Python del sistema."""
    if sys.version_info < (3, 12):
        raise SetupError('Se requiere Python 3.12 o superior.')
    target = root / '.venv'
    executable = virtual_python(root)
    if target.is_symlink():
        raise SetupError('.venv no debe ser un enlace a otro entorno. No se modificó.')
    if not target.exists():
        if check_only:
            raise SetupError('Falta .venv. Ejecuta setup.sh o setup.cmd sin --check.')
        print('Creando el entorno virtual local...', flush=True)
        venv.EnvBuilder(with_pip=True).create(target)
    if not (target / 'pyvenv.cfg').is_file() or not executable.is_file():
        raise SetupError('.venv está incompleto o pertenece a otro sistema operativo. No se sobrescribió; consérvalo aparte y vuelve a instalar.')
    if Path(sys.prefix).resolve() != target.resolve():
        return subprocess.call([str(executable), str(Path(__file__).resolve()), *sys.argv[1:]])
    if not check_only:
        print('Comprobando dependencias del monolito...', flush=True)
        subprocess.run([str(executable), '-m', 'pip', 'install', '--disable-pip-version-check',
                        '-r', str(root / 'requirements.txt')], check=True)
    return None


def ask(label, default):
    return input(f'{label} [{default}]: ').strip() or default


def hidden_password(label):
    # No degradar a entrada visible cuando no hay una terminal apropiada.
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        try:
            return getpass.getpass(label)
        except getpass.GetPassWarning:
            raise SetupError('Ejecuta el instalador desde una terminal que permita entrada oculta.') from None


def demo_password():
    from src.business.validators import password as validate
    from src.business.access import BusinessError
    first = hidden_password('Nueva contraseña para las cuatro cuentas DEMO (12–128 caracteres): ')
    try:
        validate(first)
    except BusinessError:
        raise SetupError('La contraseña DEMO debe tener entre 12 y 128 caracteres.') from None
    if first != hidden_password('Confirma la contraseña DEMO: '):
        raise SetupError('Las contraseñas no coinciden. No se cargaron datos.')
    return first


def valid_database_name(value):
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}', value) or value in {'postgres', 'template0', 'template1'}:
        raise SetupError('Usa un nombre de base exclusivo: letras minúsculas, números y guion bajo; nunca una base del sistema.')
    return value


def valid_port(value):
    try:
        number = int(value)
        if not 1 <= number <= 65535:
            raise ValueError
        return number
    except (ValueError, TypeError):
        raise SetupError('El puerto debe ser un número entre 1 y 65535.') from None


def local_connection(value):
    import psycopg
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    try:
        options = conninfo_to_dict(value)
    except psycopg.Error:
        raise SetupError('DATABASE_URL no tiene un formato válido; se omitió su contenido por privacidad.') from None
    valid_database_name(options.get('dbname', ''))
    host = options.get('host', '')
    # No usar PGSERVICE/PGHOST implícitos ni aceptar hosts remotos o listas de hosts.
    if ',' in host or (host not in {'localhost', '127.0.0.1', '::1'} and not (os.name != 'nt' and host.startswith('/'))):
        raise SetupError('DATABASE_URL debe indicar explícitamente localhost, 127.0.0.1, ::1 o un socket local absoluto.')
    if options.get('hostaddr', '') not in {'', '127.0.0.1', '::1'} or options.get('service'):
        raise SetupError('No se admiten servicios ni direcciones remotas en este instalador local.')
    valid_port(options.get('port', '5432'))
    return make_conninfo(value, connect_timeout=5)


def new_configuration():
    default_host = '127.0.0.1'
    if os.name != 'nt':
        for directory in ('/tmp', '/var/run/postgresql'):
            if (Path(directory) / '.s.PGSQL.5432').exists():
                default_host = directory
                break
    print('PostgreSQL debe estar instalado y encendido. No se cambian servicios ni usuarios del sistema.')
    host = ask('Servidor o directorio de socket PostgreSQL', default_host)
    port = valid_port(ask('Puerto PostgreSQL', '5432'))
    user = ask('Usuario PostgreSQL con permiso para crear la base', 'postgres' if os.name == 'nt' else getpass.getuser())
    database = valid_database_name(ask('Nombre de una base NUEVA para Red House', 'red_house'))
    password = hidden_password('Contraseña PostgreSQL (Enter si tu instalación local no la requiere): ')
    web_port = valid_port(ask('Puerto de la página web', '5050'))
    authority = quote(user, safe='') + (':' + quote(password, safe='') if password else '')
    url = f'postgresql://{authority}@/{database}?' + urlencode({'host': host, 'port': port})
    local_connection(url)
    return {'APP_ENV': 'development', 'DATABASE_URL': url, 'SECRET_KEY': secrets.token_urlsafe(48),
            'JWT_SECRET_KEY': secrets.token_urlsafe(48), 'HOST': '127.0.0.1',
            'PORT': str(web_port), 'HIGHCHARTS_ENABLED': 'true'}


def read_configuration(path):
    from dotenv import dotenv_values
    if path.is_symlink():
        raise SetupError('.env no debe ser un enlace a un archivo externo.')
    values = dotenv_values(path, interpolate=False)
    if values.get('APP_ENV') != 'development':
        raise SetupError('El instalador solo admite APP_ENV=development. Se conservó tu .env.')
    for key in ('SECRET_KEY', 'JWT_SECRET_KEY'):
        if len(values.get(key) or '') < 32:
            raise SetupError(f'Completa {key} en el .env existente; no se reemplazan claves automáticamente.')
    if values['SECRET_KEY'] == values['JWT_SECRET_KEY']:
        raise SetupError('Las dos claves del .env deben ser distintas. No se modificó el archivo.')
    if values.get('HOST', '127.0.0.1') not in {'127.0.0.1', 'localhost', '::1'}:
        raise SetupError('El instalador solo prepara una web de acceso local.')
    valid_port(values.get('PORT', '5000'))
    local_connection(values.get('DATABASE_URL') or '')
    return values


def write_configuration(path, values):
    # Creación exclusiva: ni una carrera ni una repetición sobreescriben secretos.
    content = '# Configuración local privada. No versionar ni compartir.\n'
    for key, value in values.items():
        escaped = str(value).replace('\\', '\\\\').replace("'", "\\'")
        content += f"{key}='{escaped}'\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as output:
        output.write(content)
    print('.env local creado. No se muestran claves ni credenciales.')


def create_database(connection, *, allow_existing, before_create=lambda: None):
    """CREATE DATABASE requiere autocommit; no existe una operación DROP aquí."""
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    name = conninfo_to_dict(connection)['dbname']
    with psycopg.connect(make_conninfo(connection, dbname='postgres'), autocommit=True) as control:
        if control.info.server_version < 140000:
            raise SetupError('Se requiere PostgreSQL 14 o superior.')
        exists = control.execute('SELECT 1 FROM pg_database WHERE datname=%s', (name,)).fetchone()
        if exists and not allow_existing:
            raise SetupError('Esa base ya existe y no hay .env que la vincule al proyecto. Elige un nombre nuevo; no se modificó la base.')
        before_create()
        if not exists:
            control.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8' TEMPLATE template0").format(sql.Identifier(name)))
            print(f'Base nueva creada: {name}.')
        else:
            print('La base configurada ya existe; se comprobará sin reinicializar datos.')


def prepare_database(connection, schema_path, *, check_only=False, password_reader=None):
    import psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
    from src.cli import seed_demo
    source = schema_path.read_text(encoding='utf-8')
    expected = set(re.findall(r'^CREATE TABLE ([a-z_]+) \(', source, re.MULTILINE))
    with psycopg.connect(connection, row_factory=dict_row,
                         options='-c search_path=red_house,pg_catalog -c statement_timeout=10000') as conn:
        conn.read_only = check_only
        if conn.info.server_version < 140000:
            raise SetupError('Se requiere PostgreSQL 14 o superior.')
        if not check_only:
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended('red-house-local-setup', 0))")
        present = conn.execute("SELECT 1 FROM pg_namespace WHERE nspname='red_house'").fetchone()
        if not present:
            if check_only:
                raise SetupError('Falta el esquema. Ejecuta el instalador sin --check.')
            occupied = conn.execute("""SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema' LIMIT 1""").fetchone()
            other_schema = conn.execute("""SELECT 1 FROM pg_namespace
                WHERE nspname !~ '^pg_' AND nspname NOT IN ('public','information_schema') LIMIT 1""").fetchone()
            if occupied or other_schema:
                raise SetupError('La base contiene objetos ajenos a Red House. No se inicializó ni se borró nada.')
            conn.execute(source)
        actual = {r['table_name'] for r in conn.execute("""SELECT table_name FROM information_schema.tables
            WHERE table_schema='red_house' AND table_type='BASE TABLE'""")}
        if actual != expected or not conn.execute("SELECT to_regclass('red_house.blood_inventory') AS view").fetchone()['view']:
            raise SetupError('El esquema no coincide con este incremento. No se migra ni se repara automáticamente.')
        # Todo registro existente se conserva, incluso si no corresponde a la carga DEMO.
        accounts = conn.execute('SELECT count(*) AS n FROM user_account').fetchone()['n']
        if accounts:
            print('Esquema y cuentas existentes conservados. No se repite la carga ni se cambian contraseñas.')
        else:
            if check_only:
                raise SetupError('Aún no hay cuentas. Ejecuta el instalador sin --check.')
            initial_catalogs = {'role', 'capability', 'blood_status_transition'}
            for table in expected - initial_catalogs:
                if conn.execute(sql.SQL('SELECT 1 FROM {} LIMIT 1').format(sql.Identifier(table))).fetchone():
                    raise SetupError('Hay datos previos sin cuentas. No se mezclará una carga DEMO con esos registros.')
            seed_demo(conn, (password_reader or demo_password)())
            print('Carga DEMO completa: 4 cuentas y 36 unidades ficticias. La contraseña solo se conserva como hash.')
        return conn.execute("""SELECT (SELECT count(*) FROM institution) AS institutions,
            (SELECT count(*) FROM user_account) AS accounts, (SELECT count(*) FROM blood_unit) AS units""").fetchone()


def configure(root, schema_path, *, check_only=False):
    import psycopg
    env_path = root / '.env'
    if env_path.is_symlink():
        raise SetupError('.env no debe ser un enlace a otro archivo.')
    existing = env_path.exists()
    if check_only and not existing:
        raise SetupError('Falta .env. Ejecuta primero el instalador sin --check.')
    values = read_configuration(env_path) if existing else new_configuration()
    try:
        connection = local_connection(values['DATABASE_URL'])
        if not check_only:
            create_database(connection, allow_existing=existing,
                            before_create=(lambda: None) if existing else lambda: write_configuration(env_path, values))
        counts = prepare_database(connection, schema_path, check_only=check_only)
    except psycopg.Error as error:
        # libpq puede incluir información privada en el mensaje original.
        raise SetupError(f'PostgreSQL no pudo completar la preparación ({type(error).__name__}). '
                         'Revisa que esté encendido, el usuario, la contraseña, el puerto y el permiso CREATEDB. '
                         'No se borraron datos; si se creó .env, se conserva para reintentar.') from None
    print(f"Listo: {counts['institutions']} instituciones, {counts['accounts']} cuentas y {counts['units']} unidades.")
    web_host = values.get('HOST', '127.0.0.1')
    if web_host == '::1':
        web_host = '[::1]'
    print(f"Dirección local: http://{web_host}:{values.get('PORT', '5000')}")
    print('Para iniciar desde esta carpeta: python run.py (o python3 run.py / py run.py).')
    return counts


def main():
    parser = argparse.ArgumentParser(description='Prepara Red House local. Requiere Python 3.12+ y PostgreSQL 14+ encendido.')
    parser.add_argument('--check', action='store_true', help='Solo comprobar una instalación existente; no instalar, crear ni cargar datos.')
    args = parser.parse_args()
    child_code = bootstrap(APP_ROOT, args.check)
    if child_code is not None:
        return child_code
    configure(APP_ROOT, SCHEMA_PATH, check_only=args.check)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print('\nInstalación cancelada. No se borró ninguna base existente.', file=sys.stderr)
        raise SystemExit(130)
    except (SetupError, OSError, ImportError, subprocess.SubprocessError) as error:
        detail = str(error) if isinstance(error, SetupError) else type(error).__name__
        print(f'No se completó la instalación: {detail}', file=sys.stderr)
        raise SystemExit(1)
