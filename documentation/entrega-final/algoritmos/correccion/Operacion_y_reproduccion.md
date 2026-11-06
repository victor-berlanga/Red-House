# Corrección de etapa 02: operación y reproducción

Incremento 0.4.4, esquema 16. Publicado y comprobado en GCP el 02/11/2026; [expediente](../../../evidencias/gcp/etapa02-20261102/RESULTADOS.md). Doce procesos API configurados; once propietarios de negocio y Monitoreo. La web usa los mismos módulos de dominio mediante despacho WSGI local, con sus credenciales restringidas; no depende de listeners API. No se crea un servicio adicional. La prueba detiene exclusivamente los listeners del fixture temporal.

## Instalar y usar fuentes públicas

Desde raíz, con el entorno de servicios instalado:

```sh
apps/services/.venv/bin/python apps/services/scripts/fetch_public_references.py hla --version 3.66.0 --directory .local/reference-data/hla
```

Descarga HTTPS con validación TLS, máximo 2 MB, timeout de conexión 5 s/lectura 30 s y SHA-256 fijado. No sobrescribe una versión local con bytes diferentes. Una CA institucional se configura mediante `REQUESTS_CA_BUNDLE`; no desactivar TLS. Por defecto, la aplicación usa `.local/reference-data/hla` de la raíz. Otra ubicación requiere `HLA_REFERENCE_DIR=/ruta/absoluta/hla` tanto en Compatibilidad como en la web modular, con `3.66.0/Allelelist.txt` dentro. Montar ese directorio de solo lectura en contenedores autorizados. El despliegue autorizado del 02/11 montó el catálogo de solo lectura en la web y ambas réplicas de Compatibilidad. CI incorpora la adquisición; ejecución remota no comprobada.

El catálogo completo permanece local e ignorado por Git, con su licencia; el paquete incluye manifiesto y atribución. GET `/api/v1/laboratory/reference-sources` publica referencias y disponibilidad verificada. Perfil: `evidence_rules` selecciona IDs y `policy.require_hla_catalogue=true` exige pertenencia para toda tipificación HLA, cualquiera que sea su código de prueba. Resultado: `hla.catalogue_version="3.66.0"`; el servidor genera `catalogue_check`. El cliente no puede aportar una comprobación favorable. Sin selección, `NOT_CHECKED`. Los registros anteriores conservan su significado, sin verificación retroactiva inventada.

Portal: `/apoyo-decisiones/fuentes`; formularios de perfil y HLA con selección de referencia/edición; detalle del resultado con comprobación de nomenclatura y ausencia de aprobación clínica.

Las respuestas viales originales están en `redhouse/reference_data/roads/`. GET `/api/v1/regional-graph-sources` muestra integridad/vigencia. POST `/api/v1/regional-graphs/from-reference` acepta `reference_id="NL-OSRM-20261102"` y `supersedes` opcional. Requiere MEDICAL, JWT/Redis, institución, idempotencia y auditoría; admite JSON y XML/XSD. `/apoyo-decisiones/importar-rutas` ejecuta el mismo flujo. Seleccionar el grafo persistido en ALG-02-GEO. El cliente no aporta pesos reales ni URLs arbitrarias.

Para adquirir una nueva instantánea candidata sin reemplazar la instalada:

```sh
apps/services/.venv/bin/python apps/services/scripts/fetch_public_references.py roads --output /ruta/nueva/instantanea-vial
```

Consulta solo los tres pares públicos definidos, con más de un segundo entre peticiones. Revisar licencia, cobertura, calidad, hashes y fecha antes de instalar el nuevo paquete. Archivar el anterior, actualizar bajo otro ID y crear sucesor mediante `supersedes`; grafos/ejecuciones persistidos retienen procedencia y geometría. No cambiar archivos o IDs históricos para simular actualización. El importador rechaza directorios existentes. La demo permite uso razonable no comercial, sin SLA; operación real requiere proveedor/instancia y cobertura adecuados.

Se comprobó adquisición real de HLA y una segunda descarga vial con este importador. La descarga vial renovada quedó en evidencia, sin instalarse. Prueba reproducible:

