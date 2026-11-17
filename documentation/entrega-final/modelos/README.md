# Modelos y diagramas finales: preparación reproducible

Estado del 14/11/2026: captura READ ONLY completada después de cerrar carga: **esquema 20, 117 tablas incluyendo `web_runtime`, 226 índices y doce servicios**. Solo se inició PostgreSQL propio y se cerró en 2,744 s totales; `postmaster.pid` quedó ausente. El primer inicio falló dentro del sandbox por `shmat` antes de abrir la base; se conserva separado. [Metadatos](../../evidencias/entrega-final/modelos-20261114/postgresql-physical.json) y [operación/cierre](../../evidencias/entrega-final/modelos-20261114/captura-operacion.json). Builder y render ejecutados; informe de 24 páginas y catálogo de 74 en Word/PDF. El [registro editorial](../../evidencias/entrega-final/modelos-20261114/validacion-final.json) delimita controles e inspección. Este directorio es propio de entrega final; los archivos de `documentation/segundo-parcial/` permanecen históricos.

## Actualización comprobada al esquema 21 — 17/11/2026

La [captura READ ONLY del 17/11](../../evidencias/entrega-final/modelos-20261117/postgresql-physical.json) aprobó sobre la instancia propia: **esquema 21, 117 tablas, 227 índices y doce servicios**. Solo se inició PostgreSQL; terminó cerrado, sin `postmaster.pid`, y `state.json` conservó sus bytes. Captura con salida 0 y 2,043 s totales, según el recibo privado conservado por dirección en `.local/artifacts/documentation/schema21-run-20261117/receipt.json`. El metadata público tiene SHA-256 `25715b794be3630b7b11bd8720f7228af217c9fdde24cee3e02414c29707160d`; no contiene filas de negocio ni credenciales.

El builder final también terminó con salida 0 y actualizó el catálogo físico, la vista relacional y las fichas a partir de esa captura real. Frente al corte 20, el catálogo conserva 117 tablas y añade únicamente el índice parcial `shared_outbox_dispatch_order` sobre `red_house.service_outbox`, coherente con la migración `021.sql`; no se inventaron conteos ni se modificó el JSON histórico. Los archivos Mermaid y SVG permanecieron sin diferencias: la topología no cambió y no se volvió a renderizar.

**Word/PDF del corte 21 y revisión editorial permanecen pendientes.** Los documentos del 14/11, sus 24/74 páginas y su aprobación editorial siguen identificados como históricos; no se atribuyen a la actualización del 17/11. Los gates actuales exigen exactamente esquema 21 y conservan READ ONLY, loopback, propietario, directorio de PostgreSQL y doce servicios. Para reproducir el corte 20 se utiliza el código de su revisión histórica, sin cambiar su metadata a 21.

## Herramientas reutilizadas

`scripts/build_partial_docs.py` ya elaboraba catálogo físico, Mermaid de FK y fichas a partir de metadatos. Su nuevo modo `--final --metadata` conserva ese flujo, exige esquema 21/READ ONLY/doce propietarios y toma las vistas del catálogo instalado. El modo histórico sigue separado. No se aplica el generador SQL ni migraciones a una base para documentarla.

`scripts/capture_final_schema.py` añade la extracción que antes no estaba versionada. Lee únicamente catálogos de tablas/columnas/restricciones/índices/disparadores/dependencias de vistas y la versión técnica de migración. Usa una transacción READ ONLY/REPEATABLE READ; no lee expedientes, usuarios de negocio, tokens, roles personales ni filas de donantes. Verifica loopback, propietario del archivo privado y `data_directory` del fixture. No imprime DSN, no modifica `state.json` y no inicia ni detiene procesos.

`scripts/render_final_diagrams.cjs` adapta el render histórico Playwright/Mermaid. Reutiliza Chrome/Playwright ya presentes y el bundle Mermaid MIT incluido en la documentación local de ClamAV. No instala Mermaid CLI ni descarga navegadores. El bundle se puede indicar con `REDHOUSE_MERMAID_BUNDLE`; su SHA se conserva en `_render.json`. Ese resultado distingue generación de revisión visual. El directorio temporal antiguo de herramientas solo conserva restos de dependencias y no constituye una instalación Mermaid utilizable.

## Reproducción y exportación pendiente

La captura requiere **solo el PostgreSQL propio de `/private/tmp/rh-load-c92ed10k` activo**. Si la serie ya lo cerró, dirección debe iniciarlo mediante el comando privado `infrastructure_commands.postgres` de su `state.json`, comprobando propiedad/directorio/puerto; conservar el PID recién creado y cerrarlo al terminar. No usar `Environment.init`, `ensure_infrastructure` o el arranque completo: no se necesitan Redis, MongoDB, API ni workers para capturar este catálogo. El script falla si PostgreSQL está cerrado y no intenta reiniciarlo.

Los dos primeros comandos documentan la captura y el builder ya concluidos el 17/11; no deben repetirse sobre el mismo archivo ni durante la carga. La exportación pendiente se realizará desde la raíz, tras liberar la ventana y cerrar el corte editorial:

