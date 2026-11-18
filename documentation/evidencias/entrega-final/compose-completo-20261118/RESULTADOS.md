# Compose completo desde copia limpia — 18/11/2026

Resultado: **PASS sin intervención manual.** Los pasos de [`deployment/README.md`](../../../../deployment/README.md) dejaron sanos los 29 contenedores duraderos: 3 bases, el gateway, 24 réplicas API/worker y la web. Hubo 3 minutos de estabilidad sin reinicios y un ciclo detener/arrancar completo.

- **Base:** `52dbe1e` (`entrega-final`), con la corrección del almacenamiento de Documentos de `4f08abf`. Copia limpia de los archivos versionados.
- **Proyecto aislado:** `redhouse-compose-20261118`, etiqueta `compose-20261118`.
- **Equipo:** Mac M1 de 8 GB; Docker Desktop con 3.825 GiB y 8 CPU.
- **Contenedores ajenos:** con autorización del usuario, se detuvieron durante el ensayo los cuatro contenedores de otros proyectos y se volvieron a levantar al terminar.

## Pasos

| Paso | Comando | Hora UTC | Resultado |
|---|---|---|---|
| B1 | `python3 deployment/prepare.py` | 04:19:30 | PASS |
| B2 | `docker compose --profile install --parallel 2 build bootstrap mongodb` | 04:19:30–04:19:45 | PASS |
| B3 | `docker compose up -d --wait postgres redis mongodb` | 04:19:45–04:20:21 | PASS |
| B4 | `docker compose --profile install run --rm bootstrap` | 04:20:21–04:20:28 | PASS: base compartida, ACL, claves y 14 cuentas ficticias |
| B5 | `docker compose --parallel 2 build` | 04:20:28–04:20:36 | PASS: 13 imágenes |
| B6 | `python3 deployment/start.py` | 04:20:36–04:22:18 | **PASS**: 29 sanos. Documentos sano al primer intento, a diferencia del [ensayo anterior](../clon-limpio-20261118/RESULTADOS.md) |

## Comprobaciones

- **Gateway, 6101–6112:** 12/12 en `/health/ready`, en `/docs/` y en `/openapi.json`, todos con 200.
- **Almacenamiento:** `/health/storage` de Documentos `up`, con proveedor `local`.
- **Portal y API:** portal en 6050 con 200. Login de `operator1` con 200. Instituciones en JSON (200, 526 bytes) y en XML (200, 1263 bytes).
- **Memoria después del arranque:** el proyecto usaba 2,639 MiB y la VM de Docker tenía 625 MiB disponibles, con el swap de 1 GiB agotado y carga de 3.24. Funciona, pero sin margen.
- **Estabilidad ([estabilidad.log](estabilidad.log)):** seis muestras cada 30 s, de 04:23:28 a 04:26:07. Siempre hubo 29 sanos, 0 reinicios y ningún mensaje de recuperación en PostgreSQL.
- **Reinicio:** `docker compose stop` dejó 0 activos. Después, `start.py` terminó con código 0 en 94 s y volvieron los 29 sanos, 12/12 en 200 y el portal en 200. Los datos persistieron: el login siguió funcionando y se conservaron las 2 instituciones.

## Diferencia con el ensayo anterior

El [clon limpio de la misma noche](../clon-limpio-20261118/RESULTADOS.md) falló por dos motivos:
- **D2:** Documentos no tenía almacenamiento configurado. La corrección de `4f08abf` lo resolvió.
- **D3:** falta de memoria, con otros cuatro contenedores activos que usaban 253 MiB. Esta vez se cerraron esos contenedores.

En 3.8 GiB el stack completo cabe con lo justo. Con más contenedores en el mismo Docker Desktop se repetiría la saturación.

## Limpieza

`docker compose --profile install down --volumes --remove-orphans`, limitado a este proyecto. Se borraron todas las imágenes del ensayo, incluidas `postgres:14-bookworm`, `redis:7.4-bookworm`, `nginx:1.28-alpine` y `alpine:3` (para leer la memoria), que se descargaron durante el ensayo y ningún otro contenedor usa. También se borró la copia y su `.local/compose` privado. No se publica el log con la configuración privada.
