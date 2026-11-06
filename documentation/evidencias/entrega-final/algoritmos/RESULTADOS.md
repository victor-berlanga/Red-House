# Evidencia de HLA y algoritmos

Fecha de trabajo: 31/10/2026. Entorno local macOS 15.7.9 x86_64, Python 3.12.6; PostgreSQL 14.23, Redis y MongoDB reales levantados por el fixture `Environment` en directorios temporales. Fuentes locales identificadas por `manifest.json`; el árbol ya contenía numerosos cambios ajenos a esta tarea. No se hizo commit ni despliegue, no se modificó la instalación habitual ni GCP.

## Resultado consolidado

**68 casos distintos aprobados según su última ejecución**, cero fallos pendientes en ese conjunto. Regresión inicial: 63 aprobados y un fallo; ampliación final: 12/12; repetición de auditoría: 1/1. Los conjuntos se superponen; `summary.json` reconcilia por clase/nombre. No equivale a repetir toda la suite del repositorio. El aviso JUnit sobre `record_property` es de formato, no un fallo funcional.

## Alcance comprobado

- Tipificación HLA estructurada y declarada, correcciones conservadas, estados pendiente/informado separados de autorización; completos no generan dictamen.
- Persistencia y recuperación de simulaciones; separación institucional, rechazo a operador, UPDATE histórico rechazado.
- Contratos JSON y XML, XSD y DTO de resultados; ejemplos de perfil, resultado y simulación validados.
- Dijkstra frente a enumeración independiente de caminos, Hopcroft–Karp frente a 512 grafos exhaustivos, caso voraz insuficiente.
- Entrenamiento/evaluación temporal, alfa sin filtración de futuro, demanda y riesgo de sobrantes por lote; simulación con urgencia y motivos de exclusión.
- GPS observado y recorrido recibido separados de planificación y ETA; fechas futuras/pesos negativos y límites rechazados.
- Formulario y detalle web mediante cliente HTTP Flask con API y almacenes reales; resultado sin dictamen visible. No es prueba visual en navegador.
- Ensayo de instalación v13 aislada, unidad y resultado históricos ficticios, migración 14 y repetición; comparación de valores históricos, sin HLA retroactivo inventado.

## Ejecuciones y comandos

`tests.xml`: regresión de `test_final_algorithms_hla.py`, `test_algorithms.py`, `test_final_quality.py`, `test_correction_backend.py`, `test_review_regressions.py` con `pytest -q --tb=short --junitxml=...`.

`final.xml`: ejecución conjunta de las fuentes finales de `test_final_algorithms_hla.py`, incluidos formulario, migración y lotes. `ampliacion.xml` y `migration.xml` conservan comprobaciones intermedias; se superponen y **no se suman** como pruebas distintas.

`benchmark.json`: `apps/services/.venv/bin/python apps/services/scripts/benchmark_academic.py`. Tamaños 10/100/1.000 para Dijkstra, HK, explicación, ranking sintético, SES y detección de inconsistencias, tiempo y pico de asignaciones Python con `tracemalloc`. Grafos sintéticos lineales/dispersos, una medición por tamaño; no benchmark HTTP, RSS, carga sostenida ni grafos densos máximos.

Ruff de los módulos nuevos y modificados de HLA/algoritmos/pruebas/formulario: aprobado. `git diff --check`: aprobado. Contratos regenerados con `apps/services/.venv/bin/python apps/services/scripts/document.py --contracts-only`.

## Incidencias conservadas

1. Primer intento: el modelo estricto rechazó strings de fecha en campos datetime. Corregido a contratos textuales con validación explícita de zona/orden.
2. Primera instalación: FK apuntaba a la vista lógica `files` dentro del esquema físico. Corregida a `stored_file(file_id)`.
3. Sandbox rechazó bind local en una ejecución; las integraciones siguientes utilizaron ejecución autorizada con puertos temporales.
4. Dos pruebas de inmutabilidad fallaron: el propietario SQL podía actualizar simulaciones. Se añadió trigger append-only además de permisos de servicio. Rechazo comprobado después.
5. Primer ensayo de migración: ruta de socket PostgreSQL superior a 103 bytes. Corregido el fixture a directorio corto en `/tmp`.
6. Preparación del ensayo v13: el catálogo actual intentó crear una vista sobre la tabla v14. El fixture ahora reproduce catálogo y versión anteriores conjuntamente.
7. El entorno base no sembraba recursos: el ensayo ahora crea unidad, muestra y resultado explícitos antes de migrar.
8. Regresión ampliada: 63/64 aprobados; el evento `ACADEMIC_ALGORITHM_EXECUTED` no estaba clasificado. Se añadió al catálogo como negocio registrado y se repitió el caso de auditoría/exportación. El fallo original se conserva en `tests.xml`.

## Límites y pendientes

**Clínicos externos:** faltan protocolos institucionales por producto/órgano, versiones autorizadas de nomenclatura y acreditación/aprobación competente. Ningún perfil se habilitó clínicamente ni se fabricó aprobación.

**Técnicos aún abiertos del prompt completo:** activación institucional de perfiles aprobados; exclusiones individualizadas en una nueva versión del motor operativo; conexión de las nuevas simulaciones con extracción autoritativa, rastreo y expedientes de Auditoría. La base operativa conserva sus algoritmos y verificaciones previos. No se declara el prompt completo terminado.

**Validación externa/plataformas:** grafo vial/proveedor y GPS físico no probados; sin nuevo GCS real para el vínculo documental, sin navegador visual ni ensayo monolito con APIs detenidas en esta entrega; sin despliegue Docker/GCP de 0.4.2/esquema 14. La migración probada usa instalación temporal v13 con datos ficticios, no una copia restaurada de producción.
