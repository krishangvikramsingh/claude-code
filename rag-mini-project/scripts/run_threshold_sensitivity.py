"""POST-HOC sensitivity of the extractive abstention threshold (min_coverage) on the evaluation set.
Informational only: the default (0.34) was fixed before the first evaluation run and is NOT changed by this analysis,
because choosing a threshold on the same set that is then reported would overstate performance."""
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rag.config import Settings  # noqa: E402
from rag.evaluation import load_cases, run_evaluation  # noqa: E402
from rag.rag_pipeline import RAGPipeline  # noqa: E402

if __name__ == "__main__":
    logging.getLogger("faiss").setLevel(logging.WARNING)
    cases = load_cases(ROOT / "data/evaluation/eval_set.json")
    rows = []
    for cov in (0.15, 0.2, 0.25, 0.3, 0.34, 0.4):
        res, summ = run_evaluation(RAGPipeline(Settings().with_(min_coverage=cov)), cases)
        by = {c["id"]: c for c in cases}
        wrong_answer_on_unanswerable = sum(1 for r in res if by[r["id"]]["expected_behavior"] == "abstain" and not r["abstained"])
        rows.append({"min_coverage": cov, "passed": f"{summ.passed}/{summ.n}", "wrongly_abstained": summ.abstention["wrongly_abstained"],
                     "unanswerable_not_refused": wrong_answer_on_unanswerable,
                     "failed_ids": [r["id"] for r in res if not r["pass"]]})
        print(rows[-1])
    out = ROOT / "artifacts" / "experiments" / "threshold_sensitivity.json"
    out.write_text(json.dumps(rows, indent=2))
