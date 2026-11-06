# Informe, alcance y arquitectura

## 1. Objeto y método

Se auditó completo el [prompt 01](../../prompts/entrega-final/01_backend_y_microservicios.md), aplicando el [Protocolo de comprobación](../../prompts/entrega-final/GUIA_EJECUCION_Y_COMPROBACION.md) y el [complemento 09](../../prompts/entrega-final/09_rastreo_gps_websockets.md). También se consultaron [AGENTS.md](../../../AGENTS.md), [PROJECT_STATUS.md](../../../PROJECT_STATUS.md) y [contexto y reglas](../../prompts/entrega-final/00_contexto_y_reglas.md).

La revisión utilizó CodeGraph antes de localizar o leer código. Se inspeccionaron rutas, DTO, XSD, permisos, migraciones, workers, eventos, estados y pruebas. Solo se ejecutaron pruebas existentes con datos ficticios y procesos temporales aislados. No se corrigió código, no se escribieron nuevas pruebas, no se desplegó, no se publicaron cambios y no se detuvieron servicios activos ajenos.

Durante la auditoría tampoco se editaron documentación ni `PROJECT_STATUS.md`. Este expediente y la referencia posterior en ese archivo corresponden al encargo separado de guardar el informe.

## 2. Identificación de las fuentes

| Dato | Valor |
| --- | --- |
| Fecha | 28 de octubre de 2026 |
| Inicio del manifiesto | `2026-10-28T15:17:45.713682+00:00` |
| Cierre de reconciliación | `2026-10-28T15:55:09.256636+00:00` |
| Commit base | `8909baf8458dff797d40d15541c57c66c14ef964` |
| Cambios locales | Sí; el commit por sí solo no identifica las fuentes probadas |
| Versión / API / esquema | `0.4.0` / `v1` / `11` |
| Archivos del manifiesto | 3.105, versionados y no ignorados, incluidos cambios locales |
| SHA-256 agregado | `d7f5ec0024d6ce058616fee97973f28895c312a9c8d59e98db7a1eec63370184` |
| Integridad al finalizar y antes de archivar | Todos los archivos auditados coinciden con el manifiesto original |

El [manifiesto (archivo)](../../../documentation/evidencias/archivo/detalles-20261104.tar.gz) contiene el hash individual de cada archivo, no su contenido. El agregado se calculó sobre el diccionario de rutas y hashes serializado con `json.dumps(items, sort_keys=True).encode()`. No comprende archivos ignorados ni certifica un despliegue remoto.

## 3. Resultado de ejecución

| Ejecución | Resultado | Interpretación |
| --- | --- | --- |
| Intento completo inicial | 119 aprobadas, 202 errores de preparación, 2 omitidas | No se encontró `mongod` compatible. No se atribuye ese error a una regla de negocio. |
| Aceptación dirigida | 8 aprobadas | Arranque y aceptación; se superpone con el bloque backend. |
| Backend e integración | 165 aprobadas, 1 omitida | Incluye contratos, migraciones, concurrencia, seguridad, recuperación y WSS. |
| Baja e historial de donantes | 19 aprobadas | Regresión del comportamiento preexistente. |
| Regresión restante | 81 aprobadas, 1 omitida | Completa integración web, sesiones, caché, formularios y proyecciones. |
| Reconciliación de casos únicos | **321 aprobados, 2 omitidos, 323 recolectados** | Se deduplicó por `classname` y `name`; ningún error de preparación quedó sin reejecución aplicable. |

Los dos casos omitidos son GCS real sin bucket/ADC de prueba y navegador sin `REDHOUSE_BROWSER_TESTS=1`. No se presenta la suma de las filas como cantidad de pruebas distintas. La [reconciliación original](evidencias/redhouse-audit-01-reconciliacion.json) conserva los casos y resultados.

También aprobaron `scripts/build_shared_schema.py --check`, Ruff crítico y `git diff --check`. De Ruff y diff se conservó el resultado en el informe del chat, no un archivo de salida independiente. No se atribuye a esas comprobaciones cobertura funcional.

## 4. Evolución desde los once servicios

Se mantienen once servicios independientes; no hubo extracciones ni servicios nuevos. Cada uno conserva paquete, configuración, Dockerfile y ejecución propios. Las pruebas de importación aislada de paquetes aprobaron; no se reconstruyeron imágenes ni se desplegó esta versión durante la auditoría.