```sh
apps/services/.venv/bin/python -m pytest apps/services/tests/test_public_reference_sources.py apps/services/tests/test_stage02_migration.py -q
```

Sin catálogo instalado, las pruebas que exigen pertenencia fallan; no se omiten ni sustituyen por regex. El paquete vial tiene vigencia finita: al caducar, revisar/instalar nueva edición y actualizar el fixture como otro incremento. No eliminar el control temporal para mantener verde una prueba.

## Cuatro niveles y dos ámbitos

1. Registro: muestra y resultados declarados, con procedencia, estado y correcciones enlazadas. `AUTHORIZED` autoriza un registro de laboratorio; no asigna un recurso.
2. Completitud: pruebas/loci exigidos por un perfil inmutable, vigencia y política técnica. `complete` y `clinical_approval=false` son distintos.
3. Evaluación: candidatos y exclusiones según instantánea; no genera dictámenes. Para órganos no interpreta HLA ni calcula PRA/cPRA/anticuerpos a partir de texto.
4. Dictamen: acto humano con cuenta, institución, motivo, fecha, ámbito e instantánea. La reserva exige vigencia actual; una propuesta no reserva.

`OPERATION_SCOPE=CLINICAL` es el valor operativo por defecto; `TESTING=True` usa `ACADEMIC` salvo configuración expresa. Inventario aplica la habilitación clínica al liberar, reservar y consumir controles de calidad, incluso cuando falta un perfil y se desactiva `REQUIRE_LAB_PROFILE`. La revisión de una evaluación también comprueba el ámbito. Un cambio de configuración no promueve una evaluación/dictamen académico o legado a clínico. Las decisiones antiguas reciben `operation_scope=LEGACY` sin alterar sus razones ni resultados.

La configuración `CLINICAL_APPROVERS` es un objeto JSON indexado por UUID del profesional, con `tenant_id`, `reference`, `components` y `valid_until` UTC. Su provisión exige acreditación externa verificable; el repositorio no contiene ninguna acreditación real. Una prueba configura una autoridad **ficticia** en memoria para verificar segregación, evidencia y revocación. No acredita práctica profesional. Retirar esa configuración invalida la habilitación. Los filtros RBC/ABO académicos nunca se activan como reglas clínicas por cambiar esta variable: la ejecución clínica habilitada por perfil mantiene revisión manual.

Se mantienen `REQUIRE_LAB_PROFILE`, `REQUIRE_ORGAN_AUTHORIZATION`, `MFA_REQUIRED_ROLES` y `REAUTH_REQUIRED_OPERATIONS`; la prueba de navegador los activa expresamente. Operaciones críticas: liberación, revisión de resultado/dictamen, reserva, destino, transición de perfil y resolución de anomalía. Reautenticación vinculada a operación, sesión y UUID de la ruta; reserva usa el UUID del recurso del cuerpo. El TTL y el uso único siguen perteneciendo a Identidad.

## Registro y estados

`lab_profiles` conserva autor, institución, propósito, fuente, pruebas, loci, versión, predecesor, inicio/fin y política. Solo nace DRAFT. `rule_actions` añade IN_REVIEW → APPROVED → RETIRED, o retiro desde DRAFT/IN_REVIEW. No se vuelve desde RETIRED ni se modifica una especificación aprobada: crear sucesor. APPROVED requiere otro autor, competencia vigente para producto/institución, perfil no sintético, documento RULE/RULE_APPROVAL verificado, vigencia finita y política documental. Gobernanza devuelve estado efectivo y acciones, separados del estado inicial inmutable.

Intervalo UTC `[effective_at, valid_until)`; sucesor efectivo invalida el anterior, aunque el anterior siga conservado. `COMPLETENESS-2.0`: `max_age_seconds` opcional (sin umbral clínico predeterminado), documentos según perfil, contradicciones declaradas entre resultados autorizados no sustituidos → revisión. Un valor diferente no demuestra incompatibilidad clínica. Ambigüedad/tipificación parcial no satisface HLA completo. Comparación de cadenas solo detecta diferencias documentales.

