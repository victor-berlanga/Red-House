import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {tables, schemaAt, partialSteps, transitiveSteps} from './model.mjs';
import {lineage} from './lineage.mjs';

const base = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const subset = (a,b) => a.every(x=>b.includes(x));
function closure(left, dependencies) {
  const result = new Set(left);
  let changed = true;
  while (changed) {
    changed = false;
    for (const d of dependencies) if (d.left.every(a=>result.has(a))) {
      for (const a of d.right) if (!result.has(a)) { result.add(a); changed = true; }
    }
  }
  return [...result];
}
function normalForms(t) {
  const attrs = t.columns.map(c=>c.name);
  const prime = new Set(t.keys.flat());
  const nonprime = attrs.filter(c=>!prime.has(c));
  const partial = [];
  for (const key of t.keys) for (let mask=0; mask<(1<<key.length)-1; mask++) {
    const part = key.filter((_,i)=>mask&(1<<i));
    const dependent = closure(part,t.dependencies).filter(c=>nonprime.includes(c));
    if (dependent.length) partial.push({part,dependent});
  }
  const nonkey = t.dependencies.filter(d=>d.right.some(a=>!d.left.includes(a)) && !subset(attrs,closure(d.left,t.dependencies)));
  return {nf2:partial.length===0,nf3:nonkey.every(d=>d.right.every(a=>d.left.includes(a)||prime.has(a))),bcnf:nonkey.length===0};
}
const canonical = rows => [...new Set(rows.map(row=>JSON.stringify(Object.fromEntries(Object.entries(row).sort()))))].sort();
const project = (rows,attrs) => canonical(rows.map(row=>Object.fromEntries(attrs.map(a=>[a,row[a]])))).map(row=>JSON.parse(row));
function join(left,right) {
  return left.flatMap(l=>right.filter(r=>Object.keys(l).filter(k=>k in r).every(k=>l[k]===r[k])).map(r=>({...l,...r})));
}
function obeysFD(rows,left,right) {
  return rows.every(a=>rows.every(b=>!left.every(k=>a[k]===b[k]) || right.every(k=>a[k]===b[k])));
}

assert.equal(new Set(tables.map(t=>t.name)).size,tables.length,'Duplicate table');
for (const stage of [1,2,3,4]) {
  const schema = schemaAt(stage);
  const index = new Map(schema.map(t=>[t.name,t]));
  for (const t of schema) {
    const names = t.columns.map(c=>c.name);
    assert.equal(new Set(names).size,names.length,`Duplicate attribute: ${t.name}`);
    assert(t.keys.length && t.keys.every(k=>k.length));
    assert(t.columns.every(c=>/^[a-z][a-z_]*$/.test(c.name) && !['array','object','json','jsonb'].includes(c.type)));
    for (const key of t.keys) {
      assert(subset(key,names));
      assert(subset(names,closure(key,t.dependencies)),`Not a superkey: ${t.name}(${key})`);
      for (const a of key) assert(!subset(names,closure(key.filter(x=>x!==a),t.dependencies)),`Nonminimal key: ${t.name}(${key})`);
    }
    for (const f of t.foreign) {
      assert(subset(f.columns,names));
      const target = index.get(f.target);
      assert(target,`Missing FK target: ${t.name} -> ${f.target}`);
      const targetColumns = f.targetColumns.length ? f.targetColumns : target.keys[0];
      assert.equal(f.columns.length,targetColumns.length,`FK arity: ${t.name}`);
      assert(target.keys.some(k=>subset(k,targetColumns)&&subset(targetColumns,k)),`Non-key FK: ${t.name}`);
      for (let i=0;i<f.columns.length;i++) assert.equal(t.columns.find(c=>c.name===f.columns[i]).type,target.columns.find(c=>c.name===targetColumns[i]).type,`FK type: ${t.name}.${f.columns[i]}`);
    }
    const nf = normalForms(t);
    if (stage>=2) assert(nf.nf2,`Partial dependency left in ${stage}NF: ${t.name}`);
    if (stage>=3) assert(nf.nf3 && nf.bcnf,`Non-key determinant left: ${t.name}`);
  }
}
for (const s of partialSteps) assert(!normalForms(schemaAt(1).find(t=>t.name===s.table)).nf2,`No genuine partial dependency: ${s.table}`);
for (const s of transitiveSteps) {
  const nf = normalForms(schemaAt(2).find(t=>t.name===s.table));
  assert(nf.nf2 && !nf.nf3,`Not a genuine 2NF -> 3NF case: ${s.table}`);
}
assert.deepEqual(schemaAt(3),schemaAt(4),'Do not invent a 4NF split if MVDs were already resolved');

const source = fs.readFileSync(path.join(base,'Modelo_0FN.md'),'utf8');
const sourceAttributes = [...source.matchAll(/^    ([A-Z_]+) \{\n([\s\S]*?)^    \}/gm)]
  .flatMap(([,table,body])=>[...body.matchAll(/^        \w+ (\w+)/gm)].map(([,attribute])=>`${table}.${attribute}`));
