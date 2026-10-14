# Reorganización del 14 de octubre de 2026

## Resultado y criterios de aceptación

- `apps/web/` reemplaza el nombre anterior del portal; lanzadores, herramientas, requisitos, pruebas y CI apuntan a esa ruta.
- Se retiraron del ejecutable los repositorios SQL, rutas, instaladores y pruebas exclusivos del monolito. Se conservaron y reubicaron los tipos de acceso y recursos usados por la integración. La web solo acepta `BACKEND_MODE=microservices`.
- `documentation/markdowns/` contiene análisis, planificación y guías vigentes; `docx/` conserva las ediciones semestrales y `database-diagrams/` el diseño lógico. `historial/primer-parcial/` identifica los esquemas SQL, guías y reporte Word/PDF del monolito anterior. Los resultados y capturas de integración quedaron dentro del historial, sin carpeta independiente de evidencias. Se consolidaron cuatro capturas idénticas.
- `data/database/README.md` enlaza al SQL de cada propietario. Las migraciones se conservan porque se necesitan para instalar y actualizar bases reales.
- `stuff/presentacion/` reemplaza la carpeta temporal anterior; el generador usa la nueva ruta. No se crearon carpetas vacías para móvil, escritorio o infraestructura futura.
- Las etiquetas redundantes se retiraron de mensajes, código corriente, contratos, documentos editables y ejemplos. El código de eritrocitos es `RBC`; los algoritmos conservan sus límites clínicos y reglas, con identificadores sin el sufijo anterior.
- Las únicas referencias textuales al identificador anterior en el código activo son las condiciones de las migraciones y su prueba: son necesarias para reconocer instalaciones previas. Los historiales firmados y capturas originales no se reescriben para cambiar etiquetas. No se afirma haber borrado contenido del historial de Git.

## Persistencia y transición

El entorno detenido se copió a `.local/runtime/` mediante `relocate.py`; el origen se conservó como respaldo. Se actualizaron rutas de configuración y del entorno virtual web, sin publicar credenciales. `upgrade.py` respaldó cada base antes de aplicar las migraciones.

La comparación de 111 tablas no detectó pérdida de filas ni modificaciones fuera de componentes, versiones y caché previstos. Usuarios e historiales mantuvieron sus huellas. Posteriormente se normalizaron nombres administrativos y la etiqueta de procedencia de rutas mediante migraciones separadas, sin modificar auditoría ni cadenas de custodia.

Los registros siguen siendo ficticios y persistentes. Las migraciones incrementan versiones de registros modificados: una evaluación anterior puede exigir nueva revisión antes de crear una reserva. No se cambian decisiones clínicas ni se recargan expedientes.

En otros equipos, si el directorio predeterminado aún no existe pero hay otro entorno preparado bajo `.local`, el lanzador informa cómo seleccionarlo o trasladarlo. No crea automáticamente una base alternativa. El traslado local no certifica portabilidad de archivos físicos de bases entre sistemas operativos.

## Verificación

