# Traspaso de Red House para Claude Code y el Equipo 01

Corte del 17/11/2026, Monterrey. **Entrega prevista el 23 de noviembre de 2026.**
El usuario pidió pausar el trabajo nuevo y continuar desde otra PC. El avance ronda 90 % según dirección, una estimación de esfuerzo
técnico. La aceptación integral sigue abierta.

### Texto listo para pegar en Claude Code

> Continúa Red House desde este traspaso. Lee CLAUDE.md, AGENTS.md, PROJECT_STATUS.md y HANDOFF_CLAUDE_CODE.md. Soy nuevo en el proyecto: explícame brevemente qué falta y qué necesitas de mi equipo o mis cuentas. Detecta mi sistema y herramientas; instala las dependencias necesarias que puedas instalar de forma segura y reversible. Solicita mi intervención únicamente para autenticación, permisos del equipo, licencias o decisiones que realmente falten. Recupera y verifica el paquete privado antes de continuar casos existentes. Empieza por el error «Ver detalle» del recordatorio Android; conserva la evidencia, evita repetir operaciones ya aceptadas y trabaja con pruebas dirigidas y commits revisables. Mantén las decisiones de seguridad, datos y alcance del documento. No asumas que conocer una credencial o tener permisos de nube autoriza a borrar datos o publicar cambios nuevos sin revisar su alcance.

## 0. Qué estamos construyendo

**Proyecto 6, Equipo 01.** Red House coordina una red regional de bancos de sangre y donación de órganos. Integra inventarios,
solicitudes, pruebas, candidatos, reservas, traslados, custodia y auditoría. El sistema trabaja con autorización institucional y
revisión humana. Los escenarios de entrega son sintéticos y cualquier habilitación clínica requiere aprobación externa.

- **Web:** Flask/Jinja2 con portal público y privado. El backend monolítico ejecuta sus módulos y conserva autonomía respecto de las
  API. Es el entorno de coordinación y consulta regional.
- **Microservicios:** 12 servicios independientes, 11 de dominio y Monitoreo. Flask versionado, contratos OpenAPI
  JSON y XML/XSD. El dominio de origen es dueño de su operación y corrige por eventos versionados.
- **Móvil Android/iOS:** Kotlin Multiplatform y Compose Multiplatform. Consume JSON por HTTPS/WSS. Donante ve feed de campañas y
  citas. Transportista ve tarea y siguiente acción con mapa protagonista. QR, cámara, GPS, almacenamiento y ciclo de vida tienen
  componentes por plataforma. El gateway se fija al compilar normal/Lab. Conserva la interfaz sin campo de gateway.
- **Escritorio:** PySide6/Python para procesos internos con XML/XSD. Cubre, según rol, recepción/expediente, laboratorio,
  inventario, conservación, reportes y auditoría. Verifica sus operaciones reales y específicas con el artefacto de cada plataforma
  reclamada.

Identidad emite JWT. El backend valida sesión, rol, revocación y ámbito en Redis. PostgreSQL conserva el estado transaccional por
propietario en base compartida. MongoDB mantiene proyecciones documentales, eventos y telemetría. Redis también administra caché,
coordinación temporal y cuotas. El almacenamiento operativo es LOCAL privado. GCS es opcional para operar y conserva acreditación
académica separada. Los clientes consumen API, con JSON móvil y XML de escritorio. El acceso a bases y Redis corresponde a los
servidores. Inicia por el [informe técnico](documentation/markdowns/Reporte_tecnico_final.md) y el
[índice documental](documentation/README.md).

## 1. Llegada a una PC nueva

1. Accede con tu propia cuenta autorizada a `https://github.com/victor-berlanga/Red-House.git`. Rama de trabajo `entrega-final`.
   Para un clon nuevo, `git clone --branch entrega-final https://github.com/victor-berlanga/Red-House.git`. Si ya hay checkout,
   conserva cambios ajenos. Registra `git status --short --branch`, `git log -10 --oneline` y `git rev-parse HEAD`. Usa el commit
   final asentado en la sección 7 cuando esté disponible.
