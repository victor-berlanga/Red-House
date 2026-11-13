# Organización conservadora del repositorio — 13/11/2026

Se conservan `apps/web`, `apps/services`, `apps/mobile`, `apps/desktop`, `data`, `documentation` y `stuff`. La arquitectura recomendada en la imagen orienta la separación de responsabilidades; mover carpetas a nombres distintos no mejora por sí mismo esa separación y rompería rutas reproducibles. No se introduce otro frontend ni paquetes compartidos sin consumidores reales.

La inspección encontró cachés y artefactos locales voluminosos, pero también datos, respaldos, evidencia y herramientas bajo `.local`. No se eliminaron datos, evidencia histórica, contratos generados, scripts SQL ni el índice CodeGraph. Los logs versionados pertenecen a evidencia fechada y no se clasifican como basura por extensión.

Se amplió `.dockerignore` para excluir `build`, `dist`, `.gradle`, `.kotlin`, `DerivedData`, `xcuserdata`, `.DS_Store` y caché PyInstaller de todas las aplicaciones. Esto evita enviarlos como contexto de construcción o copiarlos en imágenes mediante COPY de carpetas completas. `.gitignore` ya excluía entornos Python, builds y distribuciones; se añadió la caché específica PyInstaller. No cambia los artefactos seleccionados guardados como evidencia o entrega fuera de esas carpetas.

Verificación: revisión de COPY en Dockerfiles y de los patrones de exclusión; `git diff --check`. No se atribuyen ahorros de bytes o tiempos de construcción sin medir un build Docker real.
