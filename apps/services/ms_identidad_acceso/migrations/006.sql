-- Retira etiquetas de la carga inicial en nombres administrativos mutables.
-- Los registros de auditoría conservan exactamente sus valores originales.
UPDATE institutions SET name=replace(replace(name,' · DEMO',''),' DEMO',''), version=version+1
WHERE name LIKE '% DEMO%';
UPDATE catalogue SET name=replace(name,' DEMO',''), version=version+1
WHERE name LIKE '% DEMO%';
