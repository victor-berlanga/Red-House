# Esquema histórico para migración

`schema-v13.sql.gz` contiene el esquema SQL (sin datos de usuarios) de
`data/database/schema.sql` en el commit `cbe3503b39a60b6b0a995f1284b2f5b1c3405cae`.
SHA-256 del SQL descomprimido: `d3c8f8a74181c1ce79317a91f8762001e6cff4acaa5d0c66e87265d7aeca515d`.

El ensayo restaura esta versión 13 real, crea filas ficticias y ejecuta dos veces
la actualización vigente. No simula un downgrade del esquema actual ni cambia
la comprobación que rechaza versiones futuras. La compresión usa mtime=0.
