# Cambio autorizado de contraseñas de demostración — 11/11/2026

El usuario solicitó una contraseña común fácil de recordar para todas las cuentas de demostración en local y GCP. La contraseña y los respaldos de hashes se conservan únicamente en archivos privados de configuración y mantenimiento.

Se identificaron 50 cuentas locales (42 del catálogo de seis instituciones y ocho heredadas con dominio ficticio) y 37 en GCP (catálogo base, donantes sintéticos y cuentas de comprobación). Selección fijada mediante ID, nombre, rol e institución antes de actualizar. Se verificó la coincidencia al bloquear cada fila.

Operación desde Identidad con el mismo hash scrypt configurado para recuperación, helper existente de revocación, incremento de versión y evento PASSWORD_RECOVERED con motivo administrativo y correlación. Se conservaron roles, instituciones, actividad y factores MFA. Se invalidaron tokens de recuperación donde existe su tabla. La configuración local heredada carece de esa tabla y conserva su esquema.

Resultados: 50/50 hashes locales y 37/37 en GCP comprobados; 50 y 37 eventos de auditoría respectivamente. Revocadas 244 sesiones locales y 336 de GCP, sin sesiones previas activas al terminar cada operación. El ensayo posterior HTTPS confirmó login, perfil y logout de donor1, transport1 y operator1. Admin1 obtuvo 401 mfa_required con la contraseña nueva y sin OTP, conservando la exigencia de segundo factor.

Estado privado de credenciales actualizado en .local/runtime/state.json y .local/demo/state.json. GCP conserva respaldo y estado actualizado en /opt/redhouse/.local/password-maintenance-20261111 y /opt/redhouse/.local/compose/state.json. La verificación local fue de persistencia y autorización almacenada, sin un nuevo recorrido HTTP del portal local. No se necesita recompilar clientes por este cambio de datos.

Incidencias conservadas: SSH inicial rechazado, base local inicialmente detenida, transacción local revertida por tabla de recuperación ausente y docker cp rechazado sobre rootfs de solo lectura. Se corrigieron los procedimientos privados de mantenimiento; la repetición completó los cambios. Los resultados numéricos y verificaciones están en [resultado.json](resultado.json).

La clave SSH temporal de esta intervención se retiró de OS Login al terminar y se eliminaron sus dos archivos locales. Las claves anteriores se conservaron.
