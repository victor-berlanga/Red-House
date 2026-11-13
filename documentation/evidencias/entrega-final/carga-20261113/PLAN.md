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
