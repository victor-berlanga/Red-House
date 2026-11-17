# Registro de incidencias de entrega final

Corte: 17/11/2026. Registro **selectivo**, no inventario exhaustivo de todos los logs, JUnit o intentos. Consolida incidencias materiales documentadas en el reporte final, `PROJECT_STATUS.md` y recibos enlazados. Conserva intentos previos y separa defectos, fallos del arnés, brechas de verificación y dependencias externas. No crea ejecuciones nuevas ni declara etapas cerradas.

## INC-01 — Consulta N+1 en disponibilidad de Inventario

- **Fecha; componente/versión; entorno:** 17/11/2026; Inventario, API v1/versión 0.4.1; PostgreSQL local esquema 21, fixture académico y lectura HTTP local separadas.
- **Clase:** defecto técnico de consultas; aceptación SQL separada de carga HTTP.
- **Síntoma e impacto:** lectura de controles por cada unidad elevó la consulta interna a 3.189 ms sobre su límite de 3 s y contribuyó al 503 en el intento de carga. Riesgo de latencia en disponibilidad.
- **Reproducción/evidencia:** [corrección y comparación SQL](../evidencias/entrega-final/inventario-consulta-20261117/RESULTADOS.md): 17 pruebas dirigidas; dos pares AB/BA sobre 4.502 filas idénticas, original 732,73–1.297,50 ms y JOIN 43,91–74,14 ms. [Estado](../../PROJECT_STATUS.md) y [recibo de continuación](../evidencias/entrega-final/carga-finita-20261117/RESULTADOS.md) indican dictamen 201 histórico reutilizable; no es una nueva medición de carga.
- **Responsable:** rol propietario de Inventario; coordinación de carga/integración. No se atribuye a una persona.
- **Acción y estado:** sustituir consulta por unidad con LEFT JOIN; **N+1 corregida y aceptada en SQL; dictamen 201 confirmado/reutilizado, sin reenvío**. La ventana finita compuesta completó nueve casos, seis medidos, 49 HTTP sin fallos, 27 intenciones conciliadas y oráculo persistente; el raw conserva `FAILED_CLEANUP` por fallo de cierre.
- **Comprobación:** mismos 4.502 resultados/orden/valores cotejados; PostgreSQL propio cerrado. Siete familias previas conciliadas. La familia residual se revocó por separado; después, el teardown de solo lectura comprobó tres cierres nuevos; no reescribe el raw ni convierte el ensayo en PASS. Una transferencia de Inventario a GCP quedó bloqueada por auto-review en `stage`, antes de transferir; el acceso temporal se retiró. El usuario autorizó explícitamente el segundo intento, todavía sin aceptación final. **Publicación GCP no aceptada**.

## INC-02 — Versión incompatible y cierre incompleto en arnés MFA

- **Fecha; componente/versión; entorno:** 17/11/2026; arnés finito de carga, Inventario 0.4.1 frente a versión global esperada 0.4.4; fixture local PostgreSQL/Redis.
- **Clase:** fallo del arnés y de su compensación de cierre; no se atribuye a rechazo de MFA del producto.
- **Síntoma e impacto:** el parser del reto exigía la versión global y rechazaba el contrato del propietario Inventario. Fallo de `on_start` también dejó familias técnicas abiertas; el verificador de cierre inicial devolvió `false`.
- **Reproducción/evidencia:** suite pura del arnés **67/67 aprobada** después de retirar hooks privados; [recibo de la continuación finita](../evidencias/entrega-final/carga-finita-20261117/RESULTADOS.md) y su [resumen sin datos sensibles](../evidencias/entrega-final/carga-finita-20261117/resumen.json). Se corrigió el parser para cotejar versión contra OpenAPI del propietario y añadir compensación por actor.
- **Responsable:** rol propietario de pruebas de carga/Identidad. Sin persona asignada.
- **Acción y estado:** parser corregido; **runtime de negocio conserva `FAILED_CLEANUP`**. Siete familias propias anteriores quedaron conciliadas. El teardown posterior de solo lectura cerró tres familias con cero errores y ledger de negocio intacto; es una comprobación separada, no un PASS del recorrido original.
- **Comprobación:** nueve casos compuestos, seis medidos; 27 intenciones confirmadas y persistencia verificada. La sesión residual se revocó después y SQL/Redis confirmaron el cierre. Ninguna medición estima capacidad ni cierra etapas de rendimiento.

## INC-03 — Sesión de Xcode vencida al renovar perfiles iOS

