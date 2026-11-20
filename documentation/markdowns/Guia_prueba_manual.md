# Guía de prueba manual para el equipo

Corte: 20/11/2026. Sirve para que cualquier integrante pruebe Red House a mano, de punta a punta, sin conocer el código. Para el detalle de cada pantalla, consulta el [Manual de usuario](Manual_de_usuario.md); aquí solo se indica con qué cuenta entrar, en qué orden y qué debe pasar.

> Las cuentas y los datos son ficticios. **Nunca** pegues la contraseña ni los secretos de MFA en chats, capturas, documentos o commits.

Los pasos se derivan del código y de las evidencias de la rama `entrega-final`. No se volvieron a ejecutar en la VM al escribir esta guía, porque la VM estaba apagada.

## 1. Antes de empezar: encender la VM

El sistema de la nube vive en la VM `red-house` (proyecto `sistemas-integracion-01`, zona `me-central1-a`). Se apaga para no gastar crédito. Quien tenga permiso en GCP la enciende:

```sh
gcloud compute instances start red-house --project=sistemas-integracion-01 --zone=me-central1-a
```

Espera de 3 a 5 minutos y abre **https://34.18.186.116**. Debe aparecer la página pública con «Acceso institucional». Al terminar la prueba, apágala:

```sh
gcloud compute instances stop red-house --project=sistemas-integracion-01 --zone=me-central1-a
```

El certificado HTTPS vence el **24/11/2026 a las 14:08 UTC**. Después de esa hora el navegador y la app móvil rechazarán la conexión hasta renovarlo.

Alternativa sin nube: instalación local con `bash install.sh` y `bash start.sh` ([Instalación y operación](Instalacion_y_operacion.md)). El portal local queda en `http://127.0.0.1:5050` y su contraseña está en `.local/runtime/state.json`.

## 2. Cuentas

Hay 14 cuentas: 7 perfiles por 2 hospitales. Las terminadas en 1 son del Hospital 1; las terminadas en 2, del Hospital 2. **Todas usan la misma contraseña.**

| Cuenta | Perfil | MFA | Aplicación | Para qué sirve en la prueba |
| --- | --- | --- | --- | --- |
| `donor1`, `donor2` | Donante | No | App móvil | Expediente, campañas y citas |
| `operator1`, `operator2` | Operador | No | Portal web y escritorio | Registrar unidades, procesar donaciones, preparar y recibir traslados |
| `medical1`, `medical2` | Médico | **Sí** | Portal web y escritorio | Liberar unidades, solicitudes, dictámenes, reservas y destino final |
| `coordinator1`, `coordinator2` | Coordinador | **Sí** | Portal web y escritorio | Disponibilidad regional y programar traslados |
| `transport1`, `transport2` | Transportista | No | App móvil | Recolección, tránsito y entrega |
| `auditor1`, `auditor2` | Auditor | No | Portal web | Bitácora de auditoría, hallazgos y estado de la plataforma |
| `admin1`, `admin2` | Administrador | **Sí** | Portal web | Usuarios, catálogos, dispositivos y estado de la plataforma |

Cada cuenta entra solo en la aplicación de su perfil. El portal y la consola envían su identificador de aplicación al iniciar sesión (cabecera `X-RedHouse-Client`: `web`, `desktop` o `mobile`); si pruebas una cuenta en otra aplicación, el sistema responde 403 `client_not_allowed` y dice cuál usar. Esa respuesta también es una prueba válida.

### Dónde está la contraseña

En la VM, archivo `/opt/redhouse/.local/compose/state.json`, clave `password`. Si tienes permiso en GCP, léela tú mismo. El comando la imprime solo en tu terminal:

```sh
gcloud compute ssh red-house --project=sistemas-integracion-01 --zone=me-central1-a \
  --command "sudo python3 -c 'import json;print(json.load(open(\"/opt/redhouse/.local/compose/state.json\"))[\"password\"])'"
```

Si no tienes permiso, pídesela a otro integrante en persona o por llamada, no por escrito.

## 3. Segundo factor (MFA) para médico, coordinador y administrador

