-- Conserva la procedencia y sus advertencias; elimina solo la etiqueta redundante.
UPDATE routes SET source=replace(source,' · DEMO',''), version=version+1
WHERE source LIKE '% · DEMO%';
