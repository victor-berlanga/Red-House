# Modelos y diagramas finales: preparación reproducible

Estado del 14/11/2026: captura READ ONLY completada después de cerrar carga: **esquema 20, 117 tablas incluyendo `web_runtime`, 226 índices y doce servicios**. Solo se inició PostgreSQL propio y se cerró en 2,744 s totales; `postmaster.pid` quedó ausente. El primer inicio falló dentro del sandbox por `shmat` antes de abrir la base; se conserva separado. [Metadatos](../../evidencias/entrega-final/modelos-20261114/postgresql-physical.json) y [operación/cierre](../../evidencias/entrega-final/modelos-20261114/captura-operacion.json). Builder y render ejecutados; informe de 24 páginas y catálogo de 74 en Word/PDF. El [registro editorial](../../evidencias/entrega-final/modelos-20261114/validacion-final.json) delimita controles e inspección. Este directorio es propio de entrega final; los archivos de `documentation/segundo-parcial/` permanecen históricos.

## Herramientas reutilizadas

`scripts/build_partial_docs.py` ya elaboraba catálogo físico, Mermaid de FK y fichas a partir de metadatos. Su nuevo modo `--final --metadata` conserva ese flujo, exige esquema 20/READ ONLY/doce propietarios y toma las vistas del catálogo instalado. El modo histórico sigue separado. No se aplica el generador SQL ni migraciones a una base para documentarla.

`scripts/capture_final_schema.py` añade la extracción que antes no estaba versionada. Lee únicamente catálogos de tablas/columnas/restricciones/índices/disparadores/dependencias de vistas y la versión técnica de migración. Usa una transacción READ ONLY/REPEATABLE READ; no lee expedientes, usuarios de negocio, tokens, roles personales ni filas de donantes. Verifica loopback, propietario del archivo privado y `data_directory` del fixture. No imprime DSN, no modifica `state.json` y no inicia ni detiene procesos.

`scripts/render_final_diagrams.cjs` adapta el render histórico Playwright/Mermaid. Reutiliza Chrome/Playwright ya presentes y el bundle Mermaid MIT incluido en la documentación local de ClamAV. No instala Mermaid CLI ni descarga navegadores. El bundle se puede indicar con `REDHOUSE_MERMAID_BUNDLE`; su SHA se conserva en `_render.json`. Ese resultado distingue generación de revisión visual. El directorio temporal antiguo de herramientas solo conserva restos de dependencias y no constituye una instalación Mermaid utilizable.

## Secuencia exacta tras liberar la ventana de carga

La captura requiere **solo el PostgreSQL propio de `/private/tmp/rh-load-c92ed10k` activo**. Si la serie ya lo cerró, dirección debe iniciarlo mediante el comando privado `infrastructure_commands.postgres` de su `state.json`, comprobando propiedad/directorio/puerto; conservar el PID recién creado y cerrarlo al terminar. No usar `Environment.init`, `ensure_infrastructure` o el arranque completo: no se necesitan Redis, MongoDB, API ni workers para capturar este catálogo. El script falla si PostgreSQL está cerrado y no intenta reiniciarlo.

Desde la raíz, después de esa preparación y fuera de la medición:

```sh
# Captura ya ejecutada: no repetir sobre el mismo archivo.
# Para una extracción nueva, indicar otro nombre y conservar el anterior.
apps/services/.venv/bin/python scripts/capture_final_schema.py \
  --fixture /private/tmp/rh-load-c92ed10k \
  --output documentation/evidencias/entrega-final/modelos-20261114/postgresql-physical.json

# No accede a la base: utiliza exclusivamente el JSON y contratos del repositorio.
apps/services/.venv/bin/python scripts/build_partial_docs.py --final \
  --metadata documentation/evidencias/entrega-final/modelos-20261114/postgresql-physical.json

# En otra ventana, después de cerrar PostgreSQL y los trabajos de clientes.
node scripts/render_final_diagrams.cjs documentation/entrega-final/modelos/diagramas

# Catálogo Word con nombre final propio; no incorpora la portada del informe.
.local/venv-docs/bin/python scripts/export_partial_report.py --final-physical
soffice --headless --convert-to pdf --outdir documentation/pdf \
  documentation/docx/Modelo_fisico_PostgreSQL_final.docx

# Informe final con su portada/índice y referencias actualizadas.
.local/venv-docs/bin/python scripts/export_partial_report.py --final --pdf
```