> **Estado en la VM desde el 19/11/2026 (demo):** el segundo factor está **desactivado** por pedido del equipo
> (`MFA_REQUIRED_ROLES=[]` y los 4 factores registrados inactivos) y el portal ya no muestra el campo de código. Ninguna
> cuenta pide código en la VM. Lo de esta sección aplica a una instalación con MFA activo. Para reactivarlo en la VM:
> `sudo bash /opt/redhouse/.local/compose/quitar_mfa.sh revertir` ([evidencia](../evidencias/entrega-final/gcp-sin-segundo-factor-20261119/RESULTADOS.md)).

Sin factor registrado, estos perfiles reciben «mfa_enrollment_required» al iniciar sesión. No hay pantalla para registrarlo; se hace una sola vez por API.

**Cuentas que ya tienen factor en la VM.** La demostración de correcciones de GCP (`deployment/gcp/prepare_correction_demo.py`) registró factor para `admin1`, `medical1`, `medical2` y `coordinator1`. Sus secretos quedaron en el archivo privado `demo-checkpoint.json` de quien ejecutó esa demostración, fuera de Git. Para usar esas cuentas necesitas ese secreto en tu app autenticadora. Si no lo tienes, no se puede volver a registrar: la API responde 409 `mfa_exists`.

**Cuentas que puedes registrar tú: `admin2` y `coordinator2`.** Necesitas una app autenticadora (Google Authenticator, Microsoft Authenticator u otra TOTP) y `curl`.

1. Pide el desafío. Escribe la contraseña solo en tu terminal:

   ```sh
   curl -s https://34.18.186.116/services/identidad-acceso/api/v1/auth/mfa/enrollment \
     -H "Content-Type: application/json" -H "Idempotency-Key: $(uuidgen)" \
     -d '{"username":"admin2","password":"LA_CONTRASEÑA"}'
   ```

   La respuesta trae `data.secret` y `data.challenge`. El desafío vence en 5 minutos.
2. En la app autenticadora, elige «Ingresar clave de configuración», pon un nombre (por ejemplo «Red House admin2»), pega `secret` y elige «Basada en tiempo».
3. Confirma con el código de 6 dígitos que muestra la app:

   ```sh
   curl -s https://34.18.186.116/services/identidad-acceso/api/v1/auth/mfa/confirm \
     -H "Content-Type: application/json" -H "Idempotency-Key: $(uuidgen)" \
     -d '{"challenge":"EL_CHALLENGE","code":"123456"}'
   ```

   Debe responder `"accepted": true`. Tienes 5 intentos por desafío.
4. Desde ahora, al iniciar sesión con esa cuenta escribe también el código de la app.

**Limitación:** las dos cuentas médicas ya tienen factor. Para probar el perfil médico se necesita el secreto del checkpoint de la demostración. Como alternativa, `admin2` puede crear otra cuenta médica en «Usuarios» → «Crear usuario» y luego registrar su factor con los mismos pasos.

## 4. Primera vuelta: entrar con cada perfil

Abre https://34.18.186.116 → «Acceso institucional» y entra con cada cuenta del portal (`admin`, `operator`, `medical`, `coordinator` y `auditor`). Comprueba que:

- el «Panel principal» solo muestra las opciones de ese perfil;
- un botón de otro perfil aparece desactivado;
- al salir (icono junto a tu nombre) vuelves al acceso;
- con `donor1` o `transport1` el portal rechaza el acceso y dice que uses la aplicación móvil.

Prueba también un intento sin permiso. Con `operator2`, abre el enlace de una unidad del Hospital 1: debe responder que no tienes acceso y no mostrar el folio.

## 5. App Android

La app apunta a `https://34.18.186.116` y no pide la dirección del servidor; la VM debe estar encendida.

1. Consigue el APK. Compílalo desde `apps/mobile` con JDK 17 y Android SDK 35:

   ```sh
   cd apps/mobile && ./gradlew :composeApp:assembleDebug
   ```

   El archivo queda en `apps/mobile/composeApp/build/outputs/apk/debug/composeApp-debug.apk`. Otro integrante también puede pasarte ese archivo.
2. Instálalo en un teléfono Android con «Instalar apps desconocidas» permitido, o en un emulador:

   ```sh
   adb install -r apps/mobile/composeApp/build/outputs/apk/debug/composeApp-debug.apk
   ```

