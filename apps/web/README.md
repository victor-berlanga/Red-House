# Portal web

Flask/Jinja2 presenta los procesos regionales y consume exclusivamente las API de `apps/services`. No tiene repositorios PostgreSQL ni un modo SQL alternativo. La sesión técnica usa SQLite privado y cifrado; la autorización de negocio corresponde a las API y Redis.

Desde la raíz del repositorio: `bash install.sh`, después `bash start.sh`. Para operar solo el portal: `bash components.sh web`. Las operaciones requieren que sus microservicios estén disponibles.

- `src/integration/`: cliente HTTP, sesiones, formularios y rutas.
- `src/presentation/`: plantillas, recursos y formatos compartidos.
- `src/access.py`: tipos de identidad y errores del portal.
- `src/config/`: configuración por entorno.
- `scripts/run_web.py` y `scripts/session_worker.py`: procesos del portal.
- `tests/`: recorridos de navegador. Las pruebas HTTP integradas están en `../services/tests/`.

[Instalación](../../documentation/markdowns/Instalacion_y_operacion.md) · [Arquitectura](../../documentation/markdowns/Arquitectura.md).
