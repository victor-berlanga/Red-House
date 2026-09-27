-- Urgencia operativa únicamente en la solicitud; datos anteriores conservados.
ALTER TABLE recipient RENAME COLUMN urgency TO legacy_urgency;
ALTER TABLE recipient ALTER COLUMN legacy_urgency DROP NOT NULL;
ALTER TABLE recipient ALTER COLUMN legacy_urgency DROP DEFAULT;
COMMENT ON COLUMN recipient.legacy_urgency IS 'Dato histórico previo al 23-09-2026; urgencia operativa en blood_request.';