assert.equal(sourceAttributes.length,208);
assert.deepEqual(Object.keys(lineage).sort(),sourceAttributes.sort(),'Missing or invented 0NF source attribute');
const mappedTables = new Set();
for (const [origin,l] of Object.entries(lineage)) for (const target of l.targets) {
  const [table,column] = target.split('.');
  const t = tables.find(t=>t.name===table);
  assert(t,`Missing lineage target: ${origin} -> ${target}`);
  if(column) assert(t.columns.some(c=>c.name===column),`Missing lineage column: ${target}`);
  mappedTables.add(table);
}
assert.deepEqual([...mappedTables].sort(),tables.map(t=>t.name).sort(),'A final table lacks an originating 0NF group');

// Testigo reproducible de cada separación por DF. No son datos clínicos.
for (const step of [...partialSteps,...transitiveSteps]) {
  const d = step.determinant[0];
  const moved = Object.keys(step.mappings);
  const rows = [1,2].flatMap(parent=>[1,2].map(item=>({[d]:`DEMO_${parent}`,item_no:item,...Object.fromEntries(moved.map(c=>[c,`${c}_${parent}`]))})));
  assert(obeysFD(rows,[d],moved));
  assert.deepEqual(canonical(join(project(rows,[d,'item_no']),project(rows,[d,...moved]))),canonical(rows));
  const invalid = structuredClone(rows);
  invalid[1][moved[0]]='DEMO_INCONSISTENT';
  assert(!obeysFD(invalid,[d],moved),'An inconsistent input must be rejected, not silently deduplicated');
}

// DMV de directorio: teléfonos/contactos generales no asignados a un turno.
const directory = ['CONTACT_A','CONTACT_B'].flatMap(contact_id=>[1,2].map(schedule_sequence=>({site_id:'SITE_DEMO',contact_id,schedule_sequence})));
assert.deepEqual(canonical(join(project(directory,['site_id','contact_id']),project(directory,['site_id','schedule_sequence']))),canonical(directory));
// Contraejemplo: separar permiso y ámbito daría facultades que no existían.
const grants = [
  {account_role_id:'ROLE_DEMO',permission_id:'READ',scope_id:'SITE_A'},
  {account_role_id:'ROLE_DEMO',permission_id:'WRITE',scope_id:'SITE_B'},
];
assert.equal(canonical(join(project(grants,['account_role_id','permission_id']),project(grants,['account_role_id','scope_id']))).length,4);
assert.equal(grants.length,2);

// Extracción 0FN -> 1FN: anclas, orden y duplicados de valor no se pierden.
const nested = [{id:'A',contacts:['X','X'],schedules:[]},{id:'B',contacts:[],schedules:['MON']}];
const anchors = nested.map(({id})=>({id}));
const flatten = group => nested.flatMap(row=>row[group].map((value,sequence)=>({id:row.id,sequence,value})));
const contacts = flatten('contacts'), schedules = flatten('schedules');
const rebuilt = anchors.map(({id})=>({id,contacts:contacts.filter(r=>r.id===id).sort((a,b)=>a.sequence-b.sequence).map(r=>r.value),schedules:schedules.filter(r=>r.id===id).sort((a,b)=>a.sequence-b.sequence).map(r=>r.value)}));
assert.deepEqual(rebuilt,nested);

let diagrams = 0;
if (!process.argv.includes('--schema-only')) {
  const {documents} = await import('./render.mjs');
  const installed = '/Applications/Visual Studio Code.app/Contents/Resources/app/extensions/markdown-language-features/markdown-editor-out';
  const modulePath = process.env.NORMALIZATION_MERMAID_MODULE || (fs.existsSync(installed) ? path.join(installed,fs.readdirSync(installed).find(f=>/^mermaid\.core-.*\.js$/.test(f)) || '') : '');
  assert(modulePath && fs.statSync(modulePath).isFile(),'Set NORMALIZATION_MERMAID_MODULE to an existing local Mermaid parser');
  const {default:mermaid} = await import(pathToFileURL(modulePath).href);
  for (const [file,expected] of Object.entries(documents)) {
    const actual = fs.readFileSync(path.join(base,file),'utf8');
    assert.equal(actual,expected,`Markdown differs from its checked specification: ${file}`);
    for (const [,block] of actual.matchAll(/```mermaid\n([\s\S]*?)```/g)) { await mermaid.parse(block); diagrams++; }
  }
}
console.log(JSON.stringify({result:'PASS',tables:tables.length,attributes:tables.reduce((n,t)=>n+t.columns.length,0),sourceAttributes:sourceAttributes.length,partialDecompositions:partialSteps.length,transitiveDecompositions:transitiveSteps.length,stagesChecked:4,losslessDFWitnesses:partialSteps.length+transitiveSteps.length,mvdWitnesses:1,unsafePermissionSplitRejected:true,emptyGroupsAndRepeatedValuesPreserved:true,mermaidDiagrams:diagrams,limit:'DF and DMV are modeling assumptions, not discovered clinical rules or proof for unknown dependencies.'},null,2));
