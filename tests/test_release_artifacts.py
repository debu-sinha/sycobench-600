import csv
import json
from pathlib import Path

from sycobench.validate import validate_model_log, validate_prompt_identity


def test_main_results_snapshot():
    rows = list(csv.DictReader(Path("build/camera_ready/tables/main_results.csv").open()))
    assert len(rows) == 7
    by_model = {row["model"]: row for row in rows}
    assert round(float(by_model["gpt-4o"]["acc"]) * 100, 1) == 83.3
    assert round(float(by_model["google/gemini-2.5-flash"]["syco"]) * 100, 1) == 7.1
    assert round(float(by_model["mistralai/Mistral-7B-Instruct-v0.3"]["selectivity"]) * 100, 1) == 13.4


def test_raw_logs_validate_with_expected_mistral_gap():
    questions = json.loads(Path("data/questions.json").read_text(encoding="utf-8"))
    qids = [q["id"] for q in questions]
    all_models = {}
    for path in Path("results/raw_camera_ready").rglob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        all_models[data["model"]] = data

    assert len(all_models) == 7
    prompt_errors = validate_prompt_identity(all_models)
    assert prompt_errors == []

    for model, data in all_models.items():
        errors = validate_model_log(data, qids)
        if model == "mistralai/Mistral-7B-Instruct-v0.3":
            assert len(errors) == 1
            assert errors[0].startswith("Missing 45 question_ids")
        else:
            assert errors == []


def test_paper_pdf_included_without_private_copyright_form():
    assert Path("paper/sycobench_camera_ready.pdf").exists()
    assert not any("copyright_signed" in path.name.lower() for path in Path(".").rglob("*"))
    assert not any("acl_copyright" in path.name.lower() for path in Path(".").rglob("*"))
