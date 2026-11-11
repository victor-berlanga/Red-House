# Intentos de corrección conservados

Estas ejecuciones pertenecen a esta corrección, pero **no constituyen una aceptación
final del árbol actual**. Durante ellas se encontraron y corrigieron problemas. Los
resultados definitivos deben consultarse por separado; no se suman repeticiones.
El antecedente de auditoría de 58 casos y el incremento previo de 63 identidades no
se incluyen en estas cifras.

Los JUnit saneados conservan identidad, estado y duración de cada caso. Se omiten
trazas que pueden incluir tokens temporales de formularios. `intentos.json` conserva
SHA-256 del original temporal y estado de cada caso. Los originales permanecen en
`/private/tmp/rh-portal-correction-20261106/` mientras exista ese directorio.

| Archivo | Resultado del intento | Hallazgo y corrección/seguimiento |
|---|---|---|
| priority.xml | 1 pasó, 2 fallaron | Aserción de fixture y consulta de sedes privadas desde donante; se añadió contrato mínimo de sedes de agenda. |
| priority2.xml | 3 pasaron | Repetición específica corregida. |
| regression.xml | 0 ejecutados | Nombre de archivo de prueba inexistente; no cuenta como prueba. |
| regression2.xml | 33 pasaron, 2 fallaron, 1 omitido | Metadatos nuevos no coincidían con contratos JSON/XML exportados; contratos regenerados. |
| features.xml | 3 pasaron, 1 falló | Indicador de traslados consultaba fecha inexistente; cohorte definida por salida programada. |
| features2.xml | 7 pasaron, 2 fallaron | Extracción síncrona grande agotaba timeout del adaptador; pasó a worker paginado y reautorizado. |
| features3.xml | 9 pasaron | Reportes/contratos corregidos, con almacenamiento y motor de prueba identificados como dobles. |
| features4.xml | 6 pasaron | Publicación autónoma, privacidad, gran exportación, escritura perdida y revocación del worker. |
| features5.xml | 6 pasaron | Aislamiento del volumen de exportación y regresión específica. |
| features6.xml | 9 pasaron, 1 falló | Caso de bloqueo sin plazo previo esperaba rechazo indebido. El caso final establece un plazo y prueba que no puede reducirse bajo bloqueo. |
| formats.xml | 1 pasó | PDF/CSV/XLSX, zonas Monterrey/Madrid, desconocidos y protección de fórmulas. Repetido en suite final. |
| browser.xml | 2 fallaron | Selector de atributo del mapa incorrecto y conversión de respuesta del gateway del fixture. |
| browser2.xml | 2 fallaron | Falta de espera tras redimensionar ventana; conservar el evento de resize antes de medir. |
| browser3.xml | 2 fallaron | Redirección de cita y formato de fecha de campaña; corregidos. Se corrigió contraste detectado. |
| browser4.xml | 1 falló | SVG de etiqueta era texto y requería codificación antes de Base64. |
| browser5.xml | 2 fallaron | Worker acumulado agotó espera; comparación de URL de credencial incluía querystring. |
| browser6.xml | 1 pasó, 1 falló | Modular completó sangre, agenda/procesamiento, WSS y destino. HTTP agotó espera del worker al final; se pasó a worker concurrente durante el recorrido. |
| browser7.xml | 1 falló, 1 error de preparación | HTTP completó sangre y negativas de órgano; Chrome falló al abrir constancia. Cuenta temporal con contraseña cambiada permanecía en pool de renovación del fixture; se retiró del pool. Formulario de constancia comprobado después en suite específica. |
| regression3.xml | 19 pasaron, 6 fallaron, 1 interrumpido | Volumen de exportación liberado contaminó candidatos; se aislaron unidades en cuarentena. Se interrumpió este proceso propio y se conservó el resultado. El caso interrumpido no se acredita aunque JUnit original carezca de marca de fallo. |
| regression4.xml | 67 pasaron, 4 fallaron | Dos JWT vencieron durante casos prolongados; arranque MongoDB de migración agotó espera; OpenAPI cambió durante ejecución. Requieren repetición aislada con fuentes congeladas, no reinterpretación como aprobados. |

Los checks internos del navegador son observaciones dentro de un caso pytest por
modo; no se contabilizan como otros tests. Mosaicos en línea, WSS TLS local y SMTP
local son reales. TestBucket y receptor ClamD no equivalen a GCS/ClamAV reales.

## Iteraciones de aceptación ampliada

El prefijo `final-` identifica carpetas de ejecución, **no garantiza aprobación**.
Estos intentos también quedan en `ejecuciones.json` y sus JUnit saneados:

