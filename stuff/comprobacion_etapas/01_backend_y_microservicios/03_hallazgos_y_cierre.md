# Hallazgos y plan de cierre

Todos los hallazgos siguientes están **ABIERTOS** en el corte auditado. Sus estados de requisito están en las [matrices](02_matrices_requisitos.md). Este documento prepara trabajo posterior; no registra correcciones realizadas.

Las ubicaciones y números de línea corresponden al manifiesto auditado. Consultar CodeGraph y volver a comprobar las fuentes antes de editar. **Los escenarios de aceptación propuestos aquí no son pruebas ejecutadas.** La auditoría solo ejecutó pruebas preexistentes.

## 1. Orden recomendado

P1 indica prioridad de trabajo por integridad, autorización o historia; P2 indica funciones, contratos o comprobaciones incompletos. No son umbrales clínicos ni una autorización para omitir P2.

| Orden | Trabajo | Propietario | Criterio para avanzar |
| ---: | --- | --- | --- |
| 1 | F1: destino y correcciones | Inventario | Ninguna corrección evita tipo, recepción o calidad |
| 2 | F2 y parte SQL de F7: resultados, evaluación e historia | Compatibilidad e Inventario | Datos cambiados invalidan la revisión anterior; valores históricos protegidos |
| 3 | F3: datos obligatorios de custodia | Transporte/Custodia | Cada entrega de responsabilidad conserva evidencia requerida |
| 4 | F5, F4 y F6: ingreso único, autorización y recuperación GPS | Transporte/Identidad | Toda entrada usa los mismos controles; revocación y histórico comprobados |
| 5 | Resto de F7: eventos y clasificación | Propietarios/Auditoría | Cambios y decisiones nuevos consultables y exportables según permiso |
| 6 | F8: gestión posterior de rol/permisos | Identidad | Cambio institucional auditado con permisos vigentes en Redis |
| 7 | F11 y F9: consultas y reportes | Propietarios/Transporte | Filtros antes de límites; todos los reportes exigidos comprobados |
| 8 | Evidencia positiva BE-21 | Inventario/Transporte | Pronóstico con historia suficiente contrastado independientemente |
| 9 | F10 y regresión operativa | Transporte/Monitoreo/integración | Una réplica y caída total API distinguidas; nueva auditoría sobre fuentes finales |

Mantener rutas v1 compatibles o documentar una transición versionada explícita. No crear otro servicio, otra reserva ni otra regla clínica para resolver estos defectos.

## F1. Corrección de destino evita guardas obligatorias

- **Prioridad:** P1. **Requisitos:** BE-05, BE-15, BE-17, BE-18; estados/transiciones sin rutas alternativas.
- **Código:** [ms_inventario/quality.py](../../../apps/services/ms_inventario/quality.py), `resource_destination`, líneas 584–654; en especial `if not old` en 606 y controles 614–622.
- **Evidencia:** inspección estática. La prueba existente cubre el primer destino válido, no esta corrección inválida.
- **Comportamiento:** se comprueban institución actual, versión y referencia al último destino. Sin embargo, solo el primer registro valida estado, recepción, correspondencia `TRANSFUSED`/sangre o `TRANSPLANTED`/órgano y calidad. Cuando existe `old`, una corrección con `supersedes` omite ese bloque. La restricción SQL enumera destinos, pero no relaciona destino y tipo de recurso.
- **Consecuencia:** es posible registrar un destino incompatible tras un descarte/devolución, sin recepción o guardas de calidad. El historial conserva ambas filas, pero no garantiza que el nuevo hecho sea válido; además alimenta trazabilidad y analítica.
- **Acción:** aplicar invariantes también a correcciones. Distinguir corrección documental histórica de un uso nuevo; usar hechos y condiciones pertinentes sin inventar reglas clínicas ni exigir que un recurso ya retirado vuelva artificialmente a RECEIVED.
- **Aceptación pendiente:** sangre descartada no admite corrección a TRANSPLANTED; recurso sin recepción no admite uso clínico; cuarentena/controles impiden el uso cuando corresponda; corrección válida conserva autor, motivo, referencia, fecha, versión y fila previa; probar JSON/XML y ausencia de escritura en rechazos.

## F2. Resultados cambiados no invalidan evaluación y dictamen

