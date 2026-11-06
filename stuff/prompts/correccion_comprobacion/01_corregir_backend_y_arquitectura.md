# Corregir etapa 01, revisar arquitectura y verificar operación

Este prompt encarga implementación correctiva y comprobación. Guardarlo no ejecuta correcciones ni autoriza por sí mismo un despliegue. Copia el contenido desde «Encargo» en una conversación de trabajo.

## Encargo

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Corrige todos los hallazgos F1–F11 de la comprobación de etapa 01, completa sus criterios pendientes y revisa de forma crítica la distribución de responsabilidades entre microservicios. Implementa los cambios justificados y pruébalos; no termines con un plan ni con una matriz sin ejecución.

### 1. Fuentes y diagnóstico inicial

Lee completos:

- `AGENTS.md` y `PROJECT_STATUS.md`.
- Los documentos README y 01–05 de `stuff/comprobacion_etapas/01_backend_y_microservicios/`, junto con su índice de evidencias originales.
- `stuff/prompts/entrega-final/00_contexto_y_reglas.md`.
- `stuff/prompts/entrega-final/01_backend_y_microservicios.md` y `09_rastreo_gps_websockets.md`.
- La arquitectura, los contratos, los modelos de datos y las guías vigentes de operación afectados. Consulta la retroalimentación original del profesor si está disponible en la ubicación indicada por el contexto 00.

Usa CodeGraph antes de localizar o leer código cuando exista `.codegraph/`. Comprueba el árbol actual y registra commit, cambios locales y manifiesto de fuentes. No descartes trabajo previo. El expediente histórico corresponde a `8909baf` más cambios locales, versión 0.4.0 y esquema 11; verifica el estado actual antes de atribuirle esos datos.

Construye una matriz de cierre que relacione F1–F11, BE-01 a BE-24, TRACK-01 a TRACK-10 y criterios transversales con código actual, defecto confirmado, acción, propietario, contrato, migración, prueba, resultado, evidencia y dependencia. Revisa también requisitos no representados por un hallazgo: cerrar once filas no demuestra cumplimiento completo del prompt original.

### 2. Reconsiderar los límites de servicios, sin preservar una cifra

El profesor propuso una arquitectura objetivo de 24 microservicios. Los once existentes son el punto de partida, no una restricción de diseño ni una cantidad que deba defenderse. Tampoco hay que crear exactamente 24 por cuota. Conserva visibles las 24 responsabilidades y explica de manera verificable cada agrupación o separación respecto de la propuesta docente.

No interpretes las instrucciones de conservar datos, contratos y propietarios como prohibición de extraer servicios. Reutilizar una biblioteca, un bucket o PostgreSQL no obliga a compartir servicio. Evitar trabajo de migración o conservar el número actual no son justificaciones suficientes. Tampoco crees un servicio por tabla, endpoint o nombre del catálogo.

Antes de fijar la arquitectura final, entrega y utiliza estos análisis:

1. Mapa actual de servicios, módulos, propietarios de datos y consumidores. Distingue propiedad lógica, almacenamiento compartido y llamadas reales.
2. Grafo dirigido de dependencias síncronas y asíncronas, incluidos gateway, web modular, workers y almacenes. Identifica ciclos, cadenas de llamadas críticas, dependencias obligatorias y propagación de fallos.
3. Comparación por agrupación entre conservar, reorganizar módulos o extraer un servicio. Evalúa cohesión de negocio, ciclo de vida, permisos, transacciones, carga, disponibilidad, despliegue, fallos y coste operativo de la separación. Sustenta cada decisión con código, flujos o mediciones; identifica las hipótesis sin medición.
4. Fronteras transaccionales de los flujos críticos. Indica qué confirma cada transacción PostgreSQL, sus restricciones/bloqueos, qué sucede ante concurrencia y qué escrituras posteriores son recuperables. Documenta outbox/inbox, idempotencia, compensación y estado incierto cuando intervengan varios servicios.
5. Arquitectura propuesta y diferencias frente a los 24 elementos del profesor. Explica beneficios y costes tanto de lo agrupado como de lo separado, con un registro de decisiones que permita defender el resultado ante el docente.

