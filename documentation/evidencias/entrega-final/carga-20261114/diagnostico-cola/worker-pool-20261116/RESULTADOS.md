# Pool del worker aplicado; recuperación todavía parcial — 16/11/2026

Se aplicó el candidato privado cotejado con su copia fría: `worker.main` usa `setdefault("DATABASE_POOL_SIZE", 1)` y cierra sus pools en `finally`. El valor explícito 0 conserva conexión nueva por transacción; otro tamaño explícito se respeta. Solo cambia el proceso worker: `run.py`, `settings()`, los JSON y `step()` compartido con el monolito permanecen intactos.

[19 pruebas dirigidas](unitarias.xml) aprobaron en 1,41 s: 13 de cadencia y seis de configuración, ámbito y cierre. Ruff no detectó problemas en las pruebas; el worker conserva cinco avisos anteriores (I001, BLE001 dos veces, LOG015, S110), [cero nuevos](ruff.json). No se ejecutó la suite global.

## Recuperación limitada

Se reutilizó el fixture original: propietario, rutas, manifiesto y fuentes baseline verificados; no hizo falta restaurar la copia fría, ni resembrar. Workers reales Donantes/Auditoría, APIs Auditoría/Alertas y PostgreSQL/Redis/Mongo propios. Pool efectivo de workers 1; APIs 0, cuotas originales. Sin Locust ni transacciones nuevas de cliente.

**Exit 1 conservado: el límite de observación terminó con cola pendiente.** Parada solicitada a los 120,004 s; cierre normal del lote y workers a los 125,098 s, sin ampliación automática. Todos los procesos propios cerraron, sin kill forzado. No error técnico registrado. Las 63 fuentes de producto capturadas, configuraciones, manifiesto, trazas y resultados anteriores conservaron sus hashes. [Recibo saneado completo](recuperacion.json).

| Resultado | Antes | Después |
|---|---:|---:|
| Cola global/pertinente pendiente | 7469 | 5742 |
| Auditoría hacia Mongo | 6956 | 5402 |
| Auditoría hacia sí misma | 513 | 340 |
| Donantes pendiente | 0 | 0 |
| Otros servicios pendientes | 0 | 0 |
| Eventos de negocio SQL exactos | 765/765 | 765/765 |
| Avisos exactos, sin extras | 121/121 | 121/121 |
| Eventos de negocio proyectados a Mongo | 0/765 | 0/765 |

Auditoría entregó 1900 filas: 1727 hacia Mongo y 173 hacia sí misma. Las segundas generaron 173 nuevas filas Mongo de eventos READ históricos. Balance: `7469 + 173 - 1900 = 5742`. No aparecieron nuevos eventos de origen ni recordatorios; los heartbeats y la propagación sí escribieron datos auxiliares. Ambos heartbeats finales sin error.

El ritmo observado de Auditoría, incluyendo cierre, fue **15,19 entregas/s**, frente a **4,39/s** en el drenado anterior: aproximadamente **3,46 veces**. La reducción neta pendiente pasó de 5,29 a 13,81 filas/s, aproximadamente 2,61 veces. Es una comparación descriptiva: cambió el tramo de cola y Donantes ya estaba vacío; no es un A/B controlado ni una garantía bajo carga concurrente. El [discriminante SQL previo](../pool-readonly/RESULTADOS.md) sí aisló el coste de adquisición de conexión.

La cola sigue ordenada por antigüedad; los eventos de negocio permanecen detrás del histórico en Mongo. No se declara completa la recuperación, no se convierte la carga original fallida en aprobada y no se repite la carga completa. Queda preparado un perfilador privado de diez entregas reales para separar adquisición, SELECT, decodificación, UPDATE, commit, Mongo y HTTP, junto con planes e índices efectivos; todavía no ejecutado. Sin cambios de índices, timeouts, permisos ni publicación GCP.
