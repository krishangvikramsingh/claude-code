"""Generate diagrams/*.png from code (matplotlib). Reproduce with: python scripts/make_diagrams.py
The Mermaid files in diagrams/*.mmd are textual equivalents of the same flows (not rendered by this script)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "diagrams"
C = {"io": "#E8F1FB", "proc": "#FFF4D6", "err": "#FDE3E1", "store": "#E4F4E6", "edge": "#37474F"}


def box(ax, x, y, w, h, title, body="", fc=C["proc"], fs=9.5, bfs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=C["edge"], lw=1.2))
    ax.text(x + w / 2, y + h - 0.13, title, ha="center", va="top", fontsize=fs, fontweight="bold")
    if body:
        ax.text(x + w / 2, y + h - 0.42, body, ha="center", va="top", fontsize=bfs, linespacing=1.3)


def arrow(ax, p, q, style="-|>", ls="-", color=None):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=14, lw=1.3, color=color or C["edge"], linestyle=ls))


def architecture():
    fig, ax = plt.subplots(figsize=(13, 7.4))
    ax.set_xlim(0, 13); ax.set_ylim(0, 7.4); ax.axis("off")
    ax.text(6.5, 7.2, "System architecture: offline indexing and online question answering", ha="center", fontsize=13, fontweight="bold")
    ax.text(0.1, 6.6, "OFFLINE  (scripts/build_index.py or UI 'Rebuild index')", fontsize=10, fontweight="bold", color="#1B5E20")
    xs = [0.1, 2.75, 5.4, 8.05, 10.7]
    offl = [("Knowledge base", "data/knowledge_base\nPDF / DOCX / MD / TXT", C["io"]),
            ("Document processing", "document_loader\ntext_cleaner\nchunking + validation", C["proc"]),
            ("Embedding", "embeddings.py\nLSA / TF-IDF (default)\nor sentence-transformers\nL2-normalised vectors", C["proc"]),
            ("Vector index", "vector_store.py\nFAISS IndexFlatIP\n(cosine similarity)", C["proc"]),
            ("Persisted artifacts", "index.faiss, chunks.jsonl\nmanifest.json (file hashes)\nembedder.joblib\ningest_report.json", C["store"])]
    for x, (t, b, fc) in zip(xs, offl):
        box(ax, x, 4.6, 2.2, 1.8, t, b, fc)
    for a, b in zip(xs, xs[1:]):
        arrow(ax, (a + 2.2, 5.5), (b, 5.5))
    ax.text(0.1, 3.95, "ONLINE  (app.py -> rag_pipeline.RAGPipeline.ask)", fontsize=10, fontweight="bold", color="#0D47A1")
    onl = [("User question", "Streamlit UI\ntop-k, provider,\ndocument filter", C["io"]),
           ("Retriever", "retrieval.py\nembed query (same model)\ntop-k cosine search", C["proc"]),
           ("Prompt builder", "prompt_templates.py\nrules + <passage> blocks\nsanitise, context budget", C["proc"]),
           ("Generator", "generation.py\nextractive (offline) |\nAnthropic | Ollama\ncitation validation", C["proc"]),
           ("Answer + sources", "answer with [S#] labels\nfile, page, section,\nscore, passage text,\ndiagnostics / abstention", C["io"])]
    for x, (t, b, fc) in zip(xs, onl):
        box(ax, x, 1.7, 2.2, 1.9, t, b, fc)
    for a, b in zip(xs, xs[1:]):
        arrow(ax, (a + 2.2, 2.65), (b, 2.65))
    # artifacts used by retriever
    arrow(ax, (11.8, 4.6), (4.0, 3.6), ls="--")
    ax.text(8.6, 4.2, "index + chunk table + embedder loaded at query time", fontsize=8, style="italic", ha="center", bbox=dict(fc="white", ec="none", pad=1.5))
    ax.text(0.1, 1.2, "Cross-cutting: rag/config.py (settings from environment / .env, no secrets in code)  |  rag/errors.py (user-safe errors)  |  "
            "rag/evaluation.py (metrics)  |  tests/ (pytest)", fontsize=8.5)
    ax.text(0.1, 0.8, "Abstention: if top similarity < threshold or no answer sentence covers the question terms, the system replies "
            "\"I could not find this in the knowledge base.\"", fontsize=8.5)
    fig.savefig(OUT / "system_architecture.png", dpi=170, bbox_inches="tight"); plt.close(fig)


def doc_processing():
    stages = [
        ("1  Discover & fingerprint", "list files in KB folder (hidden files skipped); only .pdf .docx .md .txt are supported - other extensions are reported as failed\nSHA-256 per file -> manifest 'files' (used for stale-index detection)",
         "list of source files", C["io"]),
        ("2  Extract text  (document_loader.py)", "PDF: pypdf, one Segment per page (page no.)   |   DOCX: python-docx, split at Heading/Title styles (section)\nMD: '#' headings -> section   |   TXT: 'Heading' + '---' underline -> section\nempty file / no text / corrupted / encrypted / non-UTF-8 -> error recorded for that file",
         "Segment(text, page | None, section | None)", C["proc"]),
        ("3  Clean & normalise  (text_cleaner.py)", "drop header/footer lines repeated on >= 60% of pages and bare page numbers (paged docs only)\nUnicode NFKC, strip control chars, de-hyphenate line breaks, heading-line paragraph breaks,\ncollapse whitespace, drop empty segments  ->  stats: chars before/after, lines removed",
         "cleaned Segments", C["proc"]),
        ("4  Chunk  (chunking.py)", "per segment (so page/section stay exact): split into sentences, pack whole sentences up to chunk_size (default 500 chars),\ncarry trailing sentences <= chunk_overlap (default 100 chars) into the next chunk; hard-split over-long sentences;\nskip chunks < 40 chars. Chunk id = <file>::c<NNNN>; sha256 of lower-cased text stored",
         "Chunk(chunk_id, doc, page,\nsection, text, n_chars,\ntext_hash)", C["proc"]),
        ("5  Validate chunks", "non-empty text, n_chars == len(text), len <= chunk_size, unique ids, at least one chunk\nany violation -> file marked 'failed' (message in ingest report); other files continue",
         "validated chunks per file", C["proc"]),
        ("6  De-duplicate", "identical (case-insensitive) chunk text across files: keep first occurrence, count 'duplicates_removed'",
         "unique chunk list", C["proc"]),
        ("7  Embed  (embeddings.py)", "fit embedder on chunk texts (TF-IDF 1-2 grams + TruncatedSVD for 'lsa'; vocabulary-sized for 'tfidf';\npretrained model for 'sentence-transformers'), encode all chunks, L2-normalise -> float32 matrix",
         "vectors [n_chunks x dim]", C["proc"]),
        ("8  Index  (vector_store.py)", "faiss.IndexFlatIP.add(vectors)   (inner product on unit vectors == cosine similarity)",
         "FAISS index", C["proc"]),
        ("9  Persist", "index.faiss | chunks.jsonl (all metadata) | manifest.json (embedder, dim, chunk settings, file hashes, counts) |\nembedder.joblib | ingest_report.json (per-file status, counts, messages, timing)",
         "artifacts/index/", C["store"]),
    ]
    h, gap = 1.12, 0.32
    H = len(stages) * (h + gap) + 1.4
    fig, ax = plt.subplots(figsize=(13, H * 0.95))
    ax.set_xlim(0, 13); ax.set_ylim(0, H); ax.axis("off")
    ax.text(6.5, H - 0.35, "Document processing and indexing pipeline (as implemented in rag/ingestion.py)", ha="center", fontsize=13, fontweight="bold")
    y = H - 1.0 - h
    for i, (t, body, out, fc) in enumerate(stages):
        box(ax, 0.1, y, 9.6, h, t, body, fc, fs=10, bfs=8)
        box(ax, 10.0, y + 0.18, 2.9, h - 0.36, "output", out, C["io"], fs=8.5, bfs=7.8)
        arrow(ax, (9.7, y + h / 2), (10.0, y + h / 2))
        if i < len(stages) - 1:
            arrow(ax, (4.9, y), (4.9, y - gap))
        y -= h + gap
    # error / logging side notes
    ax.text(0.1, 0.35, "Error handling: a failing file is recorded in ingest_report.json (status 'failed' + user-safe message) and never aborts the run; "
            "if no chunks remain, build_index raises IngestionError.\nLogging: per-file segments/chunks, header-footer lines removed, "
            "short chunks skipped, duplicates removed, index size and build time (no document contents).", fontsize=8.3, va="center")
    fig.savefig(OUT / "document_processing_pipeline.png", dpi=170, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    architecture(); doc_processing(); print("diagrams written to", OUT)
