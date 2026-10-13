"""
validate_submission.py
======================
Programmatic cross-check of the final package (writes results/validation_report.txt).
Exit code 0 only if every check passes.
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = lambda *a: os.path.join(ROOT, *a)
lines, fails = [], []


def check(name, ok, detail=""):
    lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        fails.append(name)


# ---- required files
req = ["README.md", "source_code/src/watermark_core.py", "source_code/original_backup/watermark_core.py", "source_code/requirements.txt",
       "source_code/config.json", "tests/test_watermark_core.py", "data/metadata.csv", "data/README.md",
       "results/results_attacks.csv", "results/results_images.csv", "results/results_alpha_sweep.csv", "results/results_controls.csv",
       "results/run_summary.json", "results/analysis_summary.json", "results/tech_benchmark_components.csv", "results/tech_benchmark_schemes.csv",
       "results/video_demo_results.csv", "research/LITERATURE_REVIEW.md", "research/REFERENCES.md", "research/TECHNOLOGY_COMPARISON.md",
       "documentation/PROJECT_AUDIT.md", "documentation/TRANSFORMATIONS_REFERENCE.md", "documentation/EXPERIMENT_METHODOLOGY.md",
       "documentation/CHANGELOG.md", "report/Final_Project_Report.docx", "report/Final_Project_Report.pdf",
       "presentation/Final_Presentation.pptx", "presentation/Final_Presentation.pdf", "presentation/SPEAKER_NOTES.md"]
missing = [f for f in req if not os.path.exists(P(f))]
check("all required deliverables present", not missing, f"missing: {missing}" if missing else f"{len(req)} files")

# ---- dataset
meta = pd.read_csv(P("data", "metadata.csv"))
check("metadata has 100 rows and unique IDs", len(meta) == 100 and meta.image_id.is_unique)
arrs = [np.asarray(Image.open(P("data", "original", i + ".png"))) for i in meta.image_id]
check("100 images are 512x512 uint8 and pixel-unique", all(a.shape == (512, 512) and a.dtype == np.uint8 for a in arrs) and len({a.tobytes() for a in arrs}) == 100)
check("synthetic images labelled", set(meta[meta.is_synthetic == 1].category) == {"synthetic_control"} and (meta.is_synthetic == 1).sum() == 6)
check("real images have source URL, licence, rights note, SHA-256", meta[meta.is_synthetic == 0][["source_url", "repository_license", "rights_note", "source_sha256"]].notna().all().all())
check("processing status recorded for every image", (meta.processing_status == "ok").all() and (meta.attack_trials_ok == 30).all())

# ---- results
att = pd.read_csv(P("results", "results_attacks.csv")); img = pd.read_csv(P("results", "results_images.csv"))
sw = pd.read_csv(P("results", "results_alpha_sweep.csv")); ctl = pd.read_csv(P("results", "results_controls.csv"))
check("3000 attack trials, all ok", len(att) == 3000 and (att.status == "ok").all())
check("every image x protocol has 15 conditions", att.groupby(["image_id", "protocol"]).size().eq(15).all())
check("4000 sweep rows ok, 1600 control rows", len(sw) == 4000 and (sw.status == "ok").all() and len(ctl) == 1600)
check("100 watermarked PNGs exist and were validated", img.output_valid.all() and all(os.path.exists(P("outputs", "watermarked", i + "_wm.png")) for i in meta.image_id))
check("metrics in valid ranges", att.nc.between(0, 1).all() and att.ber.between(0, 1).all() and att.zncc.between(-1, 1).all())

# ---- recompute headline numbers independently from raw CSV and compare with analysis summary / docs
AS = json.load(open(P("results", "analysis_summary.json")))
a = att[att.protocol == "uint8"]
pass_rate = float((a.nc >= 0.75).mean()); mean_nc = float(a.nc.mean())
check("headline pass rate recomputed from raw CSV matches summary", abs(pass_rate - AS["E2"]["pass_rate"]) < 1e-12, f"{pass_rate:.4f}")
check("mean PSNR recomputed matches summary", abs(img.psnr_db.mean() - AS["E1"]["psnr_all"]["mean"]) < 1e-9, f"{img.psnr_db.mean():.3f} dB")
fp = ctl[ctl.control.str.startswith("c: ")].nc.mean()
check("false-positive control mean NC recomputed", abs(fp - 0.975) < 0.0015, f"{fp:.4f}")

# ---- documents
from docx import Document
from pptx import Presentation
d = Document(P("report", "Final_Project_Report.docx"))
dtext = "\n".join(p.text for p in d.paragraphs) + "\n".join(c.text for t in d.tables for r in t.rows for c in r.cells)
pres = Presentation(P("presentation", "Final_Presentation.pptx"))
ptext = "\n".join(sh.text_frame.text for s in pres.slides for sh in s.shapes if sh.has_text_frame)
check("report opens (python-docx) with figures and tables", len(d.inline_shapes) >= 15 and len(d.tables) >= 15, f"{len(d.inline_shapes)} images, {len(d.tables)} tables")
check("deck opens (python-pptx) with 24 slides, all with notes", len(pres.slides) == 24 and all(s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip() for s in pres.slides))
bad = re.compile(r"\b(TODO|TBD|lorem ipsum|placeholder|XXX|FIXME)\b", re.I)
check("no placeholder text in report/deck", not bad.search(dtext) and not bad.search(ptext))
check("report and deck agree on headline numbers", all(x in dtext for x in ("85.1 %", "0.975")) and all(x in ptext for x in ("85.1 %", "0.98")), "85.1 % pass rate; wrong-logo NC 0.975")
check("report mentions Canva not edited / no template", "Canva" in dtext)
pdf_pages = int(re.search(r"Pages:\s+(\d+)", os.popen(f'pdfinfo "{P("report", "Final_Project_Report.pdf")}"').read()).group(1))
check("report PDF has pages and TOC page numbers resolved", pdf_pages >= 30, f"{pdf_pages} pages")
toc_zero = len(re.findall(r"\.{5,}0\s*$", os.popen(f'pdftotext -layout "{P("report", "Final_Project_Report.pdf")}" - 2>/dev/null').read(), re.M))
check("no unresolved (0) page numbers in contents/lists", toc_zero == 0)
refs = open(P("research", "REFERENCES.md"), encoding="utf-8").read()
cited = set(re.findall(r"\[(\d+)\]", dtext))
listed = set(re.findall(r"^\| \[(\d+)\] ", refs, re.M))
check("every citation number in the report exists in the reference list", cited <= listed, f"unlisted: {sorted(cited - listed, key=int)}" if not cited <= listed else f"{len(cited)} cited / {len(listed)} listed")
orig_same = all(open(P("source_code/original_backup", f), "rb").read() != open(P("source_code/src", f), "rb").read() for f in ["watermark_core.py", "metrics.py", "attacks.py"])
check("original source files preserved separately (and modified versions differ)", orig_same)

out = "\n".join(lines) + f"\n\n{len(lines) - len(fails)}/{len(lines)} checks passed\n"
open(P("results", "validation_report.txt"), "w", encoding="utf-8").write(out)
print(out)
sys.exit(1 if fails else 0)
