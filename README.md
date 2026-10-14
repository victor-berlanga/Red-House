# Red House

Red regional de bancos de sangre y donación de órganos · Proyecto 6 · Equipo 01.

Portal Flask/Jinja2 conectado por HTTP a diez microservicios y Monitoreo. PostgreSQL mantiene once bases persistentes, una por servicio; Redis mantiene sesiones y caché; MongoDB conserva documentos y proyecciones. Los datos locales son ficticios. Las reglas de compatibilidad requieren revisión humana y no sustituyen decisiones clínicas.

## Instalación y ejecución

```bash
bash install.sh                 # Preparar dependencias y un entorno persistente
bash start.sh                   # Iniciar la plataforma preparada
bash components.sh estado      # Consultar disponibilidad
bash components.sh inventario  # Iniciar un servicio y su worker
bash stop.sh                    # Detener sin borrar datos
```

En Windows, los pares `.bat` ejecutan estos comandos mediante WSL/Ubuntu; no son un port nativo. En Ubuntu deben instalarse previamente Python 3.12+ con venv, PostgreSQL 14 para instalaciones nuevas, Redis 7+ y MongoDB 8.0. La instalación automática de paquetes del sistema solo está implementada para macOS.

[Requisitos, configuración y recuperación](documentation/markdowns/Instalacion_y_operacion.md).

## Organización

```text
apps/web/                  Portal actual; consume las API
apps/services/             Microservicios, migraciones, contratos y pruebas
scripts/                   Gestión conjunta del entorno
data/database/            Mapa de bases; el SQL pertenece a cada servicio
documentation/markdowns/  Análisis, planificación y guías actuales
documentation/docx/       Ediciones de la documentación semestral
documentation/database-diagrams/  Diseño lógico y normalización
documentation/historial/  Entregas anteriores, bitácora y resultados de pruebas
documentation/excel/      Matrices de roles y trazabilidad
stuff/presentacion/        Apuntes generados para exposición
.local/runtime/            Datos, secretos y logs locales; fuera de Git
```

- [Estado comprobado y pendientes](PROJECT_STATUS.md).
- [Índice documental](documentation/README.md).
- [Arquitectura](documentation/markdowns/Arquitectura.md).
- [Datos y persistencia](documentation/markdowns/Datos_y_persistencia.md).
- [Microservicios y contratos](apps/services/README.md).
- [Portal web](apps/web/README.md).

El monolito SQL anterior se retiró del código ejecutable. Sus guías de operación y resultados están identificados en el historial; el análisis y la planificación del semestre permanecen en las carpetas documentales por formato; su código permanece recuperable mediante Git. Android, escritorio, Docker y despliegue en GCP siguen pendientes.
