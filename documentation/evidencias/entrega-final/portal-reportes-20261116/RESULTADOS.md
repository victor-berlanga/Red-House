# Reportes privados desde Chrome — 16/11/2026

I06-06, alcance local: el segundo recorrido terminó **1/1 aprobado**, 112,920 s de lanzador. El monolito, sin listeners API, generó CSV/PDF/XLSX mediante `process(limit=3)` real y ClamD real. Cada descarga contiene los 1.003 identificadores autorizados en el orden SQL esperado, tamaño y SHA-256 exactos; archivos CLEAN y eventos únicos del actor comprobados.

La sesión se revocó después de completar los trabajos y antes de descargar: SQL/Redis confirmaron revocación, Chrome volvió al login (302) y hubo **cero llamadas al firmante**. Los tres archivos se conservaron. Una nueva sesión del propietario permitió descargarlos. Cero errores JavaScript, 1.322 fuentes estables y 42 procesos propios cerrados sin cierre forzado. Véanse los recibos de `intento-02/`; `fuentes.json` corresponde al manifiesto anterior y posterior idénticos.

Comando: `PYTHONPATH=.:apps/services REDHOUSE_BROWSER_TESTS=1 REDHOUSE_TEST_REPORT_BROWSER=1 ... apps/services/.venv/bin/python -m pytest apps/services/tests/test_portal_reports_browser.py::test_report_formats_and_revocation_after_completion_in_browser -q`, con rutas privadas nuevas, MongoDB local y firmas ClamAV 28185. El lanzador privado `.local/run_portal_reports_20261116_02.py` conserva configuración, huellas y cierre de procesos.

## Fallo conservado y corrección

El primer intento terminó fallido en 97,205 s: CSV/XLSX COMPLETE, PDF RETRYABLE/scanner_unavailable, sin descargas. Un diagnóstico separado del mismo PDF dio CLEAN en 6,5361 s; no identifica la excepción original ni demuestra por sí solo un timeout. No se amplió el límite del producto.

El formato nuevo imprime el contexto una vez: sobre las mismas 1.003 filas pasó de 377 páginas/1.035.507 bytes a 144 páginas/336.701 bytes. Se conservaron todos los IDs/folios. Los trabajos anteriores mantienen su versión de representación; comparación byte a byte del PDF histórico idéntica. XLSX v2 usa timestamps ZIP fijos para producir los mismos bytes al reintentar; `{}` y ausencia de contexto conservan comportamiento histórico. Siete pruebas dirigidas previas y cuatro del ajuste final están registradas por separado; no se suman como once casos distintos.

Dirección inspeccionó las páginas renderizadas 1, 2 y 144 del PDF nuevo, la página 1 anterior, el detalle real del reporte y el login tras revocación. El PDF sigue siendo operativo por registro, sin certificación regulatoria. El detalle muestra todavía `COMPLETE`; su traducción queda como ajuste de presentación posterior.

Almacenamiento LOCAL y datos sintéticos; TESTING, cuotas y TLS efímero del laboratorio. Este caso no acredita GCS, despliegue de estas fuentes, revocación anterior a extracción ni cambio de rol. La cobertura histórica de esos escenarios conserva su alcance propio. No cierra toda la etapa 06.
