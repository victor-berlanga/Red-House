# Recuperación de seguimiento móvil — 17/11/2026

`Tracking.kt` distingue los rechazos WSS de credencial vencida de los rechazos terminales. `unauthorized` y `auth_timeout` permiten volver a comprobar la sesión; únicamente `Session.request` renueva credenciales, después de HTTP 401. Los rechazos 403 terminan el seguimiento y retiran la posición visible. Indisponibilidad, límites e inactividad conservan reconexión con espera.

El presupuesto es de ocho fallos consecutivos. Solo un heartbeat recibido después de la suscripción lo reinicia. Suscripción, instantánea y estado por sí solos no lo reinician. La reconexión no publica posiciones automáticamente y conserva el diario cuando falta confirmación.

## Criterios y evidencia

| Criterio | Comprobación | Resultado |
| --- | --- | --- |
| Diferenciar 401, 403 y fallos transitorios | Once casos comunes `TrackingReconnectTest`, con `Session`/`Api` reales y transporte HTTP simulado | 11 aprobados, 0 omitidos |
| Acotar conexiones inestables y admitir continuidad saludable | Casos de ocho fallos, suscripción/cierre, heartbeat previo y posterior a suscripción | Incluidos en los once |
| Conservar diario y otras operaciones al descartar expresamente | `TrackingRecoveryTest` | 1 aprobado |
| No repetir una renovación cuya respuesta se perdió | `SessionTest.lostRefreshClearsCredentials` | 1 aprobado |
| Ejercitar transporte WSS real | `TrackingSocketTest` temporal, OkHttp y TLS de loopback con certificado validado | 1 aprobado en ejecución separada |
| Cerrar recursos y preservar publicación incierta | Tres conexiones cerradas, cero activas, una renovación, dos publicaciones únicas y un ACK | Aprobado; diario incierto conservado |

La primera ejecución dirigida aprobó 13 pruebas en un build de 3 min 57 s. El ensayo WSS aprobó una prueba en otro build de 1 min 51 s. Los conteos y huellas verificables están en [resumen.json](resumen.json). No se suman como una suite ejecutada conjuntamente.

El peer rechazó la primera credencial sintética. La comprobación HTTP simulada produjo un único refresh y las conexiones siguientes usaron la nueva credencial. La primera publicación recibió ACK; la segunda perdió deliberadamente el ACK y cerró el socket. Tras reconectar y recibir un heartbeat completo, no apareció una tercera publicación. La cancelación dejó seguimiento desconectado y los tres sockets cerrados. El peer terminó con salida 0.

## Reproducción y conservación

Desde `apps/mobile`, con JDK 17 y el SDK Android existente:

```sh
./gradlew :composeApp:testDebugUnitTest \
  --tests 'org.redhouse.mobile.TrackingReconnectTest' \
  --tests 'org.redhouse.mobile.TrackingRecoveryTest' \
  --tests 'org.redhouse.mobile.SessionTest.lostRefreshClearsCredentials' \
  --no-daemon --max-workers=1
```

El primer intento no alcanzó la compilación: el sandbox impidió abrir el lock del caché Gradle. Se conservó ese fallo y se ejecutó el mismo comando con acceso autorizado al caché. Ambos registros permanecen separados.

El ensayo adicional utilizó el peer privado revisado `wss_peer.py` y una copia temporal de `TrackingSocketTest.kt`, configurada mediante `REDHOUSE_TRACKING_WSS_LAB`. Ejecutó únicamente esa clase con el mismo task Gradle. La copia se retiró tras verificar su SHA-256, evitando incorporar a la suite normal una dependencia externa obligatoria. El resumen conserva las huellas del peer y de la prueba. Las once pruebas comunes sí quedan en el repositorio.

Registros completos, XML JUnit, recibos del cliente, reporte del peer, códigos de salida y comprobaciones de limpieza permanecen en el directorio privado `.local/artifacts/mobile/tracking-recovery-integrated-20261117/`. No publicar la clave TLS efímera ni la configuración del laboratorio.

## Límites

Después de estos ensayos se aclararon dos textos del transportista: falta de posición en la vista actual y espera de recepción institucional tras DELIVERED. No modifican Tracking ni las transiciones de custodia. Su inspección nativa se realizará con el lote agrupado; estas pruebas no se atribuyen a una captura posterior.

El transporte OkHttp/WSS y TLS son reales; autenticación HTTP y ACK son dobles controlados. El estado `PERSISTED_SQL` emitido por el peer no acredita persistencia SQL. No hubo acceso SQL, cuentas reales, GCP ni captura GPS. El ensayo tampoco acredita iOS, APK nuevo, aceptación nativa, cierre de las etapas móviles o causa del error WSS histórico: su código original sigue sin conservarse.