2. Lee primero [AGENTS.md](AGENTS.md) y [PROJECT_STATUS.md](PROJECT_STATUS.md). En este último prevalece el corte más reciente que
   sustituye explícitamente un pendiente histórico. `README.md` todavía muestra cortes históricos de backend/VM. Si las referencias
   de usuario a RTK o caveman no existen en tu PC, trabaja en español conciso con herramientas equivalentes. Si el repositorio ya
   tiene índice CodeGraph, úsalo primero para localizar código. La creación del índice es decisión del usuario.
3. Consulta la [matriz vigente](documentation/entrega-final/continuidad/Matriz.md), el
   [informe editable](documentation/markdowns/Reporte_tecnico_final.md) y los
   [prompts de entrega](stuff/prompts/entrega-final/README.md). Revisa 00, 04, 07, 08 y 09 según el bloque. La consigna original y
   retroalimentación estaban en la carpeta hermana privada `integracion/stuff`, especialmente `texto_bandeja_entrega_final.txt`,
   `proyecto.txt` y `retroalimentacionSegundoParcial.txt`. Pide copia autorizada si falta una fuente. Los prompts versionados
   recogen las instrucciones operativas y sus aclaraciones.
4. Usa esta prioridad. La consigna fija el alcance académico y el prompt 00 incorpora decisiones posteriores. Los prompts 01–09
   especifican backend, reglas, portal, móvil, escritorio, continuidad, pruebas, expediente y rastreo. `PROJECT_STATUS.md`, matrices
   y recibos determinan qué se comprobó. Conserva antecedentes y resultados fallidos.
5. Antes de tocar un entorno, separa clon limpio de continuación de un fixture conservado. Un clon sirve para validar instalación
   independiente. Para concluir un caso ya iniciado se necesitan los mismos datos y recibos, mediante la sección 5. Si falta esa
   evidencia, avanza con tareas independientes y deja el caso pendiente.

### Primeros 30 minutos

- **Min 0–10.** Identifica sistema y arquitectura con `uname -s -m` en Mac/Linux o
  `[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture` en PowerShell. Comprueba `git --version`, el acceso a Git
  con tu cuenta, rama/HEAD y los archivos de la lista anterior. Ubica el paquete GCP en la sección 7 y confirma si necesitas el
  fixture.
- **Min 10–20.** Ejecuta comprobaciones de versión según tu bloque: `python --version`, `docker version`, `docker compose version`,
  `java -version`, `adb version`, `adb devices -l`. En Mac para iOS, `xcodebuild -version` y revisión de equipo/perfiles desde Xcode
  con la cuenta autorizada. Para nube, `gcloud auth list --filter=status:ACTIVE --format="value(account)"` y
  `gcloud config get-value project`. Usa los comandos de instalación de la sección 2 y las guías de cada plataforma. No inicies un
  motor para comprobar que el binario está instalado.
- **Min 20–30.** Elige un único objetivo con dueño, criterio y evidencia faltante. En Windows puedes trabajar Android, escritorio
  nativo y backend vía Docker/WSL. Xcode, firma y ensayo en iPhone quedan con el Mac autorizado. Si solo haces documentación, lee y
  enlaza los recibos. Si vas a reanudar Android C, verifica el respaldo, el artefacto Lab y el aviso exacto antes de conectar la
  app.

## 2. Herramientas y dependencias

Instala de forma autónoma las dependencias compatibles, necesarias y reversibles, preferiblemente en el entorno de proyecto o venv.
Revisa primero los locks, el wrapper y las guías versionadas. Conserva las versiones del corte aplicable y documenta el sistema,
arquitectura y versiones probadas. Las cuentas, MFA, licencias, permisos de nube, acceso a equipos y firma Apple requieren a sus
titulares. Mantén secretos fuera de Git, argumentos, logs y capturas. La sección 6 delimita el respaldo privado del Lab.

