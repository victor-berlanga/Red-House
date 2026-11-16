from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

from pypdf import PdfReader
from redhouse.report_formats import render

ROWS = [
    {
        "id": f"synthetic-{index}",
        "folio": f"REPORT-{index}",
        "created_at": "2026-11-16T18:00:00+00:00",
    }
    for index in range(10)
]
CONTEXT = {"timezone": "America/Monterrey", "row_count": 10, "filters": {"q": "REPORT"}}


def pdf_text(content):
    return "\n".join(page.extract_text() for page in PdfReader(BytesIO(content)).pages)


def test_modern_pdf_preserves_every_record_with_one_shared_context():
    legacy = pdf_text(render(ROWS, "PDF", CONTEXT))
    modern = pdf_text(render(ROWS, "PDF", dict(CONTEXT, render_version=2)))
    assert legacy.count("reporte_timezone:") == len(ROWS)
    assert modern.count("reporte_timezone:") == 1
    assert "reporte_render_version" not in modern
    assert "reporte_row_count: 10" in modern
    for row in ROWS:
        assert f"id: {row['id']}" in modern
        assert f"folio: {row['folio']}" in modern
    assert modern.count("created_at: 2026-11-16T12:00:00-06:00") == len(ROWS)


def test_modern_xlsx_bytes_stay_identical_across_retry_times():
    context = dict(CONTEXT, render_version=2)
    with patch("zipfile.time.localtime", return_value=(2020, 1, 1, 0, 0, 0, 2, 1, 0)):
        first = render(ROWS, "XLSX", context)
    with patch(
        "zipfile.time.localtime", return_value=(2026, 11, 16, 18, 0, 0, 0, 320, 0)
    ):
        retried = render(ROWS, "XLSX", context)
    assert first == retried


def test_modern_csv_does_not_expose_internal_render_version():
    assert render(ROWS, "CSV", CONTEXT) == render(
        ROWS, "CSV", dict(CONTEXT, render_version=2)
    )


def test_historical_empty_context_keeps_legacy_zip_timestamps():
    # Migración 017 inicializó los trabajos previos con context={}.
    for context in (None, {}, CONTEXT):
        with patch(
            "zipfile.time.localtime", return_value=(2020, 1, 1, 0, 0, 0, 2, 1, 0)
        ):
            content = render(ROWS, "XLSX", context)
        with ZipFile(BytesIO(content)) as archive:
            assert all(
                info.date_time == (2020, 1, 1, 0, 0, 0) for info in archive.infolist()
            )
