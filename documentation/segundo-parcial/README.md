# Artefactos del segundo parcial

El [informe técnico](../markdowns/Reporte_tecnico_segundo_parcial.md), las
[fichas individuales](Fichas_microservicios.md), el [modelo físico](Modelo_fisico.md)
y la [matriz de cierre](../markdowns/Cierre_segundo_parcial.md) describen la
implementación. Los [resultados](../evidencias/segundo-parcial/RESULTADOS.md)
distinguen ejecuciones aprobadas, fallos conservados y limitaciones.

Exportaciones: [informe Word](../docx/Reporte_tecnico_segundo_parcial.docx),
[informe PDF](../pdf/Reporte_tecnico_segundo_parcial.pdf),
[modelo físico Word](../docx/Modelo_fisico_PostgreSQL.docx) y
[modelo físico PDF](../pdf/Modelo_fisico_PostgreSQL.pdf). Los documentos comienzan
directamente con contenido técnico. El [diagrama físico completo](diagramas/postgresql-completo.svg)
permite ampliar las 71 tablas; las figuras de resumen se incluyen en el informe.

## Regenerar anexos y documentos

Desde la raíz del repositorio, con el entorno de servicios instalado:

```sh
apps/services/.venv/bin/python scripts/build_partial_docs.py
python3 -m venv .local/docs-venv
.local/docs-venv/bin/pip install python-docx==1.2.0 Markdown==3.11.1 lxml==6.1.3 Pillow==13.0.0
.local/docs-venv/bin/python scripts/export_partial_report.py
.local/docs-venv/bin/python scripts/export_partial_report.py --physical
soffice --headless --convert-to pdf --outdir documentation/pdf documentation/docx/Reporte_tecnico_segundo_parcial.docx documentation/docx/Modelo_fisico_PostgreSQL.docx
```

La conversión a PDF requiere LibreOffice. El generador del catálogo utiliza
metadatos conservados de PostgreSQL; no crea registros ni accede a credenciales.
Si cambia el esquema instalado, actualizar primero `postgresql-physical.json`
mediante una consulta autorizada de `pg_catalog` e `information_schema`.

## Regenerar evidencia HTTP y capturas

Ejecutar las pruebas con `REDHOUSE_HTTP_EVIDENCE` apuntando a un directorio vacío
y privado; el comando completo figura en la guía de pruebas. La captura es
optativa y se usa únicamente con datos ficticios. Después de finalizar la suite:

```sh
apps/services/.venv/bin/python scripts/build_http_evidence.py /ruta/privada/captura
npm install --prefix .local/doc-tools --no-audit --no-fund playwright@1.64.1
NODE_PATH="$PWD/.local/doc-tools/node_modules" node scripts/capture_http_evidence.cjs
```

Las capturas requieren Google Chrome instalado y muestran el visor de peticiones
realmente registradas. Cada página enlaza el JSON completo, las variantes,
la persistencia, la correlación y la versión. La cobertura identifica rutas sin
ejecución; no las rellena con ejemplos artificiales.

Con el Compose de demostración activo y GCS configurado, ejecutar primero
`apps/services/.venv/bin/python deployment/prepare_browser_demo.py`. Este comando
conserva un traslado abierto existente o crea uno ficticio mediante las API;
un traslado cerrado ya no permite cargar nuevas evidencias. Después ejecutar
`NODE_PATH="$PWD/.local/doc-tools/node_modules" node scripts/capture_live_partial.cjs`
para verificar siete perfiles, gráficas, adaptación móvil, carga privada y Swagger
ejecutado. El script obtiene las cuentas del estado privado y redacta la
autorización antes de conservar evidencia.

Las fuentes de diagramas son los archivos `.mmd`. Se renderizaron con
`@mermaid-js/mermaid-cli@12.0.0`; los SVG conservan texto ampliable. La inspección
del PDF utilizó PyMuPDF 1.28.2, fuera de las dependencias de la aplicación.

Actualización del 20 de octubre: [sesiones Redis y revocaciones PostgreSQL](../evidencias/sesiones-redis/RESULTADOS.md). Los Word/PDF vigentes incorporan el almacenamiento actual; las evidencias del cierre del 19 de octubre se conservan con su fecha original.
