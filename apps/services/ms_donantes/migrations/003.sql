ALTER TABLE donors ADD COLUMN restrictions text;
ALTER TABLE donors ADD COLUMN background text;
ALTER TABLE donors ADD COLUMN donation_kind text CHECK(donation_kind IN ('VOLUNTARY','REPLACEMENT'));
ALTER TABLE donors ADD COLUMN consent_reference text;
ALTER TABLE donors ADD COLUMN consent_at text;