3. Entra con `donor1` (Inicio con siguiente paso, Citas, Campañas, Avisos, Cuenta) y con `transport1` (Inicio con orden activa y acción principal, Traslados, Avisos, Cuenta, «Abrir en mapas»); no piden MFA. Con `operator1` la app debe rechazar el acceso y decir que uses el portal o la consola. Qué ver por perfil: [Manual de usuario, secciones 4 y 8](Manual_de_usuario.md#4-donante).

iOS: se instala desde Xcode en la Mac de Victor. Los perfiles de desarrollo vencen el 24/11/2026.

## 6. Consola de escritorio

Verificada en macOS Intel con Python 3.12; Windows 11 no está verificado.

```sh
cd apps/desktop
python3 -m venv .venv
.venv/bin/pip install -r requirements-macos-lock.txt
.venv/bin/python -m redhouse_desktop
```

Por omisión se conecta a `https://34.18.186.116`. Entra con `operator1`, con un médico y con un coordinador (la barra superior cambia por perfil y el resto de las áreas está en «Más ▾»). Con `donor1`, `transport1`, `auditor1` o `admin1` debe rechazar el acceso. Qué hay en cada área: [Manual de usuario, sección 3](Manual_de_usuario.md#consola-de-escritorio).

## 7. Swagger y monitoreo

- **Swagger** de cada servicio: `https://34.18.186.116/services/<servicio>/docs/`, por ejemplo [Inventario](https://34.18.186.116/services/inventario/docs/). La lista de prefijos está en [deployment/gcp/README.md](../../deployment/gcp/README.md#abrir-el-portal).
- **Iniciar sesión a mano en Swagger.** El login (`POST /api/v1/auth/login` del servicio `identidad-acceso`) exige la cabecera `X-RedHouse-Client`. En «Try it out» elige en ese parámetro el valor que corresponda a la cuenta: `web` para admin, auditor, operador, médico y coordinador; `desktop` solo para operador, médico y coordinador cuando quieras probar la consola; `mobile` para donante y transportista. Si lo dejas vacío responde 400 `client_required`; con un valor que no corresponde al perfil, 403 `client_not_allowed`. Con `curl` agrega `-H "X-RedHouse-Client: web"`. Después copia el `access_token` en «Authorize».
- **Salud** de un servicio: `/services/<servicio>/health/live` y `/health/ready`. Deben responder 200 y mostrar la versión y el estado de PostgreSQL, MongoDB, Redis y almacenamiento.
- **Panel de monitoreo**: entra con `auditor1` (no pide MFA) y abre «Estado de la plataforma». Debe mostrar cada servicio con su estado y su última verificación. Al desplegar «Diagnóstico técnico», que solo ven auditor y administrador, aparecen tiempo medio, disponibilidad de 24 h, errores, dependencia caída, último error y versión.
- **Rutas internas bloqueadas**: `https://34.18.186.116/services/inventario/internal/...` debe rechazarse desde fuera.

## 8. Los tres procesos de punta a punta

Haz cada proceso en orden. Al final de cada uno, entra con `auditor1` → «Bitácora de auditoría» y filtra por la fecha de hoy: debe verse cada paso con su actor. Revisa también «Notificaciones» de los participantes.

### Proceso 1. Solicitud y suministro de sangre (unidad del Hospital 1, paciente del Hospital 2)

| Paso | Cuenta | Dónde | Acción | Resultado esperado |
| --- | --- | --- | --- | --- |
| 1 | `operator1` | Web | «Inventario sanguíneo» → «Registrar unidad» | Unidad en «Cuarentena» |
| 2 | `medical1` | Web | Abrir la unidad → liberar (pide confirmar identidad) | Unidad disponible |
| 3 | `medical2` | Web | «Receptores» → registrar receptor; «Registrar solicitud» | Solicitud abierta |
| 4 | `medical2` | Web | En la solicitud: «Evaluar candidatos» → «Dictamen del candidato» → «Autorizar reserva» | Reserva autorizada; si queda pendiente, «Reanudar operación», nunca otra reserva |
| 5 | `coordinator1` | Web o escritorio | «Traslados y custodia» → «Planear traslado» con `transport1` | Traslado planificado |
| 6 | `operator1` | Web | En el traslado: «Documentar: Preparado» | Listo para recolección |
| 7 | `transport1` | App Android | «Traslados» (o la orden activa en «Inicio») → abrir la tarea → recolección, inicio de tránsito y entrega (escanear, sello, contraparte, confirmar) | Estado «Entregado»; el mapa muestra la posición |
| 8 | `operator2` | Web o escritorio | Aceptar la recepción | Traslado aceptado |
| 9 | `medical2` | Web | «Registrar destino» | Unidad retirada y solicitud cerrada |

### Proceso 2. Coordinación de órgano

Igual que el proceso 1, con estas diferencias:

- el recurso es un órgano con perfil térmico de conservación;
- `medical2` registra el laboratorio HLA del receptor (escritorio: «Muestras» / «Resultados») y en la solicitud usa «Documentar constancia externa»;
- durante el traslado, `operator1` registra lecturas de temperatura en «Conservación». Una lectura fuera de intervalo bloquea la unidad hasta que un médico la revise.

Referencia de una ejecución completa: [cierre iOS B](../evidencias/entrega-final/e2eb-ios-cierre-20261117/RESULTADOS.md).

### Proceso 3. Donación voluntaria y procesamiento

| Paso | Cuenta | Dónde | Acción | Resultado esperado |
| --- | --- | --- | --- | --- |
| 1 | `operator1` | Web | «Crear campaña» y «Crear horario», luego publicar | Campaña visible en la página pública |
| 2 | `donor1` | App Android | «Campañas» → «Buscar horarios disponibles» → reservar | Cita en «Mis citas»; aviso en «Avisos» |
| 3 | `operator1` | Web | Inscripciones: confirmar y registrar asistencia | Asistencia registrada |
| 4 | `medical1` | Web | «Donantes»: «Registrar consentimiento» y evaluación | Donante evaluado |
| 5 | `medical1` | Escritorio | «Donaciones» → «Registrar colecta» | Donación recolectada |
| 6 | `operator1` | Escritorio | «Documentar procesamiento» y en «Inventario» → «Registrar derivados» | Derivados en cuarentena |
| 7 | `operator1` → `medical1` | Escritorio | Muestra y resultado; el médico revisa y libera | Resultado autorizado y unidad disponible |
| 8 | `operator2` | Web | Abrir la unidad del Hospital 1 | Acceso denegado (403) |

Referencia: [Android C consultado desde web](../evidencias/entrega-final/e2ec-android-web-20261117/RESULTADOS.md).

## 9. Fallas que puede pedir el profesor

Estas pruebas no se hacen en la VM sin coordinarse antes, porque afectan a todo el equipo.

| Qué se pide | Cómo provocarlo (instalación local) | Qué debe pasar |
| --- | --- | --- |
| Detener un microservicio | `bash components.sh detener alertas`, luego `reiniciar alertas` | Los otros 11 siguen en 200; el aviso pendiente llega al reiniciar |
| Dependencia síncrona caída | `bash components.sh detener identidad_acceso` | Login falla; una operación que la consulta responde 503 `dependency_unavailable` sin colgarse |
| Revocar un token | Cerrar sesión y reusar el token anterior | 401 |
| Intento sin permisos | `operator2` sobre un recurso del Hospital 1 | 403, sin datos |
| Sobrecarga | Ráfaga de peticiones con la misma cuenta | 429 por cuota |

Evidencia y guion reproducible: [pruebas de fallas del 18/11](../evidencias/entrega-final/fallos-consigna-20261118/RESULTADOS.md).

## 10. Si algo falla

- Anota la hora, la cuenta, la pantalla y el mensaje exacto. **No** captures la contraseña ni el código MFA.
- No repitas una acción que no respondió: usa «Reanudar operación» u «Operaciones pendientes» ([Manual de usuario, sección 11](Manual_de_usuario.md#11-si-algo-no-sale-como-esperabas)).
- Revisa si ya es un límite conocido ([Manual de usuario, sección 12](Manual_de_usuario.md#12-límites-conocidos)) o una incidencia registrada ([Registro de incidencias](../entrega-final/Registro_incidencias.md)).
