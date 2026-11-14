# Segundo intento aislado: preparación del 10 % y lectura sostenida

El conjunto sintético se preparó correctamente: 2.000 donantes preliminares, 10.000 recursos RBC (5.000 disponibles y 5.000 en cuarentena) y 100.000 eventos asociados a 10.000 recursos. Se insertó directamente por SQL; no acredita registro por API, revisión clínica ni volumen documental MongoDB. El [informe de preparación](preparacion.json) conserva 942 hashes de fuentes anteriores y posteriores coincidentes, conteos, fases, índices y planes. El ensayo empleó el [comando y huellas previas](../preparacion-10porciento-02/PREPARACION.md).

| Preparación observada | Resultado |
| --- | ---: |
| Inserción y comprobaciones incluidas | 157.918,004 ms |
| Tiempo acumulado de 1.120 guardas | 130.950,617 ms |
| Tamaño PostgreSQL inicial / final | 15.928.667 / 72.387.931 bytes |
| Incremento PostgreSQL | 56.459.264 bytes |
| Directorio lógico inicial / final | 270.013.645 / 394.035.268 bytes |
| Incremento lógico del directorio | 124.021.623 bytes |
| Segmentos WAL inicial / tras recursos / tras eventos | 1 / 2 / 5 de 16.777.216 bytes |

Los tiempos de fase incluyen guardas y otras operaciones, no representan latencia SQL pura. Una única consulta `EXPLAIN ANALYZE` registró 0,191 ms de disponibilidad y 66,616 ms de trazabilidad. No son mediciones sostenidas, p95 ni capacidad de producción.

La lectura sostenida **falló**: la guarda detuvo Locust antes de que iniciara el calentamiento. El código registra que se activó una guarda, pero agrupa excepciones de censo, acceso y límite sin conservar el tipo; por tanto, el motivo exacto no quedó registrado. La última muestra válida observó 3.493.543.936 bytes libres y 394.394.270 bytes lógicos propios; después se observaron aproximadamente 2,246 GiB libres, y tras el cierre `df` volvió a mostrar 3.482.208 KiB. La causa de esa variación no está demostrada. Los límites no se modificaron.

Locust registró seis intentos de login: tres respuestas 200 y tres 503. El log sanitizado de Identidad asigna los tres 503 en `/api/v1/auth/login` a `redis_unavailable`; el log de Redis muestra que su proceso permanecía activo hasta el cierre posterior. Esto no identifica la causa raíz. Hubo tres respuestas HTTP 200 de revocación, pero la verificación conjunta de las seis familias en PostgreSQL y Redis falló; no se acredita revocación efectiva individual. Los errores de login aparecen en el log antes de la salida `KeyboardInterrupt`, pero el arnés no registró una marca temporal de la activación de la guarda que permita ordenar el instante exacto de señal frente a los errores. El enrolamiento y la confirmación MFA de los dos perfiles correspondientes devolvieron 200.

En tres muestras, el máximo RSS sumado fue 1.924.240 KiB entre 35 procesos propios y descendientes; puede contar memoria compartida más de una vez. El máximo de porcentajes CPU sumados reportados por `ps` fue 138,0 %, no una medición instantánea. Estas muestras cubren solo el arranque fallido. No hubo seis inicios efectivos, 30 segundos de calentamiento ni 120 de medición; no hay p95/p99 válidos.

Se conservaron [resumen de Locust](locust-summary.json), [estadísticas finales](locust-final.json), [fallos](locust-failures.csv), [excepciones](locust-exceptions.csv), [serie parcial](locust-history.csv), [configuración esperada](topologia-configurada.json) y [estado sostenido](sostenida.json). Los logs y el diagnóstico completos permanecen en el laboratorio privado `/private/tmp/rh-load-fin88ii_`. Tras detener los procesos propios, la comprobación observó solo los tres PID preexistentes. El primer intento y sus archivos se conservaron por separado.
