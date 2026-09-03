"""
Render PITCH.md to a printable PDF.

Usage:  python tools/make_pitch_pdf.py [source.md] [output.pdf]

Purpose-built Markdown subset renderer (headings, paragraphs, blockquotes,
lists, tables, fenced code, rules, inline bold/italic/code). PITCH.md stays the
single source of truth; re-run this after editing it.
"""

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

# ----------------------------------------------------------------- palette
INK = colors.HexColor("#1A2030")
INK_SOFT = colors.HexColor("#5E6577")
BRASS = colors.HexColor("#8A5A18")
TEAL = colors.HexColor("#2C6B66")
RULE = colors.HexColor("#D8D3C8")
SURFACE = colors.HexColor("#F4F1EA")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


# ----------------------------------------------------------------- styles
# Set by --compact: tightens type and spacing so a document that runs a few
# lines over can be pulled back onto one page without cutting content.
TIGHT = False


def _t(normal, tight):
    return tight if TIGHT else normal


def build_styles():
    ss = getSampleStyleSheet()
    s = {}

    s["title"] = ParagraphStyle(
        "title", parent=ss["Title"], fontName="Helvetica-Bold",
        fontSize=_t(23, 19), leading=_t(27, 22), textColor=INK,
        alignment=0, spaceAfter=2,
    )
    s["h2"] = ParagraphStyle(
        "h2", fontName="Helvetica-Bold", fontSize=_t(14.5, 12.5),
        leading=_t(18, 15), textColor=INK,
        spaceBefore=_t(16, 9), spaceAfter=_t(6, 4),
    )
    s["h3"] = ParagraphStyle(
        "h3", fontName="Helvetica-Bold", fontSize=_t(11.5, 10.4),
        leading=_t(15, 13), textColor=BRASS,
        spaceBefore=_t(12, 7), spaceAfter=_t(4, 2),
    )
    s["h4"] = ParagraphStyle(
        "h4", fontName="Helvetica-Bold", fontSize=10, leading=13,
        textColor=TEAL, spaceBefore=_t(9, 6), spaceAfter=3,
    )
    s["body"] = ParagraphStyle(
        "body", fontName="Times-Roman", fontSize=_t(10.2, 9.5),
        leading=_t(14.6, 12.9), textColor=INK, alignment=TA_JUSTIFY,
        spaceAfter=_t(7, 4.5),
    )
    s["quote"] = ParagraphStyle(
        "quote", parent=s["body"], fontName="Times-Italic", fontSize=10.4,
        leading=15.4, textColor=INK, leftIndent=9, rightIndent=4,
        borderPadding=0, alignment=0, spaceAfter=5,
    )
    s["li"] = ParagraphStyle(
        "li", parent=s["body"], alignment=0, spaceAfter=_t(3, 1.5),
    )
    s["code"] = ParagraphStyle(
        "code", fontName="Courier", fontSize=6.6, leading=8.1, textColor=INK,
    )
    s["th"] = ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=8.6, leading=11,
        textColor=colors.white,
    )
    s["td"] = ParagraphStyle(
        "td", fontName="Times-Roman", fontSize=8.8, leading=11.8, textColor=INK,
    )
    s["footer"] = ParagraphStyle(
        "footer", fontName="Helvetica", fontSize=7.5, leading=10,
        textColor=INK_SOFT,
    )
    return s


# ------------------------------------------------------- inline formatting
def inline(text):
    """Escape XML, then apply **bold**, *italic*, `code`."""
    t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"`([^`]+)`",
               r'<font face="Courier" size="8.6" color="#8A5A18">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", t)
    return t


# --------------------------------------------------------- nested lists
def build_list(raw, start, end, s):
    """Build a ListFlowable from raw[(indent, ordered, text)] between
    start and end. Items indented deeper than the first become a nested
    list attached to the item above them. Returns (flowable, next_index)."""
    base = raw[start][0]
    ordered = raw[start][1]
    items = []
    i = start
    while i < end and raw[i][0] <= base:
        if raw[i][0] < base:
            break
        content = [Paragraph(inline(raw[i][2]), s["li"])]
        j = i + 1
        if j < end and raw[j][0] > base:
            k = j
            while k < end and raw[k][0] > base:
                k += 1
            sub, _ = build_list(raw, j, k, s)
            content.append(sub)
            i = k - 1
        items.append(ListItem(content, leftIndent=14))
        i += 1

    return ListFlowable(
        items,
        bulletType="1" if ordered else "bullet",
        bulletFontSize=8,
        bulletColor=BRASS if base == 0 else TEAL,
        start="1" if ordered else None,
        leftIndent=14,
        spaceBefore=3 if base else 0,
    ), i


