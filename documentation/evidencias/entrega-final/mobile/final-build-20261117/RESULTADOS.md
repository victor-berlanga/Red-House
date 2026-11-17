# Lote móvil y límite de firma — 17/11/2026

Las cuatro variantes Android normal/Lab e iOS normal/Lab compilaron con salida 0. Incluyen la recuperación WSS y los dos ajustes de texto: ubicación no disponible en esta vista y recepción institucional pendiente después de DELIVERED. No se instalaron ni activaron aplicaciones. Los artefactos previos permanecen conservados.

## Aceptación comprobada

| Criterio | Evidencia | Resultado |
| --- | --- | --- |
| Generar Android normal sin confianza privada de laboratorio | Inspección del APK y constantes generadas | Sin CA, política de red ni archivos Lab |
| Generar Android Lab sin credenciales del fixture | Inspección del APK, CA y constantes | CA esperada presente; `lab.json` ausente |
| Mantener identidades iOS y separación normal/Lab | Verificación del artefacto y manifiesto del framework | Bundles, origen, bucket y tareas de fondo coincidentes |
| Conservar acceso al Keychain | Comparación de entitlements con aplicaciones previas firmadas | Grupos de acceso iguales; identificadores de aplicación y equipo correctos |
| Comprobar firma iOS | `codesign --verify --deep --strict` | Ambas variantes aprobadas |
| Cubrir la entrega del día 23 en Monterrey | Fecha del perfil embebido, umbral `2026-11-24T06:00:00Z` | Ninguna variante cubre el umbral |

Huellas y resultados estructurados: [resumen.json](resumen.json). Las [13 pruebas JVM y la prueba WSS separada](../tracking-recovery-20261117/RESULTADOS.md) se conservaron; el lote de compilación no repitió tests. Esas pruebas no atribuyen aceptación nativa a los textos incorporados después.

## Vigencia observada

| Variante iOS | Perfil embebido: vencimiento UTC | Cobertura del día 23 |
| --- | --- | --- |
| Normal | `2026-11-17T22:39:00Z` | No |
| Lab | `2026-11-21T18:32:33Z` | No |

El certificado de desarrollo existente estaba vigente al compilar. La caducidad del perfil es independiente: el build aprobado no acredita instalación ni funcionamiento posterior a ese vencimiento.

## Intento único de renovación reversible

Se identificaron exclusivamente los dos perfiles propios por UUID, hash, equipo, bundle y dispositivo autorizado. Antes de apartarlos se conservaron copias exactas con sus permisos. Xcode intentó regenerar perfiles usando la cuenta y el certificado existentes, con `-allowProvisioningUpdates`, salida nueva y reutilización de los APK originales sin compilarlos otra vez.

El intento falló durante iOS normal con el mensaje `Authentication failed: Your session has expired. Please log in.`. Xcode también informó que no encontró un perfil de desarrollo para ese bundle. El build y el wrapper terminaron con salida 1; iOS Lab no se recompiló. No se generó un sustituto válido ni se declaró renovación exitosa.

El wrapper restauró ambos perfiles originales. Una comprobación posterior confirmó igualdad de bytes, SHA-256 y modo frente a sus backups. Los cuatro artefactos del lote aprobado permanecieron intactos. Gradle confirmó que no quedaban daemons activos. No hubo instalación, cuentas o certificados nuevos, cambios a perfiles ajenos ni reintentos automáticos.

Para continuar se requiere reautenticar la cuenta existente en Xcode y autorizar otro intento acotado. La sesión caducada no se resuelve prolongando fechas ni manipulando firmas. Aun después de autenticar, la cobertura deberá comprobarse en cada nuevo perfil embebido; no se presupone.

## Conservación y límites

La evidencia privada del lote está en `.local/artifacts/mobile/final-build-20261117-01/`: plan, fuentes congeladas, manifiestos, firmas, logs y `final-receipt.json`. El intento de renovación está separado en `.local/artifacts/mobile/profile-renewal-20261117-01/`: backups exactos, plan, recibo de restauración, códigos de salida y `final-artifact-map-private.json`. No publicar perfiles, backups, cuentas ni configuraciones privadas.

Compilar no acredita aceptación física Android/iPhone, accesibilidad, distribución final ni cierre de etapas. Este bloque no inició fixtures, emuladores, simuladores, servicios GCP o captura GPS. El iPhone y la instalación permanecen bajo coordinación de dirección.
