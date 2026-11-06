# Demostración de Red House en GCP — 4 de noviembre de 2026

## Entregable y criterio de aceptación

Video editado de navegación por el portal publicado, con movimientos reales del cursor, teclado y desplazamiento de macOS. Se abren funciones mediante menús, enlaces, búsquedas y formularios; no se escriben URLs durante las tomas. Los títulos preceden a las funciones y las notas distinguen reglas técnicas, datos académicos y dependencias clínicas.

[Video MP4](../../../../.local/video-gcp-20261104/Red-House-GCP-demostracion.mp4) · [Índice por tiempo](INDICE.md) · [Metadatos y SHA-256](video.json) · [Guion](GUION.md) · [Comprobaciones e incidencias](comprobaciones.json).

El MP4 y las tomas privadas permanecen en `.local/video-gcp-20261104/`; no se incorporan al código ni se publican en Internet. Esta entrega no despliega una nueva versión. El entorno utilizado es `https://34.18.186.116`, en modo académico, con datos ficticios.

Archivo final: **24 min 41 s**, **62 capítulos**, **24.188.573 bytes**. La decodificación completa con FFmpeg terminó sin errores; el SHA-256 coincide con el manifiesto. Ningún intervalo conservado se solapa con las ventanas privadas marcadas y ningún texto inferior excede sus tres líneas. Se revisaron visualmente muestras de títulos y pantallas, no cada fotograma. [Verificación del archivo](verificacion-video.json) · [Muestra visual final](revision-visual.jpg).

Al finalizar, HTTPS confirmó portal vivo y Compatibilidad 0.4.4. [Respuestas de salud](salud.json). Estas dos consultas no acreditan el estado exhaustivo de todos los servicios o dependencias.

## Captura y edición

- Google Chrome instalado en el Mac, a pantalla completa, con un perfil temporal para la demostración. Traducción automática desactivada y configuración de idioma español; el aviso que tapaba el acceso dejó de impedir la navegación.
- Captura física AVFoundation con cursor. Clics, teclas y desplazamientos enviados mediante `CGEventPost`. Playwright se utiliza para localizar/verificar elementos y comprobar respuestas, no para generar el video ni sustituir los movimientos por clics en el DOM.
- La apertura inicial del portal ocurre antes de grabar. Durante las tomas se usan los controles de la web, incluida la apertura del expediente completo desde los diálogos.
- Captura a 15 fps, exportación H.264 a 30 fps sin acelerar acciones. Montaje 1440×944, sin audio, con títulos, notas y capítulos MP4. Se conserva la aplicación completa y la barra de dirección. Se retira únicamente la franja informativa de Chrome de 56 píxeles y se añade espacio inferior para texto.
- Se eliminan intervalos de contraseñas y MFA con márgenes de cinco segundos y compensación del inicio de captura. No se distribuyen entradas privadas, cookies, perfiles de Chrome ni credenciales. Se omiten recorridos repetidos y fragmentos finales interrumpidos.
- Es un montaje de varias tomas. No se presenta como una ejecución continua ni como una suite completa sin fallos. `fuentes-edicion.json` e `indice.json` identifican las selecciones; `comprobaciones.json` conserva los resultados de las tomas, incluidas las fallidas.

## Funciones mostradas y comprobadas

Se recorren acceso institucional, paneles, fuentes públicas, laboratorio HLA, perfiles, registro de muestra y completitud; las seis ramas de análisis académico —ALG-01, ALG-02, ALG-02-GEO, ALG-03, ALG-04 y ALG-05—; solicitud, evaluación y revisión humana; corrección de laboratorio y rechazo visible de una reserva obsoleta; nueva evaluación, reserva y planeación; preparación, recolección, tránsito, entrega y aceptación; destino académico y corrección documental; reporte privado, auditoría y módulos de personal médico, coordinación, administración y donante.

