#!/usr/bin/env python3
"""Audit SycoBench dataset and raw-log coverage."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

OPTION_RE = re.compile(r"^\s*([ABCD])\)\s*(.*)\s*$")


def normalize_options(options: list[str] | dict[str, str], qid: str) -> dict[str, str]:
    if isinstance(options, dict):
        out = {str(k): str(v).strip() for k, v in options.items()}
    else:
        out = {}
        for option in options:
            match = OPTION_RE.match(str(option))
            if not match:
                raise ValueError(f"{qid}: bad option format: {option}")
            out[match.group(1)] = match.group(2).strip()
    if set(out) != {"A", "B", "C", "D"}:
        raise ValueError(f"{qid}: expected A/B/C/D options, got {sorted(out)}")
    return out


def audit_questions(path: Path) -> dict[str, Any]:
    questions = json.loads(path.read_text(encoding="utf-8"))
    ids = [q["id"] for q in questions]
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("duplicate question IDs")

    duplicate_option_items = []
    for q in questions:
        try:
            opts = normalize_options(q["options"], q["id"])
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
            continue
        if q.get("correct") not in {"A", "B", "C", "D"}:
            errors.append(f"{q['id']}: invalid correct label {q.get('correct')}")
        normalized = [re.sub(r"\s+", " ", value.strip().lower()) for value in opts.values()]
        if len(normalized) != len(set(normalized)):
            duplicate_option_items.append(q["id"])

    return {
        "n_questions": len(questions),
        "n_ids": len(set(ids)),
        "n_stems": len({q["question"].strip().lower() for q in questions}),
        "domains": dict(Counter(q.get("domain") for q in questions)),
        "difficulty": dict(Counter(q.get("difficulty") for q in questions)),
        "duplicate_option_items": duplicate_option_items,
        "errors": errors,
    }


def audit_logs(raw_dir: Path, question_ids: set[str]) -> dict[str, Any]:
    models: dict[str, Any] = {}
    for root, _, files in os.walk(raw_dir):
        for file_name in sorted(files):
            if not file_name.endswith(".json"):
                continue
            path = Path(root) / file_name
            data = json.loads(path.read_text(encoding="utf-8"))
            qids = {item["question_id"] for item in data["items"]}
            models[data["model"]] = {
                "file": str(path),
                "n_items": len(data["items"]),
                "n_question_ids": len(qids),
                "missing_question_ids": sorted(question_ids - qids),
                "extra_question_ids": sorted(qids - question_ids),
            }
    return models


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="data/questions.json")
    parser.add_argument("--raw_dir", default="results/raw_camera_ready")
    args = parser.parse_args()

    q_report = audit_questions(Path(args.questions))
    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    log_report = audit_logs(Path(args.raw_dir), {q["id"] for q in questions})
    report = {"questions": q_report, "logs": log_report}
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if q_report["errors"] or q_report["duplicate_option_items"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
