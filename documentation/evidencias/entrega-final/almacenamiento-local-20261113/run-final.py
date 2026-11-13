import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path

root = Path.cwd()
with tempfile.TemporaryDirectory(prefix='redhouse-clamd-test-') as directory:
    directory = Path(directory)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    config = directory / 'clamd.conf'
    config.write_text(f'''DatabaseDirectory {root / '.local/runtime/clamav/database'}
LogFile {directory / 'clamd.log'}
PidFile {directory / 'clamd.pid'}
TCPAddr 127.0.0.1
TCPSocket {port}
Foreground yes
MaxThreads 2
StreamMaxLength 10M
MaxFileSize 10M
MaxScanSize 25M
''')
    server = subprocess.Popen([str(root / '.local/tools/clamav-1.5.4/sbin/clamd'), '--config-file=' + str(config)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(120):
            if server.poll() is not None:
                raise RuntimeError('ClamD terminó antes de iniciar')
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=1) as conn:
                    conn.sendall(b'zPING\0')
                    if conn.recv(128) == b'PONG\0':
                        break
            except OSError:
                time.sleep(1)
        else:
            raise RuntimeError('ClamD no respondió a PING')
        print('ClamD real listo; firmas locales; puerto temporal.', flush=True)
        env = dict(os.environ, PYTHONPATH='apps/web', REDHOUSE_TEST_CLAMD_PORT=str(port), REDHOUSE_TEST_MONGOD=str(root / '.local/tools/mongodb-8.0.17/bin/mongod'))
        if not env.get('REDHOUSE_TEST_NGINX'):
            raise RuntimeError('REDHOUSE_TEST_NGINX es obligatorio para la suite final')
        paths = [
            'apps/services/tests/test_next_appointment.py',
            'apps/services/tests/test_label_issuance.py',
            'apps/services/tests/test_proxy_boundaries.py',
            'apps/services/tests/test_portal_storage_targets.py',
            'apps/services/tests/test_private_storage_local.py',
            'apps/services/tests/test_local_storage_reports.py',
            'apps/services/tests/test_local_storage_autonomous.py',
            'apps/services/tests/test_local_storage_https.py',
            'apps/services/tests/test_scan_idempotency.py',
            'apps/services/tests/test_final_delivery_documents.py::test_documents_scan_private_access_and_export_formats',
            'apps/services/tests/test_nginx_runtime.py',
        ]
        result = subprocess.run([str(root / 'apps/services/.venv/bin/python'), '-m', 'pytest', *paths, '-q',
            '--junitxml=' + str(root / 'documentation/evidencias/entrega-final/almacenamiento-local-20261113/final-junit.xml')], env=env)
        raise SystemExit(result.returncode)
    finally:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
