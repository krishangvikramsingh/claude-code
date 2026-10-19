"""Build Cyberion_Master_Research_Report.docx from the Markdown parts.

Usage (from repo root):  python3 research/cyberion/tools/build_docx.py
Needs pandoc on PATH. Steps: combine parts -> pandoc -> post-process the
OOXML (landscape A4, table styling, page numbers, heading page breaks).
"""
import os, re, shutil, subprocess, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Cyberion_Master_Research_Report.docx")
PARTS = ["01_Decision_Brief_and_Pain_Points.md", "02_Opportunities_Ranking_Business_Cases.md",
         "03_IIoT_Catalogue_PackQuote_Platform.md", "04_Competition_and_Validation_Toolkit.md",
         "05_Pricing_Financials_GTM_Roadmap_Strategy.md", "06_First_90_Days_and_Decision_Register.md"]
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def strip_local_links(md):
    # [text](something.md) / [text](model/...) -> text ; keep http(s) links and #anchors
    return re.sub(r"\[([^\]]+)\]\((?!https?://|#)[^)]+\)", r"\1", md)


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def combined_markdown():
    readme = read("README.md")
    # README body becomes an "About this report" chapter (drop its own H1 title lines)
    readme = re.sub(r"\A# .*\n\n\*\*.*\*\*\n", "", readme)
    readme = re.sub(r"## Document map.*?(?=\n## )", "", readme, flags=re.S)
    readme = readme.replace("## Re-running the models", "## Re-running the models (repository files)")
    chunks = ["# About this report\n\n" + readme.replace("\n## ", "\n## ")]
    for p in PARTS:
        chunks.append(read(p))
    sources = read("SOURCES.md").replace("# Source register", "# Appendix: Source register", 1)
    chunks.append(sources)
    md = "\n\n".join(strip_local_links(c) for c in chunks)
    # Explicit heading ids so the contents list links reliably
    fixed, in_code = [], False
    item = re.compile(r"^\s*([-*]|\d+\.) ")
    for line in md.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
        prev = fixed[-1] if fixed else ""
        if (not in_code and item.match(line) and prev.strip() and not item.match(prev)
                and not prev.startswith("|") and not prev.startswith(" ")):
            fixed.append("")
        fixed.append(line)
    md = "\n".join(fixed)
    toc, out, n = [], [], 0
    in_code = False
    for line in md.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
        m = None if in_code else re.match(r"^(#{1,2}) (.+)$", line)
        if m:
            n += 1
            hid = f"sec{n}"
            text = m.group(2).strip()
            toc.append((len(m.group(1)), text, hid))
            line = f"{line} {{#{hid}}}"
        out.append(line)
    toc_md = ["# Contents {.unnumbered}", ""]
    for lvl, text, hid in toc:
        plain = re.sub(r"[*_`]", "", text)
        toc_md.append(("" if lvl == 1 else "    ") + f"- [{plain}](#{hid})")
    meta = ("---\ntitle: \"Cyberion Tech Innovations\"\n"
            "subtitle: \"Master research report: industrial AI, B2B SaaS, automation and IoT for printing, packaging, plastics and polymers (India-first)\"\n"
            "date: \"19 October 2026\"\n---\n\n")
    return meta + "\n".join(toc_md) + "\n\n" + "\n".join(out)


def patch_styles(xml):
    # pandoc's styles.xml is pretty-printed with attributes in varying order, so match loosely
    xml = re.sub(r"<w:rFonts [^>]*/>", '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>', xml)
    xml = re.sub(r"<w:color [^>]*/>", '<w:color w:val="1F3864"/>', xml)
    # Heading 1 (each part) starts on a new page; pageBreakBefore must follow keepLines
    def h1(m):
        return m.group(0).replace("<w:keepLines />", "<w:keepLines /><w:pageBreakBefore />", 1)
    xml = re.sub(r'<w:style [^>]*w:styleId="Heading1"[^>]*>.*?</w:style>', h1, xml, count=1, flags=re.S)
    # Table style: borders, compact cell margins, 8 pt text, shaded bold header row
    table_style = (
        '<w:style w:type="table" w:default="1" w:styleId="Table"><w:name w:val="Table"/><w:basedOn w:val="TableNormal"/><w:uiPriority w:val="59"/><w:qFormat/>'
        '<w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/></w:pPr>'
        '<w:rPr><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
        '<w:tblPr><w:tblBorders>'
        + "".join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>' for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
        + '</w:tblBorders><w:tblCellMar><w:top w:w="30" w:type="dxa"/><w:left w:w="70" w:type="dxa"/>'
        '<w:bottom w:w="30" w:type="dxa"/><w:right w:w="70" w:type="dxa"/></w:tblCellMar></w:tblPr>'
        '<w:tblStylePr w:type="firstRow"><w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr>'
        '<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="1F3864"/></w:tcPr></w:tblStylePr></w:style>')
    xml = re.sub(r'<w:style [^>]*w:styleId="Table"[^>]*>.*?</w:style>', lambda m: table_style, xml, count=1, flags=re.S)
    return xml


TEXT_WIDTH = 16838 - 2 * 907  # landscape A4 minus margins, in DXA


