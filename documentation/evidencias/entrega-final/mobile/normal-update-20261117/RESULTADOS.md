# Actualización iOS normal — 17/11/2026

`devicectl` actualizó `org.redhouse.mobile` en el iPhone 16 Pro autorizado con salida 0. El ejecutable coincide con SHA-256 `ad7be1cf71d445eb661fdcea293057a3221435981f1e3d6027c1d844b4e9a6cd`; firma estricta verificada antes de instalar. Se reutilizó el paquete ya compilado con origen GCP `https://34.18.186.116`, sin CA de laboratorio.

El perfil renovado vence el **24/11/2026 a las 18:03:31 UTC** y cubre el día 23. Sustituye la firma instalada que vencía el 17. La operación fue actualización, sin desinstalación ni borrado explícito del contenedor/Keychain. No se inició la app ni se introdujeron credenciales, por lo que restauración de sesión y recorrido de esta variante siguen sin verificar. Lab permanece separada.

[Resumen del artefacto y operación](resumen.json). No se repitieron builds ni pruebas por la instalación.