# ------------------------------------------------------------- md -> story
def render(md, s):
    lines = md.split("\n")
    story = []
    i = 0
    n = len(lines)

    def flush_para(buf):
        if buf:
            story.append(Paragraph(inline(" ".join(buf).strip()), s["body"]))
            buf.clear()

    para = []

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # --- fenced code -------------------------------------------------
        if stripped.startswith("```"):
            flush_para(para)
            i += 1
            block = []
            while i < n and not lines[i].strip().startswith("```"):
                block.append(lines[i].rstrip())
                i += 1
            i += 1
            body = Preformatted("\n".join(block), s["code"])
            tbl = Table([[body]], colWidths=[PAGE_W - 2 * MARGIN])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                ("BOX", (0, 0), (-1, -1), 0.5, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            story.extend([Spacer(1, 3), tbl, Spacer(1, 9)])
            continue

        # --- table -------------------------------------------------------
        if stripped.startswith("|") and i + 1 < n and re.match(
            r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]
        ):
            flush_para(para)
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip()
                             for c in lines[i].strip().strip("|").split("|")])
                i += 1

            ncols = len(header)
            avail = PAGE_W - 2 * MARGIN
            if ncols == 2:
                widths = [avail * 0.34, avail * 0.66]
            elif ncols == 3:
                widths = [avail * 0.20, avail * 0.30, avail * 0.50]
            else:
                widths = [avail / ncols] * ncols

            data = [[Paragraph(inline(c), s["th"]) for c in header]]
            for r in rows:
                r = (r + [""] * ncols)[:ncols]
                data.append([Paragraph(inline(c), s["td"]) for c in r])

            tbl = Table(data, colWidths=widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, SURFACE]),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend([Spacer(1, 4), tbl, Spacer(1, 10)])
            continue

        # --- headings ----------------------------------------------------
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_para(para)
            level, text = len(m.group(1)), m.group(2)
            if level == 1:
                story.append(Paragraph(inline(text), s["title"]))
                story.append(Spacer(1, 4))
                story.append(HRFlowable(width="100%", thickness=1.6,
                                        color=BRASS, spaceAfter=_t(10, 6)))
            elif level == 2:
                story.append(Spacer(1, 4))
                story.append(Paragraph(inline(text), s["h2"]))
                story.append(HRFlowable(width="100%", thickness=0.6,
                                        color=RULE, spaceAfter=_t(7, 4)))
            elif level == 3:
                story.append(Paragraph(inline(text), s["h3"]))
            else:
                story.append(Paragraph(inline(text), s["h4"]))
            i += 1
            continue

        # --- horizontal rule --------------------------------------------
        if re.match(r"^-{3,}$", stripped):
            flush_para(para)
            story.append(Spacer(1, 5))
            i += 1
            continue

        # --- blockquote --------------------------------------------------
        if stripped.startswith(">"):
            flush_para(para)
            block = []
            while i < n and lines[i].strip().startswith(">"):
                block.append(re.sub(r"^\s*>\s?", "", lines[i]).rstrip())
                i += 1
            chunks, cur = [], []
            for bl in block:
                if bl.strip():
                    cur.append(bl.strip())
                else:
                    if cur:
                        chunks.append(" ".join(cur))
                        cur = []
            if cur:
                chunks.append(" ".join(cur))

            inner = []
            for c in chunks:
                inner.append(Paragraph(inline(c), s["quote"]))
            tbl = Table([[inner]], colWidths=[PAGE_W - 2 * MARGIN])
            tbl.setStyle(TableStyle([
                ("LINEBEFORE", (0, 0), (0, -1), 2.2, BRASS),
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend([Spacer(1, 2), tbl, Spacer(1, 8)])
            continue

        # --- lists (indent-aware, supports nesting) ----------------------
        if re.match(r"^(\s*)([-*]|\d+\.)\s+", line):
            flush_para(para)
            raw = []  # (indent, ordered, text)
            while i < n and re.match(r"^(\s*)([-*]|\d+\.)\s+", lines[i]):
                m2 = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                indent = len(m2.group(1).expandtabs(4))
                ordered = bool(re.match(r"\d+\.", m2.group(2)))
                text = m2.group(3).rstrip()
                i += 1
                # wrapped continuation lines belong to this item
                while (i < n and lines[i].strip()
                       and not re.match(r"^(\s*)([-*]|\d+\.)\s+", lines[i])
                       and lines[i].startswith(("  ", "\t"))):
                    text += " " + lines[i].strip()
                    i += 1
                raw.append((indent, ordered, text))

            story.append(build_list(raw, 0, len(raw), s)[0])
            story.append(Spacer(1, _t(7, 4)))
            continue

        # --- blank / paragraph -------------------------------------------
        if not stripped:
            flush_para(para)
        else:
            para.append(stripped)
        i += 1

    flush_para(para)
    return story


# ------------------------------------------------------------- page chrome
def make_chrome(s, doc_title):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, MARGIN - 6, PAGE_W - MARGIN, MARGIN - 6)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(INK_SOFT)
        canvas.drawString(MARGIN, MARGIN - 16, doc_title)
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 16,
                               "Page %d" % canvas.getPageNumber())
        canvas.restoreState()
    return draw


def main():
    global TIGHT
    argv = [a for a in sys.argv[1:] if a != "--compact"]
    TIGHT = "--compact" in sys.argv

    src = Path(argv[0] if argv else "PITCH.md")
    out = Path(argv[1] if len(argv) > 1 else "AI_Interview_Bot_Pitch.pdf")

    md = src.read_text(encoding="utf-8")
    s = build_styles()
    story = render(md, s)

    # Running footer / metadata title come from the document's own H1,
    # with the following H2 as a subtitle when there is one.
    h1 = re.search(r"^#\s+(.*)$", md, re.M)
    h2 = re.search(r"^##\s+(?!\d)(.*)$", md, re.M)
    doc_title = h1.group(1).strip() if h1 else src.stem
    if h2 and h1 and md.index(h2.group(0)) - md.index(h1.group(0)) < 200:
        doc_title = "%s - %s" % (doc_title, h2.group(1).strip())
    footer = (doc_title.replace("—", "-").replace("–", "-")
              .replace("’", "'").replace("‘", "'")
              .encode("ascii", "ignore").decode("ascii"))

    doc = BaseDocTemplate(
        str(out), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + 6,
        title=doc_title, author="",
        subject="AI Interview Bot",
    )
    frame = Frame(MARGIN, MARGIN + 6,
                  PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN - 6, id="body")
    doc.addPageTemplates([PageTemplate(
        id="main", frames=[frame], onPage=make_chrome(s, footer))])
    doc.build(story)
    print("Wrote %s (%d KB)" % (out, out.stat().st_size // 1024))


if __name__ == "__main__":
    main()