| Componente | Qué preparar y cómo comprobarlo |
| --- | --- |
| Backend/web | Python 3.12 según [instalación](documentation/markdowns/Instalacion_y_operacion.md), dependencias de [servicios](apps/services/README.md) y [web](apps/web/README.md). Si corres sin Docker, instala las versiones de PostgreSQL, Redis, MongoDB y las herramientas exigidas por la guía del entorno elegido. ClamAV/ClamD solo cuando el ensayo implique análisis real. En Windows, los lanzadores de servidor `.bat` invocan WSL/Ubuntu. |
| Docker y clon | Docker Engine o Docker Desktop según plataforma y Compose v2. Sigue [deployment/README.md](deployment/README.md). Trabaja con proyecto/volúmenes/puertos nuevos y aislados en el clon de verificación. `bash install.sh`, `bash start.sh`, `bash components.sh estado` y `bash stop.sh` son la ruta documentada para runtime local, nunca contra el fixture conservado. |
| Android | JDK 17, Platform SDK 35, Build Tools 34.0.0 y Gradle Wrapper del repo según [guía móvil](apps/mobile/README.md). Configura `ANDROID_HOME` o `local.properties` privado. AVD según host. El emulador de evidencia era AOSP API 30 x86_64; valida compatibilidad de imagen y arquitectura en el equipo nuevo. Desde `apps/mobile`: `./gradlew :composeApp:testDebugUnitTest :composeApp:assembleDebug`. En Windows usa `gradlew.bat`. Android en emulador es válido. |
| iPhone | Mac con Xcode completo, XcodeGen según [guía móvil](apps/mobile/README.md#ios), equipo de firma Apple autorizado e iPhone físico disponible. Usa perfiles vigentes, fecha y arquitectura comprobadas. La guía fija Xcode/XcodeGen del corte verificado y las versiones Kotlin/Gradle. Prueba firma e instalación del artefacto realmente usado. No descargar Simulator. La PC Windows puede cubrir Android, servidor o escritorio; el trabajo físico iOS requiere el Mac/iPhone autorizados. |
| Escritorio | PySide6 en venv, [guía escritorio](apps/desktop/README.md), `requirements.txt`, `requirements-build.txt` y lock específico macOS Intel donde aplique. Punto de entrada `python -m redhouse_desktop` desde `apps/desktop`. En Windows 11 comprobar con Python/Qt nativos y dependencias de ese destino. ARM/Linux conservan evidencia separada. |
| Edición y nube | [Dependencias editoriales](scripts/requirements-docs.txt) y LibreOffice/`soffice` para PDF. [Guía GCP](deployment/gcp/README.md), Google Cloud CLI, OpenSSH y autenticación con la cuenta propia autorizada. Usa GCS solo en la prueba académica separada que lo requiera. La operación actual usa LOCAL privado. |

## 3. Estado comprobado y cortes a conservar

- **Git.** `717add0` exportó el catálogo físico del esquema 21 y actualizó el informe Markdown. El catálogo real tiene 117 tablas y
  227 índices. Word/PDF del catálogo, 74 páginas Carta, revisión aprobada. **El informe técnico principal aún requiere su
  exportación y revisión final** tras incorporar Android C y la evidencia de clon limpio. `429dd90` documentó publicación GCP de
  custodia/presentación y la renovación TLS.
- **GCP.** Único destino autorizado: proyecto `sistemas-integracion-01`, instancia `red-house`, zona `me-central1-a`, VM ID
  `2861822465669755197`, IP pública `34.18.186.116`. Despliegue 30 contenedores saludables, 27 conservados al actualizar Transporte
  A/B y web, LOCAL/monolito/esquema 21, Inventario N+1 preservado. Certificado vigente al corte hasta **24/11/2026 14:08:33 UTC**,
  cubre el día local 23. Certbot emitió una vez. El wrapper original conserva FAIL por `0644` a `0600` del archivo de renovación,
  con contenido y opciones iguales. La conciliación de solo lectura y retirada de la clave SSH temporal propia aprobaron. Mantén el
  intento original y su corte TLS anterior.
  [Evidencia GCP](documentation/evidencias/entrega-final/gcp-custody-clock-lab-labels-20261117/RESULTADOS.md)
- **Casos sintéticos.** Reutiliza cierres iOS A/B, Android A/B e iOS C según sus recibos y límites. En Android C, la reserva
  conservada y el tramo Qt→web de colecta/linaje/laboratorio ya tienen evidencia. No repetir operaciones. Las lecturas Chrome del
  ABO y del cierre web quedaron acreditadas por separado.
  [iOS A](documentation/evidencias/entrega-final/e2ea-ios-cierre-20261117/RESULTADOS.md) ·
  [iOS B](documentation/evidencias/entrega-final/e2eb-ios-cierre-20261117/RESULTADOS.md) ·
  [Android C Qt/web](documentation/evidencias/entrega-final/e2ec-android-web-20261117/RESULTADOS.md)
- **Android C reciente.** Cita/Perfil vistos en AVD, con recibos privados. El cupo disputado registró rival HTTP 201, Android HTTP
  409 `slot_full`, una cita persistida y aviso comprensible. El oráculo de negocio aprobó. El wrapper conserva **FAIL de sincronía**
  por separación de 1.157 ms respecto de un umbral privado de 1 s. Prompt 07 exige un solo ganador en el último cupo. Conserva el
  límite de no simultaneidad en servidor y el criterio aparte de concurrencia. El worker de recordatorio corrió una vez, con
  evento/alertas y auditoría concordantes. Avisos mostró el recordatorio; **Ver detalle presentó «Respuesta no válida del
  servicio»**. Falta corregir y volver a abrir solo ese aviso ya persistido. Recuperación tras reinicio sigue pendiente.
  La reserva nativa de las 18:19 también acreditó renovación natural: 401 inicial, renovación y 201 automático con la misma
  clave de idempotencia, una sola cita y un único toque. El observador que se detuvo en el primer 401 conserva su FAIL;
  la conciliación posterior y la tarjeta real confirman la operación. La familia Android cerró en SQL/Redis y quedaron cero activas.
  [Expediente Android C](documentation/evidencias/entrega-final/mobile/android-c-cierre-20261117/RESULTADOS.md)
- **MOV-01 iPhone.** Usuario confirmó desafío MFA, entrada manual de `medical1` y cierre. La conciliación de solo lectura terminó
  con código 0: familia anterior de `transport1` y única familia nueva de `medical1` cerradas en PostgreSQL y ausentes en Redis. Se
  comprobó LOGIN/LOGOUT de `medical1`. No reutilices un TOTP ni publiques el código. Renovación, expiración y cambio de cuenta
  mantienen su alcance propio. La evidencia Android histórica de desafío/TOTP conserva el timeout de instrumentación. MFA móvil
  aplica aquí a MEDICAL y COORDINATOR. Reautenticación solo donde la operación autorizada la exige.
  [Evidencia MFA iPhone](documentation/evidencias/entrega-final/mobile/ios-mfa-cierre-20261117/RESULTADOS.md)
- **Carga y distribución.** Lecturas con espera de 4–6 s, 24/36/6 sesiones sobre seis identidades, aprobadas con 1.334/981/173 GET y
  cero errores. Conserva los 244 HTTP 429 del intento previo y el `FAILED_CLEANUP` original de carga finita, conciliado por
  separado. Mac Intel final 02, build/smoke y ZIP aprobados, 163 fuentes y 59 contratos. No cubre instalación limpia ni recorrido de
  negocio dentro del paquete. Firmas iOS normal/Lab renovadas hasta el 24/11; normal se actualizó sin abrir.
  [Carga](documentation/evidencias/entrega-final/carga-lecturas-paced-20261117/RESULTADOS.md) ·
  [Paquete Mac](documentation/evidencias/entrega-final/desktop/paquete-macos-20261117-02/RESULTADOS.md)

## 4. Orden de reanudación

1. **Android C, primero.** Diagnostica el detalle de Avisos con CodeGraph si está disponible. Coteja ruta y esquema JSON, status,
   envelope y parseo del cliente en el contexto exacto del aviso validado. Separa contrato del backend, validación del cliente y
   estado de UI. Corrige la causa con regresión dirigida. Reusa el aviso del worker y prueba su apertura y la recuperación de la
   sesión/app tras reinicio según las guardas vigentes. No repitas worker, reserva, último cupo ni Qt/web para resolver un GET.
   Conserva evidencia anterior y posterior y valida las negativas que aún correspondan al escenario sin repetir positivos.
2. **Cierre nativo y accesibilidad.** Incorpora la conciliación MFA iPhone ya verificada. Consulta MOV/CONT para
   sesión/renovación/expiración/revocación, permisos, durabilidad y roles concretos aún sin evidencia. Cubre TalkBack, VoiceOver y
   escritorio con recorridos necesarios y evidencia real de cada plataforma. El prompt 07 pide A/B/C en Android emulador y iPhone
   físico, y funciones autorizadas por rol. Usa la evidencia previa para evitar repetir todos los cruces rol × acción × variante.
3. **TRACK/WSS y continuidad.** Pendientes específicos: mapa iOS nativo y correlación/latencia hasta los mapas aplicables,
   interrupciones y recuperación, autorización durante sockets, concurrencia y consumidores lentos. El positivo iOS B ya cuenta.
   Coteja I06 y respaldo/restauración con RTO/RPO. Esos resultados, Locust transaccional multiperfil y
   estrés/saturación/recuperación se acreditan aparte de REST paced. Si falta un ensayo, fija alcance y límites antes de medir.
4. **Distribución y final académico.** Clon limpio en la revisión de entrega, escritorio instalable y recorrido aplicable en Windows
   11. Linux es adicional. Integra evidencia nueva al informe y genera Word/PDF una vez, con revisión de páginas conforme a la
   [sección editorial](documentation/markdowns/Reporte_tecnico_final.md#16-manuales-artefactos-y-reproducción). Prepara la
   [demostración](documentation/entrega-final/continuidad/Demostracion_final.md), inventario y cierre de matrices. El equipo aporta
   video, presentación, Ubiquitous y reflexiones/entregas individuales.

Push físico FCM/APNs y aprobación clínica siguen como dependencias externas acordadas. Bandeja, adaptadores y enlaces autorizados sí
se verifican. iOS no garantiza ejecución permanente ni callback BGAppRefresh durante el ensayo. GPS externo es opcional. Mantén
separados estado académico, autorización clínica, comportamiento físico y fallos del arnés.

### Rutina de trabajo del agente y del equipo

- Una persona o agente dirige y mantiene la matriz y el objetivo actual. Si la sesión permite agentes y el usuario lo autorizó,
  divide lecturas o comprobaciones cortas entre dos o tres agentes. Reserva el razonamiento más fuerte para integración,
  autorización y revisión final. Acota cada encargo y evita que dos agentes escriban el mismo archivo.
- Corre un único escenario pesado a la vez. Agrupa compilaciones que compartan entradas. Si ya existe un recibo aplicable, úsalo y
  repite solo por un cambio, fallo o duda concreta. Conserva los intentos fallidos. Antes de atribuir un defecto al producto, separa
  contrato, cliente, runtime y arnés.
- Antes de declarar un bloque terminado, verifica criterio y evidencia. En UI observa la pantalla real y el comportamiento. Una
  compilación o captura sintética no sustituye el recorrido. Usa una prueba dirigida o regresión proporcional, revisa el diff y
  actualiza `PROJECT_STATUS.md` y matriz aplicable. Haz un commit por bloque comprobado, con resultado y límites.
- En cada corte indica qué pasó, qué sigue y qué depende de acceso o acción humana. Nunca deduzcas un PASS de la falta de un error
  registrado. No envíes mensajes, publiques ni concedas acceso por iniciativa propia.

## 5. Continuar los mismos datos y conservar evidencia

El checkout Git basta para leer código, docs y evidencia pública. El inventario privado de origen
`.local/checkpoints/INVENTARIO-TRASPASO.md` identifica insumos, portabilidad y exclusiones para preparar una copia autorizada.
`.local` y temporales del Mac **no viajan con Git**. En otra PC pide al responsable el paquete saneado o una restauración privada
autorizada. Usa rutas relativas a tu checkout y asigna ubicaciones locales de trabajo. Los launchers privados originales incluyen
guardas de ruta/usuario/PID. Léelos y vuelve a vincular la configuración revisada al host nuevo. Respeta propietario, puerto,
ca/host, perfil ACADEMIC, `TESTING=False`, proveedor LOCAL, base y hash del launcher. No desactives controles para trasladar el
ensayo.

| Qué recuperar | Ubicación relativa en el Mac de origen |
| --- | --- |
| Plan/oráculos Android C y launcher LOCAL/WSS | `.local/artifacts/mobile/android-c-close-prepared-20261117/`. Revisar `VENTANA-MINIMA.md`, `PLAN.md` y `serve_preserved_local_wss_arrivals.py`. Los ejecutores de setup/carrera/worker sirven como evidencia de las acciones consumidas. |
| Cupo y aviso Android C | `.local/artifacts/mobile/android-c-last-slot-race-20261117-01/{driver,oracle}.private.json`, `android-c-appointment-profile-20261117-01/` y `android-c-reminder-worker-20261117-01/` bajo la misma raíz móvil. Prioriza `reminder-oracle.private.json`, `worker-once.private.json` y las capturas de aviso/detalle fallido. El setup original dejó una familia abierta al omitir `Idempotency-Key`; el cierre propio pasó por separado en `android-c-last-slot-owner-cleanup-20261117-01/receipt.private.json`. |
| MFA iPhone | `.local/artifacts/mobile/ios-mov01-mfa-preflight-20261117-01/`. `preflight.private.json` registra dos identidades, delta esperado y ruta privada al factor. `reconcile.py --both` verifica el cierre usando el ready del Mac/PID 3416 y sus helpers, mediante `apps/services/.venv/bin/python -B` en el host unido a ese fixture. Si el host se apagó o cambió PID, usa recibo ya producido o restaura y revalida las guardas. El factor queda con su titular. |
| Ready actual y cruce 04/07 | `.local/artifacts/e2eb-preserved-20261116/android-c-passive-20261117-01/runtime-ready.json` y `.local/artifacts/documentation/pending-04-07-consolidation-20261117/{PENDIENTES,CRUCE-PROMPTS}.md`. Ready del trabajo original: fixture PID 3416 y listener 18443 en el Mac. Es identificación histórica, no orden de arranque ni PID reutilizable. |
| Copias frías históricas | `.local/checkpoints/20261117-0013/`: `red-house-ms-tests-kojcusww`, `rh-load-c92ed10k`, `fixtures.json`, manifiestos SHA-256 y `preparados/`. Son anteriores a resultados recientes. El [procedimiento de pausa](documentation/entrega-final/continuidad/Pausa_20261117.md#copia-duradera-para-reinicio) identifica guardas y copias, con otros pasos de negocio ya consumidos. Recupera preferiblemente la copia fría final que incluya Android C. |
| TLS/SSH | `.local/gcp/tls-renewal-20261117-01/`, `.local/gcp/tls-reconcile-20261117-01/`, `.local/gcp/custody-clock-lab-labels-20261117-run/access/access-cleanup.json`. El backup TLS privado de la VM queda bajo control de su administrador. |

Verifica fecha y hashes de la copia fría final, detención limpia de sus motores y ausencia de un fixture ya existente en el destino.
No arranques el archivo maestro de respaldo. Restaura en ubicación aislada con guardas revisadas. Los directorios físicos de motores
y el AVD dependen de versión, host y arquitectura. Si hace falta un export lógico compatible, coordínalo con el titular sobre una
copia autorizada y verifica relaciones/versiones/objetos antes de usarlo. Nunca restaures encima de datos vigentes ni reinicialices,
resembres, cambies relojes/caducidades o repitas estados aceptados. Retira únicamente sesiones y procesos propios conforme al recibo
aplicable.

## 6. Acceso GCP y descarga del traspaso

El usuario autorizó el push de la rama de entrega y la subida del paquete a GCP. La política del proyecto
`sistemas-integracion-01` confirma los mismos cinco roles para `alberto.reyna@udem.edu` y `areyna@strategyiqs.com`:

- `roles/admin`
- `roles/compute.instanceAdmin.v1`
- `roles/compute.osAdminLogin`
- `roles/iam.serviceAccountUser`
- `roles/iap.tunnelResourceAccessor`

La asignación de Owner por CLI fue rechazada con `SOLO_MUST_INVITE_OWNERS`. Los roles anteriores sí quedaron verificados
en IAM. Queda a cada compañero comprobar el inicio de sesión con su cuenta. El encargo comprende el proyecto indicado,
incluida la VM `red-house`.

### Descargar desde otra PC

Usa Google Cloud CLI con tu propia cuenta. El bucket exige acceso privado con **Public Access Prevention** (enforced)
y **Uniform bucket-level access**. Conserva ese acceso y evita generar o publicar enlaces firmados.

Primero ejecuta `gcloud auth login alberto.reyna@udem.edu`, o sustituye esa dirección por `areyna@strategyiqs.com` si es tu cuenta.
El titular completa la autenticación en el navegador; no entrega contraseña, códigos MFA ni archivos ADC a la IA.
Comprueba la cuenta activa con `gcloud auth list`. Los comandos de VM incluyen proyecto y zona explícitos para evitar otro destino.
Para iOS, instala Xcode completo desde Apple en un Mac compatible y abre **Xcode → Settings → Accounts** con una cuenta de firma
autorizada. El titular completa licencias, autenticación y permisos del iPhone. Las Command Line Tools no sustituyen Xcode completo.
No se requieren cuentas nuevas de FCM/APNs: la recepción push real conserva el pendiente externo acordado.

1. Consulta `RELEASE.json` y `TRANSFER_VERIFIED.json` del prefijo de la sección 7. El primero identifica revisión y contenido;
   el segundo acredita que los objetos remotos coinciden. Si falta alguno, verifica con el responsable antes de usar el paquete parcial.
2. Descarga el prefijo en un directorio privado. Estos comandos cubren Bash/zsh y PowerShell, respectivamente.

   ```bash
   gcloud storage cp --recursive "gs://red-house-evidencias-sistemas-integracion-01/handoff/20261117-2a1bf7fd/" ./traspaso
   ```

   ```powershell
   gcloud storage cp --recursive "gs://red-house-evidencias-sistemas-integracion-01/handoff/20261117-2a1bf7fd/" .\traspaso
   ```

3. Comprueba SHA-256 con `shasum -a 256 -c SHA256SUMS` en Mac, `sha256sum -c SHA256SUMS` en Linux o
   `Get-FileHash -Algorithm SHA256 <archivo>` en PowerShell y coteja con el manifiesto. Extrae en un directorio aislado.
4. Si tu cuenta aún carece de GitHub, usa `git clone -b entrega-final red-house.git.bundle Red-House` desde la carpeta descargada
   tras cotejar que el bundle figura en el recibo. El archivo de fuentes sirve para consultar el corte sin historial.
5. La guía de la VM quedará en `/opt/redhouse/handoffs/20261117`. Usa el acceso propio de OS Login y comprueba la VM antes
   de entrar con `gcloud compute instances describe red-house --project=sistemas-integracion-01 --zone=me-central1-a --format="value(id)"`.
   El resultado coincide con el ID documentado en la sección 3.

El paquete previsto incluye `red-house.git.bundle`, fuentes, ZIP Mac final 02, APK Lab exacto de aproximadamente 14 MB,
evidencia y continuidad privada. Lleva respaldos fríos y exportación lógica. **La restauración en otra PC aún no está probada.**
Identifica la CA de Lab y artefacto aplicables antes de ejecutar. No uses ese APK para deducir la aceptación de otro build.

- `red-house.git.bundle` conserva la rama y su historia; `source.tar.gz` contiene el mismo corte de archivos versionados.
- `private-continuity.tar.gz` conserva herramientas, recibos, imágenes y configuración sintética bajo las rutas relativas `.local/`.
- `lab-cold.tar.gz` y `load-cold.tar.gz` son copias físicas frías; no son intercambiables entre plataformas sin validación.
- `portable-lab.tar.gz` contiene PostgreSQL con roles, archivo MongoDB, snapshot Redis y `PORTABLE-LAB.md`. Sigue esa guía en un
  destino aislado. No es directamente el formato de `deployment/gcp/restore.py`; no lo restaures sobre la VM operativa.
- `fuentes-academicas.tar.gz` incluye la consigna original y retroalimentación para que no dependas del Mac del autor.
- El APK Lab sigue apuntando a la dirección de red del laboratorio original. En otro equipo debes adaptar configuración de
  compilación, host y SAN del certificado, conservar la CA pertinente y verificar el cambio de entorno antes de instalar.

### Qué puede contener cada canal

- **Git, evidencia pública y paquetes para difusión:** fuentes, documentación y recibos saneados, sin credenciales ni datos sensibles.
- **Archivo privado Lab de este prefijo:** las copias autorizadas pueden contener configuraciones, credenciales y factores
  sintéticos del laboratorio. Trátalos como secretos. No los publiques, reenvíes ni incorpores a Git. Quedan excluidos Apple,
  ADC/GCP y SSH personal. Accede con tu propia identidad y conserva el material únicamente en el destino autorizado.

## 7. Estado del traspaso al cerrar la pausa

| Elemento | Ubicación o estado |
| --- | --- |
| Push | Rama `entrega-final`. `RELEASE.json` identifica el commit y su comprobación contra GitHub. Coteja `git rev-parse HEAD` después de clonar. |
| Paquete privado GCP | `gs://red-house-evidencias-sistemas-integracion-01/handoff/20261117-2a1bf7fd/`. Leer `RELEASE.json`, `TRANSFER_VERIFIED.json` y `SHA256SUMS` para comprobar contenido, publicación y huellas. |
| Guía VM | `/opt/redhouse/handoffs/20261117`: guía y manifiestos. Los respaldos grandes se guardan en el bucket privado para conservar espacio de la VM operativa. |
| IAM | Políticas de ambas cuentas verificadas con los cinco roles de la sección 6. Inicio de sesión real de cada compañero pendiente. |
| Estado local | Las sesiones propias de Android e iOS cerraron. El AVD y el runtime Lab se apagaron con cierre PASS. Se preservaron los datos y respaldos para la nueva PC. Clon limpio final y restauración en destino conservan sus criterios. |

Empieza por lo verificable en Git o el bundle. Conserva la pausa de operaciones de negocio hasta la nueva instrucción.
