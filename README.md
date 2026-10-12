# Red House

Red regional de bancos de sangre y donación de órganos · Proyecto 6 · Equipo 01.

El portal web Flask/Jinja2 ya opera mediante los **diez microservicios y Monitoreo**: donantes, inventario, solicitudes, revisión humana, compatibilidad DEMO, reservas, traslados, custodia, alertas y auditoría. La instalación activa contiene datos ficticios de seis instituciones de Nuevo León, con PostgreSQL, Redis y MongoDB reales. [Arranque, acceso, demostración y arquitectura](apps/web-monolito01/INTEGRACION.md).

El módulo separado de órganos cubre riñón, hígado y corazón: estudios/HLA documentales, preselección demostrativa, dictamen humano, reserva, traslado y custodia. El motor ABO/Rh sanguíneo cubre concentrados eritrocitarios; ambos procesos requieren revisión clínica.

El módulo independiente de [microservicios](apps/services/README.md) mantiene API JSON/XML, JWT y Redis, PostgreSQL, MongoDB y Swagger. La web los consume por HTTP y sus sesiones no sustituyen la autorización de las API. Resultados actuales en [VALIDACION](apps/services/docs/VALIDACION.md). Móvil, escritorio, Docker y GCP permanecen posteriores. [Apuntes TXT para presentación](stuff/temporal-microservicios/00-LEER-PRIMERO.txt).

## Arranque local

```bash
bash instalar.sh                    # Preparar dependencias/configuración
bash iniciar.sh                     # Iniciar todo, sin revisar paquetes
bash componentes.sh                 # Menú para elegir componentes
bash componentes.sh inventario      # Una API y su worker
bash componentes.sh ms              # Todas las API y workers
bash componentes.sh web             # Solo la web integrada
bash componentes.sh estado
bash componentes.sh detener todo
```

Instalación separada del arranque: conserva los datos de `.local/demo` y recupera procesos faltantes. El instalador automático es para macOS; MongoDB permanece en `.local/tools`. [Guía de opciones, requisitos y solución de errores](apps/services/docs/ARRANQUE_LOCAL.md).

## Entrega consolidada

- [Reporte Técnico Integral Red House — Word](documentation/docx/Reporte_Tecnico_Integral_Red_House.docx).
- [Reporte Técnico Integral Red House — PDF](documentation/pdf/Reporte_Tecnico_Integral_Red_House.pdf).
- [Guía del flujo regional](documentation/markdowns/Guia_del_flujo_regional.md).
- [Guía de órganos y HLA](documentation/markdowns/Guia_del_flujo_de_organos.md).
- [Capturas reales por requisito](documentation/capturas/README.md).

El reporte integral conserva el corte histórico del monolito. El estado vigente de servicios e integración está en [PROJECT_STATUS.md](PROJECT_STATUS.md) y en la [revisión del 8 de octubre](apps/services/docs/REVISION_2026_10_08.md), con sus pruebas y límites. Los documentos especializados se conservan como fuentes de detalle.

## Organización actual

```text
Red-House/
├── apps/
│   ├── services/              # Diez microservicios, monitoreo, contratos y pruebas
│   └── web-monolito01/
│       ├── src/
│       │   ├── presentation/     # Rutas HTTP, Jinja2, CSS, JS y recursos visuales
│       │   ├── integration/      # Cliente HTTP, sesiones cifradas y rutas del portal integrado
│       │   ├── business/         # Autorización común y negocio histórico del modo local
│       │   ├── data_access/      # Repositorios históricos; no se usan en modo integrado
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
│       ├── schema.sql           # Esquema inicial; ampliación en migrations/
│       └── README.md
├── documentation/
│   ├── markdowns/               # Fuentes editables de análisis y planificación
│   ├── docx/                    # Entregables Word
│   └── database-diagrams/      # Etapas 0FN–4FN y trazabilidad
│       └── normalization/      # Especificación y verificadores del modelo
├── .gitignore
├── stuff/temporal-microservicios/ # Un TXT de presentación por servicio
├── AGENTS.md                    # Requisitos permanentes
└── PROJECT_STATUS.md            # Avance comprobado y pendientes
```

`apps/`, `data/`, `documentation/` y `stuff/` son directorios hermanos dentro de este repositorio. `data_access` usa la convención de nombres de paquetes Python para la capa de acceso a datos. `apps/services` contiene componentes ejecutables; móvil y escritorio conservan su implementación posterior.

## Inicio rápido

**Instalación integrada actual:** abrir <http://127.0.0.1:5050>. Para iniciar o detener web, servicios y sus dependencias conjuntamente, seguir la [guía de integración](apps/web-monolito01/INTEGRACION.md). Las ocho cuentas anteriores conservan sus contraseñas. El `.env` habitual ya apunta al nuevo entorno; no ejecutar el instalador histórico ni reinicializar bases para arrancarlo.

Los procedimientos siguientes corresponden al modo histórico `BACKEND_MODE=local`; no provisionan los microservicios.

**Instalación existente:** la actualización local del 13 de septiembre ya aplicó la migración con respaldo y comprobación en copia; conserva las cuatro cuentas y 36 unidades anteriores. En otras instalaciones existentes, ejecutar `.venv/bin/python -m flask --app run migrate-db` después de respaldar y actualizar el código. No volver a ejecutar `schema.sql` sobre una base instalada. La aplicación no migra al arrancar.


Con Python 3.12+ y PostgreSQL 14+ ya instalado y encendido, entra a `apps/web-monolito01` y ejecuta **`sh setup.sh` en macOS/Linux** o **`.\setup.cmd` en Windows**. El asistente prepara el entorno Python, la configuración privada, una base nueva, el esquema y las cuentas DEMO. Si ya existe una instalación válida, conserva sus datos y contraseñas. La prueba nativa de Windows fue realizada por otros integrantes del equipo, según confirmación del usuario recibida el 6 de septiembre de 2026. El entorno virtual de este Mac ya se reconstruyó en la ruta actual de `Red-House` y su arranque quedó verificado; no es necesario reinstalar ni reinicializar la base existente.

Después solo ejecuta **`python run.py`** (o `python3 run.py` en macOS/Linux) desde esa carpeta y abre <http://127.0.0.1:5050>, salvo que hayas elegido otro puerto. No necesitas activar el entorno virtual. El instalador no instala ni inicia PostgreSQL.

- [Instalar, ejecutar y probar el monolito](apps/web-monolito01/README.md).
- [Entender el esquema físico y sus límites](data/database/README.md).
- [Consultar el avance real](PROJECT_STATUS.md).
- [Consultar el análisis del problema](documentation/markdowns/Analisis_del_problema.md).
- [Revisar la normalización documental](documentation/database-diagrams/Modelo_4FN.md).

El diseño adapta el ZIP de referencia `Blood_and_Organ_Donation_Platform (1).zip` a plantillas Jinja2, sin incorporar una segunda aplicación React. Ese ZIP y los modelos sustituidos se conservan como antecedentes en el repositorio de origen; no son dependencias de ejecución ni archivos incluidos en esta selección documental.
