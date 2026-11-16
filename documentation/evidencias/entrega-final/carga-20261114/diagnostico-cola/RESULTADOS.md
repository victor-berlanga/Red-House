# Diagnóstico posterior de cola y corrección de conteos

El 14/11/2026 se consultó el PostgreSQL conservado de la carga fallida en transacciones READ ONLY, con APIs y workers detenidos. Se inició y cerró únicamente el proceso propio de PostgreSQL. El primer intento se conectó por error a la base administrativa `postgres` y terminó `UndefinedTable`; se corrigió el DSN a la base `red_house`, sin inicializar ni editar datos de negocio. El arranque del motor puede actualizar archivos internos; solo lectura describe las consultas SQL.

La [instantánea saneada](cola.json) encontró 6993 entregas pendientes de Auditoría hacia MongoDB: 5615 anteriores al inicio de carga transaccional y 1378 posteriores. Otras 565 entregas de Auditoría hacia sí misma son históricas. Donantes conserva 460 hacia Auditoría y 175 hacia Alertas, todas posteriores al inicio del ensayo y sin intentos. Los 175 eventos de negocio y 57 avisos faltantes del resultado original siguen siendo el criterio fallido; estos conteos globales incluyen otras acciones y no se equiparan a ellos.

La cabeza de Auditoría es un evento READ antiguo, con un intento y `mongodb_unavailable`; las otras 6992 entregas Mongo no tienen intentos. Los últimos heartbeats almacenados de Auditoría y Donantes no contienen error. El payload de esa primera fila pudo codificarse y recuperarse con BSON real, sin abrir Mongo ni publicar su contenido. Esto descarta un error de codificación de esa fila, no acredita su entrega ni descarta otros fallos. La causa de la falta de progreso todavía no está demostrada; no se aplicó la propuesta de cambio de cadencia ni se repitió la carga.

Se corrigió separadamente el resumen de Locust: los contadores HTTP se agregan por etiqueta y los de cada método se conservan en `counts_by_method` y `measurement_counts_by_method`. Un marcador DRAIN con el mismo nombre ya no sobrescribe un recorrido TRANSACTION. Tres [pruebas dirigidas](conteos-junit.xml) aprobaron en 1,18 s; la función candidata también se contrastó con la medición conservada: 1291 HTTP y 199 recorridos. Los JSON/CSV del ensayo original permanecen intactos y fallidos. No se atribuye una medición nueva a este arreglo de presentación.

## Continuación: dos entregas baseline reales y parche aplicado

Los [diagnósticos posteriores](baseline-worker/RESULTADOS.md) entregaron una fila de Auditoría→Mongo y una de Donantes→Auditoría, con duración, estado antes/después y cierre propio verificados. También comprobaron que ambas colas habían progresado durante la carga original; la cabeza antigua no prueba bloqueo permanente. El parche acotado de cadencia se aplicó después y pasó 13 pruebas puras. Recuperación real y nueva carga siguen pendientes; las conclusiones previas permanecen como registro cronológico, sin convertir la corrida fallida en aprobada.

## Recuperación parcial y discriminante de conexión

El [drenado acotado](drenado-01/RESULTADOS.md) mantuvo exit 1: SQL alcanzó 765 eventos y 121 avisos exactos, pero quedaron 7469 entregas históricas y ninguna de las 765 proyecciones de negocio había llegado a Mongo. Todos los procesos propios cerraron. El [discriminante posterior de 20 transacciones READ ONLY](pool-readonly/RESULTADOS.md) confirmó adquisición caliente de 17,43 ms con conexión nueva frente a 0,53 ms reutilizando un pool de una conexión. Son resultados separados; no convierten la carga original en aprobada ni acreditan todavía una nueva configuración de worker.

## Reanudación del 16 de noviembre: pool exclusivo del worker

El [pool aplicado y su recuperación](worker-pool-20261116/RESULTADOS.md) pasaron 19 pruebas dirigidas; la recuperación conservó exit 1 con 5742 entregas históricas pendientes. Auditoría entregó 1900 filas en 125,098 s hasta el cierre normal; mejor ritmo observado, pero Mongo de negocio continúa pendiente. SQL mantiene 765 eventos y 121 avisos exactos. Todos los procesos propios cerraron, sin nueva carga ni publicación.
