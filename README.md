# Red House

Red regional de bancos de sangre y donación de órganos · Proyecto 6 · Equipo 01.

Portal Flask/Jinja2 con backend modular autónomo y diez microservicios más Monitoreo. El modo HTTP sigue disponible mediante configuración explícita. PostgreSQL mantiene una base persistente compartida (`red_house`), con permisos por servicio; Redis mantiene sesiones y caché; MongoDB conserva documentos y proyecciones. Los datos locales son ficticios. Las reglas de compatibilidad requieren revisión humana y no sustituyen decisiones clínicas.

El sistema desplegado está disponible en **https://34.18.186.116**. Todo se ejecuta en GCP; no requiere iniciar nada localmente. [Guía de acceso y administración](deployment/gcp/README.md).

## Instalación y ejecución local opcional

```bash
bash install.sh                 # Preparar dependencias y un entorno persistente
bash start.sh                   # Iniciar la plataforma preparada
bash components.sh estado      # Consultar disponibilidad
bash components.sh inventario  # Iniciar un servicio y su worker
bash stop.sh                    # Detener sin borrar datos
```

En Windows, los pares `.bat` ejecutan estos comandos mediante WSL/Ubuntu; no son un port nativo. En Ubuntu deben instalarse previamente Python 3.12+ con venv, PostgreSQL 14 para instalaciones nuevas, Redis 7+ y MongoDB 8.0. La instalación automática de paquetes del sistema solo está implementada para macOS.

[Requisitos, configuración y recuperación](documentation/markdowns/Instalacion_y_operacion.md).

La VM conserva una copia independiente de los datos del Docker de demostración. El entorno local quedó detenido; sus archivos y respaldos se conservan.

## Organización

```text
apps/web/                  Portal con backend modular o cliente HTTP
apps/services/             Microservicios, migraciones, contratos y pruebas
scripts/                   Gestión conjunta del entorno
data/database/            Esquema SQL compartido y referencias del origen
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

El backend web monolítico anterior se retiró del código ejecutable. Sus guías de operación y resultados están identificados en el historial; el análisis y la planificación del semestre permanecen en las carpetas documentales por formato; su código permanece recuperable mediante Git. Android y escritorio quedan fuera del segundo parcial. Docker, GCS privado y la VM GCE con acceso público por IP y HTTPS están implementados; operación productiva y redundancia siguen pendientes.

La [base compartida basada en main](documentation/markdowns/Esquema_compartido.md) conserva las 45 tablas heredadas y agrega 26 para los contratos actuales. Las instalaciones nuevas la utilizan directamente; los entornos anteriores deben ejecutar el migrador documentado, con respaldo y comprobación de filas, antes de iniciar esta versión.

## Segundo parcial

[Reporte integral](documentation/markdowns/Reporte_tecnico_segundo_parcial.md) · [Matriz de cumplimiento](documentation/markdowns/Cierre_segundo_parcial.md) · [Resultados verificables](documentation/evidencias/segundo-parcial/RESULTADOS.md) · [Docker](deployment/README.md) · [Guion de demostración](stuff/presentacion/Guion_segundo_parcial.md).

El Compose usa `.local/compose`, volúmenes propios y puertos 6050/6101–6111. Mantiene dos instancias por API y workers supervisados. No monta los archivos físicos de `.local/runtime`. El portal modular mantiene sus operaciones cuando las API están detenidas, siempre que sus dependencias compartidas estén disponibles.
