# Continuidad iOS–Qt–web del donante y la unidad

El 16/11/2026 se comprobó el tramo principal de E2E-C sobre el mismo laboratorio sintético conservado: reserva nativa iOS, colecta y laboratorio en Qt/XML, y consulta independiente del monolito. El alcance es **ACADEMIC**; el consentimiento y dictamen son datos de ensayo, sin validez clínica. Este resultado no cierra todavía todos los criterios de E2E-C del prompt 07.

## Evidencia por componente

| Componente | Resultado y evidencia |
| --- | --- |
| iPhone 16 Pro, Lab | Usuario reservó, reprogramó y canceló una cita; después reservó la cita retenida de las 19:49:41 UTC. JSON 201/200 y estados/cupos conciliados. [Agenda nativa y límites](../mobile/ios-resume-20261116/AGENDA.md), [paquete exacto](../mobile/ios-resume-20261116/PAQUETES.md). |
| PySide6, commit `379aba2` | Una ejecución Qt/XML salió 0. Colecta posterior al comienzo de la cita; procesamiento y fraccionamiento; eritrocitos AVAILABLE v3 tras perfil, muestra, resultado y revisión, plasma QUARANTINE v1, origen WITHDRAWN. Rechazos 409 sin revisión humana y 403 del operador; avisos propios y auditoría correlacionados. [Recorrido y 13 capturas](../desktop/e2ec-qt-20261116/RESULTADOS.md). |
| Monolito Flask/Jinja, Chrome real | Una ejecución salió 0: siete vistas consultaron los mismos IDs de cita, donante, donación, origen, linaje y derivados. Otro operador institucional recibió 403 sin el folio privado. Cero errores JavaScript, cero POST de negocio, cero intentos HTTP del backend a microservicios. [Recibo del navegador](web/browser.json), [recibo del runner](web/runner.json). |

La cita y la colecta comparten donante y cronología; el contrato de donación no contiene `appointment_id`. No se afirma una FK, cierre automático de cita ni relación causal que el modelo no conserva. Las consultas SQL son oráculos independientes del host: móvil solo consumió JSON y escritorio XML/XSD. La consulta web utilizó el núcleo propio del monolito y no necesitó HTTP a microservicios.

## Verificación del tramo web

El runner recibió el handoff de escritorio y comprobó el directorio PostgreSQL del laboratorio antes de operar. Los resultados esperados se fijaron antes de ejecutar. Comparó 1.314 fuentes antes/después sin cambios y conservó idénticos los dos oráculos de negocio SQL. Solo creó su servidor HTTPS y navegador; ambos quedaron cerrados. No inició ni detuvo los motores compartidos.

Dirección inspeccionó las tres capturas reales: [cita](web/cita-ios-consultada-web.png), [donación procesada](web/procesamiento-escritorio-consultado-web.png) y [linaje](web/derivados-escritorio-consultados-web.png). En linaje se detectaron etiquetas técnicas RBC/AVAILABLE/QUARANTINE; no se atribuye una corrección a estas capturas. El tramo iOS conserva confirmación humana y oráculos, pero no obtuvo captura por el fallo LocalAuthentication de XCTest.

Artefactos públicos: [fuentes](web/fuentes-antes.json), [SQL antes](web/sql-antes.json), [SQL después](web/sql-despues.json), [entorno](web/runtime-scope.json), [runner Python](web/run_shared_result.py), [runner Chrome](web/verify_shared_result.cjs) y [huellas](web/SHA256SUMS). El manifiesto posterior idéntico y los logs privados se conservan en `.local/artifacts/e2ec-web-run-20261116/`. No hay JUnit para este runner directo.

Comando de esa ejecución, conservado para trazabilidad; no repetir escrituras previas del recorrido:

```sh
PYTHONPATH=.:apps/services:apps/web apps/services/.venv/bin/python \
  .local/artifacts/e2ec-web-prepared-20261116/run_shared_result.py \
  --handoff .local/artifacts/desktop/e2ec-run-20261116/private/handoff-web.json \
  --output .local/artifacts/e2ec-web-run-20261116
```

## Criterios pendientes de E2E-C

Faltan la rama de recordatorio autorizado, competencia real de dos cuentas por el último cupo y rechazo específico de lectura de resultados de laboratorio por el donante. La reconstrucción por interfaz de auditoría también debe distinguirse del oráculo de proyección ya comprobado. No se sustituyen esos criterios con esta continuidad positiva.

El laboratorio usa `TESTING=True`, cuotas ampliadas y `WORKER_REQUIRED=False`: no acredita MFA, rate limiting, capacidad de producción, GCP, Windows ni push FCM/APNs. Los paquetes de cliente posteriores conservarán su propia identificación. Tampoco se cierran etapas 04, 05, 06 o 07 mediante este documento.