- **Prioridad:** P1. **Requisitos:** BE-06, BE-14, BE-16.
- **Código:** [ms_compatibilidad/routes.py](../../../apps/services/ms_compatibilidad/routes.py), `evaluation_create`, desde línea 45; [laboratory.py](../../../apps/services/ms_compatibilidad/laboratory.py), `completeness` en 129 y `lab_result_create` en 328; [ms_inventario/routes.py](../../../apps/services/ms_inventario/routes.py), reserva desde 223; [quality.py](../../../apps/services/ms_inventario/quality.py), `guard` desde 152.
- **Evidencia:** inspección estática; las pruebas de calidad demuestran incompletitud mientras la corrección no está autorizada, pero no invalidación posterior del dictamen antiguo.
- **Comportamiento:** completitud genera fingerprint, IDs de resultados y versión de perfil. La evaluación conserva solicitud/receptor, versión del recurso y ruta, pero no esos datos de laboratorio. Registrar/autorizar una corrección no cambia por sí mismo la versión de inventario. La reserva comprueba completitud actual y versión de recurso, sin comparar el fingerprint con lo revisado.
- **Consecuencia:** al autorizar la corrección vuelve a existir completitud y puede reutilizarse una evaluación/dictamen anterior al cambio.
- **Acción:** fijar referencias/versiones/fingerprint de perfil, muestras y resultados relevantes en la instantánea de evaluación y revisión. Compararlos al reservar y en las operaciones que exigen vigencia. Definir invalidación explícita y auditable; conservar evaluación/dictamen anterior como historia.
- **Aceptación pendiente:** evaluación y dictamen favorables previos; nueva corrección de resultado autorizada; reserva con evaluación antigua rechazada; nueva evaluación/revisión requerida; misma garantía ante cambio de perfil pertinente; ambos formatos y persistencia del rechazo.
- **Límite:** no se exige aquí inventar matching HLA clínico. La invalidación técnica es obligatoria en etapa 01; el detalle HLA de etapa 02 y aprobación profesional son dependencias distintas.

## F3. Custodia opcional en transiciones críticas

- **Prioridad:** P1. **Requisito:** BE-09 y su integración BE-08.
- **Código:** [ms_transporte/routes.py](../../../apps/services/ms_transporte/routes.py), `Transition` en 37 (`custody: CustodyCheck | None = None`), comprobaciones condicionales desde 402/410.
- **Evidencia:** inspección más regresión existente. Los recorridos antiguos completan pasos con el helper de transición sin bloque custody; las pruebas nuevas comprueban campos incorrectos cuando el bloque sí se envía.
- **Comportamiento:** COLLECTED, DELIVERED y ACCEPTED pueden procesarse sin escaneo, sello, fecha de captura, contraparte declarada y aceptación electrónica. ACCEPTED comprueba calidad aunque falte el bloque, pero no obtiene los demás datos.
- **Acción:** definir datos obligatorios por entrega de responsabilidad y una transición compatible explícita para clientes existentes. Reutilizar el hecho original y la cadena inmutable; no crear una segunda transición en Custodia.
- **Aceptación pendiente:** omitir cada dato obligatorio rechaza el comando sin avance de estado; identidad/rol/institución de contraparte y recurso escaneado correctos; fechas válidas; repetición no duplica evento; JSON/XML; cadena reconstruible tras indisponibilidad del consumidor.
- **Límite:** JWT identifica al actor autenticado. La contraparte declarada no es una segunda firma, y la confirmación no constituye certificación legal.

## F4. Autorización WSS no revalidada por recurso durante el lote

- **Prioridad:** P1. **Requisitos:** BE-08, TRACK-03, TRACK-07 y TRACK-10.
- **Código:** [tracking_socket.py](../../../apps/services/ms_transporte/tracking_socket.py), bucles de envío 182–194 y 219–232; [tracking.py](../../../apps/services/ms_transporte/tracking.py), `access` en 85 y `snapshot` en 247.
- **Evidencia:** inspección estática. Los casos existentes de revocación ordinaria no comprueban el cambio concurrente durante un lote ya obtenido.
- **Comportamiento:** snapshot valida traslado/asignación/dispositivo antes de recuperar un lote. Cada envío posterior llama `authorize(kind, credential)`, que revalida credenciales/sesión/rol, pero no vuelve a comprobar la asignación y estado del recurso. La siguiente instantánea sí lo hace.
- **Consecuencia:** si se revoca la asignación/dispositivo o cambia el estado durante replay, pueden entregarse las posiciones restantes del lote antes de la siguiente comprobación. No se afirma una filtración permanente ni una reproducción nueva ejecutada.
- **Acción:** vincular cada entrega al permiso vigente del traslado/dispositivo/asignación, o a un mecanismo equivalente que invalide el lote de manera comprobable. Suspender/cerrar cuando no pueda autorizarse.
- **Aceptación pendiente:** revocar/reasignar/finalizar durante replay de varios puntos y con consumidor retrasado; no entregar posiciones después de perder el permiso; comprobar JSON/XML, expiración, Redis inaccesible y permisos institucionales actuales.

