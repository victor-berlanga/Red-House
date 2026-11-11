# Revisión de aceptación de los siete criterios pendientes de etapa 03

Fecha: **6 de noviembre de 2026, America/Monterrey**. Las sondas registran UTC
(7 de noviembre). Encargo vigente: revisión y cierre local/integrado con tres veredictos,
posterior al encargo de corrección. El usuario confirmó **mantener la aceptación
integrada pendiente de 06**. No se encendió la VM, desplegó, escribió en GCS, cambió
IAM/red ni detuvo servicio habitual alguno. Etapas 01 y 02 conservadas.

**APTA LOCALMENTE PARA CONTINUAR A 04.** Los siete criterios permanecen **PARCIALES**
en aceptación integrada. La evidencia local previa sigue aplicando, se completaron
cuatro comprobaciones locales dirigidas y no quedó un defecto local reproducido sin
resolver en este alcance. Este veredicto no aprueba infraestructura ni descargas sin
análisis/autorización. Se adopta la distinción local/integral pedida en el encargo
actual; no se modifica el veredicto histórico ni se convierte un pendiente en aprobado.

## Evidencia histórica preservada y aplicabilidad

El expediente [correccion-20261106](../correccion-20261106/RESULTADOS.md) conserva sus
**90 casos únicos aprobados**, sus fallos/repeticiones y su veredicto de entonces.
**No se ejecutaron de nuevo.** Comparación SHA-256: las 1.234 fuentes del manifiesto
siguen idénticas y los 205 artefactos de ese expediente coinciden. El HEAD permanece
`cbe3503b39a60b6b0a995f1284b2f5b1c3405cae`, con cambios locales previos preservados.
No se atribuye toda la evidencia a ese commit: los manifiestos identifican el árbol.

La única ampliación de código de esta revisión es
`apps/services/tests/test_portal_document_acceptance.py`. No cambian producto,
contratos, migraciones, permisos, backend modular ni modo HTTP. Ver
[integridad previa](integridad-previa.json) y [fuentes revisadas](fuentes-revisadas.json).
Los recorridos históricos de Chrome, accesibilidad, persistencia, HTTP/modular y WSS
siguen siendo históricos aplicables, con los límites ya publicados.

## Inspección real del entorno

| Consulta ejecutada | Obtenido | Lo que no demuestra |
|---|---|---|
| `docker context show`, `docker ps`, `docker image ls` | Contexto `desktop-linux`; socket Docker inexistente. No se pudo inventariar contenedores/imágenes. | No prueba ausencia de imágenes; no se arrancó Docker ni se supuso un ClamAV activo. |
| Presencia local de binarios/configuración, sin publicar secretos | `gcloud`/Docker disponibles; Nginx/ClamAV no encontrados en PATH. ADC y override GCS históricos existen. Override cubre web/Transporte; no existe `.local/compose/apps/documentos.json`. Variables de ensayo GCS/ClamD/origen ausentes. | Presencia de ADC no garantiza vigencia o permiso de prueba. El campo `schema: 1` de `installation.json` es metadato del instalador, no versión SQL leída. |
| `gcloud compute instances list`, proyecto `sistemas-integracion-01` | Tres VM: `library-eg02`, `maquina01`, `red-house`, todas `TERMINATED`; `red-house` tiene etiqueta `academic`. | La VM de otro ejercicio, aunque tenga etiqueta `isolated`, no es un entorno autorizado de Red House. No se inspeccionó runtime remoto ni su esquema actual. |
| `gcloud storage buckets list`, mismo proyecto, solo metadatos | Único bucket listado: `red-house-evidencias-sistemas-integracion-01`; `public_access_prevention=enforced`, acceso uniforme activado. | No acredita descarga privada, análisis, autorización por objeto, retención ni aislamiento de pruebas. No se listaron/leyeron objetos ni se alteró el bucket. |
| Revisión de configuración versionada | Generadores existentes de ClamAV privado y TLS/WSS; gateway declara Upgrade, dos upstreams y lectura de 75 s. README GCP conserva esquema 16 como último despliegue documentado; portal local exige 17. | Tener configuración o un despliegue anterior no acredita su aplicación al código actual. No se ejecutó `nginx -t`, porque no hay binario/runtime disponible. |

Evidencia: [entorno local](entorno-local.json), [inventario remoto](inventario-gcp.json).
La primera consulta GCP dentro del sandbox no pudo escribir el archivo interno de
credenciales de gcloud; se repitió con acceso permitido para consulta de solo lectura.
Las dos consultas remotas acreditadas terminaron con código 0. No hubo rechazo del
revisor automático ni se solicitó permiso para modificar infraestructura.

