import os
import subprocess
from pathlib import Path
from threading import Thread

import pytest
from werkzeug.serving import make_server


def test_browser_workflow(app, request, tmp_path):
    if not request.config.getoption("--browser"):
        pytest.skip("Usa --browser y proporciona Playwright mediante NODE_PATH; requiere Chrome.")
    app.config["HIGHCHARTS_ENABLED"] = True
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(["node", str(Path(__file__).with_name("browser_smoke.cjs"))],
            env={**os.environ, "BASE_URL":f"http://127.0.0.1:{server.server_port}",
                 "DEMO_PASSWORD":app.config["DEMO_TEST_PASSWORD"],
                 "BROWSER_ARTIFACTS":os.getenv("BROWSER_ARTIFACTS",str(tmp_path))},
            capture_output=True, text=True, timeout=150)
        assert result.returncode == 0, result.stdout + result.stderr
        print(result.stdout)
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
