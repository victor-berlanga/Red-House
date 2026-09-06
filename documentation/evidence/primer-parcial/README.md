# Revisión del primer parcial

> **Fecha de edición documental:** 7 de septiembre de 2026.  
> **Ejecución comprobada:** 6 de septiembre de 2026.  
> **Alcance:** revisión del monolito de `Red-House`, sin implementar componentes posteriores ni modificar reglas clínicas.

## Resultado técnico

- **65 pruebas aprobadas, 0 fallos, 0 errores y 0 omisiones**, en 40.80 segundos. Se ejecutaron los archivos actuales de `apps/web-monolito01/tests/`, con un entorno Python limpio creado para esta revisión, PostgreSQL temporal exclusivo y Chrome.
- Chrome verificó altas, cambios de estado, persistencia al recargar, auditoría, perfiles, Highcharts y disposición responsive a 1440 y 390 píxeles. Resultado: gráfica renderizada, cero excepciones JavaScript y cero recursos locales faltantes.
- El esquema real contiene **23 tablas, 23 PK, 24 FK y 21 CHECK**. La carga ficticia produjo 2 instituciones, 4 cuentas y 36 unidades; la vista devolvió 36 filas. No se instalaron las 169 relaciones del modelo semestral.
- La normalización lógica volvió a aprobar sus comprobaciones: 169 relaciones, 918 atributos, 208 atributos de origen y 49 diagramas. La reconciliación de las simplificaciones del SQL está en el [README de datos](../../../data/database/README.md#reconciliación-técnica-del-primer-parcial).
- El comprobador existente `setup.sh --check`, ejecutado desde `Red-House`, aprobó la configuración y encontró 2 instituciones, 4 cuentas y 36 unidades sin reinicializar ni cargar datos. Esa consulta no equivale a probar una instalación nueva de este repositorio.

## Verificación del entorno reconstruido

El 6 de septiembre, por autorización del usuario, se conservó el entorno copiado fuera del repositorio y se creó `.venv` directamente en la ruta actual de `Red-House`. Se instalaron las dependencias declaradas de ejecución y pruebas. La activación y los ejecutables apuntan al proyecto actual, y `pip check` aprobó.

La suite se repitió con ese entorno: **65 pruebas aprobadas, 0 fallos, 0 errores y 0 omisiones, en 40.92 s**. Chrome confirmó Highcharts, cero excepciones y cero recursos faltantes. `setup.sh --check` aprobó en modo de solo lectura. El arranque con `python3 run.py`, sin activar el entorno, respondió HTTP 200 en `/health/live`, `/` y `/login` en un puerto temporal. El servidor temporal y el clúster exclusivo de pruebas quedaron detenidos.

## Evidencia conservada

| Archivo | Contenido |
| --- | --- |
| [Tests.xml](Tests.xml) | Resultado JUnit de la revisión técnica inicial: 65 casos, 40.80 s y cero omisiones. |
| [Tests_venv.xml](Tests_venv.xml) | Segunda ejecución con el entorno reconstruido del proyecto actual: 65 casos, 40.92 s y cero omisiones. |
| [Environment_check.json](Environment_check.json) | Comprobaciones del entorno, dependencias, arranque directo, preservación y origen de la confirmación de Windows. No contiene configuración privada. |
| [Schema_review.json](Schema_review.json) | Huella del SQL revisado, catálogo real de restricciones, comparación de columnas/claves y resultado del verificador lógico. La coincidencia de nombres no se presenta como prueba automática de equivalencia semántica. |
| [Inventory_mobile.png](Inventory_mobile.png) | Inventario a 390 píxeles; la tabla se desplaza dentro de su contenedor. |
| [Unit_history.png](Unit_history.png) | Unidad ficticia creada en el navegador y su movimiento persistido. |
| [Audit.png](Audit.png) | Consulta autorizada de los eventos ficticios de acceso, administración e inventario. |

Los artefactos contienen únicamente los datos sintéticos de las pruebas. No incluyen `.env`, contraseñas, JWT ni volcados de una base de usuario. Las capturas son evidencia de esta ejecución; no significan que las vistas futuras sean procesos implementados.

## Cómo repetir las comprobaciones

Seguir la sección [Pruebas reproducibles](../../../apps/web-monolito01/README.md#pruebas-reproducibles): preparar un entorno Python propio, instalar `requirements-dev.txt`, proporcionar Playwright mediante `NODE_PATH` y definir `TEST_POSTGRES_URL` hacia un clúster exclusivamente de pruebas. No usar la conexión de la base funcional como destino de pruebas.

Desde `apps/web-monolito01/`, con ese entorno y esas variables ya configurados:

```sh
python -m pytest -q --tb=short --browser -s -p no:cacheprovider
```

Para conservar un nuevo informe sin sobrescribir esta evidencia, añadir `--junitxml` con una ruta nueva y dirigir `BROWSER_ARTIFACTS` a una carpeta nueva. Para el modelo lógico, desde la raíz del repositorio:

```sh
node documentation/database-diagrams/normalization/validate.mjs
```

El catálogo físico se obtuvo mediante `information_schema.columns`, `information_schema.tables` y `pg_constraint`/`pg_get_constraintdef` después de ejecutar el SQL y `seed_demo` en una base exclusiva. Las PK se comprobaron para las 23 tablas y se contrastaron claves y columnas con `normalization/model.mjs`; la interpretación de las diferencias es la revisión documental enlazada arriba.

## Cierre del primer parcial

El usuario confirmó el 6 de septiembre de 2026 que otros integrantes del equipo ya realizaron la revisión y la prueba en Windows, y autorizó registrarlas como terminadas. Esta es una confirmación del equipo comunicada por el usuario, no una ejecución de Windows en este Mac; no se inventan nombres de revisores ni detalles de esa prueba.

Con esa confirmación, la revisión técnica existente y la reconstrucción verificada del entorno, el [Sprint Backlog](../../markdowns/Sprint_backlog.md) queda con los ocho elementos del Sprint 1 terminados. Los 21 elementos de los cortes posteriores conservan su estado. Markdown y Word mantienen las tareas y sus criterios de cierre, sin notas añadidas de avance o pendientes. No se realizaron commits, cambios de ramas ni publicaciones remotas.

## Preservación y límites

El código, el SQL, los modelos y la configuración privada no se modificaron para lograr los resultados. En la revisión técnica inicial se conservaron los 148 archivos inspeccionados; durante la reconstrucción y su verificación se conservaron idénticos los 155 archivos del proyecto ajenos al entorno virtual. Después se actualizaron únicamente la documentación de cierre y sus evidencias. La comprobación de la base existente fue de solo lectura; `.env` conserva su contenido y permisos `600`. El entorno anterior permanece como respaldo temporal en `/private/tmp/red-house-close.Yn7o33/previous_venv`, fuera del repositorio.

Cada caso retiró exclusivamente su base temporal recién creada. La base adicional de inspección también se retiró; el clúster de revisión quedó sin bases de prueba y se detuvo. No se detuvo el PostgreSQL habitual ni se alteró la base `red_house` del usuario.

Los artefactos automatizados de este directorio corresponden a macOS; la ejecución nativa de Windows consta por la confirmación del equipo indicada arriba. Este cierre no cubre carga masiva, seguridad de producción, revisión clínica, MongoDB, Redis, Docker, clientes, microservicios ni nube. La migración completa del modelo semestral y sus decisiones funcionales corresponden a incrementos posteriores.
