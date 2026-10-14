-- Normaliza el código de eritrocitos; conserva IDs y el historial inmutable.
-- La condición exacta permite actualizar instalaciones anteriores sin tocar otros códigos.
UPDATE requests SET component='RBC', version=version+1
WHERE component='RBC-DEMO';
