"""Exportaciones tabulares acotadas sin fórmulas, macros ni acciones PDF."""

import csv
from io import BytesIO, StringIO
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape


MIMES = {
    "CSV": "text/csv",
    "PDF": "application/pdf",
    "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def cells(rows):
    names = sorted({key for row in rows for key in row}) or ["sin_resultados"]
    result = [names]
    for row in rows:
        values = []
        for name in names:
            value = row.get(name)
            text = "Sin dato" if value is None else str(value)
            text = "".join(c for c in text if ord(c) >= 32)
            if text.lstrip().startswith(("=", "+", "-", "@")):
                text = "'" + text
            values.append(text)
        result.append(values)
    return result


def render(rows, format, context=None):
    if context:
        import json
        from datetime import datetime
        from zoneinfo import ZoneInfo

        zone = ZoneInfo(context["timezone"])
        converted = []
        for original in rows:
            row = dict(original)
            for key, value in row.items():
                if key.endswith("_at") or key == "eta":
                    try:
                        row[key] = (
                            datetime.fromisoformat(value.replace("Z", "+00:00"))
                            .astimezone(zone)
                            .isoformat()
                        )
                    except (ValueError, AttributeError):
                        pass
            converted.append(row)
        # Columnas de contexto mantienen CSV/XLSX tabulares, incluso sin resultados.
        metadata = {
            "reporte_" + k: json.dumps(v, ensure_ascii=False)
            if isinstance(v, (dict, list))
            else str(v)
            for k, v in context.items()
        }
        rows = [{**row, **metadata} for row in converted] or [metadata]
    table = cells(rows)
    if format == "CSV":
        output = StringIO(newline="")
        csv.writer(output).writerows(table)
        return output.getvalue().encode("utf-8-sig")
    if format == "PDF":
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

        writer = PdfWriter()
        # Una celda por línea evita cortar columnas anchas; todos los valores quedan
        # representados. Formato operativo identificado, pendiente de revisión.
        lines = ["Red House | reporte operativo v1 | sujeto a revision"]
        for index, row in enumerate(table[1:], 1):
            lines.append(f"Registro {index}")
            for name, value in zip(table[0], row):
                text = f"{name}: {value}"
                lines.extend(text[i : i + 95] for i in range(0, len(text), 95))
        for start in range(0, len(lines), 56):
            page = writer.add_blank_page(612, 792)
            font = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                }
            )
            page[NameObject("/Resources")] = DictionaryObject(
                {
                    NameObject("/Font"): DictionaryObject(
                        {NameObject("/F1"): writer._add_object(font)}
                    )
                }
            )
            body = b"BT /F1 9 Tf 36 760 Td 12 TL\n"
            for line in lines[start : start + 56]:
                value = (
                    line.encode("latin-1", "replace")
                    .replace(b"\\", b"\\\\")
                    .replace(b"(", b"\\(")
                    .replace(b")", b"\\)")
                )
                body += b"(" + value + b") Tj T*\n"
            stream = DecodedStreamObject()
            stream.set_data(body + b"ET")
            page[NameObject("/Contents")] = writer._add_object(stream)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    if format != "XLSX":
        raise ValueError("unsupported_report_format")
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        )
        archive.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Reporte" sheetId="1" r:id="rId1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        )
        lines = [
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        ]
        for i, row in enumerate(table, 1):
            lines.append(
                f'<row r="{i}">'
                + "".join(
                    '<c t="inlineStr"><is><t xml:space="preserve">'
                    + escape(value)
                    + "</t></is></c>"
                    for value in row
                )
                + "</row>"
            )
        archive.writestr(
            "xl/worksheets/sheet1.xml", "".join(lines) + "</sheetData></worksheet>"
        )
    return output.getvalue()
