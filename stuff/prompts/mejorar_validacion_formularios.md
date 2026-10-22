# Mejora de validación y mensajes de formularios

Mejora la experiencia de validación de los formularios de Red House. El usuario debe comprender qué dato es incorrecto, por qué fue rechazado y cómo corregirlo.

Lee `AGENTS.md` y `PROJECT_STATUS.md`. Contrasta las reglas actuales del backend con los formularios antes de modificar código. Atiende altas, ediciones y confirmaciones de operaciones.

## Comportamiento requerido

1. Muestra instrucciones breves junto a los campos que tengan restricciones relevantes: longitud, rango, formato o dependencia con otro campo. Indica cuándo un campo es opcional. Usa placeholders únicamente para ejemplos; la instrucción debe permanecer visible al escribir.
2. No muestres errores rojos al abrir el formulario ni durante la captura inicial. Después de un intento de envío fallido, presenta el error específico junto a cada campo afectado, con borde y texto de error. Ejemplo: «Escribe al menos 6 caracteres o deja este campo vacío».
3. Sustituye el aviso superior genérico por un resumen como «Revisa los 2 campos señalados», con enlaces a los campos afectados. Lleva el foco al resumen y permite llegar a cada campo con teclado. Usa `aria-invalid` y `aria-describedby`; no dependas exclusivamente del color.
4. Conserva los valores capturados, las selecciones y las confirmaciones tras un rechazo. No vuelvas a mostrar contraseñas. Si un archivo debe seleccionarse nuevamente, indícalo. Conserva el comportamiento de idempotencia y permite reenviar después de corregir.
5. Refleja en HTML los límites aplicables mediante `minlength`, `maxlength`, `min`, `max`, `step` y `pattern`, según corresponda. Coordina la validación nativa y la del portal para que no haya mensajes contradictorios. Mantén la validación del servidor como autoridad.
6. Para reglas entre campos, señala los campos relacionados y explica la corrección. Ejemplo: «Agrega la fecha del consentimiento o elimina la referencia». Para un consentimiento futuro, indica que debe utilizarse una fecha no posterior al momento actual.

## Formularios y reglas que deben revisarse

- **Donantes y receptores:** restricciones, antecedentes, requerimientos y estudios utilizan reglas de longitud de 6 a 1000 caracteres. Respeta cuáles son obligatorios y cuáles opcionales. En donantes, referencia y fecha del consentimiento se capturan juntas y la fecha no puede ser futura.
- **Folios:** entre 6 y 30 caracteres; letras ASCII, números, guion y guion bajo. Explica que no admiten espacios ni acentos.
- **Nombres y textos:** identifica los campos limitados a 200 caracteres y representa su límite correctamente.
- **Campañas:** cupo entre 1 y 10 000. Diferencia fecha final anterior o igual al inicio y fecha final ya vencida. Al editar, distingue un registro desactualizado de un cupo inferior a las citas reservadas; muestra el mínimo permitido cuando esté disponible.
- **Solicitudes:** cantidad entre 1 y 100; urgencia entre 1 y 3. Explica el significado de los niveles únicamente conforme a las reglas documentadas.
- **Rutas:** distancia entre 0 y 20 000 km; duración entera entre 0 y 10 080 minutos; fuente de estimación entre 6 y 1000 caracteres.
- **Ubicación:** latitud entre −90 y 90 y longitud entre −180 y 180. Conserva la explicación del periodo autorizado de captura y diferencia errores de coordenadas, fecha y permisos del dispositivo.
- **Usuarios:** cuenta entre 3 y 80 caracteres y contraseña nueva entre 12 y 128. Conserva mensajes de autenticación que no revelen si una cuenta existe.
- **Catálogos de capacidad:** cantidad entre 0 y 100 000.
- **Confirmaciones y ediciones:** motivo entre 6 y 1000 caracteres en evaluaciones, liberaciones, cancelaciones, bajas, traslados y demás operaciones que lo utilicen.
- **Inventario y traslados:** reemplaza mensajes que mezclan causas, como «Componente o caducidad inválidos» y «Horario inválido o posterior al límite capturado». Identifica el campo y la condición incumplida: componente, caducidad, recolección, salida, llegada o duración de ruta.
- **Archivos:** conserva las instrucciones existentes de formato y tamaño. Revisa los rechazos adicionales para que expliquen qué archivo o condición requiere atención sin exponer detalles internos.

Confirma estos límites en el código vigente. No cambies reglas de negocio ni relajes validaciones para evitar errores. Si una restricción parece injustificada, documéntala para revisión separada.

## Implementación

Resuelve el problema en el mecanismo compartido de formularios y en los formularios específicos que lo necesiten. Revisa especialmente:

- `apps/services/redhouse/codec.py`: conservar información estructurada y segura sobre campos, causas y límites de validación. Evitar que las validaciones entre campos pierdan su explicación.
- `apps/web/src/integration/client.py`: transportar los detalles de error al portal, además del mensaje general.
- `apps/web/src/integration/routes/common.py`: asociar errores con los campos visibles y sus etiquetas, incluyendo conversiones de números y fechas.
- `apps/web/src/presentation/templates/integration/form.html`: instrucciones, resumen, errores junto a campos y accesibilidad.
- Formularios de archivos, acceso y cualquier flujo que tenga su propio manejo de errores.

Distingue errores corregibles por el usuario de conflictos de estado, permisos o fallos de dependencias. No muestres referencias a contratos, nombres internos de campos, trazas, credenciales ni datos sensibles en mensajes operativos. Traduce las causas a español y proporciona una acción útil.

Conserva JWT, Redis, CSRF, autorización institucional, contratos versionados JSON/XML/XSD, independencia del portal y despliegue Docker. Actualiza los contratos si amplías la estructura pública de errores y conserva compatibilidad con sus consumidores.

## Validación y entrega

Prueba casos válidos e inválidos, límites exactos, campos opcionales vacíos, espacios en blanco, varios errores simultáneos, dependencias entre campos, altas y ediciones. Verifica que corregir los valores permite guardar y que un rechazo no escribe parcialmente datos de negocio.

Comprueba en navegador: ausencia de errores iniciales, instrucciones visibles, errores específicos después del envío, foco y navegación con teclado, conservación de datos, reenvío y presentación móvil. Incluye comprobaciones de errores JSON/XML y regresiones de los flujos afectados. Usa datos ficticios en un entorno de prueba aislado.

Actualiza documentación y `PROJECT_STATUS.md` con cambios, pruebas, evidencia y pendientes. Distingue lo probado localmente de lo desplegado. No declares resuelto un formulario que no se haya verificado.
