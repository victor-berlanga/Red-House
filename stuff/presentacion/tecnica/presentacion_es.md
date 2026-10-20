# Red House: implementación del segundo parcial

**Versión técnica · Español · 12–15 minutos, incluida demostración.**

Aplicación 0.3.0. Estado al 20 de octubre de 2026. Cada sección propone una diapositiva; las notas amplían la explicación oral.

## 1. Arquitectura que ejecutamos

- Portal Python/Flask con Jinja2 y gráficas Highcharts alimentadas con datos reales.
- Diez microservicios y un servicio de Monitoreo, separados por responsabilidad.
- El portal Docker usa el modo `monolith`: ejecuta módulos de negocio dentro de su proceso.

**Para explicar:** Web y microservicios reutilizan los mismos módulos versionados. El portal actual no necesita llamar por HTTP a las API para cada operación. Existe un modo HTTP configurable, pero no hay cambio automático entre modos ante fallos. Actualizar una imagen de microservicio tampoco actualiza la imagen web.

## 2. Docker y entrada a las API

- Cada servicio tiene Dockerfile e imagen propios, con dos instancias: A y B.
- Nginx ofrece una entrada común y distribuye peticiones entre ambas instancias.
- El entorno mantiene 27 contenedores: 22 instancias API, web, gateway, PostgreSQL, MongoDB y Redis.

**Para explicar:** Cada instancia API ejecuta también su worker; el portal tiene workers propios para procesar tareas pendientes. Los volúmenes conservan datos y los secretos quedan fuera del código. La redundancia demostrada cubre instancias API; las bases, el gateway y el host siguen siendo únicos.

## 3. Qué guarda cada tecnología

| Tecnología | Uso concreto |
| --- | --- |
| PostgreSQL | Una base compartida con 71 tablas de dominio y una tabla técnica para cierres y revocaciones pendientes del portal. |
| MongoDB | Eventos, auditoría, custodia, monitoreo y una vista documental reconstruible del seguimiento de traslados. |
| Redis | Sesiones, revocación, permisos, límites de peticiones, caché y bloqueos de renovación de sesión. |
| Google Cloud Storage | Archivos privados; PostgreSQL conserva sus referencias y metadatos. |

**Para explicar:** Una base SQL compartida no implica permisos administrativos compartidos: cada módulo usa credenciales limitadas. La caché acelera consultas autorizadas; las restricciones y bloqueos SQL protegen la reserva definitiva. MongoDB permite reconstruir el seguimiento sin modificar el historial original.

## 4. Autenticación, sesiones y archivos

- Cada petición protegida valida JWT y consulta en Redis la sesión, revocación y permisos.
- El portal guarda tokens cifrados en Redis; el navegador recibe una cookie con identificador opaco.
- PostgreSQL conserva el cierre y la revocación pendiente; un worker completa lo pendiente al recuperarse Redis.

**Para explicar:** Las autorizaciones consideran rol, institución y recurso. Si Redis falla, se rechazan operaciones protegidas. Si PostgreSQL falla, el portal no puede confirmar el cierre global y responde 503. Los archivos requieren autorización, verificación de contenido y descarga mediante URL firmada temporal.

## 5. Flujo de negocio y consistencia

1. Registrar recurso y solicitud; evaluar candidatos y conservar la revisión humana.
2. Confirmar reserva sin duplicar el recurso ni exceder lo solicitado.
3. Registrar traslado, entrega y aceptación; actualizar inventario, solicitud, custodia, avisos y auditoría.

**Para explicar:** Bloqueos, restricciones e idempotencia evitan duplicar operaciones. Ante una respuesta perdida, se consulta el estado y se conserva la misma clave de operación. El outbox guarda eventos pendientes en SQL; los workers los entregan y los consumidores reconocen duplicados. La proyección MongoDB usa versiones para evitar que un evento antiguo reemplace un estado posterior.

**Límite del algoritmo:** La evaluación y el orden de candidatos apoyan la revisión humana. No hay interpretación automática de HLA ni autorización clínica automática.

## 6. Contratos y monitoreo

- API REST versionadas con respuestas JSON y XML, documentación OpenAPI/Swagger y validación XML con XSD.
- Identificadores de correlación conectan peticiones, operaciones y eventos para investigar errores.
- Las comprobaciones de salud distinguen el proceso de sus dependencias: PostgreSQL, Redis, MongoDB y almacenamiento.

**Para explicar:** Monitoreo muestra disponibilidad, tiempos de respuesta, errores e historial. Android consumirá JSON y escritorio XML; ambas aplicaciones siguen pendientes. Sus contratos ya se probaron y los clientes futuros accederán a los datos mediante las API.

## 7. Evidencia que respalda la entrega

| Fecha | Verificación | Resultado |
| --- | --- | --- |
| 19 de octubre | Regresión integral del cierre | 182 pruebas aprobadas. |
| 19 de octubre | Continuidad Docker | Nueve controles aprobados, incluidos procesos web con las 22 API detenidas. |
| 20 de octubre | Actualización de sesiones | Regresión de 121 pruebas aprobada y ejecución final de nueve pruebas del módulo aprobada. |
| 20 de octubre | Restauración posterior a la actualización | 15 209 filas de 72 tablas SQL conservadas por conteo y hash; permisos comprobados. |

**Para explicar:** Las ejecuciones tienen distintos alcances. Ocho casos de las nueve pruebas finales ya aparecen en la regresión de 121; no se suman como pruebas únicas. También hay evidencia de JSON/XML, archivos GCS privados y recuperación de dependencias. Las pruebas con datos ficticios acreditan esos escenarios, sin certificar capacidad productiva ni disponibilidad entre hosts.

## 8. Demostración y siguiente etapa

**Demostración sugerida, cuatro minutos:**

1. Mostrar una solicitud, su revisión y un traslado preparado; realizar una transición autorizada.
2. Consultar un mismo recurso por API en JSON y XML desde Swagger.
3. Mostrar custodia, auditoría y un archivo verificado asociado al traslado.
4. Abrir la evidencia de continuidad con las API detenidas y explicar por qué la web conserva su operación.

**Para preparar:** Usar datos ficticios y cuentas por rol. Tener consultas y registros listos, con credenciales ocultas. Si se carga un archivo en vivo, hacerlo antes de cerrar el traslado. El [guion ampliado](../Guion_segundo_parcial.md) contiene el procedimiento de ensayo.

**Siguiente etapa:** Android, escritorio y operación productiva. También quedan validación clínica, carga sostenida y redundancia de infraestructura. El despliegue completo ya funciona en una VM Google Compute Engine mediante su IP pública y HTTPS, sin procesos locales, con datos copiados del Docker local y GCS privado. La [verificación en GCP](../../../documentation/evidencias/gcp/RESULTADOS.md) incluye flujo de sangre, JSON/XML, sesiones y archivos.

---

Respaldo: [resultados del 19 de octubre](../../../documentation/evidencias/segundo-parcial/RESULTADOS.md) · [sesiones del 20 de octubre](../../../documentation/evidencias/sesiones-redis/RESULTADOS.md) · [informe técnico](../../../documentation/markdowns/Reporte_tecnico_segundo_parcial.md).

Otras guías: [versión general](../no_tecnica/presentacion_es.md) · [English version](presentation_en.md) · [índice](../README.md).
