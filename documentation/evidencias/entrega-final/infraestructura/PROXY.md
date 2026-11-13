# Confianza del proxy — 13/11/2026

Incremento local, sin despliegue. Nginx sustituye los encabezados de dirección y protocolo en todos sus accesos internos y públicos, incluido WSS. Los encabezados de host, puerto, prefijo y `Forwarded` aportados por clientes se eliminan. La configuración pública conserva un único salto: conexión externa → gateway → servicio/web.

Waitress solo acepta `X-Forwarded-For` y `X-Forwarded-Proto` desde la dirección exacta configurada. Transporte/gevent aplica la misma frontera. Se retira el antiguo booleano `TRACKING_TRUST_PROXY`, que confiaba en protocolo sin identificar al emisor. El generador público configura `TRUSTED_PROXY_HOST=gateway`; instalaciones con configuración antigua deben regenerarla antes de actualizar. Sin proxy configurado se conserva la dirección de la conexión y no se aceptan encabezados reenviados.

`TRUSTED_PROXY_ADDRESS` acepta una dirección IP; `TRUSTED_PROXY_HOST` debe resolver a una sola IP. Son excluyentes y no admiten comodines. La resolución ocurre al arrancar: si se recrea el gateway con otra dirección, deben reiniciarse los procesos consumidores. No se confía en toda una subred Docker. Los encabezados Host directos conservan las validaciones de host de la aplicación y gateway; no se aceptan equivalentes reenviados.

Comando reproducible desde raíz:

```sh
apps/services/.venv/bin/pytest apps/services/tests/test_proxy_boundaries.py -q --tb=short -W error --junitxml=documentation/evidencias/entrega-final/infraestructura/proxy-20261113.xml
```

Siete casos: emisor no autorizado, política gevent de un salto y cuotas separadas, Waitress real con/sin peer confiable, rechazo de configuración ambigua, generador HTTP/WSS y saneamiento de los trece accesos internos. Redis de cuotas se sustituye por un contador de prueba: esto comprueba la clave por cliente y no disponibilidad Redis real. Los casos Waitress abren sockets loopback reales. La comprobación Nginx inspecciona su configuración generada; no equivale a ejecutar Nginx ni a demostrar TLS, WSS, caída de réplica o continuidad completa. Docker está instalado, pero su daemon no estaba disponible en esta ejecución. WORK-PROXY sigue parcial.

Incidencias conservadas: el sandbox impidió sockets en el primer intento. La repetición autorizada pasó seis casos, pero mostró warnings de cierre del servidor (`proxy-20261113-attempt1.xml`). Al exigir `-W error` falló por un socket del arnés sin cerrar (`proxy-20261113-attempt2.xml`). Se corrigió el cierre ordenado del loop y todos los sockets; el resultado final no tiene esos warnings. El séptimo caso se añadió al endurecer también las entradas internas.

Referencias de comportamiento: [herencia de proxy_set_header en Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header) y [confianza explícita en Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html). Las directivas de una ubicación WSS impiden heredar las del nivel superior; por eso se declara allí toda la política.
