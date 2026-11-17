# Colecta y legibilidad de formularios — 17/11/2026

El selector de donantes de colecta usaba `actor` sin definir. Ahora valida la institución contra `OperationContext.actor`, la identidad capturada al abrir el formulario. Conserva los controles de cambio de sesión y evita mostrar donantes ajenos.

Regresión dirigida: **5 pruebas aprobadas en 5,08 s**. Incluye selección de un donante elegible, rechazo de otra institución, rechazo de una respuesta tras cambiar de sesión y procesamiento. Los dobles se ajustaron al contexto de sesión vigente; no se atribuye a estas pruebas un recorrido con servicios reales. El primer intento real Android C/Qt permanece fallido, sin donación nueva y con sus dos familias cerradas; su continuación se ejecutará sobre la misma cita.

Se amplió el espacio de escritura mediante la política de crecimiento del formulario en vínculo/liberación de perfil, alta de muestra y recepción. Dirección abrió e inspeccionó estas tres capturas Qt:

- [Vínculo de perfil](01-vinculo-perfil-sintetico.png): motivo completo y controles legibles.
- [Alta de muestra](02-registro-muestra-sintetica.png): identificador y fecha visibles junto a ambas tablas.
- [Recepción](03-recepcion-muestra-sintetica.png): motivo legible y confirmación visible.

Datos sintéticos locales, renderizado offscreen y cancelación de los tres diálogos. Sin red, autenticación ni envío de operaciones; no acredita Windows, navegación Tab ni un nuevo paquete distribuible. El parche privado original tenía cabeceras de diff inválidas y no llegó a aplicarse; se integraron directamente los tres cambios previstos. No se añadió una suite para comprobar únicamente anchuras.

[Comandos, huellas y límites](resumen.json). El ejecutable macOS anterior debe reconstruirse para incluir estos cambios.

La continuación real registró una única colecta para la cita Android conservada, con estado COLLECTED v1 y cierre de una familia en SQL/Redis. Dirección inspeccionó la captura anterior al envío; la persistencia se comprobó por separado. El motivo resultó demasiado estrecho en Cocoa: se aplicó la misma política a colecta y procesamiento y se inspeccionaron dos capturas sintéticas adicionales ([colecta](04-colecta-sintetica.png), [procesamiento](05-procesamiento-sintetico.png)), cancelando ambos formularios. No se repitió la colecta ni las cinco regresiones por ese ajuste de ancho. El procesamiento real y los componentes derivados siguen pendientes.
