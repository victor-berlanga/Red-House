# Paquetes finales de observaciones — 14/11/2026

Incluyen el diálogo directo y el contador «pendientes · enviadas · para revisar». Noventa fuentes móviles permanecieron idénticas durante las tres compilaciones: [comprobación](fuentes-paquetes-finales.json) y [manifiesto](fuentes-moviles-finales.json). `TransportScreen.kt`: SHA-256 `fbb9602f2ac22c2763b80fbf3cf69dd73d6eb05ab898fa6829fe38e524f29250`.

| Paquete | Identidad y SHA-256 | Resultado |
| --- | --- | --- |
| Android normal Debug 0.3.1 (3) | `org.redhouse.mobile` · `f2a36b2176800a6c3e5a8fff9160176851497a856a76f9ce14456885638968ac` | Compiló en 4 min 10 s. Origen GCP; ZIP sin CA ni fixture de laboratorio. No se instaló en emulador durante este lote. [Recibo](paquete-android-final.json). |
| iOS normal Debug arm64 | `org.redhouse.mobile` · ejecutable `24407a7e73ea525657ae44c147cec3c32ed622decf10ab02fe3a9ee6d6b86a3f` | Build y firma aprobados; framework 3 min 45 s. Origen GCP y CA de laboratorio ausente. Instalado como actualización en iPhone 16 Pro. Perfil hasta 17/11/2026 22:39 UTC. [Recibo](paquete-ios-normal-final.json). |
| iOS Lab DebugLab arm64, privado | `org.redhouse.mobile.lab` · ejecutable `8a15714761375e073c126d07ff27661ff1cdf0f1bfe6e37d8c904368cd200c54` | Build y firma aprobados; framework 2 min 03 s. Origen exacto `https://10.0.0.20:18443` y CA fijada. Instalado como actualización. Perfil hasta 21/11/2026 18:32:33 UTC. [Recibo](paquete-ios-lab-final.json). |

Se usaron cachés, SDK y firma existentes, una compilación activa por vez. `verify_build_identity.py artifact` y `codesign --verify --deep --strict` aprobaron ambos bundles iOS antes de instalar. Las actualizaciones no desinstalaron, borraron datos, cerraron sesión ni introdujeron credenciales. Se conservaron los namespaces Keychain normal/Lab; no se leyeron sus secretos ni se inspeccionó visualmente la continuidad de ambas sesiones en estos artefactos finales. Los paquetes anteriores permanecen conservados.

Artefactos privados: `.local/artifacts/mobile/RedHouse-android-final-observations-20261114.apk`, `.local/artifacts/mobile/ios-final-observations-normal/` y `.local/artifacts/mobile/ios-final-observations-lab/`. Logs y recibos originales en `.local/artifacts/mobile/ios-sync-prepared-20261114/`. Lab no se distribuye como app normal.

No se repitieron suites completas ni QR/foto/GPS/sincronización por el cambio del contador. El [recorrido físico de recuperación](RESULTADOS.md) corresponde al Lab anterior `46af5be…`, con el mismo enqueue y anterior al contador final. Este recibo acredita compilación, identidad, firma e instalación; **no atribuye una nueva aceptación visual del contador ni repite la aceptación funcional en estos binarios**. Android sigue siendo Debug; no es release. La renovación de perfiles para el día 23 continúa pendiente.

Gradle y el fixture propio quedaron detenidos. La ventana pesada se entregó al terminar las instalaciones; no se inició otro fixture para una captura.
