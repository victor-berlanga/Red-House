# PostgreSQL · Subconjunto físico del monolito

[schema.sql](schema.sql) es la única definición física ejecutable de este incremento: **23 tablas, una vista y restricciones de historial** en el esquema `red_house`, para PostgreSQL 14 o superior. No hay una copia en el código ni un segundo modelo ORM.

Se deriva del análisis, las historias y la matriz de perfiles de `documentation/markdowns`, considerando el [modelo lógico 4FN](../../documentation/database-diagrams/Modelo_4FN.md) y su [trazabilidad](../../documentation/database-diagrams/Trazabilidad_0FN_4FN.md). No instala las 169 relaciones semestrales ni sustituye la documentación de normalización. El Excel histórico no es fuente del SQL.

## Distribución de las tablas

| Responsabilidad | Tablas físicas |
| --- | --- |
| Instituciones y sedes | `institution`, `site` |
| Contactos y medios separados | `contact`, `contact_method`, `institution_contact` |
| Capacidades institucionales independientes de contactos | `capability`, `institution_capability` |
| Identidad, perfil y ámbito vigente | `party`, `user_account`, `role`, `account_role` |
| Catálogo, ubicación y parámetros versionados | `blood_component`, `storage_location`, `parameter_version` |
| Unidad sanguínea y clasificación de ejemplo | `resource`, `blood_unit`, `blood_classification` |
| Transiciones e historial de movimientos | `blood_status_transition`, `blood_movement` |
| Auditoría y valores modificados | `audit_event`, `audit_change` |
| Controles temporales del web | `web_session`, `login_attempt` |

Los identificadores, tablas y columnas están en inglés. Las PK son UUID salvo los códigos de catálogos, claves de asociación y el contador técnico de intentos. Las FK conservan integridad referencial; no hay borrados en cascada de la evidencia.

## Proyección y decisiones del MVP

- La separación lógica entre institución, sede, contacto, medio y capacidad se conserva. No se guardan listas de teléfonos, capacidades o movimientos en columnas JSON, CSV o arreglos. La dirección administrativa de la institución y la dirección física de la sede son hechos distintos.
- La interfaz mantiene un contacto de coordinación por institución, con hasta un correo y un teléfono vigentes; las relaciones físicas permiten ampliar contactos posteriormente. No se presenta esta reducción como el catálogo completo de contactos del semestre.
- `party` conserva únicamente el nombre necesario para las cuentas internas. No se crean donantes, receptores ni expedientes clínicos antes de implementar esos procesos.
- `account_role` representa una sola asignación vigente de **cuenta–rol–ámbito**. Su PK es `account_id`; el ámbito es una institución o una región, nunca ambos. No se cruzan listas independientes de roles y tenants. El operador requiere institución. La autorización por acción está en la matriz explícita de `business/access.py`; permisos configurables, múltiples asignaciones y sus historiales requieren un incremento posterior.
- La región se identifica por un valor escalar controlado desde la carga inicial y heredado del administrador; no es todavía un catálogo geográfico. La aplicación no permite cambiar de región a instituciones existentes. Los componentes se administran regionalmente y el código de componente es único en este esquema académico.
- `resource` conserva el folio común y `blood_unit` los hechos propios de sangre. Solo se admite `BLOOD` en este corte; no se mezclan atributos de órganos en la tabla de unidades. La clasificación es un grupo ficticio con referencia de origen, no una prueba clínica ni un cálculo de compatibilidad.
- El estado y la ubicación actuales están en la unidad; los eventos previos se anexan a `blood_movement` con secuencia única por recurso, actor y motivo. Esta proyección actual se actualiza junto con el historial en una sola transacción. No se duplican el nombre de la institución ni el componente en cada unidad.
- La institución propietaria se obtiene por `blood_unit → storage_location → site → institution`. Los repositorios filtran por esa asociación y los servicios impiden movimientos entre instituciones; conocer un UUID no otorga acceso.
- `blood_inventory` es una **vista**, no una tabla duplicada. Une las referencias y calcula vigencia/disponibilidad con el reloj de PostgreSQL. No se necesita un proceso que sobrescriba estados por el paso del tiempo.
- Las versiones del único parámetro son inmutables y tienen `is_demo=true`. La versión no equivale a una validación médica. Las transiciones del pequeño catálogo son igualmente DEMO.
- La bitácora estructurada y su detalle escalar están en PostgreSQL durante el primer parcial. Las referencias de ámbito y actor son evidencia del evento, no copias modificables del perfil actual. El diseño documental futuro no se adelanta mediante tablas JSON genéricas.
- `web_session` y `login_attempt` son soporte técnico acotado de autenticación local. Redis, refresh tokens y contratos compartidos quedan para su fase; ningún cliente externo se conecta a estas tablas.

