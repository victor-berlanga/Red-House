"""Punto de entrada local. En producción usar un servidor WSGI, nunca debug."""
import os
from pathlib import Path
import subprocess
import sys

# El arranque directo elige el venv local, sin instalar ni tocar la base.
# Las importaciones WSGI/Flask CLI conservan su comportamiento anterior.
if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    environment = root / ".venv"
    executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not executable.is_file():
        raise SystemExit("Primero ejecuta setup.sh (macOS/Linux) o setup.cmd (Windows) en esta carpeta.")
    if Path(sys.prefix).resolve() != environment.resolve():
        try:
            raise SystemExit(subprocess.call([str(executable), str(Path(__file__).resolve()), *sys.argv[1:]]))
        except KeyboardInterrupt:
            raise SystemExit(130)

from src import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=False)
