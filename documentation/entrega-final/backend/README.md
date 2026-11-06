# Backend de entrega final

Paquetes locales **0.4.1**, API **v1**, esquema compartido **13**. Implementación del prompt 01 y parte backend del complemento 09. Fecha de revisión: 29 de octubre de 2026. El alcance incluye código, persistencia, contratos, adaptadores y pruebas locales; no constituye aprobación clínica ni una nueva publicación en GCP.

## Expediente y aceptación

La versión correctiva sigue pendiente de comprobación productiva e independiente. [Matriz de cierre F/BE/TRACK](correccion/Matriz_cierre.md); el expediente anterior conserva su evidencia histórica.

- [Correspondencia BE-01 a BE-24](Matriz_BE.md): propietarios, brechas, agrupación y pruebas.
- [Estados y consistencia](Estados.md): actores, condiciones, eventos, compensación y límites clínicos.
- [Rastreo WSS y puente GPS](Rastreo.md): contratos, seguridad, recuperación, simulador y matriz TRACK.
- [Resultados correctivos y reproducción](../../evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z/RESULTADOS.md): consolidación final sin sumar casos repetidos. [Evidencia anterior](../../evidencias/entrega-final/backend/RESULTADOS.md) conservada como historial.
- [Contratos](../../../apps/services/README.md): OpenAPI por paquete `ms_*/contracts/openapi.json`; cada entrada tiene ejemplo JSON, ejemplo XML y XSD. Respuestas: `*.response.json` más [XSD de sobre](../../../apps/services/redhouse/response.xsd) y validación DTO por operación mediante `redhouse.xml_response.validate_response`.

Las rutas de código de este expediente se resuelven desde la raíz del repositorio cuando aparecen entre comillas invertidas. Los enlaces relativos llevan al archivo real.

## Catálogo final y decisión de agrupación

| Servicio independiente | Puerto interno | Responsabilidades |
| --- | ---: | --- |
| Identidad y acceso | 5101 | BE-01, BE-02 |
| Donantes | 5102 | BE-03, BE-13 (colecta/procesamiento), BE-22 |
| Receptores | 5103 | BE-04, BE-16 (solicitud, retención, autorización externa) |
| Inventario | 5104 | BE-05, BE-13 (derivados), BE-15, BE-16 (reserva), BE-17, BE-18, BE-21, BE-24 (conciliación) |
| Compatibilidad | 5105 | BE-06, BE-14 |
| Priorización y geografía | 5106 | BE-07 |
| Transporte | 5107 | BE-08, BE-23, tiempos BE-21 |
| Custodia | 5108 | BE-09 |
| Alertas | 5109 | BE-10 |
| Auditoría | 5110 | BE-11 |
| Monitoreo | 5111 | BE-12 |
| Documentos y reportes | 5112 | BE-19, BE-20 |

Son **24 responsabilidades recomendadas, 12 servicios independientes y módulos dentro de esos propietarios**. Cada servicio conserva su paquete, Dockerfile, worker y configuración individual. No se crean réplicas para contar servicios. La evidencia histórica de GCP registra dos réplicas por servicio; este incremento no las actualiza ni las vuelve a verificar. La prueba local de WSS arranca dos procesos gevent independientes, mata uno y después ambos.

Identidad conserva instituciones porque el ámbito de permisos y su revocación comparten ciclo de vida. Donantes conserva agenda porque cupos y consentimiento necesitan la misma autoridad. Inventario conserva frío, caducidad, linaje y destino porque todos condicionan el bloqueo transaccional de la unidad. Laboratorio se agrupa con Compatibilidad: conserva resultados y perfiles, pero únicamente Inventario cambia disponibilidad. Receptores sigue siendo autoridad de cobertura; Inventario coordina una reserva mediante el protocolo existente de retención/confirmación/compensación. No se crea otra reserva.

Documentos es ahora propietario único de archivos, metadatos, análisis y reportes. La migración 013 traslada vistas, ACL y claves de idempotencia sin copiar tablas ni objetos. Transporte conserva adaptadores v1 y la autoridad logística; la validación de evidencia usa una consulta interna firmada. Cada propietario conserva su outbox anterior hasta drenarlo. Custodia, Auditoría, Alertas y Monitoreo mantienen procesos independientes.

La decisión se apoya en permisos, ciclo de vida e I/O externo, sin afirmar un cuello de botella medido. [Análisis completo de las seis agrupaciones, grafo y fronteras transaccionales](correccion/Arquitectura_y_decisiones.md). [Plan de despliegue y rollback](correccion/Despliegue_y_rollback.md). Web ejecuta los doce módulos versionados en modo autónomo; Android/escritorio mantienen JSON/XML sin conexión a almacenes.

## Persistencia y migración

