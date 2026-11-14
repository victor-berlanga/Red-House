# Comprobación SQL posterior de los fixtures conservados

Una consulta separada sobre los tres fixtures sintéticos del intento `vertical-01` confirmó corrección de unidad y ubicación, dos derivados vinculados a su donación procesada y el estado/versiones de origen y derivados; también confirmó sede/capacidad y sus versiones. En los esquemas emisores encontró exactamente un evento por acción con recurso y actor esperados: `RESOURCE_UPDATED`, `RESOURCE_FRACTIONATED`, y `CATALOGUE_CREATED`/`CATALOGUE_UPDATED` para cada registro institucional. Esta comprobación complementa las aserciones SQL anteriores; no cambia el resultado **0/3** del JUnit Qt original ni demuestra el 403 que ese caso no alcanzó.

El primer intento de este oráculo terminó `UndefinedTable`: se reemplazó la opción `search_path` del DSN al imponer solo lectura. Tras conservar esa opción y añadir `default_transaction_read_only=on`, el oráculo completó los tres escenarios. Arrancó y cerró solo sus procesos PostgreSQL, uno por fixture, sin API, Redis ni MongoDB; verificó directorio de datos, PID propio y transacciones de solo lectura. El arranque normal de PostgreSQL puede actualizar archivos internos: la afirmación de solo lectura se refiere a las consultas SQL.

Resultado saneado SHA-256 `a90cf5a0a6c7f91da0c2596966f31c15c519776954e47fb87571ac9f5b7dd544`. Scripts sin secretos y logs privados se conservaron en `.local/artifacts/desktop/oraculo-inventario-20261114/`; no incluyen las bases. Los scripts requieren los fixtures originales identificados en `vertical-01`, un directorio de salida privado y ejecución local autorizada. Los SHA-256 de los scripts fueron `a258888db18f391db4f936a3448ad7ed2f565a0dcb25d1ada4cfb6e5d2a69475` y `770ce88df8567d6aa5281c53a00b6667a22e902196ff594b5b9994468d1f62e1`.

La guarda de sesión de la interfaz pasó por separado con doble Qt; la corrección del área desplazable de derivados se verificó con otro doble. No se repitió la operación persistente, no se ejerció el 403 pendiente y no se acredita periférico ni proceso clínico real.

Comando empleado, con los scripts preservados en `/private/tmp` y directorio nuevo 0700; requiere autorización para sockets loopback y el mismo fixture sintético conservado:

```sh
RH_DESK_ORACLE_DIR="$(mktemp -d /private/tmp/rh-desktop-oracle.XXXXXX)"
apps/services/.venv/bin/python /private/tmp/redhouse-desktop-originals-readonly.py --output-dir "$RH_DESK_ORACLE_DIR"
```

Si los temporales ya no existen, los scripts se pueden restaurar desde el directorio privado de evidencia a sus nombres originales bajo `/private/tmp`; el fixture debe seguir disponible y detenido. El procedimiento no recrea ni inicializa datos.
