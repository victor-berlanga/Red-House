# Segunda corrección de calidad visual — 10/11/2026

**Entrega parcial de presentación; aceptación integral pendiente.** Se ejecuta `stuff/prompts/corregir_calidad_visual_web_movil.md`. Se corrigieron los patrones compartidos web y nativos, con comparaciones visuales nuevas. La revisión no cierra etapas funcionales ni acredita todas las combinaciones de ruta, permiso, estado y dispositivo. Esta revisión local no incluyó despliegue. Por autorización posterior «Publicala», la corrección web se publicó como `redhouse/web:uiux-quality-20261110`: [publicación y capturas privadas GCP](../../gcp/uiux-quality-20261110/RESULTADOS.md).

[Resumen final verificable](resumen-final.json). Emulador restaurado a 360×720 dp, fuente 130 % y orientación natural; APK final instalado y abierto sin sesión. Servidores locales de revisión y sesión de automatización Safari cerrados.

## Cambios comprobables

Web: nombre del registro enlazado al detalle, ojo exclusivo para vista rápida, hasta dos acciones directas uniformes y menú con nombres para las demás. Las operaciones conservan su método, CSRF, recurso e idempotencia. Tooltip por foco/puntero, Escape y retorno del foco. Filas sin wrapping accidental de acciones, refresco con icono de recarga, herramientas agrupadas y paginador principal inferior. Cuerpo semántico de contenido sin aplicar padding global a `.card`.

Documentos conserva sus dos consultas GET dentro de una secuencia con ancho máximo de 720 px, espacio interior y acción principal reconocible. Tipo fijo como contexto, sin seleccionar un expediente automáticamente. Las variantes de evaluación, conservación, linaje, auditoría, etiquetas, espacio de trabajo e historial reutilizan los patrones pertinentes. El acceso elimina ayudas permanentes de longitud; conserva etiquetas, MFA, recuperación y errores. Safari real reveló selectores nativos más bajos que su `min-height`; se corrigió la apariencia del select simple manteniendo el elemento HTML y su interacción nativa. Controles de formulario con base de 44 px.

Móvil: navegación inferior por rol, entrada directa al trabajo, Cuenta agrupada y logout secundario. Las etiquetas usan el ancho del destino; con fuente del sistema al 180 % o superior, los cuatro destinos se distribuyen en dos filas sin reducir la letra. Solicitudes, muestras y resultados muestran su identificador disponible o una referencia abreviada, no un título genérico repetido. Las referencias técnicas quedan en información secundaria. Resúmenes por recurso con campos elegidos; no se inventa fecha, sede o nombre cuando la respuesta no los contiene. Citas, reserva y expediente tienen objetivos separados. Transporte agrupa referencias, contactos, evidencia e historial; conserva mapa, estados de ubicación y sus efectos de ciclo de vida. Una captura detectó dos botones de regreso en la tarea: queda el de cabecera, además del regreso del sistema. Las consultas rutinarias no generan párrafos globales permanentes; se mantienen errores y estados inciertos.

## Comparación visual

Los pares web usan **fixtures Jinja sintéticos**, mismos datos y viewport Chrome de **1440×1000 CSS px**, sin reducir zoom entre imágenes. No equivalen a sesiones privadas ni certifican autorizaciones. El contador incluye solo filas completas dentro del viewport.

| Caso | Antes | Después | Resultado observado |
| --- | --- | --- | --- |
| Campañas | [Captura](before-campaigns-1440.png) | [Captura](after-campaigns-1440.png) | 5 → 11 filas completas; primera fila 93,89 → 56,5 px. |
| Avisos | [Captura](before-alerts-1440.png) | [Captura](after-alerts-1440.png) | 3 → 11 filas completas; primera fila 128,73 → 56,5 px. |
| Documentos | [Captura](before-documents-1440.png) | [Captura](after-documents-1440.png) | Dos envíos conservados, controles acolchados y ancho contenido. |
| Acceso | [Captura](before-login-1440.png) | [Captura](after-login-1440.png) | Sin ayuda de longitud inicial; referencias ARIA válidas. |
| Listado operativo | [Captura](before-operations-1440.png) | [Captura](after-operations-1440.png) | Acciones frecuentes y menú con etiquetas explícitas. |
| Cuenta Android | [Captura](donor1-baseline-account-360-130.png) | [Captura](donor1-account-360-130.png) | Identidad breve, ajustes por destino, cuatro pestañas visibles. |
| Citas Android | [Captura](donor1-baseline-work-360-130.png) | [Captura](donor1-work-360-130.png) | Jerarquía de cita y acciones secundarias bajo «Consultar cita». |