Revisa expresamente estas agrupaciones, sin imponer de antemano su separación:

- Identidad frente a Instituciones/acreditaciones.
- Laboratorio frente a Compatibilidad.
- Priorización frente a Geografía.
- Transporte frente a Rastreo, Documentos, Reportes y Sincronización.
- Inventario frente a Frío, Caducidades, Trazabilidad y Analítica.
- Donantes frente a Citas/campañas y Donación/procesamiento.

Extrae e implementa las responsabilidades cuya autonomía y beneficio estén justificados. Si conservas una agrupación cuestionada, demuestra su cohesión y por qué la separación empeoraría el diseño. No basta con decir que ya estaba implementada. Para rastreo, este encargo permite revisar su ubicación dentro de Transporte indicada en el prompt original, conservando autoridad del traslado y autorización por recurso.

ACID se evalúa por transacción; ni once ni veinticuatro servicios lo garantizan. PostgreSQL compartido y varias llamadas HTTP no constituyen una transacción global. No uses «cumple ACID» como argumento general sin identificar operación, invariantes, frontera y prueba.

Cada extracción debe tener propietario único, paquete/configuración, imagen y proceso independientes, contratos JSON/XML/XSD, salud, permisos, worker cuando corresponda, monitoreo y despliegue individual. Actualiza gateway, configuración local/Docker/GCP y consumidores afectados. Conserva PostgreSQL compartido y separación por credenciales/vistas; una extracción no autoriza acceso directo a datos ajenos. Migra referencias, colas y permisos sin doble autoridad ni doble escritura. Mantén rutas v1 o una transición versionada probada. Conserva puertos existentes y documenta los nuevos.

La web debe mantener su autonomía mediante módulos de dominio versionados; no la conviertas en dependiente obligatoria de las API ni introduzcas fallback que repita escrituras inciertas. Android sigue usando JSON y escritorio XML/XSD; ninguno accede directamente a almacenes.

### 3. Correcciones obligatorias y pruebas de cierre

Aplica los criterios completos del expediente. Como mínimo, implementa y ejecuta:

| Hallazgo | Corrección y evidencia exigidas |
| --- | --- |
| F1 | Las correcciones de destino también respetan tipo de recurso, recepción y calidad. Prueba destino incompatible, ausencia de recepción, cuarentena y corrección válida con motivo, autor, versión e historia preservada. Distingue corrección documental de uso nuevo sin exigir estados históricos artificiales. |
| F2 | Vincula evaluación/dictamen a versiones y fingerprint de los datos de laboratorio pertinentes. Tras corregir/autorizar resultados o cambiar el perfil pertinente, rechaza usar el dictamen anterior y exige nueva evaluación/revisión; conserva la historia. |
| F3 | Define y exige datos de custodia por entrega de responsabilidad. Omitir cada campo obligatorio debe rechazar sin avanzar estado. Comprueba identidad, institución, recurso escaneado, sello, fechas, aceptación, idempotencia y reconstrucción de cadena. Resuelve compatibilidad anterior explícitamente, sin mantener una vía que omita controles obligatorios. |
| F4 | Revalida autorización específica de traslado/dispositivo/asignación durante la entrega WSS. Revoca, reasigna y finaliza durante replay con lector lento; no entregues posiciones tras perder permiso. Incluye expiración y Redis inaccesible. |
| F5 | Unifica ingreso antiguo y nuevo de telemetría mediante adaptador o transición explícita: misma autorización, normalización, deduplicación, persistencia, cursor y distribución. Conserva historia anterior y prueba que ninguna entrada evade una revocación. |
| F6 | Implementa historia durable autorizada y paginada fuera de la ventana de replay. Recupera un hueco mayor que la ventana y enlaza con WSS sin pérdidas ni duplicados. Conserva captura/recepción y rechaza otro tenant. |
| F7 | Completa emisión y clasificación de eventos, consultas/exportaciones y protección SQL de valores históricos de laboratorio. Prueba cada evento nuevo, su visibilidad autorizada y rechazo de sobrescritura con credencial runtime. Las correcciones agregan versiones; los permisos solo permiten transiciones necesarias. |
| F8 | Implementa cambio institucional de rol/permisos con autorización, control de versión, límites de privilegio, auditoría y política de sesiones. Prueba retirada efectiva de permisos en Redis/tokens, actor/tenant ajeno y recuperación idempotente. |
| F9 | Filtra en el propietario antes de limitar/paginar. Con más de 1.000 filas totales y pocas en ventana, el reporte debe funcionar. Completa familias de inventario, solicitudes, caducidad, tiempos observados, custodia, actividad y trazabilidad en PDF/CSV/XLSX; prueba permisos, fórmulas escapadas, descarga privada y reintentos sin duplicación. |
| F10 | En entorno aislado, identifica todas las instancias de una API. Mantén conexión abierta, interrumpe inesperadamente una instancia, demuestra continuidad con sobreviviente y después fallo real sin ninguna instancia. Registra degradación, recuperación por cursor, persistencia y continuidad de otros dominios. No dejes una API del fixture activa que invalide el escenario. |
| F11 | Completa por recurso filtros, búsqueda, paginación estable, orden permitido, validación y documentación. Prueba combinaciones, parámetros inválidos, UTC, límites y aislamiento institucional. No añadas edición genérica de historia inmutable. |

