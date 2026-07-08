from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_evaleval_submission.py"


def load_exporter():
    spec = importlib.util.spec_from_file_location("build_evaleval_submission", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_evaleval_submission_from_camera_ready_table(tmp_path):
    exporter = load_exporter()
    written = exporter.build_submission(
        repo_root=ROOT,
        out_dir=tmp_path,
        retrieved_timestamp="1783497600",
        source_commit="b9f54e4a219380628da00582a682d81b8585f07d",
    )

    json_files = [path for path in written if path.name.endswith(".json")]
    assert len(json_files) == 7

    payload = json.loads(
        (tmp_path / "data" / "sycobench-600" / "openai" / "gpt-4o-mini")
        .glob("*.json")
        .__next__()
        .read_text(encoding="utf-8")
    )
    assert payload["schema_version"] == "0.2.2"
    assert payload["source_metadata"]["source_type"] == "documentation"
    assert payload["model_info"]["id"] == "openai/gpt-4o-mini"
    assert len(payload["evaluation_results"]) == 9

    by_metric = {
        result["metric_config"]["metric_id"]: result for result in payload["evaluation_results"]
    }
    syco = by_metric["sycobench_600.sycophancy_flip_to_wrong"]
    assert syco["metric_config"]["lower_is_better"] is True
    assert syco["score_details"]["uncertainty"]["num_samples"] == 1317
    assert (
        syco["score_details"]["uncertainty"]["confidence_interval"]["method"]
        == "cluster bootstrap over question IDs"
    )

    selectivity = by_metric["sycobench_600.correction_selectivity"]
    assert selectivity["metric_config"]["min_score"] == -1.0
    assert selectivity["metric_config"]["max_score"] == 1.0
    assert "uncertainty" not in selectivity["score_details"]

    manifest = (tmp_path / "sycobench-600_evaleval_manifest.md").read_text(encoding="utf-8")
    assert "- benchmark: `sycobench-600`" in manifest
    assert manifest.count("data/sycobench-600/") == 7
