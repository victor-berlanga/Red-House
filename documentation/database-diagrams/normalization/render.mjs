import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {tables, schemaAt, partialSteps, transitiveSteps} from './model.mjs';
import {lineage} from './lineage.mjs';

const tick = value => `\`${value}\``;
const list = values => values.map(tick).join(', ');
const domains = [...new Set(tables.map(t=>t.domain))];
const nodeId = name => name.toLowerCase().replace(/_([a-z])/g,(_,c)=>c.toUpperCase());
const keyText = t => t.keys.map((key,i)=>`${i===0?'PK':'CK'+i}: (${key.join(', ')})`).join('; ');
const index = schema => new Map(schema.map(t=>[t.name,t]));
const attributes = t => t.columns.map(c=>c.name);
const stages = [0,1,2,3,4].map(n=>n ? schemaAt(n) : []);
function fkText(t,schema) {
  const byName = index(schema);
  return t.foreign.map(f=>`(${f.columns.join(', ')}) → ${f.target}(${(f.targetColumns.length?f.targetColumns:byName.get(f.target).keys[0]).join(', ')})${f.optional?' [opcional]':''}`).join('; ') || '—';
}
function diagram(home,schema) {
  const byName = index(schema);
  const references = [...new Set(home.flatMap(t=>t.foreign.map(f=>f.target)))].filter(name=>!home.some(t=>t.name===name));
  const lines = ['erDiagram','    direction LR'];
  for (const t of [...home,...references.map(name=>byName.get(name))]) {
    const external = references.includes(t.name);
    lines.push(`    ${nodeId(t.name)}["${t.name}"] {`);
    for (const c of t.columns.filter(c=>!external || t.keys[0].includes(c.name) || home.some(h=>h.foreign.some(f=>f.target===t.name && f.targetColumns.includes(c.name))))) {
      const badges = [];
      if(t.keys[0].includes(c.name)) badges.push('PK');
      if(!external && t.foreign.some(f=>f.columns.includes(c.name))) badges.push('FK');
      if(t.keys.slice(1).some(k=>k.length===1&&k[0]===c.name)) badges.push('UK');
      lines.push(`        ${c.type} ${c.name}${badges.length?' '+badges.join(', '):''}`);
    }
    lines.push('    }');
  }
  for (const t of home) for (const f of t.foreign) {
    const one = t.keys.some(k=>k.every(c=>f.columns.includes(c)));
    const identifying = f.columns.every(c=>t.keys[0].includes(c));
    const relation = `${f.optional?'o|':'||'}${identifying?'--':'..'}${one?'o|':'o{'}`;
    const label = `by_${f.columns.join('_and_').replace(/_id\b/g,'')}`;
    lines.push(`    ${nodeId(f.target)} ${relation} ${nodeId(t.name)} : ${label}`);
  }
  return '```mermaid\n'+lines.join('\n')+'\n```\n';
}
function catalog(schema,withTypes=false) {
  return domains.map(domain=>{
    const rows = schema.filter(t=>t.domain===domain).map(t=>`| ${tick(t.name)} | ${tick(keyText(t))} | ${tick(t.columns.map(c=>withTypes?`${c.name}: ${c.type}`:c.name).join(', '))} |`);
    return `### ${domain}\n\n| Relación | Claves candidatas | Atributos completos |\n| --- | --- | --- |\n${rows.join('\n')}\n`;
  }).join('\n');
}
const sourceLinks = `[0FN de partida](./Modelo_0FN.md), [1FN](./Modelo_1FN.md), [2FN](./Modelo_2FN.md), [3FN](./Modelo_3FN.md), [4FN](./Modelo_4FN.md) y [trazabilidad completa](./Trazabilidad_0FN_4FN.md)`;
const status = '> Estado: normalización lógica desarrollada para el ejercicio académico, bajo las dependencias y decisiones declaradas. No es una base instalada, un modelo físico aprobado ni una validación clínica.\n';
const conventions = `
## Convenciones y límites

- Nombres de tablas y atributos en inglés. PK es la clave primaria escogida; CK identifica otra clave candidata y UK se dibuja solo cuando la unicidad corresponde a un atributo individual. Una CK compuesta **no** significa que cada columna sea única por separado.
- Los identificadores técnicos permiten distinguir hechos, pero no demuestran una forma normal. Se examinan también las claves candidatas compuestas, por ejemplo \`(appointment_id, sequence)\` y \`(catalog_id, version_no)\`.
- \`uuid\`, \`string\`, \`decimal\` y los demás tipos son dominios lógicos, no decisiones de longitud, motor, índices ni DDL. \`version_no\` admite rótulos de versión; \`sequence\`, \`revision_no\` y posiciones de elementos son ordinales enteros.
- Cada \`scalar_value\`, \`scalar_result\` o respuesta contiene un único valor del dominio indicado por su código. No se permiten JSON, arreglos, objetos, listas separadas por comas ni varios resultados clínicos ocultos en una cadena. Una nota narrativa es un dato textual; no sustituye una lista de hechos consultables.
- Los nombres, fechas de nacimiento y componentes de dirección son una atomización mínima propuesta de los objetos abiertos de la 0FN; no se afirma que la documentación haya aprobado un formulario clínico definitivo. No se impone un identificador nacional, una regla médica ni una equivalencia automática entre donante, receptor y cuenta.
- Los objetos \`*_details\` de referencia se resuelven por relaciones. Las entradas de una evaluación, el destino usado al enviar una alerta y el contexto de auditoría son hechos históricos: conservan el valor observado, no se reemplazan por el valor actual de otra tabla.
- Una ausencia opcional se representa mediante ausencia de la fila asociativa, cuando existe una relación específica; las FK opcionales restantes se señalan en el catálogo. No se usan filas ficticias, identificadores vacíos ni NULL dentro de claves candidatas. La traducción de opcionalidad a restricciones físicas sigue pendiente.
- Las listas con identidad propia conservan esa identidad. Las listas ordenadas o con repeticiones significativas conservan un ordinal, evento o versión; las relaciones de pertenencia sin orden tienen semántica de conjunto. No se emparejan listas independientes por su posición.
`;
const familyTable = `
## Procedencia y decisiones frente al Mermaid anterior

La entrada es exclusivamente el **modelo recién creado de 18 tablas**, no el Excel anterior. La nueva solicitud permite consultar el diagrama anterior basado en HU, conservado como antecedente en el repositorio de origen, como referencia de relaciones. Se mantiene intacta la 0FN para que la transformación sea verificable.

| Aspecto observado en la referencia | Decisión en esta normalización |
| --- | --- |
| Recurso común con detalle sanguíneo y de órgano | \`RESOURCE\` concentra solo identidad, código y clase; \`BLOOD_UNIT\` y \`ORGAN_AVAILABILITY\` conservan ciclos y datos separados. No se unifican reglas clínicas. |
| Donación, pruebas y evidencia separadas | Se extraen los episodios, muestras, pruebas, revisiones, observaciones y vínculos con versiones documentales que ya estaban anidados en la 0FN. |
| Candidato vinculado con solicitud y recurso | Se conserva una ejecución \`CANDIDATE_ASSESSMENT\` con varios \`ASSESSMENT_CANDIDATE\`; una reevaluación no sobrescribe la anterior. |
| Usuario con una institución y asignaciones de rol | Se conserva el alcance más amplio de la nueva 0FN: rol, permiso y ámbito quedan unidos por \`ACCESS_GRANT\`. No se restringe una cuenta a una institución ni se conceden permisos por productos cartesianos. |
| Alerta con un destinatario | Se conserva la lista original mediante destinatarios, entregas por canal, intentos y acuses separados, sin perder sus asociaciones. |
| Campos como alelo_1 y alelo_2 | \`HLA_CALL\` conserva una llamada por locus y posición; no se introduce una cantidad fija ni una interpretación clínica. |
| Antes/después o referencia de resultado como texto amplio | Se separan observaciones y cambios por campo. Los binarios y explicaciones documentales extensas mantienen sus fronteras de almacenamiento. |

La distribución en diecisiete dominios es documental: no determina la cantidad de microservicios ni autoriza tablas compartidas con varios escritores.
`;
const lossless = `
## Conservación de información

Para cada DF \`X → Y\` utilizada, se descompone la relación de entrada R en \`R1 = X ∪ Y\` y \`R2 = R − (Y − X)\`. La intersección contiene X y X determina R1; por ello el join de esas proyecciones no introduce tuplas espurias en una instancia que satisfaga la DF. La DF eliminada queda comprobable en su relación propietaria.

En este ejercicio la relación propietaria ya puede existir desde la extracción de 1FN. En ese caso se conserva una única copia de sus atributos y se valida la FK, no se crea una segunda tabla del mismo catálogo. Las filas propietarias sin hijos permanecen: no se reconstruyen mediante un inner join que las elimine.

Si dos copias actuales del mismo determinante contienen valores distintos, la entrada viola la DF. No se elige una de forma arbitraria: debe corregirse con evidencia, o reconocerse que se trata de versiones históricas distintas y conservar su identificador de versión. Las pruebas incluyen este contraejemplo.
`;
function transitions(steps,from,to) {
  const before=index(stages[from]),after=index(stages[to]);
  return steps.map((s,i)=>{
    const t=before.get(s.table), out=after.get(s.table), target=after.get(s.target);
    return `### ${i+1}. ${s.table}\n\n- Relación de entrada: ${tick(`${s.table}(${attributes(t).join(', ')})`)}.\n- Claves candidatas: ${tick(keyText(t))}.\n- DF que provoca la separación: ${tick(`${s.determinant.join(', ')} → ${Object.keys(s.mappings).join(', ')}`)}.\n- Atributos retirados de la fila hija: ${list(Object.keys(s.mappings))}. Se conservan en ${tick(s.target)}, bajo ${tick(target.keys[0].join(', '))}; los alias ${Object.entries(s.mappings).map(([a,b])=>tick(`${a} → ${s.target}.${b}`)).join(', ')} preservan su significado.\n- Relación resultante: ${tick(`${s.table}(${attributes(out).join(', ')})`)}. Las claves y referencias válidas se mantienen.\n\n${diagram([out,target],stages[to])}`;
  }).join('\n');
}
const checks = `
## Verificación reproducible

Desde la raíz del proyecto:

\`\`\`sh
node documentation/database-diagrams/normalization/validate.mjs
\`\`\`

El verificador comprueba los cuatro esquemas, claves declaradas y su minimalidad respecto de las DF proporcionadas, FK y tipos, redundancias parciales y transitivas, trazabilidad de los 208 atributos iniciales, cobertura de todas las tablas finales, reconstrucciones de ejemplo y sintaxis Mermaid. También detecta divergencias entre la especificación y los Markdown.

Las pruebas usan datos DEMO sin significado clínico. No descubren dependencias de negocio, no prueban todas las instancias posibles y no sustituyen la justificación algebraica ni la revisión funcional. Una DF o DMV nueva obliga a volver a evaluar la forma normal. El analizador Mermaid se carga de la instalación local de VS Code; en otro entorno se puede indicar un módulo ya instalado mediante \`NORMALIZATION_MERMAID_MODULE\`, sin instalar dependencias automáticamente.
`;

