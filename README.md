# Red House

Red regional de bancos de sangre y donación de órganos · Proyecto 6 · Equipo 01.

Este incremento implementa únicamente el **monolito web del primer parcial**, con Flask, Jinja2 y PostgreSQL. Opera con datos ficticios y no realiza decisiones clínicas. Las pantallas futuras están identificadas y sus acciones permanecen deshabilitadas.

## Organización actual

```text
Red-House/
├── apps/
│   └── web-monolito01/
│       ├── src/
│       │   ├── presentation/     # Rutas HTTP, Jinja2, CSS, JS y recursos visuales
│       │   ├── business/         # Autorización, validaciones y casos de negocio
│       │   ├── data_access/      # Conexiones, repositorios y consultas parametrizadas
│       │   ├── config/           # Configuración desde variables de entorno
│       │   └── cli.py           # Inicialización y carga académica explícitas
│       ├── scripts/
│       │   └── setup_local.py  # Preparación local compartida por ambos sistemas
│       ├── tests/
│       ├── .env.example
│       ├── requirements.txt
│       ├── requirements-dev.txt
│       ├── setup.sh            # Instalador para macOS/Linux
│       ├── setup.cmd           # Instalador para Windows
│       ├── run.py
│       └── README.md
├── data/
│   └── database/
│       ├── schema.sql           # Única definición física del subconjunto web
│       └── README.md
├── documentation/
│   ├── markdowns/               # Fuentes editables de análisis y planificación
│   ├── docx/                    # Entregables Word
│   └── database-diagrams/      # Etapas 0FN–4FN y trazabilidad
│       └── normalization/      # Especificación y verificadores del modelo
├── .gitignore
├── AGENTS.md                    # Requisitos permanentes
└── PROJECT_STATUS.md            # Avance comprobado y pendientes
```

`apps/`, `data/` y `documentation/` son directorios hermanos dentro de este repositorio. `data_access` usa la convención de nombres de paquetes Python para la capa de acceso a datos. No se crearon carpetas vacías para microservicios, móvil, escritorio, paquetes compartidos o infraestructura futura.

## Inicio rápido

Con Python 3.12+ y PostgreSQL 14+ ya instalado y encendido, entra a `apps/web-monolito01` y ejecuta **`sh setup.sh` en macOS/Linux** o **`.\setup.cmd` en Windows**. El asistente prepara el entorno Python, la configuración privada, una base nueva, el esquema y las cuentas DEMO. Si ya existe una instalación válida, conserva sus datos y contraseñas. La prueba nativa de Windows fue realizada por otros integrantes del equipo, según confirmación del usuario recibida el 6 de septiembre de 2026. El entorno virtual de este Mac ya se reconstruyó en la ruta actual de `Red-House` y su arranque quedó verificado; no es necesario reinstalar ni reinicializar la base existente.

Después solo ejecuta **`python run.py`** (o `python3 run.py` en macOS/Linux) desde esa carpeta y abre <http://127.0.0.1:5050>, salvo que hayas elegido otro puerto. No necesitas activar el entorno virtual. El instalador no instala ni inicia PostgreSQL.

- [Instalar, ejecutar y probar el monolito](apps/web-monolito01/README.md).
- [Entender el esquema físico y sus límites](data/database/README.md).
- [Consultar el avance real](PROJECT_STATUS.md).
- [Consultar el análisis del problema](documentation/markdowns/Analisis_del_problema.md).
- [Revisar la normalización documental](documentation/database-diagrams/Modelo_4FN.md).

El diseño adapta el ZIP de referencia `Blood_and_Organ_Donation_Platform (1).zip` a plantillas Jinja2, sin incorporar una segunda aplicación React. Ese ZIP y los modelos sustituidos se conservan como antecedentes en el repositorio de origen; no son dependencias de ejecución ni archivos incluidos en esta selección documental.
