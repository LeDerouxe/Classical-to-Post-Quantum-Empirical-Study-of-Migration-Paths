#!/usr/bin/env python3
"""Render the JISA packaged Markdown manuscript to a single Word file.

This is an initial-submission rendering rather than a publisher typeset proof.
It preserves the complete manuscript, tables, figures, numerical references,
and author-confirmation markers so the latter cannot be overlooked.
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "submission" / "jisa" / "jisa-submission-manuscript-en.md"
OUTPUT = ROOT / "submission" / "jisa" / "jisa-submission-manuscript-en.docx"
FIGURES = ROOT / "submission" / "jisa" / "figures-png"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    marker = OxmlElement("w:tblHeader")
    marker.set(qn("w:val"), "true")
    tr_pr.append(marker)


def set_cell_margins(cell, top=90, start=90, bottom=90, end=90) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    margin = tc_pr.first_child_found_in("w:tcMar")
    if margin is None:
        margin = OxmlElement("w:tcMar")
        tc_pr.append(margin)
    for direction, value in {"top": top, "start": start, "bottom": bottom, "end": end}.items():
        node = margin.find(qn(f"w:{direction}"))
        if node is None:
            node = OxmlElement(f"w:{direction}")
            margin.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def apply_run_format(run, size=11, italic=False, bold=False) -> None:
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(size)
    run.italic = italic
    run.bold = bold


def add_inline(paragraph, text: str, size=11) -> None:
    """Render the small Markdown subset used by the manuscript."""
    token = re.compile(r"(\*\*.*?\*\*|`.*?`|\*.*?\*)")
    position = 0
    for match in token.finditer(text):
        if match.start() > position:
            run = paragraph.add_run(text[position:match.start()])
            apply_run_format(run, size=size)
        token_text = match.group(0)
        if token_text.startswith("**"):
            run = paragraph.add_run(token_text[2:-2])
            apply_run_format(run, size=size, bold=True)
        elif token_text.startswith("`"):
            run = paragraph.add_run(token_text[1:-1])
            apply_run_format(run, size=size)
        else:
            run = paragraph.add_run(token_text[1:-1])
            apply_run_format(run, size=size, italic=True)
        position = match.end()
    if position < len(text):
        run = paragraph.add_run(text[position:])
        apply_run_format(run, size=size)


def make_table(doc: Document, rows: list[list[str]]) -> None:
    table = doc.add_table(rows=0, cols=len(rows[0]))
    table.style = "Table Grid"
    for r_i, values in enumerate(rows):
        cells = table.add_row().cells
        for c_i, value in enumerate(values):
            p = cells[c_i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if len(value) < 20 else WD_ALIGN_PARAGRAPH.LEFT
            add_inline(p, value, size=8.5)
            set_cell_margins(cells[c_i])
            if r_i == 0:
                set_cell_shading(cells[c_i], "D9E2F3")
                for run in p.runs:
                    run.bold = True
    set_repeat_table_header(table.rows[0])
    doc.add_paragraph().paragraph_format.space_after = Pt(3)


def parse_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    table_lines = []
    index = start
    while index < len(lines) and lines[index].startswith("|"):
        table_lines.append(lines[index])
        index += 1
    rows = []
    for line in table_lines:
        values = [v.strip() for v in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", v) for v in values):
            continue
        rows.append(values)
    return rows, index


def add_figure(doc: Document, line: str) -> None:
    match = re.fullmatch(r"!\[(.*?)\]\(figures/(.*?)\.svg\)", line.strip())
    if not match:
        raise ValueError(f"unexpected figure markup: {line}")
    caption, stem = match.groups()
    image = FIGURES / f"{stem}.png"
    if not image.exists():
        raise FileNotFoundError(image)
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(image), width=Inches(6.1))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(9)
    add_inline(cap, caption, size=10)
    for run in cap.runs:
        run.italic = True


def main() -> None:
    text = INPUT.read_text(encoding="utf-8")
    lines = text.splitlines()
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.85)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.08
    normal.paragraph_format.space_after = Pt(6)
    for level in range(1, 4):
        style = doc.styles[f"Heading {level}"]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.color.rgb = None
        style.font.size = Pt({1: 14, 2: 12, 3: 11}[level])
        style.font.bold = True

    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            p = doc.add_paragraph(style="Title")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_inline(p, line[2:], size=15)
            index += 1
            continue
        if line.startswith("### "):
            p = doc.add_paragraph(style="Heading 3")
            add_inline(p, line[4:], size=11)
            index += 1
            continue
        if line.startswith("## "):
            p = doc.add_paragraph(style="Heading 1")
            add_inline(p, line[3:], size=14)
            index += 1
            continue
        if line.startswith("| "):
            rows, index = parse_table(lines, index)
            make_table(doc, rows)
            continue
        if line.startswith("!["):
            add_figure(doc, line)
            index += 1
            continue
        if line.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, line[2:], size=11)
            index += 1
            continue

        paragraph_lines = [line]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or candidate.startswith(("#", "|", "![", "- ")):
                break
            paragraph_lines.append(candidate)
            index += 1
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        add_inline(p, " ".join(paragraph_lines), size=11)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_inline(footer, "JISA initial-submission manuscript", size=9)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
