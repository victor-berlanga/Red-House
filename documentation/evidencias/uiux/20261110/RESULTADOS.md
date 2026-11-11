# UI/UX web y móvil — 10 de noviembre de 2026

## Alcance y veredicto

Incremento de presentación, **aceptación integral del rediseño pendiente**. No se cierran etapas funcionales 03/04. Se conservaron los cambios previos del usuario. No se desplegó, publicó, migró, cambió infraestructura ni modificó escritorio. La comparación respecto al inicio de esta sesión está en `changed-from-session-start.json`; no debe confundirse con el diff global, que contiene trabajo previo.

La ejecución del prompt futuro está autorizada por la solicitud actual; la restricción de no actualizar estado durante la preparación de los documentos no corresponde a esta implementación.

## Implementación

- `base.html`: grupos únicos conservando los destinos y condiciones de autorización; Panel principal primero. Avisos de éxito, advertencia, error e información con iconos distintos. Una operación incierta ya no recibe un check de éxito.
- `list.html`: acceso directo al expediente junto a la vista rápida; una página no muestra dos paginadores inactivos. La exportación mantiene su alcance de página. Crear campaña pierde prominencia en horarios sin cambiar su nombre o destino.
- `dashboard.html`: tareas antes de indicadores; zona y límite exclusivo del periodo explicados. Highcharts y valores intactos.
- `values.html` y `detail.html`: estados documentales diferenciados y etiquetas de registros; los títulos libres no se traducen como estados.
- `login.html`, `public.html`, `app.css`: recuperación separada de ayuda institucional, contraste de ayudas/campos, foco y objetivos; publicaciones/vacíos con tratamiento coherente, sin contenido ficticio.
- `tracking.html`: fuente, captura, antigüedad y precisión antes del mapa. Se conservan IDs, atribución, limitaciones y controles.
- UI Compose: encabezado y menú de secciones persistentes, contenido desplazable separado, cuenta con privacidad/recuperación/logout, avisos con controles de notificación. Todos los destinos por perfil permanecen. Tema completo derivado de la web con tipografía Material nativa. Etiquetas de campos y perfiles en español; fechas visibles con zona y precisión originales. Referencias y estados desconocidos se conservan.
- `Presentation.kt` solo formatea salida; no modifica DTO, solicitudes, validadores ni valores enviados. Los campos de fecha conservan el formato contractual y reciben ayuda; todavía no se incorpora selector nativo.

## Inventario y cobertura

El inventario funcional completo del portal se conserva en [Pantallas y permisos](../../../entrega-final/portal/Pantallas_y_permisos.md). `navigation.json` registra cada destino de cada uno de los siete perfiles antes/después, incluidos administración, auditoría, reportes, laboratorio, personas, inventario, logística, órganos, agenda y avisos. Las familias de lista, detalle, formulario y panel mantienen sus acciones. Esto acredita revisión de presentación compartida, no ejecución completa de todos los módulos.

| Familia móvil / perfiles | Acciones y datos existentes conservados | Estados / alcance revisado |
| --- | --- | --- |
| Acceso / todos | Cuenta, contraseña, MFA, recuperación; gateway solo laboratorio | Red, carga, rechazo y mensaje de sesión |
| Perfil y cuenta / todos | Consulta propia, ayuda/permisos, logout, recuperación del diario | Incertidumbre y revocación no confirmada permanecen |
| Donante | Expediente, consentimiento, campañas, horarios, citas y confirmaciones | Vacío, carga, estado comunicado; fechas formateadas |
| Transporte | Tarea, ruta/contactos, QR, custodia, ubicación, evidencia | Procedencia, precisión, incertidumbre; sin alterar adaptadores |
| Operador | Inventario, detalle, lectura térmica y recepción | Mismas comprobaciones y confirmaciones |
| Coordinador | Resúmenes, reservas, tareas y programación | Referencias reales, ayuda de fechas; sin decisión clínica nueva |
| Médico | Solicitudes, muestras, resultados y completitud | Autorización documental separada de elegibilidad |
| Avisos / todos | Bandeja, reconocimiento, activación/revocación push | No acredita entrega por proveedor |
| Sincronización / transporte | Recuperar, sincronizar y limpiar estados terminales | Cola de observaciones; no custodia offline |

## Evidencia y límites

- Chrome local real: portada y acceso HTTP 200 a 1440, 768, 390 y 320 CSS px; sin desbordamiento horizontal. `browser.json` y capturas `after-public-*`, `after-login-*`. La portada muestra servicios no disponibles: no se inventan publicaciones.
- Los siete intentos de acceso local fueron rechazados con «No se puede verificar el cierre de sesión». **No son siete recorridos aprobados**. No se cambiaron conexiones, almacenes ni protecciones para conseguir acceso. Los recorridos privados y mediciones de negocio están **no medidos**.
- Plantillas reales con datos sintéticos: comparación antes/después del panel operador a los mismos cuatro anchos, sin desbordamiento. `fixture-browser.json` y capturas `*-synthetic-panel-*`. Son fixtures de presentación, no sesiones autenticadas ni evidencia de persistencia.
- Regresión Jinja: siete perfiles con conjunto de enlaces idéntico antes/después; grupos únicos; todos los templates compilan. Prueba persistente `apps/web/tests/uiux_presentation.py`: avisos inciertos y traducciones, incluido texto libre `AUTHORIZED` que no se transforma.
- `contrast.json`: contraste calculado de seis pares usados en ayuda, advertencia, acción y texto secundario, todos al menos 4,5:1. Cálculo de paleta, no certificación WCAG completa. La captura de acceso permitió detectar y corregir ayudas oscuras.
- No se atribuye validación a usuarios, TalkBack, VoiceOver, hardware físico ni persistencia por ver una captura. `FLAG_SECURE` permanece activo.

