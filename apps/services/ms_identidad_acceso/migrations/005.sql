-- Normaliza únicamente el componente de capacidades ya registradas.
UPDATE catalogue SET details=jsonb_set(details,'{component}','"RBC"'::jsonb), version=version+1
WHERE kind='capacities' AND details->>'component'='RBC-DEMO';
