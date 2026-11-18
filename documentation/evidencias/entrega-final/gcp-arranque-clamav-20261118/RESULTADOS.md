# Arranque de la VM tras apagado: ClamAV con firmas desfasadas — 18/11/2026

**Defecto real de arranque, corregido y comprobado en la VM.** Al encender la VM `red-house` después de estar apagada desde la noche del 17/11, el portal respondió **502** durante más de 10 minutos.

## Qué pasó

- `redhouse.service` terminó en `failed` a las 17:00:16 UTC: `docker compose ... up -d --wait documentos-a documentos-b` falló con `dependency failed to start: container redhouse-parcial2-clamav-1 is unhealthy`. Sin Documentos no arrancó `web`, y Nginx respondió 502.
- 25 de 30 contenedores estaban sanos; faltaban Documentos A/B, Monitoreo A/B y web.
- El healthcheck de ClamAV (`clamav_readiness.sh`) repetía `degraded: version mismatch`. ClamD tenía cargada la base `daily` **28186** y en disco estaba la **28187**.

## Causa

Al arrancar el contenedor, FreshClam descarga firmas nuevas mientras ClamD carga las anteriores. FreshClam intenta avisar a ClamD (`WARNING: Clamd was NOT notified: Can't connect to clamd through /tmp/clamd.sock`), pero el socket todavía no existe. ClamD se queda con la versión anterior y su `SelfCheck` no detecta el cambio. El healthcheck exige que la versión cargada coincida con la del disco, así que el escáner queda «unhealthy» hasta la siguiente actualización publicada, que puede tardar horas. Ocurre solo cuando la VM estuvo apagada lo suficiente para que haya firmas nuevas al encender.

## Corrección

- `deployment/start.py`: antes del grupo Documentos, `ensure_scanner()` levanta ClamAV y espera a que esté sano. Si queda «unhealthy», manda `RELOAD` a ClamD (`printf 'RELOAD\n' | nc -w 5 localhost 3310` dentro del contenedor) y vuelve a esperar, hasta 480 s. El healthcheck sigue siendo quien decide si las firmas están vigentes: la corrección no relaja ninguna regla. Si ClamAV no está configurado (instalación sin escáner), no hace nada.
- `deployment/gcp/redhouse.service`: `TimeoutStartSec` de 900 a 1800 s, para que la espera del escáner no agote el arranque completo.

## Comprobación en la VM

1. Respaldo de los originales en `/opt/redhouse/.local/compose/backups/start-clamav-reload-20261118/` (`start.py.orig`, `redhouse.service.orig`). Reversa: copiarlos de vuelta y `sudo systemctl daemon-reload`.
2. Instalación de los dos archivos; SHA-256 de `start.py` en la VM igual al del repo (`8d4f5b50…5c67a`).
3. Con ClamAV todavía en `unhealthy`, `sudo systemctl start redhouse` terminó con código 0 y el servicio quedó `active`.
4. Después: ClamAV `healthy` con `ClamAV 1.4.6/28187`, **30 de 30 contenedores sanos**, portal **200** y `/health/ready` 200 en Identidad, Inventario, Documentos, Monitoreo y Alertas.

No se reinició la VM completa para repetir la carrera; la corrección se ejercitó con el estado real que la produjo.