Estas decisiones son hipótesis físicas restringidas al incremento académico, **no una nueva demostración de 4FN del sistema completo**. Antes de ampliar el SQL hay que reconciliar sus claves y dependencias con el modelo lógico, definir migraciones y validar campos y responsabilidades. Los documentos de 0FN–4FN anteriores permanecen intactos.

## Reconciliación técnica del primer parcial

La revisión del 6 de septiembre de 2026 contrastó los RF del primer parcial, el modelo lógico, este SQL y las operaciones/pruebas del monolito. El resultado técnico es conforme para el incremento académico: las diferencias siguientes son reducciones explícitas de alcance, no una migración equivalente de las 169 relaciones. El usuario confirmó la revisión realizada por el equipo y autorizó el cierre de `P1-03`; esta confirmación y las evidencias técnicas se registran en `PROJECT_STATUS.md`. No se realizaron operaciones de Git como parte de este cierre.

| Tablas físicas revisadas | Correspondencia y límite frente al modelo lógico |
| --- | --- |
| `institution`, `site` | Conservan las identidades y códigos únicos; institución y sede son hechos distintos. La dirección es texto administrativo y ciudad, sin consultas por número, código postal o coordenadas; esos campos requieren una ampliación posterior. `version_no` controla concurrencia, no representa una versión clínica. |
| `contact`, `contact_method`, `institution_contact` | Conservan contactos y medios separados. La PK de medio pasa a `(contact_id, method_kind)` porque el MVP permite un correo y un teléfono por contacto; no maneja propósitos ni varios medios de la misma clase. La unicidad de `institution_contact.contact_id` limita cada contacto a una institución. Ampliar estas cardinalidades requiere migración, no reutilizar esa clave sin revisión. |
| `capability`, `institution_capability` | `capability_code`, ya único en el modelo lógico, funciona como clave física del catálogo. La asociación `(institution_id, capability_code)` describe pertenencia vigente, sin intervalos ni identidad propia del historial. No se mezcla con la lista independiente de contactos. |
| `party`, `user_account`, `role`, `account_role` | Se conservan identidad interna, cuenta, correo único y catálogo. `role_code` sustituye la clave técnica del rol. Una cuenta tiene una única asignación vigente de rol y ámbito, con exclusión institución/región y obligación de institución para el operador. Las concesiones múltiples, vigencias, permisos configurables y expedientes de personas no forman parte de este corte; la matriz de acciones se aplica en `business/access.py`. |
| `blood_component`, `storage_location` | Conservan PK, códigos y referencias; la región del componente y las banderas de activación delimitan el catálogo operativo. Un código de ubicación es único dentro de su sede. No se crean atributos clínicos abiertos ni un catálogo geográfico. |
| `parameter_version` | La clave técnica se conserva; la clave alternativa física incluye región: `(region_name, parameter_code, version_no)`. La numeración es regional, a diferencia de la pareja global propuesta en el modelo lógico. Solo existe el aviso DEMO de caducidad, inmutable por versión, sin calcular vidas útiles ni afirmar aprobación clínica. Esta diferencia deberá resolverse expresamente en una migración semestral. |
| `resource`, `blood_unit`, `blood_classification` | Se conserva la especialización por `resource_id` y el folio único de `resource`; no se duplica un segundo folio de unidad. No hay episodios de donación ni revisiones de laboratorio implementados: las fechas se capturan y la clasificación exige una referencia ficticia. `resource_kind` solo admite sangre. No se incorporan órganos ni supuestos de compatibilidad. |
| `blood_movement` | Se conservan identidad, secuencia única por recurso, estado, origen, destino, fecha y motivo. El actor físico referencia la cuenta interna, en vez de la persona general del modelo lógico. La operación comprueba ámbito, transición y versión, y guarda movimiento y auditoría en la misma transacción. |
| `audit_event`, `audit_change` | Proyección de `AUDIT_EVENT`, `AUDIT_RECORD` y `AUDIT_FIELD_CHANGE`: cada evento físico tiene un único objeto principal, por lo que el cambio usa `(event_id, field_name)` sin `record_no`. Correlación, resultado y ámbito son hechos del evento. Se conservan solo valores autorizados; no se implementan todavía la auditoría distribuida ni la reconstrucción completa del rol histórico. |
| `blood_status_transition` | Catálogo técnico de transiciones DEMO, sin equivalencia automática con reglas clínicas versionadas del modelo semestral. |
| `web_session`, `login_attempt` | Soporte técnico local de sesión, revocación y límites de intentos en PostgreSQL. Su temporalidad está documentada; Redis y la autenticación entre componentes permanecen posteriores. |

