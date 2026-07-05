import json
from collections import Counter
from pathlib import Path

DATA_PATH = Path("data/questions.json")


def test_dataset_counts_and_schema():
    questions = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert len(questions) == 600
    assert len({q["id"] for q in questions}) == 600
    assert len({q["question"].strip().lower() for q in questions}) == 272
    assert Counter(q["domain"] for q in questions) == {
        "analogies": 75,
        "basic_math": 75,
        "causal_reasoning": 75,
        "common_sense": 75,
        "logical_reasoning": 75,
        "reading_comprehension": 75,
        "scientific_facts": 75,
        "word_problems": 75,
    }
    assert Counter(q["difficulty"] for q in questions) == {
        "easy": 120,
        "medium": 240,
        "hard": 240,
    }


def test_options_are_unique_and_labeled():
    questions = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for q in questions:
        assert q["correct"] in {"A", "B", "C", "D"}
        assert isinstance(q["options"], list)
        labels = []
        values = []
        for option in q["options"]:
            label, value = option.split(")", 1)
            labels.append(label.strip())
            values.append(" ".join(value.lower().strip().split()))
        assert labels == ["A", "B", "C", "D"]
        assert len(values) == len(set(values)), q["id"]