const first = `# Modelo en primera forma normal (1FN)

${status}
Ruta: ${sourceLinks}.
${familyTable}
## Transformación de 0FN a 1FN

Las 18 estructuras iniciales contenían listas dentro de filas. Se conserva cada registro padre aunque su lista esté vacía; cada elemento pasa a una fila hija identificada por su propia referencia o por la clave del padre más un ordinal. Los subgrupos se extraen recursivamente: por ejemplo, destinatario → entrega → intento → acuse, y evaluación → candidato → factor.

El resultado tiene **${tables.length} relaciones lógicas**. La cantidad responde al desarrollo de los grupos e historiales del alcance semestral; no es el mínimo de tablas del primer parcial. Muchas relaciones ya satisfacen formas superiores después de esta extracción: no es necesario degradarlas para hacer el ejercicio.

Se conservan deliberadamente **ocho casos de dependencia parcial** y **cuatro de dependencia transitiva** en este esquema 1FN. Son descriptores de referencia actualmente repetidos, no copias históricas inmutables. Los demás atributos ya se sitúan en la relación correspondiente al hecho que describen.

### Ejemplo DEMO de extracción

Una institución puede tener contactos [C1, C2] y ninguna sede todavía. Se conserva su fila en \`INSTITUTION\`, dos pertenencias en \`INSTITUTION_CONTACT\` y ninguna fila en \`SITE\`. No se crea una sede ficticia, ni se elimina la institución por un join sin coincidencias. Cada método de C1 se conserva en \`CONTACT_METHOD\` con su identidad; si dos eventos tienen el mismo contenido, sus identidades u ordinales permiten conservar ambos.

${diagram(['INSTITUTION','CONTACT','CONTACT_METHOD','INSTITUTION_CONTACT','SITE','SITE_SCHEDULE'].map(n=>index(stages[1]).get(n)),stages[1])}
${conventions}
## Catálogo completo de 1FN

Este catálogo define todas las relaciones de la etapa, no solo un ejemplo. Las FK se conservan a lo largo de las etapas y se detallan en las vistas finales. Los atributos retirados en 2FN y 3FN aparecen explícitamente aquí. La [matriz de trazabilidad](./Trazabilidad_0FN_4FN.md) vincula cada atributo de 0FN con sus destinos.

${catalog(stages[1])}
${checks}`;

