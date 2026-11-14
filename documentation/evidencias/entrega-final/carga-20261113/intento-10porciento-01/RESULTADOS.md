# Primer intento del 10 %, interrumpido por la guarda de espacio

El primer intento usó el comando y las huellas registrados en [preparación](../preparacion-10porciento/PREPARACION.md). Los 941 hashes del conjunto de fuentes antes y después coincidieron; el proceso terminó con código 1. El [informe original](informe.json) conserva fases y progreso: 2.000 donantes, 10.000 recursos y 48.200 de los 100.000 eventos comprometidos. La lectura sostenida no arrancó.

La guarda de disco ejecutó 602 censos y acumuló 124.014,72 ms. Uno falló con `FileNotFoundError`: PostgreSQL retiró `pg/pg_stat_tmp/global.tmp` entre la enumeración y `lstat`. No se concluye que se agotara el espacio. El diagnóstico completo permanece privado, modo 0600, en el directorio del laboratorio preservado; su SHA-256 es `c7adbd62530a5575c91b23a9143244c6cf5b94b3e8a93b21f041e502120b14bc`. El informe tiene SHA-256 `d622fb76e64a7696156235269e116584f032d3dd79947587a6e43107bf189b8d`.

Al cerrar quedaron exactamente los procesos de PostgreSQL y MongoDB que ya existían antes del ensayo. No se borró el laboratorio fallido. Este intento no acredita el conjunto completo, lectura sostenida ni rendimiento de producción.
