# Primer intento de los tres recorridos

La corrida agrupada terminó **0/3 en 128,86 s**; `junit.xml` conserva las tres aserciones fallidas. Cada caso alcanzó sus comprobaciones previas de persistencia SQL: corrección de unidad y ubicación con versión, dos derivados en cuarentena y origen retirado, y altas/correcciones de sede y capacidad. Las ocho capturas Qt se inspeccionaron. En la captura de derivados solo se ve el primer elemento del área desplazable; la comprobación SQL anterior al fallo encontró ambos. La denegación de operador del tercer caso estaba después de la aserción fallida y no se ejecutó.

Los tres fallos consultaron `activity_events` en el ámbito del servicio Auditoría. La lectura estática de `apps/services/redhouse/events.py` muestra que `emit` inserta el evento en el ámbito del servicio emisor y lo encola hacia Auditoría; la prueba deberá consultar Inventario o Identidad para comprobar su evento fuente. Esta explicación es un diagnóstico de fuente, no una comprobación de la auditoría de esta corrida. No se repitió el laboratorio. Las huellas de producto y pruebas coinciden antes y después.

Fixture sintético aislado, gateway TLS local, servicios `TESTING`, Qt offscreen y proveedor de clave doble. El proceso de pruebas finalizó y no quedaron procesos asociados a su directorio. No se midió rendimiento ni se acredita operación clínica o periféricos físicos.
