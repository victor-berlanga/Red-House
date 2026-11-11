#!/usr/bin/env bash
# Solo pruebas locales: datos ficticios y procesos propios del fixture.
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:?features|browser-http|browser-monolith|agenda-browser|browser-degraded|migration|regression}"
output="${2:?Directorio temporal de evidencia}"
case "$output" in /private/tmp/rh-portal-correction-*/*) ;; *) echo 'Salida fuera del expediente temporal permitido' >&2; exit 2;; esac
mkdir -p "$output"
export REDHOUSE_TEST_MONGOD="${REDHOUSE_TEST_MONGOD:-$PWD/.local/tools/mongodb-8.0.17/bin/mongod}"
export REDHOUSE_TEST_STARTUP_TIMEOUT=90
export REDHOUSE_TEST_GATEWAY=embedded
export REDHOUSE_AXE_PATH="${REDHOUSE_AXE_PATH:-/private/tmp/rh-portal-correction-20261106/a11y/node_modules/axe-core/axe.min.js}"
export REDHOUSE_BROWSER_RESULTS="$output/browser"
case "$mode" in
  features) tests=(apps/services/tests/test_portal_corrections.py apps/services/tests/test_portal_documents.py apps/services/tests/test_openapi_documentation.py);;
  browser-http) export REDHOUSE_BROWSER_TESTS=1; tests=('apps/services/tests/test_correction_browser.py::test_operational_browser_corrections[http]');;
  browser-monolith) export REDHOUSE_BROWSER_TESTS=1; tests=('apps/services/tests/test_correction_browser.py::test_operational_browser_corrections[monolith]');;
  agenda-browser) export REDHOUSE_BROWSER_TESTS=1; tests=(apps/services/tests/test_portal_agenda_browser.py);;
  browser-degraded) export REDHOUSE_BROWSER_TESTS=1; tests=(apps/services/tests/test_portal_tracking.py::test_portal_browser_profiles_and_live_map);;
  migration) tests=(apps/services/tests/test_final_algorithms_hla.py::test_migration_13_to_current_preserves_rows_and_is_repeatable);;
  regression) tests=(apps/services/tests/test_web_integration.py apps/services/tests/test_continuity.py apps/services/tests/test_final_tracking.py apps/services/tests/test_final_quality.py apps/services/tests/test_final_delivery_documents.py apps/services/tests/test_final_algorithms_hla.py apps/services/tests/test_portal_tracking.py);;
  *) echo 'Modo de prueba desconocido' >&2; exit 2;;
esac
runner=()
if command -v caffeinate >/dev/null 2>&1; then runner=(caffeinate -i); fi
"${runner[@]}" apps/services/.venv/bin/python -m pytest "${tests[@]}" -q --tb=short --junitxml="$output/$mode.xml" > "$output/$mode.log" 2>&1