## Navegación antes/después

| Recorrido | Antes | Después | Naturaleza de evidencia |
| --- | --- | --- | --- |
| Lista → expediente | Vista rápida y luego expediente: 2 activaciones | Enlace directo: 1; vista rápida también disponible | Inspección de estructura; no medido con datos privados |
| Seleccionar sección móvil | Botones de todos los destinos encima del contenido | Menú persistente → sección; contenido reinicia su desplazamiento | Fuente; recorrido autenticado no medido |
| Acceso → ayuda institucional | Texto repetido respecto a recuperación | Nombre propio y contraste visible | Captura web local; sin envío de recuperación |
| Cita, custodia, programación | Confirmaciones originales | Conservadas | Regresión de código; recorrido real pendiente |

No se calculan porcentajes ni tiempos ahorrados. Las confirmaciones no cuentan como navegación redundante.

## Pendientes por hallazgo y aceptación

U01/U05/U06/U08/U10: implementación y comprobaciones de presentación descritas. U02/U04: traducción parcial; faltan estados/contextos y presentación específica exhaustiva por recurso. U03/U11/U12/U14: estructura/tema/lenguaje implementados; falta revisión nativa completa; la gota existente se reutiliza conservando su atribución ISC. U07/U09/U15/U16/U17: cambios dirigidos; falta recorrido privado completo y accesibilidad manual. U13: fechas visibles legibles y ayudas; pendiente entrada nativa y revisión integral de agenda.

UX-02 y la conservación estática de destinos están comprobados. UX-01/03/04/05/06/07/09/10 tienen evidencia parcial. UX-08 sigue pendiente para los recorridos privados y nativos. UX-11 se verifica por comparación de archivos. UX-12: limitaciones registradas aquí. No se declara aceptación total.

Pendientes funcionales detectados se dejan fuera: conectividad local, revocaciones no verificables y dependencias de servicios. Se requiere entorno aislado operativo para continuar recorridos autenticados; no se autoriza corregir infraestructura con este encargo.

## Referencias aplicadas

- [Android: navegación](https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-and-nav-patterns): separación persistente de navegación y contenido; menú para la cantidad de destinos existente.
- [NN/g: regla de tres clics](https://www.nngroup.com/articles/3-click-rule/): se distinguen navegación y confirmaciones, sin cuota artificial.
- [NHS: errores](https://service-manual.nhs.uk/design-system/components/error-summary) y [color](https://service-manual.nhs.uk/design-system/styles/colour): conservar resumen navegable y separar significado de estados de la marca.
- [Carbon: tablas](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines): herramientas proporcionadas y acceso al detalle sin añadir operaciones masivas.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) y [Compose: accesibilidad](https://developer.android.com/develop/ui/compose/accessibility/api-defaults): foco, reflow, contraste y controles nativos. Las comprobaciones parciales no acreditan conformidad completa.

El complemento de diseño sigue vigente para etapa 05: Python/PySide6, XML/XSD y criterios propios intactos. No se ha implementado escritorio.

## Compilaciones y regresión móvil

Fuentes finales: `build-reviewed.log`, **BUILD SUCCESSFUL**; Android APK debug y `compileKotlinIosArm64`. Esto comprueba compilación Kotlin compartida para iOS, no enlace Swift completo, firma ni ejecución iOS. Suite JVM: **23 casos, 21 aprobados y 2 omitidos**, cero fallos; las omisiones corresponden al laboratorio real no iniciado. Los dos casos nuevos verifican zona/precisión de fechas y distinción de estados frente a texto libre.

`instrumentation-build.log`: compilación de las pruebas nativas aprobada. Se actualizaron nombres accesibles y el recorrido por Secciones/Cuenta conservando las aserciones funcionales. Los flujos autenticados actualizados están **compilados, no ejecutados**.

Intentos conservados: caché Gradle fuera del sandbox; caché predeterminada incompleta en offline; intento redundante detenido; compilación con pruebas añadidas durante el proceso que produjo referencia no resuelta a `displayDate`. Repeticiones sobre fuentes completas aprobadas. No se descargaron SDK ni runtimes.

`public-final.json`: ayuda abre/cierra, orden de teclado cuenta → contraseña y texto raíz al 200 % sin desbordamiento a cuatro anchos. No equivale a auditoría de todos los focos ni zoom integral del navegador.

## Comprobación Android final

APK final instalado y arrancado en AOSP API 30 x86_64, pantalla 360×720 dp, fuente al **130 %**. `PresentationAccessTest` aprobó con controles visibles después de desplazar, teclado de entrada, recuperación deshabilitada sin cuenta y habilitada al introducir texto sintético, segundo factor y ausencia de gateway en la compilación normal. **Un caso único**, repetido al reforzar las aserciones; `native.log` y `native-final.log`. Sin enviar credenciales, recuperación ni datos de negocio. La jerarquía accesible queda en `android-access-130.xml`; no se retiró `FLAG_SECURE` ni se presenta como captura visual completa.

La prueba no cubre la navegación autenticada, rotación, TalkBack ni iOS físico. Portal y emulador temporales cerrados tras la comprobación; almacenes/servicios existentes intactos.
