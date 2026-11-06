# Reproducción y administración

La publicación usa las fuentes locales completas, no el `main` anterior. Mantener configuración y respaldos privados fuera de Git. No ejecutar bootstrap de instalación sobre datos existentes. El [procedimiento de despliegue y rollback](../../../entrega-final/backend/correccion/Despliegue_y_rollback.md) exige escritores detenidos y restauración de respaldo comprobada antes de migrar.

La VM queda encendida y el servicio `redhouse` habilitado. Administración mediante `gcloud compute ssh red-house --project=sistemas-integracion-01 --zone=me-central1-a`, usando OS Login. El portal público es https://34.18.186.116.

Prueba aislada del migrador, desde la raíz:

```sh
REDHOUSE_TEST_MONGOD="$PWD/.local/tools/mongodb-8.0.17/bin/mongod" apps/services/.venv/bin/python -m pytest apps/services/tests/test_correction_upgrade.py -q --junitxml=RUTA_NUEVA.xml
```

Para un nuevo recorrido autorizado, usar un directorio privado con `demo-credentials.json` preexistente, con claves `password`, `accounts` y `tenants`. No copiar secretos a evidencias ni imprimirlos. `prepare_correction_demo.py` conserva factores MFA y un checkpoint; repetirlo reutiliza datos, pero un recorrido consumado no debe ejecutarse otra vez como si la unidad siguiera en cuarentena. La reanudación de esta ejecución usó `released: true` en la entrada privada y un directorio de resultados nuevo. No borrar historia para reiniciar pruebas.

```sh
apps/services/.venv/bin/python deployment/gcp/prepare_correction_demo.py --directory DIRECTORIO_PRIVADO
/usr/local/bin/node scripts/demonstrate_gcp_corrections.cjs < DIRECTORIO_PRIVADO/demo-input.json
apps/services/.venv/bin/python deployment/gcp/verify_correction_contracts.py --input DIRECTORIO_PRIVADO/demo-input.json --shipment UUID_DEL_TRASLADO --output RUTA_NUEVA.json
```

Chrome permanece abierto al terminar y el proceso de demostración espera a que se cierre. No inicia captura, vídeo, HAR ni tracing. Los tokens expiran; regenerar sesiones con el preparador para lecturas posteriores. La preparación y demostración crean exclusivamente registros ficticios identificados y auditables; no forman parte del arranque normal.

Las firmas ClamAV se descargan con FreshClam dentro del contenedor. En el primer arranque terminó la actualización antes de que existiera el socket del motor; se solicitó `RELOAD` por su puerto privado y se verificaron versión y EICAR de nuevo (`clamav-final.json`).
