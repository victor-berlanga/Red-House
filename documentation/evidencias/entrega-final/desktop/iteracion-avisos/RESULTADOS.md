# Auditoría y acuse de avisos

El tercer intento dirigido terminó con salida 0: `operator1` confirmó el mismo aviso mediante Qt/XML, que pasó de OPEN a ACKNOWLEDGED. El oráculo SQL de solo lectura confirmó el responsable, el evento de origen y un único `ALERT_ACKNOWLEDGED`. La sesión propia se cerró. Se compararon 982 fuentes antes y después; ambos manifiestos tienen SHA-256 `d171c6a2d5a924a12bc380cc5443aec8db5932fe66725e1451d8b6daffd6cf7b`. El runner corregido tiene SHA-256 `3ecab5fa226e447d392a938d36ccec672237af7cb0fb5d875eac2dfbbc23c38e`.

Las [capturas del primer intento](real-01/) documentan listado y detalle de auditoría; las [capturas del tercero](real-03/) muestran aviso, confirmación y estado reconocido. Su [manifiesto](SHA256SUMS) incluye también la vista con doble de las traducciones. El diálogo real de confirmación mostró botones del sistema «Yes/No»; el texto de la pregunta estaba en español. La prueba fue académica, con datos sintéticos y TLS del fixture; no sustituye pruebas de Windows ni de MFA real.

Comando del tercer intento, ejecutado una sola vez desde la raíz del proyecto, con log y salida privados:

```sh
umask 077
QT_QPA_PLATFORM=offscreen PYTHONPATH=apps/desktop \
  E2EC_RECEIPT="$PWD/.local/artifacts/desktop/e2ec-run-20261116/private/handoff-web.json" \
  DESK14_ACK_CAPTURE_DIR="$PWD/.local/artifacts/desktop/desk14-ack-fixed-run-20261116/captures" \
  DESK14_ACK_PRIVATE_OUTPUT="$PWD/.local/artifacts/desktop/desk14-ack-fixed-run-20261116/private" \
  apps/desktop/.venv/bin/python -c 'import runpy,sys; sys.path.append("apps/services/.venv/lib/python3.12/site-packages"); runpy.run_path(".local/artifacts/desktop/desk14-ack-fixed-20261116/runner.py",run_name="__main__")' \
  > .local/artifacts/desktop/desk14-ack-fixed-run-20261116/private/runner.log 2>&1
```

El comando registra una escritura ya realizada; no debe repetirse sobre el mismo aviso. Los dos intentos previos y su diagnóstico se conservan a continuación.


El 16/11/2026 se ejecutó una vez el recorrido Qt/XML sobre el fixture académico compartido. El auditor abrió el listado y detalle de un evento del recorrido de donación; el operador abrió el aviso asociado. Dirección inspeccionó las tres capturas reales, conservadas en `.local/artifacts/desktop/desk14-run-20261116/captures/`.

El arnés quedó bloqueado en un diálogo Qt durante la confirmación; se interrumpió únicamente su proceso (salida 143). Un oráculo PostgreSQL de solo lectura, consultado antes del cierre, encontró un aviso objetivo en estado OPEN, sin responsable de acuse. El muestreo del proceso mostró `QMessageBox`, `QDialog` y `QEventLoop`; no acredita por sí solo el nombre del modal ni su causa exacta. **El acuse no se considera probado.** No se repitió automáticamente.

Auditor y segundo operador habían ejecutado su cierre de sesión. La familia técnica del primer operador pudo permanecer activa al interrumpir el proceso: sus tokens estaban solo en memoria y no fue posible identificar y revocar esa familia de forma inequívoca por la API. Se conserva su expiración natural como límite de limpieza, sin comprobar aquí el instante de vencimiento; no se revocaron otras sesiones. Las 982 fuentes comparadas antes y después del intento fueron idénticas. El log, captura de proceso y manifiestos permanecen privados.

El fix de acuse usa confirmación y guarda de sesión, reautenticación y diario; tres dobles de sesión/correlación pasaron antes del intento. Después del ensayo se tradujeron las etiquetas de aviso observadas; la [captura con doble](texto-final/avisos.png) es posterior y no demuestra lectura real del servicio. Se preparó un runner dirigido solo al acuse, con confirmación mediante botón explícito y plazo absoluto que rechaza el modal al vencer; no se ejecutó en ese momento. No se repitieron auditoría ni detalle en esa preparación.

La repetición dirigida terminó con salida 1 y `AssertionError`: produjo únicamente la vista del aviso y cerró su sesión. El oráculo READ ONLY posterior encontró nuevamente el aviso OPEN sin `acknowledged_by`; 982 fuentes permanecieron idénticas. No se registró acuse. Un sondeo Qt aislado posterior, sin API, reprodujo la causa: en modo offscreen `QMessageBox.question` mostraba un QMessageBox visible y modal con título vacío. El arnés exigía un título concreto y por eso no reconocía la pregunta. Se comprobó que `button(Yes).click()` devuelve la respuesta correcta; `AA_DontUseNativeDialogs` no cambió el título. El tercer runner identifica texto y botón exactos, conserva plazo/finally y añade etapa de fallo saneada; su ejecución posterior se describe arriba.

Después del acuse real se sustituyeron los botones dependientes del idioma del sistema por «Confirmar» y «Cancelar», con cancelar como opción predeterminada y de escape. El [doble Qt](dialogo-espanol-doble/confirmacion-es.png) muestra ambos botones; cuatro pruebas dirigidas pasaron, incluidas cancelación sin envío y cambio de sesión sin preparar comando. Esta corrección visual y sus dobles son posteriores al acuse real; no se repitió la escritura.

Dirección inspeccionó las vistas reales de auditoría, detalle, aviso, confirmación y acuse, y las vistas sintéticas posteriores de etiquetas y botones en español.
