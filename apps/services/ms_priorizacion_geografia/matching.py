"""Hopcroft–Karp: maximiza cobertura operativa sin asignación clínica automática."""

from collections import deque


def maximum_matching(graph):
    """Grafo slot de solicitud -> recursos aprobados. O(E sqrt(V)), orden estable."""
    adjacency = {
        slot: sorted(set(resources)) for slot, resources in sorted(graph.items())
    }
    left, right, distance = {}, {}, {}
    infinity = len(adjacency) + 1

    def bfs():
        queue = deque()
        for slot in adjacency:
            distance[slot] = 0 if slot not in left else infinity
            if slot not in left:
                queue.append(slot)
        distance[None] = infinity
        while queue:
            slot = queue.popleft()
            if distance[slot] < distance[None]:
                for resource in adjacency[slot]:
                    mate = right.get(resource)
                    if distance[mate] != infinity:
                        continue
                    distance[mate] = distance[slot] + 1
                    if mate is not None:
                        queue.append(mate)
        return distance[None] != infinity

    def dfs(slot):
        if slot is None:
            return True
        for resource in adjacency[slot]:
            mate = right.get(resource)
            if distance[mate] == distance[slot] + 1 and dfs(mate):
                left[slot], right[resource] = resource, slot
                return True
        distance[slot] = infinity
        return False

    while bfs():
        for slot in adjacency:
            if slot not in left:
                dfs(slot)
    return dict(sorted(left.items()))
