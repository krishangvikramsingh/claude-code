"""
docx_helpers.py
===============
Small layer over python-docx for the project report: A4 layout, numbered headings,
captions with a figure/table registry (for the lists of figures/tables), tables with a
navy header row, shaded code blocks, equations, a footer with PAGE fields and a static
table of contents whose page numbers are filled in by a second build pass.
"""

from __future__ import annotations

import re

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

NAVY = RGBColor(0x14, 0x21, 0x3D)
TEAL = RGBColor(0x1B, 0x8A, 0x8F)
GREY = RGBColor(0x55, 0x55, 0x55)
BODY_FONT = "Calibri"
CODE_FONT = "Consolas"


def _set_cell_bg(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def _set_par_bg(par, hex_fill):
    pPr = par._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    pPr.append(shd)


def _field(run, instr):
    for t, txt in (("begin", None), (None, instr), ("separate", None), (None, "1"), ("end", None)):
        if t:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), t)
            run._r.append(el)
        elif txt == instr:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = instr
            run._r.append(it)
        else:
            tt = OxmlElement("w:t")
            tt.text = txt
            run._r.append(tt)


class Report:
    def __init__(self, pages=None):
        self.doc = Document()
        self.pages = pages or {}            # {key: page number} from the previous pass
        self.headings = []                  # (level, number, text)
        self.figures = []                   # (label, caption)
        self.tables = []                    # (label, caption)
        self.h1_no = 0
        self.h2_no = 0
        self.h3_no = 0
        self.fig_no = 0
        self.tab_no = 0
        self.appendix = False
        self._setup()

    # ------------------------------------------------------------------ setup
    def _setup(self):
        d = self.doc
        s = d.sections[0]
        s.page_height, s.page_width = Cm(29.7), Cm(21.0)
        s.left_margin = s.right_margin = Cm(2.4)
        s.top_margin, s.bottom_margin = Cm(2.3), Cm(2.2)
        s.different_first_page_header_footer = True
        st = d.styles
        n = st["Normal"]
        n.font.name = BODY_FONT
        n.font.size = Pt(11)
        n.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
        n.paragraph_format.space_after = Pt(6)
        n.paragraph_format.line_spacing = 1.15
        for name, size, color, before, after in (("Heading 1", 18, NAVY, 18, 8), ("Heading 2", 13.5, NAVY, 12, 4),
                                                 ("Heading 3", 11.5, TEAL, 8, 3)):
            h = st[name]
            h.font.name = BODY_FONT
            h.font.size = Pt(size)
            h.font.bold = True
            h.font.color.rgb = color
            h.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
            h.element.rPr.rFonts.set(qn("w:ascii"), BODY_FONT)
            h.element.rPr.rFonts.set(qn("w:hAnsi"), BODY_FONT)
            h.paragraph_format.space_before = Pt(before)
            h.paragraph_format.space_after = Pt(after)
            h.paragraph_format.keep_with_next = True
        cap = st["Caption"]
        cap.font.name = BODY_FONT
        cap.font.size = Pt(9.5)
        cap.font.italic = True
        cap.font.bold = False
        cap.font.color.rgb = GREY
        cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(10)
        # footer with page number (not on first page)
        fp = s.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = fp.add_run()
        r.font.size = Pt(9)
        r.font.color.rgb = GREY
        _field(r, "PAGE")
        s.first_page_header.is_linked_to_previous = False
        s.first_page_footer.is_linked_to_previous = False
        s.first_page_header.paragraphs[0].text = ""
        s.first_page_footer.paragraphs[0].text = ""
        hp = s.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        hr = hp.add_run("Digital Image Watermarking — hybrid DWT–DCT–SVD   |   NMIMS MPSTME · Image and Video Processing")
        hr.font.size = Pt(8.5)
        hr.font.color.rgb = GREY

    # ------------------------------------------------------------- text utils
    def _runs(self, par, text, size=None, color=None, italic=None):
        """Inline markup: **bold**, *italic*, `code`."""
        parts = re.split(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)", text)
        for p in parts:
            if not p:
                continue
            if p.startswith("**") and p.endswith("**"):
                r = par.add_run(p[2:-2]); r.bold = True
            elif p.startswith("`") and p.endswith("`"):
                r = par.add_run(p[1:-1]); r.font.name = CODE_FONT; r.font.size = Pt((size or 11) - 1.5)
                r._r.rPr.rFonts.set(qn("w:eastAsia"), CODE_FONT)
                r.font.color.rgb = RGBColor(0x8A, 0x1F, 0x1F)
                continue
            elif p.startswith("*") and p.endswith("*") and len(p) > 2:
                r = par.add_run(p[1:-1]); r.italic = True
            else:
                r = par.add_run(p)
            if size:
                r.font.size = Pt(size)
            if color is not None:
                r.font.color.rgb = color
            if italic:
                r.italic = True
        return par

    def para(self, text, align=None, size=None, space_after=None, keep=False, italic=False, color=None):
        p = self.doc.add_paragraph()
        self._runs(p, text, size=size, italic=italic, color=color)
        if align == "center":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "justify":
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if space_after is not None:
            p.paragraph_format.space_after = Pt(space_after)
        if keep:
            p.paragraph_format.keep_with_next = True
        return p

    def bullets(self, items, style="List Bullet"):
        for it in items:
            p = self.doc.add_paragraph(style=style)
            self._runs(p, it)
            p.paragraph_format.space_after = Pt(2)
        self.doc.paragraphs[-1].paragraph_format.space_after = Pt(8)

    def numbered(self, items):
        """Manually numbered list (Word's built-in numbering would continue across lists)."""
        for i, it in enumerate(items, 1):
            p = self.doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.9)
            p.paragraph_format.first_line_indent = Cm(-0.6)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(0.9))
            self._runs(p, f"{i}.\t{it}")
        self.doc.paragraphs[-1].paragraph_format.space_after = Pt(8)

    # ---------------------------------------------------------------- headings
    def h1(self, text, numbered=True, appendix=None):
        if appendix:
            self.appendix = True
            self.h1_no = appendix if isinstance(appendix, str) else self.h1_no
            num = f"Appendix {appendix}"
            label = f"{num}: {text}"
        elif numbered:
            self.h1_no += 1
            self.h2_no = self.h3_no = 0
            self.fig_no = self.tab_no = 0
            num = str(self.h1_no)
            label = f"{num}. {text}"
        else:
            num, label = "", text
        if appendix:
            self.h2_no = self.h3_no = 0
            self.fig_no = self.tab_no = 0
        p = self.doc.add_heading(label, level=1)
        self.headings.append((1, num, text, label))
        return p

    def h2(self, text):
        self.h2_no += 1
        self.h3_no = 0
        num = f"{self.h1_no}.{self.h2_no}"
        label = f"{num} {text}"
        self.doc.add_heading(label, level=2)
        self.headings.append((2, num, text, label))

    def h3(self, text):
        self.h3_no += 1
        num = f"{self.h1_no}.{self.h2_no}.{self.h3_no}"
        label = f"{num} {text}"
        self.doc.add_heading(label, level=3)
        self.headings.append((3, num, text, label))

    def page_break(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ------------------------------------------------------- figures / tables
    def _ref(self):
        return f"{self.h1_no}"

    def figure(self, path, caption, width_cm=15.0):
        self.fig_no += 1
        label = f"Figure {self._ref()}.{self.fig_no}"
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(path, width=Cm(width_cm))
        c = self.doc.add_paragraph(f"{label}: {caption}", style="Caption")
        self.figures.append((label, caption))
        return label

    def table(self, header, rows, caption, widths=None, size=9, align=None, first_col_bold=False):
        self.tab_no += 1
        label = f"Table {self._ref()}.{self.tab_no}"
        cap = self.doc.add_paragraph(f"{label}: {caption}".replace("`", ""), style="Caption")
        cap.paragraph_format.keep_with_next = True
        cap.paragraph_format.space_after = Pt(3)
        self.tables.append((label, caption))
        t = self.doc.add_table(rows=1, cols=len(header))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(header):
            c = t.rows[0].cells[i]
            c.text = ""
            _set_cell_bg(c, "14213D")
            r = c.paragraphs[0].add_run(str(h))
            r.bold = True
            r.font.size = Pt(size)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            c.paragraphs[0].paragraph_format.space_after = Pt(1)
        # repeat header row
        trPr = t.rows[0]._tr.get_or_add_trPr()
        th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
        for ri, row in enumerate(rows):
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                par = cells[i].paragraphs[0]
                par.paragraph_format.space_after = Pt(1)
                par.paragraph_format.line_spacing = 1.0
                self._runs(par, str(v), size=size)
                if first_col_bold and i == 0:
                    for r in par.runs:
                        r.bold = True
                if align and align[i] == "r":
                    par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                elif align and align[i] == "c":
                    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if ri % 2 == 1:
                    _set_cell_bg(cells[i], "F1F4F9")
        if widths:
            t.autofit = False
            tblPr = t._tbl.tblPr
            lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
            for i, w in enumerate(widths):
                t.columns[i].width = Cm(w)
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Cm(w)
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(4)
        return label

    def code(self, text, size=8.5):
        for line in text.strip("\n").split("\n"):
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.left_indent = Cm(0.3)
            r = p.add_run(line if line else " ")
            r.font.name = CODE_FONT
            r._r.rPr.rFonts.set(qn("w:eastAsia"), CODE_FONT)
            r.font.size = Pt(size)
            _set_par_bg(p, "F4F4F2")
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def equation(self, text, number=None):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(text)
        r.font.name = "Cambria Math"
        r._r.rPr.rFonts.set(qn("w:eastAsia"), "Cambria Math")
        r.font.size = Pt(11.5)
        if number:
            ts = p.paragraph_format.tab_stops
            r2 = p.add_run(f"\t({number})")
            r2.font.size = Pt(10)
            ts.add_tab_stop(Cm(16.2), WD_TAB_ALIGNMENT.RIGHT)

    def callout(self, text, fill="EAF4F4"):
        t = self.doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = t.rows[0].cells[0]
        _set_cell_bg(c, fill)
        c.text = ""
        self._runs(c.paragraphs[0], text, size=10.5)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # ------------------------------------------------------------- lists (TOC)
    def toc_entries(self, entries, title):
        """entries: list of (indent, text, key). Writes a dotted-leader list with page numbers."""
        self.doc.add_heading(title, level=1).paragraph_format.page_break_before = True
        for indent, text, key in entries:
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.left_indent = Cm(0.6 * indent)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(16.2), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            r = p.add_run(text + "\t" + str(self.pages.get(key, "0")))
            r.font.size = Pt(10 if indent else 10.5)
            r.bold = indent == 0

    def save(self, path):
        self.doc.save(path)
