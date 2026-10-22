# Portal web

[Auditoría, seguimiento de hallazgos y errores accesibles de formularios](../../documentation/markdowns/Auditoria_y_formularios.md): comportamiento, permisos, límites y migración necesaria para instalaciones existentes.

Flask/Jinja2 presenta los procesos regionales. `BACKEND_MODE=monolith` ejecuta módulos de aplicación propios mediante WSGI y sus workers; no requiere listeners de las API. `microservices` consume HTTP. Ambos usan las mismas reglas versionadas, JWT, Redis y credenciales por propietario. El backend se selecciona antes de operar; no se cambia tras una escritura fallida. Las sesiones técnicas cifradas y las concesiones de renovación usan Redis con TTL. PostgreSQL conserva las marcas de cierre y las revocaciones pendientes en `web_runtime.session_revocations`.

Desde la raíz del repositorio: `bash install.sh`, después `bash start.sh`. Para operar solo el portal: `bash components.sh web`. El modo modular requiere PostgreSQL y Redis y las dependencias particulares de cada operación; el modo HTTP requiere además las API correspondientes.

- `src/integration/`: adaptador modular/HTTP, sesiones, formularios, rutas y archivos privados GCS.
- `src/presentation/`: plantillas, recursos y formatos compartidos.
- `src/access.py`: tipos de identidad y errores del portal.
- `src/config/`: configuración por entorno.
- `scripts/run_web.py` y `scripts/session_worker.py`: procesos del portal.
- `tests/`: recorridos de navegador. Las pruebas HTTP integradas están en `../services/tests/`.

[Instalación](../../documentation/markdowns/Instalacion_y_operacion.md) · [Arquitectura](../../documentation/markdowns/Arquitectura.md).

Docker: [instalación y operación](../../deployment/README.md), con portal en `http://127.0.0.1:6050`. El backend modular usa una copia fijada de los módulos `apps/services`, sin copiar reglas en JavaScript ni compartir sesiones internas del portal con las API. Los módulos conservan conexiones limitadas por servicio; Android y escritorio futuros utilizarán exclusivamente las API JSON/XML.
