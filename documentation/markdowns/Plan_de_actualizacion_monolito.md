# Actualización del monolito previa a microservicios

> **Fecha:** 13 de septiembre de 2026.  
> **Estado:** AM-01 a AM-14 implementados y verificados dentro del alcance académico confirmado.  
> **Origen:** retroalimentación docente proporcionada por el usuario y autorización para atenderla.  
> **Propósito:** convertir la base de inventario en una demostración regional integral y entregar un reporte técnico autosuficiente.

## 1. Cambio de secuencia

El cierre histórico del primer parcial corresponde al MVP de administración e inventario. La retroalimentación exige un incremento adicional dentro del monolito antes de extraer microservicios. El cierre anterior no demuestra la aceptación de este nuevo alcance.

La secuencia vigente para el siguiente trabajo es: definir el alcance demostrativo, ampliar el monolito, comprobar el flujo regional, consolidar el Reporte Técnico del Primer Avance y posteriormente retomar los componentes distribuidos. Los paquetes semestrales existentes conservan sus identificadores; la dependencia anterior que posponía estos procesos hasta disponer de microservicios queda sustituida para este incremento.

Se consultaron `../arquitectura.txt`, `../entregas.txt` y `../proyecto.txt`, referencias externas al repositorio. Confirman los cuatro productos y la calendarización de MongoDB, Redis y Docker. La retroalimentación es la instrucción específica más reciente sobre la ampliación previa del monolito. El plazo relativo de dos semanas no se convierte en una fecha de entrega inventada: falta confirmar su fecha de inicio.

## 2. Punto de partida comprobado

- Monolito Flask/Jinja2 con capas de presentación, negocio, acceso a datos y configuración.
- Esquema inicial de 23 tablas PostgreSQL, con inventario, movimientos, auditoría y autenticación local.
- Tres perfiles habilitados: Administrador, Operador y Auditor.
- Siete vistas de negocio futuras; recuperación de acceso sin implementación.
- Documentos especializados, normalización 0FN–4FN y evidencia histórica de pruebas.
- Existe `Reporte_Tecnico_Integral_Red_House.docx`: contiene portada, integrantes, capítulos y 14 recursos de imagen. Su existencia no demuestra que satisfaga la nueva rúbrica ni que documente un flujo regional ejecutable. Se conserva como antecedente para elaborar la entrega corregida.
- Código y documentación ya están versionados en Git; la afirmación del estado anterior sobre tener únicamente el README versionado quedó desactualizada.

## 3. Paquetes y criterios de aceptación

| ID | Cambio solicitado | Criterio de aceptación y evidencia necesaria |
| --- | --- | --- |
| AM-01 | Red institucional ampliada | Hospitales, bancos, centros de trasplantes, sedes, ubicación, contactos, capacidades, horarios, participación y estado administrables; disponibilidad regional consultable. Pruebas de validación y ámbito. |
| AM-02 | Donantes y evaluación humana | Expediente ficticio institucional, identificación, ABO/Rh, tipo de donación, antecedentes, consentimiento, restricciones, fechas y estado. La elegibilidad registrada identifica al responsable autorizado; el sistema no la deduce. Pruebas de acceso y registro de decisiones. |
| AM-03 | Donación, recolección y procesamiento | Cada unidad resultante puede trazarse a su donación, donante y eventos de recolección/procesamiento. Estados y referencias persistidos, sin inventar vidas útiles clínicas. Evidencia de navegación e integridad. |
| AM-04 | Receptores y solicitudes | Expediente independiente y restringido; solicitud con receptor, institución, componente, cantidad, urgencia registrada, fecha, responsable y justificación. Auditor y coordinador reciben únicamente los datos necesarios para sus funciones. |
| AM-05 | Inventario regional | Disponibilidad y próximas caducidades por ABO/Rh e institución, excluyendo caducados y recursos comprometidos. La demanda procede de solicitudes reales del ejercicio. No se presenta una previsión de demanda como implementada sin algoritmo y medición. |
| AM-06 | Compatibilidad demostrativa | Entradas, componente cubierto, fuente, versión, candidatos, limitaciones y necesidad de revisión clínica visibles. Casos positivos, negativos y componentes no soportados comprobados. Alcance confirmado: concentrados eritrocitarios. |
| AM-07 | Priorización explicable | Urgencia registrada, espera, distancia, estimación de traslado y viabilidad temporal mostradas con procedencia. Regla demostrativa documentada y versionada; sin decisión clínica automática. No inventar coordenadas ni tiempos de viaje reales. |
| AM-08 | Revisión, reserva y asignación | Decisión humana con motivo y responsable. Una misma unidad no puede quedar comprometida en dos operaciones concurrentes. Pruebas de competencia entre transacciones, versiones obsoletas y rollback de operación/auditoría. |
| AM-09 | Traslado y custodia | Origen, destino, recurso, responsable, vehículo, salida, ETA, estados e incidencias. Eventos con actor, fecha, observación, ubicación pertinente y evidencia. Historial protegido y transiciones controladas. |
| AM-10 | Recepción y cierre | Recepción registrada por un perfil autorizado del destino; comprobación de recursos y cierre coherente de solicitud, asignación y traslado. Rechazos e incidencias conservan trazabilidad. |
| AM-11 | Panel regional | Disponibilidad, próximas caducidades, solicitudes activas/urgentes, reservas, traslados, tiempo de respuesta e instituciones; desgloses, tendencias y alertas obtenidos de datos persistidos. Lista regional válida como alternativa al mapa. |
| AM-12 | Auditoría transversal | Acceso, consulta sensible, altas, cambios, autorizaciones, reservas, asignaciones, traslado y recepción rastreables. El Auditor no modifica evidencia ni necesita acceder al expediente clínico completo. |
| AM-13 | Migración y regresión | Migración incremental y transaccional sobre una copia de la base anterior; conserva cuentas, contraseñas, unidades e historial. No reinicializar mediante `schema.sql`. Instalación nueva y actualización verificadas por separado. |
| AM-14 | Reporte Técnico del Primer Avance | Un documento autosuficiente con los 37 apartados de la retroalimentación, diagramas renderizados y legibles, evidencia actual, resultados de pruebas y límites explícitos. Word como entregable editable; fuentes reproducibles conservadas. |