HLA admite dos identificadores soportados para la misma nomenclatura de dos puntos: `2010` y `2010:syntax-2` (validador técnico corregido). Seleccionan explícitamente la sintaxis soportada; una versión desconocida falla. Alelo: locus, `*`, entre dos y cuatro campos numéricos de al menos dos dígitos, sufijo opcional N/L/S/C/A/Q. `A*01` se guarda en `groups` con `partial=true`, nunca como alelo. La pertenencia al catálogo IPD-IMGT/HLA se comprueba si se selecciona la edición instalada; no se impone un conjunto clínico universal de loci. Las declaraciones históricas permanecen legibles, incluso si no serían válidas como entrada nueva.

La muestra tiene exactamente un sujeto directo (recurso, receptor o donación), perfil, institución y solicitud opcional. El recurso enlaza a su donación y esta a su donante; no se duplica identidad. Para receptor se valida `organ_type`. Solicitud y sujeto deben concordar por institución y producto. La prueba cruzada informada exige muestras donante/receptor, solicitud, técnica e interpretación **declarada**; el servidor no la deduce. PENDING/NOT_PERFORMED no contienen valores informados. REPORTED/CORRECTED requieren datos; HLA y prueba cruzada requieren emisión. En perfiles documentales, todo resultado informado/indeterminado exige emisión y documento verificado. Los perfiles académicos heredados sin esa política permiten el formato histórico; esto no habilita clínica.

Documentos es propietario único de objeto, privacidad, generación, SHA-256 y análisis. Para evitar circularidad se registra resultado pendiente, se prepara su documento privado, se verifica y se crea la corrección informada sobre la misma muestra. El resultado conserva una instantánea de metadatos, no el archivo. Otra muestra/institución, documento pendiente/rechazado o generación no limpia no permiten el vínculo. La prueba GCS usa un objeto ficticio nuevo y borra únicamente ese objeto; no modifica objetos habituales.

## Contratos y pantallas

Los contratos generados están en `apps/services/ms_<propietario>/contracts/`: OpenAPI, entrada JSON/XML, XSD y esquema de respuesta por operación. Se regeneran con `apps/services/.venv/bin/python apps/services/scripts/document.py --contracts-only`. DTO estrictos en entradas y variantes de resultado: evaluación explicada, cobertura, anomalías, insuficiencia histórica, geografía y salida algorítmica. La instantánea conserva el objeto documental versionado con estructura descrita por algoritmo. JSON para Android y XML/XSD para escritorio; ningún cliente recalcula reglas.

| Operación | Propietario / permiso | Persistencia y errores relevantes |
|---|---|---|
| POST/GET `/api/v1/laboratory/profiles`, `/{id}/governance`, POST `/{id}/actions` | Compatibilidad; MEDICAL para escritura/gobernanza, lectura de registro también OPERATOR | Especificación/acciones inmutables; 403 competencia/ámbito, 409 transición/vigencia, 412 secuencia, 422 contrato |
| POST muestras, `/{id}/receive`, resultados y `/{id}/review` | Compatibilidad; captura MEDICAL/OPERATOR, revisión MEDICAL | Estado recibido, emisión/documento/asociaciones; correcciones por `supersedes`, historial conservado |
| GET `/api/v1/laboratory/samples/{id}/completeness` | Compatibilidad; MEDICAL/OPERATOR de la institución | Completitud del sujeto de la muestra (recurso, receptor o donación), faltantes y conflictos; no dictamen |
| POST comprobación `/api/v1/laboratory/resources/{id}/check` | Compatibilidad; ámbito autorizado | Completitud, faltantes, conflictos, versión y huella; no dictamen |
| POST/GET evaluaciones, `/{id}/reproduce`, POST `/{id}/reviews` | Compatibilidad; MEDICAL institucional | Instantánea; consulta añade `validity` actual. 409 obsolescencia o clínica deshabilitada; reproducción no consulta reglas actuales |
| POST/GET `/api/v1/regional-graphs` | Priorización/Geografía; MEDICAL institucional | Grafo regional sintético inmutable; fuente, fecha, calidad, vigencia, restricciones, sucesor |
| POST/GET `/api/v1/decision-runs`, `/{id}/reproduce` | Priorización/Geografía; MEDICAL institucional | Seis ramas, SHA-256, instantánea, duración, resultado; 409 origen/vigencia, 422 límites, 503 dependencia |
| GET `/api/v1/decision-data` | Cada propietario: Inventario/Donantes/Receptores/Compatibilidad/Transporte; MEDICAL institucional | Solo datos mínimos; hasta 10.000 hechos por conjunto y 1.000 traslados; exceder falla explícitamente |
| GET `/api/v1/anomaly-reviews`, detalle, POST `/{id}/resolve` | Auditoría; lectura MEDICAL/COORDINATOR de institución o AUDITOR regional; resolución AUDITOR | Expediente único por huella, evidencia inalterable por runtime, historia de resolución; 403 ámbito, 412 ya resuelto |
| GET `/api/v1/documents/{id}/verified` | Documentos; permiso sobre sujeto e institución | Metadatos PRIVATE, generación/hash/CLEAN; 409 pendiente/rechazado; descarga firmada y restringida |

