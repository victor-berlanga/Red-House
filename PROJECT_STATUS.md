# Estado y seguimiento del proyecto

## Cómo mantener este documento

Este archivo es la fuente de verdad del avance del proyecto. Debe actualizarse después de cada bloque de trabajo material.

- Registrar solamente avances comprobados.
- Mover los elementos entre `Pendiente`, `En curso`, `Bloqueado` y `Terminado` según corresponda.
- Añadir las decisiones importantes y su motivo.
- Registrar las pruebas ejecutadas y su resultado.
- Asociar a cada tarea material un criterio de aceptación y una evidencia verificable cuando comience su ejecución.
- Agregar una entrada breve a la bitácora, colocando la más reciente al principio.
- No eliminar antecedentes relevantes; si una decisión cambia, marcarla como reemplazada y enlazar la nueva decisión.

## Resumen actual

- **Fecha de edición documental:** 2026-09-07
- **Última actividad registrada:** 2026-09-07
- **Fase:** Primer parcial cerrado; monolito local verificado
- **Estado general:** Los ocho paquetes del primer parcial están terminados, con revisión técnica, confirmación del equipo y prueba de Windows comunicadas por el usuario. Monolito ejecutable en `apps/web-monolito01`, entorno virtual propio y esquema PostgreSQL de 23 tablas en `data/database/schema.sql`. El cierre se limita al MVP académico; no declara terminado el sistema semestral ni sus componentes posteriores.
- **Dominio del negocio:** Red regional de bancos de sangre y donación de órganos
- **Progreso funcional:** MVP web acotado implementado y revalidado desde `Red-House` con su `.venv` reconstruido: la evidencia histórica conserva 65 pruebas aprobadas en 40.92 s con PostgreSQL temporal y Chrome; este incremento añadió la baja lógica sanguínea y dos pruebas específicas, y los 26 casos de `test_monolith.py` pasaron con PostgreSQL real. Funciones reales: acceso, administración, inventario sanguíneo ficticio, caducidad DEMO, baja lógica con visibilidad excluida, panel y auditoría. Siete pantallas de negocio futuras y recuperación de acceso son únicamente vistas; los demás productos e integraciones del semestre conservan su calendarización posterior.
- **Sprint Backlog:** 8 terminados (`P1-01` a `P1-08`), 0 en proceso y 21 pendientes de los sprints posteriores. Se cerraron los cinco paquetes restantes tras la confirmación del usuario sobre la revisión del equipo y Windows, y la reconstrucción verificada del entorno. Markdown y Word conservan tareas, criterios de cierre, responsables y dependencias, sin notas añadidas de avance ni pendientes.
- **Entorno local existente:** `.venv` reconstruido directamente en `Red-House/apps/web-monolito01/.venv`, con dependencias declaradas, activación y ejecutables de esta ruta. `pip check`, `setup.sh --check`, suite completa y arranque directo aprobados. `.env` privado y base existente conservados: 2 instituciones, 4 cuentas y 36 unidades; puerto habitual 5050. Respaldo temporal del entorno anterior en `/private/tmp/red-house-close.Yn7o33/previous_venv`. La comprobación arrancó y detuvo solo su servidor temporal; no se reinicializó la base ni se modificó el servidor habitual.
- **Preparación automatizada:** `setup.sh` y `setup.cmd` comparten `scripts/setup_local.py`; `python run.py` selecciona el entorno local sin activación manual. Instalación y arranque verificados aquí en macOS. Prueba nativa de Windows realizada por otros integrantes, según confirmación del usuario del 6 de septiembre. Requieren Python y PostgreSQL ya instalados, con PostgreSQL activo.
- **Repositorio actual:** `Red-House`, con fuentes en `documentation/markdowns`, entregables en `documentation/docx`, modelos en `documentation/database-diagrams` y evidencia de la revisión en `documentation/evidence/primer-parcial`. Los antecedentes no trasladados se identifican como pertenecientes al repositorio de origen. Las verificaciones anteriores conservan su cronología; la suite del 6 de septiembre ya corresponde al código de esta carpeta. Git muestra únicamente `main` y `README.md` versionado; no se hicieron commits, cambios de ramas ni publicaciones remotas.

## Terminado

- [x] Agregar baja lógica del inventario sanguíneo para el Operador.
  - **Criterio de aceptación:** el Operador puede retirar una unidad con motivo y versión vigente sin borrar sus tablas de identidad, movimiento o auditoría; la unidad deja de aparecer en el listado, filtros visibles, contadores, avisos y últimas unidades del panel; una cuenta sin `inventory.write` no puede ejecutar la operación; una unidad con movimiento operativo posterior al alta recibe 409 y conserva su estado.
  - **Evidencia:** `apps/web-monolito01/src/business/services/inventory.py`, `apps/web-monolito01/src/presentation/routes/inventory.py`, `apps/web-monolito01/src/data_access/repositories/inventory.py` y las plantillas de inventario. `apps/web-monolito01/tests/test_monolith.py` incorpora comprobaciones de baja, visibilidad, historial, auditoría, bloqueo tras movimiento y rechazo al Auditor. `TEST_POSTGRES_URL='dbname=postgres host=/tmp' .venv/bin/python -m pytest -q tests/test_monolith.py --tb=short`: 26 aprobadas en 85.02 s.
  - **Decisión operativa:** se reutiliza `blood_unit.current_status = 'WITHDRAWN'` como baja lógica y se agrega un movimiento `DELETE`; el detalle directo conserva trazabilidad, mientras las consultas operativas excluyen el estado. Como el MVP aún no tiene tablas separadas de asignación, traslado o entrega, cualquier movimiento posterior a la alta bloquea conservadoramente la baja.
  - **Límite:** el cambio solo cubre el inventario sanguíneo funcional del MVP; la vista de órganos sigue siendo futura y no se habilitó.

- [x] Cerrar el Sprint 1 y reconstruir el entorno virtual para el proyecto actual.
  - **Criterio de aceptación:** registrar la confirmación del usuario sobre la revisión del equipo y Windows; cerrar los paquetes del primer parcial sin alterar sus tareas, criterios, responsables o dependencias; retirar las notas añadidas de avance/pendientes del backlog; disponer de un entorno propio con arranque y pruebas aprobados, conservando configuración, código y datos.
  - **Evidencia:** `documentation/markdowns/Sprint_backlog.md` y `documentation/docx/Sprint_backlog.docx`, con 8 terminados y 21 pendientes; confirmación del usuario en esta conversación. `documentation/evidence/primer-parcial/Tests_venv.xml` y `Environment_check.json`: 65 pruebas aprobadas en 40.92 s, sin omisiones; activación y ejecutables de la ruta actual, `pip check`, comprobación de solo lectura y HTTP 200 en salud, inicio y acceso mediante `python3 run.py` sin activación manual.
  - **Preservación:** 155 archivos ajenos a `.venv` idénticos después de las pruebas, antes de actualizar esta documentación; `.env` y permisos `600` conservados; base existente sin reinicializar. Entorno anterior respaldado fuera del repositorio. Word conserva 14 tablas, formato y todas las partes distintas de `word/document.xml`; no se cambiaron código, SQL, modelos ni Git.
  - **Atribución y alcance:** la revisión humana y la prueba en Windows fueron confirmadas por el usuario como realizadas por otros integrantes; no se presentan como pruebas ejecutadas por este agente. Los cortes posteriores no se cierran ni se implementan en este trabajo.
- [x] Realizar la revisión técnica del primer parcial y repetir las pruebas completas desde `Red-House`.
  - **Criterio de aceptación:** contrastar el modelo lógico con las tablas del MVP, comprobar claves/restricciones y límites; ejecutar la suite existente con PostgreSQL y Chrome; revisar el entorno sin alterar la base habitual; conservar evidencia y distinguir aprobación técnica de cierre formal del backlog.
  - **Evidencia:** `data/database/README.md` documenta la reconciliación de las 23 tablas, incluidas las reducciones de claves, medios de contacto, ámbitos, parámetros, auditoría y procesos posteriores. `documentation/evidence/primer-parcial/` conserva resultados JUnit, catálogo físico y capturas; 65 pruebas aprobadas sin omisiones en 40.80 s, 23 PK, 24 FK, 21 CHECK y 49 diagramas lógicos comprobados.
  - **Resultado histórico:** no se detectaron fallos ni fue necesario cambiar código o SQL. En esa revisión se dejó el cierre de cinco paquetes a la espera de la confirmación del equipo, Windows y la reconstrucción del `.venv`; esos puntos quedan resueltos por la entrada de cierre posterior del 6 de septiembre, conservada al inicio de esta sección.
  - **Preservación:** los 148 archivos inspeccionados permanecían idénticos al acabar la suite. El comprobador de la base habitual fue de solo lectura; las bases temporales se retiraron y el clúster exclusivo se detuvo. `.env`, credenciales, datos, modelos y aplicación se conservaron; no se modificó `proyectoPrueba`.
- [x] Actualizar el Sprint Backlog con la evidencia del MVP y normalizar los nombres de la documentación.
  - **Criterio de aceptación:** Markdown y DOCX coincidentes, con los mismos 29 identificadores, responsables, tareas, criterios de cierre, dependencias y relaciones RF/RNF; distinguir implementación técnica de cierre del paquete; nombres descriptivos con inicial mayúscula y palabras separadas por guion bajo, referencias resolubles y generación de diagramas reproducible.
  - **Evidencia:** `documentation/markdowns/Sprint_backlog.md` y `documentation/docx/Sprint_backlog.docx`, que en esa edición tenían 3 terminados, 5 en proceso y 21 pendientes, con notas para `P1-03` a `P1-08`; esa presentación fue sustituida por el cierre posterior solicitado por el usuario. Se renombraron 17 Markdown y 11 Word, incluidos `Historias_de_usuario`, `Plan_de_trabajo` y `Modelo_4FN`, actualizando sus referencias y los nombres utilizados por el generador/verificador.
  - **Verificación:** 58 enlaces relativos resolubles, 63 bloques Mermaid conservados, 49 diagramas aceptados por el verificador de normalización; 11 Word íntegros y legibles por el lector nativo. El backlog conserva 14 tablas y solo modifica `word/document.xml`; los otros diez Word son idénticos salvo el nombre. Siete pruebas unitarias de validación y permisos aprobadas en `Red-House`; código, SQL y configuración de la aplicación conservados.
  - **Límite:** se mantuvieron los nombres convencionales `README.md`, `AGENTS.md` y `PROJECT_STATUS.md`, la fecha de edición documental del 7 de septiembre y la cronología histórica. No se repitieron las 65 pruebas completas, la instalación ni la demostración con PostgreSQL; no se modificó el repositorio de origen.
- [x] Adaptar las rutas documentales a `Red-House` y unificar las fechas iniciales solicitadas.
  - **Criterio de aceptación:** enlaces relativos resolubles bajo `documentation/`, generador y verificador alineados con `Modelo_0FN.md`, fechas iniciales existentes en Markdown y Word fijadas al 7 de septiembre de 2026 y conservación de contenido, estilos, diagramas y cronología del cuerpo.
  - **Evidencia:** 12 encabezados Markdown y 11 Word actualizados; cero enlaces relativos rotos en la selección revisada; 11 paquetes Word abiertos con el lector nativo de macOS, con una sola fecha modificada por documento y todas las demás partes internas idénticas. Los 63 bloques Mermaid de la documentación permanecen idénticos; el verificador de normalización aprueba los 49 bloques generados y las dependencias declaradas.
  - **Límite:** no se añadieron fechas a documentos que no tenían una fecha inicial. La edición documental del 7 de septiembre es la solicitada por el usuario; esta actividad se registra el 6 de septiembre. No se ejecutó el monolito, no se reinicializó ninguna base y no se cambiaron secretos, `.gitignore` ni reglas del modelo.
- [x] Automatizar la preparación local del monolito y simplificar su arranque, sin ampliar el alcance funcional.
  - **Criterio de aceptación:** entradas para macOS/Linux y Windows con lógica compartida; instalación nueva de entorno, dependencias, secretos, base, esquema y DEMO; reutilización segura sin sobrescribir configuración o contraseñas; comprobación de solo lectura y arranque directo con `python run.py`.
  - **Evidencia:** `setup.sh`, `setup.cmd`, `scripts/setup_local.py`, `run.py`, `tests/test_setup.py` y los README. Suite total de 65 pruebas aprobadas; instalación real en una copia temporal con espacios en la ruta, segunda ejecución sin entrada ni carga adicional y cuatro accesos HTTP aprobados al arrancar con el Python del sistema sin activar `.venv`.
  - **Límite:** se comprobó macOS y la lógica Python compartida, no el intérprete CMD nativo de Windows. No se instalan ni administran Python/PostgreSQL del sistema; no se crean servicios, Docker ni un segundo punto de entrada `app.py`.
- [x] Completar por autorización del usuario todos los pasos de instalación y arranque local.
  - **Criterio de aceptación:** dependencias instaladas en el proyecto, secretos privados, base nueva sin sobrescribir otras, esquema y carga DEMO completos, página accesible y acceso verificado para los cuatro usuarios.
  - **Evidencia:** `.venv`, `.env` ignorado por Git con permisos `600`, PostgreSQL con 23 tablas, dos instituciones, cuatro cuentas y 36 unidades; HTTP 200 en `/health/live`; Chrome comprobó inicio, panel con Highcharts, vista autorizada y cierre de sesión de cada cuenta. La contraseña generada se entregó al usuario y no se añadió a archivos del repositorio.
- [x] Construir el primer incremento monolítico de Red House, adaptando el diseño del ZIP a Flask/Jinja2.
  - **Criterio de aceptación:** una sola aplicación desplegable; capas de presentación, negocio, acceso a datos y configuración; sitio público y portal responsive; únicamente capacidades funcionales del MVP y vistas futuras explícitamente deshabilitadas.
  - **Evidencia:** `apps/web-monolito01/src/`, `run.py`, dependencias y README; 15 plantillas Jinja2, CSS/JavaScript e iconos, fuentes y Highcharts locales. Se conservaron el ZIP, los análisis y los modelos anteriores; no se generaron microservicios, clientes ni contenedores.
- [x] Implementar el subconjunto físico y la gestión administrativa/inventario del MVP.
  - **Criterio de aceptación:** altas y cambios persistidos en PostgreSQL, ámbito institucional verificable, caducidad derivada, referencias activas, historial, auditoría atómica y rechazo de escrituras concurrentes obsoletas.
  - **Evidencia:** `data/database/schema.sql` y su README; 23 tablas y una vista; CLI de inicialización/carga DEMO; pruebas sobre bases PostgreSQL reales creadas exclusivamente para verificación. El ejemplo contiene dos instituciones, cuatro cuentas y 36 unidades ficticias, sin credenciales predeterminadas.
  - **Límite:** es una proyección física documentada del primer parcial, no la implementación de las 169 relaciones lógicas ni una validación normativa del modelo completo.
- [x] Verificar acceso y seguridad básica del monolito.
  - **Criterio de aceptación:** JWT con expiración, CSRF, revocación, permisos por acción/ámbito, datos escapados, consultas parametrizadas, bitácora sin secretos y fallo cerrado ante PostgreSQL inaccesible.
  - **Evidencia:** `tests/test_validation.py` y `tests/test_monolith.py`; pruebas de aislamiento entre las dos instituciones, permisos no jerárquicos, baja de cuentas/instituciones, intentos fallidos, restricciones de historial, rollback ante fallo de auditoría y recuperación de conexión.
  - **Límite:** sesiones y revocación en PostgreSQL durante el primer parcial; Redis, refresh tokens, TLS/despliegue y controles distribuidos siguen pendientes.
- [x] Documentar la ejecución local y verificar el recorrido visual del incremento.
  - **Criterio de aceptación:** instrucciones reproducibles, secretos fuera del repositorio, carga explícita sin sobrescritura, formularios y persistencia comprobados en navegador, menú móvil y límites futuros visibles.
  - **Evidencia:** README raíz, `apps/web-monolito01/README.md`, `.env.example`, `tests/test_browser.py` y `tests/browser_smoke.cjs`; Chrome a 1440 y 390 píxeles, Highcharts renderizado, sin desbordamiento horizontal de página, sin excepciones JavaScript ni recursos locales faltantes. Tabla de inventario desplazable horizontalmente dentro de su contenedor.
