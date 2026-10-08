# Algoritmos y límites

## Preselección

RBC-DEMO-1.0 conserva el filtro ABO/RhD para eritrocitos documentado en el monolito. No aplica a plasma, plaquetas u órganos y no interpreta anticuerpos ni pruebas cruzadas. ORGAN-DEMO-1.0 conserva preselección por mismo tipo y ABO idéntico, con RhD excluido de ese filtro. Ninguno certifica compatibilidad clínica; reserva exige dictamen médico favorable.

Entradas: solicitud, receptor mínimo, recursos disponibles y rutas capturadas por sus propietarios. Se conservan versiones, límites de conservación capturados, procedencia y candidatos descartados por falta de ruta/tiempo. Complejidad del recorrido: O(U + R), construyendo un mapa de rutas; las consultas HTTP y PostgreSQL se miden separadamente. El endpoint registra tiempo total de evaluación.

## Orden operativo

LOGISTICS-DEMO-1.0 ordena candidatos por límite de conservación capturado, minutos, distancia e identificador estable; registra urgencia y tiempo de solicitud como contexto. Complejidad O(C log C). No aplica ponderaciones ni prioridad clínica oficial y no optimiza rutas geográficas mediante un proveedor externo.

## Propuestas de cobertura

COVERAGE-DEMO-HK-1.0 construye un grafo bipartito: un nodo por cupo solicitado y un nodo por recurso, con aristas únicamente para candidatos con dictamen favorable en su evaluación. Hopcroft–Karp busca caminos aumentantes y produce matching de cardinalidad máxima.

Problema: asignar primero un recurso flexible a un paciente flexible puede dejar sin propuesta a otro paciente que únicamente admite ese recurso. Un camino aumentante reasigna la propuesta del flexible, aumentando cobertura sin repetir recursos.

Pseudocódigo:

```text
crear grafo de cupos -> recursos aprobados
inicializar matching vacío
mientras BFS encuentre una capa de caminos aumentantes más cortos:
    para cada cupo libre:
        DFS sobre esas capas
        si existe camino aumentante, invertir sus parejas
devolver propuestas, versiones y explicaciones
```

Entradas: máximo 100 evaluaciones de solicitudes propias, sin repetir solicitud; máximo 500 cupos y 100 000 aristas. Salida: parejas solicitud/recurso, cantidad cubierta, versiones originales, explicación y tiempo. Tiempo teórico O(E √V), memoria O(V + E). El orden de nodos/aristas es determinista.

Restricciones y límites: una propuesta no reserva ni autoriza, no ejecuta prioridad clínica, no considera datos HLA ni conflictos normativos no modelados. Puede quedar obsoleta; Inventario vuelve a validar versiones, estado, capacidad y viabilidad temporal. La expansión de cupos se basa en la cantidad de la instantánea, no promete cobertura neta de asignaciones posteriores. Las reglas oficiales de balanceo, urgencia y conservación siguen pendientes de validación.

Pruebas: un caso donde falla un orden voraz; comparación independiente con búsqueda exhaustiva en los 512 grafos bipartitos 3×3; persistencia de una propuesta por API sin crear reservas. La matriz RBC se contrasta completa para los ocho grupos del ejercicio. Resultados vigentes en [VALIDACION](VALIDACION.md).
