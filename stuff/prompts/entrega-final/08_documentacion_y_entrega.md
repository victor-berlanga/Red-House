# Preparar documentación artefactos y demostración de la entrega final

Trabaja en `/Users/victorberlanga/Programacion/integracion/Red-House`. Lee `AGENTS.md`, `PROJECT_STATUS.md` y `stuff/prompts/entrega-final/00_contexto_y_reglas.md`. Consolida la entrega final a partir de la implementación y las pruebas de los prompts 01 a 07. Genera documentos y artefactos utilizables; no entregues solamente un índice o una lista de archivos por redactar.

## Comprobación de cierre

Contrasta requisitos originales, retroalimentación, código, contratos, migraciones, instalaciones, pruebas y resultados actuales. La matriz final incluye ID, componente, implementación, permiso, criterio de aceptación, caso, resultado, evidencia y límite externo.

Clasifica con precisión: implementado y probado, implementado pendiente de prueba externa, diseñado, pendiente de implementación y pendiente de aprobación clínica/normativa. No cierres una función por aparecer en un diagrama ni conviertas una dependencia clínica en una aprobación inventada.

Si encuentras un defecto técnico que impide una función comprometida, corrígelo en el componente correspondiente y repite sus pruebas antes de describirlo como entregado. No ocultes la brecha modificando el requisito o el informe. Registra la cantidad real de servicios y la cobertura de las 24 responsabilidades; no fuerces una coincidencia numérica.

Explica expresamente que el profesor recomendó una arquitectura objetivo de 24 microservicios y presenta la matriz de evolución desde los once actuales. Conserva los 24 elementos recomendados como referencias funcionales, con su implementación y evidencia, aunque algunos se agrupen. Justifica cada agrupación o extracción y distingue cantidad real de servicios independientes, módulos y réplicas. No presentes 24 procesos como obligación ni una lista de 24 carpetas como cobertura funcional; demuestra que no hay duplicación de responsabilidades, reglas o autoridades.

## Documento técnico final

Genera fuente editable, Word y PDF en las carpetas existentes, con nombres propios de la entrega final, por ejemplo `documentation/markdowns/Reporte_tecnico_final.md`, `documentation/docx/Reporte_tecnico_final.docx` y `documentation/pdf/Reporte_tecnico_final.pdf`. Conserva los documentos del segundo parcial como antecedentes fechados.

Reutiliza el diseño institucional aprobado del reporte anterior: formato carta, tipografía y jerarquía, portada con datos reales autorizados, tablas legibles, pie de página e índice enlazado. La portada anterior puede servir como plantilla gráfica, pero no arrastres una fecha o datos de corte incorrectos. No inventes integrantes, profesor, fecha final, firmas ni URL de video.

Incluye al menos:

1. Resumen ejecutivo, problema, objetivos, beneficios, alcance, actores y límites legales/éticos/de privacidad.
2. Requisitos funcionales/no funcionales, historias/casos y matriz de trazabilidad por web, servicios, móvil, escritorio, datos e infraestructura.
3. Matriz rol/acción/recurso/ámbito, procesos sanguíneos y de órganos separados y revisión humana.
4. Arquitectura real: web autónoma, catálogo de propietarios, responsabilidades agrupadas/extraídas, dependencias, versiones y límites de continuidad.
5. Tres procesos completos con sus secuencias, pasos, estados, errores, compensaciones y consulta entre productos.
6. Diseño de datos y almacenamiento: PostgreSQL compartido, MongoDB, Redis y GCS con propietarios, ciclos de vida y permisos.
7. Contratos JSON, XML/XSD, API internas, autenticación, correlación, idempotencia, paginación, errores y sincronización.
8. Registro de pruebas/HLA y perfiles, fuentes/versiones, datos faltantes, evaluación, límites y dictamen profesional, sin presentar el filtro ABO como compatibilidad clínica.
9. Algoritmos con problema, entradas/salidas, variables, restricciones, pseudocódigo, complejidad, ejemplos, métricas y explicaciones.
10. Android Kotlin/Compose: arquitectura, pantallas por perfil, JSON, cámara/QR/GPS/push, datos locales, permisos y offline.
11. Escritorio PySide6/Python: arquitectura, XML/XSD, módulos internos, captura, tablas, reportes, etiquetas e impresión.
12. Seguridad, MFA/reautenticación, dispositivos, autorización institucional, auditoría, antimalware, privacidad y políticas documentales.
13. Docker/GCE, red, HTTPS, secretos, monitoreo, despliegue/migraciones, respaldos, recuperación y objetivos/resultados RTO-RPO.
14. Pruebas y mediciones actuales, Locust y volumen, contratos, regresión, fallos, usabilidad y dispositivos/plataformas realmente evaluados.
15. Limitaciones reales, aprobaciones externas, riesgos, trabajo futuro y conclusiones sustentadas.
16. Referencias primarias en APA 7, con citas en el texto y versiones de fuentes técnicas/normativas verificadas. No inventes consulta, vigencia o aprobación profesional.

