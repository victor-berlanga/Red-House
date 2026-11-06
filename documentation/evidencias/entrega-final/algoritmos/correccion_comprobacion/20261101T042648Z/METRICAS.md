# Mediciones algorítmicas del incremento

Cinco repeticiones por combinación, con tracemalloc activo. Host compartido; no carga sostenida ni SLA. p95 es rango más cercano de cinco muestras (máximo); RSS pertenece al proceso completo. Las muestras brutas permanecen en [benchmark-final.json](benchmark-final.json).

| Algoritmo | Tamaño | Forma | Mediana ms | p95 ms | Pico Python máximo bytes |
|---|---:|---|---:|---:|---:|
| CONSISTENCY-OWNER-2.0 | 10 | authoritative snapshot facts | 0.806 | 1.978 | 4552 |
| EXPLAIN-PROFILE-2.0-REPLAY | 10 | immutable snapshot | 3.390 | 60.962 | 58506 |
| CONSISTENCY-OWNER-2.0 | 100 | authoritative snapshot facts | 5.226 | 7.591 | 41744 |
| EXPLAIN-PROFILE-2.0-REPLAY | 100 | immutable snapshot | 21.125 | 28.470 | 28440 |
| CONSISTENCY-OWNER-2.0 | 1000 | authoritative snapshot facts | 57.583 | 83.666 | 414888 |
| EXPLAIN-PROFILE-2.0-REPLAY | 1000 | immutable snapshot | 292.172 | 307.852 | 335472 |
| DEMAND-OWNER-SES-2.0 | 10 | UTC daily windows | 5.755 | 10.340 | 9502 |
| DEMAND-OWNER-SES-2.0 | 100 | UTC daily windows | 21.231 | 24.720 | 15272 |
| DEMAND-OWNER-SES-2.0 | 365 | UTC daily windows | 63.234 | 76.394 | 31584 |
| EXPLAIN-ACADEMIC-1.0 | 10 | sparse/list | 14.359 | 16.985 | 23423 |
| LOGISTICS-SIM-2.0 | 10 | sparse/list | 24.215 | 32.757 | 27353 |
| DEMAND-SES-1.0 | 10 | sparse/list | 3.898 | 6.049 | 7742 |
| CONSISTENCY-1.0 | 10 | sparse/list | 8.219 | 9.485 | 13414 |
| ROUTE-DIJKSTRA-1.0 | 10 | sparse/list | 10.417 | 16.408 | 12113 |
| COVERAGE-HK-1.0 | 10 | sparse | 0.809 | 1.749 | 2744 |
| EXPLAIN-ACADEMIC-1.0 | 100 | sparse/list | 119.504 | 154.523 | 235059 |
| LOGISTICS-SIM-2.0 | 100 | sparse/list | 242.869 | 285.161 | 260918 |
| DEMAND-SES-1.0 | 100 | sparse/list | 6.146 | 8.563 | 9278 |
| CONSISTENCY-1.0 | 100 | sparse/list | 63.923 | 69.642 | 108062 |
| ROUTE-DIJKSTRA-1.0 | 100 | sparse/list | 78.798 | 90.479 | 85446 |
| COVERAGE-HK-1.0 | 100 | sparse | 6.365 | 7.267 | 32488 |
| EXPLAIN-ACADEMIC-1.0 | 1000 | sparse/list | 1053.148 | 1335.671 | 2186156 |
| LOGISTICS-SIM-2.0 | 1000 | sparse/list | 2387.026 | 2512.781 | 2573138 |
| DEMAND-SES-1.0 | 1000 | sparse/list | 48.265 | 56.352 | 43066 |
| CONSISTENCY-1.0 | 1000 | sparse/list | 530.916 | 559.576 | 841322 |
| ROUTE-DIJKSTRA-1.0 | 1000 | sparse/list | 785.133 | 899.252 | 807027 |
| COVERAGE-HK-1.0 | 500 | sparse | 24.495 | 28.910 | 136072 |
| ROUTE-DIJKSTRA-1.0 | 90 | dense | 44.419 | 51.171 | 73914 |
| ROUTE-DIJKSTRA-1.0 | 2450 | dense | 1319.611 | 1442.440 | 1350866 |
| ROUTE-DIJKSTRA-1.0 | 9900 | dense | 5557.381 | 5941.553 | 5351930 |
| COVERAGE-HK-1.0 | 100000 | dense edge limit | 231.582 | 258.046 | 846976 |

HTTP y extracción de almacenes se miden por separado en [http-latencies.json (archivo)](../../../../archivo/detalles-20261104.tar.gz); cada endpoint conserva n y distribución. Estos datos no son equivalentes al tiempo del núcleo algorítmico.
