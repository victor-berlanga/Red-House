# Entorno integrado local — 2026-10-08

Portal web: <http://127.0.0.1:5050>. El entorno nuevo conserva una DEMO ficticia de seis instituciones de Nuevo León. Las bases de negocio pertenecen a los servicios y la web las consume por API. La antigua base del monolito y el anterior entorno de 5000 unidades se conservan como antecedentes; este último sigue detenido.

| Unidad | Swagger local |
| --- | --- |
| Identidad y acceso | http://127.0.0.1:57404/docs |
| Donantes | http://127.0.0.1:57405/docs |
| Receptores y solicitudes | http://127.0.0.1:57406/docs |
| Inventario | http://127.0.0.1:57407/docs |
| Compatibilidad | http://127.0.0.1:57408/docs |
| Priorización y geografía | http://127.0.0.1:57409/docs |
| Transporte | http://127.0.0.1:57410/docs |
| Cadena de custodia | http://127.0.0.1:57411/docs |
| Alertas | http://127.0.0.1:57412/docs |
| Auditoría | http://127.0.0.1:57413/docs |
| Monitoreo | http://127.0.0.1:57414/docs |

Son las URLs de este entorno; una instalación nueva elige otros puertos. Su disponibilidad depende de procesos locales activos y no persiste tras apagar el equipo sin iniciar nuevamente.

Preparación (12/10/2026): `bash install.sh`. Arranque habitual: `bash start.sh`, sin revisar ni instalar dependencias. Selección de componentes: `bash components.sh`. El ejecutable MongoDB se instaló de forma persistente en `.local/tools/mongodb-8.0.17`; la configuración privada ya no apunta al binario eliminado de `/private/tmp`. [Instalación, menú y comandos](ARRANQUE_LOCAL.md).

Desde la raíz:

```sh
apps/services/.venv/bin/python apps/services/scripts/integrated.py start --directory /Users/victorberlanga/Programacion/integracion/Red-House/.local/demo
apps/services/.venv/bin/python apps/services/scripts/integrated.py status --directory /Users/victorberlanga/Programacion/integracion/Red-House/.local/demo
apps/services/.venv/bin/python apps/services/scripts/integrated.py stop --directory /Users/victorberlanga/Programacion/integracion/Red-House/.local/demo
```

Se preservaron las ocho cuentas activas anteriores. Las 42 cuentas DEMO `admin1`/`operator1`/`medical1`/`coordinator1`/`transport1`/`auditor1`/`donor1`, hasta sufijo 6, usan la contraseña aleatoria del `state.json` privado en `/Users/victorberlanga/Programacion/integracion/Red-House/.local/demo`. No mostrar ese archivo ni JWT durante la presentación. En Swagger, obtener `access_token` mediante Identidad y pegar únicamente su valor en **BearerJWT → Authorize**. Administrador no tiene privilegios clínicos.

Configuración de la web: archivo privado `web-client.json`; tokens cifrados en `web-sessions.sqlite3`, nunca en archivos versionados. El directorio también contiene el resumen sin secretos `demo-nl.json`. Carga completa: 108 donantes, 72 solicitudes, 252 recursos y 18 traslados. Se restauró el límite de 180 peticiones/minuto después de la carga.

[Guía de operación y reproducción](../../web-monolito01/INTEGRACION.md) · [Resultados](VALIDACION.md).
