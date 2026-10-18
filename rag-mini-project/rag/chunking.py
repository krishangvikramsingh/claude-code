"""Sentence-aware chunking with character-based size and overlap."""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass

from .document_loader import Segment

_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


@dataclass
class Chunk:
    chunk_id: str
    doc: str            # source filename
    page: int | None
    section: str | None
    text: str
    n_chars: int
    text_hash: str

    def to_dict(self) -> dict:
        return asdict(self)


def split_sentences(text: str) -> list[str]:
    out: list[str] = []
    for para in re.split(r"\n+", text):
        out.extend(s.strip() for s in _SENT.split(para) if s.strip())
    return out


def _hard_split(sentence: str, size: int) -> list[str]:
    """Split an over-long sentence on word boundaries."""
    words, parts, cur = sentence.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > size:
            parts.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        parts.append(cur)
    return parts


def _join(items: list[str]) -> str:
    """Join units with a space, but keep a newline after heading-like units (no terminal punctuation)."""
    out = ""
    for i, it in enumerate(items):
        if i:
            out += "\n" if not re.search(r"[.!?:;,)\]\"']$", items[i - 1]) else " "
        out += it
    return out


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Pack whole sentences up to `size` chars; carry <= `overlap` chars of trailing sentences forward."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("require size > 0 and 0 <= overlap < size")
    sents: list[str] = []
    for s in split_sentences(text):
        sents.extend(_hard_split(s, size) if len(s) > size else [s])
    chunks, cur = [], []

    def length(items):
        return sum(len(x) for x in items) + max(len(items) - 1, 0)

    for s in sents:
        if cur and length(cur) + 1 + len(s) > size:
            chunks.append(_join(cur))
            carry: list[str] = []
            for prev in reversed(cur):  # trailing sentences that fit in the overlap budget
                if length([prev] + carry) <= overlap:
                    carry.insert(0, prev)
                else:
                    break
            cur = carry
            if cur and length(cur) + 1 + len(s) > size:  # overlap + new sentence must fit
                cur = []
        cur.append(s)
    if cur and (not chunks or _join(cur) != chunks[-1]):
        tail = _join(cur)
        # avoid emitting a tail that is wholly contained in the previous chunk
        if not chunks or tail not in chunks[-1]:
            chunks.append(tail)
    return chunks


def chunk_segments(doc_name: str, segments: list[Segment], size: int, overlap: int,
                   min_chars: int = 40) -> tuple[list[Chunk], dict]:
    """Chunk each segment separately so page/section metadata stays exact."""
    chunks: list[Chunk] = []
    skipped_short = 0
    n = 0
    for seg in segments:
        for t in chunk_text(seg.text, size, overlap):
            if len(t) < min_chars:
                skipped_short += 1
                continue
            n += 1
            chunks.append(Chunk(
                chunk_id=f"{doc_name}::c{n:04d}", doc=doc_name, page=seg.page, section=seg.section,
                text=t, n_chars=len(t), text_hash=hashlib.sha256(t.lower().encode()).hexdigest()[:16]))
    return chunks, {"skipped_short_chunks": skipped_short}


def validate_chunks(chunks: list[Chunk], size: int) -> list[str]:
    """Return a list of validation problems (empty list == valid)."""
    problems, seen = [], set()
    for c in chunks:
        if not c.text.strip():
            problems.append(f"{c.chunk_id}: empty text")
        if c.n_chars != len(c.text):
            problems.append(f"{c.chunk_id}: n_chars mismatch")
        if len(c.text) > size:
            problems.append(f"{c.chunk_id}: exceeds chunk size ({len(c.text)} > {size})")
        if c.chunk_id in seen:
            problems.append(f"{c.chunk_id}: duplicate id")
        seen.add(c.chunk_id)
    return problems
