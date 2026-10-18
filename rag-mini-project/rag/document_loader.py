"""Text extraction for PDF, DOCX, Markdown and plain-text files.

Each loader returns a list of `Segment`s carrying page / section metadata.
Limitations: scanned (image-only) PDFs yield no text and are rejected (no OCR);
DOCX has no reliable page numbers, so `page` is None; tables/images are ignored.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .errors import EmptyDocumentError, IngestionError, UnsupportedFormatError

SUPPORTED = {".pdf", ".docx", ".md", ".txt"}


@dataclass
class Segment:
    text: str
    page: int | None = None
    section: str | None = None


def _load_pdf(path: Path) -> list[Segment]:
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise IngestionError(f"{path.name}: encrypted PDF is not supported")
        return [Segment(text=(pg.extract_text() or ""), page=i) for i, pg in enumerate(reader.pages, 1)]
    except IngestionError:
        raise
    except (PyPdfError, ValueError, OSError, KeyError, TypeError) as e:
        raise IngestionError(f"{path.name}: corrupted or unreadable PDF ({type(e).__name__})") from e


def _load_docx(path: Path) -> list[Segment]:
    import zipfile

    from docx import Document

    try:
        doc = Document(str(path))
    except Exception as e:  # python-docx raises PackageNotFoundError, BadZipFile, KeyError, ... for bad files
        raise IngestionError(f"{path.name}: corrupted or unreadable DOCX ({type(e).__name__})") from e
    segs: list[Segment] = []
    section, buf = None, []

    def flush():
        if any(b.strip() for b in buf):
            segs.append(Segment("\n".join(buf), None, section))
        buf.clear()

    for p in doc.paragraphs:
        style = (p.style.name or "") if p.style is not None else ""
        if style.startswith("Heading") or style == "Title":
            flush()
            section = p.text.strip() or section
        elif p.text.strip():
            buf.append(p.text)
    flush()
    return segs


_MD_HEAD = re.compile(r"^(#{1,6})\s+(.*)$")


def _load_text(path: Path, markdown: bool) -> list[Segment]:
    try:
        raw = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as e:
        raise IngestionError(f"{path.name}: not valid UTF-8 text") from e
    segs: list[Segment] = []
    section, buf = None, []

    def flush():
        if any(b.strip() for b in buf):
            segs.append(Segment("\n".join(buf), None, section))
        buf.clear()

    lines = raw.splitlines()
    for i, line in enumerate(lines):
        m = _MD_HEAD.match(line) if markdown else None
        # plain-text headings: a line followed by a '---' underline (as written by the sample KB)
        is_txt_head = (not markdown and i + 1 < len(lines) and re.fullmatch(r"-{3,}", lines[i + 1].strip() or "x")
                       and line.strip())
        if m:
            flush()
            section = m.group(2).strip()
        elif is_txt_head:
            flush()
            section = line.strip()
        elif not re.fullmatch(r"[-=]{3,}", line.strip()):
            buf.append(line)
    flush()
    return segs


def load_document(path: Path) -> list[Segment]:
    """Extract raw segments from `path`. Raises IngestionError subclasses on failure."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise UnsupportedFormatError(f"{path.name}: unsupported format '{ext}' (supported: {', '.join(sorted(SUPPORTED))})")
    if not path.is_file():
        raise IngestionError(f"{path.name}: file not found")
    if path.stat().st_size == 0:
        raise EmptyDocumentError(f"{path.name}: file is empty")
    if ext == ".pdf":
        segs = _load_pdf(path)
    elif ext == ".docx":
        segs = _load_docx(path)
    else:
        segs = _load_text(path, markdown=(ext == ".md"))
    if not any(s.text.strip() for s in segs):
        raise EmptyDocumentError(f"{path.name}: no extractable text (scanned PDF or empty document?)")
    return segs