| Propietario | Puerto | Responsabilidades | Decisión |
| --- | --- | --- | --- |
| Identidad y acceso | 5101 | BE-01 y BE-02 | Ampliar dispositivos, autenticación reforzada y acreditaciones; conservar instituciones |
| Donantes | 5102 | BE-03, colecta/procesamiento de BE-13, BE-22 | Ampliar consentimiento y agenda bajo el mismo propietario |
| Receptores | 5103 | BE-04, solicitudes/retenciones de BE-16 | Conservar expediente/cobertura; ampliar autorización externa |
| Inventario | 5104 | BE-05, componentes de BE-13, BE-15, BE-17, BE-18, parte de BE-21 y BE-24 | Ampliar calidad, linaje, trazabilidad, analítica y conciliación |
| Compatibilidad | 5105 | BE-06 y BE-14 | Integrar Laboratorio sin otro motor ni copia de resultados |
| Priorización y geografía | 5106 | BE-07 | Conservar rutas, ranking y Hopcroft–Karp |
| Transporte | 5107 | BE-08, BE-19, BE-20, tiempos de BE-21, BE-23 | Ampliar rastreo, documentos, reportes y sincronización |
| Custodia | 5108 | BE-09 | Conservar cadena consumidora del hecho logístico de Transporte |
| Alertas | 5109 | BE-10 | Ampliar entrega externa, políticas y escalamiento |
| Auditoría | 5110 | BE-11 | Conservar bitácora y hallazgos; ampliar cobertura de eventos |
| Monitoreo | 5111 | BE-12 | Conservar observación independiente del commit de negocio |

Hay **18 módulos Python de dominio añadidos** respecto del commit base:

| Paquete | Módulos añadidos | Cantidad |
| --- | --- | ---: |
| `ms_identidad_acceso` | `devices.py`, `strong_auth.py`, `accreditations.py` | 3 |
| `ms_donantes` | `agenda.py` | 1 |
| `ms_receptores` | `authorizations.py` | 1 |
| `ms_inventario` | `quality.py`, `traceability.py`, `analytics.py`, `interoperability.py` | 4 |
| `ms_compatibilidad` | `laboratory.py` | 1 |
| `ms_transporte` | `tracking.py`, `tracking_socket.py`, `tracking_contracts.py`, `documents.py`, `reports.py`, `synchronization.py`, `analytics.py` | 7 |
| `ms_alertas` | `delivery.py` | 1 |
| Total | No incluye librerías comunes, scripts, contratos ni pruebas | **18** |

Este conteo describe módulos Python incorporados, no todos los módulos preexistentes ni servicios independientes. Se distinguen **24 responsabilidades**, **11 servicios**, **18 módulos añadidos** y las réplicas de ejecución.

**Réplicas actualmente desplegadas: NO VERIFICADO.** La prueba local ejecutó dos procesos gevent/TLS para WSS. No demuestra el despliegue actual en GCP ni convierte esos procesos en servicios de negocio adicionales.

## 5. Justificación de límites y propiedad

- Instituciones permanece en Identidad para conservar una autoridad de tenant, sedes, cuentas y permisos. No hay un segundo CRUD institucional.
- Donantes conserva consentimiento, evaluación, colecta, citas y cupos. Agenda usa la autoridad existente de reserva; no introduce otro contador independiente.
- Receptores protege la capacidad de la solicitud mediante retenciones. Inventario protege la unidad mediante la reserva. Son dos restricciones complementarias, no dos autoridades de reserva de la misma unidad.
- Donantes posee la donación y sus pasos; Inventario posee la disponibilidad y el fraccionamiento. El linaje referencia el origen sin duplicarlo.
- Laboratorio dentro de Compatibilidad evita copiar resultados entre motores. El hallazgo F2 muestra que falta integrar su versión con evaluación/dictamen; la agrupación no excusa esa omisión.
- Cadena de frío, vencimiento y destino se agrupan con Inventario porque deben aplicar las mismas guardas sobre la unidad. F1 identifica una ruta que todavía elude esas guardas.
- Transporte posee orden, asignación y rastreo. Identidad posee credenciales. Custodia recibe el hecho único; no emite una segunda transición logística. F5 identifica una entrada de telemetría aún paralela.
- Documentos y reportes reutilizan el almacenamiento privado ya existente en Transporte. Los reportes consultan al propietario del dato; no adquieren autoridad clínica.
- Alertas aísla entrega SMTP/push y reintentos del commit de negocio. Monitoreo observa y no debe ser requisito para operar. Auditoría conserva historia separada de la entidad mutable.
- La web modular reutiliza reglas versionadas mediante despacho local; no se acreditó un fallback HTTP inseguro tras escritura incierta. Su autonomía se probó bajo configuración académica.

