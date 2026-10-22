# Auditoría y formularios: resultados locales

Fecha: **21 de octubre de 2026**. Se ejecutaron ambos prompts de `stuff/prompts`. Este informe corresponde a la implementación y las pruebas locales en entornos aislados. Esa etapa no modificó el servicio público. Por solicitud posterior, se publicó en GCP: [respaldo, migración y verificación pública](../gcp/auditoria-formularios/RESULTADOS.md).

## Resultado comprobado

**176 casos únicos aprobados según la última ejecución de cada caso**, sin fallos ni errores pendientes en el conjunto ejecutado. No representa la ejecución de todos los tests del repositorio. [Resumen verificable por caso y ejecución](resumen.json).

Se conservan los informes de intentos anteriores: sus fallos no se ocultan ni se suman como casos nuevos. Al inicio, MongoDB agotó la espera de arranque; se habilitó una espera configurable únicamente para el entorno de pruebas. Después se corrigieron el borde/resumen visual, la espera de la transición responsive del navegador y expectativas de pruebas: 422 para caducidad, lectura del resultado de una reserva y selección con el perfil médico autorizado. Los casos afectados se repitieron y pasaron.

| Evidencia | Resultado de esa ejecución |
| --- | --- |
| [Regresión principal](regresion.xml) | 104 aprobados; tres fallos corregidos y comprobados posteriormente |
| [Verificación dirigida](verificacion-final.xml) | 69 aprobados; un caso de selección corregido después |
| [Cierre y respaldo](cierre.xml) | Hallazgos con API detenidas e inventario del respaldo aprobados; selección corregida después |
| [Selección de otra página](selector.xml) | Aprobado: conserva selección y confirmación tras rechazo |
| [Navegador final](navegador-final.xml) | Recorrido completo aprobado tras los ajustes finales de presentación |
| [Esquema](esquema.json) | Generación, restauración y comprobación del esquema de 74 tablas de dominio |

Entorno: Python 3.12.6, pytest 9.1.1, Flask 3.1.3, Pydantic 2.13.5, Psycopg 3.3.5, PostgreSQL 14, MongoDB 8.0.17 y Redis real. Cada sesión de integración creó motores con puertos libres y directorio privado en `/tmp`; los procesos se detuvieron al terminar. Se utilizaron únicamente cuentas y registros ficticios. Las credenciales no forman parte de estas evidencias.

## Criterios de aceptación y cobertura

| Requisito | Comprobación |
| --- | --- |
| Acciones, categorías y vista inicial | Eventos de negocio visibles; sesiones, lecturas y técnicos conservados y ocultos inicialmente |
| Ámbito autorizado | Exclusión de otra región, rechazo de perfiles, hallazgo ajeno y vínculo con evento ajeno |
| Filtros y exportación | Conteo, páginas y exportación coherentes; ventana temporal; filtros al regresar; CSV protegido contra fórmulas |
| Límites de exportación | 5.000 eventos exportados; 5.001 rechazados sin truncar |
| Trazabilidad | Vínculos documentados de solicitud, recurso y traslado; datos históricos ausentes sin reconstrucción inventada |
| Instantáneas nuevas | Cuenta, rol y folio capturados; contenido clínico no copiado a la bitácora |
| Hallazgos | Alta, atención, verificación y cierre; motivo/evidencia obligatorios; conflicto de versión; idempotencia; avisos dirigidos |
| Inmutabilidad | Rechazo de borrado de eventos, vínculos e historial por el rol operativo de Auditoría |
| Independencia del portal | Flujos de sangre/órganos, donación y ciclo de hallazgos con listeners HTTP de servicios detenidos |
| Validación JSON/XML | Campos, mensajes seguros, límites exactos y errores equivalentes; esquemas de respuesta y ejemplos de paquetes independientes |
| Donantes/receptores y textos | Longitudes, opcionales, espacios, folios, nombres, estudios y dependencias del consentimiento |
| Campañas | Orden/vencimiento de fechas, mínimo por citas reservadas, conflicto de versión y reenvío corregido |
| Solicitudes/rutas/ubicación/cuentas/catálogos | Límites numéricos y de texto; cantidad y órgano compatibles con el expediente; apertura/cierre del catálogo |
| Inventario/traslados | Causas separadas, rechazo sin filas parciales y guardado después de corregir |
| Portal | Valores, contraseña omitida, confirmaciones, selección fuera de la primera página, clave de idempotencia y permisos conservados |
| Archivos | Rechazos de contenido con corrección segura; archivo vacío/formato no admitido en el portal, aviso de reselección e inexistencia de filas parciales |
| Migración | Copia estructural v6 con donante/evento ficticios conservados exactamente; ejecución repetida; permisos; tres tablas nuevas |
| Respaldo | Enumeración de las 75 tablas actuales mediante consultas PostgreSQL reales, incluidas las tres de hallazgos |

