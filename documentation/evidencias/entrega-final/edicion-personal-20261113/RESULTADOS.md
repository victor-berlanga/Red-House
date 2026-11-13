# Edición personal del donante — 13 de noviembre de 2026

Backend y portal verificados en laboratorio aislado. Seis casos funcionales de API/formulario pasaron en el intento 2; el recorrido Chrome final pasó por separado en el intento 4. **No representan una única suite 7/7 sobre todo el repositorio.** No se usaron GCP, el iPhone ni datos personales reales.

| Ejecución | Resultado | Incidente o cambio |
| --- | --- | --- |
| Intento 1 | 1 aprobado, 6 fallidos; 59,86 s | La preparación intentó crear varios expedientes ligados a la misma cuenta. El servidor rechazó correctamente el duplicado. |
| Intento 2 | 6 aprobados, 1 fallido; 163,25 s | Cuentas independientes por caso. Pasaron JSON/XML, historial, permisos, campos protegidos, idempotencia, concurrencia y formulario CSRF. Chrome agotó la espera buscando un enlace exacto cuyo nombre accesible contenía además el folio. |
| Intento 3 | Chrome dirigido 1/1; 82,12 s | Acción «Editar mi nombre» visible, diagnóstico por fase y espera del DOM. Guardado y recarga pasaron. La revisión visual rechazó la captura estrecha tomada durante la transición del menú y detectó el UUID de cuenta en el resumen. |
| Intento 4 | Chrome dirigido 1/1; 77,87 s | Captura tras finalizar la transición y resumen del donante sin identificador interno de cuenta. Guardado, recarga, teclado y ausencia de UUID visible pasaron. |

Los seis casos funcionales probaron respuesta y contrato JSON/XML, conservación del dictamen clínico previo y demás campos, un solo evento/decisión para un reintento, versión obsoleta y cuerpo distinto rechazados, acceso ajeno/institucional/rol incorrecto, campos clínicos no admitidos y recibo inaccesible tras perder el vínculo de titular. Dos escrituras concurrentes con igual versión tuvieron un solo ganador. La auditoría conservó una proyección sin nombres, mientras el historial privado del propietario guardó el cambio. El formulario rechazó POST sin CSRF y persistió el cambio autorizado.

La fuente de la API personal no cambió entre esos intentos; los cambios posteriores afectaron la acción y presentación del expediente y el arnés visual. Los manifiestos comprimidos conservan los hashes exactos de 1107 archivos de servicios/contratos y código del portal, más el recorrido JavaScript, antes y después de cada ejecución. Cada pareja coincide; los cambios entre intentos permanecen identificables. El worktree partió de `acda00e`. Los manifiestos se comprimen sin pérdida; no contienen bases de datos ni credenciales.

Se inspeccionaron realmente las tres capturas del intento 4: campo y botones completos a 390 px, formulario de escritorio a 1280 px y expediente recargado con el nuevo nombre e historial, sin UUID de cuenta. Las capturas anteriores se conservan como evidencia del defecto, no como aceptación final. Se comprobó la escritura por teclado a 1280 px; 390 px acredita presentación, no un recorrido nativo. No se utilizaron métricas de píxeles como sustituto de inspección visual.

## Reproducción

Desde el worktree/checkout correspondiente, con dependencias instaladas, MongoDB local, Chrome y Playwright disponibles:

```sh
RH_BASE=/Users/victorberlanga/Programacion/integracion/Red-House
RH_LAB="$(mktemp -d /private/tmp/redhouse-personal.XXXXXXXX)"
RH_OUTPUT="$(mktemp -d /private/tmp/redhouse-personal-evidence.XXXXXXXX)"
mkdir -p "$RH_LAB/platform"
REDHOUSE_TEST_ROOT="$RH_LAB/platform" \
REDHOUSE_TEST_MONGOD="$RH_BASE/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_STARTUP_TIMEOUT=120 \
REDHOUSE_BROWSER_TESTS=1 REDHOUSE_BROWSER_ROOT="$RH_BASE" \
REDHOUSE_BROWSER_OUTPUT="$RH_OUTPUT/browser" \
"$RH_BASE/apps/services/.venv/bin/python" -m pytest \
  apps/services/tests/test_donor_personal.py -q --tb=short --show-capture=no \
  --basetemp="$RH_LAB/pytest" --junitxml="$RH_OUTPUT/junit.xml"
```

Los intentos 3 y 4 seleccionaron únicamente `::test_personal_portal_browser_renders_and_persists`. El navegador recibió las credenciales sintéticas por stdin, sin argumentos ni variables de entorno de XCTest; su reporte solo contiene fase y tipo de error. Se revisaron logs/JUnit para la contraseña del fixture y JWT antes de copiarlos. `report-review.json` registra la comparación de los dos primeros reportes, con cero sustituciones. Los procesos terminaron y se eliminaron únicamente los cuatro laboratorios propios, conservando reportes y capturas.

El portal del ensayo usa certificado autofirmado con excepción limitada al contexto Chrome. Los microservicios del fixture usan HTTP local y bases reales. No acredita TLS público, Nginx, pruebas de carga, lector de pantalla, actualización del nombre legal/de cuenta ni clientes nativos. La integración móvil y publicación siguen pendientes; CONT-05 no se cierra todavía.
