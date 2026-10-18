"""Create Coursera_<roll1>_<roll2>_<roll3>.zip with the seven required components.

Roll numbers come from docs/team_info.json (placeholders Rollno1..3 until filled in).
Run after build_docs.py / check_pages.py.  Usage: python scripts/package_submission.py
"""
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEAM = json.loads((ROOT / "docs" / "team_info.json").read_text())
ROLLS = [s["roll_no"] for s in TEAM["students"]]
NAME = "Coursera_" + "_".join(ROLLS)
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".venv", "venv", ".git", "index", "node_modules"}
EXCLUDE_FILES = {".env", ".DS_Store", "streamlit.log", "streamlit.pid"}
SECRET = re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}")


def keep(p: Path) -> bool:
    rel = p.relative_to(ROOT)
    parts = set(rel.parts)
    if parts & EXCLUDE_DIRS or p.name in EXCLUDE_FILES or p.suffix in (".pyc", ".zip"):
        return False
    return not (rel.parts[:2] == ("artifacts", "experiments") and rel.name.startswith("idx_"))


def main() -> None:
    stage = ROOT / "artifacts" / "_stage"
    if stage.exists():
        shutil.rmtree(stage)
    top = stage / NAME
    d = ROOT / "docs"
    comps = {
        "1_Project_Report": [d / "project_report.docx", d / "pdf/project_report.pdf"],
        "2_Dataset_Knowledge_Base": [d / "dataset_knowledge_base.docx", d / "pdf/dataset_knowledge_base.pdf", ROOT / "data/knowledge_base"],
        "3_Document_Processing_Module": [d / "document_processing_module.docx", d / "pdf/document_processing_module.pdf",
                                         ROOT / "diagrams/document_processing_pipeline.png", ROOT / "diagrams/document_processing_pipeline.mmd"],
        "4_Embedding_Vector_Database": [d / "embedding_vector_database.docx", d / "pdf/embedding_vector_database.pdf", ROOT / "artifacts/experiments"],
        "5_LLM_Prompt_Engineering": [d / "llm_prompt_engineering.docx", d / "pdf/llm_prompt_engineering.pdf"],
        "6_Testing_Evaluation": [d / "testing_evaluation.docx", d / "pdf/testing_evaluation.pdf", ROOT / "artifacts/evaluation", ROOT / "artifacts/tests",
                                 ROOT / "data/evaluation/eval_set.json"],
    }
    for comp, items in comps.items():
        for it in items:
            if not it.exists():
                sys.exit(f"missing: {it}")
            dst = top / comp / it.name
            if it.is_dir():
                shutil.copytree(it, dst, ignore=lambda dirpath, names: [n for n in names if n.startswith("idx_") or n in EXCLUDE_DIRS])
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(it, dst)
    src = top / "7_Source_Code_and_README"
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and keep(p):
            dst = src / p.relative_to(ROOT)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
    (top / "README_SUBMISSION.txt").write_text(
        "Submission layout\n1_Project_Report  2_Dataset_Knowledge_Base  3_Document_Processing_Module  4_Embedding_Vector_Database\n"
        "5_LLM_Prompt_Engineering  6_Testing_Evaluation  7_Source_Code_and_README (start with README.md)\n"
        "Names / roll numbers are placeholders until docs/team_info.json is completed.\n", encoding="utf-8")
    shutil.copy2(ROOT / "FINAL_COMPLIANCE_CHECKLIST.md", top / "FINAL_COMPLIANCE_CHECKLIST.md")
    # secret scan on text files
    hits = []
    for f in top.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".py", ".md", ".txt", ".json", ".csv", ".example", ".sh", ".toml", ".yml", ".mmd", ".xml", ".cfg", "") :
            try:
                if SECRET.search(f.read_text(encoding="utf-8", errors="ignore")):
                    hits.append(str(f))
            except OSError:
                pass
    if hits:
        sys.exit(f"possible secrets found: {hits}")
    out = ROOT / f"{NAME}.zip"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(top.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(stage))
    shutil.rmtree(stage)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        names = z.namelist()
    print(f"created {out} ({out.stat().st_size/1024:.0f} KB, {len(names)} files)")
    for comp in list(comps) + ["7_Source_Code_and_README"]:
        print(f"  {comp}: {sum(1 for n in names if f'/{comp}/' in n)} files")


if __name__ == "__main__":
    main()
