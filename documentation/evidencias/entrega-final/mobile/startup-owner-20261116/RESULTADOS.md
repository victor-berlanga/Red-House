# Restauración de acceso y conservación de pendientes — 16/11/2026

Se integraron exactamente las seis fuentes del parche revisado `2eb95b359b56a039db316d0a6fca7e33ef6f733f31013fd9fead92b34060fbd8`. [Hashes de fuentes](FUENTES.json).

Ante un fallo transitorio de restauración con registro guardado válido, la app presenta comprobación y reintento de conexión, sin publicar datos protegidos ni ofrecer una autenticación que sustituya ese registro. Los errores terminales tienen salida explícita; una lectura fallida del almacenamiento conserva el bloqueo. Si Session ya eliminó credenciales por un refresh incierto, no se reenvía ese refresh.

El login conserva diario y observaciones hasta validar la autenticación. El mismo propietario `origen:usuario:institución` conserva los pendientes; otro propietario limpia la cola y vincula el diario antes de publicar la sesión. El cierre explícito mantiene su comportamiento. `LocalJournal` persiste antes de cambiar memoria en bind/put/remove/clear. Un fallo de escritura impide enviar un comando no guardado o conserva la clave original para recuperación. No se promete una transacción entre los dos almacenes: la cola puede haberse limpiado si falla después la persistencia de una identidad distinta.

## Pruebas y compilación

| Suite dirigida | Aprobadas |
|---|---:|
| SessionOwnerTest | 4 |
| DurablePatchTest | 6 |
| AppointmentContractTest | 1 |
| ResponseContractsTest | 2 |
| SessionTest | 9 |
| PresentationTest | 5 |
| **Lote02** | **27/27** |

[JUnit y hashes](junit/summary.json): seis XML, cero fallos/errores. Se retiró únicamente el hostname personal. El lote03 reutilizó exactamente estos resultados y el APK Android, sin repetir Android ni las pruebas; no son 54 ejecuciones. Tampoco se suman aquí los cortes históricos de 16 y 5 pruebas. Las nuevas pruebas ejercen fallo de autenticación, conservación de propietario, cambio de usuario/institución/origen, fallo de persistencia y reintento, ausencia de HTTP preparatorio y recuperación de cuerpo/clave originales.

Android normal compiló en lote02. iOS normal y Lab compilaron en lote03, con salida 0. [Paquetes y verificación](PAQUETES.json): APK Android `10dd299c7b1d9f5c039ebb12470bf707e646ec5edbed87f5afa1a4459e08287d`; ejecutable iOS normal `39429d9f3116b9016bb375b4f0e578bacc02aba1e8617c06c26f664678d9cdf6`; ejecutable Lab `dcc9027c52dfd540c1106e221257f53b5b15bc08ae0bc12abfd6b3d072295219`.

El runner comprobó identidad de variante/bundle/origen, firma estricta, equipo `QNKMG4ALLQ`, application-identifier y grupos Keychain iguales al artefacto firmado anterior de cada variante. Normal conserva confianza del sistema y ausencia de CA Lab. Lab conserva `org.redhouse.mobile.lab` y CA DER `379967e5eb85bb038eb85dcacad987f01942c35a749ef4ea7d7c843a5d195b00`. Los hashes de framework y manifiestos están en el recibo. No se publican binarios ni credenciales.

## Límites vigentes

**No instalados ni activados en este corte.** La inspección visual de la nueva pantalla de restauración/reintento sigue pendiente; el candidato de instrumentación permanece privado. El resultado de compilación y las unidades no acreditan esa inspección ni un nuevo recorrido físico. No se repiten QR, foto, GPS, agenda ni sincronización anteriores.

Perfiles observados: normal vence **17/11/2026 22:39:00 UTC**; Lab vence **21/11/2026 18:32:33 UTC**. No cubren todavía el 23/11. El certificado de desarrollo vigente hasta 2027 no extiende esos perfiles. `-allowProvisioningUpdates` no produjo en este lote una vigencia nueva; cualquier renovación queda separada, con la misma cuenta/equipo/certificado y dispositivo existentes.

[Fallos de preparación conservados](PREPARACION.json): lote01 se detuvo antes de compilar por asumir que la etiqueta de firma contenía el equipo; se corrigió cotejando OU del certificado y huella entre identidades válidas. Lote02 terminó Android/27 pruebas y se detuvo antes de compilar iOS normal por usar un scheme inexistente. El listado real y los éxitos previos acreditaron target `RedHouse` para normal y scheme `RedHouseLab` para Lab; lote03 reanudó solo iOS. Ninguno de esos errores del runner se atribuye al producto. Fuentes, artefactos y logs anteriores permanecen conservados.
