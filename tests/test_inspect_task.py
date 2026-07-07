import pytest

pytest.importorskip("inspect_ai")

from inspect_ai import eval as inspect_eval
from inspect_ai.model import ModelOutput

from sycobench.inspect_task import sycobench_600


def _scripted_sycobench_output(messages, tools, tool_choice, config):
    del tools, tool_choice, config
    last_user = next(message.content for message in reversed(messages) if message.role == "user")
    if (
        "correct answer is A" in last_user
        or "answer should be A" in last_user
        or "right choice is A" in last_user
    ):
        return ModelOutput.from_content(model="mockllm/model", content="A")
    return ModelOutput.from_content(model="mockllm/model", content="C")


def test_sycobench_task_builds_full_default_dataset():
    task = sycobench_600()
    assert task.name == "sycobench_600"
    assert len(task.dataset) == 1800


def test_inspect_eval_runs_sycobench_protocol_with_mock_model(tmp_path):
    logs = inspect_eval(
        sycobench_600,
        model="mockllm/model",
        model_args={"custom_outputs": _scripted_sycobench_output},
        task_args={"limit": 1, "variants": 1},
        log_dir=str(tmp_path),
        display="none",
        log_samples=True,
    )

    assert len(logs) == 1
    sample = logs[0].samples[0]
    score = sample.scores["sycobench_protocol_scorer"]
    assert score.value == "C"
    assert score.answer == "C"
    assert score.metadata["baseline_correct"] is True
    assert score.metadata["pressure_robust"] is False
    assert score.metadata["wrong_suggest_flip"] is True
    assert score.metadata["protocol"]["perturbations"]["correct_suggest"]["skipped"] is True
