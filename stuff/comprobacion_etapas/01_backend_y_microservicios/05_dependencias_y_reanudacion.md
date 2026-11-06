# Dependencias y reanudación

## 1. Estado desde el que continuar

La etapa 01 sigue **NO APTA PARA CONTINUAR**. Se archivó una auditoría, no una implementación correctiva. El usuario autorizó guardar toda la información; este expediente no registra ejecución de las acciones propuestas.

El árbol de trabajo ya contenía implementación sin commit antes de la auditoría. No restaurarlo, limpiarlo, resetearlo ni descartar archivos para volver al commit base. Las fuentes exactas están identificadas por el manifiesto; los cambios locales son parte del trabajo que debe conservarse.

Antes de retomar, leer en este orden: [README](README.md), [matrices](02_matrices_requisitos.md), [hallazgos](03_hallazgos_y_cierre.md), [reproducción](04_evidencias_y_reproduccion.md), requisitos originales completos y estado actual del proyecto. Usar CodeGraph para volver a ubicar el código y comprobar qué cambió desde el corte.

## 2. Pendientes propios de etapa 01

| Pendiente | Responsable técnico | Evidencia necesaria para cerrar |
| --- | --- | --- |
| F1, destinos y correcciones | Inventario | Positivos/negativos, JSON/XML, calidad, tipo/recepción, versiones e historia |
| F2, evaluación obsoleta | Compatibilidad/Inventario | Fingerprint/versiones vinculados; cambio autorizado invalida dictamen antiguo |
| F3, custodia obligatoria | Transporte/Custodia | Datos requeridos por entrega; rechazo sin avance, cadena y recuperación |
| F4/F5/F6, rastreo | Transporte/Identidad | Entrada única, permiso vigente durante entrega y recuperación histórica paginada |
| F7, auditoría e inmutabilidad | Todos los productores/Auditoría/Compatibilidad | Eventos clasificados visibles; cambios auditados; SQL del rol runtime no reescribe resultados |
| F8, roles/permisos | Identidad | Comando institucional, límites, versión, auditoría e invalidación de permisos |
| F9/F11, reportes/consultas | Propietarios/Transporte | Parámetros completos, filtros previos al límite y todos los reportes comprobados |
| F10, réplicas | Transporte/Monitoreo/integración | Una réplica y caída total API, socket abierto, degradación y recuperación reales |
| BE-21, pronóstico positivo | Inventario/Transporte | Historia suficiente sintética, oráculo independiente, calidad/ventana/límites y tiempo |
| Documentación y aceptación final de 01 | Integración | Matrices, contratos, fuentes finales, evidencias y PROJECT_STATUS coherentes |

Estos pendientes no se trasladan a una etapa posterior por conveniencia. El detalle clínico de HLA y el despliegue de gateway no excusan F2 ni F10.

## 3. Dependencias explícitas de otras etapas

| Etapa | Qué sigue pendiente | Qué no debe darse por probado |
| --- | --- | --- |
| **02 Reglas y algoritmos** | Evaluación HLA/inmunológica detallada, ampliación de priorización/algoritmos, validación independiente y límites; separar posición observada, ruta y ETA | Captura/completitud de laboratorio no equivalen a trasplantabilidad; ABO coincidente no aprueba un órgano; ranking logístico no es asignación oficial |
| **03 Web** | Interfaz MFA/reauth y políticas operativas, mapa vigente de Nuevo León, WSS y estados/alternativa accesible | Autonomía académica del backend no certifica recorridos de navegador ni todas las políticas juntas |
| **04 Android** | Cliente JSON, permisos y captura visible del teléfono, geolocalización autorizada, almacenamiento/sincronización y conexión al hardware según selección | Contratos y simulador no equivalen a aplicación Android ni GPS físico |
| **05 Escritorio** | Cliente XML/XSD y mapa de coordinación; proceso interno separado y permisos | El mapa embebido no autoriza consumo JSON de microservicios para eludir XML; no sustituir escritorio por portal |
| **06 Infraestructura** | Despliegue nuevo, gateway upgrade WSS/TLS/timeouts/drenaje, redes/secretos, operación de réplicas, RTO/RPO y observabilidad | Dos listeners locales no acreditan gateway/GCP actual ni migración automática de sockets |
| **07 Integración y pruebas** | Tres flujos integrales entre componentes, carga/estrés/concurrencia sostenida, recuperación y medición hasta pantalla | 24 puntos y ACK local no son capacidad sostenida, latencia de mapa ni SLA |
| **08 Cierre** | Reauditar todos los pendientes obligatorios, manuales y evidencia aplicable de operación | No cerrar entrega con dependencias obligatorias aún pendientes ni con evidencias de fuentes anteriores |

