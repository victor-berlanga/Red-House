# Medición prevista — 13/11/2026

Este documento fija el experimento antes de ejecutarlo. No contiene resultados ni declara cumplida la etapa 07. Responsable: dirección/integración. El ensayo inicial de seis perfiles durante doce segundos solo valida el arnés, su negociación JSON/XML y el ciclo de sesión.

## Entorno y datos

Laboratorio local desechable y exclusivo, con PostgreSQL, MongoDB, Redis y los servicios reales. Nunca apuntar la carga a la instalación GCP compartida. Registrar versiones, commit, hashes de fuentes realmente usadas, configuración y procesos antes de cada corrida. En este Mac Intel de 16 GB no ejecutar a la vez Gradle, emulador, Xcode o ClamD. La generación y el servidor comparten equipo; sus tiempos no representan capacidad de Compute Engine.

Escala propuesta: 20.000 expedientes sintéticos, 100.000 recursos y 1.000.000 de eventos utilizados por consultas, reconstrucción o monitoreo. Fijar semilla, instante de referencia, distribución por institución/estado/fecha y relaciones antes de generar. La preparación directa de filas no acredita registro por la API ni aprobación clínica. Primero verificar 1% de la escala y extrapolar únicamente su coste de almacenamiento para decidir si cabe el conjunto; nunca extrapolar tiempos de respuesta como resultados medidos. Conservar el conteo y motivo si se necesita una escala menor.

Límite local del experimento: reservar al menos 3 GiB libres, mantener datos propios dentro de 1,5 GiB y no cambiar memoria, pools o timeouts del producto para obtener un resultado favorable. Si se alcanza un límite, detener la fase, conservar sus fallos y registrar que el nivel superior no se ejecutó. El criterio controla recursos del equipo, no define un SLA clínico.

## Secuencia

1. Prueba funcional del arnés: seis usuarios, dos incorporaciones por segundo, doce segundos, una rotación temprana forzada por usuario y revocación al salir. Exigir cero fallos, seis inicios, seis renovaciones y seis revocaciones. No es una prueba del vencimiento JWT ni una medición de capacidad.
2. Completar flujos transaccionales por perfil con recursos propios y respuestas anteriores: donante/citas, banco/inventario, médico/solicitudes-evaluación-reserva, coordinación/traslados y transporte/custodia. Ante respuesta incierta no repetir una escritura con otra clave. Contabilizar intentos, confirmaciones y estados pendientes al terminar.
3. Con dataset fijo y una versión estable, ejecutar niveles 6, 12 y 24 usuarios. Cada nivel: 30 s de calentamiento y 120 s de carga medida, pausa aleatoria de 0,5–1,5 s entre recorridos. Mantener la distribución por rol y documentar si varios usuarios comparten cuenta; ese caso no simula personas independientes.
4. Comparación de caché: repetir el nivel de 12 usuarios alternando caché activa y `Cache-Control: no-cache`, dos corridas por condición. Redis de autorización permanece activo. Registrar HIT/MISS/BYPASS y estado inicial de cachés, sin llamar a la condición «sin Redis».
5. Estrés acotado: 36 usuarios durante 60 s solo si 24 usuarios no superaron límites del equipo. Recuperación: volver a 6 usuarios durante 60 s. Un fallo o una saturación observada es resultado, no motivo para ocultar peticiones ni cambiar el criterio.

Objetivos académicos iniciales: menos de 1% de errores inesperados, p95 de lecturas menor de 2 s y de transacciones confirmadas menor de 5 s en los niveles sostenidos. Se reportarán incumplimientos por endpoint y causa; no se cambiarán después de medir. Respuestas de conflicto intencionadas se separan de fallos de infraestructura y nunca se cuentan como transacciones confirmadas.

## Registro y límites

Conservar CSV de Locust, series temporales y configuración sin credenciales; media/mediana/p95/p99, peticiones y transacciones por segundo, errores, endpoints lentos, CPU/RSS del generador y servicios, conexiones, IO y pendientes de eventos. Medir inserción, consultas/planes e índices, algoritmo y reconstrucción por separado. La validación JSON/XSD consume CPU del generador: observarla antes de atribuir saturación al servidor.

El fixture inicial utiliza Werkzeug con hilos y límites de consumo aumentados para pruebas funcionales. Sus números no representan Waitress/Nginx con réplicas ni el límite de consumo desplegado. La fase sostenida debe identificar explícitamente su topología y conservar los límites reales del producto. El alcance de cada tabla de resultados prevalece sobre esta lista de experimentos previstos.

## Piloto preparado

`apps/services/scripts/prepare_load.py` crea un directorio nuevo privado de nombre corto bajo `/tmp`, inicializa motores propios y los detiene al terminar; conserva datos e informe privado incluso ante un error. No acepta un DSN ni un directorio existente. Verifica direcciones loopback, procesos, directorios de PostgreSQL y MongoDB y configuración de Redis antes de insertar. Exige 3 GiB libres y como máximo 1,5 GiB propios antes y después de cada lote; un lote puede aumentar temporalmente el consumo entre comprobaciones. Se debe reservar espacio adicional para el arranque inicial de los motores.

La semilla predeterminada es `20261113` y el instante lógico es `2026-11-13T12:00:00Z`. El diseño usa 200 donantes preliminares, 1.000 unidades RBC ficticias repartidas por igual entre dos instituciones y entre disponible/cuarentena, y 10.000 eventos sintéticos vinculados a las unidades para la consulta de trazabilidad. Las entidades tienen UUID derivados de la semilla; los identificadores y credenciales de infraestructura son nuevos en cada ejecución. Los estados SQL son datos de prueba, no registros por API, dictámenes ni prueba de elegibilidad clínica. El informe incluye huella de las dimensiones lógicas, conteos, avance confirmado por lote, planes, índices, tamaños y tiempo de inserción. No se han medido aún esos valores.

La preparación registra el espacio y tamaño de PostgreSQL después de inicializar motores y antes de insertar el piloto, y mide el incremento por separado del coste fijo. Los eventos del piloto residen en PostgreSQL; MongoDB se inicia para el entorno integrado pero no recibe aquí un volumen sintético documental y esta fase no acredita su rendimiento. El diagnóstico detallado de errores se conserva solo en el directorio privado, con modo 0600.

Para una fase sostenida futura, arrancar exclusivamente el laboratorio privado resultante con `scripts/local.py` y sus procesos reales `run.py`: Waitress con ocho hilos por servicio y transporte con gevent; conservar límites, pools y tiempos configurados por el producto, sin `TESTING` ni límites del fixture. Es una sola instancia por servicio en loopback, sin Nginx ni réplicas, y el generador Locust comparte el mismo equipo. Esa topología debe verificarse y describirse al medir; no representa el despliegue GCP. Por separado se requiere comprobar la recuperación y cierre de sesiones y la disponibilidad de workers antes de aceptar una corrida.
