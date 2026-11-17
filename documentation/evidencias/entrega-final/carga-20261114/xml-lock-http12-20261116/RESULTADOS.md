# HTTP12 con compilación XML protegida — 16/11/2026

**Aprobado en una corrida local**, sobre el fixture conservado en esquema 21. Inicio UTC: 17/11/2026 00:01:57; fecha local Monterrey: 16/11. Esta evidencia corresponde a las tres fuentes de `9e48f11`, con hashes completos en [recibo.json](recibo.json). No es una medición GCP ni cierra todos los flujos de etapa 07.

Doce identidades sintéticas independientes, perfiles DONOR/OPERATOR y representaciones JSON/XML. Se conservaron población e historia; solo se creó por API una campaña con dos horarios. Copias privadas de configuración: API pool 2, worker pool 2 e intervalo 2 s. Sin aumento de cuotas ni cambio de objetivos: p95 de lectura menor de 2 s y recorrido menor de 5 s. Calentamiento de 30 s, medición de 120 s y conciliación con el plazo original de 30 s.

| Comprobación | Resultado |
|---|---:|
| Mínimo de usuarios durante calentamiento y medición | 12 / 12 |
| HTTP de calentamiento / fallos | 462 / 0 |
| HTTP medidos / fallos / HTTP por segundo | 1472 / 0 / 12,255 |
| Máximo p95 de lectura | 480 ms |
| p95 / p99 de recorrido DONOR | 2000 / 2200 ms |
| p95 / p99 de recorrido OPERATOR | 1400 / 1500 ms |
| Recorridos medidos / por segundo | 228 / 1,898 |
| Intentos persistidos / intentados, incluyendo calentamiento y drenado | 873 / 873 |
| Recorridos completos de toda la ejecución | 291 |
| Replays confirmados / incompletos / pendientes | 12 / 0 / 0 |
| Respuestas 429 / fallos de limpieza | 0 / 0 |

El oráculo de persistencia y eventos aprobó. Su espera final fue **0,131488 s**; no representa latencia individual de propagación. Conteo y revocación de familias de carga comprobados; logout técnico de preparación también verificado. Los tres eventos de preparación se correlacionaron con Auditoría. Locust terminó con código 0; el wrapper registra `passed`, ejecución válida y medición aceptada.

Los mapas completos de 963 fuentes y 25 huellas detalladas se persistieron antes y después y coinciden byte a byte. Incluyen las tres fuentes XML revisadas; no atribuyen congelación a móvil/escritorio. Historia, configuración original y topología permanecieron iguales. El wrapper confirmó cierre de procesos y retirada de su candado; una lectura posterior de procesos no encontró PID propio por las rutas exactas del fixture y del runner. Ventana pesada liberada. No hubo segunda corrida ni motores adicionales.

Comparación descriptiva con [la corrida del parser anterior](../xml-pools-20261116/RESULTADOS.md): HTTP medidos 1396→1472, máximo p95 de lectura 520→480 ms y de recorrido 2500→2000 ms. Son ejecuciones consecutivas sobre una población evolutiva, sin diseño A/B: permiten comprobar objetivos con el candado, **no atribuir una mejora causal ni cuantificar su coste aislado**. Los fallos previos locales y de imagen GCP permanecen fallidos; el [comparativo y las 14 pruebas puras](../xml-compilation-lock-20261116/RESULTADOS.md) conservan su propio alcance.

No aplica JUnit a esta corrida Locust. El recibo saneado conserva hashes de resúmenes privados, fase y mapas; no publica credenciales, tokens, cuerpos clínicos ni logs internos. Los cuatro mapas publicados contienen rutas relativas y SHA-256, nunca valores de configuración. La publicación GCP se documenta por separado y requiere su gate propio; este expediente no la anticipa.
