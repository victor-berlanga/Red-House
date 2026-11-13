# Consola Red House: incremento inicial

Las copias de contratos se comprueban con `python sync_contracts.py --check` desde esta carpeta. Para actualizarlas desde los propietarios del monorepo, ejecutar `python sync_contracts.py` y repetir las pruebas del cliente. El script usa solo la biblioteca estándar; la aplicación distribuida no necesita el código del servidor.

Estado: **incremento parcial; no acredita entrega final ni uso clínico**. Se probaron en laboratorio sintético por HTTPS/XML: sesión, inventario, muestras y resultados, revisión profesional, solicitudes, evaluación y reserva, recepción de custodia, solicitud de reporte y emisión de etiquetas. Se inspeccionaron ventanas Qt autenticadas de inventario, detalle y recepción. La lectura autenticada de inventario también pasó en GCP; no se modificaron datos de negocio allí.

Las familias DESK-01…14 y sus cierres pendientes están en [la matriz de evidencia](../../documentation/evidencias/entrega-final/desktop/MATRIZ.md). El personal médico puede registrar solicitudes eligiendo un receptor autorizado por búsqueda y paginación; el intento usa el diario idempotente. Siguen parciales, entre otras, administración institucional, otras clases de recurso, expedientes, cadena de custodia completa, seguimiento WSS/mapa, descarga real de reportes y auditoría. La emisión de PDF y la solicitud de impresión existen; no se han probado impresora ni lector físicos. El formulario de alta de inventario cubre solo eritrocitos. La sesión vive en memoria; al cerrar ventana o usar «Cerrar sesión» se intenta revocarla sin bloquear la interfaz, y un fallo de red impide confirmar la revocación remota.

## Entorno

Python 3.12.6 verificado en macOS x86_64; el conjunto exacto de dependencias capturado corresponde a ese entorno. Windows no está verificado. El archivo de dependencias directas aún no fija todas las transitivas específicas de Windows. En macOS x86_64 con Python 3.12.6:

```sh
cd apps/desktop
python3 -m venv .venv
.venv/bin/pip install -r requirements-macos-lock.txt
.venv/bin/python -m redhouse_desktop
```

La instalación usa la dirección institucional configurada; para laboratorio, `REDHOUSE_BASE_URL` permite seleccionar un servidor HTTPS aislado con certificado confiable y rutas `/services/<servicio>/api/v1/…`. No se desactiva TLS ni se siguen redirecciones. Los datos y permisos proceden del servidor. La interfaz evita llamadas de red en el hilo principal y limita peticiones a una a la vez. Las escrituras atómicas conectadas preparan un diario cifrado por cuenta antes del envío; si se pierde la respuesta, la recuperación conserva la misma clave. La emisión se recuperó tras interrupción de proceso con llavero macOS y servidor real de laboratorio; Windows sigue pendiente. Sin llavero nativo se bloquea la escritura. No hay cola de negocio fuera de línea.

Si se usa el proveedor GCS heredado, la configuración interna del despliegue debe fijar `REDHOUSE_GCS_BUCKET` al bucket autorizado; sin ese valor la consola rechaza descargas GCS. El almacenamiento local por capacidad sigue su propio origen permitido. La configuración no se solicita en la pantalla de acceso.

Para pruebas: `.venv/bin/pip install pytest==8.4.2` y `.venv/bin/python -m pytest tests/test_client.py tests/test_journal.py tests/test_ui.py tests/test_label_output.py`. Los XSD y OpenAPI son copias versionadas del repositorio; deben actualizarse y probarse junto al cliente cuando cambie el contrato. Se validan XSD general, servicio, versión de proceso permitida por servicio y DTO publicado por operación. La lista de versiones de proceso es explícita y separada de `info.version` del documento OpenAPI; no acepta versiones desconocidas. El DTO de inventario tiene campos opcionales en OpenAPI y no garantiza más que ese contrato.

Qt recomienda entorno virtual y distribuye Qt en sus ruedas: https://doc.qt.io/qtforpython-6/gettingstarted.html. El paquete macOS x86_64 del incremento anterior pasó una prueba de arranque y recursos; falta reconstruirlo con el resumen reciente. No está notarizado ni probado como instalador de distribución. Windows 11 y macOS arm64 no se han ejecutado. WSS, mapa y descarga de reportes están implementados, pero su integración real desde escritorio sigue pendiente.

Para comprobar un ejecutable empaquetado sin sesión ni red, ejecútalo con `--smoke-report RUTA`; crea una ventana Qt, procesa eventos, valida un XSD y un DTO incluidos y escribe JSON con `ok: true` solo si terminó correctamente. En CI sin pantalla puede usarse `QT_QPA_PLATFORM=offscreen`. Esta comprobación no sustituye la inspección visual ni la integración con servicios.