Fuentes reproducibles: [auditoría y portal](../../../apps/services/tests/test_validation_audit.py), [límites y dependencias](../../../apps/services/tests/test_form_limits.py), [migración y respaldo](../../../apps/services/tests/test_audit_migration.py). Las regresiones incluyen los flujos HTTP, continuidad del monolito, mantenimiento, JWT/Redis, contratos, concurrencia y baja de donantes existentes.

## Navegador

Chrome con Playwright, escritorio de 1440 píxeles y formulario móvil de 390 píxeles. [Informe](browser/navegador.json): **cuatro grupos de comprobaciones aprobados y cero errores JavaScript**.

- Sin errores rojos al abrir ni durante la captura inicial; ayuda permanente; dos errores al enviar; borde/texto visibles; foco y enlaces con teclado.
- Dependencia del consentimiento rechazada por el servidor; nombre y confirmación conservados; corrección guardada.
- Tres categorías iniciales, búsqueda de un recurso, descarga CSV, regreso al listado filtrado y hallazgo vinculado al evento.
- Atención por el coordinador, envío a verificación y cierre por el auditor; evidencia obligatoria e historial visible.

[Formulario móvil](browser/errores-movil.png) · [Bitácora filtrada](browser/auditoria-filtrada.png) · [Hallazgo cerrado](browser/hallazgo-cerrado.png) · [CSV ficticio](browser/auditoria.csv).

La comprobación en navegador cubre esos recorridos. Los demás formularios se verificaron mediante contratos, límites y regresiones HTTP; no se atribuye una inspección visual individual a todas sus variantes.

## Reproducción

Desde la raíz, con las dependencias de desarrollo instaladas y binarios PostgreSQL, Redis y MongoDB disponibles:

```sh
export REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod"
export REDHOUSE_TEST_STARTUP_TIMEOUT=120
apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_validation_audit.py \
  apps/services/tests/test_form_limits.py \
  apps/services/tests/test_audit_migration.py \
  apps/services/tests/test_web_integration.py \
  apps/services/tests/test_continuity.py \
  apps/services/tests/test_maintenance_web.py \
  apps/services/tests/test_security_contracts.py \
  apps/services/tests/test_flows.py \
  apps/services/tests/test_review_unit.py \
  apps/services/tests/test_donor_withdrawal.py -q
```

El navegador es explícito para no exigir Node/Chrome en la suite Python. Con Chrome y Playwright instalados, indicar en `REDHOUSE_PLAYWRIGHT` la ruta del módulo si no se usa la instalación local ya existente:

```sh
REDHOUSE_BROWSER_TESTS=1 apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_validation_audit.py::test_browser_validation_and_finding_workflow -q
```

Las credenciales de prueba se entregan al navegador por entrada estándar. El script solo acepta `127.0.0.1`. El endpoint para centralizar eventos se registra únicamente dentro del test y no existe en la aplicación instalada.

Comprobaciones complementarias realizadas: Ruff en archivos nuevos y reglas de errores en Python, sintaxis JavaScript, `git diff --check`, `export_form_constraints.py --check`, `build_shared_schema.py --check` y `docker compose config --quiet`.

## Despliegue y límites de la evidencia

Está preparada la migración **global 6→7 / Auditoría 2→3**, con tres tablas adicionales, sin reescribir eventos ni reglas clínicas. [Guía de actualización y permisos](../../markdowns/Auditoria_y_formularios.md). El respaldo enumera las tablas instaladas y ya no depende de una lista documental anterior de 71 tablas.

En esta etapa local, la migración y restauración estructural se comprobaron en PostgreSQL aislado. La prueba del inventario del respaldo sustituyó únicamente el transporte Docker por una conexión PostgreSQL real. La actualización posterior de GCP sí ejecutó `backup.py --verify`, restauró los datos operativos en contenedores aislados, ensayó la migración y actualizó el despliegue público. Esa evidencia y sus 38 controles API se documentan por separado; no se suman a los 176 casos locales.

No se repitió carga/descarga contra GCS real: se comprobaron mensajes, validación de contenido y rechazos del formulario antes de almacenar. Se mantienen las restricciones existentes; no se modificaron reglas clínicas. La evidencia de hallazgos es texto/referencia documental; no se añadieron adjuntos ni reasignación de responsable en este incremento.
