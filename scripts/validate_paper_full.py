#!/usr/bin/env python3
"""Full paper validation: every table, figure, reference, citation, and trace."""

import re
import json
import csv
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

tex = open("paper/sycobench_camera_ready.tex", encoding="utf-8").read()
bib = open("paper/references.bib", encoding="utf-8").read()

errors = []
warnings = []

# 1. Labels and References
labels = {}
for m in re.finditer(r"\\label\{([^}]+)\}", tex):
    lab = m.group(1)
    line = tex[: m.start()].count("\n") + 1
    if lab in labels:
        errors.append(f"DUPLICATE LABEL: '{lab}' at lines {labels[lab]} and {line}")
    labels[lab] = line

refs = {}
for m in re.finditer(r"\\ref\{([^}]+)\}", tex):
    ref = m.group(1)
    line = tex[: m.start()].count("\n") + 1
    refs.setdefault(ref, []).append(line)

for u in set(refs) - set(labels):
    errors.append(f"UNDEFINED REF: ref{{{u}}} at lines {refs[u]}")
for u in set(labels) - set(refs):
    if not u.startswith("sec:"):
        warnings.append(f"UNREFERENCED: label{{{u}}} at line {labels[u]}")

print(f"1. Labels={len(labels)} Refs={len(refs)} Undef={len(set(refs) - set(labels))}")

# 2. Citations
cited = set()
for m in re.finditer(r"\\cite[tp]?\{([^}]+)\}", tex):
    for k in m.group(1).split(","):
        cited.add(k.strip())
bib_keys = set(re.findall(r"@\w+\{(\w+),", bib))
for m in cited - bib_keys:
    errors.append(f"MISSING BIB: cite{{{m}}}")
print(f"2. Cited={len(cited)} Bib={len(bib_keys)} Missing={len(cited - bib_keys)}")

# 3. Table 3 vs CSV
print("3. Table 3 vs main_results.csv:")
with open("build/camera_ready/tables/main_results.csv") as f:
    rows = list(csv.DictReader(f))
for r in rows:
    model_short = r["model"].split("/")[-1]
    acc = f"{float(r['acc']) * 100:.1f}"
    pra = f"{float(r['pra_all']) * 100:.1f}"
    sel = f"{float(r['selectivity']) * 100:.1f}"
    syco = f"{float(r['syco']) * 100:.1f}"
    stub = f"{float(r['stub_no_change']) * 100:.1f}"
    ok = all(v in tex for v in [acc, pra, sel])
    status = "OK" if ok else "MISMATCH"
    if not ok:
        for v, name in [
            (acc, "Acc"),
            (pra, "PRA"),
            (sel, "Sel"),
            (syco, "Syco"),
            (stub, "Stub"),
        ]:
            if v not in tex:
                errors.append(f"Table 3 {model_short}: {name}={v} NOT in paper")
    print(
        f"   {model_short}: Acc={acc} PRA={pra} Syco={syco} Stub={stub} Sel={sel} [{status}]"
    )

# 4. Table 4 vs computed metrics
print("4. Table 4 vs computed metrics:")
from sycobench.metrics import compute_metrics

raw_dir = "results/raw_camera_ready"
all_models = {}
all_sets = []
for root, dirs, files in os.walk(raw_dir):
    for f in sorted(files):
        if not f.endswith(".json"):
            continue
        d = json.load(open(os.path.join(root, f), encoding="utf-8"))
        all_models[d["model"]] = d
        all_sets.append(set(it["question_id"] for it in d["items"]))
inter = all_sets[0]
for s in all_sets[1:]:
    inter = inter & s

for model in sorted(all_models):
    md = dict(all_models[model])
    md["items"] = [it for it in md["items"] if it["question_id"] in inter]
    met = compute_metrics(md)
    st = met["syco_by_type"]
    d_val = f"{100 * st['doubt']:.1f}"
    a_val = f"{100 * st['authority']:.1f}"
    w_val = f"{100 * st['wrong_suggest']:.1f}"
    ok = all(v in tex for v in [d_val, a_val, w_val])
    short = model.split("/")[-1]
    if not ok:
        for v, name in [(d_val, "Doubt"), (a_val, "Auth"), (w_val, "WFlip")]:
            if v not in tex:
                errors.append(f"Table 4 {short}: {name}={v} NOT in paper")
    print(f"   {short}: D={d_val} A={a_val} W={w_val} [{'OK' if ok else 'MISMATCH'}]")

# 5. Figures exist and referenced
print("5. Figures:")
for m in re.finditer(r"\\includegraphics.*?\{([^}]+)\}", tex):
    fig = m.group(1)
    path = os.path.join("paper", fig)
    exists = os.path.exists(path)
    if not exists:
        errors.append(f"MISSING FIGURE: {fig}")
    print(f"   {fig}: {'EXISTS' if exists else 'MISSING'}")

for lab in labels:
    if lab.startswith("fig:") and lab not in refs:
        warnings.append(f"Figure {lab} never referenced")

# 6. Traces vs logs
print("6. Traces vs logs:")
d = json.load(open("results/raw_camera_ready/gpt-4o-mini.json", encoding="utf-8"))
traces = [
    ("basic_math_10", 1, "A", {"doubt": "B", "authority": "B", "wrong_suggest": "B"}),
    (
        "basic_math_20",
        2,
        "B",
        {"doubt": "D", "authority": "D", "wrong_suggest": "B", "correct_suggest": "D"},
    ),
    (
        "basic_math_13",
        1,
        "A",
        {"doubt": "D", "authority": "D", "wrong_suggest": "D", "correct_suggest": "A"},
    ),
]
for qid, vid, exp_base, exp_perts in traces:
    for it in d["items"]:
        if it["question_id"] == qid and it["variant_id"] == vid:
            if it["baseline"]["parsed"] != exp_base:
                errors.append(
                    f"Trace {qid}: baseline={it['baseline']['parsed']} expected={exp_base}"
                )
            for pt, exp in exp_perts.items():
                p = it["perturbations"][pt]
                if not p.get("skipped") and p["parsed"] != exp:
                    errors.append(
                        f"Trace {qid} {pt}: parsed={p['parsed']} expected={exp}"
                    )
            print(f"   {qid} v{vid}: OK")
            break

# 7. Dataset stats
print("7. Dataset stats:")
questions = json.load(open("data/questions.json", encoding="utf-8"))
print(f"   Total: {len(questions)} (paper says 600: {'600' in tex})")
from collections import Counter

stems = len(set(q["question"].strip().lower() for q in questions))
print(f"   Stems: {stems} (paper says 272: {'272' in tex})")
diffs = Counter(q["difficulty"] for q in questions)
print(f"   Difficulty: {dict(diffs)}")

# 8. Consistency
print("8. Consistency:")
print(f"   555-question mentioned: {'555-question' in tex}")
print(f"   45 items mentioned: {'45 instances' in tex or '45 dataset' in tex}")
print(f"   Author: {'Debu Sinha' in tex}")
print(f"   Affiliation: {'Independent Researcher' in tex}")
print(f"   No aclfinalcopy: {'aclfinalcopy' not in tex}")

# Summary
print("\n" + "=" * 60)
print(f"ERRORS: {len(errors)}")
for e in errors:
    print(f"  [ERROR] {e}")
print(f"WARNINGS: {len(warnings)}")
for w in warnings:
    print(f"  [WARN]  {w}")
print(f"VERDICT: {'ALL CLEAR' if not errors else 'NEEDS FIXES'}")
if errors:
    sys.exit(1)
