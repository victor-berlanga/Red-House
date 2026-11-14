# Cierre del lote visual móvil — 14/11/2026

## Criterios y resultado

Compilar el lote completo para Android normal e iOS normal firmado; comprobar una vez el recorrido afectado de paginación Android con 105 campañas sintéticas. Conservar los intentos fallidos, los artefactos anteriores y las sesiones físicas iOS. No repetir QR, fotografía, GPS, nombre ni consentimiento por cambios de presentación.

El recorrido dirigido final `DonorVolumeJourneyTest#campaignPagination` pasó **1/1 en 50,953 s**, sin fallos. Recorrió las seis páginas y comprobó el indicador final visible `6 / 6`. [Salida instrumentada](campaign-instrumentation.txt), [captura real de la ventana emulada](campaign-page6.png) y [resumen verificable](resultados.json). Dirección inspeccionó esta captura: control superior, Anterior habilitado, Siguiente deshabilitado, tarjetas y navegación inferior legibles. La aceptación queda limitada a esta pantalla; no implica revisar toda la app ni una foto nueva. El control inferior de paginación está implementado; no se declara una inspección visual separada de ese extremo.

La [lectura HTTPS independiente del fixture](feed-page6-fixture.json) confirmó 105 campañas y cinco elementos en página 6: 101–105. El volumen se preparó por inserción SQL sintética; no acredita crear 105 campañas desde la interfaz. El laboratorio reutilizó `apps/mobile/tests/real_backend.py`, servicios Flask reales y PostgreSQL/Redis/MongoDB temporales. No escribió en GCP ni reinició el laboratorio iOS anterior.

## Cambios incluidos

- Campañas ofrece paginación al inicio y al final, con descripciones accesibles únicas. Buscar campañas limpia el foco del formulario.
- La evidencia de transporte presenta una sola etiqueta «Foto verificada», sin estado técnico `VERIFIED` duplicado.
- El test de volumen permite ejecutar exclusivamente campañas. Espera el botón habilitado antes de pulsarlo y obtiene la contraseña del fixture privado; ADB recibe solo el usuario sintético y `fixtureMode=asset`.
- README distingue el proveedor local/GCS y los resultados EXIF observados previamente. No atribuye eliminación universal de EXIF a iOS.

El cambio de etiqueta fotográfica no altera el protocolo de archivos. Se compiló el assertion actualizado, sin repetir el recorrido de fotografía ya comprobado. Tampoco se ejecutaron ensayos nuevos de filtros, nombre, consentimiento, QR o GPS.

## Compilaciones y artefactos

Android normal Debug compiló en **3 min 16 s**. Su APK conserva `org.redhouse.mobile` y gateway `https://34.18.186.116`; la inspección ZIP no encontró CA ni fixture de laboratorio. SHA-256: `51edf9a47884b7e7f7c824bb6546eda8a3c90a91fb47e04014349ebac62fca2c`. [Identidad y ruta privada](android-normal-artifact.json).

iOS normal Debug/iphoneos arm64 terminó `BUILD SUCCEEDED`; el framework compiló en **3 min 40 s**. La validación previa y posterior confirmó bundle `org.redhouse.mobile`, gateway GCP, tarea de fondo normal y ausencia de CA de laboratorio. `codesign --verify --deep --strict` terminó con código 0 usando el llavero existente. Ejecutable SHA-256: `6f88bf287618622ff2a1efd5b212eda067ae00e41b420a5b21d5ac20f83bf2ce`. Perfil válido hasta **17/11/2026 22:39 UTC**. [Manifiesto](ios-normal-artifact.json). La app quedó preparada, **sin instalar ni comprobar físicamente este artefacto**. Se conservaron los bundles anteriores y las sesiones del iPhone.

Android laboratorio y test compilaron en **1 min 49 s**. Tras corregir la sincronización del test se compiló únicamente instrumentación en **1 min 38 s**: cuatro tareas ejecutadas y 42 reutilizadas. El APK de producto permaneció idéntico por hash. APK instrumentado y `lab.json` son privados, están excluidos de Git y no se distribuyen como evidencia. Los hashes y los resultados de compilación figuran en [el resumen](resultados.json). No se ejecutó una nueva suite JVM por este lote visual.

## Intentos conservados

1. [Preparación: 9,579 s](campaign-instrumentation-failed-fixturemode.txt). Faltó `fixtureMode=asset`; falló antes del acceso por ausencia del fixture privado. Se corrigió el argumento, sin cambiar el producto.
2. [Entorno: 116,609 s](campaign-instrumentation-failed-systemui.txt). El test agotó la espera de página siguiente; durante el diagnóstico se observó el diálogo «System UI isn't responding». Esta observación no demuestra que explique por sí sola todo el timeout. Se conservó separado y se descartó el diálogo. `adb screencap` devolvía cero bytes porque `FLAG_SECURE` bloquea la captura; SurfaceFlinger registró `FB is protected: PERMISSION_DENIED`. No se quitó esa protección ni se cambió renderer.
3. [Sincronización del test: 124,065 s](campaign-instrumentation-failed-disabled.txt). Con el sistema estable, la [captura real](campaign-retry-current.png) mostró página `1 / 6`. El indicador público aparece antes de terminar la carga completa; el test pulsaba mientras el botón seguía deshabilitado. Se añadió espera `isEnabled()` antes de la pulsación, manteniendo el timeout de 90 segundos. La repetición dirigida final pasó, sin intervención manual en el recorrido.

Antes de compilar Android, el sandbox rechazó el lock de la caché Gradle existente; la compilación autorizada posterior pasó. La primera comprobación de firma dentro del sandbox no pudo validar confianza (`CSSMERR_TP_NOT_TRUSTED`); con acceso al llavero existente se verificó el mismo artefacto con código 0. Estos incidentes de preparación no se presentan como fallos del producto ni como compilaciones aprobadas.

## Fuentes, límites y cierre

[Comparación de fuentes](source-verification.json): 120 módulos backend realmente importados permanecieron idénticos. Entre 90 fuentes móviles solo cambió posteriormente el test de volumen por la espera habilitada; [manifiesto inicial](mobile-sources-before.json) y [final](mobile-sources-final.json). Se excluyeron cambios de arneses de carga ajenos que el laboratorio no importó.

Los logs completos y APK quedan en `.local/artifacts/mobile/ui-lote-20261114/`. AVD y fixture propio terminaron con código 0; los daemons Gradle se detuvieron. No se instaló iOS, no se borraron sesiones físicas y no se tocó el fixture iOS previo. Este lote no acredita release, cámaras físicas Android, nuevas capacidades clínicas ni el cierre integral de la etapa móvil.
