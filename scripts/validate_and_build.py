#!/usr/bin/env python3
"""Validate raw logs and build paper assets.

Run from repo root:
  python scripts/validate_and_build.py ...
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure `import sycobench` works when running as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
import argparse
import os
import json
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sycobench.io import load_json, save_json
from sycobench.validate import validate_model_log, validate_prompt_identity
from sycobench.metrics import compute_metrics, bootstrap_paper_ci_question_cluster

PRESSURE_TYPES = ["doubt", "authority", "wrong_suggest"]


def load_questions(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_dir", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--n_boot", type=int, default=2000, help="bootstrap replicates for confidence intervals")
    ap.add_argument(
        "--use_intersection",
        action="store_true",
        help="build metrics on intersection of question_ids across models",
    )
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    questions = load_questions(args.questions)
    qids = [q["id"] for q in questions]

    # Load model logs (supports nested subdirectories)
    all_models: Dict[str, Dict[str, Any]] = {}
    for root, dirs, files in os.walk(args.raw_dir):
        for f in files:
            if not f.endswith(".json"):
                continue
            md = load_json(os.path.join(root, f))
            all_models[md["model"]] = md

    if not all_models:
        raise SystemExit(f"No JSON model logs found under {args.raw_dir}")

    report = {"strict": args.strict, "n_boot": args.n_boot, "errors": {}, "global_errors": []}

    # Per-model checks
    for m, md in all_models.items():
        errs = validate_model_log(md, qids)
        if errs:
            report["errors"][m] = errs

    # Global prompt identity check (user prompts should match)
    prompt_errs = validate_prompt_identity(all_models)
    if prompt_errs:
        report["global_errors"].extend(prompt_errs)

    # Strict mode: fail if any errors
    if args.strict and (report["errors"] or report["global_errors"]):
        save_json(os.path.join(args.out_dir, "validation_report.json"), report)
        raise SystemExit(
            f"STRICT VALIDATION FAILED. See {os.path.join(args.out_dir, 'validation_report.json')}"
        )

    # Determine question intersection if requested
    if args.use_intersection:
        sets = []
        for m, md in all_models.items():
            sets.append(set(it["question_id"] for it in md["items"]))
        inter = set.intersection(*sets) if sets else set()
    else:
        inter = None

    # Compute metrics + CIs
    rows = []
    for m, md in all_models.items():
        md2 = md
        if inter is not None:
            md2 = dict(md)
            md2["items"] = [it for it in md["items"] if it["question_id"] in inter]
        met = compute_metrics(md2)

        # Bootstrap CIs for key metrics. Seeds match the camera-ready artifact.
        ci_syco = bootstrap_paper_ci_question_cluster(md2, n_boot=args.n_boot, seed=0)["syco"]
        ci_stub = bootstrap_paper_ci_question_cluster(md2, n_boot=args.n_boot, seed=1)["stub_no_change"]
        ci_pra = bootstrap_paper_ci_question_cluster(md2, n_boot=args.n_boot, seed=2)["pra_all"]

        # Exact-one-letter compliance rate (formatting metric)
        exact_count = sum(
            1 for it in md2["items"] if it["baseline"].get("exact_one_letter", False)
        )
        exact_rate = exact_count / len(md2["items"]) if md2["items"] else float("nan")

        # Effective correction denominator (nW minus _missing_data)
        nW_missing = sum(
            1
            for it in md2["items"]
            if not it["baseline"]["correct"]
            and it["perturbations"]
            .get("correct_suggest", {})
            .get("_missing_data", False)
        )
        nW_eff = met["nW"] - nW_missing

        rows.append(
            {
                "model": m,
                "n_runs": met["n_runs"],
                "nC": met["nC"],
                "nW": met["nW"],
                "nW_eff": nW_eff,
                "acc": met["acc"],
                "pra_all": met["pra_all"],
                "pra_mean": met["pra_mean"],
                "syco": met["syco"],
                "syco_ci_lo": ci_syco[0],
                "syco_ci_hi": ci_syco[1],
                "stub_no_change": met["stub_no_change"],
                "stub_ci_lo": ci_stub[0],
                "stub_ci_hi": ci_stub[1],
                "update": met["update"],
                "wrong_flip": met["wrong_flip"],
                "selectivity": met["selectivity"],
                "pra_ci_lo": ci_pra[0],
                "pra_ci_hi": ci_pra[1],
                "exact_one_letter": exact_rate,
            }
        )

    df = pd.DataFrame(rows).sort_values("model")
    tables_dir = os.path.join(args.out_dir, "tables")
    figs_dir = os.path.join(args.out_dir, "figures")
    os.makedirs(tables_dir, exist_ok=True)
    os.makedirs(figs_dir, exist_ok=True)

    df.to_csv(os.path.join(tables_dir, "main_results.csv"), index=False)

    # LaTeX table
    def pct(x):
        return f"{100 * x:.1f}"

    lines = []
    lines.append(r"\begin{tabular}{lrrrrr}")
    lines.append(r"\toprule")
    lines.append(r"Model & Acc & PRA$_{all}$ & Syco & Stub$_{nochange}$ & Sel \\")
    lines.append(r"\midrule")
    for _, r in df.iterrows():
        syco = f"{pct(r.syco)} [{pct(r.syco_ci_lo)}--{pct(r.syco_ci_hi)}]"
        stub = f"{pct(r.stub_no_change)} [{pct(r.stub_ci_lo)}--{pct(r.stub_ci_hi)}]"
        sel = f"{100 * r.selectivity:.1f}" if pd.notnull(r.selectivity) else "NA"
        lines.append(
            f"{r.model} & {pct(r.acc)} & {pct(r.pra_all)} & {syco} & {stub} & {sel} \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    open(os.path.join(tables_dir, "main_results.tex"), "w", encoding="utf-8").write(
        "\n".join(lines)
    )

    # Figures
    # Tradeoff: Syco vs Stub_no_change
    plt.figure()
    plt.scatter(df["syco"] * 100, df["stub_no_change"] * 100)
    for _, r in df.iterrows():
        plt.annotate(r["model"], (r["syco"] * 100, r["stub_no_change"] * 100))
    plt.xlabel("Sycophancy (%)")
    plt.ylabel("Assertion Correction Resistance (no-change) (%)")
    plt.title("SycoBench trade-off")
    plt.savefig(os.path.join(figs_dir, "tradeoff_syco_stub.pdf"), bbox_inches="tight")
    plt.close()

    # Sycophancy by type (bar chart)
    # Build per-type from compute_metrics syco_by_type
    types = ["doubt", "authority", "wrong_suggest"]
    mat = []
    labels = []
    for m, md in all_models.items():
        md2 = md
        if inter is not None:
            md2 = dict(md)
            md2["items"] = [it for it in md["items"] if it["question_id"] in inter]
        met = compute_metrics(md2)
        mat.append([met["syco_by_type"][t] * 100 for t in types])
        labels.append(m)
    mat = np.array(mat)
    x = np.arange(len(labels))
    width = 0.25
    plt.figure(figsize=(10, 4))
    for i, t in enumerate(types):
        plt.bar(x + (i - 1) * width, mat[:, i], width, label=t)
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.ylabel("Flip rate (%) | baseline correct")
    plt.title("Sycophancy by pressure type")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figs_dir, "sycophancy_by_type.pdf"), bbox_inches="tight")
    plt.close()

    save_json(os.path.join(args.out_dir, "validation_report.json"), report)
    print("Wrote:", os.path.join(args.out_dir, "validation_report.json"))
    print("Wrote tables to:", tables_dir)
    print("Wrote figures to:", figs_dir)


if __name__ == "__main__":
    main()
