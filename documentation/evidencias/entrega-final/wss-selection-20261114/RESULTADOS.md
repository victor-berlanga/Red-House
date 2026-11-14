# Selección WSS por Nginx: control y corrección — 13/14 de noviembre de 2026

La configuración corregida pasó **4/4** comprobaciones de selección/Upgrade con Nginx local real. El control antiguo reprodujo **cuatro fallos en el segundo handshake inmediato después de un primer 101**. Son dos corridas independientes con dobles echo; no aceptan el caso B completo de I06-08 ni sustituyen SQL/Mongo, autenticación, Chrome o regresión I06-07. Esos recorridos todavía no se ejecutaron sobre este cambio.

## Intentos y resultados

| Configuración e intento | Resultado JUnit | Duración JUnit | Alcance |
| --- | --- | --- | --- |
| Control antiguo 01 | 4 errores de setup | 2,822 s | Faltaba el padre de `--basetemp`; ningún Nginx ni handshake. No reproduce el mecanismo. |
| Control antiguo 02 | 4 fallos funcionales esperados | 16,662 s | Primero 101 y segundo 502 en las cuatro variantes. Reproduce el patrón investigado. |
| Corregido 01 | 4 aprobados | 17,017 s | Primero y segundo 101; ambos sockets responden después del segundo Upgrade. |

Se conservó el intento de setup y se completó solo la preparación externa del directorio padre. No se cambiaron producto, test ni aserciones entre control 02 y corregido 01. Los tiempos del wrapper incluyen censo/copias/importación y fueron 21,807 s y 24,176 s respectivamente; no son latencias de handshake. [Control de setup](control-antiguo/intento-01/junit.xml), [control funcional](control-antiguo/intento-02/review.json), [corregido](corregido/intento-01/review.json), [comparación detallada](comparison.json).

| Variante | Control: ambos caídos / primero / segundo | Corregido: ambos caídos / primero / segundo |
| --- | --- | --- |
| Privada WS, restaurar A | 502 / 101 / 502 | 502 / 101 / 101 |
| Privada WS, restaurar B | 502 / 101 / 502 | 502 / 101 / 101 |
| Pública WSS, restaurar A | 502 / 101 / 502 | 502 / 101 / 101 |
| Pública WSS, restaurar B | 502 / 101 / 502 | 502 / 101 / 101 |

El reporte identifica fase `second_upgrade` y estado HTTP numérico 502 en los cuatro controles. El caso no cuenta como reproducción si falla el setup o el primer handshake. Los logs antiguos muestran `no live upstreams` al segundo intento, mientras el primer túnel se mantiene abierto hasta su cleanup. Los corregidos muestran el peer restaurado y, donde se prueba primero el muerto, `upstream_status` `502, 101`. Los logs de cada variante incluyen `$msec`, URI sin query, estado y peer; el acceso 101 se registra al cerrar el túnel, por eso no se usa su orden como instante de apertura.

La copia pública del JUnit del control 02 normaliza únicamente CRLF a LF, procedentes del HTML de error Nginx; el XML parseado permanece idéntico. Se conserva el original privado y [sus huellas](control-antiguo/intento-02/junit-normalization.json). No cambia resultados ni constituye otra ejecución.

## Diferencias exactas

1. Nuevo grupo y zona `transporte_wss`, con los mismos destinos privados A/B y `max_fails=0`. El grupo HTTP `transporte`, sus destinos, límites y política permanecen idénticos.
2. La ruta privada `/ws/v1/tracking/` y la pública generada `/services/transporte/ws/v1/tracking/` apuntan al grupo WSS. Conexión TCP 1 s, `proxy_next_upstream error timeout` y dos intentos explícitos. Lectura 75 s, envío 10 s, encabezados y buffering conservados.
3. El comentario explica que la contabilidad de fallos se libera al terminar el túnel y separa su política de HTTP; no atribuye el fallo a `max_conns`.
4. Nuevo test parametrizado con dos peers echo y cuatro variantes. No inicia los fixtures de bases ni utiliza credenciales del producto.