- **Fecha; componente/versión; entorno:** primer intento 17/11/2026; firma iOS/Xcode; macOS y dispositivo autorizado.
- **Clase:** dependencia externa de autenticación de firma; resuelta en segundo intento.
- **Síntoma e impacto:** sesión caducada impidió al primer intento emitir perfiles que cubrieran el día 23. El runner no encontró perfil iOS normal; los perfiles originales se restauraron intactos.
- **Reproducción/evidencia:** [build y fallo inicial](../evidencias/entrega-final/mobile/final-build-20261117/RESULTADOS.md); [renovación posterior](../evidencias/entrega-final/mobile/profile-renewal-20261117/RESULTADOS.md).
- **Responsable:** rol de firma/distribución móvil y titular de la cuenta existente; no se nombra persona.
- **Acción y estado:** reautenticar Xcode y repetir una sola renovación acotada; **resuelto para firma**: ambos perfiles vencen el 24/11 cerca de 18:03 UTC y cubren el 23. Lab se instaló como actualización; normal no se instaló.
- **Comprobación:** firma/perfil/Keychain verificados. Apertura, sesión, recorridos nativos, VoiceOver y distribución general siguen pendientes.

## INC-04 — Qt no persistía mosaicos por formato de encabezados

- **Fecha; componente/versión; entorno:** 16/11/2026; consola Qt/PySide6 6.10.1; macOS local, cliente XML/WSS.
- **Clase:** defecto técnico del cliente cartográfico.
- **Síntoma e impacto:** `QNetworkReply.rawHeader(bytes)` no entregaba los encabezados al código que guardaba mosaicos; la cartografía cargaba pero no los conservaba en caché.
- **Reproducción/evidencia:** [recibo de mosaicos y mapa](../evidencias/entrega-final/desktop/mapa-mosaicos-20261116/RESULTADOS.md).
- **Responsable:** rol propietario de escritorio/cartografía.
- **Acción y estado:** pasar nombres de encabezado como `str`, preservar validaciones y política `no-store`; **corregido y verificado localmente** con cuatro pruebas, `QNetworkReply` real y relectura Qt del mismo punto, 15 mosaicos y cero publicaciones nuevas.
- **Comprobación:** salida 0, captura inspeccionada y familia cerrada. No acredita Windows, GPS en vivo, Nginx WSS ni aceptación de todos los paquetes.

## INC-05 — Analytics Qt asumía obligatorio `unit`

- **Fecha; componente/versión; entorno:** 16/11/2026; consola escritorio/analítica, contrato XML de Inventario; fixture local académico.
- **Clase:** defecto técnico de manejo de campo opcional.
- **Síntoma e impacto:** una respuesta válida omitió el campo opcional `unit`; Qt lanzó `KeyError` y terminó el primer recorrido de solo lectura con salida 1.
- **Reproducción/evidencia:** [recorrido, fallo y repetición](../evidencias/entrega-final/desktop/iteracion-analitica/RESULTADOS.md).
- **Responsable:** rol propietario de escritorio/analítica.
- **Acción y estado:** normalizar `unit` y `values` conforme a sus valores contractuales; **corregido y verificado** con regresiones enfocadas y una repetición XML real que cotejó tablas/DTO de Inventario, Receptores y Transporte.
- **Comprobación:** salida 0, capturas inspeccionadas, familias cerradas y fuentes estables. Los otros roles conservan pruebas con dobles; no prueba Windows ni accesibilidad completa.

## INC-06 — Reintento LOCAL de documento en estado `MISSING`

- **Fecha; componente/versión; entorno:** 16/11/2026; Documentos/web, esquema 21; gate local y publicación GCP existente.
- **Clase:** defecto técnico de recuperación de almacenamiento LOCAL.
- **Síntoma e impacto:** un documento previamente registrado podía quedar `MISSING`; el flujo debía permitir completar el mismo objeto sin reemplazar propietario, autorización ni inmutabilidad.
- **Reproducción/evidencia:** [publicación y límites](../evidencias/entrega-final/gcp-documentos-referencia-20261116/RESULTADOS.md): cuatro casos LOCAL/I06-08, dos relecturas Chrome y release de fuentes acotado.
- **Responsable:** rol propietario de Documentos y portal.
- **Acción y estado:** reintentar el mismo documento LOCAL en vez de crear otra referencia; **corregido y publicado** junto a etiquetas/referencias del portal.
- **Comprobación:** gate y publicación aprobaron; LOCAL, monolith y esquema 21 permanecieron. No se repitió carga real del objeto en producción ni se declara todo el HEAD publicado.

## INC-07 — Probe GCP usó credencial obsoleta; `finish` no tenía `requests`

- **Fecha; componente/versión; entorno:** 16/11/2026; runner de publicación Documentos/referencia; GCP VM `red-house`, release limitado.
- **Clase:** fallos de preparación/cliente del proceso de publicación; no fallo del producto.
- **Síntoma e impacto:** primer probe protegido recibió 401 con cero familias nuevas. Un `finish` posterior falló al importar `requests` en Python del host antes de HTTP.
- **Reproducción/evidencia:** fases y fallos preservados en [recibo GCP](../evidencias/entrega-final/gcp-documentos-referencia-20261116/RESULTADOS.md).
- **Responsable:** rol de despliegue/automatización. No se atribuye a persona ni al servicio web.
- **Acción y estado:** conciliar 401 sin login nuevo; reutilizar credencial ya rotada; reemplazar solo el cliente del helper `finish` por `urllib`; **cerrado como fallo de preparación/cliente operativo**, no defecto de producto.
- **Comprobación:** probe vigente aprobado, salud/login públicos 200 y `finish` estándar aprobado. Sin restablecer/adivinar contraseña, reconstruir imágenes o instalar dependencia; acceso temporal cerrado. Vigencia TLS del día 23 se comprueba aparte.