const second = `# Modelo en segunda forma normal (2FN)

${status}
Ruta: ${sourceLinks}.

## Criterio formal

Se parte del catálogo completo de 1FN. Una relación está en 2FN si está en 1FN y ningún atributo no primo depende funcionalmente de un subconjunto propio de una clave candidata. Se revisan **todas** las claves candidatas, no solo la PK elegida.

En particular, \`SITE\` tiene la CK \`(institution_id, site_code)\`: copiar el nombre institucional genera una dependencia parcial aunque exista \`site_id\` como PK. Análogamente, \`CATALOG_VERSION\` tiene la CK \`(catalog_id, version_no)\`; sus descriptores de catálogo se separan aquí, no se posponen erróneamente a 3FN.

## Esquema completo por transformación

El esquema 2FN es exactamente el catálogo completo de [1FN](./Modelo_1FN.md) con las ocho sustituciones siguientes. **Todas las relaciones no mencionadas conservan íntegramente sus atributos, claves y FK.** No se retiran filas padre, grupos ni hechos. Quedan ${tables.length} relaciones porque los propietarios de los descriptores ya existen en 1FN.

${transitions(partialSteps,1,2)}
${lossless}
## Anomalías eliminadas y pendiente de 3FN

Una referencia candidata copiada conserva sus dependencias: por ejemplo, \`appointment_reference → appointment_id\` induce la CK (appointment_reference, sequence) en el evento aplanado de 1FN. Al retirar esa copia, la hija mantiene su clave canónica; la clave alternativa basada en el alias se recupera al unir con APPOINTMENT, no se conserva una columna redundante solo para mantenerla materializada. La especificación incluye estas DF inversas y claves inducidas.

Una modificación del estado de un catálogo o del descriptor actual de una cita ya no exige modificar cada entrada o evento. Los datos propios del evento —estado anterior/nuevo, fecha, actor y motivo— permanecen en su fila histórica.

Todavía se repiten descriptores de rol en \`ACCOUNT_ROLE\`, de componente en \`BLOOD_UNIT\`, de receptor en \`RESOURCE_REQUEST\` y de sede de origen en \`TRANSFER_ORDER\`. Sus determinantes no son subconjuntos de las claves candidatas de esas relaciones, pero producen dependencias transitivas: se resuelven en la siguiente etapa.
${checks}`;