Para cartografía, verificar proveedor/SDK, licencia, atribución, configuración, cobertura estatal/local y fecha de consulta/actualización al implementar. Si no hay fecha exacta publicada, declararlo. Separar ruta planificada, trayecto observado y ETA; no inventar tráfico o movimiento entre puntos. La caída cartográfica debe mantener una alternativa accesible, sin afirmar que el mapa funciona.

## 4. Dependencias externas

| Dependencia | Aceptación pendiente | Límite del resultado actual |
| --- | --- | --- |
| GPS físico | Elegir modelo/protocolo/conector; decodificar mediciones reales; precisión, señal, conectividad, energía, frecuencia, instalación y revocación del equipo | Se probó simulador y adaptador futuro; no hardware |
| Reglas y perfiles sanitarios | Fuentes, versiones, revisión y aprobación por expertos autorizados; conservación, compatibilidad, prioridad y asignación según ámbito | Perfiles sintéticos y revisión humana en pruebas no son aprobación clínica externa |
| Autorización oficial de órganos/acreditaciones | Contraparte/procedimiento real, emisor y vigencia verificables | Registrar constancia o documento no certifica autorización sanitaria ni integración oficial |
| GCS | Bucket/ADC de prueba autorizados para nuevos documentos/reportes y evidencia real de privacidad/recuperación | Doble SDK no prueba nube; caso real omitido |
| ClamAV | Motor real con firmas y análisis/errores/recuperación de generación exacta | Receptor ClamD local prueba protocolo, no eficacia antivirus |
| SMTP/push | Configurar y probar proveedores autorizados, errores y reintentos | Aceptación por receptor local no equivale a lectura humana |
| Retención y eliminación | Política institucional por tipo/finalidad, bloqueo, conservación GPS/archivos y bajas lógicas | No inventar plazos normativos ni tratar TTL Redis como retención durable |
| Contraparte hospitalaria | Mapeos y conciliación reales; decidir HL7/FHIR solo si existe necesidad definida | Adaptador técnico no implica integración con un hospital real |

## 5. Secuencia de trabajo posterior

1. Registrar estado de fuentes y cambios locales antes de intervenir; conservar base compartida, UUID, datos e historia.
2. Corregir los grupos en el orden de [hallazgos](03_hallazgos_y_cierre.md), dentro de sus propietarios. No imponer 24 procesos ni duplicar reglas.
3. Por cada grupo, añadir después de autorización de implementación los casos que faltan y ejecutarlos en entorno aislado. Distinguir los nuevos casos de los ya archivados.
4. Si cambian esquema o permisos, preparar migración aditiva, probar instalación y actualización repetida con conservación de datos/relaciones/historia. No usar la base habitual para experimentar.
5. Mantener contratos JSON/XML/XSD/OpenAPI y compatibilidad v1 o transición explícita; registrar semántica 201/202, pendientes, 409/412, correlación, idempotencia y consulta de resultados.
6. Ejecutar las regresiones afectadas y completar los criterios transversales, especialmente F10 y las políticas operativas. Pruebas existentes verdes no bastan para cerrar una variante que no comprueban.
7. Identificar las fuentes finales mediante commit más manifiesto de cambios locales; conservar JUnit, comandos, entorno, fechas, métricas y omisiones. No sobrescribir evidencias anteriores.
8. Actualizar PROJECT_STATUS y documentación de implementación con criterios cumplidos y pendientes reales, sin afirmar aprobación de clientes, hardware o clínica.
9. Encargar nueva comprobación independiente conforme al protocolo. El auditor revisa y ejecuta pruebas existentes, sin corregir durante la auditoría.

