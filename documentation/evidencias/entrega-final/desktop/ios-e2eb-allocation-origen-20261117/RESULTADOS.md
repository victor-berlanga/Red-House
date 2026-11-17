# iOS B: evaluación, reserva, planificación y PREPARED origen

**PASS funcional**, 17 de noviembre de 2026. Cuatro etapas Qt/XML separadas continuaron el mismo órgano, receptor, solicitud, HLA y constancia académica previamente aceptados. No se creó otra unidad ni se cambiaron perfil, caducidad o reglas. Cada etapa conservó su corte durable y terminó con salida0.

- medical2 generó una evaluación y registró un dictamen FAVORABLE único para el recurso exacto.
- medical2 confirmó una sola reserva RESERVED y el órgano pasó a RESERVEDv8. Se conservaron clave/cuerpo/diario; no se usó recuperación ni replay automático.
- coordinator1 creó un traslado PLANNEDv1 sin inventario pendiente, con reserva/recurso exactos y transport1 autorizado. Se usó la ruta existente del mismo par institucional, versión1 y15 minutos, releída y validada; fechas posteriores al momento de planificar y anteriores a la caducidad, sin modificarla.
- operator1 documentó PREPAREDv2 en origen, sin inventario pendiente, con evento SHIPMENT_PREPARED único. No confirmó recolección, entrega ni otra custodia.

Las [cinco capturas reales](capturas) fueron abiertas e inspeccionadas por raíz: candidato, reserva, planificación, detalle y preparación. La captura de preparación tiene un límite visual: el motivo estrecho muestra solo la cola del texto. El motivo completo persistió en el comando; el ajuste visual queda pendiente para el lote final. No se repitió negocio ni se editó producto durante el soporte.

Límite del arnés de reserva: el modal Candidatos quedó abierto después de que Journal y SQL ya confirmaran DONE/COMPLETED/RESERVED. El watchdog180s cerró el modal y el oráculo concluyó con salida0. Lecturas de conciliación durante la espera probaron una reserva exacta, sin shipment todavía y órgano RESERVEDv8. No hubo otro envío ni nueva clave. Se anotó el defecto para una futura mejora del arnés; no se alteró el paquete congelado ni se preparó parche durante esta ejecución.

Cuatro familias propias quedaron revocadas en PostgreSQL y ausentes en Redis, sin errores de cierre; los factores temporales de las etapas que los requerían se retiraron. La familia preexistente del soporte sintético no formó parte del delta de cierre de operator1. Los diarios/claves se copiaron a salidas nuevas, preservando fuentes y registros anteriores.

Conservación tuvo gates separados: revisión de bloqueo y nueva liberación aceptadas por raíz, después soporte térmico XML finito claramente sintético. Los guards exigieron controles sin bloqueo, última lectura sin gap/excursión y vigencia300s; estos runners no produjeron lecturas ni alteraron el intervalo. No se afirma medición física o habilitación clínica real.

[HASHES.json](HASHES.json) fija las huellas de recibos privados, manifiestos y capturas. IDs, claves, rechazos, comandos y sesiones permanecen en .local. Esta evidencia no sustituye las siguientes comprobaciones móviles/custodia ni declara completado por sí solo todo E2E B.