const third = `# Modelo en tercera forma normal (3FN) y comprobación BCNF

${status}
Ruta: ${sourceLinks}.

## Criterio formal

Para cada DF no trivial \`X → A\`, 3FN exige que X sea superclave o que A sea un atributo primo. BCNF exige que **todo** determinante de una DF no trivial sea superclave. Se comprueba BCNF antes de concluir 4FN; añadir UUID o retirar listas no reemplaza esta comprobación.

## Esquema completo por transformación

El esquema 3FN es el esquema de [2FN](./Modelo_2FN.md), incluidas sus relaciones heredadas, con las cuatro sustituciones siguientes. Todas las relaciones restantes mantienen exactamente atributos, claves y FK. El catálogo completo resultante, también usado al comprobar 4FN, está en [Modelo_4FN.md](./Modelo_4FN.md).

${transitions(transitiveSteps,2,3)}
${lossless}
## DF y BCNF del esquema resultante

En el conjunto de dependencias declarado, cada clave candidata K determina los demás atributos de su relación. Las dependencias no clave anteriores quedan alojadas en sus propietarios: institución, catálogo, rol, componente, receptor o sede. No se conserva ninguna excepción a BCNF en el esquema final.

| Familia de relaciones | Dependencia y significado |
| --- | --- |
| Registros principales | Identificador o referencia candidata → atributos propios del registro. No se copian nombres actuales de entidades referenciadas. |
| Versiones | Identificador de versión o (propietario, versión) → contenido de esa versión. Una versión de regla no es solo su rótulo: incluye fuente, vigencia, ámbito y aprobación. |
| Eventos | Identificador de evento o (proceso, secuencia) → instante, actor y datos del hecho. Un proceso puede tener varios eventos distintos. |
| Elementos de evaluación | (evaluación, recurso) o (evaluación, número de candidato) → un candidato; (candidato, factor) → medición y peso aplicado en ese resultado. No se supone que el nombre del factor determine un peso universal. |
| Vínculos de pertenencia | La clave compuesta representa el hecho completo. No contiene la descripción de ninguno de sus extremos. |
| Versiones vigentes | En \`DOCUMENT_CURRENT_VERSION\` y \`ORGAN_CURRENT_VIABILITY\`, ambos extremos son claves candidatas. La pertenencia al mismo propietario es una restricción adicional comprobable. |

Los datos de \`ASSESSMENT_INPUT\`, observaciones, motivos, respuestas y cambios por campo son valores atómicos de un hecho identificado, no una bolsa para ocultar grupos de 0FN. Sus códigos y dominios concretos deberán validarse antes del modelo físico.

## Lo que la normalización no elimina

El estado vigente y el historial describen hechos distintos. Se conserva \`APPOINTMENT.current_status\` y sus eventos; su coherencia requerirá una transacción. Tampoco se sustituye el valor observado por un algoritmo con un join a datos actuales. Los cambios históricos permanecen anexados o versionados, no sobrescritos.

Que todas las DF conocidas satisfagan BCNF aún exige revisar las DMV. La siguiente etapa realiza esa comprobación sin asumir que toda relación de varios a varios es una independencia.
${checks}`;

