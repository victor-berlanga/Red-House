from itertools import product

from ms_compatibilidad.routes import compatible
from ms_priorizacion_geografia.matching import maximum_matching


def test_matching_finds_augmenting_path_greedy_misses():
    # El paciente flexible admite A o B; el restringido solo A.
    result = maximum_matching({"flexible": ["A", "B"], "restricted": ["A"]})
    assert result == {"flexible": "B", "restricted": "A"}


def test_matching_is_maximum_against_exhaustive_small_graphs():
    # Oráculo exhaustivo independiente para los 512 grafos bipartitos 3x3.
    left, right = ["p1", "p2", "p3"], ["r1", "r2", "r3"]
    for mask in range(512):
        graph = {
            p: [r for j, r in enumerate(right) if mask & (1 << (i * 3 + j))]
            for i, p in enumerate(left)
        }
        optimum = 0
        for assignment in product([None, *right], repeat=3):
            actual = [r for r in assignment if r is not None]
            if len(actual) == len(set(actual)) and all(
                r is None or r in graph[p] for p, r in zip(left, assignment)
            ):
                optimum = max(optimum, len(actual))
        result = maximum_matching(graph)
        assert len(result) == optimum
        assert len(set(result.values())) == len(result)


def test_rbc_demo_filter_matches_documented_matrix():
    groups = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
    expected = {
        "O-": {"O-"},
        "O+": {"O-", "O+"},
        "A-": {"O-", "A-"},
        "A+": {"O-", "O+", "A-", "A+"},
        "B-": {"O-", "B-"},
        "B+": {"O-", "O+", "B-", "B+"},
        "AB-": {"O-", "A-", "B-", "AB-"},
        "AB+": set(groups),
    }
    for recipient in groups:
        assert {donor for donor in groups if compatible(donor, recipient)} == expected[
            recipient
        ]
