# Guion presencial y video del segundo parcial

Para una exposición breve, elegir una de las [cuatro guías por nivel e idioma](README.md): general o técnica, en español e inglés. Este documento conserva el procedimiento ampliado para preparar y ensayar la demostración.

Material preparado para repartir por responsabilidades. El equipo asignará nombres y tiempos finales. No acredita participación, grabación ni publicación. La portada y los datos del equipo se agregarán después, por indicación del usuario.

## Antes de presentar

1. Seguir `deployment/README.md` en el equipo de demostración. Mantener la tapa abierta y alimentación conectada. Verificar salud y ejecutar `deployment/verify.py --phase smoke` antes del ensayo.
2. Abrir portal `http://127.0.0.1:6050`, Swagger de Identidad `http://127.0.0.1:6101/docs/` e Inventario `http://127.0.0.1:6104/docs/`.
3. Leer las cuentas ficticias desde `.local/compose/state.json` en privado. Nunca proyectar ese archivo, ADC, tokens, contraseñas o firmas completas. Mantener una terminal separada para credenciales.
4. Abrir el expediente `documentation/evidencias/segundo-parcial/http/index.html`, la matriz de cumplimiento y los resultados. Usar datos ficticios nuevos con folios de demostración.
5. Comprobar el acceso GCS mediante `/health/storage` de Transporte. Si la dependencia falla, mostrar el estado real y el registro de pruebas conservado; no presentar una carga simulada como real.

## Reparto por responsabilidades

| Bloque | Tiempo orientativo | Responsable por asignar | Resultado visible |
| --- | --- | --- | --- |
| Problema, actores y alcance | 2 minutos | Análisis | Red regional; distinción sangre/órganos y revisión humana |
| Arquitectura y continuidad | 3 minutos | Backend e infraestructura | Web autónoma, dos instancias por API, límites de infraestructura |
| Seguridad y contratos | 3 minutos | Identidad e integración | Login, JSON/XML, error de autorización y sesión Redis |
| Flujo de negocio | 7 minutos | Operación y servicios de dominio | Registro, revisión, reserva, traslado, recepción y custodia |
| Datos, documentos y archivos | 4 minutos | Persistencia | Filas SQL, proyección MongoDB, índice y archivo privado |
| Contenedores, pruebas y límites | 4 minutos | Pruebas y despliegue | Caída de una instancia, continuidad y evidencia fechada |

Los tiempos son una propuesta de ensayo; cada integrante debe explicar una responsabilidad y responder sobre su integración. El equipo completará el reparto nominal con su participación real.

## Demostración del flujo

1. Operador del origen registra una unidad ficticia RBC con vencimiento capturado. Médico del origen la libera con motivo.
2. Médico del destino registra receptor y solicitud. Obtiene evaluación, explica exclusiones, registra dictamen favorable y consulta orden operativo.
3. Reserva con confirmación. Mostrar identificador de operación. Repetir con la misma clave desde el expediente de prueba y explicar por qué no duplica la reserva.
4. Coordinación planea traslado y asigna responsable. Origen prepara; transportista registra recolección, tránsito y entrega; destino acepta.
5. Mostrar recurso recibido y solicitud cerrada. Abrir custodia con seis pasos, aviso interno y evento auditado con correlación.
6. Mostrar el flujo separado de órgano ya preparado; explicar que HLA y decisiones de trasplante no se automatizan.
7. Mostrar donación/procesamiento y el origen de la unidad como tercer proceso integrado.

## Contratos, bases y nube

- En Swagger ejecutar una consulta real autenticada en JSON y después XML. Mostrar método, URL, headers redactados, estado y cuerpo. Abrir el XSD y el resultado de su validación.
- Ejecutar una petición sin JWT: debe rechazarse. Mostrar evidencia de rol ajeno, token expirado y logout/revocación. Explicar por qué una firma JWT válida no sustituye Redis.
- Consultar datos con una credencial limitada y mostrar la vista propietaria; la base física es compartida. No usar herramientas administrativas desde las aplicaciones cliente.
- Mostrar `shipment_tracking` de MongoDB con el identificador PostgreSQL, versión y último evento. Explicar duplicados y desorden. Abrir la prueba de reconstrucción y plan de índice.
- Cargar un PNG ficticio pequeño desde Archivos de un traslado. Mostrar estado verificado y descarga privada. Explicar que URL expirada produce `ExpiredToken`; el objeto no es público.

## Continuidad durante la exposición

Usar solo el proyecto Docker de demostración. La automatización completa se encuentra en `deployment/verify.py`; conserva resultado y restaura las instancias en `finally`.

1. Detener `identidad-acceso-a` e `inventario-a`. Iniciar una sesión nueva, consultar inventario y realizar un alta ficticia por gateway. Mostrar que responde B.
2. Restaurar A y verificar salud. Explicar que el ensayo automatizado también detiene A de los once propietarios y ejecuta un flujo integrado.
3. Mostrar la prueba de web con las 22 instancias API detenidas. Si se reproduce en vivo, ejecutar `--phase web`; el portal utiliza backend y workers propios. Restaurar al concluir.
4. Explicar los límites: todas las API de un propietario impiden a los clientes API usar esa autoridad; Redis y PostgreSQL caídos impiden operaciones protegidas/transaccionales. No se omite seguridad para obtener continuidad.

## Guion del video

Seguir los mismos bloques, intercalando captura del sistema y explicación breve. Mostrar fecha y versión al inicio; narrar objetivo, entrada, resultado y persistencia en cada operación. Incluir Swagger ejecutado, XML/XSD, Redis, MongoDB, Docker y un flujo completo. Las capturas del expediente complementan la ejecución; no deben sustituirla por completo.

Antes de publicar: revisar que la grabación no exponga secretos, nombres reales de pacientes ni pantallas privadas. El equipo grabará y publicará el video en YouTube como público u oculto, comprobará acceso desde una sesión sin autenticar y agregará el enlace real a la entrega. No existe publicación realizada por este guion.

## Preguntas para el ensayo

- ¿Por qué el portal continúa si se detienen las API? Sus módulos y workers ejecutan las mismas reglas en el backend propio.
- ¿Qué evita reservar dos veces? Retención de cupo, bloqueo de recurso, restricciones únicas e idempotencia; la caché no decide.
- ¿Qué ocurre si se pierde la respuesta de un POST? Se consulta la operación y se conserva la clave; no se cambia de backend a ciegas.
- ¿Por qué MongoDB si ya hay PostgreSQL? Documentos/eventos y una proyección reconstruible; SQL conserva la autoridad transaccional.
- ¿Por qué no editar auditoría para demostrar UPDATE? El historial es inmutable; se actualiza una proyección de negocio separada.
- ¿Qué falta para producción? Validación clínica/normativa, infraestructura tolerante a fallo de host, TLS público y políticas operativas, entre otros pendientes registrados.
