# Carga final y volumen — 18/11/2026

Cierra los huecos de carga y volumen de la consigna en tres laboratorios desechables nuevos (`/private/tmp/rh-final-*`), uno a la vez, cada uno borrado al terminar y sin procesos residuales. Base `9f27266`, Mac M1 de 8 GB. El generador y los doce servicios comparten el equipo: una instancia por servicio, sin Nginx ni réplicas. No es GCP. No se tocó código de producto, cuotas ni configuración del producto.

**Criterio de aceptación** (el mismo de la [sección 15 del reporte](../../../markdowns/Reporte_tecnico_final.md#15-pruebas-y-resultados-de-rendimiento) y de la serie anterior): p95 por endpoint estrictamente menor de 2,000 ms y errores menores de 1 %. Además, todos los usuarios de la fase deben haber iniciado sesión.

## Resumen

| Tema | Resultado | Cumple |
| --- | --- | --- |
| INC-436 (429 por compartir identidades) | Con una cuenta por usuario Locust, **cero 429 en endpoints autenticados** con 24 y 36 usuarios. En la serie anterior hubo 575 (10.9 %) con 24 | Sí, causa confirmada y corregida en el arnés |
| Serie de lecturas 12/24/36/6 | 12, 24 y 6 cumplen. 36 tiene 3.48 % de 429, todos en el **feed público anónimo**, cuya cuota es por IP: los 36 usuarios virtuales salen de 127.0.0.1 | 36: **No** |
| Fase mixta, seis perfiles, 12→24→36→48→72 | Cero errores. Mayor p95 por endpoint de 130 a 470 ms. Hasta 86 RPS | Sí |
| Saturación (96 usuarios) | CPU del equipo al 93 % de media. 6 de 95 logins agotaron el tiempo de 20 s y `/health/ready` llegó a 10 s. RPS +14 % con +33 % de usuarios | **No** (punto de saturación) |
| Recuperación (12 tras 48 y tras 96) | p95 global de 62 y 82 ms, cero errores | Sí |
| Volumen SQL (1,046,236 eventos de auditoría) | Las consultas filtradas usan índice y tardan de 30 a 74 ms por API. El **listado por defecto de Auditoría** tarda 0.86 s con 146k, 3.8 s con 546k y responde **503** con 1M (`statement_timeout` de 5 s) | Filtradas: Sí. Listado por defecto: **No** desde ~300k |
| Volumen MongoDB (146,261 documentos) | 52k–129k documentos/s. La API de la proyección documental responde en 25–45 ms | Sí |
| Caché Redis (Inventario) | HIT: mediana 21.8 ms. BYPASS: 24.4 ms. Mejora pequeña con 10k unidades | n/a |
| Sin Redis | 503 `redis_unavailable` en 8–16 ms. `/health/ready` en 503 con Redis `down`. Falla cerrada, sin colgarse | Sí |

## 1. Cambio del arnés (INC-436)

- [`apps/services/scripts/load_final.py`](../../../../apps/services/scripts/load_final.py) crea el laboratorio con `Environment.init()` y la misma población que `prepare_load.py --scale-percent 10`: 2,000 donantes, 10,000 recursos y 100,000 eventos SQL. Después crea **88 cuentas sintéticas adicionales** por SQL dentro del laboratorio, con el mecanismo de `tests/load_support.prepare_transaction_fixture`, que copia el hash de `operator1`. Son MEDICAL 20, OPERATOR 20, COORDINATOR 8, AUDITOR 10, DONOR 20 con expediente propio y TRANSPORT 10. La corrida de estrés usó el doble. También crea una campaña con dos horarios de capacidad 10,000. El MFA de MEDICAL y COORDINATOR se enrola por la API pública del laboratorio. Los secretos llegan a Locust por un descriptor anónimo y no se escriben en disco.
- [`apps/services/tests/locust_final.py`](../../../../apps/services/tests/locust_final.py): cada usuario Locust toma **la siguiente cuenta libre de su rol**, así que en una fase nunca hay dos sesiones con la misma identidad. `phase.json` registra `identities_by_role` y `distinct_identities`. Calienta 30 s después de que todos inician sesión, reinicia estadísticas y mide 120 s, o 60 s en las fases de recuperación. Los logins y las revocaciones quedan fuera de la ventana medida.
- [`apps/services/scripts/load_final_report.py`](../../../../apps/services/scripts/load_final_report.py) genera las tablas y [`resumen-raw.json`](resumen-raw.json) / [`resumen-raw-estres.json`](resumen-raw-estres.json).
- Cambios entre corridas: antes del estrés se agregaron `--account-scale`, `--pause` y `--mixed-recovery-users`, una pausa de 0.8 s entre enrolamientos MFA para no rebasar la cuota anónima por IP de Identidad y la corrección del muestreo de CPU (§3). Después de las corridas solo se aplicaron cambios de formato y lint (`ruff format`/`ruff check`), sin cambio de lógica.
- `phase.json` es la medición autoritativa. `run_stats.csv` y `final.json` de Locust incluyen además el drenado y las revocaciones posteriores al corte.

```sh
# Serie de lecturas, fase mixta y volumen
PYTHONPATH=.:apps/services apps/services/.venv/bin/python apps/services/scripts/load_final.py \
  --mongod /opt/homebrew/bin/mongod --evidence documentation/evidencias/entrega-final/carga-final-20261118/raw
# Estrés 72/96 en un laboratorio nuevo, con cuentas ×2 y 65 s entre fases
PYTHONPATH=.:apps/services apps/services/.venv/bin/python apps/services/scripts/load_final.py \
  --mongod /opt/homebrew/bin/mongod --evidence documentation/evidencias/entrega-final/carga-final-20261118/raw-estres \
  --read-users "" --mixed-users 72,96 --account-scale 2 --pause 65 --skip-volume
```

Ventanas: lecturas y mixta de 17:44:37 a 18:09:12 UTC, volumen de 18:09:12 a 18:16:11 UTC y estrés de 18:16 a 18:27 UTC.

## 2. Serie de lecturas con identidad propia (repite la serie 12/24 y agrega el estrés de 36)

Mismas operaciones y espera (0.5–1.5 s) que [`tests/locustfile.py`](../../../../apps/services/tests/locustfile.py), con seis perfiles en rotación: el operador en XML y el resto en JSON. Caché activa.

| Fase | Usuarios | Sesiones/identidades | Peticiones | RPS | Media ms | p95 global | p99 global | Mayor p95 endpoint | Mayor p99 endpoint | Errores | Errores sin feed anónimo | Cumple |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lecturas-12 | 12 | 12/12 | 2900 | 24.16 | 29.5 | 57 | 92 | 86 | 170 | 0 (0.0 %) | 0 (0.0 %) | Sí |
| lecturas-24 | 24 | 24/24 | 5510 | 45.92 | 55.5 | 130 | 420 | 240 | 970 | 54 (0.98 %) | 6 (0.12 %) | Sí |
| lecturas-36 | 36 | 36/36 | 8400 | 70.0 | 52.5 | 120 | 280 | 280 | 800 | 292 (3.48 %) | 0 (0.0 %) | **No** |
| lecturas-recuperacion-6 | 6 | 6/6 | 712 | 11.87 | 41.9 | 95 | 510 | 160 | 900 | 0 (0.0 %) | 0 (0.0 %) | Sí |

- **INC-436 resuelto en el arnés:** con 24 usuarios hubo cero 429 en endpoints autenticados. Antes hubo 575, repartidos en seis endpoints autenticados ([serie anterior](../carga-serie-20261118/24-active/run_failures.csv)). Con 36, el sistema atendió 70 RPS, frente a 43.95 con 24 en la serie anterior, también sin 429 autenticados. La cuota por cuenta (180/min por servicio) no cambió.
- **Errores restantes, dos causas distintas:**
  - **429 del feed público** (48 con 24 usuarios y 292 con 36): el endpoint es anónimo y su cuota se cuenta **por IP** (`rate_limit()` sin identidad). Todos los usuarios virtuales salen de 127.0.0.1. Esta parte del arnés no se pudo corregir: simular varias IP exige configurar alias de loopback con permisos de administrador, y no se modificó la configuración del sistema. En producción, cada donante tiene su IP. Aun así, la fase de 36 no se acepta por el criterio de errores.
  - **6 respuestas 503 `redis_unavailable`** con 24 usuarios (0.12 %): el SLOWLOG de Redis quedó vacío (ningún comando de 10 ms o más), `rejected_connections` fue 0 y `aof_delayed_fsync` fue 0. El cliente tiene `socket_timeout=1` s (`redhouse/security.py`). La causa probable es que el equipo saturado no programó a tiempo al proceso cliente: la CPU llegó a 88.8 % y quedaban ~1.1 GB de RAM libre. No se atribuye a Redis. No se repitieron con 36.
- **Endpoint más lento:** `auditoria / Bitácora` en todas las fases, con p95 de 86 a 280 ms y p99 de 170 a 900 ms. Es el listado por defecto de Auditoría (ver §5).

## 3. Fase mixta con perfiles diferenciados

| Perfil (clase Locust) | Peso | Cuenta | Formato | Qué hace |
| --- | ---: | --- | --- | --- |
| Consulta web (`ConsultaWeb`) | 2 | MEDICAL con MFA | JSON | Disponibilidad regional, solicitudes e indicadores de inventario |
| Móvil donante (`MovilDonante`) | 3 | DONOR | JSON | Consulta 3/4 (agenda, avisos, expediente). **Registra** 1/4: reserva → reprograma → cancela una cita (`appointment_cycle`) |
| Móvil transportista (`MovilTransportista`) | 1 | TRANSPORT | JSON | Tareas propias y avisos de traslado |
| Escritorio (`EscritorioOperador`) | 2 | OPERATOR | **XML** | Inventario, campañas y reportes. **Registra** una unidad en cuarentena (`inventory_cycle`). **Solicita un reporte** INVENTORY CSV en Documentos (POST `export-jobs` 202 + estado), a lo sumo uno cada 120 s por operador |
| Auditor/monitoreo (`PanelAuditoria`) | 1 | AUDITOR | JSON | Bitácora, proyección documental MongoDB, hallazgos, estado regional y chequeos de Monitoreo |
| Proceso automático (`ProcesoAutomatico`) | fijo 1 | sin sesión | JSON | Sondea `/health/ready` de los 12 servicios cada 5 s |

| Fase | Usuarios | Sesiones/identidades | Peticiones | RPS | Media ms | p95 global | p99 global | Mayor p95 endpoint | Mayor p99 endpoint | Errores | Cumple |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mixta-12 | 12 | 12/11 | 1920 | 16.0 | 27.9 | 52 | 100 | 130 | 130 | 0 | Sí |
| mixta-24 | 24 | 24/23 | 3625 | 30.21 | 37.3 | 91 | 170 | 210 | 890 | 0 | Sí |
| mixta-36 | 36 | 36/35 | 5359 | 44.66 | 44.6 | 100 | 180 | 260 | 780 | 0 | Sí |
| mixta-48 | 48 | 48/47 | 7040 | 58.66 | 60.6 | 160 | 290 | 470 | 700 | 0 | Sí |
| mixta-recuperacion-12 | 12 | 12/11 | 963 | 16.05 | 31.2 | 62 | 180 | 370 | 370 | 0 | Sí |
| *Estrés (lab. nuevo)* mixta-72 | 72 | 72/71 | 10333 | 86.11 | 65.9 | 130 | 210 | 290 | 400 | 0 | Sí |
| mixta-96 | 96 | **90/95** | 11803 | 98.34 | 114.2 | 250 | 360 | **10000** | 10000 | 6 (0.05 %) | **No** |
| mixta-recuperacion-12 | 12 | 12/11 | 964 | 16.07 | 36.0 | 82 | 200 | 750 | 750 | 0 | Sí |

En «Sesiones/identidades», el usuario sobrante es el proceso automático, que no inicia sesión. Con 48 usuarios hubo 255 registros (201) y 10 reportes solicitados (202) dentro de la ventana. Con 96 hubo 468 registros y 17 reportes.

### Por perfil, 48 y 96 usuarios

| Perfil | 48: RPS | 48: media ms | 48: p95 máx. | 48: p99 máx. | 96: RPS | 96: media ms | 96: p95 máx. | 96: p99 máx. | Errores 48/96 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Consulta web (médico) | 14.83 | 64.1 | 150 | 250 | 26.59 | 118.4 | 270 | 430 | 0/0 |
| Escritorio XML (operador) | 12.89 | 59.0 | 280 | 290 | 24.67 | 110.7 | 320 | 480 | 0/0 |
| Móvil donante | 18.63 | 52.9 | 210 | 310 | 33.39 | 99.1 | 310 | 390 | 0/0 |
| Móvil transportista | 2.65 | 53.3 | 120 | 300 | 5.83 | 97.3 | 230 | 310 | 0/0 |
| Panel auditor/monitoreo | 7.46 | 85.4 | 470 | 700 | 6.87 | 131.3 | 520 | 660 | 0/0 |
| Proceso automático | 2.2 | 36.8 | 76 | 150 | 1.0 | 570.3 | 10000 | 10000 | 0/6 |

Las tablas de 12, 24, 36 y 72 están en [`resumen-raw.json`](resumen-raw.json) y [`resumen-raw-estres.json`](resumen-raw-estres.json).

### Endpoints más lentos (48 usuarios)

| Método | Endpoint | Peticiones | Media ms | p95 ms | p99 ms |
| --- | --- | ---: | ---: | ---: | ---: |
| GET | Auditor · Bitácora (`/api/v1/events`) | 179 | 231.4 | 470 | 700 |
| POST | Escritorio XML · Solicitar reporte de inventario | 10 | 130.5 | 280 | 280 |
| GET | Móvil donante · Horarios autorizados (`campaign-slots`) | 140 | 106.1 | 210 | 300 |
| GET | Escritorio XML · Inventario propio | 433 | 77.9 | 160 | 260 |
| GET | Consulta web · Disponibilidad regional | 594 | 70.4 | 150 | 240 |

Con 96 encabeza `/health/ready`, porque seis sondeos agotaron el tiempo de 10 s. Le siguen Bitácora (p95 520 ms) e Inventario propio en XML (p95 320 ms).

### Saturación y recuperación

- **Hasta 72 usuarios** escala casi lineal: 16 → 30 → 45 → 59 → 86 RPS, cero errores y mayor p95 por endpoint de 470 ms o menos.
- **Con 96 usuarios el equipo se satura:** la CPU del sistema promedió 93.4 % (máximo 99.2 %), las APIs consumieron ~198 % y Locust 22 %. El RPS solo subió 14 % (de 86 a 98) y la media casi se duplicó (de 66 a 114 ms).
  - **6 de 95 logins** agotaron el tiempo de 20 s del cliente. Los 95 inicios de sesión llegan en el mismo segundo y Login es de CPU: la verificación de contraseña tarda ~430 ms de mediana en el servidor. Identidad corre en waitress con 8 hilos, y la cola de la ráfaga pasó de 20 s. Las 171 peticiones de login que llegaron al servidor respondieron 200, así que las seis fallidas no aparecen en su log.
  - **6 sondeos `/health/ready`** expiraron a los 10 s (código 0), y Monitoreo e Inventario registraron un 503 de salud cada uno. Fuera de la ventana de medición, `mixta-96` no tiene errores de negocio.
  - La fase no se acepta: 90 de 96 sesiones, y p95 de 10,000 ms en el sondeo de salud.
- **Recuperación:** al bajar a 12 usuarios después de 48 y de 96, el p95 global fue de 62 y 82 ms, sin errores. El mayor p95 por endpoint de la recuperación posterior a 96 (750 ms, Bitácora, 18 peticiones) es una sola muestra lenta en una ventana de 60 s.
- **Caché en la fase mixta:** domina MISS (con 48 usuarios hubo 1,427 MISS y 193 HIT), porque cada registro de unidad cambia la revisión de caché de Inventario. En lectura pura, 12 usuarios dieron 397 HIT y 50 MISS.

### Recursos durante la medición (media / máximo)

| Fase | APIs CPU % | APIs RSS MB | Workers CPU % | PostgreSQL RSS MB | Locust CPU % | Sistema CPU % | RAM disponible mín. MB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lecturas-12 | 39.5 / 65.6 | 317 / 407 | 7.6 / 17.0 | 151 / 205 | 3.7 / 4.9 | 49.5 / 78.9 | 1204 |
| lecturas-36 | 104.2 / 145.5 | 321 / 370 | 14.9 / 25.7 | 190 / 301 | 12.0 / 16.0 | 64.5 / 90.1 | 1174 |
| mixta-48 | 107.2 / 144.3 | 363 / 447 | 15.1 / 27.4 | 171 / 364 | 10.4 / 15.1 | 72.3 / 92.4 | 1165 |
| mixta-72 | 166.4 / 201.4 | 400 / 469 | 20.0 / 27.2 | 188 / 412 | 17.5 / 22.7 | 87.1 / 96.1 | 1167 |
| mixta-96 | 197.6 / 222.9 | 389 / 467 | 19.1 / 27.9 | 219 / 337 | 22.0 / 26.7 | 93.4 / 99.2 | 1170 |

La CPU por proceso se suma por grupo; 100 % equivale a un núcleo. La columna «Sistema» es la CPU total del equipo. La CPU de PostgreSQL en la primera corrida no es fiable: el primer muestreo de cada backend nuevo daba picos espurios. El muestreador se corrigió antes del estrés, con PostgreSQL en 18–19 % de media con 72 y 96 usuarios. El RSS en macOS no incluye la memoria comprimida: el equipo tuvo ~1.1 GB libres durante toda la corrida, con Docker Desktop y otras aplicaciones abiertas.

## 4. Hallazgo: los reportes en segundo plano consumen la cuota interactiva del usuario (defecto, no corregido)

En la prueba de humo, con un reporte cada ~10 s por operador, aparecieron 7 respuestas 429 en 20 s ([`hallazgo-cuota-reportes/`](hallazgo-cuota-reportes/phase.json)). Los `correlation_id` de los 429 de Documentos coinciden con 429 de `GET /api/v1/resources` en Inventario.

`ms_documentos/reports.py` extrae el reporte llamando a Inventario de 100 en 100 filas, hasta 500 páginas, con la **autorización delegada del usuario** (`call(...)` reenvía su `Authorization`; el worker usa `g.worker_authorization`). Un reporte INVENTORY de ~10,000 unidades consume ~100 peticiones de la cuota de 180/min de ese usuario en Inventario. Dos reportes por minuto agotan la cuota, y el usuario recibe 429 en sus consultas interactivas y en nuevas solicitudes de reporte. El arnés final limita los reportes a uno cada 120 s por operador, un ritmo de escritorio. El defecto queda **descrito y sin corregir**. Opciones: cuota por servicio para la extracción delegada (`category="service"`), páginas más grandes o una cuota separada para trabajos.

## 5. Volumen

### 5.1 PostgreSQL: eventos de auditoría (`red_house.audit_event`, API `GET /api/v1/events`)

Es la tabla de alto volumen que el producto consulta por API, con 8 índices: la llave primaria y 7 secundarios. Las filas tienen la forma del evento real (`event` jsonb con `occurred_at`, `resource_id`, `correlation_id` y una acción del catálogo de las categorías BUSINESS/DECISION/SECURITY). Todo cae en una sola región del laboratorio.

| Punto | Filas totales | Inserción de la etapa | Tabla | Índices | Total |
| --- | ---: | --- | ---: | ---: | ---: |
| executemany, lotes de 1,000 | +20,000 | **18,891 filas/s** | | | |
| COPY 100k | 146,186 | 80,000 en 3.71 s = **21,580 filas/s** | 99.6 MiB | 73.9 MiB | 173.6 MiB |
| COPY 500k | 546,211 | 400,000 en 19.79 s = **20,212 filas/s** | 361.2 MiB | 299.0 MiB | 660.3 MiB |
| COPY 1M | **1,046,236** | 500,000 en 123.79 s = **4,039 filas/s** | 688.0 MiB | 581.3 MiB | 1,269.5 MiB |

Las 980,000 filas por COPY tardaron 147.3 s de inserción pura (6,654 filas/s en promedio) más 15.1 s de generación en Python, que no cuentan como inserción. La caída a ~4k filas/s después de ~550k coincide con índices de 300–580 MiB que ya no caben en `shared_buffers` (128 MB por omisión), con ~1.1 GB de RAM libre en el equipo. Tres de los ocho índices tienen claves aleatorias (la llave uuid, la correlación y el recurso), y `audit_execution_search` evalúa una función plpgsql por fila. Inferencia, no medición: su mantenimiento pasa a disco. PostgreSQL usó 24–54 % de CPU y 245–413 MB de RSS durante la inserción.

**Consulta del producto** (SQL exacto de `ms_auditoria/queries.py`, rol propietario y `REPEATABLE READ`). Se muestra el tiempo de ejecución de EXPLAIN ANALYZE en ms. «Sin índice» se midió con un `DROP INDEX` de los 7 índices secundarios dentro de una transacción que después se revirtió. Planes en [`planes/`](planes/).

| Consulta | Filas | count con índice | página con índice | count sin índice | página sin índice | API mediana / p95 (8 llamadas) |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Listado por defecto (sin filtros) | 146k | 195 (Seq Scan) | 681 (Seq Scan + top-N) | 227 | 639 | 861 / 883 ms, 200 |
| | 546k | 780 (Seq Scan) | 3,178 | 816 | 3,107 | **3,787 / 3,863 ms**, 200 |
| | 1.05M | 1,895 | 7,115 | 3,137 | 7,532 | **7,686 / 7,984 ms, 503 ×8** |
| Ventana de 1 h (`from`/`to`) | 146k | 1.9 (`audit_execution_search`) | 7.2 | 788 (Seq Scan) | 945 | 30 / 31 ms |
| | 546k | 2.6 | 7.2 | 2,660 | 2,706 | 30 / 31 ms |
| | 1.05M | 4.6 | 7.3 | 6,270 | 7,016 | 33 / 35 ms |
| Filtro por acción | 146k | 5.8 (`audit_action_search`) | 4.6 | 26 | 35 | 29 / 32 ms |
| | 546k | 266* | 21 | 135 | 146 | 47 / 48 ms |
| | 1.05M | 31.7 | 461* | 1,608 | 1,654 | 74 / 103 ms |

\* Primera ejecución en frío. La mediana de 5 repeticiones fue de 1.3 y 45 ms.

- **Uso de índices:** durante las llamadas a la API, `pg_stat_user_indexes` sumó 16–24 escaneos en `audit_execution_search` y `audit_action_search` en cada punto. Las consultas filtradas son prácticamente constantes con índice: 7 ms para la página con 146k y con 1M. Sin índice crecen de forma lineal: de 945 ms a 7 s.
- **Defecto de escalabilidad (no corregido):** el listado por defecto de la Bitácora, que es la primera pantalla del auditor, cuenta y ordena **todas** las filas de la región. Con o sin índice el plan es un Seq Scan con un top-N sort. Ordena por `executed_at DESC NULLS LAST, created_at DESC, id`, donde `executed_at` viene de una función plpgsql por fila. El índice `audit_execution_search (region_id, event_time(...), event_id)` no coincide con ese orden y el filtro de categoría usa un `CASE`. El tiempo crece de forma lineal, ~7 µs por fila. **Supera el umbral de 2 s desde ~300k eventos por región. Con ~1M, la consulta de página pasa el `statement_timeout=5000` del producto (`redhouse/db.py`), PostgreSQL la cancela y la API responde 503 `database_unavailable`.** Opciones: ventana temporal por omisión en el listado, un índice que coincida con el orden, paginación por cursor y conteo estimado.
- **Caché:** Auditoría no usa caché Redis, por diseño: lee en `REPEATABLE READ` sin `cached_read`. La caché aplica solo a Inventario y Catálogos (ver §5.3).

### 5.2 MongoDB: proyección documental de Auditoría (`rh_auditoria.events`, API `GET /api/v1/documentary-events`)

Antes de la carga sintética había 46,245 documentos de las fases Locust (proyección real de eventos). Se agregaron 100,000 con la forma del evento.

| Documentos | Inserción `insert_many`, lotes de 5,000 | Datos / almacenamiento / índices | `count` con índice `region_id_1_source_1` | `count` sin índice | Página de 20 (ordenada por `_id`) | API mediana / p95 |
| ---: | --- | --- | --- | --- | --- | --- |
| 56,261 | 10k en 0.19 s = 51,925/s | 33 / 7.8 / 4.5 MiB | 8 ms (COUNT_SCAN, 56,262 claves) | 13 ms (COLLSCAN, 56,261 docs) | 20 docs examinados | 21 / 41 ms |
| 96,261 | 40k en 0.31 s = 129,484/s | 50 / 11.7 / 6.4 MiB | 13 ms | 21 ms | 20 docs | 24 / 25 ms |
| **146,261** | 50k en 0.58 s = 86,298/s | 71 / 17.3 / 9.1 MiB | 32 ms | 73 ms | 20 docs | 45 / 69 ms (sin índice: 71 ms) |

El conteo crece de forma lineal con o sin índice, porque todos los documentos son de la misma región. Con índice cuesta cerca de la mitad. La página usa el índice `_id`. La API cumple con holgura, pero su `socketTimeoutMS=1500` limita el crecimiento: con la misma pendiente, el conteo sin índice llegaría a ~1.5 s cerca de 3M documentos. Es una extrapolación, no una medición.

### 5.3 Caché Redis, con y sin bypass

`GET /api/v1/resources?page_size=20` de Inventario, `operator1`, 60 llamadas secuenciales por modo con ~10,361 unidades.

| Modo | Estado | Mediana ms | p95 ms | Máx. ms |
| --- | --- | ---: | ---: | ---: |
| Activa | 59 HIT, 1 MISS | 21.8 | 44.2 | 102.9 |
| Bypass (`Cache-Control: no-cache`) | 60 BYPASS | 24.4 | 29.9 | 32.0 |

Con este volumen la consulta SQL de Inventario ya es barata, y la caché ahorra ~11 % de mediana. El p95 lo domina el ruido del equipo: la prueba de humo dio el resultado inverso, con p95 de 216 ms en BYPASS. No se afirma una mejora general. En la fase mixta, las escrituras invalidan la caché a menudo (§3).

### 5.4 Sin Redis

Al final se detuvo solo el Redis del laboratorio (SIGTERM a su PID):

| Llamada | Resultado |
| --- | --- |
| Inventario `GET /api/v1/resources` | 503 `redis_unavailable` en 15.7 ms |
| Auditoría `GET /api/v1/events` | 503 `redis_unavailable` en 7.7 ms |
| Inventario `/health/ready` | 503, con Redis `down` / `dependency_unavailable` |

Redis es obligatorio para la sesión, la autorización y la cuota, no solo para la caché. Sin él, el sistema falla cerrado y rápido. La recuperación al reiniciar Redis está en [fallos-consigna-20261118](../fallos-consigna-20261118/RESULTADOS.md).

## Estado sugerido de incidencias

- **INC-436: cerrar.** La causa era del arnés, porque 24 sesiones compartían 6 identidades. Con una identidad por usuario hubo cero 429 autenticados con 24 y 36 usuarios, y el estrés de 36 ya se ejecutó. Queda una limitación nueva y distinta: la cuota anónima por IP del feed público con un generador de una sola IP. Conviene registrarla aparte.
- **INC-290: sigue abierta por su propio criterio.** Exige repetir en el mismo equipo Intel. En la M1, 24 usuarios dieron un mayor p95 por endpoint de 240 ms en lecturas y 210 ms en la fase mixta. La evidencia apunta a una causa del equipo, pero no se repitió en el mismo hardware.
- **Nuevas:** (a) los reportes de Documentos consumen la cuota interactiva del usuario (§4); (b) el listado por defecto de Auditoría es O(n) y responde 503 con ~1M de eventos por región (§5.1); (c) la saturación con 96 usuarios en una Mac M1 de 8 GB: ráfaga de logins y sondeos de salud (§3).

## Límites

- Un solo equipo con poca memoria libre (~1.1 GB, Docker Desktop abierto) y con generador y servicios juntos. No representa capacidad en GCP ni en producción.
- El feed público anónimo se mide desde una sola IP (§2).
- La rampa de 96 usuarios es instantánea: 96 inicios de sesión en el mismo segundo. En uso real, la ráfaga de logins se reparte en el tiempo.
- El volumen de 1M se insertó por COPY con privilegios del laboratorio, no por la API. La inserción por la API de Auditoría pasa además por la bandeja de salida, anomalías y MongoDB.
- No se midió GPS/WSS bajo carga (`POST /telemetry` exige dispositivo y asignación vigentes).
- CPU y RSS por muestreo cada 2 s con psutil. La CPU de PostgreSQL de la primera corrida no es fiable (§3).
- La configuración de diagnóstico `latency-monitor-threshold` se activó en el Redis del laboratorio de la primera corrida, después de las fases afectadas. El laboratorio ya se borró.

## Archivos

- `raw/`: serie de lecturas, fase mixta 12–48 y volumen. Cada fase guarda `phase.json`, que es la medición autoritativa con recursos, `run_stats.csv`, `run_failures.csv`, `run_exceptions.csv` y `final.json`. El volumen está en `raw/volume.json`, con los planes completos.
- `raw-estres/`: 72, 96 y recuperación 12, con la misma estructura.
- `planes/`: 36 planes de PostgreSQL (EXPLAIN ANALYZE BUFFERS, JSON) y 6 explain de MongoDB.
- `hallazgo-cuota-reportes/`: fase de humo con los 429 de §4.
- `resumen-raw.json` y `resumen-raw-estres.json`: tablas por fase, perfil y endpoint.