- [x] Registrar la arquitectura tecnológica obligatoria y sus restricciones.
- [x] Crear el contexto persistente para futuras conversaciones en `AGENTS.md`.
- [x] Crear este documento de seguimiento.
- [x] Revisar la especificación ampliada e incorporar requisitos adicionales de seguridad, integración, pruebas, rendimiento y documentación.
- [x] Registrar el dominio, problema, objetivos y límite de apoyo a decisiones médicas.
- [x] Registrar los actores conocidos, funciones por cliente, catálogo inicial de microservicios y capacidades algorítmicas esperadas.
- [x] Elaborar el documento de análisis del problema en `documentation/docx/Analisis_del_problema.docx`, conservando `documentation/markdowns/Analisis_del_problema.md` como fuente editable.
- [x] Fortalecer y validar documentalmente el análisis con límites académicos explícitos, procesos de referencia, perfiles mínimos, marco mexicano provisional y pendientes diferenciados.
- [x] Corregir el alcance temporal del análisis para que documente todo el proyecto y trate el primer parcial únicamente como una fase de implementación.
- [x] Crear un nuevo borrador de requerimientos funcionales y no funcionales en Markdown y DOCX, clasificado por los ocho componentes obligatorios y conservando intacto el documento anterior como referencia.
- [x] Retirar de la versión entregable de RF/RNF la trazabilidad con el borrador anterior y las decisiones internas de alcance, conservando su contexto en el seguimiento del proyecto.
- [x] Consolidar requisitos semejantes y duplicados semánticos sin perder componentes, alcance futuro, límites clínicos ni obligaciones técnicas.
- [x] Crear una versión consolidada de historias de usuario en Markdown y DOCX, agrupada por flujo de valor y componente, con criterios de aceptación y relación explícita con los 94 RF/RNF.
- [x] Crear un borrador consolidado de reglas de negocio en Markdown y DOCX, organizado por dominio, fase y tipo de validación, con trazabilidad hacia RF/RNF e historias.
- [x] Crear un borrador consolidado de la matriz de perfiles y permisos en Markdown y DOCX, con responsabilidades, información, operaciones, restricciones, niveles de autorización, componentes y fases para los siete perfiles.
- [x] Crear un plan de trabajo del semestre en Markdown y DOCX, organizado por los cuatro cortes oficiales, con paquetes, dependencias, responsables principales y frentes, evidencias, riesgos y criterios de cierre.
- [x] Incorporar en los 29 paquetes del plan semestral los nombres de los responsables principales definidos en el Sprint Backlog.
- [x] Crear un Sprint Backlog en Markdown y DOCX con los 29 paquetes del plan semestral, dividido en cuatro sprints y maquetado para conservar legibilidad sin repetir bloques extensos de RF/RNF.
- [x] Crear los casos de uso principales en Markdown y DOCX, con quince flujos consolidados, actores, condiciones, alternativas y trazabilidad hacia requisitos, historias y reglas de negocio.
- [x] Crear la matriz de trazabilidad integral en Markdown y DOCX, con una fila única por cada uno de los 94 RF/RNF y relaciones verificadas hacia las 44 historias, 40 reglas, 15 casos de uso y nueve tipos de evidencia.
- [x] Incorporar a la matriz de trazabilidad una vista general por componente antes del desglose individual, conservando intactas las 94 relaciones detalladas.
- [x] Cerrar `P1-01` al comprobar la coherencia documental, la estabilidad de identificadores y la ausencia de referencias inexistentes, sin exigir una aprobación formal adicional.
- [x] Completar el diseño arquitectónico en Markdown y DOCX con las nueve vistas exigidas, trece diagramas, responsabilidades, datos, contenedores, Compute Engine, red, seguridad, monitoreo, procesos integrales y criterios de crecimiento.
- [x] Depurar la redacción del diseño arquitectónico para sustituir notas internas, referencias a la solicitud y expresiones de cumplimiento por restricciones, delimitaciones y criterios de evolución propios de un documento académico.
- [x] Crear el documento introductorio `Tecnologias.md` y `.docx` sobre MongoDB, Redis y contenedores Docker, con fundamentos, usos previstos, riesgos, adopción gradual y referencias oficiales.
- [x] Recalendarizar MongoDB, Redis y Docker para que durante el primer parcial permanezcan únicamente como investigación y arquitectura objetivo; su diseño detallado, configuración y uso funcional comenzarán en el segundo parcial, mientras PostgreSQL continúa en el producto mínimo.
- [x] Delimitar el producto mínimo del primer parcial a la gestión web de inventario sanguíneo básico con datos ficticios, persistencia y auditoría, sin automatizar decisiones clínicas.
- [x] Consolidar los perfiles funcionales en siete roles semestrales y limitar el primer parcial a Administrador, Operador de banco de sangre y Auditor.
- [x] Retirar del análisis el cuestionario de preguntas abiertas, renumerar los apartados posteriores y normalizar las referencias institucionales en formato APA 7.
- [x] Eliminar la sección redundante de supuestos iniciales y renumerar los apartados finales sin perder las decisiones de alcance documentadas en otras secciones.
- [x] Reubicar las referencias APA al final del análisis, después de la conclusión, conservando citas, enlaces y formato.
- [x] Crear la estructura versionable `documentation/database-diagrams` para documentar el modelo conceptual y su evolución de 0FN a 4FN.
- [x] Crear un libro Excel reproducible con datos ficticios y una propuesta visual de 0FN a 4FN, sin presentarla todavía como esquema aprobado.
- [x] Crear una primera propuesta de tablas generales en 0FN mediante Markdown y Mermaid.
  - **Criterio de aceptación:** representar los procesos principales con registros amplios, datos compuestos, listas y grupos repetitivos; diferenciar sangre y órganos; conservar la información necesaria para una normalización posterior sin efectuar descomposiciones ni generar SQL.
  - **Evidencia:** `TABLAS_GENERALES_0FN.md` (antecedente del repositorio de origen), con trece tablas, cinco diagramas Mermaid de sintaxis validada y un ejemplo ficticio de unidades y movimientos agrupados.
  - **Situación posterior:** sustituida para el proceso actual a solicitud del usuario, porque su elaboración había consultado modelos de bases de datos anteriores.
- [x] Generar una nueva propuesta ER 0FN directamente desde la documentación funcional y arquitectónica autorizada.
  - **Criterio de aceptación:** utilizar el análisis y los documentos de `documentation/markdowns` como fuentes, excluyendo modelos de bases de datos y ejercicios anteriores; justificar cada tabla; utilizar nombres y atributos en inglés; conservar datos compuestos y grupos repetitivos, sin normalizar ni generar SQL.
  - **Evidencia:** `documentation/database-diagrams/Modelo_0FN.md`, con dieciocho tablas, 208 atributos, 26 relaciones ER y justificación documental por tabla. Se validaron la sintaxis Mermaid, los ocho enlaces a fuentes, 95 identificadores documentales citados y la presencia de grupos repetitivos en todas las tablas. La aprobación funcional sigue pendiente.
- [x] Desarrollar la normalización de la nueva 0FN hasta 4FN, con referencia estructural autorizada al Mermaid basado en HU.
  - **Criterio de aceptación:** conservar la 0FN de partida; desarrollar 1FN, 2FN, 3FN/BCNF y la comprobación de 4FN con nombres en inglés, claves candidatas, DF, DMV, justificación de reconstrucción y trazabilidad de los atributos originales; mantener los límites clínicos y de almacenamiento, sin generar SQL.
  - **Evidencia:** `documentation/database-diagrams/Modelo_1FN.md` a `Modelo_4FN.md`, `Trazabilidad_0FN_4FN.md` y la especificación/comprobaciones en `documentation/database-diagrams/normalization/`. El perfil lógico final contiene 169 relaciones, 918 atributos y diecisiete dominios. Se comprobaron los 208 atributos originales, ocho separaciones parciales, cuatro transitivas, un ejemplo de DMV y 49 bloques Mermaid.
  - **Límite:** la conclusión de 4FN es relativa a las dependencias declaradas; no acredita reglas clínicas, campos definitivos, funcionalidad ni implementación física. La normalización documental está desarrollada; `P1-03` quedó cerrado para el alcance inicial tras la revisión técnica y la confirmación del equipo del 6 de septiembre.

## En curso

- [ ] Mantener actualizado el diseño arquitectónico durante los incrementos posteriores.
  - **Criterio de aceptación:** los cambios futuros de tecnologías cliente, contratos, límites de servicios, dimensionamiento o parámetros de seguridad y retención deberán reflejarse en las vistas afectadas.
  - **Evidencia actual:** `documentation/markdowns/Diseno_arquitectonico.md` y `documentation/docx/Diseno_arquitectonico.docx` constituyen la línea base terminada de `P1-02`, con 17 secciones, 13 diagramas, diez decisiones arquitectónicas, once unidades de servicio o soporte, tres flujos integrales y diez escenarios de comprobación.
  - **Pendiente:** actualizar la línea base únicamente cuando se concrete alguna de las decisiones reservadas para incrementos posteriores.
- [ ] Continuar la revisión evolutiva del modelo semestral antes de ampliar el diseño físico.
  - **Criterio de aceptación:** confirmar las hipótesis de identidad, cardinalidad, dominios atómicos, datos mínimos, propietarios y dependencias; definir claves, restricciones y subconjunto ejecutable de PostgreSQL sin confundir el alcance semestral con el MVP.
  - **Evidencia actual:** la 0FN de dieciocho registros permanece intacta; `Modelo_1FN.md` a `Modelo_4FN.md` desarrollan la normalización de sus grupos. La 4FN contiene 169 relaciones en diecisiete dominios, con claves y FK explícitas, trazabilidad y restricciones de integridad. `00_ER_BASADO_EN_HU.md` se consultó como referencia por nueva autorización del usuario, sin modificarlo ni considerar su diagrama una prueba de normalización.
  - **Avance físico al 2026-09-05:** subconjunto de 23 tablas y una vista implementado en `data/database/schema.sql`; sus proyecciones, restricciones y límites están documentados y se probaron con PostgreSQL real. El web usa una asignación vigente cuenta–rol–ámbito, sin productos independientes de permisos y tenants.
  - **Revisión técnica al 2026-09-06:** el subconjunto inicial ya se contrastó con el modelo lógico y los RF del primer parcial; las diferencias y sus límites están documentados en el README de datos. Las 23 tablas y su carga ficticia superaron las comprobaciones físicas y la suite completa. No falta repetir esta revisión como si no se hubiera realizado.
  - **Alcance posterior:** `P1-03` está cerrado para el primer parcial. La validación funcional del modelo semestral, migraciones, respaldos, retención y propietarios entre componentes se atenderán al ampliar el alcance. No se instalaron las 169 relaciones ni una base institucional de producción.
- [ ] Acordar con el usuario el siguiente proceso antes de habilitar vistas futuras.
  - **Criterio de aceptación:** confirmar navegación, formularios, nombres y alcance del MVP; acordar el siguiente proceso y validar sus reglas antes de convertir una vista futura en una operación persistente.
  - **Evidencia actual:** incremento del primer parcial revisado por el equipo según confirmación del usuario, con 65 pruebas aprobadas desde el entorno actual. La revisión inicial está cerrada; no es necesario repetirla como requisito para ese cierre.
  - **Pendiente:** elegir y delimitar el proceso posterior, infraestructura de despliegue y pruebas de volumen/usabilidad ampliadas; no se consideran completados por la existencia de pantallas.
- [ ] Revisar el borrador `Normalizacion_Red_Regional.xlsx` (antecedente del repositorio de origen) únicamente si se retoma expresamente este antecedente, fuera del proceso actual.
  - **Criterio de aceptación:** cada descomposición conserva información, corresponde a dependencias funcionales o multivaluadas justificadas y mantiene separados los hechos de sangre, órganos, seguridad y trazabilidad.
  - **Evidencia actual:** quince hojas relacionales con 0NF, 1NF, 2NF, 3NF y 4NF; 94 relaciones finales únicas en la propuesta de 4NF; una hoja complementaria que distingue PostgreSQL de los almacenes posteriores sin diseñarlos; identificadores estructurales en inglés, datos ficticios en español y generador reproducible.
  - **Pendiente histórico:** revisión del usuario si decide retomar este libro. Sus descomposiciones no se trasladarán a los documentos de formas normales ni al SQL del proceso actual; estos deberán derivarse de la nueva 0FN siguiendo el procedimiento que indique el usuario.

## Bloqueado

No hay bloqueos activos para el cierre del primer parcial. El usuario confirmó la revisión del equipo y la prueba de Windows, y autorizó reconstruir el entorno; la reconstrucción y sus pruebas se completaron. Las decisiones y tareas semestrales futuras conservan su alcance.

## Pendiente

### Definición del producto

- [ ] Revisar y aprobar los procesos principales y las reglas de negocio consolidadas.
- [ ] Validar mediante levantamiento con actores el contexto, las organizaciones, los procesos actuales y sus problemas reales.
- [ ] Identificar información capturada, decisiones apoyadas y actividades automatizables.
- [ ] Identificar riesgos de negocio y restricciones legales, éticas y de privacidad.
- [ ] Definir beneficios esperados y decisiones que deben conservar supervisión humana.
- [ ] Confirmar la región específica, las instituciones participantes y las reglas de incorporación a la red; México se adoptó únicamente como referencia jurídica académica provisional.
- [ ] Separar claramente los procesos, datos y reglas aplicables a sangre frente a donación de órganos.
- [ ] Validar con expertos autorizados las reglas de compatibilidad sanguínea, HLA, elegibilidad, prioridad, caducidad, conservación y asignación.
- [ ] Definir aprobaciones humanas, excepciones, anulaciones y evidencia requerida para cada decisión clínica u operativa.
- [ ] Definir consentimiento, privacidad, retención y acceso a ubicación, fotografías, estudios y datos clínicos.
- [ ] Modelar los estados de solicitudes, inventario, asignación, traslado y cadena de custodia.
- [ ] Establecer criterios de aceptación y prioridades.

### Arquitectura y contratos

- [x] Diseñar la arquitectura detallada y los límites iniciales de cada componente.
- [ ] Validar los límites, propietarios de datos, dependencias y responsabilidad de los diez microservicios iniciales.
- [ ] Diseñar el versionamiento y los contratos JSON/XML de la API.
- [ ] Diseñar y validar los esquemas XSD, codificación y espacios de nombres XML necesarios.
- [x] Diseñar la autenticación, renovación, revocación y permisos con JWT y Redis a nivel arquitectónico; los parámetros y contratos detallados permanecen pendientes.
- [ ] Definir el modelo de errores y los identificadores de correlación.
- [x] Diseñar el monitoreo, auditoría, logs, métricas y alertas a nivel arquitectónico.
- [x] Definir la estrategia inicial de operación sin conexión y sincronización móvil, limitada a operaciones seguras e idempotentes.
- [x] Diseñar al menos tres procesos integrales que atraviesen clientes, microservicios, Redis, datos, auditoría, notificaciones y archivos cuando apliquen.
- [x] Diseñar flujos integrales de solicitud urgente, asignación/traslado y cadena de custodia con recuperación ante fallos.
- [x] Elaborar diagramas de contexto, contenedores, componentes, despliegue, red, secuencia, comunicación, autenticación y almacenamiento.

### Datos

- [ ] Diseñar los modelos conceptual, lógico y físico de PostgreSQL, incluidas claves, restricciones, catálogos, auditoría y datos de prueba.
- [ ] Durante el segundo parcial, diseñar colecciones, documentos, relaciones, índices, versiones y crecimiento de MongoDB, justificando su uso.
- [ ] Durante el segundo parcial, definir estructura de claves, expiraciones, sesiones, revocaciones, caché, contadores, bloqueos y datos temporales en Redis.
- [ ] Definir estructura, metadatos, permisos, URLs firmadas y ciclo de vida de objetos en Google Cloud Storage.
- [ ] Diseñar migraciones, respaldos, restauración y retención de datos.
- [ ] Definir políticas de ocultamiento, eliminación lógica y separación de tenants cuando correspondan.
- [ ] Definir identificadores, etiquetas y referencias que preserven la trazabilidad de unidades, órganos, muestras, estudios y evidencias.
- [ ] Confirmar la distribución preliminar de datos entre PostgreSQL, MongoDB, Redis y Google Cloud Storage.

### Decisiones tecnológicas pendientes

- [ ] Elegir Java o Kotlin para Android.
- [ ] Elegir Electron, C#/.NET, Java/JavaFX o Python/PySide/PyQt para escritorio.
- [x] Conservar la estructura mínima en `Red-House`: `apps/web-monolito01`, `data/database` y `documentation`; el repositorio de origen permanece separado.
- [ ] Definir estrategia de ramas/versiones y materializar otros directorios únicamente al comenzar su componente.
- [ ] Determinar qué servicios opcionales de Google Cloud están justificados.
- [ ] Priorizar y delimitar matching, ranking, distancia, urgencia, caducidad, balanceo regional y detección de inconsistencias.
- [ ] Definir factores, ponderaciones, explicaciones, versionamiento y métricas de los algoritmos.
- [ ] Seleccionar la tecnología geográfica y las fuentes autorizadas de distancia/ubicación.
- [ ] Definir el volumen de datos y los objetivos medibles de rendimiento y escalabilidad.

### Implementación

- [x] Preparar y comprobar el entorno local y de pruebas del monolito con dependencias, variables documentadas y PostgreSQL real temporal.
- [ ] Preparar el entorno productivo y los entornos de los componentes posteriores.
- [ ] Durante el segundo parcial, configurar Docker para cada componente y Docker Compose local con PostgreSQL, MongoDB y Redis.
- [ ] Implementar el sistema web empresarial responsive con la red de instituciones, donantes, receptores, inventario, caducidad, solicitudes, compatibilidad, asignación, traslado, custodia, panel regional y auditoría.
- [ ] Implementar los servicios de donantes, receptores, inventario, compatibilidad, priorización, geografía, transporte, alertas, cadena de custodia y auditoría.
- [ ] Implementar el servicio de monitoreo de salud, latencia, versiones, errores, disponibilidad y dependencias.
- [ ] Implementar la aplicación Android para donantes y traslados: registro preliminar, campañas, citas, elegibilidad, escaneo, recolección/entrega, ubicación y fotografías autorizadas.
- [ ] Implementar la aplicación de escritorio para bancos y coordinadores: unidades, pruebas, inventario, compatibilidad, priorización, etiquetas, custodia y reportes regulatorios.
- [x] Configurar PostgreSQL para el producto mínimo: base local exclusiva, esquema y carga DEMO, sin alterar otras bases existentes.
- [ ] Configurar MongoDB y Redis desde el segundo parcial y Google Cloud Storage en el incremento de nube correspondiente.
- [ ] Configurar Google Compute Engine, red privada, firewall y secretos.
- [ ] Implementar URLs firmadas y evitar el almacenamiento de archivos grandes dentro de las bases de datos.
- [ ] Implementar y documentar las capacidades algorítmicas acordadas, incluyendo al menos un algoritmo no trivial y auditable.
- [ ] Completar al menos tres flujos integrales de principio a fin.

### Seguridad

- [x] Implementar hash scrypt de contraseñas en el monolito, sin contraseñas predeterminadas ni valores reales versionados.
- [x] Implementar JWT de acceso de 15 minutos, expiración y revocación local en PostgreSQL para el primer parcial.
- [ ] Incorporar refresh tokens, revocación y validación mediante Redis desde el segundo parcial.
- [x] Validar sesión, revocación, rol y autorización por recurso en las peticiones protegidas del monolito; extender a clientes y servicios cuando se implementen.
- [x] Implementar consultas parametrizadas, CSRF y escape de salida en el monolito; conservar estos controles en los incrementos posteriores.
- [ ] Validar JSON, XML/XSD y archivos; proteger el parser XML contra XXE.
- [x] Implementar límite de intentos de acceso, registro de fallos y bloqueo temporal en el monolito; los límites de consumo de API permanecen pendientes.
- [ ] Cifrar comunicaciones y mantener secretos fuera del código.
- [ ] Implementar auditoría, ocultamiento de datos sensibles y manejo seguro de errores.
- [ ] Aplicar retención, eliminación lógica y separación de tenants cuando el dominio lo requiera.
- [ ] Aplicar mínimo privilegio y segregación institucional a los datos clínicos, inventarios y solicitudes.
- [ ] Auditar consultas, cambios, asignaciones, decisiones, accesos sensibles y eventos de cadena de custodia.
- [ ] Evitar que datos clínicos, ubicaciones, fotografías o identificadores sensibles aparezcan en logs no autorizados.

### Calidad, seguridad y entrega

- [x] Comprobar `setup.cmd` en Windows nativo. El usuario confirmó el 6 de septiembre que otros integrantes ya realizaron esta prueba; se registra como terminada por esa confirmación, no como una ejecución en este Mac.
- [ ] Definir estrategia de pruebas unitarias, integración, sistema, regresión y extremo a extremo.
- [ ] Probar contratos JSON y esquemas XML/XSD.
- [ ] Probar autenticación, autorización, roles, expiración y revocación.
- [ ] Probar caídas de PostgreSQL, MongoDB, Redis, Storage y microservicios, incluidos timeouts y recuperación.
- [ ] Probar concurrencia, archivos grandes, datos masivos, seguridad básica y usabilidad.
- [ ] Crear escenarios Locust con múltiples perfiles y flujos reales.
- [ ] Registrar usuarios concurrentes, RPS, media, p95, p99, errores, saturación, recuperación y endpoints lentos.
- [ ] Medir inserciones, consultas, índices, caché, recursos, escalabilidad y comportamiento con y sin Redis.
- [ ] Generar documentación Swagger/OpenAPI.
- [ ] Revisar seguridad de autenticación, autorización, archivos y secretos.
- [ ] Configurar integración y despliegue continuos.
- [ ] Preparar observabilidad, recuperación ante fallos y operación.
- [ ] Verificar que una falla parcial no corrompa datos ni derribe innecesariamente toda la plataforma.

