-- Conserva shared_outbox_pending para consultas por next_attempt.
-- El despacho ordena por created_at,id dentro de cada servicio.
CREATE INDEX shared_outbox_dispatch_order
 ON red_house.service_outbox(service,created_at,id)
 WHERE delivered_at IS NULL;
INSERT INTO red_house.schema_migration(version,description)
 VALUES (21,'Índice parcial para despacho ordenado del outbox por servicio');
