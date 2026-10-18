"""Sweep embedder x chunk size x top-k and record actual retrieval / answer metrics.

Usage: python scripts/run_experiments.py   (writes artifacts/experiments/results.json + results.md)
Overlap is fixed at 20% of chunk size. Each configuration builds its own index in a scratch directory.
"""
import json
import logging
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rag.config import Settings  # noqa: E402
from rag.evaluation import load_cases, retrieval_metrics, run_evaluation  # noqa: E402
from rag.ingestion import build_index  # noqa: E402
from rag.rag_pipeline import RAGPipeline  # noqa: E402

OUT = ROOT / "artifacts" / "experiments"

if __name__ == "__main__":
    logging.getLogger("faiss").setLevel(logging.WARNING)
    logging.disable(logging.INFO)
    cases = load_cases(ROOT / "data/evaluation/eval_set.json")
    rows = []
    for emb in ("lsa", "tfidf"):
        for size in (250, 500, 800):
            s0 = Settings().with_(embedder=emb, chunk_size=size, chunk_overlap=size // 5, index_dir=OUT / f"idx_{emb}_{size}")
            rep = build_index(s0)
            for k in (1, 3, 5):
                s = s0.with_(top_k=k)
                results, summ = run_evaluation(RAGPipeline(s), cases, k)
                r = summ.retrieval
                rows.append({"embedder": emb, "chunk_size": size, "overlap": size // 5, "n_chunks": rep.total_chunks, "k": k,
                             "precision_at_k": r["precision_at_k"], "recall_at_k": r["recall_at_k"], "mrr": r["mrr"],
                             "hit_at_k": r["hit_at_k"], "cases_passed": f"{summ.passed}/{summ.n}"})
                print(rows[-1], flush=True)
            shutil.rmtree(s0.index_dir)  # keep the submission small; results are recorded below
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    hdr = "| embedder | chunk | overlap | #chunks | k | P@k | R@k | MRR | Hit@k | passed |\n|---|---|---|---|---|---|---|---|---|---|\n"
    (OUT / "results.md").write_text(hdr + "\n".join(
        f"| {r['embedder']} | {r['chunk_size']} | {r['overlap']} | {r['n_chunks']} | {r['k']} | {r['precision_at_k']:.3f} | "
        f"{r['recall_at_k']:.3f} | {r['mrr']:.3f} | {r['hit_at_k']:.3f} | {r['cases_passed']} |" for r in rows), encoding="utf-8")