### Documentación

- [x] Crear el documento de análisis del problema.
- [ ] Crear el documento de visión y los entregables separados de objetivos, alcance, usuarios, beneficios, riesgos y restricciones cuando correspondan.
- [x] Crear la línea base de los diagramas arquitectónicos requeridos; deberá mantenerse junto con los futuros cambios del producto.
- [ ] Documentar catálogos de microservicios, contratos JSON, XML/XSD y Swagger/OpenAPI.
- [ ] Documentar seguridad, algoritmo, infraestructura GCP, contenedores, monitoreo y recuperación.
- [ ] Documentar plan de pruebas, resultados de Locust y mediciones de rendimiento.
- [x] Crear guía local de instalación, uso por perfil, esquema y pruebas del monolito en sus README.
- [ ] Completar los manuales de despliegue, técnico y de usuario del sistema semestral.
- [ ] Registrar limitaciones, trabajo futuro, conclusiones y evidencia de operación en GCP.

## Decisiones registradas

| Fecha | Decisión | Motivo | Estado |
| --- | --- | --- | --- |
| 2026-09-07 | Implementar la baja lógica sanguínea con `WITHDRAWN`, evento de movimiento y auditoría, excluyéndola de la visibilidad operativa y reservando la acción al Operador. | El usuario confirmó que no se requiere inventario de órganos todavía y solicitó conservar historial, ocultar la unidad de los listados y bloquear la baja cuando exista actividad operativa posterior al alta. El MVP no dispone aún de entidades separadas para asignación, traslado o entrega, por lo que se aplica una protección conservadora sobre cualquier movimiento posterior. | Vigente para el MVP sanguíneo; órganos y sus reglas permanecen futuros |
| 2026-09-06 | Cerrar los ocho paquetes del primer parcial y conservar en el backlog solo tareas y criterios de cierre, sin notas añadidas de avance/pendientes. | El usuario confirmó que el equipo ya hizo la revisión y la prueba en Windows; la revisión técnica estaba aprobada y el entorno propio ya está reconstruido y verificado. | Vigente; Markdown y Word sincronizados, sin modificar los cortes posteriores |
| 2026-09-06 | Reconstruir `.venv` en la ruta actual de Red-House conservando el entorno anterior fuera del repositorio. | Autorización expresa del usuario; eliminar referencias de activación y ejecutables al repositorio de origen sin cambiar `.env`, código, SQL ni datos. | Implementado; dependencias, 65 pruebas y arranque directo aprobados |
| 2026-09-06 | Registrar como completadas las verificaciones técnicas, sin cerrar formalmente los cinco paquetes con pendientes de entorno, versionado, revisión del equipo, acuerdos o Windows. | La sección 7 del plan y las dependencias del backlog exigen evidencia adicional a una ejecución exitosa. No inventar aprobaciones, commits ni pruebas de otro sistema operativo. | Reemplazada respecto del cierre por la confirmación del usuario y reconstrucción del entorno registradas arriba |
| 2026-09-06 | Probar el código actual con un entorno Python limpio y un clúster PostgreSQL exclusivo; conservar el `.venv` copiado y la configuración existente. | Se detectaron rutas de activación/pip hacia el repositorio de origen. La revisión no debe sobrescribir el entorno ni reinicializar datos mientras se resuelve su reconstrucción. | Verificado en esa revisión; conservación del entorno copiado reemplazada por la reconstrucción autorizada registrada arriba |
| 2026-09-06 | Usar nombres descriptivos como `Historias_de_usuario` y `Sprint_backlog` en los Markdown y Word de `documentation/`, conservando las siglas técnicas FN y los archivos convencionales de referencia. | Solicitud de simplificar los nombres, retirar calificativos redundantes y evitar nombres íntegramente en mayúsculas; actualizar enlaces y generadores sin duplicar documentos. | Implementado y verificado |
| 2026-09-06 | Cerrar `P1-04` con la revisión técnica responsive y registrar el avance real de `P1-03` a `P1-08`, manteniendo abiertos los paquetes con dependencias o comprobaciones pendientes. | Las interfaces y el MVP ya tienen evidencia; la normalización semestral, organización operativa del repositorio y verificación de su entorno nuevo aún requieren seguimiento. No cambiar responsables ni inferir el cierre de etapas futuras. | Sustituida respecto de estados y notas por el cierre del primer parcial registrado arriba |
| 2026-09-06 | Mantener `documentation/markdowns`, `documentation/docx` y `documentation/database-diagrams`, con `Modelo_0FN.md` como nueva ruta de la entrada original. | El usuario reorganizó el repositorio y pidió corregir las referencias. Se mantienen los antecedentes no trasladados como atribuciones históricas, sin enlaces a archivos inexistentes ni dependencias de otra carpeta local. | Implementado y verificado |
| 2026-09-06 | Fijar al 7 de septiembre de 2026 las fechas iniciales existentes; preservar fechas de planificación, citas, pruebas y bitácora. | Unificar la fecha documental por solicitud del usuario sin alterar la cronología de hechos ni regenerar el formato de los Word. | Implementado y verificado |
| 2026-09-05 | Incorporar `setup.sh` y `setup.cmd` como entradas de una única preparación Python; reutilizar `schema.sql` y `seed_demo` y mantener `run.py` como entrada con selección de `.venv`. | El usuario pidió automatizar la preparación y posteriormente arrancar con un solo comando; se evita duplicar esquema, carga o aplicación. No se cambia la instalación existente ni se instalan servicios del sistema. | Verificado aquí en macOS; Windows confirmado por el usuario el 2026-09-06 |
| 2026-09-05 | Conservar `.env` y datos existentes, rechazar colisiones de nombre sin vínculo previo, destinos remotos y esquemas incompatibles; añadir `--check` de solo lectura. | La repetición no debe reinicializar bases, cambiar contraseñas ni mezclar DEMO con datos ajenos. Una carga nueva cancelada revierte esquema y datos; base vacía/configuración se conservan para reintentar. | Implementado y probado con PostgreSQL real |
| 2026-09-05 | Preparar `.venv` y `.env` privados, crear la base local nueva `red_house` en el PostgreSQL ya instalado y ejecutar Flask en `127.0.0.1:5050`. | El usuario pidió realizar todos los pasos de ejecución local. El puerto 5000 está ocupado por macOS; se preservaron ese servicio, la configuración de PostgreSQL y las bases anteriores. | Instalado y verificado; reinicio manual de Flask documentado |
| 2026-09-05 | Implementar únicamente el monolito en `apps/web-monolito01` y el esquema en `data/database`; mantener la raíz actual y no crear carpetas vacías de otros productos. | El usuario autorizó el incremento monolítico con la estructura discutida y pidió evitar redundancia o componentes innecesarios. | Vigente |
| 2026-09-05 | Adaptar el ZIP local a Jinja2, CSS y JavaScript, conservando paleta, navegación, tipografías e iconos; sustituir gráficas React por Highcharts. | Mantener el diseño aportado y las tecnologías obligatorias, sin incorporar otro frontend desplegable. La exportación local permite trabajar sin URL o nodo de Figma. | Implementado y verificado |
| 2026-09-05 | Crear siete vistas futuras de negocio y recuperación de acceso, con avisos visibles y acciones deshabilitadas. | El usuario pidió preparar las interfaces posteriores, aunque aún no tuvieran funcionalidad; no se simulan expedientes ni decisiones clínicas. | Implementado como vistas, no como procesos |
| 2026-09-05 | Persistir el subconjunto físico de 23 tablas y una vista, con una asignación vigente de perfil/ámbito por cuenta. | Acotar el producto mínimo; conservar asociaciones y límites institucionales sin desplegar automáticamente todo el esquema lógico semestral. La proyección se explica en `data/database/README.md`. | Vigente para el MVP; ampliaciones requieren revisión y migración |
| 2026-09-05 | Mantener sesión activa, revocación e intentos en PostgreSQL y JWT corto sin refresh en el MVP. | Redis no es una dependencia ejecutable del primer parcial según la calendarización registrada. La sesión web no se comparte con futuros clientes. | Transitorio hasta el incremento de seguridad distribuida |
| 2026-09-05 | Servir Highcharts, su módulo accesible, iconos y fuentes localmente; conservar licencias y tabla alternativa. | El CDN respondió 403 durante la revisión; los recursos locales permiten demostrar el panel sin conexión a terceros. | Verificado; autorización de licencia por revisar antes de un uso fuera del contexto académico |
| 2026-09-04 | Normalizar la nueva 0FN hasta 4FN y permitir `00_ER_BASADO_EN_HU.md` como referencia estructural, conservando la entrada original y sin utilizar el Excel. | El usuario solicita expresamente avanzar hasta 4FN y autoriza consultar Mermaid anteriores. Se documentan los pasos, hipótesis, claves, DF/DMV y correspondencias; un diagrama previo no sustituye la demostración. | Vigente; normalización documental desarrollada, subconjunto físico implementado el 2026-09-05 y resto pendiente |
| 2026-09-04 | Conservar iguales los esquemas de 3FN/BCNF y 4FN cuando las listas independientes ya quedaron separadas en 1FN. | La comprobación de 4FN revisa DMV reales y no exige crear una descomposición artificial; las asociaciones permiso–rol–ámbito, candidato–factor y evento–evidencia no son productos de conjuntos independientes. | Vigente bajo las dependencias declaradas |
| 2026-09-04 | Utilizar `Modelo_0FN.md` como nueva propuesta inicial: dieciocho tablas en inglés con relaciones ER y grupos no atómicos, justificadas desde el análisis y `documentation/markdowns`. | El usuario pidió reiniciar la derivación sin basarse en modelos anteriores. Esa restricción se aplicó al crear la 0FN; posteriormente autorizó referencias Mermaid para normalizarla. | Se conserva la 0FN; la espera y restricción de referencias para la normalización fueron reemplazadas por la nueva solicitud |
| 2026-09-04 | Crear una primera propuesta de trece registros amplios en `TABLAS_GENERALES_0FN.md`, conservando grupos repetitivos, datos compuestos y redundancia. | La solicitud inicial pedía tablas generales en Mermaid sin normalizar. Su elaboración consultó modelos anteriores; el usuario solicitó posteriormente una nueva derivación exclusivamente documental. | Sustituida para el proceso actual por `Modelo_0FN.md` |
| 2026-09-03 | Mantener PostgreSQL como almacenamiento funcional del primer parcial y trasladar el diseño detallado, instalación, configuración y uso de MongoDB, Redis y Docker al segundo parcial; durante el primer corte estas tres tecnologías solo se investigan y aparecen en la arquitectura objetivo. | El profesor indicó que MongoDB, Redis y Docker aún no se han estudiado. La secuencia conserva el alcance semestral completo sin convertir tecnologías no vistas en dependencias del producto mínimo. | Vigente |
| 2026-09-03 | Incorporar al plan semestral los responsables principales ya definidos en el Sprint Backlog y conservar la asignación de revisores en el tablero. | Mantener una sola distribución nominal para los 29 paquetes y hacer visible la responsabilidad sin añadir una sexta columna que reduzca la legibilidad. | Vigente; revisores y fechas oficiales por confirmar |
| 2026-09-02 | Utilizar los 29 identificadores del plan como elementos del Sprint Backlog y dividir su presentación en cuatro tablas, una por sprint. | Conservar trazabilidad directa con el plan y evitar la tabla de diez columnas del antecedente, que repetía RF/RNF y reducía la legibilidad. Los frentes permanecen como responsables funcionales; la asignación nominal se realizará en el tablero. | Reemplazada el 2026-09-03 respecto de la asignación nominal; permanece vigente la estructura del backlog |
| 2026-09-02 | Adoptar como línea base una arquitectura incremental: sistema web modular para el MVP y capacidades compartidas en microservicios a partir del segundo parcial. | Mantener un primer incremento ejecutable y viable, sin duplicar reglas cuando se incorporen Android y escritorio; los módulos del web se alinean con las fronteras posteriores. | Vigente como línea base arquitectónica |
| 2026-09-02 | Conservar las diez responsabilidades de dominio y agrupar inicialmente priorización y geografía en `ms-priorizacion-geografia`; añadir identidad y acceso como capacidad técnica compartida y monitoreo como servicio de soporte. | Distancia y tiempo alimentan directamente el ranking; la agrupación reduce operación académica y mantiene contratos distinguibles. Identidad es necesaria para que los clientes no compartan la sesión interna del web. | Propuesta; límites por validar antes del segundo parcial |
| 2026-09-02 | Utilizar instancias académicas compartidas de PostgreSQL, MongoDB y Redis con propiedad lógica, esquemas, colecciones, claves y credenciales separadas por servicio. | Reducir costo y administración sin crear múltiples fuentes de verdad ni permitir escrituras cruzadas; los clientes continúan sin acceso directo. | Propuesta; pendiente de reconciliación con los modelos de datos |
| 2026-09-02 | Organizar el despliegue objetivo en tres grupos lógicos de Compute Engine —entrada/web, servicios y datos— y no adoptar clúster, balanceador o mensajería hasta contar con mediciones que los justifiquen. | Proporcionar separación suficiente para la demostración académica y evitar infraestructura opcional anticipada; la línea base no se presenta como alta disponibilidad sanitaria. | Propuesta; pendiente de dimensionamiento y aprobación |
| 2026-09-01 | Organizar el plan semestral mediante los cuatro cortes oficiales y paquetes con responsable principal y revisor, sin inventar fechas ni nombres. | `entregas.txt` define etapas y un equipo de cuatro personas, pero no proporciona calendario concreto ni integrantes; la asignación nominal corresponde al tablero cuando esos datos sean confirmados. | Reemplazada el 2026-09-03 respecto de los nombres; permanece vigente la organización por cortes |
| 2026-09-01 | Definir la autorización como la combinación de perfil, acción, recurso y ámbito institucional, y expresar los niveles como responsabilidades funcionales no jerárquicas. | Evitar que un perfil con mayor alcance administrativo se interprete como autoridad clínica, conservar mínimo privilegio y representar los siete roles sin crear perfiles adicionales para cada institución o proceso. | Vigente; pendiente de aprobación funcional |
| 2026-09-01 | Consolidar las reglas de negocio en 40 reglas identificadas por dominio y no crear una regla por cada requisito o criterio de aceptación. | Mantener el documento manejable, separar políticas del dominio de requisitos técnicos y conservar trazabilidad sin inventar reglas clínicas, fórmulas ni ponderaciones. | Vigente; pendiente de aprobación funcional |
| 2026-08-31 | Eliminar del documento de historias la sección final “Cobertura y límites de esta versión”. | Su contenido repetía el propósito, los criterios transversales y las relaciones indicadas en cada ficha; la comprobación integral corresponde a la futura matriz de trazabilidad y al seguimiento interno. | Vigente |
| 2026-08-31 | Mostrar el perfil de cada HU dentro de su tabla y reservar `Responsable técnico` para las historias habilitadoras. | Hacer visible el actor sin depender de negritas dentro de la redacción, utilizar los siete perfiles consolidados del análisis y evitar presentar a equipos técnicos como usuarios funcionales. | Vigente |
| 2026-08-31 | Retirar del documento de historias la sección “Resumen del backlog” y la enumeración del subconjunto del primer parcial. | La rúbrica no exige ese resumen, cada historia ya conserva fase y prioridad, y la selección de implementación corresponde al plan de trabajo o Sprint Backlog. | Vigente |
| 2026-08-31 | Sustituir para revisión las 55 historias del borrador anterior por 35 historias de valor y 9 historias habilitadoras, conservando intactos los archivos originales. | Evitar una historia por requisito, utilizar únicamente los siete perfiles acordados, separar capacidades técnicas de necesidades humanas y conservar cobertura explícita de los 53 RF y 41 RNF. | Vigente; pendiente de aprobación funcional |
| 2026-08-31 | Consolidar el borrador de 144 requisitos en una versión de 94 —53 RF y 41 RNF— y no crear una historia de usuario independiente por cada requisito. | Reducir duplicaciones entre interfaz, servicio y algoritmo; agrupar acciones del mismo objetivo; y mantener las historias enfocadas en flujos de valor, dejando los RNF vinculados principalmente a criterios técnicos y pruebas. | Vigente; pendiente de aprobación funcional |
| 2026-08-31 | Eliminar del entregable de RF/RNF las secciones “Trazabilidad con el borrador anterior” y “Decisiones de alcance de esta versión”. | La primera era una ayuda interna de migración y no la matriz de trazabilidad solicitada; la segunda repetía decisiones conservadas en el análisis y en este seguimiento. El entregable debe concentrarse en los requerimientos aprobables. | Vigente |
| 2026-08-31 | Crear `REQUERIMIENTOS_FUNCIONALES_Y_NO_FUNCIONALES.md` y `.docx` como nueva versión clasificada por componente y conservar sin modificaciones `Req Funcionales y No Funcionales.docx`. | Aplicar la clasificación exigida por la rúbrica, mantener trazabilidad con el borrador de origen y permitir una revisión segura antes de reemplazar cualquier antecedente. | Reemplazada por la versión consolidada |
| 2026-08-31 | Hacer que el análisis, los requisitos, las historias y los demás entregables funcionales cubran todo el proyecto; utilizar los parciales solo para clasificar y priorizar la implementación. | Evitar que la delimitación del producto mínimo se interprete como eliminación de las capacidades posteriores del alcance documental. | Vigente |
| 2026-08-31 | Colocar las referencias como última sección del análisis, después del resultado de la validación y la conclusión. | Seguir una organización académica convencional y facilitar la lectura continua del cierre antes de consultar las fuentes. | Vigente |
| 2026-08-31 | Eliminar la sección de supuestos iniciales del análisis y conservar sus decisiones relevantes únicamente en los apartados específicos de límites, alcance, responsabilidad humana y marco jurídico. | La rúbrica no solicita una sección de supuestos y su contenido ya estaba desarrollado en otras partes del documento. | Vigente |
| 2026-08-31 | Eliminar del documento de análisis la sección de preguntas abiertas y conservar las decisiones todavía no resueltas en el seguimiento y en los futuros requisitos; presentar las referencias con citas autor-fecha y lista APA 7. | Evitar que el entregable parezca un cuestionario inconcluso sin ocultar los pendientes reales, y uniformar la atribución académica de las fuentes. | Vigente |
| 2026-08-31 | Consolidar los perfiles en Administrador, Operador de banco de sangre, Personal médico autorizado, Coordinador regional, Personal de traslado, Donante y Auditor; habilitar durante el MVP únicamente Administrador, Operador y Auditor. | Reducir complejidad académica sin perder la separación entre administración, operación, decisión clínica, coordinación, traslado, donación y auditoría. | Vigente |
| 2026-08-31 | Usar México como referencia jurídica académica provisional, sin afirmar cumplimiento regulatorio ni despliegue en una institución real. | Permitir un análisis concreto y verificable sin convertir el documento en asesoría jurídica ni inventar la región definitiva. | Vigente para documentación académica |
| 2026-08-31 | Acotar el MVP del primer parcial al sistema web con instituciones, tipos de componentes sanguíneos, inventario básico, caducidad demostrativa, persistencia y auditoría. | Cumplir la demostración con un flujo pequeño completo y evitar implementar reglas clínicas, órganos y algoritmos antes de validarlos. | Vigente |
| 2026-08-27 | Utilizar inglés para hojas, tablas, atributos y rótulos estructurales del Excel, manteniendo en español los valores ficticios almacenados como datos. | Establecer desde el modelado una nomenclatura técnica consistente sin alterar el contenido demostrativo solicitado. | Vigente |
| 2026-08-27 | Modelar las citas con `current_status` y `APPOINTMENT_STATUS_HISTORY`. | Una cita solo puede tener un estado vigente, pero debe conservar de forma auditable todos sus cambios anteriores. | Borrador por validar transiciones |
| 2026-08-27 | Organizar el libro Excel con una hoja por registro o tabla inicial y mostrar dentro de ella las tablas que nacen al normalizar. | Reproducir la lógica de la plantilla académica y conservar la trazabilidad visual de cada descomposición. | Vigente |
| 2026-08-27 | Incluir quince hojas relacionales de 0FN a 4FN y una hoja informativa para los almacenes complementarios. | Las formas normales aplican a PostgreSQL; MongoDB, Redis y Cloud Storage requieren modelos propios. | Borrador por validar |
| 2026-08-27 | Utilizar exclusivamente datos ficticios e identificar como `DEMO` cualquier valor relacionado con compatibilidad, urgencia, rutas o algoritmos. | Evitar presentar ejemplos académicos como reglas clínicas o datos reales. | Vigente |
| 2026-08-27 | Representar la 0FN mediante varios registros orientados a procesos, en lugar de una relación universal iniciada por una solicitud. | Instituciones, campañas, citas, altas de personas, inventario, alertas, archivos y sincronización existen independientemente de una solicitud; la normalización no puede recuperar hechos ausentes. | Vigente |
| 2026-08-27 | Normalizar posteriormente solo los registros transaccionales destinados a PostgreSQL y diseñar MongoDB, Redis y Cloud Storage por separado. | Los modelos documental, clave-valor y de objetos no siguen las formas normales relacionales y tienen ciclos de vida distintos. | Vigente |
| 2026-08-27 | Mantener los modelos de datos como Mermaid y Markdown dentro de `documentation/database-diagrams`. | Permitir visualización local en VS Code, revisión por diferencias y versionamiento junto con el código. | Vigente |
| 2026-08-27 | Diseñar primero el ER conceptual, documentar una relación 0FN y avanzar después por 1FN, 2FN, 3FN y 4FN antes del SQL definitivo. | Separar la comprensión del dominio de la implementación física y conservar evidencia de cada descomposición. | Vigente |
| 2026-08-27 | No instalar una extensión externa de Mermaid en el entorno actual. | VS Code 1.134.0 ya incorpora Mermaid; la extensión histórica fue integrada al editor y duplicarla es innecesario. | Vigente |
| 2026-08-12 | Usar `AGENTS.md` como contexto persistente y `PROJECT_STATUS.md` como seguimiento. | Separar los requisitos estables del avance cambiante y facilitar la continuidad entre conversaciones. | Vigente |
| 2026-08-12 | Mantener web, microservicios, Android y escritorio como componentes desacoplados. | Es una restricción obligatoria del proyecto. | Vigente |
| 2026-08-12 | Reservar JSON para Android y XML para escritorio. | Es una restricción obligatoria de integración. | Vigente |
| 2026-08-12 | Registrar la cantidad de seis a diez microservicios como recomendación, no como obligación. | La especificación la presenta como una cantidad sugerida y condicionada al proyecto. | Vigente |
| 2026-08-12 | Posponer responsables, calendario, parciales y metodología de sprints. | El usuario indicó ignorar por entonces la división del equipo y los tiempos de entrega. | Reemplazada parcialmente el 2026-09-01: ya se definieron etapas y frentes; fechas exactas, asignaciones nominales y metodología de sprints continúan pendientes |
| 2026-08-12 | Adoptar el dominio de red regional de bancos de sangre y donación de órganos. | Es el Proyecto 6 asignado al Equipo 01. | Vigente |
| 2026-08-12 | Tratar matching, ranking y priorización como apoyo auditable a la decisión. | La plataforma no puede sustituir la evaluación médica, ética o normativa. | Vigente |
| 2026-08-12 | Dirigir la aplicación móvil a donantes y personal de traslado, y la de escritorio a bancos y coordinadores. | Son los consumidores y procesos definidos en la descripción del proyecto. | Vigente |
| 2026-08-12 | Usar como catálogo inicial diez servicios del dominio. | La descripción enumera donantes, receptores, inventario, compatibilidad, priorización, geografía, transporte, alertas, custodia y auditoría. | Por validar límites |
| 2026-08-12 | Considerar siete capacidades algorítmicas esperadas. | La descripción solicita matching, ranking, distancia, urgencia, caducidad, balanceo e inconsistencias. | Por priorizar |
| 2026-08-12 | Mantener el análisis como documento funcional, no como especificación médica. | La región, las reglas clínicas y la normativa aún requieren validación especializada. | Vigente |
| 2026-08-12 | Usar DOCX como formato de entrega del análisis y conservar Markdown como fuente. | DOCX puede abrirse en Microsoft Word e importarse en Google Docs; Markdown facilita futuras revisiones controladas. | Vigente |

