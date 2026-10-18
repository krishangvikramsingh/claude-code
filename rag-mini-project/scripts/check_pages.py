"""Convert docs/*.docx to PDF (LibreOffice) and validate page limits.  Usage: python scripts/check_pages.py"""
import json
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
LIMITS = {"project_report": 15, "dataset_knowledge_base": 2, "document_processing_module": None,
          "embedding_vector_database": 2, "llm_prompt_engineering": 2, "testing_evaluation": 3}

if __name__ == "__main__":
    out = DOCS / "pdf"
    out.mkdir(exist_ok=True)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out)] + [str(DOCS / f"{n}.docx") for n in LIMITS],
                   check=True, capture_output=True, timeout=300)
    res, ok = {}, True
    for n, lim in LIMITS.items():
        pages = len(PdfReader(str(out / f"{n}.pdf")).pages)
        good = lim is None or pages <= lim
        ok &= good
        res[n] = {"pages": pages, "limit": lim, "within_limit": good}
        print(f"{n:32} pages={pages:2} limit={lim}  {'OK' if good else 'EXCEEDS'}")
    (ROOT / "artifacts" / "page_counts.json").write_text(json.dumps(res, indent=2))
    sys.exit(0 if ok else 1)