Toda petición protegida comprueba JWT/sesión Redis, permisos, idempotencia de escritura, correlación y auditoría según infraestructura existente. Los rechazos no insertan una reserva; el diario técnico de operación/compensación puede persistir, para recuperar intentos fallidos.

Portal: `/apoyo-decisiones`, formulario e historial, detalle con reproducción; `/laboratorio/perfiles` con estado efectivo; muestras/recepción/resultados; evaluación/dictamen y aviso de obsolescencia; `/revision-anomalias` con resolución autorizada. La captura web inicial de perfil es académica; la aprobación exige el procedimiento externo y API autorizada. Los formularios inicial y de corrección HLA conservan grupo parcial, ambigüedad, versión y antecedentes; la prueba cruzada dispone de campos explícitos para ambas muestras, solicitud, técnica e interpretación declarada. `/laboratorio/muestras/{id}/completitud` muestra la completitud actual por separado.

## Grafo regional y observaciones

Ejemplo: [grafo_nuevo_leon_sintetico.json](grafo_nuevo_leon_sintetico.json). Coordenadas aproximadas y pesos ficticios, no red vial real. Fecha de validez explícita; fuera de ella se registra una nueva versión. Adaptador reproducible:

```sh
apps/services/.venv/bin/python apps/services/scripts/register_regional_graph.py \
  --url https://HOST_AUTORIZADO --file documentation/entrega-final/algoritmos/correccion/grafo_nuevo_leon_sintetico.json \
  --key registro-nuevo-leon-sintetico-v1
```

El token se suministra por `REDHOUSE_ACCESS_TOKEN` fuera del repositorio. No se acepta un grafo arbitrario en `decision-runs`; se referencia el registro autorizado. La fuente pública OSRM/OSM y su licencia ya se integran mediante el importador descrito arriba; cobertura hospitalaria, actualidad vial operativa y hardware GPS siguen pendientes. La prueba integra ingreso WSS real con emisor SIMULATOR y lectura posterior por logística; no demuestra GPS físico.

| Concepto | Fuente y significado | Límite |
|---|---|---|
| Ubicación observada | Snapshot de Transporte; captura, recepción, precisión, fuente, estado LIVE/STALE/NO_FIX/NO_DATA | No extrapola medición ni completa coordenadas ausentes |
| Recorrido observado | Historial autorizado de Transporte hasta cursor de snapshot; máximo 2.000 eventos, `history_complete` | Lectura por API del propietario, no recepción WSS directa del cálculo; recepción por socket probada por separado |
| Ruta planificada | Grafo registrado, aristas permitidas y pesos declarados | No tráfico; fuente sintética o referencia OSRM/OSM identificada |
| ETA | Corte de simulación + minutos de ruta desde origen del grafo | No ETA medido desde GPS, no entrega ni condición térmica |