## Riesgos y observaciones

- **Resuelto:** el `.venv` copiado con rutas antiguas fue respaldado fuera del repositorio y sustituido por un entorno creado en la ubicación actual. Activación, ejecutables, dependencias y arranque comprobados; no copiar este entorno a otra ruta o equipo, sino ejecutar allí el instalador.
- La inspección local de Git muestra `README.md` versionado y la rama `main`; esta actualización no realiza commits, ramas ni publicaciones. El cierre del backlog se registra por autorización del usuario y su confirmación de la revisión del equipo, sin atribuir al agente operaciones de Git ni evidencias externas no examinadas.
- La preparación automatizada requiere Python 3.12+, PostgreSQL 14+ activo y permisos adecuados para crear una base nueva; no instala ni arranca servicios. En Windows `.env` hereda los permisos de la carpeta y debe mantenerse privado; el modo POSIX `600` no configura ACL de Windows. La prueba nativa fue confirmada por el usuario como realizada por el equipo.
- El incremento verificado es exclusivamente académico y local. No hay validación clínica, recuperación por correo, refresh tokens, despliegue WSGI/TLS, permisos mínimos PostgreSQL diferenciados, RLS, respaldos ni evidencia de carga considerable; no debe publicarse ni utilizar datos reales como si estuviera listo para operación sanitaria.
- El esquema mínimo y la restricción de una asignación vigente por cuenta necesitan migraciones explícitas al ampliar roles, reglas, contactos, geografía o propietarios. No debe sustituirse la base existente ejecutando de nuevo `schema.sql`.
- El umbral de 72 horas y las transiciones de inventario son DEMO; las fechas capturadas no se calculan con vidas útiles clínicas. El historial rechaza cambios ordinarios mediante triggers, pero no es una garantía frente al propietario de PostgreSQL.
- Highcharts conserva una licencia independiente; revisar las condiciones aplicables antes de distribuir o desplegar fuera de la demostración académica. No se incorporó un servicio externo de exportación de gráficas.
- Concentrar MongoDB, Redis, microservicios y Docker en el segundo parcial incrementa la carga de aprendizaje e integración de esa etapa; el documento introductorio y las fronteras arquitectónicas del primer parcial deberán utilizarse para preparar decisiones sin adelantar configuración o implementación.
- Las fechas de cierre del nuevo Sprint Backlog proceden del documento de referencia anterior y deberán confirmarse contra el calendario oficial; no se utilizaron para inferir fechas de inicio ni asignaciones personales.
- El Sprint Backlog registra el cierre del primer parcial con evidencia técnica y confirmación del equipo comunicada por el usuario el 6 de septiembre. La fecha de edición documental sigue siendo el 7 de septiembre por solicitud del usuario; no es la fecha real de ejecución de las pruebas ni de una revisión Windows presenciada por este agente.
- La agrupación inicial de priorización y geografía y la transición de propietarios desde el web hacia microservicios son propuestas arquitectónicas; deberán aprobarse antes de fijar contratos o migraciones para evitar dos escritores y dependencias circulares.
- La distribución en tres grupos de Compute Engine es una línea base lógica no dimensionada. Su correspondencia con máquinas, costos, respaldos y objetivos de recuperación debe confirmarse antes del despliegue.
- La validación del análisis es documental y académica; no incluye entrevistas, observación de procesos ni aprobación clínica o jurídica. Esto no bloquea el MVP ficticio, pero sí cualquier afirmación de preparación para uso real.
- El perfil lógico ya cuenta con una normalización documentada hasta 4FN, pero sus dependencias, campos y cardinalidades son hipótesis académicas. No debe convertirse automáticamente en migraciones o SQL ni desplegar sus 169 relaciones como requisito del primer parcial.
- Los 208 atributos de 0FN tienen destinos comprobados, pero la cobertura de nombres y las pruebas con datos DEMO no demuestran por sí solas la semántica de todos los objetos abiertos ni la ausencia de dependencias clínicas desconocidas. Una nueva DF o DMV obliga a revisar la forma normal.
- Los registros 0FN son deliberadamente redundantes y multivaluados para fines didácticos; no representan recomendaciones de tablas o columnas JSONB en PostgreSQL.
- La 0FN ampliada mejora la cobertura, pero sus campos no sustituyen el levantamiento regulatorio ni la validación de reglas, estados, catálogos, propietarios y datos mínimos.
- El libro Excel es un borrador didáctico; sus tablas 1FN–4FN no deben convertirse en migraciones hasta documentar claves, dependencias y revisión funcional en los archivos Markdown correspondientes.
- El alcance es amplio y requerirá fases e hitos claros para evitar que todos los componentes avancen sin contratos estables.
- La convivencia de JSON y XML exige contratos, validación y pruebas específicas para impedir divergencias entre clientes.
- La infraestructura obligatoria incluye varios servicios distribuidos; el entorno local debe diseñarse para que sea reproducible y no dependa innecesariamente de la nube durante el desarrollo.
- El procesamiento simultáneo de JSON y XML amplía la superficie de validación; la protección XXE y las pruebas XSD son requisitos explícitos.
- El alcance de seguridad y tolerancia a fallos es transversal; implementarlo tarde produciría retrabajo en todos los componentes.
- Sangre y órganos tienen procesos, compatibilidades, tiempos, conservación y obligaciones regulatorias diferentes; modelarlos como un único tipo genérico sería riesgoso.
- La plataforma procesa información clínica, identidad, ubicación y evidencias; una fuga o autorización incorrecta tendría impacto alto.
- Los algoritmos de compatibilidad y prioridad pueden afectar decisiones críticas; deben ser explicables, versionados, probados y sujetos a aprobación humana.
- La asignación concurrente de recursos requiere controles para impedir duplicidad, pérdida de trazabilidad o estados inconsistentes.
- Caducidad, urgencia, distancia y disponibilidad hacen que los datos cambien rápidamente; caché y sincronización deben evitar decisiones basadas en información obsoleta.
- La operación interinstitucional exige definir claramente tenants, intercambio autorizado de datos y responsabilidades sobre cada registro.

## Verificaciones realizadas