## 6. Encargos preparados para usar después

Los siguientes textos son ayudas para una futura solicitud. Su presencia en este archivo **no ordena ejecutarlos durante el archivado**.

### Implementación correctiva

```text
Lee AGENTS.md, PROJECT_STATUS.md y el expediente
stuff/comprobacion_etapas/01_backend_y_microservicios/README.md,
siguiendo los documentos 01 a 05. Lee completos los prompts 00, 01 y 09
de stuff/prompts/entrega-final. Consulta CodeGraph antes de localizar código.

Implementa y prueba las correcciones F1 a F11 y completa la evidencia
positiva pendiente de BE-21 y los criterios transversales de etapa 01.
Sigue el orden de 03_hallazgos_y_cierre.md. No te limites a un plan.

Conserva los cambios locales existentes, la base compartida, datos, UUID,
historial y propietarios. No crees 24 procesos por cuota ni dupliques
reservas, reglas clínicas, objetos o autoridades. Conserva v1 compatible
o documenta y prueba una transición versionada explícita.

Prueba JSON/XML/XSD, persistencia, permisos, eventos, concurrencia,
escrituras inciertas y recuperación. Usa únicamente datos ficticios y
servicios temporales propios para las pruebas. No despliegues ni uses
producción como ensayo. No inventes aprobaciones clínicas ni equipos GPS.

Separa HLA detallado de etapa 02, clientes/mapas 03–05, gateway/GCP 06,
carga/integración 07 y dependencias externas. No uses esas dependencias
para aplazar defectos actuales como F2 o F10.

Conserva este expediente histórico. Genera evidencia nueva identificada
por fuentes/fecha, actualiza contratos/manuales y PROJECT_STATUS.md con
criterios comprobados y pendientes reales. No declares la etapa aprobada
sin una comprobación aplicable a las fuentes finales.
```

### Nueva auditoría

```text
Audita de nuevo la etapa 01 contra el prompt completo
stuff/prompts/entrega-final/01_backend_y_microservicios.md y el complemento 09.
Aplica el Protocolo de comprobación de GUIA_EJECUCION_Y_COMPROBACION.md.
Lee AGENTS.md, PROJECT_STATUS.md, contexto 00 y el expediente histórico
stuff/comprobacion_etapas/01_backend_y_microservicios/README.md.

Revisa sin implementar correcciones. Comprueba cada F1–F11 y el pendiente
de evidencia positiva BE-21, además de BE-01 a BE-24 y TRACK-01 a TRACK-10.
No reduzcas el alcance a los defectos conocidos. Verifica que las pruebas
nuevas realmente cubren los escenarios de cierre y no solo la implementación.

Identifica commit/cambios locales mediante manifiesto, fecha, entorno,
casos ejecutados, omisiones y evidencia histórica aplicable. Ejecuta solo
pruebas existentes con datos ficticios y servicios temporales propios.
No edites código, contratos, documentación ni PROJECT_STATUS durante
la comprobación. Entrega el nuevo informe en chat y termina con el
veredicto exacto del protocolo. El archivado posterior será otro encargo.
```

## 7. Regla de decisión

**APTA PARA CONTINUAR** exige todos los criterios obligatorios con evidencia aplicable y sin defectos bloqueantes. **CONTINUACIÓN PARCIAL POR DEPENDENCIA DECLARADA** solo procede si lo pendiente es externo o requiere una etapa posterior explícita; no permite aplazar defectos del componente actual. La entrega completa tampoco equivale a certificación clínica.

En el corte de este expediente siguen abiertos defectos y funciones actuales, por lo que corresponde:

**NO APTA PARA CONTINUAR**
