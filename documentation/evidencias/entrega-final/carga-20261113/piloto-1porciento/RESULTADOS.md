# Piloto sintético de volumen, 13/11/2026

Se ejecutó una sola preparación aislada del 1 % con semilla `20261113` e instante lógico `2026-11-13T12:00:00Z`. Se crearon 200 donantes preliminares, 1.000 recursos RBC (500 disponibles y 500 en cuarentena) y 10.000 eventos sintéticos de trazabilidad vinculados a los 1.000 recursos. Las filas se insertaron directamente por SQL: no acreditan registro por API, decisiones clínicas ni validación humana. MongoDB participó en la infraestructura, sin volumen documental sintético en este ensayo.

Comando desde la raíz del repositorio:

```sh
PYTHONPATH=.:apps/services apps/services/.venv/bin/python apps/services/scripts/prepare_load.py --seed 20261113 --mongod "$PWD/.local/tools/mongodb-8.0.17/bin/mongod"
```

Se comprobó que existían dos procesos PostgreSQL y uno MongoDB antes del ensayo y que permanecían exactamente esos tres tras el cierre de los motores propios. El proceso de preparación terminó con código 0; el informe original sin credenciales es [informe.json](informe.json). Las 12 pruebas unitarias ligeras posteriores se registran en [unitarias.xml](unitarias.xml). Las [huellas](fuentes-despues.sha256) se tomaron inmediatamente después del piloto, antes de esas pruebas, y los archivos de preparación y pruebas conservaron la misma huella después de ellas. No hay una huella anterior al piloto que permita demostrar retrospectivamente igualdad al inicio.

| Medida observada | Resultado |
| --- | ---: |
| Tiempo de inserción, incluyendo comprobaciones de espacio | 25.660,75 ms |
| Tamaño PostgreSQL tras inicialización / después de insertar | 15.928.667 / 21.851.483 bytes |
| Incremento PostgreSQL | 5.922.816 bytes |
| Tamaño lógico del directorio privado tras inicialización / después | 270.011.706 / 292.806.502 bytes |
| Incremento lógico del directorio | 22.794.796 bytes |
| Espacio libre al terminar la preparación | 5.058.895.872 bytes |

Una ejecución `EXPLAIN ANALYZE` informó 0,237 ms para disponibilidad y 12,43 ms para trazabilidad; son observaciones individuales del laboratorio, no pruebas sostenidas, p95, capacidad de servicio ni rendimiento GCP. El informe conserva ambos planes y seis índices observados. El tamaño del directorio suma longitudes lógicas de archivos; no equivale necesariamente a bloques físicos ocupados.

Después del cierre, `pg_wal` contenía dos segmentos de 16.777.216 bytes cada uno. La diferencia entre el incremento del directorio y el de la base fue 16.871.980 bytes, cercana al tamaño de un segmento; el número y tamaño inicial de archivos WAL no se registraron, así que no puede afirmarse cuánto de esa diferencia corresponde a un segmento añadido. Los valores `Plan Rows: 50` del plan de trazabilidad son estimaciones del optimizador, no el límite de la consulta; el código conservado después del piloto usa `LIMIT 2000`.

Una extrapolación estrictamente lineal del incremento lógico del directorio al 100 % daría unos 2.279.479.600 bytes adicionales, más el coste fijo inicial: excedería el límite de 1,5 GiB propios y reduciría el margen libre por debajo de 3 GiB. Es una cota de planificación conservadora que multiplica también posibles costes discretos de WAL y otros archivos; no es una predicción validada ni un resultado de la escala completa. No se ejecutó esa escala, carga sostenida, estrés ni medición MongoDB.