| Fecha | Verificación | Resultado |
| --- | --- | --- |
| 2026-09-06 | Entorno reconstruido en la ruta actual: activación, ejecutables, `pip check`, `setup.sh --check`, suite completa con PostgreSQL temporal y Chrome, y arranque con `python3 run.py`. | PASS: **65 pruebas, 40.92 s; 0 fallos, 0 errores y 0 omisiones**. HTTP 200 en `/health/live`, `/` y `/login` sin activación manual. Los 155 archivos ajenos a `.venv` permanecieron idénticos durante la verificación; `.env`, código y datos conservados. Clúster y servidor temporales detenidos. Informes `Tests_venv.xml` y `Environment_check.json` en la carpeta de evidencia. |
| 2026-09-06 | Confirmación humana del cierre y sincronización documental. | El usuario confirmó la revisión por otros integrantes y la prueba Windows. Backlog: 29 elementos, 8 terminados y 21 pendientes, sin notas de avance/pendientes, con tareas, criterios, responsables y dependencias conservados. Word: 14 tablas, integridad y lectura nativa comprobadas; las demás partes OOXML permanecen idénticas. |
| 2026-09-06 | Suite actual de `Red-House`: `python -m pytest -q --tb=short --browser -s -p no:cacheprovider`, con entorno limpio, PostgreSQL temporal exclusivo y Chrome. | PASS: **65 pruebas, 40.80 s; 0 fallos, 0 errores, 0 omisiones**. Highcharts renderizado, cero excepciones JavaScript y cero recursos faltantes; formularios, persistencia, permisos, aislamiento, auditoría y responsive comprobados. Resultado JUnit y capturas en `documentation/evidence/primer-parcial/`. Los 148 archivos inspeccionados permanecían idénticos al terminar las pruebas. |
| 2026-09-06 | Reconciliación del SQL inicial con el modelo lógico y consulta del catálogo de PostgreSQL temporal. | PASS técnico: 23 tablas, 23 PK, 24 FK y 21 CHECK, sin columnas JSON ni arreglos; 2 instituciones, 4 cuentas y 36 unidades, con 36 filas en la vista. Se documentaron las diferencias de claves/cardinalidades y el soporte técnico local. El verificador lógico aprobó 169 relaciones, 918 atributos, 208 atributos de origen y 49 diagramas. No se certificó el SQL completo como 4FN ni se cambiaron reglas clínicas. |
| 2026-09-06 | `PYTHONDONTWRITEBYTECODE=1 sh apps/web-monolito01/setup.sh --check`, instalación de dependencias limpia y revisión de Git/rutas del entorno. | PASS de consulta: configuración y base existentes conservadas, 2 instituciones/4 cuentas/36 unidades; `pip check` del entorno limpio sin dependencias incompatibles y secretos excluidos de Git. Hallazgos: `.venv` copiado con referencias a `proyectoPrueba`, solo `README.md` versionado y Windows nativo no comprobado. No se confunden estos pendientes con fallos de la suite. |
| 2026-09-06 | Sincronización del backlog y normalización de nombres en `Red-House`. | PASS: 28 renombres; 29 elementos y responsables conservados, criterios de cierre y dependencias intactos, estados 3 terminados / 5 en proceso / 21 pendientes coincidentes en Markdown y Word. Cero enlaces relativos rotos entre 58 comprobados; 12 fechas iniciales Markdown y 11 Word conservadas. El backlog mantiene sus 14 tablas y las demás partes OOXML sin cambios; los diez Word restantes conservan todos sus bytes. Lectura nativa de los once Word comprobada. |
| 2026-09-06 | `node documentation/database-diagrams/normalization/validate.mjs`, después del cambio de nombres. | PASS: 169 relaciones, 918 atributos, 208 atributos de origen y 49 diagramas aceptados; documentos generados coincidentes con los nombres nuevos. Los 63 bloques Mermaid de la selección documental y 110 archivos de código, SQL, configuración y modelos protegidos permanecen idénticos. |
| 2026-09-06 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_validation.py`, desde el monolito de `Red-House`. | PASS: 7 pruebas en 0.02 s. Comprobación de validación y permisos sin crear bases, arrancar la aplicación ni instalar dependencias. No equivale a repetir aquí la suite histórica de 65 pruebas con PostgreSQL y Chrome. |
| 2026-09-06 | Rutas y fechas de la selección documental de `Red-House`. | PASS: 12 encabezados Markdown y 11 DOCX con la fecha solicitada; cero enlaces relativos rotos. En cada Word solo cambió el texto de un párrafo inicial de `word/document.xml`; estilos, imágenes, relaciones y demás partes conservadas byte a byte, integridad ZIP/XML y lectura nativa de los 11 archivos comprobadas. Se conservaron las fechas del cuerpo y los 63 bloques Mermaid originales. |
| 2026-09-06 | `node documentation/database-diagrams/normalization/validate.mjs`, con rutas adaptadas. | PASS: 169 relaciones, 918 atributos, 208 atributos de origen, 4 etapas, 12 reconstrucciones por DF, testigo de DMV y contraejemplo de permisos; 49 diagramas aceptados y coincidencia exacta entre los Markdown y su generador. Solo se adaptaron referencias documentales, no tablas, atributos, dependencias ni algoritmos. |
| 2026-09-05 | Suite ampliada del monolito y del instalador: `.venv/bin/python -m pytest -q --tb=short --browser -s`, con clúster PostgreSQL temporal y Chrome. | PASS: **65 pruebas, 53.25 s**. Incluye 33 casos del instalador: validación de destinos/puertos, secreto no expuesto, archivo privado y exclusivo, rutas con espacios, selección de entorno, instalación nueva/repetición, conservación de contraseñas y auditoría, colisiones, objetos ajenos, esquema parcial, cancelación con rollback y modo de solo lectura. Chrome: Highcharts cargado, cero excepciones y cero recursos faltantes. Capturas en `/private/tmp/red-house-installer.ZiELgb/screenshots`. |
| 2026-09-05 | Instalación completa desde `sh setup.sh` en una copia sin `.env` ni `.venv`, con espacio en la ruta; repetición y arranque mediante `python3 run.py`. | PASS: entorno y paquetes instalados, base nueva `red_house_setup_e2e_zielgb` exclusivamente en el clúster temporal del puerto 55471, esquema y 4 cuentas/36 unidades; segunda ejecución sin solicitar contraseña ni duplicar datos. HTTP 200 en salud y cuatro recorridos acceso → panel → cierre en el puerto 5051 sin activar `.venv`. Se detuvo esa copia, se retiró exclusivamente su base ficticia regenerable y se detuvo el clúster de pruebas. Evidencia auxiliar en `/private/tmp/red-house-installer.ZiELgb/verify.py`. |
| 2026-09-05 | Preservación del entorno original y controles estáticos del instalador. | PASS: `setup.sh --check` conserva 2 instituciones, 4 cuentas y 36 unidades; `.env` original y temporal idénticos antes/después de las comprobaciones por hash, exclusión Git comprobada, aplicación original aún responde en 5050. Sintaxis `sh`, compilación Python, `pip check` y `git diff --check` aprobados. No hay Windows disponible en este equipo: no se declara comprobada la ejecución nativa de CMD. |
| 2026-09-05 | Instalación persistente y comprobación contra la aplicación local del usuario. | PASS: `pip check` sin incompatibilidades, siete pruebas unitarias aprobadas en la nueva `.venv`, 23 tablas/dos instituciones/cuatro cuentas/36 unidades en `red_house`, HTTP 200 y cuatro recorridos de inicio → panel Highcharts → vista autorizada → cierre en Chrome, sin errores de JavaScript ni recursos faltantes. No se agregaron unidades de prueba extra al conjunto inicial. `.env` con permisos `600` y excluido de Git; ninguna clave ni contraseña se documentó en archivos versionados. |
| 2026-09-05 | Suite completa del monolito antes de incorporar el instalador: `python -m pytest -q --tb=short --browser -s`, con `TEST_POSTGRES_URL`, Playwright externo y Chrome local. | PASS: **32 pruebas, 39.09 s**. Bases PostgreSQL 14.23 aleatorias por caso, esquema real y fixtures sintéticos; autenticación/CSRF, expiración/revocación, ámbitos y perfiles, administración, inventario, caducidad, concurrencia, rollback, auditoría, reinicialización rechazada, pérdida de conexión y recuperación. Ninguna base de usuario fue reutilizada o borrada. |
| 2026-09-05 | Recorrido Chrome y revisión de capturas de sitio público, acceso, panel, inventario, alta/movimiento, instituciones, configuración, auditoría y vistas futuras. | PASS: escritorio 1440×1000 y móvil 390×844; alta y movimiento persistidos al recargar, gráfica Highcharts real, menú accesible, tabla desplazable y ausencia de desbordamiento horizontal de página. `chartLoaded=true`, cero excepciones JavaScript y cero recursos locales faltantes. Capturas reproducibles mediante `BROWSER_ARTIFACTS`; evidencia temporal de esta ejecución en `/private/tmp/red-house-verify.5g99bi/screenshots`. |
| 2026-09-05 | Comprobaciones estáticas y entorno. | PASS: compilación Python, sintaxis de JavaScript propio y prueba de navegador, `pip check` sin dependencias incompatibles, enlaces relativos de los tres README sin destinos faltantes y `git diff --check`. Dependencias directas fijadas; secretos y artefactos temporales excluidos del repositorio. |
| 2026-09-04 | Normalización 1FN–4FN y comprobación reproducible con `node documentation/database-diagrams/normalization/validate.mjs`. | PASS: 169 relaciones, 918 atributos, 208 atributos de origen trazados, claves declaradas mínimas respecto de sus DF, FK y tipos coherentes, ocho casos de dependencia parcial y cuatro transitivos, doce reconstrucciones por DF y rechazo de copias inconsistentes. Se comprobó una reconstrucción por DMV, un contraejemplo que rechaza la separación indebida de permisos y ámbitos, y la conservación de anclas vacías y valores repetidos en el ejemplo de extracción. Los cuatro esquemas y los 49 bloques Mermaid fueron aceptados; los Markdown coinciden con la especificación. La evidencia no sustituye revisión funcional ni descubre dependencias desconocidas. |
| 2026-09-04 | Validación de la nueva derivación documental ER 0FN. | El analizador Mermaid local aceptó el diagrama con dieciocho tablas, 208 atributos y 26 relaciones. Se comprobó que no hubiera tablas o atributos duplicados, que cada relación usara entidades declaradas, que todas las tablas conservaran grupos repetitivos y tuvieran justificación documental, y que existieran los ocho documentos enlazados y los 95 identificadores citados. Se revisaron las propuestas de cardinalidad, la separación de sangre y órganos, los grupos anidados y las fronteras de almacenamiento. Es evidencia sintáctica y documental, no aprobación clínica ni funcional. |
| 2026-09-04 | Revisión de la propuesta de tablas generales 0FN y validación local de Mermaid. | El analizador Mermaid instalado con VS Code aceptó los cinco bloques, que contienen trece tablas. Se revisaron el significado de cada fila, los grupos repetitivos, la separación de sangre y órganos, las referencias provisionales y la ausencia de reglas clínicas nuevas, SQL o descomposición normalizada. El validador temporal previo tenía una ruta de módulo obsoleta; se utilizó el módulo instalado actual sin cambiar dependencias. |
| 2026-09-03 | Revisión de calendarización y documento introductorio de MongoDB, Redis y Docker. | Se verificó que PostgreSQL permanece en el primer parcial y que el diseño detallado, configuración y uso funcional de MongoDB, Redis y Docker comienzan en el segundo. Se sincronizaron `entregas.txt`, el contexto persistente, análisis, RF/RNF, historias, casos de uso, trazabilidad, plan, Sprint Backlog, arquitectura y notas de datos. Los diez DOCX regenerados son paquetes OOXML íntegros; permanecen 94 requisitos, 44 historias, 40 reglas, 15 casos de uso y 29 paquetes, sin cambiar responsables ni estados del backlog. |
| 2026-09-03 | Validación de responsables principales en el plan semestral. | Los 29 paquetes identifican exactamente una persona y conservan su frente: Alejandra Morón 7, Alberto Reyna 8, Galia Sejudo 8 y Victor Berlanga 6. Las asignaciones coinciden con el Sprint Backlog; Markdown y DOCX mantienen las mismas diez tablas de contenido, el Word conserva 11 tablas contando el bloque de estado, integridad OOXML y una vista previa legible. |
| 2026-09-03 | Validación de la matriz general y del desglose renumerado. | Se comprobó una vista general con ocho componentes y una fila de cobertura integral, seguida por las ocho matrices detalladas. Permanecen 94 filas individuales y 94 IDs únicos; los apartados avanzan de forma consecutiva del 1 al 13. El DOCX contiene 13 tablas, mantiene orientación horizontal, fuente de 9 puntos en la nueva matriz e integridad OOXML. |
| 2026-09-02 | Validación integral de los casos de uso y la matriz de trazabilidad. | Se comprobaron 15 casos de uso principales y 94 filas únicas de requisitos, sin faltantes, duplicados ni referencias inexistentes. La matriz cubre los 53 RF, 41 RNF, 35 HU, 9 HE, 40 RN, 15 CU y 9 tipos de verificación; sus fases coinciden con el documento de requerimientos. Los DOCX conservan el diseño homologado, tablas legibles e integridad OOXML. |
| 2026-09-02 | Validación estructural, de contenido y legibilidad del Sprint Backlog. | Se comprobaron 29 identificadores únicos distribuidos 8+8+8+5, con tareas y criterios de cierre iguales a los del plan semestral; el estado actualizado contiene dos elementos terminados, cuatro en proceso y 23 pendientes. El DOCX contiene 14 tablas, encabezados repetibles, filas no divisibles, anchos controlados, fuente mínima de 9.5 puntos e integridad OOXML. |
| 2026-09-02 | Validación estructural y editorial del diseño arquitectónico. | Se comprobaron 17 secciones, 13 bloques Mermaid con cierres y numeración consistentes, las nueve vistas obligatorias y cuatro secuencias de negocio además de autenticación. El DOCX contiene 13 diagramas incrustados sin código Mermaid expuesto, 20 tablas y estructura ZIP/XML íntegra. Se verificó la eliminación de los apartados redundantes de restricciones y documentos de base, así como la ausencia de expresiones orientadas al cumplimiento de la solicitud. |
| 2026-09-02 | Revisión cruzada del diseño contra `proyecto.txt`, `entregas.txt`, `arquitectura.txt` y los documentos consolidados. | Se verificaron los cuatro productos, perfiles y MVP vigentes; JSON exclusivo para Android, XML/XSD exclusivo para escritorio y producción de ambas respuestas en servicios; OpenAPI/Swagger; distancia y tiempo; propiedad autoritativa; PostgreSQL, MongoDB, Redis y Storage; contenedores, Compute Engine, red, seguridad, monitoreo, tres flujos integrales y clúster condicionado. No se eligieron tecnologías cliente, fórmulas clínicas, proveedores ni parámetros no confirmados. |
| 2026-09-01 | Depuración académica del plan de trabajo semestral. | Se eliminó `2.3 Línea base al iniciar el plan` por duplicar el seguimiento operativo y se reformularon las referencias a las fuentes del curso, al rango de microservicios, al catálogo inicial y al entorno `ubiquitous`. Permanecen las cuatro etapas, 29 paquetes, tres flujos, ocho dependencias, ocho frentes, diez riesgos y ocho indicadores. Markdown y DOCX coinciden; el Word conserva 11 tablas, integridad OOXML y diseño homologado. |
| 2026-09-01 | Validación estructural, de cobertura y visual del plan de trabajo del semestre. | Se comprobaron las cuatro etapas oficiales y 29 paquetes secuenciados: 8 del primer parcial, 8 del segundo, 8 del tercero y 5 de entrega final. Permanecen tres flujos integrales, ocho dependencias, ocho frentes, diez riesgos y ocho indicadores. El plan cubre las tecnologías, productos, datos, seguridad, nube, algoritmos, pruebas y límites clínicos obligatorios sin inventar semanas o nombres. Markdown y DOCX coinciden; el Word contiene 12 tablas íntegras y conserva el diseño homologado. |
| 2026-09-01 | Simplificación semestral de la matriz de perfiles y permisos. | Se eliminaron el apartado exclusivo de permisos del primer parcial y la trazabilidad principal por perfil, debido a que la fase ya está incluida en las tablas vigentes y la rúbrica contempla una matriz de trazabilidad independiente. Participantes sin perfil pasó a ser el punto 6. Permanecen siete perfiles, tres perfiles iniciales identificados y 32 operaciones protegidas. Markdown y DOCX coinciden; el Word conserva 7 tablas, integridad OOXML y el diseño homologado. |
| 2026-09-01 | Validación estructural, funcional y visual de la matriz de perfiles y permisos. | Se comprobaron exactamente siete perfiles consolidados, únicamente tres perfiles iniciales, 32 operaciones protegidas y cinco participantes sin rol funcional. Las referencias corresponden a 43 RF/RNF, 33 HU y 36 RN existentes. Markdown y DOCX coinciden; el paquete OOXML contiene 9 tablas íntegras y conserva título rojo, línea azul, bloque gris, jerarquías y tablas homologadas. |
| 2026-09-01 | Revisión integral de redacción académica de las reglas de negocio. | Se retiró la subsección metadocumental de interpretación y trazabilidad, se reformularon el propósito, la delimitación técnica, la obligatoriedad por fase y el control de cambios, y se eliminaron referencias al proceso de elaboración o a entregables posteriores. Permanecen 40 reglas, sus IDs, fases, tipos de validación y trazabilidad: 50 referencias RF/RNF y 33 HU válidas. Markdown y DOCX coinciden; el paquete OOXML, las 10 tablas y el diseño homologado continúan íntegros. |
| 2026-09-01 | Validación estructural, funcional y visual de las reglas de negocio consolidadas. | Se comprobaron 40 IDs únicos: GOB 5, ACC 6, PER 5, INV 6, SOL 6, LOG 7 y COM 5; fases: 6 de Primer parcial, 25 Posteriores y 9 Transversales; validación: 14 Técnicas, 4 Demostrativas y 22 Clínicas/normativas. Las 50 referencias RF/RNF y 33 HU existen; HU-MON-001 y HU-MON-002 permanecen únicamente como historias técnicas. Markdown y DOCX coinciden, el paquete OOXML es íntegro, `textutil` extrae el contenido y la vista previa conserva título rojo, línea azul, bloque gris y tablas rojas con filas alternadas. |
| 2026-08-31 | Validación cruzada de los ajustes puntuales en análisis, RF/RNF e historias contra `proyecto.txt`, `entregas.txt` y `arquitectura.txt`. | El primer parcial conserva únicamente panel principal básico y tres perfiles funcionales; los siete perfiles permanecen en el alcance completo. RF-WEB-015 y HU-WEB-013 tienen prioridad Alta; RNF-MS-002 exige respuestas JSON y XML, OpenAPI/Swagger y XSD; RF-MS-004/005 cubren distancia y tiempo sin fórmulas nuevas; la institución quedó como entidad única reutilizable como catálogo. Se conservaron 53 RF, 41 RNF, 35 HU, 9 HE y la trazabilidad de los 94 requisitos. Los tres DOCX superaron integridad ZIP/XML y extracción con `textutil`. |
| 2026-08-31 | Eliminación del punto 9 de las historias consolidadas. | Markdown y Word terminan en los criterios de aceptación de `HE-MON-001`; no permanece el encabezado ni los dos párrafos de “Cobertura y límites de esta versión”. Se conservaron 35 HU, 9 HE, 94 relaciones RF/RNF, 47 tablas, el diseño homologado y la integridad OOXML. |
| 2026-08-31 | Incorporación de usuarios y responsables en las fichas de historias. | Las 35 HU contienen una fila `Usuario` con los perfiles consolidados aplicables o el público general para la página abierta; las 9 HE contienen `Responsable técnico`. Las 35 etiquetas cambiaron de `Historia.` a `Historia:` y las 9 habilitadoras usan `Historia habilitadora:`; ningún actor permanece resaltado en negritas dentro de la frase. Se conservaron 44 identificadores, 94 relaciones RF/RNF, 47 tablas, 16 partes XML válidas e integridad OOXML. |
| 2026-08-31 | Eliminación del resumen del backlog en Markdown y DOCX. | No permanecen el encabezado, la tabla de cantidades ni el párrafo que enumeraba las historias del primer parcial. Los apartados siguientes quedaron renumerados del 3 al 9. Se conservaron 35 HU, 9 HE y las 94 relaciones RF/RNF; el Word mantiene el tema homologado, contiene 47 tablas, integridad OOXML y vista previa legible. |
| 2026-08-31 | Homologación visual del DOCX de historias con los demás entregables. | Se regeneró el Word utilizando el mismo tema y estilos de `Requerimientos_funcionales_y_no_funcionales.docx`: título rojo con línea azul, bloque gris de metadatos, jerarquías roja y gris azulada y tablas compactas con encabezado rojo y filas alternadas. Se conservaron 35 HU, 9 HE y las 94 relaciones RF/RNF; el paquete contiene 48 tablas, 16 partes XML válidas, metadatos propios, integridad comprimida y vista previa legible. El Markdown no cambió. |
| 2026-08-31 | Validación estructural, trazabilidad y presentación de las historias de usuario consolidadas. | Se comprobaron 35 identificadores HU y 9 HE únicos, distribuidos como WEB 17, MS 5, MOV 8, DESK 7, DAT 1, INF 2, SEC 1 y MON 3. Los 53 RF y 41 RNF aparecen relacionados sin faltantes ni referencias ajenas. El DOCX inicial contenía 47 tablas, metadatos correctos, integridad OOXML, contenido completo extraíble y vista previa legible; posteriormente fue homologado visualmente sin cambiar su contenido. Los archivos anteriores de historias no fueron modificados. |
| 2026-08-31 | Validación estructural y de cobertura de la versión consolidada de RF/RNF. | Se comprobaron 94 identificadores únicos: 53 RF y 41 RNF. Cobertura total por componente: WEB 22, MS 15, MOV 11, DESK 11, DAT 9, INF 8, SEC 11 y MON 7. Todas las filas conservan fase, prioridad y validación; los términos obligatorios de tecnologías, contratos, seguridad, integración, algoritmos, pruebas y monitoreo permanecen cubiertos. El DOCX contiene 18 tablas, metadatos correctos, integridad OOXML y vista previa inicial legible. |
| 2026-08-31 | Validación posterior a retirar las secciones internas del RF/RNF. | Markdown y DOCX terminan en `10.2 Requerimientos no funcionales` de Monitoreo; no contienen los puntos 11 y 12 ni la referencia interna al DOCX anterior. Se conservaron 144 identificadores únicos —82 RF y 62 RNF—. El Word quedó con 19 tablas, metadatos correctos e integridad OOXML. |
| 2026-08-31 | Validación estructural del nuevo documento de RF/RNF en Markdown y DOCX. | Se comprobaron 144 identificadores únicos: 82 RF y 62 RNF; cobertura WEB 30, MS 29, MOV 18, DESK 15, DAT 12, INF 14, SEC 17 y MON 9. Todas las filas contienen fase, prioridad y estado de validación. El DOCX conserva 20 tablas, metadatos correctos, contenido extraíble, integridad OOXML y vista previa inicial legible. El DOCX anterior no fue modificado. |
| 2026-08-31 | Validación de la corrección de alcance completo en Markdown y DOCX. | El análisis declara que la documentación abarca todo el proyecto y sus cuatro productos, conserva el MVP como subconjunto del primer parcial y deriva los requisitos para la solución completa. No permanecen las frases que limitaban los requisitos al primer parcial. El DOCX conserva cinco tablas, 13 referencias, 13 enlaces, Referencias como última sección, integridad OOXML y una vista previa inicial legible. |
| 2026-08-31 | Verificación del orden final de cierre y referencias en Markdown y DOCX. | Resultado de la validación, Conclusión y Referencias quedaron como puntos 20, 21 y 22; Referencias es la última sección. Se conservaron 13 entradas, 13 enlaces activos, sangría francesa y doble espacio; el paquete OOXML es íntegro. |
| 2026-08-31 | Verificación de eliminación de supuestos iniciales y renumeración final en Markdown y DOCX. | No permanece el encabezado ni el contenido de supuestos; en esa revisión Referencias, Resultado de la validación y Conclusión quedaron como puntos 20, 21 y 22. Las 13 referencias conservaron enlaces activos, sangría francesa y doble espacio; el paquete OOXML fue íntegro. Numeración histórica reemplazada posteriormente al mover Referencias al final. |
| 2026-08-31 | Verificación de eliminación del punto 21, renumeración y referencias APA 7 en Markdown y DOCX. | No permanece el cuestionario ni su encabezado; Referencias, Resultado de la validación y Conclusión quedaron como puntos 21, 22 y 23. Se comprobaron 13 referencias ordenadas, citas autor-fecha concordantes, 13 enlaces activos y formato Word con sangría francesa y doble espacio. El paquete OOXML no presenta errores. |
| 2026-08-31 | Validación de la consolidación de perfiles en Markdown y DOCX. | El análisis contiene exactamente los siete perfiles acordados, identifica solo Administrador, Operador de banco de sangre y Auditor para el primer parcial, y separa receptores, instituciones, autoridades y soporte como participantes sin rol adicional. El DOCX es OOXML válido, conserva cinco tablas y no contiene los roles sustituidos. |
| 2026-08-31 | Contraste del análisis con fuentes oficiales de OMS, Cámara de Diputados, DOF, CENATRA y Plataforma de Normalización. | Se confirmó una base documental suficiente para el ejercicio: separación regulatoria de sangre y trasplantes, responsabilidades humanas y marcos de privacidad; la NOM-253-SSA1-2012 aparece vigente y la actualización 2024 continúa como proyecto a la fecha de revisión. |
| 2026-08-31 | Revisión de coherencia y alcance académico de `documentation/markdowns/Analisis_del_problema.md`. | El documento distingue hechos, hipótesis, decisiones académicas y pendientes; delimita el MVP y declara expresamente que la validación no habilita uso sanitario real. `git diff --check` no detectó errores de formato. |
| 2026-08-31 | Regeneración y validación de `documentation/docx/Analisis_del_problema.docx`. | Word 2007+ válido, paquete OOXML íntegro, texto completo extraíble y vista previa legible con títulos, listas y tablas. |
| 2026-08-27 | Validación de nomenclatura estructural y datos del libro en inglés/español. | Las 16 hojas, 129 nombres de relaciones entre todas las fases y 316 atributos únicos se generan en inglés; los valores ficticios de las filas permanecen en español. |
| 2026-08-27 | Validación del estado actual y el historial de citas. | `APPOINTMENTS.current_status` contiene un único estado vigente; `APPOINTMENT_STATUS_HISTORY` conserva en orden cuatro transiciones para la cita 1 y tres para la cita 2 sin perder `SOLICITADA`. |
| 2026-08-27 | Revisión de conservación y alcance de roles en la hoja `Users`. | Los cuatro permisos y cuatro asignaciones de ámbito presentes en 0NF se conservan; cada ámbito final referencia `user_role_id` y utiliza una FK específica a institución o sede. |
| 2026-08-27 | Revisión del libro después de limpiar títulos y anotaciones visuales. | No quedan sufijos `_0FN` a `_4FN` en nombres de tablas ni textos grises de cambio, dependencia o advertencia; las formas normales permanecen identificadas únicamente en las franjas amarillas. |
| 2026-08-27 | Validación OOXML y prueba de integridad comprimida de `Normalizacion_Red_Regional.xlsx`. | Excel 2007+ válido, 16 hojas y ningún archivo interno dañado. |
| 2026-08-27 | Verificación automática de fases, fórmulas y almacenes del libro. | Las 15 hojas relacionales contienen exactamente 0NF, 1NF, 2NF, 3NF y 4NF; la hoja de nube no simula formas normales y no existen fórmulas. |
| 2026-08-27 | Comparación de estilos y revisión visual mediante Quick Look de las hojas `Institutions` y `Appointments`. | Se conservaron Arial 10, amarillo `#FFFF00`, naranja `#FF9900`, bordes negros, franjas A:Q, tablas laterales y resúmenes inferiores. |
| 2026-08-27 | Ejecución del generador `generate_normalizacion_excel.py` con XlsxWriter 3.2.9. | El libro se produjo correctamente y los nombres finales de las relaciones se verificaron. |
| 2026-08-27 | Comprobación de integridad después de reparar la duplicación accidental de `01_MODELO_SIN_NORMALIZAR.md` (antecedente del repositorio de origen). | El archivo quedó en 814 líneas, con un título principal, un bloque Mermaid y una sección de próximo paso; `git diff --check` no detectó errores. |
| 2026-08-27 | Validación posterior a la ampliación de todos los bloques Mermaid de `00_MODELO_ER_CONCEPTUAL.md` (antecedente del repositorio de origen) y `01_MODELO_SIN_NORMALIZAR.md` (antecedente del repositorio de origen) con Mermaid 11.15 integrado en VS Code. | Los dos bloques fueron aceptados sin errores de sintaxis. |
| 2026-08-27 | Revisión de cobertura de la 0FN ampliada contra dominio, productos, algoritmos y almacenes obligatorios. | Se documentaron diez registros operativos y estructuras preliminares para MongoDB, Redis y Cloud Storage; los requisitos tecnológicos que no corresponden a datos quedaron identificados como arquitectura o integración. |
| 2026-08-27 | Revisión de formato posterior a la ampliación mediante `git diff --check`. | No se detectaron errores de espacios o formato de parche. |
| 2026-08-27 | Validación de los bloques Mermaid del modelo conceptual y 0FN con el analizador Mermaid 11.15 incluido en VS Code. | Ambos bloques fueron aceptados sin errores de sintaxis. |
| 2026-08-27 | Inspección de Visual Studio Code y su soporte local de Mermaid. | Se detectó VS Code 1.134.0 y el paquete Mermaid integrado; no se requirió instalar una extensión. |
| 2026-08-27 | Revisión de formato de los nuevos documentos mediante `git diff --check`. | No se detectaron errores de espacios o formato de parche. |
| 2026-08-12 | Validación de `documentation/docx/Analisis_del_problema.docx`. | Reconocido como Microsoft Word 2007+, estructura OOXML íntegra y extracción de texto correcta desde el título hasta la conclusión. |
| 2026-08-12 | Revisión estructural de `documentation/markdowns/Analisis_del_problema.md`. | El documento desarrolla contexto, problema, causas, consecuencias, actores, procesos, información, decisiones, riesgos, privacidad, beneficios, indicadores, supuestos y preguntas abiertas; no contiene portada ni integrantes. |
| 2026-08-12 | Revisión de la descripción del Proyecto 6. | Se registraron el dominio, objetivos, problema, módulos, usuarios objetivo, servicios y algoritmos sin afirmar que estén implementados. |
| 2026-08-12 | Comparación de la especificación ampliada contra el contexto inicial. | No se detectaron nuevos lenguajes, frameworks o bases centrales obligatorias; se incorporaron precisiones de seguridad, XSD/XXE, integración, resiliencia, algoritmos, pruebas, rendimiento y documentación. |
| 2026-08-12 | Inspección inicial del directorio `proyectoPrueba`. | El directorio estaba vacío antes de crear la documentación base. |