La sintaxis Python de los tres scripts se comprobó antes de iniciar la captura. El builder terminó con los conteos esperados. El primer render conservó dieciocho figuras y falló al analizar un punto y coma en una nota de secuencia; se corrigió únicamente ese texto y se repitió esa figura. Los ajustes posteriores de legibilidad/título se renderizaron por selección, sin repetir todos los diagramas. La primera conversión LibreOffice abortó en AppKit bajo sandbox; la misma fuente convirtió después con ejecución autorizada y perfil aislado. El índice del informe se estabilizó en dos pasadas. No se presentan esos intentos como ejecuciones iniciales sin fallos ni se sobrescribe la verificación editorial previa.

## Archivos editables y salidas que faltan

Están escritas cinco fuentes de detalle: `diagramas/componentes.mmd`, `despliegue.mmd`, `archivos.mmd`, `secuencia.mmd` y `datos.mmd`, más `archivos-resumen.mmd` y `secuencia-resumen.mmd` para lectura en papel. Representan doce propietarios, LOCAL principal/GCS opcional, revisión humana y límites de un host. `datos.mmd` es la vista conceptual de relaciones de negocio; sus flechas no afirman cardinalidades SQL. Las secuencias describen mecanismos, sin acreditar ejecución integral por aparecer en un dibujo.

El builder produjo `Modelo_fisico.md`, `Modelo_relacional.md`, `Fichas_microservicios.md`, `diagramas/postgresql-completo.mmd`, `modelo-relacional.mmd` y doce `postgresql-<propietario>.mmd`. `Modelo_conceptual.md` explica la vista de negocio. Las vistas por servicio muestran tablas referidas por sus vistas SQL y claves de contexto; **no declaran propiedad de escritura por el mero hecho de consultarlas**. Las tablas compartidas se repiten como referencias gráficas, no como copias físicas. Los modelos lógicos 0FN–4FN del semestre mantienen su origen y no se reescriben para aparentar el esquema actual.

Se generaron **21 SVG ampliables y siete PNG**. El informe imprime los dos resúmenes y la gráfica de carga; enlaza los diagramas amplios para conservar su legibilidad. El renderer evita rasterizar el catálogo físico completo como una imagen enorme. Los Word/PDF finales están en las carpetas existentes, con nombre propio; el registro editorial conserva hashes, paginación y alcance de inspección. Un archivo `_render.json` con estado GENERATED no constituye por sí solo aprobación editorial ni verificación clínica.

## Validación mínima del cierre

1. Sintaxis/formato de los tres scripts modificados y del renderer; CLI rechaza combinación de modos y destinos históricos. Sin suite funcional ni motores adicionales.
2. Captura: READ ONLY verdadero, versión 20, doce nombres de servicio, tablas únicas por esquema/nombre, columnas ordenadas, índices y FK con destino existente. Registro de inicio/cierre del único PostgreSQL propio. No conservar filas ni configuración privada en el JSON público.
3. Builder: conteos MD coinciden con JSON; `web_runtime` no se suma mediante cifras manuales antiguas; doce fichas y doce vistas gráficas de servicio; relaciones provienen de FK, no de nombres parecidos. Contratos/versiones se leen del árbol actual.
4. Mermaid: parse/render secuenciales, SVG íntegros y enlaces del catálogo válidos. Revisar visualmente vista completa ampliable, modelo relacional, una vista por servicio y las cinco figuras resumidas; no asumir legibilidad por obtener salida.
5. Word/PDF: ZIP íntegro, páginas/títulos/índice, tablas dentro de página, sin texto recortado, sin datos de portada históricos ni cifras de once servicios/71 tablas como si fueran actuales. Conservar manifiesto de fuentes/artefactos y revisar diferencias; no atribuir este cierre editorial a una nueva regresión de producto.

El informe final vincula este catálogo y sus resultados documentales. Los hashes identifican un corte, que no se reexporta por cada resultado futuro. Aprobación clínica, aceptación integrada de procesos y acciones humanas conservan su estado separado.
