# Comprobación independiente del incremento

Auditor: agente separado `/root/auditor_fuentes_publicas`, autorizado expresamente por el usuario. Solo lectura de fuentes; pruebas aisladas permitidas. No representa profesional sanitario ni institución clínica. Transcripción de resultados del auditor, conservando el alcance declarado.

## Primera revisión

- F1, severidad media: la política `require_hla_catalogue` dependía de que `required_tests` incluyera literalmente `HLA`. Una tipificación bajo `CUSTOM_HLA` podía completar el perfil con un nombre ausente del catálogo. No otorgaba aprobación clínica, pero incumplía completitud técnica. Reproducción negativa posterior del implementador falló en JSON y XML.
- F2, severidad baja: `source_status.available` comprobaba fechas, sin comprobar archivos. Podía anunciar disponibilidad con fuente ausente. Se pidió integrar verificación de integridad.
- Primera conclusión: F1 impedía aprobar ese mecanismo. Oráculos y referencias restantes revisados sin otros defectos bloqueantes confirmados.

## Revisión correctiva final comunicada

El auditor confirmó F1 cerrado: la reproducción `CUSTOM_HLA` devuelve `complete=False`, `missing=['HLA:A','HLA:CATALOGUE_UNVERIFIED']`, `satisfied_loci=[]` y aprobación clínica falsa. Confirmó F2 cerrado: archivos ausentes producen `integrity_verified=False` y `available=False`.

Ejecutó independientemente 22 pruebas, aprobadas en 3,54 s, en `independent-public-final.xml`:

```sh
PYTHONPATH=apps/services apps/services/.venv/bin/python -m pytest apps/services/tests/test_public_reference_sources.py apps/services/tests/test_final_algorithms_hla.py apps/services/tests/test_stage02_oracles.py -q -k 'pinned_public or catalogue_unavailable or normative_transition or road_integrity or dijkstra_against or forecast_no_future or missing_hla_ambiguity or urgency_simulation or limits_empty_graph or expiry_estimate or each_missing_rank or forecast_lots' --junitxml=/tmp/independent-public-final.xml
```

También inspeccionó los 15 casos persistidos de `public-sources-after-audit.xml`, diferenciándolos de ejecución propia; señaló que navegador y documentación aún requerían cierre en ese momento. Su veredicto fue **APTA PARA CONTINUAR**, exclusivamente para F1/F2 y los mecanismos académicos revisados, sin acreditar cierre integral de etapa, habilitación clínica, GCP o GPS físico. La evidencia final posterior se remitió de nuevo para contraste.

## Contraste del expediente final

El auditor revisó los artefactos posteriores y confirmó:

- 1.117/1.117 SHA-256 coinciden con `sources-final.json`.
- 1.993 evidencias históricas intactas respecto del estado inicial.
- Las 110 identidades consolidadas tienen un caso aprobado en el JUnit señalado, sin sumar reintentos.
- Navegador aprobado con 23 comprobaciones, ningún error de consola y solo el 409 esperado.
- Documentación coherente; ningún enlace local roto en los siete documentos examinados.
- F1/F2 cerrados y presentación de `catalogue_check` incorporada.

No encontró nuevos defectos bloqueantes confirmados. Advirtió que 108/109 pasaron en la ejecución de regresión y el caso Redis503 pasó después aislado; el reintento no demuestra eliminación de la causa raíz. Vigilar recurrencias, conservando esta limitación.

Veredicto del auditor: **APTA PARA CONTINUAR**, para el incremento técnico académico 0.4.4/esquema 16. Para etapa 02 completa: **CONTINUACIÓN PARCIAL POR DEPENDENCIA DECLARADA**. No ejecutó independientemente los 110 casos, Chrome, GCS ni GCP; sus 22 pruebas anteriores siguen separadas de esta inspección final. No acredita habilitación clínica ni despliegue productivo.
