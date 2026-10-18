"""End-to-end pipeline: question -> retrieval -> prompt -> generation -> answer + sources."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .config import Settings
from .generation import Generation, make_generator
from .prompt_templates import build_prompt
from .retrieval import Retrieved, Retriever


@dataclass
class RAGAnswer:
    question: str
    answer: str
    abstained: bool
    cited: list[str]
    retrieved: list[Retrieved]
    provider: str
    diagnostics: dict = field(default_factory=dict)

    def sources(self) -> list[dict]:
        out = []
        for r in self.retrieved:
            out.append({"label": r.label, "doc": r.chunk.doc, "page": r.chunk.page, "section": r.chunk.section,
                        "chunk_id": r.chunk.chunk_id, "score": round(r.score, 4), "cited": r.label in self.cited})
        return out


class RAGPipeline:
    def __init__(self, s: Settings):
        self.s = s
        self.retriever = Retriever(s)
        self.generator = make_generator(s)

    def ask(self, question: str, k: int | None = None, doc_filter: set[str] | None = None) -> RAGAnswer:
        t0 = time.time()
        hits = self.retriever.retrieve(question, k, doc_filter)       # raises RetrievalError on bad input
        t1 = time.time()
        built = build_prompt(question, hits, self.s.max_context_chars)
        gen: Generation = self.generator.generate(question, built)
        t2 = time.time()
        diag = {"retrieval_ms": round((t1 - t0) * 1000, 1), "generation_ms": round((t2 - t1) * 1000, 1),
                "k": k or self.s.top_k, "passages_in_prompt": len(built.used), "passages_dropped": built.dropped,
                "context_truncated": built.truncated, "injection_flagged": built.flagged,
                "top_score": round(hits[0].score, 4) if hits else None, **gen.notes}
        return RAGAnswer(question, gen.text, gen.abstained, gen.cited, hits, gen.provider, diag)