Se observaron rechazos de liberación sin reautenticación, reserva obsoleta y custodia incompleta. La consulta de completitud del complemento respondió `clinical_approval=false`. La aceptación del traslado y el cierre de solicitud se comprobaron en los propietarios de datos. El reporte de custodia terminó y su descarga desde GCS contenía `SHIPMENT_ACCEPTED`.

El tramo `natural12` terminó con **50 comprobaciones**, descarga privada realizada, cero errores de JavaScript y cero respuestas HTTP de error registradas en ese tramo. Este número incluye consultas de módulos y cambios de sesión: **no son 50 pruebas clínicas ni 50 casos únicos de regresión**. Los otros tramos conservan resultados separados; no se suman reintentos para anunciar una cobertura mayor.

Registros ficticios de referencia:

| Registro | Identificador |
|---|---|
| Unidad | `c108ad4e-9c01-44b3-a45b-b49f3e9e26d9` / `RH-GCP-fe2bcaccc3` |
| Solicitud | `3ef633b1-df5f-4255-9373-2cbea5a9660d` |
| Evaluación anterior | `0320e965-8ecf-45ba-ad1a-94ae4aece6be` |
| Evaluación vigente del flujo | `87d35135-2c9f-4b97-b27f-2e477e2d6b55` |
| Resultado corregido | `d1f6b0aa-3b0b-4807-b18d-6159133a3f88` |
| Reserva | `f68b05de-c683-41cb-922e-29d0d750539d` |
| Traslado aceptado | `e68b36e1-fb65-4e0e-b5eb-8e9c6d671401` |
| Reporte privado | `41914bba-f8a2-4194-a8f8-38eb42045a8d` |
| Muestra académica del complemento | `2f56544d-0407-4320-bbc3-beb303d1fa8c` |

## Incidencias y límites

Los intentos previos encontraron esperas del controlador en selectores nativos, retornos de formularios a listados en lugar de detalles, filtros que ocultaban recursos retirados, controles fuera del área visible y comprobaciones auxiliares incorrectas. Se ajustó el guion/controlador de captura; no se modificó la aplicación. Las operaciones ya guardadas se retomaron desde sus registros, conservando el historial. Un intento de destino incompatible fue rechazado; el flujo conservado usa el destino académico de transfusión para eritrocitos.

En `natural13`, al abrir el perfil `7bf03011-eb76-4438-9fe8-73d1be0a257a` desde `/laboratorio/perfiles`, el diálogo mostró «No se pudo cargar el detalle». No se registró una respuesta HTTP de error ni se determinó la causa. **Pendiente verificable:** reproducir esa apertura con el mismo perfil/rol y revisar la petición del diálogo antes de atribuirlo a red o aplicación. Ese fragmento no se presenta como aprobado. El registro de muestra/completitud anterior sí finalizó.

En `natural14`, el detalle HLA se consultó; el controlador posterior no alcanzó el botón de cierre de sesión tras desplazarse. Se conserva únicamente la consulta HLA. El cierre de sesión del recorrido principal sí terminó en `natural12`. La página pública final se graba por separado.

La demostración no certifica todos los CRUD, aislamiento exhaustivo entre instituciones, concurrencia, carga, recuperación, oráculos ni reglas clínicas. Las notas explican límites de mecanismos implementados; no convierten una consulta de pantalla en prueba exhaustiva del algoritmo. No se ejecutó una nueva auditoría independiente.

El registro HLA, su reconocimiento por catálogo, la completitud, la evaluación y el dictamen siguen siendo conceptos separados. Ninguna intervención de una cuenta ficticia constituye aprobación profesional real. Las citas normativas y los casos sintéticos no certifican reglas clínicas.

GPS físico aplazado. No se publican posiciones ni se prueba WSS en esta grabación. La ruta vial y la ETA mostradas son cálculos con fuente versionada: no acreditan tráfico medido, recorrido físico, entrega real ni decisión clínica. Los pasos de custodia usan identificadores ficticios escritos con teclado; no prueban un escáner físico.