Prueba JSON y XML/XSD donde corresponda, estado persistido y ausencia de escritura en rechazos. Incluye casos positivos, negativos, concurrencia y reintentos pertinentes. Usa servicios/almacenes reales temporales para integración; identifica los dobles unitarios. No reduzcas una prueba a comprobar la misma condición que acabas de escribir.

Completa además:

- BE-21: pronóstico positivo con historia sintética suficiente y resultado contrastado con un oráculo independiente; calidad, ventana, consumo, descarte, límites y tiempo medido.
- BE-19: integración real GCS y ClamAV con firmas cuando existan accesos autorizados; generación/hash, privacidad, rechazo, timeout y recuperación. Un doble SDK o receptor ClamD no acredita esas integraciones reales.
- Políticas operativas: integración conjunta de MFA, reautenticación, perfil de laboratorio y autorización externa cuando apliquen. No presentes recorridos en modo académico como validación de esa configuración.
- Contratos: entradas válidas, persistencia y permisos por operación nueva/afectada; recorrer documentación o errores no basta.
- Autonomía web, migraciones repetibles, permisos SQL/Redis, conservación de datos y regresión de dominios afectados por extracciones.

No inventes reglas clínicas, certificaciones o disponibilidad de hardware. HLA detallado, clientes completos, mapas y GPS físico siguen sujetos a sus etapas/dependencias; eso no excusa defectos técnicos actuales. Si falta una capacidad de interfaz necesaria para recorrer una corrección en navegador, implementa la integración mínima real y documenta ese alcance.

### 4. Navegador real y comprobación en producción

La comprobación en navegador es obligatoria. Ejecuta primero una prueba automatizada reproducible, preferentemente con Playwright o la herramienta existente, contra la aplicación completa en entorno aislado con configuración equivalente a producción. Activa expresamente las pruebas opcionales; no aceptes una omisión silenciosa ni sustituyas navegador por Flask test client, capturas estáticas o llamadas HTTP.

Después ejecuta una comprobación con navegador contra la URL HTTPS de producción vigente. Verifica la URL en la configuración y en el despliegue real; no asumas que una IP histórica sigue vigente. Comprueba versión de web, API, workers y esquema: debe corresponder al resultado correctivo. Si producción sigue en una versión anterior, su recorrido no demuestra las correcciones.

Recorridos mínimos según permisos y capacidades afectadas:

1. Inicio/cierre de sesión, MFA y reautenticación de perfiles críticos, sesiones expiradas y acceso denegado entre roles/instituciones usando cuentas de prueba.
2. Un flujo autorizado de solicitud, evaluación/revisión, reserva, traslado, custodia y recepción/destino con datos ficticios; verifica persistencia después de recargar y consulta coherente desde otro perfil autorizado.
3. Corrección de laboratorio que invalida la revisión antigua y rechazo visible al intentar reutilizarla; nueva revisión válida permite continuar.
4. Registro/corrección de destino y custodia con campos faltantes: mensaje útil y ausencia de avance indebido.
5. Cambio de rol y retirada efectiva de permisos; filtros, reportes y descarga privada, incluido rechazo de acceso ajeno.
6. Rastreo WSS por el gateway real con datos sintéticos identificados, reconexión y permiso vigente. Comprueba mapa y estados si están implementados; si faltan, registra el límite y no declares ese recorrido aprobado.
7. Auditoría visible de cambios y decisiones, sin datos sensibles expuestos; comprobación responsive en escritorio y móvil, consola JavaScript y solicitudes de red.

Distribuye los casos según el entorno: ejecuta negativos, concurrencia y fallos completos en aislamiento; repite los recorridos seguros en producción. No detengas dependencias ni provoques carga, interrupciones o cambios clínicos reales en producción. Usa tenant/cuentas/recursos sintéticos autorizados, identifica los registros y conserva la auditoría. No elimines historia para limpiar una prueba. No envíes correos/push a personas sin autorización.

Usa autorizaciones vigentes y accesos seguros disponibles. Este prompt exige preparar y verificar la versión correctiva, pero no concede nuevos gastos ni acceso inexistente. Antes de solicitar una autorización pendiente de despliegue o migración productiva, termina implementación, pruebas aisladas, respaldo/restauración ensayados, plan de despliegue, rollback y artefactos concretos revisables. Si el despliegue ya está autorizado en la conversación, ejecútalo dentro de su alcance y después verifica navegador; no vuelvas a pedir la misma aprobación.

Si faltan URL, credenciales, cuentas sintéticas o permiso para publicar/probar escrituras, continúa todo el trabajo independiente y señala exactamente qué falta. No inventes acceso, no pruebes sobre expedientes reales y no marques la aceptación productiva como cumplida. Probar localhost en modo producción no equivale a probar producción desplegada.

Conserva por recorrido: fecha, entorno/URL, versión desplegada, rol de prueba, pasos, esperado/obtenido, capturas, errores de consola/red, respuesta y evidencia de persistencia. Redacta tokens, cookies, credenciales y datos personales en trazas, vídeos, HAR y capturas antes de guardarlos. Una prueba exitosa demuestra esos recorridos en esa versión; no certifica todo el sistema ni capacidad sostenida.

### 5. Evidencia, documentación y condición de salida

Conserva intacto el expediente histórico. Guarda evidencia nueva en `documentation/evidencias/entrega-final/backend/correccion_comprobacion/`, identificada por ejecución y manifiesto, sin sobrescribir resultados anteriores.

Actualiza documentación vigente de arquitectura/decisiones, matriz de las 24 responsabilidades, contratos, modelos, instalación, despliegue, puertos, permisos, pruebas y `PROJECT_STATUS.md`. Explica el número final de servicios independientes, módulos y réplicas por separado. Incluye una explicación defendible ante el profesor de cada diferencia respecto de su propuesta de 24 servicios, con beneficios, costes y pruebas.

Ejecuta la regresión aplicable a las fuentes finales. Deduplica por identidad de caso si combinas ejecuciones; conserva intentos fallidos, correcciones, omisiones y comandos. Vincula cada cierre con código final, contrato, migración cuando aplique, prueba ejecutada y evidencia. Obtener pruebas verdes preexistentes no cierra variantes que no verifican.

Antes de terminar, vuelve a contrastar todos los requisitos de 01/09 y F1–F11. Separa claramente:

- Defectos corregidos y comprobados.
- Decisiones arquitectónicas implementadas y evidencia de independencia/cohesión.
- Pruebas locales frente a pruebas productivas de la misma versión.
- Dependencias externas y de etapas posteriores.
- Criterios todavía incumplidos y su bloqueo concreto.

No declares la etapa apta ni producción validada mientras falten criterios obligatorios o permanezcan defectos bloqueantes. Entrega el resultado de implementación y deja identificada la necesidad de una nueva comprobación independiente sobre las fuentes finales; no presentes tu autoevaluación como auditoría independiente.