Conclusión acotada: **no hay un entorno aislado operativo confirmado para este ensayo**.
No se afirma que todo el proyecto carezca de infraestructura. Crear/encender recursos,
actualizar la VM habitual o ensayar caídas sobre ella exigiría alcance y autorización
separados; el usuario decidió diferirlo a 06.

## Estado de los siete criterios

La evidencia histórica F/B/C/R/D conserva el significado de la matriz; **L** identifica
las cuatro pruebas locales nuevas de este expediente. Los responsables siguientes
se asignan por función de Equipo 01, sin inventar nombres personales.

| Criterio | Estado integrado y clasificación | Evidencia local aplicable | Pendiente, responsable y etapa | Prerrequisito y cierre exacto |
|---|---|---|---|---|
| WEB-12 | PARCIAL. Falta comprobación integrada de infraestructura; no se reprodujo defecto de laboratorio. | B: ABO/HLA, revisión/corrección, historia y rechazo de incompleto; F/R: vínculo privado y ámbito. L: generación/hash exactos y revocación en Documentos. | QA web + Documentos + infraestructura 06: estudio privado completo en Chrome. | Entorno autorizado, resultado propio y GCS/ClamAV reales; I06-01/02/04/05. |
| WEB-15 | PARCIAL. Dependencia de almacenamiento/análisis real en la evidencia del traslado. | B: secuencia de custodia hasta aceptación y rechazo ajeno; permisos de Transporte conservados. | QA web + Transporte/Documentos + 06: archivo real en el recorrido. | Traslado ficticio asignado y abierto, objeto privado analizado; I06-01/02/05, orden ajena rechazada. |
| WEB-19 | PARCIAL. Había cobertura local insuficientemente explícita de sucesión/generación; se completó con L. Queda integración real. | F: formulario/retención; R: análisis/formatos con dobles. L: sucesión 1→2, bifurcación 412, política obsoleta 412, bloqueo 409, generación/hash incorrectos 409, sesión revocada 401 y recuperación. | Documentos + seguridad/infraestructura 06 + QA web: ciclo general con objeto y motor reales. | Bucket privado, motor/firma real y política de conservación; I06-01 a I06-05. Metadatos SQL no prueban retención/hold en GCS. |
| WEB-21 | PARCIAL. Falta entrega integrada real; generación/filtros locales conservan aceptación. | F: 1.003 filas, formatos, fórmulas, contexto y revocación antes de extracción; B: reporte ajeno 403. L: firma solo tras análisis exacto y permiso vigente del propietario documental. | Documentos/Identidad + QA web + 06: descarga de los tres formatos y revocación entre creación/descarga. | Trabajo propio, worker y GCS/ClamAV reales; I06-06. La nueva prueba L de revocación es de documento general, no se atribuye a reporte real. |
| WEB-24 | PARCIAL. Integración de fallos con infraestructura de destino pendiente. | R: fallos de dependencias/procesos; B/D: reconexión/cartografía y continuidad; L: almacenamiento/escáner simulados no autorizan descarga y recuperación conserva documento. | Infraestructura 06 + QA web/Documentos/Transporte. | Fallos limitados al ensayo, restauración controlada y almacenes propios; I06-05/07/08. |
| TRACK-09 | PARCIAL. Gateway real y continuidad simultánea en destino sin comprobar. | B: WSS real y pérdida/replay/permisos; D: cartografía degradada con acceso privado; R: caída de procesos/almacenes. No se combinan como prueba de Nginx. | Infraestructura 06 + Transporte/Identidad + QA web. | Gateway y réplicas aislados; mapa abierto más escritura web autónoma durante caída; I06-07/08. |
| TRACK-10 | PARCIAL. Cierre integrado pendiente, trazabilidad local comprobada. | 90 casos históricos aplicables, cuatro nuevos locales, manifiestos y resultados separados; simulador identificado. | QA 03/06 integra I06-09; clientes físicos se aceptan en 04/05/07. | Completar I06-01 a I06-08 y conservar IDs/fuentes/estados. Teléfonos/escritorio no se presentan como probados ni bloquean por sí solos la 03 local. |

El [ensayo de cierre](../../../../entrega-final/portal/Aceptacion_integrada_06.md)
define cada I06, secuencia de navegador, consultas, cortes, recuperación, responsables,
prerrequisitos y solicitud mínima de autorización. **No se marcaron aprobados estos
siete criterios; la matriz conserva 27 APROBADOS y 7 PARCIALES.**

## Pruebas nuevas realmente ejecutadas

