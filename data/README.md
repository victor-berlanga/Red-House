# Datos del repositorio

Esta carpeta orienta sobre el modelo y los datos de prueba. No contiene bases físicas, credenciales ni una segunda copia de las migraciones.

[Mapa de bases](database/README.md). Los archivos privados del entorno se guardan en `.local/runtime/`, excluido de Git. La carga regional explícita está en `apps/services/scripts/seed_nuevo_leon.py`; nunca se ejecuta automáticamente al arrancar.