## Bitácora de trabajo

### 2026-09-07 — Baja lógica del inventario sanguíneo

- Se confirmó el alcance final con el usuario: solo el inventario sanguíneo funcional del MVP; la vista de órganos continúa futura y deshabilitada.
- Se agregó una acción de baja lógica exclusiva del Operador, con CSRF, confirmación en navegador, control de versión, ruta de formulario y método HTTP `DELETE`. La unidad cambia a `WITHDRAWN`, agrega movimiento y auditoría atómica, y no se borra físicamente.
- El listado, los filtros visibles, el resumen, los avisos de caducidad, el panel y sus últimas unidades excluyen bajas. El detalle directo conserva la trazabilidad. El formulario normal ya no permite convertir manualmente una unidad a `WITHDRAWN` para evitar saltarse los bloqueos.
- Se bloquea la operación si existe un movimiento posterior al alta; esta es la representación conservadora disponible en el MVP para impedir bajas de recursos con actividad de asignación, traslado, entrega u otro movimiento operativo. Auditor y otros perfiles sin `inventory.write` reciben 403.
- Pruebas: `26 passed in 85.02s` en `tests/test_monolith.py` contra PostgreSQL real mediante socket explícito; se añadieron dos pruebas de integración para baja/visibilidad y bloqueo/permisos, incluyendo el método HTTP `DELETE`. El recorrido de navegador con Playwright temporal aprobó `1 passed in 22.21s`, sin recursos faltantes ni excepciones. La ejecución global con la URL documentada `postgresql:///postgres` obtuvo 62 aprobadas, pero cuatro pruebas del instalador fallaron antes de preparar la base porque `setup_local.local_connection` rechaza esa URL con socket implícito; no corresponden al cambio y los casos del monolito pasaron. `git diff --check` y compilación Python también aprobaron.

### 2026-09-06 — Cierre del primer parcial y entorno propio de Red-House

- El usuario confirmó que otros integrantes ya hicieron la revisión del equipo y la prueba Windows, y pidió marcarlas como terminadas y retirar del backlog las notas de avance/pendientes. No se inventaron revisores ni se presentó Windows como una prueba ejecutada en este Mac.
- Se reconstruyó `.venv` por autorización expresa, directamente en la ruta actual. El anterior se movió a `/private/tmp/red-house-close.Yn7o33/previous_venv` como respaldo temporal; `.env`, credenciales y base existente se conservaron.
- Activación, ejecutables y `pip check` aprobados. Se repitieron las 65 pruebas con el entorno nuevo y PostgreSQL temporal exclusivo: cero fallos/omisiones en 40.92 s; Chrome sin errores ni recursos faltantes. El arranque mediante `python3 run.py` respondió HTTP 200 en las tres rutas públicas comprobadas. Se detuvieron solo el servidor y el clúster temporales usados por la verificación.
- Los cinco elementos que seguían en proceso pasaron a terminados: el Sprint 1 tiene ocho terminados y los cortes posteriores mantienen sus 21 pendientes. Se conservaron tareas, criterios, responsables, dependencias, trazabilidad, 14 tablas y estilos del Word; se retiraron las notas añadidas de avance/pendientes.
- Se actualizaron únicamente el entorno virtual, la documentación de cierre y dos artefactos de evidencia; no se modificaron aplicación, SQL, modelos, secretos, datos ni el repositorio de origen. No se realizaron commits ni publicaciones. Los hallazgos abiertos de la revisión anterior quedan sustituidos por este cierre y su confirmación.

### 2026-09-06 — Revisión técnica y verificación completa del primer parcial

- Se revisaron los RF del primer parcial, el plan, el backlog, el modelo lógico y el esquema del monolito. La reconciliación de las 23 tablas quedó documentada sin cambiar modelos, columnas, restricciones ni código.
- Se preparó un entorno Python limpio y un clúster PostgreSQL exclusivo en `/private/tmp/red-house-review.RDIhXZ`. Se ejecutaron las 65 pruebas del código actual de `Red-House`, con Chrome, sin fallos ni omisiones, en 40.80 s. Se revisaron además las capturas de inventario móvil, historial de unidad y auditoría.
- El catálogo real confirmó 23 PK, 24 FK y 21 CHECK. Las bases creadas por los casos y la inspección se retiraron; el clúster temporal quedó sin bases de prueba y se detuvo. El PostgreSQL habitual y sus datos no se alteraron.
- `setup.sh --check` aprobó la instalación existente en modo de solo lectura. Se detectaron las rutas antiguas del `.venv` copiado; no se sobrescribió y se solicitó autorización para reconstruirlo. También se consultó al usuario por los acuerdos de ramas/incidencias y un entorno Windows.
- Se conservaron resultados JUnit, catálogo y capturas bajo `documentation/evidence/primer-parcial/`, y se sincronizaron los avances del backlog en Markdown y Word. Los criterios y estados no se relajaron: el versionado y la revisión del equipo previstos por el plan, el entorno copiado y Windows siguen pendientes de resolución.
- No se hicieron commits, publicaciones, cambios al esquema o a la aplicación, ni modificaciones al repositorio de origen. Las copias anteriores a esta revisión documental se conservaron fuera del repositorio.

### 2026-09-06 — Seguimiento del MVP y nombres descriptivos de documentación

- Se contrastaron el código, las pruebas disponibles y el seguimiento previo con los 29 paquetes. `P1-04` pasa a terminado; `P1-07` y `P1-08` pasan de pendiente a en proceso. Se detalló qué está implementado y qué falta para cerrar `P1-03` a `P1-08`, sin modificar responsables, criterios, dependencias, RF/RNF ni fechas de entrega.
- Se renombraron los 17 Markdown y 11 Word de `documentation/`, retirando mayúsculas sostenidas, prefijos de orden y calificativos redundantes. Se sincronizaron referencias en los README, este seguimiento, los documentos y los dos auxiliares de generación/verificación de normalización. No se renombraron carpetas ni archivos convencionales de contexto.
- Se conservaron los estilos y tablas de los Word, las fechas documentales del 7 de septiembre, la cronología del cuerpo y los 63 bloques Mermaid. Se comprobaron la correspondencia entre Markdown y Word, los enlaces y el verificador de normalización con los nuevos nombres.
- Se aprobaron siete pruebas unitarias en este repositorio; las 65 pruebas completas y los recorridos de Chrome permanecen como evidencia histórica del entorno original. No se modificaron la aplicación, el esquema, los secretos, `.gitignore`, los datos ni el repositorio de origen.
- Las copias previas, los controles y el registro de renombres de esta edición se conservaron fuera del repositorio en `/private/tmp/red-house-backlog.LIahkJ`.

### 2026-09-06 — Adaptación documental al repositorio Red-House

- Se actualizaron las rutas activas a `documentation/markdowns`, `documentation/docx` y `documentation/database-diagrams`, incluidos el nuevo nombre de la 0FN y los comandos del generador/verificador. Los modelos sustituidos y el diagrama anterior basado en HU siguen identificados como antecedentes externos, sin crear copias ni enlaces inexistentes.
- Se cambiaron al 7 de septiembre de 2026 las 12 fechas iniciales existentes en Markdown y las 11 de los Word, conservando las fechas del calendario, las citas y la bitácora. No se añadieron fechas a los documentos que no tenían una fecha inicial.
- Se corrigieron el árbol y los enlaces del README y se distinguió la instalación del repositorio de origen de una eventual instalación nueva en `Red-House`. Las evidencias históricas no se presentan como pruebas recién ejecutadas en esta carpeta.
- Se comprobaron enlaces, coincidencia con el generador, sintaxis Mermaid, integridad de Word y conservación del contenido no solicitado. Las copias previas y los controles auxiliares de esta edición permanecen fuera del repositorio, en `/private/tmp/red-house-docs.Dz9ip1`.
- El alcance no incluyó cambios al código del monolito, esquema SQL, secretos, reglas de Git ni al repositorio de origen.

### 2026-09-05 — Instaladores locales y arranque simplificado

- Se añadieron `setup.sh`, `setup.cmd` y una única implementación Python que prepara el entorno y reutiliza el esquema y la carga DEMO existentes. PostgreSQL y Python deben estar instalados; no se cambian servicios, usuarios del sistema ni componentes futuros.
- Se conservaron las claves y la contraseña del entorno ya preparado. El instalador no sobrescribe `.env`, no inicializa bases ajenas ni repara esquemas incompletos; `--check` no instala paquetes ni escribe en la base. La carga nueva se revierte completa al cancelar y puede reintentarse sin borrar la base.
- Se mantuvo `run.py`, añadiendo únicamente la selección automática de la `.venv` propia al arrancar directamente, sin crear una aplicación duplicada ni alterar las importaciones Flask/WSGI.
- Pasaron las 65 pruebas de regresión. Se ejecutó además una instalación real desde cero y su repetición en una ruta temporal con espacios; `python3 run.py` arrancó sin activar el entorno y las cuatro cuentas completaron acceso, panel y cierre por HTTP. La ejecución de CMD en Windows queda expresamente pendiente.
- Se actualizaron las guías raíz, del monolito y de datos. Se eliminó solo la base ficticia creada para la prueba de instalación, regenerable mediante los mismos pasos, y se cerraron su servidor web y el clúster temporal. La base `red_house`, su configuración privada y la aplicación original en 5050 permanecieron intactas.

### 2026-09-05 — Instalación y ejecución local por solicitud del usuario

- Se comprobó el PostgreSQL de Homebrew ya activo y que no existiera una base `red_house`; se creó exclusivamente esa base, sin modificar otras bases, roles, contraseñas ni la configuración del servidor.
- Se preparó `apps/web-monolito01/.venv`, se instalaron las dependencias fijadas y se creó `.env` privado con claves aleatorias distintas, conexión local y puerto web 5050. El puerto 5000 se dejó al servicio de macOS que ya lo utiliza.
- Se ejecutaron `init-db` y `seed-demo` sobre la nueva base. La contraseña aleatoria de las cuatro cuentas se introdujo por entrada oculta, se almacenó mediante hash en PostgreSQL y se entregó al usuario, sin guardar su texto en archivos del proyecto.
- Se abrió una ventana de Terminal con `.venv/bin/python run.py` y se verificaron `/health/live`, los cuatro accesos, sus vistas autorizadas, Highcharts y el cierre de sesión mediante Chrome. Los controles de instalación y siete pruebas unitarias también aprobaron; no se repitió la carga ni se ejecutó la suite destructiva de fixtures sobre la base del usuario.
- Se actualizaron las instrucciones de arranque/detención y este seguimiento. La aplicación queda disponible localmente mientras permanezca ejecutándose; los scripts y capturas de verificación se guardaron solo en `/private/tmp/red-house-local.koWSFd`.

### 2026-09-05 — Primer incremento ejecutable del monolito Red House

- Se aplicó el alcance autorizado: Flask/Jinja2, PostgreSQL, administración, inventario sanguíneo ficticio, caducidad DEMO, panel, seguridad y auditoría; no se implementaron otros productos ni infraestructura futura.
- Se adaptó el ZIP conservando su lenguaje visual y sustituyendo React por plantillas del monolito. Se prepararon siete vistas futuras y la recuperación de acceso, sin operaciones habilitadas.
- Se creó el esquema físico incremental de 23 tablas y una vista, con datos atómicos, referencias, índices, controles de versión e historial; se documentaron sus límites respecto de las 169 relaciones lógicas, sin alterar los Mermaid anteriores.
- Se implementaron JWT corto, revocación local, CSRF, hash scrypt, autorización institucional, protección de consultas, fallos seguros y auditoría de accesos/cambios sin secretos.
- Se probaron operaciones sobre PostgreSQL real en un clúster temporal aislado. Se corrigió una caché de CSRF indebidamente compartida por un fixture de pruebas y un uso de `MultiDict.update` que acumulaba valores en otra prueba; no se debilitó la protección de la aplicación.
- Chrome permitió corregir un desbordamiento móvil causado por una etiqueta accesible con posicionamiento absoluto y mejorar la tabla desplazable y los mensajes vacíos. Se importaron localmente los recursos de Highcharts tras comprobar el error del CDN.
- La ejecución final aprobó 32 pruebas; se verificaron capturas de escritorio/móvil y persistencia después de recargar. Se añadieron guías de instalación, uso, seguridad, esquema y pruebas, y se actualizó este seguimiento con pendientes reales.
- No se crearon credenciales fijas, archivos `.env` con valores reales, servicios, clientes, Dockerfiles ni integraciones de nube. Los recursos de verificación y las capturas permanecen fuera del repositorio.
- Al finalizar se comprobó que no quedaran bases de casos de prueba y se detuvo exclusivamente el clúster PostgreSQL temporal. No queda un servidor web ejecutándose; el arranque local del usuario está documentado en el README.

### 2026-09-04 — Normalización de la nueva 0FN hasta 4FN