## Modelos diagramas y catálogos

Actualiza modelos conceptual, lógico y físico PostgreSQL con tablas/índices/restricciones reales, linaje, auditoría y correspondencia por servicio. Sincroniza SQL de referencia con migraciones e instalación nueva, sin aplicar generadores sobre la base activa para extraer secretos.

Documenta colecciones MongoDB, documentos, índices, pipelines, versionamiento, crecimiento y reconstrucción; claves Redis, prefijos/ACL, TTL, revocación, caché, contadores y bloqueos; buckets, objetos/generaciones, metadatos, análisis, privacidad, retención, eliminación/recuperación y URLs firmadas.

Entrega diagramas legibles y fuentes editables de contexto, contenedores, componentes, despliegue, red, autenticación, almacenamiento, secuencia y comunicación. Incluye estados y flujos de datos de los tres procesos y del modo offline. Distingue lo desplegado de la arquitectura futura tolerante a pérdida de host; no dibujes multizona como existente si solo está diseñada.

Cada ficha de servicio debe tener propósito, propietario, límites, consumidores, dependencias, datos, eventos, puertos, endpoints públicos/internos, salud, imagen/worker, permisos, errores y evidencia. Los módulos agrupados se identifican como módulos; un microservicio debe ser desplegable individualmente.

## Documentación del GPS y rastreo en vivo

Consolida TRACK-01 a TRACK-10 de la [especificación de rastreo GPS por WebSockets y mapa de Nuevo León](09_rastreo_gps_websockets.md). Incluye contrato de ingreso/eventos JSON y XML/XSD, asignaciones de dispositivo, permisos, WSS/gateway, almacenamiento/cursor, reconexión, diagrama de datos y manual del simulador/adaptador. Documenta proveedor, cobertura, atribución y procedencia/actualización del mapa, separando cartografía, posición observada, ruta planificada y ETA.

Entrega evidencia del recorrido completo con puntos simulados y mapas actualizados por sockets reales, con privacidad y fallos. Registra modelo/protocolo/conectividad aún desconocidos del GPS físico, requisitos de integración y pruebas de aceptación para cuando esté disponible. No describas como probado un equipo inexistente ni cierres el seguimiento con una imagen estática o una simulación que evite el backend. Incorpora el alcance real en la matriz y en el guion de demostración.

## Manuales obligatorios

- **Instalación y despliegue:** requisitos/versiones, variables sin valores reales, secretos, PostgreSQL/MongoDB/Redis, Compose, arranque/parada, salud, migración, actualización por réplica, respaldo/restauración, rollback y diagnóstico. Incluir GCE/HTTPS y límites de autorización para modificar infraestructura.
- **Android:** Android Studio/SDK, Gradle, configuración HTTPS, compilación/APK, instalación, permisos de cámara/QR/GPS/push, cuentas ficticias obtenidas de forma privada, sincronización y cierre. Diferenciar claves de prueba y firma de entrega.
- **Escritorio:** entorno o instalable por plataforma verificada, configuración, almacén de credenciales, XML/XSD, actualización, lector, impresora, exportaciones y recuperación.
- **Usuario:** tareas por perfil y componente con capturas reales, errores frecuentes, permisos, incidentes, operaciones pendientes y límites clínicos. Las credenciales no se imprimen en el manual.
- **Técnico:** estructura, decisiones de arquitectura, propietarios de datos, contratos, estados, reglas/algoritmos, eventos, consistencia, seguridad, pipeline y extensión de módulos.
- **Operación y continuidad:** matriz de fallos, contactos/responsabilidades reales disponibles, alertas, indicadores, respaldo, recuperación, RTO/RPO y respuesta a indisponibilidad de GCS/Redis/host.

