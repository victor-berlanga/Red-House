# Diagnóstico seguro de cámara — 13/11/2026

Durante la preparación del laboratorio Android se utilizó por error el token de la consola local como credencial gRPC. La excepción del helper privado mostró ese valor en un diagnóstico. No era una credencial de Red House, GCP ni una cuenta del equipo. No se reproduce aquí el valor ni su huella.

Se corrigió `apps/mobile/tests/aim_virtual_camera.py`: ante errores gRPC muestra únicamente el código; ante otros errores muestra un mensaje fijo. El canal se cierra en `finally`. Se aplicó el mismo límite al helper privado empleado durante el ensayo, con comprobación de sintaxis y sin ejecutar llamadas a un emulador. No se cambiaron los parámetros ni el protocolo de cámara.

La prueba del helper versionado inyecta una excepción que contiene una credencial sintética y verifica salida sin el valor ni detalles del servidor, código de salida 1 y cierre del canal. **1/1 aprobada**, 0,713 s según JUnit; tiempo de pared del comando observado: 1,61 s. Después se corrigieron únicamente el espaciado de imports y la anotación del límite de excepciones para Ruff; análisis estático aprobado. [JUnit](junit.xml), con nombre del equipo omitido, y [fuentes finales](fuentes.sha256). No acredita lectura QR ni operación gRPC real.

Reproducción local, sin red ni emulador:

```sh
apps/services/.venv/bin/python -m pytest apps/mobile/tests/test_camera_diagnostics.py -q
apps/services/.venv/bin/python -m ruff check apps/mobile/tests/aim_virtual_camera.py apps/mobile/tests/test_camera_diagnostics.py
```

Tras cerrar los emuladores propios se verificó que no hubiera procesos de emulador ni dispositivos emulados registrados. Se renovó atómicamente el token local de consola: archivo regular del usuario, permisos 0600 y propietario conservados; comprobación de identidad del archivo antes de reemplazarlo. No se imprimió ni conservó copia del valor anterior o nuevo. [Resultado mínimo](rotacion.json). La renovación evita reutilizar ese valor en futuros arranques; no retira el diagnóstico previo del historial. No se modificaron credenciales del producto.

El intento óptico de custodia y los demás recorridos de la etapa 04 conservan sus resultados separados. Este cambio corrige exclusivamente el manejo de errores de la herramienta de diagnóstico.
