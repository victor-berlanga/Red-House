# Distribución de la consola de escritorio

## Alcance

La entrega usa Python 3.12, PySide6 y PyInstaller. Cada ejecutable se construye en su plataforma: no se presenta el paquete macOS como instalable en Windows. El flujo [desktop.yml](../../../.github/workflows/desktop.yml) prepara cuatro destinos y conserva cada resultado por separado.

| Destino | Entorno de CI | Artefacto | Límite de aceptación |
| --- | --- | --- | --- |
| Windows x64 | `windows-2025` | ZIP con ejecutable y dependencias | El runner es Windows Server; no sustituye el ensayo en el Windows 11 del equipo |
| macOS Intel | `macos-15-intel` | TAR.GZ con `RedHouse.app` | Requiere comprobar apertura, permisos y tareas en el equipo de destino |
| macOS Apple Silicon | `macos-15` | TAR.GZ con `RedHouse.app` | Construcción separada; no se declara binario universal |
| Linux x64 | `ubuntu-24.04` | TAR.GZ con ejecutable y dependencias | Objetivo adicional; no certifica otras distribuciones ni sistemas con bibliotecas anteriores |

Los nombres y arquitecturas de runners proceden de la [referencia de GitHub Actions](https://docs.github.com/en/actions/reference/runners/github-hosted-runners). Qt 6.10 contempla macOS 13 o posterior, Windows 11 y Ubuntu 24.04 entre sus plataformas; esto describe la biblioteca y **no acredita** esos destinos para Red House. [Plataformas de Qt 6.10](https://doc.qt.io/qt-6.10/supported-platforms.html).

## Comprobaciones del flujo

1. Comprobar que las treinta copias de contratos coinciden con sus propietarios mediante `sync_contracts.py --check`. El flujo también se activa al cambiar contratos del servidor.
2. Crear un entorno Python aislado e instalar las dependencias directas fijadas de la consola y del empaquetador.
3. Ejecutar pruebas de contratos, diario cifrado, descarga, rastreo e interacción Qt sin red. Excluir explícitamente el laboratorio de servicios reales, que tiene su propia preparación y evidencia.
4. Construir mediante `build.bat` o `build.sh`.
5. Arrancar el ejecutable distribuible con `--smoke-report`: crear ventana, procesar eventos y cargar los contratos incluidos. El proceso no inicia sesión ni accede a servicios o al llavero.
6. Conservar JUnit, resultado de arranque, versión del runner/Python, dependencias resueltas, commit y SHA-256 del archivo distribuible. Si una etapa falla, el trabajo falla y conserva los informes disponibles.

Qt usa la plataforma `offscreen` en CI. Ese arranque comprueba carga y recursos, **no** legibilidad, interacción del usuario, accesibilidad, impresión física, permisos del llavero ni integración con el sistema de ventanas. Estas comprobaciones requieren el recorrido nativo y las capturas reales del producto.

Los paquetes de CI no constituyen distribuciones firmadas/notarizadas para terceros. Las dependencias transitivas se registran por ejecución; el bloqueo transitivo disponible de macOS no se atribuye a Windows o Linux. Los artefactos se conservan catorce días en Actions.

## Estado comprobado al 13/11/2026

Workflow preparado; YAML y sus tres bloques Python analizados localmente. Treinta contratos comparados sin diferencias. No se ha ejecutado Actions ni se atribuye éxito a sus cuatro destinos. El paquete macOS Intel se reconstruyó después de seguridad, custodia, descarga y corrección de impresión; su ejecutable pasó la comprobación de arranque/recursos. Los ensayos XML reales y de interfaz existentes figuran en [evidencia de escritorio](../../evidencias/entrega-final/desktop/).

Para reclamar cada destino deben existir su trabajo CI aprobado, artefacto identificado y recorrido de aceptación correspondiente. Windows 11 conserva además la comprobación en el equipo disponible del usuario.

## Actualización con evidencia local — 17/11/2026

El paquete [macOS Intel actualizado](../../evidencias/entrega-final/desktop/paquete-macos-20261117/RESULTADOS.md) se construyó con las fuentes vigentes, incluidos mapas, reportes y analítica. Compilación y smoke terminaron con salida 0; 160 fuentes se mantuvieron estables, 58 contratos embebidos coincidieron con sus originales y la ventana de login empaquetada se abrió e inspeccionó. El ZIP pasó CRC completo. Esto acredita el arranque/UI del artefacto en macOS Intel, sin iniciar sesión ni ejecutar un proceso de negocio desde el paquete.

Este resultado local no equivale a ejecutar el workflow de Actions ni a aceptar todos los destinos. No prueba Windows 11, macOS Apple Silicon, Linux, notarización/distribución firmada, impresión física ni el proceso funcional en el paquete. La accesibilidad completa de escritorio permanece pendiente según la [matriz de escritorio](../../evidencias/entrega-final/desktop/MATRIZ.md). Los resultados del 13/11 siguen como antecedente, no se reescriben como ejecución de CI.
