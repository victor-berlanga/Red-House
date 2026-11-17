# Paquete macOS Intel final 02 — 17/11/2026

PyInstaller reconstruyó `RedHouse.app` con las fuentes finales de escritorio, incluidas las correcciones de colecta/selectores, revisión de conservación y formularios, y las fechas locales/amplitud del motivo del traslado. **Build y smoke terminaron con salida 0.** Dirección abrió e inspeccionó la [ventana real del ejecutable empaquetado](login-packaged.png): cuenta, contraseña, foco visible y botón legibles, sin recortes ni campo gateway. No se inició sesión ni se ejecutó otra operación de negocio.

| Criterio | Resultado del artefacto 02 |
|---|---|
| Fuentes estables | 163 archivos comparados sin cambios durante el empaquetado |
| Contratos embebidos | 59 archivos idénticos a sus propietarios/copia de cliente |
| Smoke del ejecutable | Ventana creada, `login.xsd` cargado y `ok=true` |
| Cierre del proceso visible propio | Cerrado después de capturar; salida −15 por terminación deliberada, sin autenticación |
| Integridad del ZIP | 1.629 entradas, cero errores CRC |
| Nombres de configuración privada buscados | Ninguna coincidencia en el control documentado; no equivale a demostrar ausencia de cualquier secreto por contenido |

El ZIP privado `.local/dist/RedHouse-macOS-x86_64-20261117-02.zip` ocupa **56.632.855 bytes** y tiene SHA-256 `c8d648fd905b45dacbe273bce0b1940172dd18fef903960a82e4d7f49bd88d30`. El ejecutable tiene SHA-256 `8fa8dc9c3ea6b754688cff8a3590d2eab4bc2d2a194d94d27f054518423f5b8e`. El [resumen](resumen.json) conserva hashes de fuentes relevantes y de los recibos privados originales.

## Contratos y fallo previo conservado

La comprobación previa inicialmente falló porque `quality_review.xsd`, ya existente y utilizado por el cliente, no estaba incluido en el mapa de `sync_contracts.py`. Dirección añadió únicamente la correspondencia con su propietario; la comprobación posterior confirmó 59 contratos sin diferencias. El fallo inicial queda conservado en el recibo privado de preparación y resumido aquí. No se cambió el contrato de negocio ni se reescribe ese fallo como un primer intento aprobado.

## Reproducción y límites

Se reutilizó el procedimiento de Python 3.12/PyInstaller con `--windowed --onedir --collect-all keyring`, contratos mediante `--add-data`, salida nueva y smoke `--smoke-report`. Script, snapshots y control de contratos están en `.local/artifacts/desktop/final-package-20261117-02/`; compilación, smoke y captura originales permanecen en `/private/tmp/redhouse-desktop-20261117-final-02/evidence/`. El [paquete anterior](../paquete-macos-20261117/RESULTADOS.md), sus 160 fuentes/58 contratos y hash siguen como corte histórico independiente.

Esta evidencia acredita reconstrucción y arranque/UI del artefacto final en macOS Intel. Se retienen los ensayos funcionales aplicables del código; no se presentan como repetidos desde el paquete. No acredita instalación limpia sin herramientas del repositorio, otro recorrido transaccional empaquetado, Windows 11, Apple Silicon, Linux, notarización ni impresión física. Los pendientes de accesibilidad y distribución mantienen su alcance propio; no se cierra toda la etapa 05/07 por compilar.