El marco de ventana del host cambia entre algunos pares, pero el área Android conserva ancho y escala. Los pares Android son sesiones reales de la **misma cuenta de demostración donor1**, mismos datos existentes, **360×720 dp y fuente 130 %**. El APK anterior se reconstruyó en una copia aislada de las fuentes guardadas al inicio. Después se reinstaló la corrección. No se restauró ni sobrescribió el árbol de trabajo para obtener el antes. Las capturas proceden de la ventana visible del emulador macOS; **FLAG_SECURE permanece intacto**.

Otras familias: [traslado](transport1-task-360-130.png), [contactos](transport1-contacts-360-130.png), [reserva de cita](donor1-booking-form-360-130.png), [Región](coordinator1-subhub-360-130.png), [Laboratorio](medical1-subhub-360-130.png), [formulario compacto](custom-form-320.png), [linaje](custom-lineage-1440.png), [conservación](custom-conservation-1440.png) y [evaluación](custom-evaluation-1440.png).

## Cobertura y límites

| Ejecución | Evidencia | Alcance real |
| --- | --- | --- |
| Chrome: 280 combinaciones de maquetación | [chrome.json](chrome.json) | 7 envolventes de rol × 8 familias × 5 anchos: 1440, 1024, 768, 390, 320. Algunas combinaciones de fixture no están autorizadas en la aplicación: no son pruebas de permisos ni rutas autenticadas. |
| Chrome: 24 variantes adicionales y 4 ensayos de texto | [extra-browser.json](extra-browser.json) | Conservación, linaje, evaluación, formulario, carga, detalle, vacío y error a 1440/768/320. Simulación CSS de texto al 200 % en cuatro familias a 1024; no equivale a zoom de navegador ni a lector de pantalla. |
| Safari real macOS 26.6.1 | [safari.json](safari.json) | Campañas, avisos, documentos, acceso y operaciones en los cinco anchos CSS medidos. Safari conservó el zoom previo 85 % (DPR 1,7 sobre Retina 2×); se ajustó el tamaño exterior para obtener el ancho CSS solicitado. No se usa Safari para medir la ganancia antes/después ni se atribuye esta prueba a iOS. |
| Flask local real | [runtime-web.json](runtime-web.json) | Portada, login y recuperación respondieron 200. Login privado bloqueado: «No se puede verificar el cierre de sesión. Reintenta más tarde». No se cambió infraestructura, seguridad ni backend para sortearlo. |
| Android autenticado | [android-acceptance.json](android-acceptance.json) | Consultas y navegación de cinco perfiles de demostración con sus permisos reales. Las credenciales se aportan al proceso de instrumentación, no al código ni a las evidencias. MFA intacto para médico/coordinador. |
| Android autenticado, texto 200 % | [android-large-auth.json](android-large-auth.json) | Donante a 412 dp: citas, reserva sin enviar, Cuenta, Privacidad, Avisos, regresos y logout. Las cuatro opciones inferiores quedan legibles en dos filas; no acredita los otros cuatro perfiles a esa escala. |
| Android acceso, teclado y escala | [android-scales.json](android-scales.json) | 360 y 412 dp × fuente 100/130/200 %. Cinco recorridos completos aprobados. El de 412 dp/200 % agotó 140 s después de acceso/teclado: rotación pendiente. Las primeras capturas prematuras se repitieron con espera de recreación de Activity. |
| Compilación/regresión | [invariantes.json](invariantes.json) | APK Android, instrumentación y Kotlin iOS arm64; 21 pruebas JVM aprobadas y 2 omitidas por ausencia del laboratorio aislado. No se ejecutó ni enlazó una aplicación iOS en esta revisión. |