```sh
# Captura ya aprobada; no repetir sobre esta salida existente.
# Para otro corte, usar nombre nuevo y conservar ambos anteriores.
apps/services/.venv/bin/python scripts/capture_final_schema.py \
  --fixture /private/tmp/rh-load-c92ed10k \
  --output documentation/evidencias/entrega-final/modelos-20261117/postgresql-physical.json

# No accede a la base: utiliza exclusivamente el JSON y contratos del repositorio.
apps/services/.venv/bin/python scripts/build_partial_docs.py --final \
  --metadata documentation/evidencias/entrega-final/modelos-20261117/postgresql-physical.json

# Las fuentes Mermaid/SVG no cambiaron al pasar a 21: no repetir este render.
# Solo ante cambios futuros de topología y en una ventana autorizada:
# node scripts/render_final_diagrams.cjs documentation/entrega-final/modelos/diagramas

# Catálogo Word con nombre final propio; no incorpora la portada del informe.
.local/venv-docs/bin/python scripts/export_partial_report.py --final-physical
soffice --headless --convert-to pdf --outdir documentation/pdf \
  documentation/docx/Modelo_fisico_PostgreSQL_final.docx

# Informe final con su portada/índice y referencias actualizadas.
.local/venv-docs/bin/python scripts/export_partial_report.py --final --pdf
```

La sintaxis Python de los tres scripts se comprobó antes de iniciar la captura. El builder terminó con los conteos esperados. El primer render conservó dieciocho figuras y falló al analizar un punto y coma en una nota de secuencia; se corrigió únicamente ese texto y se repitió esa figura. Los ajustes posteriores de legibilidad/título se renderizaron por selección, sin repetir todos los diagramas. La primera conversión LibreOffice abortó en AppKit bajo sandbox; la misma fuente convirtió después con ejecución autorizada y perfil aislado. El índice del informe se estabilizó en dos pasadas. No se presentan esos intentos como ejecuciones iniciales sin fallos ni se sobrescribe la verificación editorial previa.

## Archivos editables y cortes de salida

Están escritas cinco fuentes de detalle: `diagramas/componentes.mmd`, `despliegue.mmd`, `archivos.mmd`, `secuencia.mmd` y `datos.mmd`, más `archivos-resumen.mmd` y `secuencia-resumen.mmd` para lectura en papel. Representan doce propietarios, LOCAL principal/GCS opcional, revisión humana y límites de un host. `datos.mmd` es la vista conceptual de relaciones de negocio; sus flechas no afirman cardinalidades SQL. Las secuencias describen mecanismos, sin acreditar ejecución integral por aparecer en un dibujo.

El builder produjo `Modelo_fisico.md`, `Modelo_relacional.md`, `Fichas_microservicios.md`, `diagramas/postgresql-completo.mmd`, `modelo-relacional.mmd` y doce `postgresql-<propietario>.mmd`. `Modelo_conceptual.md` explica la vista de negocio. Las vistas por servicio muestran tablas referidas por sus vistas SQL y claves de contexto; **no declaran propiedad de escritura por el mero hecho de consultarlas**. Las tablas compartidas se repiten como referencias gráficas, no como copias físicas. Los modelos lógicos 0FN–4FN del semestre mantienen su origen y no se reescriben para aparentar el esquema actual.

En el corte del 14/11 se generaron **21 SVG ampliables y siete PNG**; se conservan sin cambios en la actualización al esquema 21. El informe imprime los dos resúmenes y la gráfica de carga; enlaza los diagramas amplios para conservar su legibilidad. El renderer evita rasterizar el catálogo físico completo como una imagen enorme. Los Word/PDF del corte anterior están en las carpetas existentes, con nombre propio; su registro editorial conserva hashes, paginación y alcance de inspección. La exportación y revisión del nuevo corte 21 siguen pendientes. Un archivo `_render.json` con estado GENERATED no constituye por sí solo aprobación editorial ni verificación clínica.

## Validación mínima del cierre

1. Sintaxis/formato de los tres scripts modificados y del renderer; CLI rechaza combinación de modos y destinos históricos. Sin suite funcional ni motores adicionales.
2. Captura nueva: READ ONLY verdadero, versión 21, doce nombres de servicio, tablas únicas por esquema/nombre, columnas ordenadas, índices y FK con destino existente. Registro de inicio/cierre del único PostgreSQL propio. No conservar filas ni configuración privada en el JSON público.
3. Builder: conteos MD coinciden con JSON; `web_runtime` no se suma mediante cifras manuales antiguas; doce fichas y doce vistas gráficas de servicio; relaciones provienen de FK, no de nombres parecidos. Contratos/versiones se leen del árbol actual.
4. Mermaid: parse/render secuenciales, SVG íntegros y enlaces del catálogo válidos. Revisar visualmente vista completa ampliable, modelo relacional, una vista por servicio y las cinco figuras resumidas; no asumir legibilidad por obtener salida.
5. Word/PDF: ZIP íntegro, páginas/títulos/índice, tablas dentro de página, sin texto recortado, sin datos de portada históricos ni cifras de once servicios/71 tablas como si fueran actuales. Conservar manifiesto de fuentes/artefactos y revisar diferencias; no atribuir este cierre editorial a una nueva regresión de producto.

El informe final vincula este catálogo y sus resultados documentales. Los hashes identifican un corte, que no se reexporta por cada resultado futuro. Aprobación clínica, aceptación integrada de procesos y acciones humanas conservan su estado separado.