[Parche exacto](candidate.patch), [huellas y base](source-versions.json). La fuente privada es `deployment/nginx.conf`; `deployment/gcp/configure_public.py` concatena esa fuente y genera la ruta pública. No se cambió Compose ni JSON de aplicaciones/almacenamiento. La prueba ejecutó el generador únicamente sobre archivos vacíos en su directorio propio.

## Aserciones y preparación

- Ambos peers están sin listener; el primer intento único debe recibir 502.
- Preparación explícita de 3,1 s con ambos caídos. El control usa `now-checked <= fail_timeout` en segundos enteros: 2,1 s podía seguir dentro de delta 2. La pausa permite comparar el mismo escenario contra la política histórica; no hay espera entre primer y segundo Upgrade.
- Se restaura solo A o B; no se hace GET de salud al upstream. Solo se consultó la salud local de Nginx antes del corte.
- Cada cliente abre una vez. Primero exige 101 y el peer esperado; segundo se solicita inmediatamente y exige lo mismo. En el corregido, echo de ambos confirma que el primero sigue operativo después del segundo.
- Cada corrida de cuatro casos conservó 1395 huellas iguales antes/después. Control y corregido usan el mismo test y binario; solo difieren las dos fuentes de configuración leídas. Los reportes guardan fase, códigos, tiempos monotónicos, peer y versión/hash Nginx.
- Rutas temporales de Nginx se sustituyen antes de insertar la ruta TLS. El ensayo público real y la comprobación estática verifican que `/private/tmp` no corrompe el certificado.

El control usa las dos fuentes del commit `ccac9242ddcdb8931f9604cbe73cd868cf6fb716`, copiadas a un snapshot propio. El test actual se conserva en ambas corridas. Los `command.json` de cada intento contienen los argv y entorno exactos; `sources-before/after.json` preservan los censos del checkout, y `selection.json` las huellas de la configuración realmente leída, incluida la antigua del snapshot.

AST, Ruff, formato y aplicación limpia aprobados antes del ensayo. `nginx -t` pasó dentro de cada caso funcional. Nginx **1.30.6**, binario SHA-256 `a77a9c3e7b625f2df5ba8e070a36172dc1ae461c1e8b5ca37bdf9ce7c5cd991c`.

## Límites y siguiente ensayo

Los peers son dobles echo estrechos y no son Transporte. No prueban autenticación, autorización, persistencia, replay, revocación, permisos, capacidad ni seguridad clínica. El control reproduce externamente el patrón y la nueva política lo evita en estas cuatro variantes. No se capturaron contadores internos `fails/checked/conns`; no se declaran observados.

`max_fails=0` permite que cada nueva conexión pruebe un destino caído. El segundo intento es failover de handshake, sin retransmisión de mensajes tras 101. Un segundo limita TCP, no el Upgrade completo: un peer TCP vivo que no entregue cabeceras puede esperar el timeout de lectura de 75 s. No se prueba ese caso ni un SLA. No hay reintento añadido en el cliente.

La ruta pública usa certificado efímero confiado explícitamente por Python; no acredita CA del sistema. Ruta privada WS sin TLS, pública WSS con TLS. Sin Chrome, mosaicos, DB, contenedores ni GCP en este discriminante. Compose conserva `nginx:1.28-alpine`; no se extrapola a esa imagen ni a la instalación publicada.

Todos los Nginx, threads y sockets propios cerraron; `ps` no encontró procesos Nginx del ensayo. [Cleanup y devolución de ventana](cleanup.json). Los directorios privados conservan configuración y clave efímera con permisos propios; no se copiaron certificados privados ni archivos de configuración/estado a evidencia pública. No se borraron bases ni históricos.

B01/B02 continúan fallidos. [Comandos preparados para B03 y regresión 07](planned-browser-commands.json) usan la misma versión de producto y arnés S2, cada uno con fixture y directorio nuevos. **No ejecutados**; requieren otra ventana de dirección. No hay commit ni publicación por este agente.
