# Comprobaciones físicas de Lab renovada — 17/11/2026

El usuario operó Red House Lab actualizada en su iPhone 16 Pro y confirmó cuatro resultados:

- Apertura en acceso e Inicio después de login manual de la cuenta sintética donante. No se acreditó restauración de la sesión anterior.
- VoiceOver anunció «Avisos» y permitió abrir la pestaña mediante doble toque. Acredita ese control, no el orden de lectura completo ni conformidad general de accesibilidad.
- Después de Actualizar, el recordatorio mostró «Recordatorio de tu cita», sustituyendo el código APPOINTMENT_REMINDER observado en el corte previo.
- «Compartir campaña» abrió el menú nativo de iOS. Se indicó cerrarlo sin enviar contenido; no se publicó información externa.

Son comprobaciones funcionales asistidas por la persona usuaria. Dos intentos de captura XCTest fallaron con LocalAuthentication −4, el segundo tras confirmar el dispositivo desbloqueado. Se conservan separados; no se atribuye fallo del producto ni aceptación visual a esas capturas. La imagen alternativa solicitada sigue pendiente. La restauración de VoiceOver al estado anterior no quedó confirmada por separado.

La [renovación y actualización](../profile-renewal-20261117/RESULTADOS.md) identifica el artefacto y perfil. El [resumen](resumen.json) conserva el alcance observado. No se repitieron citas, edición de nombre, QR, fotografía o sincronización por esta actualización.