AM-01 a AM-14 cuentan con implementación y evidencia para el alcance delimitado. La suite final aprobó 89 pruebas en 92.68 s, sin fallos, errores ni omisiones; incluye migración, permisos, concurrencia y recorrido completo en Chrome. Resultados y capturas: `documentation/evidence/ampliacion-monolito/`. El reporte incorpora la matriz de trazabilidad y el diccionario físico. La aceptación docente permanece independiente de esta comprobación técnica.

AM-09 registra evidencia mediante referencias documentales; no carga archivos binarios. AM-06 cubre solo eritrocitos y AM-07 utiliza criterios demostrativos explicables. Estas limitaciones se conservan expresamente en el reporte.

## 4. Decisiones confirmadas

1. **Órganos — confirmado por el usuario el 13 de septiembre:** flujo sanguíneo completo y sección de órganos separada, documentada y señalada como pendiente. No se implementará un motor HLA ni un flujo de asignación de órganos en este incremento.
2. **Componentes del motor — confirmado por el usuario el 13 de septiembre:** concentrados eritrocitarios con criterios demostrativos y autorización humana. Plasma y plaquetas no utilizan esa tabla.

Como preparación se localizó la referencia primaria de Australian Red Cross Lifeblood sobre [compatibilidad por componente](https://www.lifeblood.com.au/health-professionals/products/component-compatibility). Su uso documental no constituye validación clínica o normativa mexicana. El alcance demostrativo fue confirmado y se implementó como RBC-DEMO-1.0; no acredita validación clínica.

## 5. Estructura del reporte consolidado

El reporte incluye portada e integrantes tomados del documento existente, control de versiones, introducción, contexto empresarial, problema, organizaciones, proceso AS-IS de referencia documental, problemas detectados, TO-BE, objetivos, alcance, exclusiones, actores, permisos, RF, RNF, historias, criterios de aceptación, casos de uso, reglas, trazabilidad, arquitectura, diagramas, PostgreSQL, MongoDB, Redis, archivos, seguridad, auditoría, interfaces, evidencias, plan y resultados de pruebas, riesgos, plan de trabajo, conclusiones y referencias.

Los diseños futuros de MongoDB, Redis y almacenamiento deberán identificarse con su nivel de detalle y fase de implementación. Describirlos en el reporte no declara que estén instalados. El proceso AS-IS tampoco debe presentarse como observado en hospitales reales: el análisis existente es documental y académico.

Se incorporaron diagramas de contexto, contenedores, componentes, despliegue, red, secuencia, comunicación entre aplicaciones, autenticación y almacenamiento. La ejecución local actual y la arquitectura distribuida futura están diferenciadas en los propios diagramas. Las referencias a los documentos especializados complementarán el contenido principal, sin obligar al evaluador a abrirlos para comprender la entrega.

## 6. Estrategia de comprobación

- Reutilizar la suite actual y añadir pruebas proporcionales a los nuevos procesos.
- Probar el recorrido desde una donación en una institución hasta la recepción y cierre de una solicitud en otra.
- Probar permisos positivos y negativos por institución, región, expediente y tarea logística asignada.
- Comprobar doble reserva concurrente, estados obsoletos, cancelaciones, unidades caducadas y fallos de auditoría.
- Verificar migración desde el esquema anterior en una base exclusiva de pruebas antes de actualizar la instalación existente.
- Capturar evidencia de navegador del flujo nuevo y de los perfiles, incluidos formularios y tablas en pantalla pequeña.
- Conservar los resultados históricos y nuevos por separado. No reutilizar las 65 pruebas antiguas como evidencia del incremento nuevo.

## 7. Resultado del incremento

El monolito ya ejecuta el recorrido regional y la base habitual fue actualizada mediante migración incremental después de probar una copia restaurada. Se conservaron cuatro cuentas, sus contraseñas, 36 unidades y todo el historial anterior. Se habilitan seis perfiles; el Administrador puede crear las cuentas nuevas siguiendo `Guia_del_flujo_regional.md`.

El Reporte Técnico del Primer Avance se entrega en Word y PDF, con 37 apartados, doce diagramas renderizados, 56 tablas, 19 imágenes y resultados actuales. Las fuentes y generadores permanecen en el repositorio; once documentos especializados conservan el contenido anterior con una nota de vigencia. Los diseños distribuidos se identifican como futuros y órganos/HLA conserva su sección pendiente. No se declara validación clínica experta ni aceptación docente.