El inventario [rutas.csv](rutas.csv) contiene 207 filas extraídas de rutas/roles y sus familias. Donde el permiso depende de funciones o recursos figura **PENDIENTE**, no un rol supuesto. No se declara una matriz de autorización completa. [plantillas.csv](plantillas.csv) contiene las 28 plantillas de integración actuales: 27 originales y la macro nueva. Fuente/compilación y revisión de una familia no acreditan una visita a cada ruta consumidora. [cobertura-movil.csv](cobertura-movil.csv) relaciona recorridos nativos con sus capturas y estados probados.

La tanda final autenticada registra **5/5 recorridos aprobados y 28 capturas**, más una repetición donante a 412 dp/200 % con seis capturas. Esto acredita las aserciones y las consultas descritas, no aprobación visual universal: se conserva el límite de representación observado en transporte.

Pasos observados: desde el trabajo nativo, Cuenta requiere una pulsación; Privacidad requiere otra y vuelve con un regreso del sistema. Citas → Gestionar citas e historial → Buscar horarios requiere dos pulsaciones y se ensayan dos regresos. Región/Laboratorio → consulta secundaria requiere dos pulsaciones. Traslados → tarea → Contactos y ruta → consultar contactos requiere tres. No se envían reservas, transiciones ni lectura de avisos en estos recorridos.

En fixtures web, abrir vista rápida requiere un clic y Escape devuelve el foco; el nombre accede directamente al detalle mediante enlace. «Marcar como leída» conserva su formulario POST; se comprueba estructura y claves, sin ejecutarlo sobre datos reales. Documentos conserva dos envíos GET. No se midieron tiempos ni desplazamientos completos de un proceso privado: siguen pendientes por el bloqueo de sesión. No se atribuye mejora porcentual ni validación por usuarios.

## Criterios C01–C10

«Resuelto en muestra» significa corregido en componentes y evidencia identificada, sin extenderlo a rutas que no se ejecutaron.

| ID | Estado | Evidencia y límite |
| --- | --- | --- |
| C01 | Resuelto en muestra | Macro `row_actions`, campañas/avisos/operaciones, foco y Escape en Chrome. |
| C02 | Resuelto en muestra | Comparaciones de filas a igual viewport y escala; altura flexible ante texto largo. |
| C03 | Resuelto en muestra | Barra y paginación compartidas; capturas antes/después. |
| C04 | Resuelto en muestra | Documentos con cuerpo de formulario; revisión Chrome/Safari. |
| C05 | Resuelto en muestra; variantes pendientes | Plantillas particulares migradas; conservación/linaje/evaluación/formulario/carga con fixtures propios. No todas las rutas reales visitadas. |
| C06 | Resuelto | Acceso real público y fixture; ARIA sin referencias ausentes, MFA/recuperación conservados. |
| C07 | Implementado; revisión visual parcial | Navegación inferior autenticada por cinco perfiles; regreso contextual/sistema. Persiste una limitación de representación/captura en la tarea de traslado, descrita abajo. |
| C08 | Resuelto en recorridos probados | Cuenta, listados y mensajes; referencias disponibles en segundo nivel. |
| C09 | Resuelto en muestra; regresión operativa pendiente | Agenda/reserva y traslado/contactos separados. No se ejecutan custodia, GPS, cámara ni operaciones inciertas en esta revisión. |
| C10 | Pendiente | Hay evidencia visual nueva y límites explícitos; falta cobertura privada web exhaustiva, accesibilidad asistida e iOS físico. |

## Criterios V01–V14

