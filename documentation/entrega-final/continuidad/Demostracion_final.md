# Índice operativo de demostración final

Estado de corte: documentación de apoyo en curso. Este índice ordena evidencia existente; no afirma una ejecución final integrada, aceptación académica ni entrega completa. Los recorridos registrados usaron datos sintéticos y entornos de laboratorio salvo cuando la evidencia indique otro alcance.

## Orden sugerido

1. **Ingreso de unidad y revisión de laboratorio.** Operador recibe una muestra y captura resultado; personal médico autorizado revisa. La ejecución Qt/XML verificó persistencia, versión, vínculo por muestra y auditoría. [Resultados](../../evidencias/entrega-final/desktop/iteracion-laboratorio/RESULTADOS.md) · [matriz de continuidad](Matriz.md).
2. **Solicitud, evaluación y reserva revisada por persona autorizada.** Mostrar consulta de candidato, vigencia, dictamen humano y reserva; separar el resultado algorítmico de la decisión. El ensayo de evaluación fue Qt/XML con solicitud y unidad sintéticas; la reserva comprobó recuperación con la misma clave y una sola reserva. [Evaluación](../../evidencias/entrega-final/desktop/iteracion-evaluacion/RESULTADOS.md) · [reserva y límites](../../evidencias/entrega-final/desktop/iteracion-reserva/RESULTADOS.md).
3. **Traslado y cadena de custodia.** Mostrar tarea del transportista, lectura QR, transiciones de recolección/tránsito/entrega y aceptación del destinatario. La ejecución Android aprobó el recorrido sintético y contrastó eventos en SQL/Mongo; no demuestra GPS físico, cámara física ni una prueba física de teléfono. [Resultados móviles](../../evidencias/entrega-final/mobile/RESULTADOS.md) · [estado del 14/11](../../../PROJECT_STATUS.md) · [matriz móvil](../../entrega-final/mobile/Matriz.md).

Los tres ensayos son evidencias separadas; la secuencia no se ha aceptado como una única demostración integral ni acredita por sí sola los tres flujos integrales exigidos. Antes de grabar, confirmar la versión desplegada siguiendo el [procedimiento GCE](../../../deployment/gcp/README.md). El paquete actual de escritorio es [macOS Intel](../../evidencias/entrega-final/desktop/paquete-mac-20261114/RESULTADOS.md); los paquetes móviles constan en el [registro de compilación y firma](../../evidencias/entrega-final/mobile/seguimiento-20261114/paquetes.md).

## Quién debe participar

El equipo asigna integrantes y confirma autoría; este documento no atribuye nombres ni contribuciones. Perfiles para el recorrido: operador de laboratorio, personal médico autorizado, coordinador y transportista. Una persona del equipo presenta y otra registra incidencias si el grupo así lo decide. Las reflexiones deben redactarlas y aprobarlas sus autores.

## Pendientes antes de declarar cierre

- Firma iOS para la fecha de entrega: el perfil actual vence el **17/11/2026**; la firma válida para el día 23 sigue pendiente.
- Windows 11 de escritorio sin verificación; el runner Windows de CI no sustituye la prueba en el equipo destino.
- Recepción física de FCM/APNs pendiente externa y sin cuentas configuradas por decisión del equipo.
- Grabar y conservar el video final, hacer la exposición, recibir reflexiones individuales y confirmar la subida a Ubiquitous. Son entregas humanas; no se sustituyen por este guion ni por evidencia del segundo parcial.
- No publicar credenciales, archivos privados, tokens ni pantallas con datos sensibles. La aprobación clínica/normativa sigue fuera del alcance de estos ensayos sintéticos.