- Se mantuvo `Modelo_0FN.md` como entrada inalterada y se revisó `00_ER_BASADO_EN_HU.md` como referencia autorizada, sin modificar ese Mermaid ni utilizar el Excel anterior.
- Se completaron los cuatro documentos reservados para 1FN, 2FN, 3FN y 4FN. El primero contiene el catálogo íntegro de relaciones; 2FN y 3FN definen sustituciones explícitas y conservan las relaciones no afectadas; 4FN presenta el esquema completo con atributos, claves, referencias y diecisiete dominios.
- Se justificaron ocho dependencias parciales y cuatro transitivas, incluyendo las claves candidatas compuestas aunque exista un UUID. Se conservaron las DF inversas y claves inducidas por referencias candidatas repetidas en las etapas intermedias.
- Se comprobó BCNF y se documentó la independencia entre contactos generales y horarios de sede, junto con el contraejemplo de permisos que no deben separarse por ámbito. No se introdujo una separación artificial entre 3FN y 4FN.
- Se creó `Trazabilidad_0FN_4FN.md` para los 208 atributos originales. La atomización produce 169 relaciones y 918 atributos lógicos; no se prescribe desplegarlos todos en el MVP ni convertir eventos/documentos extensos en almacenamiento relacional duplicado.
- Se incorporaron una especificación legible y verificable, un emisor de parches Markdown sin escrituras directas y un verificador documental en `documentation/database-diagrams/normalization/`.
- Se validaron los esquemas, referencias, ejemplos de reconstrucción, contraejemplos y 49 bloques Mermaid. La validación usa el analizador local de VS Code sin instalar dependencias.
- Se actualizaron el índice y este seguimiento. No se generó SQL, se implementaron reglas clínicas, se modificaron documentos funcionales ni se instaló una base de datos; el progreso funcional sigue en 0 %.

### 2026-09-04 — Nueva derivación ER 0FN desde documentación

- A solicitud del usuario, se reinició la derivación tomando como fuentes el análisis y los documentos de `documentation/markdowns`, sin consultar los modelos de bases de datos ni el Excel anteriores para diseñar la nueva propuesta.
- Se creó `documentation/database-diagrams/Modelo_0FN.md` con dieciocho tablas, nombres y atributos en inglés, 26 relaciones y una justificación documental para cada tabla.
- Se definió el significado de cada fila a partir de los registros y operaciones descritos: citas, unidades, solicitudes, evaluaciones, asignaciones y traslados conservan su seguimiento propio. Los estudios, candidatos, autorizaciones e historiales permanecen agrupados, sin descomposición normalizada.
- Se mantuvieron separados los datos de sangre y órganos, la evaluación de candidatos y la decisión humana, así como las referencias a archivos y las fronteras de almacenamiento futuro.
- Se validaron la sintaxis Mermaid, 208 atributos, la correspondencia entre tablas y relaciones, los grupos repetitivos de las dieciocho tablas, ocho enlaces documentales y 95 identificadores citados.
- Se actualizaron el índice y este estado para distinguir la propuesta vigente de los antecedentes. Los archivos anteriores se conservaron; no se implementó una base de datos, se generó SQL ni se aplicó una forma normal posterior.

### 2026-09-04 — Propuesta de tablas generales en 0FN

- Se creó `TABLAS_GENERALES_0FN.md` (antecedente del repositorio de origen) con trece registros amplios distribuidos en cinco diagramas Mermaid y una tabla que explica el significado de cada fila.
- Se incluyeron instituciones, acceso, campañas, donantes, receptores, inventario sanguíneo, disponibilidad de órganos, solicitudes y decisiones, traslado y custodia, alertas, documentación, auditoría y dispositivos.
- Se conservaron listas, datos compuestos, subgrupos repetitivos y datos redundantes. Se añadió un ejemplo ficticio para mostrar unidades con movimientos dentro de una misma fila de inventario.
- Se mantuvieron las reglas clínicas pendientes de validación y las fronteras conceptuales con MongoDB, Redis y Storage, sin diseñar colecciones o claves ni incluir archivos binarios o credenciales reutilizables.
- Se validaron sintácticamente los cinco diagramas y se enlazó el documento desde el índice de datos. No se modificaron los modelos previos, las etapas de normalización ni el Excel; `P1-03` continúa en proceso y el avance funcional permanece en 0 %.
- La normalización de esta propuesta queda pendiente del procedimiento específico que indicará el usuario.

### 2026-09-03 — Investigación tecnológica y ajuste de calendarización

- Se crearon las versiones ahora ubicadas en `documentation/markdowns/Tecnologias.md` y `documentation/docx/Tecnologias.docx` como investigación introductoria de MongoDB, Redis y contenedores Docker, con conceptos, usos previstos en la red regional, beneficios, riesgos, controles y referencias oficiales en formato APA 7.
- Se conservó PostgreSQL como persistencia real del producto mínimo y se trasladaron al segundo parcial el diseño detallado, instalación, configuración y uso funcional de MongoDB, Redis y Docker.
- Se actualizó `entregas.txt` y se sincronizaron los documentos vigentes de análisis, requisitos, historias, casos de uso, trazabilidad, arquitectura, plan, Sprint Backlog y datos sin cambiar identificadores, responsables o estados.
- Se regeneraron los DOCX afectados con el estilo homologado y se comprobaron su integridad OOXML, el contenido por fases y la conservación de 94 RF/RNF, 44 HU/HE, 40 reglas, 15 casos de uso y 29 paquetes.

### 2026-09-03 — Responsables nominales en el plan semestral

- Se añadieron a los 29 paquetes del plan los mismos responsables principales establecidos en el Sprint Backlog, sin modificar actividades, frentes, dependencias ni criterios de cierre.
- La columna `Frente responsable` cambió a `Responsable principal y frente`, conservando cinco columnas para evitar reducir la legibilidad.
- La distribución quedó en Alejandra Morón con 7 paquetes, Alberto Reyna con 8, Galia Sejudo con 8 y Victor Berlanga con 6.
- El apartado de participación identifica a los cuatro integrantes y aclara que la persona revisora continuará asignándose en el tablero.
- Markdown y DOCX se comprobaron entre sí y contra el Sprint Backlog; el Word conserva 11 tablas, estructura OOXML íntegra y anchos ajustados para la nueva información.

### 2026-09-03 — Vista general de la matriz de trazabilidad

- Se añadió el apartado `4. Matriz general de trazabilidad` antes de las matrices detalladas.
- La nueva vista relaciona por componente el alcance general, RF/RNF, HU/HE, familias o reglas de negocio, casos de uso y tipos de verificación; incluye una fila final con la cobertura integral.
- Se aclaró que los rangos representan agrupaciones de lectura y que la relación exacta y su fase permanecen en el desglose individual.
- Las matrices de Sistema web a Monitoreo se recorrieron a los apartados 5 a 12 y el control de integridad pasó al apartado 13, sin cambiar IDs ni asociaciones existentes.
- Se regeneró el DOCX y se verificaron sus 13 tablas, la orientación horizontal, la fuente de 9 puntos de la nueva matriz, la extracción completa del contenido y la integridad OOXML.

### 2026-09-02 — Casos de uso y matriz de trazabilidad integral

- Se crearon `Casos_de_uso.md` y `.docx` con quince casos consolidados para el alcance semestral, incluidos actores, fases, precondiciones, postcondiciones, flujos principales, alternativas, excepciones y relaciones con RF/RNF, HU/HE y RN.
- Se crearon `Matriz_de_trazabilidad.md` y `.docx` con una fila por cada uno de los 94 requerimientos, clasificada por los ocho componentes obligatorios y vinculada con historias, reglas, casos de uso y evidencia prevista.
- Se verificó la cobertura de 53 RF, 41 RNF, 35 HU, 9 HE, 40 RN, 15 CU y 9 tipos de verificación, sin identificadores faltantes, duplicados o desconocidos y sin discrepancias de fase.
- Los documentos mantienen el límite de apoyo a decisiones, la separación entre sangre y órganos y el uso de reglas demostrativas mientras no exista validación clínica o normativa competente; no incorporan fórmulas ni criterios clínicos nuevos.
- Los DOCX conservan el estilo homologado: casos de uso en orientación vertical y matriz en orientación horizontal para preservar la legibilidad de las tablas.
- `P1-01` se marcó como terminado junto con `P1-02`; `P1-03` a `P1-06` permanecen en proceso y los 23 elementos restantes continúan pendientes. No se modificaron responsables, tareas, dependencias ni relaciones RF/RNF.

### 2026-09-02 — Sprint Backlog alineado con el plan semestral

- Se creó `Sprint_backlog.md` y su versión `.docx` sin reemplazar el antecedente conservado en el repositorio de origen.
- Los 29 paquetes del plan se trasladaron sin modificar sus actividades ni criterios de cierre y se distribuyeron en cuatro sprints: 8 del primer parcial, 8 del segundo, 8 del tercero y 5 de la entrega final.
- Se conservaron las fechas de cierre del Sprint Backlog anterior como referencias sujetas a confirmación y se asignó una persona responsable principal por afinidad con las responsabilidades nominales de ese antecedente; cada elemento mantiene también su frente y sus dependencias.
- Las ocho asignaciones registradas inicialmente con el nombre abreviado `Alfredo` se corrigieron a `Alberto Reyna`, sin modificar tareas, estados, dependencias ni relaciones RF/RNF.
- Cada sprint incluye una tabla de cuatro columnas para las tareas y otra de dos columnas para su relación con RF/RNF, con objetivo e incremento separados, fuente mínima de 9.5 puntos, encabezados repetibles, filas no divisibles y estado resaltado.
- El estado actualizado registra `P1-01` y `P1-02` como terminados; `P1-03` a `P1-06` permanecen en proceso, y los 23 elementos restantes continúan pendientes. La terminación se determina por la existencia y comprobación del entregable, sin requerir una aprobación formal adicional.
- Se verificaron correspondencia con el plan, 29 responsables, 29 relaciones de trazabilidad, cobertura de los 94 RF/RNF, ausencia de códigos inexistentes, IDs, estados, fechas, estructura OOXML, propiedades y tamaños de fuente.

### 2026-09-02 — Eliminación del apartado redundante de restricciones

- Se eliminó “Restricciones y condiciones de evolución” porque sus delimitaciones ya se encuentran desarrolladas en las decisiones, la seguridad, el almacenamiento, la escalabilidad y la evolución por parciales.
- La conclusión se renumeró como apartado 17 sin modificar su contenido.
- Este ajuste reemplaza la organización adoptada en la revisión editorial anterior y conserva intacta la arquitectura técnica.

### 2026-09-02 — Revisión de redacción del diseño arquitectónico

- El apartado 17 se reformuló como restricciones y condiciones de evolución, con delimitaciones vigentes y evidencia requerida para concretar cada decisión.
- Se eliminó la antigua relación de documentos de base, cuyo contenido describía el proceso de elaboración en lugar de la arquitectura.
- La conclusión pasó al apartado 18 y se retiraron expresiones orientadas al cumplimiento de la solicitud, como referencias al “equipo académico”, a “superar el mínimo” o a componentes todavía no construidos.
- Se conservaron las decisiones, las fases, los diagramas, los límites clínicos y la cobertura funcional y tecnológica del diseño.

### 2026-09-02 — Diseño arquitectónico integral

- Se revisaron `proyecto.txt`, `entregas.txt`, `arquitectura.txt`, el análisis y los documentos consolidados de requisitos, historias, reglas, permisos y plan semestral.
- Se creó la fuente editable ahora ubicada en `documentation/markdowns/Diseno_arquitectonico.md` y su versión `documentation/docx/Diseno_arquitectonico.docx` con el diseño visual homologado.
- Se documentaron contexto, contenedores, componentes, comunicación, autenticación, almacenamiento, despliegue local y en Google Cloud, red, seguridad, resiliencia, monitoreo, algoritmos y crecimiento condicionado.
- Se incorporaron 13 diagramas: las nueve categorías exigidas, el proceso demostrable del primer parcial, los tres flujos integrales y el flujo común de autenticación.
- El diseño conserva el sistema web modular del MVP, los tres perfiles iniciales, el panel básico, la institución como fuente única y la evolución posterior hacia microservicios, Android, escritorio y panel regional.
- Los servicios producen JSON y XML; Android consume únicamente JSON y escritorio únicamente XML/XSD. Ningún cliente obtiene acceso directo a PostgreSQL, MongoDB o Redis.
- Se propuso agrupar priorización y geografía para contener la complejidad académica, mantener transporte y custodia separados, compartir infraestructura de datos con propiedad lógica y posponer clústeres o mensajería hasta contar con mediciones.
- Se verificaron estructura Markdown, numeración, cobertura, consistencia cruzada, 13 imágenes incrustadas, integridad OOXML y vista previa del Word. No se implementó código ni infraestructura.

### 2026-09-01 — Depuración académica del plan semestral

- Se eliminó la línea base del punto 2.3 porque funcionaba como reporte de estado y duplicaba el seguimiento conservado fuera del entregable.
- El calendario se expresó directamente mediante los cuatro cortes oficiales, sin explicar qué archivos proporcionaron o no las fechas.
- La cantidad de microservicios se reformuló como una decisión basada en responsabilidades y rango recomendado, sin lenguaje de respuesta a la consigna.
- El catálogo de servicios y el despliegue en `ubiquitous` quedaron redactados como condiciones formales del plan.
- Se conservaron las cuatro etapas, 29 paquetes de trabajo, tres flujos integrales, dependencias, frentes, riesgos, indicadores y criterios de cierre.
- Se regeneró el DOCX y se verificaron equivalencia con Markdown, 11 tablas, integridad OOXML y diseño homologado.

### 2026-09-01 — Plan de trabajo del semestre

- Se revisaron completos `entregas.txt`, `arquitectura.txt` y `proyecto.txt`; `prompt.txt` se excluyó conforme a la instrucción recibida.
- Se creó un plan semestral en Markdown y DOCX con los cuatro cortes oficiales y sin inventar fechas, semanas, nombres o decisiones tecnológicas pendientes.
- Se definieron 29 paquetes de trabajo: ocho para cada parcial y cinco para la entrega final, con frente responsable, dependencias, evidencia y criterio de cierre.
- El plan incorpora los cuatro productos, PostgreSQL, MongoDB, Redis, Cloud Storage, Docker, Compute Engine, contratos JSON/XML/XSD, JWT, Swagger, monitoreo, algoritmos, Locust y recuperación ante fallos.
- Se planearon tres flujos integrales del dominio y se conservaron el límite de apoyo a decisiones, los datos ficticios y la validación previa de reglas clínicas o normativas.
- Se añadieron dependencias críticas, frentes de participación, criterio común de terminado, riesgos, indicadores y control de cambios.
- Se verificaron secuencia, cobertura, equivalencia entre formatos, integridad OOXML, extracción de texto y diseño homologado.

### 2026-09-01 — Simplificación de la matriz para uso semestral

- Se retiró el apartado `Permisos habilitados en el primer parcial` porque duplicaba las fases ya indicadas en el alcance, los perfiles y cada operación protegida.
- Se retiró `Trazabilidad principal por perfil` para reservar esas relaciones a la matriz de trazabilidad integral solicitada como entregable independiente.
- `Participantes sin perfil funcional` pasó del punto 7 al punto 6 y quedó como cierre del documento.
- Se conservaron los siete perfiles, la identificación de los tres perfiles iniciales, las 32 operaciones protegidas y las restricciones de autorización.
- Se regeneró el DOCX y se comprobaron equivalencia con Markdown, integridad OOXML, siete tablas y diseño homologado.

### 2026-09-01 — Matriz consolidada de perfiles y permisos

- Se creó una fuente Markdown y un DOCX nuevo con el diseño homologado de los entregables funcionales.
- La matriz conserva los siete perfiles del alcance completo y separa explícitamente los permisos funcionales del primer parcial para Administrador, Operador de banco de sangre y Auditor.
- Para cada perfil se documentaron responsabilidad, información consultable, información registrable, restricciones, nivel de autorización, componentes y fase de habilitación.
- Se consolidaron 32 operaciones protegidas por área, perfil, tipo de permiso, fase y condición, aplicando ámbito institucional, mínimo privilegio y denegación por defecto.
- Receptor o paciente, público general, institución, autoridad y soporte permanecen como participantes sin convertirse en roles adicionales.
- La trazabilidad principal utiliza únicamente identificadores existentes: 43 RF/RNF, 33 HU y 36 RN.
- Se verificaron equivalencia entre Markdown y Word, integridad OOXML, extracción de texto, estilos, tablas y vista previa inicial.

### 2026-09-01 — Depuración académica de las reglas de negocio

- Se sustituyeron formulaciones que describían cómo se construyó el documento por una exposición directa del propósito y alcance de las reglas.
- Se eliminó la subsección `2.3 Interpretación y trazabilidad` porque contenía instrucciones de lectura, referencias a la matriz futura y ejemplos pedagógicos ya cubiertos por el contenido normativo.
- El cierre se reformuló como vigencia y control de cambios; se retiró la referencia a la aprobación académica y al siguiente entregable.
- Se revisó el documento completo para detectar expresiones similares y se conservaron únicamente las menciones académicas necesarias para distinguir datos y reglas demostrativas de criterios clínicos o regulatorios reales.
- No cambiaron las 40 reglas, sus identificadores, fases, tipos de validación ni relaciones con RF/RNF e historias de usuario.
- Se regeneró el DOCX y se verificaron equivalencia con Markdown, integridad OOXML, extracción de texto, tablas, estilos y vista previa.

### 2026-09-01 — Reglas de negocio consolidadas

- Se derivaron las reglas a partir del análisis vigente, los 94 RF/RNF y las 35 HU con sus criterios, sin modificar esos documentos.
- Se consolidaron 40 reglas distribuidas entre gobierno y responsabilidad humana, acceso e instituciones, personas, inventario, solicitudes, logística y comunicación o auditoría.
- Cada regla conserva fase, tipo de validación y trazabilidad principal; no se repitieron requisitos puramente técnicos de infraestructura o monitoreo.
- Las reglas clínicas y normativas quedaron expresamente pendientes de validación, y no se definieron criterios médicos, fórmulas ni ponderaciones.
- Se mantuvo el MVP del primer parcial en acceso, perfiles iniciales, instituciones y catálogos, inventario sanguíneo ficticio, caducidad demostrativa, panel básico y auditoría.
- Se generaron Markdown y DOCX con el diseño homologado y se verificaron IDs, referencias, contenido, integridad OOXML, extracción y vista previa.

### 2026-08-31 — Correcciones puntuales de alcance y consistencia documental

- Se agregó al alcance del primer parcial el panel principal básico por perfil inicial, sin convertirlo en el panel regional posterior.
- RF-WEB-003 y las historias relacionadas ahora distinguen los tres perfiles habilitados en el primer parcial de los siete perfiles definidos para el alcance completo.
- RNF-MS-002 y HE-MS-001 exigen que los microservicios produzcan JSON y XML, además de documentar ambos formatos con OpenAPI/Swagger y utilizar XSD donde corresponda.
- RF-MS-004, RF-MS-005 y sus historias relacionadas explicitan la comparación u optimización por distancia y tiempo como apoyo a la priorización y el traslado, sin introducir reglas ni ponderaciones.
- RF-WEB-015 quedó con prioridad Alta, consistente con HU-WEB-013; ambos separan el panel básico inicial de su evolución regional.
- Instituciones quedó definida como entidad administrable y fuente conceptual única que puede reutilizarse como catálogo de referencia.
- Se sincronizaron únicamente las frases y celdas afectadas en las fuentes Markdown y los tres DOCX, conservando IDs, fases, estructura, estilo y trazabilidad.

