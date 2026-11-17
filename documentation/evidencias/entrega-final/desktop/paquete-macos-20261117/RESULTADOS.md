# Paquete macOS Intel actualizado — 17/11/2026

PyInstaller generó `RedHouse.app` con las fuentes vigentes de escritorio, incluidos los mapas, reportes y analítica ya probados. Compilación y prueba de arranque terminaron con salida 0. El paquete distribuible se conserva en `.local/dist/RedHouse-macOS-x86_64-20261117.zip`, fuera del repositorio versionado.

## Aceptación comprobada

| Criterio | Resultado |
| --- | --- |
| Fuentes estables durante el empaquetado | 160 archivos comparados, sin cambios |
| Contratos completos y vigentes | 58 archivos embebidos idénticos a los originales; sincronización sin diferencias |
| Arranque del ejecutable empaquetado | Ventana creada y contrato `login.xsd` cargado correctamente |
| Inspección visual real | [Ventana del paquete](login-packaged.png) abierta e inspeccionada: cuenta, contraseña, foco visible y botón legibles, sin solapamientos |
| Cierre del proceso propio | Terminado después de la captura; no se inició sesión ni quedaron procesos propios |
| Integridad del ZIP | 1.627 entradas; comprobación CRC completa sin errores |
| Archivos privados de configuración | No se encontraron `.env`, `lab.json`, `credentials.json`, P12, PFX ni perfiles móviles por nombre dentro del ZIP |

El ZIP ocupa 56.627.299 bytes y su SHA-256 es `b39da094f5d140129c1946663a505d940c413962dc08075d23f409efad0c4816`. El ejecutable tiene SHA-256 `03e13934f89cd46a76d463a1d9d0e58f270e13127ca9d475b83953219f6ce494`. El [resumen estructurado](resumen.json) conserva los controles y límites.

La captura corresponde únicamente a la ventana del proceso empaquetado, sin credenciales ni escritorio ajeno. El arranque visible se cerró deliberadamente mediante SIGTERM después de capturar; su código `-15` no sustituye los resultados 0 de compilación y smoke. Se conservan advertencias de alias de fuente y del plugin offscreen sin error funcional observado.

## Reproducción y límites

Se utilizó Python 3.12 y PyInstaller 6.22, con `--windowed --onedir --collect-all keyring` y los contratos incluidos mediante `--add-data`. El script, las fuentes congeladas, los logs, el recibo de cierre y el manifiesto privado permanecen en `.local/artifacts/desktop/final-package-20261117/`. La salida original está en `/private/tmp/redhouse-desktop-20261117-final/`.

Esto acredita empaquetado y arranque en macOS Intel. No acredita Windows 11, Apple Silicon, Linux, notarización ni un nuevo recorrido de negocio dentro del paquete. Se reutilizan las pruebas funcionales existentes del mismo código; no se repitieron por empaquetar. Los requisitos de accesibilidad y las pruebas nativas pendientes mantienen su estado anterior.
