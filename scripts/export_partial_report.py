"""Exporta Markdown técnico a Word sin portada; LibreOffice produce el PDF."""

import argparse
from pathlib import Path

import markdown
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from lxml import html
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def export(paths, destination):
    document = Document()
    section = document.sections[0]
    section.top_margin = section.bottom_margin = Inches(0.7)
    section.left_margin = section.right_margin = Inches(0.75)
    normal = document.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(10)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08
    for name in ("Title", "Heading 1", "Heading 2", "Heading 3", "Heading 4"):
        document.styles[name].font.color.rgb = RGBColor.from_string("8E2434")
    footer = section.footer.paragraphs[0]
    footer.text = "Red House · Segundo parcial · "
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    for source in paths:
        root = html.fragment_fromstring(
            markdown.markdown(source.read_text(), extensions=["tables", "fenced_code"]),
            create_parent="div",
        )
        for node in root:
            text = node.text_content().strip()
            if node.tag in ("h1", "h2", "h3", "h4"):
                document.add_heading(text, int(node.tag[1]))
            elif node.tag == "table":
                rows = node.xpath(".//tr")
                if not rows:
                    continue
                table = document.add_table(rows=0, cols=len(rows[0].xpath("./th|./td")))
                table.style = "Light Shading Accent 1"
                for index, row in enumerate(rows):
                    cells = table.add_row().cells
                    for cell, content in zip(cells, row.xpath("./th|./td")):
                        cell.text = content.text_content().strip()
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                run.font.size = Pt(8)
                    if index == 0:
                        repeat = OxmlElement("w:tblHeader")
                        table.rows[-1]._tr.get_or_add_trPr().append(repeat)
                document.add_paragraph()
            elif node.tag in ("ul", "ol"):
                for item in node.xpath("./li"):
                    document.add_paragraph(
                        item.text_content(),
                        style="List Bullet" if node.tag == "ul" else "List Number",
                    )
            elif node.tag == "pre":
                paragraph = document.add_paragraph(text)
                for run in paragraph.runs:
                    run.font.name, run.font.size = "Consolas", Pt(8)
            elif node.tag == "p" and node.xpath(".//img"):
                for image in node.xpath(".//img"):
                    path = (
                        (source.parent / image.get("src")).resolve().with_suffix(".png")
                    )
                    if path.exists():
                        with Image.open(path) as bitmap:
                            width, height = bitmap.size
                        scale = min(6.7 / width, 8 / height)
                        document.add_picture(str(path), width=Inches(width * scale))
                        document.add_paragraph(image.get("alt", ""), style="Caption")
                    else:
                        raise FileNotFoundError(path)
            elif text:
                document.add_paragraph(text)
        links = sorted(
            {(a.text_content(), a.get("href")) for a in root.xpath(".//a[@href]")}
        )
        if links:
            document.add_heading("Referencias y archivos de esta sección", 2)
            for label, href in links:
                if not href.startswith(("http://", "https://", "#")):
                    href = str((source.parent / href).resolve().relative_to(ROOT))
                document.add_paragraph(label + ": " + href, style="Caption")
    destination.parent.mkdir(parents=True, exist_ok=True)
    document.save(destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical", action="store_true")
    args = parser.parse_args()
    sources = (
        [ROOT / "documentation/segundo-parcial/Modelo_fisico.md"]
        if args.physical
        else [
            ROOT / "documentation/markdowns/Reporte_tecnico_segundo_parcial.md",
            ROOT / "documentation/segundo-parcial/Fichas_microservicios.md",
            ROOT / "documentation/markdowns/Cierre_segundo_parcial.md",
            ROOT / "documentation/evidencias/segundo-parcial/RESULTADOS.md",
            ROOT / "documentation/evidencias/sesiones-redis/RESULTADOS.md",
        ]
    )
    name = (
        "Modelo_fisico_PostgreSQL"
        if args.physical
        else "Reporte_tecnico_segundo_parcial"
    )
    export(sources, ROOT / "documentation/docx" / (name + ".docx"))
    print(name + ".docx")


if __name__ == "__main__":
    main()