## INC-08 — p95 no cumple objetivo previo con 24 usuarios

- **Fecha; componente/versión; entorno:** 14/11/2026; servicios HTTP/Locust; laboratorio local, esquema 21, sin GCP ni réplicas.
- **Clase:** incumplimiento de rendimiento medido, sin causa técnica atribuida.
- **Síntoma e impacto:** con 24 usuarios, p95 de Traslados llegó a 2.100 ms y Tareas propias a 2.000 ms; el criterio previo exigía estrictamente menos de 2.000 ms.
- **Reproducción/evidencia:** [serie de carga 12/24](../evidencias/entrega-final/carga-20261114/serie-12-24/RESULTADOS.md).
- **Responsable:** roles de rendimiento/servicios propietarios.
- **Acción y estado:** investigar/optimizar y repetir con las mismas condiciones/umbral; **no aceptado**. Cero errores y ejecución completa no cambian el incumplimiento. El escenario de 36 usuarios se omitió conforme al plan.
- **Comprobación:** se conserva la métrica original y las seis fases. La ventana finita posterior cubrió seis casos, pero no estima capacidad ni reemplaza el incumplimiento a 24 usuarios. No atribuir causa precisa a un endpoint.

## INC-09 — Aceptación nativa Windows 11 no disponible

- **Fecha; componente/versión; entorno:** brecha vigente al 17/11/2026; consola PySide6; paquete aceptado solo en macOS Intel local.
- **Clase:** dependencia de plataforma/entorno de aceptación; no defecto observado.
- **Síntoma e impacto:** no hay ejecución del workflow Windows ni recorrido en Windows 11; un runner Windows Server no probaría la instalación del equipo destino.
- **Reproducción/evidencia:** [matriz de distribución](continuidad/Distribucion_escritorio.md) y [paquete macOS Intel](../evidencias/entrega-final/desktop/paquete-macos-20261117/RESULTADOS.md).
- **Responsable:** rol escritorio/entrega y entorno Windows de destino; persona no asignada.
- **Acción y estado:** ejecutar build/instalación/flujo en Windows 11 si ese destino se mantiene; **pendiente de entorno/aceptación, no defecto confirmado**. La accesibilidad completa de consola también sigue pendiente.
- **Comprobación:** macOS Intel tiene smoke e inspección de login; eso no sustituye Windows, Apple Silicon, Linux, lector o negocio empaquetado.

## INC-10 — Push físico FCM/APNs pendiente por dependencia externa

- **Fecha; componente/versión; entorno:** vigente al 17/11/2026; Alertas y clientes Android/iOS; no se configuraron proyectos/cuentas/certificados push.
- **Clase:** dependencia externa deliberadamente no configurada; no defecto de producto.
- **Síntoma e impacto:** no existe evidencia de recepción física FCM/APNs; bandeja interna y adaptadores no prueban entrega del proveedor.
- **Reproducción/evidencia:** [dependencias móviles](mobile/Dependencias_externas.md), [matriz móvil](mobile/Matriz.md) y [agenda/recordatorio iOS](../evidencias/entrega-final/mobile/ios-resume-20261116/AGENDA.md).
- **Responsable:** propietario de Alertas más administrador del proyecto/proveedor, roles aún no asignados nominalmente.
- **Acción y estado:** requiere decisión/autorización y credenciales del proveedor; **dependencia externa abierta, no defecto de producto**. No crear cuentas ni claves para este registro.
- **Comprobación:** recordatorio persistido y bandeja iOS comprobados; recepción push física continúa no verificada.

## INC-11 — Accesibilidad de lectores de pantalla sin aceptación

- **Fecha; componente/versión; entorno:** vigente al 17/11/2026; portal, Android, iOS y escritorio; pruebas nativas disponibles.
- **Clase:** verificación de accesibilidad pendiente; no defecto observado.
- **Síntoma e impacto:** VoiceOver/TalkBack y accesibilidad completa de escritorio no se han probado de forma aceptada; no hay defecto concreto que se pueda afirmar.
- **Reproducción/evidencia:** [prompt 07, usabilidad](../../stuff/prompts/entrega-final/07_integracion_pruebas_y_rendimiento.md#usabilidad-y-evidencia-real), [matriz móvil](mobile/Matriz.md) y [distribución escritorio](continuidad/Distribucion_escritorio.md).
- **Responsable:** roles de móvil, escritorio y UX/accesibilidad; nombres por confirmar.
- **Acción y estado:** recorrer tareas autorizadas con lector, foco, escala y teclado; **verificación pendiente**, no reportar como fallo observado.
- **Comprobación:** capturas o navegación visual normal no equivalen a prueba de lector de pantalla.

