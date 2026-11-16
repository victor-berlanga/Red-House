# Recorrido compartido iOS–escritorio: tramo Qt/XML

El 16 de noviembre de 2026 se ejecutó una vez el tramo de escritorio, con salida 0, sobre el laboratorio compartido iniciado para iOS. La consola correspondía al commit `379aba2`. El entorno operaba en alcance **ACADEMIC** con datos y consentimiento sintéticos; ningún resultado constituye autorización clínica. El fixture ya estaba activo: este recorrido no inició ni detuvo sus motores.

La cita final, creada desde iOS para el mismo donante, estaba BOOKED. El runner consultó su agenda por XML, comprobó que la hora real de inicio había transcurrido antes de escribir y verificó que la colecta registrada no fuese anterior. Donación y cita se correlacionan por donante: el contrato de donación no contiene `appointment_id` ni se demuestra una clave foránea entre ellas.

Antes del dictamen se verificó el rechazo 409 `human_review_required` de una colecta de donante aún no evaluado. Con consentimiento académico vigente, `medical1` documentó el dictamen sintético y registró la colecta en Qt; `operator1` documentó su procesamiento, registró la unidad ligada a esa donación y la fraccionó. El origen quedó WITHDRAWN; el derivado de eritrocitos recibió perfil sintético ABO, muestra y resultado, y `medical1` revisó y liberó la unidad mediante Qt hasta AVAILABLE. El derivado de plasma quedó QUARANTINE. También se verificó el rechazo XML 403 de alta de sede por operador.

El runner comprobó lectura XML de avisos propios y proyección en Auditoría para cita, colecta, procesamiento, fraccionamiento, recepción, resultado, revisión y liberación. Los oráculos SQL de solo lectura correlacionaron identificadores, actores, estados, versiones y eventos de los servicios propietarios. La lectura SQL pertenece al arnés de verificación en el host; la aplicación de escritorio se comunicó con los servicios mediante HTTPS y XML/XSD. Las sesiones creadas por el runner se cerraron; el fixture permaneció activo para la consulta web coordinada por dirección.

Se compararon 982 fuentes de escritorio y servicios antes y después: manifiestos idénticos, SHA-256 `905029a854b971253cbc038f9834a0cc6811922a8db1f31fdaa896ebbb1848d4`. Los tres scripts privados utilizados, sin credenciales incorporadas, conservan estas huellas:

- `runner.py`: `aa67a14032d15830e9158c00236aa6b39d07fb7065aef7478c49f80ebd9bb1f5`.
- `profile_setup.py`: `0bd723bc67fba96409929e90eb1a54ad480ef5f84506b6f79813ac78f9e73400`.
- `laboratory_gui.py`: `409c98e337194806318ece768925a1deaa38630c7bd45834660aeb92ee7d26c5`.

El comando ejecutado, desde la raíz del proyecto, usó un directorio privado nuevo y la CA verificada del handoff. Los valores de credenciales y los identificadores no se pasaron por línea de comandos:

```sh
umask 077
QT_QPA_PLATFORM=offscreen PYTHONPATH=apps/desktop \
  DESKTOP_CAPTURE_DIR="$PWD/.local/artifacts/desktop/e2ec-run-20261116/captures" \
  E2EC_PRIVATE_OUTPUT="$PWD/.local/artifacts/desktop/e2ec-run-20261116/private" \
  apps/desktop/.venv/bin/python -c 'import runpy,sys; sys.path.append("apps/services/.venv/lib/python3.12/site-packages"); sys.path.insert(0,".local/artifacts/desktop/e2ec-prepared-20261116"); runpy.run_path(".local/artifacts/desktop/e2ec-prepared-20261116/runner.py",run_name="__main__")' \
  > .local/artifacts/desktop/e2ec-run-20261116/private/runner.log 2>&1
```

Este comando es el registro de la ejecución, no una instrucción para repetir escrituras sobre el mismo fixture. El log, los manifiestos y el recibo con IDs permanecen privados; el recibo se entregó al tramo web. No existe JUnit para esta invocación directa. Las [13 capturas Qt](capturas/) contienen únicamente datos sintéticos y referencias de ensayo; sus huellas constan en [SHA256SUMS](SHA256SUMS). Dirección inspeccionó colecta, procesamiento, perfil, muestra, revisión y liberación. El nombre largo del perfil aparecía truncado en la tabla de esa ejecución; el ajuste de ancho y tooltip y su [vista con doble](../iteracion-calidad-unidad/texto-perfil-20261116/perfil-final.png) son posteriores y no forman parte del ensayo real.

Este tramo no prueba Windows, impresión física, push externo ni una aprobación o aplicación clínica. El resultado integral iOS–Qt–web requiere además el oráculo web independiente; no se afirma aquí su resultado.