## F5. Ingreso de telemetría anterior permanece paralelo

- **Prioridad:** P1. **Requisitos:** BE-08, BE-24, TRACK-01/02/04/07.
- **Código:** [ms_transporte/routes.py](../../../apps/services/ms_transporte/routes.py), `telemetry_create` en 493 y `telemetry_list` en 557; [tracking.py](../../../apps/services/ms_transporte/tracking.py), `publish` desde 107. Prueba: [test_evidence_catalog.py](../../../apps/services/tests/test_evidence_catalog.py), recorrido desde 315.
- **Evidencia:** inspección y prueba existente que ingresa ubicación por la ruta antigua sin crear la nueva asignación GPS.
- **Comportamiento:** `/api/v1/shipments/{id}/telemetry` valida responsable, estado y fecha, pero escribe en `transport_telemetry` sin consultar `tracking_assignments` ni usar `tracking_points`. No produce el mismo cursor/flujo WSS. Su GET lee exclusivamente el historial antiguo.
- **Acción:** mantener compatibilidad v1 mediante un adaptador a la misma autorización, normalización, deduplicación, persistencia y distribución, o introducir una transición versionada explícita. Conservar datos históricos; no crear un tercer almacén ni borrar telemetría previa.
- **Aceptación pendiente:** todas las entradas autorizadas aparecen en el historial/cursor y suscripción correspondiente; ruta antigua no permite eludir asignación revocada; reenviar por dos entradas no duplica el mismo evento; origen/fuente y captura/recepción quedan explícitos; conservación/migración de registros anteriores.

## F6. Sin recuperación histórica fuera de la ventana de replay

- **Prioridad:** P2, obligatoria para el cierre. **Requisitos:** TRACK-04, BE-08 y recuperación relacionada con BE-23.
- **Código:** [tracking.py](../../../apps/services/ms_transporte/tracking.py), `snapshot`, líneas 247–274. La ventana predeterminada es 10.000 cursores; cada lote limita a 100 eventos.
- **Evidencia:** inspección; existe prueba de cursor inválido y resincronización, no recuperación de los puntos antiguos mediante otro contrato.
- **Comportamiento:** cursor anterior al mínimo devuelve `resync_required`. Una instantánea sin cursor devuelve última posición, sin los eventos perdidos. No existe API alternativa de historia antigua de `tracking_points`; GET telemetry consulta otra tabla.
- **Acción:** separar replay acotado de consulta histórica durable, autorizada y paginada. Explicar qué recupera cada mecanismo y cómo deduplicar al enlazarlos. Mantener captura y recepción originales.
- **Aceptación pendiente:** historial mayor que ventana, cursor vencido, recuperación paginada del hueco autorizado, continuación WSS sin pérdidas/duplicados y rechazo institucional. No inventar puntos ni presentar atrasados como actuales.

## F7. Cobertura de auditoría e inmutabilidad de laboratorio

- **Prioridad:** P1 para historia/decisiones; completar todo el grupo antes del cierre. **Requisitos:** BE-10, BE-11, BE-14, BE-15 y trazabilidad transversal.
- **Código de cambios sin evento:** [quality.py](../../../apps/services/ms_inventario/quality.py), `cold_equipment_create` 320–329; [delivery.py](../../../apps/services/ms_alertas/delivery.py), `alert_subscription_create` 333–365 y revocación 384–396. `atomic` no emite automáticamente un evento de dominio por cada función.
- **Código de clasificación:** [audit_catalog.py](../../../apps/services/redhouse/audit_catalog.py), `describe` en 135; [ms_auditoria/queries.py](../../../apps/services/ms_auditoria/queries.py), categorías predeterminadas en 21. Acciones nuevas como `LAB_RESULT_AUTHORIZED`, `RESOURCE_DESTINATION_RECORDED`, `MFA_ENROLLED`, `EXPORT_REQUESTED`, `EXTERNAL_AUTHORIZATION_RECORDED` y `DOCUMENT_PREPARED` quedan sin entrada específica.
- **Código de inmutabilidad:** [extension_schema.py](../../../apps/services/redhouse/extension_schema.py), `lab_results: True` en 32 y concesión de UPDATE desde 117; [009.sql](../../../apps/services/redhouse/shared_migrations/009.sql), tabla de resultados y lista de protección histórica.
- **Evidencia:** inspección estática. Las pruebas de historia de otras tablas y corrección por API no prueban protección de los valores originales con credencial de servicio.
- **Comportamiento:** alta de equipo y alta/revocación de suscripción no emiten evento; acciones no clasificadas caen en TECHNICAL/UNKNOWN y quedan fuera de la consulta predeterminada BUSINESS/DECISION/SECURITY; el rol de Compatibilidad puede actualizar todas las columnas de `lab_results` mediante su vista.
- **Acción:** emitir eventos con actor, institución, fecha, recurso y correlación apropiados; completar catálogo y clasificación sin exponer secretos/valores sensibles; proteger columnas de resultado, origen y versión contra sobrescritura, permitiendo solo las transiciones necesarias. Una opción técnica debe distinguir campos registrados de estado mutable, sin conceder UPDATE total como solución.
- **Aceptación pendiente:** verificar evento único y visible tras cada cambio; consulta/exportación incluye nuevas decisiones según permiso; rechazo auditado y minimizado; intento SQL con rol de servicio no reescribe valor histórico; corrección crea una versión y conserva la anterior; migración repetible preserva datos y permisos.