Las 23 tablas tienen PK; el catálogo real de PostgreSQL confirmó 24 FK y 21 restricciones `CHECK`, sin columnas JSON ni arreglos. La vista `blood_inventory` reconstruyó las 36 unidades ficticias mediante sus referencias sin crear una tabla duplicada. El conjunto lógico volvió a superar su verificador de 49 diagramas y dependencias declaradas. Esto comprueba el alcance técnico descrito, no reglas clínicas desconocidas ni una certificación de 4FN de todo el SQL.

Los [resultados y límites de la revisión](../../documentation/evidence/primer-parcial/README.md) incluyen el catálogo obtenido, las pruebas y evidencia de navegador. No fue necesario cambiar `schema.sql` ni los modelos de 0FN–4FN.

## Integridad y operación

- Caducidad posterior a recolección; listas permitidas de estados, grupos DEMO, perfiles y tipos; unicidad de folios/correos/códigos y asociaciones.
- Índices de referencias, caducidad disponible, ámbito/fecha de auditoría, sesiones e intentos. No se afirma que sustituyan mediciones de volumen o `EXPLAIN`.
- `version_no` evita sobrescrituras de formularios antiguos. Los movimientos usan bloqueo de fila, control de versión y secuencia única. Los parámetros usan bloqueo transaccional regional.
- Historiales de auditoría, movimientos y parámetros rechazan `UPDATE` y `DELETE` mediante triggers. No se han creado roles PostgreSQL diferenciados ni políticas RLS: es una base académica local, no un límite frente a su propietario, `TRUNCATE` o cambios DDL autorizados.
- La aplicación maneja rollback y errores sin mostrar SQL, credenciales ni detalles de conexión. No hay auto-reintento ciego de operaciones de negocio.

## Inicialización y pruebas

La vía recomendada es `setup.sh` (macOS/Linux) o `setup.cmd` (Windows), descrita en el [README del monolito](../../apps/web-monolito01/README.md). El instalador crea una base local nueva y reutiliza este `schema.sql` y la función de carga DEMO de `src/cli.py`: no mantiene copias del esquema o las semillas. Esquema y carga nuevos se confirman juntos en una transacción. Una repetición conserva las cuentas y sus contraseñas; se rechazan bases ajenas, esquemas parciales y mezclas con datos previos. `--check` utiliza una conexión de solo lectura y nunca inicializa ni carga datos.

Como alternativa manual, usa `init-db` y `seed-demo` del mismo README. El primero ejecuta el archivo completo dentro de una transacción; no incorpora `DROP` ni `IF NOT EXISTS` que pudieran ocultar un esquema incompatible. Una segunda inicialización manual se rechaza sin modificar datos existentes. No combines ambas vías sobre una base ya preparada.

Si se ejecuta manualmente, debe ser en una base dedicada vacía y con transacción única, por ejemplo desde este directorio:

```sh
psql --single-transaction --set=ON_ERROR_STOP=1 --dbname=red_house --file=schema.sql
```

No ejecutes el SQL sobre una base institucional ni hagas ambos métodos de inicialización. La carga ficticia es opcional y explícita, pero es la vía proporcionada para crear los primeros accesos del entorno DEMO. No hay un SQL con contraseñas ni datos de pacientes.

Las pruebas de integración crean bases temporales distintas a partir del mismo `schema.sql`; prueban restricciones, autorización, movimientos simultáneos, rollback ante fallo de auditoría y pérdida de conectividad. No utilizan SQLite ni repositorios simulados como evidencia de persistencia. Las mediciones masivas, restauración, migraciones de datos existentes y validación normativa siguen pendientes.
