# Escrituras sostenidas: plan previo

Incremento preparado después de la serie de lecturas. **Todavía no ejecutado.** Reutiliza `/private/tmp/rh-load-c92ed10k` sin inicializar, migrar o repoblar el volumen. Una preparación SQL separada crea doce identidades sintéticas independientes: seis donantes con expediente y seis operadores, una campaña con dos horarios y un perfil académico DRAFT sin habilitación clínica. El manifiesto privado permite cotejar y conservar esa preparación. Los DSN administrativos de preparación/oráculo son distintos de los usuarios de ejecución de los servicios; no se amplían privilegios.

Dos recorridos con respuestas previas: donante JSON consulta campaña/horarios, reserva, reprograma y cancela su cita; operador XML/XSD registra unidad en cuarentena, registra y recibe su muestra, y consulta el resultado. Cada escritura conserva un intento privado antes del envío; se repite una clave/cuerpo por usuario para comprobar idempotencia. Un resultado incierto detiene ese usuario y permanece para conciliación, sin generar otra clave.

Doce sesiones listas antes de admitir recorridos; 30 s de calentamiento, drenado de sus ciclos, 120 s medidos y drenado final separado. Pausas de 4–6 s entre recorridos, cuotas intactas. Se conservan HTTP/s y recorridos confirmados/s por separado, mediana/p95/p99, errores/429 y datos de recursos. Objetivos del plan vigente: p95 GET inferior a 2 s y p95 de cada recorrido inferior a 5 s. El incumplimiento de latencia se separa de una ejecución inválida. La corrida exige cero escrituras inciertas o sin conciliar para aceptarse.

El oráculo coteja todos los intentos, incluidos calentamiento/drenado/parciales, con idempotencia, filas, versiones, propietario/institución, efectos extra, auditoría y avisos. Solo ciclos iniciados y terminados dentro de medición aportan recorridos/s. Se verifica revocación de doce familias en PostgreSQL/Redis, topología/fuentes estables y cierre de procesos propios. El diario con `fsync`, validación de contratos y generador comparten el equipo con los servicios; su coste forma parte de este entorno, no debe atribuirse íntegramente al servidor.

Preparación comprobada por revisión fuerte y dirección. Corridas puras separadas: 47 casos en 2,06 s, uno dirigido a cierre/interrupción en 0,98 s; después de corregir umbrales, 40 dirigidos en 2,42 s. No se suman como casos distintos. Resultados observados en herramientas, sin JUnit archivado. Una revisión posterior incorporó también la instantánea global de fuentes de servicios y esquema antes/después; dos casos dirigidos de deriva/estabilidad aprobaron en 1,07 s. Ruff y diff limpios. Ningún resultado sostenido se deriva de esos dobles.

Comando previsto, con ventana local exclusiva y log privado nuevo:

```sh
apps/services/.venv/bin/python apps/services/scripts/prepare_load.py --transaction-directory /private/tmp/rh-load-c92ed10k
```

El directorio transaccional nuevo conserva sus resultados sin sobrescribir la serie de lectura. Este incremento no cubre todavía carga transaccional de evaluación/reserva, planificación/custodia o GPS, ni mediciones en GCP.