## F8. Gestión institucional de rol/permisos incompleta

- **Prioridad:** P2. **Requisito:** BE-01.
- **Código:** [ms_identidad_acceso/routes.py](../../../apps/services/ms_identidad_acceso/routes.py), `user_create` en 529 y `user_state` en 568.
- **Evidencia:** inspección del catálogo y rutas. La asignación al alta y la activación/desactivación sí tienen pruebas.
- **Comportamiento:** se asigna rol al crear usuario. El PATCH posterior modifica active/version e invalida permisos; no existe comando para cambiar el rol/permisos de una cuenta existente.
- **Acción:** completar gestión institucional mediante el propietario actual, con control de versión, auditoría, límites de privilegio y política explícita de sesiones. No hace falta crear otro servicio ni imponer un sistema de roles arbitrarios si no lo exige el dominio.
- **Aceptación pendiente:** ADMIN autorizado cambia rol permitido; actor/tenant ajeno rechazado; versión obsoleta/conflicto; Redis y tokens no mantienen permisos retirados; JSON/XML; recuperación ante escritura incierta y evento único.

## F9. Reportes y filtros incompletos

- **Prioridad:** P2. **Requisito:** BE-20.
- **Código:** [reports.py](../../../apps/services/ms_transporte/reports.py), SOURCES/FIELDS desde 22/47, `ReportCreate` en 62, `export_create` en 239; límite 282 antes del filtro temporal 291–302. [analytics.py de Transporte](../../../apps/services/ms_transporte/analytics.py) contiene tiempos observados no incorporados al exportador.
- **Evidencia:** inspección y pruebas de generación EXPIRY con PDF/CSV/XLSX mediante doble de GCS. No se acreditan todas las familias con esa prueba.
- **Comportamiento:** consultar un propietario con total superior a 1.000 bloquea el reporte antes de reducirlo por fechas, aunque la ventana solicitada sea pequeña. SHIPMENTS exporta departure_at/eta, sin tiempos observados. El control admite ventana/orden, pero no todos los filtros necesarios por familia.
- **Acción:** aplicar filtros autorizados en el propietario antes de paginar/limitar; mantener un límite operativo explícito. Completar el reporte de tiempos reales y la matriz de inventario, solicitudes, caducidad, tiempos, custodia, actividad y trazabilidad. Reutilizar GCS/autoridad existente.
- **Aceptación pendiente:** más de 1.000 registros totales y pocos dentro de ventana exportan correctamente; cada familia genera CSV/PDF/XLSX legibles; orden/filtros, permisos, otro usuario/tenant, fórmulas escapadas, análisis y descarga privada; pérdida de respuesta/reintento no duplica objeto/job; fechas estimadas no se presentan como duración observada.
- **Dependencia:** cerrar clasificación F7 para que ACTIVITY incluya decisiones nuevas. La integración GCS real se registra aparte de la lógica de selección/formato.

## F10. Caída total de API y pérdida de conexión no acreditadas