### 2026-08-31 — Eliminación de la sección final de cobertura

- Se retiró completamente el punto 9 de Markdown y Word por repetir límites y comprobaciones presentes en otros apartados.
- La matriz de trazabilidad integral creada posteriormente conserva la comprobación formal entre requisitos, historias, criterios, reglas, casos y pruebas.
- El documento ahora termina con `HE-MON-001` y sus criterios de aceptación.
- Se verificó que permanecen 35 HU, 9 HE, las 94 relaciones con RF/RNF, 47 tablas, el diseño homologado y la integridad OOXML.

### 2026-08-31 — Usuarios dentro de las fichas de historias

- Se añadió una fila `Usuario` a las 35 historias de usuario con los perfiles consolidados del análisis que pueden participar en cada flujo.
- La página pública quedó asociada con el público general sin perfil de acceso; esto no crea un octavo rol autenticado.
- Las 9 historias habilitadoras utilizan `Responsable técnico` para distinguir equipos de trabajo de perfiles funcionales.
- Las frases conservan el formato “Como…, quiero…” sin resaltar al actor en negritas y la etiqueta cambió a `Historia:`; las habilitadoras utilizan `Historia habilitadora:`.
- Markdown y Word conservaron 35 HU, 9 HE, 94 relaciones con requerimientos, el diseño homologado y la integridad OOXML.

### 2026-08-31 — Retiro del resumen del backlog

- Se eliminó de Markdown y Word la tabla de cantidades por componente y el párrafo que enumeraba el subconjunto del primer parcial.
- La fase y prioridad continúan indicadas dentro de cada historia; la planeación del primer parcial permanece destinada al plan de trabajo o Sprint Backlog.
- Los apartados posteriores se renumeraron para que el documento avance de Propósito y alcance a Cobertura y límites mediante nueve secciones.
- Se verificó que no cambiaron las 35 HU, las 9 historias habilitadoras, los criterios de aceptación ni las 94 relaciones con requerimientos.
- El DOCX conserva el diseño homologado y quedó con 47 tablas, integridad OOXML y vista previa legible.

### 2026-08-31 — Homologación visual del documento de historias

- Se conservó sin cambios el contenido de `Historias_de_usuario.md`.
- El DOCX se regeneró tomando como plantilla real los estilos y el tema del documento consolidado de RF/RNF.
- Se aplicaron el título rojo oscuro con línea azul, el bloque gris de identificación, las jerarquías de encabezado y las tablas compactas con encabezados rojos y filas alternadas utilizadas en los demás entregables.
- Se eliminaron el diseño centrado, la portada amplia y el encabezado y pie de página que no pertenecían al conjunto documental anterior.
- Se verificaron nuevamente los 44 elementos, las 94 referencias a requisitos, las 48 tablas, las partes XML, la integridad del paquete y la vista previa.

### 2026-08-31 — Historias de usuario consolidadas

- Se revisaron las 55 historias originales contra el análisis corregido y los 94 RF/RNF consolidados, sin modificar los archivos anteriores.
- Se reemplazaron los roles antiguos por los siete perfiles aprobados y se evitó presentar al sistema, a una base de datos o a un arquitecto como usuario final.
- Se agruparon las funciones por flujo de valor en 35 historias de usuario y los requisitos técnicos en 9 historias habilitadoras.
- Cada elemento recibió fase, prioridad, validación, requisitos relacionados y criterios de aceptación verificables sin inventar reglas clínicas.
- Se conservó el alcance de todo el proyecto y se identificó el subconjunto viable del primer parcial: acceso, perfiles, catálogos, instituciones, inventario sanguíneo ficticio, panel, persistencia y auditoría.
- Se generaron `Historias_de_usuario.md` y `.docx`; se validaron los 44 identificadores, la relación con los 94 requerimientos, las 47 tablas, la integridad OOXML y la presentación inicial del Word.

### 2026-08-31 — Consolidación de RF/RNF semejantes

- Se revisaron las duplicaciones entre funcionalidades web, responsabilidades de microservicios y capacidades algorítmicas.
- Se agruparon acciones del mismo flujo, como inventario sanguíneo, revisión de compatibilidad, logística móvil, contratos de API y pruebas técnicas.
- Se conservaron separados los procesos con objetivos o riesgos distintos, especialmente donantes, receptores, sangre, órganos, asignación y custodia.
- La versión pasó de 144 a 94 requisitos: 53 funcionales y 41 no funcionales, manteniendo los ocho componentes obligatorios.
- Se generaron archivos consolidados separados porque el DOCX previo se encontraba abierto en Word durante la edición; el archivo abierto no fue sobrescrito.
- Se validaron identificadores, columnas, cobertura temática, integridad OOXML y presentación inicial del DOCX consolidado.

### 2026-08-31 — Limpieza de secciones internas del RF/RNF

- Se eliminaron el punto 11 de trazabilidad con el borrador anterior y el punto 12 de decisiones internas de alcance.
- Se retiró también del encabezado la referencia al archivo anterior para que la versión entregable se concentre en los requerimientos.
- Las aclaraciones indispensables sobre cobertura total, fases y límite clínico permanecen en el propósito y alcance.
- La matriz de trazabilidad académica se elaboró posteriormente con los requisitos consolidados, historias, criterios, reglas, casos y tipos de verificación.
- El DOCX se regeneró y se verificó que mantiene los 144 requisitos, termina en Monitoreo y conserva integridad OOXML.

### 2026-08-31 — Nueva versión de RF/RNF clasificada por componente

- Se creó una fuente Markdown y un DOCX nuevos sin borrar ni modificar el borrador anterior.
- Los requerimientos se organizaron por sistema web, microservicios, aplicación móvil, aplicación de escritorio, bases de datos, infraestructura, seguridad y monitoreo.
- Cada requerimiento recibió identificador por componente, fase, prioridad y estado de validación técnica, demostrativa o clínica/normativa.
- Se preservó el alcance completo, se identificó el subconjunto del primer parcial y se incorporó una tabla de trazabilidad por rangos con el documento anterior.
- Se comprobaron 144 identificadores únicos, la cobertura de los ocho componentes, la integridad del DOCX y la legibilidad de su vista previa inicial.

### 2026-08-31 — Alcance documental corregido para todo el proyecto

- Se aclaró desde el encabezado y el enfoque académico que el análisis cubre la solución completa y que los parciales solo ordenan la implementación.
- Se incorporaron expresamente el sistema web, los microservicios, Android y escritorio dentro del alcance documental total.
- Se mantuvo sin ampliaciones el producto mínimo del primer parcial y se indicó que las capacidades posteriores seguirán presentes en requisitos, historias y arquitectura.
- El resultado de la validación y la conclusión ahora conducen a requisitos funcionales y no funcionales de todo el proyecto, clasificados por componente y fase.
- Se regeneró el DOCX y se comprobaron contenido, tablas, referencias, enlaces, integridad OOXML y legibilidad de la vista previa inicial.

### 2026-08-31 — Referencias reubicadas al final

- Resultado de la validación y Conclusión se renumeraron como puntos 20 y 21.
- Referencias se movió después de la conclusión y quedó como punto 22 y última sección del análisis.
- Se conservaron sin cambios las 13 referencias APA y las citas autor-fecha dentro del contenido.
- El DOCX se regeneró y se verificaron los enlaces, la sangría francesa, el doble espacio y la integridad OOXML.

### 2026-08-31 — Eliminación de supuestos iniciales

- Se eliminó completamente la sección de supuestos iniciales por no ser un apartado solicitado expresamente en la rúbrica y repetir decisiones ya documentadas.
- Referencias, Resultado de la validación y Conclusión se renumeraron como puntos 20, 21 y 22.
- Se conservaron en sus apartados correspondientes el alcance académico, los datos ficticios, la supervisión humana y la referencia jurídica provisional.
- El DOCX se regeneró y se comprobó que mantiene las 13 referencias APA, sus enlaces y el formato de sangría francesa y doble espacio.

### 2026-08-31 — Referencias APA 7 y cierre del cuestionario abierto

- Se eliminó completamente el antiguo punto 21 de preguntas abiertas para el levantamiento.
- Referencias, Resultado de la validación y Conclusión se renumeraron como puntos 21, 22 y 23.
- Las fuentes institucionales se convirtieron en 13 referencias APA 7 ordenadas alfabéticamente; las dos leyes de privacidad se citaron por separado.
- Se incorporaron citas autor-fecha dentro de la introducción, el marco jurídico y el resultado de la validación para mantener correspondencia con la lista de referencias.
- El DOCX se regeneró con enlaces activos, sangría francesa y doble espacio en las referencias, y se verificó su integridad OOXML.

### 2026-08-31 — Consolidación de perfiles del sistema

- Se sustituyeron los diez perfiles preliminares por siete: Administrador, Operador de banco de sangre, Personal médico autorizado, Coordinador regional, Personal de traslado, Donante y Auditor.
- El ámbito regional o institucional quedó como restricción del Administrador, y las funciones operativas de banco y laboratorio se agruparon en el Operador de banco de sangre.
- El primer parcial quedó limitado a tres perfiles funcionales: Administrador, Operador de banco de sangre y Auditor.
- Receptores, instituciones, autoridades regulatorias y soporte técnico permanecen reconocidos como participantes, pero no generan roles adicionales en el alcance actual.
- Se regeneró el DOCX y se verificaron su integridad OOXML, el contenido de los siete perfiles y la ausencia de los roles reemplazados.

### 2026-08-31 — Fortalecimiento y validación académica del análisis

- Se declaró el carácter académico, documental y no clínico de la validación.
- Se sustituyó la lista genérica de procesos por modelos de referencia separados para sangre, órganos y coordinación interinstitucional, conservando pendientes de campo.
- Se añadieron perfiles mínimos, una clasificación conceptual de información y un alcance ejecutable para el primer parcial.
- Se adoptó México como referencia jurídica provisional y se contrastaron fuentes oficiales vigentes sin convertirlas en reglas clínicas.
- El MVP quedó limitado a inventario sanguíneo básico con datos ficticios, catálogos, acceso, persistencia y auditoría.
- Se regeneró el DOCX desde la fuente Markdown y se validaron integridad, contenido y presentación visual.

### 2026-08-27 — Nomenclatura en inglés y corrección del ciclo de citas

- Se tradujeron al inglés las 16 hojas, todos los nombres de tabla de las fases intermedias y finales, los 316 atributos únicos y los rótulos visibles del libro.
- Los datos ficticios permanecen en español, incluidos nombres, estados demostrativos, canales, motivos y descripciones.
- `CITAS` fue reemplazada visualmente por `APPOINTMENTS` y su campo de estado por `current_status`.
- `APPOINTMENT_STATUS_HISTORY` conserva las secuencias `SOLICITADA`, `APROBADA`, `PROGRAMADA` y `CONFIRMADA` según el estado alcanzado por cada ejemplo.
- Se restauró el estado `SOLICITADA` que se perdía en la segunda cita y se añadió identidad propia a cada necesidad de accesibilidad.
- El libro se regeneró, se validó como OOXML, se comprobó que conserva 94 relaciones finales únicas y se revisaron visualmente `Institutions` y `Appointments`.

### 2026-08-27 — Corrección de roles y ámbitos de usuario

- Se reemplazó la relación polimórfica e independiente de ámbitos por `USER_ROLE_INSTITUTIONS` y `USER_ROLE_SITES`.
- `USER_ROLES` recibió `user_role_id` para que cada ámbito quede ligado al rol concreto que el usuario puede ejercer.
- Se restauraron en 1FN los datos demostrativos de permiso `prueba_capturar` y ámbito `S3`, que estaban presentes en 0FN pero no se habían conservado en las fases siguientes.
- La propuesta de 4FN pasó de 93 a 94 relaciones únicas y se revisó visualmente la hoja `Usuarios`.

### 2026-08-27 — Limpieza visual de nombres y anotaciones del Excel

- Se eliminaron de los títulos de tabla los sufijos `_0FN`, `_1FN`, `_2FN`, `_3FN` y `_4FN` para mostrar únicamente nombres previstos de relaciones.
- Se retiraron todas las anotaciones grises, incluidas las leyendas de cambio, dependencia revisada y advertencias inferiores.
- Se conservaron las franjas amarillas que distinguen 0FN, 1FN, 2FN, 3FN y 4FN.
- Se actualizó el generador, se regeneró el libro y se comprobaron su integridad interna y apariencia mediante Quick Look.

### 2026-08-27 — Libro Excel de normalización 0FN a 4FN

- Se creó `Normalizacion_Red_Regional.xlsx` tomando como referencia la estructura visual del archivo académico proporcionado.
- Se incorporaron quince hojas relacionales: Instituciones, Usuarios, Campañas, Citas, Donantes, Donaciones, Receptores, Inventario, Solicitudes, Evaluaciones, Asignaciones, Traslados, Alertas, Archivos y Dispositivos.
- Cada hoja conserva el registro inicial y las tablas derivadas en 1FN, 2FN, 3FN y 4FN; cada fase se distingue mediante su franja amarilla.
- Se añadió `Almacenes_Cloud` para explicar PostgreSQL, MongoDB, Redis y Google Cloud Storage sin aplicarles incorrectamente formas normales relacionales.
- Todos los registros son ficticios; los valores sensibles o algorítmicos se marcaron como demostrativos y no se definieron reglas clínicas.
- Se añadió un generador reproducible y se validaron integridad OOXML, fases, estilos, ausencia de fórmulas y apariencia visual.
- El libro permanece como borrador sujeto a revisión; los documentos formales de 1FN a 4FN continúan pendientes.

### 2026-08-27 — Reparación de duplicación en la 0FN

- Se detectaron 37 repeticiones accidentales posteriores a la primera copia válida de la 0FN.
- Se conservaron las primeras 811 líneas verificadas y se restauró el párrafo final del documento.
- El archivo resultante contiene 814 líneas y una sola copia de cada sección; no se descartaron campos únicos del modelo.
- Se validaron nuevamente los dos diagramas Mermaid y el formato del parche.

### 2026-08-27 — Ampliación y corrección de la 0FN

- Se reemplazó la relación universal centrada en una solicitud por diez registros no normalizados orientados a procesos independientes.
- Se incorporaron instituciones y acceso, campañas y citas, donantes, receptores, inventario, solicitudes y asignaciones, traslado y custodia, alertas, archivos y reportes, y sincronización móvil.
- Se separaron explícitamente los grupos de sangre y órganos y se añadieron entradas, versiones, explicaciones y revisión humana para los algoritmos esperados, sin definir reglas clínicas ni ponderaciones.
- Se documentaron cinco documentos preliminares de MongoDB, familias de claves temporales de Redis y metadatos de objetos de Google Cloud Storage.
- Se añadió una matriz de cobertura para distinguir requisitos de datos de tecnologías de aplicación, API e infraestructura.
- Se validó nuevamente la sintaxis Mermaid y el formato de los cambios; 1FN continúa pendiente de revisión funcional.

### 2026-08-27 — Inicio del modelo ER y ruta de normalización

- Se creó `documentation/database-diagrams` con un índice de trabajo y documentos separados para el modelo conceptual, 0FN, 1FN, 2FN, 3FN y 4FN.
- Se elaboró un ERD conceptual inicial de 16 entidades para el núcleo de instituciones, donación, inventario, solicitudes, evaluación, asignación, traslado, custodia y evidencias.
- Se documentó una relación maestra 0FN con objetos y grupos repetitivos deliberados para analizar anomalías y dependencias.
- Las etapas 1FN a 4FN quedaron expresamente pendientes, con objetivos y criterios de aceptación, sin adelantar descomposiciones ni comandos SQL.
- Se validaron los dos diagramas con Mermaid 11.15 integrado en VS Code 1.134.0.
- No se instalaron extensiones ni se definieron reglas clínicas.

### 2026-08-12 — Conversión del análisis a Word

- Se generó `documentation/docx/Analisis_del_problema.docx` con estilos para títulos, párrafos, listas, tabla y enlaces.
- Se verificó la integridad del paquete DOCX y la presencia del contenido completo.
- Se conservó el archivo Markdown como fuente editable para evitar pérdida de contenido en futuras revisiones.

### 2026-08-12 — Documento de análisis del problema

- Se creó `documentation/markdowns/Analisis_del_problema.md` sin portada ni nombres de integrantes.
- Se desarrollaron el contexto, formulación, causas, consecuencias, actores, procesos por investigar, información, decisiones humanas, automatización, alcance, riesgos, privacidad, beneficios e indicadores.
- Se separaron los procesos de sangre y órganos y se mantuvo la supervisión médica y normativa como límite obligatorio.
- Se contrastó el marco general con fuentes oficiales de la OMS sin adoptar reglas clínicas ni una jurisdicción específica.

### 2026-08-12 — Definición del dominio del Proyecto 6

- Se estableció que la solución será una red regional de bancos de sangre y donación de órganos.
- Se documentaron objetivos, problema, actores conocidos, procesos, funciones por aplicación y catálogo inicial de microservicios.
- Se registraron las capacidades algorítmicas esperadas y el requisito de supervisión médica y normativa.
- Se añadió una distribución preliminar de datos, expresamente marcada como hipótesis pendiente de validación.
- No se implementaron reglas clínicas, algoritmos ni código.

### 2026-08-12 — Consolidación de requisitos ampliados

- Se revisó la especificación completa y se comparó con la arquitectura inicial.
- Se añadieron requisitos de seguridad, contratos XML/XSD, protección XXE, integración, tolerancia a fallos, algoritmo, grandes volúmenes, pruebas y documentación.
- Se ignoraron responsables por integrante, calendario académico y entregables por parcial, según la indicación del usuario.
- Se registraron como recomendaciones, y no como obligaciones, la cantidad de microservicios, las herramientas de tablero y la metodología de sprints.

### 2026-08-12 — Inicio de documentación

- Se documentaron la visión, componentes, tecnologías y restricciones obligatorias.
- Se creó una lista inicial de trabajo pendiente sin asumir decisiones de negocio aún no tomadas.
- No se creó código, infraestructura ni configuración ejecutable.

## Próximo paso recomendado

El monolito está listo para arrancar desde `apps/web-monolito01` con `python3 run.py`, sin activar `.venv` ni repetir la instalación o reinicializar la base. El primer parcial está cerrado; antes de implementar más funcionalidad debe acordarse el siguiente proceso y validar sus reglas. MongoDB, Redis, microservicios, clientes, nube y Docker mantienen su calendarización posterior.