## Paquete liberable y reproducibilidad

Prepara una versión identificada con manifiesto de fuentes y hashes, dependencias fijadas, scripts y configuración de ejemplo sin secretos. Incluye APK de demostración, ejecutable/instalable de escritorio para plataformas verificadas, imágenes o instrucciones reproducibles, contratos/XSD, esquemas, datos ficticios y procedimientos de prueba.

Revisa licencias de dependencias, mapas, iconos y bibliotecas necesarias para distribución, con fuentes oficiales. No incluyas credenciales, ADC, claves de firma privadas, `.env` real, backups privados ni datos clínicos reales en repositorio/ZIP/imágenes/instalables.

Demuestra instalación en clon limpio y datos nuevos, actualización desde copia de la versión vigente, reinicio sin reinicialización y restauración aislada. Mantén el origen y los datos habituales. El clon limpio del segundo parcial no acredita el paquete final ampliado.

Verifica que instrucciones y rutas funcionan desde la raíz, que se pueden ejecutar pruebas documentadas y que los instalables arrancan sin depender de rutas absolutas del equipo del desarrollador. Expón prerrequisitos externos y condiciones reales de compilación/firma.

## Demostración y participación del equipo

Prepara guion presencial y de video con datos ficticios: donación Android, procesamiento/escritorio, solicitud/evaluación/reserva, traslado con QR/GPS/evidencia, recepción XML, uso/destino, auditoría y panel web. Incluye rechazo institucional, escritura concurrente y caída de una réplica con recuperación. Nunca proyectes archivos privados o tokens completos.

Genera material de apoyo y capturas/grabaciones reales cuando el entorno lo permita. Prepara una alternativa honesta para dependencias externas caídas, mostrando estado y evidencia fechada sin sustituir ejecución por simulación oculta.

Conserva la confirmación de que presentación y video del segundo parcial ya se realizaron. La demostración final ampliada requiere su propia evidencia; no reutilices esa confirmación como prueba de una presentación final inexistente. La publicación/envío de videos requiere autorización vigente y una URL comprobable; no inventes el enlace.

Construye un registro de responsabilidades y contribuciones sustentado en acuerdos, tareas, cambios y evidencias reales. No deduzcas dominio técnico individual exclusivamente de cantidad de commits ni atribuyas trabajo no comprobado. Si falta el reparto nominal, prepara el formato y solicita ese dato concreto sin detener documentación independiente.

Incluye guía de defensa técnica por componente: explicar arquitectura/contratos/migraciones, localizar y corregir un error pequeño en una rama o entorno de prueba, ejecutar pruebas y justificar decisiones. No introduzcas errores deliberados en la instalación entregada.

## Verificación de documentos y cierre

Comprueba enlaces locales y referencias, títulos/índice y páginas, tablas/figuras, consistencia de números/versiones, ausencia de texto fuera de página, integridad Word/PDF y correspondencia con código/artefactos. Inspecciona visualmente el PDF y los diagramas relevantes; un archivo generado sin esa revisión no basta para declarar calidad editorial.

Entrega índice navegable de la versión final, matriz de cumplimiento, informes de pruebas, artefactos y manuales, con brechas explícitas. Actualiza `PROJECT_STATUS.md` y los índices vigentes conservando la historia.

La respuesta final debe indicar qué se entrega, cómo instalar/demostrar, qué verificaciones pasaron y qué aprobación externa o plataforma sigue pendiente. No declares sistema clínicamente certificado, alta disponibilidad multizona, publicación en tienda o aceptación académica si no existe evidencia verificable.
