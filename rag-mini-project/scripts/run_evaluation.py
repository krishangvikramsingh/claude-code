"""Run the full evaluation set against the persisted index.  Usage: python scripts/run_evaluation.py [--k 4]"""
import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rag.config import Settings, load_dotenv_if_present  # noqa: E402
from rag.evaluation import load_cases, run_evaluation, write_outputs  # noqa: E402
from rag.rag_pipeline import RAGPipeline  # noqa: E402

if __name__ == "__main__":
    load_dotenv_if_present()
    logging.getLogger("faiss").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int)
    a = ap.parse_args()
    s = Settings()
    results, summ = run_evaluation(RAGPipeline(s), load_cases(ROOT / "data/evaluation/eval_set.json"), a.k)
    write_outputs(results, summ, ROOT / "artifacts" / "evaluation")
    print(json.dumps(summ.__dict__, indent=2))
    for r in results:
        print(f"{r['id']} {'PASS' if r['pass'] else 'FAIL'} {r['category']:18} {r['failure_explanation']}")
