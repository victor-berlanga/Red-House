# Verificación backend: 28 de octubre de 2026

Código de la entrega: paquetes 0.4.0, contratos v1 y esquema compartido 11. Pruebas locales aisladas; no se migró la base habitual ni se desplegó en GCP. La [matriz BE](../../../entrega-final/backend/Matriz_BE.md) identifica la implementación y aceptación por responsabilidad. El [manual](../../../entrega-final/backend/README.md) conserva comandos, configuración y pendientes.

## Ejecuciones

No sumar estas cifras: las ejecuciones se superponen. Los informes de intentos con fallos se conservan y sus correcciones se identifican. Los JUnit omiten salidas capturadas y nombre del equipo; mantienen casos, resultado, duración y propiedades de medición.

| Evidencia | Resultado | Alcance y resolución |
| --- | --- | --- |
| [regresion.xml](regresion.xml) | 283 casos: 280 aprobados, 1 fallo, 2 omitidos; 1146.864 s | Regresión previa a los últimos ajustes. Único fallo: ejemplos MFA no cumplían longitudes/patrón. Corregido en `redhouse/examples.py`; reejecución de los 14 casos de `test_review_unit.py` aprobada dentro de cierre y políticas. |
| [integracion.xml](integracion.xml) | 18/18 aprobados; 251.115 s | Primera integración de documentos, adaptadores y rastreo. Evidencia de incremento, no sustituye las ejecuciones posteriores. |
| [cierre.xml](cierre.xml) | 53/53 aprobados; 382.571 s | Identidad MFA/reauth/recuperación, agenda/procesamiento/linaje, laboratorio/frío/destino, SMTP/push/documentos/reportes, GPS/WSS, custodia, sincronización, migraciones y paquetes independientes. Incluye dos procesos gevent TLS, caída de una y ambas réplicas y concurrencia de emisores/suscriptores. |
| [politicas-contratos.xml](politicas-contratos.xml) | 32 casos: 30 aprobados y 2 fallos; 119.760 s | Última ampliación de políticas inmutables. Falló la corrección de perfil térmico JSON/XML por `SELECT FOR UPDATE` sobre vista sin permiso UPDATE. Se retiró ese bloqueo: el registro es inmutable y UNIQUE(supersedes) evita bifurcar la corrección. |
| [politicas-correccion.xml](politicas-correccion.xml) | 8/8 aprobados; 43.169 s | Reejecuta los dos casos corregidos y catálogos, gate de laboratorio operativo, ejemplos WSS, preservación de ACL/sesiones y worker de caducidad deduplicado. Los dos fallos anteriores quedan resueltos. |
| [autonomia-contratos.xml](autonomia-contratos.xml) | 8/8 aprobados; 198.589 s | Web modular con todas las API detenidas, flujo de sangre/órgano y donación, Redis fallando/recuperado, contrato HTTP de todas las rutas registradas y salud. Usa datos/perfiles académicos; MFA operativo se valida por separado. |
| [esquema.json](esquema.json) | Instalación/restauración idénticas, 107 tablas de dominio | `build_shared_schema.py --check`: conserva base histórica, relaciones, historial, catálogos y roles. La comparación histórica parte de 45 tablas; el incremento desde la versión actual 7 agrega 33 a las 74 existentes. |
| [contratos.json](contratos.json) | 238 operaciones HTTP; 104 pares de solicitudes JSON/XML; 13 pares WSS | Todos los ejemplos con cuerpo validan DTO, XSD y paridad. Incluye propietarios y hash del esquema generado. No significa 238 procesos ni 238 operaciones clínicas ejecutadas con éxito. |

Se detectó una interrupción del servidor durante una ejecución; se repitió la suite hasta completar el informe `cierre.xml`. Un primer arranque del sandbox rechazó sockets localhost; las ejecuciones de integración posteriores usaron permiso para crear únicamente servicios temporales. No se trata de un fallo de dominio. Ningún fallo funcional observado queda sin una reejecución aprobada; no se presenta una segunda ejecución completa de toda la regresión como si hubiese ocurrido.

Las dos omisiones de la regresión son explícitas: GCS real sin bucket/ADC de pruebas configurados y recorrido opcional de navegador sin `REDHOUSE_BROWSER_TESTS=1`. No se tomaron nuevas capturas de navegador ni se verificó la instancia remota.

## Criterios comprobados

