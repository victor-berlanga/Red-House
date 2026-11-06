# Documentos y reportes

Propietario independiente BE-19/BE-20, versión 0.4.1, puerto 5112 (6112 por Compose local). API, worker e imagen propios. Datos: vistas de `stored_file`, `document_metadata`, `file_scans`, `export_jobs`; colas técnicas filtradas. No necesita MongoDB.

Los sujetos se autorizan mediante su propietario y JWT delegado. GCS almacena objetos privados; generación, SHA-256 y análisis ClamAV limpio son requisitos de descarga. El worker crea PDF/CSV/XLSX con nombres deterministas y recuperación idempotente.

Contratos JSON/XML/XSD en `contracts/`; configuración, decisiones y migración 013 en [documentación correctiva](../../../documentation/entrega-final/backend/correccion/Arquitectura_y_decisiones.md). Las rutas v1 documentales de Transporte delegan una sola vez al nuevo propietario.

Instalación: dependencias `requirements-storage.txt`, configuración propia con SQL/Redis/JWT/clave de servicio, GCS y ClamAV. `run.py documentos --config RUTA` y `worker.py documentos --config RUTA` ejecutan procesos separados. `Dockerfile` empaqueta este dominio y utilidades técnicas. `/health/storage` comprueba GCS; la ausencia de motor nunca se interpreta como análisis limpio.
