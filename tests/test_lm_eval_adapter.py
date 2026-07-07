from pathlib import Path

import yaml
from jinja2 import Template

from sycobench.io import load_json


def _adapter_config() -> dict:
    return yaml.safe_load(Path("integrations/lm_eval/sycobench_600.yaml").read_text())


def test_lm_eval_adapter_targets_published_hf_dataset():
    config = _adapter_config()

    assert config["task"] == "sycobench_600_baseline"
    assert config["tag"] == ["sycobench"]
    assert config["dataset_path"] == "dsinha/sycobench-600"
    assert config["test_split"] == "test"
    assert config["output_type"] == "multiple_choice"
    assert config["doc_to_choice"] == ["A", "B", "C", "D"]
    assert config["doc_to_target"] == "correct_index"


def test_lm_eval_adapter_prompt_matches_released_question_shape():
    config = _adapter_config()
    question = load_json("data/questions.json")[0]
    correct_index = ord(question["correct"]) - ord("A")

    rendered = Template(config["doc_to_text"]).render(**question)

    assert question["question"] in rendered
    assert "A) theater" in rendered
    assert "D) library" in rendered
    assert rendered.endswith("Answer:")
    assert correct_index == 2
    assert question["options"][correct_index] == "C) workshop"
