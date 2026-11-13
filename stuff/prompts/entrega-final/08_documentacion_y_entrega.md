# Preparar documentación artefactos y demostración de la entrega final

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Consolida la entrega final a partir de la implementación y las pruebas de los prompts 01 a 07. Genera documentos y artefactos utilizables; no entregues solamente un índice o una lista de archivos por redactar.

## Comprobación de cierre

Contrasta requisitos originales, retroalimentación, código, contratos, migraciones, instalaciones, pruebas y resultados actuales. La matriz final incluye ID, componente, implementación, permiso, criterio de aceptación, caso, resultado, evidencia y límite externo.

Consulta también `../stuff/entregas.txt`, especialmente «TERCER PARCIAL» y «ENTREGA FINAL», y `../stuff/retroalimentacionSegundoParcial.txt` cuando estén disponibles. Los entregables académicos que se explicitan abajo deben conservarse aunque esos archivos externos no acompañen al repositorio. La exclusión de móvil/escritorio en el segundo parcial y la confirmación de su presentación anterior permanecen como antecedentes; no conviertas requisitos finales en incumplimientos retroactivos.

Aplica las decisiones vigentes de `00_contexto_y_reglas.md`: servidor privado como almacenamiento operativo principal y GCS opcional en producto, con prueba académica independiente; sin offline universal; Android probado en emulador e iOS en iPhone físico sin descargar Simulator; FCM/APNs no configurados y recepción física pendiente, bandeja/adaptadores verificables. macOS/Windows 11 son plataformas de trabajo y Linux es objetivo adicional verificable. Donante: feed de campañas/citas y compartir texto público con selector nativo. Transportista: mapa protagonista, tarea y siguiente acción. La revisión de UI exige pantallas renderizadas y recorridos observados.

Clasifica con precisión: implementado y probado, implementado pendiente de prueba externa, diseñado, pendiente de implementación y pendiente de aprobación clínica/normativa. No cierres una función por aparecer en un diagrama ni conviertas una dependencia clínica en una aprobación inventada.

