# Catálogo de conservación: recorrido real académico

El 16 de noviembre se ejecutó un recorrido Qt/XML con el fixture E2E-B local ya activo, 12 servicios `TESTING=False` y alcance `ACADEMIC`. La unidad de este ensayo fue distinta del órgano del traslado E2E-B. El perfil térmico, sus temperaturas y sus referencias eran sintéticos; no acreditan una política ni autorización clínica.

Una preparación XML creó la unidad sintética en cuarentena y vinculó el perfil de laboratorio académico existente. En Qt, una cuenta OPERATOR registró un equipo; una cuenta MEDICAL, autenticada con MFA, registró un perfil térmico y vinculó ambos a esa unidad. La consulta XML posterior y SQL de solo lectura comprobaron el equipo, el perfil térmico y la conservación del mismo `lab_profile_id`. SQL confirmó un evento de alta del equipo y uno del perfil con sus actores. Cada comando Qt usó su diario e idempotencia. No se comprobó aquí una lectura térmica ni la liberación de esta unidad.

Los procesos de preparación y Qt terminaron con **código 0**, observado en la salida de la herramienta. Sus logs privados estaban vacíos; no se presenta un log de salida inexistente. Los recibos privados guardaron los IDs y el oráculo de cierre confirmó dos familias de sesión nuevas revocadas en SQL y ausentes en Redis para la preparación, y otras dos para Qt. No se revocaron sesiones de otras cuentas. El fixture compartido se mantuvo activo para el traslado.

[Equipo](equipo.png), [perfil](perfil.png) y [vínculo](vinculo.png): ventanas reales capturadas durante el recorrido. Dirección las inspeccionó y aceptó su legibilidad. El adaptador de ensayo rellenó y accionó los controles reales; no simuló respuestas del servicio.

## Reproducción y límites

Los scripts utilizados están en [procedimiento](procedimiento). Requieren el fixture privado conservado, CA y cuentas sintéticas existentes, salida nueva 0700 y factor MFA propio 0600. La preparación guarda cada clave y cuerpo antes del POST; ante respuesta incierta debe consultarse su diario, no crear otra unidad automáticamente. El runner conserva la clave del diario de ensayo en archivo privado; no verifica Keychain nativo. Sus comandos observados fueron:

```sh
E2EB_READY="$PWD/.local/artifacts/e2eb-preserved-20261116/run-02/runtime-ready.json" E2EB_BOOTSTRAP_PRIVATE="$PWD/.local/artifacts/e2eb-preserved-20261116/cold-setup-01" E2EB_MFA_PRIVATE="$PWD/.local/artifacts/e2eb-preserved-20261116/bootstrap-01/medical1-factor.json" E2EB_EXISTING_HANDOFF="$PWD/.local/artifacts/e2eb-preserved-20261116/e2eb-incremental-handoff.json" PYTHONPATH=apps/services apps/services/.venv/bin/python .local/artifacts/desktop/catalogo-frio-candidato-20261116/real-preparado/setup_unit.py
COLD_HANDOFF="$PWD/.local/artifacts/e2eb-preserved-20261116/cold-setup-01/handoff.json" COLD_FACTOR="$PWD/.local/artifacts/e2eb-preserved-20261116/bootstrap-01/medical1-factor.json" COLD_OUTPUT="$PWD/.local/artifacts/e2eb-preserved-20261116/cold-qt-01" PYTHONPATH="apps/desktop:apps/services:apps/services/.venv/lib/python3.12/site-packages:.local/artifacts/desktop/catalogo-frio-candidato-20261116/real-preparado" apps/desktop/.venv/bin/python .local/artifacts/desktop/catalogo-frio-candidato-20261116/real-preparado/runner.py
```

Los comandos se muestran para identificar la ejecución: sus directorios ya contienen resultados y **no deben reutilizarse para otro intento**. Los IDs, diarios, credenciales y archivos de configuración permanecen privados. No se verificaron Windows, GCP ni política clínica mediante este ensayo.

Las huellas de scripts, capturas y fuentes afectadas figuran en [SHA256SUMS](SHA256SUMS). La fotografía completa de fuentes del cliente tomada antes de la ventana de recepción permanece en el expediente privado; no se presenta como comparación posterior de este recorrido.

## Comprobación posterior del ancho, sin envío

Dirección inspeccionó también [receptor](ancho-receptor.png) y [planificación](ancho-planificacion.png) después del ajuste de crecimiento horizontal incorporado en `3d2b910`. Son ventanas Cocoa reales con datos sintéticos en memoria y respuestas simuladas, sin red ni escritura. Folio, nombre, estudios y motivo quedan legibles. Planificación se capturó durante la consulta simulada de ruta, con acción final deshabilitada; no acredita una planificación adicional. Estas dos capturas se separan del recorrido API anterior.