Motivo técnico: la revisión de casos anteriores no encontró aserciones explícitas
suficientes para sucesión de versiones, análisis de generación/hash distinto y
revocación posterior a creación. Se añadió cobertura focalizada; no se repitió la
suite completa ni se tocó el producto para conseguir un resultado favorable.

| Caso nuevo | Resultado final | Evidencia y límite |
|---|---|---|
| `test_document_versions_conflict_and_hold_are_persistent` | APROBADO en repetición dirigida | SQL conserva versiones y bloqueo; 412/403/409 por contrato, un evento de conservación. Doble GCS; no Chrome. |
| `test_document_exact_analysis_generation_and_revoked_download` | APROBADO | Generación solicitada al firmante igual a la analizada; generación/hash discordantes 409 sin firmar; ajeno 403, logout revoca en Redis y siguiente descarga 401. No descarga GCS real ni invalidación de URL ya emitida. |
| `test_document_dependency_failure_blocks_download_then_recovers[scanner]` | APROBADO | Motor sin configurar: 503, documento no VERIFIED, descarga 409; receptor TCP doble restaurado permite verificar el mismo ID. No prueba firmas antivirus reales. |
| `test_document_dependency_failure_blocks_download_then_recovers[storage]` | APROBADO | Doble SDK inyecta error de conexión: 503, descarga 409 y sin firma; recuperación verifica el mismo ID. No prueba caída real de GCS. |

Primera ejecución: **3 aprobados y 1 fallo**, 68,75 s. El fallo era una expectativa
incorrecta del comprobador: esperaba `legal_hold=False` en la segunda versión, pero
la migración 010 y el esquema vigente definen `DEFAULT true`. Se corrigió solo esa
expectativa y su comentario. Tras la repetición se ajustaron tres constructores de diccionario del fixture a literales por Ruff C408, sin cambio funcional; el manifiesto distingue esos hashes. Repetición del caso: **1 aprobado**, 45,32 s. Se conservan
[JUnit inicial](documents.xml), [JUnit dirigido](versions-repeat.xml) e
[identidades/conteo](ejecuciones.json). Resultado consolidado nuevo: **4 casos únicos
aprobados**, sin omisiones. No sumar las cinco ejecuciones como cinco casos.

Entorno: fixtures existentes con PostgreSQL/Redis/MongoDB temporales, cuentas
ficticias propias y API HTTP reales del entorno local. TestBucket ampliado registra
argumentos de firma; ClamD es receptor TCP doble. Ninguna conexión GCS en estos tests.
**No se ejecutó un navegador nuevo**: falta el entorno real requerido y se conserva
la evidencia Chrome histórica, sin presentarla como ejecutada hoy en esta revisión.

Comandos, desde raíz; para repetir elegir directorios de salida nuevos:

```sh
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_STARTUP_TIMEOUT=90 apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_portal_document_acceptance.py -q --tb=short \
  --junitxml=/private/tmp/rh-portal-acceptance-20261106/documents/junit.xml

REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" \
REDHOUSE_TEST_STARTUP_TIMEOUT=90 apps/services/.venv/bin/python -m pytest \
  apps/services/tests/test_portal_document_acceptance.py::test_document_versions_conflict_and_hold_are_persistent \
  -q --tb=short --junitxml=/private/tmp/rh-portal-acceptance-20261106/versions-repeat/junit.xml
```

También se ejecutaron verificación de hashes/conteo de JUnit histórico, revisión
estática de código/configuración, Ruff del nuevo test y comprobaciones documentales.
La [verificación final](verificacion-final.json) y el [manifiesto de este expediente](artefactos-sha256.json)
registran sus resultados. Logs completos temporales se conservan fuera de Git;
JUnit publicados no incluyen stdout/stderr de formularios o credenciales.

## Decisión y límites

El alcance web local tiene evidencia aplicable; las carencias locales de comprobación
identificadas en esta revisión quedan cubiertas por los casos nuevos. Las pruebas de
navegador con GCS/ClamAV y gateway reales continúan pendientes **en aceptación integrada
06**, por decisión expresa del usuario. No se aceptan descargas en cuarentena, datos
ajenos, fallback de escrituras ni una configuración insegura por falta de infraestructura.

La aprobación local permite desarrollar 04 sobre contratos existentes. No certifica
un despliegue, un motor clínico ni clientes móviles/escritorio. Las URL firmadas ya
emitidas tienen ventana de cinco minutos; revocar una sesión impide obtener una nueva
firma, no prueba invalidación inmediata de una URL anterior. Ese límite debe quedar
verificado y aceptado en seguridad 06 antes del cierre integral.

**APTA LOCALMENTE PARA CONTINUAR A 04.**
