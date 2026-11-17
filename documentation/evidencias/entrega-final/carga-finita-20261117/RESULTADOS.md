# Cobertura finita de tres perfiles — 17/11/2026

Los nueve casos académicos de MEDICAL/XML, COORDINATOR/XML y TRANSPORT/JSON completaron sus operaciones por evidencia compuesta. La ventana de negocio midió exclusivamente seis casos nuevos: dos por perfil. Su oráculo de persistencia aprobó, pero **esa ejecución conserva estado FAILED por un fallo al cerrar una sesión técnica**. Una comprobación posterior de solo lectura aprobó el cierre corregido; no se repitieron las operaciones de negocio.

## Resultados de negocio y medición

| Control | Resultado observado |
| --- | --- |
| Identidades conectadas | 3, una por perfil |
| Ventana medida | 120 segundos, después de 30 segundos de calentamiento |
| Casos medidos | 6 completados; 2 por perfil |
| HTTP durante medición | 49 peticiones; 0 errores |
| Mayor p95 de lectura | 630 ms; umbral previo estrictamente menor de 2.000 ms |
| Composición de casos de negocio | 9: tres preflights más seis casos medidos |
| Intenciones conciliadas | 27 de 27 confirmadas; ninguna sin resultado |
| Replays | 3 confirmados sin duplicar operaciones |
| Oráculo | Persistencia verificada; 156 eventos fuente y 30 destinatarios esperados; sin outbox pendiente |
| Cierre original de la última ventana | Runner 0; dos revocaciones HTTP, un error CLEANUP y verificador de familias false |
| Procesos y archivos | Procesos propios cerrados; fuentes, configuración e historia ajena conservadas; bloqueo retirado |

Es una muestra finita pequeña para cubrir responsabilidades y contratos. No estima capacidad máxima, no demuestra alta disponibilidad, no incluye GPS bajo carga y no reemplaza la serie anterior que incumplió su objetivo con 24 usuarios. Los tiempos y errores de intentos anteriores no se suman a esta ventana.

## Latencia de recorridos medidos

| Perfil | Muestras | Media | p95 / p99 |
| --- | ---: | ---: | ---: |
| Transporte | 2 | 2.061,51 ms | 2.100 / 2.100 ms |
| Coordinación | 2 | 1.907,96 ms | 2.400 / 2.400 ms |
| Médico | 2 | 40.970,74 ms | 56.000 / 56.000 ms |

Estos tiempos incluyen esperas de MFA, especialmente en el recorrido médico; no son solo tiempo de backend. Cada perfil completó dos casos en una ventana de 120,0087 s. La muestra no permite extrapolar percentiles ni capacidad; no se definió un umbral de latencia de transacción para este ensayo finito. El resumen conserva las estadísticas HTTP por operación, con medias, p95 y p99.

## Intentos conservados y correcciones

1. Un primer arranque se detuvo antes de sembrar por configuración local no académica. Las copias privadas de API/worker se corrigieron a ACADEMIC con TESTING=False, conservando MFA y reautenticación.
2. El primer recorrido de los nueve casos completó coordinación y transporte, pero el dictamen médico devolvió 503. La [consulta N+1 de Inventario](../inventario-consulta-20261117/RESULTADOS.md) fue corregida y comparada con SQL real equivalente.
3. La primera continuación abrió por error la base administrativa de mantenimiento. Se corrigió únicamente la selección de base del arnés; todas las guardas READ ONLY de los nueve casos aprobaron antes de otro recorrido.
4. La siguiente continuación guardó el dictamen con su evaluación y clave originales, pero rechazó el desafío MFA de reserva: el arnés exigía versión 0.4.4 global y el propietario Inventario declara 0.4.1. Se corrigió la comparación contra OpenAPI del propietario; no se relajó seguridad del producto. Se conciliaron y revocaron las seis familias propias de los dos intentos de negocio fallidos, con logout del propietario, rechazo 401 posterior, SQL/Redis y seis eventos fuente LOGOUT. Cada lote conservó las otras 42 familias de su snapshot y no creó nuevas.
5. El último recorrido recuperó la misma reserva con su clave y cuerpo originales, reutilizando la evaluación y la respuesta real 201 del dictamen. Los seis casos restantes y el oráculo aprobaron. El cierre conserva un error CLEANUP; su tipo concreto no quedó registrado en la estadística original. Se corrigió el riesgo de cancelación del cierre desde el greenlet del usuario y se comprobó por separado, como se describe abajo. No se atribuye una causa exacta no observada ni se cambia el resultado original a aprobado.

Las regresiones del parser y compensación inicial aprobaron 76 pruebas puras antes del último recorrido. Esa compensación inicial todavía no resolvió el cierre real completo. Los intentos, fuentes congeladas y recibos privados permanecen separados; [resumen público](resumen.json) conserva sus resultados sin credenciales, cuerpos ni diarios privados.

## Identificación y límites de reproducción

Última ventana: `finite-continuation-20261117T183325Z-38890985`, fixture local conservado `rh-load-c92ed10k`, esquema 21, pool de dos conexiones por proceso y workers separados. Candidato Inventario SHA-256 `6714dd289d983f7c4060c33d6abfc40523277f14629625d24786acd048eeafa6`. El arnés original y sus adaptaciones específicas se conservan en `.local/artifacts/inventory-query-20261117/continuation/`; el fixture no debe volver a sembrarse ni ejecutarse desde el primer caso después de consumirlos.

La familia restante del último intento se cerró después mediante logout del propietario: 200, mismo JWT rechazado con 401, SQL revocada, Redis ausente y evento fuente LOGOUT. Las otras 47 familias permanecieron iguales, incluidas las dos que este run ya había cerrado; no se crearon nuevas. PostgreSQL/Redis propios cerraron con salida 0. Esto no reescribe la estadística original FAILED.

## Cierre corregido: prueba real separada

El cierre de red ahora se ejecuta en un greenlet propio, independiente del usuario que Locust detiene. `test_stop` espera esos cierres con un límite de 30 segundos y conserva códigos de fallo sin secretos. Sesenta y siete pruebas puras aprobaron después de archivar y retirar los acoples privados de continuación, incluida la cancelación del actor mientras su cierre continúa. El código entregable conserva únicamente el escenario genérico y sus regresiones.

El ensayo `finite-teardown-readonly-20261117T184706Z-cf3ab78f` reutilizó autenticación y ciclo de vida de `FiniteRoleUser` con tres perfiles y ocho segundos de observación. Una guarda rechazaba escrituras de negocio; solo permitió GET y las operaciones de autenticación/renovación/revocación necesarias. El ledger de negocio permaneció idéntico.

Runner y wrapper terminaron con salida 0: tres inicios de sesión, tres revocaciones, cero errores, tres greenlets de cierre terminados y ninguna entrada pendiente. SQL/Redis confirmaron las tres familias cerradas. Fuentes, topología e historia ajena permanecieron iguales; todos los procesos propios cerraron y se retiró el bloqueo.

La aceptación es **compuesta**: operaciones y persistencia del recorrido original, conciliación de su sesión restante y cierre real corregido en una prueba separada. No transforma el raw FAILED en un PASS ni atribuye seis operaciones nuevas al ensayo de ocho segundos. Los demás escenarios de rendimiento, GPS y etapa 07 conservan su estado. Publicación GCP pendiente en este corte.
