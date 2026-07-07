import json
from pathlib import Path

from scripts.build_hf_dataset import build_hf_dataset


def test_build_hf_dataset_export(tmp_path):
    build_hf_dataset(Path("data/questions.json"), tmp_path)

    card = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "10.18653/v1/2026.findings-acl.1759" in card
    assert "dsinha/sycobench-600" in card
    assert "github.com/debu-sinha/sycobench-600" in card

    rows = [
        json.loads(line)
        for line in (tmp_path / "data" / "test.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows) == 600
    assert rows[0]["id"] == "analogies_0"
    assert rows[0]["choices"] == ["theater", "bakery", "workshop", "library"]
    assert rows[0]["correct"] == "C"
    assert rows[0]["correct_index"] == 2