`received_via=OWNER_HISTORY_API` identifica la lectura por el algoritmo. La antigua entrada académica `websocket_track` solo declara puntos en HTTP; su métrica se llama `declared_track_points`, no acredita recepción WSS. Un proveedor/Transporte indisponible no produce una ruta o posición inventada.

## Migración, respaldo y reversión

Migración aditiva [015.sql](../../../../apps/services/redhouse/shared_migrations/015.sql); instalador `redhouse.shared_migrations.upgrade` con bloqueo global y ACL de propietarios. No ejecutar en una instalación habitual sin alcance autorizado y respaldo coordinado. Nuevo esquema instala 16; actualización desde 13/14/15 conserva historia. La migración 016 agrega referencias de perfil, comprobación HLA y procedencia vial sin recalcular registros anteriores. Repetir no duplica versiones.

La prueba `test_stage02_migration.py` crea bases 14 y 15 pobladas desde esquema histórico + migraciones, hace `pg_dump -Fc`, restaura con `pg_restore` en otra base nueva, migra dos veces y compara cada columna histórica, cantidad de filas y ACL. Cada origen permanece en su versión inicial; la copia llega a 16. Desde 15 también se comparan grafos, ejecuciones y acciones de regla. Es prueba de mecanismo sobre datos ficticios; no es un respaldo de producción.

Rollback operativo: detener exclusivamente escritores del despliegue autorizado; restaurar respaldo en base separada; comprobar versión, cuentas, ACL e historia; apuntar versión anterior de aplicación a esa copia y comprobar salud/flujos antes de habilitar escritores. No bajar esquema con DROP COLUMN ni borrar versiones nuevas. Cambios producidos después del respaldo requieren conciliación explícita. El usuario autorizó expresamente la publicación el 02/11/2026; el expediente GCP documenta respaldo, conservación, migración y comprobaciones.

## Comprobación reproducible

Ejecutar desde raíz, con PostgreSQL/MongoDB/Redis locales disponibles para el fixture. `conftest.py` crea puertos, bases, roles, secretos y datos ficticios temporales; no usa instalaciones habituales. Los sockets pueden requerir permisos del entorno de ejecución.

```sh
apps/services/.venv/bin/python -m pytest apps/services/tests/test_stage02_corrections.py apps/services/tests/test_stage02_oracles.py apps/services/tests/test_stage02_migration.py apps/services/tests/test_final_algorithms_hla.py apps/services/tests/test_final_quality.py -q --junitxml=/tmp/stage02-core.xml
apps/services/.venv/bin/python -m pytest apps/services/tests/test_correction_backend.py apps/services/tests/test_security_contracts.py apps/services/tests/test_flows.py apps/services/tests/test_algorithms.py -q --junitxml=/tmp/stage02-regression.xml
apps/services/.venv/bin/python apps/services/scripts/benchmark_stage02.py > /tmp/stage02-benchmark.json
```

Navegador en ejecución separada: `REDHOUSE_STAGE02_EVIDENCE=/ruta/nueva apps/services/.venv/bin/python -m pytest apps/services/tests/test_stage02_browser.py -q`. Requiere Chrome y Playwright (ruta predeterminada del entorno local o `REDHOUSE_PLAYWRIGHT`). Activa TLS, Secure, MFA, reautenticación y controles de laboratorio/órganos. No reutilizar con otros tests la sesión cuyo enrolamiento MFA revoca tokens iniciales.

GCS: seleccionar explícitamente bucket existente con `REDHOUSE_GCS_TEST_BUCKET`, proyecto y ADC autorizadas, sin versionar credenciales; ejecutar `test_stage02_gcs.py`. ClamD de esa prueba es un receptor TCP controlado, no una certificación antimalware. Sin acceso autorizado el requisito cloud queda no verificado; el doble SDK no lo sustituye.

Evidencia final y estados: [matriz](Matriz_cierre.md) y [expediente](../../../evidencias/entrega-final/algoritmos/correccion_comprobacion/20261101T042648Z/RESULTADOS.md). Las cuentas, referencias de competencia y datos de prueba son ficticios. La aceptación técnica no aprueba reglas clínicas.
