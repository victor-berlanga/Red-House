# Alta preliminar Android — 16/11/2026

**Alta funcional comprobada por UI nativa y oráculo de solo lectura.** La cuenta sintética existente `donor2` no tenía expediente propio. No se creó ningún usuario ni se enroló o modificó MFA. El usuario autorizó explícitamente un único expediente sintético local; no se cambiaron datos de las cuentas anteriores.

La continuación Android observó Nombre vacío y habilitado tras la carga, introdujo nombre sintético, visitó la opción de grupo desconocido, seleccionó O+ y marcó expresamente el checkbox inicialmente desmarcado. Se pulsó Registrar una sola vez. La interfaz mostró «Expediente preliminar registrado. Tu institución revisará la información.»; no se repitió el POST.

El [recibo sanitizado](RECIBO.json) acredita un expediente propio PRELIMINARY versión 1, actor/institución correctos, un resultado de idempotencia y un evento DONOR_REGISTERED coincidente en Auditoría SQL/Mongo. El cuerpo y la clave observados en servidor quedan en el recibo privado; no se afirma medición independiente de la clave nativa. Las dos familias técnicas del intento inicial y la continuación se revocaron en SQL y quedaron ausentes en Redis. Logout de la cuenta propia completado y AVD cerrado con salida 0; el servidor quedó disponible para raíz.

`donors.consent=true` corresponde al consentimiento explícito del registro preliminar. No se inventó consentimiento documental: referencia/fecha permanecieron null y `consent_versions` conservó cero filas. PRELIMINARY no acredita aptitud clínica ni autoriza donación. El nombre y grupo de este ensayo son datos sintéticos, sin preselecciones del formulario.

## Fallos conservados y límite visual

La [instrumentación original](instrumentacion-inicial.txt) falló en 18,003 s antes de introducir el nombre: intentó escribir mientras Nombre estaba Disabled. El oráculo intermedio confirmó cero expedientes y cierre de esa familia. En la continuación se observó Nombre habilitado tras cargar; por tanto el fallo inicial corresponde a sincronización del arnés. No se recompilaron APK ni se reejecutó la instrumentación.

**No hay inspección visual aceptada de este formulario.** El árbol de accesibilidad y SQL acreditan el comportamiento funcional. La captura previa al envío tomó una ventana del terminal Codex superpuesta, no el AVD. Dirección la abrió y la descartó; el original permanece privado y no se publica ni se recorta para aparentar una captura válida. No se creó otro expediente ni se mantuvo el laboratorio abierto para repetirla.

Los [hashes](FUENTES.json) identifican fuentes, recibos privados y los dos APK conservados. Esta prueba no añade ejecución física iOS del alta, aprobación clínica, consentimiento documental ni cierre total de etapa04. Tampoco repite los positivos de cámara, QR, GPS, agenda o sincronización anteriores.