Se conserva PostgreSQL compartido y las cuentas por servicio con vistas `access_*`. Migraciones 008–011 añaden 33 tablas; 012 protege historia de laboratorio y 013 extrae Documentos sin nuevas tablas de dominio: **107 tablas de dominio y una técnica del portal**. No se recrean UUID, instituciones, usuarios ni datos anteriores. La columna nullable `stored_file.shipment_id` permite documentos no logísticos; los archivos logísticos conservan sus relaciones. Se amplía el catálogo institucional sin crear otra tabla de instituciones. La vista `shared_schema_version` permite comprobar versión 13 desde credenciales mínimas.

`apps/services/scripts/upgrade.py --directory RUTA_PRIVADA` respalda antes de migrar. Verificar su `--help` para el entorno correspondiente. La actualización SQL se ejecuta transaccionalmente, es repetible y requiere el propietario de esquema, nunca credenciales cliente. La ampliación Redis `upgrade_final_acl.py` conserva contraseñas, sesiones y reglas previas; después ejecuta `ACL SAVE`. Si Redis falla después del commit SQL, repetir la actualización completa aplica la ampliación sin duplicar tablas ni registros. No usar `provision.py` para actualizar una instalación con datos.

Antes de actualizar un entorno existente: comprobar el respaldo y la política de acceso, detener escrituras durante el cambio de esquema y reiniciar procesos con el mismo código. No ejecutar un downgrade destructivo. Recuperar desde respaldo en una base nueva y cambiar conexiones tras verificar integridad. Los ensayos de instalación/restauración usan bases temporales, no la instalación compartida del usuario. La copia de la versión 7 procede del esquema versionado `8909baf` y contiene registros ficticios de conservación.

| Almacén | Autoridad y recuperación |
| --- | --- |
| PostgreSQL | Transacciones, resultados, consentimientos, asignaciones, historial GPS, idempotencia y outbox. Eventos inmutables y privilegios mínimos. |
| MongoDB | Proyecciones de auditoría/custodia/transporte/monitoreo. GPS se reintenta desde outbox SQL. No es la única copia de puntos confirmados. |
| Redis | Sesión, permisos versionados, revocación, MFA/reauth, rate limit, caché y última posición TTL 300 s. Fallo de autorización produce rechazo seguro. |
| GCS | Binarios privados; SQL conserva propietario, referencia, hash, generación, metadatos y análisis. URL firmada no concede acceso a otro sujeto. |
| SQLite local del puente | Hasta 1000 puntos pendientes cifrados con Fernet. Se retiran solo tras ACK de persistencia SQL. No sustituye al historial servidor. |

Retención: consentimientos, resultados, destinos y eventos conservan correcciones enlazadas. Documentos nacen privados con bloqueo de conservación. No se inventa una duración sanitaria ni se habilita borrado automático de historia. La institución debe aprobar duración/finalidad y procedimiento de eliminación antes de producción; el backlog cifra sus datos y el cliente debe purgarlos al perder autorización conforme a esa política. El caché temporal sí caduca.

## Configuración y seguridad

Secreto/configuración real fuera del repositorio. Los ficheros JSON privados generados por la instalación aceptan las siguientes claves; las de correo/MFA también pueden proceder de variables de entorno.

| Configuración | Uso |
| --- | --- |
| `MFA_REQUIRED_ROLES` | Por defecto `ADMIN`, `MEDICAL`, `COORDINATOR` fuera de pruebas. TOTP RFC 6238, ventana ±1, contador antirrepetición y límite de intentos. |
| `REAUTH_REQUIRED_OPERATIONS` | Por defecto liberación, autorización de resultado, reserva y destino. Prueba de 120 s ligada a usuario, sesión, institución, versión de permisos, operación y recurso; encabezado `X-Reauthentication-Proof`. |
| `REQUIRE_LAB_PROFILE` | `true` operativo. Impide liberar/reservar/usar una unidad sin perfil y resultados autorizados. `false` conserva únicamente el recorrido académico anterior; no habilita operación clínica. |
| `REQUIRE_ORGAN_AUTHORIZATION` | `true` operativo. Exige constancia externa vigente antes de retener una solicitud de órgano. Registrar constancia no autentica a la autoridad externa. |
| `SMTP_HOST/PORT/USERNAME/PASSWORD/FROM` | SMTP con STARTTLS y autenticación. `SMTP_TEST_RECEIVER` se limita a localhost en pruebas. |
| `PUSH_ADAPTER_URL/TOKEN` | Adaptador HTTPS autenticado que acepta destinatario/código/referencia mínima; deduplicación mediante clave. `PUSH_TEST_RECEIVER` solo localhost de pruebas. |
| `STORAGE_ENABLED`, `GCS_BUCKET` | Activar almacenamiento en el JSON privado de Transporte; ADC y firma V4 con la cuenta autorizada, sin claves en clientes. |
| `CLAMD_HOST/PORT` | ClamD INSTREAM en red privada; timeout y límite de tamaño. Inaccesible/error bloquea descarga. Configurar servicio y actualización de firmas antes de producción. |
| `MONITOR_ALERT_TARGETS` | Lista de instituciones/regiones destinatarias de avisos de degradación y recuperación. Monitoreo no participa en transacciones de negocio. |

