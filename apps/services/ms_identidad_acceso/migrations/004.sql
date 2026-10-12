-- Generación transaccional de caché; no depende de una invalidación Redis posterior.
CREATE TABLE cache_revision(name text PRIMARY KEY, revision bigint NOT NULL DEFAULT 0);
INSERT INTO cache_revision(name) VALUES ('catalogues');
CREATE FUNCTION bump_read_cache() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 UPDATE cache_revision SET revision=revision+1 WHERE name='catalogues';
 RETURN NULL;
END; $$;
CREATE TRIGGER catalogue_cache AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON catalogue FOR EACH STATEMENT EXECUTE FUNCTION bump_read_cache();
