# Validación de sesiones Redis — 20 de octubre de 2026

La aplicación utiliza Redis para sesiones técnicas cifradas y concesiones de renovación. PostgreSQL conserva cierres y revocaciones pendientes en `web_runtime.session_revocations`, con credenciales exclusivas. El navegador recibe una cookie opaca. Los archivos del almacén anterior permanecen en respaldos privados; la aplicación ya no los abre ni los monta.

## Criterios de aceptación y resultados

| Comprobación | Resultado observado | Evidencia |
| --- | --- | --- |
| Regresión de web, continuidad, seguridad, instalador y contratos | 121 pruebas aprobadas, sin fallos, errores ni omisiones; 798.33 s | [JUnit](regresion.xml), [salida](regresion.txt) |
| Validación final del módulo, incluido descifrado fallido | 9 pruebas aprobadas; 82.26 s. Ejecución posterior al endurecimiento del manejo de credenciales indescifrables | [JUnit](sesiones-final.xml), [salida](sesiones-final.txt) |
| HTTP real en Docker, backend autónomo y todas las API detenidas | Login 302, renovación 200, logout 302; cookie cerrada redirige a login. Tokens cifrados, TTL 86380 s; sin volumen de sesiones local | [Docker](docker.json) |
| Migración local y Docker repetible | 120 681 filas locales y 15 122 Docker conservadas, conteos iguales en cada una de las 71 tablas del dominio; credenciales estables al repetir bootstrap | [Migración](migracion.json) |
| Respaldo y restauración en motores nuevos | 15209 filas de 72 tablas idénticas por conteo/hash, incluida la cola técnica; rol del portal con acceso técnico y sin acceso al esquema de dominio. Redis restaurado, TTL de prueba 3531 s | [Restauración](backup-restore.json) |

Las nueve pruebas finales verifican cifrado y expiración, lectura desde dos instancias web, ACL Redis y permisos SQL, renovación simultánea, logout durante renovación, caída de Redis y recuperación, caída de PostgreSQL, repetición de la actualización y recuperación de una clave de cifrado. No se suman las dos ejecuciones como pruebas distintas: ocho casos del módulo ya están incluidos en la regresión.

## Comportamiento ante fallos

Las sesiones duran hasta 24 horas; renovar no amplía ese límite. Las concesiones duran 60 segundos y verifican su propietario antes de guardar o liberar. Una renovación concurrente rechazada devuelve 409. La marca PostgreSQL evita reactivar una cookie cerrada desde una copia antigua de Redis.

Si Redis falla durante logout, el cierre queda registrado en PostgreSQL y el worker completa la revocación cuando vuelve Redis. Si PostgreSQL falla, el acceso protegido devuelve 503; logout elimina la cookie, pero responde 503 al no poder confirmar el cierre global. Una credencial indescifrable permanece pendiente, sin marcarse como revocada. Las marcas vencidas se eliminan; las credenciales confirmadas se borran del registro inmediatamente.

## Reproducción y alcance

```sh
apps/services/.venv/bin/python -m pytest apps/services/tests/test_web_sessions.py -q
apps/services/.venv/bin/python deployment/verify_web_sessions.py
apps/services/.venv/bin/python deployment/backup.py --verify --leave-stopped --output documentation/evidencias/sesiones-redis/backup-restore.json
```

La prueba pytest usa almacenes temporales independientes. Los comandos Docker requieren una instalación preparada; la verificación HTTP requiere el portal iniciado. El respaldo conserva datos y secretos fuera del repositorio. Las pruebas de caídas usan conexiones a un puerto cerrado y las pruebas de continuidad detienen listeners de API. La restauración usa motores nuevos. No se presenta como prueba de carga sostenida ni de disponibilidad entre hosts.

Las sesiones anteriores ya estaban vencidas: no había sesiones ni revocaciones vigentes que importar. Los usuarios deben iniciar sesión nuevamente. Las guías de [instalación local](../../markdowns/Instalacion_y_operacion.md) y [Docker](../../../deployment/README.md) describen la actualización.

Los [incidentes](incidentes.json) registran un primer fallo por escritura exclusiva de configuración y un error posterior de descubrimiento de fixtures. Ambos fueron corregidos antes de las ejecuciones aprobadas. Las evidencias del 19 de octubre se conservan con su fecha y alcance originales.