| ID | Estado | Comprobación |
| --- | --- | --- |
| V01 | Resuelto en muestra | Acciones uniformes; sin texto «Abrir expediente» en columna; detalle enlazado. |
| V02 | Resuelto en muestra | 5/3 → 11/11 filas completas sin reducir tipografía ni zoom. |
| V03 | Resuelto en muestra | Recarga correcta, autoactualización junto a herramientas, paginador inferior. |
| V04 | Resuelto en muestra | Cuerpos semánticos; select Safari corregido; no padding global de `.card`. |
| V05 | Resuelto | Acceso limpio, nombres/errores ARIA, MFA y recuperación conservados. |
| V06 | Implementado; revisión visual parcial | Destinos por rol y carga inicial; ausencia de «Secciones». Cinco recorridos pasan, pero no se aprueba toda captura de la tarea de traslado. |
| V07 | Resuelto en cinco recorridos | Cuenta agrupada, ajustes secundarios y cierre de sesión comprobado. |
| V08 | Resuelto en muestra | Resúmenes explícitos por recurso; campos secundarios disponibles bajo demanda. |
| V09 | Resuelto en muestra | Agenda y transporte por objetivos; pendientes los estados operativos que requieren escrituras. |
| V10 | Resuelto en muestra | Sin mensajes rutinarios permanentes; errores y sincronización mantienen contexto. Falta ensayo exhaustivo de incertidumbre. |
| V11 | Pendiente/bloqueado | Inventario completo de fuente, pero sin resolver todas las autorizaciones por recurso ni recorrer todas las rutas privadas. |
| V12 | Parcial | Chrome/Safari reales, cinco anchos, teclado/foco, Android cinco recorridos completos de escala y uno agotado (412 dp/200 %, rotación pendiente). Sin TalkBack/VoiceOver, iOS físico ni auditoría WCAG completa. |
| V13 | Parcial | Invariantes de fuente, contratos intactos, consultas reales y logout; falta repetir recorridos de escritura en laboratorio aislado. |
| V14 | Parcial | Componentes compartidos y pares comparables; quedan variantes de cobertura sin aceptación visual. |

## Integridad, pruebas y reproducción

[presentation.patch](presentation.patch) permite revisar el delta respecto de la copia inicial. [invariantes.json](invariantes.json) enumera los archivos existentes modificados desde la copia inicial. [integridad-adaptadores.json](integridad-adaptadores.json) compara fuentes de integración web y adaptadores móviles con la línea base de preparación, y comprueba que las contraseñas/secretos de demostración conocidos no aparecen en los APK. Los cambios previos del repositorio se conservaron; el `git diff` global incluye trabajo anterior y no describe por sí solo esta intervención.

No se modificaron servicios, contratos, DTO, clientes HTTP, validadores, bases, migraciones, permisos, workers, GPS/QR/cámara ni despliegue durante esta corrección. Los literales de rutas API de App/Donor/Transport coinciden con el antes; los efectos superiores de Transporte coinciden byte a byte. Esto es evidencia de alcance, **no una demostración completa de equivalencia funcional**. Las sesiones nativas producen los registros normales de acceso/dispositivo y revocación. No se crearon citas, evidencias clínicas, documentos o transiciones de custodia.

Archivos nuevos: macro `integration/row_actions.html`; `static/js/row-actions.js`; iconos lineales de recarga, sobre abierto, más acciones y chevron; `NavigationPresentation.kt`; implementaciones Android/iOS de regreso presentacional; instrumentación `VisualProfileTest`, `VisualScaleTest` y `BaselineVisualTest`. Los tests de recorridos existentes conservan aserciones funcionales y actualizan etiquetas/navegación. Los que necesitan `lab.json` solo se compilaron: no se ejecutaron contra GCP para evitar escrituras de negocio.

Compilación con JDK 17 y caché Gradle ya disponible, sin descargar runtimes/SDK:

```sh
GRADLE_USER_HOME=/private/tmp/redhouse-gradle-home \
JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home \
./apps/mobile/gradlew -p apps/mobile \
  :composeApp:testDebugUnitTest :composeApp:assembleDebug \
  :composeApp:assembleDebugAndroidTest :composeApp:compileKotlinIosArm64 \
  --offline --max-workers=2
```

El APK entregable queda en `.local/artifacts/mobile/RedHouse-uiux-quality-20261110-debug.apk`; su SHA-256 final figura en `invariantes.json`. No contiene credenciales. Las pruebas visuales autenticadas requieren argumentos de ejecución; sin ellos se omiten. `BaselineVisualTest` exige además `baseline=true` para evitar ejecutarlo contra la UI nueva.