| Carpeta | Resultado | Hallazgo y tratamiento |
|---|---|---|
| `final-http` | Falló tras 1 check | Axe detectó contraste en resumen del panel a 390 px. Se oscureció el texto sobre el fondo del área principal. |
| `final-http2` | Falló tras 7 checks | El comprobador intentaba pulsar el botón oculto de zona horaria, aunque el selector ya guarda automáticamente. Se espera la respuesta antes de seleccionar. |
| `final-http3` | Falló tras 18 checks | Agenda concurrente, procesamiento y SMTP completados; Axe detectó contraste en párrafo del resumen de error. Se hizo heredar el color del aviso. |
| `final-http4` | Falló tras 1 check | Redis no permitió verificar la autorización; respuesta 503 segura. No se atribuye una causa definitiva ni se interpreta como éxito. Se repite aislado, manteniendo timeouts del producto y reduciendo la frecuencia del worker del fixture. |
| `final-http5` | Falló tras 31 checks | Reserva pendiente recuperada; Axe detectó contraste en estados/metadatos del mapa. Se corrigieron colores específicos de esa vista. |
| `final-http6` | Falló tras 38 checks | Mapa con ocho eventos, replay, cursor caducado, reasignación, expiración y revocación comprobados. Al hacer logout, la página redirigió al login y la aserción buscó un nodo eliminado; se admite el cierre por redirección y se exige ausencia de historial. |
| `final-monolith` | Falló tras 40 checks | Con doce API detenidas, operaciones previas, WSS, expiración, revocación y logout pasaron. El comprobador consultaba GET `/users/{id}`, contrato inexistente (405); se consulta la lista autorizada por nombre y se selecciona el ID exacto antes de cambiar el rol. |
| `final-monolith2` | Falló tras 40 checks | El backend rechazó cambiar un coordinador mediante administrador institucional (403 correcto). Se cambia el usuario de ensayo a operador con acceso al traslado: permite probar pérdida de rol mediante la operación autorizada, sin ampliar privilegios administrativos. |

Las capturas iniciales del mapa reflejaban el encuadre previo al cambio de ancho.
La repetición pulsa «Ver Nuevo León» tras redimensionar y espera la animación antes
de capturar. No modifica los puntos ni los datos recibidos del backend.
Los controles del mapa recalculan ahora el tamaño visible antes de encuadrar el
estado o la última posición, evitando dimensiones anteriores al cambio de ancho.

- `final-http7`: aprobado (1 caso, 57 pasos internos); 831,44 s. Fuentes idénticas al inicio/final.
- `final-monolith3`: aprobado (1 caso, 57 pasos internos); 768,77 s. Doce API detenidas; fuentes idénticas al inicio/final.
- `final-agenda`: dos fallos reales de presentación: `APPOINTMENT_REMINDER` se mostraba como evento sin clasificación. Renovación real ya pasó en ambos modos. Se añadieron etiquetas de agenda y se repite; los fallos originales permanecen en el expediente.

- `final-agenda2`: dos fallos del comprobador al esperar un POST de cambio de zona cuando la zona seleccionada ya era la activa. Pasaron renovación, recordatorios, diálogos/axe, rechazo ATTEND de donante, error/foco, asistencia y ámbito ajeno. Se corrigió la espera condicional. La revisión visual detectó además que la ficha mostraba el periodo de campaña sin el horario reservado: se añadieron sede/inicio/fin/estado reales a lista y detalle; no se inventa horario para inscripciones antiguas sin sede.

- `final-agenda3`: dos casos aprobados, 205,61 s; ocho pasos por modo. Sede/horario, asistencia, persistencia, teclado y CSV de auditoría en dos zonas comprobados.

- `final-regression`: 61 aprobados, un fallo y una omisión, 915,66 s. El ensayo 13→actual usaba `schema.sql` regenerado a 17 mientras forzaba `LATEST_VERSION=13`: el rechazo de versión futura era correcto. Se prepara una base histórica 13 real desde el SQL del commit de partida, guardado como fixture comprimido reproducible con SHA-256; no se cambia la guardia del migrador. Se repite únicamente ese caso. El navegador anterior se ejecutará aparte con salida nueva para conservar históricos y comprobar cartografía caída.

- `final-migration`: un caso aprobado en 39,13 s. Esquema 13 histórico real, migración a 17 repetida, filas e historia conservadas. Solo se corrigió la preparación del fixture.

- `final-features2`: 23 casos aprobados en 155,88 s; repetición final con manifiestos y caso adicional de contexto CSV regional. No sumar las 22 identidades repetidas de `final-features`.

- `final-degraded`: un caso aprobado en 103,56 s. Mosaicos bloqueados, marcador/reconexión y traslado privado disponibles; salida nueva conserva histórico. TLS directo con destino WSS sustituido por fixture, separado del gateway real del recorrido principal.