El enrolamiento MFA comprueba contraseña y secreto TOTP antes de activar el factor, cifra el secreto y revoca sesiones anteriores. Los nuevos clientes deberán presentar `otp` en login y usar la ruta de reautenticación. La recuperación responde igual exista o no la cuenta, limita solicitudes, exige contacto previamente verificado y token de un uso de 15 minutos. Cambiar contraseña revoca sesiones y conserva MFA. La clave privada del servicio protege factores y correo pendiente: su rotación requiere recifrar esos registros antes de retirar la clave anterior. El servidor no envía tokens de recuperación en respuestas o logs; salen por correo.

La entrega de correo se registra como `ACCEPTED_BY_SMTP`; la de alertas como `ACCEPTED_BY_ADAPTER`. Ninguno significa que una persona leyó el mensaje. Las pruebas usan receptores TCP/HTTP reales locales. El doble de ClamD valida el protocolo y los fallos, no certifica detección de malware por firmas. GCS nuevo se verifica con doble de SDK; la suite real exige bucket/ADC de pruebas configurados.

Contratos REST: `Accept`/`Content-Type` explícitos JSON o XML; fechas con zona, UUID, DTO estricto, errores 400/401/403/404/406/409/412/415/422/429/503. Los comandos nuevos de versión usan 412; las rutas v1 previas conservan sus 409. 201 confirma compromiso local; 202 de traslado/exportación exige consultar el recurso hasta su estado final. `Idempotency-Key` conserva la semántica del protocolo transaccional existente. Los comandos de sincronización usan además UUID persistente del comando. Credenciales, enrolamiento y reautenticación emiten secretos de una sola presentación: ante respuesta perdida se solicita nueva emisión; nunca se recuperan desde una lista.

Documentos: preparar, transferir por URL GCS V4 privada, verificar hash/tamaño/tipo/estructura y análisis ClamD de la generación exacta, descargar. Sin análisis limpio no hay descarga, incluso para objetos históricos marcados VERIFIED. Reportes: crear job, consultar estado, reintentar `RETRYABLE`, obtener archivo privado. Exportaciones limitadas a 1000 filas minimizadas y ventana máxima de un año; CSV protege fórmulas, XLSX usa texto sin macros, PDF no incorpora acciones. Formatos operativos sujetos a revisión; no se declara certificación regulatoria.

## Reproducción local

Desde la raíz, con dependencias instaladas en `apps/services/.venv` y binarios PostgreSQL, Redis y MongoDB disponibles:

```sh
apps/services/.venv/bin/python apps/services/scripts/document.py --contracts-only
apps/services/.venv/bin/python scripts/build_shared_schema.py
apps/services/.venv/bin/python -m pytest apps/services/tests/test_final_*.py apps/services/tests/test_audit_migration.py apps/services/tests/test_continuity.py -q --tb=short
apps/services/.venv/bin/python -m pytest apps/services/tests -q --tb=short
apps/services/.venv/bin/python -m ruff check --select E9,F63,F7,F82 apps/services apps/web/src/integration
apps/services/.venv/bin/python -m ruff format --check apps/services apps/web/src/integration
```

Los fixtures crean dependencias en `/tmp/red-house-ms-tests-*`, puertos aleatorios y datos sintéticos. Requieren permiso para sockets localhost. No apuntar estas pruebas al entorno compartido, al bucket productivo ni a GCP. `REDHOUSE_TEST_MONGOD` admite una ruta explícita al ejecutable local. La evidencia distingue pruebas unitarias, HTTP/WSS reales, dobles externos y omisiones.

## Límites de esta etapa

BE-06 conserva RBC-1.0/ORGAN-1.0 y captura/perfiles de laboratorio; no entrega un motor clínico HLA aprobado. BE-07 conserva LOGISTICS-1.0 y COVERAGE-HK-1.0; el prompt 02 integra reglas adicionales. Los perfiles nuevos son exclusivamente sintéticos: activar reglas reales requiere fuente y aprobación competente. La analítica muestra calidad de datos, demanda incompleta si supera 1000 solicitudes, brecha bruta y pronóstico empírico; no ejecuta abastecimiento.

Pendientes externos: dispositivo físico y protocolo concreto, políticas institucionales de retención, validación clínica/regulatoria, SMTP/push reales autorizados, ClamAV con firmas y prueba GCS en entorno designado. Pendientes de etapas consumidoras: formularios/MFA y mapas web, Android Kotlin, escritorio PySide6 y cartografía vigente; la entrega backend publica contratos para ellos. No se afirma GPS físico, mapa integrado, publicación GCP nueva ni capacidad de producción a partir de una prueba local.