Recibe de 05–07 el registro `documentation/entrega-final/continuidad/Matriz.md`, con los criterios CONT-01 a CONT-10 definidos en [Continuidad obligatoria de las etapas 01 a 04](07_integracion_pruebas_y_rendimiento.md#continuidad-obligatoria-de-las-etapas-01-a-04), y el resultado de integración de 07, incluidos los ensayos de continuidad operativa de [06](06_seguridad_infraestructura_y_continuidad.md). Para cada pendiente conserva origen, responsable, dependencia, acción, evidencia vigente y disposición final: resuelto y verificado, fallo técnico abierto, verificación pendiente o cambio de alcance autorizado por quien define el requisito. Identifica la decisión y su fecha; una excepción no acredita funcionamiento. Conserva los archivos de prompts 01–04 y sus resultados históricos. No los reejecutes ni reescribas para hacer coincidir el cierre; las brechas reales se atienden y verifican en las etapas posteriores correspondientes. Reutiliza la evidencia aplicable consolidada por 07; repite comprobaciones cuando haya cambios, fallos o dudas que invaliden su vigencia.

Si encuentras un defecto técnico que impide una función comprometida, corrígelo en el componente correspondiente y repite sus pruebas antes de describirlo como entregado. No ocultes la brecha modificando el requisito o el informe. Registra la cantidad real de servicios y la cobertura de las 24 responsabilidades; no fuerces una coincidencia numérica.

Explica expresamente que el profesor recomendó una arquitectura objetivo de 24 microservicios y presenta la matriz de evolución desde los once actuales. Conserva los 24 elementos recomendados como referencias funcionales, con su implementación y evidencia, aunque algunos se agrupen. Justifica cada agrupación o extracción y distingue cantidad real de servicios independientes, módulos y réplicas. No presentes 24 procesos como obligación ni una lista de 24 carpetas como cobertura funcional; demuestra que no hay duplicación de responsabilidades, reglas o autoridades.

Registra además el requisito textual «Sistema desplegado en la nube y en ubiquitous» de `../stuff/entregas.txt`. El usuario aclaró que Ubiquitous es la plataforma donde el equipo debe subir los entregables; esa subida queda a cargo humano. Prepara archivos e inventario verificables, conservando la confirmación de envío como pendiente del equipo. No lo declares cumplido por tener GCE ni inventes un despliegue técnico adicional.

## Documento técnico final

Genera fuente editable, Word y PDF en las carpetas existentes, con nombres propios de la entrega final, por ejemplo `documentation/markdowns/Reporte_tecnico_final.md`, `documentation/docx/Reporte_tecnico_final.docx` y `documentation/pdf/Reporte_tecnico_final.pdf`. Conserva los documentos del segundo parcial como antecedentes fechados.

Reutiliza el diseño institucional aprobado del reporte anterior: formato carta, tipografía y jerarquía, portada con datos reales autorizados, tablas legibles, pie de página e índice enlazado. La portada anterior puede servir como plantilla gráfica, pero no arrastres una fecha o datos de corte incorrectos. No inventes integrantes, profesor, fecha final, firmas ni URL de video.

Incluye al menos:

1. Resumen ejecutivo, problema, objetivos, beneficios, alcance, actores y límites legales/éticos/de privacidad.
2. Requisitos funcionales/no funcionales, historias/casos y matriz de trazabilidad por web, servicios, móvil, escritorio, datos e infraestructura.
3. Matriz rol/acción/recurso/ámbito, procesos sanguíneos y de órganos separados y revisión humana.
4. Arquitectura real: web autónoma, catálogo de propietarios, responsabilidades agrupadas/extraídas, dependencias, versiones y límites de continuidad.
5. Tres procesos completos con sus secuencias, pasos, estados, errores, compensaciones y consulta entre productos.
6. Diseño de datos y almacenamiento: PostgreSQL compartido, MongoDB, Redis y archivos privados del servidor; GCS opcional para producto, con resultado académico de prueba separado.
7. Contratos JSON, XML/XSD, API internas, autenticación, correlación, idempotencia, paginación, errores y sincronización.
8. Registro de pruebas/HLA y perfiles, fuentes/versiones, datos faltantes, evaluación, límites y dictamen profesional, sin presentar el filtro ABO como compatibilidad clínica.
9. Algoritmos con problema, entradas/salidas, variables, restricciones, pseudocódigo, complejidad, ejemplos, métricas y explicaciones.
10. móvil Android/iOS con Kotlin Multiplatform y Compose Multiplatform: arquitectura, cinco roles, JSON, feed donante, mapa/tarea transportista, cámara/QR/GPS, bandeja, permisos y almacenamiento local limitado a operaciones permitidas.
11. Escritorio PySide6/Python: arquitectura, XML/XSD, módulos internos, captura, tablas, reportes, etiquetas e impresión.
12. Seguridad, MFA/reautenticación, dispositivos, autorización institucional, auditoría, antimalware, privacidad y políticas documentales.
13. Docker/GCE, red, HTTPS, secretos, monitoreo, despliegue/migraciones, respaldos, recuperación y objetivos/resultados RTO-RPO.
14. Pruebas y mediciones actuales, Locust y volumen, contratos, regresión, fallos, usabilidad y dispositivos/plataformas realmente evaluados.
15. Limitaciones reales, aprobaciones externas, riesgos, trabajo futuro y conclusiones sustentadas.
16. Referencias primarias en APA 7, con citas en el texto y versiones de fuentes técnicas/normativas verificadas. No inventes consulta, vigencia o aprobación profesional.

## Modelos diagramas y catálogos

Actualiza modelos conceptual, lógico y físico PostgreSQL con tablas/índices/restricciones reales, linaje, auditoría y correspondencia por servicio. Sincroniza SQL de referencia con migraciones e instalación nueva, sin aplicar generadores sobre la base activa para extraer secretos.

Documenta colecciones MongoDB, documentos, índices, pipelines, versionamiento, crecimiento y reconstrucción; claves Redis, prefijos/ACL, TTL, revocación, caché, contadores y bloqueos; archivos privados del servidor y, por separado, bucket GCS si se prueba como requisito académico. Informa estado, generación/hash, metadatos, análisis, privacidad, retención y recuperación sin presentar GCS como almacenamiento operativo requerido.

Entrega diagramas legibles y fuentes editables de contexto, contenedores, componentes, despliegue, red, autenticación, almacenamiento, secuencia y comunicación. Incluye estados y flujos de los tres procesos y de las operaciones concretas que admiten borrador/caché local; no presentes un modo offline universal. Distingue lo desplegado de la arquitectura futura tolerante a pérdida de host.

Cada ficha de servicio debe tener propósito, propietario, límites, consumidores, dependencias, datos, eventos, puertos, endpoints públicos/internos, salud, imagen/worker, permisos, errores y evidencia. Los módulos agrupados se identifican como módulos; un microservicio debe ser desplegable individualmente.

## Documentación del GPS y rastreo en vivo

Consolida TRACK-01 a TRACK-10 de la [especificación de rastreo GPS por WebSockets y mapa de Nuevo León](09_rastreo_gps_websockets.md). Incluye contrato de ingreso/eventos JSON y XML/XSD, asignaciones de dispositivo, permisos, WSS/gateway, almacenamiento/cursor, reconexión, diagrama de datos y manual del simulador/adaptador. Documenta proveedor, cobertura, atribución y procedencia/actualización del mapa, separando cartografía, posición observada, ruta planificada y ETA.

Entrega evidencia del recorrido completo con puntos simulados y mapas actualizados por sockets reales, con privacidad y fallos. Documenta captura Android/iOS y las pruebas físicas ejecutadas o todavía pendientes, con evidencia por plataforma; registra modelo/protocolo y aceptación del GPS externo solo si se incorpora esa extensión opcional. No describas como probado un equipo inexistente ni cierres el seguimiento con una imagen estática o una simulación que evite el backend. Incorpora el alcance real en la matriz y en el guion de demostración.

## Manuales obligatorios

- **Instalación y despliegue:** requisitos/versiones, variables sin valores reales, secretos, PostgreSQL/MongoDB/Redis, Compose, arranque/parada, salud, migración, actualización por réplica, respaldo/restauración, rollback y diagnóstico. Incluir GCE/HTTPS y límites de autorización para modificar infraestructura.
- **Móvil Android/iOS:** Android Studio/SDK, Gradle, macOS/Xcode, configuración HTTPS, compilación/APK Android y compilación/arranque iOS, firma e instalación por plataforma, permisos de cámara/QR/GPS/push, cuentas ficticias obtenidas de forma privada, sincronización y cierre. Diferenciar claves de prueba y firma de entrega.
- **Escritorio:** entorno o instalable por plataforma verificada, configuración, almacén de credenciales, XML/XSD, actualización, lector, impresora, exportaciones y recuperación.
- **Usuario:** tareas por perfil y componente con capturas reales, errores frecuentes, permisos, incidentes, operaciones pendientes y límites clínicos. Las credenciales no se imprimen en el manual.
- **Técnico:** estructura, decisiones de arquitectura, propietarios de datos, contratos, estados, reglas/algoritmos, eventos, consistencia, seguridad, pipeline y extensión de módulos.
- **Operación y continuidad:** matriz de fallos, contactos/responsabilidades reales disponibles, alertas, indicadores, respaldo, recuperación, RTO/RPO y respuesta a indisponibilidad de GCS/Redis/host.

## Paquete liberable y reproducibilidad

Prepara una versión identificada con manifiesto de fuentes y hashes, dependencias fijadas, scripts y configuración de ejemplo sin secretos. Incluye APK de demostración, artefacto iOS para el destino autorizado, ejecutable/instalable de escritorio para plataformas verificadas, imágenes o instrucciones reproducibles, contratos/XSD, esquemas, datos ficticios y procedimientos de prueba.

En Android demuestra ejecución en emulador; no exijas teléfono. En iOS respeta la prueba con iPhone físico autorizado y no descargues runtime Simulator. Separa compilación, firma/provisioning, instalación, arranque y recorridos funcionales del iPhone identificado. Una `.app` arm64 sin firma solo acredita compilación. Si firma o acceso siguen pendientes, entrega fuentes/instrucciones y deja verificación abierta. No presentes recepción push física: FCM/APNs siguen pendientes externos por decisión. Verifica macOS y Windows 11 en alcance de trabajo y Linux como objetivo adicional, sin atribuir ejecución no realizada.

Revisa licencias de dependencias, mapas, iconos y bibliotecas necesarias para distribución, con fuentes oficiales. No incluyas credenciales, ADC, claves de firma privadas, `.env` real, backups privados ni datos clínicos reales en repositorio/ZIP/imágenes/instalables.

Demuestra instalación en clon limpio y datos nuevos, actualización desde copia de la versión vigente, reinicio sin reinicialización y restauración aislada. Mantén el origen y los datos habituales. El clon limpio del segundo parcial no acredita el paquete final ampliado.

Verifica que instrucciones y rutas funcionan desde la raíz, que se pueden ejecutar pruebas documentadas y que los instalables arrancan sin depender de rutas absolutas del equipo del desarrollador. Expón prerrequisitos externos y condiciones reales de compilación/firma.

## Demostración y participación del equipo

Prepara guion presencial y de video con datos ficticios: donación desde Android o iOS, procesamiento/escritorio, solicitud/evaluación/reserva, traslado con QR/GPS/evidencia, recepción XML, uso/destino, auditoría y panel web. Incluye rechazo institucional, escritura concurrente y caída de una réplica con recuperación. Nunca proyectes archivos privados o tokens completos.

Genera material de apoyo y capturas/grabaciones reales cuando el entorno lo permita. Prepara una alternativa honesta para dependencias externas caídas, mostrando estado y evidencia fechada sin sustituir ejecución por simulación oculta.

El video final es un entregable propio. Prepara y comprueba esta lista, con segmentos o marcas de tiempo que permitan localizar la evidencia:

- Problema, usuarios, alcance y arquitectura real de la solución.
- Sistema web, aplicación Android, aplicación iOS y escritorio, identificando las plataformas realmente ejecutadas y sus pendientes.
- Microservicios, Swagger/OpenAPI y una comunicación real JSON/XML con autenticación y datos sensibles ocultos.
- Monitoreo, despliegue GCP y dependencias de datos/archivos, mostrando la versión presentada.
- Algoritmo: problema, entradas, resultado explicable, restricciones y revisión humana.
- Pruebas de carga: entorno, perfiles, volumen, resultados de Locust y sus límites; no es necesario saturar la instalación durante la grabación.
- Integración de los procesos demostrados, autorización, rechazo y recuperación ante fallos conforme al guion.

Conserva archivo reproducible, duración, fecha, versión de fuentes/artefactos y ubicación de la grabación final. Un guion, capturas sueltas o el video del segundo parcial no cumplen este entregable. Si no se puede grabar un segmento requerido, registra la causa y la evidencia faltante sin marcarlo aprobado. La presentación presencial se prepara con el mismo alcance; distingue material preparado, ensayo y presentación efectivamente realizada.

Conserva la confirmación de que presentación y video del segundo parcial ya se realizaron. La demostración final ampliada requiere su propia evidencia; no reutilices esa confirmación como prueba de una presentación final inexistente. La publicación/envío de videos requiere autorización vigente y una URL comprobable; no inventes el enlace.

Construye un registro de responsabilidades y contribuciones sustentado en acuerdos, tareas, cambios y evidencias reales. No deduzcas dominio técnico individual exclusivamente de cantidad de commits ni atribuyas trabajo no comprobado. Si falta el reparto nominal, prepara el formato y solicita ese dato concreto sin detener documentación independiente.

Incluye guía de defensa técnica por componente: explicar arquitectura/contratos/migraciones, localizar y corregir un error pequeño en una rama o entorno de prueba, ejecutar pruebas y justificar decisiones. No introduzcas errores deliberados en la instalación entregada.

Entrega una **reflexión individual auténtica de cada integrante**, con autoría identificada, contribución propia, decisiones que puede explicar, una dificultad y su resolución, aprendizaje y limitaciones pendientes, vinculando evidencias cuando corresponda. La persona debe aportar y confirmar su contenido; no inventes experiencias, dominio técnico ni opiniones personales. Si falta su aportación, prepara preguntas o plantilla y registra ese entregable pendiente, continuando el trabajo independiente.

Consolida un **registro de incidencias** de la entrega final. Cada entrada debe incluir ID, fecha, componente/versión, entorno, síntoma e impacto, reproducción o evidencia, responsable, acción, estado y comprobación de resolución. Enlaza incidentes históricos pertinentes y fallos/repeticiones de 05–07 sin borrarlos, duplicarlos ni presentarlos como casos nuevos. Diferencia defecto técnico, fallo del arnés y dependencia externa; una incidencia cerrada requiere evidencia aplicable. Vincula las incidencias abiertas con el registro de pendientes y la matriz final.

## Verificación de documentos y cierre

Comprueba enlaces locales y referencias, títulos/índice y páginas, tablas/figuras, consistencia de números/versiones, ausencia de texto fuera de página, integridad Word/PDF y correspondencia con código/artefactos. Inspecciona visualmente el PDF y los diagramas relevantes; un archivo generado sin esa revisión no basta para declarar calidad editorial.

Entrega índice navegable de la versión final, matriz de cumplimiento, registro de pendientes con disposición, informes de pruebas, artefactos, manuales, video, material de presentación, participación, incidencias y reflexiones individuales, con brechas explícitas. Comprueba que el inventario académico contiene cada pieza y su estado. Actualiza `PROJECT_STATUS.md` y los índices vigentes conservando la historia.

El cierre depende de evidencia vigente de 07 y continuidad de 06: resultados por plataforma, procesos, contratos, permisos, recuperación, objetivos/mediciones RTO-RPO y pendientes heredados. GCS se verifica como requisito académico independiente aunque no sea dependencia del producto. Push físico, firma, prueba iPhone, aclaración de consigna y aprobación externa conservan estado propio; enumerarlos no los aprueba. Video, exposición, entrega individual y reflexiones requieren ejecución/aporte humano. No inventes evento, persona, autoría, respuesta o enlace. Puedes entregar paquete parcial identificado con precisión, sin atribuir aceptación integral.

La aprobación clínica institucional limita la operación clínica real; su ausencia no invalida por sí sola los mecanismos académicos que 02 y 07 permiten verificar con datos y perfiles sintéticos. Distingue ese límite de una función técnica o prueba académica obligatoria faltante. No conviertas el cierre académico en certificación médica ni presentes una dependencia clínica como resuelta mediante simulación.

La respuesta final debe indicar qué se entrega, cómo instalar/demostrar, qué verificaciones pasaron y qué aprobación externa o plataforma sigue pendiente. No declares sistema clínicamente certificado, alta disponibilidad multizona, publicación en tienda o aceptación académica si no existe evidencia verificable.

## Alcance móvil y aceptación por destino

Conserva el alcance Android/iOS de Kotlin Multiplatform/Compose Multiplatform establecido el 6 de noviembre de 2026 y la decisión posterior de prueba en iPhone físico. Documenta código compartido y adaptadores, permisos, segundo plano, seguridad, push y pruebas por destino. Entrega APK, artefacto iOS e instrucciones macOS/Xcode conforme al apartado de reproducibilidad, separando compilación, firma, instalación y ejecución. No impongas descargar Simulator ni declares probado un teléfono o publicadas tiendas sin evidencia. Muestra el recorrido aplicación móvil → Transporte → WSS → mapas; GPS externo queda opcional.