const integrity = `
## Restricciones de integridad que acompañan al modelo

Estas restricciones no son pruebas de normalización ni reglas clínicas nuevas; evitan que las asociaciones pierdan el significado que tenían en la 0FN. Su traducción a FK compuestas, restricciones diferidas, transacciones y autorización se decidirá en el modelo físico.

1. **Recurso y sujeto.** Cada \`RESOURCE\` tiene exactamente un subtipo sanguíneo u órgano acorde con \`resource_kind\`. Cada \`STUDY_SUBJECT\` tiene exactamente uno de \`DONOR_SUBJECT\`, \`RECIPIENT_SUBJECT\` o \`RESOURCE_SUBJECT\`. Los resultados sanguíneos y de órganos corresponden al \`study_kind\` de la prueba; HLA no impone por sí mismo elegibilidad o compatibilidad.
2. **Solicitud, candidato y asignación.** El candidato referido por \`ALLOCATION_ASSESSMENT\` debe pertenecer a una evaluación de la misma solicitud y al mismo recurso de \`ALLOCATION\`. Su ausencia no permite omitir la autorización humana requerida. La cantidad de unidades se representa por varias asignaciones a recursos individuales; su suma y los estados activos se validan transaccionalmente. Un recurso no puede tener asignaciones activas incompatibles (RN-LOG-002).
3. **Permisos.** \`ACCESS_GRANT\` autoriza un permiso en un ámbito para una asignación de rol concreta y con vigencia. No se generan permisos efectivos uniendo libremente listas de roles, permisos y sitios. Los subtipos de \`ACCESS_SCOPE\` son excluyentes; la habilitación de un rol no reemplaza \`PROFESSIONAL_AUTHORIZATION\`. La cuenta del donante se vinculará únicamente tras verificar su identidad; no se deduce por nombre o correo de contacto.
4. **Campañas.** \`APPOINTMENT_CAMPAIGN\` es opcional. Cuando existe, su slot pertenece a una campaña publicada y la sede coincide con la de la cita. Los cambios de slot conservan referencias anterior y nueva. El cálculo de cupos no cuenta estados cancelados como citas activas; los estados concretos siguen pendientes de validación.
5. **Ubicación y custodia.** La institución actual de una unidad se obtiene desde \`STORAGE_LOCATION → SITE → INSTITUTION\`. No se guarda de nuevo en \`BLOOD_UNIT\`. Los traslados conservan su asignación y extremos; cambiar un extremo no reescribe eventos confirmados. La corrección de un evento pertenece al mismo traslado y referencia un evento previo. Captura y evidencia corresponden al mismo traslado, finalidad y periodo autorizados.
6. **Versiones y correcciones.** Cada \`TEST_REVISION.corrects_revision_id\` refiere una revisión anterior de la misma prueba. El documento o viabilidad señalado como vigente pertenece al mismo propietario de su puntero; las versiones de documentos, reglas, métodos y parámetros ya usadas permanecen inmutables. \`object_identifier\` identifica una versión concreta del objeto, no solo una ruta reutilizable. Las actualizaciones de estado vigente se realizan junto con su evento histórico.
7. **Vínculos contextualizados.** Las entradas afectadas por un cambio pertenecen a la versión de catálogo del cambio. Un profesional asignado a una atención tiene facultades para ese ámbito; una autorización de solicitud no se supone válida solo porque exista. Una condición de slot pertenece a su campaña. \`AUDIT_FIELD_CHANGE\` referencia el par exacto (evento, registro afectado).
8. **Alertas y sincronización.** Intentos y acuses quedan unidos a una entrega y destinatario; el destino observado no cambia al editar el contacto. Una operación idempotente conserva un único resultado confirmado y rechaza reuso de su referencia para otra acción o contenido. \`ALLOCATION_ATTEMPT\` conserva los intentos de esa operación, no varias asignaciones confirmadas. \`SYNC_OPERATION\` registra operaciones de cualquier cliente autorizado, no obliga a operar sin conexión.
9. **Referencias entre propietarios.** Los pares tipo/referencia de auditoría, reportes, entradas históricas, origen de alertas y sincronización son localizadores de hechos o snapshots, no FK polimórficas hacia cualquier tabla. Se validan con su propietario y conservan contexto mínimo si el acceso se restringe. No se utilizan para saltarse FK en las asignaciones, solicitudes o custodia. Las FK del catálogo son lógicas; si los datos se separan por servicios, su cumplimiento requiere contratos y consistencia explícita, no acceso directo del cliente.
10. **Claves y mínimos propuestos.** Los códigos institucionales y de trazabilidad se consideran únicos en la red del ejercicio; las referencias de muestra/prueba son únicas dentro de su institución emisora. Una cuenta por actor y un registro local activo por par donante–institución son hipótesis registradas, no requisitos regulatorios. Si el levantamiento exige otra cardinalidad, se versiona el identificador o la asociación y se vuelve a comprobar el modelo. En el MVP una unidad puede conservar un origen externo documentado en \`BLOOD_ORIGIN\` sin inventar un donante o implementar el flujo clínico completo.
`;
function finalViews() {
  const schema=stages[4];
  return domains.map(domain=>{
    const local=schema.filter(t=>t.domain===domain);
    let result=`<a id="domain-${domain.slice(0,2)}"></a>\n\n### ${domain}\n\n`;
    for(let offset=0;offset<local.length;offset+=6) {
      const part=local.slice(offset,offset+6);
      result+=`#### Vista ${Math.floor(offset/6)+1}\n\nTablas desarrolladas: ${list(part.map(t=>t.name))}. Las otras cajas muestran solo claves de referencia; su definición completa está en el dominio correspondiente.\n\n`;
      result+=diagram(part,schema)+'\n';
      result+='| Tabla | Claves candidatas | Referencias lógicas |\n| --- | --- | --- |\n';
      result+=part.map(t=>`| ${tick(t.name)} | ${tick(keyText(t))} | ${tick(fkText(t,schema))} |`).join('\n')+'\n\n';
    }
    return result;
  }).join('\n');
}
const fourth = `# Modelo en cuarta forma normal (4FN)

${status}
Ruta: ${sourceLinks}.

## Resultado

Se normalizó el modelo de 18 registros 0FN en **${tables.length} relaciones lógicas**, con **${tables.reduce((n,t)=>n+t.columns.length,0)} atributos declarados**, claves, referencias y vistas por dominio. La [trazabilidad](./Trazabilidad_0FN_4FN.md) cubre los **208 atributos originales**, incluidos sus grupos repetitivos.

El resultado satisface 4FN **respecto de las DF y las independencias declaradas en este ejercicio**. Las reglas clínicas, formularios mínimos, hipótesis de cardinalidad y traducción física requieren validación posterior. El diagrama anterior basado en HU se utilizó como referencia estructural autorizada; no se trasladó como una normalización demostrada.

## 1. Comprobación de 4FN

Para toda DMV no trivial \`X ↠ Y\`, X debe ser superclave. La DMV es trivial cuando \`Y ⊆ X\` o \`X ∪ Y = R\`. Las DF son un caso particular; por ello también se exige BCNF. Una descomposición por DMV usa \`XY\` y \`X(R − Y)\`, y su join recupera la relación cuando la independencia declarada es válida. [Fundamento: Fagin, 1977, apartados 2 y 3](https://www.comp.nus.edu.sg/~lingtw/papers/fagin.pdf).

### DMV identificada en los grupos originales

Considérese la vista plana de directorio \`SITE_DIRECTORY(site_id, contact_id, schedule_sequence)\`. Para esta vista se define que los contactos generales de una sede y sus horarios de apertura son conjuntos independientes: el directorio **no asigna cada contacto a un turno**. La clave candidata es el triple completo; no se declara una DF entre sus componentes.

- \`site_id ↠ contact_id\`.
- \`site_id ↠ schedule_sequence\`.
- \`site_id\` no es superclave, por lo que la vista combinada no está en 4FN.
- Se conservan \`SITE_CONTACT(site_id, contact_id)\` y la proyección \`(site_id, sequence)\` de \`SITE_SCHEDULE\`. Los datos del horario permanecen en \`SITE_SCHEDULE\`, determinados por su identidad o por (site_id, sequence).

Con C1/C2 y horarios 1/2, la vista combinada tiene cuatro filas. Las dos proyecciones conservan dos pertenencias cada una; su join reproduce exactamente las cuatro combinaciones. Si una sede aún no tiene horarios, su fila y sus contactos siguen existiendo por separado; no se reconstruye todo con un inner join.

**La separación ya se realizó al extraer las listas en 1FN.** No se vuelve a combinar la información solo para descomponerla en 4FN. Por eso el conjunto de relaciones de 3FN/BCNF y el de 4FN son iguales: cambia la comprobación realizada, no necesariamente el número de tablas. Si posteriormente se registran teléfonos asignados a turnos concretos, ese nuevo hecho requerirá su asociación y dejará de ser independiente.

### Asociaciones que no admiten separación independiente

| Grupo | Unidad que debe permanecer asociada |
| --- | --- |
| Roles, permisos y ámbitos | Una concesión (asignación de rol, permiso, ámbito, vigencia). READ en A y WRITE en B no autorizan READ en B ni WRITE en A. |
| Candidato y factores | El recurso dentro de una ejecución y cada factor de ese candidato; no todos los factores de una solicitud se aplican indiscriminadamente a todos sus candidatos. |
| Prueba, muestra y observación | La prueba, su revisión y el resultado concreto; varios resultados no prueban independencia entre muestra, locus o método. |
| Destinatarios y canales | Cada entrega pertenece a un destinatario y a un canal; los acuses pertenecen a sus intentos, no a cualquier envío de la alerta. |
| Evento y evidencia | El documento/version corresponde a un evento de custodia y su autorización de captura. No toda fotografía de un traslado prueba todos sus eventos. |
| Versión y aprobación | Fuente, vigencia, ámbito y responsable pertenecen a la versión aplicada; no son listas intercambiables. |

Cada relación final describe un registro, un elemento de una lista, una versión, un evento o una asociación contextualizada. Sus descriptores dependen de las claves declaradas; los conjuntos independientes del propietario están en relaciones distintas. No se postula ninguna DMV residual no trivial con determinante no superclave. Esto no es una prueba sobre dependencias desconocidas del negocio.
${conventions}
## 2. Diagramas completos por dominio

Las vistas se dividen siguiendo la guía de diagramas ER para mantener legibles las claves, atributos y relaciones. En cada vista las tablas desarrolladas contienen **todos** sus atributos. Las cajas externas solo repiten claves para mostrar conexiones entre dominios. Una tabla tiene una única definición canónica aunque aparezca como referencia en varias vistas.

Las líneas sólidas representan FK contenidas en la PK de la relación hija; las discontinuas, otras asociaciones. \`o|\` indica opcionalidad y la terminación de varios indica cero o más filas hijas. Las CK compuestas completas y los extremos exactos de cada FK se indican debajo de las vistas.

| Dominio | Relaciones |
| --- | --- |
${domains.map(d=>`| [${d}](#domain-${d.slice(0,2)}) | ${tables.filter(t=>t.domain===d).length} |`).join('\n')}

${finalViews()}
${integrity}
## 3. Fronteras de almacenamiento e implementación gradual

- La normalización se aplica al **perfil relacional lógico** de los hechos estructurados. No convierte MongoDB, Redis o Storage en tablas normalizadas. Eventos, telemetría o explicaciones extensas pueden tener una representación documental posterior; antes de trasladar un grupo se definirá su propietario y su referencia autoritativa. Los registros de control estructurados y las referencias de este modelo no autorizan duplicar escritores.
- \`DOCUMENT_VERSION\` conserva metadatos de versiones de objetos privados en Google Cloud Storage; nunca el binario, una contraseña, un JWT completo ni una URL firmada reutilizable. La evidencia extendida conserva acceso mínimo y referencias auditables.
- Redis continúa reservado para sesiones, revocación, caché, límites y bloqueos temporales desde el segundo parcial. Sus TTL y estructuras no forman parte de este ejercicio. Los clientes siguen accediendo solo mediante API.
- Primer parcial: seleccionar el subconjunto de cuentas/ámbitos iniciales, instituciones, catálogo de componentes, unidades ficticias y auditoría. No desplegar las ${tables.length} relaciones solo porque aparecen en el alcance semestral. No se crearon SQL, migraciones, bases instaladas ni datos reales.
- La siguiente etapa es revisar el modelo lógico y sus restricciones para definir el modelo físico incremental; la documentación de 1FN–4FN queda desarrollada, no confundida con funcionalidad terminada.
${checks}`;

const trace = `# Trazabilidad del modelo 0FN a 4FN

${status}
Origen inalterado: [Modelo_0FN.md](./Modelo_0FN.md). Resultado: [Modelo_4FN.md](./Modelo_4FN.md).

Cada una de las ${Object.keys(lineage).length} filas siguientes corresponde a un atributo de las 18 estructuras originales. Cuando el origen es una lista u objeto, se indican sus relaciones hijas; sus subcampos están definidos en los diagramas completos. Los identificadores y columnas añadidos para distinguir elementos, versiones y sucesos son decisiones de atomización, no requisitos clínicos nuevos.

Las fronteras de MongoDB, Redis y archivos se mantienen documentadas en la 4FN. Una referencia histórica no se elimina como si fuera una redundancia actual. Las derivaciones —institución desde sede, tipo desde recurso, frecuencia desde ocurrencias y cupo desde citas— se señalan para distinguir información reconstruible de un dato descartado.

| Atributo 0FN | Destino lógico 4FN | Transformación o conservación |
| --- | --- | --- |
${Object.entries(lineage).map(([source,l])=>`| ${tick(source)} | ${list(l.targets)} | ${l.note} |`).join('\n')}

## Especificación y comprobación

[model.mjs](./normalization/model.mjs) declara los esquemas de las cuatro etapas y sus claves/DF; [lineage.mjs](./normalization/lineage.mjs) declara esta correspondencia. [render.mjs](./normalization/render.mjs) calcula los documentos sin escribir archivos. [validate.mjs](./normalization/validate.mjs) comprueba que no falte un atributo inicial, que todos los destinos existan y que cada tabla final provenga de al menos un grupo de la 0FN. Es una comprobación estructural, no una aprobación de todos los subcampos clínicos posibles.
`;

export const documents = {
  'Modelo_1FN.md':first,
  'Modelo_2FN.md':second,
  'Modelo_3FN.md':third,
  'Modelo_4FN.md':fourth,
  'Trazabilidad_0FN_4FN.md':trace,
};
// El comando imprime un parche para aplicar con apply_patch; no escribe al disco.
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const file = process.argv[2];
  if (!file) console.log(JSON.stringify(Object.entries(documents).map(([name,body])=>({name,bytes:Buffer.byteLength(body),lines:body.split('\n').length}))));
  else {
    if (!(file in documents)) throw new Error('Unknown documentation target');
    const filename=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..',file);
    const body=documents[file];
    const old=fs.existsSync(filename)?fs.readFileSync(filename,'utf8'):null;
    const lines=value=>value.replace(/\n$/,'').split('\n');
    const patch=old===body ? null : old===null
      ? `*** Begin Patch\n*** Add File: ${filename}\n${lines(body).map(l=>'+'+l).join('\n')}\n*** End Patch`
      : `*** Begin Patch\n*** Update File: ${filename}\n@@\n${lines(old).map(l=>'-'+l).join('\n')}\n${lines(body).map(l=>'+'+l).join('\n')}\n*** End Patch`;
    console.log(JSON.stringify({file,patch}));
  }
}