- **Prioridad:** P2; criterio obligatorio de etapa 01. **Requisitos:** aceptación de réplicas, BE-12, TRACK-09/10.
- **Código/evidencia:** [test_final_tracking.py](../../../apps/services/tests/test_final_tracking.py), prueba de dos procesos desde 661; cierre de socket antes de terminar proceso en 722; consulta a otra API activa en 748–755.
- **Resultado real:** dos listeners gevent/TLS se inician; un punto persiste y se recupera desde el sobreviviente. Al detener ambos, fallan sus conexiones WSS. Otra instancia HTTP de Transporte del fixture sigue funcionando y devuelve snapshot; Inventario sigue disponible.
- **Límite:** no es una caída total de todas las réplicas de la API Transporte. Se cierran previamente los sockets, por lo que no prueba interrupción inesperada de una conexión abierta ni drenaje del gateway.
- **Acción:** diseñar escenario aislado que identifique todas las instancias de una API, pruebe una caída y luego caída total. Mantener un socket abierto durante interrupción, registrar degradación y recuperación por cursor. Distinguir el ensayo local del gateway/despliegue de etapa 06.
- **Aceptación pendiente:** evidencia de qué procesos atendían solicitudes y cuáles se detuvieron; resultado con sobreviviente, fallo real cuando no queda instancia, estado que reciben consumidores, continuidad acordada de otros dominios, recuperación de historial/operaciones y ausencia de éxito falso.
- **Regla operativa:** detener solo procesos creados por el propio ensayo; nunca usar servicios habituales o producción como sustituto.

## F11. Consultas de nuevos recursos sin filtros/búsqueda completos

- **Prioridad:** P2. **Requisitos:** contratos y operaciones del prompt 01; BE-24 y propietarios afectados.
- **Código:** [extension_contracts.py](../../../apps/services/redhouse/extension_contracts.py), `install_reads` desde 40; usos de equipos/perfiles en [quality.py](../../../apps/services/ms_inventario/quality.py), desde 288.
- **Evidencia:** inspección. Existe paginación y detalle institucional; el helper recibe filtros opcionales y varios recursos nuevos no los declaran.
- **Comportamiento:** el catálogo de parámetros no ofrece búsqueda/filtros exigidos para esos recursos. No se afirma que toda consulta existente carezca de filtros ni que un orden fijo sea por sí mismo inválido.
- **Acción:** inventariar por recurso lista/detalle/alta/comandos, filtros, búsqueda, orden permitido y límites. Extender contratos JSON/XML/OpenAPI/DTO/XSD cuando corresponda, reutilizando validación y consultas parametrizadas. No ofrecer DELETE/PATCH genérico sobre registros históricos inmutables.
- **Aceptación pendiente:** filtros combinados, búsqueda válida/inválida, paginación estable, parámetros y orden permitidos, UTC con zona, enumeraciones, campos opcionales y límites; resultados minimizados por tenant; formatos y errores coherentes.

## 2. Otras comprobaciones necesarias, sin inventar nuevos defectos

| Pendiente | Estado al auditar | Cierre esperado |
| --- | --- | --- |
| BE-21, pronóstico positivo | PARCIAL: cálculo inspeccionado y caso de historial insuficiente probado | Datos sintéticos con historia suficiente; oráculo independiente; demanda/consumo/descarte/ventana/calidad explicados; medir tiempo sin ejecutar asignación |
| BE-19, GCS/antivirus reales | PARCIAL: doble SDK y receptor ClamD, GCS real omitido | Bucket/ADC autorizados y ClamAV real; análisis por generación/hash, rechazo y recuperación comprobados |
| Autonomía con políticas operativas juntas | Autonomía académica aprobada; controles reforzados probados por separado | Integrar MFA/reauth/perfil/constancia con clientes correspondientes sin atribuirlo al ensayo académico |
| Contratos positivos por operación | Catálogo y errores recorridos; flujos positivos seleccionados | Relacionar cada operación nueva con entrada válida, persistencia, respuesta y permisos, además de ejemplos/XSD |
| Documentación de cierre | El estado anterior afirma implementación más amplia que el veredicto | Después de corregir, actualizar matrices, contratos/manuales y PROJECT_STATUS con fuentes y resultados nuevos; conservar esta auditoría |

No se registró como defecto una supuesta segunda revisión desfavorable ignorada: la restricción de unicidad de la revisión no sustentaba esa hipótesis. Tampoco se exigen reglas clínicas inventadas, HL7/FHIR sin contraparte, 24 procesos ni firma legal inexistente.

## 3. Condición de salida

No cerrar un hallazgo por cambiar código o añadir una prueba sin ejecutar. Cada cierre debe enlazar requisito, fuentes finales, contrato, migración si aplica, caso positivo/negativo, resultado y límites. Repetir regresiones afectadas y ejecutar una nueva comprobación independiente. Conservar este corte histórico y sus evidencias originales.

**NO APTA PARA CONTINUAR**
