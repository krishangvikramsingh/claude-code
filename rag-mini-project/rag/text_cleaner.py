"""Cleaning / normalisation of extracted text."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from .document_loader import Segment

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_PAGE_NUM = re.compile(r"^\s*(page\s+)?\d{1,4}(\s*(/|of)\s*\d{1,4})?\s*$", re.I)


def _mark_heading_lines(text: str) -> str:
    """Heuristic: a short, capitalised line without terminal punctuation that is followed by a capitalised line
    is a heading -> force a paragraph break after it (PDF extraction loses heading styling, so headings would
    otherwise be glued to the next sentence). Limitation: can misfire on hard-wrapped lines that happen to match."""
    lines = text.split("\n")
    out = []
    for i, ln in enumerate(lines):
        out.append(ln)
        st = ln.strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if (st and st[0].isupper() and len(st) <= 60 and len(st.split()) <= 8 and not re.search(r"[.!?:;,]$", st)
                and nxt and (nxt[0].isupper() or nxt[0].isdigit())):
            out.append("")
    return "\n".join(out)


def normalize_text(text: str) -> str:
    """Unicode NFKC, strip control chars, de-hyphenate line breaks, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text)
    text = _CTRL.sub(" ", text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)          # join words hyphenated across lines
    text = _mark_heading_lines(text)
    paragraphs = re.split(r"\n\s*\n", text)
    out = []
    for p in paragraphs:
        p = re.sub(r"\s*\n\s*", " ", p)                    # single newlines -> space
        p = re.sub(r"[ \t]{2,}", " ", p).strip()
        if p:
            out.append(p)
    return "\n\n".join(out)


def _line_key(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip().lower())


def remove_repeated_lines(segments: list[Segment], min_pages: int = 2, ratio: float = 0.6) -> tuple[list[Segment], int]:
    """Drop header/footer lines repeated on >= `ratio` of paged segments, and bare page numbers.

    Returns (segments, number_of_lines_removed). Only applies to segments that have page numbers.
    """
    paged = [s for s in segments if s.page is not None]
    removed = 0
    repeated: set[str] = set()
    if len(paged) >= min_pages:
        counts: Counter[str] = Counter()
        for s in paged:
            keys = {_line_key(ln) for ln in s.text.splitlines() if ln.strip()}
            counts.update(keys)
        repeated = {k for k, c in counts.items() if c / len(paged) >= ratio and len(k) < 120}
    result = []
    for s in segments:
        if s.page is None:
            result.append(s)
            continue
        kept = []
        for ln in s.text.splitlines():
            if _line_key(ln) in repeated or _PAGE_NUM.match(ln):
                removed += 1 if ln.strip() else 0
            else:
                kept.append(ln)
        result.append(Segment("\n".join(kept), s.page, s.section))
    return result, removed


def clean_segments(segments: list[Segment]) -> tuple[list[Segment], dict]:
    """Full cleaning: repeated header/footer removal, normalisation, drop empty segments."""
    before = sum(len(s.text) for s in segments)
    segs, removed = remove_repeated_lines(segments)
    cleaned = [Segment(normalize_text(s.text), s.page, s.section) for s in segs]
    dropped = sum(1 for s in cleaned if not s.text)
    cleaned = [s for s in cleaned if s.text]
    after = sum(len(s.text) for s in cleaned)
    return cleaned, {"chars_before": before, "chars_after": after,
                     "header_footer_lines_removed": removed, "empty_segments_dropped": dropped}
