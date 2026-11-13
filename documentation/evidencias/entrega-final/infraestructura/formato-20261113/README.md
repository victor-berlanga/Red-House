# Formato reproducible del backend

La comprobación de formato exigida por el workflow existente detectó fuentes sin normalizar. Se aplicó Ruff exclusivamente a los 274 archivos Python versionados bajo `apps/services` y `apps/web/src/integration`; 56 cambiaron. Los archivos móviles y de escritorio no forman parte de este incremento.

[Verificación](verificacion.json): versión exacta de Ruff, SHA antes/después y comparación del árbol sintáctico Python sin posiciones. Los 274 árboles permanecieron idénticos; los hashes anteriores de los 56 archivos modificados coinciden con `9b04a90`. El cambio no modifica operaciones, constantes, contratos ni dependencias. Las evidencias funcionales anteriores conservan sus hashes originales; no se presentan como nuevas ejecuciones.

Reproducción desde la raíz, con el entorno de servicios instalado:

```sh
apps/services/.venv/bin/python -m ruff check --select E9,F63,F7,F82 apps/services apps/web/src/integration
apps/services/.venv/bin/python -m ruff format --check apps/services apps/web/src/integration
```

El análisis estático pasó. El formato de archivos no versionados de trabajos posteriores se revisa con sus propios cambios. Esta corrección no acredita ejecución remota de CI.