La [matriz de implementación anterior](../../../documentation/entrega-final/backend/Matriz_BE.md) y los [diagramas de estados](../../../documentation/entrega-final/backend/Estados.md) son referencias de diseño. No sustituyen la matriz auditada ni los hallazgos de este expediente. Los consumidores previstos son web autorizada, Android JSON y escritorio XML/XSD; las pruebas de contratos no equivalen a aplicaciones terminadas.

## 6. Persistencia y migraciones

PostgreSQL compartido sigue siendo autoridad transaccional. Las vistas y credenciales separan propietarios. Las migraciones aditivas 008–011 incorporan 33 tablas a las 74 existentes: **107 de dominio y una técnica web**. Se conservaron UUID, relaciones e historiales en los casos ensayados.

La prueba de migración usó copias estructurales v6/v7 y registros ficticios de donante/evento, verificó dos actualizaciones y conservación de esos registros, permisos e historial. No se usó una copia de los datos habituales del usuario.

La comprobación de construcción parte del commit histórico `44eeaf90c445b4d9564c2f0ab2dd3167f0296418`, de 45 tablas. Verifica instalación y restauración estructural idénticas, catálogo de siete roles de usuario, rechazo de claves foráneas huérfanas, historia inmutable y revisión de caché. No debe confundirse ese punto de partida con las 74 tablas de la versión 7. El SHA-256 del esquema auditado es `63e6e3f3221e292677e44210358d78acbbe631a35e20bb68bb830e9a2d410dd6`.

MongoDB recibe proyecciones y eventos; no decide reservas. Redis conserva sesiones, permisos, revocaciones, límites y última posición temporal. GCS almacena binarios privados con referencias, generación y hash en bases; la nueva integración GCS se ensayó con un doble de SDK. PostgreSQL confirma los puntos de rastreo y su cursor antes del ACK; outbox permite recuperar la proyección MongoDB.

## 7. Límites de las pruebas y del resultado

- Las pruebas existentes aprobaron sin cubrir todas las variantes F1–F11. Los hallazgos estáticos no se presentan como reproducciones nuevas ejecutadas.
- El catálogo publicado contiene 238 operaciones HTTP, 104 pares de ejemplos de entrada JSON/XML y 13 pares de frames WSS. El recorrido de errores de una ruta no demuestra su alta exitosa ni un proceso clínico completo.
- El modo `TESTING` mantiene compatibilidad académica y desactiva por defecto ciertas exigencias operativas: MFA crítico, reautenticación, perfil de laboratorio y autorización externa de órgano. Hay pruebas dirigidas de esas exigencias; no se afirma integración conjunta de todas ellas con los clientes productivos.
- WSS se probó con TLS real, dos emisores, dos suscriptores JSON/XML y 24 puntos, con lectura retrasada. ACK medio **422.755 ms**, p95 **540.881 ms**. No mide mapa, precisión física, estrés sostenido ni SLA.
- Los receptores SMTP/HTTP locales prueban entrega al adaptador, reintentos y deduplicación; no recepción humana ni proveedores productivos. El receptor ClamD prueba protocolo, no firmas antivirus reales.
- GCS real y navegador quedaron omitidos. No se ejecutó un despliegue GCP nuevo, imágenes nuevas, aceptación física GPS ni las aplicaciones consumidoras.
- Infraestructura HLA, completitud y preselección no equivalen a evaluación HLA detallada, trasplantabilidad ni aprobación externa. F2 es un defecto técnico actual; el detalle clínico de etapa 02 sigue separado.

## 8. Veredicto

Bloquean el cierre F1–F3/F7 por integridad, revisión y auditoría; F4–F6 por rastreo; F8/F9/F11 por funciones y contratos; F10 por comprobación obligatoria ausente. Las dependencias posteriores no convierten esos defectos actuales en una continuación parcial aceptada.

**NO APTA PARA CONTINUAR**
