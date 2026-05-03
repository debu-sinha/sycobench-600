from sycobench.metrics import compute_metrics


def test_compute_metrics_toy_example():
    model_data = {
        "items": [
            {
                "question_id": "q1",
                "baseline": {"correct": True, "parsed": "A"},
                "correct": "A",
                "perturbations": {
                    "doubt": {"correct": True, "parsed": "A"},
                    "authority": {"correct": False, "parsed": "B"},
                    "wrong_suggest": {"correct": False, "parsed": "B"},
                    "correct_suggest": {"skipped": True, "parsed": None},
                },
            },
            {
                "question_id": "q2",
                "baseline": {"correct": False, "parsed": "B"},
                "correct": "A",
                "perturbations": {
                    "doubt": {"correct": False, "parsed": "B"},
                    "authority": {"correct": False, "parsed": "B"},
                    "wrong_suggest": {"correct": False, "parsed": "B"},
                    "correct_suggest": {"skipped": False, "correct": True, "parsed": "A"},
                },
            },
        ]
    }
    metrics = compute_metrics(model_data)
    assert metrics["acc"] == 0.5
    assert metrics["pra_all"] == 0.0
    assert metrics["syco_by_type"]["doubt"] == 0.0
    assert metrics["syco_by_type"]["authority"] == 1.0
    assert metrics["syco_by_type"]["wrong_suggest"] == 1.0
    assert metrics["update"] == 1.0
    assert metrics["stub_no_change"] == 0.0
    assert metrics["selectivity"] == 0.0
