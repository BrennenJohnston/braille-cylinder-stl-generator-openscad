"""Generate docs/MakerWorld_Quick_Start_Guide.pdf from docs/MAKERWORLD_QUICK_START.md.

The markdown file is the single source of truth; this script renders it to PDF
with fpdf2. Braille glyphs (U+2800-U+28FF) are covered by registering Segoe UI
Symbol as a fallback font, so braille examples render as dots, not tofu boxes.

Usage (from the repo root):
    .venv\\Scripts\\python scripts\\generate_quick_start_pdf.py

Requires the Windows system fonts Segoe UI (segoeui.ttf / segoeuib.ttf /
segoeuii.ttf) and Segoe UI Symbol (seguisym.ttf).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from fpdf import FPDF

REPO_ROOT = Path(__file__).resolve().parents[1]
MD_PATH = REPO_ROOT / "docs" / "MAKERWORLD_QUICK_START.md"
PDF_PATH = REPO_ROOT / "docs" / "MakerWorld_Quick_Start_Guide.pdf"
FONT_DIR = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"

BODY_SIZE = 10.5
BODY_COLOR = (30, 30, 30)
QUOTE_COLOR = (85, 85, 85)
HEADING_COLOR = (30, 73, 118)  # matches the web app's high-contrast blue


def md_inline(text: str) -> str:
    """Normalize markdown inline syntax to what fpdf2's markdown mode supports.

    fpdf2 understands **bold**, __italic__ and [text](url); it has no inline
    code, so backticks are stripped. Autolinks <url> become [url](url).
    """
    text = text.replace("`", "")
    text = re.sub(r"<(https?://[^>]+)>", r"[\1](\1)", text)
    # fpdf2 cannot nest styles inside link text; drop emphasis markers there
    text = re.sub(r"\[([^\]]*)\]", lambda m: "[" + m.group(1).replace("*", "") + "]", text)
    # *italic* -> __italic__ (single asterisks only; ** pairs are left alone)
    text = re.sub(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", r"__\1__", text)
    return text


def strip_inline(text: str) -> str:
    """Remove all inline markdown, for contexts without markdown support (tables)."""
    text = text.replace("`", "")
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", r"\1", text)
    return text


class QuickStartPDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("segoe", size=8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="C")


def build_pdf() -> QuickStartPDF:
    pdf = QuickStartPDF(format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(auto=True, margin=18)

    pdf.add_font("segoe", style="", fname=FONT_DIR / "segoeui.ttf")
    pdf.add_font("segoe", style="B", fname=FONT_DIR / "segoeuib.ttf")
    pdf.add_font("segoe", style="I", fname=FONT_DIR / "segoeuii.ttf")
    pdf.add_font("segoe", style="BI", fname=FONT_DIR / "segoeuiz.ttf")
    pdf.add_font("seguisym", style="", fname=FONT_DIR / "seguisym.ttf")
    # Braille (and any other glyph Segoe UI lacks) falls back to Segoe UI Symbol.
    pdf.set_fallback_fonts(["seguisym"])

    pdf.add_page()
    return pdf


def body_font(pdf: FPDF) -> None:
    pdf.set_font("segoe", size=BODY_SIZE)
    pdf.set_text_color(*BODY_COLOR)


def emit_heading(pdf: FPDF, level: int, text: str) -> None:
    sizes = {1: 19, 2: 14.5, 3: 11.5, 4: 10.5}
    before = {1: 0, 2: 5, 3: 4, 4: 3}
    if pdf.get_y() > pdf.h - 45:  # avoid orphan headings at the page bottom
        pdf.add_page()
    pdf.ln(before[level])
    pdf.set_font("segoe", style="B", size=sizes[level])
    pdf.set_text_color(*HEADING_COLOR)
    pdf.multi_cell(0, None, strip_inline(text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)


def emit_paragraph(pdf: FPDF, text: str) -> None:
    body_font(pdf)
    pdf.multi_cell(0, 5.2, md_inline(text), markdown=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)


def emit_list_item(pdf: FPDF, text: str, bullet: str) -> None:
    body_font(pdf)
    left = pdf.l_margin
    pdf.set_x(left + 3)
    pdf.cell(6, 5.2, bullet)
    pdf.multi_cell(
        pdf.w - pdf.r_margin - (left + 9), 5.2, md_inline(text),
        markdown=True, new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(0.5)


def emit_quote(pdf: FPDF, lines: list[str]) -> None:
    pdf.set_font("segoe", size=BODY_SIZE)
    pdf.set_text_color(*QUOTE_COLOR)
    top = pdf.get_y()
    left = pdf.l_margin
    pdf.set_x(left + 5)
    text = "\n".join(md_inline(line) for line in lines)
    pdf.multi_cell(
        pdf.w - pdf.r_margin - (left + 5), 5.4, text,
        markdown=True, new_x="LMARGIN", new_y="NEXT",
    )
    bottom = pdf.get_y()
    pdf.set_draw_color(*HEADING_COLOR)
    pdf.set_line_width(0.8)
    pdf.line(left + 1.5, top + 0.5, left + 1.5, bottom - 0.5)
    pdf.ln(2)


def emit_table(pdf: FPDF, rows: list[list[str]]) -> None:
    body_font(pdf)
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.2)
    with pdf.table(
        line_height=5.2,
        padding=1.5,
        text_align="LEFT",
        col_widths=tuple([3, 4, 4][: len(rows[0])]) or None,
    ) as table:
        for i, row in enumerate(rows):
            tr = table.row()
            for cell in row:
                tr.cell(strip_inline(cell))
    pdf.ln(2)


def parse_blocks(md: str):
    """Yield (kind, payload) blocks from the guide's constrained markdown."""
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped == "---":
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            yield "h" + str(len(m.group(1))), m.group(2)
            i += 1
            continue
        if stripped.startswith(">"):
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            yield "quote", quote
            continue
        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            yield "table", rows
            continue
        m = re.match(r"^(-|\d+\.)\s+(.*)$", stripped)
        if m:
            marker, text = m.group(1), m.group(2)
            i += 1
            # absorb hanging-indent continuation lines
            while i < len(lines) and lines[i].startswith("  ") and lines[i].strip() \
                    and not re.match(r"^\s*(-|\d+\.)\s", lines[i]):
                text += " " + lines[i].strip()
                i += 1
            yield "li", (marker, text)
            continue
        # paragraph: absorb until a blank line or a new block marker
        para = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", ">", "|", "- ")) or nxt == "---" \
                    or re.match(r"^\d+\.\s", nxt):
                break
            para.append(nxt)
            i += 1
        yield "p", " ".join(para)


def main() -> int:
    md = MD_PATH.read_text(encoding="utf-8")
    pdf = build_pdf()
    for kind, payload in parse_blocks(md):
        if kind in ("h1", "h2", "h3", "h4"):
            emit_heading(pdf, int(kind[1]), payload)
        elif kind == "quote":
            emit_quote(pdf, payload)
        elif kind == "table":
            emit_table(pdf, payload)
        elif kind == "li":
            marker, text = payload
            emit_list_item(pdf, text, "\u2022" if marker == "-" else marker)
        else:
            emit_paragraph(pdf, payload)
    pdf.output(str(PDF_PATH))
    print(f"Wrote {PDF_PATH} ({PDF_PATH.stat().st_size:,} bytes, {pdf.page_no()} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
