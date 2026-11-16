# Paquetes móviles — 16/11/2026

## Estado posterior comprobado

El lote de horarios/recuperación actualizó iOS Lab sin desinstalar, conservando bundle `org.redhouse.mobile.lab`, origen `https://10.0.0.22:18443`, CA y grupos Keychain. Ejecutable SHA-256 `5807ab3ce3f9235c17178af64cd26b102312cdf0082ecb7892e8c15658106e50`; framework `f627a5f66b479e28028260dba863f9dad550231f3798db4e1aaf9644b36391e7`. El usuario recuperó el intento pendiente y completó las ramas funcionales de [agenda/TLS](AGENDA.md). No existe captura iOS válida; ambos retornos trusted recuperaron la misma cuenta sin credenciales. Las caducidades de la tabla inicial siguen vigentes. La app normal y su sesión permanecieron intactas.

Android normal del primer lote: SHA-256 `cdf5cfee15bfc90270952efc2f8e1273dbe1bda9917c60252e1ef52044e43099`, sin assets Lab y sin instalarlo contra GCP anterior. Android Lab posterior, con las etiquetas de avisos: SHA-256 `7ba1bf602c0034a84d6820ea282e74eb8a29bfa789078c97562a56e9ec9f5b66`. Se compiló una vez el producto, con PresentationTest 5/5. El ajuste posterior de selector reconstruyó solo el APK instrumentado privado (`c69c70c7ad00add2857202c8c7c22e61b8a605d8eaf7a7f89cb42692ca8c9a22`); el APK de producto conservó su hash.

run03 Android terminó `OK (1 test)` y dirección inspeccionó una [captura original](android-visual/booking-inline-error.png), con campaña/sede/fecha/cupos/error legibles **durante el refresco**, sin atribuir reposo final. La sesión técnica se revocó; AVD y Gradle quedaron cerrados. Los intentos iniciales de boot guard y selector/logcat se conservan separados, sin atribuirlos al producto. [Resultado del lote y JUnit](LOTE-HORARIOS.md); [referencias y hashes de APK privados](ANDROID-LAB-ETIQUETAS.json). No se publican APK Lab/test ni credenciales.

Los candidatos posteriores de recuperación al iniciar, conservación de pendientes al autenticar y aviso de disponibilidad ocupada permanecen privados; no forman parte de estos binarios ni de sus pruebas.

## Corte inicial: rotación de CA y origen Lab

Se compiló e instaló una actualización de `org.redhouse.mobile.lab` (`DebugLab`) en el iPhone 16 Pro físico, sin desinstalar. El usuario autorizó el cambio de origen y el reinicio de sesión Lab, declaró no haber añadido pendientes y confirmó después acceso como donante. La app normal y su Keychain no se modificaron.

| Elemento | Evidencia |
|---|---|
| Ejecutable Lab SHA-256 | `fce5f19d19c82207b38e3478af4e41a2431b096e05dd1f2a8c35964d96b52613` |
| Framework SHA-256 | `70c73aa4fedb2d7923c1560eabfaf97245444b745c8c6054c1f4597e1b9a48b0` |
| CA DER SHA-256 | `379967e5eb85bb038eb85dcacad987f01942c35a749ef4ea7d7c843a5d195b00` |
| Perfil Lab, vencimiento UTC | 21/11/2026 18:32:33 |
| CA y certificado servidor, vencimiento UTC | 30/11/2026 19:25:52 |
| Perfil normal anterior, vencimiento UTC | 17/11/2026 22:39:00 |

La CA y el certificado servidor anteriores habían vencido el 16/11 a las 18:26 UTC. Se archivaron antes de rotar ambos; la nueva hoja contiene SAN para la IP LAN actual. Se verificaron firma, identidad de bundle, coincidencia de CA empaquetada y conexión HTTPS con validación de CA/SAN. La validación offline rechazó IP anterior y CA anterior; esto **no acredita** todavía negativos TLS del cliente nativo.

Fuentes móviles sin cambios respecto al lote final del 14/11; configuración Lab regenerada para el nuevo origen y la nueva CA. `TransportScreen.kt` conserva SHA-256 `fbb9602f2ac22c2763b80fbf3cf69dd73d6eb05ab898fa6829fe38e524f29250`. El ejecutable normal conservó SHA-256 `24407a7e73ea525657ae44c147cec3c32ed622decf10ab02fe3a9ee6d6b86a3f`.

El primer comando de compilación falló antes de compilar por ruta relativa de proyecto incorrecta; el comando corregido terminó `BUILD SUCCEEDED`. El primer arranque del arnés privado falló por una IP antigua en su bind; se corrigió el único literal restante y se verificó cierre antes del segundo arranque. Estos fallos de operación no se atribuyen al producto. El fixture original se reanudó sin reseed; su configuración y datos conservados coincidían con el checkpoint de pausa.

Una captura con el runner existente falló al inicializar XCTest (`LocalAuthentication`, código −4). No hay imagen válida ni inspección visual acreditada en este incremento. No se repitieron QR, foto, GPS ni recuperación positiva de observaciones.

Recibos privados, logs, artefacto firmado y manifiesto: `.local/artifacts/mobile/ios-resume-20261116/`. Claves y credenciales permanecen fuera de la evidencia pública. La agenda E2E-C se documentará con sus resultados reales; este recibo no declara ese recorrido completado.
