# Filtros automáticos — 14 de septiembre de 2026

**90 pruebas aprobadas en 112.12 s; sin fallos, errores u omisiones.** Suite completa con PostgreSQL y Chrome en bases temporales. No se modificaron datos del negocio en la instalación habitual. La aplicación se reinició en el puerto 5050 y el clúster exclusivo de pruebas se detuvo.

## Alcance y aceptación

| Capacidad | Evidencia |
| --- | --- |
| Filtros en diez secciones: inventario, auditoría, instituciones, sedes, ubicaciones, componentes, usuarios, donantes, receptores y solicitudes | Recorrido de `filters_browser.cjs` |
| Texto con espera de 300 ms; selectores y fechas al cambiar | Una sola consulta al escribir un folio, selección y fecha sin pulsar Filtrar |
| Actualización de resultados, paginación y contadores | Filtrar una unidad desde página 2 vuelve a página 1 y muestra un registro/contador; filtro institucional ajeno devuelve cero |
| URL, Atrás/Adelante y Limpiar | Atrás restaura criterios y resultados; Limpiar restaura todos |
| Cancelación y respuestas obsoletas | Respuesta anterior retrasada no reemplaza el resultado vigente |
| Fallos recuperables | Fallo de red conserva resultados y muestra Reintentar; siguiente consulta exitosa |
| Formularios sin guardar | Filtrar donantes conserva un borrador de nombre en el formulario POST |
| Sesión expirada | Redirección al acceso, sin insertar el HTML de login como resultados |
| Móvil y alternativa sin JavaScript | 390 px sin desbordamiento; GET convencional mantiene botón funcional sin JavaScript |
| Regresión de negocio | Flujo sanguíneo completo, privacidad, concurrencia, migración y auditoría siguen aprobando |

## Archivos

- [Tests.xml](Tests.xml): informe JUnit completo.
- [Browser_results.json](filters/Browser_results.json): resultados específicos de los filtros.
- [Inventario filtrado](filters/Inventario_filtrado.png).
- [Sin coincidencias](filters/Inventario_sin_coincidencias.png).
- [Error y reintento](filters/Error_y_reintento.png).
- [Donantes en móvil](filters/Donantes_mobile.png).
- [Usuarios](filters/Usuarios_filtrados.png) y [auditoría](filters/Auditoria_filtrada.png).

Las capturas contienen datos ficticios de las pruebas. Las evidencias anteriores permanecen como cortes históricos. El servidor reiniciado respondió HTTP 200 en salud y en el recurso `filters.js`.

## Implementación

JavaScript nativo, Fetch y AbortController sobre las rutas GET existentes; Flask/Jinja2 sigue generando el HTML con autorización y auditoría. El navegador extrae solo resultados, paginación y contadores, conservando filtros y formularios POST. Las consultas SQL mantienen parámetros y ámbito institucional. No hay nuevas dependencias de ejecución, cambios de esquema ni endpoints de microservicios.

## Reproducir

Desde `apps/web-monolito01`, definir `TEST_POSTGRES_URL` hacia un clúster exclusivo con permiso para crear bases, `NODE_PATH` hacia Playwright y `BROWSER_ARTIFACTS` hacia una carpeta nueva. Requiere Chrome.

```sh
python -m pytest -q --browser -p no:cacheprovider --tb=short --junitxml=/ruta/nueva/Tests.xml
```