def size_columns(m):
    tbl = m.group(0)
    rows = [re.findall(r"<w:tc>.*?</w:tc>", r, flags=re.S) for r in re.findall(r"<w:tr>.*?</w:tr>", tbl, flags=re.S)]
    ncols = max(len(r) for r in rows)
    lens = [[] for _ in range(ncols)]
    longest_word = [0] * ncols
    for r in rows:
        for i, c in enumerate(r):
            text = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", c))
            lens[i].append(len(text))
            longest_word[i] = max([longest_word[i]] + [len(w) for w in text.split() if not w.startswith("http")])
    weights = []
    for i in range(ncols):
        mx, mean = max(lens[i] or [1]), sum(lens[i]) / max(1, len(lens[i]))
        weights.append(max(5, longest_word[i] * 1.5, 0.5 * min(mx, 70) + 0.5 * mean))
    total = sum(weights)
    widths = [int(TEXT_WIDTH * w / total) for w in weights]
    widths[-1] += TEXT_WIDTH - sum(widths)
    look = re.search(r"<w:tblLook [^>]*/>", tbl)
    tblpr = ('<w:tblPr><w:tblStyle w:val="Table"/><w:tblW w:w="%d" w:type="dxa"/><w:tblLayout w:type="fixed"/>%s</w:tblPr>'
             % (TEXT_WIDTH, look.group(0) if look else ""))
    tbl = re.sub(r"<w:tblPr>.*?</w:tblPr>", lambda _: tblpr, tbl, count=1, flags=re.S)
    grid = "<w:tblGrid>" + "".join('<w:gridCol w:w="%d"/>' % w for w in widths) + "</w:tblGrid>"
    tbl = re.sub(r"<w:tblGrid>.*?</w:tblGrid>", lambda _: grid, tbl, count=1, flags=re.S)

    def fix_row(rm):
        idx = iter(range(ncols))
        return re.sub(r"<w:tcPr ?/>|<w:tcPr>", lambda _: '<w:tcPr><w:tcW w:w="%d" w:type="dxa"/>' % widths[min(next(idx), ncols - 1)] + ("</w:tcPr>" if _.group(0).endswith("/>") else ""), rm.group(0))
    return re.sub(r"<w:tr>.*?</w:tr>", fix_row, tbl, flags=re.S)


def patch_document(xml):
    # Landscape A4 with 1.6 cm margins and a footer reference
    sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFooterCyb"/>'
            '<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>'
            '<w:pgMar w:top="907" w:right="907" w:bottom="907" w:left="907" w:header="454" w:footer="454" w:gutter="0"/>'
            '<w:titlePg w:val="0"/></w:sectPr>')
    xml = re.sub(r"<w:sectPr\b[^>]*/>|<w:sectPr\b.*?</w:sectPr>", lambda m: sect, xml, flags=re.S)
    if 'xmlns:r=' not in xml[:2000]:
        xml = xml.replace("<w:document ", '<w:document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" ', 1)
    # Tables: fixed full text width, columns weighted by their content
    xml = re.sub(r"<w:tbl>.*?</w:tbl>", size_columns, xml, flags=re.S)
    # (pandoc already marks the header row with tblHeader, so it repeats across pages)
    # Table text: force 8 pt on every run inside tables (Compact style would otherwise win)
    def shrink(tbl):
        t = tbl.group(0)
        t = re.sub(r"<w:r>(?!<w:rPr>)", "<w:r><w:rPr><w:sz w:val=\"16\"/><w:szCs w:val=\"16\"/></w:rPr>", t)
        t = re.sub(r"<w:r><w:rPr>(?!<w:sz )", "<w:r><w:rPr><w:sz w:val=\"16\"/><w:szCs w:val=\"16\"/>", t)
        return t
    xml = re.sub(r"<w:tbl>.*?</w:tbl>", shrink, xml, flags=re.S)
    return xml


FOOTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          f'<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
          '<w:r><w:rPr><w:sz w:val="16"/><w:color w:val="7F7F7F"/></w:rPr><w:t xml:space="preserve">Cyberion Tech Innovations · Master research report · page </w:t></w:r>'
          '<w:r><w:rPr><w:sz w:val="16"/><w:color w:val="7F7F7F"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
          '<w:r><w:rPr><w:sz w:val="16"/><w:color w:val="7F7F7F"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
          '<w:r><w:rPr><w:sz w:val="16"/><w:color w:val="7F7F7F"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
          '<w:r><w:rPr><w:sz w:val="16"/><w:color w:val="7F7F7F"/></w:rPr><w:t>1</w:t></w:r>'
          '<w:r><w:rPr><w:sz w:val="16"/><w:color w:val="7F7F7F"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')


def main():
    tmp = tempfile.mkdtemp()
    md_path = os.path.join(tmp, "report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(combined_markdown())
    raw = os.path.join(tmp, "raw.docx")
    subprocess.run(["pandoc", md_path, "-f", "markdown+pipe_tables-auto_identifiers", "-o", raw], check=True)
    with zipfile.ZipFile(raw) as zin, zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/styles.xml":
                data = patch_styles(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/document.xml":
                data = patch_document(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/_rels/document.xml.rels":
                data = data.decode("utf-8").replace("</Relationships>",
                    '<Relationship Id="rIdFooterCyb" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>').encode("utf-8")
            elif item.filename == "[Content_Types].xml":
                data = data.decode("utf-8").replace("</Types>",
                    '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>').encode("utf-8")
            zout.writestr(item, data)
        zout.writestr("word/footer1.xml", FOOTER)
    shutil.rmtree(tmp)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