Los scripts de reproducción sin secretos se conservan en [scripts](scripts/). Necesitan las dependencias locales existentes, los archivos privados de configuración autorizados y una copia inicial en `.local/uiux-quality-20261110/before`; no se distribuyen credenciales ni datos de configuración. Las pruebas navegador sirven fixtures por `127.0.0.1:15053`; el servidor Flask real se ensayó en `127.0.0.1:15054`. Safari requiere automatización remota, que el usuario habilitó expresamente.

## Incidencias y pendientes concretos

- Se conservan intentos iniciales de instrumentación y sus repeticiones. Fallaron esperas/selectores del arnés y el acceso MFA del primer ensayo ADB; no se presentan como pruebas aprobadas. El informe autenticado de referencia es `android-acceptance.json`; los intentos previos y sus fallos se conservan aparte.
- La captura por región de escritorio se descartó porque podía incluir otras ventanas. La captura por identificador de ventana también omitía capas del renderizador (incluso una barra inferior parcialmente vacía). Las capturas finales de perfiles usan el rectángulo exacto de la ventana del teléfono, elevado y situado fuera del Dock; se comprueba visualmente que no incluyen otras aplicaciones. Una rotación se tomó durante la transición y mostró negro: no acredita revisión visual. Se repitió tras esperar la recreación de Activity.
- **Límite visual aún abierto en transporte:** algunas capturas del detalle/contactos muestran el espacio de Avisos vacío en la barra inferior. El destino existe en la jerarquía y el recorrido lo pulsa con éxito; otras capturas muestran las cuatro opciones. No se ha aislado definitivamente si la omisión procede de captura/composición del emulador o del renderizado de la vista. No se declara esa superficie visualmente aprobada ni se atribuye el fallo a un dispositivo físico.
- Una repetición concurrente agotó tiempos de Safari/capturas Chrome y del acceso médico; se conserva en `intento-final-concurrente` y se repitió sin esa concurrencia. El primer ensayo de texto al 200 % detectó desbordamiento en el login. Se corrigieron las columnas con `minmax(0,1fr)`, anchura mínima y wrapping del título; la repetición pasó. La fixture de login también se corrigió para usar contexto público sin shell autenticado.
- Un diagnóstico directo de autenticación generó una sesión cuyo intento de logout por una ruta incorrecta respondió 400. No se afirma que esa sesión se revocara; se descartaron sus tokens y conserva la expiración normal. Los recorridos finales usan el cierre de sesión real de la app y verifican eliminación del almacén local.
- La repetición de acceso/teclado/rotación a 412 dp y fuente 200 % agotó el límite del host (140 s), sin resultado final de instrumentación. Se conserva como `timeout`, no aprobada; se detuvo el proceso y se restauraron 360×720 dp, fuente 130 % y orientación natural. La sesión autenticada donante a 412 dp/200 % sí terminó con logout verificado.
- Pendiente desbloquear el entorno privado web y revisar cada ruta/variante autorizada: administración, auditoría y superficies operativas no quedan aprobadas por sus fixtures genéricos. Pendientes contraste exhaustivo, lectores de pantalla, estados de conflicto/incertidumbre y regresión de escrituras en laboratorio aislado. iOS físico queda para el usuario, conforme a su indicación.
- No se cambian datos ni dependencias para producir estados convenientes. No se declara la etapa 04 finalizada. La etapa 05 conserva PySide6 y XML/XSD; heredará componentes de escritorio, no la navegación inferior móvil.

## Referencias de diseño

Se usan los patrones del prompt: [acciones Gmail](https://support.google.com/mail/answer/2473038?hl=en) y [comprensión de iconos NN/g](https://www.nngroup.com/articles/icon-usability/); [hubs NHS App](https://design-system.nhsapp.service.nhs.uk/patterns/hub-page/) y [subhubs](https://design-system.nhsapp.service.nhs.uk/patterns/sub-hub-page/); [tablas Carbon](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines); [ayudas NHS](https://service-manual.nhs.uk/design-system/components/hint-text); [accesibilidad Compose](https://developer.android.com/develop/ui/compose/accessibility/api-defaults). Orientan agrupación, jerarquía y semántica. No certifican usabilidad ni conformidad de Red House.