- Lanzador: 39 pruebas aprobadas, incluida protección frente a un entorno previo y rechazo de Homebrew en Linux. Además, [14 comprobaciones reales del ciclo de vida](resultados/lanzador.json) aprobaron instalación nueva, inicio parcial, reinicio, conflictos, bloqueo, recuperación y conservación de cuentas.
- Primera suite completa: 162 aprobadas y un fallo de aislamiento en una prueba que reutilizaba un donante previamente registrado. Se corrigió usando una cuenta e institución explícitas por prueba. Una repetición intermedia se interrumpió voluntariamente para completar esa corrección; no se presenta como suite aprobada.
- [Regresión final](resultados/regresion.xml): **164 pruebas aprobadas, cero fallos, errores u omisiones, en 597.68 s**. Incluye la cuenta de donante aislada, las migraciones definitivas, el rechazo de conexiones SQL históricas desde el portal y la protección del entorno anterior.
- Navegador Chrome: [51 visitas](resultados/navegador/report.json), siete perfiles, escritorio/móvil y alternativa sin JavaScript; cero errores registrados. Un primer intento agotó el tiempo al iniciar sesión; la comprobación directa posterior devolvió API 200 y web 302, y la repetición completa pasó. No se atribuye una causa no demostrada.
- Entorno conservado: [once servicios y portal con HTTP 200](resultados/entorno.json); seis instituciones, 108 donantes, 72 receptores/solicitudes, 216 unidades sanguíneas, 36 ofertas de órganos y 18 traslados. Las 18 cadenas de custodia verificaron sus hashes.
- [Conservación de tablas](resultados/persistencia.json). Los respaldos SQL y configuraciones privadas permanecen fuera de Git.
- Sintaxis Python/Bash, comprobaciones estáticas fatales y formato Ruff aprobados. Contratos JSON/XML/XSD parseados, enlaces locales Markdown resueltos y cinco BAT ASCII/CRLF comprobados. Word/Excel reabiertos como ZIP/XML válidos; no quedan etiquetas redundantes independientes en su texto XML.

## Recuperación y límites

El árbol anterior del código está en el commit `6abb3169b7c4f62282d46d058bb9ca66fd6b83c8`. También se conservó una copia local previa al retrabajo fuera del repositorio. El modo histórico no debe reinstalarse sobre las bases de los microservicios.

El reporte integral Word y PDF del monolito conserva su corte histórico; se actualizaron etiquetas textuales y se regeneró el PDF desde el Word. Las capturas antiguas mantienen su contenido original. No representan la interfaz actual.

Windows nativo, ejecución real de BAT/WSL en Windows, Linux/Ubuntu completo, CI remoto, GCS real, Docker y GCP siguen sin certificarse en este incremento. El portal continúa disponible en `http://127.0.0.1:5050`.


## Corrección de clasificación documental

Se revisaron el propósito, cobertura, encabezados y referencias de los 16 Markdown archivados, las 12 ediciones Word y los modelos de normalización. La fecha de elaboración no es un criterio suficiente para archivar documentación del semestre.

- Se restituyeron once fuentes Markdown de análisis, requisitos, historias, casos de uso, trazabilidad, permisos, reglas, tecnologías, arquitectura objetivo, plan y backlog, junto con sus once ediciones Word.
- Se restituyeron seis documentos de normalización y sus cuatro módulos de generación/validación en `documentation/database-diagrams/`. Representan diseño lógico académico; el SQL físico vigente sigue perteneciendo a cada servicio.
- Permanecen en el historial las cinco guías/reglas/pruebas/plan específicos del monolito, su SQL, el reporte integral y sus recursos visuales. En particular, ORGAN-1.0 describe las condiciones de aquella implementación; las reglas actuales se consultan en Algoritmos y en el código de los servicios.
- Se sustituyeron avisos desactualizados en las once fuentes y sus Word. Los estados del backlog quedaron expresamente identificados con su corte original. No se cambiaron requisitos, reglas clínicas, fechas originales ni se declaró cumplido el alcance pendiente.
- Se actualizaron índices, rutas, referencias y estado del proyecto. Markdown mantiene las fuentes editables; las ediciones Word no se presentan como exportaciones completamente sincronizadas.

**Aceptación y comprobaciones:** 32 archivos restituidos; enlaces locales Markdown sin destinos inexistentes; once Word con ZIP/XML íntegros y aviso revisado. Validador de normalización aprobado: 169 relaciones, 918 atributos, 208 atributos de origen y 49 diagramas Mermaid. El primer intento detectó diferencias de notación en enlaces relativos (`./`); se ajustaron los documentos generados a su fuente y la repetición pasó. No se modificaron aplicaciones, configuración ni datos de ejecución en esta corrección. No se repitió la regresión del sistema para cambios exclusivamente documentales; no se realizó revisión visual página por página de Word.
