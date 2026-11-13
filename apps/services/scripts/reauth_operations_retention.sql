-- Ejecutar como propietario de access_inventario.operations o rol autorizado.
-- Idempotente; conserva SELECT, INSERT y UPDATE para recuperación de la saga.
REVOKE DELETE ON access_inventario.operations FROM rh_inventario;