| Criterio | Prueba/evidencia |
| --- | --- |
| 24 responsabilidades delimitadas sin 24 procesos ni segunda reserva | [Matriz BE](../../../entrega-final/backend/Matriz_BE.md), catálogo de once propietarios, paquetes aislados en `test_review_unit`. |
| Conservación del esquema y registros | Copias estructurales v6/v7 con donante/evento ficticios conservados y migración repetida, privilegios y respaldo de 108 tablas incluyendo la técnica web; `test_audit_migration` en cierre/políticas. |
| JSON/XML de identidad y negocio | Helper `api` valida éxito contra JSON Schema o XSD+DTO en ambas representaciones. Ejemplos completos en contratos.json y errores de todas las rutas en autonomía-contratos.xml. |
| Roles/tenant, donante sin evaluación, solicitudes y reserva concurrente | Regresión de seguridad, flujos y recuperación; nuevos casos de agenda/calidad/dispositivos. No copiar permisos al cliente como autoridad. |
| MFA, prueba de reautenticación y recuperación de un uso | `test_final_identity`: TOTP vector RFC, secreto cifrado, contador, ámbito de proof, contacto verificado, SMTP receptor, expiración/política y revocación. |
| Muestra recibida, resultados completos/autorizados y corrección | `test_final_quality`: faltantes/rol indebido impiden liberar; versión nueva no autorizada invalida completitud; excursión pone cuarentena. |
| Unidad derivada y destino real separado de recepción | `test_final_operations` y `test_final_tracking`: padre/hijos, donación y destino; recepción sola no marca uso, TRANSFUSED se registra después con autorización. |
| Políticas, procedencia y caducidad | Políticas de alerta y frío con autor, institución, fuente, fecha efectiva, versión y supersedes; historias conservadas. Worker repetido bloquea vencimiento sin borrar ni duplicar alerta/evento. |
| Documento no analizado inaccesible y reportes privados | `test_final_delivery_documents`: 409 antes de análisis, 403 fuera del ámbito, generación/hash, CSV/PDF/XLSX legibles, rechazo de malware simulado y dependencia caída. |
| Recordatorio/escalamiento deduplicados y entrega externa | SMTP TCP y adaptador push HTTP receptores reales locales; fallo/reintento y seis entregas por tres etapas/dos canales. ACK/cierre/revocación. Aceptación del adaptador no significa lectura humana. |
| Comando repetido/conflicto y autorización actual | `test_final_tracking`: UUID persistente, mismo recibo, cuerpo distinto 409, versión 412, otro usuario/dispositivo revocado 403; cursor y finalización. |
| WSS real y GPS futuro | CLI ejecutada contra TLS verificado en JSON/XML, normalización RMC, spool cifrado, duplicados/desorden/replay, revocación, límites y dependencias reiniciadas. Hardware y mapas pendientes. |
| Autonomía y fallos parciales | Dos procesos WSS independientes, uno caído y ambos caídos; pruebas web con todas las API detenidas. SQL durable conserva puntos y Mongo se recupera por outbox; Redis/SQL fallidos no omiten autorización/persistencia. |

## Medición WSS acotada

`test_concurrent_emitters_subscribers_and_delayed_consumer` registra en propiedades del JUnit: **2 emisores, 2 suscriptores JSON/XML con lectura retrasada, 24 puntos**, todos los cursores 1–24 recuperados por ambos. Media publicación→ACK **304.948 ms**, p95 **427.112 ms** en esta ejecución local. TLS y persistencia SQL están dentro del recorrido. No incluye renderizado de mapa, precisión GPS real ni estrés sostenido; no constituye SLA. Los valores dependen del equipo y de la carga de las pruebas.

## Límites y pendientes reales

- GPS físico: modelo, protocolo/conector, conectividad, frecuencia, energía, instalación, precisión reportada, señal y revocación del dispositivo real. No se afirma integración física con una simulación.
- Clientes y mapa: etapas 03/04/05; proveedor/licencia/atribución/fecha de cartografía vigente, mapa estatal/local, accesibilidad, permisos Android y latencia hasta pantalla. TRACK-05/06 y aceptación gráfica de TRACK-10 siguen abiertos.
- Clínica: perfiles sintéticos y decisiones humanas. HLA clínico y ampliación de reglas/priorización quedan en prompt 02 más aprobación de expertos; no se certifica protocolo ni autorización sanitaria.
- Infraestructura externa: SMTP/push de producción, ClamAV real con firmas y GCS autorizado para los nuevos documentos. El ensayo ClamD usa receptor de protocolo; el SDK GCS usa doble. La evidencia histórica GCP conserva su alcance anterior.
- Operación: aprobar políticas de retención/eliminación, desplegar código/configuración de MFA y preparar clientes antes del endurecimiento productivo. Definir y medir RTO/RPO y capacidad/estrés sostenido en las etapas de infraestructura/pruebas.
- Reportes/analítica: exportación máxima 1000 filas, ventana de un año; demanda de máximo 1000 solicitudes con indicador de completitud, brecha bruta y pronóstico empírico sin validación predictiva clínica. Formatos regulatorios necesitan contraparte y revisión.

Ruff crítico, formato de los 198 archivos Python del ámbito y `git diff --check` aprobados. Se corrigió también el formato pendiente de `ms_auditoria/findings.py` sin alterar su comportamiento. Comandos completos y configuración en el [manual backend](../../../entrega-final/backend/README.md).
