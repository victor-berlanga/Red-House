"""HTTP counts must not be overwritten by transaction/drain statistics."""

import pytest

from scripts.sustained_read import request_counts


@pytest.mark.parametrize("count_field", ["requests", "num_requests"])
def test_same_label_keeps_http_transaction_and_drain_counts_separate(count_field):
    rows = [
        {"method": method, "name": "Shared label", count_field: count}
        for method, count in (
            ("TRANSACTION", 199),
            ("DRAIN", 1),
            ("GET", 2),
            ("POST", 3),
        )
    ]
    http, by_method = request_counts(rows, count_field)
    assert http == {"Shared label": 5}
    assert by_method == {
        "TRANSACTION": {"Shared label": 199},
        "DRAIN": {"Shared label": 1},
        "GET": {"Shared label": 2},
        "POST": {"Shared label": 3},
    }
    assert request_counts(list(reversed(rows)), count_field) == (http, by_method)


def test_empty_measurement_has_no_invented_request_counts():
    assert request_counts([], "requests") == ({}, {})
