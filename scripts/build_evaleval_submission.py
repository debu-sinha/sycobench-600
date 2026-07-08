"""Build Every Eval Ever aggregate records for SycoBench-600 paper results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.2.2"
BENCHMARK_ID = "sycobench-600"
ACL_URL = "https://aclanthology.org/2026.findings-acl.1759/"
DOI_URL = "https://doi.org/10.18653/v1/2026.findings-acl.1759"
HF_DATASET = "dsinha/sycobench-600"
SOURCE_REPO = "https://github.com/debu-sinha/sycobench-600"
INSPECT_REGISTER = (
    "https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/register/sycobench-600"
)
LM_EVAL_PR = "https://github.com/EleutherAI/lm-evaluation-harness/pull/3919"
DEFAULT_SOURCE_COMMIT = "b9f54e4a219380628da00582a682d81b8585f07d"


MODEL_METADATA: dict[str, dict[str, str]] = {
    "gpt-4o": {
        "name": "gpt-4o",
        "id": "openai/gpt-4o",
        "developer": "OpenAI",
        "developer_slug": "openai",
        "inference_platform": "OpenAI API",
        "base_url": "https://api.openai.com/v1",
        "raw_log": "results/raw_camera_ready/gpt-4o.json",
    },
    "gpt-4o-mini": {
        "name": "gpt-4o-mini",
        "id": "openai/gpt-4o-mini",
        "developer": "OpenAI",
        "developer_slug": "openai",
        "inference_platform": "OpenAI API",
        "base_url": "https://api.openai.com/v1",
        "raw_log": "results/raw_camera_ready/gpt-4o-mini.json",
    },
    "anthropic/claude-sonnet-4": {
        "name": "anthropic/claude-sonnet-4",
        "id": "anthropic/claude-sonnet-4",
        "developer": "Anthropic",
        "developer_slug": "anthropic",
        "inference_platform": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "raw_log": "results/raw_camera_ready/anthropic/claude-sonnet-4.json",
    },
    "anthropic/claude-3.5-haiku": {
        "name": "anthropic/claude-3.5-haiku",
        "id": "anthropic/claude-3.5-haiku",
        "developer": "Anthropic",
        "developer_slug": "anthropic",
        "inference_platform": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "raw_log": "results/raw_camera_ready/anthropic/claude-3.5-haiku.json",
    },
    "google/gemini-2.5-flash": {
        "name": "google/gemini-2.5-flash",
        "id": "google/gemini-2.5-flash",
        "developer": "Google",
        "developer_slug": "google",
        "inference_platform": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "raw_log": "results/raw_camera_ready/google/gemini-2.5-flash.json",
    },
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": {
        "name": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "developer": "Meta",
        "developer_slug": "meta-llama",
        "inference_platform": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "raw_log": (
            "results/raw_camera_ready/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8.json"
        ),
    },
    "mistralai/Mistral-7B-Instruct-v0.3": {
        "name": "mistralai/Mistral-7B-Instruct-v0.3",
        "id": "mistralai/Mistral-7B-Instruct-v0.3",
        "developer": "Mistral AI",
        "developer_slug": "mistralai",
        "inference_platform": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "raw_log": "results/raw_camera_ready/mistralai/Mistral-7B-Instruct-v0.3.json",
    },
}


METRICS: tuple[dict[str, Any], ...] = (
    {
        "column": "acc",
        "metric_id": "sycobench_600.baseline_accuracy",
        "metric_name": "Baseline accuracy",
        "metric_kind": "accuracy",
        "description": "Baseline multiple-choice accuracy before follow-up pressure.",
        "lower_is_better": False,
        "num_samples_column": "n_runs",
    },
    {
        "column": "pra_all",
        "metric_id": "sycobench_600.pressure_robust_accuracy_all",
        "metric_name": "Pressure-robust accuracy",
        "metric_kind": "accuracy",
        "description": (
            "Unconditional rate where baseline, doubt, authority, and wrong-suggestion "
            "answers are all correct."
        ),
        "lower_is_better": False,
        "num_samples_column": "n_runs",
        "ci": ("pra_ci_lo", "pra_ci_hi"),
    },
    {
        "column": "pra_mean",
        "metric_id": "sycobench_600.pressure_robust_accuracy_mean",
        "metric_name": "Mean post-pressure accuracy",
        "metric_kind": "accuracy",
        "description": "Mean post-perturbation accuracy across misleading pressure types.",
        "lower_is_better": False,
        "num_samples_column": "n_runs",
    },
    {
        "column": "syco",
        "metric_id": "sycobench_600.sycophancy_flip_to_wrong",
        "metric_name": "Sycophancy flip-to-wrong rate",
        "metric_kind": "error_rate",
        "description": (
            "Macro-average rate of flipping away from the correct answer under misleading "
            "pressure, conditioned on baseline correctness."
        ),
        "lower_is_better": True,
        "num_samples_column": "nC",
        "ci": ("syco_ci_lo", "syco_ci_hi"),
    },
    {
        "column": "stub_no_change",
        "metric_id": "sycobench_600.stubbornness_no_change",
        "metric_name": "Stubbornness no-change rate",
        "metric_kind": "error_rate",
        "description": (
            "Rate of keeping the original wrong baseline answer under a correct user "
            "suggestion, conditioned on baseline-wrong runs with correction data."
        ),
        "lower_is_better": True,
        "num_samples_column": "nW_eff",
        "ci": ("stub_ci_lo", "stub_ci_hi"),
    },
    {
        "column": "update",
        "metric_id": "sycobench_600.correct_suggestion_update_rate",
        "metric_name": "Correct-suggestion update rate",
        "metric_kind": "accuracy",
        "description": (
            "Rate of updating to the correct answer after a correct user suggestion, "
            "conditioned on baseline-wrong runs with correction data."
        ),
        "lower_is_better": False,
        "num_samples_column": "nW_eff",
    },
    {
        "column": "wrong_flip",
        "metric_id": "sycobench_600.wrong_suggestion_flip_rate",
        "metric_name": "Wrong-suggestion flip rate",
        "metric_kind": "error_rate",
        "description": (
            "Flip-to-wrong rate under the explicit wrong-suggestion condition, "
            "conditioned on baseline correctness."
        ),
        "lower_is_better": True,
        "num_samples_column": "nC",
    },
    {
        "column": "selectivity",
        "metric_id": "sycobench_600.correction_selectivity",
        "metric_name": "Correction selectivity",
        "metric_kind": "score",
        "description": "Aggregate trade-off Update - WrongFlip.",
        "lower_is_better": False,
        "min_score": -1.0,
        "max_score": 1.0,
    },
    {
        "column": "exact_one_letter",
        "metric_id": "sycobench_600.exact_one_letter_rate",
        "metric_name": "Exact one-letter response rate",
        "metric_kind": "format_compliance",
        "description": "Rate at which the model response parsed as exactly one answer letter.",
        "lower_is_better": False,
        "num_samples_column": "n_runs",
    },
)


def slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-").lower()


def stable_uuid(value: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, value))


def unix_from_run_id(run_id: str | None) -> str | None:
    if not run_id:
        return None
    match = re.search(r"_(\d{8})_(\d{6})_", run_id)
    if not match:
        return None
    dt = datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    return str(int(dt.timestamp()))


def read_raw_metadata(repo_root: Path, raw_log: str) -> dict[str, str]:
    path = repo_root / raw_log
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "run_id": str(data.get("run_id", "")),
        "schema_version": str(data.get("schema_version", "")),
        "questions_sha256": str(data.get("questions_sha256", "")),
        "n_questions": str(data.get("n_questions", "")),
        "variants": str(data.get("variants", "")),
        "seed": str(data.get("seed", "")),
        "temperature": str(data.get("temperature", "")),
        "workers": str(data.get("workers", "")),
        "evaluation_timestamp": unix_from_run_id(data.get("run_id")),
    }


def source_data(source_commit: str) -> dict[str, Any]:
    return {
        "dataset_name": "SycoBench-600",
        "source_type": "hf_dataset",
        "hf_repo": HF_DATASET,
        "hf_split": "test",
        "samples_number": 600,
        "additional_details": {
            "acl_anthology": ACL_URL,
            "doi": DOI_URL,
            "source_repository": SOURCE_REPO,
            "source_commit": source_commit,
            "raw_logs": f"{SOURCE_REPO}/tree/{source_commit}/results/raw_camera_ready",
            "camera_ready_table": (
                f"{SOURCE_REPO}/blob/{source_commit}/build/camera_ready/tables/main_results.csv"
            ),
            "paper_setting": "555-question intersection across all seven evaluated models",
            "n_bootstrap_samples": "2000",
        },
    }


def uncertainty(metric: dict[str, Any], row: dict[str, str]) -> dict[str, Any] | None:
    values: dict[str, Any] = {}
    if num_col := metric.get("num_samples_column"):
        values["num_samples"] = int(float(row[num_col]))
    if ci_cols := metric.get("ci"):
        values["confidence_interval"] = {
            "lower": float(row[ci_cols[0]]),
            "upper": float(row[ci_cols[1]]),
            "confidence_level": 0.95,
            "method": "cluster bootstrap over question IDs",
        }
        values["num_bootstrap_samples"] = 2000
    return values or None


def metric_record(
    row: dict[str, str],
    metric: dict[str, Any],
    model_id: str,
    eval_timestamp: str | None,
    generation_config: dict[str, Any],
    source_commit: str,
) -> dict[str, Any]:
    score_details: dict[str, Any] = {
        "score": float(row[metric["column"]]),
        "details": {
            "source_column": metric["column"],
            "n_runs": str(row["n_runs"]),
            "n_baseline_correct": str(row["nC"]),
            "n_baseline_wrong": str(row["nW"]),
            "n_baseline_wrong_effective": str(row["nW_eff"]),
            "reported_setting": "555-question intersection, 3 variants per question",
        },
    }
    if maybe_uncertainty := uncertainty(metric, row):
        score_details["uncertainty"] = maybe_uncertainty

    result_id = f"{BENCHMARK_ID}:{model_id}:{metric['metric_id']}"
    return {
        "evaluation_result_id": result_id,
        "evaluation_name": f"SycoBench-600 {metric['metric_name']}",
        "source_data": source_data(source_commit),
        "evaluation_timestamp": eval_timestamp,
        "metric_config": {
            "evaluation_description": metric["description"],
            "metric_id": metric["metric_id"],
            "metric_name": metric["metric_name"],
            "metric_kind": metric["metric_kind"],
            "metric_unit": "proportion",
            "metric_parameters": {
                "variants": 3.0,
                "intersection_question_ids": 555.0,
            },
            "lower_is_better": metric["lower_is_better"],
            "score_type": "continuous",
            "min_score": metric.get("min_score", 0.0),
            "max_score": metric.get("max_score", 1.0),
        },
        "score_details": score_details,
        "generation_config": generation_config,
    }


def record_for_model(
    row: dict[str, str],
    repo_root: Path,
    retrieved_timestamp: str,
    source_commit: str,
) -> tuple[dict[str, Any], Path]:
    model = row["model"]
    metadata = MODEL_METADATA[model]
    raw_metadata = read_raw_metadata(repo_root, metadata["raw_log"])
    eval_timestamp = raw_metadata.get("evaluation_timestamp")

    generation_config = {
        "generation_args": {
            "temperature": float(raw_metadata["temperature"]),
            "max_tokens": 128,
            "reasoning": False,
        },
        "additional_details": {
            "seed": raw_metadata["seed"],
            "variants": raw_metadata["variants"],
            "workers": raw_metadata["workers"],
            "prompting": "single-letter MCQ baseline plus fixed follow-up perturbations",
        },
    }
    evaluation_id = f"{BENCHMARK_ID}/{metadata['id']}/{retrieved_timestamp}"
    record = {
        "schema_version": SCHEMA_VERSION,
        "evaluation_id": evaluation_id,
        "evaluation_timestamp": eval_timestamp,
        "retrieved_timestamp": retrieved_timestamp,
        "source_metadata": {
            "source_name": "SycoBench-600 ACL Findings 2026 camera-ready artifact",
            "source_type": "documentation",
            "source_organization_name": "SycoBench-600",
            "source_organization_url": SOURCE_REPO,
            "evaluator_relationship": "third_party",
            "additional_details": {
                "acl_anthology": ACL_URL,
                "doi": DOI_URL,
                "huggingface_dataset": f"https://huggingface.co/datasets/{HF_DATASET}",
                "inspect_evals_register": INSPECT_REGISTER,
                "lm_evaluation_harness_pr": LM_EVAL_PR,
                "source_commit": source_commit,
            },
        },
        "eval_library": {
            "name": "sycobench",
            "version": "0.1.0",
            "additional_details": {
                "protocol": "SycoBench-600 full paper protocol",
                "inspect_task": "sycobench/inspect_task.py@sycobench_600",
                "schema_version": raw_metadata["schema_version"],
                "questions_sha256": raw_metadata["questions_sha256"],
            },
        },
        "model_info": {
            "name": metadata["name"],
            "id": metadata["id"],
            "developer": metadata["developer"],
            "inference_platform": metadata["inference_platform"],
            "additional_details": {
                "provider": "openai_compatible",
                "base_url": metadata["base_url"],
                "run_id": raw_metadata["run_id"],
                "raw_log_path": metadata["raw_log"],
                "raw_log_url": f"{SOURCE_REPO}/blob/{source_commit}/{metadata['raw_log']}",
            },
        },
        "evaluation_results": [
            metric_record(
                row,
                metric,
                metadata["id"],
                eval_timestamp,
                generation_config,
                source_commit,
            )
            for metric in METRICS
        ],
    }
    rel_path = (
        Path("data")
        / BENCHMARK_ID
        / metadata["developer_slug"]
        / slugify(metadata["id"].split("/", 1)[-1])
        / f"{stable_uuid(evaluation_id)}.json"
    )
    return record, rel_path


def build_submission(
    repo_root: Path,
    out_dir: Path,
    retrieved_timestamp: str,
    source_commit: str,
) -> list[Path]:
    csv_path = repo_root / "build" / "camera_ready" / "tables" / "main_results.csv"
    written: list[Path] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            record, rel_path = record_for_model(
                row,
                repo_root=repo_root,
                retrieved_timestamp=retrieved_timestamp,
                source_commit=source_commit,
            )
            out_path = out_dir / rel_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            written.append(out_path)
    manifest_path = out_dir / "sycobench-600_evaleval_manifest.md"
    manifest_lines = [
        "# SycoBench-600 EvalEval Submission",
        "",
        f"- benchmark: `{BENCHMARK_ID}`",
        f"- schema_version: `{SCHEMA_VERSION}`",
        f"- retrieved_timestamp: `{retrieved_timestamp}`",
        f"- source_commit: `{source_commit}`",
        "",
        "| File | SHA-256 |",
        "| --- | --- |",
    ]
    for path in written:
        rel = str(path.relative_to(out_dir)).replace("\\", "/")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_lines.append(f"| `{rel}` | `{digest}` |")
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    written.append(manifest_path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--out-dir", type=Path, default=Path("build/evaleval_submission"))
    parser.add_argument("--retrieved-timestamp", default=str(int(time.time())))
    parser.add_argument("--source-commit", default=DEFAULT_SOURCE_COMMIT)
    args = parser.parse_args()

    written = build_submission(
        repo_root=args.repo_root.resolve(),
        out_dir=args.out_dir.resolve(),
        retrieved_timestamp=str(args.retrieved_timestamp),
        source_commit=args.source_commit,
    )
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
